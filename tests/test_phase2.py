import ast
import json
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from django.test import RequestFactory

from apps.ai_agents.iface_case_generator.runner import APITestRunner
from apps.ai_agents.iface_case_generator.exporters import (
    generate_pytest_script,
    generate_postman_collection,
)
from apps.ai_agents.iface_case_generator.views import (
    execute_test_cases,
    export_pytest_view,
    export_postman_view,
)
from apps.llm.base import LLMServiceFactory
from apps.llm.deepseek import DeepSeekChatModel
from apps.llm.qwen import QwenChatModel
from langchain_openai import ChatOpenAI


SAMPLE_TEST_CASES = [
    {
        "name": "Get User Profile",
        "description": "Fetch user profile with valid authorization",
        "priority": "P0",
        "request": {
            "method": "GET",
            "path": "/api/v1/users/42",
            "headers": [{"name": "Authorization", "value": "Bearer token123"}],
            "query": [{"name": "details", "value": "full"}],
            "body": {}
        },
        "assertions": [
            {
                "expression": "code",
                "condition": "EQUALS",
                "expectedValue": 200
            },
            {
                "expression": "$.data.username",
                "condition": "EQUALS",
                "expectedValue": "alice"
            },
            {
                "expression": "$.data.role",
                "condition": "CONTAINS",
                "expectedValue": "admin"
            }
        ]
    },
    {
        "name": "Create Item Invalid Payload",
        "description": "Validation failure for missing required fields",
        "priority": "P1",
        "request": {
            "method": "POST",
            "path": "/api/v1/items",
            "headers": [{"name": "Content-Type", "value": "application/json"}],
            "body": {"name": ""}
        },
        "assertions": [
            {
                "expression": "status_code",
                "condition": "EQUALS",
                "expectedValue": 422
            },
            {
                "expression": "$.error.message",
                "condition": "NOT_NULL"
            }
        ]
    }
]


