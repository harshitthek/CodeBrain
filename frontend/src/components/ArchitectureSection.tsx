import React, { useState } from 'react';

interface LayerInfo {
  number: string;
  title: string;
  tagline: string;
  modules: Array<{ name: string; file: string; detail: string }>;
}

const LAYERS: LayerInfo[] = [
  {
    number: '01',
    title: 'Presentation & CLI Layer',
    tagline: 'Reactive HTML5 UI, edge-ready React showcase, and headless CI runner',
    modules: [
      {
        name: 'Auto-Pilot QA Pipeline',
        file: 'apps/core/templates/pipeline.html',
        detail: '4-step stepper with real-time SSE progress events and direct TMS exports.',
      },
      {
        name: 'React 19 Vite Edge Showcase',
        file: 'frontend/src/',
        detail: 'Pure-void design system, high-speed static edge deployment with vercel.json.',
      },
      {
        name: 'Headless CI/CD Runner',
        file: 'apps/core/management/commands/run_test_suite.py',
        detail: 'Runs automated test suites in CI pipelines with JUnit XML and JSON summaries.',
      },
    ],
  },
  {
    number: '02',
    title: 'Application & Agent Layer',
    tagline: 'Autonomous Actor-Critic reflection, Pydantic v2 schemas, and closed-loop HTTPX execution',
    modules: [
      {
        name: 'ActorCriticReflectionEngine',
        file: 'apps/ai_agents/common/orchestrator.py',
        detail: 'Iterative Generator ⇄ Reviewer feedback loop with monotonic regression safeguards.',
      },
      {
        name: 'Async APITestRunner',
        file: 'apps/ai_agents/iface_case_generator/runner.py',
        detail: 'Concurrent httpx engine with DNS IP pinning, TLS verification, and SSRF guards.',
      },
      {
        name: 'Enterprise Exporters',
        file: 'apps/core/exporters/',
        detail: 'Pluggable Jira Cloud, TestRail, XMind (.xmind), and JUnit XML exporters.',
      },
    ],
  },
  {
    number: '03',
    title: 'Service & Universal LLM Layer',
    tagline: 'Multi-provider LLM abstraction with thread-safe progress and SSE stream producers',
    modules: [
      {
        name: 'Universal LLMServiceFactory',
        file: 'apps/llm/base.py',
        detail: 'Instantiates DeepSeek, Qwen, OpenAI, Ollama, Groq, and custom vLLM endpoints.',
      },
      {
        name: 'ProgressRegistry & SSELogEmitter',
        file: 'apps/utils/progress_registry.py',
        detail: 'Thread-safe background progress registry yielding SSE events to the browser.',
      },
      {
        name: 'TaskContext Lifecycle Manager',
        file: 'apps/utils/logger_manager.py',
        detail: 'Context-scoped thread-local logging and task isolation.',
      },
    ],
  },
  {
    number: '04',
    title: 'Storage & Zero-Docker Hybrid RAG',
    tagline: 'Zero-Docker local vector store, BM25 lexical search, and RRF fusion',
    modules: [
      {
        name: 'HybridRetriever',
        file: 'apps/knowledge/hybrid_retriever.py',
        detail: 'Combines vector cosine similarity with rank-BM25 via Reciprocal Rank Fusion.',
      },
      {
        name: 'Local Vector Store',
        file: 'apps/knowledge/vector_store.py',
        detail: 'Self-contained NumPy cosine similarity store persisted to disk without Docker.',
      },
      {
        name: 'Relational Database',
        file: 'apps/core/models.py',
        detail: 'Django ORM schema for test cases, review rubrics, execution logs, and iterations.',
      },
    ],
  },
];

