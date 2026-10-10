import io
import json
import pytest
from django.test import RequestFactory
from django.urls import reverse

from apps.core.models import TestCase, TestCaseReview
from apps.ai_agents.test_case_generator.schemas import (
    GeneratedTestCaseItem,
    extract_and_parse_test_cases,
)
from apps.ai_agents.test_case_reviewer.views import (
    export_test_cases_excel,
    case_review,
)
from apps.core.views import update_test_case_status
from apps.ai_agents.prd_analyzer.views import extract_content_from_file
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.django_db
class TestPhase1Suite:

    def test_pydantic_schema_validation(self):
        """Verify GeneratedTestCaseItem handles strings and lists gracefully."""
        # 1. Standard list inputs
        item1 = GeneratedTestCaseItem.model_validate({
            "description": "Valid login test",
            "test_steps": ["Enter username", "Enter password", "Click Submit"],
            "expected_results": ["Dashboard displayed"],
            "priority": "P1"
        })
        assert len(item1.test_steps) == 3
        assert item1.priority == "P1"

        # 2. String inputs auto-coerced to lists
        item2 = GeneratedTestCaseItem.model_validate({
            "description": "String step test",
            "test_steps": "Step 1\nStep 2\nStep 3",
            "expected_results": "Expected result here",
        })
        assert isinstance(item2.test_steps, list)
        assert len(item2.test_steps) == 3
        assert isinstance(item2.expected_results, list)
        assert item2.expected_results[0] == "Expected result here"

    def test_extract_and_parse_json_markdown_blocks(self):
        """Verify extraction from markdown fences, dirty preambles, and brackets."""
        markdown_response = """
Here are your requested test cases:
```json
[
  {
    "description": "Checkout test",
    "test_steps": ["Add item", "Proceed to payment"],
    "expected_results": ["Receipt generated"]
  }
]
```
Let me know if you need more!
"""
        cases = extract_and_parse_test_cases(markdown_response)
        assert len(cases) == 1
        assert cases[0]["description"] == "Checkout test"

    def test_extract_and_parse_trailing_commas(self):
        """Verify greedy bracket parser repairs trailing commas."""
        dirty_json = """
[
  {
    "description": "Dirty comma test",
    "test_steps": ["Action 1",],
    "expected_results": ["Outcome 1",],
  },
]
"""
        cases = extract_and_parse_test_cases(dirty_json)
        assert len(cases) == 1
        assert cases[0]["description"] == "Dirty comma test"

    def test_update_test_case_status_endpoint(self):
        """Verify update_test_case_status updates DB and creates review comments."""
        tc = TestCase.objects.create(
            title="Search Test",
            description="Verify search bar filters products",
            test_steps="1. Type query\n2. Press Enter",
            expected_results="Relevant products listed",
            status="pending"
        )

        rf = RequestFactory()
        payload = {
            "test_case_id": tc.id,
            "status": "approved",
            "comments": "Looks solid, approved for sprint 12."
        }
        request = rf.post(
            "/api/update-status/",
            data=json.dumps(payload),
            content_type="application/json"
        )
        response = update_test_case_status(request)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True

        tc.refresh_from_db()
        assert tc.status == "approved"

        # Check that review record was recorded
        reviews = TestCaseReview.objects.filter(test_case=tc)
        assert reviews.count() == 1
        assert reviews.first().review_comments == "Looks solid, approved for sprint 12."

    def test_export_test_cases_excel_openpyxl(self):
        """Verify openpyxl Excel exporter outputs valid .xlsx spreadsheet."""
        tc = TestCase.objects.create(
            title="Export Test",
            description="Verify export to Excel",
            test_steps="Step 1",
            expected_results="Result 1",
            status="approved",
            priority="p1"
        )

        rf = RequestFactory()
        request = rf.get(f"/test_case_reviewer/api/export-test-cases-excel/?ids={tc.id}")
        response = export_test_cases_excel(request)

        assert response.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response["Content-Type"]
        assert response["Content-Disposition"].endswith('.xlsx"')

        # Verify readable by openpyxl
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        assert "Test Cases" in wb.sheetnames
        sheet = wb["Test Cases"]
        assert sheet.cell(row=1, column=1).value == "No."
        assert sheet.cell(row=2, column=2).value == tc.id

    def test_prd_extract_content_from_file_text_and_md(self):
        """Verify prd analyzer file extractor handles .txt and .md files."""
        md_file = SimpleUploadedFile("spec.md", b"# Feature Specification\nUser can reset password via email.")
        content = extract_content_from_file(md_file, ".md")
        assert "# Feature Specification" in content

        txt_file = SimpleUploadedFile("notes.txt", b"Requirement notes line 1\nRequirement notes line 2")
        content_txt = extract_content_from_file(txt_file, ".txt")
        assert "Requirement notes line 1" in content_txt

    def test_pydantic_schema_rejects_empty_and_null_steps_and_results(self):
        """Verify GeneratedTestCaseItem rejects null or empty steps/results."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GeneratedTestCaseItem.model_validate({
                "description": "Empty steps",
                "test_steps": [],
                "expected_results": ["Result 1"]
            })

        with pytest.raises(ValidationError):
            GeneratedTestCaseItem.model_validate({
                "description": "Whitespace steps",
                "test_steps": ["   ", ""],
                "expected_results": ["Result 1"]
            })

        with pytest.raises(ValidationError):
            GeneratedTestCaseItem.model_validate({
                "description": "Empty expected results",
                "test_steps": ["Step 1"],
                "expected_results": []
            })

        with pytest.raises(ValidationError):
            GeneratedTestCaseItem.model_validate({
                "description": "Empty string step",
                "test_steps": "   ",
                "expected_results": ["Result 1"]
            })

    def test_extract_and_parse_bracketed_prose_before_array(self):
        """Verify extraction succeeds when bracketed text appears before JSON array."""
        text = """Here is the breakdown for [Order Service]:
