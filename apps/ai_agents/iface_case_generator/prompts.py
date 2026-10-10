from pathlib import Path
import yaml
import json
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from apps.ai_agents.common.base_prompts import BasePromptManager


class APITestCaseGeneratorPromptManager(BasePromptManager):
    """API test case generator prompt manager"""
    
    def __init__(self, config_path: str):
        """Initialize and load configuration file"""
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
    
    def get_api_test_case_generator_prompt(self) -> ChatPromptTemplate:
        """Get prompt template for API test case generation"""
        config = self.config
        
        # Prepare system message variables and format template
        system_vars = {
            'role': config['role'],
            'capabilities': config['capabilities'],
            'api_analysis_focus': ', '.join(config['api_analysis_focus']),
            'template_understanding': '\n'.join(config['template_understanding']),
            'case_count': '{case_count}'
        }
        
        # Create system message template
        system_template_formatted = config['system_template'].format(**system_vars)
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template_formatted)
        
        # Create human message template
        human_message_prompt = HumanMessagePromptTemplate.from_template(config['human_template'])
        
        # Combine into chat prompt template
        return ChatPromptTemplate.from_messages([
            system_message_prompt,
            human_message_prompt
        ])


class APITestCaseGeneratorPrompt:
    """API test case generator prompt"""
    
    def __init__(self):
        # Load config file from configs subfolder in current directory
        config_path = Path(__file__).parent / "configs" / "prompt_config.yaml"
        # Initialize specific prompt template manager
        self.prompt_manager = APITestCaseGeneratorPromptManager(str(config_path))
        self.prompt_template = self.prompt_manager.get_api_test_case_generator_prompt()
    
    def format_messages(self, api_info: Dict[str, Any], priority: str, 
                       case_count: int, api_test_case_min_template: str, 
                       include_format_instructions: bool = False,
                       case_rule_override: str | None = None) -> list:
        """Format messages
        
        Args:
            api_info: API specification info
            priority: Test case priority
            case_count: Number of test cases to generate
            api_test_case_min_template: Test case structure template
            include_format_instructions: Whether to include format instructions (used on retry)
            case_rule_override: Custom test case generation rules (Markdown format) to override default rules (optional)
            
        Returns:
            List of formatted messages
        """
        # Generate response summary; if present include header, otherwise empty
        response_summary = self._format_response_summary(api_info)
        response_block = f"## Response Summary\n{response_summary}" if response_summary else ""
        
        # Get base messages
        messages = self.prompt_template.format_messages(
            api_name=api_info.get('name', ''),
            method=api_info.get('method', ''),
            path=api_info.get('path', ''),
            priority=priority,
            case_count=case_count,
            api_parameters_info=self._format_api_parameters_info(api_info),
            api_response_summary=response_block,
            api_test_case_min_template=api_test_case_min_template
        )

        # If rules override is provided, append/replace in the last human message
        if case_rule_override:
            override_text = str(case_rule_override)
            markers = ['## Test Case Generation Rules']
            for msg in reversed(messages):
                if hasattr(msg, 'content'):
                    content = msg.content
                    if isinstance(content, str):
                        replaced = False
                        for marker in markers:
                            idx = content.find(marker)
                            if idx >= 0:
                                msg.content = content[:idx] + override_text
                                replaced = True
                                break
                        if not replaced:
                            msg.content = content + f"\n\n{override_text}"
                    break
        
        # If format instructions are needed (on retry), append to last HumanMessage
        if include_format_instructions:
            try:
                from .api_test_case_parser import get_format_instructions
                format_instr = get_format_instructions()
                format_extra = f"\n\nImportant Requirements:\n- Output JSON only, no explanatory text\n- Strictly follow the format instructions below:\n{format_instr}"
                
                for msg in reversed(messages):
                    if hasattr(msg, 'content') and hasattr(msg, 'type') and msg.type == 'human':
                        if isinstance(msg.content, str):
                            msg.content += format_extra
                        break
            except ImportError:
                pass
        
        return messages
    
    def _format_api_parameters_info(self, api_info: Dict[str, Any]) -> str:
        """Format key parameter info"""
        request = api_info.get('request', {})
        
        params_info = []
        
        # Query parameters
        for param in request.get('query', []):
            params_info.append({
                'name': param.get('key'),
                'type': param.get('paramType'),
                'required': param.get('required'),
                'sample': param.get('value'),
                'minimum': param.get('minimum', None),
                'maximum': param.get('maximum', None),
                'minLength': param.get('minLength', None),
                'maxLength': param.get('maxLength'),
                'location': 'query'
            })
        
        # Rest parameters
        for param in request.get('rest', []):
            params_info.append({
                'name': param.get('key'),
                'type': param.get('paramType'),
                'required': param.get('required'),
                'sample': param.get('value'),
                'minimum': param.get('minimum', None),
                'maximum': param.get('maximum', None),
                'minLength': param.get('minLength', None),
                'maxLength': param.get('maxLength', None),
                'location': 'path'
            })
        
        # Body parameters
        body = request.get('body', {})
        if body.get('bodyType') == 'JSON':
            json_body = body.get('jsonBody', {})
            schema = json_body.get('jsonSchema', {})
            properties = schema.get('properties', {})
            
            json_value_dict = {}
            json_value_str = json_body.get('jsonValue', '')
            if json_value_str:
                try:
                    json_value_dict = json.loads(json_value_str)
                except json.JSONDecodeError:
                    pass
            
            for prop_name, sample_value in json_value_dict.items():
                prop_info = properties.get(prop_name, {})
                
                params_info.append({
                    'name': prop_name,
                    'type': prop_info.get('type'),
                    'required': prop_info.get('required'),
                    'sample': sample_value,
                    'minimum': prop_info.get('minimum'),
                    'maximum': prop_info.get('maximum'),
                    'minLength': prop_info.get('minLength'),
                    'maxLength': prop_info.get('maxLength'),
                    'location': 'body'
                })
        
        result = ""
        if params_info:
            result += "\n"
            for param in params_info:
                if param['name']:
                    result += f"- {param['name']} ({param['location']}): {param['type']}"
                    if param['required']:
                        result += " [Required]"
                    if param['sample']:
                        result += f" Sample: {param['sample']}"
                    if param['minimum'] is not None or param['maximum'] is not None:
                        result += f" Range: {param['minimum']}-{param['maximum']}"
                    if param['minLength'] is not None or param['maxLength'] is not None:
                        result += f" Length: {param['minLength']}-{param['maxLength']}"
                    result += "\n"
        else:
            result += "No parameters\n"
        
        return result
    
    def _format_response_summary(self, api_info: Dict[str, Any]) -> str:
        """Format response summary information"""
        # TODO: Currently interface response info is not passed to LLM, add later if needed
        return ""