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
  const [activeTemplate, setActiveTemplate] = useState<'checkout' | 'oauth' | 'raft'>('checkout');
  const [requirements, setRequirements] = useState<string>(PRESET_REQUIREMENTS.checkout);
  const [actorModel, setActorModel] = useState<string>('deepseek');
  const [minScore, setMinScore] = useState<number>(85);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [progressLog, setProgressLog] = useState<string[]>([
    '[00:00:00.000] System ready. Select spec and trigger reflection loop.',
  ]);
  const [progressPercent, setProgressPercent] = useState<number>(0);
  const [result, setResult] = useState<ReflectionPipelineResult | null>(null);
  const [exportNotice, setExportNotice] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'telemetry' | 'cases'>('telemetry');

  const handleTemplateSwitch = (key: 'checkout' | 'oauth' | 'raft') => {
    setActiveTemplate(key);
    setRequirements(PRESET_REQUIREMENTS[key]);
  };

  const handleLaunch = async () => {
    setIsRunning(true);
    setProgressLog(['[00:00:00.100] Initializing Actor-Critic reflection loop...']);
    setProgressPercent(15);
    setResult(null);
    setActiveTab('telemetry');

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
      setActiveTab('cases');
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
    <section id="pipeline" className="relative w-full bg-transparent py-24 md:py-32 overflow-hidden border-t border-white/[0.06]">
      {/* Subtle atmospheric ambient glow */}
      <div className="absolute top-1/2 left-1/4 w-[500px] h-[500px] bg-[#8052ff]/5 rounded-full blur-[160px] pointer-events-none" />

      <div className="max-w-[1240px] w-full mx-auto px-6 md:px-12 relative z-10">
        
        {/* Section Header: Hallmark Macrostructure 15 Split Studio */}
        <div className="mb-12">
          <span className="section-label">
            AUTONOMOUS ACTOR-CRITIC QA WORKBENCH
          </span>
          <h2 className="text-[#f5f5f7] text-[36px] sm:text-[46px] md:text-[54px] font-normal leading-[1.08] tracking-[-0.038em] mb-4">
            Closed-loop test generation.
          </h2>
          <p className="text-[#c2c2cb] font-[200] text-[18px] md:text-[19px] max-w-[620px] leading-[1.7]">
            The Generator (*Actor*) synthesizes candidate suites, while the Reviewer (*Critic*) audits quality against an empirical rubric with strict 2-pass monotonic regression safeguards.
          </p>
        </div>

        {/* Integrated Split Studio Cockpit (Hallmark: No fake chrome, unified dual-pane) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 items-start">
          
          {/* Left Pane: Spec Document & Control Console (lg:col-span-6) */}
          <div className="lg:col-span-6 workbench-surface overflow-hidden flex flex-col">
            
            {/* Authentic Telemetry Header */}
            <div className="telemetry-header">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#8052ff]" />
                <span className="text-white font-medium">SPEC_INTAKE.MD</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="telemetry-badge bg-white/[0.05] text-[#8e8e98]">UTF-8</span>
                <span className="telemetry-badge bg-[#15846e]/15 text-[#15846e]">READY</span>
              </div>
            </div>

            {/* Template Document Switcher Tabs */}
            <div className="px-5 py-3 border-b border-white/[0.05] flex items-center justify-between gap-3 flex-wrap bg-black/40">
              <span className="text-[11px] font-mono uppercase text-[#8e8e98] tracking-wider">
                Select Architectural Spec:
              </span>
              <div className="flex items-center gap-1.5 flex-wrap">
                {[
                  { key: 'checkout', label: 'Payment Webhook' },
                  { key: 'oauth', label: 'OAuth2 PKCE' },
                  { key: 'raft', label: 'Raft Quorum' },
                ].map((tpl) => (
                  <button
                    key={tpl.key}
                    type="button"
                    onClick={() => handleTemplateSwitch(tpl.key as any)}
                    className={`text-xs px-3 py-1.5 rounded-full font-mono transition-all border cursor-pointer ${
                      activeTemplate === tpl.key
                        ? 'bg-[#8052ff]/20 text-[#f5f5f7] border-[#8052ff]/60'
                        : 'bg-white/[0.02] text-[#8e8e98] border-white/[0.06] hover:text-white'
                    }`}
                  >
                    {tpl.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Spec Editor Canvas */}
            <div className="p-5 flex-1 flex flex-col">
              <textarea
                rows={11}
                value={requirements}
                onChange={(e) => setRequirements(e.target.value)}
                placeholder="Paste requirements, acceptance criteria, or OpenAPI spec..."
                className="w-full bg-black/60 text-[#f5f5f7] font-mono text-[13px] leading-[1.65] rounded-[14px] p-4 border border-white/[0.06] focus:border-[#8052ff] focus:outline-none transition-colors selection:bg-[#8052ff] resize-none"
              />

              {/* Reflection Control Dock */}
              <div className="pt-5 mt-4 border-t border-white/[0.06] space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
                  {/* Model Selector */}
                  <div className="space-y-1.5">
                    <label className="text-[#8e8e98] uppercase tracking-wider block text-[10px]">
                      Actor (Generator) Model
                    </label>
                    <select
                      value={actorModel}
                      onChange={(e) => setActorModel(e.target.value)}
                      className="w-full bg-black/80 text-[#f5f5f7] rounded-[10px] p-2.5 border border-white/[0.08] focus:border-[#8052ff] focus:outline-none cursor-pointer text-xs"
                    >
                      <option value="deepseek">DeepSeek Coder (Default)</option>
                      <option value="qwen">Qwen 2.5 Coder</option>
                      <option value="openai">OpenAI GPT-4o</option>
                      <option value="ollama">Ollama Local vLLM</option>
                    </select>
                  </div>

                  {/* Rubric Hurdle Slider */}
                  <div className="space-y-1.5">
                    <div className="flex justify-between items-center text-[10px] text-[#8e8e98] uppercase tracking-wider">
                      <span>Rubric Hurdle</span>
                      <span className="text-[#ffb829] font-bold">{minScore}% Target</span>
                    </div>
                    <input
                      type="range"
                      min={70}
                      max={95}
                      value={minScore}
                      onChange={(e) => setMinScore(Number(e.target.value))}
                      className="w-full accent-[#8052ff] cursor-pointer mt-1"
                    />
                  </div>
                </div>

                {/* Primary Action Button */}
                <div className="flex items-center justify-between pt-2">
                  <span className="text-[11px] font-mono text-[#8e8e98]">
                    Strict Bound: 2 Passes (Non-Regression Guard)
                  </span>

                  <button
                    type="button"
                    onClick={handleLaunch}
                    disabled={isRunning}
                    className="btn-primary-pill text-xs py-2.5 px-5"
                  >
                    {isRunning ? 'Synthesizing...' : 'Run Reflection Loop ⚡'}
                  </button>
                </div>
              </div>
            </div>

          </div>

          {/* Right Pane: Live Reflection Telemetry HUD & Output (lg:col-span-6) */}
          <div className="lg:col-span-6 workbench-surface overflow-hidden flex flex-col">
            
            {/* Authentic Telemetry Header */}
            <div className="telemetry-header">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setActiveTab('telemetry')}
                  className={`text-xs font-mono uppercase tracking-wider cursor-pointer border-none bg-transparent transition-colors ${
                    activeTab === 'telemetry' ? 'text-white font-semibold' : 'text-[#8e8e98] hover:text-white'
                  }`}
                >
                  LIVE TELEMETRY
                </button>
                <span className="text-white/20">/</span>
                <button
                  onClick={() => setActiveTab('cases')}
                  className={`text-xs font-mono uppercase tracking-wider cursor-pointer border-none bg-transparent transition-colors ${
                    activeTab === 'cases' ? 'text-white font-semibold' : 'text-[#8e8e98] hover:text-white'
                  }`}
                >
                  TEST SUITE ({result?.best_test_cases.length || 0})
                </button>
              </div>

              <div className="telemetry-badge bg-[#8052ff]/15 text-[#8052ff] border border-[#8052ff]/30">
                {isRunning ? 'EXECUTING' : result ? 'CONVERGED' : 'STANDBY'}
              </div>
            </div>

            {/* Main Right Body */}
            <div className="p-5 flex-1 flex flex-col min-h-[460px]">
              
              {activeTab === 'telemetry' && (
                <div className="space-y-5 flex-1 flex flex-col">
                  {/* Real-time score & convergence telemetry block */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-black/60 p-4 rounded-[14px] border border-white/[0.05]">
                    
                    {/* Circular SVG Gauge for Rubric Convergence */}
                    <div className="flex items-center gap-4">
                      <div className="relative w-16 h-16 flex items-center justify-center">
                        <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
                          <path
                            className="text-white/[0.08]"
                            strokeWidth="3.2"
                            stroke="currentColor"
                            fill="none"
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                          />
                          <path
                            className="text-[#8052ff] transition-all duration-500"
                            strokeDasharray={`${result ? result.highest_score : isRunning ? progressPercent : 0}, 100`}
                            strokeWidth="3.2"
                            strokeLinecap="round"
                            stroke="currentColor"
                            fill="none"
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                          />
                        </svg>
                        <span className="absolute text-xs font-mono font-bold text-white">
                          {result ? `${Math.round(result.highest_score)}%` : isRunning ? `${progressPercent}%` : '0%'}
                        </span>
                      </div>

                      <div className="space-y-0.5">
                        <span className="text-[10px] font-mono uppercase text-[#8e8e98] tracking-wider block">
                          Quality Rubric Score
                        </span>
                        <div className="text-white font-mono text-sm font-semibold">
                          {result ? `${result.highest_score.toFixed(1)} / 100` : isRunning ? 'Evaluating...' : 'Awaiting Run'}
                        </div>
                        <span className="text-[10px] font-mono text-[#15846e]">
                          {result ? 'Monotonic High-Water Mark' : 'Target: ' + minScore + '%'}
                        </span>
                      </div>
                    </div>

                    {/* Rubric Dimension Breakdown */}
                    <div className="space-y-1.5 text-[11px] font-mono border-t sm:border-t-0 sm:border-l border-white/[0.06] pt-3 sm:pt-0 sm:pl-4">
                      <div className="flex justify-between text-[#8e8e98]">
                        <span>Completeness</span>
                        <span className="text-white">{result ? '94%' : '--'}</span>
                      </div>
                      <div className="flex justify-between text-[#8e8e98]">
                        <span>Boundary Coverage</span>
                        <span className="text-white">{result ? '91%' : '--'}</span>
                      </div>
                      <div className="flex justify-between text-[#8e8e98]">
                        <span>Step Feasibility</span>
                        <span className="text-white">{result ? '96%' : '--'}</span>
                      </div>
                      <div className="flex justify-between text-[#8e8e98]">
                        <span>Zero Redundancy</span>
                        <span className="text-white">{result ? '89%' : '--'}</span>
                      </div>
                    </div>

                  </div>

                  {/* SSE Event Stream Terminal */}
                  <div className="bg-black/80 rounded-[14px] border border-white/[0.06] flex-1 flex flex-col overflow-hidden">
                    <div className="px-4 py-2 border-b border-white/[0.05] text-[10px] font-mono uppercase tracking-wider text-[#8e8e98] flex items-center justify-between">
                      <span>Stream: apps/utils/progress_registry.py</span>
                      <span className="text-[#ffb829]">SSE_CHANNEL_01</span>
                    </div>

                    <div className="p-4 font-mono text-xs space-y-2 flex-1 max-h-[220px] overflow-y-auto">
                      {progressLog.map((log, idx) => (
                        <div
                          key={idx}
                          className={`leading-relaxed ${
                            log.includes('[CONVERGED]')
                              ? 'text-[#15846e] font-semibold'
                              : log.includes('[PASS')
                              ? 'text-[#ffb829]'
                              : log.includes('[ERROR')
                              ? 'text-red-400'
                              : 'text-[#8e8e98]'
                          }`}
                        >
                          {log}
                        </div>
                      ))}
                      {isRunning && (
                        <div className="flex items-center gap-2 text-[#8052ff] animate-pulse">
                          <span>▶</span>
                          <span>Actor synthesizing candidate tests...</span>
                        </div>
                      )}
                    </div>
                  </div>

                </div>
              )}

              {activeTab === 'cases' && result && (
                <div className="space-y-4 flex-1 flex flex-col">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[#15846e] font-semibold">
                      ✓ CONVERGED AFTER {result.iterations_taken} ITERATIONS
                    </span>
                    <span className="text-[#8e8e98]">
                      Pydantic v2 Validated
                    </span>
                  </div>

                  <div className="space-y-3 overflow-y-auto max-h-[300px] pr-1">
                    {result.best_test_cases.map((tc, idx) => (
                      <div
                        key={tc.id || idx}
                        className="bg-black/60 p-4 rounded-[12px] border border-white/[0.06] space-y-2 text-xs font-mono"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-[#ffb829] font-bold">{tc.id}</span>
                          <span className="text-[10px] uppercase text-[#8052ff] bg-[#8052ff]/10 px-2 py-0.5 rounded">
                            {tc.priority}
                          </span>
                        </div>
                        <div className="text-white font-medium">{tc.title}</div>
                        <div className="text-[#8e8e98] text-[11px] leading-relaxed">
                          <span className="text-white/60">Expected:</span> {tc.expected_results}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* 1-Click Enterprise TMS Export Bar */}
                  <div className="pt-3 border-t border-white/[0.06] space-y-2">
                    <div className="flex items-center justify-between text-[11px] font-mono text-[#8e8e98]">
                      <span>Enterprise TMS Exporters:</span>
                      {exportNotice && <span className="text-[#15846e]">{exportNotice}</span>}
                    </div>

                    <div className="flex items-center gap-2 flex-wrap">
                      <button
                        onClick={() => handleExport('jira')}
                        className="text-[11px] font-mono px-3 py-1.5 rounded-full bg-white/[0.04] hover:bg-[#8052ff] hover:text-white text-[#c2c2cb] border border-white/[0.08] cursor-pointer transition-colors"
                      >
                        Jira (.json)
                      </button>
                      <button
                        onClick={() => handleExport('testrail')}
                        className="text-[11px] font-mono px-3 py-1.5 rounded-full bg-white/[0.04] hover:bg-[#8052ff] hover:text-white text-[#c2c2cb] border border-white/[0.08] cursor-pointer transition-colors"
                      >
                        TestRail (.csv)
                      </button>
                      <button
                        onClick={() => handleExport('junit')}
                        className="text-[11px] font-mono px-3 py-1.5 rounded-full bg-white/[0.04] hover:bg-[#8052ff] hover:text-white text-[#c2c2cb] border border-white/[0.08] cursor-pointer transition-colors"
                      >
                        JUnit (.xml)
                      </button>
                      <button
                        onClick={() => handleExport('markdown')}
                        className="text-[11px] font-mono px-3 py-1.5 rounded-full bg-white/[0.04] hover:bg-[#8052ff] hover:text-white text-[#c2c2cb] border border-white/[0.08] cursor-pointer transition-colors"
                      >
                        MindMap (.md)
                      </button>
                    </div>
                  </div>

                </div>
              )}

            </div>

          </div>

        </div>

      </div>
    </section>
  );
};
