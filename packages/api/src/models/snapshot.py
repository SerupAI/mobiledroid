"""Snapshot model for device state persistence."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import Base


class SnapshotStatus(str, Enum):
    """Snapshot status."""
    CREATING = "creating"
    READY = "ready"
    FAILED = "failed"
    RESTORING = "restoring"


class Snapshot(Base):
    """Snapshot of a device state."""
    
    __tablename__ = "snapshots"
    
    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Profile relationship
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    profile = relationship("Profile", back_populates="snapshots")
    
    # Snapshot metadata
    status = Column(SQLEnum(SnapshotStatus), default=SnapshotStatus.CREATING, nullable=False)
    size_bytes = Column(Integer, nullable=True)
    android_version = Column(String(10), nullable=False)
    device_model = Column(String(100), nullable=False)
    
    # Storage location
    storage_path = Column(String(500), nullable=True)  # S3/MinIO path
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "profile_id": str(self.profile_id),
            "status": self.status,
            "size_bytes": self.size_bytes,
            "android_version": self.android_version,
            "device_model": self.device_model,
            "storage_path": self.storage_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }