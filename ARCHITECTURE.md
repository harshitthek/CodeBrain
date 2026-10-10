# CodeBrain System Architecture

CodeBrain is an autonomous AI quality engineering platform built with Django, LangChain, Pydantic v2, and asynchronous HTTPX execution engines. It orchestrates specialized QA agents across requirement analysis, test case generation, multi-criteria auditing, live API contract testing, and enterprise TMS synchronization.

---

## High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           Presentation & CLI Layer                           │
│  - Django HTML5 UI (Bootstrap 5, EventSource SSE, /pipeline/ Auto-Pilot)     │
│  - React 18 + Vite Interactive Showcase (frontend/ — Vercel-ready)           │
│  - Headless CI/CD CLI (python manage.py run_test_suite)                      │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │ HTTP / SSE / CLI
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Application & Agent Layer                            │
│  ┌─────────────────────┐  ┌──────────────────────┐  ┌─────────────────────┐  │
│  │     apps/core/      │  │   apps/ai_agents/    │  │   apps/knowledge/   │  │
│  │ - Dashboard & Cases │  │ - ActorCriticEngine  │  │ - OpenAPI Parser    │  │
│  │ - /pipeline/ Views  │  │ - TestCaseGenerator  │  │ - Postman Parser    │  │
│  │ - Jira / TestRail   │  │ - TestCaseReviewer   │  │ - HybridRetriever   │  │
│  │ - XMind / JUnit XML │  │ - PRDAnalyzer        │  │ - Chroma/SQLite DB  │  │
│  │ - SSE Stream Views  │  │ - IfaceCaseGenerator │  │ - Milvus Facade     │  │
│  │                     │  │ - APITestRunner      │  │                     │  │
│  │                     │  │ - JavaCodeAnalyzer   │  │                     │  │
│  └─────────────────────┘  └──────────────────────┘  └─────────────────────┘  │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Service & Infrastructure Layer                        │
│  ┌────────────────────────────────┐  ┌────────────────────────────────────┐  │
│  │           apps/llm/            │  │            apps/utils/             │  │
│  │ - Universal LLMServiceFactory  │  │ - ProgressRegistry (Thread-Safe)   │  │
│  │   (DeepSeek, Qwen, OpenAI,     │  │ - SSELogEmitter (Stream Producer)  │  │
│  │    Ollama, Groq, Custom vLLM)  │  │ - TaskContext Lifecycle Manager    │  │
│  └────────────────────────────────┘  └────────────────────────────────────┘  │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                     ┌─────────────────┴─────────────────┐
                     ▼                                   ▼
┌─────────────────────────────────────┐   ┌────────────────────────────────────┐
│         Relational Storage          │   │       Vector & Lexical Storage     │
│  - SQLite (Default zero-config dev) │   │  - Embedded SQLite/Chroma Store    │
│  - MySQL 8.x (Production/UAT)       │   │  - PureBM25Index + RRF Fusion      │
│                                     │   │  - Milvus 2.x (Optional Cluster)   │
└─────────────────────────────────────┘   └────────────────────────────────────┘
```

---

## Layer Breakdown

### 1. Presentation & CLI Layer
- **Django Server-Rendered UI**: Templates in `templates/` and `apps/ai_agents/*/templates/`, plus the unified multi-agent Auto-Pilot console in `apps/core/templates/pipeline.html`.
- **Interactive Showcase (`frontend/`)**: Standalone Vite + React + TypeScript showcase configured with `vercel.json` for static/edge hosting.
- **Headless CLI (`run_test_suite.py`)**: Django management command for executing API test suites in CI/CD pipelines with JUnit XML and JSON summary output.

### 2. Application & Orchestration Layer
- **`apps/ai_agents/common/orchestrator.py` (`ActorCriticReflectionEngine`)**: Runs iterative `Generator ⇄ Reviewer` feedback loops with monotonic regression safeguards, ensuring refined test suites never degrade below previously achieved quality scores.
- **`apps/ai_agents/iface_case_generator/runner.py` (`APITestRunner`)**: Asynchronous `httpx` execution engine with `verify_tls=True` by default, SSRF/DNS-rebinding guards (`_resolve_safe_target` + IP pinning + HTTPS `sni_hostname`), and JSONPath/regex assertion evaluators.
- **`apps/core/exporters/`**: Pluggable enterprise exporters for **Jira Cloud** (`JiraExporter`), **TestRail** (`TestRailExporter`), **XMind (`.xmind`)** (`XMindExporter`), and **JUnit XML** (`JUnitExporter`).

### 3. Universal LLM Service Layer (`apps/llm/`)
- **`LLMServiceFactory` (`apps/llm/base.py`)**: Instantiates `DeepSeekChatModel`, `QwenChatModel`, or `ChatOpenAI` adapters for `openai`, `ollama`, `groq`, and custom OpenAI-compatible endpoints, enforcing provider-scoped API keys and masked credential logging.

### 4. Storage & Hybrid RAG Layer (`apps/knowledge/`)
- **Relational DB**: Defaults to SQLite (`db.sqlite3`); switches to MySQL when `USE_MYSQL=true` or `MYSQL_HOST` is set.
- **Zero-Docker Hybrid RAG**: Combines `PersistentSQLiteVectorStore` (`chroma_store.py`) and `PureBM25Index` (`hybrid_retriever.py`) via Reciprocal Rank Fusion (RRF), with optional Milvus cluster support (`ENABLE_MILVUS = True`).

---

## Real-Time Streaming Architecture (SSE)

```
Browser                       Django Server                      LLM / Agent Task
   │                                │                                    │
   ├── POST /generate/ ────────────>│                                    │
   │                                ├── Generate task_id                 │
   │                                ├── Spawn worker thread ────────────>│
   │<── JSON {task_id} ─────────────┤                                    │
   │                                │                                    │
   ├── GET /progress/stream/{id} ──>│                                    │
   │                                ├── SSELogEmitter                    │
   │                                │   (yields data: {...}\n\n)         │
   │                                │<── emit log / update percentage ───┤
   │<── SSE message ────────────────┤                                    │
   │<── SSE [DONE] ─────────────────┤<── task completed ─────────────────┤
```

1. The client initiates a task via HTTP POST and receives a `task_id`.
2. The client opens an `EventSource` connection to `/progress/stream/<task_id>/`.
3. The background worker executes the agent or pipeline, publishing step logs and completion percentages to `ProgressRegistry`.
4. `SSELogEmitter` streams events to the browser until completion.
