# Project: DTU ROVC 2026 Specification & AI Tutorial QA Framework

## Architecture
- **Specification Under Test**: `NAT-001-ROVC.pdf` (DTU ROV Challenge 2026, 20m x 10m arena, depth 0.6m - 1.8m).
- **Notebooks Under Test**: `soup-python-repair-tutorial.ipynb`, `bug-whisper-python.ipynb`, `adapter-model-combine.ipynb` in `Tutorial/` (or archived in `docs/tutorial_qa/notebooks/`).
- **Quality Engineering Engine**: CodeBrain (`apps/ai_agents/common/orchestrator.py`, `apps/ai_agents/prd_analyzer/`, `apps/ai_agents/test_case_generator/`, `apps/ai_agents/test_case_reviewer/`, `apps/core/exporters/`).
- **Data Flow**:
  1. Spec & Requirements Analysis: `PrdAnalyserAgent` extracts functional modules and test point matrix from `NAT-001-ROVC.pdf`.
  2. Bounded Reflection Loop: `ActorCriticReflectionEngine` (`TestCaseGeneratorAgent` ⇄ `TestCaseReviewerAgent`) generates and evaluates test cases until rubric score >= 85.0 with monotonic regression safeguard.
  3. Notebook AST & Pipeline Verification: Automated static AST parser, dependency checker, ChatML budget auditor, and adapter merging exception verifier.
  4. Enterprise Exporters: Converged test suite exported to JUnit XML, XMind / Markdown mind-map, Excel `.xlsx` (with injection sanitization), and JSON.
  5. Consolidated QA Deliverables: Comprehensive `qa_report.md` in `Tutorial/` (and archived in `docs/tutorial_qa/`).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F01 | Submerged Gate Navigation (Task 1) | 1.0m gate clearance, 0.6m-1.8m submerged depth, contact-free passage, max 3 attempts | M1 | Survey (NAT-001-ROVC) |
| F02 | Vision Target Touch (Task 2) | Low-visibility/unlit pool, onboard illumination, camera target detection, non-destructive touch | M1 | Survey (NAT-001-ROVC) |
| F03 | Maze Traversal (Task 3) | 3-section maze (straight, obstacles, 1.5m high walls), path traversal, dead-end exit, timing | M1 | Survey (NAT-001-ROVC) |
| F04 | Weight Constraint (Physical) | Vehicle weight <= 35.0 kg (strict disqualification if >35.0 kg), lightweight bonus (<20.0 kg) | M1 | Survey (NAT-001-ROVC) |
| F05 | External Kill Switch (Safety) | Hardwired exterior emergency stop disconnecting all actuators, accessible in <3 sec | M1 | Survey (NAT-001-ROVC) |
| F06 | Electrical Fusing & Protection | Branch fusing on 230V/50Hz supply, DC motor rails, reverse polarity & short circuit protection | M1 | Survey (NAT-001-ROVC) |
| F07 | Footprint Bonus Envelope | Dimensions L < 75cm, B < 65.01cm, H < 60.01cm verified for bonus scoring | M1 | Survey (NAT-001-ROVC) |
| F08 | Pneumatics & Lasers (Safety) | Gas pressure capped at <= 6.0 bar with relief valve; laser safety Class 2 or lower | M1 | Survey (NAT-001-ROVC) |
| F09 | Tether & Comms Management | ~50m umbilical handling, strain relief, tether snag recovery, surface telemetry display | M1 | Survey (NAT-001-ROVC) |
| F10 | Category I: School User Story | Teleoperated flight, basic sensor telemetry, safety switch verification, mentor governance | M1 | Survey (NAT-001-ROVC) |
| F11 | Category II: College User Story | Technical Design Report, CAD/math models, ROS nodes, indigenous thruster/hull bonuses | M1 | Survey (NAT-001-ROVC) |
| F12 | Category III: Industry User Story | Industrial reliability, defense/commercial transferability, advanced autonomous navigation | M1 | Survey (NAT-001-ROVC) |
| F13 | Gate Boundary & Wall Clearance | 1.0m gate passage tolerance, boundary clearance testing, boundary depth 0.6m & 1.8m | M1 | Survey (NAT-001-ROVC) |
| F14 | Task Boundary & Penalty Checks | Maze collision deduction (<=5 pts per contact), 3-attempt gate limit, time-out penalties | M1 | Survey (NAT-001-ROVC) |
| F15 | Overweight & Disqualification | Vehicle mass > 35.0kg boundary rejection, leak detection DQ, safety non-compliance | M1 | Survey (NAT-001-ROVC) |
| F16 | Actor-Critic Rubric Convergence | Quality rubric score >= 85.0 across Completeness, Coverage, Redundancy, Feasibility | M1 | Survey (CodeBrain) |
| F17 | Notebook Python AST Syntax | 100% clean AST parsing across all 54 code cells in all 3 tutorial notebooks | M2 | Survey (Notebooks) |
| F18 | Dependency & Environment Audit | Python 3.10-3.12 vs 3.13 checks, torchao uninstall sanitization, missing kagglehub detection | M2 | Survey (Notebooks) |
| F19 | Cell Execution DAG Order | Linear execution flow validation, zero undeclared global variables or broken forward references | M2 | Survey (Notebooks) |
| F20 | ChatML & Context Budgets | ChatML template compliance, response loss masking, strict <512 / <768 token budgets | M2 | Survey (Notebooks) |
| F21 | Model Merging & Adapter Save | FP16 unquantized merging vs 4-bit BnB dequant/requant, PEFT rounding, exception handling | M2 | Survey (Notebooks) |
| F22 | Structured JSON Test Suite Export | Pydantic v2 validated JSON export of converged test suite | M3 | Survey (CodeBrain) |
| F23 | Excel Workbook (.xlsx) Export | Stylized Excel export with formula injection sanitization (`_sanitize_excel_text`) | M3 | Survey (CodeBrain) |
| F24 | JUnit XML & Mind-Map Exports | Standard JUnit XML test suite report & XMind/Markmap compatible mindmap export | M3 | Survey (CodeBrain) |
| F25 | Comprehensive QA Report | Detailed `qa_report.md` in `Tutorial/` (and `docs/tutorial_qa/`) with audit results & metrics | M4 | Survey (Deliverables) |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | ROVC 2026 Test Suite Generation & Actor-Critic Convergence | Features F01-F16: Task 1-3, Safety, Tiers, Boundary & Exception cases via CodeBrain ActorCritic reflection (Score >= 85.0) | None | DONE |
| M2 | Notebooks Code Integrity & Pipeline Verification | Features F17-F21: AST verification, dependency audit, DAG flow, ChatML budgets, adapter merging | None | DONE |
| M3 | Multi-Format Test Suite Exporter Integration | Features F22-F24: Export converged suite to JSON, Excel (.xlsx), JUnit XML, XMind/Markdown | M1 | DONE |
| M4 | Consolidated QA Deliverables & Final QA Report | Feature F25: Final `qa_report.md` and complete QA package in `Tutorial/` and `docs/tutorial_qa/` | M1, M2, M3 | DONE |

