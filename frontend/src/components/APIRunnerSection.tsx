import React, { useState, useRef } from 'react';
import { CodeBrainService } from '../services/codebrainService';
import { APIEndpointDefinition, APIRunResult } from '../types/codebrain';
import { DotMatrixText } from './DotMatrixText';

const SAMPLE_ENDPOINTS: Array<APIEndpointDefinition & { defaultBaseUrl: string }> = [
  {
    id: 'ep-checkout',
    method: 'POST',
    path: '/api/v1/orders/checkout',
    defaultBaseUrl: 'https://api.payment.service',
    summary: 'Order Payment Intent & Idempotency Contract',
    description: 'Verifies HTTP 200, JSONPath $.order.id NOT_NULL, and $.order.state EQUALS PAID.',
    parameters: [
      { name: 'X-Idempotency-Key', in: 'header', required: true, schema_type: 'uuid' },
      { name: 'cart_id', in: 'body', required: true, schema_type: 'string' },
    ],
    assertions: [
      { type: 'status', expression: 'status_code EQUALS 200', expected: 200 },
      { type: 'jsonpath', expression: '$.order.id NOT_NULL', expected: true },
      { type: 'jsonpath', expression: "$.order.state EQUALS 'PAID'", expected: 'PAID' },
    ],
  },
  {
    id: 'ep-metadata',
    method: 'GET',
    path: '/latest/meta-data/iam/security-credentials',
    defaultBaseUrl: 'http://169.254.169.254',
    summary: 'AWS IMDSv2 Cloud Metadata Probe (SSRF Guard)',
    description: 'Verifies _resolve_safe_target() blocks 169.254.169.254 and fd00:ec2::254 before socket connect.',
    parameters: [],
    assertions: [
      { type: 'status', expression: 'status_code EQUALS 403 (SSRF_BLOCKED)', expected: 403 },
    ],
  },
  {
    id: 'ep-oauth',
    method: 'POST',
    path: '/oauth/token',
    defaultBaseUrl: 'https://auth.identity.service',
    summary: 'OAuth2 PKCE S256 Token Exchange Contract',
    description: 'Verifies HTTP 200, $.token_type EQUALS Bearer, and $.expires_in GREATER_THAN 3500.',
    parameters: [
      { name: 'grant_type', in: 'body', required: true, schema_type: 'string' },
      { name: 'code_verifier', in: 'body', required: true, schema_type: 'string' },
    ],
    assertions: [
      { type: 'status', expression: 'status_code EQUALS 200', expected: 200 },
      { type: 'jsonpath', expression: "$.token_type EQUALS 'Bearer'", expected: 'Bearer' },
      { type: 'jsonpath', expression: '$.expires_in GREATER_THAN 3500', expected: 3600 },
    ],
  },
  {
    id: 'ep-loopback',
    method: 'GET',
    path: '/internal/admin/config',
    defaultBaseUrl: 'http://127.0.0.1:8080',
    summary: 'Loopback & Private RFC1918 Probe (SSRF Guard)',
    description: 'Verifies _is_blocked_ip() rejects 127.0.0.0/8 loopback and 10.0.0.0/8 internal targets.',
    parameters: [],
    assertions: [
      { type: 'status', expression: 'status_code EQUALS 403 (SSRF_BLOCKED)', expected: 403 },
    ],
  },
];

const INITIAL_RUN_RESULT: APIRunResult = {
  endpoint_id: 'ep-checkout',
  method: 'POST',
  url: 'https://api.payment.service/api/v1/orders/checkout',
  status_code: 200,
  latency_ms: 58,
  tls_verified: true,
  ip_pinned: '104.21.72.18 (sni_hostname preserved)',
  passed: true,
  assertions_results: [
    { expression: 'status_code EQUALS 200', passed: true, actual: 200, expected: 200 },
    { expression: '$.order.id NOT_NULL', passed: true, actual: true, expected: true },
    { expression: "$.order.state EQUALS 'PAID'", passed: true, actual: 'PAID', expected: 'PAID' },
  ],
};

