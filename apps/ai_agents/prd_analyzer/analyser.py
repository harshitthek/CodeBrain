from typing import Dict, Any, List, Optional, Tuple
import json

from apps.llm.base import BaseLLMService
from apps.knowledge.service import KnowledgeService
from .prompts import PrdAnalyserPrompt
# from langchain_core.messages import SystemMessage, HumanMessage
from apps.utils.logger_manager import get_logger

class PrdAnalyserAgent:
    """PRD Analyzer Agent, used to extract test points and test scenarios from PRD documents."""
    
    def __init__(self, llm_service: BaseLLMService, knowledge_service: KnowledgeService = None):
        self.llm_service = llm_service
        self.knowledge_service = knowledge_service
        self.prompt = PrdAnalyserPrompt()
        self.logger = get_logger(self.__class__.__name__)
    
    def analyse(self, markdown_content: str) -> Dict[str, Any]:
        """
        Analyze PRD document and extract test points and scenarios.
        
        Args:
            markdown_content: Markdown content of PRD document
            
        Returns:
            Dictionary containing test points and scenarios:
            {
                "test_points": [...],
                "summary": {...}
            }
        """
        try:
            self.logger.info(f"Starting PRD analysis, document length: {len(markdown_content)} characters")
            
            # Format messages using prompt template
            messages = self.prompt.format_messages(markdown_content=markdown_content)
            
            self.logger.info(f"Constructed PRD analysis prompt: \n{'='*50}\n{messages}\n{'='*50}")
            
            # Call LLM service
            response = self.llm_service.invoke(messages)
            result = response.content
            self.logger.info(f"Raw result from LLM service: \n{'='*50}\n{result}\n{'='*50}")
            
            # Parse JSON result
            try:
                if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    json_str = result.split("```")[1].split("```")[0].strip()
                else:
                    json_str = result
                    
                raw_result = json.loads(json_str)
                validated_result = self._validate_analysis_result(raw_result)
                self.logger.info(
                    "Successfully parsed and cleaned PRD analysis result, valid test points: %s, valid scenarios: %s",
                    len(validated_result["test_points"]),
                    sum(len(point["scenarios"]) for point in validated_result["test_points"])
                )

                return validated_result
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON result: {str(e)}")
                self.logger.error(f"Raw response: {result}")
                raise ValueError(f"Unable to parse generated analysis result: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Error during PRD analysis: {str(e)}", exc_info=True)
            raise Exception(f"PRD analysis failed: {str(e)}")
    
    def _validate_analysis_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Clean LLM response, filter invalid items, and compute summary."""
        if not isinstance(result, dict):
            raise ValueError("Invalid analysis result format, expected JSON object")

        raw_points = result.get("test_points")
        if not isinstance(raw_points, list):
            self.logger.warning("test_points in analysis result is not a list; using empty list")
            raw_points = []

        required_point_fields = {"id", "title", "description", "priority", "scenarios"}
        required_scenario_fields = {"id", "title", "description", "test_type"}

        valid_points: List[Dict[str, Any]] = []
        dropped_points = 0
        dropped_scenarios = 0

        for point in raw_points:
            if not isinstance(point, dict):
                dropped_points += 1
                continue

            if not required_point_fields.issubset(point.keys()):
                dropped_points += 1
                continue

            scenarios = point.get("scenarios")
            if not isinstance(scenarios, list):
                dropped_points += 1
                continue

            valid_scenarios: List[Dict[str, Any]] = []
            for scenario in scenarios:
                if not isinstance(scenario, dict):
                    dropped_scenarios += 1
                    continue
                if not required_scenario_fields.issubset(scenario.keys()):
                    dropped_scenarios += 1
                    continue
                valid_scenarios.append(scenario)

            if not valid_scenarios:
                dropped_points += 1
                continue

            cleaned_point = dict(point)
            cleaned_point["scenarios"] = valid_scenarios
            valid_points.append(cleaned_point)

        summary = self._build_summary(valid_points)

        if dropped_points or dropped_scenarios:
            self.logger.warning(
                "PRD analysis result cleaned: dropped %s invalid test points, %s invalid scenarios",
                dropped_points,
                dropped_scenarios,
            )

        return {
            "test_points": valid_points,
            "summary": summary,
        }

    def _build_summary(self, test_points: List[Dict[str, Any]]) -> Dict[str, int]:
        """Compute summary information based on valid test points."""
        total_test_points = len(test_points)
        total_test_scenarios = sum(len(point["scenarios"]) for point in test_points)

        priority_stats = {"high": 0, "medium": 0, "low": 0}
        for point in test_points:
            normalized_priority = self._normalize_priority(point.get("priority"))
            if normalized_priority in priority_stats:
                priority_stats[normalized_priority] += 1

        return {
            "total_test_points": total_test_points,
            "total_test_scenarios": total_test_scenarios,
            "high_priority_points": priority_stats["high"],
            "medium_priority_points": priority_stats["medium"],
            "low_priority_points": priority_stats["low"],
        }

    @staticmethod
    def _normalize_priority(raw_priority: Optional[str]) -> str:
        """Normalize priority string to uniform format."""
        if raw_priority is None:
            return "low"

        value = str(raw_priority).strip().lower()
        if value in {"high", "p0"}:
            return "high"
        if value in {"medium", "p1"}:
            return "medium"
        if value in {"low", "p2", "p3"}:
            return "low"
        return "low"

