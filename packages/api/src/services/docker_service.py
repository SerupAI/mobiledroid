"""Docker service for managing redroid containers."""

import asyncio
from typing import Any

import docker
from docker.models.containers import Container
import structlog

from src.config import settings
from src.services.fingerprint_service import FingerprintService

logger = structlog.get_logger()


class DockerService:
    """Service for managing Docker containers."""

    def __init__(self, fingerprint_service: FingerprintService):
        self.client = docker.from_env()
        self.fingerprint_service = fingerprint_service
        self._ensure_network()

    def _ensure_network(self) -> None:
        """Ensure the Docker network exists."""
        try:
            self.client.networks.get(settings.docker_network)
            logger.debug("Docker network exists", network=settings.docker_network)
        except docker.errors.NotFound:
            self.client.networks.create(
                settings.docker_network,
                driver="bridge",
            )
            logger.info("Created Docker network", network=settings.docker_network)

    def _get_available_port(self, start: int = 5555, end: int = 5600) -> int:
        """Find an available port for ADB."""
        used_ports = set()

        for container in self.client.containers.list():
            if container.name.startswith("mobiledroid-"):
                ports = container.ports
                for port_bindings in ports.values():
                    if port_bindings:
                        for binding in port_bindings:
                            used_ports.add(int(binding["HostPort"]))

        for port in range(start, end):
            if port not in used_ports:
                return port

        raise RuntimeError("No available ports for ADB")

    async def create_container(
        self,
        profile_id: str,
        name: str,
        fingerprint: dict[str, Any],
        proxy: dict[str, Any] | None = None,
    ) -> tuple[str, int]:
        """Create a new redroid container for a profile.

        Returns:
            Tuple of (container_id, adb_port)
        """
        container_name = f"mobiledroid-{profile_id}"
        adb_port = self._get_available_port()

        # Build environment variables from fingerprint
        env = self.fingerprint_service.fingerprint_to_env(fingerprint)

        # Add proxy configuration if provided
        if proxy and proxy.get("type") != "none":
            env["PROXY_HOST"] = proxy.get("host", "")
            env["PROXY_PORT"] = str(proxy.get("port", ""))
            if proxy.get("username"):
                env["PROXY_USERNAME"] = proxy.get("username", "")
            if proxy.get("password"):
                env["PROXY_PASSWORD"] = proxy.get("password", "")

        # Device configuration for redroid
        device_width = int(env.get("DEVICE_WIDTH", 1080))
        device_height = int(env.get("DEVICE_HEIGHT", 2400))
        device_dpi = int(env.get("DEVICE_DPI", 420))

        # Build command with redroid-specific options
        command = [
            f"androidboot.redroid_width={device_width}",
            f"androidboot.redroid_height={device_height}",
            f"androidboot.redroid_dpi={device_dpi}",
            "androidboot.redroid_fps=30",
            "androidboot.redroid_gpu_mode=guest",
        ]

        try:
            # Stop and remove existing container with same name
            try:
                existing = self.client.containers.get(container_name)
                logger.info("Removing existing container", name=container_name)
                existing.stop(timeout=5)
                existing.remove()
            except docker.errors.NotFound:
                pass

            # Create and start the container
            container = self.client.containers.run(
                settings.redroid_image,
                command=command,
                name=container_name,
                detach=True,
                privileged=True,
                environment=env,
                ports={
                    "5555/tcp": adb_port,
                },
                network=settings.docker_network,
                labels={
                    "mobiledroid.profile_id": profile_id,
                    "mobiledroid.profile_name": name,
                },
                # Memory and CPU limits
                mem_limit="4g",
                cpu_quota=200000,  # 2 CPU cores
                # Required for Android
                tmpfs={
                    "/dev/shm": "size=256m",
                },
            )

            logger.info(
                "Created container",
                container_id=container.id,
                name=container_name,
                adb_port=adb_port,
            )

            return container.id, adb_port

        except Exception as e:
            logger.error(
                "Failed to create container",
                error=str(e),
                profile_id=profile_id,
            )
            raise

    async def start_container(self, container_id: str) -> bool:
        """Start a stopped container."""
        try:
            container = self.client.containers.get(container_id)
            container.start()
            logger.info("Started container", container_id=container_id)
            return True
        except Exception as e:
            logger.error("Failed to start container", error=str(e))
            return False

    async def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """Stop a running container."""
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout)
            logger.info("Stopped container", container_id=container_id)
            return True
        except Exception as e:
            logger.error("Failed to stop container", error=str(e))
            return False

    async def remove_container(self, container_id: str, force: bool = True) -> bool:
        """Remove a container."""
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            logger.info("Removed container", container_id=container_id)
            return True
        except docker.errors.NotFound:
            logger.debug("Container not found", container_id=container_id)
            return True
        except Exception as e:
            logger.error("Failed to remove container", error=str(e))
            return False

    def get_container_status(self, container_id: str) -> str | None:
        """Get container status."""
        try:
            container = self.client.containers.get(container_id)
            return container.status
        except docker.errors.NotFound:
            return None
        except Exception as e:
            logger.error("Failed to get container status", error=str(e))
            return None

    def get_container_logs(
        self,
        container_id: str,
        tail: int = 100,
    ) -> str:
        """Get container logs."""
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=True)
            return logs.decode("utf-8")
        except Exception as e:
            logger.error("Failed to get container logs", error=str(e))
            return ""

    async def wait_for_boot(
        self,
        container_id: str,
        timeout: int = 120,
    ) -> bool:
        """Wait for Android to fully boot in container."""
        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                logger.warning("Boot timeout", container_id=container_id)
                return False

            try:
                container = self.client.containers.get(container_id)
                result = container.exec_run(
                    "getprop sys.boot_completed",
                    demux=True,
                )
                stdout = result.output[0] or b""
                if stdout.strip() == b"1":
                    logger.info(
                        "Android boot completed",
                        container_id=container_id,
                        elapsed=elapsed,
                    )
                    return True
            except Exception as e:
                logger.debug("Boot check error", error=str(e))

            await asyncio.sleep(2)

    def list_containers(self) -> list[Container]:
        """List all mobiledroid containers."""
        return self.client.containers.list(
            all=True,
            filters={"name": "mobiledroid-"},
        )
