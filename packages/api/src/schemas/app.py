"""Schemas for app install service."""

from pydantic import BaseModel, Field


class AppResponse(BaseModel):
    """Response schema for an available app."""
    id: str
    package: str
    name: str
    category: str


class AppListResponse(BaseModel):
    """Response schema for listing apps."""
    apps: list[AppResponse]
    total: int


class BundleResponse(BaseModel):
    """Response schema for an app bundle."""
    id: str
    name: str
    description: str
    apps: list[str]
    app_count: int


class BundleDetailResponse(BaseModel):
    """Response schema for bundle details with full app info."""
    id: str
    name: str
    description: str
    apps: list[AppResponse]


class BundleListResponse(BaseModel):
    """Response schema for listing bundles."""
    bundles: list[BundleResponse]
    total: int


class AppInstallRequest(BaseModel):
    """Request schema for installing an app."""
    wait_for_install: bool = Field(
        default=True,
        description="Wait for installation to complete before returning"
    )
    timeout: int = Field(
        default=120,
        description="Timeout in seconds when waiting for install"
    )


class BundleInstallRequest(BaseModel):
    """Request schema for installing a bundle."""
    sequential: bool = Field(
        default=True,
        description="Install apps one at a time (recommended)"
    )


class AppInstallResultResponse(BaseModel):
    """Response schema for app installation result."""
    success: bool
    app: str | None = None
    package: str | None = None
    already_installed: bool = False
    installed: bool = False
    install_initiated: bool = False
    error: str | None = None


class BundleInstallResultResponse(BaseModel):
    """Response schema for bundle installation result."""
    success: bool
    bundle: str
    apps: list[dict]
    success_count: int
    fail_count: int
    skip_count: int


class InstalledAppResponse(BaseModel):
    """Response schema for an installed app."""
    id: str
    package: str
    name: str
    category: str
    installed: bool = True


class InstalledAppsResponse(BaseModel):
    """Response schema for listing installed apps."""
    apps: list[InstalledAppResponse]
    total: int


class AppLaunchResponse(BaseModel):
    """Response schema for app launch."""
    success: bool
    app_id: str
    package: str | None = None
    error: str | None = None


class AuroraStatusResponse(BaseModel):
    """Response schema for Aurora Store status."""
    installed: bool
    package: str = "com.aurora.store"
