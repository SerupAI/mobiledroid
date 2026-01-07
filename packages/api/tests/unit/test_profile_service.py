"""Unit tests for ProfileService."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.profile_service import ProfileService
from src.models.profile import Profile, ProfileStatus
from src.schemas.profile import ProfileCreate, ProfileUpdate, DeviceFingerprint, ProxyConfig, ScreenConfig


@pytest.mark.asyncio
class TestProfileServiceCreate:
    """Tests for profile creation."""

    async def test_create_profile_success(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        sample_fingerprint,
        sample_proxy,
    ):
        """Test successful profile creation."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        data = ProfileCreate(
            name="New Profile",
            fingerprint=sample_fingerprint,
            proxy=sample_proxy,
        )

        profile = await service.create(data)

        assert profile.id is not None
        assert profile.name == "New Profile"
        assert profile.status == ProfileStatus.STOPPED
        assert profile.container_id is None
        assert profile.fingerprint["model"] == "Pixel 7"
        assert profile.proxy["type"] == "http"

    async def test_create_profile_with_default_proxy(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        sample_fingerprint,
    ):
        """Test profile creation with default (no) proxy."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        data = ProfileCreate(
            name="No Proxy Profile",
            fingerprint=sample_fingerprint,
            proxy=ProxyConfig(type="none"),
        )

        profile = await service.create(data)

        assert profile.proxy["type"] == "none"
        assert profile.proxy["host"] is None


@pytest.mark.asyncio
class TestProfileServiceGet:
    """Tests for profile retrieval."""

    async def test_get_profile_exists(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        sample_profile,
    ):
        """Test getting an existing profile."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        profile = await service.get(sample_profile.id)

        assert profile is not None
        assert profile.id == sample_profile.id
        assert profile.name == sample_profile.name

    async def test_get_profile_not_found(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
    ):
        """Test getting a non-existent profile."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        profile = await service.get("non-existent-id")

        assert profile is None

    async def test_get_all_profiles(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        sample_profile,
    ):
        """Test getting all profiles."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        profiles, total = await service.get_all()

        assert total >= 1
        assert len(profiles) >= 1
        assert any(p.id == sample_profile.id for p in profiles)

    async def test_get_all_with_pagination(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        sample_fingerprint,
        sample_proxy,
    ):
        """Test pagination of profiles."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        # Create multiple profiles
        for i in range(5):
            data = ProfileCreate(
                name=f"Profile {i}",
                fingerprint=sample_fingerprint,
                proxy=sample_proxy,
            )
            await service.create(data)

        # Test pagination
        profiles, total = await service.get_all(skip=0, limit=2)
        assert len(profiles) == 2
        assert total >= 5


@pytest.mark.asyncio
class TestProfileServiceUpdate:
    """Tests for profile updates."""

    async def test_update_profile_name(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        sample_profile,
    ):
        """Test updating profile name."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        data = ProfileUpdate(name="Updated Name")
        profile = await service.update(sample_profile.id, data)

        assert profile.name == "Updated Name"

    async def test_update_profile_fingerprint(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        sample_profile,
    ):
        """Test updating profile fingerprint."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        new_fingerprint = DeviceFingerprint(
            model="Galaxy S23",
            brand="samsung",
            manufacturer="Samsung",
            build_fingerprint="samsung/dm1q/dm1q:14/UP1A.231005.007/S911U1UEU1AWLB:user/release-keys",
            android_version="14",
            sdk_version="34",
            hardware="qcom",
            board="kalama",
            product="dm1q",
            screen=ScreenConfig(width=1080, height=2340, dpi=425),
        )

        data = ProfileUpdate(fingerprint=new_fingerprint)
        profile = await service.update(sample_profile.id, data)

        assert profile.fingerprint["model"] == "Galaxy S23"
        assert profile.fingerprint["brand"] == "samsung"

    async def test_update_running_profile_fails(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        running_profile,
    ):
        """Test that updating a running profile fails."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        data = ProfileUpdate(name="Should Fail")

        with pytest.raises(ValueError, match="Cannot update a running profile"):
            await service.update(running_profile.id, data)

    async def test_update_profile_not_found(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
    ):
        """Test updating a non-existent profile."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        data = ProfileUpdate(name="New Name")
        profile = await service.update("non-existent-id", data)

        assert profile is None


@pytest.mark.asyncio
class TestProfileServiceDelete:
    """Tests for profile deletion."""

    async def test_delete_profile_success(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        sample_profile,
    ):
        """Test successful profile deletion."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        result = await service.delete(sample_profile.id)

        assert result is True

        # Verify profile is gone
        profile = await service.get(sample_profile.id)
        assert profile is None

    async def test_delete_profile_with_container(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        running_profile,
    ):
        """Test deleting a profile with associated container."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        result = await service.delete(running_profile.id)

        assert result is True
        mock_docker_service.stop_container.assert_called_once_with(running_profile.container_id)
        mock_docker_service.remove_container.assert_called_once_with(running_profile.container_id)

    async def test_delete_profile_not_found(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
    ):
        """Test deleting a non-existent profile."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        result = await service.delete("non-existent-id")

        assert result is False


