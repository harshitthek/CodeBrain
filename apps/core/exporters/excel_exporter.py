import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from typing import List, Dict, Any, Optional


def _sanitize_excel_text(val: Any) -> str:
    """Prepend ' to any cell beginning with '=', '+', '-', '@', or whitespace before them,
    preventing spreadsheet formula injection attacks.
    """
    if val is None:
        return ""
    if isinstance(val, (list, tuple)):
        s = "\n".join(str(x) for x in val)
    else:
        s = str(val)

    stripped = s.lstrip()
    if stripped and stripped[0] in ('=', '+', '-', '@', '\t', '\r'):
        return f"'{s}"
    return s


class ExcelTestSuiteExporter:
    """Enterprise-grade OpenPyXL test suite exporter.
    
    Produces styled, injection-hardened Excel workbooks with:
    - Segoe UI professional typography
    - Corporate header styling with navy fill and borders
    - Alternating row striping (clean white and light slate-blue)
    - Explicit text cell typing (data_type='s')
    - Formula injection sanitization (_sanitize_excel_text)
    - Dynamic column widths and frozen header panes
    """

    HEADERS = [
        "Case ID",
        "Name",
        "Priority",
        "Case Type",
        "Preconditions",
        "Test Steps",
        "Expected Results",
        "Category / Tag"
    ]

    COLUMN_WIDTHS = {
        1: 16,  # Case ID
        2: 38,  # Name
        3: 12,  # Priority
        4: 14,  # Case Type
        5: 42,  # Preconditions
        6: 55,  # Test Steps
        7: 55,  # Expected Results
        8: 34   # Category / Tag
    }

    def __init__(self, sheet_title: str = "ROVC Test Cases"):
        self.sheet_title = sheet_title

    def create_workbook(self, test_cases: List[Dict[str, Any]]) -> openpyxl.Workbook:
        """Build and style an openpyxl Workbook for the given test cases."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = self.sheet_title
        ws.freeze_panes = "A2"

        # Typography & Fills
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")

        even_row_fill = PatternFill(start_color="F2F5F9", end_color="F2F5F9", fill_type="solid")
        odd_row_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

        cell_font = Font(name="Segoe UI", size=10, color="1E293B")

        thin_border = Border(
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'),
            bottom=Side(style='thin', color='D9D9D9')
        )

        align_center = Alignment(horizontal="center", vertical="top", wrap_text=True)
        align_left = Alignment(horizontal="left", vertical="top", wrap_text=True)
        align_header = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Header Row
        ws.append(self.HEADERS)
        ws.row_dimensions[1].height = 28

        for col_idx in range(1, len(self.HEADERS) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = align_header
            cell.border = thin_border

        # Data Rows
        for row_idx, tc in enumerate(test_cases, start=2):
            cid = tc.get("case_id") or tc.get("id") or f"TC-{row_idx-1:03d}"
            name = tc.get("name") or tc.get("title") or tc.get("description", "")
            priority = tc.get("priority", "Medium")
            case_type = tc.get("case_type", "Functional")

            preconditions = tc.get("preconditions", "")
            if isinstance(preconditions, (list, tuple)):
                preconditions = "\n".join(str(p) for p in preconditions)

            steps = tc.get("test_steps", "")
            if isinstance(steps, (list, tuple)):
                steps = "\n".join(str(s) for s in steps)

            expected = tc.get("expected_results", "")
            if isinstance(expected, (list, tuple)):
                expected = "\n".join(str(e) for e in expected)

            category = tc.get("category") or tc.get("tag") or tc.get("category_tag", "")

            # Sanitize each text field against formula injection
            sanitized_cid = _sanitize_excel_text(cid)
            sanitized_name = _sanitize_excel_text(name)
            sanitized_priority = _sanitize_excel_text(priority)
            sanitized_case_type = _sanitize_excel_text(case_type)
            sanitized_preconditions = _sanitize_excel_text(preconditions)
            sanitized_steps = _sanitize_excel_text(steps)
            sanitized_expected = _sanitize_excel_text(expected)
            sanitized_category = _sanitize_excel_text(category)

            ws.append([
                sanitized_cid,
                sanitized_name,
                sanitized_priority,
                sanitized_case_type,
                sanitized_preconditions,
                sanitized_steps,
                sanitized_expected,
                sanitized_category
            ])

            row_fill = even_row_fill if row_idx % 2 == 0 else odd_row_fill

            for col_idx in range(1, len(self.HEADERS) + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                # Mandatory formula injection protection: set data_type='s'
                cell.data_type = 's'
                cell.font = cell_font
                cell.fill = row_fill
                cell.border = thin_border

                if col_idx in (1, 3, 4):  # Case ID, Priority, Case Type
                    cell.alignment = align_center
                else:
                    cell.alignment = align_left

        # Column widths
        for col_idx, width in self.COLUMN_WIDTHS.items():
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = width

        return wb

    def export_to_file(self, test_cases: List[Dict[str, Any]], file_path: str) -> None:
        """Export test cases directly to an Excel file path."""
        wb = self.create_workbook(test_cases)
        wb.save(file_path)
