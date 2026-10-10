import React, { useState } from 'react';
import { DotMatrixText } from './DotMatrixText';

interface LayerInfo {
  number: string;
  title: string;
  tagline: string;
  modules: Array<{ name: string; file: string; detail: string }>;
}

const LAYERS: LayerInfo[] = [
  {
    number: '01',
    title: 'Presentation & Headless CLI Layer',
    tagline: 'Django SSE templates, Archival React datasheet, & CI/CD runner',
    modules: [
      {
        name: 'Auto-Pilot QA Pipeline View',
        file: 'apps/core/templates/pipeline.html',
        detail: 'Server-rendered 4-step pipeline console with EventSource SSE progress streaming.',
      },
      {
        name: 'Archival Datasheet UI',
        file: 'frontend/src/',
        detail: '5x7 dot-matrix technical showcase with interactive Actor-Critic, HTTPX, and Hybrid RAG benches.',
      },
      {
        name: 'Headless CI/CD CLI Runner',
        file: 'apps/core/management/commands/run_test_suite.py',
        detail: 'Executes API suites via python manage.py run_test_suite with JUnit XML and non-zero exit codes.',
      },
    ],
  },
  {
    number: '02',
    title: 'Application & Multi-Agent Orchestration Layer',
    tagline: 'Actor-Critic reflection, Pydantic v2 validation, & async HTTPX execution',
    modules: [
      {
        name: 'ActorCriticReflectionEngine',
        file: 'apps/ai_agents/common/orchestrator.py',
        detail: 'Bounded 2-pass Generator ⇄ Reviewer feedback loop with monotonic regression safeguards.',
      },
      {
        name: 'Async APITestRunner',
        file: 'apps/ai_agents/iface_case_generator/runner.py',
        detail: 'Concurrent httpx engine with DNS IP pinning, HTTPS SNI preservation, and SSRF guards.',
      },
      {
        name: 'Enterprise TMS Exporters',
        file: 'apps/core/exporters/',
        detail: 'JiraExporter, TestRailExporter, XMindExporter (.xmind), and JUnitExporter (.xml).',
      },
    ],
  },
  {
    number: '03',
    title: 'Universal LLM & Real-Time Telemetry Layer',
    tagline: 'Multi-provider LLM factory with masked credentials & thread-safe SSE registry',
    modules: [
      {
        name: 'LLMServiceFactory',
        file: 'apps/llm/base.py',
        detail: 'Instantiates DeepSeek, Qwen, OpenAI, Ollama, Groq, and custom runtime OpenAI-compatible gateways.',
      },
      {
        name: 'ProgressRegistry & SSELogEmitter',
        file: 'apps/utils/progress_registry.py',
        detail: 'Thread-safe progress bus streaming real-time step logs over /progress/stream/<task_id>/.',
      },
      {
        name: 'TaskContext Lifecycle Manager',
        file: 'apps/utils/logger_manager.py',
        detail: 'Thread-local task context isolation and structured execution logging.',
      },
    ],
  },
  {
    number: '04',
    title: 'Storage & Zero-Docker Hybrid RAG Layer',
    tagline: 'Embedded SQLite vector store, PureBM25 lexical search, & OpenAPI/Postman parsers',
    modules: [
      {
        name: 'HybridRetriever & PureBM25',
        file: 'apps/knowledge/hybrid_retriever.py',
        detail: 'Merges dense cosine rankings and Okapi BM25 rankings via Reciprocal Rank Fusion (k=60).',
      },
      {
        name: 'PersistentSQLiteVectorStore',
        file: 'apps/knowledge/chroma_store.py',
        detail: 'Zero-Docker 384-dim embedded SQLite vector store with optional Milvus 2.x cluster mode.',
      },
      {
        name: 'OpenAPI & Postman Spec Parsers',
        file: 'apps/knowledge/openapi_parser.py',
        detail: 'Resolves circular $ref schemas and nested Postman v2.1 folders into normalized contracts.',
      },
    ],
  },
];

const LLM_PROVIDERS = [
  {
    provider: 'deepseek',
    className: 'DeepSeekChatModel',
    defaultModel: 'deepseek-v3.1',
    endpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    timeout: 'max_tokens=128000 / temp=0.7',
  },
  {
    provider: 'qwen',
    className: 'QwenChatModel',
    defaultModel: 'qwen3-max-2025-09-23',
    endpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    timeout: 'max_tokens=65000 / temp=0.7',
  },
  {
    provider: 'openai',
    className: 'ChatOpenAI',
    defaultModel: 'gpt-4o-mini',
    endpoint: 'https://api.openai.com/v1',
    timeout: 'max_tokens=4096 / temp=0.7',
  },
  {
    provider: 'ollama',
    className: 'ChatOpenAI',
    defaultModel: 'llama3',
    endpoint: 'http://localhost:11434/v1',
    timeout: 'max_tokens=4096 / local zero-key',
  },
  {
    provider: 'groq',
    className: 'ChatOpenAI',
    defaultModel: 'llama-3.3-70b-versatile',
    endpoint: 'https://api.groq.com/openai/v1',
    timeout: 'max_tokens=4096 / temp=0.7',
  },
];

