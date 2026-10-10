"""
Progress Tracking Data Model Definitions

This module defines Pydantic data models for task progress tracking, supporting:
1. Task progress info (step, message, percentage)
2. Interface processing status (current API, total, completed)
3. File generation info (file path)
4. Real-time log collection (log list)
5. Extension field support

Primary usage:
- Store task progress data in progress_registry.py
- Serialize progress info in SSE stream transmissions
- Return structured progress data in frontend polling APIs
- Provide type safety and data validation

Data flow:
1. Business logic calls set_progress(task_id, ProgressUpdate)
2. progress_registry merges ProgressUpdate into ProgressData
3. SSE/polling API returns ProgressData to frontend
4. Frontend parses and updates UI display
"""

from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field
from enum import Enum
import time


class LogLevel(str, Enum):
    """Log level enum"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TaskStatus(str, Enum):
    """Task status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SSELogEntry(BaseModel):
    """SSE log entry data model"""
    seq: int = Field(ge=1, description="Log sequence number")
    ts: float = Field(ge=0, description="Timestamp")
    task_id: str = Field(min_length=1, description="Task ID")
    level: LogLevel = Field(description="Log level")
    name: str = Field(default="", description="Log source name")
    thread: str = Field(default="", description="Thread name")
    msg: str = Field(description="Log message content")
    # Extension: task type and module name, supporting multi-task parallel categorized display
    class TaskType(str, Enum):
        GENERATION = "generation"
        REVIEW = "review"
        ANALYSIS = "analysis"
        OTHER = "other"

    task_type: TaskType = Field(default=TaskType.GENERATION, description="Task type")
    module: str = Field(default="", description="Business module name")
    
    class Config:
        validate_assignment = True


class ProgressData(BaseModel):
    """Task progress data model"""
    
    # Basic progress information
    step: Optional[int] = Field(None, ge=0, description="Current step number")
    message: Optional[str] = Field(None, description="Current step description")
    percentage: Optional[float] = Field(None, ge=0, le=100, description="Completion percentage (0-100)")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    
    # API / Interface related
    current_api: Optional[str] = Field(None, description="Current interface name being processed")
    total_apis: Optional[int] = Field(None, ge=0, description="Total number of interfaces")
    completed_apis: Optional[int] = Field(None, ge=0, description="Number of completed interfaces")
    
    # File related
    file_path: Optional[str] = Field(None, description="Generated file path")
    
    # Log related
    logs: List[str] = Field(default_factory=list, max_items=2000, description="Log list")
    
    # Timestamps
    timestamp: float = Field(default_factory=time.time, description="Last update timestamp")
    created_at: float = Field(default_factory=time.time, description="Task creation timestamp")
    
    # Other extension fields
    extra: dict = Field(default_factory=dict, description="Other extension data")
    
    class Config:
        populate_by_name = True
        # Optimize serialization performance
        json_encoders = {
            time: lambda v: v,
        }
        # Validate assignment
        validate_assignment = True
        # Allow extra fields
        extra = "allow"


class ProgressUpdate(BaseModel):
    """Progress update data model (used for set_progress function)"""
    
    # Basic progress information
    step: Optional[int] = Field(None, ge=0)
    message: Optional[str] = None
    percentage: Optional[float] = Field(None, ge=0, le=100)
    status: Optional[TaskStatus] = None
    
    # API / Interface related
    current_api: Optional[str] = None
    total_apis: Optional[int] = Field(None, ge=0)
    completed_apis: Optional[int] = Field(None, ge=0)
    
    # File related
    file_path: Optional[str] = None
    
    # Log related (special handling)
    log: Optional[Union[str, List[str]]] = Field(None, description="Log to append")
    
    # Other extension fields
    extra: Optional[dict] = None
    
    class Config:
        # Allow extra fields
        extra = "allow"