export const ArchitectureSection: React.FC = () => {
  const [activeLayer, setActiveLayer] = useState<number>(0);

  return (
    <section id="architecture" className="relative w-full bg-black py-24 md:py-32 overflow-hidden border-t border-white/[0.06]">
      <div className="max-w-[1240px] w-full mx-auto px-6 md:px-12">
        
        {/* Section Header */}
        <div className="mb-14">
          <span className="section-label">
            SYSTEM ARCHITECTURE & INVARIANTS
          </span>
          <h2 className="text-white text-[38px] sm:text-[52px] md:text-[64px] font-normal leading-[1.08] tracking-[-0.038em] mb-4">
            Four layers of deterministic quality.
          </h2>
          <p className="text-[#bdbdbd] font-[200] text-[18px] md:text-[19px] max-w-[580px] leading-[1.7]">
            Engineered with strict architectural invariants: bounded latency, zero-Docker standalone execution, and monotonic regression safeguards.
          </p>
        </div>

        {/* 4-Layer Interactive Deck */}
        <div className="space-y-4 mb-16">
          {LAYERS.map((layer, index) => {
            const isActive = activeLayer === index;

            return (
              <div
                key={layer.number}
                className={`glass-surface transition-all duration-300 rounded-[20px] overflow-hidden ${
                  isActive ? 'border-white/[0.18] bg-white/[0.03]' : 'hover:border-white/[0.1]'
                }`}
              >
                <div
                  onClick={() => setActiveLayer(index)}
                  className="p-6 sm:p-7 flex flex-col md:flex-row md:items-center justify-between gap-4 cursor-pointer select-none"
                >
                  <div className="flex items-center gap-4">
                    <span className="text-[#8052ff] font-mono text-sm font-semibold">
                      {layer.number}
                    </span>
                    <h3 className="text-white text-[20px] sm:text-[22px] font-normal">
                      {layer.title}
                    </h3>
                  </div>

                  <div className="flex items-center gap-4">
                    <span className="text-[#9a9a9a] text-xs font-[200] md:text-right hidden sm:block">
                      {layer.tagline}
                    </span>
                    <span className="text-[#ffb829] text-sm">
                      {isActive ? '−' : '+'}
                    </span>
                  </div>
                </div>

                {isActive && (
                  <div className="px-6 pb-7 sm:px-7 sm:pb-8 pt-2 border-t border-white/[0.05]">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
                      {layer.modules.map((mod, mIdx) => (
                        <div
                          key={mIdx}
                          className="bg-black/60 p-5 rounded-[16px] border border-white/[0.06] space-y-2.5"
                        >
                          <div className="text-white text-sm font-medium">
                            {mod.name}
                          </div>
                          <div className="text-[#8052ff] font-mono text-[11px] truncate">
                            {mod.file}
                          </div>
                          <p className="text-[#9a9a9a] text-xs font-[200] leading-relaxed">
                            {mod.detail}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Guaranteed Architectural Invariants */}
        <div className="pt-8 border-t border-white/[0.08]">
          <span className="text-[#9a9a9a] text-[11px] font-mono uppercase tracking-[0.15em] block mb-6">
            GUARANTEED ARCHITECTURAL INVARIANTS
          </span>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="space-y-2">
              <h4 className="text-white text-base font-normal">
                1. Bounded Iterations (Bound = 2)
              </h4>
              <p className="text-[#bdbdbd] font-[200] text-sm leading-relaxed">
                Prevents infinite feedback loops and non-deterministic cloud latency spikes. Reflection is strictly bounded.
              </p>
            </div>

            <div className="space-y-2">
              <h4 className="text-white text-base font-normal">
                2. Monotonic Regression Safeguard
              </h4>
              <p className="text-[#bdbdbd] font-[200] text-sm leading-relaxed">
                If subsequent iterations score lower than previous passes, the engine guarantees preservation of the highest-scoring suite.
              </p>
            </div>

            <div className="space-y-2">
              <h4 className="text-white text-base font-normal">
                3. Zero-Docker Standalone RAG
              </h4>
              <p className="text-[#bdbdbd] font-[200] text-sm leading-relaxed">
                All development and testing operates locally without requiring external Docker containers or heavy vector clusters.
              </p>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
};
