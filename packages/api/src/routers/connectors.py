"""API router for service connectors."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db
from src.schemas.connector import (
    ConnectorConfigureRequest,
    ConnectorListResponse,
    ConnectorResponse,
    ConnectorStatusResponse,
    PublicIPResponse,
    TailscaleConfigRequest,
    TailscaleConnectRequest,
    TailscaleExitNodeResponse,
    TailscaleNodesResponse,
)
from src.services.connector_service import ConnectorService

router = APIRouter(prefix="/connectors", tags=["connectors"])


async def get_service(db: AsyncSession = Depends(get_db)) -> ConnectorService:
    """Get connector service dependency."""
    return ConnectorService(db)


# === General Connector Endpoints ===


@router.get("", response_model=ConnectorListResponse)
async def list_connectors(
    service: ConnectorService = Depends(get_service),
) -> ConnectorListResponse:
    """List all available connectors."""
    connectors = await service.list_connectors()
    return ConnectorListResponse(
        connectors=[
            ConnectorResponse(
                id=c.id,
                name=c.name,
                description=c.description,
                type=c.connector_type.value,
                enabled=c.is_enabled,
                config=c.get_config(),
            )
            for c in connectors
        ],
        total=len(connectors),
    )


@router.get("/{connector_id}", response_model=ConnectorResponse)
async def get_connector(
    connector_id: str,
    service: ConnectorService = Depends(get_service),
) -> ConnectorResponse:
    """Get a specific connector by ID."""
    connector = await service.get_connector(connector_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector '{connector_id}' not found",
        )
    return ConnectorResponse(
        id=connector.id,
        name=connector.name,
        description=connector.description,
        type=connector.connector_type.value,
        enabled=connector.is_enabled,
        config=connector.get_config(),
    )


@router.get("/{connector_id}/status", response_model=ConnectorStatusResponse)
async def get_connector_status(
    connector_id: str,
    service: ConnectorService = Depends(get_service),
) -> ConnectorStatusResponse:
    """Get status of a specific connector."""
    conn_status = await service.get_connector_status(connector_id)
    if not conn_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector '{connector_id}' not found",
        )
    return ConnectorStatusResponse(
        connected=conn_status.connected,
        healthy=conn_status.healthy,
        message=conn_status.message,
        details=conn_status.details,
    )


@router.post("/{connector_id}/configure", response_model=ConnectorResponse)
async def configure_connector(
    connector_id: str,
    request: ConnectorConfigureRequest,
    service: ConnectorService = Depends(get_service),
) -> ConnectorResponse:
    """Configure a connector."""
    connector = await service.configure_connector(connector_id, request.config)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector '{connector_id}' not found",
        )
    return ConnectorResponse(
        id=connector.id,
        name=connector.name,
        description=connector.description,
        type=connector.connector_type.value,
        enabled=connector.is_enabled,
        config=connector.get_config(),
    )


@router.post("/{connector_id}/enable", response_model=ConnectorResponse)
async def enable_connector(
    connector_id: str,
    service: ConnectorService = Depends(get_service),
) -> ConnectorResponse:
    """Enable a connector."""
    connector = await service.enable_connector(connector_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector '{connector_id}' not found",
        )
    return ConnectorResponse(
        id=connector.id,
        name=connector.name,
        description=connector.description,
        type=connector.connector_type.value,
        enabled=connector.is_enabled,
        config=connector.get_config(),
    )


@router.post("/{connector_id}/disable", response_model=ConnectorResponse)
async def disable_connector(
    connector_id: str,
    service: ConnectorService = Depends(get_service),
) -> ConnectorResponse:
    """Disable a connector."""
    connector = await service.disable_connector(connector_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector '{connector_id}' not found",
        )
    return ConnectorResponse(
        id=connector.id,
        name=connector.name,
        description=connector.description,
        type=connector.connector_type.value,
        enabled=connector.is_enabled,
        config=connector.get_config(),
    )


# === Tailscale-specific Endpoints ===


@router.post("/tailscale/configure", response_model=ConnectorResponse)
async def configure_tailscale(
    request: TailscaleConfigRequest,
    service: ConnectorService = Depends(get_service),
) -> ConnectorResponse:
    """Configure Tailscale connector."""
    config = {}
    if request.exit_node:
        config["exit_node"] = request.exit_node
    if request.tailnet:
        config["tailnet"] = request.tailnet

    connector = await service.configure_connector("tailscale", config)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tailscale connector not found",
        )
    return ConnectorResponse(
        id=connector.id,
        name=connector.name,
        description=connector.description,
        type=connector.connector_type.value,
        enabled=connector.is_enabled,
        config=connector.get_config(),
    )


@router.post("/tailscale/connect")
async def tailscale_connect(
    request: TailscaleConnectRequest | None = None,
    service: ConnectorService = Depends(get_service),
) -> dict:
    """Connect to Tailscale exit node."""
    exit_node = request.exit_node if request else None
    success = await service.tailscale_connect(exit_node)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect to Tailscale exit node",
        )

    return {"success": True, "message": "Connected to Tailscale exit node"}


@router.post("/tailscale/disconnect")
async def tailscale_disconnect(
    service: ConnectorService = Depends(get_service),
) -> dict:
    """Disconnect from Tailscale exit node."""
    success = await service.tailscale_disconnect()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect from Tailscale exit node",
        )

    return {"success": True, "message": "Disconnected from Tailscale exit node"}


@router.get("/tailscale/nodes", response_model=TailscaleNodesResponse)
async def list_tailscale_exit_nodes(
    service: ConnectorService = Depends(get_service),
) -> TailscaleNodesResponse:
    """List available Tailscale exit nodes."""
    nodes = await service.tailscale_list_exit_nodes()
    return TailscaleNodesResponse(
        nodes=[
            TailscaleExitNodeResponse(
                id=node["id"],
                hostname=node["hostname"],
                dns_name=node["dns_name"],
                ips=node["ips"],
                online=node["online"],
                active=node["active"],
            )
            for node in nodes
        ]
    )


@router.get("/tailscale/ip", response_model=PublicIPResponse)
async def get_tailscale_public_ip(
    service: ConnectorService = Depends(get_service),
) -> PublicIPResponse:
    """Get current public IP (to verify exit node is working)."""
    ip = await service.tailscale_get_public_ip()
    conn_status = await service.get_connector_status("tailscale")

    exit_node_active = False
    if conn_status and conn_status.details:
        exit_node_active = bool(conn_status.details.get("exit_node"))

    return PublicIPResponse(ip=ip, exit_node_active=exit_node_active)
