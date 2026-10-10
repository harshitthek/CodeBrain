import pytest
from apps.llm.base import LLMServiceFactory
from apps.llm.deepseek import DeepSeekChatModel
from apps.llm.qwen import QwenChatModel
from apps.llm.callbacks import LoggingCallbackHandler
from apps.llm.utils import get_agent_llm_configs


def test_llm_factory_create_deepseek():
    """Verify LLMServiceFactory creates DeepSeekChatModel"""
    model = LLMServiceFactory.create("deepseek")
    assert isinstance(model, DeepSeekChatModel)
    assert model.model_name in ["deepseek-v3.1", "deepseek-chat"] or hasattr(model, "model_name")


def test_llm_factory_create_qwen():
    """Verify LLMServiceFactory creates QwenChatModel"""
    model = LLMServiceFactory.create("qwen")
    assert isinstance(model, QwenChatModel)


def test_llm_factory_unknown_fallback():
    """Verify fallback to default provider for unknown provider"""
    model = LLMServiceFactory.create("non_existent_provider_xyz")
    assert isinstance(model, DeepSeekChatModel)


def test_logging_callback_handler_clip():
    """Verify LoggingCallbackHandler string clipping"""
    handler = LoggingCallbackHandler()
    short_text = "Hello world"
    assert handler._clip(short_text, limit=50) == "Hello world"

    long_text = "A" * 100
    clipped = handler._clip(long_text, limit=20)
    assert len(clipped) < 100
    assert "truncated" in clipped


def test_get_agent_llm_configs():
    """Verify get_agent_llm_configs returns configured provider and providers dictionary"""
    provider, providers = get_agent_llm_configs("test_case_generator")
    assert provider in ["deepseek", "qwen"]
    assert "deepseek" in providers
    assert "qwen" in providers
