"""
Task Progress Registry

Provides thread-safe task progress data storage and management, supporting progress tracking during concurrent task execution.

Main features:
- Store and update task progress data (step, percentage, message, etc.)
- Collect and append task execution logs
- Provide progress query and cleanup interfaces
- Support expired task cleanup mechanism

Core characteristics:
- Thread-safe: Uses locks to protect shared data
- Type-safe: Data validation based on Pydantic models
- Log management: Automatically caps log count to prevent memory leaks
- Timestamps: Automatically records last updated timestamp

Usage scenarios:
- Progress tracking for test case generation tasks
- Status monitoring for long-running tasks
- Data source for real-time frontend progress display
"""

import threading
import time
from typing import Dict, Optional
from .progress_schema import ProgressData, ProgressUpdate, TaskStatus

_progress_registry: Dict[str, ProgressData] = {}
_lock = threading.Lock()


def set_progress(task_id: str, data: dict) -> None:
    """Merge task progress data, appending logs to the log list if provided.

    Uses standardized ProgressData model for type validation and data management.
    """
    with _lock:
        # Get current progress data, create new if not present
        current = _progress_registry.get(task_id)
        if current is None:
            current = ProgressData()
        
        # Parse update data
        try:
            update_data = ProgressUpdate(**data)
        except Exception as e:
            # If parsing fails, fall back to raw logic
            current_dict = current.dict()
            current_dict.update(data)
            current_dict['timestamp'] = time.time()
            _progress_registry[task_id] = ProgressData(**current_dict)
            return
        
        # Handle log appending
        if update_data.log is not None:
            if isinstance(update_data.log, list):
                current.logs.extend([str(x) for x in update_data.log])
            else:
                current.logs.append(str(update_data.log))
            # Cap log length
            current.logs = current.logs[-2000:]
        
        # Update other fields
        update_dict = update_data.dict(exclude={'log'}, exclude_none=True)
        for key, value in update_dict.items():
            if hasattr(current, key):
                setattr(current, key, value)
        
        # Automatically update task status
        if current.percentage is not None:
            if current.percentage >= 100:
                current.status = TaskStatus.COMPLETED
            elif current.percentage > 0:
                current.status = TaskStatus.RUNNING
        
        # Update timestamp
        current.timestamp = time.time()
        
        # Save updated data
        _progress_registry[task_id] = current


def get_progress(task_id: str) -> Optional[ProgressData]:
    with _lock:
        return _progress_registry.get(task_id)


def clear_progress(task_id: str) -> None:
    with _lock:
        if task_id in _progress_registry:
            del _progress_registry[task_id]


def cleanup_expired(max_age_seconds: int = 3600) -> None:
    now = time.time()
    expired: Dict[str, ProgressData] = {}
    with _lock:
        for tid, prog in list(_progress_registry.items()):
            if now - prog.timestamp > max_age_seconds:
                expired[tid] = prog
                del _progress_registry[tid]

