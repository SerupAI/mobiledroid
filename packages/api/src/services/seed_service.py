"""Service for seeding initial database data."""

from uuid6 import uuid7
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from src.models.llm_provider import LLMProvider
from src.models.llm_model import LLMModel
from src.models.integration import Integration, IntegrationPurpose
from src.config import settings

logger = structlog.get_logger()


class SeedService:
    """Service for seeding initial database data."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def seed_initial_data(self) -> None:
        """Seed initial LLM providers, models, and integrations."""
        try:
            await self._seed_providers()
            await self._seed_models()
            await self._seed_integrations()
            await self.db.commit()
            logger.info("Initial data seeded successfully")
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to seed initial data", error=str(e))
            raise
    
    async def _seed_providers(self) -> None:
        """Seed LLM providers."""
        providers = [
            {
                "id": str(uuid7()),
                "name": "anthropic",
                "display_name": "Anthropic",
                "base_url": "https://api.anthropic.com",
                "api_key_encrypted": settings.anthropic_api_key,
                "description": "Anthropic's Claude models for advanced reasoning and conversation",
                "max_requests_per_minute": 60,
                "max_tokens_per_minute": 200000,
            },
            {
                "id": str(uuid7()),
                "name": "openai", 
                "display_name": "OpenAI",
                "base_url": "https://api.openai.com/v1",
                "api_key_encrypted": settings.openai_api_key,
                "description": "OpenAI's GPT models for various AI tasks",
                "max_requests_per_minute": 60,
                "max_tokens_per_minute": 150000,
            }
        ]
        
        for provider_data in providers:
            # Check if provider already exists
            result = await self.db.execute(
                select(LLMProvider).where(LLMProvider.name == provider_data["name"])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                provider = LLMProvider(**provider_data)
                self.db.add(provider)
                logger.info("Created provider", name=provider_data["name"])
            else:
                # Update API key if it's different
                if existing.api_key_encrypted != provider_data["api_key_encrypted"]:
                    existing.api_key_encrypted = provider_data["api_key_encrypted"]
                    logger.info("Updated provider API key", name=provider_data["name"])
    
    async def _seed_models(self) -> None:
        """Seed LLM models."""
        # Get providers
        result = await self.db.execute(select(LLMProvider))
        providers = {p.name: p for p in result.scalars().all()}
        
        if not providers:
            logger.warning("No providers found, cannot seed models")
            return
        
        models = []
        
        # Anthropic models
        if "anthropic" in providers:
            anthropic_id = providers["anthropic"].id
            models.extend([
                {
                    "id": str(uuid7()),
                    "provider_id": anthropic_id,
                    "name": "claude-sonnet-4-5-20250929",
                    "display_name": "Claude 4.5 Sonnet",
                    "description": "Most capable Claude model for complex reasoning and analysis",
                    "max_tokens": 200000,
                    "supports_streaming": True,
                    "supports_images": True,
                    "supports_functions": True,
                    "input_cost_per_million": Decimal("3.00"),
                    "output_cost_per_million": Decimal("15.00"),
                    "speed_tier": "fast",
                    "quality_tier": "high",
                },
                {
                    "id": str(uuid7()),
                    "provider_id": anthropic_id,
                    "name": "claude-3-haiku-20240307",
                    "display_name": "Claude 3 Haiku",
                    "description": "Fast and affordable model for simple tasks",
                    "max_tokens": 200000,
                    "supports_streaming": True,
                    "supports_images": True,
                    "supports_functions": False,
                    "input_cost_per_million": Decimal("0.25"),
                    "output_cost_per_million": Decimal("1.25"),
                    "speed_tier": "fast",
                    "quality_tier": "medium",
                },
            ])
        
        # OpenAI models
        if "openai" in providers:
            openai_id = providers["openai"].id
            models.extend([
                {
                    "id": str(uuid7()),
                    "provider_id": openai_id,
                    "name": "gpt-4o",
                    "display_name": "GPT-4 Omni",
                    "description": "Most capable GPT-4 model",
                    "max_tokens": 128000,
                    "supports_streaming": True,
                    "supports_images": True,
                    "supports_functions": True,
                    "input_cost_per_million": Decimal("5.00"),
                    "output_cost_per_million": Decimal("15.00"),
                    "speed_tier": "medium",
                    "quality_tier": "high",
                },
                {
                    "id": str(uuid7()),
                    "provider_id": openai_id,
                    "name": "gpt-4o-mini",
                    "display_name": "GPT-4 Omni Mini",
                    "description": "Efficient model for most tasks",
                    "max_tokens": 128000,
                    "supports_streaming": True,
                    "supports_images": True,
                    "supports_functions": True,
                    "input_cost_per_million": Decimal("0.15"),
                    "output_cost_per_million": Decimal("0.60"),
                    "speed_tier": "fast",
                    "quality_tier": "medium",
                },
            ])
        
        for model_data in models:
            # Check if model already exists
            result = await self.db.execute(
                select(LLMModel).where(
                    LLMModel.name == model_data["name"],
                    LLMModel.provider_id == model_data["provider_id"]
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                model = LLMModel(**model_data)
                self.db.add(model)
                logger.info("Created model", name=model_data["name"])
    
    async def _seed_integrations(self) -> None:
        """Seed default integrations."""
        # Get Claude 4.5 Sonnet model
        result = await self.db.execute(
            select(LLMModel)
            .join(LLMProvider)
            .where(
                LLMModel.name == "claude-sonnet-4-5-20250929",
                LLMProvider.name == "anthropic"
            )
        )
        claude_model = result.scalar_one_or_none()
        
        if not claude_model:
            logger.warning("Claude model not found, cannot create default integrations")
            return
        
        integrations = [
            {
                "id": str(uuid7()),
                "name": "Default Chat",
                "description": "Default integration for chat conversations",
                "purpose": IntegrationPurpose.CHAT,
                "provider_id": claude_model.provider_id,
                "model_id": claude_model.id,
                "max_tokens": 4096,
                "temperature": 0.0,
                "is_default": True,
                "priority": 100,
            },
            {
                "id": str(uuid7()),
                "name": "Default Automation",
                "description": "Default integration for device automation tasks",
                "purpose": IntegrationPurpose.AUTOMATION,
                "provider_id": claude_model.provider_id,
                "model_id": claude_model.id,
                "max_tokens": 4096,
                "temperature": 0.0,
                "is_default": True,
                "priority": 100,
            },
            {
                "id": str(uuid7()),
                "name": "Default Analysis",
                "description": "Default integration for screenshot and UI analysis",
                "purpose": IntegrationPurpose.ANALYSIS,
                "provider_id": claude_model.provider_id,
                "model_id": claude_model.id,
                "max_tokens": 4096,
                "temperature": 0.0,
                "is_default": True,
                "priority": 100,
            }
        ]
        
        for integration_data in integrations:
            # Check if integration already exists
            result = await self.db.execute(
                select(Integration).where(
                    Integration.purpose == integration_data["purpose"],
                    Integration.is_default == True
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                integration = Integration(**integration_data)
                self.db.add(integration)
                logger.info("Created integration", purpose=integration_data["purpose"].value)