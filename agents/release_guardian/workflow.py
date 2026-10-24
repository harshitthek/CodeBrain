"""Conversation state machine for the CodeBrain Release Guardian agent."""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from typing import Any

from uagents_core.contrib.protocols.chat import MetadataContent

from apps.release_guardian.policy import ReleaseGuardianPolicyError
from apps.release_guardian.service import (
    ReleaseGuardianConfigurationError,
    ReleaseGuardianService,
)

from .cards import intake_card, review_card
from .session import SessionStage, SessionStore


@dataclass
class WorkflowResponse:
    text: str
    card: MetadataContent | None = None


class ReleaseGuardianWorkflow:
    """Turns chat/card input into a QA plan and an explicit approval decision."""

    _INTRODUCTION_MESSAGES = frozenset(
        {
            "hi",
            "hello",
            "hey",
            "help",
            "what can you do",
            "what do you do",
            "how does this work",
        }
    )
    _ROUTED_AGENT_MENTION = re.compile(r"^\s*@agent1[0-9a-z]+\b\s*", re.IGNORECASE)

    def __init__(
        self, service: ReleaseGuardianService, sessions: SessionStore | None = None
    ) -> None:
        self.service = service
        self.sessions = sessions or SessionStore()

    async def welcome(self, sender: str) -> WorkflowResponse:
        await self.sessions.get(sender)
        return WorkflowResponse(
            text=(
                "I am CodeBrain Release Guardian. I use ASI:One-backed Actor–Critic reasoning "
                "to turn a feature requirement into a focused QA plan. An operator-configured repository "
                "test run is optional and will never run until you approve it."
            ),
            card=intake_card(self.service.available_targets()),
        )

    async def handle(
        self,
        sender: str,
        text: str,
        selection: dict[str, Any] | None = None,
        cancelled: bool = False,
    ) -> WorkflowResponse:
        session = await self.sessions.get(sender)
        if cancelled:
            return WorkflowResponse(
                "No action was taken. Send a requirement whenever you are ready."
            )

        payload = self._payload_from_input(text, selection)
        action = str(payload.get("action", "")).strip()
        if action == "approve_live_check":
            return await self._execute_approved_check(sender, session)
        if action == "finish_without_check":
            await self.sessions.complete(sender)
            return WorkflowResponse(
                "QA review complete. No external request was made. You can send another requirement to start a new plan."
            )

        requirements = self._strip_routed_agent_mention(
            str(payload.get("requirements") or text)
        )
        if self._is_introduction_message(requirements):
            return await self.welcome(sender)
        if not requirements:
            return await self.welcome(sender)

        target_id = str(payload.get("target", "none"))
        case_count = self._case_count(payload.get("case_count", 1))
        try:
            plan = await asyncio.to_thread(
                self.service.build_qa_plan,
                requirements,
                case_count,
                target_id,
            )
        except (ReleaseGuardianPolicyError, ReleaseGuardianConfigurationError) as error:
            return WorkflowResponse(
                str(error), intake_card(self.service.available_targets())
            )
        except Exception:  # noqa: BLE001 - keep provider details and prompts out of chat responses.
            return WorkflowResponse(
                "I could not create the QA plan. Please retry with a concise requirement.",
                intake_card(self.service.available_targets()),
            )

        await self.sessions.save_plan(sender, plan)
        case_titles = "; ".join(case.title for case in plan.test_cases[:3])
        target_note = (
            "Approve the card only if you want the selected configured repository test run."
            if plan.target_id
            else "No verification target was selected, so this review stays entirely in chat."
        )
        return WorkflowResponse(
            text=(
                f"Created {len(plan.test_cases)} QA cases (quality signal {plan.quality_signal:.1f}/100): "
                f"{case_titles}. This score is a QA signal, not a release authorization. {target_note}"
            ),
            card=review_card(plan),
        )

    async def _execute_approved_check(
        self, sender: str, session: Any
    ) -> WorkflowResponse:
        if (
            session.stage != SessionStage.REVIEW
            or session.plan is None
            or not session.plan.target_id
        ):
            return WorkflowResponse(
                "There is no pending approved repository test run. Create a QA plan first."
            )
        try:
            report = await asyncio.to_thread(
                self.service.execute_live_check, session.plan
            )
        except ReleaseGuardianPolicyError as error:
            return WorkflowResponse(str(error))
        except Exception:  # noqa: BLE001 - do not expose network internals or retry a live request.
            return WorkflowResponse(
                "The configured repository test run could not complete. No retry was attempted."
            )

        await self.sessions.complete(sender)
        verdict = "passed" if report.failed == 0 else "needs attention"
        return WorkflowResponse(
            f"Repository test run against {report.target_label} {verdict}: "
            f"{report.passed}/{report.total} passed ({report.pass_rate:.1f}%). "
            "This is evidence for the QA plan, not permission to deploy."
        )

    @staticmethod
    def _case_count(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 1

    @classmethod
    def _strip_routed_agent_mention(cls, text: str) -> str:
        """Remove ASI:One's leading routing mention before interpreting user intent."""
        return cls._ROUTED_AGENT_MENTION.sub("", text or "").strip()

    @classmethod
    def _is_introduction_message(cls, text: str) -> bool:
        normalised = " ".join(text.casefold().split()).strip(".!?")
        return normalised in cls._INTRODUCTION_MESSAGES

    @staticmethod
    def _payload_from_input(
        text: str, selection: dict[str, Any] | None
    ) -> dict[str, Any]:
        if selection:
            return dict(selection)
        try:
            decoded = json.loads(text)
        except (TypeError, json.JSONDecodeError):
            return {}
        return decoded if isinstance(decoded, dict) else {}
