from django.conf import settings


def get_agent_llm_configs(agent_name: str):
    """
    Get LLM configuration for AI Agent
    """
    llm_config = getattr(settings, "LLM_PROVIDERS", {})
    # global_default_provider is the global default LLM provider; used if agent has no provider configured
    global_default_provider = llm_config.get("default_provider", "deepseek")
    global_providers = {k: v for k, v in llm_config.items() if k != "default_provider"}

    agent_defaults = getattr(settings, "AGENT_LLM_DEFAULTS", {})
    # agent_provider_config is the config in AGENT_LLM_DEFAULTS from settings.py, i.e., default provider for each agent
    agent_provider = agent_defaults.get(agent_name).get("provider", global_default_provider)

    return agent_provider, global_providers

