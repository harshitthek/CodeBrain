"""Explicit execution policy for CodeBrain Release Guardian.

The chat user can choose *whether* a configured test run happens, but can never
provide a repository path or command. Those are deployment-time operator
settings so the agent cannot be turned into a remote command runner.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path


class ReleaseGuardianPolicyError(ValueError):
    """Raised when a request is outside the agent's declared safety policy."""


@dataclass(frozen=True)
class VerificationTarget:
    """A named, operator-configured action that may be selected in a chat card."""

    target_id: str
    label: str
    description: str


@dataclass(frozen=True)
class RepositoryVerification:
    """Trusted deployment-time details for one repository test run."""

    repository_path: Path
    command: tuple[str, ...]
    timeout_seconds: int


CONFIGURED_REPOSITORY = VerificationTarget(
    target_id="configured_repository",
    label="Configured release repository",
    description=(
        "Runs the deployment-configured pytest command in one trusted local Git repository. "
        "No path or command is accepted from chat."
    ),
)


class ReleaseGuardianPolicy:
    """Constrains the optional action to a safe, local pytest verification."""

    max_requirement_chars = 12_000
    max_case_count = 5
    _allowed_pytest_options = frozenset(
        {"-q", "--quiet", "--disable-warnings", "--maxfail=1"}
    )

    def __init__(
        self,
        enabled_target_ids: tuple[str, ...] | None = None,
        repository_path: str = "",
        repository_test_command: str = "python -m pytest -q",
        repository_test_timeout: int = 120,
    ) -> None:
        self._repository_path = repository_path.strip()
        self._repository_test_command = repository_test_command.strip()
        self._repository_test_timeout = repository_test_timeout
        self._targets = (
            {CONFIGURED_REPOSITORY.target_id: CONFIGURED_REPOSITORY}
            if self._repository_path
            else {}
        )
        self._enabled_target_ids = (
            tuple(self._targets) if enabled_target_ids is None else enabled_target_ids
        )

    def enabled_targets(self) -> list[VerificationTarget]:
        return [
            self._targets[target_id]
            for target_id in self._enabled_target_ids
            if target_id in self._targets
        ]

    def get_target(self, target_id: str | None) -> VerificationTarget | None:
        if not target_id or target_id == "none":
            return None
        target = self._targets.get(target_id)
        if target is None or target_id not in self._enabled_target_ids:
            raise ReleaseGuardianPolicyError(
                "That verification target is not enabled for this agent."
            )
        return target

    def repository_verification(
        self, target: VerificationTarget
    ) -> RepositoryVerification:
        """Return the only executable configuration after strict local validation."""
        if target.target_id != CONFIGURED_REPOSITORY.target_id:
            raise ReleaseGuardianPolicyError(
                "That verification target does not support repository execution."
            )
        if not self._repository_path:
            raise ReleaseGuardianPolicyError(
                "No release repository is configured for this agent."
            )

        repository_path = Path(self._repository_path).expanduser()
        if not repository_path.is_absolute():
            raise ReleaseGuardianPolicyError(
                "RELEASE_GUARDIAN_REPO_PATH must be an absolute path."
            )

        try:
            command = tuple(shlex.split(self._repository_test_command))
        except ValueError as error:
            raise ReleaseGuardianPolicyError(
                "The configured repository test command is invalid."
            ) from error
        if len(command) < 3 or command[0] not in {"python", "python3", "python3.12"}:
            raise ReleaseGuardianPolicyError(
                "RELEASE_GUARDIAN_REPO_TEST_COMMAND must start with 'python -m pytest'."
            )
        if command[1:3] != ("-m", "pytest") or any(
            option not in self._allowed_pytest_options for option in command[3:]
        ):
            raise ReleaseGuardianPolicyError(
                "RELEASE_GUARDIAN_REPO_TEST_COMMAND may only run pytest with approved quiet options."
            )
        if not 5 <= self._repository_test_timeout <= 300:
            raise ReleaseGuardianPolicyError(
                "RELEASE_GUARDIAN_REPO_TEST_TIMEOUT must be between 5 and 300 seconds."
            )
        return RepositoryVerification(
            repository_path=repository_path.resolve(),
            command=command,
            timeout_seconds=self._repository_test_timeout,
        )

    def validate_requirements(self, requirements: str) -> str:
        cleaned = " ".join((requirements or "").split())
        if len(cleaned) < 10:
            raise ReleaseGuardianPolicyError(
                "Please provide at least a short feature requirement (10 characters or more)."
            )
        if len(cleaned) > self.max_requirement_chars:
            raise ReleaseGuardianPolicyError(
                f"Requirements exceed the {self.max_requirement_chars}-character safety limit."
            )
        return cleaned

    def validate_case_count(self, case_count: int) -> int:
        if not 1 <= case_count <= self.max_case_count:
            raise ReleaseGuardianPolicyError(
                f"Choose between 1 and {self.max_case_count} test cases for an agent run."
            )
        return case_count
