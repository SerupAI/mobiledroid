"""Snapshot API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db
from src.models.snapshot import Snapshot
from src.services.snapshot_service import SnapshotService
from src.services.docker_service import DockerService
from src.services.fingerprint_service import get_fingerprint_service


router = APIRouter(prefix="/snapshots", tags=["snapshots"])


# Pydantic models
class CreateSnapshotRequest(BaseModel):
    """Request to create a snapshot."""
    name: str
    description: Optional[str] = None
    profile_id: str


class RestoreSnapshotRequest(BaseModel):
    """Request to restore from a snapshot."""
    new_profile_name: Optional[str] = None


class SnapshotResponse(BaseModel):
    """Snapshot response."""
    id: str
    name: str
    description: Optional[str]
    profile_id: str
    status: str
    size_bytes: Optional[int]
    android_version: str
    device_model: str
    storage_path: Optional[str]
    created_at: str
    completed_at: Optional[str]

    @classmethod
    def from_model(cls, snapshot: Snapshot) -> "SnapshotResponse":
        return cls(
            id=str(snapshot.id),
            name=snapshot.name,
            description=snapshot.description,
            profile_id=str(snapshot.profile_id),
            status=snapshot.status,
            size_bytes=snapshot.size_bytes,
            android_version=snapshot.android_version,
            device_model=snapshot.device_model,
            storage_path=snapshot.storage_path,
            created_at=snapshot.created_at.isoformat(),
            completed_at=snapshot.completed_at.isoformat() if snapshot.completed_at else None,
        )


async def get_snapshot_service(db: AsyncSession = Depends(get_db)) -> SnapshotService:
    """Get snapshot service dependency."""
    fingerprint_service = get_fingerprint_service()
    docker_service = DockerService(fingerprint_service)
    return SnapshotService(db, docker_service)


@router.post("/", response_model=SnapshotResponse)
async def create_snapshot(
    request: CreateSnapshotRequest,
    snapshot_service: SnapshotService = Depends(get_snapshot_service),
) -> SnapshotResponse:
    """Create a snapshot of a running device."""
    snapshot = await snapshot_service.create(
        profile_id=request.profile_id,
        name=request.name,
        description=request.description,
    )
    
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create snapshot. Profile must be running.",
        )
    
    return SnapshotResponse.from_model(snapshot)


@router.get("/", response_model=List[SnapshotResponse])
async def list_snapshots(
    profile_id: Optional[str] = None,
    limit: int = 50,
    snapshot_service: SnapshotService = Depends(get_snapshot_service),
) -> List[SnapshotResponse]:
    """List snapshots."""
    snapshots = await snapshot_service.list(profile_id=profile_id, limit=limit)
    return [SnapshotResponse.from_model(s) for s in snapshots]


@router.get("/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(
    snapshot_id: str,
    snapshot_service: SnapshotService = Depends(get_snapshot_service),
) -> SnapshotResponse:
    """Get a snapshot by ID."""
    snapshot = await snapshot_service.get(snapshot_id)
    
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snapshot not found",
        )
    
    return SnapshotResponse.from_model(snapshot)


@router.post("/{snapshot_id}/restore")
async def restore_snapshot(
    snapshot_id: str,
    request: RestoreSnapshotRequest,
    snapshot_service: SnapshotService = Depends(get_snapshot_service),
):
    """Restore a device from a snapshot."""
    profile = await snapshot_service.restore(
        snapshot_id=snapshot_id,
        new_profile_name=request.new_profile_name,
    )
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to restore from snapshot",
        )
    
    return {
        "message": "Profile restored successfully",
        "profile_id": str(profile.id),
        "profile_name": profile.name,
    }


@router.delete("/{snapshot_id}")
async def delete_snapshot(
    snapshot_id: str,
    snapshot_service: SnapshotService = Depends(get_snapshot_service),
):
    """Delete a snapshot."""
    success = await snapshot_service.delete(snapshot_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snapshot not found or failed to delete",
        )
    
    return {"message": "Snapshot deleted successfully"}