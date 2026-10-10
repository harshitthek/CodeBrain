import React, { useState } from 'react';
import { CodeBrainService } from '../services/codebrainService';
import { TestCaseItem, ReflectionPipelineResult } from '../types/codebrain';

const PRESET_REQUIREMENTS = {
  checkout: `FEATURE: Autonomous Checkout & Payment Webhook Processing
- Users add items to cart and submit order via POST /api/checkout.
- Checkout generates Stripe payment intent and reserves inventory in Redis.
- Stripe asynchronously triggers POST /api/webhooks/payment with HMAC-SHA256 signature in X-Signature header.
- Webhook listener must verify signature against internal secret, transition order from PENDING to PAID, and ensure idempotent processing so duplicate deliveries never double-fulfill.
- Under downstream payment gateway timeout (>5000ms), circuit breaker must transition to OPEN and queue order to delayed retry topic.`,

  oauth: `FEATURE: Enterprise OAuth2 PKCE & JWT Token Rotation
- Clients initiate authorization with PKCE code_challenge (S256).
- Token endpoint POST /oauth/token exchanges code_verifier for access token (60-minute TTL) and refresh token (30-day TTL).
- Refresh token rotation: Every refresh request invalidates the previous token and issues a new pair.
- Replay attack mitigation: If an invalidated refresh token is presented, immediately revoke the entire lineage of tokens.
- Clock skew tolerance is strictly 300 seconds with cryptographic device fingerprinting.`,

  raft: `FEATURE: Distributed Raft Quorum Leader Election
- Nodes broadcast heartbeat RPC every 150-300ms with randomized jitter.
- If no heartbeat received within election timeout, follower increments term and transitions to Candidate.
- Candidate requests votes from all peers via RequestVote RPC.
- Leader elected once strict majority (N/2 + 1) votes acquired.
- If split vote occurs, election times out with backoff jitter and starts new term.
- Network partitions must reject writes if leader cannot reach quorum.`,
};

