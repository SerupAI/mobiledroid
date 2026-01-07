"""Integration tests for Profiles API endpoints."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture(autouse=True)
def mock_services():
    """Auto-use fixture to mock Docker and ADB services for all integration tests."""
    with patch("src.routers.profiles.DockerService") as mock_docker_cls, \
         patch("src.routers.profiles.ADBService") as mock_adb_cls:
        mock_docker = MagicMock()
        mock_docker.create_container = AsyncMock(return_value=("container-id", 5555))
        mock_docker.start_container = AsyncMock(return_value=True)
        mock_docker.stop_container = AsyncMock(return_value=True)
        mock_docker.remove_container = AsyncMock(return_value=True)
        mock_docker.wait_for_boot = AsyncMock(return_value=True)
        mock_docker.get_container_status.return_value = None
        mock_docker_cls.return_value = mock_docker

        mock_adb = MagicMock()
        mock_adb.connect = AsyncMock(return_value=True)
        mock_adb.disconnect = AsyncMock(return_value=True)
        mock_adb.screenshot = AsyncMock(return_value=b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        mock_adb.get_device_info = AsyncMock(return_value={
            "model": "Pixel 7",
            "brand": "google",
            "manufacturer": "Google",
            "android_version": "14",
        })
        mock_adb._devices = {}
        mock_adb_cls.return_value = mock_adb

        yield {"docker": mock_docker, "docker_cls": mock_docker_cls, "adb": mock_adb, "adb_cls": mock_adb_cls}


@pytest.mark.asyncio
class TestProfilesAPICreate:
    """Tests for POST /profiles endpoint."""

    async def test_create_profile_success(self, client, sample_profile_data):
        """Test successful profile creation."""
        response = await client.post("/profiles", json=sample_profile_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_profile_data["name"]
        assert data["status"] == "stopped"
        assert data["id"] is not None
        assert data["fingerprint"]["model"] == "Pixel 7"

    async def test_create_profile_minimal(self, client):
        """Test creating profile with minimal required fields."""
        minimal_data = {
            "name": "Minimal Profile",
            "fingerprint": {
                "model": "Test Device",
                "brand": "test",
                "manufacturer": "Test Inc",
                "build_fingerprint": "test/test/test:14/TEST.123/456:user/release-keys",
            }
        }

        response = await client.post("/profiles", json=minimal_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Profile"
        assert data["proxy"]["type"] == "none"

    async def test_create_profile_validation_error(self, client):
        """Test profile creation with validation errors."""
        invalid_data = {
            "name": "",  # Empty name
            "fingerprint": {
                "model": "Test",
                "brand": "test",
                # Missing required fields
            }
        }

        response = await client.post("/profiles", json=invalid_data)

        assert response.status_code == 422

    async def test_create_profile_invalid_proxy(self, client):
        """Test profile creation with invalid proxy config."""
        data = {
            "name": "Invalid Proxy Profile",
            "fingerprint": {
                "model": "Test Device",
                "brand": "test",
                "manufacturer": "Test",
                "build_fingerprint": "test/test/test:14/TEST/123:user/release-keys",
            },
            "proxy": {
                "type": "http",
                "port": 99999,  # Invalid port
            }
        }

        response = await client.post("/profiles", json=data)

        assert response.status_code == 422


@pytest.mark.asyncio
class TestProfilesAPIList:
    """Tests for GET /profiles endpoint."""

    async def test_list_profiles_empty(self, client):
        """Test listing profiles when none exist."""
        response = await client.get("/profiles")

        assert response.status_code == 200
        data = response.json()
        assert data["profiles"] == []
        assert data["total"] == 0

    async def test_list_profiles_with_data(self, client, sample_profile):
        """Test listing profiles with existing data."""
        response = await client.get("/profiles")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(p["id"] == sample_profile.id for p in data["profiles"])

    async def test_list_profiles_pagination(self, client, sample_profile_data):
        """Test profile listing with pagination."""
        # Create multiple profiles
        for i in range(5):
            profile_data = sample_profile_data.copy()
            profile_data["name"] = f"Profile {i}"
            await client.post("/profiles", json=profile_data)

        # Test pagination
        response = await client.get("/profiles?skip=0&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["profiles"]) == 2
        assert data["total"] >= 5


@pytest.mark.asyncio
class TestProfilesAPIGet:
    """Tests for GET /profiles/{profile_id} endpoint."""

    async def test_get_profile_success(self, client, sample_profile):
        """Test getting an existing profile."""
        response = await client.get(f"/profiles/{sample_profile.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_profile.id
        assert data["name"] == sample_profile.name

    async def test_get_profile_not_found(self, client):
        """Test getting a non-existent profile."""
        response = await client.get("/profiles/non-existent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestProfilesAPIUpdate:
    """Tests for PATCH /profiles/{profile_id} endpoint."""

    async def test_update_profile_name(self, client, sample_profile):
        """Test updating profile name."""
        response = await client.patch(
            f"/profiles/{sample_profile.id}",
            json={"name": "Updated Name"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    async def test_update_profile_fingerprint(self, client, sample_profile):
        """Test updating profile fingerprint."""
        new_fingerprint = {
            "model": "Galaxy S23",
            "brand": "samsung",
            "manufacturer": "Samsung",
            "build_fingerprint": "samsung/dm1q/dm1q:14/UP1A.231005.007/S911U1UEU1AWLB:user/release-keys",
        }

        response = await client.patch(
            f"/profiles/{sample_profile.id}",
            json={"fingerprint": new_fingerprint}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["fingerprint"]["model"] == "Galaxy S23"

    async def test_update_profile_not_found(self, client):
        """Test updating a non-existent profile."""
        response = await client.patch(
            "/profiles/non-existent-id",
            json={"name": "New Name"}
        )

        assert response.status_code == 404

    async def test_update_running_profile_fails(self, client, running_profile):
        """Test that updating a running profile fails."""
        response = await client.patch(
            f"/profiles/{running_profile.id}",
            json={"name": "Should Fail"}
        )

        assert response.status_code == 400
        assert "running" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestProfilesAPIDelete:
    """Tests for DELETE /profiles/{profile_id} endpoint."""

    async def test_delete_profile_success(self, client, sample_profile):
        """Test successful profile deletion."""
        response = await client.delete(f"/profiles/{sample_profile.id}")

        assert response.status_code == 204

        # Verify profile is deleted
        get_response = await client.get(f"/profiles/{sample_profile.id}")
        assert get_response.status_code == 404

    async def test_delete_profile_not_found(self, client):
        """Test deleting a non-existent profile."""
        response = await client.delete("/profiles/non-existent-id")

        assert response.status_code == 404


@pytest.mark.asyncio
class TestProfilesAPIStart:
    """Tests for POST /profiles/{profile_id}/start endpoint."""

    async def test_start_profile_success(self, client, sample_profile, mock_services):
        """Test successfully starting a profile."""
        response = await client.post(f"/profiles/{sample_profile.id}/start")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["container_id"] == "container-id"
        assert data["adb_port"] == 5555

    async def test_start_profile_not_found(self, client):
        """Test starting a non-existent profile."""
        response = await client.post("/profiles/non-existent-id/start")

        assert response.status_code == 404


@pytest.mark.asyncio
class TestProfilesAPIStop:
    """Tests for POST /profiles/{profile_id}/stop endpoint."""

    async def test_stop_profile_success(self, client, running_profile, mock_services):
        """Test successfully stopping a profile."""
        response = await client.post(f"/profiles/{running_profile.id}/stop")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"

    async def test_stop_profile_not_found(self, client):
        """Test stopping a non-existent profile."""
        response = await client.post("/profiles/non-existent-id/stop")

        assert response.status_code == 404


@pytest.mark.asyncio
class TestProfilesAPIScreenshot:
    """Tests for GET /profiles/{profile_id}/screenshot endpoint."""

    async def test_get_screenshot_success(self, client, running_profile, mock_services):
        """Test getting a screenshot from a running profile."""
        # Update mock to include device
        mock_services["adb"]._devices[f"localhost:{running_profile.adb_port}"] = MagicMock()

        response = await client.get(f"/profiles/{running_profile.id}/screenshot")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    async def test_get_screenshot_profile_not_running(self, client, sample_profile):
        """Test getting screenshot from a stopped profile."""
        response = await client.get(f"/profiles/{sample_profile.id}/screenshot")

        assert response.status_code == 404


@pytest.mark.asyncio
class TestProfilesAPIDeviceInfo:
    """Tests for GET /profiles/{profile_id}/device-info endpoint."""

    async def test_get_device_info_success(self, client, running_profile, mock_services):
        """Test getting device info from a running profile."""
        # Update mock to include device
        mock_services["adb"]._devices[f"localhost:{running_profile.adb_port}"] = MagicMock()

        response = await client.get(f"/profiles/{running_profile.id}/device-info")

        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "Pixel 7"

    async def test_get_device_info_profile_not_running(self, client, sample_profile):
        """Test getting device info from a stopped profile."""
        response = await client.get(f"/profiles/{sample_profile.id}/device-info")

        assert response.status_code == 404