[
  {
    "description": "Order placement test",
    "test_steps": ["Submit cart", "Select payment"],
    "expected_results": ["Order confirmed"]
  }
]
Hope this helps!"""
        cases = extract_and_parse_test_cases(text)
        assert len(cases) == 1
        assert cases[0]["description"] == "Order placement test"

    def test_export_test_cases_excel_sanitizes_formulas_and_uppercases_priority(self):
        """Verify Excel export neutralizes formula prefixes and uppercases priority."""
        tc = TestCase.objects.create(
            title="Formula Test",
            description="=cmd|'/C calc'!A0",
            test_steps="+1+2\n-5\n@SUM(A1:B2)",
            expected_results="\tDangerous tab",
            status="approved",
            priority="p3"
        )

        rf = RequestFactory()
        request = rf.get(f"/test_case_reviewer/api/export-test-cases-excel/?ids={tc.id}")
        response = export_test_cases_excel(request)

        assert response.status_code == 200
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        sheet = wb["Test Cases"]

        # Check sanitized values
        row = 2
        desc_cell = sheet.cell(row=row, column=3).value
        steps_cell = sheet.cell(row=row, column=4).value
        results_cell = sheet.cell(row=row, column=5).value
        priority_cell = sheet.cell(row=row, column=7).value

        assert desc_cell.startswith("'=")
        assert steps_cell.startswith("'+")
        assert results_cell.startswith("'\t")
        assert priority_cell == "P3"

    def test_update_test_case_status_with_authenticated_user(self):
        """Verify authenticated user is attributed as reviewer on status update."""
        from django.contrib.auth.models import User
        user = User.objects.create_user(username="lead_qa", password="password123")

        tc = TestCase.objects.create(
            title="Reviewer Attribution Test",
            description="Check reviewer user is saved",
            test_steps="1. Step",
            expected_results="Result",
            status="pending"
        )

        rf = RequestFactory()
        payload = {
            "test_case_id": tc.id,
            "status": "approved",
            "comments": "Signed off by Lead QA."
        }
        request = rf.post(
            "/api/update-status/",
            data=json.dumps(payload),
            content_type="application/json"
        )
        request.user = user

        response = update_test_case_status(request)
        assert response.status_code == 200

        review = TestCaseReview.objects.filter(test_case=tc).first()
        assert review is not None
        assert review.reviewer == user
        assert review.review_comments == "Signed off by Lead QA."

    def test_update_test_case_status_validation_and_safe_error(self, monkeypatch):
        """Verify invalid status returns 400 and server exceptions return safe error."""
        tc = TestCase.objects.create(
            title="Validation Test",
            description="Desc",
            test_steps="Step",
            expected_results="Result",
            status="pending"
        )

        rf = RequestFactory()
        # Invalid status
        bad_req = rf.post(
            "/api/update-status/",
            data=json.dumps({"test_case_id": tc.id, "status": "invalid_status"}),
            content_type="application/json"
        )
        bad_resp = update_test_case_status(bad_req)
        assert bad_resp.status_code == 400

        # Server exception safe message
        def fake_save(*args, **kwargs):
            raise RuntimeError("Database connection secret_key=12345 timeout")

        monkeypatch.setattr(TestCase, "save", fake_save)

        err_req = rf.post(
            "/api/update-status/",
            data=json.dumps({"test_case_id": tc.id, "status": "approved"}),
            content_type="application/json"
        )
        err_resp = update_test_case_status(err_req)
        assert err_resp.status_code == 500
        err_data = json.loads(err_resp.content)
        assert err_data["success"] is False
        assert err_data["message"] == "Failed to update test case status"
        assert "secret_key" not in err_data["message"]
