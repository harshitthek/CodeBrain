"""Runnable direct-ACP Agentverse agent for CodeBrain Release Guardian."""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from uagents import Agent, Context, Protocol
from uagents.asgi import ASGIServer
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    MetadataContent,
    TextContent,
    chat_protocol_spec,
)
from uagents_core.contrib.protocols.chat.cards import extract_card_response
from uagents_core.utils.registration import (
    AgentverseRequestError,
    RegistrationRequestCredentials,
    register_chat_agent,
)

from apps.release_guardian.service import ReleaseGuardianService

from .workflow import ReleaseGuardianWorkflow

AGENT_NAME = "codebrain-release-guardian"
AGENTVERSE_PROFILE_NAME = "CodeBrain"
AGENTVERSE_METADATA = {
    "categories": ["developer-tools"],
    "tags": ["quality-assurance", "test-planning", "release-readiness"],
}
AGENT_DESCRIPTION = (
    "Turns product requirements into Actor-Critic QA plans and, after explicit approval, "
    "runs a policy-gated pytest verification in one operator-configured release repository."
)
logger = logging.getLogger(__name__)


class _SubmitCompatibleASGIServer(ASGIServer):
    """Accept a root-path webhook while keeping `/submit` as the canonical ACP route."""

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http" and scope.get("path") in {"", "/"}:
            scope = {**scope, "path": "/submit"}
        await super().__call__(scope, receive, send)


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _public_endpoint(value: str) -> str:
    """Validate and normalize the public HTTPS endpoint required by Agentverse's v2 API."""
    endpoint = value.strip().rstrip("/")
    if not endpoint.endswith("/submit"):
        endpoint = f"{endpoint}/submit"
    parsed = urlparse(endpoint)
    hostname = parsed.hostname
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or not hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.params
        or parsed.path != "/submit"
    ):
        raise ValueError(
            "AGENTVERSE_PUBLIC_ENDPOINT must be a public HTTPS /submit URL without credentials or query data."
        )

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if (
        hostname.lower() == "localhost"
        or hostname.lower().endswith(".local")
        or (address is not None and not address.is_global)
    ):
        raise ValueError(
            "AGENTVERSE_PUBLIC_ENDPOINT must not point to localhost or a private network address."
        )
    return endpoint


def _local_endpoint(port: int) -> str | None:
    """Validate the optional loopback ACP endpoint used for local testing."""
    configured = os.getenv("FETCH_AGENT_LOCAL_ENDPOINT", "").strip()
    if not configured:
        return None
    parsed = urlparse(configured)
    hostname = parsed.hostname
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or not hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.params
        or parsed.path != "/submit"
        or parsed.port != port
    ):
        raise ValueError(
            "FETCH_AGENT_LOCAL_ENDPOINT must be an HTTP(S) loopback /submit URL "
            "on FETCH_AGENT_PORT, without credentials or query data."
        )
    try:
        is_loopback = ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        is_loopback = hostname.lower() == "localhost"
    if not is_loopback:
        raise ValueError(
            "FETCH_AGENT_LOCAL_ENDPOINT must point to localhost or a loopback IP address."
        )
    return configured


def _runtime_endpoint(port: int) -> str | None:
    """Return public ACP transport or, for local use, an explicit loopback route."""
    configured = os.getenv("AGENTVERSE_PUBLIC_ENDPOINT", "").strip()
    return _public_endpoint(configured) if configured else _local_endpoint(port)


def register_production_agentverse_profile(seed: str) -> bool:
    """Optionally register the deployed chat agent through Agentverse's v2 API."""
    registration = _agentverse_registration_settings()
    if registration is None:
        return False
    api_key, endpoint = registration

    try:
        registered = register_chat_agent(
            name=AGENTVERSE_PROFILE_NAME,
            endpoint=endpoint,
            active=True,
            credentials=RegistrationRequestCredentials(
                agentverse_api_key=api_key,
                agent_seed_phrase=seed,
            ),
            description=AGENT_DESCRIPTION,
            readme=Path(__file__).with_name("README.md").read_text(encoding="utf-8"),
            starter_prompts=[
                "Create a focused QA plan from these acceptance criteria.",
                "Review this release requirement for boundary and exception coverage.",
            ],
            metadata={**AGENTVERSE_METADATA, "is_public": "True"},
        )
    except (AgentverseRequestError, OSError, RuntimeError) as error:
        logger.warning(
            "Agentverse v2 registration did not complete (%s); continuing with the configured ACP runtime.",
            error,
        )
        return False
    return bool(registered)


