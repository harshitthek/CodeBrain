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
    <section id="pipeline" className="relative w-full bg-black py-28 md:py-36 overflow-hidden border-t border-white/[0.05]">
      {/* Background flare */}
      <div className="absolute top-1/2 left-1/3 w-[600px] h-[600px] bg-[#8052ff]/5 rounded-full blur-[160px] pointer-events-none" />

      <div className="max-w-[1280px] w-full mx-auto px-6 md:px-12 relative z-10">
        
        {/* Section Header: Sculptural typography */}
        <div className="mb-16">
          <span className="section-label">
            AUTONOMOUS ACTOR-CRITIC QA STUDIO
          </span>
          <h2 className="text-white text-[42px] sm:text-[56px] md:text-[72px] lg:text-[78px] font-normal leading-[1.08] tracking-[-0.038em] mb-5">
            Closed-loop test generation.
          </h2>
          <p className="text-[#bdbdbd] font-[200] text-[18px] md:text-[19px] max-w-[560px] leading-[1.7]">
            Input raw requirements. The Generator (*Actor*) synthesizes test candidates, while the Reviewer (*Critic*) audits quality and guides bounded self-healing iterations.
          </p>
        </div>

        {/* Floating Minimalist Stepper Dock */}
        <div className="flex flex-wrap items-center gap-2 mb-10 p-1.5 rounded-full bg-white/[0.03] border border-white/[0.06] w-fit">
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
                className={`px-5 py-2.5 rounded-full text-xs font-mono uppercase tracking-[0.08em] transition-all duration-300 border-none cursor-pointer flex items-center gap-2 ${
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
          <div className="glass-surface p-8 md:p-10 max-w-[960px] space-y-7">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <span className="text-[#9a9a9a] text-xs uppercase font-mono tracking-wider">
                Select Architectural Spec Template:
              </span>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setRequirements(PRESET_REQUIREMENTS.checkout)}
                  className="text-xs px-3.5 py-1.5 rounded-full bg-white/[0.04] hover:bg-white/[0.08] text-white transition-colors border-none cursor-pointer font-mono"
                >
                  Payment Webhook
                </button>
                <button
                  type="button"
                  onClick={() => setRequirements(PRESET_REQUIREMENTS.oauth)}
                  className="text-xs px-3.5 py-1.5 rounded-full bg-white/[0.04] hover:bg-white/[0.08] text-white transition-colors border-none cursor-pointer font-mono"
                >
                  OAuth2 Token Rotation
                </button>
                <button
                  type="button"
                  onClick={() => setRequirements(PRESET_REQUIREMENTS.raft)}
                  className="text-xs px-3.5 py-1.5 rounded-full bg-white/[0.04] hover:bg-white/[0.08] text-white transition-colors border-none cursor-pointer font-mono"
                >
                  Raft Leader Election
                </button>
              </div>
            </div>

            <div className="relative">
              <textarea
                rows={10}
                value={requirements}
                onChange={(e) => setRequirements(e.target.value)}
                placeholder="Paste requirements, acceptance criteria, or OpenAPI JSON/YAML spec..."
                className="w-full bg-black/60 text-white font-mono text-[14px] leading-[1.7] rounded-[18px] p-6 border border-white/[0.06] focus:border-[#8052ff] focus:outline-none transition-colors selection:bg-[#8052ff]"
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
          <div className="glass-surface p-8 md:p-10 max-w-[960px] space-y-9">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              
              {/* Actor Model Selector */}
              <div className="space-y-3">
                <label className="block text-[#9a9a9a] text-xs uppercase font-semibold font-mono tracking-wider">
                  Generator (Actor) Model
                </label>
                <select
                  value={actorModel}
                  onChange={(e) => setActorModel(e.target.value)}
                  className="w-full bg-black/70 text-white text-[14px] font-mono rounded-[14px] p-4 border border-white/[0.08] focus:border-[#8052ff] focus:outline-none"
                >
                  <option value="deepseek" className="bg-black">DeepSeek Chat (Default)</option>
                  <option value="qwen" className="bg-black">Qwen 2.5 Coder</option>
                  <option value="openai" className="bg-black">OpenAI GPT-4o</option>
                  <option value="ollama" className="bg-black">Ollama Local</option>
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
                <div className="bg-black/70 text-[#bdbdbd] text-[13px] font-mono rounded-[14px] p-4 border border-white/[0.06]">
                  Strict Bound = 2 Passes
                </div>
                <span className="text-[#9a9a9a] text-[11px] font-[200] block">
                  Guarantees monotonic score non-regression
                </span>
              </div>

            </div>

            {/* Visual Reflection Loop Flow */}
            <div className="p-6 rounded-[18px] bg-black/50 border border-white/[0.04] flex flex-col md:flex-row items-center justify-between gap-4 text-xs font-mono">
              <div className="flex items-center gap-3">
                <span className="w-2.5 h-2.5 rounded-full bg-[#8052ff]" />
                <span className="text-white">Actor: Synthesize Candidates</span>
              </div>
              <span className="text-[#9a9a9a]">⇄</span>
              <div className="flex items-center gap-3">
                <span className="w-2.5 h-2.5 rounded-full bg-[#ffb829]" />
                <span className="text-white">Critic: Multi-Dimension Audit</span>
              </div>
              <span className="text-[#9a9a9a]">⇄</span>
              <div className="flex items-center gap-3">
                <span className="w-2.5 h-2.5 rounded-full bg-[#15846e]" />
                <span className="text-white">Monotonic Safeguard: Converge</span>
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
                Launch Reflection Loop 🚀
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Reflection Progress Telemetry (Futuristic Live Console) */}
        {currentStep === 3 && (
          <div className="glass-surface p-8 md:p-10 max-w-[960px] space-y-7">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="w-2.5 h-2.5 rounded-full bg-[#8052ff] animate-ping" />
                <span className="text-white text-[18px] font-normal">
                  Actor-Critic Reflection Active...
                </span>
              </div>
              <span className="text-[#ffb829] font-mono text-sm font-semibold">
                {progressPercent}%
              </span>
            </div>

            {/* Glowing neon progress line */}
            <div className="w-full bg-white/[0.06] rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-[#8052ff] h-full transition-all duration-300 shadow-[0_0_12px_#8052ff]"
                style={{ width: `${progressPercent}%` }}
              />
            </div>

            {/* Telemetry Output Stream */}
            <div className="bg-black/80 rounded-[18px] border border-white/[0.06] p-6 font-mono text-[13px] text-[#bdbdbd] space-y-2.5 max-h-[320px] overflow-y-auto">
              {progressLog.map((log, idx) => (
                <div key={idx} className="leading-relaxed flex items-baseline gap-2">
                  <span className="text-[#8052ff] select-none">❯</span>
                  <span>{log}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 4: Approved Test Cases Preview & TMS Exporters */}
        {currentStep === 4 && result && (
          <div className="max-w-[1080px] space-y-12">
            
            {/* Score Banner */}
            <div className="glass-surface p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <span className="text-[#15846e] text-xl font-bold">✓</span>
                  <span className="text-white text-[24px] font-normal tracking-[-0.02em]">
                    Quality Audit Converged ({result.highest_score}%)
                  </span>
                </div>
                <p className="text-[#9a9a9a] font-[200] text-sm">
                  Suite refined in {result.total_iterations} iterations with Monotonic Regression Safeguard confirmed.
                </p>
              </div>

              {/* Exporters buttons */}
              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={() => handleExport('jira')}
                  className="text-xs px-4 py-2.5 rounded-full bg-[#8052ff] text-white font-mono uppercase tracking-wider border-none cursor-pointer hover:opacity-90 transition-opacity"
                >
                  Jira JSON
                </button>
                <button
                  type="button"
                  onClick={() => handleExport('testrail')}
                  className="text-xs px-4 py-2.5 rounded-full bg-white/[0.06] text-white font-mono uppercase tracking-wider border-none cursor-pointer hover:bg-white/[0.1] transition-colors"
                >
                  TestRail
                </button>
                <button
                  type="button"
                  onClick={() => handleExport('markdown')}
                  className="text-xs px-4 py-2.5 rounded-full bg-white/[0.06] text-white font-mono uppercase tracking-wider border-none cursor-pointer hover:bg-white/[0.1] transition-colors"
                >
                  XMind / MD
                </button>
                <button
                  type="button"
                  onClick={() => handleExport('junit')}
                  className="text-xs px-4 py-2.5 rounded-full bg-white/[0.06] text-white font-mono uppercase tracking-wider border-none cursor-pointer hover:bg-white/[0.1] transition-colors"
                >
                  JUnit XML
                </button>
              </div>
            </div>

            {exportNotice && (
              <div className="text-[#ffb829] text-xs font-mono">
                ✓ {exportNotice}
              </div>
            )}

            {/* 4 Rubric Dials */}
            {result.iterations[result.iterations.length - 1] && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 pt-2">
                {[
                  { label: 'Completeness', score: result.iterations[result.iterations.length - 1].rubric.completeness },
                  { label: 'Coverage', score: result.iterations[result.iterations.length - 1].rubric.coverage },
                  { label: 'Redundancy', score: result.iterations[result.iterations.length - 1].rubric.redundancy },
                  { label: 'Feasibility', score: result.iterations[result.iterations.length - 1].rubric.feasibility },
                ].map((dim) => (
                  <div key={dim.label}>
                    <div className="text-white text-[32px] font-normal tracking-[-0.03em] mb-1">
                      {dim.score}%
                    </div>
                    <div className="text-[#9a9a9a] text-[11px] uppercase tracking-[0.12em] font-mono">
                      {dim.label}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Approved Test Cases List */}
            <div className="space-y-6 pt-4">
              <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
                <span className="text-white text-[22px] font-normal">
                  Approved Test Cases ({result.best_test_cases.length})
                </span>
                <button
                  type="button"
                  onClick={() => setCurrentStep(1)}
                  className="ghost-link text-xs"
                >
                  ↻ Test Another Specification
                </button>
              </div>

              <div className="space-y-5">
                {result.best_test_cases.map((tc, idx) => (
                  <div
                    key={tc.id || idx}
                    className="glass-surface p-7 space-y-4"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span
                          className={`text-[11px] px-3 py-1 rounded-full font-mono font-bold uppercase ${
                            tc.priority === 'p0'
                              ? 'bg-red-500/15 text-red-400 border border-red-500/30'
                              : 'bg-[#8052ff]/15 text-[#8052ff] border border-[#8052ff]/30'
                          }`}
                        >
                          {tc.priority.toUpperCase()}
                        </span>
                        <span className="text-white text-[18px] font-normal">
                          {tc.title}
                        </span>
                      </div>
                      <span className="text-[#15846e] text-xs font-mono uppercase tracking-wider">
                        APPROVED
                      </span>
                    </div>

                    <p className="text-[#bdbdbd] font-[200] text-[15px] leading-relaxed">
                      {tc.description}
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 text-xs font-mono">
                      <div className="bg-black/70 p-4 rounded-[14px] border border-white/[0.04]">
                        <div className="text-[#9a9a9a] uppercase mb-2">Test Steps:</div>
                        <ol className="list-decimal list-inside space-y-1.5 text-white/90 font-[200]">
                          {tc.test_steps.map((s, i) => (
                            <li key={i}>{s}</li>
                          ))}
                        </ol>
                      </div>

                      <div className="bg-black/70 p-4 rounded-[14px] border border-white/[0.04]">
                        <div className="text-[#9a9a9a] uppercase mb-2">Expected Results:</div>
                        <ul className="list-disc list-inside space-y-1.5 text-white/90 font-[200]">
                          {tc.expected_results.map((r, i) => (
                            <li key={i}>{r}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        )}

      </div>
    </section>
  );
};
