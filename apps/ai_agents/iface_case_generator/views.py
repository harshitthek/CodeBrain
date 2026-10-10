from apps.ai_agents.iface_case_generator.iface_case_generator import parse_api_definitions, generate_test_cases_for_apis

from django.conf import settings
from django.http import JsonResponse, FileResponse
from apps.utils.progress_registry import get_progress as get_task_progress
from apps.utils.logger_manager import get_logger, set_task_context, clear_task_context
from django.shortcuts import render
# from apps.ai_agents.common.base_prompts import PromptTemplateManager
from apps.llm.utils import get_agent_llm_configs

import json
import os
import time
from pathlib import Path
import yaml


logger = get_logger(__name__)

# Fetch LLM configurations
llm_config = getattr(settings, 'LLM_PROVIDERS', {})
DEFAULT_PROVIDER, PROVIDERS = get_agent_llm_configs("iface_case_generator")


def iface_case_generator(request):
    """
    View function for API test case generator page
    """
    logger.info("===== Entering iface_case_generator view =====")
    logger.info(f"Request method: {request.method}")
    
    if request.method == 'GET':
        context = {
            'llm_providers': PROVIDERS,
            'llm_provider': DEFAULT_PROVIDER,
        }
        return render(request, 'iface_case_generator.html', context)
    elif request.method == 'POST':
        if 'single_file' in request.FILES:
            uploaded_file = request.FILES['single_file']
            logger.info(f"Received file: {uploaded_file.name}")
            
            # Check file type
            if not uploaded_file.name.lower().endswith(('.json', '.yaml', '.yml')):
                return JsonResponse({
                    'success': False,
                    'error': 'Unsupported file format. Please upload a JSON or YAML file (MeterSphere, OpenAPI/Swagger, or Postman).'
                })

            
            try:
                # Ensure uploads directory exists
                uploads_dir = os.path.join(settings.MEDIA_ROOT)
                os.makedirs(uploads_dir, exist_ok=True)
                
                # Generate unique filename
                file_name = uploaded_file.name
                base_name, ext = os.path.splitext(file_name)
                counter = 1
                while os.path.exists(os.path.join(uploads_dir, file_name)):
                    file_name = f"{base_name}_{counter}{ext}"
                    counter += 1
                
                # Save file to uploads directory
                file_path = os.path.join(uploads_dir, file_name)
                with open(file_path, 'wb+') as f:
                    for chunk in uploaded_file.chunks():
                        f.write(chunk)
                
                logger.info(f"File saved successfully: {file_path}")
                
                # Parse JSON file and extract API list
                api_list = parse_api_definitions(file_path)
                
                return JsonResponse({
                    'success': True,
                    'api_list': api_list,
                    'file_path': file_path
                })
                
            except Exception as e:
                logger.error(f"Failed to save file: {str(e)}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'error': f'Failed to save file: {str(e)}'
                })
        
        elif 'generate_test_cases' in request.POST:
            file_path = request.POST.get('file_path')
            selected_apis = json.loads(request.POST.get('selected_apis'))
            count_per_api = int(request.POST.get('count_per_api', 1))
            priority = request.POST.get('priority', 'P0')
            llm_provider = request.POST.get('llm_provider', 'deepseek')
            task_id = request.POST.get('task_id') or f"task_{int(time.time()*1000)}_{request.user.id if request.user.is_authenticated else 'anon'}"
            
            # Background thread for asynchronous generation, return immediately
            import threading
            def _bg_job():
                try:
                    set_task_context(task_id)
                    rules_override = request.POST.get('rules_override') or None
                    generate_test_cases_for_apis(
                        file_path, selected_apis, count_per_api, priority, llm_provider, task_id,
                        rules_override=rules_override
                    )
                except Exception as e:
                    logger.error(f"Background generation failed: {e}")
                finally:
                    clear_task_context()
            t = threading.Thread(target=_bg_job, name=f"gen-{task_id}")
            t.daemon = True
            t.start()
            
            return JsonResponse({
                'success': True,
                'task_id': task_id
            })
        
        else:
            return JsonResponse({
                'success': False,
                'error': 'No file received'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Unsupported request method'
    })


def get_generation_progress_api(request):
    """Query progress: return progress from in-memory registry by task_id"""
    try:
        task_id = request.GET.get('task_id')
        if not task_id:
            return JsonResponse({'success': False, 'message': 'Missing task_id'})
        progress = get_task_progress(task_id)
        if not progress:
            return JsonResponse({'success': False, 'message': 'Progress information not found'})
        
        progress_dict = progress.dict() if hasattr(progress, 'dict') else progress
        return JsonResponse({'success': True, 'progress': progress_dict})
    except Exception as e:
        logger.error(f"Failed to get progress: {e}")
        return JsonResponse({'success': False, 'message': str(e)})


