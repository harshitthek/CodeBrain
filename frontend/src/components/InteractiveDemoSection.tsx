import React, { useState } from 'react';

interface QueryPreset {
  id: string;
  question: string;
  source: string;
  answer: string;
  references: string[];
}

const PRESETS: QueryPreset[] = [
  {
    id: 'consensus',
    question: 'Where is our distributed consensus leader election logic defined?',
    source: 'Codebase + RFC-042',
    answer: 'Leader election resides in `pkg/consensus/raft_election.go#L44-L112`, utilizing a randomized heart-beat jitter (150-300ms) with Raft quorum validation across the active peer cluster.',
    references: ['pkg/consensus/raft_election.go', 'docs/architecture/rfc-042.md', 'commit 94c8b2f'],
  },
  {
    id: 'incident',
    question: 'Why did the payment webhook handler fail during Tuesday peak traffic?',
    source: 'Postmortem #204 + Datadog trace',
    answer: 'A database connection pool starvation under spike load caused webhook ACK timeouts (>5000ms), triggering Stripe exponential retry storms. Resolved in PR #1492 with connection pool pooling headroom and circuit-breaking.',
    references: ['postmortems/2026-10-06-webhook-timeout.md', 'apps/payments/webhook.py', 'incident-slack-#war-room'],
  },
  {
    id: 'auth',
    question: 'What are the token rotation constraints for enterprise SSO customers?',
    source: 'Security Policy + Auth Module',
    answer: 'Enterprise SAML/OIDC bearer tokens rotate strictly on a 60-minute cycle with a 5-minute clock-skew grace period. Refresh tokens require cryptographic device fingerprint verification.',
    references: ['security/iam_policies.md', 'apps/core/auth_pipeline.py'],
  },
];

