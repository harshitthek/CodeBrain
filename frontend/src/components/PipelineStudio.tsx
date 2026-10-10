import React, { useState } from 'react';
import { CodeBrainService } from '../services/codebrainService';
import { ReflectionPipelineResult } from '../types/codebrain';
import { DotMatrixText } from './DotMatrixText';

const PRESET_SPECS = {
  checkout: {
    code: '01',
    label: 'PAYMENT_WEBHOOK.MD',
    content: `FEATURE: Autonomous Checkout & Payment Webhook Processing
- Users add items to cart and submit order via POST /api/checkout.
- Checkout generates Stripe payment intent and reserves inventory in Redis.
- Stripe asynchronously triggers POST /api/webhooks/payment with HMAC-SHA256 signature in X-Signature header.
- Webhook listener must verify signature against internal secret, transition order from PENDING to PAID, and ensure idempotent processing so duplicate deliveries never double-fulfill.
- Under downstream payment gateway timeout (>5000ms), circuit breaker must transition to OPEN and queue order to delayed retry topic.`,
  },
  oauth: {
    code: '02',
    label: 'OAUTH2_PKCE.MD',
    content: `FEATURE: Enterprise OAuth2 PKCE & JWT Token Rotation
- Clients initiate authorization with PKCE code_challenge (S256).
- Token endpoint POST /oauth/token exchanges code_verifier for access token (60-minute TTL) and refresh token (30-day TTL).
- Refresh token rotation: Every refresh request invalidates the previous token and issues a new pair.
- Replay attack mitigation: If an invalidated refresh token is presented, immediately revoke the entire lineage of tokens.
- Clock skew tolerance is strictly 300 seconds with cryptographic device fingerprinting.`,
  },
  raft: {
    code: '03',
    label: 'RAFT_QUORUM.MD',
    content: `FEATURE: Distributed Raft Quorum Leader Election
- Nodes broadcast heartbeat RPC every 150-300ms with randomized jitter.
- If no heartbeat received within election timeout, follower increments term and transitions to Candidate.
- Candidate requests votes from all peers via RequestVote RPC.
- Leader elected once strict majority (N/2 + 1) votes acquired.
- If split vote occurs, election times out with backoff jitter and starts new term.
- Network partitions must reject writes if leader cannot reach quorum.`,
  },
};

