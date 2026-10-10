import React, { useState } from 'react';
import { CodeBrainService } from '../services/codebrainService';
import { TestCaseItem, ReflectionPipelineResult } from '../types/codebrain';

const PRESET_REQUIREMENTS = {
  checkout: `FEATURE: Autonomous Checkout & Payment Webhook Processing
- Users add items to cart and submit order via POST /api/checkout.
- Checkout generates Stripe payment intent.
- Stripe asynchronously triggers POST /api/webhooks/payment with HMAC-SHA256 signature in X-Signature header.
- Webhook listener must verify signature against internal secret, transition order from PENDING to PAID, and ensure idempotent processing so duplicate webhook deliveries do not double-bill or duplicate fulfillment.
- In case of downstream payment gateway timeout (>5000ms), circuit breaker must transition to OPEN and queue order to delayed retry topic.`,

  oauth: `FEATURE: Enterprise OAuth2 PKCE & JWT Token Rotation
- Clients initiate authorization with PKCE code_challenge (S256).
- Token endpoint POST /oauth/token exchanges code_verifier for access token (60-minute TTL) and refresh token (30-day TTL).
- Refresh token rotation: Every refresh request invalidates the previous refresh token and issues a new pair.
- Replay attack mitigation: If an invalidated refresh token is ever used, immediately revoke all tokens in the lineage and alert security.
- Clock skew tolerance is strictly 300 seconds.`,

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
      setProgressLog((prev) => [...prev, `[ERROR] Pipeline failed: ${err.message}`]);
    } finally {
      setIsRunning(false);
    }
  };

  const handleExport = async (target: 'jira' | 'testrail' | 'markdown' | 'junit') => {
    if (!result || !result.best_test_cases.length) return;
    const exp = await CodeBrainService.exportTMS(target, result.best_test_cases, 'QA');
    
    // Create client download
    const blob = new Blob([exp.content], { type: exp.mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = exp.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setExportNotice(`Exported ${exp.filename} successfully.`);
    setTimeout(() => setExportNotice(null), 3500);
  };

  return (
    <section id="pipeline" className="relative w-full bg-black py-20 md:py-32 overflow-hidden border-t border-white/[0.04]">
      <div className="max-w-[1280px] w-full mx-auto px-6 md:px-10">
        
        {/* Section Header */}
        <div className="mb-14">
          <span className="section-label">
            AUTONOMOUS ACTOR-CRITIC QA STUDIO
          </span>
          <h2 className="text-white text-[38px] sm:text-[54px] md:text-[68px] lg:text-[78px] font-normal leading-[1.08] tracking-[-1.8px] sm:tracking-[-2.6px] md:tracking-[-3.12px] mb-4">
            Closed-loop test generation.
          </h2>
          <p className="text-[#bdbdbd] font-[200] text-[18px] max-w-[580px]">
            Input raw requirements. The Generator (*Actor*) synthesizes test candidates, while the Reviewer (*Critic*) audits quality and guides bounded self-healing iterations.
          </p>
        </div>

        {/* Stepper Header (Clean, minimalist, no card borders) */}
        <div className="flex items-center justify-between max-w-[720px] mb-12 border-b border-white/[0.08] pb-6">
          {[
            { num: 1, label: 'Intake' },
            { num: 2, label: 'Parameters' },
            { num: 3, label: 'Reflection' },
            { num: 4, label: 'Export & Sync' },
          ].map((step) => {
            const isActive = currentStep === step.num;
            const isCompleted = currentStep > step.num;

            return (
              <button
                key={step.num}
                onClick={() => (!isRunning ? setCurrentStep(step.num) : null)}
                disabled={isRunning}
                className="flex items-center gap-3 bg-transparent border-none cursor-pointer group text-left"
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold transition-colors duration-300 ${
                    isActive
                      ? 'bg-[#8052ff] text-white'
                      : isCompleted
                      ? 'bg-[#15846e] text-white'
                      : 'bg-white/[0.08] text-[#9a9a9a]'
                  }`}
                >
                  {isCompleted ? '✓' : step.num}
                </div>
                <span
                  className={`text-[13px] uppercase tracking-wider font-mono hidden sm:inline ${
                    isActive ? 'text-white font-semibold' : 'text-[#9a9a9a]'
                  }`}
                >
                  {step.label}
                </span>
              </button>
            );
          })}
        </div>

        {/* Step 1: Requirements Intake */}
        {currentStep === 1 && (
          <div className="max-w-[840px] space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <span className="text-[#9a9a9a] text-[13px] uppercase tracking-wider font-mono">
                Load Architecture Preset:
              </span>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setRequirements(PRESET_REQUIREMENTS.checkout)}
                  className="text-xs px-3 py-1.5 rounded-full bg-white/[0.05] hover:bg-white/[0.1] text-white transition-colors border-none cursor-pointer"
                >
                  Payment Webhook
                </button>
                <button
                  type="button"
                  onClick={() => setRequirements(PRESET_REQUIREMENTS.oauth)}
                  className="text-xs px-3 py-1.5 rounded-full bg-white/[0.05] hover:bg-white/[0.1] text-white transition-colors border-none cursor-pointer"
                >
                  OAuth2 Token Rotation
                </button>
                <button
                  type="button"
                  onClick={() => setRequirements(PRESET_REQUIREMENTS.raft)}
                  className="text-xs px-3 py-1.5 rounded-full bg-white/[0.05] hover:bg-white/[0.1] text-white transition-colors border-none cursor-pointer"
                >
                  Raft Leader Election
                </button>
              </div>
            </div>

            <div>
              <textarea
                rows={9}
                value={requirements}
                onChange={(e) => setRequirements(e.target.value)}
                placeholder="Paste requirements text, user stories, acceptance criteria, or OpenAPI spec..."
                className="w-full bg-white/[0.03] text-white font-[200] text-[16px] leading-[1.6] rounded-[24px] p-6 border border-white/[0.08] focus:border-[#8052ff] focus:outline-none transition-colors"
              />
            </div>

            <div className="flex items-center justify-between pt-2">
              <span className="text-[#9a9a9a] text-[13px] font-[200]">
                Supports Markdown PRDs, user stories, and raw API contracts.
              </span>
              <button
                type="button"
                onClick={() => setCurrentStep(2)}
                className="btn-primary-pill"
              >
                Configure Reflection →
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Agent Reflection Parameters */}
        {currentStep === 2 && (
          <div className="max-w-[840px] space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Actor Model */}
              <div>
                <label className="block text-[#9a9a9a] text-[12px] uppercase font-semibold tracking-wider mb-2 font-mono">
                  Generator (Actor) Model
                </label>
                <select
                  value={actorModel}
                  onChange={(e) => setActorModel(e.target.value)}
                  className="w-full bg-white/[0.04] text-white text-[15px] rounded-[16px] p-3.5 border border-white/[0.08] focus:border-[#8052ff] focus:outline-none"
                >
                  <option value="deepseek" className="bg-black">DeepSeek Chat (Default)</option>
                  <option value="qwen" className="bg-black">Qwen 2.5 Coder</option>
                  <option value="openai" className="bg-black">OpenAI GPT-4o</option>
                  <option value="ollama" className="bg-black">Ollama Local</option>
                </select>
                <span className="text-[#9a9a9a] text-[11px] font-[200] block mt-1.5">
                  Managed via Universal LLMServiceFactory
                </span>
              </div>

              {/* Target Quality Score */}
              <div>
                <label className="block text-[#9a9a9a] text-[12px] uppercase font-semibold tracking-wider mb-2 font-mono">
                  Target Score ({minScore}%)
                </label>
                <input
                  type="range"
                  min={60}
                  max={95}
                  value={minScore}
                  onChange={(e) => setMinScore(Number(e.target.value))}
                  className="w-full accent-[#8052ff] mt-2"
                />
                <span className="text-[#9a9a9a] text-[11px] font-[200] block mt-1.5">
                  Critic approval threshold before convergence
                </span>
              </div>

              {/* Max Passes (Strict Invariant Bound = 2) */}
              <div>
                <label className="block text-[#9a9a9a] text-[12px] uppercase font-semibold tracking-wider mb-2 font-mono">
                  Max Passes (Bound = 2)
                </label>
                <input
                  type="text"
                  readOnly
                  value="2 (Monotonic Safeguard)"
                  className="w-full bg-white/[0.02] text-[#9a9a9a] text-[15px] font-mono rounded-[16px] p-3.5 border border-white/[0.06] cursor-not-allowed"
                />
                <span className="text-[#9a9a9a] text-[11px] font-[200] block mt-1.5">
                  Architectural Invariant 1: bounded latency
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-white/[0.06]">
              <button
                type="button"
                onClick={() => setCurrentStep(1)}
                className="ghost-link"
              >
                ← Back to Requirements
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

        {/* Step 3: Reflection Progress Telemetry */}
        {currentStep === 3 && (
          <div className="max-w-[840px] space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="w-2.5 h-2.5 rounded-full bg-[#8052ff] animate-ping" />
                <span className="text-white text-[18px] font-normal">
                  Actor-Critic Reflection Active...
                </span>
              </div>
              <span className="text-[#ffb829] font-mono text-sm">
                {progressPercent}%
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-white/[0.06] rounded-full h-2 overflow-hidden">
              <div
                className="bg-[#8052ff] h-full transition-all duration-300"
                style={{ width: `${progressPercent}%` }}
              />
            </div>

            {/* Telemetry Stream Output */}
            <div className="bg-black border border-white/[0.08] rounded-[24px] p-6 font-mono text-[13px] text-[#bdbdbd] space-y-2 max-h-[300px] overflow-y-auto">
              {progressLog.map((log, idx) => (
                <div key={idx} className="leading-relaxed">
                  <span className="text-[#8052ff]">❯</span> {log}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 4: Approved Test Cases Preview & TMS Exporters */}
        {currentStep === 4 && result && (
          <div className="space-y-12">
            
            {/* Audit Score Banner */}
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 p-6 rounded-[24px] bg-white/[0.02] border border-white/[0.06]">
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <span className="text-[#15846e] text-lg font-bold">✓</span>
                  <span className="text-white text-[20px] font-normal">
                    Quality Audit Converged ({result.highest_score}%)
                  </span>
                </div>
                <p className="text-[#9a9a9a] font-[200] text-sm">
                  Generated in {result.total_iterations} reflection passes with Monotonic Regression Safeguard verified.
                </p>
              </div>

              {/* Exporters buttons */}
              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={() => handleExport('jira')}
                  className="text-xs px-3.5 py-2 rounded-full bg-[#8052ff] text-white font-medium border-none cursor-pointer hover:opacity-90 transition-opacity"
                >
                  Export Jira JSON
                </button>
                <button
                  type="button"
                  onClick={() => handleExport('testrail')}
                  className="text-xs px-3.5 py-2 rounded-full bg-white/[0.08] text-white font-medium border-none cursor-pointer hover:bg-white/[0.12] transition-colors"
                >
                  Export TestRail
                </button>
                <button
                  type="button"
                  onClick={() => handleExport('markdown')}
                  className="text-xs px-3.5 py-2 rounded-full bg-white/[0.08] text-white font-medium border-none cursor-pointer hover:bg-white/[0.12] transition-colors"
                >
                  Export XMind / MD
                </button>
                <button
                  type="button"
                  onClick={() => handleExport('junit')}
                  className="text-xs px-3.5 py-2 rounded-full bg-white/[0.08] text-white font-medium border-none cursor-pointer hover:bg-white/[0.12] transition-colors"
                >
                  Export JUnit XML
                </button>
              </div>
            </div>

            {exportNotice && (
              <div className="text-[#ffb829] text-xs font-mono">
                {exportNotice}
              </div>
            )}

            {/* Rubric Breakdown Dimensions */}
            {result.iterations[result.iterations.length - 1] && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 pt-2">
                {[
                  { label: 'Completeness', score: result.iterations[result.iterations.length - 1].rubric.completeness },
                  { label: 'Coverage', score: result.iterations[result.iterations.length - 1].rubric.coverage },
                  { label: 'Redundancy', score: result.iterations[result.iterations.length - 1].rubric.redundancy },
                  { label: 'Feasibility', score: result.iterations[result.iterations.length - 1].rubric.feasibility },
                ].map((dim) => (
                  <div key={dim.label}>
                    <div className="text-white text-[28px] font-normal tracking-[-0.8px]">
                      {dim.score}%
                    </div>
                    <div className="text-[#9a9a9a] text-[11px] uppercase tracking-wider font-mono">
                      {dim.label}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Approved Test Cases Table floating on black void */}
            <div className="space-y-6 pt-6">
              <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
                <span className="text-white text-[22px] font-normal">
                  Approved Test Suite ({result.best_test_cases.length} cases)
                </span>
                <button
                  type="button"
                  onClick={() => setCurrentStep(1)}
                  className="ghost-link text-xs"
                >
                  ↻ Run Another Specification
                </button>
              </div>

              <div className="space-y-6">
                {result.best_test_cases.map((tc, idx) => (
                  <div
                    key={tc.id || idx}
                    className="p-6 rounded-[24px] bg-white/[0.02] border border-white/[0.05] space-y-4"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span
                          className={`text-[11px] px-2.5 py-1 rounded-full font-mono font-bold uppercase ${
                            tc.priority === 'p0'
                              ? 'bg-red-500/20 text-red-400'
                              : 'bg-[#8052ff]/20 text-[#8052ff]'
                          }`}
                        >
                          {tc.priority.toUpperCase()}
                        </span>
                        <span className="text-white text-[17px] font-normal">
                          {tc.title}
                        </span>
                      </div>
                      <span className="text-[#15846e] text-xs font-mono uppercase tracking-wider">
                        APPROVED
                      </span>
                    </div>

                    <p className="text-[#bdbdbd] font-[200] text-sm">
                      {tc.description}
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 text-xs font-mono">
                      <div className="bg-black/60 p-4 rounded-[16px] border border-white/[0.04]">
                        <div className="text-[#9a9a9a] uppercase mb-2">Test Steps:</div>
                        <ol className="list-decimal list-inside space-y-1 text-white/90 font-[200]">
                          {tc.test_steps.map((s, i) => (
                            <li key={i}>{s}</li>
                          ))}
                        </ol>
                      </div>

                      <div className="bg-black/60 p-4 rounded-[16px] border border-white/[0.04]">
                        <div className="text-[#9a9a9a] uppercase mb-2">Expected Results:</div>
                        <ul className="list-disc list-inside space-y-1 text-white/90 font-[200]">
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
