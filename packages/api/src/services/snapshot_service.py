"""Service for managing device snapshots."""

import uuid
from datetime import datetime
from typing import List, Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.profile import Profile, ProfileStatus
from src.models.snapshot import Snapshot, SnapshotStatus
from src.services.docker_service import DockerService


logger = structlog.get_logger()


class SnapshotService:
    """Service for managing device snapshots."""

    def __init__(
        self,
        db: AsyncSession,
        docker_service: DockerService,
    ):
        """Initialize snapshot service."""
        self.db = db
        self.docker_service = docker_service

    async def create(
        self,
        profile_id: str,
        name: str,
        description: Optional[str] = None,
    ) -> Optional[Snapshot]:
        """Create a snapshot of a running device."""
        # Get profile
        profile = await self.db.get(Profile, profile_id)
        if not profile:
            logger.warning("Profile not found", profile_id=profile_id)
            return None

        # Check if profile is running
        if profile.status != ProfileStatus.RUNNING:
            logger.warning(
                "Cannot snapshot non-running profile",
                profile_id=profile_id,
                status=profile.status,
            )
            return None

        # Create snapshot record
        snapshot = Snapshot(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            profile_id=profile_id,
            status=SnapshotStatus.CREATING,
            android_version=profile.fingerprint.get("android_version", "Unknown"),
            device_model=profile.fingerprint.get("model", "Unknown"),
        )
        self.db.add(snapshot)
        await self.db.commit()

        try:
            # Create Docker image from running container
            container_id = profile.container_id
            if not container_id:
                raise Exception("No container ID found")

            # Create image tag
            image_tag = f"mobiledroid/snapshot:{snapshot.id}"
            
            # Commit container to create image
            success = await self.docker_service.commit_container(
                container_id=container_id,
                image_tag=image_tag,
                message=f"Snapshot: {name}",
            )

            if success:
                # Get image size
                image_info = await self.docker_service.get_image_info(image_tag)
                size_bytes = image_info.get("Size", 0) if image_info else 0

                # Update snapshot
                snapshot.status = SnapshotStatus.READY
                snapshot.storage_path = image_tag
                snapshot.size_bytes = size_bytes
                snapshot.completed_at = datetime.utcnow()
                
                logger.info(
                    "Snapshot created successfully",
                    snapshot_id=snapshot.id,
                    image_tag=image_tag,
                    size_mb=size_bytes / 1024 / 1024,
                )
            else:
                snapshot.status = SnapshotStatus.FAILED
                logger.error("Failed to create snapshot image")

        except Exception as e:
            logger.error(
                "Snapshot creation error",
                error=str(e),
                snapshot_id=snapshot.id,
            )
            snapshot.status = SnapshotStatus.FAILED

        await self.db.commit()
        await self.db.refresh(snapshot)
        return snapshot

    async def list(
        self,
        profile_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Snapshot]:
        """List snapshots."""
        query = select(Snapshot).order_by(Snapshot.created_at.desc())
        
        if profile_id:
            query = query.where(Snapshot.profile_id == profile_id)
            
        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get(self, snapshot_id: str) -> Optional[Snapshot]:
        """Get a snapshot by ID."""
        return await self.db.get(Snapshot, snapshot_id)

    async def restore(
        self,
        snapshot_id: str,
        new_profile_name: Optional[str] = None,
    ) -> Optional[Profile]:
        """Restore a device from a snapshot."""
        # Get snapshot
        snapshot = await self.get(snapshot_id)
        if not snapshot:
            logger.warning("Snapshot not found", snapshot_id=snapshot_id)
            return None

        if snapshot.status != SnapshotStatus.READY:
            logger.warning(
                "Snapshot not ready",
                snapshot_id=snapshot_id,
                status=snapshot.status,
            )
            return None

        # Get original profile for fingerprint
        original_profile = await self.db.get(Profile, snapshot.profile_id)
        if not original_profile:
            logger.error("Original profile not found", profile_id=snapshot.profile_id)
            return None

        # Create new profile from snapshot
        from src.services.profile_service import ProfileService
        profile_service = ProfileService(
            self.db,
            self.docker_service,
            None,  # ADB service not needed for creation
        )

        # Generate name if not provided
        if not new_profile_name:
            new_profile_name = f"{snapshot.name} (Restored)"

        # Create new profile
        new_profile = await profile_service.create(
            name=new_profile_name,
            fingerprint=original_profile.fingerprint,
            proxy=original_profile.proxy,
        )

        if not new_profile:
            logger.error("Failed to create new profile")
            return None

        # Override the Docker image to use our snapshot
        new_profile_id = new_profile.id
        
        # Start the profile using the snapshot image
        success = await self.docker_service.start_from_snapshot(
            profile_id=new_profile_id,
            fingerprint=original_profile.fingerprint,
            snapshot_image=snapshot.storage_path,
        )

        if success:
            # Get container info
            containers = await self.docker_service.list_containers(
                filters={"label": [f"profile_id={new_profile_id}"]}
            )
            
            if containers:
                container = containers[0]
                new_profile.container_id = container["Id"]
                new_profile.status = ProfileStatus.RUNNING
                new_profile.last_started_at = datetime.utcnow()
                
                await self.db.commit()
                await self.db.refresh(new_profile)
                
                logger.info(
                    "Profile restored from snapshot",
                    profile_id=new_profile_id,
                    snapshot_id=snapshot_id,
                )
                return new_profile
            else:
                logger.error("Container not found after restoration")
                new_profile.status = ProfileStatus.ERROR
                await self.db.commit()
        else:
            logger.error("Failed to start from snapshot")
            new_profile.status = ProfileStatus.ERROR
            await self.db.commit()

        return None

    async def delete(self, snapshot_id: str) -> bool:
        """Delete a snapshot."""
        snapshot = await self.get(snapshot_id)
        if not snapshot:
            return False

        try:
            # Delete Docker image if it exists
            if snapshot.storage_path:
                await self.docker_service.remove_image(snapshot.storage_path)

            # Delete database record
            await self.db.delete(snapshot)
            await self.db.commit()
            
            logger.info("Snapshot deleted", snapshot_id=snapshot_id)
            return True

        except Exception as e:
            logger.error(
                "Failed to delete snapshot",
                error=str(e),
                snapshot_id=snapshot_id,
            )
            await self.db.rollback()
            return False