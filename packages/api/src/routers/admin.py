"""Admin endpoints for system management."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.db.session import get_db
from src.services.seed_service import SeedService

logger = structlog.get_logger()

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/seed")
async def force_seed(
    force: bool = Query(
        default=True,
        description="Force re-seed even if data exists"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Force re-seed the database with initial data.

    Use this endpoint to:
    - Re-seed providers, models, and integrations
    - Update configuration after changing env vars
    - Reset to default values

    Note: This will NOT overwrite existing API keys with empty values.
    To update API keys, use the provider update endpoints or direct SQL.
    """
    logger.info("Admin seed endpoint called", force=force)

    seed_service = SeedService(db)
    await seed_service.seed_initial_data(force=force)

    return {
        "success": True,
        "message": "Database seeded successfully" if force else "Seed check completed",
        "force": force,
    }


@router.get("/status")
async def admin_status(db: AsyncSession = Depends(get_db)):
    """Get admin status including seed state."""
    from sqlalchemy import select, func
    from src.models.llm_provider import LLMProvider
    from src.models.llm_model import LLMModel
    from src.models.integration import Integration

    # Count entities
    providers_result = await db.execute(select(func.count(LLMProvider.id)))
    models_result = await db.execute(select(func.count(LLMModel.id)))
    integrations_result = await db.execute(select(func.count(Integration.id)))

    providers_count = providers_result.scalar()
    models_count = models_result.scalar()
    integrations_count = integrations_result.scalar()

    return {
        "seeded": providers_count > 0,
        "counts": {
            "providers": providers_count,
            "models": models_count,
            "integrations": integrations_count,
        }
    }
