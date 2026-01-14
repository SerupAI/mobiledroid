"""Device control API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db
from src.models.profile import ProfileStatus
from src.services.profile_service import ProfileService
from src.services.docker_service import DockerService
from src.services.adb_service import ADBService
from src.services.fingerprint_service import get_fingerprint_service

router = APIRouter(prefix="/devices", tags=["devices"])


async def get_adb_service() -> ADBService:
    """Get ADB service dependency."""
    return ADBService()


async def get_profile_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProfileService:
    """Get profile service dependency."""
    fingerprint_service = get_fingerprint_service()
    docker_service = DockerService(fingerprint_service)
    adb_service = ADBService()
    return ProfileService(db, docker_service, adb_service)


class TapAction(BaseModel):
    """Tap action payload."""

    x: int = Field(..., ge=0, description="X coordinate")
    y: int = Field(..., ge=0, description="Y coordinate")


class SwipeAction(BaseModel):
    """Swipe action payload."""

    x1: int = Field(..., ge=0, description="Start X coordinate")
    y1: int = Field(..., ge=0, description="Start Y coordinate")
    x2: int = Field(..., ge=0, description="End X coordinate")
    y2: int = Field(..., ge=0, description="End Y coordinate")
    duration: int = Field(default=300, ge=100, le=5000, description="Duration in ms")


class InputTextAction(BaseModel):
    """Text input action payload."""

    text: str = Field(..., min_length=1, max_length=1000, description="Text to input")


class KeyAction(BaseModel):
    """Key press action payload."""

    keycode: str = Field(..., description="Android keycode (e.g., KEYCODE_BACK)")


class ShellAction(BaseModel):
    """Shell command action payload."""

    command: str = Field(..., min_length=1, max_length=1000, description="Shell command")


class LaunchAppAction(BaseModel):
    """Launch app action payload."""

    package: str = Field(..., description="Package name (e.g., com.android.chrome)")


class ActionResponse(BaseModel):
    """Response for device actions."""

    success: bool
    message: str | None = None
    data: dict | None = None


async def get_profile_adb_address(
    profile_id: str,
    service: ProfileService,
) -> str:
    """Get ADB address for a profile (container_name:5555)."""
    profile = await service.get(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )
    if profile.status != ProfileStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile is not running",
        )
    if not profile.adb_port:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile has no ADB port",
        )
    # Use container name for Docker networking
    return f"mobiledroid-{profile_id}:5555"


@router.post("/{profile_id}/tap", response_model=ActionResponse)
async def tap(
    profile_id: str,
    action: TapAction,
    service: Annotated[ProfileService, Depends(get_profile_service)],
    adb: Annotated[ADBService, Depends(get_adb_service)],
) -> ActionResponse:
    """Tap at coordinates on device."""
    address = await get_profile_adb_address(profile_id, service)
    # Don't reconnect if already connected - ADB service handles caching
    success = await adb.tap(address, action.x, action.y)
    return ActionResponse(
        success=success,
        message="Tap executed" if success else "Tap failed",
    )


@router.post("/{profile_id}/swipe", response_model=ActionResponse)
async def swipe(
    profile_id: str,
    action: SwipeAction,
    service: Annotated[ProfileService, Depends(get_profile_service)],
    adb: Annotated[ADBService, Depends(get_adb_service)],
) -> ActionResponse:
    """Swipe gesture on device."""
    address = await get_profile_adb_address(profile_id, service)
    # Don't reconnect if already connected - ADB service handles caching
    success = await adb.swipe(
        address,
        action.x1,
        action.y1,
        action.x2,
        action.y2,
        action.duration,
    )
    return ActionResponse(
        success=success,
        message="Swipe executed" if success else "Swipe failed",
    )


@router.post("/{profile_id}/type", response_model=ActionResponse)
async def input_text(
    profile_id: str,
    action: InputTextAction,
    service: Annotated[ProfileService, Depends(get_profile_service)],
    adb: Annotated[ADBService, Depends(get_adb_service)],
) -> ActionResponse:
    """Input text on device."""
    address = await get_profile_adb_address(profile_id, service)
    # Don't reconnect if already connected - ADB service handles caching
    success = await adb.input_text(address, action.text)
    return ActionResponse(
        success=success,
        message="Text input executed" if success else "Text input failed",
    )


@router.post("/{profile_id}/key", response_model=ActionResponse)
async def press_key(
    profile_id: str,
    action: KeyAction,
    service: Annotated[ProfileService, Depends(get_profile_service)],
    adb: Annotated[ADBService, Depends(get_adb_service)],
) -> ActionResponse:
    """Press a key on device."""
    address = await get_profile_adb_address(profile_id, service)
    host, port = address.rsplit(":", 1)
    await adb.connect(host, int(port))
    success = await adb.press_key(address, action.keycode)
    return ActionResponse(
        success=success,
        message="Key press executed" if success else "Key press failed",
    )


@router.post("/{profile_id}/back", response_model=ActionResponse)
async def press_back(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
    adb: Annotated[ADBService, Depends(get_adb_service)],
) -> ActionResponse:
    """Press back button."""
    address = await get_profile_adb_address(profile_id, service)
    host, port = address.rsplit(":", 1)
    await adb.connect(host, int(port))
    success = await adb.press_back(address)
    return ActionResponse(
        success=success,
        message="Back pressed" if success else "Back press failed",
    )


@router.post("/{profile_id}/home", response_model=ActionResponse)
async def press_home(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
    adb: Annotated[ADBService, Depends(get_adb_service)],
) -> ActionResponse:
    """Press home button."""
    address = await get_profile_adb_address(profile_id, service)
    host, port = address.rsplit(":", 1)
    await adb.connect(host, int(port))
    success = await adb.press_home(address)
    return ActionResponse(
        success=success,
        message="Home pressed" if success else "Home press failed",
    )


@router.post("/{profile_id}/shell", response_model=ActionResponse)
async def shell_command(
    profile_id: str,
    action: ShellAction,
    service: Annotated[ProfileService, Depends(get_profile_service)],
    adb: Annotated[ADBService, Depends(get_adb_service)],
) -> ActionResponse:
    """Execute shell command on device."""
    address = await get_profile_adb_address(profile_id, service)
    host, port = address.rsplit(":", 1)
    await adb.connect(host, int(port))
    result = await adb.shell(address, action.command)
    return ActionResponse(
        success=result is not None,
        message=result if result else "Shell command failed",
        data={"output": result} if result else None,
    )


@router.post("/{profile_id}/launch", response_model=ActionResponse)
async def launch_app(
    profile_id: str,
    action: LaunchAppAction,
    service: Annotated[ProfileService, Depends(get_profile_service)],
    adb: Annotated[ADBService, Depends(get_adb_service)],
) -> ActionResponse:
    """Launch an app on device."""
    address = await get_profile_adb_address(profile_id, service)
    host, port = address.rsplit(":", 1)
    await adb.connect(host, int(port))
    success = await adb.launch_app(address, action.package)
    return ActionResponse(
        success=success,
        message=f"Launched {action.package}" if success else "Launch failed",
    )


@router.get("/{profile_id}/ui-hierarchy")
async def get_ui_hierarchy(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
    adb: Annotated[ADBService, Depends(get_adb_service)],
) -> ActionResponse:
    """Get UI hierarchy XML from device."""
    address = await get_profile_adb_address(profile_id, service)
    host, port = address.rsplit(":", 1)
    await adb.connect(host, int(port))
    hierarchy = await adb.get_ui_hierarchy(address)
    return ActionResponse(
        success=hierarchy is not None,
        data={"hierarchy": hierarchy} if hierarchy else None,
    )


class PasteAction(BaseModel):
    """Paste text action payload."""

    text: str = Field(..., min_length=1, max_length=5000, description="Text to paste")


@router.post("/{profile_id}/paste", response_model=ActionResponse)
async def paste_text(
    profile_id: str,
    action: PasteAction,
    service: Annotated[ProfileService, Depends(get_profile_service)],
    adb: Annotated[ADBService, Depends(get_adb_service)],
) -> ActionResponse:
    """Paste text to the device.

    This attempts to set the clipboard and paste, falling back to
    typing the text if clipboard access is not available.
    """
    address = await get_profile_adb_address(profile_id, service)
    success = await adb.set_clipboard(address, action.text)
    return ActionResponse(
        success=success,
        message="Text pasted" if success else "Paste failed",
    )


@router.get("/{profile_id}/clipboard", response_model=ActionResponse)
async def get_clipboard(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
    adb: Annotated[ADBService, Depends(get_adb_service)],
) -> ActionResponse:
    """Get clipboard contents from the device.

    Note: This requires a clipboard helper app to be installed.
    Returns null if clipboard cannot be read.
    """
    address = await get_profile_adb_address(profile_id, service)
    content = await adb.get_clipboard(address)
    return ActionResponse(
        success=content is not None,
        message="Clipboard read" if content else "Could not read clipboard",
        data={"content": content} if content else None,
    )
