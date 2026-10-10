import pytest
import json
from apps.ai_agents.iface_case_generator.iface_test_case_parser import (
    clean_json_fence,
    parse_minimal_cases_or_raise,
    get_format_instructions,
)
from apps.ai_agents.iface_case_generator.iface_test_case_schema import (
    MinimalCase,
    MinimalRequestQueryParam,
    ResponseBodyAssertion,
    JsonPathAssertion,
    JsonPathAssertionItem,
)
from apps.ai_agents.iface_case_generator.iface_case_generator import APITestCaseGeneratorAgent


def test_clean_json_fence():
    """Verify clean_json_fence removes ```json code fences properly"""
    raw_fence = '```json\n{"name": "test"}\n```'
    assert clean_json_fence(raw_fence) == '{"name": "test"}'

    raw_plain = '{"name": "test"}'
    assert clean_json_fence(raw_plain) == '{"name": "test"}'


def test_parse_minimal_cases_or_raise():
    """Verify parsing valid minimal case JSON"""
    sample_json = json.dumps([
        {
            "name": "Verify successful login with valid credentials",
            "description": "Test user authentication flow",
            "request_body_json": {"username": "admin"},
            "assertion_condition": "EQUALS"
        }
    ])
    cases = parse_minimal_cases_or_raise(sample_json)
    assert len(cases) == 1
    assert cases[0].name == "Verify successful login with valid credentials"
    assert cases[0].description == "Test user authentication flow"
    assert cases[0].assertion_condition == "EQUALS"
    assert cases[0].request_body_json == {"username": "admin"}


def test_get_format_instructions():
    """Verify format instructions string"""
    instructions = get_format_instructions()
    assert isinstance(instructions, str)
    assert len(instructions) > 0


def test_has_request_parameters():
    """Verify APITestCaseGeneratorAgent._has_request_parameters logic"""
    agent = APITestCaseGeneratorAgent(llm_provider="deepseek")

    # Empty request
    assert agent._has_request_parameters({"request": {}}) is False

    # With query params
    api_with_query = {
        "request": {
            "query": [{"name": "page", "value": "1"}]
        }
    }
    assert agent._has_request_parameters(api_with_query) is True

    # With JSON body
    api_with_json_body = {
        "request": {
            "body": {
                "bodyType": "JSON",
                "jsonBody": {
                    "jsonValue": '{"username": "admin"}'
                }
            }
        }
    }
    assert agent._has_request_parameters(api_with_json_body) is True
