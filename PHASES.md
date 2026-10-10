# CodeBrain Modernization Roadmap & Phase Plan

This document tracks the completed 4-phase engineering modernization that transformed CodeBrain from an assistive prompt-wrapper into an autonomous, closed-loop quality engineering platform.

---

## Phase Matrix Overview

| Phase | Status | PR | Core Objective | Key Deliverables |
|---|---|---|---|---|
| **Phase 1: Reliability & Output Hardening** | **COMPLETED** | [PR #1](https://github.com/harshitthek/CodeBrain/pull/1) | Fix routing bugs, harden JSON parsing, and expand intake formats. | - URL route normalization (`/test_case_reviewer/`)<br>- Pydantic v2 `GeneratedTestCaseItem` validation & multi-strategy JSON extractor<br>- Multi-format PRD ingestion (`.md`, `.txt`, `.docx`) with per-request tempfiles<br>- `.xlsx` `openpyxl` export with formula sanitization & atomic `update_test_case_status` persistence |
| **Phase 2: Closed-Loop API Runner & Universal LLMs** | **COMPLETED** | [PR #2](https://github.com/harshitthek/CodeBrain/pull/2) | Transform generated test cases into executable, verifiable assertions. | - Async `httpx` `APITestRunner` with JSONPath & dot-path assertions<br>- SSRF guard, DNS resolution validation, IP pinning with HTTPS `sni_hostname`, & TLS verification<br>- Universal `LLMServiceFactory` (`deepseek`, `qwen`, `openai`, `ollama`, `groq`, custom)<br>- Standalone Pytest script & Postman Collection v2.1 exporters |
| **Phase 3: Zero-Docker RAG & Spec Ingestion** | **COMPLETED** | [PR #3](https://github.com/harshitthek/CodeBrain/pull/3) | Enable local vector search without external containers; support API schemas. | - Zero-Docker `PersistentSQLiteVectorStore` (`chroma_store.py`)<br>- Pure-Python BM25 + Dense Vector Reciprocal Rank Fusion (`HybridRetriever`)<br>- OpenAPI 3.x / Swagger 2.0 parser with circular `$ref` resolution (`openapi_parser.py`)<br>- Recursive Postman Collection v2.1 parser (`postman_parser.py`) |
| **Phase 4: Multi-Agent Orchestration & Enterprise Sync** | **COMPLETED** | [PR #4](https://github.com/harshitthek/CodeBrain/pull/4) | Connect isolated agents into an autonomous QA feedback pipeline. | - `ActorCriticReflectionEngine` (`Generator ⇄ Reviewer`) with monotonic regression safeguards<br>- Unified Auto-Pilot QA Pipeline UI (`/pipeline/`)<br>- Jira Cloud, TestRail, XMind (`.xmind`), Markdown mind-map, & JUnit XML exporters<br>- Headless CI/CD CLI test runner (`python manage.py run_test_suite`) |

---

## Phase Dependencies & Progression

```
┌────────────────────────────────────────────────────────────┐
│ Phase 1: Reliability & Output Hardening (PR #1)            │
│ - Normalized routes, Pydantic v2 schemas, .xlsx/.md/.txt   │
└─────────────────────────────┬──────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│ Phase 2: Closed-Loop API Runner & Universal LLMs (PR #2)   │
│ - Async HTTPX runner, SSRF/IP pinning, Pytest/Postman/LLMs │
└─────────────────────────────┬──────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│ Phase 3: Zero-Docker RAG & Spec Ingestion (PR #3)          │
│ - Embedded SQLite/Chroma vector store, BM25+Vector RRF,    │
│   OpenAPI 3.x / Swagger 2.0 & Postman Collection parsers   │
└─────────────────────────────┬──────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│ Phase 4: Multi-Agent Orchestration & Integrations (PR #4)  │
│ - Actor-Critic loop, /pipeline/ UI, Jira/TestRail/XMind,   │
│   Headless CI/CD run_test_suite management command         │
└────────────────────────────────────────────────────────────┘
```

---

## Detailed Deliverables & Verification Suites

### Phase 1 (`tests/test_phase1.py`)
- **Schema Validation**: [`apps/ai_agents/test_case_generator/schemas.py`](apps/ai_agents/test_case_generator/schemas.py) (`GeneratedTestCaseItem`, `extract_and_parse_test_cases`).
- **PRD Multi-Format Intake**: [`apps/ai_agents/prd_analyzer/views.py`](apps/ai_agents/prd_analyzer/views.py) (`extract_content_from_file`, `prd_analyzer`).
- **Excel Export & Review Persistence**: [`apps/ai_agents/test_case_reviewer/views.py`](apps/ai_agents/test_case_reviewer/views.py) (`export_test_cases_excel`) and [`apps/core/views.py`](apps/core/views.py) (`update_test_case_status`).

### Phase 2 (`tests/test_phase2.py`)
- **Async API Test Runner**: [`apps/ai_agents/iface_case_generator/runner.py`](apps/ai_agents/iface_case_generator/runner.py) (`APITestRunner`).
- **Pytest & Postman Exporters**: [`apps/ai_agents/iface_case_generator/exporters.py`](apps/ai_agents/iface_case_generator/exporters.py) (`generate_pytest_script`, `generate_postman_collection`, `_resolve_body`).
- **Universal LLM Factory**: [`apps/llm/base.py`](apps/llm/base.py) (`LLMServiceFactory`).

### Phase 3 (`tests/test_phase3.py`)
- **Zero-Docker Vector Store**: [`apps/knowledge/chroma_store.py`](apps/knowledge/chroma_store.py) (`PersistentSQLiteVectorStore`).
- **Hybrid Lexical + Dense Retriever**: [`apps/knowledge/hybrid_retriever.py`](apps/knowledge/hybrid_retriever.py) (`PureBM25Index`, `HybridRetriever`).
- **API Spec Ingestion**: [`apps/knowledge/openapi_parser.py`](apps/knowledge/openapi_parser.py) and [`apps/knowledge/postman_parser.py`](apps/knowledge/postman_parser.py).

### Phase 4 (`tests/test_phase4.py`)
- **Actor-Critic Orchestrator**: [`apps/ai_agents/common/orchestrator.py`](apps/ai_agents/common/orchestrator.py) (`ActorCriticReflectionEngine`).
- **Enterprise Exporters**: [`apps/core/exporters/`](apps/core/exporters) (`JiraExporter`, `TestRailExporter`, `XMindExporter`, `JUnitExporter`).
- **Headless CLI Runner**: [`apps/core/management/commands/run_test_suite.py`](apps/core/management/commands/run_test_suite.py).

---

## Architectural Invariants

1. **Zero-Docker Standalone Execution**: All local development and testing workflows operate without requiring Docker containers (SQLite default, embedded vector stores, mockable services).
2. **Deterministic Schemas**: All LLM outputs are validated through Pydantic v2 models and multi-strategy JSON repair parsers.
3. **Security-First Execution**: Outbound API runner requests enforce TLS verification by default, block private/loopback/metadata ranges unless explicitly allowlisted, and pin validated DNS records with HTTPS SNI preservation.
4. **Backward Compatibility**: All relational models (`core_testcase`, `core_testcasereview`, `core_knowledgebase`) migrate cleanly without breaking existing records.
5. **Fail-Closed Fallbacks**: When external API keys or cluster vector stores are unavailable, subsystems degrade gracefully without crashing request handlers.
