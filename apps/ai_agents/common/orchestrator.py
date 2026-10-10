import time
import json
import re
import asyncio
from typing import List, Dict, Any, Optional
from apps.utils.logger_manager import get_logger, set_task_context, clear_task_context
from apps.utils.progress_registry import set_progress

logger = get_logger(__name__)


class ActorCriticReflectionEngine:
    """Actor-Critic reflection engine for iterative self-healing test case generation.
    
    Enforces a strict upper bound of max_iterations=2 (Invariant 1).
    Monotonically tracks candidate suites to prevent regressions.
    """

    def __init__(
        self,
        generator_agent: Any,
        reviewer_agent: Any,
        min_score: float = 85.0,
        max_iterations: int = 2
    ):
        self.generator = generator_agent
        self.reviewer = reviewer_agent
        self.min_score = float(min_score)
        # Invariant 1: Hard upper bound on iterations
        self.max_iterations = min(max(int(max_iterations), 1), 2)

    def _parse_review_response(self, review_raw: Any) -> Dict[str, Any]:
        """Extract structured score, suggestions, and weaknesses from reviewer output."""
        content = review_raw.content if hasattr(review_raw, 'content') else str(review_raw)
        
        # Try JSON extraction first
        parsed = None
        if "{" in content and "}" in content:
            try:
                start = content.index("{")
                end = content.rindex("}") + 1
                json_str = content[start:end]
                parsed = json.loads(json_str)
            except Exception:
                pass

        if isinstance(parsed, dict):
            raw_score = parsed.get('score', 0)
            try:
                score_val = float(raw_score)
            except (ValueError, TypeError):
                score_val = 70.0
            
            # Normalize 1-10 scores to 10-100 scale
            if score_val <= 10.0:
                score_val = score_val * 10.0

            return {
                "score": round(score_val, 1),
                "strengths": parsed.get('strengths', []),
                "weaknesses": parsed.get('weaknesses', []),
                "suggestions": parsed.get('suggestions', []),
                "missing_scenarios": parsed.get('missing_scenarios', []),
                "recommendation": parsed.get('recommendation', 'Pending'),
                "comments": parsed.get('comments', content[:200])
            }

        # Fallback heuristic parser
        score_match = re.search(r'(?:score|Score|points|Points|rating|Rating)[\s:="]+(\d+(?:\.\d+)?)', content)
        if score_match:
            try:
                score_val = float(score_match.group(1))
                if score_val <= 10.0:
                    score_val = score_val * 10.0
            except ValueError:
                score_val = 75.0
        else:
            score_val = 75.0

        return {
            "score": round(score_val, 1),
            "strengths": ["Clear scenario outline"],
            "weaknesses": ["Boundary conditions could be more comprehensive"],
            "suggestions": ["Add explicit edge cases and boundary assertions"],
            "missing_scenarios": ["Invalid inputs and timeout paths"],
            "recommendation": "Pass" if score_val >= self.min_score else "Refine",
            "comments": content[:200]
        }

    def _evaluate_candidate_suite(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run critic evaluation across the candidate test suite."""
        if not test_cases:
            return {
                "score": 0.0,
                "strengths": [],
                "weaknesses": ["Empty test case suite generated"],
                "suggestions": ["Regenerate with valid requirements"],
                "missing_scenarios": ["All core scenarios"],
                "recommendation": "Reject",
                "comments": "No test cases generated"
            }

        # If reviewer supports evaluate_suite directly and returns a valid result dict:
        if hasattr(self.reviewer, 'evaluate_suite'):
            try:
                res = self.reviewer.evaluate_suite(test_cases)
                if isinstance(res, dict) and isinstance(res.get('score'), (int, float)):
                    return res
            except Exception:
                pass

        # Otherwise evaluate sample or combined representation
        class MockCaseObj:
            def __init__(self, desc, steps, results):
                self.description = desc
                self.test_steps = steps if isinstance(steps, str) else "\n".join(str(s) for s in steps)
                self.expected_results = results if isinstance(results, str) else "\n".join(str(r) for r in results)

        scores = []
        all_weaknesses = []
        all_suggestions = []
        all_missing = []

        # Evaluate representative sample of cases to conserve latency
        sample_cases = test_cases[:3]
        for c in sample_cases:
            desc = c.get('description') or c.get('title') or c.get('name', 'Test Case')
            steps = c.get('test_steps', [])
            expected = c.get('expected_results', [])
            case_obj = MockCaseObj(desc, steps, expected)
            try:
                rev = self.reviewer.review(case_obj)
                p = self._parse_review_response(rev)
                scores.append(p['score'])
                all_weaknesses.extend(p['weaknesses'])
                all_suggestions.extend(p['suggestions'])
                all_missing.extend(p['missing_scenarios'])
            except Exception as e:
                logger.warning(f"Error reviewing candidate case: {e}")
                scores.append(75.0)

        avg_score = round(sum(scores) / len(scores), 1) if scores else 70.0
        return {
            "score": avg_score,
            "strengths": ["Structured test format adherence"],
            "weaknesses": list(dict.fromkeys(all_weaknesses))[:5],
            "suggestions": list(dict.fromkeys(all_suggestions))[:5],
            "missing_scenarios": list(dict.fromkeys(all_missing))[:5],
            "recommendation": "Pass" if avg_score >= self.min_score else "Refine",
            "comments": f"Evaluated {len(sample_cases)} sample cases with average quality score {avg_score}."
        }

    def _build_refinement_input(
        self,
        original_req: str,
        current_cases: List[Dict[str, Any]],
        critique: Dict[str, Any]
    ) -> str:
        """Construct targeted critique prompt for actor refinement pass."""
        lines = [
            original_req,
            "\n### PREVIOUS AUDIT FEEDBACK (CRITIC AUDIT)",
            f"Quality Score: {critique.get('score', 0)}/100 (Threshold required: {self.min_score})",
        ]
        if critique.get('weaknesses'):
            lines.append("Identified Weaknesses:\n" + "\n".join(f"- {w}" for w in critique['weaknesses']))
        if critique.get('suggestions'):
            lines.append("Required Improvements:\n" + "\n".join(f"- {s}" for s in critique['suggestions']))
        if critique.get('missing_scenarios'):
            lines.append("Missing Edge Scenarios to add:\n" + "\n".join(f"- {m}" for m in critique['missing_scenarios']))

        lines.append(
            "\nPlease refine and harden the test case suite to address all identified weaknesses, "
            "incorporating boundary validations, explicit expected results, and missing exception paths."
        )
        return "\n".join(lines)

    def run(self, requirements: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Synchronously execute Actor-Critic reflection pipeline."""
        start_time = time.perf_counter()
        if task_id:
            set_task_context(task_id)

        history: List[Dict[str, Any]] = []
        best_suite: List[Dict[str, Any]] = []
        best_score: float = -1.0
        current_input = requirements
        iteration = 0
        converged = False

        try:
            while iteration < self.max_iterations:
                iteration += 1
                if task_id:
                    set_progress(task_id, {
                        'step': 2 + (iteration - 1) * 2,
                        'message': f'Actor generating candidate test cases (Iteration {iteration}/{self.max_iterations})',
                        'percentage': 20 + (iteration - 1) * 35
                    })

                # 1. Actor generation
                try:
                    if hasattr(self.generator, 'generate'):
                        current_cases = self.generator.generate(current_input)
                    else:
                        current_cases = []
                except Exception as gen_err:
                    if best_suite:
                        logger.warning(f"Actor generation failed on refinement iteration {iteration}: {gen_err}. Preserving best suite.")
                        history.append({
                            "iteration": iteration,
                            "error": str(gen_err),
                            "critique": {"weaknesses": [f"Generation failed: {gen_err}"]}
                        })
                        break
                    raise gen_err

                if task_id:
                    set_progress(task_id, {
                        'step': 3 + (iteration - 1) * 2,
                        'message': f'Critic evaluating suite quality (Iteration {iteration}/{self.max_iterations})',
                        'percentage': 40 + (iteration - 1) * 35
                    })

                # 2. Critic evaluation
                critique = self._evaluate_candidate_suite(current_cases)
                try:
                    score = float(critique.get('score', 0.0))
                except (ValueError, TypeError):
                    score = 0.0

                history.append({
                    "iteration": iteration,
                    "score": score,
                    "case_count": len(current_cases),
                    "critique": critique
                })

                # Monotonic safeguard: retain best iteration
                if score > best_score:
                    best_score = score
                    best_suite = current_cases

                # Check convergence threshold
                if score >= self.min_score:
                    converged = True
                    break

                # Prepare refinement for next iteration
                if iteration < self.max_iterations:
                    current_input = self._build_refinement_input(requirements, current_cases, critique)

            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            if task_id:
                set_progress(task_id, {
                    'step': 5,
                    'message': f'Reflection pipeline complete: Score {best_score}/100 across {iteration} iterations',
                    'percentage': 100
                })

            return {
                "success": True,
                "converged": converged,
                "final_cases": best_suite,
                "final_score": best_score,
                "iterations_run": iteration,
                "max_iterations": self.max_iterations,
                "duration_ms": elapsed_ms,
                "history": history
            }

        finally:
            if task_id:
                clear_task_context()

    async def async_run(self, requirements: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Asynchronously execute Actor-Critic reflection pipeline."""
        start_time = time.perf_counter()
        if task_id:
            set_task_context(task_id)

        history: List[Dict[str, Any]] = []
        best_suite: List[Dict[str, Any]] = []
        best_score: float = -1.0
        current_input = requirements
        iteration = 0
        converged = False

        try:
            while iteration < self.max_iterations:
                iteration += 1
                if task_id:
                    set_progress(task_id, {
                        'step': 2 + (iteration - 1) * 2,
                        'message': f'Actor generating candidate test cases (Iteration {iteration}/{self.max_iterations})',
                        'percentage': 20 + (iteration - 1) * 35
                    })

                # 1. Async Actor generation
                try:
                    if hasattr(self.generator, 'async_generate'):
                        current_cases = await self.generator.async_generate(current_input)
                    elif hasattr(self.generator, 'generate'):
                        current_cases = self.generator.generate(current_input)
                    else:
                        current_cases = []
                except Exception as gen_err:
                    if best_suite:
                        logger.warning(f"Async actor generation failed on refinement iteration {iteration}: {gen_err}. Preserving best suite.")
                        history.append({
                            "iteration": iteration,
                            "error": str(gen_err),
                            "critique": {"weaknesses": [f"Generation failed: {gen_err}"]}
                        })
                        break
                    raise gen_err

                if task_id:
                    set_progress(task_id, {
                        'step': 3 + (iteration - 1) * 2,
                        'message': f'Critic evaluating suite quality (Iteration {iteration}/{self.max_iterations})',
                        'percentage': 40 + (iteration - 1) * 35
                    })

                # 2. Critic evaluation (sync or async)
                critique = self._evaluate_candidate_suite(current_cases)
                try:
                    score = float(critique.get('score', 0.0))
                except (ValueError, TypeError):
                    score = 0.0

                history.append({
                    "iteration": iteration,
                    "score": score,
                    "case_count": len(current_cases),
                    "critique": critique
                })

                if score > best_score:
                    best_score = score
                    best_suite = current_cases

                if score >= self.min_score:
                    converged = True
                    break

                if iteration < self.max_iterations:
                    current_input = self._build_refinement_input(requirements, current_cases, critique)

            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            if task_id:
                set_progress(task_id, {
                    'step': 5,
                    'message': f'Reflection pipeline complete: Score {best_score}/100 across {iteration} iterations',
                    'percentage': 100
                })

            return {
                "success": True,
                "converged": converged,
                "final_cases": best_suite,
                "final_score": best_score,
                "iterations_run": iteration,
                "max_iterations": self.max_iterations,
                "duration_ms": elapsed_ms,
                "history": history
            }

        finally:
            if task_id:
                clear_task_context()
