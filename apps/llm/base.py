from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import os
import time
from dotenv import load_dotenv
from apps.utils.logger_manager import get_logger
from django.conf import settings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from .callbacks import LoggingCallbackHandler
# from .deepseek import DeepSeekChatModel
# from .qwen import QwenChatModel


# Load environment variables from .env file
load_dotenv()

class BaseLLMService(BaseChatModel):
    """Base LLM service class"""
    
    def __init__(self):
        # Use unified logger manager to get logger
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text response"""
        pass
    
    @abstractmethod
    def generate_with_history(self, 
                             messages: List[Dict[str, str]], 
                             **kwargs) -> str:
        """Generate response based on conversation history"""
        pass
    
    def _log_request(self, method_name: str, prompt_or_messages, **kwargs):
        """Record request log"""
        if isinstance(prompt_or_messages, str):
            # For a single prompt, only log the first 100 characters
            prompt_preview = prompt_or_messages[:100] + "..." if len(prompt_or_messages) > 100 else prompt_or_messages
            self.logger.info(f"Start calling {method_name}: prompt='{prompt_preview}'")
        else:
            # For message list, log message count and the last message
            last_msg = prompt_or_messages[-1] if prompt_or_messages else {}
            last_content = last_msg.get('content', '')
            content_preview = last_content[:100] + "..." if len(last_content) > 100 else last_content
            self.logger.info(f"Start calling {method_name}: message count={len(prompt_or_messages)}, last message='{content_preview}'")
        
        # Log key parameters
        important_params = {k: v for k, v in kwargs.items() if k in ['model', 'temperature', 'max_tokens']}
        if important_params:
            self.logger.info(f"Call parameters: {important_params}")
    
    def _log_response(self, method_name: str, response: str, elapsed_time: float):
        """Record response log"""
        response_preview = response[:100] + "..." if len(response) > 100 else response
        self.logger.info(f"Call succeeded {method_name}: elapsed={elapsed_time:.2f}s, response='{response_preview}'")
    
    def _log_error(self, method_name: str, error: Exception, elapsed_time: float):
        """Record error log"""
        self.logger.error(f"Call failed {method_name}: elapsed={elapsed_time:.2f}s, error={str(error)}", exc_info=True)

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Implement method required by BaseChatModel"""
        raise NotImplementedError()
    
    @property
    def _llm_type(self) -> str:
        """Return LLM type"""
        return "base_llm_service"

class LLMServiceFactory:
    """LLM Service Factory"""
    
    @staticmethod
    def create(provider: str, **config) -> Any:
        """Create LLM service instance supporting DeepSeek, Qwen, OpenAI, Ollama, Groq, and custom endpoints"""
        logger = get_logger("LLMServiceFactory")
        logger.info(f"Creating LLM service: provider={provider}")
        
        # Get LLM configuration
        llm_config = getattr(settings, 'LLM_PROVIDERS', {})
        default_provider = llm_config.get('default_provider', 'deepseek')
        providers = {k: v for k, v in llm_config.items() if k != 'default_provider'}
        
        # Check if provider exists
        if provider not in providers:
            if 'base_url' in config or 'model' in config:
                logger.info(f"Using custom runtime config for provider: {provider}")
                provider_config = {}
            else:
                logger.warning(f"Unsupported LLM provider: {provider}, falling back to default: {default_provider}")
                provider = default_provider
                provider_config = providers.get(provider, {}).copy()
        else:
            provider_config = providers.get(provider, {}).copy()
        
        # Get API key
        api_key = (
            config.get('api_key')
            or provider_config.get('api_key')
            or os.getenv(f"{provider.upper()}_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or ("ollama" if provider.lower() == "ollama" else "placeholder_key")
        )
        provider_config['api_key'] = api_key
        
        # Create callback handler
        callbacks = [LoggingCallbackHandler()]
        
        # Merge configurations: settings.py config as base, runtime config overrides
        final_config = {
            **provider_config,  # Default configuration from settings.py
            **config,           # Runtime configuration (higher priority)
            'callbacks': callbacks,
            'verbose': True
        }

        # Normalize api_base to base_url if present
        if 'api_base' in final_config and 'base_url' not in final_config:
            final_config['base_url'] = final_config.pop('api_base')
        
        # Remove metadata not accepted by ChatOpenAI
        final_config.pop('name', None)
        
        # Log final configuration (for debugging)
        logger.info(f"Final config for {provider}: {final_config}")
        
        # Create corresponding service instance according to provider
        if provider.lower() == "deepseek":
            from .deepseek import DeepSeekChatModel
            return DeepSeekChatModel(**final_config)
        elif provider.lower() == "qwen":
            from .qwen import QwenChatModel
            return QwenChatModel(**final_config)
        else:
            from langchain_openai import ChatOpenAI
            logger.info(f"Instantiating universal ChatOpenAI for provider: {provider}")
            return ChatOpenAI(**final_config)
