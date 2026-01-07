"""Unit tests for DockerService."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

import docker.errors


@pytest.mark.asyncio
class TestDockerServiceInit:
    """Tests for DockerService initialization."""

    async def test_init_creates_network_if_not_exists(self, mock_fingerprint_service):
        """Test that initialization creates the network if it doesn't exist."""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.networks.get.side_effect = docker.errors.NotFound("not found")

            from src.services.docker_service import DockerService
            service = DockerService(mock_fingerprint_service)

            mock_client.networks.create.assert_called_once()

    async def test_init_uses_existing_network(self, mock_fingerprint_service):
        """Test that initialization uses existing network."""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.networks.get.return_value = MagicMock()

            from src.services.docker_service import DockerService
            service = DockerService(mock_fingerprint_service)

            mock_client.networks.create.assert_not_called()


@pytest.mark.asyncio
class TestDockerServiceContainerCreation:
    """Tests for container creation."""

    async def test_create_container_success(self, mock_fingerprint_service):
        """Test successful container creation."""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.networks.get.return_value = MagicMock()
            mock_client.containers.list.return_value = []

            mock_container = MagicMock()
            mock_container.id = "new-container-id"
            mock_client.containers.run.return_value = mock_container
            mock_client.containers.get.side_effect = docker.errors.NotFound("not found")

            from src.services.docker_service import DockerService
            service = DockerService(mock_fingerprint_service)

            container_id, adb_port = await service.create_container(
                profile_id="test-profile",
                name="Test Profile",
                fingerprint={
                    "model": "Pixel 7",
                    "brand": "google",
                    "manufacturer": "Google",
                    "screen": {"width": 1080, "height": 2400, "dpi": 420},
                },
                proxy=None,
            )

            assert container_id == "new-container-id"
            assert adb_port >= 5555
            mock_client.containers.run.assert_called_once()

    async def test_create_container_with_proxy(self, mock_fingerprint_service):
        """Test container creation with proxy configuration."""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.networks.get.return_value = MagicMock()
            mock_client.containers.list.return_value = []

            mock_container = MagicMock()
            mock_container.id = "proxy-container-id"
            mock_client.containers.run.return_value = mock_container
            mock_client.containers.get.side_effect = docker.errors.NotFound("not found")

            from src.services.docker_service import DockerService
            service = DockerService(mock_fingerprint_service)

            await service.create_container(
                profile_id="test-profile",
                name="Proxy Profile",
                fingerprint={
                    "model": "Pixel 7",
                    "brand": "google",
                    "manufacturer": "Google",
                    "screen": {"width": 1080, "height": 2400, "dpi": 420},
                },
                proxy={
                    "type": "http",
                    "host": "proxy.example.com",
                    "port": 8080,
                    "username": "user",
                    "password": "pass",
                },
            )

            # Verify proxy env vars were passed
            call_kwargs = mock_client.containers.run.call_args
            env = call_kwargs.kwargs.get("environment", {})
            assert env.get("PROXY_HOST") == "proxy.example.com"
            assert env.get("PROXY_PORT") == "8080"

    async def test_create_container_removes_existing(self, mock_fingerprint_service):
        """Test that existing container is removed before creating new one."""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.networks.get.return_value = MagicMock()
            mock_client.containers.list.return_value = []

            existing_container = MagicMock()
            mock_client.containers.get.return_value = existing_container

            mock_container = MagicMock()
            mock_container.id = "new-container-id"
            mock_client.containers.run.return_value = mock_container

            from src.services.docker_service import DockerService
            service = DockerService(mock_fingerprint_service)

            await service.create_container(
                profile_id="test-profile",
                name="Test Profile",
                fingerprint={"model": "Pixel 7", "brand": "google", "manufacturer": "Google", "screen": {"width": 1080, "height": 2400, "dpi": 420}},
            )

            existing_container.stop.assert_called_once()
            existing_container.remove.assert_called_once()


