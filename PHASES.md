# CodeBrain Modernization Roadmap & Phase Plan

This document outlines the strategic engineering phases to transition CodeBrain from an L1 assistive prompt-wrapper into an L2/L3 autonomous quality engineering platform.

---

## Phase Matrix Overview

| Phase | Core Objective | Key Deliverables | Target Architecture |
|---|---|---|---|
| **Phase 1: Reliability & Output Hardening** | Fix routing bugs, harden JSON parsing, and expand intake formats. | - URL route normalization<br>- Pydantic v2 structured outputs<br>- Multi-format PRD ingestion (.md, .txt, .docx)<br>- Excel/CSV export & review persistence | Deterministic data contracts & reliable foundational UX |
| **Phase 2: Closed-Loop API Runner & Universal LLMs** | Transform generated test cases into executable, verifiable assertions. | - Async HTTPX API test execution engine<br>- JSONPath assertion runner<br>- Universal OpenAI/Claude/Ollama adapter<br>- Real-time token streaming over SSE<br>- Pytest & Postman export | Executable, closed-loop testing platform |
| **Phase 3: Zero-Docker RAG & Spec Ingestion** | Enable local vector search without external containers; support API schemas. | - ChromaDB embedded vector store backend<br>- OpenAPI 3.x / Swagger parser<br>- Postman Collection intake<br>- BM25 + Vector hybrid retrieval | Self-contained, zero-container local intelligence |
| **Phase 4: Multi-Agent Orchestration & Integrations** | Connect isolated agents into an autonomous QA feedback pipeline. | - Actor-Critic reflection loop (Generator ⇄ Reviewer)<br>- Unified PRD-to-Execution pipeline UI<br>- Jira, TestRail, & XMind mindmap export<br>- Headless CI/CD test execution CLI | Autonomous, enterprise-integrated quality workflow |

---

## Phase Dependencies & Progression

```
┌────────────────────────────────────────────────────────┐
│ Phase 1: Reliability & Output Hardening               │
│ - Normalized routes, Pydantic schemas, multi-format    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 2: Closed-Loop API Runner & Universal LLMs       │
│ - HTTPX execution engine, token streaming, Ollama/OpenAI│
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 3: Zero-Docker RAG & Spec Ingestion              │
│ - Embedded ChromaDB, OpenAPI/Swagger parser, BM25 RAG  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 4: Multi-Agent Orchestration & Integrations      │
│ - Actor-Critic loops, unified pipeline, Jira/TestRail  │
└────────────────────────────────────────────────────────┘
```

---

## Implementation Rules & Invariants

Across all phases, the following architectural invariants must be preserved:

1. **Zero-Docker Standalone Execution**: All local development and testing workflows must function without running Docker containers (SQLite default, embedded vector stores, mockable services).
2. **Deterministic Schemas**: Never rely on unanchored regular expressions to extract structured output from LLMs; enforce Pydantic v2 models and JSON schema validation.
3. **Zero AI-Signaling & Clean Maintainer Style**: Commit messages, documentation, and user interfaces must be declarative, factual, and devoid of marketing fluff.
4. **Backward Compatibility**: Existing database tables (`core_testcase`, `core_testcasereview`, `core_knowledgebase`) must migrate smoothly without schema breakage.
5. **Fail-Closed Fallbacks**: If external API keys or vector databases are offline, the system must degrade gracefully without crashing view handlers.
