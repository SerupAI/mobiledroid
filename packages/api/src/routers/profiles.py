"""Profile management API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db
from src.schemas.profile import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    ProfileListResponse,
)
from src.services.profile_service import ProfileService
from src.services.docker_service import DockerService
from src.services.adb_service import ADBService
from src.services.fingerprint_service import get_fingerprint_service, FingerprintService

router = APIRouter(prefix="/profiles", tags=["profiles"])


async def get_profile_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProfileService:
    """Get profile service dependency."""
    fingerprint_service = get_fingerprint_service()
    docker_service = DockerService(fingerprint_service)
    adb_service = ADBService()
    return ProfileService(db, docker_service, adb_service)


@router.post(
    "",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_profile(
    data: ProfileCreate,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileResponse:
    """Create a new device profile."""
    profile = await service.create(data)
    return ProfileResponse.model_validate(profile)


@router.get("", response_model=ProfileListResponse)
async def list_profiles(
    service: Annotated[ProfileService, Depends(get_profile_service)],
    skip: int = 0,
    limit: int = 100,
) -> ProfileListResponse:
    """List all profiles."""
    profiles, total = await service.get_all(skip=skip, limit=limit)
    return ProfileListResponse(
        profiles=[ProfileResponse.model_validate(p) for p in profiles],
        total=total,
    )


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileResponse:
    """Get a profile by ID."""
    profile = await service.get(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )
    return ProfileResponse.model_validate(profile)


@router.patch("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: str,
    data: ProfileUpdate,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileResponse:
    """Update a profile."""
    try:
        profile = await service.update(profile_id, data)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile {profile_id} not found",
            )
        return ProfileResponse.model_validate(profile)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> None:
    """Delete a profile."""
    success = await service.delete(profile_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )


@router.post("/{profile_id}/start", response_model=ProfileResponse)
async def start_profile(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileResponse:
    """Start a profile's container.

    Returns immediately after launching the container.
    Use GET /profiles/{id}/ready to monitor boot progress.
    """
    try:
        profile = await service.start_async(profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile {profile_id} not found",
            )
        return ProfileResponse.model_validate(profile)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start profile: {str(e)}",
        )


@router.post("/{profile_id}/stop", response_model=ProfileResponse)
async def stop_profile(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileResponse:
    """Stop a profile's container."""
    try:
        profile = await service.stop(profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile {profile_id} not found",
            )
        return ProfileResponse.model_validate(profile)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop profile: {str(e)}",
        )


@router.get("/{profile_id}/screenshot")
async def get_screenshot(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> Response:
    """Get a screenshot from a running profile."""
    screenshot = await service.get_screenshot(profile_id)
    if not screenshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not running or screenshot unavailable",
        )
    return Response(content=screenshot, media_type="image/png")


@router.get("/{profile_id}/device-info")
async def get_device_info(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
):
    """Get device info from a running profile."""
    info = await service.get_device_info(profile_id)
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not running or info unavailable",
        )
    return info


@router.post("/{profile_id}/sync-status", response_model=ProfileResponse)
async def sync_profile_status(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileResponse:
    """Sync profile status with actual container status."""
    profile = await service.sync_status(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )
    return ProfileResponse.model_validate(profile)


@router.get("/{profile_id}/ready")
async def check_device_ready(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
):
    """Check if the device is ready for interaction (ADB connected, screenshot available)."""
    ready_status = await service.check_ready(profile_id)
    if ready_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )
    return ready_status
