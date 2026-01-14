"""Chat session and message database models."""

from datetime import datetime
from typing import TYPE_CHECKING
import enum
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.profile import Profile
    from src.models.task import Task


class ChatMessageRole(str, enum.Enum):
    """Role of the message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    STEP = "step"
    ERROR = "error"
    SYSTEM = "system"


class ChatSession(Base, TimestampMixin):
    """A chat conversation session with a device profile."""

    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Session metadata
    initial_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)

    # Aggregated metrics
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timing
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    profile: Mapped["Profile"] = relationship("Profile", back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )
    # Back-reference to task (if session was created by a task execution)
    task: Mapped["Task | None"] = relationship(
        "Task",
        back_populates="chat_session",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<ChatSession {self.id}: {self.status}>"


class ChatMessage(Base):
    """Individual message in a chat session."""

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Message content
    role: Mapped[ChatMessageRole] = mapped_column(
        Enum(ChatMessageRole),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # For step messages
    step_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    action_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    action_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Token tracking (per message)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cumulative_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Screenshot path (stored in filesystem: /app/data/screenshots/{session_id}/)
    screenshot_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<ChatMessage {self.id}: [{self.role.value}]>"
