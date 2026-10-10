import json
import zipfile
import io
import asyncio
import xml.etree.ElementTree as ET
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from django.test import RequestFactory
from django.core.management import call_command, CommandError

from apps.ai_agents.common.orchestrator import ActorCriticReflectionEngine
from apps.core.exporters import (
    JiraExporter,
    TestRailExporter,
    XMindExporter,
    JUnitExporter,
)
from apps.core.views import pipeline_view, pipeline_export_tms


SAMPLE_TEST_CASES = [
    {
        "id": "TC-001",
        "title": "Verify user authentication with valid token",
        "description": "User passes valid bearer token and receives 200 OK with profile",
        "priority": "P0",
        "preconditions": "Active user registered in database",
        "test_steps": [
            "Send POST /api/v1/auth/login with credentials",
            "Extract authorization bearer token",
            "Send GET /api/v1/user/profile with header Authorization: Bearer <token>"
        ],
        "expected_results": [
            "Status code 200 with auth token returned",
            "Token is non-empty string",
            "Profile data contains matching username"
        ]
    },
    {
        "id": "TC-002",
        "title": "Reject authentication with expired token",
        "description": "User passes expired token and receives 401 Unauthorized",
        "priority": "P1",
        "preconditions": "Expired token generated",
        "test_steps": [
            "Send GET /api/v1/user/profile with expired token header"
        ],
        "expected_results": [
            "Status code 401 Unauthorized returned with error code TOKEN_EXPIRED"
        ]
    }
]


