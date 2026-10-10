import xml.sax.saxutils as saxutils
from typing import List, Dict, Any


class JUnitExporter:
    """JUnit XML test report generator for CI/CD pipeline integration.
    
    Transforms APITestRunner execution results into standard JUnit XML
    compatible with Jenkins, GitHub Actions, and GitLab CI.
    """

    def __init__(self, suite_name: str = "CodeBrain API Test Suite"):
        self.suite_name = suite_name

    def generate_junit_xml(self, test_results: List[Dict[str, Any]]) -> str:
        """Produce standard JUnit XML structure from executed test cases."""
        total_tests = len(test_results)
        failures = sum(1 for r in test_results if not r.get('passed', False))
        total_time_sec = round(sum(r.get('latency_ms', 0) for r in test_results) / 1000.0, 3)

        suite_name_esc = saxutils.escape(self.suite_name)

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<testsuites name="{suite_name_esc}" tests="{total_tests}" failures="{failures}" errors="0" time="{total_time_sec}">',
            f'  <testsuite name="{suite_name_esc}" tests="{total_tests}" failures="{failures}" errors="0" time="{total_time_sec}">'
        ]

        for case in test_results:
            case_name = saxutils.escape(str(case.get('name', 'Test Case')))
            case_id = saxutils.escape(str(case.get('case_id', 'TC')))
            method = saxutils.escape(str(case.get('method', 'GET')))
            classname = f"CodeBrain.{method}"
            time_sec = round(case.get('latency_ms', 0) / 1000.0, 3)

            passed = case.get('passed', False)
            if passed:
                lines.append(f'    <testcase classname="{classname}" name="{case_name}" id="{case_id}" time="{time_sec}" />')
            else:
                err_msg = case.get('error') or f"Status code {case.get('status_code')} failed assertions"
                err_msg_esc = saxutils.escape(str(err_msg))

                # Assertion details
                assertion_details = []
                for a in case.get('assertions', []):
                    if not a.get('passed', False):
                        assertion_details.append(f"Assertion failed: {a.get('expression')} (expected: {a.get('expected')}, actual: {a.get('actual')})")
                detail_text = saxutils.escape("\n".join(assertion_details) if assertion_details else err_msg)

                lines.append(f'    <testcase classname="{classname}" name="{case_name}" id="{case_id}" time="{time_sec}">')
                lines.append(f'      <failure message="{err_msg_esc}" type="AssertionError">{detail_text}</failure>')
                lines.append('    </testcase>')

        lines.append('  </testsuite>')
        lines.append('</testsuites>')

        return "\n".join(lines)