@pytest.mark.asyncio
class TestDockerServiceContainerOperations:
    """Tests for container start/stop/remove operations."""

    async def test_start_container_success(self, mock_fingerprint_service):
        """Test successful container start."""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.networks.get.return_value = MagicMock()

            mock_container = MagicMock()
            mock_client.containers.get.return_value = mock_container

            from src.services.docker_service import DockerService
            service = DockerService(mock_fingerprint_service)

            result = await service.start_container("test-container-id")

            assert result is True
            mock_container.start.assert_called_once()

    async def test_start_container_failure(self, mock_fingerprint_service):
        """Test container start failure."""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.networks.get.return_value = MagicMock()

            mock_client.containers.get.side_effect = Exception("Container not found")

            from src.services.docker_service import DockerService
            service = DockerService(mock_fingerprint_service)

            result = await service.start_container("nonexistent-container")

            assert result is False

    async def test_stop_container_success(self, mock_fingerprint_service):
        """Test successful container stop."""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.networks.get.return_value = MagicMock()

            mock_container = MagicMock()
            mock_client.containers.get.return_value = mock_container

            from src.services.docker_service import DockerService
            service = DockerService(mock_fingerprint_service)

            result = await service.stop_container("test-container-id")

            assert result is True
            mock_container.stop.assert_called_once()

    async def test_remove_container_success(self, mock_fingerprint_service):
        """Test successful container removal."""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.networks.get.return_value = MagicMock()

            mock_container = MagicMock()
            mock_client.containers.get.return_value = mock_container

            from src.services.docker_service import DockerService
            service = DockerService(mock_fingerprint_service)

            result = await service.remove_container("test-container-id")

            assert result is True
            mock_container.remove.assert_called_once_with(force=True)

    async def test_remove_container_not_found(self, mock_fingerprint_service):
        """Test removing non-existent container returns True."""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.networks.get.return_value = MagicMock()

            mock_client.containers.get.side_effect = docker.errors.NotFound("not found")

            from src.services.docker_service import DockerService
            service = DockerService(mock_fingerprint_service)

            result = await service.remove_container("nonexistent")

            assert result is True


@pytest.mark.asyncio
class TestDockerServiceStatus:
    """Tests for container status checks."""

    async def test_get_container_status_running(self, mock_fingerprint_service):
        """Test getting status of running container."""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.networks.get.return_value = MagicMock()

            mock_container = MagicMock()
            mock_container.status = "running"
            mock_client.containers.get.return_value = mock_container

            from src.services.docker_service import DockerService
            service = DockerService(mock_fingerprint_service)

            status = service.get_container_status("test-container")

            assert status == "running"

    async def test_get_container_status_not_found(self, mock_fingerprint_service):
        """Test getting status of non-existent container."""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.networks.get.return_value = MagicMock()

            mock_client.containers.get.side_effect = docker.errors.NotFound("not found")

            from src.services.docker_service import DockerService
            service = DockerService(mock_fingerprint_service)

            status = service.get_container_status("nonexistent")

            assert status is None


@pytest.mark.asyncio
class TestDockerServiceBootWait:
    """Tests for waiting for Android boot."""

    async def test_wait_for_boot_success(self, mock_fingerprint_service):
        """Test successful boot wait."""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.networks.get.return_value = MagicMock()

            mock_container = MagicMock()
            mock_container.exec_run.return_value = MagicMock(output=(b"1\n", None))
            mock_client.containers.get.return_value = mock_container

            from src.services.docker_service import DockerService
            service = DockerService(mock_fingerprint_service)

            result = await service.wait_for_boot("test-container", timeout=5)

            assert result is True

    async def test_wait_for_boot_timeout(self, mock_fingerprint_service):
        """Test boot wait timeout."""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.networks.get.return_value = MagicMock()

            mock_container = MagicMock()
            # Always return "not booted"
            mock_container.exec_run.return_value = MagicMock(output=(b"0\n", None))
            mock_client.containers.get.return_value = mock_container

            from src.services.docker_service import DockerService
            service = DockerService(mock_fingerprint_service)

            result = await service.wait_for_boot("test-container", timeout=1)

            assert result is False


@pytest.mark.asyncio
class TestDockerServicePortAllocation:
    """Tests for port allocation."""

    async def test_get_available_port_first(self, mock_fingerprint_service):
        """Test getting first available port."""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.networks.get.return_value = MagicMock()
            mock_client.containers.list.return_value = []

            from src.services.docker_service import DockerService
            service = DockerService(mock_fingerprint_service)

            port = service._get_available_port()

            assert port == 5555

    async def test_get_available_port_skips_used(self, mock_fingerprint_service):
        """Test that used ports are skipped."""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client
            mock_client.networks.get.return_value = MagicMock()

            # Create mock container using port 5555
            mock_container = MagicMock()
            mock_container.name = "mobiledroid-test"
            mock_container.ports = {"5555/tcp": [{"HostPort": "5555"}]}
            mock_client.containers.list.return_value = [mock_container]

            from src.services.docker_service import DockerService
            service = DockerService(mock_fingerprint_service)

            port = service._get_available_port()

            assert port == 5556
