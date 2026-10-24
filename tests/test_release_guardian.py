import asyncio
import importlib
import subprocess
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

import pytest

from agents.release_guardian.cards import card_payload_size, home_card, intake_card
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


async def create_guided_plan(
    workflow: ReleaseGuardianWorkflow,
    sender: str,
    requirements: str,
    *,
    case_count: str = "3",
    target: str = "none",
):
    """Walk the only supported path to an ASI:One QA-plan generation."""
    session = await workflow.sessions.get(sender)
    await workflow.handle(
        sender,
        "",
        {"action": "home_selection", "choice": "create_qa_plan", "flow_id": session.flow_id},
    )
    session = await workflow.sessions.get(sender)
    await workflow.handle(
        sender,
        "",
        {
            "action": "input_method_selection",
            "choice": "paste_requirement",
            "flow_id": session.flow_id,
        },
    )
    session = await workflow.sessions.get(sender)
    await workflow.handle(
        sender,
        "",
        {
            "action": "submit_requirement",
            "requirements": requirements,
            "case_count": case_count,
            "target": target,
            "flow_id": session.flow_id,
        },
    )
    session = await workflow.sessions.get(sender)
    return await workflow.handle(
        sender, "", {"action": "generate_plan", "flow_id": session.flow_id}
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
    for card in (
        home_card("test-flow"),
        intake_card(
            configured_policy(make_test_repository(tmp_path)).enabled_targets(),
            "test-flow",
        ),
    ):
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
        response = await create_guided_plan(
            workflow,
            "agent1user",
            "A verified user can reset a password using an email link.",
            target="configured_repository",
        )
        assert response.card is not None
        session = await workflow.sessions.get("agent1user")
        assert session.plan is not None
        assert session.plan.target_id == "configured_repository"

        result = await workflow.handle(
            "agent1user",
            "",
            {
                "action": "review_selection",
                "choice": "run_configured_test",
                "flow_id": session.flow_id,
            },
        )
        assert "1/1 passed" in result.text

    asyncio.run(exercise_workflow())


def test_workflow_shows_reviewable_cases_and_claims_one_live_check(tmp_path):
    service = ReleaseGuardianService(
        policy=configured_policy(make_test_repository(tmp_path)),
        pipeline_runner=pipeline_result,
    )
    workflow = ReleaseGuardianWorkflow(service)

    async def exercise_workflow():
        response = await create_guided_plan(
            workflow,
            "agent1user",
            "A verified user can reset a password using an email link.",
            target="configured_repository",
        )
        assert "Steps: Request reset" in response.text
        assert "Expected: The password is changed" in response.text
        assert "Reviewer focus: Exercise a rate-limit boundary" in response.text
        session = await workflow.sessions.get("agent1user")

        first, second = await asyncio.gather(
            workflow.handle(
                "agent1user", "",
                {"action": "review_selection", "choice": "run_configured_test", "flow_id": session.flow_id},
            ),
            workflow.handle(
                "agent1user", "",
                {"action": "review_selection", "choice": "run_configured_test", "flow_id": session.flow_id},
            ),
        )
        responses = (first.text, second.text)
        assert sum("1/1 passed" in text for text in responses) == 1
        assert any(
            "already running" in text or "already started" in text or "no pending" in text
            for text in responses
        )

    asyncio.run(exercise_workflow())


def test_workflow_accepts_asi_one_planner_style_card_responses(tmp_path):
    service = ReleaseGuardianService(
        policy=configured_policy(make_test_repository(tmp_path)),
        pipeline_runner=pipeline_result,
    )
    workflow = ReleaseGuardianWorkflow(service)

    async def exercise_workflow():
        created = await workflow.handle("agent1user", "The user selected Create a QA plan.")
        assert created.card is not None
        created = await workflow.handle("agent1user", "The user selected Paste a feature requirement.")
        assert created.card is not None
        drafted = await workflow.handle(
            "agent1user", "The user said: A verified user can reset a password using an email link."
        )
        assert "Review this request" in drafted.text
        generated = await workflow.handle("agent1user", "The user selected Generate QA plan.")
        assert "Created" in generated.text

    asyncio.run(exercise_workflow())


def test_unavailable_configured_repository_is_not_offered_as_a_target(tmp_path):
    missing = tmp_path / "does-not-exist"
    service = ReleaseGuardianService(
        policy=ReleaseGuardianPolicy(
            enabled_target_ids=("configured_repository",),
            repository_path=str(missing),
        ),
        pipeline_runner=pipeline_result,
    )
    assert service.available_targets() == []
    with pytest.raises(ReleaseGuardianPolicyError, match="unavailable"):
        service.build_qa_plan(
            "A verified user can reset a password using an email link.",
            target_id="configured_repository",
        )


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


@pytest.mark.parametrize(
    "greeting",
    [
        "hii",
        "hiii!",
        "heyyy",
        "hellooo 👋",
        "@codebrain hii",
        "hiii @codebrain",
        "@agent1q2j6crzl0hvhq8vc3unxqr2t96jeytsqwyzjaw8hzqxppkcvc95nun37g6k hiii",
    ],
    ids=(
        "double-i",
        "triple-i-punctuation",
        "extended-hey",
        "extended-hello-emoji",
        "leading-handle",
        "trailing-handle",
        "address-handle",
    ),
)
def test_workflow_answers_casual_greeting_variants_without_starting_the_qa_pipeline(
    greeting,
):
    def fail_if_called(_requirements, _case_count):
        raise AssertionError("A casual greeting must not start the ASI:One QA pipeline")

    workflow = ReleaseGuardianWorkflow(
        ReleaseGuardianService(pipeline_runner=fail_if_called)
    )

    async def exercise_greeting():
        response = await workflow.handle("agent1user", greeting)
        assert "CodeBrain Release Guardian" in response.text
        assert response.card is not None

    asyncio.run(exercise_greeting())


@pytest.mark.parametrize(
    "planner_message",
    [
        'The user said: "hi"',
        "User message: hello",
        "The user wants to say hello to the agent.",
        'The user said: "hiii"',
        "User message: heyyy 👋",
        "The user wants to say hellooo to the agent.",
    ],
    ids=(
        "plain-hi",
        "plain-hello",
        "plain-agent-hello",
        "extended-hi",
        "extended-hey-emoji",
        "extended-agent-hello",
    ),
)
def test_workflow_answers_asi_one_planner_wrapped_greetings(planner_message):
    def fail_if_called(_requirements, _case_count):
        raise AssertionError("A planner-wrapped greeting must not start the QA pipeline")

    workflow = ReleaseGuardianWorkflow(
        ReleaseGuardianService(pipeline_runner=fail_if_called)
    )

    async def exercise_greeting():
        response = await workflow.handle("agent1user", planner_message)
        assert "CodeBrain Release Guardian" in response.text
        assert response.card is not None

    asyncio.run(exercise_greeting())


@pytest.mark.parametrize(
    "message",
    [
        "I have several repositories — can you run verification against multiple repos, or use a path I paste here?",
        "The agent restarted while I was reviewing. Do I need to resubmit the feature requirement?",
        "A verified user can reset a password using an email link.",
    ],
)
def test_home_never_treats_free_text_as_a_requirement(message):
    def fail_if_called(_requirements, _case_count):
        raise AssertionError("Home-screen text must not start the QA pipeline")

    workflow = ReleaseGuardianWorkflow(
        ReleaseGuardianService(pipeline_runner=fail_if_called)
    )

    async def exercise_message():
        response = await workflow.handle("agent1user", message)
        assert "not treated that message as a requirement" in response.text
        assert response.card is not None

    asyncio.run(exercise_message())


def test_guided_questions_build_a_preview_without_calling_asi_one():
    def fail_if_called(_requirements, _case_count):
        raise AssertionError("A draft preview must not call the QA pipeline")

    workflow = ReleaseGuardianWorkflow(
        ReleaseGuardianService(pipeline_runner=fail_if_called)
    )

    async def exercise_guided_entry():
        session = await workflow.sessions.get("agent1user")
        await workflow.handle(
            "agent1user", "",
            {"action": "home_selection", "choice": "create_qa_plan", "flow_id": session.flow_id},
        )
        session = await workflow.sessions.get("agent1user")
        await workflow.handle(
            "agent1user", "",
            {"action": "input_method_selection", "choice": "guided_questions", "flow_id": session.flow_id},
        )
        session = await workflow.sessions.get("agent1user")
        response = await workflow.handle(
            "agent1user", "",
            {
                "action": "submit_guided_requirement",
                "feature": "Password reset",
                "user": "Verified account holder",
                "success": "The account password is reset with an emailed link",
                "failure": "Expired links cannot be reused",
                "case_count": "3",
                "target": "none",
                "flow_id": session.flow_id,
            },
        )
        saved = await workflow.sessions.get("agent1user")
        assert "Review this request" in response.text
        assert saved.stage.value == "plan_preview"
        assert "Expired links cannot be reused" in saved.requirements

    asyncio.run(exercise_guided_entry())


def test_stale_or_wrong_stage_card_cannot_start_generation():
    def fail_if_called(_requirements, _case_count):
        raise AssertionError("A stale card must not start the QA pipeline")

    workflow = ReleaseGuardianWorkflow(
        ReleaseGuardianService(pipeline_runner=fail_if_called)
    )

    async def exercise_rejection():
        session = await workflow.sessions.get("agent1user")
        response = await workflow.handle(
            "agent1user", "",
            {"action": "generate_plan", "flow_id": session.flow_id},
        )
        assert "not treated that message as a requirement" in response.text
        response = await workflow.handle(
            "agent1user", "",
            {"action": "home_selection", "choice": "create_qa_plan", "flow_id": "stale"},
        )
        assert "not treated that message as a requirement" in response.text

    asyncio.run(exercise_rejection())


def test_legacy_text_card_selection_needs_the_current_flow_id():
    """Older ACP clients may relay a card selection JSON as chat text."""
    workflow = ReleaseGuardianWorkflow(
        ReleaseGuardianService(pipeline_runner=pipeline_result)
    )

    async def exercise_legacy_selection():
        session = await workflow.sessions.get("agent1user")
        response = await workflow.handle(
            "agent1user",
            '{"action":"home_selection","choice":"create_qa_plan","flow_id":"%s"}'
            % session.flow_id,
        )
        assert "Choose how" in response.text
        assert (await workflow.sessions.get("agent1user")).stage.value == "input_method"

        response = await workflow.handle(
            "agent1user",
            '{"action":"input_method_selection","choice":"paste_requirement","flow_id":"stale"}',
        )
        assert "Choose an input method" in response.text
        assert (await workflow.sessions.get("agent1user")).stage.value == "input_method"

    asyncio.run(exercise_legacy_selection())


def test_finishing_a_review_invalidates_old_card_flow_ids():
    workflow = ReleaseGuardianWorkflow(
        ReleaseGuardianService(pipeline_runner=pipeline_result)
    )

    async def exercise_completed_flow():
        await create_guided_plan(
            workflow,
            "agent1user",
            "A verified user can reset a password using an email link.",
        )
        reviewed = await workflow.sessions.get("agent1user")
        old_flow_id = reviewed.flow_id
        response = await workflow.handle(
            "agent1user",
            "",
            {"action": "review_selection", "choice": "finish", "flow_id": old_flow_id},
        )
        fresh = await workflow.sessions.get("agent1user")
        assert "QA review complete" in response.text
        assert fresh.flow_id != old_flow_id
        assert fresh.stage.value == "home"

        response = await workflow.handle(
            "agent1user",
            "",
            {
                "action": "home_selection",
                "choice": "create_qa_plan",
                "flow_id": old_flow_id,
            },
        )
        assert "not treated that message as a requirement" in response.text
        assert (await workflow.sessions.get("agent1user")).stage.value == "home"

    asyncio.run(exercise_completed_flow())


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
    assert agent._handle_messages_concurrently is False


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


def test_agent_factory_supports_loopback_acp_for_local_testing(monkeypatch):
    from agents.release_guardian.agent import create_release_guardian_agent

    monkeypatch.delenv("AGENTVERSE_PUBLIC_ENDPOINT", raising=False)
    monkeypatch.setenv("FETCH_AGENT_PORT", "8123")
    monkeypatch.setenv(
        "FETCH_AGENT_LOCAL_ENDPOINT", "http://127.0.0.1:8123/submit"
    )
    agent = create_release_guardian_agent(
        "local direct ACP verification seed", publish_manifest=False
    )
    assert agent.agent_type == "custom"
    assert [endpoint.url for endpoint in agent._endpoints] == [
        "http://127.0.0.1:8123/submit"
    ]


def test_agent_factory_routes_root_path_webhooks_to_submit(monkeypatch):
    from agents.release_guardian.agent import create_release_guardian_agent

    monkeypatch.delenv("AGENTVERSE_PUBLIC_ENDPOINT", raising=False)
    agent = create_release_guardian_agent(
        "root webhook compatibility verification seed", publish_manifest=False
    )
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    asyncio.run(
        agent._server(
            {
                "type": "http",
                "method": "GET",
                "path": "/",
                "headers": {b"user-agent": b"release-guardian-test"},
                "client": ("127.0.0.1", 0),
            },
            receive,
            send,
        )
    )
    assert sent[0]["status"] == 200


def test_agent_factory_rejects_non_loopback_local_endpoint(monkeypatch):
    from agents.release_guardian.agent import create_release_guardian_agent

    monkeypatch.delenv("AGENTVERSE_PUBLIC_ENDPOINT", raising=False)
    monkeypatch.setenv("FETCH_AGENT_PORT", "8000")
    monkeypatch.setenv(
        "FETCH_AGENT_LOCAL_ENDPOINT", "https://agent.example.com/submit"
    )
    with pytest.raises(ValueError, match="loopback"):
        create_release_guardian_agent("invalid local endpoint seed", publish_manifest=False)


def test_agentverse_registration_waits_until_the_local_listener_is_ready(monkeypatch):
    from agents.release_guardian.agent import create_release_guardian_agent

    monkeypatch.setenv("AGENTVERSE_V2_REGISTRATION_ENABLED", "true")
    monkeypatch.setenv("AGENTVERSE_API_KEY", "agentverse-api-key-for-test")
    monkeypatch.setenv("AGENTVERSE_PUBLIC_ENDPOINT", "https://agent.example.com/submit")
    agent = create_release_guardian_agent(
        "listener-ready verification seed", publish_manifest=False
    )
    agent._server._server = SimpleNamespace(started=True)
    with patch(
        "agents.release_guardian.agent.register_production_agentverse_profile",
        return_value=True,
    ) as register:
        asyncio.run(agent._on_startup[-1](None))
    register.assert_called_once_with("listener-ready verification seed")


def test_agentverse_registration_skips_when_listener_does_not_become_ready(monkeypatch):
    from agents.release_guardian.agent import create_release_guardian_agent

    monkeypatch.setenv("AGENTVERSE_V2_REGISTRATION_ENABLED", "true")
    monkeypatch.setenv("AGENTVERSE_API_KEY", "agentverse-api-key-for-test")
    monkeypatch.setenv("AGENTVERSE_PUBLIC_ENDPOINT", "https://agent.example.com/submit")
    monkeypatch.setenv("AGENTVERSE_LISTENER_WAIT_SECONDS", "0")
    agent = create_release_guardian_agent(
        "listener-not-ready verification seed", publish_manifest=False
    )
    with patch(
        "agents.release_guardian.agent.register_production_agentverse_profile"
    ) as register:
        asyncio.run(agent._on_startup[-1](None))
    register.assert_not_called()


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


def test_public_endpoint_must_use_the_acp_submit_route(monkeypatch):
    from agents.release_guardian.agent import register_production_agentverse_profile

    monkeypatch.setenv("AGENTVERSE_V2_REGISTRATION_ENABLED", "true")
    monkeypatch.setenv("AGENTVERSE_API_KEY", "agentverse-api-key-for-test")
    monkeypatch.setenv("AGENTVERSE_PUBLIC_ENDPOINT", "https://agent.example.com/status")
    with pytest.raises(ValueError, match="HTTPS /submit URL"):
        register_production_agentverse_profile("verification seed")

    monkeypatch.setenv("AGENTVERSE_PUBLIC_ENDPOINT", "https://127.0.0.1:8000/submit")
    with pytest.raises(
        ValueError, match="must not point to localhost or a private network address"
    ):
        register_production_agentverse_profile("verification seed")
