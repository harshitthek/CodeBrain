"""A stateless adapter from CodeBrain's QA pipeline to the Fetch chat workflow."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from django.conf import settings

from .policy import (
    ReleaseGuardianPolicy,
    ReleaseGuardianPolicyError,
    VerificationTarget,
)
from .schemas import ExecutionReport, QAPlan, TestCaseSummary


class ReleaseGuardianConfigurationError(RuntimeError):
    """Raised when a required runtime credential has not been configured."""


class NullKnowledgeService:
    """Keeps the agent self-contained instead of initialising optional RAG services."""

    def search_relevant_knowledge(self, _query: str, **_kwargs: Any) -> str:
        return ""


class ReleaseGuardianService:
    """Creates a QA plan and, after approval, runs a configured repository test suite."""

    def __init__(
        self,
        policy: ReleaseGuardianPolicy | None = None,
        pipeline_runner: Callable[[str, int], dict[str, Any]] | None = None,
    ) -> None:
        self.policy = policy or self._configured_policy()
        self._pipeline_runner = pipeline_runner

    @staticmethod
    def _configured_policy() -> ReleaseGuardianPolicy:
        configured = getattr(
            settings, "RELEASE_GUARDIAN_ALLOWED_TARGETS", ("configured_repository",)
        )
        return ReleaseGuardianPolicy(
            enabled_target_ids=tuple(configured),
            repository_path=str(getattr(settings, "RELEASE_GUARDIAN_REPO_PATH", "")),
            repository_test_command=str(
                getattr(
                    settings,
                    "RELEASE_GUARDIAN_REPO_TEST_COMMAND",
                    "python -m pytest -q",
                )
            ),
            repository_test_timeout=int(
                getattr(settings, "RELEASE_GUARDIAN_REPO_TEST_TIMEOUT", 120)
            ),
        )

    def available_targets(self) -> list[VerificationTarget]:
        ready_targets: list[VerificationTarget] = []
        for target in self.policy.enabled_targets():
            try:
                self._repository_verification(target)
            except ReleaseGuardianPolicyError:
                continue
            ready_targets.append(target)
        return ready_targets

    def build_qa_plan(
        self, requirements: str, case_count: int = 3, target_id: str | None = None
    ) -> QAPlan:
        cleaned_requirements = self.policy.validate_requirements(requirements)
        case_count = self.policy.validate_case_count(case_count)
        target = self.policy.get_target(target_id)
        if target is not None:
            self._repository_verification(target)
        result = self._run_pipeline(cleaned_requirements, case_count)
        cases = self._normalise_cases(result.get("final_cases", []), case_count)
        if not cases:
            raise RuntimeError(
                "CodeBrain did not return a usable test suite. Please try again."
            )

        history = result.get("history", [])
        latest_critique = history[-1].get("critique", {}) if history else {}
        notes = (
            latest_critique.get("suggestions", [])
            if isinstance(latest_critique, dict)
            else []
        )
        return QAPlan(
            requirements=cleaned_requirements,
            test_cases=cases,
            quality_signal=self._bounded_score(result.get("final_score", 0)),
            converged=bool(result.get("converged", False)),
            iterations_run=min(max(int(result.get("iterations_run", 1)), 1), 2),
            target_id=target.target_id if target else None,
            target_label=target.label if target else None,
            reviewer_notes=[str(note)[:240] for note in notes[:3]],
        )

    def execute_live_check(self, plan: QAPlan) -> ExecutionReport:
        target = self.policy.get_target(plan.target_id)
        if target is None:
            raise ReleaseGuardianPolicyError(
                "There is no approved verification target in this plan."
            )
        return self._run_repository_tests(target)

    def _run_repository_tests(self, target: VerificationTarget) -> ExecutionReport:
        verification, repository_root = self._repository_verification(target)
        commit = (
            self._git_value(repository_root, "rev-parse", "--short", "HEAD")
            or "no-commit"
        )
        dirty_files = self._git_status_count(repository_root)
        command = (sys.executable, *verification.command[1:])
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=repository_root,
                env=self._safe_test_environment(),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=verification.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            duration_ms = (time.monotonic() - started) * 1000
            return ExecutionReport(
                target_id=target.target_id,
                target_label=target.label,
                total=1,
                passed=0,
                failed=1,
                pass_rate=0,
                total_duration_ms=round(duration_ms, 1),
                results=[
                    {
                        "name": "Configured pytest suite",
                        "passed": False,
                        "timed_out": True,
                        "timeout_seconds": verification.timeout_seconds,
                        "commit": commit,
                        "dirty_files": dirty_files,
                    }
                ],
            )

        duration_ms = (time.monotonic() - started) * 1000
        passed, failed = self._pytest_counts(
            completed.stdout or "", completed.returncode
        )
        total = passed + failed
        return ExecutionReport(
            target_id=target.target_id,
            target_label=target.label,
            total=total,
            passed=passed,
            failed=failed,
            pass_rate=round((passed / total) * 100, 1) if total else 0,
            total_duration_ms=round(duration_ms, 1),
            results=[
                {
                    "name": "Configured pytest suite",
                    "passed": completed.returncode == 0,
                    "exit_code": completed.returncode,
                    "commit": commit,
                    "dirty_files": dirty_files,
                }
            ],
        )

    def _repository_verification(
        self, target: VerificationTarget
    ) -> tuple[Any, Path]:
        """Validate the configured target before it is shown or approved in chat."""
        verification = self.policy.repository_verification(target)
        return verification, self._git_repository_root(verification.repository_path)

    @staticmethod
    def _safe_test_environment() -> dict[str, str]:
        """Pass only OS execution basics; do not pass API keys or Django secrets to tests."""
        allowed = ("PATH", "SYSTEMROOT", "WINDIR", "TMP", "TEMP", "TMPDIR")
        environment = {name: value for name in allowed if (value := os.getenv(name))}
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return environment

    @staticmethod
    def _git_repository_root(path: Path) -> Path:
        if not path.is_dir():
            raise ReleaseGuardianPolicyError(
                "The configured release repository path is unavailable."
            )
        try:
            result = subprocess.run(
                ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ReleaseGuardianPolicyError(
                "Could not validate the configured release repository."
            ) from error
        if result.returncode != 0 or not result.stdout.strip():
            raise ReleaseGuardianPolicyError(
                "RELEASE_GUARDIAN_REPO_PATH must point inside a Git repository."
            )
        return Path(result.stdout.strip()).resolve()

    @staticmethod
    def _git_value(repository_root: Path, *args: str) -> str:
        try:
            result = subprocess.run(
                ["git", "-C", str(repository_root), *args],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return ""
        return result.stdout.strip() if result.returncode == 0 else ""

    @classmethod
    def _git_status_count(cls, repository_root: Path) -> int:
        value = cls._git_value(repository_root, "status", "--porcelain")
        return len(value.splitlines()) if value else 0

    @staticmethod
    def _pytest_counts(output: str, return_code: int) -> tuple[int, int]:
        passed_match = re.search(r"(?:^|[\n,]\s*)(\d+)\s+passed\b", output)
        failed_match = re.search(r"(?:^|[\n,]\s*)(\d+)\s+(?:failed|errors?)\b", output)
        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        if return_code == 0:
            return max(passed, 1), failed
        return passed, max(failed, 1)

    def _run_pipeline(self, requirements: str, case_count: int) -> dict[str, Any]:
        if self._pipeline_runner is not None:
            return self._pipeline_runner(requirements, case_count)

        provider = str(getattr(settings, "RELEASE_GUARDIAN_LLM_PROVIDER", "asi1"))
        if provider.lower() == "asi1" and not os.getenv("ASI1_API_KEY"):
            raise ReleaseGuardianConfigurationError(
                "ASI1_API_KEY is required for Release Guardian's ASI:One reasoning step."
            )

        from apps.ai_agents.common.orchestrator import ActorCriticReflectionEngine
        from apps.ai_agents.test_case_generator.generator import TestCaseGeneratorAgent
        from apps.ai_agents.test_case_reviewer.reviewer import TestCaseReviewerAgent
        from apps.llm.base import LLMServiceFactory

        llm = LLMServiceFactory.create(provider)
        knowledge = NullKnowledgeService()
        generator = TestCaseGeneratorAgent(
            llm_service=llm,
            knowledge_service=knowledge,
            case_design_methods=[
                "Equivalence Partitioning",
                "Boundary Value Analysis",
                "Scenario Testing",
            ],
            case_categories=["Functional", "Boundary", "Exception"],
            case_count=case_count,
        )
        reviewer = TestCaseReviewerAgent(llm_service=llm, knowledge_service=knowledge)
        engine = ActorCriticReflectionEngine(
            generator_agent=generator,
            reviewer_agent=reviewer,
            min_score=float(getattr(settings, "RELEASE_GUARDIAN_MIN_SCORE", 85.0)),
            max_iterations=2,
        )
        return engine.run(requirements)

    @staticmethod
    def _bounded_score(value: Any) -> float:
        try:
            return round(max(0.0, min(float(value), 100.0)), 1)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _normalise_cases(raw_cases: Any, case_count: int) -> list[TestCaseSummary]:
        normalised: list[TestCaseSummary] = []
        if not isinstance(raw_cases, list):
            return normalised
        for index, case in enumerate(raw_cases[:case_count], start=1):
            if not isinstance(case, dict):
                continue
            title = str(
                case.get("title") or case.get("description") or f"QA case {index}"
            )
            steps = case.get("test_steps") or case.get("steps") or []
            expected = case.get("expected_results") or case.get("expected") or []
            if isinstance(steps, str):
                steps = [line.strip() for line in steps.splitlines() if line.strip()]
            if isinstance(expected, str):
                expected = [
                    line.strip() for line in expected.splitlines() if line.strip()
                ]
            try:
                normalised.append(
                    TestCaseSummary(
                        title=title[:240],
                        steps=[str(step)[:500] for step in steps if str(step).strip()],
                        expected_results=[
                            str(item)[:500] for item in expected if str(item).strip()
                        ],
                        priority=str(case.get("priority", "P1")).upper()[:10],
                    )
                )
            except ValueError:
                continue
        return normalised
