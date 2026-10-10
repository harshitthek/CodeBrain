import React, { useState } from 'react';
import { DotMatrixText } from './DotMatrixText';
import { ConstellationCanvas } from './ConstellationCanvas';
import { SheetPageId } from './Navbar';

interface HeroSectionProps {
  onNavigate: (page: SheetPageId) => void;
}

interface ShippedRow {
  no: string;
  matrixLabel: string;
  modulePath: string;
  origin: string;
  phase: string;
  summary: string;
  classes: string;
  verification: string;
  targetSection: SheetPageId;
  isPromptRow?: boolean;
}

const SHIPPED_SUBSYSTEMS: ShippedRow[] = [
  {
    no: '01',
    matrixLabel: 'PIPELINE',
    modulePath: 'apps/ai_agents/common/orchestrator.py',
    origin: 'ACTOR-CRITIC',
    phase: 'PR #04',
    summary:
      'Autonomous Generator ⇄ Reviewer feedback loop bounded at max_iterations=2 with a monotonic regression safeguard that preserves the highest-scoring suite.',
    classes: 'ActorCriticReflectionEngine.run(), _evaluate_candidate_suite(), _build_refinement_input()',
    verification: 'tests/test_phase4.py (16 passed)',
    targetSection: 'pipeline',
  },
  {
    no: '02',
    matrixLabel: 'GENERATOR',
    modulePath: 'apps/ai_agents/test_case_generator/',
    origin: 'PYDANTIC V2',
    phase: 'PR #01',
    summary:
      'Transforms raw requirements into structured manual test suites using Equivalence Partitioning, Boundary Value, Decision Table, and Orthogonal Array design.',
    classes: 'TestCaseGeneratorAgent, GeneratedTestCaseItem, extract_and_parse_test_cases()',
    verification: 'tests/test_phase1.py (15 passed)',
    targetSection: 'pipeline',
  },
  {
    no: '03',
    matrixLabel: 'REVIEWER',
    modulePath: 'apps/ai_agents/test_case_reviewer/',
    origin: '4-DIM RUBRIC',
    phase: 'PR #01',
    summary:
      'Audits candidate suites across Completeness, Coverage, Redundancy, and Feasibility; exports formula-sanitized .xlsx workbooks via openpyxl.',
    classes: 'TestCaseReviewerAgent, review_cases(), export_test_cases_excel()',
    verification: 'tests/test_phase1.py · core.view_testcase enforced',
    targetSection: 'pipeline',
  },
  {
    no: '04',
    matrixLabel: 'HTTPX RUN',
    modulePath: 'apps/ai_agents/iface_case_generator/runner.py',
    origin: 'SSRF PINNED',
    phase: 'PR #02',
    summary:
      'Concurrent async httpx test runner evaluating status codes, dot-paths, jsonpath-ng queries, and regexes with DNS IP pinning and cloud metadata blocking.',
    classes: 'APITestRunner._resolve_safe_target(), _is_blocked_ip(), _evaluate_assertions()',
    verification: 'tests/test_phase2.py (16 passed)',
    targetSection: 'apirunner',
  },
  {
    no: '05',
    matrixLabel: 'HYBRID RAG',
    modulePath: 'apps/knowledge/hybrid_retriever.py',
    origin: 'BM25 + RRF',
    phase: 'PR #03',
    summary:
      'Zero-Docker embedded SQLite vector store (384-dim cosine similarity) fused with pure-Python Okapi BM25 (k1=1.5, b=0.75) via Reciprocal Rank Fusion (k=60).',
    classes: 'PersistentSQLiteVectorStore, PureBM25, HybridRetriever.search_hybrid()',
    verification: 'tests/test_phase3.py (14 passed)',
    targetSection: 'rag',
  },
  {
    no: '06',
    matrixLabel: 'PARSERS',
    modulePath: 'apps/knowledge/openapi_parser.py',
    origin: 'OPENAPI 3.X',
    phase: 'PR #03',
    summary:
      'Ingests OpenAPI 3.x / Swagger 2.0 (with circular $ref cycle protection), Postman Collections v2.1, and .docx / .md / .txt PRD documents.',
    classes: 'parse_openapi_spec(), parse_postman_collection(), extract_content_from_file()',
    verification: 'tests/test_phase1.py & tests/test_phase3.py',
    targetSection: 'rag',
  },
  {
    no: '07',
    matrixLabel: 'EXPORTERS',
    modulePath: 'apps/core/exporters/',
    origin: 'JIRA / JUNIT',
    phase: 'PR #04',
    summary:
      'Synthesizes standalone Pytest + httpx modules, Postman v2.1 collections, Jira Cloud issues, TestRail suites, XMind (.xmind) archives, and JUnit XML.',
    classes: 'JiraExporter, TestRailExporter, XMindExporter, JUnitExporter, generate_pytest_script()',
    verification: 'tests/test_phase2.py & tests/test_phase4.py',
    targetSection: 'apirunner',
  },
  {
    no: '08',
    matrixLabel: 'YOUR SPEC ?',
    modulePath: 'Interactive Actor-Critic Reflection Workbench',
    origin: 'YOUR PRD / API',
    phase: '20··',
    summary:
      'Load a payment webhook, OAuth2 PKCE, or Raft consensus specification—or paste your own PRD—and run the 2-pass Actor-Critic loop live.',
    classes: 'POST /pipeline/run/ · python manage.py run_test_suite',
    verification: '61 / 61 Total Repository Tests Passing',
    targetSection: 'pipeline',
    isPromptRow: true,
  },
];

