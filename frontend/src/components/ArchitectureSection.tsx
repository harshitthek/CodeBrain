import React, { useState } from 'react';

interface LayerInfo {
  id: string;
  number: string;
  title: string;
  role: string;
  components: Array<{ name: string; path: string; description: string }>;
}

const LAYERS: LayerInfo[] = [
  {
    id: 'presentation',
    number: '01',
    title: 'Presentation & CLI Layer',
    role: 'Multi-interface access: reactive web UI, standalone edge showcase, and headless CI runner',
    components: [
      {
        name: 'Auto-Pilot QA Pipeline',
        path: 'apps/core/templates/pipeline.html',
        description: 'Unified 4-step stepper with real-time SSE telemetry streams and direct TMS exports.',
      },
      {
        name: 'React 19 Vite Edge Showcase',
        path: 'frontend/src/',
        description: 'Pure-void design system, high-speed static edge deployment with vercel.json.',
      },
      {
        name: 'Headless CI/CD Runner',
        path: 'apps/core/management/commands/run_test_suite.py',
        description: 'Executes automated test suites in CI pipelines with JUnit XML and JSON summaries.',
      },
    ],
  },
  {
    id: 'agents',
    number: '02',
    title: 'Application & Agent Layer',
    role: 'Autonomous Actor-Critic reflection, Pydantic v2 schemas, and closed-loop HTTPX execution',
    components: [
      {
        name: 'ActorCriticReflectionEngine',
        path: 'apps/ai_agents/common/orchestrator.py',
        description: 'Iterative Generator ⇄ Reviewer feedback loop with monotonic regression safeguards.',
      },
      {
        name: 'Async APITestRunner',
        path: 'apps/ai_agents/iface_case_generator/runner.py',
        description: 'Concurrent httpx engine with DNS IP pinning, TLS verification, and SSRF guards.',
      },
      {
        name: 'Enterprise Exporters',
        path: 'apps/core/exporters/',
        description: 'Pluggable Jira Cloud, TestRail, XMind (.xmind), and JUnit XML exporters.',
      },
    ],
  },
  {
    id: 'services',
    number: '03',
    title: 'Service & Universal LLM Layer',
    role: 'Multi-provider LLM abstraction with thread-safe progress and SSE stream producers',
    components: [
      {
        name: 'Universal LLMServiceFactory',
        path: 'apps/llm/base.py',
        description: 'Instantiates DeepSeek, Qwen, OpenAI, Ollama, Groq, and custom OpenAI-compatible endpoints.',
      },
      {
        name: 'ProgressRegistry & SSELogEmitter',
        path: 'apps/utils/progress_registry.py',
        description: 'Thread-safe background progress registry yielding SSE events to the browser.',
      },
      {
        name: 'TaskContext Lifecycle Manager',
        path: 'apps/utils/logger_manager.py',
        description: 'Context-scoped thread-local logging and task isolation.',
      },
    ],
  },
  {
    id: 'storage',
    number: '04',
    title: 'Storage & Zero-Docker Hybrid RAG',
    role: 'Zero-Docker local vector store, BM25 lexical search, and RRF fusion',
    components: [
      {
        name: 'PersistentSQLiteVectorStore',
        path: 'apps/knowledge/chroma_store.py',
        description: 'Local vector store operating without external Docker containers.',
      },
      {
        name: 'PureBM25 + Dense RRF',
        path: 'apps/knowledge/hybrid_retriever.py',
        description: 'Reciprocal Rank Fusion uniting lexical keywords and semantic embeddings.',
      },
      {
        name: 'Dual Relational Engine',
        path: 'config/settings.py',
        description: 'SQLite for zero-config local development; switches to MySQL 8.x when USE_MYSQL=true.',
      },
    ],
  },
];

