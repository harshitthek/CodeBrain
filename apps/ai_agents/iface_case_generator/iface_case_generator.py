import json
import time
import copy
import os
import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from .prompts import APITestCaseGeneratorPrompt
from apps.llm.base import LLMServiceFactory
from .iface_test_case_parser import parse_minimal_cases_or_raise
from .retry_utils import generate_with_retry
from apps.utils.logger_manager import set_task_context, clear_task_context

from apps.utils.progress_registry import set_progress
from apps.utils.progress_schema import TaskStatus
from apps.utils.logger_manager import get_logger

# Attach unified task_type to logs in this module for frontend to distinguish "generation" tasks
_base_logger = get_logger('apps.iface_case_generator')
logger = logging.LoggerAdapter(_base_logger, {'task_type': 'generation'})

class APITestCaseGeneratorAgent:
    """API Test Case Generator Agent"""
    
    def __init__(self, llm_provider: str = "deepseek"):
        self.llm_provider = llm_provider
        self.llm = LLMServiceFactory.create(llm_provider)
        self.prompt = APITestCaseGeneratorPrompt()
        self.test_case_full_template = self._load_test_case_full_template()
        self.max_workers = 5
        # Optional: user-overridden "Test Case Generation Rules"
        self.rule_override: Optional[str] = None
    
    def _has_request_parameters(self, api_info: Dict[str, Any]) -> bool:
        """Check whether the API specification contains any request parameters (query/rest/body(JSON)).
        - query/rest: Non-empty list is considered having parameters
        - body(JSON): jsonBody.jsonValue is parseable and contains keys, or jsonSchema.properties contains keys
        """
        request = api_info.get('request') or {}

        # query
        query_params = request.get('query')
        if isinstance(query_params, list) and len(query_params) > 0:
            return True

        # rest
        rest_params = request.get('rest')
        if isinstance(rest_params, list) and len(rest_params) > 0:
            return True

        # body (JSON)
        body = request.get('body')
        if isinstance(body, dict) and body.get('bodyType') == 'JSON':
            json_body = body.get('jsonBody', {}) or {}
            json_value_str = json_body.get('jsonValue')
            if isinstance(json_value_str, str) and json_value_str.strip():
                try:
                    parsed = json.loads(json_value_str)
                    if isinstance(parsed, dict) and len(parsed) > 0:
                        return True
                except Exception:
                    pass
            props = (json_body.get('jsonSchema') or {}).get('properties') or {}
            if isinstance(props, dict) and len(props) > 0:
                return True

        return False

    def _load_test_case_full_template(self) -> Dict[str, Any]:
        """Load test case structure template"""
        template_path = os.path.join(
            os.path.dirname(__file__),
            'templates',
            'iface_test_case_template.jsonc'
        )
        try:
            import json5  # type: ignore
            with open(template_path, 'r', encoding='utf-8') as f:
                return json5.load(f)
        except Exception as e:
            logger.warning(f"Failed to parse template using json5 or not installed, falling back to standard JSON: {e}")
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def _generate_multiple_test_cases(self, api_info: Dict[str, Any], 
                                      priority: str, count: int) -> Optional[List[Dict[str, Any]]]:
        """Generate multiple test cases for an API in a single LLM call (returns array).
        Uses minimal output protocol where LLM only generates diff fields, merged locally into full template.
        Uses Pydantic parsing and automatic retry mechanism.
        """
        try:
            minimal_cases = self._generate_with_retry(api_info, priority, count)
            if not minimal_cases:
                return None

            processed: List[Dict[str, Any]] = []
            for mcase in minimal_cases:
                try:
                    mcase_dict = mcase.dict() if hasattr(mcase, 'dict') else mcase
                    processed.append(self._merge_minimal_case_to_full_case(mcase_dict, api_info, priority))
                except Exception as e:
                    logger.error("Failed to merge minimal test case: %s", e)
            return processed
        except Exception as e:
            logger.error("Failed to generate multiple test cases: %s", e)
            return None

    def _create_minimal_generation_template(self) -> Dict[str, Any]:
        return {
            "id": "TC-001",
            "name": "Case Name (Interface Name_Test Point Description, <= 40 chars)",
            "description": "Case Description (<= 60 chars, optional)",
            "request_body_json": { 
                "param_name": "Parameter name to test (e.g., isVirtually)",
                "param_value": "Parameter value for testing (e.g., 1)"     
            },
            "request_query": [
                {
                    "param_name": "Parameter name to test (e.g., pageSize)",
                    "param_value": "Parameter value for testing (e.g., 10)"
                }
            ],
            "request_rest": [
                {
                    "param_name": "Parameter name to test (e.g., userCode)",
                    "param_value": "Parameter value for testing (e.g., oa1922897972947259394)"
                }
            ],
            "assertion_condition": "Assertion condition, based on whether test parameters are valid or invalid, value must be EQUALS or NOT_EQUALS"
        }

    def _build_messages_minimal(self, api_info: Dict[str, Any], priority: str, count: int, 
                               include_format_instructions: bool = False) -> list:
        minimal_template = self._create_minimal_generation_template()
        return self.prompt.format_messages(
            api_info=api_info,
            priority=priority,
            case_count=count,
            api_test_case_min_template=json.dumps(minimal_template, ensure_ascii=False, indent=2),
            include_format_instructions=include_format_instructions,
            case_rule_override=self.rule_override
        )

    def _generate_with_retry(self, api_info: Dict[str, Any], priority: str, count: int) -> Optional[List]:
        """Generate minimal cases using retry mechanism"""
        
        include_format_instructions = False

        def call_llm_once():
            messages = self._build_messages_minimal(
                api_info, priority, count,
                include_format_instructions=include_format_instructions
            )
            
            try:
                prompt_text = "\n\n".join([getattr(m, 'content', str(m)) for m in messages])
                logger.info("[LLM Prompt-MULTI] API=%s Count=%s\n%s", api_info.get('name', ''), count, prompt_text)
            except Exception:
                pass

            if hasattr(self.llm, 'generate_with_history'):
                response = self.llm.generate_with_history(messages)
            else:
                from langchain_core.messages import HumanMessage, SystemMessage
                langchain_messages = []
                for msg in messages:
                    if hasattr(msg, 'type') and msg.type == 'system':
                        langchain_messages.append(SystemMessage(content=msg.content))
                    elif hasattr(msg, 'type') and msg.type == 'human':
                        langchain_messages.append(HumanMessage(content=msg.content))
                    elif hasattr(msg, 'role') and msg.role == 'system':
                        langchain_messages.append(SystemMessage(content=msg.content))
                    elif hasattr(msg, 'role') and msg.role == 'user':
                        langchain_messages.append(HumanMessage(content=msg.content))
                    else:
                        langchain_messages.append(msg)
                invoke_result = self.llm.invoke(langchain_messages)
                response = getattr(invoke_result, 'content', invoke_result)
            
            logger.info("LLM multi-case raw response: %s", response)
            return response

        def on_retry(attempt):
            logger.warning("Parsing failed, retry #%d, enhancing format constraints", attempt + 1)
            nonlocal count
            count = max(1, count // 2)
            nonlocal include_format_instructions
            include_format_instructions = True

        try:
            return generate_with_retry(
                call_llm=call_llm_once,
                parse_cases=parse_minimal_cases_or_raise,
                on_retry=on_retry,
                max_retries=2
            )
        except Exception as e:
            logger.error("Still failed after retries: %s", e)
            return None

    def _merge_minimal_case_to_full_case(self, minimal_case: Dict[str, Any], api_info: Dict[str, Any], priority: str) -> Dict[str, Any]:
        """Use template structure defined in template file and fill LLM generated parameters and assertions back into template to form a valid test case"""
        full_case = copy.deepcopy(self.test_case_full_template)
        # 1. Directly reuse request structure in API definition, parameters and assertions are generated by LLM and backfilled
        full_case['request'] = copy.deepcopy(api_info.get('request')) 

        req = full_case.get('request')
        child0 = req['children'][0]

        # 2. Fill priority and tags
        full_case['priority'] = priority
        full_case['tags'] = ['CodeBrain']

        # 3. Fill case name
        name = minimal_case.get('name') or 'CodeBrain Generated Case'
        full_case['name'] = name
        full_case['request']['name'] = name

        # 4. Backfill LLM generated parameters into full_case request
        self._apply_minimal_request_overrides(full_case, minimal_case, api_info)

        # 5. Backend fixed assertion generation, only LLM condition is used
        assertion_condition = minimal_case.get('assertion_condition', 'EQUALS')
        fixed_assertion = self._generate_fixed_assertion(assertion_condition)
        
        child0['assertionConfig']['assertions'] = [fixed_assertion]

        return full_case

    def _apply_minimal_request_overrides(self, full_case: Dict[str, Any], minimal_case: Dict[str, Any], api_info: Dict[str, Any]) -> None:
        """Apply LLM generated diff values to request (body/query/rest) and sync type information from API definition"""
        req = full_case.get('request', {})
        
        if 'request_body_json' in minimal_case:
            body = req.get('body')
            if not isinstance(body, dict):
                raise ValueError("Invalid request: missing body or wrong type")
            json_body = body.get('jsonBody')
            if not isinstance(json_body, dict):
                raise ValueError("Invalid request: missing body.jsonBody or wrong type")
            data_by_type = body.get('bodyDataByType')
            if not isinstance(data_by_type, dict):
                raise ValueError("Invalid request: missing body.bodyDataByType or wrong type")

            json_value_str = json.dumps(minimal_case['request_body_json'], ensure_ascii=False, indent=2)
            json_body['jsonValue'] = json_value_str
            data_by_type['jsonValue'] = json_value_str
        
        if 'request_query' in minimal_case:
            llm_query = minimal_case['request_query'] or []
            full_case_query = req.get('query', [])

            full_case_query_map: Dict[str, Any] = {}
            for param in full_case_query:
                param_key = param.get('key') or param.get('name')
                if param_key:
                    full_case_query_map[param_key] = param

            merged_query: List[Dict[str, Any]] = []
            for llm_param in llm_query:
                q_name = llm_param.get('param_name') or llm_param.get('key') or llm_param.get('name')
                q_value = llm_param.get('param_value') or llm_param.get('value')
                if q_name in full_case_query_map:
                    api_param = full_case_query_map[q_name]
                    merged_param = api_param.copy()
                    merged_param['value'] = q_value
                    merged_query.append(merged_param)
                else:
                    logger.warning(f"Query parameter not found in API definition: {q_name}")

            req['query'] = merged_query
        
        if 'request_rest' in minimal_case:
            llm_rest = minimal_case['request_rest'] or []
            full_case_rest = req.get('rest', [])
            
            full_case_rest_map = {}
            for param in full_case_rest:
                param_key = param.get('key') or param.get('name')
                if param_key:
                    full_case_rest_map[param_key] = param
            
            merged_rest = []
            for llm_param in llm_rest:
                param_name = llm_param.get('param_name') or llm_param.get('key')
                param_value = llm_param.get('param_value') or llm_param.get('value')
                
                if param_name in full_case_rest_map:
                    api_param = full_case_rest_map[param_name]
                    merged_param = api_param.copy()
                    merged_param['value'] = param_value
                    merged_rest.append(merged_param)
                else:
                    logger.warning(f"Parameter not found in API definition: {param_name}")
            
            req['rest'] = merged_rest
        
        full_case['request'] = req

    def generate_test_cases_for_apis_batch(self, api_definitions: List[Dict], 
                                       selected_apis: List[str], count_per_api: int, 
                                       priority: str, task_id: Optional[str] = None) -> Dict:
        """Batch generate test cases (multi-threaded generation, main thread merge)"""
        try:
            if not task_id:
                task_id = f"task_{int(time.time()*1000)}"
            
            set_task_context(task_id)
            
            # step 1 - Initialize progress data, including empty logs
            set_progress(task_id, {
                'step': 1,
                'message': 'Parsing API definition file',
                'percentage': 10,
                'logs': []
            })
            path_to_api: Dict[str, Dict[str, Any]] = {}
            for api in api_definitions:
                api_path = api.get('path')
                if api_path:
                    path_to_api[api_path] = api

            valid_paths = [p for p in selected_apis if p in path_to_api]
            if not valid_paths:
                set_progress(task_id, {
                    'step': -1,
                    'message': 'No valid API paths found',
                    'percentage': 0
                })
                return {
                    'success': False,
                    'message': 'No valid API paths found',
                }

            # step 2
            set_progress(task_id, {
                'step': 2,
                'message': 'Validating API parameters',
                'percentage': 20
            })
            logger.info(f"Starting concurrent generation. Selected APIs: {len(valid_paths)}, Cases per API: {count_per_api}")

            results_by_path: Dict[str, List[Dict[str, Any]]] = {p: [] for p in valid_paths}

            # step 3
            set_progress(task_id, {
                'step': 3,
                'message': 'Calling LLM to generate test cases',
                'percentage': 30,
                'total_apis': len(valid_paths),
                'completed_apis': 0
            })
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_path = {}
                for api_path in valid_paths:
                    api_def = path_to_api[api_path]
                    fut = executor.submit(self._generate_cases_for_single_api, api_def, priority, count_per_api, task_id)
                    future_to_path[fut] = (api_path, api_def.get('name', ''))

                completed = 0
                for fut in as_completed(future_to_path):
                    api_path, api_name = future_to_path[fut]
                    try:
                        cases = fut.result() or []
                        results_by_path[api_path].extend(cases)
                        completed += 1
                        percent = 30 + int((completed * 50) / max(1, len(valid_paths)))
                        set_progress(task_id, {
                            'step': 3,
                            'message': f'Processing API: {api_name}',
                            'percentage': percent,
                            'current_api': api_name,
                            'total_apis': len(valid_paths),
                            'completed_apis': completed
                        })
                        logger.info(f"API generation completed: {api_name} - Added {len(cases)} cases")
                    except Exception as e:
                        completed += 1
                        logger.error(f"API generation exception: {api_name}: {e}")

            # step 4
            set_progress(task_id, {
                'step': 4,
                'message': 'Merging test cases',
                'percentage': 80
            })
            total_cases = 0
            for api_path, cases in results_by_path.items():
                api_def = path_to_api[api_path]
                if 'apiTestCaseList' not in api_def or not isinstance(api_def['apiTestCaseList'], list):
                    api_def['apiTestCaseList'] = []
                api_def['apiTestCaseList'].extend(cases)
                total_cases += len(cases)

            # step 5
            logger.info(f"Merge completed, successfully merged {total_cases} test cases for {len(results_by_path)} APIs")
            return {
                'success': True,
                'message': f'Successfully generated {total_cases} test cases for {len(valid_paths)} APIs',
                'generated_cases': total_cases,
                'selected_api_count': len(valid_paths),
                'task_id': task_id
            }

        except Exception as e:
            logger.error(f"Batch test case generation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            clear_task_context()

    def _generate_cases_for_single_api(self, api_def: Dict[str, Any], priority: str, count_per_api: int, task_id: str = None) -> List[Dict[str, Any]]:
        """Generate multiple test cases for a single API (concurrent by API, single LLM call)"""        
        if task_id:
            set_task_context(task_id)
        
        try:
            api_name = api_def.get('name', '')
            if not self._has_request_parameters(api_def):
                logger.warning("API query, rest, and body have no request parameters, skipping LLM generation: %s", api_name)
                return []
            cases = self._generate_multiple_test_cases(api_def, priority, count_per_api) or []
            logger.info("API generation completed: %s - Added %d cases", api_name, len(cases))
            return cases
        except Exception as e:
            logger.error("API multi-case generation exception: %s: %s", api_def.get('name', ''), e)
            return []
        finally:
            if task_id:
                clear_task_context()

    def _generate_fixed_assertion(self, condition: str) -> Dict[str, Any]:
        """Backend fixed assertion structure generation, only LLM decides condition"""
        ts = int(time.time() * 1000)
        return {
            "assertionType": "RESPONSE_BODY",
            "enable": True,
            "name": "Response Body",
            "id": f"{ts}",
            "projectId": None,
            "assertionBodyType": "JSON_PATH",
            "jsonPathAssertion": {
                "assertions": [{
                    "enable": True,
                    "expression": "code",
                    "condition": condition,
                    "expectedValue": "10000",
                    "valid": True
                }]
            },
            "xpathAssertion": {"responseFormat": "XML", "assertions": []},
            "documentAssertion": None,
            "regexAssertion": {"assertions": []},
            "bodyAssertionClassByType": "io.metersphere.project.api.assertion.body.MsJSONPathAssertion",
            "bodyAssertionDataByType": {
                "assertions": [{
                    "enable": True,
                    "expression": "code",
                    "condition": condition,
                    "expectedValue": "10000",
                    "valid": True
                }]
            }
        }


def parse_api_definitions(file_path: str) -> List[Dict]:
    """Parse API definition file and extract API list"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        api_list = []
        for api in data.get('apiDefinitions', []):
            case_count = len(api.get('apiTestCaseList', []))
            api_list.append({
                'path': api.get('path', ''),
                'name': api.get('name', ''),
                'method': api.get('method', ''),
                'has_test_cases': case_count > 0,
                'test_case_count': case_count
            })
        
        return api_list
    except Exception as e:
        logger.error(f"Failed to parse API definition file: {e}")
        return []


def generate_test_cases_for_apis(file_path: str, selected_apis: list, count_per_api: int, 
                                 priority: str, llm_provider: str, task_id: Optional[str] = None,
                                 rules_override: Optional[str] = None) -> Dict:
    """Batch generate test cases for selected API specifications
    
    Args:
        file_path: API definition file path (JSON format, exported from MeterSphere)
        selected_apis: List of selected API endpoints
        count_per_api: Number of test cases to generate per API (1-10)
        priority: Test case priority (P0-P4)
        llm_provider: LLM provider name (e.g., 'deepseek', 'qwen', etc.)
        task_id: Task ID for progress tracking and log correlation (optional)
        rules_override: Custom test case generation rules (Markdown format) to override defaults (optional)
        
    Returns:
        Dict: Dictionary containing generation result
            - success: bool
            - message: str
            - generated_cases: int
            - selected_api_count: int
            - task_id: str
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        agent = APITestCaseGeneratorAgent(llm_provider)
        if rules_override:
            try:
                agent.rule_override = rules_override
                logger.info("Using custom rules override: length=%d", len(rules_override))
            except Exception:
                pass
        
        result = agent.generate_test_cases_for_apis_batch(
            data['apiDefinitions'], selected_apis, count_per_api, priority, task_id
        )
        try:
            logger.info("Batch generation return: %s", result)
        except Exception:
            pass
        
        if result['success']:
            logger.info("Starting to write back file: %s", file_path)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logger.info("Write back successful, setting 100% progress and download path")
            except Exception as e:
                logger.error("Failed to write back file: %s", e)
                if task_id:
                    try:
                        set_progress(task_id, {
                            'step': -1,
                            'message': f'Failed to write back file: {e}',
                            'status': TaskStatus.FAILED
                        })
                    except Exception:
                        pass
                return result

            if task_id:
                try:
                    set_progress(task_id, {
                        'step': 5,
                        'message': f'{result.get("message", "Generation completed")}, file saved',
                        'percentage': 100,
                        'file_path': file_path,
                        'status': TaskStatus.COMPLETED
                    })
                    logger.info("Set 100% progress and download path")
                except Exception as e:
                    logger.error("Failed to set 100% progress: %s", e)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate test cases: {e}")
        return {
            'success': False,
            'error': str(e)
        }
