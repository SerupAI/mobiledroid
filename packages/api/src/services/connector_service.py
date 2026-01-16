"""Connector service for managing service connectors."""

from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.connectors import (
    Connector,
    ConnectorStatus,
    ProxyConnector,
    TailscaleConnector,
    connector_registry,
)
from src.connectors.base import ProxyConfig
from src.models.connector import ConnectorType as DBConnectorType
from src.models.connector import ServiceConnector

logger = structlog.get_logger()


class ConnectorService:
    """Service for managing connectors and their persistence.

    This service bridges the connector framework (in-memory logic)
    with database persistence for configurations.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def initialize_connectors(self) -> None:
        """Initialize connectors from database and register them.

        Called at startup to load saved configurations.
        """
        # Register built-in connectors
        self._register_builtin_connectors()

        # Load configurations from database
        await self._load_connector_configs()

    def _register_builtin_connectors(self) -> None:
        """Register built-in connector implementations."""
        # Tailscale connector - enabled by default if container is available
        if not connector_registry.get("tailscale"):
            tailscale = TailscaleConnector()
            tailscale.enable()  # Enable by default
            connector_registry.register(tailscale)

        # Future: Register other built-in connectors
        # connector_registry.register(BrightDataConnector())

    async def _load_connector_configs(self) -> None:
        """Load connector configurations from database."""
        result = await self.db.execute(select(ServiceConnector))
        db_connectors = result.scalars().all()

        for db_connector in db_connectors:
            connector = connector_registry.get(db_connector.id)
            if connector:
                # Apply saved configuration
                connector.configure(db_connector.config)
                if db_connector.enabled:
                    connector.enable()
                else:
                    connector.disable()

                logger.info(
                    "Loaded connector config from database",
                    connector_id=db_connector.id,
                    enabled=db_connector.enabled,
                )

    async def list_connectors(self) -> list[Connector]:
        """List all registered connectors."""
        return connector_registry.get_all()

    async def get_connector(self, connector_id: str) -> Connector | None:
        """Get a specific connector by ID."""
        return connector_registry.get(connector_id)

    async def get_connector_status(self, connector_id: str) -> ConnectorStatus | None:
        """Get status of a specific connector."""
        connector = connector_registry.get(connector_id)
        if not connector:
            return None
        return await connector.get_status()

    async def configure_connector(
        self,
        connector_id: str,
        config: dict[str, Any],
    ) -> Connector | None:
        """Configure a connector and persist to database.

        Args:
            connector_id: The connector to configure
            config: Configuration dictionary

        Returns:
            The configured connector, or None if not found
        """
        connector = connector_registry.get(connector_id)
        if not connector:
            return None

        # Update in-memory configuration
        connector.configure(config)

        # Persist to database
        await self._upsert_connector_db(connector)

        logger.info(
            "Connector configured",
            connector_id=connector_id,
            config_keys=list(config.keys()),
        )

        return connector

    async def enable_connector(self, connector_id: str) -> Connector | None:
        """Enable a connector and persist to database.

        Args:
            connector_id: The connector to enable

        Returns:
            The enabled connector, or None if not found
        """
        connector = connector_registry.get(connector_id)
        if not connector:
            return None

        connector.enable()
        await self._upsert_connector_db(connector)

        logger.info("Connector enabled", connector_id=connector_id)
        return connector

    async def disable_connector(self, connector_id: str) -> Connector | None:
        """Disable a connector and persist to database.

        Args:
            connector_id: The connector to disable

        Returns:
            The disabled connector, or None if not found
        """
        connector = connector_registry.get(connector_id)
        if not connector:
            return None

        connector.disable()
        await self._upsert_connector_db(connector)

        logger.info("Connector disabled", connector_id=connector_id)
        return connector

    async def get_proxy_config_for_profile(
        self,
        proxy_connector_id: str | None = None,
    ) -> ProxyConfig | None:
        """Get proxy configuration for a profile.

        If proxy_connector_id is specified, use that connector.
        Otherwise, use the first enabled proxy connector.

        Args:
            proxy_connector_id: Optional specific connector ID

        Returns:
            ProxyConfig or None if no proxy available
        """
        if proxy_connector_id:
            connector = connector_registry.get(proxy_connector_id)
            if connector and isinstance(connector, ProxyConnector):
                return await connector.get_proxy_config()
            return None

        # Use first enabled proxy connector
        proxy_connector = connector_registry.get_enabled_proxy_connector()
        if proxy_connector:
            return await proxy_connector.get_proxy_config()

        return None

    async def _upsert_connector_db(self, connector: Connector) -> ServiceConnector:
        """Insert or update connector in database.

        Args:
            connector: The connector to persist

        Returns:
            The database record
        """
        # Check if exists
        result = await self.db.execute(
            select(ServiceConnector).where(ServiceConnector.id == connector.id)
        )
        db_connector = result.scalar_one_or_none()

        if db_connector:
            # Update existing
            db_connector.name = connector.name
            db_connector.description = connector.description
            db_connector.enabled = connector.is_enabled
            db_connector.config = connector.get_config()
        else:
            # Create new
            db_connector = ServiceConnector(
                id=connector.id,
                name=connector.name,
                description=connector.description,
                connector_type=DBConnectorType(connector.connector_type.value),
                enabled=connector.is_enabled,
                config=connector.get_config(),
            )
            self.db.add(db_connector)

        await self.db.flush()
        return db_connector

    # Tailscale-specific methods

    async def tailscale_connect(self, exit_node: str | None = None) -> bool:
        """Connect to Tailscale exit node.

        Args:
            exit_node: Exit node hostname (uses configured if not specified)

        Returns:
            True if successful
        """
        connector = connector_registry.get("tailscale")
        if not connector or not isinstance(connector, TailscaleConnector):
            logger.error("Tailscale connector not found")
            return False

        return await connector.connect(exit_node)

    async def tailscale_disconnect(self) -> bool:
        """Disconnect from Tailscale exit node.

        Returns:
            True if successful
        """
        connector = connector_registry.get("tailscale")
        if not connector or not isinstance(connector, TailscaleConnector):
            logger.error("Tailscale connector not found")
            return False

        return await connector.disconnect()

    async def tailscale_list_exit_nodes(self) -> list[dict[str, Any]]:
        """List available Tailscale exit nodes.

        Returns:
            List of exit node info
        """
        connector = connector_registry.get("tailscale")
        if not connector or not isinstance(connector, TailscaleConnector):
            return []

        return await connector.list_exit_nodes()

    async def tailscale_get_public_ip(self) -> str | None:
        """Get current public IP via Tailscale.

        Returns:
            Public IP address
        """
        connector = connector_registry.get("tailscale")
        if not connector or not isinstance(connector, TailscaleConnector):
            return None

        return await connector.get_public_ip()


# Dependency function
async def get_connector_service(db: AsyncSession) -> ConnectorService:
    """Get connector service dependency."""
    return ConnectorService(db)
