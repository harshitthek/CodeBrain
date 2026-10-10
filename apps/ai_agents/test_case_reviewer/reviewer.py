from typing import Dict, Any, List
import json
import logging

from apps.llm.base import BaseLLMService
from apps.knowledge.service import KnowledgeService
from apps.core.models import TestCase
from .prompts import TestCaseReviewerPrompt
# from langchain_core.messages import SystemMessage, HumanMessage
from apps.utils.logger_manager import get_logger



class TestCaseReviewerAgent:
    """Test case review Agent."""
    
    def __init__(self, llm_service: BaseLLMService, knowledge_service: KnowledgeService):
        self.llm_service = llm_service
        self.knowledge_service = knowledge_service
        self.prompt = TestCaseReviewerPrompt()
        self.logger = get_logger(self.__class__.__name__)
    
    def review(self, test_case: TestCase) -> Dict[str, Any]:
        """Review test case."""
        try:
            self.logger.info(f"Test case data for review: \n{test_case}")
            # Construct test case data dictionary
            test_case_dict = {
                "description": test_case.description,
                "test_steps": test_case.test_steps,
                "expected_results": test_case.expected_results
            }
            
            # Format messages
            messages = self.prompt.format_messages(test_case_dict)
            
            self.logger.info(f"Constructed review prompt: \n{'='*50}\n{messages}\n{'='*50}")
            
            # Call LLM service
            result = self.llm_service.invoke(messages)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during review: {str(e)}", exc_info=True)
            raise Exception(f"Review failed: {str(e)}")

    def _format_prompt(self, test_case):
        """Format prompt."""
        try:
            prompt = f"""Please review the following test case:
            Description:
            {test_case.description}
            Test Steps:
            {test_case.test_steps}
            Expected Results:
            {test_case.expected_results}
            """
            return prompt.strip()
            
        except Exception as e:
            self.logger.error(f"Error formatting prompt: {str(e)}", exc_info=True)
            raise Exception(f"Failed to format prompt: {str(e)}")