const INVARIANTS = [
  {
    code: 'INV-01',
    title: 'Bounded Reflection Convergence',
    module: 'apps/ai_agents/common/orchestrator.py',
    desc: 'Enforces a hard upper bound of max_iterations = 2 and tracks the monotonic high-water score so regressions never overwrite a superior suite.',
  },
  {
    code: 'INV-02',
    title: 'SSRF & DNS Rebinding Protection',
    module: 'apps/ai_agents/iface_case_generator/runner.py',
    desc: 'Blocks 169.254.169.254, fd00:ec2::254, metadata.google.internal, loopback, and private ranges; pins validated DNS IP with HTTPS sni_hostname.',
  },
  {
    code: 'INV-03',
    title: 'Zero-Docker Embedded Persistence',
    module: 'apps/knowledge/chroma_store.py',
    desc: 'Runs out-of-the-box using Python 3.10+ and SQLite (db.sqlite3 + chroma_vectors.sqlite3) with zero mandatory Docker or Milvus daemons.',
  },
  {
    code: 'INV-04',
    title: 'Credential Masking & Safe Serialization',
    module: 'apps/llm/utils.py · apps/core/views.py',
    desc: 'Never serializes plaintext API keys into template contexts or JSON responses; preserves stored secrets when masked placeholders are submitted.',
  },
  {
    code: 'INV-05',
    title: 'File & Spreadsheet Sanitization',
    module: 'apps/ai_agents/test_case_reviewer/views.py',
    desc: 'Isolates concurrent .docx pypandoc conversions via per-request tempfiles and forces openpyxl string cells (data_type="s") with "=" escaping.',
  },
];