const DELIVERY_PHASES = [
  {
    pr: 'PR #01',
    title: 'Phase 1 — Quick Wins & Reliability',
    tests: '15 / 15 PASSED',
    testFile: 'tests/test_phase1.py',
    targetPage: 'pipeline' as SheetPageId,
    highlights: [
      'Pydantic v2 schema validation & JSON repair (schemas.py)',
      'Thread-safe SSE progress bus (ProgressRegistry & SSELogEmitter)',
      'Formula-sanitized .xlsx export with core.view_testcase RBAC',
      'Isolated tempfile .docx PRD extraction via pypandoc',
    ],
  },
  {
    pr: 'PR #02',
    title: 'Phase 2 — Closed-Loop Runner & Universal LLMs',
    tests: '16 / 16 PASSED',
    testFile: 'tests/test_phase2.py',
    targetPage: 'apirunner' as SheetPageId,
    highlights: [
      'Async APITestRunner via httpx.AsyncClient + asyncio.Semaphore(5)',
      'DNS IP pinning with HTTPS sni_hostname & cloud metadata SSRF blocking',
      'Standalone Pytest + httpx and Postman v2.1 code exporters',
      'Universal OpenAI-compatible LLM gateway (Ollama, vLLM, Groq)',
    ],
  },
  {
    pr: 'PR #03',
    title: 'Phase 3 — Zero-Docker Hybrid RAG & Spec Ingestion',
    tests: '14 / 14 PASSED',
    testFile: 'tests/test_phase3.py',
    targetPage: 'rag' as SheetPageId,
    highlights: [
      'Zero-Docker embedded SQLite 384-dim vector store (chroma_store.py)',
      'Pure-Python Okapi BM25 (k1=1.5, b=0.75) + Reciprocal Rank Fusion (k=60)',
      'OpenAPI 3.x / Swagger 2.0 parser with circular $ref cycle protection',
      'Postman Collection v2.1 recursive folder parser',
    ],
  },
  {
    pr: 'PR #04',
    title: 'Phase 4 — Multi-Agent Orchestration & Enterprise Sync',
    tests: '16 / 16 PASSED',
    testFile: 'tests/test_phase4.py',
    targetPage: 'agents' as SheetPageId,
    highlights: [
      'Autonomous ActorCriticReflectionEngine (Generator ⇄ Reviewer loop)',
      'Monotonic high-water score retention across reflection passes',
      'Jira Cloud, TestRail, XMind (.xmind), and JUnit XML exporters',
      'Headless CI/CD CLI runner (python manage.py run_test_suite)',
    ],
  },
];

