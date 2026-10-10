import json
import re
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator


class GeneratedTestCaseItem(BaseModel):
    """Schema for an individual generated test case."""
    description: str = Field(..., description="Summary of the test scenario")
    preconditions: Optional[str] = Field(default="", description="Setup steps or preconditions")
    test_steps: List[str] = Field(..., description="Sequential actions taken")
    expected_results: List[str] = Field(..., description="Expected verified outcomes")
    case_type: Optional[str] = Field(default="Functional", description="Category of test")
    priority: Optional[str] = Field(default="P2", description="Priority level: P0, P1, P2, P3")

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, v: Any) -> str:
        if not v or not str(v).strip():
            raise ValueError("description must not be empty")
        return str(v).strip()

    @field_validator("preconditions", mode="before")
    @classmethod
    def validate_preconditions(cls, v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, list):
            return "\n".join(str(item).strip() for item in v if str(item).strip())
        return str(v).strip()

    @field_validator("test_steps", mode="before")
    @classmethod
    def validate_test_steps(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            cleaned = [str(step).strip() for step in v if str(step).strip()]
            if not cleaned:
                raise ValueError("test_steps must not be empty")
            return cleaned
        if isinstance(v, str) and v.strip():
            lines = [line.strip() for line in v.split("\n") if line.strip()]
            if not lines:
                raise ValueError("test_steps must not be empty")
            return lines
        raise ValueError("test_steps must not be empty")

    @field_validator("expected_results", mode="before")
    @classmethod
    def validate_expected_results(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            cleaned = [str(item).strip() for item in v if str(item).strip()]
            if not cleaned:
                raise ValueError("expected_results must not be empty")
            return cleaned
        if isinstance(v, str) and v.strip():
            lines = [line.strip() for line in v.split("\n") if line.strip()]
            if not lines:
                raise ValueError("expected_results must not be empty")
            return lines
        raise ValueError("expected_results must not be empty")


def extract_and_parse_test_cases(response_text: str) -> List[Dict[str, Any]]:
    """Robust multi-strategy extractor and validator for LLM-generated test cases."""
    if not response_text or not response_text.strip():
        raise ValueError("Empty LLM response received")

    cleaned_text = response_text.strip()
    raw_json_obj = None

    # Strategy 1: Markdown code fences
    if "```json" in cleaned_text:
        try:
            block = cleaned_text.split("```json")[1].split("```")[0].strip()
            raw_json_obj = json.loads(block)
        except Exception:
            pass

    if raw_json_obj is None and "```" in cleaned_text:
        try:
            block = cleaned_text.split("```")[1].split("```")[0].strip()
            raw_json_obj = json.loads(block)
        except Exception:
            pass

    # Strategy 2: Direct JSON parse
    if raw_json_obj is None:
        try:
            raw_json_obj = json.loads(cleaned_text)
        except Exception:
            pass

    # Strategy 3: Greedy bracket extraction [...]
    if raw_json_obj is None:
        end_idx = cleaned_text.rfind("]")
        if end_idx != -1:
            search_start = 0
            while True:
                start_idx = cleaned_text.find("[", search_start)
                if start_idx == -1 or start_idx >= end_idx:
                    break
                substring = cleaned_text[start_idx : end_idx + 1]
                try:
                    raw_json_obj = json.loads(substring)
                    break
                except Exception:
                    try:
                        import json5  # type: ignore
                        raw_json_obj = json5.loads(substring)
                        break
                    except Exception:
                        fixed = re.sub(r",\s*([\]}])", r"\1", substring)
                        try:
                            raw_json_obj = json.loads(fixed)
                            break
                        except Exception:
                            pass
                search_start = start_idx + 1

    # Strategy 4: Dictionary wrapping (e.g. {"test_cases": [...]})
    if isinstance(raw_json_obj, dict):
        for key in ["test_cases", "cases", "data", "results"]:
            if key in raw_json_obj and isinstance(raw_json_obj[key], list):
                raw_json_obj = raw_json_obj[key]
                break

    if not isinstance(raw_json_obj, list):
        raise ValueError(f"Unable to extract a valid JSON test case list from LLM output:\n{response_text[:300]}")

    validated_cases: List[Dict[str, Any]] = []
    for item in raw_json_obj:
        if isinstance(item, dict):
            try:
                validated_model = GeneratedTestCaseItem.model_validate(item)
                validated_cases.append(validated_model.model_dump())
            except Exception:
                continue

    if not validated_cases:
        raise ValueError("No valid test cases remained after schema validation")

    return validated_cases