class TestPhase4Suite:
    """Comprehensive test suite for Phase 4 multi-agent orchestration and enterprise sync."""

    # -------------------------------------------------------------------------
    # 1. Actor-Critic Reflection Engine
    # -------------------------------------------------------------------------
    def test_actor_critic_convergence(self):
        """Actor-Critic reflection engine converges early when quality threshold is met."""
        mock_generator = MagicMock()
        mock_generator.generate.return_value = SAMPLE_TEST_CASES

        mock_reviewer = MagicMock()
        # Returns score 90 (>= 85 threshold)
        mock_reviewer.review.return_value = MagicMock(
            content=json.dumps({
                "score": 9.0,
                "strengths": ["Clear steps"],
                "weaknesses": [],
                "suggestions": []
            })
        )

        engine = ActorCriticReflectionEngine(
            generator_agent=mock_generator,
            reviewer_agent=mock_reviewer,
            min_score=85.0,
            max_iterations=2
        )
        result = engine.run("Test user authentication requirements")

        assert result["success"] is True
        assert result["converged"] is True
        assert result["iterations_run"] == 1
        assert result["final_score"] == 90.0
        assert len(result["final_cases"]) == 2

    def test_actor_critic_strict_termination_bound(self):
        """Actor-Critic engine terminates strictly at max_iterations=2 even if score remains low."""
        mock_generator = MagicMock()
        mock_generator.generate.return_value = SAMPLE_TEST_CASES

        mock_reviewer = MagicMock()
        # Returns low score 65 across all calls
        mock_reviewer.review.return_value = MagicMock(
            content=json.dumps({
                "score": 6.5,
                "strengths": [],
                "weaknesses": ["Missing error scenarios"],
                "suggestions": ["Add 4xx checks"]
            })
        )

        engine = ActorCriticReflectionEngine(
            generator_agent=mock_generator,
            reviewer_agent=mock_reviewer,
            min_score=85.0,
            max_iterations=5  # Engine must clamp max_iterations to 2
        )
        assert engine.max_iterations == 2

        result = engine.run("Requirements with edge cases")
        assert result["success"] is True
        assert result["converged"] is False
        assert result["iterations_run"] == 2
        assert len(result["history"]) == 2

    def test_actor_critic_monotonic_regression_safeguard(self):
        """Engine reverts to best-scoring iteration if iteration 2 regresses in quality."""
        suite_iter1 = [SAMPLE_TEST_CASES[0]]
        suite_iter2 = [SAMPLE_TEST_CASES[1]]

        mock_generator = MagicMock()
        # First call returns suite_iter1, second call returns suite_iter2
        mock_generator.generate.side_effect = [suite_iter1, suite_iter2]

        mock_reviewer = MagicMock()
        # Iteration 1 scores 80.0, Iteration 2 drops to 70.0
        rev1 = MagicMock(content=json.dumps({"score": 8.0}))
        rev2 = MagicMock(content=json.dumps({"score": 7.0}))
        mock_reviewer.review.side_effect = [rev1, rev2]

        engine = ActorCriticReflectionEngine(
            generator_agent=mock_generator,
            reviewer_agent=mock_reviewer,
            min_score=85.0,
            max_iterations=2
        )
        result = engine.run("Authentication specification")

        assert result["success"] is True
        assert result["final_score"] == 80.0
        # Final cases must be from iteration 1 (best score), preventing regression
        assert result["final_cases"] == suite_iter1

    # -------------------------------------------------------------------------
    # 2. Jira Exporter
    # -------------------------------------------------------------------------
    def test_jira_exporter_formatting(self):
        """JiraExporter formats issues with project key, priority mapping, and formatted description."""
        exporter = JiraExporter(project_key="AUTH", issue_type="Test")
        payload = exporter.format_issue(SAMPLE_TEST_CASES[0])

        assert "fields" in payload
        fields = payload["fields"]
        assert fields["project"]["key"] == "AUTH"
        assert fields["issuetype"]["name"] == "Test"
        assert fields["priority"]["name"] == "Highest"  # P0 -> Highest
        assert "Verify user authentication" in fields["summary"]
        assert "*Test Steps:*" in fields["description"]
        assert "*Expected Results:*" in fields["description"]
        assert "CodeBrain" in fields["labels"]

    def test_jira_sync_mock(self):
        """JiraExporter syncs issues idempotently to Jira REST API."""
        exporter = JiraExporter(project_key="AUTH")

        mock_ping = MagicMock(status_code=200)
        mock_post = MagicMock(
            status_code=201,
            json=lambda: {"id": "10001", "key": "AUTH-42"}
        )

        with patch("httpx.Client.get", return_value=mock_ping):
            with patch("httpx.Client.post", return_value=mock_post):
                res = exporter.sync_to_jira(
                    SAMPLE_TEST_CASES[:1],
                    jira_base_url="https://jira.example.com",
                    auth_email="qa@example.com",
                    api_token="secret-token"
                )
                assert res["success"] is True
                assert res["created_count"] == 1
                assert res["created_issues"][0]["key"] == "AUTH-42"

    # -------------------------------------------------------------------------
    # 3. TestRail Exporter
    # -------------------------------------------------------------------------
    def test_testrail_exporter_formatting(self):
        """TestRailExporter structures steps and expected assertions into separated items."""
        exporter = TestRailExporter(section_id=105)
        case_data = exporter.format_case(SAMPLE_TEST_CASES[0])

        assert case_data["title"] == SAMPLE_TEST_CASES[0]["title"]
        assert case_data["template_id"] == 2  # Separated steps
        assert case_data["priority_id"] == 4  # P0 -> Critical (4)
        assert len(case_data["custom_steps_separated"]) == 3
        assert case_data["custom_steps_separated"][0]["content"] == "Send POST /api/v1/auth/login with credentials"
        assert case_data["custom_steps_separated"][0]["expected"] == "Status code 200 with auth token returned"

    # -------------------------------------------------------------------------
    # 4. XMind MindMap Exporter
    # -------------------------------------------------------------------------
    def test_xmind_exporter_archive_and_markdown(self):
        """XMindExporter produces valid ZIP archives and hierarchical markdown mindmaps."""
        exporter = XMindExporter(root_title="Authentication Suite")

        # 1. Test markdown outline
        md = exporter.generate_markdown_mindmap(SAMPLE_TEST_CASES)
        assert "# Authentication Suite" in md
        assert "## Priority P0" in md
        assert "## Priority P1" in md
        assert "- **Steps**" in md

        # 2. Test valid ZIP archive
        archive_bytes = exporter.generate_xmind_archive(SAMPLE_TEST_CASES)
        assert isinstance(archive_bytes, bytes)
        assert len(archive_bytes) > 0

        # Unpack zip and verify contents
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as z:
            names = z.namelist()
            assert "content.json" in names
            assert "metadata.json" in names
            assert "manifest.json" in names

            content_raw = z.read("content.json").decode("utf-8")
            content_json = json.loads(content_raw)
            assert isinstance(content_json, list)
            root_topic = content_json[0]["rootTopic"]
            assert root_topic["title"] == "Authentication Suite"
            assert "children" in root_topic
            assert len(root_topic["children"]["attached"]) >= 2

    # -------------------------------------------------------------------------
    # 5. JUnit XML Exporter
    # -------------------------------------------------------------------------
    def test_junit_xml_exporter_generation(self):
        """JUnitExporter produces standard parsable JUnit XML with test and failure counts."""
        exporter = JUnitExporter(suite_name="Auth API Integration Tests")
        mock_results = [
            {
                "case_id": "TC-001",
                "name": "User Login Success",
                "method": "POST",
                "passed": True,
                "status_code": 200,
                "latency_ms": 142.5
            },
            {
                "case_id": "TC-002",
                "name": "Invalid Password Rejection",
                "method": "POST",
                "passed": False,
                "status_code": 500,
                "latency_ms": 320.0,
                "error": "Expected 401 Unauthorized but received 500 Internal Server Error",
                "assertions": [
                    {"expression": "code", "expected": 401, "actual": 500, "passed": False}
                ]
            }
        ]

        xml_output = exporter.generate_junit_xml(mock_results)
        assert "<?xml version=" in xml_output

        # Parse with standard XML ElementTree to confirm well-formed XML
        root = ET.fromstring(xml_output)
        assert root.tag == "testsuites"
        assert root.attrib["tests"] == "2"
        assert root.attrib["failures"] == "1"

        testcases = root.findall(".//testcase")
        assert len(testcases) == 2
        assert testcases[0].attrib["name"] == "User Login Success"
        assert testcases[1].attrib["name"] == "Invalid Password Rejection"
        assert len(testcases[1].findall("failure")) == 1

    # -------------------------------------------------------------------------
    # 6. Headless CI/CD Command-Line Runner
    # -------------------------------------------------------------------------
    def test_run_test_suite_command_success(self, tmp_path):
        """run_test_suite management command runs successfully and emits JUnit XML."""
        spec_file = tmp_path / "mock_spec.json"
        spec_content = {
            "apiDefinitions": [
                {
                    "name": "Health Check",
                    "path": "/health",
                    "method": "GET",
                    "request": {},
                    "apiTestCaseList": [
                        {
                            "name": "Get Health Status",
                            "path": "/health",
                            "method": "GET",
                            "assertions": [{"expression": "code", "condition": "EQUALS", "expectedValue": 200}]
                        }
                    ]
                }
            ]
        }
        spec_file.write_text(json.dumps(spec_content), encoding="utf-8")
        junit_output = tmp_path / "test-results.xml"

        mock_summary = {
            "total": 1,
            "passed": 1,
            "failed": 0,
            "pass_rate": 100.0,
            "total_duration_ms": 50.0,
            "results": [
                {
                    "case_id": "TC-1",
                    "name": "Get Health Status",
                    "method": "GET",
                    "passed": True,
                    "status": "PASSED",
                    "latency_ms": 50.0
                }
            ]
        }

        with patch("apps.ai_agents.iface_case_generator.runner.APITestRunner.execute_suite", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_summary
            with patch("apps.ai_agents.iface_case_generator.runner.APITestRunner._is_safe_target", return_value=True):
                call_command(
                    'run_test_suite',
                    spec_file=str(spec_file),
                    base_url='https://api.example.com',
                    output_junit=str(junit_output),
                    min_pass_rate=100.0
                )

        assert junit_output.exists()
        xml_content = junit_output.read_text(encoding="utf-8")
        assert "<testsuites" in xml_content

    def test_run_test_suite_command_failure_gate(self, tmp_path):
        """run_test_suite raises CommandError when failure rate exceeds threshold."""
        spec_file = tmp_path / "fail_spec.json"
        spec_content = {
            "apiDefinitions": [
                {
                    "name": "Failing Endpoint",
                    "path": "/api/fail",
                    "method": "POST",
                    "apiTestCaseList": [
                        {"name": "Fail Test", "path": "/api/fail", "method": "POST"}
                    ]
                }
            ]
        }
        spec_file.write_text(json.dumps(spec_content), encoding="utf-8")

        mock_summary = {
            "total": 1,
            "passed": 0,
            "failed": 1,
            "pass_rate": 0.0,
            "total_duration_ms": 120.0,
            "results": [
                {
                    "case_id": "TC-F",
                    "name": "Fail Test",
                    "method": "POST",
                    "passed": False,
                    "status": "FAILED",
                    "latency_ms": 120.0,
                    "error": "Connection timed out"
                }
            ]
        }

        with patch("apps.ai_agents.iface_case_generator.runner.APITestRunner.execute_suite", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_summary
            with patch("apps.ai_agents.iface_case_generator.runner.APITestRunner._is_safe_target", return_value=True):
                with pytest.raises(CommandError) as exc_info:
                    call_command(
                        'run_test_suite',
                        spec_file=str(spec_file),
                        base_url='https://api.example.com',
                        min_pass_rate=100.0
                    )
                assert "Test suite failed quality gate" in str(exc_info.value)

    # -------------------------------------------------------------------------
    # 7. Pipeline View & TMS API Endpoints
    # -------------------------------------------------------------------------
    def test_pipeline_view_and_export_api(self):
        """Pipeline views render correctly and export endpoints return expected payloads."""
        factory = RequestFactory()

        # 1. Pipeline view rendering
        req_view = factory.get('/pipeline/')
        resp_view = pipeline_view(req_view)
        assert resp_view.status_code == 200

        # 2. Jira export endpoint
        req_jira = factory.post(
            '/pipeline/export/',
            data=json.dumps({"target": "jira", "test_cases": SAMPLE_TEST_CASES, "project_key": "PAY"}),
            content_type='application/json'
        )
        resp_jira = pipeline_export_tms(req_jira)
        assert resp_jira.status_code == 200
        jira_data = json.loads(resp_jira.content)
        assert jira_data["success"] is True
        assert "PAY_jira_issues.json" in jira_data["filename"]

        # 3. XMind export endpoint
        req_xmind = factory.post(
            '/pipeline/export/',
            data=json.dumps({"target": "xmind", "test_cases": SAMPLE_TEST_CASES, "project_key": "PAY"}),
            content_type='application/json'
        )
        resp_xmind = pipeline_export_tms(req_xmind)
        assert resp_xmind.status_code == 200
        assert resp_xmind["Content-Type"] == "application/vnd.xmind.workbook"
        assert len(resp_xmind.content) > 0
