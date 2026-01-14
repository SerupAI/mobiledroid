"""Task schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """Schema for creating a task."""

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Natural language task description",
        examples=["Open Chrome and search for 'weather'"],
    )
    output_format: str | None = Field(
        default=None,
        max_length=255,
        description="Expected output format (e.g., 'json', 'text', 'screenshot')",
    )
    priority: Literal["low", "normal", "high", "urgent"] = Field(
        default="normal",
        description="Task priority level",
    )
    scheduled_at: datetime | None = Field(
        default=None,
        description="Schedule task for future execution (UTC)",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts on failure",
    )
    queue_immediately: bool = Field(
        default=True,
        description="If true, queue task immediately; if false, create as pending",
    )


class TaskLogResponse(BaseModel):
    """Schema for task log response."""

    id: int
    level: str
    message: str
    action_type: str | None
    action_data: str | None
    screenshot_path: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    """Schema for task response."""

    id: str
    profile_id: str
    prompt: str
    output_format: str | None
    status: str
    result: str | None
    error_message: str | None
    priority: str
    scheduled_at: datetime | None
    max_retries: int
    retry_count: int
    queue_job_id: str | None
    queued_at: datetime | None
    steps_taken: int
    tokens_used: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    chat_session_id: str | None = None  # Link to chat session created during execution
    logs: list[TaskLogResponse] = []

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Schema for task list response."""

    tasks: list[TaskResponse]
    total: int


class QueueStatsResponse(BaseModel):
    """Schema for queue statistics."""

    queued_jobs: int
    task_counts: dict[str, int]
