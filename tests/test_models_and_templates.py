import pytest
from django.template.loader import render_to_string
from apps.core.models import TestCase as TestCaseModel, TestCaseReview as TestCaseReviewModel, KnowledgeBase
from apps.core.forms import TestCaseForm, TestCaseReviewForm, KnowledgeBaseForm


def test_model_choices():
    """Verify translated model choices retain DB keys while providing English labels"""
    # TestCase status choices
    status_dict = dict(TestCaseModel.STATUS_CHOICES)
    assert status_dict['pending'] == 'Pending Review'
    assert status_dict['approved'] == 'Approved'
    assert status_dict['rejected'] == 'Rejected'

    # TestCase bu choices
    bu_dict = dict(TestCaseModel.BU_CHOICES)
    assert bu_dict['education'] == 'Education'
    assert bu_dict['ai_application'] == 'AI Application'

    # TestCase priority choices
    priority_dict = dict(TestCaseModel.PRIORITY_CHOICES)
    assert priority_dict['p0'] == 'P0'
    assert priority_dict['p1'] == 'P1'

    # TestCase string representation
    tc = TestCaseModel(
        description="Verify user authentication",
        test_steps="1. Enter credentials\n2. Submit",
        expected_results="Dashboard displayed"
    )
    s = str(tc)
    assert "Verify user authentication" in s
    assert "Dashboard displayed" in s


def test_form_fields():
    """Verify TestCaseForm and TestCaseReviewForm field labels and widgets"""
    tc_form = TestCaseForm()
    assert 'title' in tc_form.fields
    assert 'description' in tc_form.fields
    assert 'test_steps' in tc_form.fields
    assert 'expected_results' in tc_form.fields

    review_form = TestCaseReviewForm()
    assert 'comments' in review_form.fields
    assert 'status' in review_form.fields


def test_template_rendering_index():
    """Verify index.html template renders cleanly with context"""
    context = {
        'total_test_cases': 10,
        'pending_count': 5,
        'approved_count': 3,
        'rejected_count': 2,
        'recent_test_cases': [],
    }
    rendered = render_to_string('index.html', context)
    assert "CodeBrain" in rendered


def test_template_rendering_generate():
    """Verify generate.html template renders cleanly"""
    context = {
        'providers': {'deepseek': {'name': 'DeepSeek'}, 'qwen': {'name': 'Qwen'}},
        'default_provider': 'deepseek',
    }
    rendered = render_to_string('generate.html', context)
    assert "Generate" in rendered or "generate" in rendered


def test_template_rendering_knowledge():
    """Verify knowledge.html template renders cleanly"""
    rendered = render_to_string('knowledge.html', {})
    assert "Knowledge" in rendered or "knowledge" in rendered


def test_template_rendering_upload():
    """Verify upload.html template renders cleanly"""
    rendered = render_to_string('upload.html', {})
    assert "Upload" in rendered or "upload" in rendered
