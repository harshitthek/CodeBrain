"""Non-mutating local and deployment readiness checks for Release Guardian.

Run with ``python -m agents.release_guardian.preflight`` before a local demo.
Use ``--deployment --check-public-endpoint`` on the host that will run the
public uAgent. The checker never calls ASI:One, registers an agent, executes
pytest, or prints secret values.
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str
    required: bool = True


def _configured(name: str) -> bool:
    value = os.getenv(name, "").strip()
    return bool(value) and not any(
        marker in value.casefold()
        for marker in ("replace-with", "your-public-domain", "/absolute/path")
    )


def _readiness_checks(deployment: bool) -> list[Check]:
    checks: list[Check] = []
    supported = (3, 10) <= sys.version_info[:2] <= (3, 13)
    checks.append(
        Check(
            "Python version",
            supported,
            f"{sys.version_info.major}.{sys.version_info.minor} "
            "(Fetch supports Python 3.10-3.13)",
        )
    )

    try:
        from uagents_core.contrib.protocols.chat import chat_protocol_spec

        protocol_ok = (
            chat_protocol_spec.name == "AgentChatProtocol"
            and chat_protocol_spec.version == "0.3.0"
        )
        checks.append(
            Check(
                "ACP runtime",
                protocol_ok,
                f"{chat_protocol_spec.name} {chat_protocol_spec.version}",
            )
        )
    except ImportError:
        checks.append(
            Check(
                "ACP runtime",
                False,
                "Install requirements-agent.txt in this virtual environment.",
            )
        )

    for name in ("DJANGO_SECRET_KEY", "FETCH_AGENT_SEED", "ASI1_API_KEY"):
        checks.append(Check(name, _configured(name), "configured" if _configured(name) else "missing"))

    debug = os.getenv("DJANGO_DEBUG", "false").strip().lower() in {"1", "true", "yes", "on"}
    checks.append(
        Check(
            "DJANGO_DEBUG",
            not debug if deployment else True,
            "must be false for public deployment" if debug else "disabled",
            required=deployment,
        )
    )

    repo_path = os.getenv("RELEASE_GUARDIAN_REPO_PATH", "").strip()
    if repo_path:
        repo = Path(repo_path).expanduser()
        checks.append(
            Check(
                "Configured repository",
                repo.is_absolute() and repo.is_dir() and (repo / ".git").exists(),
                "available Git repository" if repo.is_dir() and (repo / ".git").exists() else "must be an available absolute Git repository",
                required=False,
            )
        )
    else:
        checks.append(Check("Configured repository", True, "not configured; QA-plan-only mode", required=False))

    local_endpoint = os.getenv("FETCH_AGENT_LOCAL_ENDPOINT", "").strip()
    if local_endpoint and not os.getenv("AGENTVERSE_PUBLIC_ENDPOINT", "").strip():
        try:
            from .agent import _local_endpoint

            port = int(os.getenv("FETCH_AGENT_PORT", "8000"))
            endpoint = _local_endpoint(port)
            checks.append(
                Check("Local ACP endpoint", endpoint is not None, endpoint or "not configured")
            )
        except (ValueError, TypeError) as error:
            checks.append(Check("Local ACP endpoint", False, str(error)))

    if deployment:
        from .agent import _agentverse_registration_settings

        try:
            registration = _agentverse_registration_settings()
            endpoint = registration[1] if registration else ""
            checks.append(
                Check(
                    "Agentverse registration",
                    registration is not None,
                    f"enabled for {endpoint}" if registration else "disabled; mailbox-only mode",
                    required=False,
                )
            )
        except ValueError as error:
            checks.append(Check("Agentverse registration", False, str(error)))
    return checks


def _check_public_endpoint() -> Check:
    endpoint = os.getenv("AGENTVERSE_PUBLIC_ENDPOINT", "").strip()
    if not endpoint:
        return Check("Public ACP endpoint", False, "AGENTVERSE_PUBLIC_ENDPOINT is missing")
    try:
        with urllib.request.urlopen(endpoint, timeout=10) as response:  # noqa: S310 - operator-configured HTTPS endpoint.
            return Check(
                "Public ACP endpoint",
                200 <= response.status < 300,
                f"HTTP {response.status}",
            )
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        return Check("Public ACP endpoint", False, f"unreachable: {type(error).__name__}")


def _check_agentverse_api() -> Check:
    """Verify credential acceptance without creating or changing an Agentverse profile."""
    try:
        from uagents_core.config import AgentverseConfig
        from uagents_core.identity import Identity

        from .agent import _agentverse_registration_settings

        registration = _agentverse_registration_settings()
        if registration is None:
            return Check("Agentverse API credentials", False, "registration is disabled")
        api_key, _endpoint = registration
        seed = os.getenv("FETCH_AGENT_SEED", "").strip()
        if not seed:
            return Check("Agentverse API credentials", False, "FETCH_AGENT_SEED is missing")
        address = Identity.from_seed(seed, 0).address
        request = urllib.request.Request(
            f"{AgentverseConfig().agents_api}/{address}",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310 - fixed Agentverse API URL.
            return Check("Agentverse API credentials", response.status < 300, f"HTTP {response.status}")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return Check(
                "Agentverse API credentials",
                True,
                "authenticated; this agent profile is not registered yet",
            )
        return Check("Agentverse API credentials", False, f"rejected (HTTP {error.code})")
    except (ImportError, OSError, TimeoutError, ValueError) as error:
        return Check(
            "Agentverse API credentials",
            False,
            f"unavailable: {type(error).__name__}",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deployment", action="store_true", help="enforce public deployment settings")
    parser.add_argument(
        "--check-public-endpoint",
        action="store_true",
        help="perform a GET health check against the configured public endpoint",
    )
    parser.add_argument(
        "--check-agentverse-api",
        action="store_true",
        help="perform a read-only authenticated Agentverse API check",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env")
    checks = _readiness_checks(args.deployment)
    if args.check_public_endpoint:
        checks.append(_check_public_endpoint())
    if args.check_agentverse_api:
        checks.append(_check_agentverse_api())

    for check in checks:
        label = "PASS" if check.passed else ("WARN" if not check.required else "FAIL")
        print(f"{label:4} {check.name}: {check.detail}")
    failed = [check for check in checks if check.required and not check.passed]
    print("READY" if not failed else f"NOT READY: {len(failed)} required check(s) failed")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
