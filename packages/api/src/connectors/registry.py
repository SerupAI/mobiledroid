"""Connector registry for managing available connectors."""

from typing import TypeVar

import structlog

from src.connectors.base import (
    Connector,
    ConnectorType,
    ProxyConnector,
)

logger = structlog.get_logger()

T = TypeVar("T", bound=Connector)


class ConnectorRegistry:
    """Registry for managing service connectors.

    The registry maintains a collection of available connectors
    and provides methods for querying and managing them.
    """

    def __init__(self) -> None:
        self._connectors: dict[str, Connector] = {}

    def register(self, connector: Connector) -> None:
        """Register a connector.

        Args:
            connector: The connector instance to register
        """
        if connector.id in self._connectors:
            logger.warning(
                "Connector already registered, overwriting",
                connector_id=connector.id
            )

        self._connectors[connector.id] = connector
        logger.info(
            "Connector registered",
            connector_id=connector.id,
            connector_type=connector.connector_type.value
        )

    def unregister(self, connector_id: str) -> Connector | None:
        """Unregister a connector by ID.

        Args:
            connector_id: The connector ID to remove

        Returns:
            The removed connector, or None if not found
        """
        connector = self._connectors.pop(connector_id, None)
        if connector:
            logger.info("Connector unregistered", connector_id=connector_id)
        return connector

    def get(self, connector_id: str) -> Connector | None:
        """Get a connector by ID.

        Args:
            connector_id: The connector ID to look up

        Returns:
            The connector, or None if not found
        """
        return self._connectors.get(connector_id)

    def get_all(self) -> list[Connector]:
        """Get all registered connectors."""
        return list(self._connectors.values())

    def get_by_type(self, connector_type: ConnectorType) -> list[Connector]:
        """Get all connectors of a specific type.

        Args:
            connector_type: The type of connectors to retrieve

        Returns:
            List of matching connectors
        """
        return [
            c for c in self._connectors.values()
            if c.connector_type == connector_type
        ]

    def get_proxy_connectors(self) -> list[ProxyConnector]:
        """Get all proxy connectors."""
        return [
            c for c in self._connectors.values()
            if isinstance(c, ProxyConnector)
        ]

    def get_enabled_proxy_connector(self) -> ProxyConnector | None:
        """Get the first enabled proxy connector.

        Returns:
            The enabled proxy connector, or None
        """
        for connector in self.get_proxy_connectors():
            if connector.is_enabled:
                return connector
        return None

    def get_enabled(self) -> list[Connector]:
        """Get all enabled connectors."""
        return [c for c in self._connectors.values() if c.is_enabled]

    def configure(self, connector_id: str, config: dict) -> bool:
        """Configure a connector.

        Args:
            connector_id: The connector to configure
            config: Configuration dictionary

        Returns:
            True if successful, False if connector not found
        """
        connector = self.get(connector_id)
        if not connector:
            return False

        connector.configure(config)
        logger.info(
            "Connector configured",
            connector_id=connector_id,
            config_keys=list(config.keys())
        )
        return True

    def enable(self, connector_id: str) -> bool:
        """Enable a connector.

        Args:
            connector_id: The connector to enable

        Returns:
            True if successful, False if connector not found
        """
        connector = self.get(connector_id)
        if not connector:
            return False

        connector.enable()
        logger.info("Connector enabled", connector_id=connector_id)
        return True

    def disable(self, connector_id: str) -> bool:
        """Disable a connector.

        Args:
            connector_id: The connector to disable

        Returns:
            True if successful, False if connector not found
        """
        connector = self.get(connector_id)
        if not connector:
            return False

        connector.disable()
        logger.info("Connector disabled", connector_id=connector_id)
        return True


# Global registry instance
connector_registry = ConnectorRegistry()
