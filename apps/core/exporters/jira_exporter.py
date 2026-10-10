import json
from typing import List, Dict, Any, Optional
import httpx
from apps.utils.logger_manager import get_logger

logger = get_logger(__name__)


class JiraExporter:
    """Enterprise Atlassian Jira & Xray Test Case exporter.
    
    Transforms CodeBrain test cases into standard Jira issue payloads
    and provides idempotent REST synchronization.
    """

    PRIORITY_MAP = {
        "P0": "Highest",
        "P1": "High",
        "P2": "Medium",
        "P3": "Low",
        "p0": "Highest",
        "p1": "High",
        "p2": "Medium",
        "p3": "Low",
    }

    def __init__(self, project_key: str = "TEST", issue_type: str = "Test"):
        self.project_key = project_key.upper()
        self.issue_type = issue_type

    def format_issue(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a single CodeBrain test case into a Jira REST API issue creation dict."""
        summary = test_case.get('title') or test_case.get('name') or test_case.get('description', 'Test Case')
        if len(summary) > 250:
            summary = summary[:247] + "..."

        desc_raw = test_case.get('description', '')
        preconditions = test_case.get('preconditions', '')
        steps_raw = test_case.get('test_steps', [])
        expected_raw = test_case.get('expected_results', [])

        if isinstance(steps_raw, list):
            steps_text = "\n".join(f"{idx}. {step}" for idx, step in enumerate(steps_raw, start=1))
        else:
            steps_text = str(steps_raw)

        if isinstance(expected_raw, list):
            expected_text = "\n".join(f"{idx}. {exp}" for idx, exp in enumerate(expected_raw, start=1))
        else:
            expected_text = str(expected_raw)

        description_parts = [
            f"*Description:*\n{desc_raw}" if desc_raw else "",
            f"*Preconditions:*\n{preconditions}" if preconditions else "",
            f"*Test Steps:*\n{steps_text}" if steps_text else "",
            f"*Expected Results:*\n{expected_text}" if expected_text else "",
            "\n_Generated autonomously by CodeBrain QA Engine_"
        ]
        full_description = "\n\n".join(part for part in description_parts if part)

        p_val = test_case.get('priority', 'P2')
        jira_priority = self.PRIORITY_MAP.get(p_val, "Medium")

        return {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": full_description,
                "issuetype": {"name": self.issue_type},
                "priority": {"name": jira_priority},
                "labels": ["CodeBrain", "Automated-QA"]
            }
        }

    def export_suite(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch format a full suite of test cases into Jira issue payloads."""
        return [self.format_issue(tc) for tc in test_cases]

    def sync_to_jira(
        self,
        test_cases: List[Dict[str, Any]],
        jira_base_url: str,
        auth_email: str,
        api_token: str,
        timeout: float = 15.0
    ) -> Dict[str, Any]:
        """Synchronize test cases to Jira REST API with credential ping and error handling."""
        jira_base = jira_base_url.rstrip('/')
        auth = (auth_email, api_token)
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        # 1. Validation ping check (Invariant: TMS Authentication Drift check)
        try:
            with httpx.Client(timeout=timeout) as client:
                ping_resp = client.get(f"{jira_base}/rest/api/2/myself", auth=auth, headers=headers)
                if ping_resp.status_code == 404:
                    ping_resp = client.get(f"{jira_base}/rest/api/3/myself", auth=auth, headers=headers)
                if ping_resp.status_code not in (200, 201):
                    return {
                        "success": False,
                        "error": f"Jira authentication failed ({ping_resp.status_code}): {ping_resp.text[:200]}",
                        "created_issues": []
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to connect to Jira at {jira_base}: {str(e)}",
                "created_issues": []
            }

        # 2. Sequential/batch creation
        created_issues = []
        errors = []
        with httpx.Client(timeout=timeout) as client:
            for tc in test_cases:
                payload = self.format_issue(tc)
                try:
                    create_resp = client.post(
                        f"{jira_base}/rest/api/2/issue",
                        auth=auth,
                        json=payload,
                        headers=headers
                    )
                    if create_resp.status_code in (200, 201):
                        res_data = create_resp.json()
                        created_issues.append({
                            "id": res_data.get("id"),
                            "key": res_data.get("key"),
                            "summary": payload["fields"]["summary"]
                        })
                    else:
                        errors.append(f"Issue '{payload['fields']['summary']}': {create_resp.status_code} {create_resp.text[:150]}")
                except Exception as e:
                    errors.append(f"Issue '{payload['fields']['summary']}': {str(e)}")

        return {
            "success": len(errors) == 0,
            "total": len(test_cases),
            "created_count": len(created_issues),
            "created_issues": created_issues,
            "errors": errors
        }
