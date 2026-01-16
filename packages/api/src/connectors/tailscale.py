"""Tailscale connector for residential IP routing.

Tailscale provides SOCKS5 proxy functionality when connected
to a tailnet with an exit node. This allows routing container
traffic through your home network for residential IP addresses.

Architecture:
    - Tailscale runs in a Docker container (tailscale-proxy)
    - The container exposes SOCKS5 proxy on port 1055
    - Android containers route traffic through this proxy
    - EC2 host keeps its public IP (not affected by exit node)
"""

import asyncio
import json
import shutil
from typing import Any

import structlog

from src.connectors.base import (
    ConnectorStatus,
    ProxyConfig,
    ProxyConnector,
)

logger = structlog.get_logger()

# Container mode: Tailscale runs in Docker container
CONTAINER_MODE = True
CONTAINER_NAME = "tailscale-proxy"


class TailscaleConnector(ProxyConnector):
    """Tailscale exit node connector.

    Routes Android container traffic through a Tailscale exit node,
    providing residential IP addresses while EC2 keeps its public IP.

    Architecture (Container Mode - Default):
        - Tailscale runs in tailscale-proxy Docker container
        - Provides SOCKS5 proxy at tailscale-proxy:1055
        - Only Android containers use the residential IP
        - EC2 host maintains its public IP for SSH/API access

    Configuration:
        exit_node: Hostname of the exit node (e.g., "desktop-tp59f6k")
        tailnet: Optional tailnet name
        auth_key: Auth key for container auto-join
        container_mode: Use Docker container (default: true)

    Usage:
        1. Set up an exit node at home (PC, Raspberry Pi, etc.)
        2. Generate auth key at admin.tailscale.com/settings/keys
        3. Set TAILSCALE_AUTH_KEY and TAILSCALE_EXIT_NODE env vars
        4. Start with: docker compose --profile proxy up -d
    """

    id = "tailscale"
    name = "Tailscale Exit Node"
    description = "Route Android traffic through your home network via Tailscale"

    # Tailscale proxy ports
    SOCKS5_PORT = 1055  # For apps that support SOCKS5
    HTTP_PROXY_PORT = 8080  # For Android global proxy (HTTP only)

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._exit_node = config.get("exit_node") if config else None
        self._tailnet = config.get("tailnet") if config else None
        self._container_mode = config.get("container_mode", CONTAINER_MODE) if config else CONTAINER_MODE

    @property
    def exit_node(self) -> str | None:
        """Get configured exit node hostname."""
        return self._config.get("exit_node", self._exit_node)

    @property
    def tailnet(self) -> str | None:
        """Get configured tailnet name."""
        return self._config.get("tailnet", self._tailnet)

    def configure(self, config: dict[str, Any]) -> None:
        """Update configuration."""
        super().configure(config)
        if "exit_node" in config:
            self._exit_node = config["exit_node"]
        if "tailnet" in config:
            self._tailnet = config["tailnet"]

    async def get_status(self) -> ConnectorStatus:
        """Get Tailscale connection status.

        In container mode, checks the Docker container status.
        In host mode, checks the host Tailscale installation.
        """
        if self._container_mode:
            return await self._get_container_status()
        else:
            return await self._get_host_status()

    async def _get_container_status(self) -> ConnectorStatus:
        """Get status of Tailscale Docker container."""
        try:
            # Check if container is running
            result = await self._run_command(
                f"docker inspect --format='{{{{.State.Running}}}}' {CONTAINER_NAME}"
            )
            is_running = result.strip().lower() == "true"

            if not is_running:
                return ConnectorStatus(
                    connected=False,
                    healthy=False,
                    message="Tailscale container not running. Start with: docker compose --profile proxy up -d",
                    details={"container_mode": True, "container_name": CONTAINER_NAME}
                )

            # Get Tailscale status from container
            result = await self._run_command(
                f"docker exec {CONTAINER_NAME} tailscale status --json"
            )
            status = json.loads(result)

            backend_state = status.get("BackendState", "Unknown")
            is_connected = backend_state == "Running"

            # Check exit node status
            exit_node_status = status.get("ExitNodeStatus")
            current_exit_node = None
            if exit_node_status:
                current_exit_node = exit_node_status.get("TailscaleIPs", [None])[0]

            # Get Tailscale IP
            tailscale_ips = status.get("TailscaleIPs", [])
            our_ip = tailscale_ips[0] if tailscale_ips else None

            return ConnectorStatus(
                connected=is_connected,
                healthy=is_connected and bool(current_exit_node),
                message=f"Container connected via exit node" if current_exit_node else "Container connected (no exit node)",
                details={
                    "container_mode": True,
                    "container_name": CONTAINER_NAME,
                    "backend_state": backend_state,
                    "exit_node": current_exit_node,
                    "tailscale_ip": our_ip,
                    "configured_exit_node": self.exit_node,
                }
            )

        except Exception as e:
            logger.error("Failed to get Tailscale container status", error=str(e))
            return ConnectorStatus(
                connected=False,
                healthy=False,
                message=f"Container error: {str(e)}",
                details={"container_mode": True}
            )

    async def _get_host_status(self) -> ConnectorStatus:
        """Get status of host Tailscale installation (legacy mode)."""
        if not self._is_tailscale_installed():
            return ConnectorStatus(
                connected=False,
                healthy=False,
                message="Tailscale is not installed on host",
                details={"container_mode": False}
            )

        try:
            result = await self._run_command("tailscale status --json")
            status = json.loads(result)

            backend_state = status.get("BackendState", "Unknown")
            is_running = backend_state == "Running"

            # Check exit node status
            exit_node_status = status.get("ExitNodeStatus")
            current_exit_node = None
            if exit_node_status:
                current_exit_node = exit_node_status.get("TailscaleIPs", [None])[0]

            # Get our Tailscale IP
            tailscale_ips = status.get("TailscaleIPs", [])
            our_ip = tailscale_ips[0] if tailscale_ips else None

            return ConnectorStatus(
                connected=is_running,
                healthy=is_running and bool(current_exit_node),
                message=f"Host connected via exit node" if current_exit_node else "Host connected (no exit node)",
                details={
                    "container_mode": False,
                    "backend_state": backend_state,
                    "exit_node": current_exit_node,
                    "tailscale_ip": our_ip,
                    "configured_exit_node": self.exit_node,
                }
            )

        except Exception as e:
            logger.error("Failed to get Tailscale host status", error=str(e))
            return ConnectorStatus(
                connected=False,
                healthy=False,
                message=f"Host error: {str(e)}",
                details={"container_mode": False}
            )

    async def test_connection(self) -> bool:
        """Test Tailscale connectivity."""
        status = await self.get_status()
        return status.connected

    async def get_proxy_config(self) -> ProxyConfig | None:
        """Get HTTP proxy configuration for Tailscale.

        In container mode, returns the Docker container hostname.
        Android containers connect to tailscale-proxy:8080 for HTTP proxy.

        Note: Android's global HTTP proxy only supports HTTP, not SOCKS5.
        The tailscale-proxy container runs both SOCKS5 (1055) and HTTP (8080) proxies.
        """
        if not self.is_enabled:
            return None

        status = await self.get_status()
        if not status.connected:
            logger.warning("Tailscale not connected, cannot provide proxy")
            return None

        # Determine proxy host based on mode
        if self._container_mode:
            # Use Docker container name (containers on same network)
            proxy_host = CONTAINER_NAME
        else:
            # Use host.docker.internal for host-mode Tailscale
            proxy_host = "host.docker.internal"

        # Return HTTP proxy config (Android's global proxy only supports HTTP)
        # Traffic flows: Android Container -> HTTP Proxy -> Tailscale Container -> Exit Node -> Internet
        return ProxyConfig(
            type="http",
            host=proxy_host,
            port=self.HTTP_PROXY_PORT,
            enabled=True,
        )

    async def connect(self, exit_node: str | None = None) -> bool:
        """Connect to Tailscale and set exit node.

        Args:
            exit_node: Exit node hostname (uses configured if not specified)

        Returns:
            True if successful
        """
        node = exit_node or self.exit_node
        if not node:
            logger.error("No exit node configured")
            return False

        try:
            # Connect to Tailscale with exit node
            cmd = f"tailscale up --exit-node={node} --accept-routes"
            await self._run_command(cmd)

            logger.info("Connected to Tailscale exit node", exit_node=node)
            return True

        except Exception as e:
            logger.error("Failed to connect to Tailscale", error=str(e))
            return False

    async def disconnect(self) -> bool:
        """Disconnect from exit node (stay on tailnet).

        Returns:
            True if successful
        """
        try:
            # Remove exit node but stay connected to tailnet
            await self._run_command("tailscale up --exit-node=")
            logger.info("Disconnected from Tailscale exit node")
            return True

        except Exception as e:
            logger.error("Failed to disconnect from Tailscale", error=str(e))
            return False

    async def list_exit_nodes(self) -> list[dict[str, Any]]:
        """List available exit nodes on the tailnet.

        Returns:
            List of exit node information
        """
        if not self._is_tailscale_installed():
            return []

        try:
            result = await self._run_command("tailscale status --json")
            status = json.loads(result)

            nodes = []
            peers = status.get("Peer", {})

            for peer_id, peer_info in peers.items():
                # Check if peer is an exit node
                if peer_info.get("ExitNode") or peer_info.get("ExitNodeOption"):
                    nodes.append({
                        "id": peer_id,
                        "hostname": peer_info.get("HostName", "Unknown"),
                        "dns_name": peer_info.get("DNSName", ""),
                        "ips": peer_info.get("TailscaleIPs", []),
                        "online": peer_info.get("Online", False),
                        "active": peer_info.get("ExitNode", False),
                    })

            return nodes

        except Exception as e:
            logger.error("Failed to list exit nodes", error=str(e))
            return []

    async def get_public_ip(self) -> str | None:
        """Get current public IP (to verify exit node is working).

        Returns:
            Public IP address or None
        """
        try:
            # Use curl to check public IP
            result = await self._run_command(
                "curl -s --max-time 5 https://ifconfig.me"
            )
            return result.strip() if result else None
        except Exception:
            return None

    def _is_tailscale_installed(self) -> bool:
        """Check if Tailscale is installed on the system."""
        return shutil.which("tailscale") is not None

    async def _run_command(self, cmd: str) -> str:
        """Run a shell command and return output.

        Args:
            cmd: Command to run

        Returns:
            Command output

        Raises:
            RuntimeError: If command fails
        """
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"Command failed: {error}")

        return stdout.decode() if stdout else ""
