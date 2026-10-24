"""Tests for Release Guardian's non-mutating deployment preflight."""

from __future__ import annotations

import urllib.error
from unittest.mock import patch

from agents.release_guardian import preflight


def _configure_agentverse_environment(monkeypatch):
    monkeypatch.setenv("AGENTVERSE_V2_REGISTRATION_ENABLED", "true")
    monkeypatch.setenv("AGENTVERSE_API_KEY", "test-agentverse-key")
    monkeypatch.setenv("AGENTVERSE_PUBLIC_ENDPOINT", "https://agent.example.com/submit")
    monkeypatch.setenv("FETCH_AGENT_SEED", "release guardian preflight test seed")


def test_agentverse_api_preflight_accepts_a_missing_profile_after_authentication(monkeypatch):
    _configure_agentverse_environment(monkeypatch)
    error = urllib.error.HTTPError(
        "https://agentverse.ai/v2/agents/test", 404, "Not Found", {}, None
    )
    with patch("urllib.request.urlopen", side_effect=error):
        check = preflight._check_agentverse_api()

    assert check.passed is True
    assert "not registered" in check.detail


def test_agentverse_api_preflight_reports_rejected_credentials(monkeypatch):
    _configure_agentverse_environment(monkeypatch)
    error = urllib.error.HTTPError(
        "https://agentverse.ai/v2/agents/test", 403, "Forbidden", {}, None
    )
    with patch("urllib.request.urlopen", side_effect=error):
        check = preflight._check_agentverse_api()

    assert check.passed is False
    assert check.detail == "rejected (HTTP 403)"
