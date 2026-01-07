"""End-to-end tests for profile lifecycle.

These tests validate the complete profile lifecycle against a real (or mocked)
Docker environment and ADB connections. They test the integration between
all components working together.

For local development, these tests use mocked Docker and ADB services.
For CI/production testing against real infrastructure, set E2E_REAL_DOCKER=1.
"""

import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# Check if we should use real Docker
USE_REAL_DOCKER = os.environ.get("E2E_REAL_DOCKER", "0") == "1"


@pytest.mark.asyncio
class TestProfileLifecycleE2E:
    """End-to-end tests for complete profile lifecycle."""

    async def test_complete_profile_lifecycle(self, client, sample_profile_data):
        """Test complete profile lifecycle: create -> start -> screenshot -> stop -> delete."""
        with patch("src.routers.profiles.DockerService") as mock_docker_cls, \
             patch("src.routers.profiles.ADBService") as mock_adb_cls:
            # Setup mocks
            mock_docker = MagicMock()
            mock_docker.create_container = AsyncMock(return_value=("e2e-container-id", 5556))
            mock_docker.wait_for_boot = AsyncMock(return_value=True)
            mock_docker.stop_container = AsyncMock(return_value=True)
            mock_docker.remove_container = AsyncMock(return_value=True)
            mock_docker.get_container_status.return_value = None
            mock_docker_cls.return_value = mock_docker

            mock_adb = MagicMock()
            mock_adb.connect = AsyncMock(return_value=True)
            mock_adb.disconnect = AsyncMock(return_value=True)
            mock_adb.screenshot = AsyncMock(return_value=b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
            mock_adb.get_device_info = AsyncMock(return_value={
                "model": "Pixel 7",
                "brand": "google",
            })
            mock_adb._devices = {}
            mock_adb_cls.return_value = mock_adb

            # Step 1: Create profile
            create_response = await client.post("/profiles", json=sample_profile_data)
            assert create_response.status_code == 201
            profile = create_response.json()
            profile_id = profile["id"]
            assert profile["status"] == "stopped"
            assert profile["name"] == sample_profile_data["name"]

            # Step 2: Start profile
            start_response = await client.post(f"/profiles/{profile_id}/start")
            assert start_response.status_code == 200
            started_profile = start_response.json()
            assert started_profile["status"] == "running"
            assert started_profile["container_id"] is not None
            assert started_profile["adb_port"] is not None

            # Update mock to include the device
            mock_adb._devices[f"localhost:{started_profile['adb_port']}"] = MagicMock()

            # Step 3: Get screenshot
            screenshot_response = await client.get(f"/profiles/{profile_id}/screenshot")
            assert screenshot_response.status_code == 200
            assert screenshot_response.headers["content-type"] == "image/png"

            # Step 4: Get device info
            info_response = await client.get(f"/profiles/{profile_id}/device-info")
            assert info_response.status_code == 200
            device_info = info_response.json()
            assert "model" in device_info

            # Step 5: Stop profile
            stop_response = await client.post(f"/profiles/{profile_id}/stop")
            assert stop_response.status_code == 200
            stopped_profile = stop_response.json()
            assert stopped_profile["status"] == "stopped"

            # Step 6: Delete profile
            delete_response = await client.delete(f"/profiles/{profile_id}")
            assert delete_response.status_code == 204

            # Verify profile is deleted
            get_response = await client.get(f"/profiles/{profile_id}")
            assert get_response.status_code == 404

    async def test_multiple_profiles_lifecycle(self, client, sample_profile_data):
        """Test managing multiple profiles simultaneously."""
        with patch("src.routers.profiles.DockerService") as mock_docker_cls, \
             patch("src.routers.profiles.ADBService") as mock_adb_cls:
            # Port counter for unique ports
            port_counter = [5555]

            def get_next_port():
                port = port_counter[0]
                port_counter[0] += 1
                return port

            mock_docker = MagicMock()
            mock_docker.create_container = AsyncMock(
                side_effect=lambda **kwargs: (f"container-{kwargs['profile_id']}", get_next_port())
            )
            mock_docker.wait_for_boot = AsyncMock(return_value=True)
            mock_docker.stop_container = AsyncMock(return_value=True)
            mock_docker.remove_container = AsyncMock(return_value=True)
            mock_docker.get_container_status.return_value = None
            mock_docker_cls.return_value = mock_docker

            mock_adb = MagicMock()
            mock_adb.connect = AsyncMock(return_value=True)
            mock_adb.disconnect = AsyncMock(return_value=True)
            mock_adb._devices = {}
            mock_adb_cls.return_value = mock_adb

            profile_ids = []

            # Create 3 profiles
            for i in range(3):
                profile_data = sample_profile_data.copy()
                profile_data["name"] = f"E2E Profile {i}"
                response = await client.post("/profiles", json=profile_data)
                assert response.status_code == 201
                profile_ids.append(response.json()["id"])

            # List should show all 3
            list_response = await client.get("/profiles")
            assert list_response.status_code == 200
            assert list_response.json()["total"] >= 3

            # Start all profiles
            for profile_id in profile_ids:
                response = await client.post(f"/profiles/{profile_id}/start")
                assert response.status_code == 200
                assert response.json()["status"] == "running"

            # Stop all profiles
            for profile_id in profile_ids:
                response = await client.post(f"/profiles/{profile_id}/stop")
                assert response.status_code == 200
                assert response.json()["status"] == "stopped"

            # Delete all profiles
            for profile_id in profile_ids:
                response = await client.delete(f"/profiles/{profile_id}")
                assert response.status_code == 204

    async def test_profile_restart_cycle(self, client, sample_profile_data):
        """Test profile can be started, stopped, and started again."""
        with patch("src.routers.profiles.DockerService") as mock_docker_cls, \
             patch("src.routers.profiles.ADBService") as mock_adb_cls:
            # Track container state
            container_state = {"running": False}

            mock_docker = MagicMock()
            mock_docker.create_container = AsyncMock(return_value=("restart-container", 5560))
            mock_docker.wait_for_boot = AsyncMock(return_value=True)
            mock_docker.start_container = AsyncMock(return_value=True)
            mock_docker.stop_container = AsyncMock(return_value=True)
            mock_docker.remove_container = AsyncMock(return_value=True)

            def get_status(container_id):
                return "running" if container_state["running"] else "exited"
            mock_docker.get_container_status.side_effect = get_status
            mock_docker_cls.return_value = mock_docker

            mock_adb = MagicMock()
            mock_adb.connect = AsyncMock(return_value=True)
            mock_adb.disconnect = AsyncMock(return_value=True)
            mock_adb._devices = {}
            mock_adb_cls.return_value = mock_adb

            # Create profile
            create_response = await client.post("/profiles", json=sample_profile_data)
            assert create_response.status_code == 201
            profile_id = create_response.json()["id"]

            # First start
            mock_docker.get_container_status.return_value = None  # No container yet
            start1_response = await client.post(f"/profiles/{profile_id}/start")
            assert start1_response.status_code == 200
            assert start1_response.json()["status"] == "running"
            container_state["running"] = True

            # First stop
            stop1_response = await client.post(f"/profiles/{profile_id}/stop")
            assert stop1_response.status_code == 200
            assert stop1_response.json()["status"] == "stopped"
            container_state["running"] = False

            # Second start (container exists but stopped)
            mock_docker.get_container_status.return_value = "exited"
            start2_response = await client.post(f"/profiles/{profile_id}/start")
            assert start2_response.status_code == 200
            assert start2_response.json()["status"] == "running"

            # Cleanup
            await client.delete(f"/profiles/{profile_id}")


@pytest.mark.asyncio
class TestErrorRecoveryE2E:
    """End-to-end tests for error scenarios and recovery."""

    async def test_profile_start_boot_failure_recovery(self, client, sample_profile_data):
        """Test recovery when Android boot fails."""
        with patch("src.routers.profiles.DockerService") as mock_docker_cls, \
             patch("src.routers.profiles.ADBService") as mock_adb_cls:
            boot_attempt = [0]

            async def boot_with_retry(*args, **kwargs):
                boot_attempt[0] += 1
                return boot_attempt[0] >= 2  # Fail first, succeed second

            mock_docker = MagicMock()
            mock_docker.create_container = AsyncMock(return_value=("boot-fail-container", 5565))
            mock_docker.wait_for_boot = AsyncMock(side_effect=boot_with_retry)
            mock_docker.stop_container = AsyncMock(return_value=True)
            mock_docker.remove_container = AsyncMock(return_value=True)
            mock_docker.get_container_status.return_value = None
            mock_docker_cls.return_value = mock_docker

            mock_adb = MagicMock()
            mock_adb.connect = AsyncMock(return_value=True)
            mock_adb._devices = {}
            mock_adb_cls.return_value = mock_adb

            # Create profile
            create_response = await client.post("/profiles", json=sample_profile_data)
            profile_id = create_response.json()["id"]

            # First start - boot fails
            start1_response = await client.post(f"/profiles/{profile_id}/start")
            assert start1_response.status_code == 200
            assert start1_response.json()["status"] == "error"

            # Second start - boot succeeds
            start2_response = await client.post(f"/profiles/{profile_id}/start")
            assert start2_response.status_code == 200
            assert start2_response.json()["status"] == "running"

            # Cleanup
            await client.post(f"/profiles/{profile_id}/stop")
            await client.delete(f"/profiles/{profile_id}")

    async def test_concurrent_profile_operations(self, client, sample_profile_data):
        """Test concurrent operations on same profile are handled correctly."""
        import asyncio

        with patch("src.routers.profiles.DockerService") as mock_docker_cls, \
             patch("src.routers.profiles.ADBService") as mock_adb_cls:
            mock_docker = MagicMock()
            mock_docker.create_container = AsyncMock(return_value=("concurrent-container", 5570))
            mock_docker.wait_for_boot = AsyncMock(return_value=True)
            mock_docker.stop_container = AsyncMock(return_value=True)
            mock_docker.remove_container = AsyncMock(return_value=True)
            mock_docker.get_container_status.return_value = None
            mock_docker_cls.return_value = mock_docker

            mock_adb = MagicMock()
            mock_adb.connect = AsyncMock(return_value=True)
            mock_adb.disconnect = AsyncMock(return_value=True)
            mock_adb._devices = {}
            mock_adb_cls.return_value = mock_adb

            # Create profile
            create_response = await client.post("/profiles", json=sample_profile_data)
            profile_id = create_response.json()["id"]

            # Start profile first
            await client.post(f"/profiles/{profile_id}/start")

            # Try concurrent update operations (should fail for running profile)
            async def update_profile():
                return await client.patch(
                    f"/profiles/{profile_id}",
                    json={"name": "Concurrent Update"}
                )

            # Run concurrent updates
            results = await asyncio.gather(
                update_profile(),
                update_profile(),
                update_profile(),
                return_exceptions=True
            )

            # All should fail because profile is running
            for result in results:
                if not isinstance(result, Exception):
                    assert result.status_code == 400

            # Cleanup
            await client.post(f"/profiles/{profile_id}/stop")
            await client.delete(f"/profiles/{profile_id}")


@pytest.mark.asyncio
class TestDataPersistenceE2E:
    """End-to-end tests for data persistence."""

    async def test_profile_data_persists(self, client, sample_profile_data):
        """Test that profile data persists across API calls."""
        with patch("src.routers.profiles.DockerService"), \
             patch("src.routers.profiles.ADBService"):
            # Create profile
            create_response = await client.post("/profiles", json=sample_profile_data)
            profile_id = create_response.json()["id"]

            # Get profile multiple times
            for _ in range(3):
                get_response = await client.get(f"/profiles/{profile_id}")
                assert get_response.status_code == 200
                assert get_response.json()["name"] == sample_profile_data["name"]
                assert get_response.json()["fingerprint"]["model"] == sample_profile_data["fingerprint"]["model"]

            # Cleanup
            await client.delete(f"/profiles/{profile_id}")

    async def test_profile_updates_persist(self, client, sample_profile_data):
        """Test that profile updates persist."""
        with patch("src.routers.profiles.DockerService"), \
             patch("src.routers.profiles.ADBService"):
            # Create profile
            create_response = await client.post("/profiles", json=sample_profile_data)
            profile_id = create_response.json()["id"]

            # Update profile
            await client.patch(
                f"/profiles/{profile_id}",
                json={"name": "Persisted Update"}
            )

            # Verify update persisted
            get_response = await client.get(f"/profiles/{profile_id}")
            assert get_response.json()["name"] == "Persisted Update"

            # Cleanup
            await client.delete(f"/profiles/{profile_id}")
