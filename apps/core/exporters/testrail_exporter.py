from typing import List, Dict, Any, Optional
import httpx
from apps.utils.logger_manager import get_logger

logger = get_logger(__name__)


class TestRailExporter:
    """Enterprise TestRail TMS Test Case exporter.
    
    Transforms CodeBrain test cases into TestRail v2 API structures
    with step-separated assertions and provides REST synchronization.
    """

    PRIORITY_MAP = {
        "P0": 4,  # Critical
        "P1": 3,  # High
        "P2": 2,  # Medium
        "P3": 1,  # Low
        "p0": 4,
        "p1": 3,
        "p2": 2,
        "p3": 1,
    }

    def __init__(self, section_id: int = 1, suite_id: Optional[int] = None):
        self.section_id = int(section_id)
        self.suite_id = int(suite_id) if suite_id else None

    def format_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a single CodeBrain test case into TestRail add_case payload."""
        title = test_case.get('title') or test_case.get('name') or test_case.get('description', 'Test Case')
        if len(title) > 250:
            title = title[:247] + "..."

        steps_raw = test_case.get('test_steps', [])
        expected_raw = test_case.get('expected_results', [])

        steps_list = steps_raw if isinstance(steps_raw, list) else [s.strip() for s in str(steps_raw).split('\n') if s.strip()]
        expected_list = expected_raw if isinstance(expected_raw, list) else [e.strip() for e in str(expected_raw).split('\n') if e.strip()]

        # Pair steps with expected results for TestRail separated steps template
        steps_separated = []
        max_len = max(len(steps_list), len(expected_list), 1)
        for i in range(max_len):
            step_content = steps_list[i] if i < len(steps_list) else "Perform step verification"
            step_exp = expected_list[i] if i < len(expected_list) else "Verified outcome as expected"
            steps_separated.append({
                "content": step_content,
                "expected": step_exp
            })

        p_val = test_case.get('priority', 'P2')
        priority_id = self.PRIORITY_MAP.get(p_val, 2)

        return {
            "title": title,
            "type_id": 1,         # Automated
            "template_id": 2,     # Test Case (Steps)
            "priority_id": priority_id,
            "estimate": "2m",
            "custom_preconds": test_case.get('preconditions', ''),
            "custom_steps_separated": steps_separated
        }

    def export_suite(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch format a full suite of test cases into TestRail payloads."""
        return [self.format_case(tc) for tc in test_cases]

    def sync_to_testrail(
        self,
        test_cases: List[Dict[str, Any]],
        testrail_base_url: str,
        user_email: str,
        api_key: str,
        section_id: Optional[int] = None,
        timeout: float = 15.0
    ) -> Dict[str, Any]:
        """Synchronize test cases to TestRail REST API."""
        base_url = testrail_base_url.rstrip('/')
        target_section = section_id or self.section_id
        auth = (user_email, api_key)
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        # 1. Ping check
        try:
            with httpx.Client(timeout=timeout) as client:
                ping_resp = client.get(
                    f"{base_url}/index.php?/api/v2/get_user_by_email&email={user_email}",
                    auth=auth,
                    headers=headers
                )
                if ping_resp.status_code not in (200, 201):
                    return {
                        "success": False,
                        "error": f"TestRail authentication failed ({ping_resp.status_code}): {ping_resp.text[:200]}",
                        "created_cases": []
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to connect to TestRail at {base_url}: {str(e)}",
                "created_cases": []
            }

        # 2. Sequential creation
        created_cases = []
        errors = []
        with httpx.Client(timeout=timeout) as client:
            for tc in test_cases:
                payload = self.format_case(tc)
                try:
                    create_resp = client.post(
                        f"{base_url}/index.php?/api/v2/add_case/{target_section}",
                        auth=auth,
                        json=payload,
                        headers=headers
                    )
                    if create_resp.status_code in (200, 201):
                        res_data = create_resp.json()
                        created_cases.append({
                            "id": res_data.get("id"),
                            "title": payload["title"]
                        })
                    else:
                        errors.append(f"Case '{payload['title']}': {create_resp.status_code} {create_resp.text[:150]}")
                except Exception as e:
                    errors.append(f"Case '{payload['title']}': {str(e)}")

        return {
            "success": len(errors) == 0,
            "total": len(test_cases),
            "created_count": len(created_cases),
            "created_cases": created_cases,
            "errors": errors
        }
