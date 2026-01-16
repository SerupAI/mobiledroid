"""Service for seeding initial database data."""

from uuid6 import uuid7
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog

from src.models.llm_provider import LLMProvider
from src.models.llm_model import LLMModel
from src.models.integration import Integration, IntegrationPurpose
from src.config import settings

logger = structlog.get_logger()


class SeedError(Exception):
    """Error during seeding."""
    pass


class SeedService:
    """Service for seeding initial database data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _is_seeded(self) -> bool:
        """Check if database has already been seeded.

        Returns True if any LLM providers exist in the database.
        """
        result = await self.db.execute(
            select(func.count(LLMProvider.id))
        )
        count = result.scalar()
        return count > 0

    async def seed_initial_data(self, force: bool = False) -> None:
        """Seed initial LLM providers, models, and integrations.

        Args:
            force: If True, re-seed even if data exists. If False (default),
                   skip seeding if data already exists.

        Behavior:
        - If data exists and force=False: Skip (idempotent)
        - If data exists and force=True: Update with new values
        - Does NOT require env vars to be set (keys can be set via API/DB later)
        """
        # Check if already seeded
        is_seeded = await self._is_seeded()

        if is_seeded and not force:
            logger.info("Database already seeded, skipping (use force=True to re-seed)")
            return

        if is_seeded and force:
            logger.info("Force re-seeding database")

        try:
            await self._seed_providers()
            await self.db.commit()
            logger.info("Providers seeded, committing transaction")

            await self._seed_models()
            await self.db.commit()
            logger.info("Models seeded, committing transaction")

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
            },
            {
                "id": str(uuid7()),
                "name": "google",
                "display_name": "Google AI",
                "base_url": "https://generativelanguage.googleapis.com",
                "api_key_encrypted": settings.gemini_api_key,
                "description": "Google's Gemini models for multimodal AI tasks",
                "max_requests_per_minute": 60,
                "max_tokens_per_minute": 1000000,
            },
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
                # Only update API key if env var provides a non-empty key
                # This prevents overwriting a database-stored key with empty on restart
                new_key = provider_data["api_key_encrypted"]
                if new_key and existing.api_key_encrypted != new_key:
                    existing.api_key_encrypted = new_key
                    logger.info("Updated provider API key from env var", name=provider_data["name"])
    
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

        # Google/Gemini models
        if "google" in providers:
            google_id = providers["google"].id
            models.extend([
                {
                    "id": str(uuid7()),
                    "provider_id": google_id,
                    "name": "gemini-2.0-flash",
                    "display_name": "Gemini 2.0 Flash",
                    "description": "Fast and capable Gemini model for multimodal tasks",
                    "max_tokens": 1000000,
                    "supports_streaming": True,
                    "supports_images": True,
                    "supports_functions": True,
                    "input_cost_per_million": Decimal("0.10"),
                    "output_cost_per_million": Decimal("0.40"),
                    "speed_tier": "fast",
                    "quality_tier": "high",
                },
                {
                    "id": str(uuid7()),
                    "provider_id": google_id,
                    "name": "gemini-1.5-pro",
                    "display_name": "Gemini 1.5 Pro",
                    "description": "Advanced Gemini model with 1M context window",
                    "max_tokens": 1000000,
                    "supports_streaming": True,
                    "supports_images": True,
                    "supports_functions": True,
                    "input_cost_per_million": Decimal("1.25"),
                    "output_cost_per_million": Decimal("5.00"),
                    "speed_tier": "medium",
                    "quality_tier": "high",
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
        """Seed default integrations with fallback chain.

        Creates integrations for each purpose with fallback chain:
        Anthropic (primary) -> OpenAI (fallback) -> Gemini (last resort)
        """
        # Get models for each provider
        result = await self.db.execute(
            select(LLMModel)
            .join(LLMProvider)
            .where(
                LLMModel.name == "claude-sonnet-4-5-20250929",
                LLMProvider.name == "anthropic"
            )
        )
        claude_model = result.scalar_one_or_none()

        result = await self.db.execute(
            select(LLMModel)
            .join(LLMProvider)
            .where(
                LLMModel.name == "gpt-4o",
                LLMProvider.name == "openai"
            )
        )
        gpt_model = result.scalar_one_or_none()

        result = await self.db.execute(
            select(LLMModel)
            .join(LLMProvider)
            .where(
                LLMModel.name == "gemini-2.0-flash",
                LLMProvider.name == "google"
            )
        )
        gemini_model = result.scalar_one_or_none()

        if not claude_model:
            logger.warning("Claude model not found, cannot create default integrations")
            return

        purposes = [
            (IntegrationPurpose.CHAT, "Chat"),
            (IntegrationPurpose.AUTOMATION, "Automation"),
            (IntegrationPurpose.ANALYSIS, "Analysis"),
        ]

        for purpose, purpose_name in purposes:
            # Check if default integration already exists for this purpose
            result = await self.db.execute(
                select(Integration).where(
                    Integration.purpose == purpose,
                    Integration.is_default == True
                )
            )
            existing_default = result.scalar_one_or_none()

            if existing_default:
                logger.info("Default integration already exists", purpose=purpose.value)
                continue

            # Create Gemini fallback (last in chain, no fallback)
            gemini_integration_id = None
            if gemini_model:
                gemini_integration_id = str(uuid7())
                gemini_integration = Integration(
                    id=gemini_integration_id,
                    name=f"Gemini {purpose_name}",
                    description=f"Gemini fallback integration for {purpose_name.lower()}",
                    purpose=purpose,
                    provider_id=gemini_model.provider_id,
                    model_id=gemini_model.id,
                    max_tokens=4096,
                    temperature=0.0,
                    is_default=False,
                    priority=30,
                    fallback_integration_id=None,
                )
                self.db.add(gemini_integration)
                logger.info("Created Gemini integration", purpose=purpose.value)

            # Create OpenAI fallback (points to Gemini)
            openai_integration_id = None
            if gpt_model:
                openai_integration_id = str(uuid7())
                openai_integration = Integration(
                    id=openai_integration_id,
                    name=f"OpenAI {purpose_name}",
                    description=f"OpenAI fallback integration for {purpose_name.lower()}",
                    purpose=purpose,
                    provider_id=gpt_model.provider_id,
                    model_id=gpt_model.id,
                    max_tokens=4096,
                    temperature=0.0,
                    is_default=False,
                    priority=50,
                    fallback_integration_id=gemini_integration_id,
                )
                self.db.add(openai_integration)
                logger.info("Created OpenAI integration", purpose=purpose.value)

            # Create Anthropic default (points to OpenAI fallback)
            anthropic_integration = Integration(
                id=str(uuid7()),
                name=f"Default {purpose_name}",
                description=f"Default integration for {purpose_name.lower()} (Anthropic)",
                purpose=purpose,
                provider_id=claude_model.provider_id,
                model_id=claude_model.id,
                max_tokens=4096,
                temperature=0.0,
                is_default=True,
                priority=100,
                fallback_integration_id=openai_integration_id,
            )
            self.db.add(anthropic_integration)
            logger.info("Created default Anthropic integration", purpose=purpose.value)