export const ArchitectureSection: React.FC = () => {
  const [activeLayerId, setActiveLayerId] = useState<string>('agents');
  const activeLayer = LAYERS.find((l) => l.id === activeLayerId) || LAYERS[1];

  return (
    <section id="architecture" className="relative w-full bg-black py-20 md:py-32 overflow-hidden border-t border-white/[0.04]">
      <div className="max-w-[1280px] w-full mx-auto px-6 md:px-10">
        
        {/* Section Header */}
        <div className="mb-14">
          <span className="section-label">
            SYSTEM ARCHITECTURE & INVARIANTS
          </span>
          <h2 className="text-white text-[38px] sm:text-[54px] md:text-[68px] lg:text-[78px] font-normal leading-[1.08] tracking-[-1.8px] sm:tracking-[-2.6px] md:tracking-[-3.12px] mb-4">
            Four layers of deterministic quality.
          </h2>
          <p className="text-[#bdbdbd] font-[200] text-[18px] max-w-[580px]">
            Engineered with strict architectural invariants: bounded latency, zero-Docker standalone execution, and monotonic regression safeguards.
          </p>
        </div>

        {/* 4 Layers Tabs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          {LAYERS.map((layer) => {
            const isActive = layer.id === activeLayerId;
            return (
              <button
                key={layer.id}
                onClick={() => setActiveLayerId(layer.id)}
                className={`p-5 rounded-[20px] text-left transition-all duration-200 border-none cursor-pointer ${
                  isActive
                    ? 'bg-white/[0.08] text-white'
                    : 'bg-white/[0.02] text-[#9a9a9a] hover:bg-white/[0.04] hover:text-white'
                }`}
              >
                <div className="text-xs font-mono text-[#8052ff] mb-1">
                  LAYER {layer.number}
                </div>
                <div className="text-sm font-normal text-white">
                  {layer.title}
                </div>
              </button>
            );
          })}
        </div>

        {/* Active Layer Details */}
        <div className="bg-white/[0.02] rounded-[24px] p-8 md:p-12 border border-white/[0.06] space-y-8">
          <div>
            <div className="text-[#ffb829] text-xs font-mono uppercase tracking-wider mb-2">
              Layer Role & Scope
            </div>
            <h3 className="text-white text-[24px] sm:text-[30px] font-normal mb-2">
              {activeLayer.title}
            </h3>
            <p className="text-[#bdbdbd] font-[200] text-[17px]">
              {activeLayer.role}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
            {activeLayer.components.map((comp) => (
              <div
                key={comp.name}
                className="bg-black/60 p-6 rounded-[20px] border border-white/[0.04] space-y-3"
              >
                <div className="text-white text-[17px] font-normal">
                  {comp.name}
                </div>
                <div className="text-xs font-mono text-[#8052ff] truncate">
                  {comp.path}
                </div>
                <p className="text-[#bdbdbd] font-[200] text-xs leading-relaxed">
                  {comp.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Architectural Invariants floating on void */}
        <div className="mt-16 pt-10 border-t border-white/[0.06]">
          <span className="text-[#9a9a9a] text-[12px] uppercase tracking-wider font-mono block mb-6">
            Guaranteed Architectural Invariants
          </span>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <div className="text-white text-[16px] font-normal mb-1">
                1. Bounded Iterations (Max = 2)
              </div>
              <p className="text-[#bdbdbd] font-[200] text-sm leading-relaxed">
                Prevents infinite feedback loops and non-deterministic cloud bill spikes. Reflection is strictly bounded.
              </p>
            </div>
            <div>
              <div className="text-white text-[16px] font-normal mb-1">
                2. Monotonic Regression Safeguard
              </div>
              <p className="text-[#bdbdbd] font-[200] text-sm leading-relaxed">
                If subsequent iterations score lower than previous passes, the engine guarantees preservation of the highest-scoring suite.
              </p>
            </div>
            <div>
              <div className="text-white text-[16px] font-normal mb-1">
                3. Zero-Docker Local RAG
              </div>
              <p className="text-[#bdbdbd] font-[200] text-sm leading-relaxed">
                All development and testing operates locally without requiring running Docker containers or heavy vector clusters.
              </p>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
};