@pytest.mark.django_db
class TestPhase2Suite:

    def test_ssrf_safety_checks(self):
        """Runner must reject cloud metadata IP and invalid schemes."""
        runner = APITestRunner(base_url="http://169.254.169.254")
        assert runner._is_safe_target("http://169.254.169.254/latest/meta-data/") is False
        assert runner._is_safe_target_url("http://169.254.169.254/api") is False

        safe_runner = APITestRunner(base_url="https://api.example.com")
        assert safe_runner._is_safe_target("https://api.example.com/api/test") is True
        assert safe_runner._is_safe_target("ftp://api.example.com/api/test") is False

    def test_assertion_evaluator_operators(self):
        """Runner evaluates operators correctly."""
        runner = APITestRunner(base_url="http://127.0.0.1:8000")

        # EQUALS & NOT_EQUALS
        assert runner._evaluate_operator(200, "EQUALS", "200") is True
        assert runner._evaluate_operator("active", "EQUALS", "active") is True
        assert runner._evaluate_operator("active", "NOT_EQUALS", "inactive") is True

        # CONTAINS & NOT_CONTAINS
        assert runner._evaluate_operator("welcome admin user", "CONTAINS", "admin") is True
        assert runner._evaluate_operator(["admin", "editor"], "CONTAINS", "admin") is True
        assert runner._evaluate_operator("hello world", "NOT_CONTAINS", "admin") is True

        # GREATER_THAN & LESS_THAN
        assert runner._evaluate_operator(50, "GREATER_THAN", 20) is True
        assert runner._evaluate_operator(15, "LESS_THAN", 30) is True

        # IS_NULL & NOT_NULL
        assert runner._evaluate_operator(None, "IS_NULL", None) is True
        assert runner._evaluate_operator("data", "NOT_NULL", None) is True
        assert runner._evaluate_operator(None, "NOT_NULL", None) is False

        # REGEX_MATCH
        assert runner._evaluate_operator("user_12345", "REGEX_MATCH", r"^user_\d+$") is True
        assert runner._evaluate_operator("guest", "REGEX_MATCH", r"^user_\d+$") is False

    def test_jsonpath_extraction(self):
        """Runner extracts values with dot syntax and JSONPath expressions."""
        runner = APITestRunner(base_url="http://127.0.0.1:8000")
        payload = {
            "code": 200,
            "data": {
                "profile": {
                    "username": "alice",
                    "scores": [10, 20, 30]
                }
            }
        }

        assert runner._extract_jsonpath(payload, "code") == 200
        assert runner._extract_jsonpath(payload, "data.profile.username") == "alice"
        assert runner._extract_jsonpath(payload, "$.data.profile.scores[1]") == 20
        assert runner._extract_jsonpath(payload, "nonexistent.field") is None

    def test_execute_suite_with_mock_client(self):
        """Execute suite returns structured summary metrics and assertions."""
        runner = APITestRunner(base_url="http://127.0.0.1:8000")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {
            "code": 200,
            "data": {"username": "alice", "role": "super-admin"}
        }

        with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            summary = asyncio.run(runner.execute_suite(SAMPLE_TEST_CASES[:1]))

            assert summary["total_executed"] == 1
            assert summary["passed"] == 1
            assert summary["failed"] == 0
            assert summary["pass_rate"] == 100.0
            assert len(summary["results"]) == 1

            res = summary["results"][0]
            assert res["status"] == "PASSED"
            assert res["status_code"] == 200
            assert len(res["assertions"]) == 3
            assert all(a["passed"] for a in res["assertions"])

    def test_pytest_exporter_generates_valid_python(self):
        """Generated pytest script must be syntactically valid Python code."""
        code = generate_pytest_script(SAMPLE_TEST_CASES, base_url="https://api.example.com")
        assert "import pytest" in code
        assert "import httpx" in code
        assert "def test_1_get_user_profile():" in code
        assert "assert response.status_code == 200" in code

        # Verify python AST parses without syntax errors
        parsed = ast.parse(code)
        assert isinstance(parsed, ast.Module)

    def test_postman_exporter_structure(self):
        """Generated Postman collection conforms to v2.1.0 schema."""
        collection = generate_postman_collection(SAMPLE_TEST_CASES, base_url="https://api.example.com")
        assert "info" in collection
        assert collection["info"]["schema"] == "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        assert len(collection["item"]) == 2

        first_item = collection["item"][0]
        assert first_item["name"] == "Get User Profile"
        assert first_item["request"]["method"] == "GET"
        assert "event" in first_item
        assert len(first_item["event"]) > 0

        script_exec = first_item["event"][0]["script"]["exec"]
        assert any("pm.response.to.have.status(200)" in line for line in script_exec)

    def test_universal_llm_factory(self):
        """LLMServiceFactory creates DeepSeek, Qwen, and universal OpenAI-compatible models."""
        # DeepSeek
        ds_model = LLMServiceFactory.create("deepseek")
        assert isinstance(ds_model, DeepSeekChatModel)

        # Qwen
        qwen_model = LLMServiceFactory.create("qwen")
        assert isinstance(qwen_model, QwenChatModel)

        # OpenAI
        openai_model = LLMServiceFactory.create("openai")
        assert isinstance(openai_model, ChatOpenAI)
        assert openai_model.model_name == "gpt-4o-mini"

        # Ollama
        ollama_model = LLMServiceFactory.create("ollama")
        assert isinstance(ollama_model, ChatOpenAI)
        assert "11434" in str(ollama_model.openai_api_base)

        # Groq
        groq_model = LLMServiceFactory.create("groq")
        assert isinstance(groq_model, ChatOpenAI)
        assert "groq.com" in str(groq_model.openai_api_base)

        # Custom provider with runtime parameters
        custom_model = LLMServiceFactory.create(
            "custom-llm",
            model="custom-mistral-7b",
            base_url="http://my-vllm:8000/v1",
            api_key="token-custom"
        )
        assert isinstance(custom_model, ChatOpenAI)
        assert custom_model.model_name == "custom-mistral-7b"

    def test_api_execution_view_validation(self):
        """Execution view returns 400 for missing target base_url or cases."""
        rf = RequestFactory()

        # Missing base_url
        req1 = rf.post(
            "/iface_case_generator/api/execute/",
            data=json.dumps({"test_cases": SAMPLE_TEST_CASES}),
            content_type="application/json"
        )
        resp1 = execute_test_cases(req1)
        assert resp1.status_code == 400

        # Missing test_cases
        req2 = rf.post(
            "/iface_case_generator/api/execute/",
            data=json.dumps({"base_url": "http://127.0.0.1:8000"}),
            content_type="application/json"
        )
        resp2 = execute_test_cases(req2)
        assert resp2.status_code == 400

    def test_api_export_views(self):
        """Export views return downloadable files with correct content types."""
        rf = RequestFactory()

        # Pytest export
        req_pytest = rf.post(
            "/iface_case_generator/api/export-pytest/",
            data=json.dumps({
                "base_url": "http://127.0.0.1:8000",
                "test_cases": SAMPLE_TEST_CASES
            }),
            content_type="application/json"
        )
        resp_pytest = export_pytest_view(req_pytest)
        assert resp_pytest.status_code == 200
        assert resp_pytest["Content-Type"] == "text/x-python"
        assert b"import pytest" in resp_pytest.content

        # Postman export
        req_postman = rf.post(
            "/iface_case_generator/api/export-postman/",
            data=json.dumps({
                "base_url": "http://127.0.0.1:8000",
                "test_cases": SAMPLE_TEST_CASES
            }),
            content_type="application/json"
        )
        resp_postman = export_postman_view(req_postman)
        assert resp_postman.status_code == 200
        assert resp_postman["Content-Type"] == "application/json"
        parsed = json.loads(resp_postman.content.decode("utf-8"))
        assert "item" in parsed