export const ArchitectureSection: React.FC = () => {
  const [activeLayer, setActiveLayer] = useState<number>(0);

  return (
    <section id="architecture" className="relative w-full py-12 md:py-16 border-t border-[#262523]">
      <div className="max-w-[1180px] mx-auto px-5 sm:px-10 md:px-14">
        {/* Top Sheet Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <span className="meta-label">
            SHEET 05B // ARCHITECTURE.MD · PHASES.MD · apps/llm/base.py
          </span>
          <span className="meta-label">
            4-LAYER STACK · <span className="text-[#262523] font-medium">05 ARCHITECTURAL INVARIANTS</span> · 05 CONFIGURED LLM PROVIDERS
          </span>
        </div>

        {/* Dot-Matrix Section Title */}
        <div className="mb-8 overflow-x-auto pb-1">
          <DotMatrixText
            text="SYSTEM ARCHITECTURE"
            pitch={5.0}
            dotRadius={1.95}
            showBed={false}
          />
        </div>

        <div className="rule-heavy" />

        {/* 4-Layer Accordion Ledger */}
        <div className="divide-y divide-[#D5D2C9] border-b border-[#262523]">
          {LAYERS.map((layer, index) => {
            const isActive = activeLayer === index;
            return (
              <div key={layer.number}>
                <div
                  onClick={() => setActiveLayer(index)}
                  className={`py-5 px-2 flex flex-col sm:flex-row sm:items-center justify-between gap-2 cursor-pointer transition-colors ${
                    isActive ? 'bg-[#EAE7E0]/80' : 'hover:bg-[#EAE7E0]/40'
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <span
                      className={`text-[13px] font-semibold ${
                        isActive ? 'text-[#B33920]' : 'text-[#625F58]'
                      }`}
                    >
                      LAYER {layer.number}
                    </span>
                    <span className="text-[16px] font-medium text-[#262523]">
                      {layer.title}
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-[12px] text-[#57554F] hidden md:inline">
                      {layer.tagline}
                    </span>
                    <span className="text-[14px] font-semibold text-[#B33920]">
                      {isActive ? '[−]' : '[+]'}
                    </span>
                  </div>
                </div>

                {isActive && (
                  <div className="grid grid-cols-1 md:grid-cols-3 border-t border-[#D5D2C9] bg-[#EAE7E0] divide-y md:divide-y-0 md:divide-x divide-[#D5D2C9]">
                    {layer.modules.map((mod, mIdx) => (
                      <div key={mIdx} className="p-5 space-y-2">
                        <div className="text-[13px] font-semibold text-[#262523]">
                          {mod.name}
                        </div>
                        <div className="text-[11px] text-[#B33920]">
                          <code>{mod.file}</code>
                        </div>
                        <p className="text-[12px] text-[#57554F] leading-[1.6]">
                          {mod.detail}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Universal LLMServiceFactory Provider Matrix */}
        <div className="pt-12">
          <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
            <span className="meta-label text-[#262523] font-semibold">
              UNIVERSAL LLM PROVIDER MATRIX // config/settings.py · apps/llm/base.py (LLMServiceFactory)
            </span>
            <span className="meta-label text-[#2A6F4E]">
              CREDENTIAL MASKING: ENABLED (get_all_configs)
            </span>
          </div>

          <div className="border border-[#262523] bg-[#EAE7E0] divide-y divide-[#D5D2C9]">
            <div className="grid grid-cols-12 gap-2 px-4 py-2.5 bg-[#262523] text-[#F2F0EC] text-[10px] uppercase tracking-[0.14em]">
              <div className="col-span-3 sm:col-span-2">PROVIDER KEY</div>
              <div className="col-span-4 sm:col-span-3">ADAPTER CLASS</div>
              <div className="col-span-5 sm:col-span-2">DEFAULT MODEL</div>
              <div className="hidden sm:block sm:col-span-3">GATEWAY ENDPOINT</div>
              <div className="hidden sm:block sm:col-span-2 text-right">DEFAULTS</div>
            </div>
            {LLM_PROVIDERS.map((p) => (
              <div
                key={p.provider}
                className="grid grid-cols-12 gap-2 px-4 py-3 items-center text-[11px] hover:bg-[#F2F0EC] transition-colors"
              >
                <div className="col-span-3 sm:col-span-2 font-semibold text-[#B33920]">
                  <code>{p.provider}</code>
                </div>
                <div className="col-span-4 sm:col-span-3 text-[#262523] truncate">
                  <code>{p.className}</code>
                </div>
                <div className="col-span-5 sm:col-span-2 text-[#262523] font-medium truncate">
                  {p.defaultModel}
                </div>
                <div className="hidden sm:block sm:col-span-3 text-[#57554F] truncate">
                  <code>{p.endpoint}</code>
                </div>
                <div className="hidden sm:block sm:col-span-2 text-right text-[#625F58] text-[10px]">
                  {p.timeout}
                </div>
              </div>
            ))}
            <div className="px-4 py-3 bg-[#F2F0EC] text-[11px] text-[#57554F] flex flex-wrap items-center justify-between gap-2">
              <span>
                <strong className="text-[#262523]">Custom Runtime Providers:</strong> Unconfigured provider names passed to{' '}
                <code className="text-[#262523]">LLMServiceFactory.create(provider, **config)</code> require a runtime{' '}
                <code className="text-[#B33920]">model</code> or <code className="text-[#B33920]">base_url</code> override (instantiated via{' '}
                <code className="text-[#262523]">ChatOpenAI</code>); otherwise the factory logs a warning and falls back to{' '}
                <code className="text-[#262523]">default_provider (&apos;deepseek&apos;)</code>.
              </span>
            </div>
          </div>
        </div>

        {/* All 5 Architectural Invariants + Headless CLI */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 pt-12">
          {/* Left 7 Cols: All 5 Architectural Invariants */}
          <div className="lg:col-span-7 space-y-3">
            <div className="meta-label text-[#262523] font-semibold">
              FIVE ARCHITECTURAL INVARIANTS (PHASES.MD)
            </div>
            <div className="divide-y divide-[#D5D2C9] border border-[#D5D2C9] bg-[#EAE7E0]">
              {INVARIANTS.map((inv) => (
                <div key={inv.code} className="p-3.5 space-y-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[12px] font-semibold text-[#262523]">
                      <span className="text-[#B33920] mr-2">{inv.code}</span>
                      {inv.title}
                    </span>
                    <code className="text-[10px] text-[#625F58]">{inv.module}</code>
                  </div>
                  <p className="text-[11px] text-[#57554F] leading-[1.55]">{inv.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Right 5 Cols: Headless CI/CD CLI & Custom Agent Registration */}
          <div className="lg:col-span-5 space-y-6">
            <div className="space-y-2.5">
              <div className="meta-label text-[#262523] font-semibold">
                01 // HEADLESS CI/CD CLI RUNNER (run_test_suite.py)
              </div>
              <pre className="bg-[#EAE7E0] border border-[#D5D2C9] p-4 text-[11px] text-[#262523] overflow-x-auto leading-[1.65]">
{`python manage.py run_test_suite path/to/suite.json \\
  --base-url https://api.example.com \\
  --concurrency 5 \\
  --timeout 10.0 \\
  --junit-output reports/junit.xml \\
  --json-output reports/summary.json`}
              </pre>
            </div>

            <div className="space-y-2.5">
              <div className="meta-label text-[#262523] font-semibold">
                02 // REGISTERING A NEW SUB-APP AGENT (AGENTS.MD)
              </div>
              <pre className="bg-[#EAE7E0] border border-[#D5D2C9] p-4 text-[11px] text-[#262523] overflow-x-auto leading-[1.65]">
{`from apps.llm.base import LLMServiceFactory
from apps.llm.utils import get_agent_llm_configs

config = get_agent_llm_configs("security_scanner")
llm = LLMServiceFactory.create(
    config["default_provider"]
)`}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
