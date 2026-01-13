"""Task database models."""

from datetime import datetime
from typing import TYPE_CHECKING
import enum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.profile import Profile


class TaskStatus(str, enum.Enum):
    """Task execution status."""

    PENDING = "pending"
    SCHEDULED = "scheduled"  # Waiting for scheduled time
    QUEUED = "queued"  # In Redis queue, waiting for worker
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    """Task priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskLogLevel(str, enum.Enum):
    """Task log level."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    ACTION = "action"


class Task(Base, TimestampMixin):
    """AI task to be executed on a device profile."""

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Task definition
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    output_format: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status tracking
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, values_callable=lambda x: [e.value for e in x]),
        default=TaskStatus.PENDING,
        nullable=False,
    )
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Priority and scheduling
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, values_callable=lambda x: [e.value for e in x]),
        default=TaskPriority.NORMAL,
        nullable=False,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Queue tracking
    queue_job_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    queued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Metrics
    steps_taken: Mapped[int] = mapped_column(default=0, nullable=False)
    tokens_used: Mapped[int] = mapped_column(default=0, nullable=False)

    # Relationships
    profile: Mapped["Profile"] = relationship("Profile", back_populates="tasks")
    logs: Mapped[list["TaskLog"]] = relationship(
        "TaskLog",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskLog.created_at",
    )

    def __repr__(self) -> str:
        return f"<Task {self.id}: {self.status.value}>"


class TaskLog(Base):
    """Log entry for a task execution step."""

    __tablename__ = "task_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Log content
    level: Mapped[TaskLogLevel] = mapped_column(
        Enum(TaskLogLevel, values_callable=lambda x: [e.value for e in x]),
        default=TaskLogLevel.INFO,
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    action_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    action_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    screenshot_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="logs")

    def __repr__(self) -> str:
        return f"<TaskLog {self.id}: [{self.level.value}] {self.message[:50]}>"
