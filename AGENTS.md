# CodeBrain Agents Architecture

CodeBrain implements an agentic quality engineering framework where autonomous agents specialize in distinct phases of software testing and collaborate via an Actor-Critic reflection orchestrator. Each agent is packaged as an isolated Django sub-app under `apps/ai_agents/`, containing its own domain logic, prompt definitions, Pydantic v2 validation schemas, controllers, and UI views.

---

## Agent & Orchestrator Roster

| Component | Location | Primary Responsibility | Input Format | Output Format |
|---|---|---|---|---|
| `orchestrator` | `apps/ai_agents/common/orchestrator.py` | Autonomous Actor-Critic reflection loop (`Generator ⇄ Reviewer`) | Requirements text, target score, max iterations | Converged test suite, iteration history, quality rubric telemetry |
| `test_case_generator` | `apps/ai_agents/test_case_generator/` | Requirements-to-testcase generation | Structured text / requirement specs | Pydantic-validated test case suite (JSON & tabular) |
| `test_case_reviewer` | `apps/ai_agents/test_case_reviewer/` | Multi-criteria test case review & scoring | Existing test case definitions | Scoring rubric, improvement recommendations, & `.xlsx` export |
| `prd_analyzer` | `apps/ai_agents/prd_analyzer/` | Product requirements breakdown | `.docx`, `.md`, `.txt`, or pasted PRD text | Functional decomposition & test point matrix |
| `iface_case_generator` | `apps/ai_agents/iface_case_generator/` | HTTP/REST interface test generation, execution, & export | Endpoint spec, OpenAPI 3.x / Swagger 2.0, or Postman Collection | Positive/boundary/negative assertions, live `httpx` run results, Pytest & Postman exports |
| `java_code_analyzer` | `apps/ai_agents/java_code_analyzer/` | Source code testability analysis | Java method/class declarations | Exception paths, branch hotspots, test targets |

---

## Agent Deep Dives

### 1. Autonomous Actor-Critic Orchestrator (`apps/ai_agents/common/orchestrator.py`)

**Purpose**: Connects the Test Case Generator (*Actor*) and Test Case Reviewer (*Critic*) in a bounded feedback loop (`ActorCriticReflectionEngine`).

- **Entry Point**: `apps/core/views.py` (`pipeline_view`, `pipeline_run_api`, `pipeline_export_tms`) at `/pipeline/`
- **Convergence Mechanics**:
  - Generates an initial suite via `TestCaseGeneratorAgent` and audits it via `TestCaseReviewerAgent`.
  - If the rubric score is below `min_score` (default `85.0`) and `iteration < max_iterations`, constructs a targeted refinement prompt containing the reviewer's itemized feedback and weak dimensions.
  - **Monotonic Regression Safeguard**: Tracks the highest-scoring suite across all iterations so that if a subsequent pass scores lower, the best suite is preserved.
- **Enterprise Exports**: Directly exports converged suites to **Jira Cloud** (`JiraExporter`), **TestRail** (`TestRailExporter`), **XMind (`.xmind`)** (`XMindExporter`), **Markdown** mind-maps, and **JUnit XML** (`JUnitExporter`).

### 2. Test Case Generator (`test_case_generator`)

**Purpose**: Transforms raw feature requirements and acceptance criteria into standardized, structured manual test case suites.

- **Entry Point**: `apps/ai_agents/test_case_generator/views.py` (`generate_cases`)
- **Prompt Definition**: `apps/ai_agents/test_case_generator/prompts.py` (`TestCaseGeneratorPrompt`)
- **Schema Validation**: `apps/ai_agents/test_case_generator/schemas.py` (`GeneratedTestCaseItem`, `extract_and_parse_test_cases`)
  - Normalizes string or list `test_steps`, `expected_results`, and `preconditions`.
  - Rejects empty required fields and repairs markdown code fences or trailing commas in LLM JSON outputs.
- **Key Parameters**:
  - `requirements`: Freeform requirement text or user stories.
  - `design_methods`: Equivalence Partitioning, Boundary Value Analysis, Scenario Testing, Decision Table, Orthogonal Array.
  - `test_types`: Functional, Boundary, Exception, UI/Interaction, Performance, Security.
  - `case_count`: Target number of test cases.
- **Data Persistence & Streaming**: Commits generated suites to the `TestCase` model and streams real-time progress via `ProgressRegistry` and `SSELogEmitter`.

### 3. Test Case Reviewer (`test_case_reviewer`)

**Purpose**: Acts as an automated QA lead, auditing generated or authored test cases against industry standards.

- **Entry Point**: `apps/ai_agents/test_case_reviewer/views.py` (`review_cases`, `export_test_cases_excel`)
- **Prompt Definition**: `apps/ai_agents/test_case_reviewer/prompts.py` (`TestCaseReviewerPrompt`)
- **Evaluation Dimensions**:
  - **Completeness**: Evaluates precondition clarity, input specification, and expected outcome precision.
  - **Coverage**: Identifies overlooked boundary conditions and negative scenarios.
  - **Redundancy**: Flags duplicate test logic and low-value assertions.
  - **Feasibility**: Assesses step reproducibility and environment preconditions.
- **Excel Export**: Exports selected or all reviewed test cases to `.xlsx` workbooks using `openpyxl`, preserving stored priorities, enforcing `core.view_testcase` permission, and forcing string cell types (`data_type = 's'`) with leading `=` escaping.