export const PipelineStudio: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [requirements, setRequirements] = useState<string>(PRESET_REQUIREMENTS.checkout);
  const [actorModel, setActorModel] = useState<string>('deepseek');
  const [minScore, setMinScore] = useState<number>(85);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [progressLog, setProgressLog] = useState<string[]>([]);
  const [progressPercent, setProgressPercent] = useState<number>(0);
  const [result, setResult] = useState<ReflectionPipelineResult | null>(null);
  const [exportNotice, setExportNotice] = useState<string | null>(null);

  const handleLaunch = async () => {
    setCurrentStep(3);
    setIsRunning(true);
    setProgressLog([]);
    setProgressPercent(10);
    setResult(null);

    try {
      const pipelineRes = await CodeBrainService.runPipeline(
        requirements,
        minScore,
        2,
        actorModel,
        (log, pct) => {
          setProgressLog((prev) => [...prev, log]);
          setProgressPercent(pct);
        }
      );
      setResult(pipelineRes);
      setCurrentStep(4);
    } catch (err: any) {
      setProgressLog((prev) => [...prev, `[ERROR] Reflection loop failed: ${err.message}`]);
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

    setExportNotice(`Exported ${exp.filename}`);
    setTimeout(() => setExportNotice(null), 3500);
  };

  return (
    <section id="pipeline" className="relative w-full bg-black py-24 md:py-32 overflow-hidden border-t border-white/[0.06]">
      {/* Background flare */}
      <div className="absolute top-1/2 left-1/3 w-[600px] h-[600px] bg-[#8052ff]/5 rounded-full blur-[160px] pointer-events-none" />

      <div className="max-w-[1240px] w-full mx-auto px-6 md:px-12 relative z-10">
        
        {/* Section Header: Sculptural typography */}
        <div className="mb-14">
          <span className="section-label">
            AUTONOMOUS ACTOR-CRITIC QA STUDIO
          </span>
          <h2 className="text-white text-[38px] sm:text-[52px] md:text-[64px] font-normal leading-[1.08] tracking-[-0.038em] mb-4">
            Closed-loop test generation.
          </h2>
          <p className="text-[#bdbdbd] font-[200] text-[18px] md:text-[19px] max-w-[580px] leading-[1.7]">
            Input raw requirements. The Generator (*Actor*) synthesizes test candidates, while the Reviewer (*Critic*) audits quality and guides bounded self-healing iterations.
          </p>
        </div>

        {/* Floating Minimalist Stepper Dock */}
        <div className="flex flex-wrap items-center gap-2 mb-10 p-1.5 rounded-full bg-white/[0.03] border border-white/[0.08] w-fit">
          {[
            { num: 1, label: '01 Requirements Intake' },
            { num: 2, label: '02 Reflection Bounds' },
            { num: 3, label: '03 Live Reflection' },
            { num: 4, label: '04 Verified Exports' },
          ].map((step) => {
            const isActive = currentStep === step.num;
            const isCompleted = currentStep > step.num;

            return (
              <button
                key={step.num}
                onClick={() => (!isRunning ? setCurrentStep(step.num) : null)}
                disabled={isRunning}
                className={`px-4 py-2 rounded-full text-xs font-mono uppercase tracking-[0.08em] transition-all duration-300 border-none cursor-pointer flex items-center gap-2 ${
                  isActive
                    ? 'bg-[#8052ff] text-white font-medium shadow-[0_0_20px_-2px_rgba(128,82,255,0.5)]'
                    : isCompleted
                    ? 'bg-white/[0.05] text-[#15846e]'
                    : 'bg-transparent text-[#9a9a9a] hover:text-white'
                }`}
              >
                {isCompleted && <span>✓</span>}
                <span>{step.label}</span>
              </button>
            );
          })}
        </div>

        {/* Step 1: Requirements Intake (Glass Studio Console) */}
        {currentStep === 1 && (
          <div className="glass-surface p-7 md:p-10 max-w-[1040px] space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-white/[0.06]">
              <span className="text-[#9a9a9a] text-xs uppercase font-mono tracking-wider flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#8052ff]" />
                Select Architectural Spec Template:
              </span>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setRequirements(PRESET_REQUIREMENTS.checkout)}
                  className="text-xs px-3.5 py-1.5 rounded-full bg-white/[0.04] hover:bg-white/[0.08] text-white transition-colors border border-white/[0.06] cursor-pointer font-mono"
                >
                  Payment Webhook
                </button>
                <button
                  type="button"
                  onClick={() => setRequirements(PRESET_REQUIREMENTS.oauth)}
                  className="text-xs px-3.5 py-1.5 rounded-full bg-white/[0.04] hover:bg-white/[0.08] text-white transition-colors border border-white/[0.06] cursor-pointer font-mono"
                >
                  OAuth2 Token Rotation
                </button>
                <button
                  type="button"
                  onClick={() => setRequirements(PRESET_REQUIREMENTS.raft)}
                  className="text-xs px-3.5 py-1.5 rounded-full bg-white/[0.04] hover:bg-white/[0.08] text-white transition-colors border border-white/[0.06] cursor-pointer font-mono"
                >
                  Raft Leader Election
                </button>
              </div>
            </div>

            <div className="relative">
              <textarea
                rows={9}
                value={requirements}
                onChange={(e) => setRequirements(e.target.value)}
                placeholder="Paste requirements, acceptance criteria, or OpenAPI JSON/YAML spec..."
                className="w-full bg-black/60 text-white font-mono text-[14px] leading-[1.7] rounded-[18px] p-6 border border-white/[0.08] focus:border-[#8052ff] focus:outline-none transition-colors selection:bg-[#8052ff]"
              />
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
              <span className="text-[#9a9a9a] text-xs font-[200]">
                Supports Markdown user stories, PRD documents, and OpenAPI contracts.
              </span>
              <button
                type="button"
                onClick={() => setCurrentStep(2)}
                className="btn-primary-pill"
              >
                Configure Reflection Parameters →
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Agent Reflection Parameters */}
        {currentStep === 2 && (
          <div className="glass-surface p-7 md:p-10 max-w-[1040px] space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              
              {/* Actor Model Selector */}
              <div className="space-y-3">
                <label className="block text-[#9a9a9a] text-xs uppercase font-semibold font-mono tracking-wider">
                  Generator (Actor) Model
                </label>
                <select
                  value={actorModel}
                  onChange={(e) => setActorModel(e.target.value)}
                  className="w-full bg-black/80 text-white text-[14px] font-mono rounded-[14px] p-4 border border-white/[0.1] focus:border-[#8052ff] focus:outline-none cursor-pointer"
                >
                  <option value="deepseek" className="bg-black">DeepSeek Coder (Default)</option>
                  <option value="qwen" className="bg-black">Qwen 2.5 Coder</option>
                  <option value="openai" className="bg-black">OpenAI GPT-4o</option>
                  <option value="ollama" className="bg-black">Ollama Local vLLM</option>
                </select>
                <span className="text-[#9a9a9a] text-[11px] font-[200] block">
                  Instantiated via Universal LLMServiceFactory
                </span>
              </div>

              {/* Target Quality Rubric Hurdle */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-[#9a9a9a] text-xs uppercase font-semibold font-mono tracking-wider">
                    Target Score Hurdle
                  </label>
                  <span className="text-[#ffb829] font-mono font-bold text-sm">
                    {minScore}%
                  </span>
                </div>
                <input
                  type="range"
                  min={65}
                  max={95}
                  value={minScore}
                  onChange={(e) => setMinScore(Number(e.target.value))}
                  className="w-full accent-[#8052ff] cursor-pointer mt-3"
                />
                <span className="text-[#9a9a9a] text-[11px] font-[200] block">
                  Critic threshold to trigger suite convergence
                </span>
              </div>

              {/* Monotonic Safeguard Invariant */}
              <div className="space-y-3">
                <label className="block text-[#9a9a9a] text-xs uppercase font-semibold font-mono tracking-wider">
                  Iteration Bound
                </label>
                <div className="bg-black/80 text-[#bdbdbd] text-[13px] font-mono rounded-[14px] p-4 border border-white/[0.08]">
                  Strict Bound = 2 Passes
                </div>
                <span className="text-[#9a9a9a] text-[11px] font-[200] block">
                  Guarantees monotonic score non-regression
                </span>
              </div>

            </div>

            <div className="flex items-center justify-between pt-4 border-t border-white/[0.06]">
              <button
                type="button"
                onClick={() => setCurrentStep(1)}
                className="ghost-link"
              >
                ← Back to Specification
              </button>

              <button
                type="button"
                onClick={handleLaunch}
                className="btn-primary-pill"
              >
                Launch Reflection Loop ⚡
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Live Reflection Telemetry */}
        {currentStep === 3 && (
          <div className="glass-surface p-7 md:p-10 max-w-[1040px] space-y-7">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
              <div>
                <span className="text-[#ffb829] text-xs uppercase font-mono tracking-widest block mb-1">
                  AUTONOMOUS EXECUTION IN PROGRESS
                </span>
                <h3 className="text-white text-xl font-normal tracking-[-0.02em]">
                  Actor-Critic Reflection Engine
                </h3>
              </div>
              <div className="text-xs font-mono text-[#15846e] px-3 py-1.5 rounded-full bg-[#15846e]/10 border border-[#15846e]/30">
                LIVE SSE TELEMETRY STREAM
              </div>
            </div>

            {/* Progress bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-mono text-[#9a9a9a]">
                <span>Convergence Progress</span>
                <span>{progressPercent}%</span>
              </div>
              <div className="w-full h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-[#8052ff] to-[#15846e] transition-all duration-300"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>

            {/* Reflection Dual Nodes Simulation */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
              <div className="bg-black/60 p-5 rounded-[18px] border border-white/[0.06] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono uppercase text-[#8052ff] font-semibold">
                    Node 01: Actor (Generator)
                  </span>
                  <span className="text-[10px] font-mono text-[#9a9a9a]">apps/ai_agents/test_case_generator/</span>
                </div>
                <p className="text-xs text-[#bdbdbd] font-[200]">
                  Synthesizing candidate test cases, equivalence partitions, boundary values, and negative exception paths.
                </p>
              </div>

              <div className="bg-black/60 p-5 rounded-[18px] border border-white/[0.06] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono uppercase text-[#ffb829] font-semibold">
                    Node 02: Critic (Reviewer)
                  </span>
                  <span className="text-[10px] font-mono text-[#9a9a9a]">apps/ai_agents/test_case_reviewer/</span>
                </div>
                <p className="text-xs text-[#bdbdbd] font-[200]">
                  Auditing completeness, coverage gaps, step feasibility, and rubric score vs. {minScore}% threshold.
                </p>
              </div>
            </div>

            {/* Console Log Terminal */}
            <div className="bg-black rounded-[18px] border border-white/[0.08] overflow-hidden">
              <div className="terminal-bar">
                <div className="terminal-dots">
                  <div className="terminal-dot bg-[#ff5f56]" />
                  <div className="terminal-dot bg-[#ffbd2e]" />
                  <div className="terminal-dot bg-[#27c93f]" />
                </div>
                <span className="text-[#9a9a9a] text-[11px] font-mono">
                  sse_emitter.py — thread-safe logger
                </span>
                <span className="w-12" />
              </div>

              <div className="p-5 font-mono text-xs space-y-2 max-h-[220px] overflow-y-auto">
                {progressLog.map((log, idx) => (
                  <div
                    key={idx}
                    className={`leading-relaxed ${
                      log.includes('[CONVERGED]')
                        ? 'text-[#15846e]'
                        : log.includes('[PASS')
                        ? 'text-[#ffb829]'
                        : 'text-[#bdbdbd]'
                    }`}
                  >
                    {log}
                  </div>
                ))}
                {isRunning && (
                  <div className="flex items-center gap-2 text-[#8052ff] animate-pulse">
                    <span>▶</span>
                    <span>Awaiting agent response token stream...</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Verified Test Cases & Enterprise TMS Exports */}
        {currentStep === 4 && result && (
          <div className="space-y-8 max-w-[1040px]">
            {/* Telemetry Summary Banner */}
            <div className="glass-surface p-7 md:p-8 grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <div className="text-[#9a9a9a] text-xs font-mono uppercase tracking-wider mb-1">
                  Suite Status
                </div>
                <div className="text-[#15846e] text-xl font-mono font-medium">
                  CONVERGED
                </div>
              </div>

              <div>
                <div className="text-[#9a9a9a] text-xs font-mono uppercase tracking-wider mb-1">
                  Rubric Score
                </div>
                <div className="text-[#ffb829] text-xl font-mono font-medium">
                  {result.highest_score.toFixed(1)} / 100
                </div>
              </div>

              <div>
                <div className="text-[#9a9a9a] text-xs font-mono uppercase tracking-wider mb-1">
                  Passes Taken
                </div>
                <div className="text-white text-xl font-mono font-medium">
                  {result.iterations_taken} Iterations
                </div>
              </div>

              <div>
                <div className="text-[#9a9a9a] text-xs font-mono uppercase tracking-wider mb-1">
                  Total Cases
                </div>
                <div className="text-white text-xl font-mono font-medium">
                  {result.best_test_cases.length} Items
                </div>
              </div>
            </div>

            {/* Generated Test Cases Table */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-white text-xl font-normal tracking-[-0.02em]">
                  Pydantic-Validated Test Suite ({result.best_test_cases.length})
                </h3>
                <span className="text-[#9a9a9a] text-xs font-mono">
                  Preserved via Monotonic Guard
                </span>
              </div>

              <div className="space-y-4">
                {result.best_test_cases.map((tc, idx) => (
                  <div
                    key={tc.id || idx}
                    className="glass-surface p-6 rounded-[20px] space-y-4 hover:border-white/[0.12] transition-colors"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-white/[0.05]">
                      <div className="flex items-center gap-3">
                        <span className="text-[#ffb829] font-mono text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#ffb829]/10 border border-[#ffb829]/20">
                          {tc.id}
                        </span>
                        <h4 className="text-white font-normal text-base">
                          {tc.title}
                        </h4>
                      </div>
                      <span className="text-xs font-mono uppercase px-2.5 py-0.5 rounded-full bg-white/[0.05] text-[#9a9a9a] self-start">
                        PRIORITY: {tc.priority}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                      <div>
                        <span className="text-[#9a9a9a] uppercase block mb-1">Preconditions:</span>
                        <p className="text-[#bdbdbd] font-[200] leading-relaxed">
                          {tc.preconditions}
                        </p>
                      </div>
                      <div>
                        <span className="text-[#9a9a9a] uppercase block mb-1">Expected Outcome:</span>
                        <p className="text-white font-[200] leading-relaxed">
                          {tc.expected_results}
                        </p>
                      </div>
                    </div>

                    <div>
                      <span className="text-[#9a9a9a] text-xs font-mono uppercase block mb-1">
                        Execution Steps:
                      </span>
                      <ol className="list-decimal list-inside text-xs font-mono text-[#bdbdbd] font-[200] space-y-1 pl-1">
                        {Array.isArray(tc.test_steps) ? (
                          tc.test_steps.map((st, sIdx) => <li key={sIdx}>{st}</li>)
                        ) : (
                          <li>{tc.test_steps}</li>
                        )}
                      </ol>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Enterprise TMS Export Action Strip */}
            <div className="glass-surface p-7 md:p-8 rounded-[24px] space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h4 className="text-white text-base font-normal mb-1">
                    Export Converged Test Suite to Enterprise Systems
                  </h4>
                  <p className="text-[#9a9a9a] text-xs font-[200]">
                    Strict schema validation. Zero formulas, injection-safe, and ready for CI/CD ingestion.
                  </p>
                </div>
                {exportNotice && (
                  <span className="text-[#15846e] text-xs font-mono animate-fade-in">
                    ✓ {exportNotice}
                  </span>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-3 pt-2">
                <button
                  onClick={() => handleExport('jira')}
                  className="text-xs px-4 py-2.5 rounded-full bg-white/[0.04] hover:bg-[#8052ff] hover:text-white text-[#bdbdbd] transition-all border border-white/[0.08] cursor-pointer font-mono uppercase tracking-wider"
                >
                  Download Jira Cloud (.json)
                </button>
                <button
                  onClick={() => handleExport('testrail')}
                  className="text-xs px-4 py-2.5 rounded-full bg-white/[0.04] hover:bg-[#8052ff] hover:text-white text-[#bdbdbd] transition-all border border-white/[0.08] cursor-pointer font-mono uppercase tracking-wider"
                >
                  Download TestRail (.csv)
                </button>
                <button
                  onClick={() => handleExport('junit')}
                  className="text-xs px-4 py-2.5 rounded-full bg-white/[0.04] hover:bg-[#8052ff] hover:text-white text-[#bdbdbd] transition-all border border-white/[0.08] cursor-pointer font-mono uppercase tracking-wider"
                >
                  Download JUnit XML (.xml)
                </button>
                <button
                  onClick={() => handleExport('markdown')}
                  className="text-xs px-4 py-2.5 rounded-full bg-white/[0.04] hover:bg-[#8052ff] hover:text-white text-[#bdbdbd] transition-all border border-white/[0.08] cursor-pointer font-mono uppercase tracking-wider"
                >
                  Download Mind-Map (.md)
                </button>
                <button
                  onClick={() => setCurrentStep(1)}
                  className="ghost-link ml-auto text-xs"
                >
                  Start New Session ↺
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </section>
  );
};