def get_testcase_rule_template(request):
    """Return 'Test Case Generation Rules' text from template (read-only)"""
    try:
        config_path = Path(__file__).parent / 'configs' / 'prompt_config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}

        human_tpl = (cfg.get('human_template') or '').strip()
        rule_text = ''
        if human_tpl:
            marker = '## Test Case Generation Rules'
            idx = human_tpl.find(marker)
            if idx >= 0:
                rule_text = human_tpl[idx:]
            if not rule_text:
                rule_text = human_tpl
        return JsonResponse({'success': True, 'rule_text': rule_text})
    except Exception as e:
        logger.error(f"Failed to read rule template: {e}")
        return JsonResponse({'success': False, 'message': str(e)})


def download_file(request):
    """File download view"""
    file_path = request.GET.get('file_path')
    if not file_path or not os.path.exists(file_path):
        return JsonResponse({'error': 'File does not exist'}, status=404)
    
    # Security check: ensure file is inside uploads directory
    uploads_dir = os.path.abspath('uploads')
    file_abs_path = os.path.abspath(file_path)
    
    if not file_abs_path.startswith(uploads_dir):
        return JsonResponse({'error': 'Access denied'}, status=404)
    
    filename = os.path.basename(file_path)
    resp = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
    resp['Content-Type'] = 'application/octet-stream'
    resp['X-Content-Type-Options'] = 'nosniff'
    return resp


def _normalize_case_to_flat_contract(case: dict, api_defaults: dict = None) -> dict:
    """Normalize MeterSphere case structure to flat runner/exporter contract."""
    c = dict(case)
    api_defaults = api_defaults or {}
    req = c.setdefault('request', {})

    if not req.get('path'):
        req['path'] = api_defaults.get('path', '')
    if not req.get('method'):
        req['method'] = api_defaults.get('method', 'GET')

    if not c.get('path') and req.get('path'):
        c['path'] = req['path']
    if not c.get('method') and req.get('method'):
        c['method'] = req['method']

    # 1. Normalize body
    if 'request_body_json' not in c:
        body_obj = req.get('body')
        if isinstance(body_obj, dict):
            json_body = body_obj.get('jsonBody')
            if isinstance(json_body, dict):
                raw_val = json_body.get('jsonValue', '')
                if isinstance(raw_val, str) and raw_val.strip():
                    try:
                        c['request_body_json'] = json.loads(raw_val)
                    except Exception:
                        c['request_body_json'] = raw_val
                elif isinstance(raw_val, dict):
                    c['request_body_json'] = raw_val

    # 2. Normalize query params
    if 'request_query' not in c and req.get('query'):
        mapped_q = []
        for q in req.get('query', []):
            if isinstance(q, dict):
                k = q.get('param_name') or q.get('name') or q.get('key')
                v = q.get('param_value') if q.get('param_value') is not None else q.get('value')
                if k:
                    mapped_q.append({'param_name': k, 'param_value': v})
        c['request_query'] = mapped_q

    # 3. Normalize REST params
    if 'request_rest' not in c and req.get('rest'):
        mapped_r = []
        for r in req.get('rest', []):
            if isinstance(r, dict):
                k = r.get('param_name') or r.get('name') or r.get('key')
                v = r.get('param_value') if r.get('param_value') is not None else r.get('value')
                if k:
                    mapped_r.append({'param_name': k, 'param_value': v})
        c['request_rest'] = mapped_r

    # 4. Flatten assertions from children if not already present
    if not c.get('assertions'):
        flat_assertions = []
        for child in req.get('children', []):
            if isinstance(child, dict):
                cfg = child.get('assertionConfig', {})
                for a in cfg.get('assertions', []):
                    jpa = a.get('jsonPathAssertion', {})
                    if jpa.get('assertions'):
                        flat_assertions.extend(jpa['assertions'])
                    elif 'expression' in a:
                        flat_assertions.append(a)
        if flat_assertions:
            c['assertions'] = flat_assertions
            if not c.get('assertion_condition') and flat_assertions[0].get('condition'):
                c['assertion_condition'] = flat_assertions[0].get('condition')

    return c


