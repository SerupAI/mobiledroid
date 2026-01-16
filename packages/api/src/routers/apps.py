"""API router for app installation service."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db
from src.schemas.app import (
    AppInstallRequest,
    AppInstallResultResponse,
    AppLaunchResponse,
    AppListResponse,
    AppResponse,
    AuroraStatusResponse,
    BundleDetailResponse,
    BundleInstallRequest,
    BundleInstallResultResponse,
    BundleListResponse,
    BundleResponse,
    InstalledAppResponse,
    InstalledAppsResponse,
)
from src.services.adb_service import ADBService
from src.services.app_install_service import AppCategory, AppInstallService
from src.services.profile_service import ProfileService

router = APIRouter(prefix="/apps", tags=["apps"])


def get_adb_service() -> ADBService:
    """Get ADB service dependency."""
    return ADBService()


def get_app_service(adb: ADBService = Depends(get_adb_service)) -> AppInstallService:
    """Get app install service dependency."""
    return AppInstallService(adb)


async def get_profile_service(db: AsyncSession = Depends(get_db)) -> ProfileService:
    """Get profile service dependency."""
    return ProfileService(db)


# === App Catalog Endpoints ===


@router.get("", response_model=AppListResponse)
async def list_apps(
    category: str | None = None,
    service: AppInstallService = Depends(get_app_service),
) -> AppListResponse:
    """List available apps for installation.

    Optionally filter by category (social, messaging, productivity, entertainment, utilities).
    """
    cat = None
    if category:
        try:
            cat = AppCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {category}. Valid options: {[c.value for c in AppCategory]}"
            )

    apps = service.list_apps(cat)
    return AppListResponse(
        apps=[
            AppResponse(
                id=app["id"],
                package=app["package"],
                name=app["name"],
                category=app["category"],
            )
            for app in apps
        ],
        total=len(apps),
    )


@router.get("/bundles", response_model=BundleListResponse)
async def list_bundles(
    service: AppInstallService = Depends(get_app_service),
) -> BundleListResponse:
    """List available app bundles for one-click installation."""
    bundles = service.list_bundles()
    return BundleListResponse(
        bundles=[
            BundleResponse(
                id=bundle["id"],
                name=bundle["name"],
                description=bundle["description"],
                apps=bundle["apps"],
                app_count=bundle["app_count"],
            )
            for bundle in bundles
        ],
        total=len(bundles),
    )


@router.get("/bundles/{bundle_id}", response_model=BundleDetailResponse)
async def get_bundle(
    bundle_id: str,
    service: AppInstallService = Depends(get_app_service),
) -> BundleDetailResponse:
    """Get bundle details with full app information."""
    bundle = service.get_bundle(bundle_id)
    if not bundle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bundle '{bundle_id}' not found",
        )
    return BundleDetailResponse(
        id=bundle["id"],
        name=bundle["name"],
        description=bundle["description"],
        apps=[
            AppResponse(
                id=app["id"],
                package=app["package"],
                name=app["name"],
                category="",  # Not included in get_bundle
            )
            for app in bundle["apps"]
        ],
    )


# === Profile-specific App Endpoints ===


@router.get("/profiles/{profile_id}/installed", response_model=InstalledAppsResponse)
async def get_installed_apps(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
    app_service: AppInstallService = Depends(get_app_service),
    profile_service: ProfileService = Depends(get_profile_service),
) -> InstalledAppsResponse:
    """Get list of known installed apps on a profile's device."""
    profile = await profile_service.get(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{profile_id}' not found",
        )

    if profile.status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile must be running to check installed apps",
        )

    adb_addr = f"mobiledroid-{profile_id}:5555"
    apps = await app_service.get_installed_apps(adb_addr)

    return InstalledAppsResponse(
        apps=[
            InstalledAppResponse(
                id=app["id"],
                package=app["package"],
                name=app["name"],
                category=app["category"],
            )
            for app in apps
        ],
        total=len(apps),
    )


