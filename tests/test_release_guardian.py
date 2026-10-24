import asyncio
import importlib
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from agents.release_guardian.cards import card_payload_size, intake_card
from agents.release_guardian.workflow import ReleaseGuardianWorkflow
from apps.release_guardian.policy import (
    ReleaseGuardianPolicy,
    ReleaseGuardianPolicyError,
)
from apps.release_guardian.service import (
    ReleaseGuardianConfigurationError,
    ReleaseGuardianService,
)


def pipeline_result(_requirements, _case_count):
    return {
        "success": True,
        "converged": True,
        "final_score": 92.5,
        "iterations_run": 2,
        "final_cases": [
            {
                "description": "Reset password with a verified email",
                "test_steps": [
                    "Request reset",
                    "Open verified email",
                    "Set a new password",
                ],
                "expected_results": [
                    "The password is changed and the old password is rejected"
                ],
                "priority": "P0",
            },
            {
                "description": "Reject an expired password-reset link",
                "test_steps": ["Open an expired reset link"],
                "expected_results": [
                    "Show a safe expiry message and do not change the password"
                ],
                "priority": "P1",
            },
        ],
        "history": [{"critique": {"suggestions": ["Exercise a rate-limit boundary"]}}],
    }


def make_test_repository(tmp_path: Path) -> Path:
    """Create a minimal, real Git repository whose pytest suite is deterministic."""
    repository = tmp_path / "release-fixture"
    repository.mkdir()
    (repository / "test_release.py").write_text(
        "def test_release_fixture_is_healthy():\n    assert 2 + 2 == 4\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "init", "-q", str(repository)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return repository


def configured_policy(repository: Path) -> ReleaseGuardianPolicy:
    return ReleaseGuardianPolicy(
        enabled_target_ids=("configured_repository",),
        repository_path=str(repository),
        repository_test_command="python -m pytest -q",
        repository_test_timeout=30,
    )


def test_policy_only_exposes_a_configured_repository_and_rejects_other_commands(
    tmp_path,
):
    repository = make_test_repository(tmp_path)
    policy = configured_policy(repository)
    target = policy.get_target("configured_repository")
    assert target is not None
    verification = policy.repository_verification(target)
    assert verification.repository_path == repository.resolve()
    assert verification.command == ("python", "-m", "pytest", "-q")
    with pytest.raises(ReleaseGuardianPolicyError):
        policy.get_target("https://untrusted.example")
    with pytest.raises(ReleaseGuardianPolicyError, match="may only run pytest"):
        ReleaseGuardianPolicy(
            enabled_target_ids=("configured_repository",),
            repository_path=str(repository),
            repository_test_command="python -m pytest -q tests/unit",
        ).repository_verification(target)
    assert ReleaseGuardianPolicy().enabled_targets() == []


def test_cards_follow_the_standard_metadata_contract_and_size_limit(tmp_path):
    card = intake_card(
        configured_policy(make_test_repository(tmp_path)).enabled_targets()
    )
    assert card.metadata["card_protocol_version"] == "1"
    assert card.metadata["requires_card_interaction"] == "true"
    assert card.metadata["card_kind"] == "form"
    assert card_payload_size(card) < 64 * 1024


def test_plan_is_normalised_and_runs_a_real_configured_repository_suite(tmp_path):
    service = ReleaseGuardianService(
        policy=configured_policy(make_test_repository(tmp_path)),
        pipeline_runner=pipeline_result,
    )
    plan = service.build_qa_plan(
        "A verified user can reset a password using an email link.",
        case_count=3,
        target_id="configured_repository",
    )
    assert plan.quality_signal == 92.5
    assert plan.iterations_run == 2
    assert plan.target_id == "configured_repository"
    assert len(plan.test_cases) == 2

    report = service.execute_live_check(plan)
    assert report.pass_rate == 100.0
    assert report.passed == 1
    assert report.failed == 0
    assert report.results[0]["exit_code"] == 0
    assert report.results[0]["commit"] == "no-commit"


def test_pytest_summary_parser_reports_multiline_counts_without_exposing_output():
    assert ReleaseGuardianService._pytest_counts(
        "\n73 passed, 7 warnings in 8.65s\n", 0
    ) == (73, 0)
    assert ReleaseGuardianService._pytest_counts(
        "\n2 failed, 4 passed in 1.0s\n", 1
    ) == (4, 2)


def test_workflow_requires_approval_before_it_runs_the_repository_suite(tmp_path):
    service = ReleaseGuardianService(
        policy=configured_policy(make_test_repository(tmp_path)),
        pipeline_runner=pipeline_result,
    )
    workflow = ReleaseGuardianWorkflow(service)

    async def exercise_workflow():
        response = await workflow.handle(
            "agent1user",
            "",
            {
                "action": "create_qa_plan",
                "requirements": "A verified user can reset a password using an email link.",
                "case_count": "3",
                "target": "configured_repository",
            },
        )
        assert response.card is not None
        session = await workflow.sessions.get("agent1user")
        assert session.plan is not None
        assert session.plan.target_id == "configured_repository"

        result = await workflow.handle(
            "agent1user", "", {"action": "approve_live_check"}
        )
        assert "1/1 passed" in result.text

    asyncio.run(exercise_workflow())


def test_workflow_answers_a_greeting_without_calling_asi_one():
    def fail_if_called(_requirements, _case_count):
        raise AssertionError("A greeting must not start the ASI:One QA pipeline")

    workflow = ReleaseGuardianWorkflow(
        ReleaseGuardianService(pipeline_runner=fail_if_called)
    )

    async def exercise_greeting():
        response = await workflow.handle("agent1user", "Hi!")
        assert "CodeBrain Release Guardian" in response.text
        assert response.card is not None

    asyncio.run(exercise_greeting())


def test_workflow_strips_asi_one_routing_mention_before_classifying_a_greeting():
    def fail_if_called(_requirements, _case_count):
        raise AssertionError("A routed greeting must not start the ASI:One QA pipeline")

    workflow = ReleaseGuardianWorkflow(
        ReleaseGuardianService(pipeline_runner=fail_if_called)
    )

    async def exercise_routed_greeting():
        response = await workflow.handle(
            "agent1user",
            "@agent1q2j6crzl0hvhq8vc3unxqr2t96jeytsqwyzjaw8hzqxppkcvc95nun37g6k hi",
        )
        assert "CodeBrain Release Guardian" in response.text
        assert response.card is not None

    asyncio.run(exercise_routed_greeting())


def test_asi_one_key_is_required_for_the_real_pipeline(monkeypatch):
    monkeypatch.delenv("ASI1_API_KEY", raising=False)
    service = ReleaseGuardianService()
    with pytest.raises(ReleaseGuardianConfigurationError, match="ASI1_API_KEY"):
        service.build_qa_plan(
            "A verified user can reset a password using an email link."
        )


def test_asi_one_provider_uses_the_configured_openai_compatible_endpoint():
    from django.conf import settings

    from apps.llm.base import LLMServiceFactory

    model = LLMServiceFactory.create("asi1")
    assert model.model_name == settings.LLM_PROVIDERS["asi1"]["model"]
    assert "api.asi1.ai" in str(model.openai_api_base)
    assert model.request_timeout == settings.LLM_PROVIDERS["asi1"]["timeout"]


def test_core_views_delay_knowledge_initialization_until_an_endpoint_needs_it():
    import apps.core.views as core_views

    with patch("apps.knowledge.service.get_knowledgeService_instance") as factory:
        importlib.reload(core_views)
        assert not factory.called
    importlib.reload(core_views)


def test_agent_factory_uses_mailbox_only_when_no_public_endpoint_is_configured(
    monkeypatch,
):
    from agents.release_guardian.agent import create_release_guardian_agent

    monkeypatch.delenv("AGENTVERSE_PUBLIC_ENDPOINT", raising=False)
    agent = create_release_guardian_agent(
        "release guardian local verification seed", publish_manifest=False
    )
    assert agent.name == "codebrain-release-guardian"
    assert agent.address.startswith("agent1")
    assert agent.agent_type == "mailbox"


def test_agent_factory_uses_the_public_endpoint_as_direct_acp_transport(monkeypatch):
    from agents.release_guardian.agent import create_release_guardian_agent

    monkeypatch.setenv("AGENTVERSE_PUBLIC_ENDPOINT", "https://agent.example.com/submit")
    agent = create_release_guardian_agent(
        "direct ACP verification seed", publish_manifest=False
    )
    assert agent.agent_type == "custom"
    assert [endpoint.url for endpoint in agent._endpoints] == [
        "https://agent.example.com/submit"
    ]


def test_agentverse_v2_registration_is_opt_in_and_uses_public_endpoint(monkeypatch):
    from agents.release_guardian.agent import register_production_agentverse_profile

    monkeypatch.delenv("AGENTVERSE_V2_REGISTRATION_ENABLED", raising=False)
    assert register_production_agentverse_profile("verification seed") is False

    monkeypatch.setenv("AGENTVERSE_V2_REGISTRATION_ENABLED", "true")
    monkeypatch.setenv("AGENTVERSE_API_KEY", "agentverse-api-key-for-test")
    monkeypatch.setenv("AGENTVERSE_PUBLIC_ENDPOINT", "https://agent.example.com/submit")
    with patch(
        "agents.release_guardian.agent.register_chat_agent", return_value=True
    ) as register:
        assert register_production_agentverse_profile("verification seed") is True

    assert register.call_args.kwargs["endpoint"] == "https://agent.example.com/submit"
    assert register.call_args.kwargs["name"] == "CodeBrain"
    assert (
        register.call_args.kwargs["credentials"].agent_seed_phrase
        == "verification seed"
    )
    assert (
        register.call_args.kwargs["credentials"].agentverse_api_key
        == "agentverse-api-key-for-test"
    )


def test_agentverse_v2_registration_rejects_the_inspector_or_private_endpoint(
    monkeypatch,
):
    from agents.release_guardian.agent import register_production_agentverse_profile

    monkeypatch.setenv("AGENTVERSE_V2_REGISTRATION_ENABLED", "true")
    monkeypatch.setenv("AGENTVERSE_API_KEY", "agentverse-api-key-for-test")
    monkeypatch.setenv(
        "AGENTVERSE_PUBLIC_ENDPOINT",
        "https://agentverse.ai/inspect/?uri=http://127.0.0.1:8000",
    )
    with pytest.raises(ValueError, match="without credentials or query data"):
        register_production_agentverse_profile("verification seed")

    monkeypatch.setenv("AGENTVERSE_PUBLIC_ENDPOINT", "https://127.0.0.1:8000/submit")
    with pytest.raises(
        ValueError, match="must not point to localhost or a private network address"
    ):
        register_production_agentverse_profile("verification seed")