## Interface Contracts
### CodeBrain Agent Schema Contract
- `TestCaseGeneratorAgent`:
  - Inputs: `requirements` (str), `case_count` (int), `design_methods` (list[str]), `test_types` (list[str]).
  - Output: list of `GeneratedTestCaseItem` objects conforming to Pydantic schema:
    - `case_id`: str (e.g. `ROVC-TC-001`)
    - `name`: str
    - `description`: str
    - `preconditions`: str or list[str]
    - `test_steps`: str or list[str]
    - `expected_results`: str or list[str]
    - `priority`: "High" | "Medium" | "Low"
    - `case_type`: "Functional" | "Boundary" | "Exception" | "UI" | "Performance" | "Security"
- `TestCaseReviewerAgent`:
  - Inputs: list of test case dicts / `MockCaseObj`.
  - Output: Rubric dictionary `{score: float, strengths: list[str], weaknesses: list[str], suggestions: list[str], missing_scenarios: list[str], recommendation: str, comments: str}`.
  - Scale: Score 1-10 normalized to 10-100 scale; threshold >= 85.0.

## Code Layout
- Target workspace: `Tutorial/` (or `docs/tutorial_qa/`)
  - `qa_report.md`: Consolidated QA report.
  - `rovc_testcases.json`: Structured JSON test case export.
  - `rovc_testcases.xlsx`: Openpyxl stylized Excel workbook.
  - `junit_testcases.xml`: Standard JUnit XML test suite.
  - `testcases_mindmap.md`: Markmap-compatible Markdown mind-map.
- Agent metadata workspace: `.agents/teamwork/`
  - `orchestrator_1/`: Orchestrator planning and progress tracking.
  - `worker_m1/`: Milestone 1 Actor-Critic generation.
  - `worker_m2/`: Milestone 2 Notebook verification script & outputs.
  - `worker_m3/`: Milestone 3 Multi-format exporters execution.
  - `reviewer_1/`, `reviewer_2/`: Independent verification & review.
  - `challenger_1/`, `challenger_2/`: Adversarial verification.
  - `auditor_1/`: Forensic integrity audit.
