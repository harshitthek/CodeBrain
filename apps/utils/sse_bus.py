"""
SSE Log Bus

Provides task log queue management and publishing, supporting SSE stream transmissions.
Each task maintains an independent queue and sequence number, implementing a producer-consumer pattern.

Global variables:
- _task_bus: Task queue dictionary {task_id: (queue, seq)}
- _bus_lock: Thread-safe lock
"""

import time
from typing import Dict, Tuple, Any
from queue import Queue, Empty
from threading import Lock
from .progress_schema import SSELogEntry, LogLevel

# In-memory task log bus: one queue and incrementing sequence number per task_id (sync queue)
_task_bus: Dict[str, Tuple[Queue, int]] = {}
_bus_lock = Lock()


def get_queue(task_id: str) -> Tuple[Queue, int]:
    """Get task queue and sequence number, create new if not existing"""
    with _bus_lock:
        if task_id in _task_bus:
            return _task_bus[task_id]
        q: Queue = Queue(maxsize=1000)
        _task_bus[task_id] = (q, 0)
        return _task_bus[task_id]


def publish_log(task_id: str, level: str, msg: str, name: str = "", thread: str = "", task_type: str = "generation", module: str = "") -> None:
    """Publish log to task queue with backpressure control (drop oldest if full)"""
    q, seq = get_queue(task_id)
    seq += 1
    # Update seq
    with _bus_lock:
        _task_bus[task_id] = (q, seq)
    # Use Pydantic model to create log entry
    try:
        # Validate log level
        log_level = LogLevel(level) if level in [e.value for e in LogLevel] else LogLevel.INFO
    except ValueError:
        log_level = LogLevel.INFO
    
    # Normalize task type
    try:
        tt = SSELogEntry.TaskType(task_type)
    except Exception:
        tt = SSELogEntry.TaskType.GENERATION

    item = SSELogEntry(
        seq=seq,
        ts=time.time(),
        task_id=task_id,
        level=log_level,
        name=name,
        thread=thread,
        msg=msg,
        task_type=tt,
        module=module or name,
    )
    # Backpressure: drop oldest if full
    if q.full():
        try:
            q.get_nowait()  # Remove and return oldest element at queue head
        except Empty:
            pass
    try:
        q.put_nowait(item)
    except Exception:
        # Ignore put failure under race condition when queue is full
        pass


