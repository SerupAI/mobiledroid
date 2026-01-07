"""Task schemas."""

from datetime import datetime

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
    steps_taken: int
    tokens_used: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    logs: list[TaskLogResponse] = []

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Schema for task list response."""

    tasks: list[TaskResponse]
    total: int
