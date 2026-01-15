"""Profile schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ScreenConfig(BaseModel):
    """Screen configuration."""

    width: int = Field(default=1080, ge=320, le=3840)
    height: int = Field(default=2400, ge=480, le=3840)
    dpi: int = Field(default=420, ge=120, le=640)


class DeviceFingerprint(BaseModel):
    """Device fingerprint configuration."""

    # Required fields
    model: str = Field(..., min_length=1, max_length=100, examples=["Pixel 7"])
    brand: str = Field(..., min_length=1, max_length=50, examples=["google"])
    manufacturer: str = Field(..., min_length=1, max_length=50, examples=["Google"])

    # Build info
    build_fingerprint: str = Field(
        ...,
        min_length=1,
        examples=["google/panther/panther:14/UP1A.231005.007/10754064:user/release-keys"],
    )
    android_version: str = Field(default="14", examples=["14"])
    sdk_version: str = Field(default="34", examples=["34"])

    # Hardware
    hardware: str = Field(default="panther", examples=["panther", "qcom"])
    board: str = Field(default="panther", examples=["panther", "kalama"])
    product: str = Field(default="", examples=["panther"])

    # Screen
    screen: ScreenConfig = Field(default_factory=ScreenConfig)

    # Optional identifiers (auto-generated if not provided)
    android_id: str | None = Field(default=None, max_length=16)
    serial: str | None = Field(default=None, max_length=20)

    # Locale settings
    timezone: str = Field(default="America/New_York")
    locale: str = Field(default="en_US")


class ProxyConfig(BaseModel):
    """Proxy configuration."""

    type: Literal["none", "http", "socks5"] = "none"
    host: str | None = Field(default=None, max_length=255)
    port: int | None = Field(default=None, ge=1, le=65535)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=255)


class ProfileCreate(BaseModel):
    """Schema for creating a profile."""

    name: str = Field(..., min_length=1, max_length=255)
    fingerprint: DeviceFingerprint
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    proxy_connector_id: str | None = Field(
        default=None,
        description="Service connector ID for proxy (e.g., 'tailscale'). Overrides manual proxy config."
    )


class ProfileUpdate(BaseModel):
    """Schema for updating a profile."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    fingerprint: DeviceFingerprint | None = None
    proxy: ProxyConfig | None = None
    proxy_connector_id: str | None = Field(
        default=None,
        description="Service connector ID for proxy (e.g., 'tailscale'). Set to empty string to clear."
    )


class ProfileResponse(BaseModel):
    """Schema for profile response."""

    id: str
    name: str
    status: str
    container_id: str | None
    adb_port: int | None
    fingerprint: dict
    proxy: dict
    proxy_connector_id: str | None = None
    created_at: datetime
    updated_at: datetime
    last_started_at: datetime | None
    last_stopped_at: datetime | None

    class Config:
        from_attributes = True


class ProfileListResponse(BaseModel):
    """Schema for profile list response."""

    profiles: list[ProfileResponse]
    total: int
