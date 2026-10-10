# Empty file to make llm a Python package 

# Export LLMServiceFactory from base module
from langchain_core.language_models.chat_models import BaseChatModel
from .base import LLMServiceFactory

# Export all classes and functions accessible at package level
__all__ = ['LLMServiceFactory', 'BaseChatModel'] 