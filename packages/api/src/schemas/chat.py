"""Chat session and message schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from src.models.chat import ChatMessageRole


class ChatMessageSchema(BaseModel):
    """Schema for a chat message."""
    id: int
    role: ChatMessageRole
    content: str
    step_number: Optional[int] = None
    action_type: Optional[str] = None
    action_reasoning: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cumulative_tokens: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionSchema(BaseModel):
    """Schema for a chat session."""
    id: str
    profile_id: str
    initial_prompt: str
    status: str
    total_tokens: int
    total_input_tokens: int
    total_output_tokens: int
    total_steps: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    messages: List[ChatMessageSchema] = []

    class Config:
        from_attributes = True


class ChatSessionSummarySchema(BaseModel):
    """Summary schema for listing chat sessions (without messages)."""
    id: str
    profile_id: str
    initial_prompt: str
    status: str
    total_tokens: int
    total_steps: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    message_count: int = 0

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Response for chat history endpoint."""
    sessions: List[ChatSessionSummarySchema]
    total_tokens: int
    total_sessions: int


class ChatCostResponse(BaseModel):
    """Response with cost calculation."""
    total_tokens: int
    input_tokens: int
    output_tokens: int
    # Cost in USD (based on Claude pricing)
    estimated_cost_usd: float
    # Breakdown by model if available
    cost_per_1k_input: float = 0.003  # Claude Sonnet pricing
    cost_per_1k_output: float = 0.015