const INITIAL_CONVERGED_RESULT: ReflectionPipelineResult = {
  success: true,
  converged: true,
  total_iterations: 2,
  max_iterations: 2,
  min_score: 85.0,
  highest_score: 93.5,
  iterations: [
    {
      iteration: 1,
      actor_model: 'deepseek',
      critic_model: 'critic-lead',
      cases_generated: 3,
      rubric: {
        score: 78.5,
        completeness: 82,
        coverage: 70,
        redundancy: 88,
        feasibility: 85,
        strengths: [
          'Structured positive-path steps with clear preconditions',
          'Valid HTTP status assertions and standard response fields',
        ],
        weaknesses: [
          'Missing negative security and fault-injection scenarios',
          'Boundary assertions needed for failure recovery and replay paths',
        ],
        suggestions: [
          'Incorporate explicit timeout/partition simulation',
          'Add cryptographic/security tampering assertions',
        ],
        missing_scenarios: [
          'Fault-injection degradation path',
          'Adversarial replay or spoofing vector',
        ],
        recommendation: 'Refine',
        comments:
          'Initial score 78.5% is below required 85.0%. Triggering targeted Pass 02 refinement.',
      },
      safeguard_triggered: false,
      timestamp: '2026-10-11T00:00:00.000Z',
      telemetry_logs: [
        'Initial generation completed via TestCaseGeneratorPrompt',
        'Critic rubric evaluation score: 78.5% (Target: 85.0%)',
      ],
    },
    {
      iteration: 2,
      actor_model: 'deepseek',
      critic_model: 'critic-lead',
      cases_generated: 5,
      rubric: {
        score: 93.5,
        completeness: 95,
        coverage: 92,
        redundancy: 94,
        feasibility: 96,
        strengths: [
          'Exceptional boundary and negative exception coverage',
          'Detailed security and cryptographic verification steps',
          'Explicit fault-tolerance assertions under degraded conditions',
        ],
        weaknesses: [],
        suggestions: ['Ready for direct export to Jira, TestRail, XMind, and JUnit XML'],
        missing_scenarios: [],
        recommendation: 'Pass',
        comments:
          'Refinement achieved 93.5% score. Monotonic regression safeguard verified monotonic quality increase (+15.0%).',
      },
      safeguard_triggered: false,
      timestamp: '2026-10-11T00:00:05.000Z',
      telemetry_logs: [
        'Targeted refinement pass executed with itemized Critic feedback',
        'Refined rubric evaluation score: 93.5% (Threshold passed)',
        'Monotonic regression check: Passed (no score drop)',
      ],
    },
  ],
  best_test_cases: [
    {
      id: 'TC-101',
      title: 'Verify standard successful checkout workflow with authorized token',
      description: 'Ensure checkout processes normally with positive balance and valid session.',
      test_steps: [
        'Send POST /api/checkout with valid cart_id and auth bearer token',
        'Verify payment intent created with Stripe payload',
        'Inspect database order state transition from PENDING to PAID',
      ],
      expected_results: [
        'HTTP 200 with order_id and tracking confirmation',
        'Cart marked as cleared in session cache',
      ],
      status: 'approved',
      priority: 'p0',
      feature: 'Checkout Flow',
      llm_provider: 'deepseek',
    },
    {
      id: 'TC-102',
      title: 'Verify payment webhook processing with valid HMAC signature',
      description: 'Webhook listener validates signature header and dispatches order fulfillment event.',
      test_steps: [
        'Post simulated Stripe event to /api/webhooks/payment with valid X-Signature',
        'Check signature verification using internal secret',
        'Confirm webhook idempotent replay returns HTTP 200 without duplicate billing',
      ],
      expected_results: [
        'HTTP 200 ACK returned in <200ms',
        'Fulfillment message queued to RabbitMQ',
      ],
      status: 'approved',
      priority: 'p0',
      feature: 'Payment Webhook',
      llm_provider: 'deepseek',
    },
    {
      id: 'TC-103',
      title: 'Boundary test: maximum cart item count and price overflow',
      description: 'Verify shopping cart rejects item count beyond 999 units.',
      test_steps: [
        'Add 1,000 items to active cart session',
        'Attempt checkout submission',
      ],
      expected_results: [
        'HTTP 422 Unprocessable Entity with error code ERR_CART_LIMIT_EXCEEDED',
      ],
      status: 'approved',
      priority: 'p1',
      feature: 'Boundary Validation',
      llm_provider: 'deepseek',
    },
    {
      id: 'TC-104',
      title: 'Exception test: Webhook signature tampering & invalid HMAC',
      description: 'Ensure forged or expired X-Signature header is rejected with 401 Unauthorized.',
      test_steps: [
        'Post simulated webhook with tampered body payload differing from signed digest',
        'Assert HMAC-SHA256 signature mismatch',
        'Verify audit log records SECURITY_SIGNATURE_MISMATCH event',
      ],
      expected_results: [
        'HTTP 401 Unauthorized with error message "Invalid signature digest"',
        'Zero order state modification or fulfillment actions triggered',
      ],
      status: 'approved',
      priority: 'p0',
      feature: 'Security & Auth',
      llm_provider: 'deepseek',
    },
    {
      id: 'TC-105',
      title: 'Resilience test: Downstream payment gateway 504 timeout & circuit breaker',
      description: 'Verify system executes circuit-breaker fallback when Stripe API response exceeds 5000ms.',
      test_steps: [
        'Simulate 6000ms latency on external payment gateway mock',
        'Submit customer checkout request',
        'Verify fallback queued to delayed retry topic with exponential backoff jitter',
      ],
      expected_results: [
        'HTTP 503 with user-friendly retry-after header',
        'Circuit breaker transitions from CLOSED to OPEN after 3 consecutive timeouts',
      ],
      status: 'approved',
      priority: 'p1',
      feature: 'Fault Tolerance',
      llm_provider: 'deepseek',
    },
  ],
};

const DESIGN_METHODS = [
  {
    code: 'M-01',
    name: 'Equivalence Partitioning',
    scope: 'Valid vs. invalid input classes (authorized session, expired token, malformed payload).',
    coverage: 'Reduces combinatorial explosion while preserving full domain class coverage.',
  },
  {
    code: 'M-02',
    name: 'Boundary Value Analysis',
    scope: 'Exact threshold edges (cart count 999 vs 1,000; clock skew +300s vs +301s; timeout 5,000ms).',
    coverage: 'Targets off-by-one and arithmetic overflow bugs at specification boundaries.',
  },
  {
    code: 'M-03',
    name: 'Decision Table Matrix',
    scope: 'Multi-condition state transitions (HMAC valid/invalid × Idempotency key new/replayed).',
    coverage: 'Verifies compound boolean business rules and state machine guards.',
  },
  {
    code: 'M-04',
    name: 'Orthogonal Array (OATS)',
    scope: 'Pairwise parameter combinations across headers, auth scopes, and payload permutations.',
    coverage: 'Maximizes pairwise defect detection with minimal test suite bloat.',
  },
  {
    code: 'M-05',
    name: 'Scenario & Fault Injection',
    scope: 'End-to-end user journeys coupled with downstream 504 timeouts and network partitions.',
    coverage: 'Validates circuit-breaker state machines, dead-letter queues, and rollback safety.',
  },
];

