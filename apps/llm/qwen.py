from langchain_openai import ChatOpenAI
from typing import Any, Dict, Optional
import os
import logging


logger = logging.getLogger(__name__)

class QwenChatModel(ChatOpenAI):
    """Qwen Chat Model"""

    def __init__(
        self,
        api_key: Optional[str] = None,  # Factory passes API key
        base_url: Optional[str] = None,
        model: str = None,  # Factory passes model name
        extra_body: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        # All parameters are passed by factory, no default value logic
        logger.info(f"Parameters for initializing QwenChatModel: model={model}, base_url={base_url}, api_key={api_key}, extra_body={extra_body}, kwargs={kwargs}")

        # Pass all parameters:
        # - api_key: passed by factory
        # - model: passed by factory
        # - extra_body: for custom parameters (e.g. Alibaba Cloud-specific parameters)
        # - **kwargs: for standard OpenAI parameters (temperature, max_tokens, etc.)
        super().__init__(
            model=model,
            base_url=base_url,
            api_key=api_key,
            extra_body=extra_body,
            **kwargs
        )