"""Tailscale connector for residential IP routing.

Tailscale provides SOCKS5 proxy functionality when connected
to a tailnet with an exit node. This allows routing container
traffic through your home network for residential IP addresses.
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


class TailscaleConnector(ProxyConnector):
    """Tailscale exit node connector.

    Routes container traffic through a Tailscale exit node,
    providing residential IP addresses for better evasion.

    Configuration:
        exit_node: Hostname of the exit node (e.g., "home-pi")
        tailnet: Optional tailnet name
        auth_key: Optional auth key for auto-join

    Usage:
        1. Install Tailscale on the host machine
        2. Set up an exit node at home (Raspberry Pi, etc.)
        3. Configure this connector with the exit node hostname
        4. Enable the connector to route traffic through home IP
    """

    id = "tailscale"
    name = "Tailscale Exit Node"
    description = "Route traffic through your home network via Tailscale"

    # Tailscale SOCKS5 proxy port (when using --socks5-server)
    SOCKS5_PORT = 1055

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._exit_node = config.get("exit_node") if config else None
        self._tailnet = config.get("tailnet") if config else None

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
        """Get Tailscale connection status."""
        if not self._is_tailscale_installed():
            return ConnectorStatus(
                connected=False,
                healthy=False,
                message="Tailscale is not installed",
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
                message=f"Connected via exit node" if current_exit_node else "Connected (no exit node)",
                details={
                    "backend_state": backend_state,
                    "exit_node": current_exit_node,
                    "tailscale_ip": our_ip,
                    "configured_exit_node": self.exit_node,
                }
            )

        except Exception as e:
            logger.error("Failed to get Tailscale status", error=str(e))
            return ConnectorStatus(
                connected=False,
                healthy=False,
                message=f"Error: {str(e)}",
            )

    async def test_connection(self) -> bool:
        """Test Tailscale connectivity."""
        status = await self.get_status()
        return status.connected

    async def get_proxy_config(self) -> ProxyConfig | None:
        """Get SOCKS5 proxy configuration for Tailscale.

        Note: This requires Tailscale to be running with
        --socks5-server flag for SOCKS5 proxy support.
        """
        if not self.is_enabled:
            return None

        status = await self.get_status()
        if not status.connected:
            logger.warning("Tailscale not connected, cannot provide proxy")
            return None

        # Return SOCKS5 proxy config
        # Traffic flows: Container -> SOCKS5 -> Tailscale -> Exit Node -> Internet
        return ProxyConfig(
            type="socks5",
            host="host.docker.internal",  # Access host from container
            port=self.SOCKS5_PORT,
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
