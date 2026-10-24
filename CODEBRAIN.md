# CodeBrain: Complete Project & Interview Study Guide

> **Quick Summary**: CodeBrain is an autonomous AI quality engineering platform that converts product requirements (PRDs), API specifications (OpenAPI/Postman), and source code into verified, executable test suites. Instead of a simple single-pass prompt, it uses an **Actor-Critic reflection loop**, runs live HTTP assertions asynchronously with built-in SSRF protection, and exports directly to enterprise test management systems (Jira, TestRail, XMind, Pytest, JUnit).

---

## Table of Contents
1. [The Problem and Our Solution](#1-the-problem-and-our-solution)
2. [How Our Project Solves the Problem](#2-how-our-project-solves-the-problem)
3. [Architecture of the Project](#3-architecture-of-the-project)
4. [How It Works (End-to-End Workflow)](#4-how-it-works-end-to-end-workflow)
5. [Feasibility Analysis](#5-feasibility-analysis)
6. [Comprehensive Interview Questions & Answers](#6-comprehensive-interview-questions--answers)
   - [System Design & Multi-Agent Architecture](#a-system-design--multi-agent-architecture)
   - [AI, LLM Orchestration & Prompt Engineering](#b-ai-llm-orchestration--prompt-engineering)
   - [Security & Network Hardening](#c-security--network-hardening)
   - [Quality Engineering & Domain Expertise](#d-quality-engineering--domain-expertise)
   - [Production Scalability & CI/CD](#e-production-scalability--cicd)

---

## 1. The Problem and Our Solution

### The Core Problem
In traditional software development and QA engineering, testing suffers from five major bottlenecks:
1. **Manual & Labor-Intensive Test Authoring**: QA engineers spend 40–60% of their sprint analyzing PRDs, manually writing test scenarios, boundary conditions, and edge cases.
2. **Ambiguous & Rapidly Evolving PRDs**: Requirements are often incomplete, leading to missed corner cases, regressions, and production bugs.
3. **Flaws of Naive GenAI ("Prompt Wrappers")**: 
   - LLMs hallucinate invalid inputs or unrealistic steps.
   - They output malformed JSON or markdown fences that crash automated parsers.
   - Single-pass generation lacks self-correction: if the initial prompt misses an edge case, the output stays incomplete.
4. **The Disconnect Between Authoring and Execution (Open-Loop Testing)**: Generated test cases usually live as static text in Word docs or spreadsheets; they are not executable code and don't verify against live APIs.
5. **Heavy Infrastructure Overhead & Tool Silos**: Enterprise RAG systems usually require complex Dockerized vector databases (Milvus clusters), and transferring tests into Jira, TestRail, or CI/CD pipelines requires tedious copy-pasting.

### Our Solution: CodeBrain
**CodeBrain** is an **Autonomous Multi-Agent AI Quality Engineering & Closed-Loop API Testing Platform**.
- **Specialized Autonomous Agents**: Decomposes the QA workflow across dedicated agents for requirement breakdown, test generation, test review, live API execution, and Java code analysis.
- **Actor-Critic Reflection Engine**: Pairs an Actor (*Generator*) with an automated Critic (*Reviewer*) in a self-healing feedback loop that scores and refines suites until they meet a strict quality threshold (e.g. $\ge 85/100$).
- **Monotonic Regression Safeguards**: Ensures that iterative refinement never degrades suite quality below an earlier pass.
- **Closed-Loop Execution**: Validates generated API tests against real endpoints using an asynchronous HTTPX runner with JSONPath assertion evaluation.
- **Zero-Docker Hybrid RAG**: Provides local BM25 lexical search + dense vector retrieval with Reciprocal Rank Fusion (RRF) using embedded SQLite, requiring zero external database containers.
- **Enterprise Ecosystem Integration**: 1-click native export to Jira Cloud, TestRail, XMind mind-maps, Excel (.xlsx), Pytest scripts, Postman v2.1 collections, and JUnit XML.

---

## 2. How Our Project Solves the Problem

| Pain Point | How CodeBrain Solves It | Key Component |
|---|---|---|
| **Ambiguous Requirements** | Automatically ingests `.docx`, `.md`, or `.txt` PRDs; extracts functional boundaries, user stories, acceptance criteria, and missing risk catalogs. | [`prd_analyzer`](file:///Users/pernavjain/Documents/CodeBrain/apps/ai_agents/prd_analyzer/views.py) |
| **Hallucinations & Broken JSON** | Enforces strict Pydantic v2 data models with multi-strategy regex fallback parsers that strip markdown fences and repair syntax errors. | [`schemas.py`](file:///Users/pernavjain/Documents/CodeBrain/apps/ai_agents/test_case_generator/schemas.py) |
| **Low-Quality / Incomplete Tests** | Critic agent scores candidate suites across 4 dimensions: *Completeness*, *Coverage*, *Redundancy*, and *Feasibility*. Refines iteratively if score < 85. | [`orchestrator.py`](file:///Users/pernavjain/Documents/CodeBrain/apps/ai_agents/common/orchestrator.py) |
| **Static Tests That Don't Run** | Closed-loop asynchronous runner executes HTTP requests live, verifies status codes, dot-paths, and JSONPath assertions, and flags failures. | [`APITestRunner`](file:///Users/pernavjain/Documents/CodeBrain/apps/ai_agents/iface_case_generator/runner.py) |
| **Complex Docker Dependencies** | Lightweight embedded SQLite vector store + pure-Python Okapi BM25 engine running out-of-the-box on local dev machines without Docker. | [`PersistentSQLiteVectorStore`](file:///Users/pernavjain/Documents/CodeBrain/apps/knowledge/chroma_store.py), [`HybridRetriever`](file:///Users/pernavjain/Documents/CodeBrain/apps/knowledge/hybrid_retriever.py) |
| **Manual Copy-Pasting to TMS** | Generates Jira Cloud issues, TestRail suites, XMind hierarchical mind-maps, sanitized Excel sheets, and headless CI/CD JUnit XML. | [`apps/core/exporters/`](file:///Users/pernavjain/Documents/CodeBrain/apps/core/exporters/) |

---

## 3. Architecture of the Project

CodeBrain is designed as a **modular 4-tier architecture** adhering to clean separation of concerns:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         1. Presentation & CLI Layer                          │
│  - Django HTML5 UI (Bootstrap 5, Server-Sent Events / SSE for live logs)     │
│  - React 18 + TypeScript + Vite Interactive Showcase (frontend/)             │
│  - Headless CI/CD CLI (python manage.py run_test_suite)                      │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │ HTTP / SSE / CLI
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                      2. Application & Multi-Agent Layer                      │
│  ┌───────────────────────┐ ┌────────────────────────┐ ┌────────────────────┐ │
│  │   ActorCriticEngine   │ │   TestCaseGenerator    │ │  TestCaseReviewer  │ │
│  │ (orchestrator.py)     │ │ (Pydantic v2 Schemas)  │ │ (4-D Rubric Score) │ │
│  └───────────────────────┘ └────────────────────────┘ └────────────────────┘ │
│  ┌───────────────────────┐ ┌────────────────────────┐ ┌────────────────────┐ │
│  │      PRDAnalyzer      │ │   IfaceCaseGenerator   │ │  JavaCodeAnalyzer  │ │
│  │ (.docx/.md/.txt RAG)  │ │ (Async APITestRunner)  │ │ (AST & Hotspots)   │ │
│  └───────────────────────┘ └────────────────────────┘ └────────────────────┘ │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    3. Service & Infrastructure Layer                         │
│  ┌────────────────────────────────────┐ ┌──────────────────────────────────┐ │
│  │     Universal LLMServiceFactory    │ │  Real-Time Progress & Telemetry  │ │
│  │ (DeepSeek, Qwen, OpenAI, Ollama,   │ │ (ProgressRegistry, SSELogEmitter,│ │
│  │  Groq, custom OpenAI/vLLM endpoints)│ │  TaskContext lifecycle manager) │ │
│  └────────────────────────────────────┘ └──────────────────────────────────┘ │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                     ┌─────────────────┴─────────────────┐
                     ▼                                   ▼
┌────────────────────────────────────────┐ ┌───────────────────────────────────┐
│          4. Relational Storage         │ │    4. Vector & Lexical Storage    │
│ - SQLite 3 (Zero-config local default) │ │ - PersistentSQLiteVectorStore     │
│ - MySQL 8.x (Production/UAT)           │ │ - PureBM25Index (Okapi BM25)      │
│ - Django ORM Models (TestCase, Review) │ │ - RRF (Reciprocal Rank Fusion)    │
│                                        │ │ - Milvus 2.x (Optional Cluster)   │
└────────────────────────────────────────┘ └───────────────────────────────────┘
```

### Module Breakdown
- **`apps/ai_agents/`**: Contains domain-specific AI sub-apps with their own views, prompt definitions, and schemas.
- **`apps/core/`**: Central dashboard, database models (`TestCase`, `TestCaseReview`), Auto-Pilot pipeline (`/pipeline/`), and enterprise exporters.
- **`apps/knowledge/`**: Document ingestion, OpenAPI 3.x / Swagger 2.0 parser, Postman collection parser, and the zero-Docker hybrid retriever.
- **`apps/llm/`**: Factory pattern supporting runtime model switching (DeepSeek, Qwen, OpenAI, Groq, Ollama) with masked API keys.
- **`apps/utils/`**: Thread-safe progress registry and Server-Sent Events (SSE) bus for real-time frontend streaming.

---

## 4. How It Works (End-to-End Workflow)

The complete lifecycle from raw requirement to executed test suite follows 5 distinct stages:

```
[PRD / Spec Intake] ──> [Hybrid RAG Retrieval] ──> [Actor-Critic Reflection] ──> [Closed-Loop API Run] ──> [Enterprise TMS Export]
  (.docx / OpenAPI)       (BM25 + Dense Vectors)      (Generator ⇄ Reviewer)       (Async HTTPX Runner)     (Jira / Pytest / JUnit)
```

```
Step 1: Intake & Ingestion
  │  • Upload PRD (.docx, .md, .txt) or API spec (OpenAPI JSON/YAML, Postman JSON).
  │  • System extracts endpoints, parameters, request bodies, and functional requirements.
  ▼
Step 2: Context Augmentation (Hybrid RAG)
  │  • PureBM25Index captures exact keyword matches (API paths, status codes, param names).
  │  • PersistentSQLiteVectorStore captures semantic concepts.
  │  • Reciprocal Rank Fusion (RRF) merges results to feed enriched context to the agents.
  ▼
Step 3: Actor-Critic Reflection Loop (Self-Healing)
  │  • Iteration 1: Actor (Generator) generates structured test cases using QA methods
  │    (Equivalence Partitioning, Boundary Value Analysis, Scenario Testing).
  │  • Critic (Reviewer) audits the suite against 4 dimensions: Completeness, Coverage,
  │    Redundancy, Feasibility. Calculates score (0–100).
  │  • Condition: Is Score >= 85.0?
  │      ├─ YES ──> Converged! Proceed to Step 4.
  │      └─ NO  ──> Refinement Pass (bounded to max 2 iterations).
  │                 Critic injects itemized feedback (missing edge cases, weak assertions).
  │                 Actor regenerates suite addressing specific weaknesses.
  │                 Monotonic Safeguard: Retains highest-scoring suite if refinement regresses.
  ▼
Step 4: Closed-Loop Execution (API Testing)
  │  • APITestRunner dispatches asynchronous HTTP requests using HTTPX.
  │  • Security verification: Enforces TLS, blocks private/metadata IPs, pins DNS.
  │  • Evaluates assertions: Status code matching, dot-path & JSONPath extractions, regex checks.
  ▼
Step 5: Enterprise Export & Synchronization
     • 1-Click Sync to Jira Cloud (issues/tests) and TestRail (test suites/sections).
     • Visual Mind-Map export to XMind (.xmind) and Markdown.
     • Automated Excel (.xlsx) export with formula-injection sanitization.
     • Standalone Pytest script and Postman Collection v2.1 generation.
     • Headless CI/CD JUnit XML reporting for Jenkins, GitHub Actions, and GitLab CI.
```

### Real-Time Streaming Architecture (SSE)
To keep the UI responsive during multi-step LLM operations:
1. Client triggers a task via `POST` and receives a unique `task_id`.
2. Client opens an HTML5 `EventSource` connection to `/progress/stream/<task_id>/`.
3. Background worker threads publish step updates and percentage completion to [`ProgressRegistry`](file:///Users/pernavjain/Documents/CodeBrain/apps/utils/progress_registry.py).
4. [`SSELogEmitter`](file:///Users/pernavjain/Documents/CodeBrain/apps/utils/sse_bus.py) streams real-time updates (`data: {...}\n\n`) directly to the browser.

---

## 5. Feasibility Analysis

### A. Technical Feasibility (High)
- **Mature Tech Stack**: Built with Python 3.11, Django 5.x, Pydantic v2, HTTPX, and Openpyxl.
- **Strict Verification**: Comprehensive test suite with **61 passing automated tests** across all 4 modernization phases (`tests/test_phase1.py` through `tests/test_phase4.py`).
- **Zero-Docker Standalone Execution**: Operates out-of-the-box using embedded SQLite and local vectors. No Docker, Kubernetes, or background daemons are required to start developing.

### B. Operational & Cost Feasibility (High)
- **Universal LLM Flexibility**: Eliminates single-vendor lock-in. Developers can use:
  - Budget cloud models (DeepSeek, Groq, Qwen).
  - High-end models (OpenAI `gpt-4o-mini`).
  - **100% Free / Local Privacy-First models** via Ollama (`llama3`, `mistral`, `deepseek-coder`).
- **Token Efficiency**: Bounded iterations (`max_iterations = 2`) and targeted refinement prompts prevent runaway LLM costs and infinite token loops.

### C. Security Feasibility (Enterprise-Hardened)
- **SSRF & DNS Rebinding Protection**:
  - Outbound API requests block cloud instance metadata endpoints (`169.254.169.254`, `fd00:ec2::254`, `metadata.google.internal`).
  - Rejects private IPv4/IPv6 loopback, multicast, and link-local ranges by default.
  - Pins the pre-validated DNS IP address with HTTPS `sni_hostname` and `Host` header preservation.
- **Formula Injection Mitigation**: Excel exports force cell types to string (`data_type = 's'`) and escape leading `=`, `+`, `-`, or `@` characters to neutralize CSV/XLSX formula injection.
- **Credential Masking**: Automatically masks API keys in telemetry and log files.

### D. Integration Feasibility (Non-Disruptive)
- CodeBrain does not force teams to abandon their current tooling. It integrates smoothly into Jira, TestRail, Postman, and existing CI/CD pipelines via standard JUnit XML.

---

## 6. Comprehensive Interview Questions & Answers

### A. System Design & Multi-Agent Architecture

#### Q1: Why use an Actor-Critic architecture instead of a single prompt or standard prompt chaining?
> **Answer**: 
> A single-pass prompt is "open-loop": the LLM produces an answer without evaluating its quality, which frequently leads to hallucinations, missing boundary cases, or shallow assertions. 
> CodeBrain implements a **closed-loop Actor-Critic architecture** (`ActorCriticReflectionEngine`):
> 1. The **Actor** (*TestCaseGenerator*) generates a candidate test suite.
> 2. The **Critic** (*TestCaseReviewer*) evaluates the suite against an objective rubric (*Completeness, Coverage, Redundancy, Feasibility*).
> 3. If the score is below threshold (e.g. 85.0), the Critic generates an itemized critique containing specific gaps and missing scenarios.
> 4. The Actor receives this targeted critique and refines the suite. This feedback loop significantly raises test depth and consistency while keeping latency bounded.

#### Q2: What is the "Monotonic Regression Safeguard" and why is it necessary?
> **Answer**: 
> In LLM reflection loops, subsequent iterations are not guaranteed to be strictly better. Sometimes an LLM, while fixing one edge case, accidentally removes other valid test scenarios or reduces overall suite coherence. 
> CodeBrain's **Monotonic Regression Safeguard** tracks the quality score and candidate suite across every pass. If Iteration 2 scores lower than Iteration 1 (e.g., 78 vs 83), the orchestrator automatically discards the regressed suite and returns the highest-scoring candidate from Iteration 1.

#### Q3: Why did you choose Server-Sent Events (SSE) over WebSockets for live streaming?
> **Answer**: 
> 1. **Unidirectional Communication**: The workflow only requires the server to stream progress updates and logs down to the browser; the client does not need to send upstream messages during task execution.
> 2. **Simpler Protocol & Infrastructure**: SSE operates over standard HTTP/1.1 or HTTP/2, requiring no custom WebSocket handshakes, special reverse proxy configurations, or separate socket servers.
> 3. **Native Browser Reconnection**: HTML5 `EventSource` has built-in auto-reconnection and event ID tracking out of the box.

#### Q4: How does the Zero-Docker Hybrid RAG work?
> **Answer**: 
> Traditional RAG systems require external vector databases (like Milvus or Qdrant) running in Docker. CodeBrain implements a pure-Python, zero-Docker hybrid retrieval system:
> 1. **Dense Vector Search**: Uses [`PersistentSQLiteVectorStore`](file:///Users/pernavjain/Documents/CodeBrain/apps/knowledge/chroma_store.py) with cosine similarity over 384-dimensional dense vectors stored in a local SQLite table (`vector_chunks`).
> 2. **Lexical Keyword Search**: Uses [`PureBM25Index`](file:///Users/pernavjain/Documents/CodeBrain/apps/knowledge/hybrid_retriever.py), a zero-dependency Okapi BM25 implementation. This is critical for exact keyword matches on technical symbols like API paths (`/api/v1/orders`), parameter names, and HTTP error codes.
> 3. **Reciprocal Rank Fusion (RRF)**: Merges the ranked lists from both dense and lexical retrievers using:
>    $$\text{RRF\_Score}(d) = \frac{w_{\text{dense}}}{60 + \text{rank}_{\text{dense}}(d)} + \frac{w_{\text{bm25}}}{60 + \text{rank}_{\text{bm25}}(d)}$$
> This ensures balanced retrieval: semantic concepts from the vector store and exact identifier matches from BM25.

---

### B. AI, LLM Orchestration & Prompt Engineering

#### Q5: How do you handle LLM hallucinations and malformed JSON output?
> **Answer**: 
> We implement a multi-layered defense:
> 1. **Pydantic v2 Schema Enforcement**: Every output must parse into strict models (`GeneratedTestCaseItem`, `TestSteps`, etc.) with type validation and defaults.
> 2. **Multi-Strategy JSON Extractor**: 
>    - Strategy 1: Standard `json.loads` after regex-stripping markdown code fences (````json ... ````).
>    - Strategy 2: Bracket matching (`{...}` / `[...]`) to extract embedded JSON objects even if the LLM output contains conversational preamble or postscript.
>    - Strategy 3: Heuristic text fallback parser to recover test steps and expected results if the JSON is truncated.
> 3. **Normalizer Functions**: Automatically convert single string steps into lists and coerce malformed priorities (e.g. "urgent" $\rightarrow$ "High").

#### Q6: How does CodeBrain prevent LLM vendor lock-in?
> **Answer**: 
> Through the **Universal LLM Factory** (`LLMServiceFactory` in [`apps/llm/base.py`](file:///Users/pernavjain/Documents/CodeBrain/apps/llm/base.py)). It abstracts provider differences behind a unified LangChain-compatible interface. By simply setting environment variables or selecting a provider in the UI, users can switch between:
> - **DeepSeek** (`DeepSeekChatModel`)
> - **Qwen** (`QwenChatModel`)
> - **OpenAI** (`ChatOpenAI` / `gpt-4o-mini`)
> - **Groq** (ultra-fast inference)
> - **Ollama** (offline local models)
> - **Custom OpenAI-compatible gateways** (vLLM, LiteLLM)

#### Q7: How does CodeBrain handle circular `$ref` references in OpenAPI/Swagger schemas?
> **Answer**: 
> Real-world OpenAPI schemas often contain recursive data structures (e.g., a `Category` object with a list of child `Category` objects). Naive recursive parsers result in infinite recursion and `RecursionError`.
> In [`apps/knowledge/openapi_parser.py`](file:///Users/pernavjain/Documents/CodeBrain/apps/knowledge/openapi_parser.py), we maintain a visited reference set (`visited_refs`) during traversal. If a schema pointer is encountered that is already in the current resolution path, resolution halts and substitutes an elliptical mock object `{"_circular_ref": ref_path}`.

---

### C. Security & Network Hardening

#### Q8: What is SSRF and DNS Rebinding, and how does CodeBrain protect against them?
> **Answer**: 
> - **The Risk**: When an automated runner makes outbound HTTP requests to user-provided URLs or API specs, an attacker could supply endpoints like `http://169.254.169.254/latest/meta-data/` (to steal AWS cloud credentials) or `http://127.0.0.1:8000/admin` (to attack internal microservices). Furthermore, in a **DNS Rebinding** attack, a domain initially resolves to a benign public IP, but resolves to `127.0.0.1` at the moment of request execution.
> - **CodeBrain's Defense (`APITestRunner._resolve_safe_target`)**:
>   1. **Blacklisted IP Ranges**: Rejects link-local (`169.254.0.0/16`), IPv6 metadata (`fd00:ec2::254`), Google metadata (`metadata.google.internal`), multicast, reserved, and private/loopback addresses (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`).
>   2. **DNS Resolution & IP Pinning**: Resolves the hostname via `socket.getaddrinfo`, verifies that every returned IP is public and safe, and then pins the request directly to that validated IP address.
>   3. **SNI & Host Header Preservation**: When connecting to the pinned IP over HTTPS, sets `sni_hostname` and the `Host` header to the original domain name so TLS certificate validation succeeds without opening a DNS rebinding window.

#### Q9: What is Formula Injection (CSV/Excel Injection) and how did you mitigate it?
> **Answer**: 
> - **The Risk**: If test case descriptions or inputs contain characters like `=CMD|' /C calc'!A0` or `=SUM(...)`, opening the exported `.xlsx` workbook in Microsoft Excel could execute arbitrary system commands or exfiltrate data.
> - **Our Mitigation** in [`export_test_cases_excel`](file:///Users/pernavjain/Documents/CodeBrain/apps/ai_agents/test_case_reviewer/views.py):
>   1. Every written cell is explicitly forced to string data type (`cell.data_type = 's'`).
>   2. Any cell value starting with `=`, `+`, `-`, or `@` is sanitized by prefixing it with a single quote (`'`), rendering it as harmless literal text in Excel.

---

### D. Quality Engineering & Domain Expertise

#### Q10: What traditional QA design techniques does the Test Case Generator apply?
> **Answer**: 
> Rather than generating generic scenarios, the generator prompt instructs the LLM to systematically apply established QA design methods:
> 1. **Equivalence Partitioning (EP)**: Divides input data into valid and invalid partitions.
> 2. **Boundary Value Analysis (BVA)**: Tests minimum, just below minimum, nominal, just above maximum, and maximum values.
> 3. **Decision Table Testing**: Maps combinations of input conditions to specific output actions.
> 4. **Orthogonal Array Testing**: Generates pairwise combinations to maximize multi-variable test coverage with minimal test count.
> 5. **Negative & Exception Testing**: Explicitly tests timeouts, authorization failures, malformed payloads, and SQLi/XSS boundaries.

#### Q11: What are the 4 review dimensions evaluated by the Critic agent?
> **Answer**:
> 1. **Completeness**: Are preconditions, test steps, test data, and expected outcomes explicitly defined?
> 2. **Coverage**: Does the suite cover normal paths, boundary values, error conditions, and user experience edge cases?
> 3. **Redundancy**: Are there duplicate test cases or redundant assertions that add maintenance overhead without adding test value?
> 4. **Feasibility**: Are the steps unambiguous, reproducible, and executable by any engineer or automation script?

#### Q12: How does the closed-loop API runner evaluate test assertions?
> **Answer**: 
> In [`runner.py`](file:///Users/pernavjain/Documents/CodeBrain/apps/ai_agents/iface_case_generator/runner.py), the runner evaluates assertions across 3 targets:
> 1. **Status Code**: Checks whether the HTTP response code matches expected status (e.g. `200`, `201`, `400`).
> 2. **JSONPath & Dot-Notation Extraction**: Uses `jsonpath-ng.ext` to query deeply nested response fields (e.g. `$.data.user.id` or `orders[0].status`).
> 3. **Assertion Operators**: Supports `EQUALS`, `NOT_EQUALS`, `CONTAINS`, `NOT_CONTAINS`, `GREATER_THAN`, `LESS_THAN`, `IS_NULL`, `NOT_NULL`, and `REGEX_MATCH`.

---

### E. Production Scalability & CI/CD

#### Q13: How does CodeBrain integrate into an automated CI/CD pipeline?
> **Answer**: 
> CodeBrain provides a dedicated headless CLI management command:
> ```bash
> python manage.py run_test_suite path/to/suite.json \
>   --base-url https://api.staging.example.com \
>   --junit-output reports/junit.xml \
>   --json-output reports/summary.json
> ```
> - **JUnit XML Compatibility**: Standard test report format parsed natively by GitHub Actions, GitLab CI, and Jenkins.
> - **Exit Codes**: Returns exit code `0` on 100% pass, and `1` on any failure, allowing build pipelines to break on regressions automatically.

#### Q14: If this platform needs to scale to 10,000 QA engineers, where are the bottlenecks and how would you resolve them?
> **Answer**: 
> | Potential Bottleneck | Resolution Strategy |
> |---|---|
> | **LLM Rate Limits & Latency** | Implement token bucket rate limiters, response caching for identical spec chunks, and distributed fallback across multiple LLM API keys or self-hosted vLLM clusters. |
> | **Synchronous Worker Threads** | Replace Python in-process threads with a distributed task queue using **Celery + Redis / RabbitMQ**, allowing worker nodes to autoscale horizontally. |
> | **Relational DB Contention** | Switch from local SQLite to **MySQL 8.x / PostgreSQL** with connection pooling (e.g., PgBouncer), read replicas, and indexed query optimizations. |
> | **Vector Search Scale** | Switch from embedded SQLite vectors to the built-in **Milvus 2.x cluster mode** (`ENABLE_MILVUS = True`), which supports billions of vectors with partitioned indices. |
> | **SSE Connection Concurrency** | Offload SSE connection handling to an asynchronous ASGI server (e.g., Uvicorn / Daphne) or an edge reverse proxy (e.g., NGINX / Cloudflare). |

---

## 7. Key Project Metrics & Highlights (Elevator Pitch)

- **Language & Framework**: Python 3.11+, Django 5.x, React 18 + Vite
- **Test Automation**: 61/61 pytest tests passing across 4 phases
- **Key Architectures**: Actor-Critic Reflection Loop, Monotonic Regression Safeguard, Zero-Docker Hybrid RAG (BM25 + Dense Vectors via RRF)
- **Security Hardened**: SSRF protection, DNS rebinding prevention with IP pinning, Excel formula injection sanitization
- **Enterprise Ready**: 1-click sync with Jira Cloud, TestRail, XMind, Pytest, Postman v2.1, and JUnit XML
