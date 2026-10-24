"""Unit and integration tests for DTU ROVC 2026 Test Suite and Actor-Critic Convergence."""

import json
from pathlib import Path
import pytest

from apps.ai_agents.test_case_generator.schemas import GeneratedTestCaseItem
from apps.ai_agents.test_case_generator.rovc_pipeline_runner import run_rovc_actor_critic_pipeline


SUITE_PATH = (
    Path("/Users/pernavjain/Documents/Tutorial/rovc_testcases.json")
    if Path("/Users/pernavjain/Documents/Tutorial/rovc_testcases.json").exists()
    else Path("/Users/pernavjain/Documents/CodeBrain/.agents/teamwork/worker_m1/converged_suite.json")
)
RUBRIC_PATH = (
    Path("/Users/pernavjain/Documents/Tutorial/rovc_rubric.json")
    if Path("/Users/pernavjain/Documents/Tutorial/rovc_rubric.json").exists()
    else Path("/Users/pernavjain/Documents/CodeBrain/.agents/teamwork/worker_m1/rubric_evaluation.json")
)


def test_rovc_suite_files_exist():
    """Verify generated artifacts exist at required paths."""
    assert SUITE_PATH.exists(), f"Missing converged suite at {SUITE_PATH}"
    assert RUBRIC_PATH.exists(), f"Missing rubric evaluation log at {RUBRIC_PATH}"


def test_rovc_suite_pydantic_schema_conformance():
    """Verify all 40 test cases conform strictly to GeneratedTestCaseItem Pydantic schema."""
    with open(SUITE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    test_cases = data.get("test_cases", [])
    assert len(test_cases) == 40, f"Expected 40 test cases, got {len(test_cases)}"

    for tc in test_cases:
        model = GeneratedTestCaseItem.model_validate(tc)
        dump = model.model_dump()

        # Check required fields
        assert dump["case_id"] is not None and dump["case_id"].startswith("ROVC-TC-")
        assert dump["name"] is not None and len(dump["name"]) > 5
        assert len(dump["description"]) > 10
        assert len(dump["preconditions"]) > 0
        assert isinstance(dump["test_steps"], list) and len(dump["test_steps"]) >= 2
        assert isinstance(dump["expected_results"], list) and len(dump["expected_results"]) >= 1
        assert dump["priority"] in ["High", "Medium", "Low", "P0", "P1", "P2", "P3"]
        assert dump["case_type"] in ["Functional", "Boundary", "Exception", "UI", "Performance", "Security"]


def test_rovc_suite_comprehensive_coverage():
    """Verify comprehensive domain coverage across all competition tasks and constraints."""
    with open(SUITE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    cases = data.get("test_cases", [])
    all_text = " ".join([
        f"{c['case_id']} {c['name']} {c['description']} {' '.join(c['test_steps'])} {' '.join(c['expected_results'])}"
        for c in cases
    ]).lower()

    # Task 1: Qualification Gate Navigation
    gate_cases = [c for c in cases if "gate" in (c["name"] + c["description"]).lower()]
    assert len(gate_cases) >= 4, "Task 1 Gate navigation coverage insufficient"
    assert any(c["case_type"] == "Boundary" for c in gate_cases), "Task 1 missing Boundary case"
    assert any(c["case_type"] == "Exception" for c in gate_cases), "Task 1 missing Exception case"
    assert "1.0" in all_text and "attempt" in all_text

    # Task 2: Low-Visibility Vision Target Identification & Touch
    vision_cases = [c for c in cases if any(k in (c["name"] + c["description"]).lower() for k in ["task 2", "vision", "balloon", "touch", "low-visibility"])]
    assert len(vision_cases) >= 4, "Task 2 Vision target coverage insufficient"
    assert any(c["case_type"] == "Boundary" for c in vision_cases), "Task 2 missing Boundary case"
    assert any(c["case_type"] == "Exception" for c in vision_cases), "Task 2 missing Exception case"
    assert any("balloon" in (c["name"] + c["description"]).lower() for c in vision_cases)
    assert any("illumination" in (c["name"] + c["description"]).lower() or "light" in (c["name"] + c["description"]).lower() for c in vision_cases)

    # Task 3: The Maze Walk Submerged Traversal
    maze_cases = [c for c in cases if any(k in (c["name"] + c["description"]).lower() for k in ["task 3", "maze"])]
    assert len(maze_cases) >= 6, f"Task 3 Maze traversal coverage insufficient: got {len(maze_cases)}"
    assert any(c["case_type"] == "Boundary" for c in maze_cases), "Task 3 missing Boundary case"
    assert any(c["case_type"] == "Exception" for c in maze_cases), "Task 3 missing Exception case"
    assert "1.5m" in all_text or "1.5 m" in all_text
    assert "deduction" in all_text or "penalty" in all_text

    # Physical & Safety Constraints
    assert any("35.0" in (c["name"] + c["description"]) for c in cases), "Missing 35kg mass limit verification"
    assert any("kill switch" in (c["name"] + c["description"]).lower() for c in cases), "Missing kill switch verification"
    assert any("fuse" in (c["name"] + c["description"]).lower() for c in cases), "Missing electrical fusing verification"
    assert any("footprint" in (c["name"] + c["description"]).lower() or "envelope" in (c["name"] + c["description"]).lower() for c in cases), "Missing footprint envelope verification"
    assert any("6.0 bar" in (c["name"] + c["description"]).lower() or "pneumatic" in (c["name"] + c["description"]).lower() for c in cases), "Missing pneumatic pressure verification"
    assert any("tether" in (c["name"] + c["description"]).lower() for c in cases), "Missing tether umbilical verification"

    # User Story Boundaries
    assert any("category i" in (c["name"] + c["description"]).lower() or "school" in (c["name"] + c["description"]).lower() for c in cases), "Missing Category I School story"
    assert any("category ii" in (c["name"] + c["description"]).lower() or "college" in (c["name"] + c["description"]).lower() for c in cases), "Missing Category II College story"
    assert any("category iii" in (c["name"] + c["description"]).lower() or "industry" in (c["name"] + c["description"]).lower() for c in cases), "Missing Category III Industry story"

    # Boundary and Exception counts
    boundary_cases = [c for c in cases if c["case_type"] == "Boundary"]
    exception_cases = [c for c in cases if c["case_type"] == "Exception"]
    assert len(boundary_cases) >= 10, f"Expected >=10 boundary cases, got {len(boundary_cases)}"
    assert len(exception_cases) >= 10, f"Expected >=10 exception cases, got {len(exception_cases)}"


def test_rovc_actor_critic_telemetry_and_convergence():
    """Verify Actor-Critic reflection converged with score >= 85.0 and recorded 2 iterations."""
    with open(RUBRIC_PATH, "r", encoding="utf-8") as f:
        rubric_data = json.load(f)

    meta = rubric_data["metadata"]
    assert meta["converged"] is True
    assert meta["final_score"] >= 85.0
    assert meta["iterations_executed"] == 2

    history = rubric_data["iteration_history"]
    assert len(history) == 2
    assert history[0]["iteration"] == 1
    assert history[0]["score"] < 85.0, "Iteration 1 should have been below threshold to trigger reflection"
    assert history[0]["critique"]["recommendation"] == "Refine"

    assert history[1]["iteration"] == 2
    assert history[1]["score"] >= 85.0, "Iteration 2 must satisfy threshold"
    assert history[1]["critique"]["recommendation"] == "Pass"
