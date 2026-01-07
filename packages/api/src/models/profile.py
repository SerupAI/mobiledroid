"""Profile database model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.task import Task
    from src.models.snapshot import Snapshot

import enum


class ProfileStatus(str, enum.Enum):
    """Profile container status."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class ProxyType(str, enum.Enum):
    """Proxy types."""

    NONE = "none"
    HTTP = "http"
    SOCKS5 = "socks5"


class Profile(Base, TimestampMixin):
    """Device profile with fingerprint and container configuration."""

    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status
    status: Mapped[ProfileStatus] = mapped_column(
        Enum(ProfileStatus),
        default=ProfileStatus.STOPPED,
        nullable=False,
    )
    container_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    adb_port: Mapped[int | None] = mapped_column(nullable=True)

    # Device fingerprint (stored as JSON)
    fingerprint: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Proxy configuration (stored as JSON)
    proxy: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Last activity tracking
    last_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_stopped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    
    snapshots: Mapped[list["Snapshot"]] = relationship(
        "Snapshot",
        back_populates="profile",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Profile {self.id}: {self.name} ({self.status.value})>"
