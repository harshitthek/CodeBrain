"""In-memory, per-sender workflow state for the chat agent."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import StrEnum

from apps.release_guardian.schemas import QAPlan


class SessionStage(StrEnum):
    INTAKE = "intake"
    REVIEW = "review"
    RUNNING = "running"
    COMPLETE = "complete"


@dataclass
class GuardianSession:
    stage: SessionStage = SessionStage.INTAKE
    plan: QAPlan | None = None


class SessionStore:
    """A concurrency-safe session registry; restart recovery is intentionally explicit."""

    def __init__(self) -> None:
        self._sessions: dict[str, GuardianSession] = {}
        self._lock = asyncio.Lock()

    async def get(self, sender: str) -> GuardianSession:
        async with self._lock:
            return self._sessions.setdefault(sender, GuardianSession())

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
