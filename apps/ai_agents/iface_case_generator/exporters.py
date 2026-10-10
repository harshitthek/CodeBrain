import json
from typing import List, Dict, Any, Optional


def _resolve_body(case: Dict[str, Any], req_info: Optional[Dict[str, Any]] = None) -> Any:
    """Unwrap request body envelopes (e.g. MeterSphere bodyType/jsonBody/raw) and parse JSON strings."""
    if req_info is None:
        req_info = case.get('request') or {}

    def _unwrap(val: Any) -> Any:
        if isinstance(val, dict) and 'bodyType' in val:
            json_body_node = val.get('jsonBody')
            if isinstance(json_body_node, dict) and json_body_node.get('jsonValue') is not None:
                return json_body_node.get('jsonValue')
            if isinstance(val.get('raw'), str):
                return val.get('raw')
            return None
        return val

    cand_body = _unwrap(req_info.get('body'))
    body = case.get('request_body_json')
    if body is None:
        body = cand_body if cand_body is not None else case.get('body')
    body = _unwrap(body)

    if isinstance(body, str) and body.strip():
        try:
            body = json.loads(body)
        except Exception:
            pass
    return body


def generate_pytest_script(test_cases: List[Dict[str, Any]], base_url: str = "http://127.0.0.1:8000") -> str:
    """Generate runnable Pytest script for the provided API test cases."""
    base_url = base_url.rstrip('/')
    code_lines = [
        '"""',
        'Auto-generated Pytest API Suite by CodeBrain.',
        '"""',
        'import re',
        'import pytest',
        'import httpx',
        'from jsonpath_ng.ext import parse as parse_jsonpath',
        '',
        f'BASE_URL = {base_url!r}',
        '',
        'def _extract_jsonpath(payload, expression):',
        '    if not isinstance(payload, (dict, list)):',
        '        return None',
        '    if isinstance(payload, dict) and expression in payload:',
        '        return payload[expression]',
        '    if not expression.startswith("$") and "." in expression:',
        '        curr = payload',
        '        for part in expression.split("."):',
        '            if isinstance(curr, dict) and part in curr:',
        '                curr = curr[part]',
        '            else:',
        '                curr = None',
        '                break',
        '        if curr is not None:',
        '            return curr',
        '    query = expression if expression.startswith("$") else f"$.{expression}"',
        '    try:',
        '        matches = parse_jsonpath(query).find(payload)',
        '        return matches[0].value if matches else None',
        '    except Exception:',
        '        return None',
        '',
        'def _evaluate_assertion(actual, condition, expected):',
        '    op = (condition or "EQUALS").upper()',
        '    if op in ("IS_NULL", "NULL", "NONE"):',
        '        return actual is None',
        '    if op in ("NOT_NULL", "NOT_NONE", "EXISTS"):',
        '        return actual is not None and actual != ""',
        '    if actual is None:',
        '        return False',
        '    if op in ("EQUALS", "EQ", "=="):',
        '        return str(actual).strip() == str(expected).strip()',
        '    if op in ("NOT_EQUALS", "NEQ", "!="):',
        '        return str(actual).strip() != str(expected).strip()',
        '    if op == "CONTAINS":',
        '        return str(expected) in ( [str(x) for x in actual] if isinstance(actual, list) else str(actual) )',
        '    if op == "NOT_CONTAINS":',
        '        return str(expected) not in str(actual)',
        '    if op in ("GREATER_THAN", "GT", ">"):',
        '        return float(actual) > float(expected)',
        '    if op in ("LESS_THAN", "LT", "<"):',
        '        return float(actual) < float(expected)',
        '    if op in ("REGEX_MATCH", "REGEX"):',
        '        return bool(re.search(str(expected), str(actual)))',
        '    return str(actual) == str(expected)',
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

        body = _resolve_body(case, req_info)

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
        code_lines.append(f'    url = f"{{BASE_URL}}" + {path!r}')
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
            if expr in ('code', 'status', 'status_code', 'http_status'):
                try:
                    expected_status = int(a.get('expectedValue', a.get('expected', 200)))
                except (ValueError, TypeError):
                    pass

        condition = case.get('assertion_condition', 'EQUALS')
        if condition == 'NOT_EQUALS':
            code_lines.append(f'        assert response.status_code != 200, f"Expected error status, got {{response.status_code}}"')
        else:
            code_lines.append(f'        assert response.status_code == {expected_status}, f"Expected {expected_status}, got {{response.status_code}}: {{response.text}}"')

        code_lines.append('        content_type = response.headers.get("content-type", "")')
        code_lines.append('        data = response.json() if response.content and "json" in content_type.lower() else None')

        non_status_assertions = [
            a for a in assertions
            if isinstance(a, dict) and a.get('expression') and a.get('expression') not in ('code', 'status', 'status_code', 'http_status')
        ]
        if non_status_assertions:
            code_lines.append('        assert data is not None, "Expected JSON response body for assertions"')
            for a in non_status_assertions:
                expr = a.get('expression')
                cond = (a.get('condition') or a.get('operator') or condition or 'EQUALS').upper()
                exp_val = a.get('expectedValue', a.get('expected'))
                code_lines.append(
                    f'        assert _evaluate_assertion(_extract_jsonpath(data, {expr!r}), {cond!r}, {exp_val!r}), f"Assertion failed for {expr!r}"'
                )
        else:
            code_lines.append('        if response.content and "json" in content_type.lower():')
            code_lines.append('            assert data is not None')
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

        body_data = _resolve_body(case, req_info)
        req_body = {}
        if body_data:
            raw_payload = body_data if isinstance(body_data, str) else json.dumps(body_data, ensure_ascii=False, indent=2)
            req_body = {
                "mode": "raw",
                "raw": raw_payload,
                "options": {"raw": {"language": "json"}}
            }

        # Assertions script
        assertions = case.get('assertions') or []
        if 'jsonPathAssertion' in case:
            assertions = case['jsonPathAssertion'].get('assertions', [])

        expected_status = 200
        for a in assertions:
            expr = a.get('expression', '')
            if expr in ('code', 'status', 'status_code', 'http_status'):
                try:
                    expected_status = int(a.get('expectedValue', a.get('expected', 200)))
                except (ValueError, TypeError):
                    pass

        condition = case.get('assertion_condition', 'EQUALS')
        test_script_lines = [
            'pm.test("Status code is valid", function () {',
            f'    pm.response.to.have.status({expected_status});' if condition != 'NOT_EQUALS' else '    pm.expect(pm.response.code).to.not.equal(200);',
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
