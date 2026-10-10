"""
Minimal output parser module for LLM.
Provides parsing functionality from text to MinimalCase list, replacing bare json.loads.
"""
import json
from typing import List
# from pydantic import ValidationError
from langchain_core.output_parsers import PydanticOutputParser
from .iface_test_case_schema import MinimalCase

# Create Pydantic parser
api_test_case_parser = PydanticOutputParser(pydantic_object=MinimalCase)


def clean_json_fence(text: str) -> str:
    """Strip ```json ... ``` code fence from LLM output"""
    s = text.strip()
    if s.startswith('```json'):
        s = s[7:]
    if s.endswith('```'):
        s = s[:-3]
    return s.strip()


def parse_minimal_cases_or_raise(response_text: str) -> List[MinimalCase]:
    """
    Parse LLM response into a list of MinimalCase objects
    
    Args:
        response_text: Raw string output from LLM
        
    Returns:
        List[MinimalCase]: List of parsed structured objects
        
    Raises:
        ValidationError: Field missing or invalid type
        json.JSONDecodeError: Invalid JSON format
    """
    cleaned = clean_json_fence(response_text)
    parsed = json.loads(cleaned)  # Raise JSONDecodeError if JSON is invalid

    # Normalize to list (supports LLM returning single object or array)
    items = parsed if isinstance(parsed, list) else [parsed]
    results: List[MinimalCase] = []
    
    for item in items:
        # Hand over to parser for field/type validation and conversion
        obj = api_test_case_parser.parse(json.dumps(item, ensure_ascii=False))
        results.append(obj)
    
    return results


def get_format_instructions() -> str:
    """
    Get format instruction text to inject into prompt for strict LLM output constraint
    
    Returns:
        str: Format instructions text
    """
    return api_test_case_parser.get_format_instructions()
