from pathlib import Path
import yaml
# from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from apps.ai_agents.common.base_prompts import BasePromptManager
class TestCaseGeneratorPromptManager(BasePromptManager):
    """Test case generation prompt manager."""
    
    def __init__(self, config_path: str):
        """Initialize and load configuration file."""
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
    
    def get_test_case_generator_prompt(self) -> ChatPromptTemplate:
        """Get test case generation prompt template."""
        config = self.config
        
        # Prepare system message variables and format template
        system_vars = {
            'role': config['role'],
            'capabilities': config['capabilities'],
            'test_methods': ', '.join(config['test_methods']),
            'test_types': ', '.join(config['test_types'])
        }
        
        # Create system message template
        system_template_formatted = config['system_template'].format(**system_vars)
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template_formatted)
        
        # Create human message template
        human_message_prompt = HumanMessagePromptTemplate.from_template(config['human_template'])
        
        # Assemble into chat prompt template
        return ChatPromptTemplate.from_messages([
            system_message_prompt,
            human_message_prompt
        ])


class TestCaseGeneratorPrompt:
    """Test case generation prompt."""
    
    def __init__(self):
        # Get configuration file from configs subdirectory
        config_path = Path(__file__).parent / "configs" / "prompt_config.yaml"
        # Initialize prompt template manager
        self.prompt_manager = TestCaseGeneratorPromptManager(str(config_path))
        self.prompt_template = self.prompt_manager.get_test_case_generator_prompt()
    
    def format_messages(self, requirements: str, case_design_methods: str = "", 
                       case_categories: str = "", knowledge_context: str = "", case_count: int = 10) -> list:
        """Format messages.
        
        Args:
            requirements: Requirements description
            case_design_methods: Test case design methods
            case_categories: Test case categories
            knowledge_context: Knowledge base context
            case_count: Number of test cases to generate
        Returns:
            Formatted message list
        """
        # Handle empty values
        if not case_design_methods:
            case_design_methods = "all applicable test case design methods"
        
        if not case_categories:
            case_categories = "all applicable test types"
            
        # Format knowledge context prompt
        knowledge_prompt = (
            f"referring to the following knowledge base content:\n{knowledge_context}"
            if knowledge_context
            else "based on your expertise"
        )
        
        return self.prompt_template.format_messages(
            requirements=requirements,
            case_design_methods=case_design_methods,
            case_categories=case_categories,
            case_count=case_count,
            knowledge_context=knowledge_prompt
        )