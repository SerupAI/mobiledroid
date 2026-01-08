"""Integration configuration database model."""

from typing import TYPE_CHECKING
import enum

from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.llm_provider import LLMProvider
    from src.models.llm_model import LLMModel


class IntegrationPurpose(str, enum.Enum):
    """Purpose/use case for LLM integration."""
    
    CHAT = "chat"  # Interactive chat conversations
    AUTOMATION = "automation"  # Device automation tasks
    ANALYSIS = "analysis"  # Screenshot/UI analysis
    PLANNING = "planning"  # Multi-step task planning
    CODE_GENERATION = "code_generation"  # Generate automation scripts
    CONTENT_MODERATION = "content_moderation"  # Safety/content filtering


class Integration(Base, TimestampMixin):
    """LLM integration configuration for specific purposes."""

    __tablename__ = "integrations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Purpose configuration
    purpose: Mapped[IntegrationPurpose] = mapped_column(
        Enum(IntegrationPurpose), 
        nullable=False
    )
    
    # Model selection
    provider_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("llm_providers.id"), 
        nullable=False
    )
    model_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("llm_models.id"), 
        nullable=False
    )
    
    # Model parameters
    max_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    top_p: Mapped[float | None] = mapped_column(Float, nullable=True)
    top_k: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Configuration
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Higher = preferred
    
    # Fallback configuration
    fallback_integration_id: Mapped[str | None] = mapped_column(
        String(36), 
        ForeignKey("integrations.id"), 
        nullable=True
    )
    
    # Rate limiting
    max_requests_per_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_limit_per_hour: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    provider: Mapped["LLMProvider"] = relationship(
        "LLMProvider",
        back_populates="integrations",
    )
    
    model: Mapped["LLMModel"] = relationship(
        "LLMModel", 
        back_populates="integrations",
    )
    
    # Self-referential relationship for fallback
    fallback_integration: Mapped["Integration"] = relationship(
        "Integration",
        remote_side=[id],
        post_update=True,
    )

    def __repr__(self) -> str:
        return f"<Integration {self.name}: {self.purpose.value} -> {self.model.name if self.model else 'Unknown'}>"