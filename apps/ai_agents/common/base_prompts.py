"""Prompt management base class."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.chat import SystemMessagePromptTemplate, HumanMessagePromptTemplate


class BasePromptManager:
    """Base prompt manager - provides common methods without handling config loading."""
    
    def _create_chat_prompt_template(self, system_template: str, human_template: str) -> ChatPromptTemplate:
        """Create chat prompt template."""
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        
        return ChatPromptTemplate.from_messages([
            system_message_prompt,
            human_message_prompt
        ])


class BasePrompt:
    """Base prompt class - interface definition."""
    
    def format_messages(self, **kwargs):
        """Format messages - subclasses must implement."""
        raise NotImplementedError("Subclasses must implement format_messages method")
