"""Service connectors for MobileDroid.

Connectors provide pluggable integrations for:
- Proxy services (Tailscale, Bright Data, Oxylabs)
- Storage services (MinIO, S3)
- LLM routing (LiteLLM, Ollama)
"""

from src.connectors.base import (
    Connector,
    ConnectorStatus,
    ConnectorType,
    ProxyConnector,
)
from src.connectors.registry import connector_registry
from src.connectors.tailscale import TailscaleConnector

__all__ = [
    "Connector",
    "ConnectorStatus",
    "ConnectorType",
    "ProxyConnector",
    "TailscaleConnector",
    "connector_registry",
]
