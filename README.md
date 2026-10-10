# CodeBrain

Intelligent automated testing platform powered by Large Language Models, focusing on manual and interface test case generation, test case auditing, requirement decomposition, knowledge retrieval, and Java source code analysis.

---

## Architecture and Documentation

Detailed technical documentation for specific subsystems:

- [AGENTS.md](file:///e:/projects/CodeBrain/AGENTS.md): Full breakdown of all 5 specialized AI agents, prompt schemas, and the guide to registering new agents.
- [MEMORY.md](file:///e:/projects/CodeBrain/MEMORY.md): Knowledge base subsystem, vector database schema, embedding pipelines (BGE-M3 vs Aliyun), and RAG context augmentation.
- [ARCHITECTURE.md](file:///e:/projects/CodeBrain/ARCHITECTURE.md): Multi-tier system architecture, dynamic LLM factory, and Server-Sent Events (SSE) streaming engine.

---

## Core Capabilities

- **Multi-Agent Collaboration**: Specialized agents for test case generation, test case auditing, PRD requirement breakdown, interface contract assertions, and Java static code analysis.
- **Dynamic Model Switching**: Runtime model selection (DeepSeek, Qwen, and custom OpenAI-compatible providers) per agent directly from the web interface.
- **Real-Time Event Streaming**: Token-level logs, status transitions, and progress percentages streamed over Server-Sent Events (SSE).
- **RAG Knowledge Base**: Semantic search and retrieval over testing assets (PRDs, technical specs, past defects) backed by Milvus and embedding models.
- **Zero-Dependency Local Execution**: Auto-detecting SQLite database for immediate development without requiring Docker or external database services.

---

## Functional Agent Roster

| Agent | Entry Route | Description |
|---|---|---|
| **Test Case Generator** | `/test_case_generator/` | Generates structured test case suites from requirements with configurable design methods and test types. |
| **Test Case Reviewer** | `/review/` | Evaluates test cases across completeness, coverage, redundancy, and feasibility rubrics. |
| **PRD Analyzer** | `/prd_analyzer/` | Decomposes product requirements into functional points and edge-case verification matrices. |
| **Interface Case Generator** | `/iface_case_generator/` | Synthesizes API contract validations, JSONPath assertions, and boundary checks from endpoint specs. |
| **Java Code Analyzer** | `/java_code_analyzer/` | Inspects Java method signatures, branching complexity, and unhandled exceptions to generate QA checklists. |

---

## Technology Stack

- **Backend**: Python 3.11+, Django 5.x, LangChain
- **Database**: SQLite (default local mode) / MySQL 8.x (production mode)
- **Vector Engine**: Milvus 2.4.x (optional, gracefully degraded when offline)
- **Embeddings**: `BAAI/bge-m3` (local) or `text-embedding-v4` (cloud)
- **Frontend**: Django HTML5 templates, Bootstrap 5, EventSource SSE listeners

---

## Quick Start (Local Development)

### 1. Environment Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # On Linux/macOS
.\.venv\Scripts\Activate.ps1    # On Windows PowerShell

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Migration

CodeBrain defaults to a local SQLite database (`db.sqlite3`) with zero external service requirements:

```bash
python manage.py migrate
```

To connect to MySQL instead, set `USE_MYSQL=true` and specify database credentials via environment variables:
```bash
export USE_MYSQL=true
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DB=code_brain_db
```

### 3. Configure LLM Credentials (Optional)

Export API keys for the providers you intend to use:

```bash
export DEEPSEEK_API_KEY="your-deepseek-key"
export QWEN_API_KEY="your-qwen-key"
```

*(On Windows PowerShell, use `$env:DEEPSEEK_API_KEY="your-key"`)*

### 4. Start Server

```bash
python manage.py runserver 127.0.0.1:8000
```

Access the dashboard at `http://127.0.0.1:8000/`.

---

## Test Suite Execution

Run the regression test suite using `pytest`:

```bash
pytest -v
```

All 24 test suites execute against in-memory models and mock LLM callbacks without requiring network access or active API keys.

---

## Project Structure

```
CodeBrain/
├── apps/
│   ├── ai_agents/              # Agent implementations
│   │   ├── test_case_generator/
│   │   ├── test_case_reviewer/
│   │   ├── prd_analyzer/
│   │   ├── iface_case_generator/
│   │   └── java_code_analyzer/
│   ├── core/                   # Core models (TestCase, TestCaseReview), dashboard, SSE streaming
│   ├── knowledge/              # Vector database helpers, chunking, and embedding clients
│   ├── llm/                    # Dynamic LLM factory, callbacks, and provider adapters
│   └── utils/                  # SSE bus, progress registry, and logging managers
├── config/                     # Django project settings and routing
├── static/                     # CSS stylesheets and client JavaScript
├── templates/                  # Base and application HTML templates
├── tests/                      # Pytest unit and integration test suites
├── videos/                     # Demo recordings
├── AGENTS.md                   # Detailed agent specifications and developer guide
├── MEMORY.md                   # Knowledge base and vector retrieval architecture
├── ARCHITECTURE.md             # System design and event-streaming flow
├── manage.py
├── pytest.ini
└── requirements.txt
```

---

## License

This project is licensed under the terms of the MIT License. See [LICENSE](file:///e:/projects/CodeBrain/LICENSE) for details.
