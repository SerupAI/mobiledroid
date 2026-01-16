"""LLM integration service for managing provider and model selection."""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import structlog

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.llm_provider import LLMProvider
from src.models.llm_model import LLMModel
from src.models.integration import Integration, IntegrationPurpose

logger = structlog.get_logger()


class IntegrationConfigError(Exception):
    """Error getting integration configuration."""
    pass


class NoAPIKeyError(IntegrationConfigError):
    """No API key configured for provider."""
    pass


class IntegrationConfig:
    """Configuration for LLM integration."""

    def __init__(
        self,
        provider_name: str,
        model_name: str,
        api_key: str,
        base_url: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.0,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        integration_id: Optional[str] = None,
        fallback_integration_id: Optional[str] = None,
    ):
        self.provider_name = provider_name
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.integration_id = integration_id
        self.fallback_integration_id = fallback_integration_id


class IntegrationService:
    """Service for managing LLM integrations and model selection."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._config_cache: Dict[str, IntegrationConfig] = {}
        self._cache_expires: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=5)  # Cache configs for 5 minutes
    
    async def get_integration_config(
        self,
        purpose: IntegrationPurpose,
        fallback_to_default: bool = True,
        use_fallback_chain: bool = True,
    ) -> Optional[IntegrationConfig]:
        """Get integration configuration for a specific purpose.

        Args:
            purpose: The integration purpose (CHAT, AUTOMATION, ANALYSIS, etc.)
            fallback_to_default: If True, falls back to any default integration
            use_fallback_chain: If True, follows the fallback_integration_id chain
                               when the primary integration's API key is missing

        Returns:
            IntegrationConfig if found, None otherwise
        """
        cache_key = f"{purpose.value}"

        # Check cache first
        if self._is_cached(cache_key):
            logger.debug("Using cached integration config", purpose=purpose.value)
            return self._config_cache[cache_key]

        # Query database for default active integration for this purpose
        query = (
            select(Integration)
            .options(
                selectinload(Integration.provider),
                selectinload(Integration.model)
            )
            .where(
                Integration.purpose == purpose,
                Integration.is_default == True,
                Integration.active == True
            )
            .order_by(Integration.priority.desc(), Integration.created_at.asc())
            .limit(1)
        )

        result = await self.db.execute(query)
        integration = result.scalars().first()

        if not integration and fallback_to_default:
            # Try to get any default integration
            query = (
                select(Integration)
                .options(
                    selectinload(Integration.provider),
                    selectinload(Integration.model)
                )
                .where(
                    Integration.is_default == True,
                    Integration.active == True
                )
                .order_by(Integration.priority.desc())
                .limit(1)
            )

            result = await self.db.execute(query)
            integration = result.scalars().first()

        if not integration:
            logger.warning("No active integration found", purpose=purpose.value)
            return None

        # Try to build configuration, following fallback chain if API key is missing
        config = await self._build_config_with_fallback(
            integration,
            use_fallback_chain=use_fallback_chain
        )

        if config:
            # Cache the configuration
            self._config_cache[cache_key] = config
            self._cache_expires[cache_key] = datetime.utcnow() + self._cache_ttl

        return config

    async def _build_config_with_fallback(
        self,
        integration: Integration,
        use_fallback_chain: bool = True,
        visited_ids: Optional[set] = None,
    ) -> Optional[IntegrationConfig]:
        """Build config from integration, following fallback chain if needed.

        Args:
            integration: The integration to build config from
            use_fallback_chain: Whether to follow fallback chain on error
            visited_ids: Set of already-visited integration IDs to prevent cycles

        Returns:
            IntegrationConfig if successful, None if all fallbacks exhausted
        """
        if visited_ids is None:
            visited_ids = set()

        # Prevent infinite loops
        if integration.id in visited_ids:
            logger.error("Circular fallback chain detected", integration_id=integration.id)
            return None

        visited_ids.add(integration.id)

        try:
            # Try to get API key
            api_key = await self._decrypt_api_key(integration.provider.api_key_encrypted)

            config = IntegrationConfig(
                provider_name=integration.provider.name,
                model_name=integration.model.name,
                api_key=api_key,
                base_url=integration.provider.base_url,
                max_tokens=integration.max_tokens or integration.model.max_tokens,
                temperature=integration.temperature,
                top_p=integration.top_p,
                top_k=integration.top_k,
                integration_id=integration.id,
                fallback_integration_id=integration.fallback_integration_id,
            )

            logger.info(
                "Integration config loaded",
                provider=integration.provider.name,
                model=integration.model.name,
            )

            return config

        except (NoAPIKeyError, ValueError) as e:
            logger.warning(
                "Failed to load integration config",
                provider=integration.provider.name,
                error=str(e),
            )

            # Try fallback if available and enabled
            if use_fallback_chain and integration.fallback_integration_id:
                logger.info(
                    "Trying fallback integration",
                    current_provider=integration.provider.name,
                    fallback_id=integration.fallback_integration_id,
                )

                fallback = await self._get_integration_by_id(
                    integration.fallback_integration_id
                )

                if fallback:
                    return await self._build_config_with_fallback(
                        fallback,
                        use_fallback_chain=True,
                        visited_ids=visited_ids,
                    )

            return None

    async def _get_integration_by_id(self, integration_id: str) -> Optional[Integration]:
        """Get integration by ID with eager loading."""
        query = (
            select(Integration)
            .options(
                selectinload(Integration.provider),
                selectinload(Integration.model)
            )
            .where(Integration.id == integration_id)
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_chat_config(self) -> Optional[IntegrationConfig]:
        """Get configuration for chat purposes."""
        return await self.get_integration_config(IntegrationPurpose.CHAT)
    
    async def get_automation_config(self) -> Optional[IntegrationConfig]:
        """Get configuration for automation purposes."""
        return await self.get_integration_config(IntegrationPurpose.AUTOMATION)
    
    async def get_analysis_config(self) -> Optional[IntegrationConfig]:
        """Get configuration for analysis purposes."""
        return await self.get_integration_config(IntegrationPurpose.ANALYSIS)
    
    async def list_providers(self, active_only: bool = True) -> list[LLMProvider]:
        """List all LLM providers."""
        query = select(LLMProvider)
        if active_only:
            query = query.where(LLMProvider.active == True)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def list_models(
        self, 
        provider_id: Optional[str] = None,
        active_only: bool = True
    ) -> list[LLMModel]:
        """List LLM models, optionally filtered by provider."""
        query = select(LLMModel).options(selectinload(LLMModel.provider))
        
        if provider_id:
            query = query.where(LLMModel.provider_id == provider_id)
        if active_only:
            query = query.where(LLMModel.active == True)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def list_integrations(
        self, 
        purpose: Optional[IntegrationPurpose] = None,
        active_only: bool = True
    ) -> list[Integration]:
        """List integrations, optionally filtered by purpose."""
        query = (
            select(Integration)
            .options(
                selectinload(Integration.provider),
                selectinload(Integration.model)
            )
        )
        
        if purpose:
            query = query.where(Integration.purpose == purpose)
        if active_only:
            query = query.where(Integration.active == True)
        
        query = query.order_by(Integration.purpose, Integration.priority.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._config_cache.clear()
        self._cache_expires.clear()
        logger.info("Integration config cache cleared")
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if configuration is cached and not expired."""
        if cache_key not in self._config_cache:
            return False
        
        if cache_key not in self._cache_expires:
            return False
        
        if datetime.utcnow() > self._cache_expires[cache_key]:
            # Expired
            self._config_cache.pop(cache_key, None)
            self._cache_expires.pop(cache_key, None)
            return False
        
        return True
    
    async def _decrypt_api_key(self, encrypted_key: Optional[str]) -> str:
        """Decrypt API key from database storage.

        TODO: Implement proper encryption/decryption.
        For now, we'll assume keys are stored in plaintext.

        Raises:
            NoAPIKeyError: If no API key is configured
        """
        if not encrypted_key:
            raise NoAPIKeyError("No API key configured for provider")

        # TODO: Implement proper decryption
        return encrypted_key


# Dependency function
async def get_integration_service(db: AsyncSession) -> IntegrationService:
    """Get integration service dependency."""
    return IntegrationService(db)