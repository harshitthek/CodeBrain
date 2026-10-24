from typing import Dict, Any, List
import json
import logging

from apps.llm.base import BaseLLMService
from apps.knowledge.service import KnowledgeService
from apps.core.models import TestCase
from .prompts import TestCaseReviewerPrompt
# from langchain_core.messages import SystemMessage, HumanMessage
from apps.utils.logger_manager import get_logger



class TestCaseReviewerAgent:
    """Test case review Agent."""
    
    def __init__(self, llm_service: BaseLLMService, knowledge_service: KnowledgeService):
        self.llm_service = llm_service
        self.knowledge_service = knowledge_service
        self.prompt = TestCaseReviewerPrompt()
        self.logger = get_logger(self.__class__.__name__)
    
    def review(self, test_case: TestCase) -> Dict[str, Any]:
        """Review test case."""
        try:
            self.logger.info(f"Test case data for review: \n{test_case}")
            # Construct test case data dictionary
            test_case_dict = {
                "description": test_case.description,
                "test_steps": test_case.test_steps,
                "expected_results": test_case.expected_results
            }
            
            # Format messages
            messages = self.prompt.format_messages(test_case_dict)
            
            self.logger.info(f"Constructed review prompt: \n{'='*50}\n{messages}\n{'='*50}")
            
            # Call LLM service
            result = self.llm_service.invoke(messages)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during review: {str(e)}", exc_info=True)
            raise Exception(f"Review failed: {str(e)}")

    def _format_prompt(self, test_case):
        """Format prompt."""
        try:
            prompt = f"""Please review the following test case:
            Description:
            {test_case.description}
            Test Steps:
            {test_case.test_steps}
            Expected Results:
            {test_case.expected_results}
            """
            return prompt.strip()
            
        except Exception as e:
            self.logger.error(f"Error formatting prompt: {str(e)}", exc_info=True)
            raise Exception(f"Failed to format prompt: {str(e)}")

    def evaluate_suite(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Audit candidate test suite against CodeBrain multi-criteria quality rubric.
        
        Evaluates across 5 dimensions:
        1. Completeness: Explicit preconditions, numbered reproducible steps, verifiable expected results
        2. Coverage: All core tasks, physical/safety mandates, and tier user stories
        3. Boundaries: Rigorous tolerance bounds and threshold tests
        4. Exceptions: Failure modes, emergency shutdowns, fault recoveries
        5. Redundancy & Clarity: Unique test objectives, unambiguous assertions
        """
        if not test_cases:
            return {
                "score": 0.0,
                "strengths": [],
                "weaknesses": ["Empty test case suite provided for evaluation."],
                "suggestions": ["Regenerate suite with structured requirements."],
                "missing_scenarios": ["All core scenarios missing."],
                "recommendation": "Reject",
                "comments": "Suite is empty."
            }

        strengths: List[str] = []
        weaknesses: List[str] = []
        suggestions: List[str] = []
        missing_scenarios: List[str] = []

        total_cases = len(test_cases)

        # 1. Completeness Check (Max 20 pts)
        completeness_pts = 20.0
        missing_preconditions = sum(1 for tc in test_cases if not tc.get("preconditions"))
        short_steps = sum(1 for tc in test_cases if len(tc.get("test_steps", [])) < 2)
        short_results = sum(1 for tc in test_cases if not tc.get("expected_results"))
        if missing_preconditions > total_cases * 0.1:
            completeness_pts -= 4.0
            weaknesses.append(f"{missing_preconditions} test cases lack explicit preconditions.")
            suggestions.append("Ensure every test case specifies exact initial environmental preconditions.")
        if short_steps > 0:
            completeness_pts -= 3.0
            weaknesses.append(f"{short_steps} test cases have fewer than 2 procedural steps.")
            suggestions.append("Provide detailed sequential steps for all test procedures.")
        if short_results > 0:
            completeness_pts -= 5.0
            weaknesses.append(f"{short_results} test cases lack verifiable expected results.")
        if completeness_pts >= 18.0:
            strengths.append("High completeness: Detailed preconditions, sequential steps, and verifiable outcomes across all test cases.")

        # 2. Coverage Check (Max 25 pts)
        coverage_pts = 25.0
        all_text = " ".join([
            f"{tc.get('name', '')} {tc.get('description', '')} {' '.join(tc.get('test_steps', []) if isinstance(tc.get('test_steps'), list) else [str(tc.get('test_steps'))])} {' '.join(tc.get('expected_results', []) if isinstance(tc.get('expected_results'), list) else [str(tc.get('expected_results'))])}"
            for tc in test_cases
        ]).lower()

        # Tasks coverage
        has_gate = any("gate" in (tc.get("name", "") + " " + tc.get("description", "")).lower() for tc in test_cases)
        has_vision = any(any(k in (tc.get("name", "") + " " + tc.get("description", "")).lower() for k in ["vision", "balloon", "touch", "low-visibility"]) for tc in test_cases)
        has_maze = any("maze" in (tc.get("name", "") + " " + tc.get("description", "")).lower() for tc in test_cases)

        # Safety & physical
        has_weight = any("weight" in (tc.get("name", "") + " " + tc.get("description", "")).lower() or "35" in (tc.get("name", "") + " " + tc.get("description", "")).lower() for tc in test_cases)
        has_kill = any("kill switch" in (tc.get("name", "") + " " + tc.get("description", "")).lower() for tc in test_cases)
        has_fusing = any("fuse" in (tc.get("name", "") + " " + tc.get("description", "")).lower() or "fusing" in (tc.get("name", "") + " " + tc.get("description", "")).lower() for tc in test_cases)

        # User stories / categories
        has_cat1 = any(any(k in (tc.get("name", "") + " " + tc.get("description", "")).lower() for k in ["category i", "school"]) for tc in test_cases)
        has_cat2 = any(any(k in (tc.get("name", "") + " " + tc.get("description", "")).lower() for k in ["category ii", "college", "undergraduate"]) for tc in test_cases)
        has_cat3 = any(any(k in (tc.get("name", "") + " " + tc.get("description", "")).lower() for k in ["category iii", "industry", "professional"]) for tc in test_cases)

        if not has_gate:
            coverage_pts -= 4.0
            missing_scenarios.append("Task 1 Submerged gate navigation scenarios.")
        if not has_vision:
            coverage_pts -= 4.0
            missing_scenarios.append("Task 2 Vision balloon identification and soft touch scenarios.")
        if not has_maze:
            coverage_pts -= 4.0
            missing_scenarios.append("Task 3 Submerged maze traversal scenarios.")
        if not (has_weight and has_kill and has_fusing):
            coverage_pts -= 4.0
            missing_scenarios.append("Critical safety scenarios: Weight limit, Kill switch cutoff, or Electrical fusing.")
        if not (has_cat1 and has_cat2 and has_cat3):
            coverage_pts -= 3.0
            missing_scenarios.append("User story boundary coverage for Category I (School), II (College), and III (Industry).")
        if coverage_pts >= 23.0:
            strengths.append("Comprehensive domain coverage spanning Tasks 1-3, all physical/safety constraints, and participant categories.")

        # 3. Boundaries & Extremes (Max 20 pts)
        boundary_pts = 20.0
        boundary_cases = [tc for tc in test_cases if str(tc.get("case_type", "")).lower() == "boundary" or "boundary" in tc.get("name", "").lower() or "boundary" in tc.get("description", "").lower()]
        if len(boundary_cases) < 4:
            boundary_pts -= 6.0
            weaknesses.append(f"Insufficient boundary test cases (found {len(boundary_cases)}, recommended >= 8).")
            suggestions.append("Expand boundary coverage with explicit threshold limits (e.g. 35.00kg weight limit, 1.0m gate clearance, depth extremes).")
        elif len(boundary_cases) < 8:
            boundary_pts -= 2.0
            weaknesses.append("Boundary cases should cover all critical numerical tolerances.")
        else:
            strengths.append(f"Robust boundary coverage with {len(boundary_cases)} dedicated boundary test cases.")

        has_weight_bound = any("35.0" in all_text and ("pass" in all_text or "dq" in all_text or "disqualification" in all_text) for _ in [1])
        has_gate_bound = any("1.0" in all_text and ("clearance" in all_text or "width" in all_text) for _ in [1])
        if not (has_weight_bound and has_gate_bound):
            boundary_pts -= 3.0
            weaknesses.append("Explicit numerical boundary thresholds missing for vehicle mass or gate dimensions.")
            suggestions.append("Include explicit numerical boundary checks for 35.00 kg weight limit and 1.0m gate clearance.")

        # 4. Exception Scenarios (Max 20 pts)
        exception_pts = 20.0
        exception_cases = [tc for tc in test_cases if str(tc.get("case_type", "")).lower() == "exception" or "exception" in tc.get("name", "").lower() or "failure" in tc.get("name", "").lower()]
        if len(exception_cases) < 4:
            exception_pts -= 6.0
            weaknesses.append(f"Insufficient exception scenarios (found {len(exception_cases)}, recommended >= 8).")
            suggestions.append("Add fault handling test cases: thruster stall, tether snag, dark pool lighting failure, kill switch actuation, structural leak.")
        elif len(exception_cases) < 8:
            exception_pts -= 2.0
            weaknesses.append("Exception coverage could be improved with more failure scenarios.")
        else:
            strengths.append(f"Extensive exception test suite with {len(exception_cases)} failure and emergency scenarios.")

        # 5. Redundancy & Clarity (Max 15 pts)
        redundancy_pts = 15.0
        ids = [tc.get("case_id") or tc.get("id") for tc in test_cases if tc.get("case_id") or tc.get("id")]
        if len(ids) != len(set(ids)):
            redundancy_pts -= 4.0
            weaknesses.append("Duplicate test case identifiers detected.")
            suggestions.append("Ensure each test case has a globally unique case_id.")
        descriptions = [tc.get("description", "").strip().lower() for tc in test_cases if tc.get("description")]
        if len(descriptions) != len(set(descriptions)):
            redundancy_pts -= 3.0
            weaknesses.append("Duplicate test case descriptions detected.")
        if redundancy_pts >= 14.0:
            strengths.append("High clarity and zero redundancy: All test cases have unique identifiers and distinct objectives.")

        # Total rubric score
        total_score = round(max(0.0, min(100.0, completeness_pts + coverage_pts + boundary_pts + exception_pts + redundancy_pts)), 1)
        recommendation = "Pass" if total_score >= 85.0 else "Refine"
        comments = (
            f"Quality rubric score: {total_score}/100. "
            f"Evaluated {total_cases} test cases across Completeness ({completeness_pts:.1f}/20), "
            f"Coverage ({coverage_pts:.1f}/25), Boundaries ({boundary_pts:.1f}/20), "
            f"Exceptions ({exception_pts:.1f}/20), and Redundancy ({redundancy_pts:.1f}/15)."
        )

        return {
            "score": total_score,
            "rubric_breakdown": {
                "completeness": round(completeness_pts, 1),
                "coverage": round(coverage_pts, 1),
                "boundaries": round(boundary_pts, 1),
                "exceptions": round(exception_pts, 1),
                "redundancy": round(redundancy_pts, 1),
            },
            "strengths": strengths[:5],
            "weaknesses": weaknesses[:5],
            "suggestions": suggestions[:5],
            "missing_scenarios": missing_scenarios[:5],
            "recommendation": recommendation,
            "comments": comments
        }