@router.get("/profiles/{profile_id}/aurora/status", response_model=AuroraStatusResponse)
async def check_aurora_status(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
    app_service: AppInstallService = Depends(get_app_service),
    profile_service: ProfileService = Depends(get_profile_service),
) -> AuroraStatusResponse:
    """Check if Aurora Store is installed on profile's device."""
    profile = await profile_service.get(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{profile_id}' not found",
        )

    if profile.status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile must be running to check Aurora Store status",
        )

    adb_addr = f"mobiledroid-{profile_id}:5555"
    installed = await app_service.is_aurora_installed(adb_addr)

    return AuroraStatusResponse(installed=installed)


@router.post("/profiles/{profile_id}/install/{app_id}", response_model=AppInstallResultResponse)
async def install_app(
    profile_id: str,
    app_id: str,
    request: AppInstallRequest | None = None,
    db: AsyncSession = Depends(get_db),
    app_service: AppInstallService = Depends(get_app_service),
    profile_service: ProfileService = Depends(get_profile_service),
) -> AppInstallResultResponse:
    """Install an app on a profile's device via Aurora Store.

    This opens Aurora Store to the app's page and clicks Install.
    The AI agent can also be used for more complex installation scenarios.
    """
    profile = await profile_service.get(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{profile_id}' not found",
        )

    if profile.status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile must be running to install apps",
        )

    adb_addr = f"mobiledroid-{profile_id}:5555"

    # Use request params or defaults
    wait = request.wait_for_install if request else True
    timeout = request.timeout if request else 120

    result = await app_service.install_app(
        adb_addr,
        app_id,
        wait_for_install=wait,
        timeout=timeout,
    )

    return AppInstallResultResponse(**result)


@router.post("/profiles/{profile_id}/install/bundle/{bundle_id}", response_model=BundleInstallResultResponse)
async def install_bundle(
    profile_id: str,
    bundle_id: str,
    request: BundleInstallRequest | None = None,
    db: AsyncSession = Depends(get_db),
    app_service: AppInstallService = Depends(get_app_service),
    profile_service: ProfileService = Depends(get_profile_service),
) -> BundleInstallResultResponse:
    """Install all apps in a bundle on a profile's device.

    This installs each app sequentially via Aurora Store.
    Recommended for initial device setup.
    """
    profile = await profile_service.get(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{profile_id}' not found",
        )

    if profile.status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile must be running to install apps",
        )

    adb_addr = f"mobiledroid-{profile_id}:5555"
    sequential = request.sequential if request else True

    result = await app_service.install_bundle(
        adb_addr,
        bundle_id,
        sequential=sequential,
    )

    if not result.get("success") and result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )

    return BundleInstallResultResponse(**result)


@router.post("/profiles/{profile_id}/launch/{app_id}", response_model=AppLaunchResponse)
async def launch_app(
    profile_id: str,
    app_id: str,
    db: AsyncSession = Depends(get_db),
    app_service: AppInstallService = Depends(get_app_service),
    profile_service: ProfileService = Depends(get_profile_service),
) -> AppLaunchResponse:
    """Launch an installed app on a profile's device."""
    profile = await profile_service.get(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{profile_id}' not found",
        )

    if profile.status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile must be running to launch apps",
        )

    adb_addr = f"mobiledroid-{profile_id}:5555"
    success = await app_service.launch_app(adb_addr, app_id)

    from src.services.app_install_service import POPULAR_APPS
    app_info = POPULAR_APPS.get(app_id)

    return AppLaunchResponse(
        success=success,
        app_id=app_id,
        package=app_info["package"] if app_info else None,
        error=None if success else f"Failed to launch {app_id}",
    )


@router.post("/profiles/{profile_id}/open-aurora/{app_id}")
async def open_app_in_aurora(
    profile_id: str,
    app_id: str,
    db: AsyncSession = Depends(get_db),
    app_service: AppInstallService = Depends(get_app_service),
    profile_service: ProfileService = Depends(get_profile_service),
) -> dict:
    """Open an app's page in Aurora Store (for manual install).

    Use this when you want to review the app before installing,
    or when automated install doesn't work.
    """
    profile = await profile_service.get(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{profile_id}' not found",
        )

    if profile.status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile must be running to open Aurora Store",
        )

    adb_addr = f"mobiledroid-{profile_id}:5555"
    success = await app_service.open_app_by_id(adb_addr, app_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to open {app_id} in Aurora Store",
        )

    return {
        "success": True,
        "message": f"Opened {app_id} in Aurora Store",
        "app_id": app_id,
    }
