"""Fingerprint API routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query

from src.services.fingerprint_service import FingerprintService, get_fingerprint_service

router = APIRouter(prefix="/fingerprints", tags=["fingerprints"])


@router.get("")
async def list_fingerprints(
    service: Annotated[FingerprintService, Depends(get_fingerprint_service)],
    brand: str | None = Query(None, description="Filter by brand"),
    model: str | None = Query(None, description="Search by model name"),
    android_version: str | None = Query(None, description="Filter by Android version"),
) -> dict[str, Any]:
    """List available device fingerprints."""
    if brand or model or android_version:
        fingerprints = service.search_fingerprints(
            brand=brand,
            model=model,
            android_version=android_version,
        )
    else:
        fingerprints = service.get_all_fingerprints()

    return {
        "fingerprints": fingerprints,
        "total": len(fingerprints),
    }


@router.get("/random")
async def get_random_fingerprint(
    service: Annotated[FingerprintService, Depends(get_fingerprint_service)],
) -> dict[str, Any]:
    """Generate a random device fingerprint.

    Returns a randomly selected device profile with unique identifiers
    (Android ID, serial number, MAC addresses) generated fresh each time.
    This is useful for creating new profiles without manually selecting
    a device type.
    """
    return service.generate_random_fingerprint()


@router.get("/{device_id}")
async def get_fingerprint(
    device_id: str,
    service: Annotated[FingerprintService, Depends(get_fingerprint_service)],
) -> dict[str, Any]:
    """Get a specific device fingerprint."""
    fingerprint = service.get_fingerprint(device_id)
    if not fingerprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fingerprint {device_id} not found",
        )
    return fingerprint


@router.get("/brands/list")
async def list_brands(
    service: Annotated[FingerprintService, Depends(get_fingerprint_service)],
) -> dict[str, Any]:
    """List all available brands."""
    fingerprints = service.get_all_fingerprints()
    brands = sorted(set(fp.get("brand", "").lower() for fp in fingerprints if fp.get("brand")))
    return {"brands": brands}


@router.get("/android-versions/list")
async def list_android_versions(
    service: Annotated[FingerprintService, Depends(get_fingerprint_service)],
) -> dict[str, Any]:
    """List all available Android versions."""
    fingerprints = service.get_all_fingerprints()
    versions = sorted(
        set(fp.get("android_version", "") for fp in fingerprints if fp.get("android_version")),
        reverse=True,
    )
    return {"android_versions": versions}
