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


def intake_card(targets: list[VerificationTarget]) -> MetadataContent:
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
                label="Generate QA plan", selection={"action": "create_qa_plan"}
            ),
        )
    )


def review_card(plan: QAPlan) -> MetadataContent:
    rows = [
        ReviewSummaryRow(
            label="Quality signal", value=f"{plan.quality_signal:.1f}/100"
        ),
        ReviewSummaryRow(label="Reflection passes", value=str(plan.iterations_run)),
        ReviewSummaryRow(label="QA cases", value=str(len(plan.test_cases))),
    ]
    if plan.target_label:
        rows.append(
            ReviewSummaryRow(label="Verification target", value=plan.target_label)
        )
        approve = CtaAction(
            label="Approve repository test run",
            selection={"action": "approve_live_check"},
        )
        reject = CtaAction(
            label="Finish without test run",
            selection={"action": "finish_without_check"},
        )
    else:
        approve = CtaAction(
            label="Finish QA review", selection={"action": "finish_without_check"}
        )
        reject = None

    for index, case in enumerate(plan.test_cases[:3], start=1):
        rows.append(
            ReviewSummaryRow(
                label=f"QA case {index}", value=_truncate(case.title, 140)
            )
        )
    return create_card_content(
        ReviewCardPayload(
            title="Review the QA plan before any external call",
            summary_rows=rows,
            approve_cta=approve,
            reject_cta=reject,
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
