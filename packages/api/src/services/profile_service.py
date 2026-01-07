"""Profile service for managing device profiles."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog
from uuid6 import uuid7

from src.models.profile import Profile, ProfileStatus
from src.schemas.profile import ProfileCreate, ProfileUpdate
from src.services.docker_service import DockerService
from src.services.adb_service import ADBService

logger = structlog.get_logger()


class ProfileService:
    """Service for managing device profiles."""

    def __init__(
        self,
        db: AsyncSession,
        docker_service: DockerService,
        adb_service: ADBService,
    ):
        self.db = db
        self.docker = docker_service
        self.adb = adb_service

    async def create(self, data: ProfileCreate) -> Profile:
        """Create a new profile."""
        profile = Profile(
            id=str(uuid7()),
            name=data.name,
            fingerprint=data.fingerprint.model_dump(),
            proxy=data.proxy.model_dump(),
            status=ProfileStatus.STOPPED,
        )

        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)

        logger.info("Created profile", profile_id=profile.id, name=profile.name)
        return profile

    async def get(self, profile_id: str) -> Profile | None:
        """Get a profile by ID."""
        result = await self.db.execute(
            select(Profile).where(Profile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Profile], int]:
        """Get all profiles with pagination."""
        # Get total count
        count_result = await self.db.execute(
            select(Profile.id)
        )
        total = len(count_result.all())

        # Get profiles
        result = await self.db.execute(
            select(Profile)
            .order_by(Profile.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        profiles = list(result.scalars().all())

        return profiles, total

    async def update(
        self,
        profile_id: str,
        data: ProfileUpdate,
    ) -> Profile | None:
        """Update a profile."""
        profile = await self.get(profile_id)
        if not profile:
            return None

        if profile.status == ProfileStatus.RUNNING:
            raise ValueError("Cannot update a running profile")

        if data.name is not None:
            profile.name = data.name
        if data.fingerprint is not None:
            profile.fingerprint = data.fingerprint.model_dump()
        if data.proxy is not None:
            profile.proxy = data.proxy.model_dump()

        await self.db.flush()
        await self.db.refresh(profile)

        logger.info("Updated profile", profile_id=profile_id)
        return profile

    async def delete(self, profile_id: str) -> bool:
        """Delete a profile."""
        profile = await self.get(profile_id)
        if not profile:
            return False

        # Stop and remove container if exists
        if profile.container_id:
            await self.docker.stop_container(profile.container_id)
            await self.docker.remove_container(profile.container_id)

        await self.db.delete(profile)
        await self.db.flush()

        logger.info("Deleted profile", profile_id=profile_id)
        return True

    async def start(self, profile_id: str) -> Profile | None:
        """Start a profile's container."""
        profile = await self.get(profile_id)
        if not profile:
            return None

        if profile.status == ProfileStatus.RUNNING:
            logger.info("Profile already running", profile_id=profile_id)
            return profile

        try:
            profile.status = ProfileStatus.STARTING
            await self.db.flush()

            # Create or start container
            if profile.container_id:
                # Try to start existing container
                status = self.docker.get_container_status(profile.container_id)
                if status == "exited":
                    await self.docker.start_container(profile.container_id)
                elif status is None:
                    # Container doesn't exist, create new one
                    container_id, adb_port = await self.docker.create_container(
                        profile_id=profile.id,
                        name=profile.name,
                        fingerprint=profile.fingerprint,
                        proxy=profile.proxy,
                    )
                    profile.container_id = container_id
                    profile.adb_port = adb_port
            else:
                # Create new container
                container_id, adb_port = await self.docker.create_container(
                    profile_id=profile.id,
                    name=profile.name,
                    fingerprint=profile.fingerprint,
                    proxy=profile.proxy,
                )
                profile.container_id = container_id
                profile.adb_port = adb_port

            # Wait for Android to boot
            boot_success = await self.docker.wait_for_boot(
                profile.container_id,
                timeout=120,
            )

            if not boot_success:
                profile.status = ProfileStatus.ERROR
                await self.db.flush()
                return profile

            # Connect via ADB
            adb_address = f"localhost:{profile.adb_port}"
            await self.adb.connect("localhost", profile.adb_port)

            profile.status = ProfileStatus.RUNNING
            profile.last_started_at = datetime.utcnow()
            await self.db.flush()
            await self.db.refresh(profile)

            logger.info(
                "Started profile",
                profile_id=profile_id,
                adb_port=profile.adb_port,
            )
            return profile

        except Exception as e:
            logger.error(
                "Failed to start profile",
                profile_id=profile_id,
                error=str(e),
            )
            profile.status = ProfileStatus.ERROR
            await self.db.flush()
            raise

    async def stop(self, profile_id: str) -> Profile | None:
        """Stop a profile's container."""
        profile = await self.get(profile_id)
        if not profile:
            return None

        if profile.status == ProfileStatus.STOPPED:
            return profile

        try:
            profile.status = ProfileStatus.STOPPING
            await self.db.flush()

            # Disconnect ADB
            if profile.adb_port:
                await self.adb.disconnect(f"localhost:{profile.adb_port}")

            # Stop container
            if profile.container_id:
                await self.docker.stop_container(profile.container_id)

            profile.status = ProfileStatus.STOPPED
            profile.last_stopped_at = datetime.utcnow()
            await self.db.flush()
            await self.db.refresh(profile)

            logger.info("Stopped profile", profile_id=profile_id)
            return profile

        except Exception as e:
            logger.error(
                "Failed to stop profile",
                profile_id=profile_id,
                error=str(e),
            )
            profile.status = ProfileStatus.ERROR
            await self.db.flush()
            raise

    async def get_screenshot(self, profile_id: str) -> bytes | None:
        """Get a screenshot from a running profile."""
        profile = await self.get(profile_id)
        if not profile or profile.status != ProfileStatus.RUNNING:
            return None

        if not profile.adb_port:
            return None

        return await self.adb.screenshot(f"localhost:{profile.adb_port}")

    async def get_device_info(self, profile_id: str) -> dict[str, Any] | None:
        """Get device info from a running profile."""
        profile = await self.get(profile_id)
        if not profile or profile.status != ProfileStatus.RUNNING:
            return None

        if not profile.adb_port:
            return None

        return await self.adb.get_device_info(f"localhost:{profile.adb_port}")

    async def sync_status(self, profile_id: str) -> Profile | None:
        """Sync profile status with actual container status."""
        profile = await self.get(profile_id)
        if not profile:
            return None

        if profile.container_id:
            container_status = self.docker.get_container_status(profile.container_id)

            if container_status == "running":
                profile.status = ProfileStatus.RUNNING
            elif container_status == "exited":
                profile.status = ProfileStatus.STOPPED
            elif container_status is None:
                profile.status = ProfileStatus.STOPPED
                profile.container_id = None
                profile.adb_port = None
            else:
                profile.status = ProfileStatus.ERROR

            await self.db.flush()
            await self.db.refresh(profile)

        return profile

    async def check_ready(self, profile_id: str) -> dict[str, Any] | None:
        """Check if device is ready for interaction."""
        profile = await self.get(profile_id)
        if not profile:
            return None

        result = {
            "profile_id": profile_id,
            "status": profile.status.value,
            "container_running": False,
            "adb_connected": False,
            "screen_available": False,
            "ready": False,
            "message": "Unknown state",
        }

        # Check profile status
        if profile.status == ProfileStatus.STOPPED:
            result["message"] = "Profile is stopped"
            return result

        if profile.status == ProfileStatus.STARTING:
            result["message"] = "Device is booting..."
            return result

        if profile.status == ProfileStatus.ERROR:
            result["message"] = "Profile is in error state"
            return result

        if profile.status != ProfileStatus.RUNNING:
            result["message"] = f"Profile status: {profile.status.value}"
            return result

        # Check container
        if profile.container_id:
            container_status = self.docker.get_container_status(profile.container_id)
            result["container_running"] = container_status == "running"
            if not result["container_running"]:
                result["message"] = "Container not running"
                return result

        # Check ADB connection
        if profile.adb_port:
            try:
                devices = await self.adb.list_devices()
                adb_addr = f"localhost:{profile.adb_port}"
                result["adb_connected"] = any(adb_addr in d for d in devices)
            except Exception as e:
                logger.debug("ADB check failed", error=str(e))
                result["adb_connected"] = False

            if not result["adb_connected"]:
                result["message"] = "ADB not connected"
                return result

        # Try to get a screenshot to verify screen is ready
        try:
            screenshot = await self.adb.screenshot(f"localhost:{profile.adb_port}")
            result["screen_available"] = screenshot is not None and len(screenshot) > 0
        except Exception as e:
            logger.debug("Screenshot check failed", error=str(e))
            result["screen_available"] = False

        if not result["screen_available"]:
            result["message"] = "Screen not available yet"
            return result

        # All checks passed
        result["ready"] = True
        result["message"] = "Device ready"
        return result
