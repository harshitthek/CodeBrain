"""In-memory, per-sender workflow state for the chat agent."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import StrEnum
from uuid import uuid4

from apps.release_guardian.schemas import QAPlan


class SessionStage(StrEnum):
    HOME = "home"
    INPUT_METHOD = "input_method"
    REQUIREMENT_ENTRY = "requirement_entry"
    GUIDED_ENTRY = "guided_entry"
    PLAN_PREVIEW = "plan_preview"
    GENERATING = "generating"
    REVIEW = "review"
    RUNNING = "running"
    COMPLETE = "complete"


@dataclass
class GuardianSession:
    stage: SessionStage = SessionStage.HOME
    flow_id: str = ""
    requirements: str = ""
    case_count: int = 3
    target_id: str = "none"
    plan: QAPlan | None = None

    def __post_init__(self) -> None:
        if not self.flow_id:
            self.flow_id = uuid4().hex


class SessionStore:
    """A concurrency-safe session registry; restart recovery is intentionally explicit."""

    def __init__(self) -> None:
        self._sessions: dict[str, GuardianSession] = {}
        self._lock = asyncio.Lock()

    async def get(self, sender: str) -> GuardianSession:
        async with self._lock:
            return self._sessions.setdefault(sender, GuardianSession())

    async def reset(self, sender: str) -> GuardianSession:
        """Discard this in-memory flow and issue a fresh card-flow identity."""
        async with self._lock:
            session = GuardianSession()
            self._sessions[sender] = session
            return session

    async def transition(
        self, sender: str, expected: SessionStage | tuple[SessionStage, ...], target: SessionStage
    ) -> GuardianSession | None:
        """Move one session only when it is in an expected stage."""
        expected_stages = (expected,) if isinstance(expected, SessionStage) else expected
        async with self._lock:
            session = self._sessions.setdefault(sender, GuardianSession())
            if session.stage not in expected_stages:
                return None
            session.stage = target
            return session

    async def save_draft(
        self,
        sender: str,
        requirements: str,
        case_count: int,
        target_id: str,
    ) -> GuardianSession:
        async with self._lock:
            session = self._sessions.setdefault(sender, GuardianSession())
            session.requirements = requirements
            session.case_count = case_count
            session.target_id = target_id
            session.plan = None
            session.stage = SessionStage.PLAN_PREVIEW
            return session

    async def claim_generation(self, sender: str) -> GuardianSession | None:
        """Atomically reserve a reviewed draft for one model-generation run."""
        async with self._lock:
            session = self._sessions.setdefault(sender, GuardianSession())
            if session.stage != SessionStage.PLAN_PREVIEW or not session.requirements:
                return None
            session.stage = SessionStage.GENERATING
            return session

    async def save_plan(self, sender: str, plan: QAPlan) -> None:
        async with self._lock:
            session = self._sessions.setdefault(sender, GuardianSession())
            session.plan = plan
            session.stage = SessionStage.REVIEW

    async def claim_live_check(self, sender: str) -> QAPlan | None:
        """Atomically reserve the one permitted repository test run for a plan.

        ACP handlers can run concurrently. Marking the session as running while
        holding the registry lock prevents two rapid approval messages from
        starting the same configured test suite twice.
        """
        async with self._lock:
            session = self._sessions.setdefault(sender, GuardianSession())
            if (
                session.stage != SessionStage.REVIEW
                or session.plan is None
                or not session.plan.target_id
            ):
                return None
            session.stage = SessionStage.RUNNING
            return session.plan

    async def complete(self, sender: str) -> None:
        async with self._lock:
            session = self._sessions.setdefault(sender, GuardianSession())
            session.stage = SessionStage.COMPLETE
