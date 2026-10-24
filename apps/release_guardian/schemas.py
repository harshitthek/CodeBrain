"""Validated, serialisable boundary models for the Release Guardian workflow."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class TestCaseSummary(BaseModel):
    title: str
    steps: list[str] = Field(min_length=1)
    expected_results: list[str] = Field(min_length=1)
    priority: str = "P1"

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Test case title must not be empty")
        return cleaned


class QAPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    requirements: str
    test_cases: list[TestCaseSummary] = Field(min_length=1)
    quality_signal: float = Field(ge=0, le=100)
    converged: bool
    iterations_run: int = Field(ge=1, le=2)
    target_id: str | None = None
    target_label: str | None = None
    reviewer_notes: list[str] = Field(default_factory=list)


class ExecutionReport(BaseModel):
    target_id: str
    target_label: str
    total: int = Field(ge=0)
    passed: int = Field(ge=0)
    failed: int = Field(ge=0)
    pass_rate: float = Field(ge=0, le=100)
    total_duration_ms: float = Field(ge=0)
    results: list[dict[str, Any]] = Field(default_factory=list)
