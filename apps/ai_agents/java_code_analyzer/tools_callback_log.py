"""
Tool invocation functions and tool callback logging.
"""
import json
import time
from typing import Any, Dict, Optional


def to_log_str(value: Any, *, limit: int = 8000) -> str:
    """Convert arbitrary object to printable log string with length protection."""
    try:
        if value is None:
            s = "null"
        elif isinstance(value, (dict, list, tuple)):
            s = json.dumps(value, ensure_ascii=False)
        else:
            s = str(value)
    except Exception as e:
        s = f"<unprintable:{type(value).__name__}:{e}>"

    if len(s) > limit:
        return s[:limit] + f"...<truncated,len={len(s)}>"
    return s


def invoke_tool(logger, tool, args: Dict[str, Any], *, label: str, limit: int = 8000) -> Any:
    """Unified tool invocation with audit logging."""
    tool_name = getattr(tool, "name", str(tool))
    t0 = time.time()
    logger.info(
        "[JavaCodeAnalyzer][ToolCall] start label=%s tool=%s args=%s",
        label,
        tool_name,
        to_log_str(args, limit=limit),
    )
    try:
        result = tool.invoke(args)
        elapsed_ms = int((time.time() - t0) * 1000)
        logger.info(
            "[JavaCodeAnalyzer][ToolCall] end label=%s tool=%s elapsed_ms=%s result=%s",
            label,
            tool_name,
            elapsed_ms,
            to_log_str(result, limit=limit),
        )
        return result
    except Exception:
        elapsed_ms = int((time.time() - t0) * 1000)
        logger.exception(
            "[JavaCodeAnalyzer][ToolCall] error label=%s tool=%s elapsed_ms=%s args=%s",
            label,
            tool_name,
            elapsed_ms,
            to_log_str(args, limit=limit),
        )
        raise


def log_node_start(logger, name: str, state: Dict[str, Any], *, project_id: Optional[str] = None) -> float:
    """Record LangGraph node start log and return start time."""
    start = time.time()
    try:
        logger.info(
            "[JavaCodeAnalyzer][LangGraph] node_start=%s base=%s new=%s project_id=%s",
            name,
            (state.get("base_commit") or "")[:8],
            (state.get("new_commit") or "")[:8],
            project_id,
        )
    except Exception:
        pass
    return start


def log_node_end(logger, name: str, start: float, **extra) -> None:
    """Record LangGraph node end log with elapsed time."""
    elapsed_ms = int((time.time() - start) * 1000)
    try:
        if extra:
            logger.info(
                "[JavaCodeAnalyzer][LangGraph] node_end=%s elapsed_ms=%s extra=%s",
                name,
                elapsed_ms,
                extra,
            )
        else:
            logger.info(
                "[JavaCodeAnalyzer][LangGraph] node_end=%s elapsed_ms=%s",
                name,
                elapsed_ms,
            )
    except Exception:
        pass
