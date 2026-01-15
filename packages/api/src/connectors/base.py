"""Base classes for service connectors."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel


class ConnectorType(str, Enum):
    """Types of connectors."""
    PROXY = "proxy"
    STORAGE = "storage"
    LLM = "llm"


class ConnectorStatus(BaseModel):
    """Status of a connector."""
    connected: bool = False
    healthy: bool = False
    message: str | None = None
    details: dict[str, Any] = {}


class ProxyConfig(BaseModel):
    """Proxy configuration provided by a connector."""
    type: str  # "http" or "socks5"
    host: str
    port: int
    username: str | None = None
    password: str | None = None
    enabled: bool = True


class Connector(ABC):
    """Base class for all service connectors.

    Connectors are pluggable integrations that provide services
    to MobileDroid without creating hard dependencies.
    """

    # Connector identification
    id: str
    name: str
    description: str
    connector_type: ConnectorType

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize connector with optional configuration."""
        self._config = config or {}
        self._enabled = False

    @property
    def is_enabled(self) -> bool:
        """Check if connector is enabled."""
        return self._enabled

    def enable(self) -> None:
        """Enable the connector."""
        self._enabled = True

    def disable(self) -> None:
        """Disable the connector."""
        self._enabled = False

    def configure(self, config: dict[str, Any]) -> None:
        """Update connector configuration."""
        self._config.update(config)

    def get_config(self) -> dict[str, Any]:
        """Get current configuration."""
        return self._config.copy()

    @abstractmethod
    async def get_status(self) -> ConnectorStatus:
        """Get current status of the connector."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the connector can connect successfully."""
        pass

    def to_dict(self) -> dict[str, Any]:
        """Serialize connector to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.connector_type.value,
            "enabled": self._enabled,
            "config": self._config,
        }


class ProxyConnector(Connector):
    """Base class for proxy connectors.

    Proxy connectors provide proxy configuration for routing
    container traffic through external services (Tailscale,
    residential proxies, etc.)
    """

    connector_type = ConnectorType.PROXY

    @abstractmethod
    async def get_proxy_config(self) -> ProxyConfig | None:
        """Get proxy configuration for container injection.

        Returns None if proxy is not available/configured.
        """
        pass

    async def connect(self) -> bool:
        """Connect to the proxy service.

        Override in subclasses if connection requires setup.
        """
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the proxy service.

        Override in subclasses if disconnection requires cleanup.
        """
        return True


class StorageConnector(Connector):
    """Base class for storage connectors (future)."""

    connector_type = ConnectorType.STORAGE

    @abstractmethod
    async def upload(self, key: str, data: bytes) -> str:
        """Upload data and return URL/path."""
        pass

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """Download data by key."""
        pass
