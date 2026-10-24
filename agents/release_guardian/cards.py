"""Standards-based interactive cards used in ASI:One chat."""

from __future__ import annotations

from uagents_core.contrib.protocols.chat import MetadataContent
from uagents_core.contrib.protocols.chat.cards import (
    CtaAction,
    FormCardPayload,
    FormField,
    FormFieldOption,
    ReviewCardPayload,
    ReviewSummaryRow,
    create_card_content,
)

from apps.release_guardian.policy import VerificationTarget
from apps.release_guardian.schemas import QAPlan


def home_card(flow_id: str) -> MetadataContent:
    """Render the only entry point for a new Release Guardian conversation."""
    return create_card_content(
        FormCardPayload(
            title="CodeBrain Release Guardian",
            fields=[
                FormField(
                    name="choice",
                    kind="select",
                    label="What would you like to do?",
                    options=[
                        FormFieldOption(value="create_qa_plan", label="Create a QA plan"),
                        FormFieldOption(value="about", label="What can this agent do?"),
                        FormFieldOption(value="start_over", label="Start over"),
                    ],
                    required=True,
                )
            ],
            submit_cta=CtaAction(
                label="Continue",
                selection={"action": "home_selection", "flow_id": flow_id},
            ),
        )
    )


def input_method_card(flow_id: str) -> MetadataContent:
    return create_card_content(
        FormCardPayload(
            title="Choose how to provide the QA requirement",
            fields=[
                FormField(
                    name="choice",
                    kind="select",
                    label="Input method",
                    options=[
                        FormFieldOption(value="paste_requirement", label="Paste a feature requirement"),
                        FormFieldOption(value="guided_questions", label="Answer guided questions"),
                        FormFieldOption(value="demo_example", label="Use a safe demo example"),
                        FormFieldOption(value="back_home", label="Back to the main menu"),
                    ],
                    required=True,
                )
            ],
            submit_cta=CtaAction(
                label="Continue",
                selection={"action": "input_method_selection", "flow_id": flow_id},
            ),
        )
    )


def intake_card(targets: list[VerificationTarget], flow_id: str = "") -> MetadataContent:
    """Collect a requirement only after the user selected the paste-input path."""
    target_options = [FormFieldOption(value="none", label="No test run — QA plan only")]
    target_options.extend(
        FormFieldOption(value=target.target_id, label=target.label)
        for target in targets
    )
    return create_card_content(
        FormCardPayload(
            title="Create a Release Guardian QA plan",
            fields=[
                FormField(
                    name="requirements",
                    kind="text",
                    label="Feature requirement or acceptance criteria",
                    placeholder="Example: Users can reset a password by verified email.",
                    required=True,
                ),
                FormField(
                    name="case_count",
                    kind="select",
                    label="Number of QA cases",
                    options=[
                        FormFieldOption(value="1", label="1 rapid QA case"),
                        FormFieldOption(value="3", label="3 expanded QA cases"),
                    ],
                    required=True,
                ),
                FormField(
                    name="target",
                    kind="select",
                    label="Optional post-review repository test run",
                    options=target_options,
                    required=True,
                ),
            ],
            submit_cta=CtaAction(
                label="Review requirement",
                selection={"action": "submit_requirement", "flow_id": flow_id},
            ),
        )
    )


def guided_requirement_card(
    targets: list[VerificationTarget], flow_id: str
) -> MetadataContent:
    target_options = [FormFieldOption(value="none", label="No test run — QA plan only")]
    target_options.extend(
        FormFieldOption(value=target.target_id, label=target.label)
        for target in targets
    )
    return create_card_content(
        FormCardPayload(
            title="Describe the feature in four short fields",
            fields=[
                FormField(name="feature", kind="text", label="Feature or change", required=True),
                FormField(name="user", kind="text", label="Who uses it?", required=True),
                FormField(name="success", kind="text", label="Expected successful outcome", required=True),
                FormField(name="failure", kind="text", label="Important failure or edge case", required=False),
                FormField(
                    name="case_count",
                    kind="select",
                    label="Number of QA cases",
                    options=[
                        FormFieldOption(value="1", label="1 focused QA case"),
                        FormFieldOption(value="3", label="3 expanded QA cases"),
                    ],
                    required=True,
                ),
                FormField(
                    name="target",
                    kind="select",
                    label="Optional post-review repository test run",
                    options=target_options,
                    required=True,
                ),
            ],
            submit_cta=CtaAction(
                label="Review requirement",
                selection={"action": "submit_guided_requirement", "flow_id": flow_id},
            ),
        )
    )


def preview_card(
    requirements: str, case_count: int, target_label: str | None, flow_id: str
) -> MetadataContent:
    return create_card_content(
        ReviewCardPayload(
            title="Confirm the QA-plan request",
            summary_rows=[
                ReviewSummaryRow(label="Requirement", value=_truncate(requirements, 360)),
                ReviewSummaryRow(label="QA depth", value=f"{case_count} case(s)"),
                ReviewSummaryRow(
                    label="Verification",
                    value=target_label or "QA plan only — no repository test offered",
                ),
            ],
            approve_cta=CtaAction(
                label="Generate QA plan",
                selection={"action": "generate_plan", "flow_id": flow_id},
            ),
            reject_cta=CtaAction(
                label="Edit requirement",
                selection={"action": "edit_requirement", "flow_id": flow_id},
            ),
        )
    )


def review_card(plan: QAPlan, flow_id: str) -> MetadataContent:
    """Provide a stage-validated next-step menu after the QA plan text."""
    choices = [
        FormFieldOption(value="finish", label="Finish QA review"),
        FormFieldOption(value="revise", label="Revise the requirement"),
    ]
    if plan.target_id:
        choices.append(
            FormFieldOption(value="run_configured_test", label="Run configured pytest verification")
        )
    return create_card_content(
        FormCardPayload(
            title="Choose the next QA-plan step",
            fields=[
                FormField(
                    name="choice",
                    kind="select",
                    label="Next step",
                    options=choices,
                    required=True,
                )
            ],
            submit_cta=CtaAction(
                label="Continue",
                selection={"action": "review_selection", "flow_id": flow_id},
            ),
        )
    )


def card_payload_size(card: MetadataContent) -> int:
    """Expose a testable guard for the ASI card payload limit."""
    return len(card.metadata.get("card_payload", "").encode("utf-8"))


def format_plan_for_chat(plan: QAPlan, max_chars: int = 6_000) -> str:
    """Render the reviewable QA evidence in the ACP text message.

    A review card intentionally contains a compact confirmation summary. The
    user still needs the actual steps and expected results in the ASI:One
    conversation before approving an external test run.
    """
    lines = ["QA plan to review:"]
    for index, case in enumerate(plan.test_cases, start=1):
        lines.append(f"{index}. [{case.priority}] {_truncate(case.title, 240)}")
        lines.append("   Steps: " + " → ".join(_truncate(step, 300) for step in case.steps))
        lines.append(
            "   Expected: "
            + " | ".join(_truncate(result, 300) for result in case.expected_results)
        )
    if plan.reviewer_notes:
        lines.append("Reviewer focus: " + " | ".join(_truncate(note, 240) for note in plan.reviewer_notes))
    return _truncate("\n".join(lines), max_chars)


def _truncate(value: str, limit: int) -> str:
    cleaned = " ".join(str(value).split())
    return cleaned if len(cleaned) <= limit else f"{cleaned[: limit - 1]}…"
