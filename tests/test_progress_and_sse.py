import pytest
import time
from apps.utils.progress_schema import ProgressData, ProgressUpdate, TaskStatus, LogLevel, SSELogEntry
from apps.utils.progress_registry import set_progress, get_progress, clear_progress, cleanup_expired
from apps.utils.sse_bus import publish_log, get_queue
from apps.utils.logger_manager import set_task_context, clear_task_context, task_id_var


def test_progress_schema_and_status():
    """Verify ProgressData defaults and validation"""
    p = ProgressData()
    assert p.status == TaskStatus.PENDING
    assert p.percentage is None
    assert p.logs == []

    # Update with percentage >= 100 sets status to COMPLETED
    set_progress("task-test-1", {"percentage": 100, "message": "All done"})
    data = get_progress("task-test-1")
    assert data is not None
    assert data.status == TaskStatus.COMPLETED
    assert data.message == "All done"

    # Clean up
    clear_progress("task-test-1")
    assert get_progress("task-test-1") is None


def test_progress_registry_log_capping():
    """Verify progress log capping to 2000 entries"""
    task_id = "task-test-logs"
    # Append 2100 logs
    logs_to_add = [f"Log line {i}" for i in range(2100)]
    set_progress(task_id, {"log": logs_to_add})

    data = get_progress(task_id)
    assert len(data.logs) == 2000
    assert data.logs[-1] == "Log line 2099"

    clear_progress(task_id)


def test_sse_bus_publish_and_queue():
    """Verify publish_log puts message on queue with sequence number"""
    task_id = "task-sse-test"
    publish_log(
        task_id=task_id,
        level="INFO",
        msg="Starting test run",
        name="test_runner"
    )

    q, seq = get_queue(task_id)
    assert seq >= 1
    assert not q.empty()

    item = q.get_nowait()
    assert isinstance(item, SSELogEntry)
    assert item.msg == "Starting test run"
    assert item.level == LogLevel.INFO
    assert item.task_id == task_id


def test_task_context_manager():
    """Verify set_task_context and clear_task_context"""
    set_task_context("task-ctx-99")
    assert task_id_var.get() == "task-ctx-99"

    clear_task_context()
    assert task_id_var.get() is None
