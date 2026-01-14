"""Settings router for LLM providers, models, and integrations."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from src.db.session import get_db
from src.models.llm_provider import LLMProvider
from src.models.llm_model import LLMModel
from src.models.integration import Integration
from src.schemas.settings import (
    LLMProviderResponse,
    LLMProviderUpdate,
    LLMModelResponse,
    IntegrationResponse,
    IntegrationUpdate,
    ProvidersListResponse,
    ModelsListResponse,
    IntegrationsListResponse,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/settings", tags=["settings"])


def mask_api_key(api_key: str | None) -> str | None:
    """Mask an API key for display, showing first 8 and last 4 characters."""
    if not api_key:
        return None
    if len(api_key) <= 12:
        return "*" * len(api_key)
    return f"{api_key[:8]}...{api_key[-4:]}"


def provider_to_response(provider: LLMProvider) -> LLMProviderResponse:
    """Convert a provider model to a response schema."""
    return LLMProviderResponse(
        id=provider.id,
        name=provider.name,
        display_name=provider.display_name,
        base_url=provider.base_url,
        has_api_key=bool(provider.api_key_encrypted),
        api_key_masked=mask_api_key(provider.api_key_encrypted),
        active=provider.active,
        description=provider.description,
        max_requests_per_minute=provider.max_requests_per_minute,
        max_tokens_per_minute=provider.max_tokens_per_minute,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


def model_to_response(model: LLMModel) -> LLMModelResponse:
    """Convert a model to a response schema."""
    return LLMModelResponse(
        id=model.id,
        provider_id=model.provider_id,
        name=model.name,
        display_name=model.display_name,
        description=model.description,
        context_window=model.context_window,
        max_output_tokens=model.max_output_tokens,
        input_cost_per_1k=model.input_cost_per_1k,
        output_cost_per_1k=model.output_cost_per_1k,
        supports_vision=model.supports_vision,
        supports_function_calling=model.supports_function_calling,
        active=model.active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def integration_to_response(integration: Integration) -> IntegrationResponse:
    """Convert an integration to a response schema."""
    return IntegrationResponse(
        id=integration.id,
        purpose=integration.purpose.value,
        provider_id=integration.provider_id,
        provider_name=integration.provider.display_name if integration.provider else "",
        model_id=integration.model_id,
        model_name=integration.model.display_name if integration.model else "",
        active=integration.active,
        created_at=integration.created_at,
        updated_at=integration.updated_at,
    )


# Provider endpoints
@router.get("/providers", response_model=ProvidersListResponse)
async def list_providers(db: AsyncSession = Depends(get_db)):
    """List all LLM providers."""
    result = await db.execute(select(LLMProvider).order_by(LLMProvider.name))
    providers = result.scalars().all()

    return ProvidersListResponse(
        providers=[provider_to_response(p) for p in providers],
        total=len(providers),
    )


@router.get("/providers/{provider_id}", response_model=LLMProviderResponse)
async def get_provider(provider_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific LLM provider."""
    result = await db.execute(select(LLMProvider).where(LLMProvider.id == provider_id))
    provider = result.scalar_one_or_none()

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    return provider_to_response(provider)


