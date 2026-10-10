import json
from typing import List, Dict, Any


def generate_pytest_script(test_cases: List[Dict[str, Any]], base_url: str = "http://127.0.0.1:8000") -> str:
    """Generate runnable Pytest script for the provided API test cases."""
    base_url = base_url.rstrip('/')
    code_lines = [
        '"""',
        'Auto-generated Pytest API Suite by CodeBrain.',
        f'Target Base URL: {base_url}',
        '"""',
        'import pytest',
        'import httpx',
        '',
        f'BASE_URL = "{base_url}"',
        '',
    ]

    for idx, case in enumerate(test_cases, start=1):
        clean_name = case.get('name', f'test_case_{idx}').replace(' ', '_').replace('-', '_')
        clean_name = "".join(c for c in clean_name if c.isalnum() or c == '_').lower()
        fn_name = f"test_{idx}_{clean_name}"

        req_info = case.get('request') or {}
        method = (case.get('method') or req_info.get('method') or 'GET').upper()
        path = case.get('path') or req_info.get('path', '/')
        if not path.startswith('/'):
            path = '/' + path

        body = case.get('request_body_json') or req_info.get('body') or case.get('body')
        query_params = {}
        raw_query = case.get('request_query') or req_info.get('query') or case.get('query_params', [])
        for q in raw_query:
            if isinstance(q, dict):
                k = q.get('param_name') or q.get('name')
                v = q.get('param_value') if q.get('param_value') is not None else q.get('value')
                if k:
                    query_params[k] = v

        # Substitute path parameters if provided
        for rp in (case.get('request_rest') or req_info.get('rest') or []):
            if isinstance(rp, dict):
                rk = rp.get('param_name') or rp.get('name') or rp.get('key')
                rv = rp.get('param_value') if rp.get('param_value') is not None else rp.get('value')
                if rk and rv is not None:
                    path = path.replace('{' + str(rk) + '}', str(rv)).replace(':' + str(rk), str(rv))

        headers_dict = {"User-Agent": "CodeBrain-Pytest/2.0"}
        raw_headers = case.get('headers') or req_info.get('headers', [])
        for h in raw_headers:
            if isinstance(h, dict) and h.get('name') and h.get('value'):
                headers_dict[h['name']] = str(h['value'])

        desc = case.get("description", case.get("name", "Test Case"))
        code_lines.append(f"def {fn_name}():")
        code_lines.append(f'    {repr(str(desc))}')
        code_lines.append(f'    url = BASE_URL + {path!r}')
        code_lines.append(f'    headers = {headers_dict!r}')
        if query_params:
            code_lines.append(f'    params = {query_params!r}')
        else:
            code_lines.append('    params = None')

        if body is not None:
            code_lines.append(f'    json_body = {body!r}')
        else:
            code_lines.append('    json_body = None')

        code_lines.append(f'    with httpx.Client(timeout=10.0) as client:')
        code_lines.append(f'        response = client.request({method!r}, url, params=params, json=json_body, headers=headers)')

        # Assertions
        assertions = case.get('assertions') or []
        if 'jsonPathAssertion' in case:
            assertions = case['jsonPathAssertion'].get('assertions', [])

        expected_status = 200
        for a in assertions:
            expr = a.get('expression', '')
            if expr in ('code', 'status', 'status_code'):
                try:
                    expected_status = int(a.get('expectedValue', a.get('expected', 200)))
                except (ValueError, TypeError):
                    pass

        condition = case.get('assertion_condition', 'EQUALS')
        if condition == 'NOT_EQUALS':
            code_lines.append(f'        assert response.status_code != 200, f"Expected error status, got {{response.status_code}}"')
        else:
            code_lines.append(f'        assert response.status_code == {expected_status}, f"Expected {expected_status}, got {{response.status_code}}: {{response.text}}"')

        code_lines.append('        data = response.json()')
        code_lines.append('        assert data is not None')
        code_lines.append('')

    return "\n".join(code_lines)


def generate_postman_collection(test_cases: List[Dict[str, Any]], base_url: str = "http://127.0.0.1:8000", collection_name: str = "CodeBrain API Suite") -> Dict[str, Any]:
    """Generate Postman Collection v2.1.0 schema for test cases."""
    base_url = base_url.rstrip('/')
    items = []

    for idx, case in enumerate(test_cases, start=1):
        req_info = case.get('request') or {}
        method = (case.get('method') or req_info.get('method') or 'GET').upper()
        path = case.get('path') or req_info.get('path', '/')
        if path.startswith('/'):
            path = path[1:]
        path_segments = [p for p in path.split('/') if p]

        query = []
        raw_query = case.get('request_query') or req_info.get('query') or case.get('query_params', [])
        for q in raw_query:
            if isinstance(q, dict):
                k = q.get('param_name') or q.get('name')
                v = q.get('param_value') if q.get('param_value') is not None else q.get('value')
                if k:
                    query.append({"key": str(k), "value": str(v) if v is not None else ""})

        body_data = case.get('request_body_json') or req_info.get('body') or case.get('body')
        req_body = {}
        if body_data:
            req_body = {
                "mode": "raw",
                "raw": json.dumps(body_data, ensure_ascii=False, indent=2),
                "options": {"raw": {"language": "json"}}
            }

        # Assertions script
        assertions = case.get('assertions') or []
        if 'jsonPathAssertion' in case:
            assertions = case['jsonPathAssertion'].get('assertions', [])

        expected_status = 200
        for a in assertions:
            expr = a.get('expression', '')
            if expr in ('code', 'status', 'status_code'):
                try:
                    expected_status = int(a.get('expectedValue', a.get('expected', 200)))
                except (ValueError, TypeError):
                    pass

        condition = case.get('assertion_condition', 'EQUALS')
        test_script_lines = [
            'pm.test("Status code is valid", function () {',
            f'    pm.response.to.have.status({expected_status});' if condition != 'NOT_EQUALS' else '    pm.expect(pm.response.code).to.be.oneOf([400, 401, 403, 404, 500]);',
            '});',
            'pm.test("Response is valid JSON", function () {',
            '    var jsonData = pm.response.json();',
            '    pm.expect(jsonData).to.not.be.null;',
            '});'
        ]

        # Request headers
        header_list = [
            {"key": "Accept", "value": "application/json", "type": "text"},
            {"key": "Content-Type", "value": "application/json", "type": "text"}
        ]
        raw_headers = case.get('headers') or req_info.get('headers', [])
        for h in raw_headers:
            if isinstance(h, dict) and h.get('name') and h.get('value'):
                header_list.append({"key": str(h['name']), "value": str(h['value']), "type": "text"})

        items.append({
            "name": case.get('name', f"Test Case {idx}"),
            "event": [
                {
                    "listen": "test",
                    "script": {
                        "type": "text/javascript",
                        "exec": test_script_lines
                    }
                }
            ],
            "request": {
                "method": method,
                "header": header_list,
                "body": req_body,
                "url": {
                    "raw": f"{base_url}/{path}",
                    "host": [base_url],
                    "path": path_segments,
                    "query": query
                },
                "description": case.get('description', '')
            }
        })

    return {
        "info": {
            "name": collection_name,
            "_postman_id": "codebrain-gen-suite-001",
            "description": "Exported from CodeBrain Intelligent Testing Platform",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": items
    }