def _agentverse_registration_settings() -> tuple[str, str] | None:
    """Return validated opt-in registration settings without exposing secrets."""
    if not _env_bool("AGENTVERSE_V2_REGISTRATION_ENABLED"):
        return None
    api_key = (
        os.getenv("AGENTVERSE_API_KEY") or os.getenv("AGENTVERSE_KEY") or ""
    ).strip()
    endpoint_value = os.getenv("AGENTVERSE_PUBLIC_ENDPOINT", "")
    if not api_key or not endpoint_value.strip():
        raise ValueError(
            "Set AGENTVERSE_API_KEY (or AGENTVERSE_KEY) and AGENTVERSE_PUBLIC_ENDPOINT "
            "before enabling AGENTVERSE_V2_REGISTRATION_ENABLED."
        )
    return api_key, _public_endpoint(endpoint_value)


def configure_django() -> None:
    """Initialise project settings without starting optional vector/RAG infrastructure."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    os.environ["CODEBRAIN_KNOWLEDGE_ENABLED"] = "false"
    import django

    django.setup()


def create_release_guardian_agent(
    seed: str,
    workflow: ReleaseGuardianWorkflow | None = None,
    publish_manifest: bool = True,
) -> Agent:
    """Build the ACP agent; public deployments use the configured direct HTTPS endpoint."""
    if not seed.strip():
        raise ValueError("FETCH_AGENT_SEED must not be empty.")

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    port = int(os.getenv("FETCH_AGENT_PORT", "8000"))
    endpoint = _runtime_endpoint(port)
    agent = Agent(
        name=AGENT_NAME,
        port=port,
        seed=seed,
        endpoint=endpoint,
        mailbox=endpoint is None,
        publish_agent_details=True,
        description=AGENT_DESCRIPTION,
        metadata=AGENTVERSE_METADATA,
        readme_path=str(Path(__file__).with_name("README.md")),
        loop=loop,
        handle_messages_concurrently=True,
    )

    # Special methods are resolved on the class, so use a small ASGI subclass
    # rather than assigning ``__call__`` on the server instance.
    agent._server = _SubmitCompatibleASGIServer(
        port=port,
        loop=loop,
        queries=agent._queries,
        logger=agent._logger,
    )

    protocol = Protocol(spec=chat_protocol_spec)
    guardian = workflow or ReleaseGuardianWorkflow(ReleaseGuardianService())

    @agent.on_event("startup")
    async def register_after_listener_starts(_ctx: Context) -> None:
        """Register only after the uAgent listener has been brought online.

        Agentverse evaluates the registered public endpoint. uAgents schedules
        startup callbacks before its Uvicorn coroutine gets a chance to bind,
        so wait for the listener and run blocking registration off the event
        loop before advertising the endpoint.
        """
        if not _env_bool("AGENTVERSE_V2_REGISTRATION_ENABLED"):
            return
        wait_seconds = float(os.getenv("AGENTVERSE_LISTENER_WAIT_SECONDS", "10"))
        deadline = asyncio.get_running_loop().time() + max(wait_seconds, 0)
        while True:
            server = agent._server.server
            if server is not None and server.started:
                break
            if asyncio.get_running_loop().time() >= deadline:
                logger.error(
                    "Agentverse registration skipped because the local ACP listener did not become ready."
                )
                return
            await asyncio.sleep(0.1)
        try:
            registered = await asyncio.to_thread(register_production_agentverse_profile, seed)
        except ValueError as error:
            logger.error("Agentverse registration configuration is invalid: %s", error)
            return
        if registered:
            logger.info("Agentverse v2 profile registration completed.")

    @protocol.on_message(ChatAcknowledgement)
    async def acknowledge_chat_response(
        ctx: Context, sender: str, _msg: ChatAcknowledgement
    ) -> None:
        ctx.logger.debug("Chat acknowledgement received from %s", sender)

    @protocol.on_message(ChatMessage)
    async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage) -> None:
        await ctx.send(sender, ChatAcknowledgement(acknowledged_msg_id=msg.msg_id))
        selection = None
        cancelled = False
        for content in msg.content:
            if isinstance(content, MetadataContent):
                card_response = extract_card_response(content)
                if card_response:
                    selection = card_response.selection
                    cancelled = card_response.cancelled
                    break
        response = await guardian.handle(
            sender, msg.text().strip(), selection, cancelled
        )
        content = [TextContent(response.text)]
        if response.card is not None:
            content.append(response.card)
        await ctx.send(sender, ChatMessage(content=content))

    agent.include(protocol, publish_manifest=publish_manifest)
    return agent


def main() -> None:
    load_dotenv()
    seed = os.getenv("FETCH_AGENT_SEED", "").strip()
    if not seed:
        raise SystemExit(
            "FETCH_AGENT_SEED is required. Generate a private seed and keep it out of version control."
        )
    configure_django()
    try:
        _agentverse_registration_settings()
    except ValueError as error:
        raise SystemExit(str(error)) from error
    agent = create_release_guardian_agent(seed, publish_manifest=True)
    print(f"{AGENT_NAME} address: {agent.address}")
    agent.run()


if __name__ == "__main__":
    main()
