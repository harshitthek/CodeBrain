# CodeBrain System Architecture

CodeBrain is an intelligent AI testing assistant platform built with Django, LangChain, and modern agentic engineering patterns. It orchestrates specialized AI agents across software quality assurance workflows.

---

## High-Level Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Presentation Layer (UI)                         │
│  - Django HTML5 Templates (Bootstrap 5, Select2, FontAwesome)         │
│  - Client-Side EventSource (SSE Listener for Live Logs & Progress)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / SSE
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      Application Layer (Django)                        │
│  ┌──────────────────┐  ┌────────────────────┐  ┌───────────────────┐  │
│  │   apps/core/     │  │  apps/ai_agents/   │  │  apps/knowledge/  │  │
│  │  - Dashboard     │  │  - TestCaseGen     │  │  - Document Intake│  │
│  │  - Test Cases    │  │  - CaseReviewer    │  │  - Vector Query   │  │
│  │  - Reviews DB    │  │  - PRDAnalyzer     │  │  - Embeddings     │  │
│  │  - SSE Endpoints │  │  - IfaceCaseGen    │  │                   │  │
│  │                  │  │  - JavaCodeAnalyzer│  │                   │  │
│  └──────────────────┘  └────────────────────┘  └───────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Service & Orchestration Layer                      │
│  ┌─────────────────────────┐  ┌────────────────────────────────────┐  │
│  │      apps/llm/          │  │           apps/utils/              │  │
│  │  - LLMServiceFactory    │  │  - ProgressRegistry (In-Memory)    │  │
│  │  - LangChain Model Wrap │  │  - SSELogEmitter (Stream Producer) │  │
│  │  - LoggingCallback      │  │  - LoggerManager                   │  │
│  └─────────────────────────┘  └────────────────────────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
┌───────────────────────────────────┐   ┌────────────────────────────────┐
│       Relational Storage          │   │         Vector Storage         │
│  - SQLite (Local zero-config dev) │   │  - Milvus 2.4.x (Standalone)   │
│  - MySQL 8.x (Production/UAT)     │   │  - BGE-M3 / Aliyun Embeddings  │
└───────────────────────────────────┘   └────────────────────────────────┘
```

---

## Layer Breakdown

### 1. Presentation Layer
- **HTML5 Templates**: Stored in `templates/` and app-specific `apps/ai_agents/*/templates/`.
- **Vanilla JavaScript**: Lightweight client logic in `static/js/` handling form submission, dynamic DOM rendering, and SSE connections.
- **Server-Sent Events (SSE)**: Long-running agent reasoning and generation tasks stream progress logs to the browser in real time without polling overhead.

### 2. Application Layer
- **`apps/core`**: Core models (`TestCase`, `TestCaseReview`, `KnowledgeBase`), shared dashboards, file upload handlers, and SSE streaming views (`stream_progress`).
- **`apps/ai_agents`**: Self-contained sub-applications for each agent persona.
- **`apps/knowledge`**: Document parsing and vector database access facade.

### 3. Service Layer
- **`apps/llm`**:
  - `LLMServiceFactory`: Factory returning initialized `ChatOpenAI` descendants.
  - `LoggingCallbackHandler`: LangChain callback capturing token usage, execution duration, and prompt/response truncation.
  - Dynamic model resolution using configuration in `config/settings.py`.
- **`apps/utils`**:
  - `ProgressRegistry`: Thread-safe dictionary tracking asynchronous task states (`pending`, `running`, `completed`, `failed`), step messages, and log queues.
  - `TaskContext`: Context manager abstracting lifecycle updates and exception handling during background execution.

### 4. Storage & Persistence
- **Relational DB**: Configured dynamically in `config/settings.py`. Defaults to SQLite (`db.sqlite3`) for local use; switches to MySQL when `USE_MYSQL=true` or `MYSQL_HOST` is present.
- **Vector DB**: Milvus 2.4.x instance used for semantic search over ingested documentation. Can be disabled via `ENABLE_MILVUS = False`.

---

## Real-Time Streaming Architecture (SSE)

```
Browser                       Django Server                      LLM / Task
   │                                │                                │
   ├── POST /generate/ ────────────>│                                │
   │                                ├── Generate task_id             │
   │                                ├── Spawn worker thread ────────>│
   │<── JSON {task_id} ─────────────┤                                │
   │                                │                                │
   ├── GET /progress/stream/{id} ──>│                                │
   │                                ├── SSELogEmitter                │
   │                                │   (yields data: {...}\n\n)     │
   │                                │<── emit log / update status ───┤
   │<── SSE message ────────────────┤                                │
   │<── SSE message ────────────────┤<── emit log / update status ───┤
   │<── SSE [DONE] ─────────────────┤                                │
   │                                │<── task finished ──────────────┤
```

1. The client initiates a task via standard HTTP POST and immediately receives a `task_id`.
2. The client opens an `EventSource` connection to `/progress/stream/<task_id>/`.
3. The background thread executes the agent pipeline, emitting step logs and percentage updates to `ProgressRegistry`.
4. `SSELogEmitter` streams these events to the client until completion.
