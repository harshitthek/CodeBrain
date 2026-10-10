import pytest
from apps.ai_agents.test_case_generator.prompts import TestCaseGeneratorPrompt as TCGenPrompt
from apps.ai_agents.test_case_reviewer.prompts import TestCaseReviewerPrompt as TCRevPrompt
from apps.ai_agents.prd_analyzer.prompts import PrdAnalyserPrompt
from apps.ai_agents.iface_case_generator.prompts import APITestCaseGeneratorPrompt
from apps.ai_agents.java_code_analyzer.prompts import JavaCodeAnalyzerPromptManager
from pathlib import Path


def test_test_case_generator_prompt():
    """Verify TestCaseGeneratorPrompt message formatting"""
    prompt_obj = TCGenPrompt()
    messages = prompt_obj.format_messages(
        requirements="User logs in with valid email and password",
        case_design_methods="Equivalence Partitioning",
        case_categories="Functional Testing",
        knowledge_context="Context info",
        case_count=5
    )
    assert len(messages) >= 2
    sys_content = messages[0].content
    assert "Test Case Generation Assistant" in sys_content or "test case" in sys_content.lower()

    human_content = messages[1].content
    assert "User logs in with valid email and password" in human_content
    assert "Equivalence Partitioning" in human_content
    assert "5" in human_content


def test_test_case_reviewer_prompt():
    """Verify TestCaseReviewerPrompt message formatting"""
    prompt_obj = TCRevPrompt()
    sample_case = {
        "title": "Login Test",
        "description": "User login test",
        "test_steps": "1. Enter username\n2. Enter password",
        "expected_results": "Login success"
    }
    messages = prompt_obj.format_messages(sample_case)
    assert len(messages) >= 2
    sys_content = messages[0].content
    assert "Test Case Reviewer" in sys_content or "review" in sys_content.lower()
    human_content = messages[1].content
    assert "User login test" in human_content


def test_prd_analyzer_prompt():
    """Verify PrdAnalyserPrompt message formatting"""
    prompt_obj = PrdAnalyserPrompt()
    prd_text = "### Requirement 1: User Profile Update\nUsers can change their display name."
    messages = prompt_obj.format_messages(markdown_content=prd_text)
    assert len(messages) >= 2
    sys_content = messages[0].content
    assert "PRD" in sys_content or "Product Requirement" in sys_content
    human_content = messages[1].content
    assert "User Profile Update" in human_content


def test_iface_case_generator_prompt():
    """Verify APITestCaseGeneratorPrompt message formatting"""
    prompt_obj = APITestCaseGeneratorPrompt()
    sample_api = {
        "path": "/api/v1/users",
        "method": "GET",
        "summary": "Get user list"
    }
    messages = prompt_obj.format_messages(
        api_info=sample_api,
        priority="P0",
        case_count=3,
        api_test_case_min_template="{}"
    )
    assert len(messages) >= 2
    sys_content = messages[0].content
    assert "API Test Case" in sys_content or "API" in sys_content
    human_content = messages[1].content
    assert "/api/v1/users" in human_content


def test_java_code_analyzer_prompt():
    """Verify JavaCodeAnalyzerPromptManager loading"""
    manager = JavaCodeAnalyzerPromptManager()
    sys_prompt = manager.get_system_prompt()
    assert sys_prompt is not None
    assert "Java" in sys_prompt or "java" in sys_prompt.lower()

    user_prompt = manager.get_user_prompt(
        repo_path="/test/repo",
        base_commit="abc1234",
        new_commit="def5678"
    )
    assert "/test/repo" in user_prompt
    assert "abc1234" in user_prompt
    assert "def5678" in user_prompt
