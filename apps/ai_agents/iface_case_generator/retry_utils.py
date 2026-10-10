"""
Retry utilities module.
Provides automatic retry mechanism upon parsing failures.
"""
from typing import List, Callable
from pydantic import ValidationError
import json


def generate_with_retry(
    call_llm: Callable[[], str],
    parse_cases: Callable[[str], List],
    on_retry: Callable[[int], None],
    max_retries: int = 2
) -> List:
    """
    Generation and parsing workflow with retries.
    
    Args:
        call_llm: Function executing an LLM request returning raw text
        parse_cases: Function parsing text into cases
        on_retry: Callback function invoked on failure
        max_retries: Maximum number of retries
        
    Returns:
        List: Parsed list of structured objects
        
    Raises:
        ValidationError: Schema validation error
        json.JSONDecodeError: JSON formatting error
    """
    last_err = None
    
    for attempt in range(max_retries + 1):
        try:
            raw = call_llm()
            return parse_cases(raw)
        except (ValidationError, json.JSONDecodeError, ValueError) as e:
            last_err = e
            if attempt == max_retries:
                raise e
            on_retry(attempt)
    
    raise last_err
