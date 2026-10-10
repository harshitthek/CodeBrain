from pathlib import Path
import yaml
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from apps.ai_agents.common.base_prompts import BasePromptManager


class TestCaseReviewerPromptManager(BasePromptManager):
    """Test case review prompt manager."""
    
    def __init__(self, config_path: str):
        """Initialize and load configuration file."""
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
    
    def get_test_case_reviewer_prompt(self) -> ChatPromptTemplate:
        """Get test case review prompt template."""
        config = self.config
        
        # Prepare system message variables and format template
        system_vars = {
            'role': config['role'],
            'evaluation_aspects': ', '.join(config['evaluation_aspects'])
        }
        
        # Create system message template
        system_template_formatted = config['system_template'].format(**system_vars)
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template_formatted)
        
        # Prepare human message variables
        human_vars = {
            'review_points': '\n'.join(f"- {point}" for point in config['review_points'])
        }
        
        # Create human message template
        human_message_prompt = HumanMessagePromptTemplate.from_template(config['human_template'])
        
        # Assemble into chat prompt template
        return ChatPromptTemplate.from_messages([
            system_message_prompt,
            human_message_prompt
        ])


class TestCaseReviewerPrompt:
    """Test case review prompt."""
    
    def __init__(self):
        # Get configuration file from configs subdirectory
        config_path = Path(__file__).parent / "configs" / "prompt_config.yaml"
        # Initialize prompt template manager
        self.prompt_manager = TestCaseReviewerPromptManager(str(config_path))
        self.prompt_template = self.prompt_manager.get_test_case_reviewer_prompt()
    
    def format_messages(self, test_case: Dict[str, Any]) -> list:
        """Format messages.
        
        Args:
            test_case: Test case data dictionary
            
        Returns:
            Formatted message list
        """
        # Format test case data as string
        test_case_str = (
            f"Description:\n{test_case.get('description', '')}\n\n"
            f"Test Steps:\n{test_case.get('test_steps', '')}\n\n"
            f"Expected Results:\n{test_case.get('expected_results', '')}"
        )
        
        # Get review points list
        review_points = '\n'.join(
            f"- {point}" 
            for point in self.prompt_manager.config['review_points']
        )
        
        return self.prompt_template.format_messages(
            test_case=test_case_str,
            review_points=review_points
        )