### 4. PRD Analyzer (`prd_analyzer`)

**Purpose**: Performs functional requirement decomposition to surface implicit edge cases and prevent specification gaps.

- **Entry Point**: `apps/ai_agents/prd_analyzer/views.py` (`prd_analyzer`, `extract_content_from_file`)
- **Supported Formats**: `.docx` (converted via `pypandoc` using isolated per-request temporary files), `.md`, `.txt`, or pasted text (explicitly honoring active tab `input_mode`).
- **Output Schema**:
  - Module decomposition
  - User story boundaries
  - Test point matrix
  - Risk assessment and edge case catalog

### 5. Interface Case Generator & Closed-Loop Runner (`iface_case_generator`)

**Purpose**: Generates API contract tests, executes them asynchronously against live targets, and exports runnable test code.

- **Entry Points**: `apps/ai_agents/iface_case_generator/views.py` (`generate_iface_cases`, `parse_spec_file`, `execute_test_cases`, `export_pytest_view`, `export_postman_view`)
- **Spec Ingestion**: Parses **OpenAPI 3.x / Swagger 2.0** (`apps/knowledge/openapi_parser.py`) and **Postman Collections** (`apps/knowledge/postman_parser.py`) into normalized endpoint definitions.
- **Async Execution Engine (`runner.py` — `APITestRunner`)**:
  - Executes suites concurrently via `httpx.AsyncClient` with `asyncio.Semaphore` concurrency control and TLS verification (`verify_tls=True`).
  - **SSRF & DNS Rebinding Protection**: Rejects cloud metadata endpoints (`169.254.169.254`, `fd00:ec2::254`, `metadata.google.internal`), link-local/multicast/reserved ranges, and private/loopback addresses by default, pinning the validated DNS IP with HTTPS `sni_hostname` and `Host` header preservation.
  - **Assertion Operators**: `EQUALS`, `NOT_EQUALS`, `CONTAINS`, `NOT_CONTAINS`, `GREATER_THAN`, `LESS_THAN`, `IS_NULL`, `NOT_NULL`, and `REGEX_MATCH` over status codes, dot-notation paths, and `jsonpath-ng` expressions.
- **Exporters (`exporters.py`)**:
  - `generate_pytest_script`: Emits syntactically valid, self-contained `pytest` + `httpx` test modules with `repr()`-escaped literals and JSONPath assertion helpers.
  - `generate_postman_collection`: Emits Postman Collection v2.1.0 JSON with pre-configured `pm.test(...)` scripts.

### 6. Java Code Analyzer (`java_code_analyzer`)

**Purpose**: Bridges static source code inspection with black-box and grey-box testing.

- **Entry Point**: `apps/ai_agents/java_code_analyzer/views.py`
- **Prompt Definition**: `apps/ai_agents/java_code_analyzer/prompts.py`
- **Architecture**: Coordinates with an optional AST parsing service (`JAVA_ANALYZER_SERVICE_URL`) to identify method signatures, cyclomatic complexity branches, and unhandled exception paths.

---

## Inter-Agent Collaboration Pipeline

```
[PRD Document (.docx / .md / .txt)]        [OpenAPI 3.x / Swagger / Postman Spec]
                │                                            │
                ▼                                            ▼
       ┌────────────────┐                         ┌──────────────────────┐
       │  prd_analyzer  │                         │ iface_case_generator │
       └────────┬───────┘                         └──────────┬───────────┘
                │                                            │
                ▼                                            ├──> Live Async HTTPX Runner
   ┌─────────────────────────┐                               ├──> Pytest Script Export
   │   test_case_generator   │◄──────────┐                   └──> Postman v2.1 Export
   └────────────┬────────────┘           │
                │                        │ Actor-Critic
                ▼                        │ Feedback Loop
   ┌─────────────────────────┐           │ (if score < threshold)
   │   test_case_reviewer    ├───────────┘
   └────────────┬────────────┘
                │
                ▼ (Converged Suite)
   ┌─────────────────────────────────────────────────────────┐
   │ Enterprise Export: Jira | TestRail | XMind | JUnit | XLSX│
   └─────────────────────────────────────────────────────────┘
```

---

## Adding a New Agent

To register a new custom agent (e.g. `security_scanner`):

1. **Create the App Directory**:
   ```
   apps/ai_agents/security_scanner/
   ├── __init__.py
   ├── apps.py
   ├── prompts.py
   ├── views.py
   ├── urls.py
   ├── templates/
   └── static/
   ```

2. **Define Prompt and Schema**:
   Implement prompt templates inheriting from base system instructions in `prompts.py` and Pydantic v2 output schemas in `schemas.py`.

3. **Wire LLM Orchestration**:
   ```python
   from apps.llm.base import LLMServiceFactory
   from apps.llm.utils import get_agent_llm_configs

   config = get_agent_llm_configs("security_scanner")
   llm = LLMServiceFactory.create(config["default_provider"])
   ```

4. **Register in Django Settings**:
   Add `'apps.ai_agents.security_scanner.apps.SecurityScannerConfig'` to `INSTALLED_APPS` and default model settings to `AGENT_LLM_DEFAULTS` in `config/settings.py`.

5. **Expose URLs**:
   Include `path('security_scanner/', include('apps.ai_agents.security_scanner.urls'))` in `config/urls.py`.
