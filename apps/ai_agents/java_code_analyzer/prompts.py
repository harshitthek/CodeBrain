"""
Prompt manager for Java Code Analyzer AI Agent.
"""
from pathlib import Path

from apps.ai_agents.common.base_prompts import BasePromptManager


class JavaCodeAnalyzerPromptManager(BasePromptManager):
    """Prompt manager for Java Code Analyzer AI Agent"""
    
    def __init__(self):
        super().__init__()

    def get_system_prompt(self) -> str:
        """Get prompt template for rendering Markdown report (used in node_render)."""
        import yaml

        current_dir = Path(__file__).parent
        config_path = current_dir / "configs" / "prompt_config.yaml"

        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)

        return config.get("java_code_analyzer_system_prompt", "")
    
    def get_user_prompt(self, repo_path: str, base_commit: str, new_commit: str) -> str:
        """Get user prompt"""
        return f"""Please analyze the change impact between the following two commits and provide testing recommendations:
            Repository Path: {repo_path}
            Base Commit: {base_commit}
            Target Commit: {new_commit}
            Autonomously invoke suitable tools for in-depth analysis and generate corresponding test cases.
            """