"""Debug endpoints for troubleshooting."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db
from src.services.integration_service import IntegrationService
from src.services.seed_service import SeedService
from src.models.integration import IntegrationPurpose, Integration
from src.models.llm_model import LLMModel
from src.models.llm_provider import LLMProvider
from sqlalchemy import delete, select

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/chat-config")
async def get_chat_config_debug(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Debug endpoint to check what chat configuration is being used."""
    integration_service = IntegrationService(db)
    config = await integration_service.get_chat_config()
    
    if not config:
        return {"error": "No chat config found"}
    
    return {
        "provider_name": config.provider_name,
        "model_name": config.model_name,
        "base_url": config.base_url,
        "max_tokens": config.max_tokens,
        "temperature": config.temperature,
        "has_api_key": bool(config.api_key),
    }


@router.get("/integrations")
async def list_integrations_debug(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all integrations for debugging."""
    integration_service = IntegrationService(db)
    integrations = await integration_service.list_integrations()
    
    return [
        {
            "id": integration.id,
            "name": integration.name,
            "purpose": integration.purpose.value,
            "provider_name": integration.provider.name,
            "model_name": integration.model.name,
            "active": integration.active,
            "is_default": integration.is_default,
            "priority": integration.priority,
        }
        for integration in integrations
    ]


@router.post("/reseed")
async def reseed_data_debug(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Clear and re-seed LLM data with correct model."""
    try:
        # Clear existing data
        await db.execute(delete(Integration))
        await db.execute(delete(LLMModel))
        await db.execute(delete(LLMProvider))
        
        # Re-seed with correct data
        seed_service = SeedService(db)
        await seed_service.seed_initial_data()
        
        return {"status": "success", "message": "Data re-seeded successfully"}
        
    except Exception as e:
        await db.rollback()
        return {"status": "error", "message": str(e)}


@router.get("/database")
async def check_database_debug(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Check what's actually in the database tables."""
    try:
        # Check providers
        providers_result = await db.execute(select(LLMProvider))
        providers = providers_result.scalars().all()
        
        # Check models  
        models_result = await db.execute(select(LLMModel))
        models = models_result.scalars().all()
        
        # Check integrations
        integrations_result = await db.execute(select(Integration))
        integrations = integrations_result.scalars().all()
        
        return {
            "providers": [{"id": p.id, "name": p.name, "has_api_key": bool(p.api_key_encrypted)} for p in providers],
            "models": [{"id": m.id, "name": m.name, "provider_id": m.provider_id} for m in models], 
            "integrations": [{"id": i.id, "name": i.name, "purpose": i.purpose.value, "provider_id": i.provider_id, "model_id": i.model_id, "active": i.active} for i in integrations]
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/fix-api-keys")
async def fix_api_keys_debug(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Fix API keys in providers if they're missing."""
    try:
        from src.config import settings
        
        # Update Anthropic provider
        anthropic_result = await db.execute(select(LLMProvider).where(LLMProvider.name == "anthropic"))
        anthropic_provider = anthropic_result.scalar_one_or_none()
        
        if anthropic_provider and settings.anthropic_api_key:
            anthropic_provider.api_key_encrypted = settings.anthropic_api_key
            
        # Update OpenAI provider
        openai_result = await db.execute(select(LLMProvider).where(LLMProvider.name == "openai"))
        openai_provider = openai_result.scalar_one_or_none()
        
        if openai_provider and settings.openai_api_key:
            openai_provider.api_key_encrypted = settings.openai_api_key
            
        await db.commit()
        
        return {"status": "success", "message": "API keys updated"}
        
    except Exception as e:
        await db.rollback()
        return {"status": "error", "message": str(e)}


@router.get("/settings")
async def check_settings_debug():
    """Check what settings values are loaded."""
    from src.config import settings
    import os

    return {
        "anthropic_api_key_set": bool(settings.anthropic_api_key),
        "openai_api_key_set": bool(settings.openai_api_key),
        "anthropic_api_key_length": len(settings.anthropic_api_key or ""),
        "openai_api_key_length": len(settings.openai_api_key or ""),
        "env_anthropic_set": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "env_openai_set": bool(os.environ.get("OPENAI_API_KEY")),
        "env_anthropic_length": len(os.environ.get("ANTHROPIC_API_KEY", "")),
        "env_openai_length": len(os.environ.get("OPENAI_API_KEY", ""))
    }


@router.get("/ui-hierarchy/{profile_id}")
async def get_ui_hierarchy_debug(
    profile_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get the current UI hierarchy for a profile's device.

    This shows what elements the agent sees and what coordinates it would use.
    """
    from src.services.profile_service import ProfileService
    from src.services.adb_service import ADBService
    from src.agent.vision import VisionService

    profile_service = ProfileService(db)
    profile = await profile_service.get_profile(profile_id)

    if not profile:
        return {"error": "Profile not found"}

    if profile.status != "running":
        return {"error": f"Profile not running (status: {profile.status})"}

    try:
        # Connect to device
        adb_service = ADBService()
        address = f"mobiledroid-{profile_id}:5555"
        connected = await adb_service.connect(f"mobiledroid-{profile_id}", 5555)

        if not connected:
            return {"error": f"Failed to connect to device at {address}"}

        device = adb_service.get_device(address)
        if not device:
            return {"error": f"Device not found after connect: {address}"}

        # Get UI hierarchy
        vision = VisionService(device)
        state = await vision.get_state()

        # Format the hierarchy as Claude would see it
        formatted = vision.format_ui_for_prompt(
            state["ui_elements"],
            state["screen_width"],
            state["screen_height"]
        )

        return {
            "screen_size": f"{state['screen_width']}x{state['screen_height']}",
            "element_count": len(state["ui_elements"]),
            "formatted_hierarchy": formatted,
            "raw_elements": state["ui_elements"][:20],  # First 20 elements
        }

    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}