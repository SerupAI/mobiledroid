"""LLM provider database model."""

from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.llm_model import LLMModel
    from src.models.integration import Integration


class LLMProvider(Base, TimestampMixin):
    """LLM provider configuration (Anthropic, OpenAI, etc.)."""

    __tablename__ = "llm_providers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Encrypted API key storage
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Provider configuration
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Rate limiting settings
    max_requests_per_minute: Mapped[int | None] = mapped_column(nullable=True)
    max_tokens_per_minute: Mapped[int | None] = mapped_column(nullable=True)

    # Relationships
    models: Mapped[list["LLMModel"]] = relationship(
        "LLMModel",
        back_populates="provider",
        cascade="all, delete-orphan",
    )
    
    integrations: Mapped[list["Integration"]] = relationship(
        "Integration",
        back_populates="provider",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<LLMProvider {self.name}: {self.display_name}>"