export const InteractiveDemoSection: React.FC<{ onRequestAccess: () => void }> = ({ onRequestAccess }) => {
  const [selectedId, setSelectedId] = useState<string>(PRESETS[0].id);
  const [customInput, setCustomInput] = useState<string>('');
  const [isSynthesizing, setIsSynthesizing] = useState<boolean>(false);

  const activePreset = PRESETS.find((p) => p.id === selectedId) || PRESETS[0];

  const handleSelect = (preset: QueryPreset) => {
    setSelectedId(preset.id);
    setCustomInput('');
    setIsSynthesizing(true);
    setTimeout(() => setIsSynthesizing(false), 350);
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customInput.trim()) return;
    setIsSynthesizing(true);
    setTimeout(() => setIsSynthesizing(false), 450);
  };

  return (
    <section id="synthesis" className="relative w-full bg-black py-20 md:py-32 overflow-hidden">
      <div className="max-w-[1280px] w-full mx-auto px-6 md:px-10">
        {/* Asymmetric Alternating Layout: Text Left, Interactive Right */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 lg:gap-14 items-center">
          
          {/* Left Column: Monolithic headline + metrics */}
          <div className="lg:col-span-5 flex flex-col items-start">
            <span className="section-label">
              AUTONOMOUS SYNTHESIS
            </span>

            {/* Display Headline */}
            <h2 className="text-white text-[42px] sm:text-[56px] md:text-[68px] lg:text-[78px] font-normal leading-[1.08] tracking-[-1.8px] sm:tracking-[-2.4px] md:tracking-[-3.12px] mb-8">
              Zero friction. Infinite recall.
            </h2>

            {/* Ultra-light body */}
            <div className="space-y-6 max-w-[480px] mb-12">
              <p className="text-[#bdbdbd] font-[200] text-[17px] md:text-[18px] leading-[1.6]">
                Instead of searching through 20 tabs or interrupting teammates on Slack, ask questions in natural language.
              </p>
              <p className="text-[#bdbdbd] font-[200] text-[17px] md:text-[18px] leading-[1.6]">
                Dala traverses code dependencies, specifications, and discussions in parallel, returning exact answers with verified citations.
              </p>
            </div>

            {/* Pure typography metrics floating on void (no cards, no borders) */}
            <div className="grid grid-cols-3 gap-8 pt-4 w-full max-w-[440px]">
              <div>
                <div className="text-white text-[32px] md:text-[42px] font-normal tracking-[-1.2px] leading-none mb-2">
                  113ms
                </div>
                <div className="text-[#9a9a9a] text-[12px] uppercase tracking-[0.05em] font-normal">
                  Neural synthesis
                </div>
              </div>

              <div>
                <div className="text-white text-[32px] md:text-[42px] font-normal tracking-[-1.2px] leading-none mb-2">
                  100%
                </div>
                <div className="text-[#9a9a9a] text-[12px] uppercase tracking-[0.05em] font-normal">
                  Private perimeter
                </div>
              </div>

              <div>
                <div className="text-white text-[32px] md:text-[42px] font-normal tracking-[-1.2px] leading-none mb-2">
                  50+
                </div>
                <div className="text-[#9a9a9a] text-[12px] uppercase tracking-[0.05em] font-normal">
                  Connected sources
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Interactive Synthesis Terminal floating on black void */}
          <div className="lg:col-span-7 flex flex-col justify-center">
            {/* Minimalist interactive area with pure void surface */}
            <div className="w-full relative">
              {/* Query Selection Presets (ghost pills) */}
              <div className="flex flex-wrap gap-3 mb-6">
                {PRESETS.map((p) => {
                  const isSelected = p.id === selectedId && !customInput;
                  return (
                    <button
                      key={p.id}
                      onClick={() => handleSelect(p)}
                      className={`text-[13px] px-4 py-2 rounded-full transition-all duration-200 border-none cursor-pointer ${
                        isSelected
                          ? 'bg-[#8052ff] text-white font-medium'
                          : 'bg-white/[0.05] text-[#9a9a9a] hover:text-white hover:bg-white/[0.08]'
                      }`}
                    >
                      {p.id === 'consensus' && '⚡ Leader Election'}
                      {p.id === 'incident' && '⚠️ Webhook Outage'}
                      {p.id === 'auth' && '🔒 Token Rotation'}
                    </button>
                  );
                })}
              </div>

              {/* Input Bar: floating on black with bone-white text */}
              <form onSubmit={handleCustomSubmit} className="relative mb-8">
                <div className="flex items-center bg-white/[0.03] hover:bg-white/[0.05] transition-colors rounded-[24px] px-5 py-4 w-full">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="text-[#8052ff] mr-3 shrink-0">
                    <polygon points="12,2 22,20 2,20" fill="#8052ff" />
                  </svg>
                  <input
                    type="text"
                    value={customInput || activePreset.question}
                    onChange={(e) => setCustomInput(e.target.value)}
                    placeholder="Ask Dala anything about your codebase, bugs, or specs..."
                    className="w-full bg-transparent text-white font-[200] text-[16px] md:text-[17px] focus:outline-none placeholder-[#9a9a9a]"
                  />
                  <button
                    type="submit"
                    className="ml-3 text-[#ffb829] text-[13px] uppercase font-semibold tracking-wider hover:opacity-80 shrink-0"
                  >
                    Synthesize
                  </button>
                </div>
              </form>

              {/* Synthesized Output Display floating on black void */}
              <div className="relative pt-2">
                {isSynthesizing ? (
                  <div className="py-12 flex items-center justify-center gap-3 text-[#9a9a9a]">
                    <span className="w-2 h-2 rounded-full bg-[#8052ff] animate-ping" />
                    <span className="text-sm font-[200] tracking-wide text-[#bdbdbd]">
                      Traversing distributed organizational graph...
                    </span>
                  </div>
                ) : (
                  <div className="space-y-6 animate-fadeIn">
                    {/* Source Tag */}
                    <div className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#15846e]" />
                      <span className="text-[#ffb829] text-[12px] uppercase font-semibold tracking-wider">
                        {customInput ? 'Synthesized from 12 Cross-Domain Nodes' : activePreset.source}
                      </span>
                    </div>

                    {/* Synthesized Response Text */}
                    <p className="text-white font-[200] text-[18px] md:text-[19px] leading-[1.6]">
                      {customInput
                        ? `Identified relevant references across repository architecture and team conversations for "${customInput}". Query resolved in 94ms with cryptographic integrity verification.`
                        : activePreset.answer}
                    </p>

                    {/* Citations list */}
                    <div className="pt-2">
                      <div className="text-[#9a9a9a] text-[12px] uppercase tracking-wider mb-3 font-medium">
                        Verified Citation Nodes
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {activePreset.references.map((ref, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[9999px] bg-white/[0.04] text-[#bdbdbd] text-[13px] font-mono hover:text-white transition-colors"
                          >
                            <svg width="8" height="8" viewBox="0 0 10 10" fill="none">
                              <polygon points="5,1 9,9 1,9" fill="#8052ff" />
                            </svg>
                            {ref}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Subtle prompt to request full access */}
              <div className="mt-10 pt-6 flex items-center justify-between border-t border-white/[0.05]">
                <span className="text-[#9a9a9a] text-[13px] font-[200]">
                  Ready to deploy Dala into your enterprise workspace?
                </span>
                <button
                  onClick={onRequestAccess}
                  className="accent-link text-[13px]"
                >
                  Request Early Access →
                </button>
              </div>

            </div>
          </div>

        </div>
      </div>
    </section>
  );
};
