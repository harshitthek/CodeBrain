"""Guided, card-first conversation state machine for Release Guardian."""

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

from .cards import (
    format_plan_for_chat,
    guided_requirement_card,
    home_card,
    intake_card,
    input_method_card,
    preview_card,
    review_card,
)
from .session import GuardianSession, SessionStage, SessionStore


@dataclass
class WorkflowResponse:
    text: str
    card: MetadataContent | None = None


class ReleaseGuardianWorkflow:
    """Accept structured card progressions before asking ASI:One to reason.

    A raw chat message is never interpreted as a feature requirement at the
    home screen. This prevents greetings, planner paraphrases, questions, and
    delivery retries from accidentally starting Actor-Critic generation.
    """

    _ROUTED_AGENT_MENTION = re.compile(
        r"^\s*@(?:agent1[0-9a-z]+|codebrain(?:-release-guardian)?)\b\s*",
        re.IGNORECASE,
    )
    _PLANNER_SELECTION = re.compile(
        r"^\s*(?:the\s+)?user\s+selected\s+[\"']?(?P<label>.+?)[\"']?[.!?]?\s*$",
        re.IGNORECASE,
    )
    _PLANNER_TEXT_PREFIX = re.compile(
        r"""^\s*(?:(?:the\s+)?user(?:'s)?\s+(?:message|input|text)|
        (?:the\s+)?user\s+(?:said|says|wrote|writes|sent))\s*(?:is|was|:|-)?\s*""",
        re.IGNORECASE | re.VERBOSE,
    )
    _PLANNER_ACTIONS = {
        "create a qa plan": ("home_selection", "create_qa_plan"),
        "what can this agent do": ("home_selection", "about"),
        "start over": ("home_selection", "start_over"),
        "paste a feature requirement": ("input_method_selection", "paste_requirement"),
        "paste a requirement": ("input_method_selection", "paste_requirement"),
        "answer guided questions": ("input_method_selection", "guided_questions"),
        "use a safe demo example": ("input_method_selection", "demo_example"),
        "back to the main menu": ("input_method_selection", "back_home"),
        "generate qa plan": ("generate_plan", ""),
        "edit requirement": ("edit_requirement", ""),
        "finish qa review": ("review_selection", "finish"),
        "revise the requirement": ("review_selection", "revise"),
        "run configured pytest verification": ("review_selection", "run_configured_test"),
    }
    _DEMO_REQUIREMENT = (
        "A verified user can request a password-reset email. The reset link expires "
        "after 15 minutes and cannot be used twice."
    )

    def __init__(
        self, service: ReleaseGuardianService, sessions: SessionStore | None = None
    ) -> None:
        self.service = service
        self.sessions = sessions or SessionStore()

    async def welcome(self, sender: str, notice: str | None = None) -> WorkflowResponse:
        return self._home_response(await self.sessions.get(sender), notice)

    async def handle(
        self,
        sender: str,
        text: str,
        selection: dict[str, Any] | None = None,
        cancelled: bool = False,
    ) -> WorkflowResponse:
        if cancelled:
            session = await self.sessions.reset(sender)
            return self._home_response(session, "That card interaction was cancelled. Choose an option to begin.")

        session = await self.sessions.get(sender)
        if selection:
            return await self._handle_card_selection(sender, session, dict(selection))

        text_selection = self._text_card_selection(text)
        if text_selection is not None:
            return await self._handle_card_selection(sender, session, text_selection)

        planner_selection = self._planner_selection(text, session)
        if planner_selection is not None:
            return await self._handle_card_selection(sender, session, planner_selection)
        return await self._handle_text(sender, session, text)

    def _home_response(self, session: GuardianSession, notice: str | None = None) -> WorkflowResponse:
        message = notice or (
            "CodeBrain Release Guardian is a guided QA-planning agent. It creates and reviews "
            "QA plans with ASI:One only after you choose a workflow below. It can optionally run "
            "one operator-configured pytest check after an explicit review decision."
        )
        return WorkflowResponse(message, home_card(session.flow_id))

    async def _handle_text(self, sender: str, session: GuardianSession, text: str) -> WorkflowResponse:
        if session.stage == SessionStage.COMPLETE:
            session = await self.sessions.reset(sender)
            return self._home_response(session, "That workflow is complete. Choose an option to start a new one.")
        if session.stage == SessionStage.HOME:
            return self._home_response(
                session,
                "CodeBrain Release Guardian has not treated that message as a requirement. "
                "Select Create a QA plan, then choose how to provide the input.",
            )
        if session.stage == SessionStage.INPUT_METHOD:
            return WorkflowResponse("Choose an input method before I can accept a requirement.", input_method_card(session.flow_id))
        if session.stage == SessionStage.REQUIREMENT_ENTRY:
            return await self._save_draft(sender, session, self._unwrap_planner_text(text), 3, "none")
        if session.stage == SessionStage.GUIDED_ENTRY:
            return WorkflowResponse(
                "Use the guided form so I can collect the feature, user, success outcome, and edge case separately.",
                guided_requirement_card(self.service.available_targets(), session.flow_id),
            )
        if session.stage == SessionStage.PLAN_PREVIEW:
            return WorkflowResponse(
                "Review the request and use the card to generate or edit it. I have not started ASI:One generation yet.",
                self._preview_card(session),
            )
        if session.stage == SessionStage.GENERATING:
            return WorkflowResponse("The QA plan is being generated. Please wait for the review card.")
        if session.stage == SessionStage.REVIEW and session.plan is not None:
            return WorkflowResponse(
                "Use the review card to finish, revise the requirement, or explicitly run the configured verification.",
                review_card(session.plan, session.flow_id),
            )
        if session.stage == SessionStage.RUNNING:
            return WorkflowResponse("The configured repository check is already running. Please wait for its result.")
        session = await self.sessions.reset(sender)
        return self._home_response(session)

    async def _handle_card_selection(
        self, sender: str, session: GuardianSession, selection: dict[str, Any]
    ) -> WorkflowResponse:
        if not self._selection_matches_flow(selection, session):
            return await self._handle_text(sender, session, "")

        action = str(selection.get("action", "")).strip()
        choice = str(selection.get("choice", "")).strip()
        if action == "home_selection" and session.stage in {SessionStage.HOME, SessionStage.COMPLETE}:
            return await self._home_selection(sender, session, choice)
        if action == "input_method_selection" and session.stage == SessionStage.INPUT_METHOD:
            return await self._input_method_selection(sender, session, choice)
        if action == "submit_requirement" and session.stage == SessionStage.REQUIREMENT_ENTRY:
            return await self._save_draft(
                sender, session, str(selection.get("requirements", "")),
                self._case_count(selection.get("case_count", 3)), str(selection.get("target", "none")),
            )
        if action == "submit_guided_requirement" and session.stage == SessionStage.GUIDED_ENTRY:
            return await self._save_draft(
                sender, session, self._guided_requirements(selection),
                self._case_count(selection.get("case_count", 3)), str(selection.get("target", "none")),
            )
        if action == "generate_plan" and session.stage == SessionStage.PLAN_PREVIEW:
            return await self._generate_plan(sender)
        if action == "edit_requirement" and session.stage == SessionStage.PLAN_PREVIEW:
            updated = await self.sessions.transition(sender, SessionStage.PLAN_PREVIEW, SessionStage.REQUIREMENT_ENTRY)
            assert updated is not None
            return WorkflowResponse(
                "Paste the revised requirement. It will be shown for confirmation before ASI:One is called.",
                intake_card(self.service.available_targets(), updated.flow_id),
            )
        if action == "review_selection" and session.stage == SessionStage.REVIEW:
            return await self._review_selection(sender, session, choice)
        return await self._handle_text(sender, session, "")

    async def _home_selection(self, sender: str, session: GuardianSession, choice: str) -> WorkflowResponse:
        if choice == "create_qa_plan":
            updated = await self.sessions.transition(sender, (SessionStage.HOME, SessionStage.COMPLETE), SessionStage.INPUT_METHOD)
            if updated is None:
                return await self._handle_text(sender, session, "")
            return WorkflowResponse("Choose how you would like to provide the QA requirement.", input_method_card(updated.flow_id))
        if choice == "about":
            return self._home_response(
                session,
                "I turn an explicitly submitted feature requirement into a reviewable QA plan. "
                "I cannot use repository paths or commands from chat, and I only offer one configured pytest check after review.",
            )
        if choice == "start_over":
            return self._home_response(await self.sessions.reset(sender), "Started a fresh guided workflow.")
        return self._home_response(session, "Choose one of the listed options to continue.")

    async def _input_method_selection(self, sender: str, session: GuardianSession, choice: str) -> WorkflowResponse:
        if choice == "paste_requirement":
            updated = await self.sessions.transition(sender, SessionStage.INPUT_METHOD, SessionStage.REQUIREMENT_ENTRY)
            assert updated is not None
            return WorkflowResponse(
                "Paste the feature requirement or acceptance criteria. I will show a confirmation card before generation.",
                intake_card(self.service.available_targets(), updated.flow_id),
            )
        if choice == "guided_questions":
            updated = await self.sessions.transition(sender, SessionStage.INPUT_METHOD, SessionStage.GUIDED_ENTRY)
            assert updated is not None
            return WorkflowResponse(
                "Answer the guided fields. The combined requirement will be shown for confirmation.",
                guided_requirement_card(self.service.available_targets(), updated.flow_id),
            )
        if choice == "demo_example":
            return await self._save_draft(sender, session, self._DEMO_REQUIREMENT, 1, "none")
        if choice == "back_home":
            return self._home_response(await self.sessions.reset(sender))
        return WorkflowResponse("Choose one of the listed input methods.", input_method_card(session.flow_id))

    async def _save_draft(
        self, sender: str, session: GuardianSession, requirements: str, case_count: int, target_id: str
    ) -> WorkflowResponse:
        try:
            cleaned = self.service.policy.validate_requirements(requirements)
            count = self.service.policy.validate_case_count(case_count)
            target = self.service.policy.get_target(target_id)
            available_target_ids = {item.target_id for item in self.service.available_targets()}
            if target is not None and target.target_id not in available_target_ids:
                raise ReleaseGuardianPolicyError("That verification target is currently unavailable.")
        except ReleaseGuardianPolicyError as error:
            return WorkflowResponse(str(error), self._entry_card(session))

        saved = await self.sessions.save_draft(sender, cleaned, count, target.target_id if target else "none")
        return WorkflowResponse("Review this request before I call ASI:One to generate a QA plan.", self._preview_card(saved))

    async def _generate_plan(self, sender: str) -> WorkflowResponse:
        session = await self.sessions.claim_generation(sender)
        if session is None:
            return await self._handle_text(sender, await self.sessions.get(sender), "")
        try:
            plan = await asyncio.to_thread(
                self.service.build_qa_plan, session.requirements, session.case_count, session.target_id
            )
        except (ReleaseGuardianPolicyError, ReleaseGuardianConfigurationError) as error:
            restored = await self.sessions.transition(sender, SessionStage.GENERATING, SessionStage.PLAN_PREVIEW)
            return WorkflowResponse(str(error), self._preview_card(restored or session))
        except Exception:  # noqa: BLE001 - provider internals stay out of chat.
            restored = await self.sessions.transition(sender, SessionStage.GENERATING, SessionStage.PLAN_PREVIEW)
            return WorkflowResponse(
                "I could not create the QA plan. Review the request and try again.", self._preview_card(restored or session)
            )

        await self.sessions.save_plan(sender, plan)
        current = await self.sessions.get(sender)
        return WorkflowResponse(
            text=(
                f"Created {len(plan.test_cases)} QA cases (quality signal {plan.quality_signal:.1f}/100). "
                "This score is a QA signal, not a release authorization.\n\n"
                f"{format_plan_for_chat(plan)}"
            ),
            card=review_card(plan, current.flow_id),
        )

    async def _review_selection(self, sender: str, session: GuardianSession, choice: str) -> WorkflowResponse:
        if choice == "finish":
            await self.sessions.complete(sender)
            current = await self.sessions.reset(sender)
            return WorkflowResponse(
                "QA review complete. No external request was made. Choose an option to begin another guided workflow.",
                home_card(current.flow_id),
            )
        if choice == "revise":
            updated = await self.sessions.transition(sender, SessionStage.REVIEW, SessionStage.REQUIREMENT_ENTRY)
            assert updated is not None
            return WorkflowResponse(
                "Paste the revised requirement. I will ask for confirmation before generating again.",
                intake_card(self.service.available_targets(), updated.flow_id),
            )
        if choice == "run_configured_test":
            return await self._execute_approved_check(sender)
        return WorkflowResponse(
            "Choose a next step from the review card.", review_card(session.plan, session.flow_id) if session.plan else None
        )

    async def _execute_approved_check(self, sender: str) -> WorkflowResponse:
        plan = await self.sessions.claim_live_check(sender)
        if plan is None:
            return WorkflowResponse("There is no pending configured repository test run to start, or it has already started.")
        try:
            report = await asyncio.to_thread(self.service.execute_live_check, plan)
        except ReleaseGuardianPolicyError as error:
            await self.sessions.complete(sender)
            current = await self.sessions.reset(sender)
            return WorkflowResponse(str(error), home_card(current.flow_id))
        except Exception:  # noqa: BLE001 - do not expose runtime details in chat.
            await self.sessions.complete(sender)
            current = await self.sessions.reset(sender)
            return WorkflowResponse("The configured repository test run could not complete. No retry was attempted.", home_card(current.flow_id))

        await self.sessions.complete(sender)
        current = await self.sessions.reset(sender)
        verdict = "passed" if report.failed == 0 else "needs attention"
        return WorkflowResponse(
            f"Repository test run against {report.target_label} {verdict}: "
            f"{report.passed}/{report.total} passed ({report.pass_rate:.1f}%). "
            "This is evidence for the QA plan, not permission to deploy.",
            home_card(current.flow_id),
        )

    def _preview_card(self, session: GuardianSession) -> MetadataContent:
        target_label = next(
            (target.label for target in self.service.available_targets() if target.target_id == session.target_id), None
        )
        return preview_card(session.requirements, session.case_count, target_label, session.flow_id)

    def _entry_card(self, session: GuardianSession) -> MetadataContent:
        if session.stage == SessionStage.GUIDED_ENTRY:
            return guided_requirement_card(self.service.available_targets(), session.flow_id)
        return intake_card(self.service.available_targets(), session.flow_id)

    @staticmethod
    def _case_count(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _selection_matches_flow(selection: dict[str, Any], session: GuardianSession) -> bool:
        return str(selection.get("flow_id", "")) == session.flow_id

    @classmethod
    def _text_card_selection(cls, text: str) -> dict[str, Any] | None:
        """Accept a legacy client card response only when it is fully structured.

        The chat-card protocol allows older clients to put the CTA selection
        JSON in ``TextContent`` rather than a ``MetadataContent`` response.
        We accept that compatibility form only when it includes both the card
        action and the server-issued flow ID; arbitrary JSON and free text
        therefore still cannot advance the workflow.
        """
        try:
            payload = json.loads(cls._ROUTED_AGENT_MENTION.sub("", text or "").strip())
        except (TypeError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        selection = payload.get("selection", payload)
        if not isinstance(selection, dict):
            return None
        if "action" not in selection or "flow_id" not in selection:
            return None
        return dict(selection)

    @classmethod
    def _planner_selection(cls, text: str, session: GuardianSession) -> dict[str, str] | None:
        match = cls._PLANNER_SELECTION.match(text or "")
        if not match:
            return None
        mapped = cls._PLANNER_ACTIONS.get(" ".join(match.group("label").casefold().split()))
        if mapped is None:
            return None
        action, choice = mapped
        selection = {"action": action, "flow_id": session.flow_id}
        if choice:
            selection["choice"] = choice
        return selection

    @classmethod
    def _unwrap_planner_text(cls, text: str) -> str:
        cleaned = cls._ROUTED_AGENT_MENTION.sub("", text or "").strip()
        return cls._PLANNER_TEXT_PREFIX.sub("", cleaned).strip().strip("\"'")

    @staticmethod
    def _guided_requirements(selection: dict[str, Any]) -> str:
        feature = str(selection.get("feature", "")).strip()
        user = str(selection.get("user", "")).strip()
        success = str(selection.get("success", "")).strip()
        failure = str(selection.get("failure", "")).strip()
        sections = [
            f"Feature or change: {feature}",
            f"Intended user: {user}",
            f"Successful outcome: {success}",
        ]
        if failure:
            sections.append(f"Important failure or edge case: {failure}")
        return "\n".join(sections)
