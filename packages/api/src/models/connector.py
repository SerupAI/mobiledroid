"""Service connector database model for storing connector configurations."""

import enum
from typing import Any

from sqlalchemy import Boolean, Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class ConnectorType(str, enum.Enum):
    """Types of service connectors."""

    PROXY = "proxy"
    STORAGE = "storage"
    LLM = "llm"


class ServiceConnector(Base, TimestampMixin):
    """Database model for service connector configurations.

    Stores persistent configuration for connectors like Tailscale,
    Bright Data, MinIO, etc. The actual connector logic lives in
    the connectors/ module; this just stores the configuration.
    """

    __tablename__ = "service_connectors"

    # Primary identifier (e.g., "tailscale", "brightdata")
    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    # Display information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Type and status
    connector_type: Mapped[ConnectorType] = mapped_column(
        Enum(ConnectorType),
        nullable=False,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Configuration stored as JSON
    # For Tailscale: {"exit_node": "home-pi", "tailnet": "example.org"}
    # For Bright Data: {"zone": "residential", "country": "US"}
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ServiceConnector {self.id}: {self.connector_type.value} enabled={self.enabled}>"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.connector_type.value,
            "enabled": self.enabled,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