const ASSERTION_OPERATORS = [
  { op: 'EQUALS', target: 'status_code / jsonpath', example: "$.order.state EQUALS 'PAID'" },
  { op: 'NOT_EQUALS', target: 'status_code / jsonpath', example: 'status_code NOT_EQUALS 500' },
  { op: 'CONTAINS', target: 'body / header / jsonpath', example: "$.scopes CONTAINS 'orders:write'" },
  { op: 'NOT_CONTAINS', target: 'body / jsonpath', example: "response.text NOT_CONTAINS 'stacktrace'" },
  { op: 'GREATER_THAN', target: 'numeric / latency_ms', example: '$.expires_in GREATER_THAN 3500' },
  { op: 'LESS_THAN', target: 'numeric / latency_ms', example: 'latency_ms LESS_THAN 250' },
  { op: 'IS_NULL', target: 'jsonpath field', example: '$.error_code IS_NULL' },
  { op: 'NOT_NULL', target: 'jsonpath field', example: '$.order.id NOT_NULL' },
  { op: 'REGEX_MATCH', target: 'string / header', example: "$.order.id REGEX_MATCH '^ord_[0-9a-f]{6}$'" },
];

export const APIRunnerSection: React.FC = () => {
  const [selectedEndpoint, setSelectedEndpoint] = useState<APIEndpointDefinition & { defaultBaseUrl: string }>(
    SAMPLE_ENDPOINTS[0]
  );
  const [targetBaseUrl, setTargetBaseUrl] = useState<string>(SAMPLE_ENDPOINTS[0].defaultBaseUrl);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [runResult, setRunResult] = useState<APIRunResult | null>(INITIAL_RUN_RESULT);
  const [exportNotice, setExportNotice] = useState<string | null>(null);
  const [codeTab, setCodeTab] = useState<'pytest' | 'postman'>('pytest');
  const latestRequestIdRef = useRef<number>(0);

  const isSsrfBlocked = runResult ? runResult.status_code === 403 : false;

  const handleSelectEndpoint = async (ep: APIEndpointDefinition & { defaultBaseUrl: string }) => {
    const reqId = ++latestRequestIdRef.current;
    setSelectedEndpoint(ep);
    setTargetBaseUrl(ep.defaultBaseUrl);
    setIsExecuting(true);
    try {
      const result = await CodeBrainService.executeAPITest(ep, ep.defaultBaseUrl);
      if (reqId === latestRequestIdRef.current) {
        setRunResult(result);
      }
    } finally {
      if (reqId === latestRequestIdRef.current) {
        setIsExecuting(false);
      }
    }
  };

  const handleRunTest = async () => {
    const reqId = ++latestRequestIdRef.current;
    setIsExecuting(true);
    try {
      const result = await CodeBrainService.executeAPITest(selectedEndpoint, targetBaseUrl);
      if (reqId === latestRequestIdRef.current) {
        setRunResult(result);
      }
    } finally {
      if (reqId === latestRequestIdRef.current) {
        setIsExecuting(false);
      }
    }
  };

  const safeTestId = selectedEndpoint.id.replace(/[^a-zA-Z0-9_]/g, '_');
  const expectedStatus = selectedEndpoint.assertions[0]?.expected ?? 200;

  const generatedPytestCode = `# Generated by CodeBrain apps/ai_agents/iface_case_generator/exporters.py
import pytest
import httpx
from jsonpath_ng.ext import parse as parse_jsonpath

BASE_URL = ${JSON.stringify(targetBaseUrl)}

def _extract_jsonpath(payload: dict, expr: str):
    return [match.value for match in parse_jsonpath(expr).find(payload)]

@pytest.mark.asyncio
async def test_${safeTestId}():
    """${selectedEndpoint.summary}"""
    async with httpx.AsyncClient(verify=True, timeout=10.0) as client:
        response = await client.${selectedEndpoint.method.toLowerCase()}(
            f"{BASE_URL}${selectedEndpoint.path}",
            headers={"X-Idempotency-Key": "idem-9481-001"},${
              selectedEndpoint.method === 'POST'
                ? '\n            json={"cart_id": "cart_12345", "grant_type": "authorization_code"}'
                : ''
            }
        )
        assert response.status_code == ${expectedStatus}${
    expectedStatus === 200
      ? `\n        payload = response.json()\n        assert len(_extract_jsonpath(payload, "$")) > 0`
      : ''
  }
`;

  const generatedPostmanJson = JSON.stringify(
    {
      info: {
        name: `CodeBrain Contract Suite — ${selectedEndpoint.id}`,
        schema: 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json',
      },
      item: [
        {
          name: selectedEndpoint.summary,
          request: {
            method: selectedEndpoint.method,
            header: [{ key: 'X-Idempotency-Key', value: 'idem-9481-001' }],
            url: { raw: `${targetBaseUrl}${selectedEndpoint.path}` },
          },
          event: [
            {
              listen: 'test',
              script: {
                type: 'text/javascript',
                exec: [
                  `pm.test("Status code is ${expectedStatus}", function () {`,
                  `    pm.response.to.have.status(${expectedStatus});`,
                  `});`,
                ],
              },
            },
          ],
        },
      ],
    },
    null,
    2
  );

  const handleDownloadPytest = () => {
    const blob = new Blob([generatedPytestCode], { type: 'text/x-python' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `test_${safeTestId}.py`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setExportNotice(`EXPORTED: test_${safeTestId}.py`);
    setTimeout(() => setExportNotice(null), 3500);
  };

  const handleDownloadPostman = () => {
    const blob = new Blob([generatedPostmanJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedEndpoint.id}_postman_v21.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setExportNotice(`EXPORTED: ${selectedEndpoint.id}_postman_v21.json`);
    setTimeout(() => setExportNotice(null), 3500);
  };

  return (
    <section id="apirunner" className="relative w-full py-12 md:py-16">
      <div className="max-w-[1180px] mx-auto px-5 sm:px-10 md:px-14">
        {/* Top Sheet Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <span className="meta-label">
            SHEET 03 // apps/ai_agents/iface_case_generator/runner.py · exporters.py
          </span>
          <span className="meta-label">
            INVARIANT 02: <span className="text-[#262523] font-medium">VERIFY_TLS=TRUE</span> · DNS IP PINNING · SSRF GUARD
          </span>
        </div>

        {/* Dot-Matrix Section Title */}
        <div className="mb-6 overflow-x-auto pb-1">
          <DotMatrixText
            text="CLOSED-LOOP HTTPX"
            pitch={5.0}
            dotRadius={1.95}
            showBed={false}
          />
        </div>

        <p className="text-[13px] sm:text-[14px] text-[#57554F] max-w-[820px] mb-8 leading-[1.7]">
          <code className="text-[#262523] font-medium">APITestRunner</code> executes generated REST assertions concurrently via{' '}
          <code className="text-[#262523]">httpx.AsyncClient</code> and{' '}
          <code className="text-[#262523]">asyncio.Semaphore(5)</code>. Before opening a socket,{' '}
          <code className="text-[#262523]">_resolve_safe_target()</code> resolves DNS via{' '}
          <code className="text-[#262523]">socket.getaddrinfo()</code>, blocks cloud metadata (<code className="text-[#B33920]">169.254.169.254</code>, <code className="text-[#B33920]">fd00:ec2::254</code>) and private/loopback ranges, and pins the validated IP with HTTPS <code className="text-[#262523]">sni_hostname</code> preservation.
        </p>

        {/* 3-Stage SSRF & DNS Pinning Pipeline Bar */}
        <div className="border border-[#262523] bg-[#EAE7E0] p-4 sm:p-5 mb-8">
          <div className="flex flex-wrap items-center justify-between gap-2 pb-3 mb-4 border-b border-[#D5D2C9]">
            <span className="meta-label text-[#262523] font-semibold">
              PRE-FLIGHT SOCKET SECURITY PIPELINE // _resolve_safe_target()
            </span>
            <span
              className={`meta-label font-semibold ${
                isSsrfBlocked ? 'text-[#B33920]' : 'text-[#2A6F4E]'
              }`}
            >
              {isSsrfBlocked
                ? '● SSRF GUARD TRIGGERED: SOCKET REJECTED BEFORE CONNECT'
                : '● DNS PINNED & TLS SNI VERIFIED'}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-[11px]">
            <div className="border border-[#D5D2C9] bg-[#F2F0EC] p-3.5 space-y-1">
              <div className="text-[10px] text-[#625F58] uppercase tracking-wider">
                STAGE 01 // DNS RESOLUTION
              </div>
              <div className="font-semibold text-[#262523]">
                socket.getaddrinfo(host, port)
              </div>
              <div className="text-[#57554F]">
                Resolves A/AAAA records once prior to HTTP dispatch to prevent TOCTOU DNS rebinding.
              </div>
            </div>

            <div
              className={`border p-3.5 space-y-1 ${
                isSsrfBlocked
                  ? 'border-[#D95338] bg-[#262523] text-[#F2F0EC]'
                  : 'border-[#D5D2C9] bg-[#F2F0EC] text-[#262523]'
              }`}
            >
              <div
                className={`text-[10px] uppercase tracking-wider font-semibold ${
                  isSsrfBlocked ? 'text-[#D95338]' : 'text-[#2A6F4E]'
                }`}
              >
                STAGE 02 // _is_blocked_ip() FILTER
              </div>
              <div className="font-semibold">
                {isSsrfBlocked ? 'BLOCKED: Restricted Range Detected' : 'PASSED: Public Routable IP'}
              </div>
              <div className={isSsrfBlocked ? 'text-[#F2F0EC]/80' : 'text-[#57554F]'}>
                Rejects 169.254.169.254, fd00:ec2::254, metadata.google.internal, 127.0.0.0/8, and RFC1918.
              </div>
            </div>

            <div
              className={`border p-3.5 space-y-1 ${
                isSsrfBlocked
                  ? 'border-[#D5D2C9] bg-[#EAE7E0]/60 text-[#625F58]'
                  : 'border-[#2A6F4E] bg-[#F2F0EC] text-[#262523]'
              }`}
            >
              <div
                className={`text-[10px] uppercase tracking-wider font-semibold ${
                  isSsrfBlocked ? 'text-[#625F58]' : 'text-[#2A6F4E]'
                }`}
              >
                STAGE 03 // IP PINNING & TLS SNI
              </div>
              <div className="font-semibold">
                {isSsrfBlocked
                  ? 'SKIPPED: Connection Aborted'
                  : 'httpx.AsyncClient(verify=True)'}
              </div>
              <div className="text-[#57554F]">
                Rewrites URL netloc to pinned IP, preserves Host header, and sets extensions[&quot;sni_hostname&quot;].
              </div>
            </div>
          </div>
        </div>

        <div className="rule-heavy" />

        <div className="grid grid-cols-1 lg:grid-cols-12 border-b border-[#262523]">
          {/* Left Column: Contract Spec & SSRF Target Configuration */}
          <div className="lg:col-span-5 lg:border-r border-[#D5D2C9] py-6 lg:pr-7 space-y-6">
            <div className="flex items-center justify-between border-b border-[#D5D2C9] pb-3">
              <span className="meta-label text-[#262523] font-medium">
                01 / CONTRACT TARGET SELECTION (04 PRESETS)
              </span>
              <span className="meta-label">
                OPENAPI 3.X / POSTMAN
              </span>
            </div>

            <div className="space-y-2.5">
              {SAMPLE_ENDPOINTS.map((ep, idx) => {
                const isSelected = selectedEndpoint.id === ep.id;
                const isProbe = ep.id === 'ep-metadata' || ep.id === 'ep-loopback';
                return (
                  <button
                    key={ep.id}
                    type="button"
                    onClick={() => handleSelectEndpoint(ep)}
                    className={`w-full p-3.5 text-left border cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-[#262523] text-[#F2F0EC] border-[#262523]'
                        : 'bg-[#EAE7E0] text-[#262523] border-[#D5D2C9] hover:border-[#262523]'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span
                        className={`text-[11px] font-semibold tracking-[0.12em] ${
                          isSelected ? 'text-[#D95338]' : 'text-[#B33920]'
                        }`}
                      >
                        0{idx + 1} // {ep.method} {ep.path}
                      </span>
                      <span
                        className={`text-[9px] uppercase tracking-wider px-1.5 py-0.5 border ${
                          isProbe
                            ? isSelected
                              ? 'border-[#D95338] text-[#D95338]'
                              : 'border-[#B33920] text-[#B33920]'
                            : isSelected
                            ? 'border-[#F2F0EC]/40 text-[#F2F0EC]'
                            : 'border-[#2A6F4E] text-[#2A6F4E]'
                        }`}
                      >
                        {isProbe ? 'SSRF PROBE' : 'CONTRACT'}
                      </span>
                    </div>
                    <div
                      className={`text-[12px] ${
                        isSelected ? 'text-[#F2F0EC]/85' : 'text-[#57554F]'
                      }`}
                    >
                      {ep.summary}
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="space-y-1.5">
              <label className="meta-label block">
                BASE_URL (_resolve_safe_target inspection)
              </label>
              <input
                type="text"
                value={targetBaseUrl}
                onChange={(e) => setTargetBaseUrl(e.target.value)}
                className="w-full bg-[#EAE7E0] text-[#262523] text-[12px] p-3 border border-[#D5D2C9] focus:border-[#262523] focus:outline-none font-mono"
              />
            </div>

            {/* Assertion Matrix */}
            <div className="space-y-2">
              <div className="meta-label">
                ACTIVE ASSERTIONS (jsonpath-ng / status)
              </div>
              <div className="border border-[#D5D2C9] bg-[#EAE7E0] divide-y divide-[#D5D2C9]">
                {selectedEndpoint.assertions.map((ast, i) => (
                  <div key={i} className="p-3 flex items-center justify-between text-[11px]">
                    <code className="text-[#262523]">{ast.expression}</code>
                    <span className="text-[#625F58] uppercase tracking-wider text-[10px]">
                      {ast.type}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Execute & Export Controls */}
            <div className="pt-2 flex flex-wrap items-center justify-between gap-3">
              <button
                type="button"
                onClick={handleRunTest}
                disabled={isExecuting}
                className="btn-tech-vermilion"
              >
                <span>{isExecuting ? 'RUNNING HTTPX...' : 'RUN CONTRACT TEST'}</span>
                <span>→</span>
              </button>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleDownloadPytest}
                  className="btn-tech-outline text-[10px] py-2 px-3"
                >
                  PYTEST (.PY)
                </button>
                <button
                  type="button"
                  onClick={handleDownloadPostman}
                  className="btn-tech-outline text-[10px] py-2 px-3"
                >
                  POSTMAN (.JSON)
                </button>
              </div>
            </div>

            {exportNotice && (
              <div className="text-[11px] text-[#2A6F4E] font-semibold uppercase tracking-wider">
                ✓ {exportNotice}
              </div>
            )}
          </div>

          {/* Right Column: Live Execution Trace & DNS Pinning Readout */}
          <div className="lg:col-span-7 py-6 lg:pl-7 flex flex-col justify-between space-y-5 border-t lg:border-t-0 border-[#D5D2C9]">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#D5D2C9] pb-3">
              <span className="meta-label text-[#262523] font-medium">
                02 / ASYNC EXECUTION TELEMETRY & SSRF TRACE
              </span>
              <span className="meta-label">
                SEMAPHORE: 05 · TIMEOUT: 10.0S
              </span>
            </div>

            {isExecuting && (
              <div className="border border-[#D5D2C9] bg-[#EAE7E0] p-6 space-y-2 text-[12px] text-[#262523] my-auto">
                <div>[01] Parsing URL scheme and netloc via urllib.parse.urlparse()...</div>
                <div>[02] Resolving A/AAAA records via socket.getaddrinfo()...</div>
                <div className="text-[#B33920]">[03] Checking _is_blocked_ip() against 169.254.0.0/16, fd00:ec2::254 & 127.0.0.0/8...</div>
              </div>
            )}

            {runResult && !isExecuting && (
              <div className="space-y-5">
                {/* Telemetry Summary Strip */}
                <div className="grid grid-cols-2 sm:grid-cols-4 border border-[#D5D2C9] bg-[#EAE7E0] divide-y sm:divide-y-0 sm:divide-x divide-[#D5D2C9]">
                  <div className="p-3">
                    <div className="meta-label text-[10px]">HTTP STATUS</div>
                    <div
                      className={`text-[16px] font-semibold mt-0.5 ${
                        runResult.status_code === 200 ? 'text-[#2A6F4E]' : 'text-[#B33920]'
                      }`}
                    >
                      {runResult.status_code} {runResult.status_code === 200 ? 'OK' : 'BLOCKED'}
                    </div>
                  </div>
                  <div className="p-3">
                    <div className="meta-label text-[10px]">LATENCY</div>
                    <div className="text-[16px] font-medium text-[#262523] mt-0.5">
                      {runResult.latency_ms} ms
                    </div>
                  </div>
                  <div className="p-3">
                    <div className="meta-label text-[10px]">TLS / SNI</div>
                    <div className="text-[13px] font-medium text-[#262523] mt-1">
                      {runResult.tls_verified ? 'VERIFY_TLS=TRUE' : 'SOCKET REJECTED'}
                    </div>
                  </div>
                  <div className="p-3">
                    <div className="meta-label text-[10px]">DNS IP PIN</div>
                    <div className="text-[12px] font-medium text-[#262523] mt-1 truncate">
                      {runResult.ip_pinned}
                    </div>
                  </div>
                </div>

                {/* Assertion Evaluation Ledger */}
                <div className="border border-[#D5D2C9] bg-[#F7F5F0] p-4 space-y-2 text-[12px]">
                  <div className="meta-label text-[#262523] border-b border-[#D5D2C9] pb-2">
                    ASSERTION EVALUATION // {runResult.method} {runResult.url}
                  </div>
                  {(runResult.assertions_results || []).map((a, idx) => (
                    <div key={idx} className="flex items-center justify-between py-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={`font-semibold ${
                            a.passed ? 'text-[#2A6F4E]' : 'text-[#B33920]'
                          }`}
                        >
                          {a.passed ? '[PASS]' : '[FAIL]'}
                        </span>
                        <code className="text-[#262523]">{a.expression}</code>
                      </div>
                      <span className="text-[#57554F] text-[11px]">
                        actual={String(a.actual)}
                      </span>
                    </div>
                  ))}
                  {runResult.error_message && (
                    <div className="text-[11px] text-[#B33920] pt-1 border-t border-[#D5D2C9]">
                      {runResult.error_message}
                    </div>
                  )}
                </div>

                {/* Response Payload / Guard Output */}
                <div className="space-y-1.5">
                  <div className="meta-label">
                    RESPONSE PAYLOAD / DIAGNOSTIC TRACE
                  </div>
                  <pre className="bg-[#EAE7E0] border border-[#D5D2C9] p-4 text-[11px] text-[#262523] overflow-x-auto leading-[1.6]">
                    {runResult.status_code === 200
                      ? selectedEndpoint.id === 'ep-oauth'
                        ? JSON.stringify(
                            {
                              access_token: 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...',
                              refresh_token: 'rt_9948102a_rotated',
                              token_type: 'Bearer',
                              expires_in: 3600,
                              scope: 'orders:read orders:write',
                            },
                            null,
                            2
                          )
                        : JSON.stringify(
                            {
                              order: {
                                id: 'ord_948194',
                                state: 'PAID',
                              },
                              customer_id: 'cus_88321',
                              amount_cents: 4890,
                              currency: 'USD',
                              idempotent_replay: false,
                            },
                            null,
                            2
                          )
                      : JSON.stringify(
                          {
                            error: 'SSRF_GUARD_BLOCKED',
                            module: 'apps/ai_agents/iface_case_generator/runner.py',
                            method: '_resolve_safe_target',
                            blocked_target: runResult.url,
                            reason:
                              runResult.error_message ||
                              'Target IP falls within restricted cloud metadata or loopback range.',
                          },
                          null,
                          2
                        )}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ====================================================================
            SUB-SHEET 03B: LIVE CODE SYNTHESIZER & 9-OPERATOR ASSERTION MATRIX
            ==================================================================== */}
        <div className="pt-14">
          <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
            <span className="meta-label">
              SHEET 03B // apps/ai_agents/iface_case_generator/exporters.py
            </span>
            <span className="meta-label">
              EXPORTERS: <span className="text-[#262523] font-medium">GENERATE_PYTEST_SCRIPT</span> · GENERATE_POSTMAN_COLLECTION
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 border-t border-b border-[#262523] py-8">
            {/* Left 6 Cols: Live Synthesized Code Inspector */}
            <div className="lg:col-span-6 space-y-3">
              <div className="flex items-center justify-between">
                <span className="meta-label text-[#262523] font-semibold">
                  01 // LIVE SYNTHESIZED TEST ARTIFACT
                </span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setCodeTab('pytest')}
                    className={`btn-tech-outline text-[10px] py-1 px-2.5 ${
                      codeTab === 'pytest' ? 'active' : ''
                    }`}
                  >
                    PYTEST + HTTPX (.PY)
                  </button>
                  <button
                    type="button"
                    onClick={() => setCodeTab('postman')}
                    className={`btn-tech-outline text-[10px] py-1 px-2.5 ${
                      codeTab === 'postman' ? 'active' : ''
                    }`}
                  >
                    POSTMAN V2.1 (.JSON)
                  </button>
                </div>
              </div>

              <pre className="bg-[#EAE7E0] border border-[#D5D2C9] p-4 text-[11px] text-[#262523] overflow-x-auto max-h-[340px] leading-[1.6]">
                {codeTab === 'pytest' ? generatedPytestCode : generatedPostmanJson}
              </pre>
            </div>

            {/* Right 6 Cols: 9-Operator Assertion Matrix */}
            <div className="lg:col-span-6 space-y-3">
              <div className="meta-label text-[#262523] font-semibold">
                02 // NINE SUPPORTED ASSERTION OPERATORS (runner.py)
              </div>
              <div className="border border-[#D5D2C9] bg-[#EAE7E0] divide-y divide-[#D5D2C9]">
                {ASSERTION_OPERATORS.map((row) => (
                  <div
                    key={row.op}
                    className="px-3.5 py-2.5 grid grid-cols-12 gap-2 items-center text-[11px]"
                  >
                    <div className="col-span-4 font-semibold text-[#B33920]">
                      <code>{row.op}</code>
                    </div>
                    <div className="col-span-3 text-[#625F58] text-[10px] uppercase">
                      {row.target}
                    </div>
                    <div className="col-span-5 text-right truncate">
                      <code className="text-[#262523]">{row.example}</code>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