export const HeroSection: React.FC<HeroSectionProps> = ({ onNavigate }) => {
  const [expandedNo, setExpandedNo] = useState<string | null>('01');
  const [brainPhase, setBrainPhase] = useState<'SCATTERED' | 'CONVERGING' | 'ORBITING'>('SCATTERED');

  const handleRowClick = (row: ShippedRow) => {
    if (row.isPromptRow) {
      onNavigate('pipeline');
      return;
    }
    setExpandedNo((prev) => (prev === row.no ? null : row.no));
  };

  return (
    <section id="hero" className="relative w-full pt-8 pb-16 md:pt-12 md:pb-20 overflow-x-clip">
      <div className="max-w-[1180px] mx-auto px-5 sm:px-10 md:px-14">
        {/* UPPER STAGE: Full-Width Scatter Canvas + 12-Column Asymmetric Split */}
        <div className="relative w-full pb-10">
          {/* Full-Viewport Scatter Canvas anchored to the Upper Stage */}
          <ConstellationCanvas
            className="z-0"
            onPhaseChange={setBrainPhase}
          />

          {/* Top Metadata Classification Row */}
          <div className="relative z-10 flex flex-wrap items-center justify-between gap-4 mb-8">
            <div className="meta-label">
              DJANGO 5.X · LANGCHAIN · PYDANTIC V2 · HTTPX · SQLITE RAG
            </div>
            <div className="meta-label flex items-center gap-2">
              <span
                className={`inline-block w-1.5 h-1.5 rounded-full ${
                  brainPhase === 'ORBITING' ? 'bg-[#2A6F4E]' : 'bg-[#D95338]'
                }`}
              />
              <span>
                FIG 01 // CORTICAL TOPOLOGY:{' '}
                <strong className="text-[#262523] font-medium">{brainPhase}</strong>
              </span>
            </div>
          </div>

          {/* 12-Column Split: Left (7 Cols Typographic Statement) | Right (5 Cols 3D Brain Target Stage) */}
          <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            {/* Left Column (7 cols): Dot-Matrix Headline, Abstract, CTAs, and Key Metrics */}
            <div className="lg:col-span-7 space-y-7">
              <div className="space-y-3 sm:space-y-4 overflow-x-auto pb-1">
                <div>
                  <DotMatrixText
                    text="WHAT CODEBRAIN"
                    pitch={5.3}
                    dotRadius={2.05}
                    ghostRadius={0.95}
                    showBed={false}
                  />
                </div>
                <div>
                  <DotMatrixText
                    text="ALREADY SHIPPED"
                    pitch={5.3}
                    dotRadius={2.05}
                    ghostRadius={0.95}
                    showBed={false}
                  />
                </div>
              </div>

              <p className="text-[13px] sm:text-[14px] text-[#57554F] leading-[1.75] max-w-[560px]">
                CodeBrain is an autonomous multi-agent quality engineering platform. Specialized Django agents decompose PRDs and OpenAPI specs, synthesize Pydantic-validated test suites, critique and self-refine weak edge cases in a bounded 2-pass{' '}
                <strong className="text-[#262523] font-medium">Actor-Critic loop</strong>, and execute live HTTP assertions with DNS-pinned SSRF protection.
              </p>

              <div className="flex flex-wrap items-center gap-3 pt-1">
                <button
                  type="button"
                  onClick={() => onNavigate('pipeline')}
                  className="btn-tech-vermilion"
                >
                  <span>OPEN WORKBENCH</span>
                  <span>→</span>
                </button>
                <button
                  type="button"
                  onClick={() => onNavigate('apirunner')}
                  className="btn-tech-outline bg-[#F2F0EC]/85"
                >
                  <span>HTTPX RUNNER</span>
                </button>
              </div>

              {/* Inline 4-Metric Bar aligned with bottom of 3D Brain */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-5 border-t border-[#D5D2C9] max-w-[560px]">
                <div>
                  <div className="text-[18px] font-semibold text-[#262523]">61 / 61</div>
                  <div className="meta-label text-[10px]">PYTEST SUITE</div>
                </div>
                <div>
                  <div className="text-[18px] font-semibold text-[#D95338]">02 MAX</div>
                  <div className="meta-label text-[10px]">REFLECTION PASSES</div>
                </div>
                <div>
                  <div className="text-[18px] font-semibold text-[#262523]">00</div>
                  <div className="meta-label text-[10px]">DOCKER DEPS</div>
                </div>
                <div>
                  <div className="text-[18px] font-semibold text-[#262523]">06</div>
                  <div className="meta-label text-[10px]">DOMAIN AGENTS</div>
                </div>
              </div>
            </div>

            {/* Right Column (5 cols): 3D Brain Target Stage & Orthographic Datum Caption */}
            <div className="lg:col-span-5 h-[320px] sm:h-[360px] lg:h-[390px] flex flex-col justify-between pointer-events-none select-none">
              <div className="flex items-center justify-between text-[10px] text-[#87847C] tracking-[0.14em] uppercase lg:pl-4">
                <span>L-HEMISPHERE: ACTOR</span>
                <span>R-HEMISPHERE: CRITIC</span>
              </div>

              {/* Center space is occupied by the converged 3D Pin-Matrix Brain on ConstellationCanvas */}
              <div className="my-auto" />

              <div className="flex items-center justify-between text-[10px] text-[#87847C] tracking-[0.14em] uppercase border-t border-[#D5D2C9] pt-3 lg:pl-4">
                <span>SLICES: 26 CORTICAL + 14 FOLIA</span>
                <span className="text-[#D95338]">CLICK CORTEX TO SURGE</span>
              </div>
            </div>
          </div>
        </div>

        {/* Primary Carbon Rule (Matches Reference Table Top Rule) */}
        <div className="rule-heavy" />

        {/* Table Column Headers: NO. | SUBSYSTEM | MODULE / SPEC | ORIGIN | PHASE */}
        <div className="grid grid-cols-12 gap-2 py-4 items-center border-b border-[#D5D2C9]">
          <div className="col-span-2 sm:col-span-1 meta-label">NO.</div>
          <div className="col-span-10 sm:col-span-6 md:col-span-5 meta-label">SUBSYSTEM</div>
          <div className="hidden md:block md:col-span-3 meta-label">MODULE</div>
          <div className="hidden sm:block sm:col-span-3 md:col-span-2 meta-label">ARCHITECTURE</div>
          <div className="hidden sm:block sm:col-span-2 md:col-span-1 meta-label text-right">REF</div>
        </div>

        {/* Numbered Dot-Matrix Rows (01 .. 08) */}
        <div className="divide-y divide-[#D5D2C9]">
          {SHIPPED_SUBSYSTEMS.map((row) => {
            const isExpanded = expandedNo === row.no;
            const isPrompt = Boolean(row.isPromptRow);

            return (
              <div key={row.no} className="transition-colors">
                <div
                  onClick={() => handleRowClick(row)}
                  className={`grid grid-cols-12 gap-2 py-5 sm:py-6 items-center cursor-pointer transition-colors ${
                    isExpanded ? 'bg-[#EAE7E0]/70' : 'hover:bg-[#EAE7E0]/45'
                  }`}
                >
                  {/* Column 1: Slashed-zero Index Number */}
                  <div className="col-span-2 sm:col-span-1">
                    <span
                      className={`text-[13px] font-medium tracking-[0.08em] ${
                        isPrompt ? 'text-[#D95338] font-semibold' : 'text-[#87847C]'
                      }`}
                    >
                      {row.no}
                    </span>
                  </div>

                  {/* Column 2: 5x7 Dot-Matrix Specimen on Fixed 11-Char Ghost Bed */}
                  <div className="col-span-10 sm:col-span-6 md:col-span-5 overflow-x-auto">
                    <DotMatrixText
                      text={row.matrixLabel}
                      padToChars={11}
                      pitch={5.2}
                      dotRadius={2.0}
                      ghostRadius={1.0}
                      showBed={true}
                      accentChars={['?']}
                    />
                  </div>

                  {/* Column 3: Python Module Path */}
                  <div className="hidden md:block md:col-span-3 pr-3">
                    <span
                      className={`text-[12px] truncate block ${
                        isPrompt ? 'text-[#87847C]' : 'text-[#57554F]'
                      }`}
                    >
                      {row.modulePath}
                    </span>
                  </div>

                  {/* Column 4: Origin / Mechanism */}
                  <div className="hidden sm:block sm:col-span-3 md:col-span-2">
                    <span
                      className={`meta-value ${
                        isPrompt ? 'text-[#87847C]' : 'text-[#262523]'
                      }`}
                    >
                      {row.origin}
                    </span>
                  </div>

                  {/* Column 5: Phase / Year */}
                  <div className="hidden sm:block sm:col-span-2 md:col-span-1 text-right">
                    <span
                      className={`meta-value ${
                        isPrompt ? 'text-[#87847C]' : 'text-[#262523]'
                      }`}
                    >
                      {row.phase}
                    </span>
                  </div>
                </div>

                {/* Expandable Technical Specification Drawer */}
                {isExpanded && !isPrompt && (
                  <div className="bg-[#EAE7E0] border-t border-[#D5D2C9] px-4 sm:px-8 py-5 grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
                    <div className="lg:col-span-7 space-y-2">
                      <div className="meta-label text-[#D95338]">
                        SPECIFICATION // {row.modulePath}
                      </div>
                      <p className="text-[13px] text-[#262523] leading-[1.65]">
                        {row.summary}
                      </p>
                      <div className="text-[11px] text-[#57554F] pt-1">
                        <span className="text-[#87847C] uppercase tracking-wider">Entrypoints: </span>
                        <code>{row.classes}</code>
                      </div>
                    </div>
                    <div className="lg:col-span-5 flex flex-col sm:flex-row lg:flex-col items-start sm:items-center lg:items-end justify-between gap-3">
                      <div className="text-[11px] text-[#2A6F4E] font-medium uppercase tracking-[0.12em]">
                        ✓ {row.verification}
                      </div>
                      <button
                        type="button"
                        onClick={() => onNavigate(row.targetSection)}
                        className="btn-tech-primary"
                      >
                        <span>OPEN SHEET</span>
                        <span>→</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Bottom Heavy Carbon Rule + Sheet Status Colophon */}
        <div className="rule-heavy" />
        <div className="pt-4 pb-14 flex flex-wrap items-center justify-between gap-4">
          <div className="meta-label text-[#57554F]">
            CODEBRAIN.EXE — DETERMINISTIC ENGINE READY
          </div>
          <div className="meta-label text-[#57554F]">
            07 SUBSYSTEMS SHIPPED / 01 INTERACTIVE SLOT OPEN
          </div>
        </div>

        {/* =================================================================
            4-PHASE ENGINEERING DELIVERY ROADMAP (PHASES.MD VERIFICATION)
           ================================================================= */}
        <div className="border-t border-[#262523] pt-12">
          <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
            <span className="meta-label">
              SHEET 01B // PHASES.MD — MERGED PULL REQUEST LEDGER (PR #01 → PR #04)
            </span>
            <span className="meta-label text-[#2A6F4E] font-semibold">
              ✓ 61 / 61 AUTOMATED PYTEST VERIFICATIONS PASSING
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {DELIVERY_PHASES.map((p) => (
              <div
                key={p.pr}
                className="border border-[#D5D2C9] bg-[#EAE7E0]/55 p-6 flex flex-col justify-between space-y-5"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between border-b border-[#D5D2C9] pb-3">
                    <span className="text-[11px] font-semibold tracking-[0.14em] text-[#D95338] uppercase">
                      {p.pr} // {p.testFile}
                    </span>
                    <span className="text-[10px] font-semibold tracking-[0.12em] text-[#2A6F4E] border border-[#2A6F4E]/40 bg-[#F2F0EC] px-2 py-0.5">
                      {p.tests}
                    </span>
                  </div>

                  <h3 className="text-[16px] font-semibold text-[#262523]">
                    {p.title}
                  </h3>

                  <ul className="space-y-1.5 text-[12px] text-[#57554F] list-none p-0 m-0">
                    {p.highlights.map((h, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-[#D95338] font-bold">·</span>
                        <span>{h}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="pt-3 border-t border-[#D5D2C9] flex items-center justify-between">
                  <span className="meta-label text-[10px]">STATUS: MERGED TO MAIN</span>
                  <button
                    type="button"
                    onClick={() => onNavigate(p.targetPage)}
                    className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#262523] hover:text-[#D95338] bg-transparent border-none cursor-pointer p-0"
                  >
                    OPEN DEDICATED SHEET →
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