def _extract_cases_from_payload(data: dict) -> list:
    """Extract test cases directly from data or from referenced file_path and normalize them."""
    if not isinstance(data, dict):
        raise ValueError("Request payload must be a JSON object")
    cases = data.get('test_cases')
    if cases is not None:
        if not isinstance(cases, list) or not all(isinstance(c, dict) for c in cases):
            raise ValueError("test_cases must be a list of objects")
        if cases:
            return [_normalize_case_to_flat_contract(c) for c in cases]
    file_path = data.get('file_path')
    if file_path:
        media_root = os.path.realpath(str(settings.MEDIA_ROOT))
        real_path = os.path.realpath(str(file_path))
        try:
            is_within_media = os.path.commonpath([real_path, media_root]) == media_root
        except ValueError:
            is_within_media = False

        if is_within_media and os.path.isfile(real_path):
            try:
                with open(real_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                extracted = []
                for api in content.get('apiDefinitions', []):
                    for case in api.get('apiTestCaseList', []):
                        if not isinstance(case, dict):
                            continue
                        extracted.append(_normalize_case_to_flat_contract(case, api_defaults=api))
                return extracted
            except Exception as e:
                logger.warning(f"Failed to read test cases from {real_path}: {e}")
    return []


def execute_test_cases(request):
    """Execute API test cases asynchronously against a target base URL"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    if getattr(settings, 'REQUIRE_RUNNER_AUTH', False):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'Authentication required'}, status=403)

    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            return JsonResponse({'success': False, 'message': 'Invalid JSON payload'}, status=400)
        base_url = str(data.get('base_url', '')).strip()
        test_cases = _extract_cases_from_payload(data)

        if not base_url:
            return JsonResponse({'success': False, 'message': 'Target base_url is required'}, status=400)
        if not test_cases:
            return JsonResponse({'success': False, 'message': 'No test cases found for execution'}, status=400)

        from asgiref.sync import async_to_sync
        from .runner import APITestRunner

        runner = APITestRunner(base_url=base_url)
        MAX_EXECUTION_CASES = 100
        if len(test_cases) > MAX_EXECUTION_CASES:
            return JsonResponse({
                'success': False,
                'message': f'Submitted test suite exceeds maximum limit of {MAX_EXECUTION_CASES} cases.'
            }, status=400)

        summary = async_to_sync(runner.execute_suite)(test_cases)

        return JsonResponse({
            'success': True,
            'summary': summary
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON in request body'}, status=400)
    except ValueError as ve:
        return JsonResponse({'success': False, 'message': str(ve)}, status=400)
    except Exception as e:
        logger.error(f"Error executing test suite: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'message': f"Execution error: {str(e)}"}, status=500)



def export_pytest_view(request):
    """Export test cases to standalone executable Pytest script"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    try:
        from django.http import HttpResponse
        from .exporters import generate_pytest_script

        data = json.loads(request.body)
        if not isinstance(data, dict):
            return JsonResponse({'success': False, 'message': 'Invalid JSON payload'}, status=400)
        base_url = str(data.get('base_url', 'http://127.0.0.1:8000'))
        test_cases = _extract_cases_from_payload(data)

        if not test_cases:
            return JsonResponse({'success': False, 'message': 'No test cases found to export'}, status=400)

        script_code = generate_pytest_script(test_cases, base_url=base_url)

        response = HttpResponse(script_code, content_type='text/x-python')
        response['Content-Disposition'] = 'attachment; filename="test_api_generated.py"'
        return response

    except (json.JSONDecodeError, ValueError) as ve:
        return JsonResponse({'success': False, 'message': str(ve)}, status=400)
    except Exception as e:
        logger.error(f"Failed to export Pytest script: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


def export_postman_view(request):
    """Export test cases to Postman Collection v2.1.0 JSON"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    try:
        from django.http import HttpResponse
        from .exporters import generate_postman_collection

        data = json.loads(request.body)
        if not isinstance(data, dict):
            return JsonResponse({'success': False, 'message': 'Invalid JSON payload'}, status=400)
        base_url = str(data.get('base_url', 'http://127.0.0.1:8000'))
        test_cases = _extract_cases_from_payload(data)

        if not test_cases:
            return JsonResponse({'success': False, 'message': 'No test cases found to export'}, status=400)

        collection = generate_postman_collection(test_cases, base_url=base_url)
        content = json.dumps(collection, ensure_ascii=False, indent=2)

        response = HttpResponse(content, content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="codebrain_postman_collection.json"'
        return response

    except (json.JSONDecodeError, ValueError) as ve:
        return JsonResponse({'success': False, 'message': str(ve)}, status=400)
    except Exception as e:
        logger.error(f"Failed to export Postman collection: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

