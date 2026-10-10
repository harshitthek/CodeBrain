import re
import json
import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import ipaddress
import socket
from urllib.parse import urlparse, urlunparse
import httpx
from jsonpath_ng.ext import parse as parse_jsonpath
from .exporters import _resolve_body


class APITestRunner:
    """Asynchronous HTTP test execution engine evaluating status codes and JSONPath assertions."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        max_concurrency: int = 5,
        verify_tls: bool = True,
        verify: Optional[bool] = None,
        allow_private: Optional[bool] = None,
    ):
        self.base_url = base_url.strip().rstrip('/')
        self.timeout = timeout
        self.max_concurrency = max_concurrency
        self.verify_tls = verify if verify is not None else verify_tls
        self.verify = self.verify_tls
        if allow_private is None:
            try:
                from django.conf import settings
                allow_private = bool(getattr(settings, 'ALLOW_PRIVATE_RUNNER_TARGETS', False))
            except Exception:
                allow_private = False
        self.allow_private = allow_private
        self.semaphore = asyncio.Semaphore(max_concurrency)

    def _is_blocked_ip(self, ip: Any, hostname: str = "") -> bool:
        try:
            from django.conf import settings
            allowed_hosts = set(getattr(settings, 'RUNNER_ALLOWED_HOSTS', ()) or ())
        except Exception:
            allowed_hosts = set()

        if ip == ipaddress.ip_address('fd00:ec2::254'):
            return True
        if ip.is_link_local or ip.is_multicast or ip.is_unspecified or ip.is_reserved:
            return True
        if isinstance(ip, ipaddress.IPv4Address) and ip in ipaddress.IPv4Network('169.254.0.0/16'):
            return True
        if not self.allow_private and str(ip) not in allowed_hosts and hostname not in allowed_hosts:
            if ip.is_private or ip.is_loopback:
                return True
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            v4 = ip.ipv4_mapped
            if (
                v4.is_link_local
                or v4.is_multicast
                or v4.is_unspecified
                or v4.is_reserved
                or v4 in ipaddress.IPv4Network('169.254.0.0/16')
            ):
                return True
            if not self.allow_private and str(v4) not in allowed_hosts and hostname not in allowed_hosts:
                if v4.is_private or v4.is_loopback:
                    return True
        return False

    def _resolve_safe_target(self, url: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate URL target, resolve hostname, and return (is_safe, validated_ip, original_netloc)."""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                return False, None, None
            hostname = (parsed.hostname or '').lower().strip('[]')
            if not hostname:
                return False, None, None

            if hostname in ('169.254.169.254', 'metadata.google.internal', 'metadata.goog', 'fd00:ec2::254'):
                return False, None, None

            # Check IP representation (including decimal and hex)
            try:
                try:
                    ip = ipaddress.ip_address(int(hostname, 0))
                except (ValueError, TypeError):
                    ip = ipaddress.ip_address(hostname)

                if self._is_blocked_ip(ip, hostname):
                    return False, None, None
                return True, str(ip), None
            except ValueError:
                # Hostname is a domain name: resolve DNS and reject on failure
                try:
                    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
                    addr_info = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
                    if not addr_info:
                        return False, None, None
                    validated_ips: List[str] = []
                    for _, _, _, _, sockaddr in addr_info:
                        resolved_ip = ipaddress.ip_address(sockaddr[0])
                        if self._is_blocked_ip(resolved_ip, hostname):
                            return False, None, None
                        validated_ips.append(str(resolved_ip))
                    return True, validated_ips[0], parsed.netloc
                except (socket.gaierror, ValueError, OSError):
                    return False, None, None
        except Exception:
            return False, None, None

    def _is_safe_target_url(self, url: str) -> bool:
        """Prevent requests to cloud instance metadata and invalid endpoints."""
        return self._is_safe_target(url)

    def _is_safe_target(self, url: str) -> bool:
        """Validate URL protocol and prevent cloud metadata access and SSRF."""
        is_safe, _, _ = self._resolve_safe_target(url)
        return is_safe


    def _substitute_path_variables(self, path: str, rest_params: List[Dict[str, Any]]) -> str:
        """Replace path placeholders like /users/{id} with parameter values."""
        resolved_path = path
        for param in rest_params:
            key = param.get('param_name') or param.get('name')
            val = param.get('param_value') if param.get('param_value') is not None else param.get('value')
            if key and val is not None:
                resolved_path = resolved_path.replace(f"{{{key}}}", str(val))
                resolved_path = resolved_path.replace(f":{key}", str(val))
        return resolved_path

    def _extract_jsonpath(self, payload: Any, expression: str) -> Any:
        """Extract a value from parsed JSON using dot-notation or JSONPath."""
        if not isinstance(payload, (dict, list)):
            return None

        # Direct key lookup
        if isinstance(payload, dict) and expression in payload:
            return payload[expression]

        # Dot-path traversal (e.g. data.profile.username)
        if not expression.startswith('$') and '.' in expression:
            parts = expression.split('.')
            curr = payload
            for part in parts:
                if isinstance(curr, dict) and part in curr:
                    curr = curr[part]
                else:
                    curr = None
                    break
            if curr is not None:
                return curr

        # JSONPath evaluation via jsonpath-ng
        jsonpath_query = expression if expression.startswith('$') else f"$.{expression}"
        try:
            jp_parser = parse_jsonpath(jsonpath_query)
            matches = jp_parser.find(payload)
            if matches:
                return matches[0].value
        except Exception:
            pass

        return None

    def _evaluate_operator(self, actual: Any, operator: str, expected: Any) -> bool:
        """Evaluate comparison operator between actual and expected values."""
        op = operator.upper()

        if op in ('IS_NULL', 'NULL'):
            return actual is None

        if op in ('NOT_NULL', 'NOTNULL'):
            return actual is not None

        if actual is None:
            return False

        actual_str = str(actual).strip()
        expected_str = str(expected).strip() if expected is not None else ""

        if op in ('EQUALS', 'EQUAL', '=='):
            # Numeric comparison if both are numeric
            try:
                return float(actual_str) == float(expected_str)
            except (ValueError, TypeError):
                return actual_str.lower() == expected_str.lower()

        if op in ('NOT_EQUALS', 'NOT_EQUAL', '!='):
            try:
                return float(actual_str) != float(expected_str)
            except (ValueError, TypeError):
                return actual_str.lower() != expected_str.lower()

        if op == 'CONTAINS':
            if isinstance(actual, (list, tuple)):
                return expected_str in [str(x) for x in actual]
            return expected_str.lower() in actual_str.lower()

        if op == 'NOT_CONTAINS':
            if isinstance(actual, (list, tuple)):
                return expected_str not in [str(x) for x in actual]
            return expected_str.lower() not in actual_str.lower()

        if op in ('GREATER_THAN', 'GT', '>'):
            try:
                return float(actual_str) > float(expected_str)
            except (ValueError, TypeError):
                return actual_str > expected_str

        if op in ('LESS_THAN', 'LT', '<'):
            try:
                return float(actual_str) < float(expected_str)
            except (ValueError, TypeError):
                return actual_str < expected_str

        if op in ('REGEX_MATCH', 'REGEX'):
            try:
                return re.search(expected_str, actual_str) is not None
            except Exception:
                return False

        return actual_str.lower() == expected_str.lower()

    def _evaluate_assertions(self, response: httpx.Response, assertions: List[Dict[str, Any]], condition_hint: str = "EQUALS") -> List[Dict[str, Any]]:
        """Evaluate JSONPath and HTTP assertions on response body and status."""
        results = []
        parsed_json = None
        try:
            parsed_json = response.json()
        except Exception:
            pass

        if not assertions:
            is_success = 200 <= response.status_code < 300
            if condition_hint == "NOT_EQUALS":
                is_success = response.status_code >= 400
            results.append({
                "expression": "status_code",
                "condition": condition_hint,
                "operator": condition_hint,
                "expected": "2xx Success" if condition_hint == "EQUALS" else "4xx/5xx Error",
                "actual": response.status_code,
                "passed": is_success,
                "message": f"Status code verified: {response.status_code}"
            })
            return results

        for item in assertions:
            expr_str = item.get('expression', 'code')
            cond = (item.get('condition') or condition_hint or 'EQUALS').upper()
            expected = item.get('expectedValue', item.get('expected', '10000'))

            if expr_str in ('code', 'status', 'status_code') and (parsed_json is None or expr_str not in parsed_json):
                actual_val = response.status_code
            else:
                actual_val = self._extract_jsonpath(parsed_json, expr_str) if parsed_json is not None else None

            passed = self._evaluate_operator(actual_val, cond, expected)

            results.append({
                "expression": expr_str,
                "condition": cond,
                "operator": cond,
                "expected": expected,
                "actual": actual_val,
                "passed": passed,
                "message": "Passed" if passed else f"Assertion failed: expected '{expected}', got '{actual_val}'"
            })

        return results

    async def execute_case(self, client: httpx.AsyncClient, case: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single test case asynchronously."""
        async with self.semaphore:
            req_info = case.get('request') or {}
            raw_path = case.get('path') or req_info.get('path') or case.get('url', '/')
            rest_params = case.get('request_rest') or req_info.get('rest') or case.get('rest_params', [])
            resolved_path = self._substitute_path_variables(raw_path, rest_params)

            full_url = resolved_path if resolved_path.startswith(('http://', 'https://')) else f"{self.base_url}{resolved_path if resolved_path.startswith('/') else '/' + resolved_path}"
            method = (case.get('method') or req_info.get('method') or 'GET').upper()

            # Extract query parameters
            query_params = {}
            raw_query = case.get('request_query') or req_info.get('query') or case.get('query_params', [])
            for q in raw_query:
                if isinstance(q, dict):
                    name = q.get('param_name') or q.get('name')
                    val = q.get('param_value') if q.get('param_value') is not None else q.get('value')
                    if name:
                        query_params[name] = val

            # Extract body
            body_json = _resolve_body(case, req_info)
            if not isinstance(body_json, (dict, list)):
                body_json = None

            # Extract assertions
            assertions = []
            if 'assertions' in case and isinstance(case['assertions'], list):
                assertions = case['assertions']
            elif 'assertion_item' in case:
                assertions = [case['assertion_item']]
            elif 'jsonPathAssertion' in case:
                assertions = case['jsonPathAssertion'].get('assertions', [])

            condition_hint = case.get('assertion_condition', 'EQUALS')

            is_safe, resolved_ip, original_netloc = self._resolve_safe_target(full_url)
            if not is_safe:
                return {
                    "case_id": case.get('id', 'N/A'),
                    "name": case.get('name', 'Blocked URL'),
                    "method": method,
                    "url": full_url,
                    "passed": False,
                    "status": "FAILED",
                    "status_code": 0,
                    "latency_ms": 0,
                    "error": "URL target rejected by security policy (prohibited address).",
                    "assertions": []
                }

            headers = {
                "User-Agent": "CodeBrain-APITestRunner/2.0",
                "Accept": "application/json",
            }
            # Custom request headers
            custom_headers = case.get('headers') or req_info.get('headers', [])
            for h in custom_headers:
                if isinstance(h, dict) and h.get('name') and h.get('value'):
                    h_name = str(h['name']).strip()
                    if original_netloc and resolved_ip and h_name.lower() == 'host':
                        continue
                    headers[h_name] = str(h['value'])

            if body_json and not any(k.lower() == "content-type" for k in headers):
                headers["Content-Type"] = "application/json"

            request_url = full_url
            request_kwargs: Dict[str, Any] = {}
            if original_netloc and resolved_ip:
                parsed_full = urlparse(full_url)
                ip_host = f"[{resolved_ip}]" if ":" in resolved_ip and not resolved_ip.startswith("[") else resolved_ip
                pinned_netloc = f"{ip_host}:{parsed_full.port}" if parsed_full.port else ip_host
                request_url = urlunparse(parsed_full._replace(netloc=pinned_netloc))
                headers["Host"] = original_netloc
                if parsed_full.scheme == "https" and parsed_full.hostname:
                    request_kwargs["extensions"] = {"sni_hostname": parsed_full.hostname}

            start_time = time.perf_counter()
            try:
                response = await client.request(
                    method=method,
                    url=request_url,
                    params=query_params if query_params else None,
                    json=body_json,
                    headers=headers,
                    timeout=self.timeout,
                    **request_kwargs,
                )
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

                assertion_evals = self._evaluate_assertions(response, assertions, condition_hint)
                all_passed = all(a['passed'] for a in assertion_evals)

                return {
                    "case_id": case.get('id', 'TC'),
                    "name": case.get('name', f"{method} {resolved_path}"),
                    "method": method,
                    "url": full_url,
                    "passed": all_passed,
                    "status": "PASSED" if all_passed else "FAILED",
                    "status_code": response.status_code,
                    "latency_ms": elapsed_ms,
                    "assertions": assertion_evals,
                    "response_preview": response.text[:400]
                }

            except Exception as exc:
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return {
                    "case_id": case.get('id', 'TC'),
                    "name": case.get('name', f"{method} {resolved_path}"),
                    "method": method,
                    "url": full_url,
                    "passed": False,
                    "status": "ERROR",
                    "status_code": 0,
                    "latency_ms": elapsed_ms,
                    "error": f"Request exception: {str(exc)}",
                    "assertions": []
                }

    async def execute_suite(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a full test suite asynchronously and return execution summary."""
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            tasks = [self.execute_case(client, case) for case in test_cases]
            results = await asyncio.gather(*tasks)

        total = len(results)
        passed_count = sum(1 for r in results if r['passed'])
        failed_count = total - passed_count
        pass_rate = round((passed_count / total * 100), 1) if total > 0 else 0.0
        total_duration = round(sum(r['latency_ms'] for r in results), 2)
        avg_latency = round(total_duration / total, 1) if total > 0 else 0.0

        return {
            "total": total,
            "total_executed": total,
            "passed": passed_count,
            "failed": failed_count,
            "pass_rate": pass_rate,
            "total_duration_ms": total_duration,
            "avg_latency_ms": avg_latency,
            "results": results
        }
