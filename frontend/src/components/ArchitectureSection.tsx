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
        name: 'PersistentSQLiteVectorStore',
        file: 'apps/knowledge/chroma_store.py',
        detail: 'Local vector store operating without external Docker containers.',
      },
      {
        name: 'PureBM25 + Dense RRF',
        file: 'apps/knowledge/hybrid_retriever.py',
        detail: 'Reciprocal Rank Fusion uniting lexical keywords and semantic embeddings.',
      },
      {
        name: 'Dual Relational Engine',
        file: 'config/settings.py',
        detail: 'SQLite for zero-config local development; switches to MySQL 8.x when USE_MYSQL=true.',
      },
    ],
  },
];

export const ArchitectureSection: React.FC = () => {
  const [selectedLayerIndex, setSelectedLayerIndex] = useState<number>(1);
  const activeLayer = LAYERS[selectedLayerIndex];

  return (
    <section id="architecture" className="relative w-full bg-black py-28 md:py-36 overflow-hidden border-t border-white/[0.05]">
      <div className="max-w-[1280px] w-full mx-auto px-6 md:px-12">
        
        {/* Section Header */}
        <div className="mb-16">
          <span className="section-label">
            SYSTEM ARCHITECTURE & INVARIANTS
          </span>
          <h2 className="text-white text-[42px] sm:text-[56px] md:text-[72px] lg:text-[78px] font-normal leading-[1.08] tracking-[-0.038em] mb-5">
            Four layers of deterministic quality.
          </h2>
          <p className="text-[#bdbdbd] font-[200] text-[18px] md:text-[19px] max-w-[560px] leading-[1.7]">
            Engineered with strict architectural invariants: bounded latency, zero-Docker standalone execution, and monotonic regression safeguards.
          </p>
        </div>

        {/* 4 Layers Architectural Stack */}
        <div className="space-y-4 mb-16">
          {LAYERS.map((layer, idx) => {
            const isSelected = selectedLayerIndex === idx;

            return (
              <div
                key={layer.number}
                onClick={() => setSelectedLayerIndex(idx)}
                className={`p-7 rounded-[22px] cursor-pointer transition-all duration-300 ${
                  isSelected
                    ? 'glass-surface bg-white/[0.03]'
                    : 'bg-white/[0.01] hover:bg-white/[0.02] border border-transparent'
                }`}
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div className="flex items-center gap-6">
                    <span className="text-[#8052ff] font-mono text-sm tracking-widest font-bold">
                      {layer.number}
                    </span>
                    <h3 className="text-white text-[20px] sm:text-[24px] font-normal tracking-[-0.02em]">
                      {layer.title}
                    </h3>
                  </div>
                  <span className="text-[#9a9a9a] font-[200] text-sm md:text-right max-w-[420px]">
                    {layer.tagline}
                  </span>
                </div>

                {/* Expanded Submodules */}
                {isSelected && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-5 pt-8 mt-6 border-t border-white/[0.06] animate-fadeIn">
                    {layer.modules.map((m) => (
                      <div
                        key={m.name}
                        className="bg-black/60 p-5 rounded-[16px] border border-white/[0.04] space-y-2"
                      >
                        <div className="text-white text-[16px] font-normal">
                          {m.name}
                        </div>
                        <div className="text-xs font-mono text-[#8052ff] truncate">
                          {m.file}
                        </div>
                        <p className="text-[#bdbdbd] font-[200] text-xs leading-relaxed">
                          {m.detail}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Guaranteed Invariants */}
        <div className="pt-10 border-t border-white/[0.06]">
          <span className="text-[#9a9a9a] text-[11px] uppercase tracking-[0.15em] font-mono block mb-8">
            Guaranteed Architectural Invariants
          </span>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            <div>
              <div className="text-white text-[18px] font-normal mb-2">
                1. Bounded Iterations (Bound = 2)
              </div>
              <p className="text-[#bdbdbd] font-[200] text-sm leading-relaxed">
                Prevents infinite feedback loops and non-deterministic cloud latency spikes. Reflection is strictly bounded.
              </p>
            </div>
            <div>
              <div className="text-white text-[18px] font-normal mb-2">
                2. Monotonic Regression Safeguard
              </div>
              <p className="text-[#bdbdbd] font-[200] text-sm leading-relaxed">
                If subsequent iterations score lower than previous passes, the engine guarantees preservation of the highest-scoring suite.
              </p>
            </div>
            <div>
              <div className="text-white text-[18px] font-normal mb-2">
                3. Zero-Docker Standalone RAG
              </div>
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
