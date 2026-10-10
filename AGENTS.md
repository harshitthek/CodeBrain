# CodeBrain Agents Architecture

CodeBrain implements an agentic testing framework where autonomous agents specialize in distinct phases of quality assurance. Each agent is packaged as an isolated Django sub-app under `apps/ai_agents/`, containing its own domain logic, prompt definitions, validation schemas, controllers, and UI views.

---

## Agent Roster

| Agent Name | Location | Primary Responsibility | Input Format | Output Format |
|---|---|---|---|---|
| `test_case_generator` | `apps/ai_agents/test_case_generator/` | Requirements-to-testcase generation | Structured text / requirement specs | Formatted test case suite (JSON & tabular) |
| `test_case_reviewer` | `apps/ai_agents/test_case_reviewer/` | Multi-criteria test case review & scoring | Existing test case definitions | Scoring rubric & improvement recommendations |
| `prd_analyzer` | `apps/ai_agents/prd_analyzer/` | Product requirements breakdown | PRD text / functional specifications | Functional decomposition & test point matrix |
| `iface_case_generator` | `apps/ai_agents/iface_case_generator/` | HTTP/RPC interface test generation | Endpoint spec, method, JSON payload/params | Positive, boundary, & negative test assertions |
| `java_code_analyzer` | `apps/ai_agents/java_code_analyzer/` | Source code testability analysis | Java method/class declarations | Exception paths, branch hotspots, test targets |

---

## Agent Deep Dives

### 1. Test Case Generator (`test_case_generator`)

**Purpose**: Transforms raw feature requirements and acceptance criteria into standardized, structured manual test case suites.

- **Entry Point**: `apps/ai_agents/test_case_generator/views.py` (`generate_cases`)
- **Prompt Definition**: `apps/ai_agents/test_case_generator/prompts.py` (`TestCaseGeneratorPrompt`)
- **Key Parameters**:
  - `requirements`: Freeform requirement text or user stories.
  - `design_methods`: Equivalence Partitioning, Boundary Value Analysis, Scenario Testing, Decision Table, Orthogonal Array.
  - `test_types`: Functional, Boundary, Exception, UI/Interaction, Performance, Security.
  - `case_count`: Target number of test cases.
- **Data Persistence**: Successful generations can be committed directly to the `TestCase` model in the relational database.
- **Streaming**: Supports live generation through Server-Sent Events (SSE) via `ProgressRegistry` and `SSELogEmitter`.

### 2. Test Case Reviewer (`test_case_reviewer`)

**Purpose**: Acts as an automated QA lead, auditing generated or authored test cases against industry standards.

- **Entry Point**: `apps/ai_agents/test_case_reviewer/views.py` (`review_cases`)
- **Prompt Definition**: `apps/ai_agents/test_case_reviewer/prompts.py` (`TestCaseReviewerPrompt`)
- **Evaluation Dimensions**:
  - **Completeness**: Evaluates precondition clarity, input specification, and expected outcome precision.
  - **Coverage**: Identifies overlooked boundary conditions and negative scenarios.
  - **Redundancy**: Flags duplicate test logic and low-value assertions.
  - **Feasibility**: Assesses step reproducibility and environment preconditions.
- **Data Persistence**: Scores and itemized reviews are recorded in the `TestCaseReview` model linked to the parent test case.

### 3. PRD Analyzer (`prd_analyzer`)

**Purpose**: Performs functional requirement decomposition to surface implicit edge cases and prevent specification gaps.

- **Entry Point**: `apps/ai_agents/prd_analyzer/views.py`
- **Prompt Definition**: `apps/ai_agents/prd_analyzer/prompts.py`
- **Output Schema**:
  - Module decomposition
  - User story boundaries
  - Test point matrix
  - Risk assessment and edge case catalog
- **Fault Tolerance**: Includes automatic JSON fence stripping and malformed JSON repair fallback to guarantee parseable output when working with reasoning models.

### 4. Interface Case Generator (`iface_case_generator`)

**Purpose**: Generates API contract tests, boundary scenarios, and JSONPath assertion suites for REST endpoints.

- **Entry Point**: `apps/ai_agents/iface_case_generator/views.py`
- **Prompt Definition**: `apps/ai_agents/iface_case_generator/prompts.py`
- **Schema Validation**: Uses Pydantic schema `apps/ai_agents/iface_case_generator/iface_test_case_schema.py` (`IfaceTestCaseData`, `JsonPathAssertionItem`).
- **Assertion Coverage**:
  - Status code verification (200, 400, 401, 403, 404, 422, 500)
  - Schema type validation
  - Field existence, nullability, and regex constraints
  - Header inspection and response timing budgets

### 5. Java Code Analyzer (`java_code_analyzer`)

**Purpose**: Bridges static source code inspection with black-box and grey-box testing.

- **Entry Point**: `apps/ai_agents/java_code_analyzer/views.py`
- **Prompt Definition**: `apps/ai_agents/java_code_analyzer/prompts.py`
- **Architecture**:
  - Coordinates with an optional AST parsing microservice (`JAVA_ANALYZER_SERVICE_URL`).
  - Identifies method signatures, cyclomatic complexity branches, unhandled exception paths, and parameter validations.
  - Converts identified code branches directly into recommended QA verification checklists.

---

## Inter-Agent Collaboration Pipeline

Agents can operate independently or sequentially:

```
[PRD Document]
      │
      ▼
┌──────────────┐
│ prd_analyzer │ ──> Functional Decomposition & Test Points
└──────────────┘
      │
      ▼
┌─────────────────────┐
│ test_case_generator │ ──> Structured Test Cases
└─────────────────────┘
      │
      ├──────────────────────────────┐
      ▼                              ▼
┌────────────────────┐   ┌──────────────────────┐
│ test_case_reviewer │   │ iface_case_generator │
└────────────────────┘   └──────────────────────┘
      │                              │
      ▼                              ▼
 [Quality Score]          [API Test Assertions]
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
   Implement prompt templates inheriting from base system instructions in `prompts.py`.

3. **Wire LLM Orchestration**:
   ```python
   from apps.llm.base import LLMServiceFactory
   from apps.llm.utils import get_agent_llm_configs

   config = get_agent_llm_configs("security_scanner")
   llm = LLMServiceFactory.create(config["default_provider"])
   ```

4. **Register in Django Settings**:
   Add `'apps.ai_agents.security_scanner.apps.SecurityScannerConfig'` to `INSTALLED_APPS` in `config/settings.py`.
   Add default model settings to `AGENT_LLM_DEFAULTS` in `config/settings.py`.

5. **Expose URLs**:
   Include `path('security_scanner/', include('apps.ai_agents.security_scanner.urls'))` in `config/urls.py`.
