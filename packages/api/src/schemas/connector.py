"""Schemas for service connectors."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ConnectorStatusResponse(BaseModel):
    """Status response for a connector."""
    connected: bool
    healthy: bool
    message: str | None = None
    details: dict[str, Any] = {}


class ConnectorResponse(BaseModel):
    """Response schema for a connector."""
    id: str
    name: str
    description: str | None = None
    type: str
    enabled: bool
    config: dict[str, Any] = {}
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ConnectorListResponse(BaseModel):
    """Response schema for listing connectors."""
    connectors: list[ConnectorResponse]
    total: int


class ConnectorConfigureRequest(BaseModel):
    """Request schema for configuring a connector."""
    config: dict[str, Any] = Field(
        ...,
        description="Configuration dictionary for the connector"
    )


class ConnectorEnableRequest(BaseModel):
    """Request schema for enabling/disabling a connector."""
    enabled: bool = True


# Tailscale-specific schemas

class TailscaleConfigRequest(BaseModel):
    """Request schema for Tailscale configuration."""
    exit_node: str | None = Field(
        None,
        description="Hostname of the exit node (e.g., 'home-pi')"
    )
    tailnet: str | None = Field(
        None,
        description="Tailnet domain name (optional)"
    )


class TailscaleConnectRequest(BaseModel):
    """Request schema for connecting to Tailscale exit node."""
    exit_node: str | None = Field(
        None,
        description="Exit node to connect to (uses configured if not specified)"
    )


class TailscaleExitNodeResponse(BaseModel):
    """Response schema for a Tailscale exit node."""
    id: str
    hostname: str
    dns_name: str
    ips: list[str]
    online: bool
    active: bool


class TailscaleNodesResponse(BaseModel):
    """Response schema for listing Tailscale exit nodes."""
    nodes: list[TailscaleExitNodeResponse]


class PublicIPResponse(BaseModel):
    """Response schema for public IP check."""
    ip: str | None
    exit_node_active: bool