@router.patch("/providers/{provider_id}", response_model=LLMProviderResponse)
async def update_provider(
    provider_id: str,
    update: LLMProviderUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an LLM provider (API key, settings)."""
    result = await db.execute(select(LLMProvider).where(LLMProvider.id == provider_id))
    provider = result.scalar_one_or_none()

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Update fields
    if update.api_key is not None:
        # For now, store key directly. In production, encrypt it.
        provider.api_key_encrypted = update.api_key if update.api_key else None
        logger.info("Updated API key for provider", provider_id=provider_id, provider_name=provider.name)

    if update.active is not None:
        provider.active = update.active

    if update.max_requests_per_minute is not None:
        provider.max_requests_per_minute = update.max_requests_per_minute

    if update.max_tokens_per_minute is not None:
        provider.max_tokens_per_minute = update.max_tokens_per_minute

    await db.commit()
    await db.refresh(provider)

    return provider_to_response(provider)


# Model endpoints
@router.get("/models", response_model=ModelsListResponse)
async def list_models(
    provider_id: str | None = None,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List all LLM models, optionally filtered by provider."""
    query = select(LLMModel)

    if provider_id:
        query = query.where(LLMModel.provider_id == provider_id)
    if active_only:
        query = query.where(LLMModel.active == True)

    query = query.order_by(LLMModel.provider_id, LLMModel.name)

    result = await db.execute(query)
    models = result.scalars().all()

    return ModelsListResponse(
        models=[model_to_response(m) for m in models],
        total=len(models),
    )


@router.get("/models/{model_id}", response_model=LLMModelResponse)
async def get_model(model_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific LLM model."""
    result = await db.execute(select(LLMModel).where(LLMModel.id == model_id))
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return model_to_response(model)


# Integration endpoints
@router.get("/integrations", response_model=IntegrationsListResponse)
async def list_integrations(db: AsyncSession = Depends(get_db)):
    """List all integrations (purpose -> model mappings)."""
    result = await db.execute(
        select(Integration)
        .options(selectinload(Integration.provider), selectinload(Integration.model))
        .order_by(Integration.purpose)
    )
    integrations = result.scalars().all()

    return IntegrationsListResponse(
        integrations=[integration_to_response(i) for i in integrations],
        total=len(integrations),
    )


@router.get("/integrations/{integration_id}", response_model=IntegrationResponse)
async def get_integration(integration_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific integration."""
    result = await db.execute(
        select(Integration)
        .options(selectinload(Integration.provider), selectinload(Integration.model))
        .where(Integration.id == integration_id)
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    return integration_to_response(integration)


@router.patch("/integrations/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: str,
    update: IntegrationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an integration (change model, activate/deactivate)."""
    result = await db.execute(
        select(Integration)
        .options(selectinload(Integration.provider), selectinload(Integration.model))
        .where(Integration.id == integration_id)
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    if update.model_id is not None:
        # Verify the model exists and belongs to the same provider
        model_result = await db.execute(select(LLMModel).where(LLMModel.id == update.model_id))
        new_model = model_result.scalar_one_or_none()

        if not new_model:
            raise HTTPException(status_code=400, detail="Model not found")

        # Update provider_id to match the new model's provider
        integration.model_id = update.model_id
        integration.provider_id = new_model.provider_id
        logger.info(
            "Updated integration model",
            integration_id=integration_id,
            purpose=integration.purpose.value,
            new_model=new_model.name,
        )

    if update.active is not None:
        integration.active = update.active

    await db.commit()
    await db.refresh(integration)

    # Reload relationships
    result = await db.execute(
        select(Integration)
        .options(selectinload(Integration.provider), selectinload(Integration.model))
        .where(Integration.id == integration_id)
    )
    integration = result.scalar_one()

    return integration_to_response(integration)


# Utility endpoint to check if providers are configured
@router.get("/status")
async def get_settings_status(db: AsyncSession = Depends(get_db)):
    """Get overall settings status - which providers have API keys configured."""
    result = await db.execute(select(LLMProvider))
    providers = result.scalars().all()

    provider_status = {}
    for p in providers:
        provider_status[p.name] = {
            "display_name": p.display_name,
            "has_api_key": bool(p.api_key_encrypted),
            "active": p.active,
        }

    # Check integrations
    integrations_result = await db.execute(
        select(Integration).options(selectinload(Integration.provider))
    )
    integrations = integrations_result.scalars().all()

    ready_integrations = []
    missing_integrations = []

    for i in integrations:
        if i.active and i.provider and i.provider.api_key_encrypted:
            ready_integrations.append(i.purpose.value)
        else:
            missing_integrations.append({
                "purpose": i.purpose.value,
                "reason": "inactive" if not i.active else "missing_api_key",
            })

    return {
        "providers": provider_status,
        "ready_integrations": ready_integrations,
        "missing_integrations": missing_integrations,
        "fully_configured": len(missing_integrations) == 0,
    }
