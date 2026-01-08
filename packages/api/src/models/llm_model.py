"""LLM model database model."""

from typing import TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import String, Integer, Boolean, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.llm_provider import LLMProvider
    from src.models.integration import Integration


class LLMModel(Base, TimestampMixin):
    """Available LLM models per provider."""

    __tablename__ = "llm_models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    provider_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("llm_providers.id"), 
        nullable=False
    )
    
    # Model identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # API model name
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)  # Human-readable name
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Model capabilities
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    supports_streaming: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_images: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_functions: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Pricing (per 1M tokens)
    input_cost_per_million: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 6), nullable=True
    )
    output_cost_per_million: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 6), nullable=True
    )
    
    # Model status
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deprecated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Performance characteristics
    speed_tier: Mapped[str | None] = mapped_column(String(20), nullable=True)  # fast, medium, slow
    quality_tier: Mapped[str | None] = mapped_column(String(20), nullable=True)  # high, medium, low

    # Relationships
    provider: Mapped["LLMProvider"] = relationship(
        "LLMProvider",
        back_populates="models",
    )
    
    integrations: Mapped[list["Integration"]] = relationship(
        "Integration",
        back_populates="model",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<LLMModel {self.provider.name if self.provider else 'Unknown'}/{self.name}: {self.display_name}>"