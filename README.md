<div align="center">

# CodeBrain

**Autonomous Multi-Agent AI Quality Engineering & Closed-Loop API Testing Platform**

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django 6.x](https://img.shields.io/badge/Django-6.x-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Tests](https://img.shields.io/badge/Tests-pytest-2ea44f?logo=pytest&logoColor=white)](tests/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

[Architecture](ARCHITECTURE.md) · [Agents Guide](AGENTS.md) · [Hybrid RAG & Memory](MEMORY.md) · [Roadmap](PHASES.md) · [Design System](DESIGN.md)

</div>

---

## Overview

**CodeBrain** is an autonomous quality engineering platform that transforms product requirements, API specifications, and source code into verified, executable test suites. Rather than acting as a single-pass prompt wrapper, CodeBrain coordinates specialized AI agents through an **Actor-Critic reflection loop**, executes generated HTTP/REST assertions asynchronously, and syncs converged test suites directly to enterprise Test Management Systems.

## Fetch-a-thon 3: CodeBrain Release Guardian

**CodeBrain Release Guardian** is the hackathon submission entry point. It makes the existing Actor–Critic pipeline usable from ASI:One through the Fetch `AgentChatProtocol` 0.3.0 rather than treating the website as the primary demo.

```
ASI:One chat → requirement card → ASI:One Actor–Critic QA plan
         → review card → explicit approval → configured repository pytest run → QA evidence
```

The agent is intentionally conservative:

- It uses `ASI1_API_KEY` for the required ASI:One reasoning step. ACP transport itself does **not** require a model key.
- It returns standards-based interactive cards and acknowledges incoming ACP chat messages.
- It never deploys, writes to a target, uses a secret submitted in chat, or accepts an arbitrary repository path or command.
- Its optional action runs a constrained `python -m pytest` command only in a trusted local Git repository configured by the operator. It is offered only after the user approves the review card and its subprocess receives no API keys or Django secrets.
- A quality score is explicitly presented as a QA signal, never as an automatic release decision.

### Publish checklist (account-bound)

The code is ready for these steps, which require your own Fetch/ASI account and must be performed after deployment:

1. Create an Agentverse account and register the running agent's printed `agent1...` address.
2. Set a public Agentverse profile name, description, and the repo URL.
3. Open an ASI:One shared chat, discover the agent, and complete the requirement → review → approval flow there.
4. Replace the placeholders below with the actual URLs before submission.

| Submission item | Value |
|---|---|
| Agentverse profile | `PUBLISH: add the public Agentverse profile URL` |
| Agent address | `agent1q2j6crzl0hvhq8vc3unxqr2t96jeytsqwyzjaw8hzqxppkcvc95nun37g6k` |
| Direct ACP endpoint | `https://f3bd-103-207-175-132.ngrok-free.app/submit` (temporary ngrok endpoint; re-run deployment preflight before submitting) |
| ASI:One demo chat | `PUBLISH: add the shared ASI:One chat URL` |
| Demo video | `PUBLISH: add the public video URL` |

### Run the Fetch agent locally

Use Python **3.10–3.13** for the uAgents runtime. Copy the safe template, add only your own private values, configure the repository to verify, then run the agent:

```bash
cp .env.example .env
# Set DJANGO_SECRET_KEY, FETCH_AGENT_SEED, ASI1_API_KEY, and an absolute
# RELEASE_GUARDIAN_REPO_PATH in .env.
# ASI1_REQUEST_TIMEOUT defaults to 60 seconds per model request.
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-agent.txt
python -m agents.release_guardian.preflight
python -m agents.release_guardian.agent
```

The command prints the address needed in Agentverse. The agent's detailed behavior and safety boundary are in [agents/release_guardian/README.md](agents/release_guardian/README.md).

### Optional: register a deployed public agent through the Agentverse v2 API

Use this opt-in path only after deploying the agent behind a public HTTPS reverse proxy that forwards `/submit` to
`FETCH_AGENT_PORT`. Do **not** use the Agentverse Inspector URL or `localhost` as the endpoint.

```bash
# In .env — never commit these values.
AGENTVERSE_V2_REGISTRATION_ENABLED=true
AGENTVERSE_API_KEY=your-agentverse-api-key
AGENTVERSE_PUBLIC_ENDPOINT=https://release-guardian.example.com/submit
```

The registration uses the existing `FETCH_AGENT_SEED`, so it preserves the same `agent1...`
identity. On successful startup it publishes the public profile, chat protocol, README, and
starter prompts through Agentverse's v2 API; the runtime also receives ACP directly on that exact public URL. If Agentverse is temporarily unavailable, the agent still starts and logs a generic registration warning without exposing credentials.

---

```
[PRD (.docx/.md/.txt)] ──> [PRD Analyzer] ──> [Test Case Generator] ◄──┐ Actor-Critic
                                                        │              │ Reflection Loop
                                                        ▼              │ (Monotonic Guard)
[OpenAPI / Postman]    ──> [Iface Generator]  [Test Case Reviewer]  ───┘
                                  │                     │
                                  ▼                     ▼
                     [Async HTTPX API Runner]  [Jira | TestRail | XMind | JUnit | XLSX]
                     [Pytest & Postman Export]
```

---

## Key Capabilities

| Pillar | Capabilities |
|---|---|
| **Autonomous Actor-Critic Pipeline** | Iterative `Generator ⇄ Reviewer` feedback loop (`/pipeline/`) with configurable quality thresholds and monotonic regression safeguards that preserve the highest-scoring suite across passes. |
| **Closed-Loop API Test Runner** | Asynchronous `httpx` runner (`APITestRunner`) evaluating status codes, dot-paths, `jsonpath-ng` queries, and regexes with TLS verification and SSRF / DNS-rebinding IP pinning. |
| **Executable Code & Spec Export** | One-click export of API suites to standalone **Pytest (`httpx`)** scripts and **Postman Collection v2.1** JSON, plus manual suites to **Jira Cloud**, **TestRail**, **XMind (`.xmind`)**, **Excel (`.xlsx`)**, and **JUnit XML**. |
| **Zero-Docker Hybrid RAG** | Embedded SQLite/Chroma vector store (`PersistentSQLiteVectorStore`) paired with pure-Python **Okapi BM25 + Dense Vector Reciprocal Rank Fusion (`HybridRetriever`)**; optional Milvus cluster mode. |
| **Spec & Multi-Format Ingestion** | Native ingestion of `.docx`, `.md`, and `.txt` PRDs, plus **OpenAPI 3.x / Swagger 2.0** (with circular `$ref` protection) and **Postman Collections**. |
| **Universal LLM Factory** | Runtime model switching across **DeepSeek**, **Qwen**, **OpenAI** (`gpt-4o-mini`), **Ollama** (local), **Groq**, and custom OpenAI-compatible gateways (`vLLM`, `LiteLLM`). |

---

## Agent & Workflow Roster

| Module | Route | Responsibility |
|---|---|---|
| **Auto-Pilot Pipeline** | `/pipeline/` | End-to-end Actor-Critic generation, review, iterative refinement, and TMS export. |
| **Test Case Generator** | `/test_case_generator/` | Synthesizes Pydantic-validated manual test suites using Equivalence, Boundary, Decision Table, and Orthogonal Array methods. |
| **Test Case Reviewer** | `/test_case_reviewer/` | Audits test cases on completeness, coverage, redundancy, and feasibility rubrics; exports `.xlsx` workbooks. |
| **PRD Analyzer** | `/prd_analyzer/` | Decomposes `.docx`, `.md`, `.txt`, or pasted specifications into functional modules, test point matrices, and risk catalogs. |
| **Interface Case Generator** | `/iface_case_generator/` | Generates positive/boundary/negative API assertions from specs, runs them live via `APITestRunner`, and exports Pytest/Postman artifacts. |
| **Java Code Analyzer** | `/java_code_analyzer/` | Inspects Java methods, branching complexity, and exception paths to produce grey-box QA verification checklists. |

---

## Quick Start

### 1. Install Dependencies & Migrate

CodeBrain runs out-of-the-box with local **SQLite** and **embedded vector storage** (no Docker required):

```bash
python3.12 -m venv .venv
source .venv/bin/activate        # Linux / macOS
.\.venv\Scripts\Activate.ps1     # Windows PowerShell

pip install -r requirements.txt
cp .env.example .env
# Set DJANGO_SECRET_KEY and set DJANGO_DEBUG=true only for local development.
python manage.py migrate
```

MySQL is optional. Only when `USE_MYSQL=true` or `MYSQL_HOST` is configured, install its
driver separately with `pip install -r requirements-mysql.txt`. On macOS, install the MySQL
client development tools (for example, `brew install pkg-config mysql-client`) before that step.

### 2. Configure LLM Keys

Set the environment variables for any provider(s) you plan to use:

```bash
export DEEPSEEK_API_KEY="your-deepseek-key"
export QWEN_API_KEY="your-qwen-key"
export OPENAI_API_KEY="your-openai-key"
export GROQ_API_KEY="your-groq-key"
export OLLAMA_BASE_URL="http://localhost:11434/v1"
```

### 3. Launch the Platform

```bash
python manage.py runserver 127.0.0.1:8000
```

- **Main Dashboard**: `http://127.0.0.1:8000/`
- **Auto-Pilot Pipeline**: `http://127.0.0.1:8000/pipeline/`

*(Optional)* To run the interactive React + Vite showcase in `frontend/`:

```bash
cd frontend && npm install && npm run dev
```

### 4. Headless CI/CD CLI Runner

Run API contract suites in CI/CD pipelines with JUnit XML reporting and non-zero failure exit codes:

```bash
python manage.py run_test_suite --spec-file path/to/suite.json \
  --base-url https://api.example.com \
  --output-junit reports/junit.xml \
  --output-pytest reports/generated_tests.py
```

---

## Testing

Install the development test dependencies and run the complete verification suite:

```bash
pip install -r requirements-dev.txt
pytest -q
```

---

## Repository Layout

```
CodeBrain/
├── apps/
│   ├── ai_agents/                  # Specialized AI agents & Actor-Critic orchestrator
│   │   ├── common/                 # ActorCriticReflectionEngine (orchestrator.py)
│   │   ├── test_case_generator/    # Generator agent & Pydantic v2 schemas
│   │   ├── test_case_reviewer/     # Multi-criteria Reviewer agent & .xlsx exporter
│   │   ├── prd_analyzer/           # Multi-format (.docx/.md/.txt) PRD decomposer
│   │   ├── iface_case_generator/   # API generator, async HTTPX runner, Pytest/Postman exporters
│   │   └── java_code_analyzer/     # Java AST & source code analyzer
│   ├── core/                       # Core models, /pipeline/ views, TMS exporters, CLI runner
│   │   ├── exporters/              # Jira, TestRail, XMind (.xmind), & JUnit XML exporters
│   │   └── management/commands/    # Headless CI/CD command (run_test_suite.py)
│   ├── knowledge/                  # Embedded SQLite/Chroma store, BM25+Vector RRF, OpenAPI/Postman parsers
│   ├── llm/                        # Universal LLMServiceFactory & callback telemetry
│   └── utils/                      # SSE event bus, ProgressRegistry, TaskContext
├── config/                         # Django settings & URL routing
├── frontend/                       # React 18 + TypeScript + Vite interactive showcase (Vercel-ready)
├── static/ & templates/            # Web UI assets and Bootstrap 5 templates
└── tests/                          # Pytest suites (test_phase1.py .. test_phase4.py & unit tests)
```

---

## Using CodeBrain in Your Project

CodeBrain exposes a REST API. Once it's running locally, any external project can call it over HTTP — no SDK, no special setup required.

### Step 1 — Start CodeBrain

```bash
cd path/to/CodeBrain
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS

python manage.py runserver 8000
```

Leave this terminal running. CodeBrain is now available at `http://localhost:8000`.

---

### Step 2 — Call it from your project

Inside **your own project folder**, create a file (e.g. `generate_tests.py`) and paste:

```python
import requests
import json

# Describe the feature you want test cases for
requirements = """
User registration:
- User enters name, email, and password
- Email must be unique
- Password must be at least 8 characters
- On success, send a welcome email
- On duplicate email, show an error message
"""

# Send to CodeBrain
response = requests.post("http://localhost:8000/pipeline/run/", json={
    "requirements": requirements,
    "llm_provider": "deepseek",   # or "openai", "groq", "ollama"
    "min_score": 85.0,            # retry until test quality hits this score
    "max_iterations": 2,          # max refinement rounds
    "case_count": 10              # number of test cases to generate
})

data = response.json()

print(f"Score: {data['final_score']}")
print(f"Converged: {data['converged']}")

# Print each generated test case
for case in data["final_cases"]:
    print(f"\n[{case['priority']}] {case['title']}")
    print(f"  Steps: {case['test_steps']}")
    print(f"  Expected: {case['expected_results']}")

# Save to a file in your project
with open("test_cases.json", "w") as f:
    json.dump(data["final_cases"], f, indent=2)

print("\nSaved to test_cases.json")
```

Run it:

```bash
pip install requests   # only needed once
python generate_tests.py
```

You'll get a `test_cases.json` file in your project folder with all generated test cases.

---

### Step 3 (Optional) — Push directly to Jira

If you use Jira, CodeBrain can push the test cases straight to your board:

```python
requests.post("http://localhost:8000/pipeline/export/", json={
    "target": "jira",
    "project_key": "YOUR-PROJECT-KEY",   # e.g. "MAT" for a project called Matiks
    "test_cases": data["final_cases"]
})
```

Make sure `JIRA_URL`, `JIRA_EMAIL`, and `JIRA_API_TOKEN` are set in CodeBrain's `.env` before running.

---

### Available API Endpoints

| Endpoint | What it does |
|---|---|
| `POST /pipeline/run/` | Full Actor-Critic loop — generates + reviews + refines test cases |
| `POST /test_case_generator/generate/` | Generate test cases only (no review loop) |
| `POST /test_case_reviewer/review/` | Review and score an existing test suite |
| `POST /prd_analyzer/analyze/` | Break down a PRD document into test points |
| `POST /iface_case_generator/generate/` | Generate API contract tests from OpenAPI / Postman spec |
| `POST /iface_case_generator/execute/` | Run generated API tests live against a real server |
| `POST /pipeline/export/` | Push a test suite to Jira, TestRail, XMind, or JUnit XML |

---

### Supported LLM Providers

| `llm_provider` value | Required environment variable |
|---|---|
| `asi1` | `ASI1_API_KEY` |
| `deepseek` | `DEEPSEEK_API_KEY` |
| `qwen` | `QWEN_API_KEY` |
| `openai` | `OPENAI_API_KEY` |
| `groq` | `GROQ_API_KEY` |
| `ollama` | none — runs locally |

---

## Authors & Contributors

- **Harshit Sharma** — [@harshitthek](https://github.com/harshitthek)
- **Pernav Jain** — [@here-2007](https://github.com/here-2007)
- **Mridul Jain** — [@Mridulxjain](https://github.com/Mridulxjain)

---

## License

Released under the [Apache License 2.0](LICENSE).