@pytest.mark.asyncio
class TestProfileServiceStart:
    """Tests for starting profiles."""

    async def test_start_profile_success(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        sample_profile,
    ):
        """Test successfully starting a profile."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        profile = await service.start(sample_profile.id)

        assert profile.status == ProfileStatus.RUNNING
        assert profile.container_id == "test-container-id"
        assert profile.adb_port == 5555
        assert profile.last_started_at is not None
        mock_docker_service.create_container.assert_called_once()
        mock_docker_service.wait_for_boot.assert_called_once()
        mock_adb_service.connect.assert_called_once_with("localhost", 5555)

    async def test_start_already_running_profile(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        running_profile,
    ):
        """Test starting an already running profile."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        profile = await service.start(running_profile.id)

        assert profile.status == ProfileStatus.RUNNING
        mock_docker_service.create_container.assert_not_called()

    async def test_start_profile_boot_failure(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        sample_profile,
    ):
        """Test profile start when boot fails."""
        mock_docker_service.wait_for_boot.return_value = False

        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        profile = await service.start(sample_profile.id)

        assert profile.status == ProfileStatus.ERROR

    async def test_start_profile_not_found(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
    ):
        """Test starting a non-existent profile."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        profile = await service.start("non-existent-id")

        assert profile is None


@pytest.mark.asyncio
class TestProfileServiceStop:
    """Tests for stopping profiles."""

    async def test_stop_profile_success(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        running_profile,
    ):
        """Test successfully stopping a profile."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        profile = await service.stop(running_profile.id)

        assert profile.status == ProfileStatus.STOPPED
        assert profile.last_stopped_at is not None
        mock_adb_service.disconnect.assert_called_once()
        mock_docker_service.stop_container.assert_called_once()

    async def test_stop_already_stopped_profile(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        sample_profile,
    ):
        """Test stopping an already stopped profile."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        profile = await service.stop(sample_profile.id)

        assert profile.status == ProfileStatus.STOPPED
        mock_docker_service.stop_container.assert_not_called()

    async def test_stop_profile_not_found(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
    ):
        """Test stopping a non-existent profile."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        profile = await service.stop("non-existent-id")

        assert profile is None


@pytest.mark.asyncio
class TestProfileServiceScreenshot:
    """Tests for screenshots."""

    async def test_get_screenshot_success(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        running_profile,
    ):
        """Test getting a screenshot from a running profile."""
        mock_adb_service._devices[f"localhost:{running_profile.adb_port}"] = MagicMock()
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        screenshot = await service.get_screenshot(running_profile.id)

        assert screenshot == b"fake-png-data"
        mock_adb_service.screenshot.assert_called_once()

    async def test_get_screenshot_stopped_profile(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        sample_profile,
    ):
        """Test getting a screenshot from a stopped profile."""
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        screenshot = await service.get_screenshot(sample_profile.id)

        assert screenshot is None


@pytest.mark.asyncio
class TestProfileServiceSyncStatus:
    """Tests for status synchronization."""

    async def test_sync_status_running(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        running_profile,
    ):
        """Test syncing status with running container."""
        mock_docker_service.get_container_status.return_value = "running"
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        profile = await service.sync_status(running_profile.id)

        assert profile.status == ProfileStatus.RUNNING

    async def test_sync_status_exited(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        running_profile,
    ):
        """Test syncing status with exited container."""
        mock_docker_service.get_container_status.return_value = "exited"
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        profile = await service.sync_status(running_profile.id)

        assert profile.status == ProfileStatus.STOPPED

    async def test_sync_status_container_removed(
        self,
        db_session,
        mock_docker_service,
        mock_adb_service,
        running_profile,
    ):
        """Test syncing status when container is removed."""
        mock_docker_service.get_container_status.return_value = None
        service = ProfileService(db_session, mock_docker_service, mock_adb_service)

        profile = await service.sync_status(running_profile.id)

        assert profile.status == ProfileStatus.STOPPED
        assert profile.container_id is None
        assert profile.adb_port is None