export const PipelineStudio: React.FC = () => {
  const [activePreset, setActivePreset] = useState<'checkout' | 'oauth' | 'raft'>('checkout');
  const [requirements, setRequirements] = useState<string>(PRESET_SPECS.checkout.content);
  const [actorModel, setActorModel] = useState<string>('deepseek');
  const [minScore, setMinScore] = useState<number>(85);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [progressLog, setProgressLog] = useState<string[]>([
    '[00:00.00] ActorCriticReflectionEngine initialized (max_iterations=2, monotonic_guard=ON).',
    '[00:01.20] Iteration 1: Actor synthesized 3 candidate test cases -> Critic scored 78.5% (< 85.0% hurdle).',
    '[00:03.80] [PASS 2] Constructing _build_refinement_input() with Critic itemized weaknesses & missing scenarios.',
    '[00:06.40] [CONVERGED] Iteration 2 scored 93.5% (+15.0%). Monotonic high-water suite (5 cases) locked.',
  ]);
  const [progressPercent, setProgressPercent] = useState<number>(100);
  const [result, setResult] = useState<ReflectionPipelineResult | null>(INITIAL_CONVERGED_RESULT);
  const [exportNotice, setExportNotice] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'ledger' | 'iterations' | 'schema'>('ledger');

  const handlePresetSelect = async (key: 'checkout' | 'oauth' | 'raft') => {
    if (isRunning) return;
    setActivePreset(key);
    const nextReq = PRESET_SPECS[key].content;
    setRequirements(nextReq);
    setIsRunning(true);
    setResult(null);
    setProgressLog([`[00:00.10] Loading SPEC ${PRESET_SPECS[key].code} (${PRESET_SPECS[key].label}) -> Running ActorCriticReflectionEngine...`]);
    setProgressPercent(20);

    try {
      const res = await CodeBrainService.runPipeline(
        nextReq,
        minScore,
        2,
        actorModel,
        (log, pct) => {
          setProgressLog((prev) => [...prev, log]);
          setProgressPercent(pct);
        }
      );
      setResult(res);
    } catch (err: any) {
      setResult(null);
      setProgressLog((prev) => [...prev, `[ERROR] ${err.message || 'Execution failed'}`]);
    } finally {
      setIsRunning(false);
    }
  };

  const handleRunReflection = async () => {
    if (isRunning) return;
    setIsRunning(true);
    setResult(null);
    setProgressLog(['[00:00.10] POST /pipeline/run/ -> Invoking ActorCriticReflectionEngine.run()...']);
    setProgressPercent(15);

    try {
      const res = await CodeBrainService.runPipeline(
        requirements,
        minScore,
        2,
        actorModel,
        (log, pct) => {
          setProgressLog((prev) => [...prev, log]);
          setProgressPercent(pct);
        }
      );
      setResult(res);
      setActiveView('ledger');
    } catch (err: any) {
      setResult(null);
      setProgressLog((prev) => [...prev, `[ERROR] ${err.message || 'Execution failed'}`]);
    } finally {
      setIsRunning(false);
    }
  };

  const handleExport = async (target: 'jira' | 'testrail' | 'markdown' | 'junit') => {
    if (!result || !result.best_test_cases.length) return;
    const exp = await CodeBrainService.exportTMS(target, result.best_test_cases, 'QA');

    const blob = new Blob([exp.content], { type: exp.mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = exp.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setExportNotice(`EXPORTED: ${exp.filename}`);
    setTimeout(() => setExportNotice(null), 3500);
  };

  const latestRubric = result?.iterations?.[result.iterations.length - 1]?.rubric;

  const schematicStatusLabel = isRunning
    ? '● EXECUTING PASSES...'
    : !result
    ? '● STANDBY'
    : result.converged
    ? `● CONVERGED AT PASS 0${result.total_iterations} (${result.highest_score.toFixed(1)} / 100)`
    : `● NOT CONVERGED AT PASS 0${result.total_iterations} (${result.highest_score.toFixed(1)} / 100)`;

  const stateReadout = isRunning
    ? 'REFLECTING'
    : !result
    ? 'STANDBY'
    : result.converged
    ? 'CONVERGED'
    : 'NOT CONVERGED';

  return (
    <section id="pipeline" className="relative w-full py-12 md:py-16">
      <div className="max-w-[1180px] mx-auto px-5 sm:px-10 md:px-14">
        {/* Top Sheet Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <span className="meta-label">
            SHEET 02 // apps/ai_agents/common/orchestrator.py · views.py (/pipeline/)
          </span>
          <span className="meta-label">
            INVARIANT 01: <span className="text-[#262523] font-medium">MAX_ITERATIONS = 02</span> · MONOTONIC REGRESSION SAFEGUARD
          </span>
        </div>

        {/* Dot-Matrix Section Title */}
        <div className="mb-6 overflow-x-auto pb-1">
          <DotMatrixText
            text="ACTOR-CRITIC LOOP"
            pitch={5.0}
            dotRadius={1.95}
            showBed={false}
          />
        </div>

        <p className="text-[13px] sm:text-[14px] text-[#57554F] max-w-[820px] mb-8 leading-[1.7]">
          <code className="text-[#262523] font-medium">ActorCriticReflectionEngine</code> pairs{' '}
          <code className="text-[#262523]">TestCaseGeneratorAgent</code> (Actor) with{' '}
          <code className="text-[#262523]">TestCaseReviewerAgent</code> (Critic). When Pass 01 scores below{' '}
          <code className="text-[#B33920] font-medium">min_score ({minScore}.0)</code>,{' '}
          <code className="text-[#262523]">_build_refinement_input()</code> feeds itemized weaknesses and missing edge scenarios into Pass 02 while tracking the monotonic high-water suite across iterations.
        </p>

        {/* Animated Architectural Feedback Loop Schematic Bar */}
        <div className="border border-[#262523] bg-[#EAE7E0] p-4 sm:p-5 mb-8">
          <div className="flex flex-wrap items-center justify-between gap-2 pb-3 mb-4 border-b border-[#D5D2C9]">
            <span className="meta-label text-[#262523] font-semibold">
              CLOSED-LOOP REFLECTION TOPOLOGY // GENERATOR ⇄ REVIEWER CONVERGENCE
            </span>
            <span
              className={`meta-label font-semibold ${
                isRunning || (result && !result.converged)
                  ? 'text-[#B33920]'
                  : result?.converged
                  ? 'text-[#2A6F4E]'
                  : 'text-[#625F58]'
              }`}
            >
              {schematicStatusLabel}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-stretch text-[11px]">
            <div className="border border-[#D5D2C9] bg-[#F2F0EC] p-3 flex flex-col justify-between">
              <div className="text-[10px] text-[#625F58] uppercase tracking-wider">STAGE 01 // INPUT</div>
              <div className="font-semibold text-[#262523] mt-1">PRD & Spec Ingestion</div>
              <div className="text-[10px] text-[#57554F] mt-1">
                <code>prd_analyzer</code> (.docx pypandoc / .md / .txt)
              </div>
            </div>

            <div className="border border-[#262523] bg-[#262523] text-[#F2F0EC] p-3 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[#D95338] uppercase tracking-wider font-semibold">STAGE 02 // ACTOR</span>
                <span className="w-2 h-2 rounded-full bg-[#D95338]" />
              </div>
              <div className="font-semibold mt-1">TestCaseGeneratorAgent</div>
              <div className="text-[10px] text-[#F2F0EC]/75 mt-1">
                Synthesizes Pydantic v2 <code>GeneratedTestCaseItem</code> suite
              </div>
            </div>

            <div className="border border-[#B33920] bg-[#F2F0EC] p-3 flex flex-col justify-between">
              <div className="text-[10px] text-[#B33920] uppercase tracking-wider font-semibold">
                STAGE 03 // CRITIC ⇄ LOOP
              </div>
              <div className="font-semibold text-[#262523] mt-1">TestCaseReviewerAgent</div>
              <div className="text-[10px] text-[#57554F] mt-1">
                Audits 4 dimensions; triggers Pass 02 if <code>score &lt; {minScore}.0</code>
              </div>
            </div>

            <div className="border border-[#D5D2C9] bg-[#F2F0EC] p-3 flex flex-col justify-between">
              <div className="text-[10px] text-[#2A6F4E] uppercase tracking-wider font-semibold">STAGE 04 // SAFEGUARD</div>
              <div className="font-semibold text-[#262523] mt-1">Monotonic High-Water</div>
              <div className="text-[10px] text-[#57554F] mt-1">
                Retains <code>best_test_cases</code> if Pass 02 regresses
              </div>
            </div>

            <div className="border border-[#D5D2C9] bg-[#F2F0EC] p-3 flex flex-col justify-between">
              <div className="text-[10px] text-[#625F58] uppercase tracking-wider">STAGE 05 // SYNC</div>
              <div className="font-semibold text-[#262523] mt-1">Enterprise TMS Export</div>
              <div className="text-[10px] text-[#57554F] mt-1">
                Jira · TestRail · XMind (.xmind) · JUnit XML · XLSX
              </div>
            </div>
          </div>
        </div>

        <div className="rule-heavy" />

        {/* Split Engineering Datasheet Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 border-b border-[#262523]">
          {/* Left Column: Specification Input & Parameters (5 cols) */}
          <div className="lg:col-span-5 lg:border-r border-[#D5D2C9] py-6 lg:pr-7 space-y-6">
            <div className="flex items-center justify-between border-b border-[#D5D2C9] pb-3">
              <span className="meta-label text-[#262523] font-medium">
                01 / REQUIREMENT SPECIFICATION
              </span>
              <span className="meta-label text-[#B33920]">
                .DOCX · .MD · .TXT
              </span>
            </div>

            {/* Preset Spec Selector */}
            <div className="grid grid-cols-3 gap-2">
              {(Object.keys(PRESET_SPECS) as Array<'checkout' | 'oauth' | 'raft'>).map((key) => {
                const spec = PRESET_SPECS[key];
                const isSelected = activePreset === key;
                return (
                  <button
                    key={key}
                    type="button"
                    disabled={isRunning}
                    onClick={() => handlePresetSelect(key)}
                    className={`p-2.5 text-left border cursor-pointer transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                      isSelected
                        ? 'bg-[#262523] text-[#F2F0EC] border-[#262523]'
                        : 'bg-[#EAE7E0] text-[#57554F] border-[#D5D2C9] hover:border-[#262523]'
                    }`}
                  >
                    <div
                      className={`text-[10px] tracking-[0.14em] ${
                        isSelected ? 'text-[#D95338]' : 'text-[#625F58]'
                      }`}
                    >
                      SPEC {spec.code}
                    </div>
                    <div className="text-[11px] font-medium truncate mt-0.5">
                      {spec.label}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Editable PRD / Requirement Spec Well */}
            <div>
              <textarea
                rows={10}
                value={requirements}
                onChange={(e) => setRequirements(e.target.value)}
                className="w-full bg-[#EAE7E0] text-[#262523] text-[12px] leading-[1.65] p-4 border border-[#D5D2C9] focus:border-[#262523] focus:outline-none resize-none font-mono"
                placeholder="Paste requirement specification or user stories..."
              />
            </div>

            {/* Parameter Controls: LLMServiceFactory & min_score */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-[#D5D2C9]">
              <div className="space-y-1.5">
                <label className="meta-label block">
                  LLM_PROVIDER (apps/llm/base.py)
                </label>
                <select
                  value={actorModel}
                  onChange={(e) => setActorModel(e.target.value)}
                  className="w-full bg-[#EAE7E0] text-[#262523] text-[12px] p-2.5 border border-[#D5D2C9] focus:border-[#262523] focus:outline-none cursor-pointer font-mono"
                >
                  <option value="deepseek">deepseek (DeepSeekChatModel)</option>
                  <option value="qwen">qwen (QwenChatModel)</option>
                  <option value="openai">openai (ChatOpenAI)</option>
                  <option value="groq">groq (ChatOpenAI)</option>
                  <option value="ollama">ollama (ChatOpenAI)</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <span className="meta-label">MIN_SCORE HURDLE</span>
                  <span className="text-[12px] font-semibold text-[#B33920]">
                    {minScore}.0 / 100
                  </span>
                </div>
                <input
                  type="range"
                  min={70}
                  max={95}
                  value={minScore}
                  onChange={(e) => setMinScore(Number(e.target.value))}
                  className="w-full accent-[#B33920] cursor-pointer mt-2"
                />
              </div>
            </div>

            {/* Trigger Button */}
            <div className="pt-2 flex items-center justify-between gap-4">
              <div className="meta-label">
                ROUTE: <span className="text-[#262523]">POST /pipeline/run/</span>
              </div>
              <button
                type="button"
                onClick={handleRunReflection}
                disabled={isRunning}
                className="btn-tech-vermilion"
              >
                <span>{isRunning ? 'EXECUTING PASSES...' : 'EXECUTE REFLECTION'}</span>
                <span>→</span>
              </button>
            </div>
          </div>

          {/* Right Column: Rubric Telemetry, SSE Log & Converged Suite (7 cols) */}
          <div className="lg:col-span-7 py-6 lg:pl-7 flex flex-col justify-between space-y-6 border-t lg:border-t-0 border-[#D5D2C9]">
            {/* Top Telemetry Header & View Switcher */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#D5D2C9] pb-3">
              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={() => setActiveView('ledger')}
                  className={`bg-transparent border-none cursor-pointer text-[11px] uppercase tracking-[0.14em] p-0 ${
                    activeView === 'ledger'
                      ? 'text-[#262523] font-semibold underline underline-offset-4'
                      : 'text-[#625F58] hover:text-[#262523]'
                  }`}
                >
                  02A / CONVERGED SUITE ({result?.best_test_cases.length || 0})
                </button>
                <span className="text-[#D5D2C9]">/</span>
                <button
                  type="button"
                  onClick={() => setActiveView('iterations')}
                  className={`bg-transparent border-none cursor-pointer text-[11px] uppercase tracking-[0.14em] p-0 ${
                    activeView === 'iterations'
                      ? 'text-[#262523] font-semibold underline underline-offset-4'
                      : 'text-[#625F58] hover:text-[#262523]'
                  }`}
                >
                  02B / PASS 01 vs PASS 02 DIFF ({result?.total_iterations || 0})
                </button>
                <span className="text-[#D5D2C9]">/</span>
                <button
                  type="button"
                  onClick={() => setActiveView('schema')}
                  className={`bg-transparent border-none cursor-pointer text-[11px] uppercase tracking-[0.14em] p-0 ${
                    activeView === 'schema'
                      ? 'text-[#262523] font-semibold underline underline-offset-4'
                      : 'text-[#625F58] hover:text-[#262523]'
                  }`}
                >
                  02C / PYDANTIC JSON
                </button>
              </div>

              <div className="meta-label">
                STATE:{' '}
                <span
                  className={
                    isRunning || (result && !result.converged)
                      ? 'text-[#B33920] font-semibold'
                      : result?.converged
                      ? 'text-[#2A6F4E] font-semibold'
                      : 'text-[#262523]'
                  }
                >
                  {stateReadout}
                </span>
              </div>
            </div>

            {/* 4-Dimension Rubric Readout Strip */}
            <div className="grid grid-cols-2 sm:grid-cols-5 border border-[#D5D2C9] bg-[#EAE7E0] divide-y sm:divide-y-0 sm:divide-x divide-[#D5D2C9]">
              <div className="p-3">
                <div className="meta-label text-[10px]">BEST SCORE</div>
                <div className="text-[18px] font-semibold text-[#B33920] mt-0.5">
                  {result ? `${result.highest_score.toFixed(1)}` : isRunning ? `${progressPercent}%` : '--'}
                </div>
              </div>
              <div className="p-3">
                <div className="meta-label text-[10px]">COMPLETENESS</div>
                <div className="text-[16px] font-medium text-[#262523] mt-0.5">
                  {latestRubric ? `${latestRubric.completeness}%` : '--'}
                </div>
              </div>
              <div className="p-3">
                <div className="meta-label text-[10px]">COVERAGE</div>
                <div className="text-[16px] font-medium text-[#262523] mt-0.5">
                  {latestRubric ? `${latestRubric.coverage}%` : '--'}
                </div>
              </div>
              <div className="p-3">
                <div className="meta-label text-[10px]">FEASIBILITY</div>
                <div className="text-[16px] font-medium text-[#262523] mt-0.5">
                  {latestRubric ? `${latestRubric.feasibility}%` : '--'}
                </div>
              </div>
              <div className="p-3 col-span-2 sm:col-span-1">
                <div className="meta-label text-[10px]">REDUNDANCY</div>
                <div className="text-[16px] font-medium text-[#262523] mt-0.5">
                  {latestRubric ? `${latestRubric.redundancy}%` : '--'}
                </div>
              </div>
            </div>

            {/* Live ProgressRegistry / SSELogEmitter Output */}
            <div className="border border-[#D5D2C9] bg-[#EAE7E0] p-3.5 space-y-1.5 max-h-[135px] overflow-y-auto text-[11px]">
              <div className="flex items-center justify-between text-[#625F58] pb-1 border-b border-[#D5D2C9] uppercase tracking-wider text-[10px]">
                <span>SSE STREAM // apps/utils/progress_registry.py</span>
                <span>TASK_CONTEXT: ACTIVE</span>
              </div>
              {progressLog.map((line, i) => (
                <div
                  key={i}
                  className={
                    line.includes('[CONVERGED]')
                      ? 'text-[#2A6F4E] font-medium'
                      : line.includes('[PASS 2]') || line.includes('[ERROR]')
                      ? 'text-[#B33920] font-medium'
                      : 'text-[#57554F]'
                  }
                >
                  {line}
                </div>
              ))}
            </div>

            {/* Main Output Area: Test Cases Ledger OR Iteration Diff OR Pydantic JSON */}
            {result && activeView === 'ledger' && (
              <div className="space-y-4">
                <div className="divide-y divide-[#D5D2C9] border border-[#D5D2C9] bg-[#F7F5F0] max-h-[300px] overflow-y-auto">
                  {result.best_test_cases.map((tc, idx) => (
                    <div key={tc.id || idx} className="p-4 space-y-2">
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2.5">
                          <span className="text-[11px] font-semibold text-[#B33920]">
                            {String(idx + 1).padStart(2, '0')} // {tc.id}
                          </span>
                          <span className="text-[13px] font-medium text-[#262523]">
                            {tc.title}
                          </span>
                        </div>
                        <span className="text-[10px] uppercase tracking-[0.14em] px-2 py-0.5 border border-[#262523] text-[#262523] font-medium">
                          {tc.priority}
                        </span>
                      </div>

                      <div className="text-[11px] text-[#57554F] pl-4 border-l border-[#D5D2C9] space-y-1">
                        <div>
                          <span className="text-[#625F58] uppercase">Steps: </span>
                          {tc.test_steps.join(' → ')}
                        </div>
                        <div>
                          <span className="text-[#2A6F4E] uppercase font-medium">Expected: </span>
                          {Array.isArray(tc.expected_results)
                            ? tc.expected_results.join(' · ')
                            : tc.expected_results}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result && activeView === 'iterations' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.iterations.map((iter) => (
                  <div
                    key={iter.iteration}
                    className="border border-[#D5D2C9] bg-[#F7F5F0] p-4 space-y-2.5 text-[12px]"
                  >
                    <div className="flex items-center justify-between border-b border-[#D5D2C9] pb-2">
                      <span className="font-semibold text-[#262523] uppercase tracking-wider">
                        ITERATION 0{iter.iteration} ({iter.cases_generated} CASES)
                      </span>
                      <span
                        className={`font-semibold ${
                          iter.rubric.recommendation === 'Pass'
                            ? 'text-[#2A6F4E]'
                            : 'text-[#B33920]'
                        }`}
                      >
                        {iter.rubric.score.toFixed(1)} / 100 [{iter.rubric.recommendation.toUpperCase()}]
                      </span>
                    </div>
                    <p className="text-[11px] text-[#57554F]">{iter.rubric.comments}</p>
                    {iter.rubric.weaknesses.length > 0 && (
                      <div className="text-[11px] space-y-1">
                        <div className="text-[#B33920] uppercase tracking-wider text-[10px]">
                          Critic Identified Weaknesses:
                        </div>
                        {iter.rubric.weaknesses.map((w, wi) => (
                          <div key={wi} className="text-[#57554F]">
                            - {w}
                          </div>
                        ))}
                      </div>
                    )}
                    {iter.rubric.strengths.length > 0 && (
                      <div className="text-[11px] space-y-1">
                        <div className="text-[#2A6F4E] uppercase tracking-wider text-[10px]">
                          Verified Strengths:
                        </div>
                        {iter.rubric.strengths.map((s, si) => (
                          <div key={si} className="text-[#57554F]">
                            + {s}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {result && activeView === 'schema' && (
              <pre className="bg-[#EAE7E0] border border-[#D5D2C9] p-4 text-[11px] text-[#262523] overflow-x-auto max-h-[300px] leading-[1.6]">
                {JSON.stringify(result.best_test_cases, null, 2)}
              </pre>
            )}

            {/* Enterprise Exporters Bar (apps/core/exporters/) */}
            <div className="pt-3 border-t border-[#D5D2C9] flex flex-wrap items-center justify-between gap-3">
              <div className="meta-label">
                {exportNotice ? (
                  <span className="text-[#2A6F4E] font-semibold">✓ {exportNotice}</span>
                ) : (
                  <span>EXPORTERS // apps/core/exporters/</span>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  disabled={!result}
                  onClick={() => handleExport('jira')}
                  className="btn-tech-outline text-[10px] py-1.5 px-3 disabled:opacity-40"
                >
                  JIRA (.JSON)
                </button>
                <button
                  type="button"
                  disabled={!result}
                  onClick={() => handleExport('testrail')}
                  className="btn-tech-outline text-[10px] py-1.5 px-3 disabled:opacity-40"
                >
                  TESTRAIL (.JSON)
                </button>
                <button
                  type="button"
                  disabled={!result}
                  onClick={() => handleExport('junit')}
                  className="btn-tech-outline text-[10px] py-1.5 px-3 disabled:opacity-40"
                >
                  JUNIT (.XML)
                </button>
                <button
                  type="button"
                  disabled={!result}
                  onClick={() => handleExport('markdown')}
                  className="btn-tech-outline text-[10px] py-1.5 px-3 disabled:opacity-40"
                >
                  XMIND MAP (.MD)
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* ====================================================================
            SUB-SHEET 02B: PRD ANALYZER, TEST DESIGN METHODS & PYDANTIC V2 SCHEMAS
            ==================================================================== */}
        <div className="pt-14">
          <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
            <span className="meta-label">
              SHEET 02B // apps/ai_agents/test_case_generator/schemas.py · prd_analyzer/views.py
            </span>
            <span className="meta-label">
              VALIDATION: <span className="text-[#262523] font-medium">PYDANTIC V2 NORMALIZATION</span> · XLSX FORMULA GUARD
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 border-t border-b border-[#262523] py-8">
            {/* Left 6 Cols: 5 Test Design Methodologies */}
            <div className="lg:col-span-6 space-y-4">
              <div className="meta-label text-[#262523] font-semibold">
                01 // FIVE FORMAL TEST DESIGN METHODOLOGIES (prompts.py)
              </div>
              <div className="divide-y divide-[#D5D2C9] border border-[#D5D2C9] bg-[#EAE7E0]">
                {DESIGN_METHODS.map((dm) => (
                  <div key={dm.code} className="p-3.5 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-[12px] font-semibold text-[#262523]">
                        <span className="text-[#B33920] mr-2">{dm.code}</span>
                        {dm.name}
                      </span>
                    </div>
                    <p className="text-[11px] text-[#57554F]">{dm.scope}</p>
                    <div className="text-[10px] text-[#2A6F4E] uppercase tracking-wider">
                      ✓ {dm.coverage}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right 6 Cols: Pydantic v2 Repair, PRD Isolation & Excel Sanitizer */}
            <div className="lg:col-span-6 space-y-5">
              <div className="meta-label text-[#262523] font-semibold">
                02 // PYDANTIC V2 SCHEMA REPAIR & SECURITY SAFEGUARDS
              </div>

              <div className="border border-[#D5D2C9] bg-[#EAE7E0] p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[12px] font-semibold text-[#262523]">
                    Pydantic v2 Output Validation & JSON Fence Repair
                  </span>
                  <span className="text-[10px] text-[#B33920] font-semibold">
                    schemas.py
                  </span>
                </div>
                <p className="text-[11px] text-[#57554F] leading-[1.6]">
                  <code>GeneratedTestCaseItem</code> and <code>extract_and_parse_test_cases()</code> strip markdown code fences, repair trailing commas in raw LLM outputs, coerce string or list <code>test_steps</code>, <code>expected_results</code>, and <code>preconditions</code>, and reject empty required fields before committing to the database.
                </p>
              </div>

              <div className="border border-[#D5D2C9] bg-[#EAE7E0] p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[12px] font-semibold text-[#262523]">
                    PRD Analyzer Concurrent Tempfile & Tab Mode Isolation
                  </span>
                  <span className="text-[10px] text-[#B33920] font-semibold">
                    prd_analyzer/views.py
                  </span>
                </div>
                <p className="text-[11px] text-[#57554F] leading-[1.6]">
                  <code>extract_content_from_file()</code> converts uploaded <code>.docx</code> specifications via <code>pypandoc</code> using isolated per-request <code>tempfile.NamedTemporaryFile(delete=False)</code> cleaned up inside a <code>finally</code> block, eliminating race conditions across concurrent workers.
                </p>
              </div>

              <div className="border border-[#D5D2C9] bg-[#EAE7E0] p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[12px] font-semibold text-[#262523]">
                    Reviewer .xlsx Formula-Injection Sanitizer & RBAC Guard
                  </span>
                  <span className="text-[10px] text-[#2A6F4E] font-semibold">
                    test_case_reviewer/views.py
                  </span>
                </div>
                <p className="text-[11px] text-[#57554F] leading-[1.6]">
                  <code>export_test_cases_excel()</code> enforces <code>@permission_required('core.view_testcase')</code>, preserves stored case priority, and forces <code>cell.data_type = 's'</code> with leading <code>=</code> prefix escaping so malicious test inputs never execute as spreadsheet formulas.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
