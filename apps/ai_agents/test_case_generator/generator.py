from typing import Dict, Any, List, Optional
import json
# from langchain_core.messages import SystemMessage, HumanMessage
from apps.llm.base import BaseLLMService
from apps.knowledge.service import KnowledgeService
from .prompts import TestCaseGeneratorPrompt
from .schemas import extract_and_parse_test_cases, GeneratedTestCaseItem
from apps.utils.logger_manager import get_logger
import re


class TestCaseGeneratorAgent:
    """Test Case Generator Agent"""
    
    def __init__(self, llm_service: BaseLLMService, knowledge_service: KnowledgeService, case_design_methods: List[str], case_categories: List[str], case_count: int = 10):
        self.llm_service = llm_service
        self.case_design_methods = case_design_methods
        self.case_categories = case_categories
        self.case_count = case_count
        self.knowledge_service = knowledge_service
        self.prompt = TestCaseGeneratorPrompt()
        self.logger = get_logger(self.__class__.__name__)
    
    async def async_generate(self, input_text: str, input_type: str = "requirement") -> List[Dict[str, Any]]:
        """Asynchronously generate test cases"""
        self.logger.info("Starting test case generation - async mode, entering TestCaseGeneratorAgent")
        input_type_desc = "Requirements Description" if input_type == "requirement" else "Code Snippet"
        
        # Get knowledge context
        knowledge_context = self._get_knowledge_context(input_text)
        self.logger.info(f"Retrieved knowledge base context: \n{'='*50}\n{knowledge_context}\n{'='*50}")
        
        case_design_methods = ",".join(self.case_design_methods) if self.case_design_methods else ""
        case_categories = ",".join(self.case_categories) if self.case_categories else ""
        
        messages = self.prompt.format_messages(
            requirements=input_text,
            case_design_methods=case_design_methods,
            case_categories=case_categories,
            case_count=self.case_count,
            knowledge_context=knowledge_context
        )
        self.logger.info(f"Constructed LLM prompt + user requirement message: \n{'='*50}\n{messages}\n{'='*50}")
        
        try:
            response = await self.llm_service.ainvoke(messages)
            result = response.content
            self.logger.info(f"Raw LLM response: \n{'='*50}\n{result}\n{'='*50}")
            
            try:
                valid_test_cases = extract_and_parse_test_cases(result)
            except Exception as parse_err:
                if "schema validation" in str(parse_err):
                    raise parse_err
                self.logger.warning(f"Schema parser fallback: {str(parse_err)}")
                json_str = self._extract_json_from_response(result)
                if not json_str:
                    raise parse_err
                test_cases = json.loads(json_str)
                cleaned_cases = self._validate_test_cases(test_cases)
                recovered_cases = []
                for tc in cleaned_cases:
                    try:
                        recovered_cases.append(GeneratedTestCaseItem.model_validate(tc).model_dump())
                    except Exception:
                        continue
                if not recovered_cases:
                    raise parse_err
                valid_test_cases = recovered_cases

            if len(valid_test_cases) > self.case_count:
                self.logger.warning(f"LLM overgenerated: expected {self.case_count}, got {len(valid_test_cases)}, auto-truncating.")
                valid_test_cases = valid_test_cases[: self.case_count]
            return valid_test_cases
            
        except Exception as e:
            raise ValueError(f"Unable to parse generated test cases: {str(e)}\nRaw response: {result}")
    
    def generate(self, input_text: str, input_type: str = "requirement") -> List[Dict[str, Any]]:
        """Synchronously generate test cases"""
        self.logger.info("Starting test case generation - sync mode, entering TestCaseGeneratorAgent")
        input_type_desc = "Requirements Description" if input_type == "requirement" else "Code Snippet"
        
        knowledge_context = self._get_knowledge_context(input_text)
        self.logger.info(f"Retrieved knowledge base context: \n{'='*50}\n{knowledge_context}\n{'='*50}")
        
        case_design_methods = ",".join(self.case_design_methods) if self.case_design_methods else ""
        case_categories = ",".join(self.case_categories) if self.case_categories else ""
        
        messages = self.prompt.format_messages(
            requirements=input_text,
            case_design_methods=case_design_methods,
            case_categories=case_categories,
            case_count=self.case_count,
            knowledge_context=knowledge_context
        )
        self.logger.info(f"Constructed LLM prompt + user requirement message: \n{'='*50}\n{messages}\n{'='*50}")
        
        try:
            response = self.llm_service.invoke(messages)
            result = response.content
            self.logger.info(f"Raw LLM response: \n{'='*50}\n{result}\n{'='*50}")
            
            try:
                valid_test_cases = extract_and_parse_test_cases(result)
            except Exception as parse_err:
                if "schema validation" in str(parse_err):
                    raise parse_err
                self.logger.warning(f"Schema parser fallback: {str(parse_err)}")
                json_str = self._extract_json_from_response(result)
                if not json_str:
                    raise parse_err
                test_cases = json.loads(json_str)
                cleaned_cases = self._validate_test_cases(test_cases)
                recovered_cases = []
                for tc in cleaned_cases:
                    try:
                        recovered_cases.append(GeneratedTestCaseItem.model_validate(tc).model_dump())
                    except Exception:
                        continue
                if not recovered_cases:
                    raise parse_err
                valid_test_cases = recovered_cases

            if len(valid_test_cases) > self.case_count:
                valid_test_cases = valid_test_cases[: self.case_count]
            return valid_test_cases
            
        except Exception as e:
            raise ValueError(f"Unable to parse generated test cases: {str(e)}\nRaw response: {result}")
    
    def _get_knowledge_context(self, input_text: str) -> str:
        """Get relevant knowledge context"""
        try:
            knowledge = self.knowledge_service.search_relevant_knowledge(input_text)
            if knowledge:
                return f"{knowledge}"
        except Exception as e:
            self.logger.warning(f"Failed to get knowledge context: {str(e)}")
        return ""
    
    def _validate_test_cases(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and fix test case format
        
        Args:
            test_cases: Raw test cases list
            
        Returns:
            Validated and normalized test cases list
        """  
        valid_test_cases = []
        required_fields = {"description", "test_steps", "expected_results"}
        
        for i, test_case in enumerate(test_cases):
            try:
                if not isinstance(test_case, dict):
                    self.logger.warning(f"Test case #{i+1} is not dictionary format, skipped")
                    continue
                
                missing_fields = required_fields - set(test_case.keys())
                if missing_fields:
                    self.logger.warning(f"Test case #{i+1} missing required fields: {missing_fields}, skipped")
                    continue
                
                if not isinstance(test_case['description'], str):
                    self.logger.warning(f"Test case #{i+1} description is not string format, skipped")
                    continue
                
                if not isinstance(test_case['test_steps'], list):
                    self.logger.warning(f"Test case #{i+1} test_steps format cannot be repaired, skipped")
                    continue
                
                if not isinstance(test_case['expected_results'], list):
                    self.logger.warning(f"Test case #{i+1} expected_results format cannot be repaired, skipped")
                    continue
                
                if not test_case['description'].strip():
                    self.logger.warning(f"Test case #{i+1} description is empty, skipped")
                    continue
                
                if not test_case['test_steps']:
                    self.logger.warning(f"Test case #{i+1} test_steps is empty, skipped")
                    continue
                
                if not test_case['expected_results']:
                    self.logger.warning(f"Test case #{i+1} expected_results is empty, skipped")
                    continue

                valid_test_cases.append(test_case)
                
            except Exception as e:
                self.logger.warning(f"Error processing test case #{i+1}: {str(e)}, skipped")
                continue
        
        if not valid_test_cases:
            raise ValueError("No valid test cases found")
        
        self.logger.info(f"Processed {len(test_cases)} test cases in total, {len(valid_test_cases)} valid")
        
        return valid_test_cases
            
    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from response and perform basic repair
        
        Args:
            response: Raw response string
            
        Returns:
            Repaired JSON string
        """
        result = ""
        right_format_pattern = r'^\[([\s\S]*)\]$'
        match = re.search(right_format_pattern, response)
        if match:
            result = match.group(0)
        else:
            last_comma_index = response.rfind('},')
            if last_comma_index != -1:
                result = response[:last_comma_index+1] + ']'
        return result
