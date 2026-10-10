from langchain_openai import ChatOpenAI
from typing import Any, Dict, Optional
import os
import logging


logger = logging.getLogger(__name__)


class DeepSeekChatModel(ChatOpenAI):
    """DeepSeek Chat Model"""

    def __init__(
        self,
        api_key: Optional[str] = None,  # Factory passes API key
        base_url: Optional[str] = None,
        model: Optional[str] = None,  # Factory passes model name
        enable_thinking: Optional[bool] = None,
        extra_body: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        # Handle enable_thinking parameter (DeepSeek-specific parameter placed in extra_body)
        if enable_thinking is not None:
            if extra_body is None:
                extra_body = {}
            extra_body["enable_thinking"] = enable_thinking
        # Pass all parameters:
        # - api_key: passed by factory
        # - model: passed by factory
        # - extra_body: for custom parameters (e.g. enable_thinking)
        # - **kwargs: for standard OpenAI parameters (temperature, max_tokens, etc.)
        logger.info(f"Parameters for initializing DeepSeekChatModel: model={model}, base_url={base_url}, api_key={api_key}, extra_body={extra_body}, kwargs={kwargs}")
        super().__init__(
            model=model,
            base_url=base_url,
            api_key=api_key,
            extra_body=extra_body,
            **kwargs
        )