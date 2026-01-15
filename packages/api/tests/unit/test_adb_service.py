"""Unit tests for ADBService."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from io import BytesIO

from PIL import Image


@pytest.mark.asyncio
class TestADBServiceConnect:
    """Tests for ADB connect/disconnect."""

    async def test_connect_success(self):
        """Test successful ADB connection."""
        with patch("src.services.adb_service.adb") as mock_adb:
            mock_adb.connect.return_value = "connected"
            mock_device = MagicMock()
            mock_adb.device.return_value = mock_device

            from src.services.adb_service import ADBService
            service = ADBService()

            result = await service.connect("localhost", 5555)

            assert result is True
            assert "localhost:5555" in service._devices
            mock_adb.connect.assert_called_once_with("localhost:5555", timeout=30)

    async def test_connect_failure(self):
        """Test ADB connection failure."""
        with patch("src.services.adb_service.adb") as mock_adb:
            mock_adb.connect.return_value = None

            from src.services.adb_service import ADBService
            service = ADBService()

            result = await service.connect("localhost", 5555)

            assert result is False
            assert "localhost:5555" not in service._devices

    async def test_connect_exception(self):
        """Test ADB connection with exception."""
        with patch("src.services.adb_service.adb") as mock_adb:
            mock_adb.connect.side_effect = Exception("Connection refused")

            from src.services.adb_service import ADBService
            service = ADBService()

            result = await service.connect("localhost", 5555)

            assert result is False

    async def test_disconnect_success(self):
        """Test successful ADB disconnect."""
        with patch("src.services.adb_service.adb") as mock_adb:
            from src.services.adb_service import ADBService
            service = ADBService()
            service._devices["localhost:5555"] = MagicMock()

            result = await service.disconnect("localhost:5555")

            assert result is True
            assert "localhost:5555" not in service._devices
            mock_adb.disconnect.assert_called_once_with("localhost:5555")


@pytest.mark.asyncio
class TestADBServiceScreenshot:
    """Tests for screenshot functionality."""

    async def test_screenshot_success(self):
        """Test successful screenshot."""
        with patch("src.services.adb_service.adb"):
            from src.services.adb_service import ADBService
            service = ADBService()

            # Create a mock device with screenshot capability
            mock_device = MagicMock()
            mock_image = Image.new("RGB", (100, 100), color="red")
            mock_device.screenshot.return_value = mock_image
            service._devices["localhost:5555"] = mock_device

            result = await service.screenshot("localhost:5555")

            assert result is not None
            assert isinstance(result, bytes)
            mock_device.screenshot.assert_called_once()

    async def test_screenshot_device_not_connected(self):
        """Test screenshot with no connected device."""
        with patch("src.services.adb_service.adb") as mock_adb:
            # Simulate device not found
            mock_adb.device.side_effect = Exception("device not found")

            from src.services.adb_service import ADBService
            service = ADBService()

            result = await service.screenshot("localhost:5555")

            assert result is None

    async def test_screenshot_base64(self):
        """Test base64 screenshot."""
        with patch("src.services.adb_service.adb"):
            from src.services.adb_service import ADBService
            service = ADBService()

            mock_device = MagicMock()
            mock_image = Image.new("RGB", (100, 100), color="blue")
            mock_device.screenshot.return_value = mock_image
            service._devices["localhost:5555"] = mock_device

            result = await service.screenshot_base64("localhost:5555")

            assert result is not None
            assert isinstance(result, str)
            # Base64 encoded PNG should start with iVBOR...
            assert result.startswith("iVBOR")


@pytest.mark.asyncio
class TestADBServiceInput:
    """Tests for input operations."""

    async def test_tap_success(self):
        """Test successful tap."""
        with patch("src.services.adb_service.adb"):
            from src.services.adb_service import ADBService
            service = ADBService()

            mock_device = MagicMock()
            service._devices["localhost:5555"] = mock_device

            result = await service.tap("localhost:5555", 100, 200)

            assert result is True
            mock_device.click.assert_called_once_with(100, 200)

    async def test_tap_device_not_connected(self):
        """Test tap with no connected device."""
        with patch("src.services.adb_service.adb") as mock_adb:
            # Simulate device not found
            mock_adb.device.side_effect = Exception("device not found")

            from src.services.adb_service import ADBService
            service = ADBService()

            result = await service.tap("localhost:5555", 100, 200)

            assert result is False

    async def test_swipe_success(self):
        """Test successful swipe."""
        with patch("src.services.adb_service.adb"):
            from src.services.adb_service import ADBService
            service = ADBService()

            mock_device = MagicMock()
            service._devices["localhost:5555"] = mock_device

            result = await service.swipe("localhost:5555", 100, 200, 100, 800, 300)

            assert result is True
            mock_device.swipe.assert_called_once_with(100, 200, 100, 800, 0.3)

    async def test_input_text_success(self):
        """Test successful text input."""
        with patch("src.services.adb_service.adb"):
            from src.services.adb_service import ADBService
            service = ADBService()

            mock_device = MagicMock()
            service._devices["localhost:5555"] = mock_device

            result = await service.input_text("localhost:5555", "Hello World")

            assert result is True
            mock_device.shell.assert_called_once_with("input text 'Hello World'")

    async def test_input_text_with_quotes(self):
        """Test text input with single quotes escaped."""
        with patch("src.services.adb_service.adb"):
            from src.services.adb_service import ADBService
            service = ADBService()

            mock_device = MagicMock()
            service._devices["localhost:5555"] = mock_device

            result = await service.input_text("localhost:5555", "It's a test")

            assert result is True
            mock_device.shell.assert_called_once_with("input text 'It'\\''s a test'")


@pytest.mark.asyncio
class TestADBServiceKeys:
    """Tests for key press operations."""

    async def test_press_key_success(self):
        """Test successful key press."""
        with patch("src.services.adb_service.adb"):
            from src.services.adb_service import ADBService
            service = ADBService()

            mock_device = MagicMock()
            service._devices["localhost:5555"] = mock_device

            result = await service.press_key("localhost:5555", "KEYCODE_ENTER")

            assert result is True
            mock_device.shell.assert_called_once_with("input keyevent KEYCODE_ENTER")

    async def test_press_back(self):
        """Test back button press."""
        with patch("src.services.adb_service.adb"):
            from src.services.adb_service import ADBService
            service = ADBService()

            mock_device = MagicMock()
            service._devices["localhost:5555"] = mock_device

            result = await service.press_back("localhost:5555")

            assert result is True
            mock_device.shell.assert_called_with("input keyevent KEYCODE_BACK")

    async def test_press_home(self):
        """Test home button press."""
        with patch("src.services.adb_service.adb"):
            from src.services.adb_service import ADBService
            service = ADBService()

            mock_device = MagicMock()
            service._devices["localhost:5555"] = mock_device

            result = await service.press_home("localhost:5555")

            assert result is True
            mock_device.shell.assert_called_with("input keyevent KEYCODE_HOME")

    async def test_press_enter(self):
        """Test enter key press."""
        with patch("src.services.adb_service.adb"):
            from src.services.adb_service import ADBService
            service = ADBService()

            mock_device = MagicMock()
            service._devices["localhost:5555"] = mock_device

            result = await service.press_enter("localhost:5555")

            assert result is True
            mock_device.shell.assert_called_with("input keyevent KEYCODE_ENTER")


@pytest.mark.asyncio
class TestADBServiceDeviceInfo:
    """Tests for device info retrieval."""

    async def test_get_device_info_success(self):
        """Test successful device info retrieval."""
        with patch("src.services.adb_service.adb"):
            from src.services.adb_service import ADBService
            service = ADBService()

            mock_device = MagicMock()
            mock_device.shell.side_effect = [
                "Pixel 7\n",      # model
                "google\n",       # brand
                "Google\n",       # manufacturer
                "14\n",           # android_version
                "34\n",           # sdk_version
                "google/panther/panther:14/...\n",  # fingerprint
            ]
            service._devices["localhost:5555"] = mock_device

            result = await service.get_device_info("localhost:5555")

            assert result is not None
            assert result["model"] == "Pixel 7"
            assert result["brand"] == "google"
            assert result["manufacturer"] == "Google"
            assert result["android_version"] == "14"
            assert result["sdk_version"] == "34"

    async def test_get_device_info_not_connected(self):
        """Test device info when not connected."""
        with patch("src.services.adb_service.adb") as mock_adb:
            # Simulate device not found
            mock_adb.device.side_effect = Exception("device not found")

            from src.services.adb_service import ADBService
            service = ADBService()

            result = await service.get_device_info("localhost:5555")

            assert result is None


@pytest.mark.asyncio
class TestADBServiceShell:
    """Tests for shell command execution."""

    async def test_shell_success(self):
        """Test successful shell command."""
        with patch("src.services.adb_service.adb"):
            from src.services.adb_service import ADBService
            service = ADBService()

            mock_device = MagicMock()
            mock_device.shell.return_value = "command output\n"
            service._devices["localhost:5555"] = mock_device

            result = await service.shell("localhost:5555", "ls /sdcard")

            assert result == "command output\n"
            mock_device.shell.assert_called_once_with("ls /sdcard")

    async def test_shell_not_connected(self):
        """Test shell command when not connected."""
        with patch("src.services.adb_service.adb") as mock_adb:
            # Simulate device not found
            mock_adb.device.side_effect = Exception("device not found")

            from src.services.adb_service import ADBService
            service = ADBService()

            result = await service.shell("localhost:5555", "ls")

            assert result is None

    async def test_get_ui_hierarchy(self):
        """Test UI hierarchy retrieval."""
        with patch("src.services.adb_service.adb"):
            from src.services.adb_service import ADBService
            service = ADBService()

            mock_device = MagicMock()
            mock_device.shell.return_value = '<?xml version="1.0"?><hierarchy>...</hierarchy>'
            service._devices["localhost:5555"] = mock_device

            result = await service.get_ui_hierarchy("localhost:5555")

            assert result is not None
            assert "hierarchy" in result


@pytest.mark.asyncio
class TestADBServiceApps:
    """Tests for app operations."""

    async def test_install_apk_success(self):
        """Test successful APK installation."""
        with patch("src.services.adb_service.adb"):
            from src.services.adb_service import ADBService
            service = ADBService()

            mock_device = MagicMock()
            service._devices["localhost:5555"] = mock_device

            result = await service.install_apk("localhost:5555", "/path/to/app.apk")

            assert result is True
            mock_device.install.assert_called_once_with("/path/to/app.apk")

    async def test_install_apk_failure(self):
        """Test APK installation failure."""
        with patch("src.services.adb_service.adb"):
            from src.services.adb_service import ADBService
            service = ADBService()

            mock_device = MagicMock()
            mock_device.install.side_effect = Exception("Installation failed")
            service._devices["localhost:5555"] = mock_device

            result = await service.install_apk("localhost:5555", "/path/to/app.apk")

            assert result is False

    async def test_launch_app_success(self):
        """Test successful app launch."""
        with patch("src.services.adb_service.adb"):
            from src.services.adb_service import ADBService
            service = ADBService()

            mock_device = MagicMock()
            service._devices["localhost:5555"] = mock_device

            result = await service.launch_app("localhost:5555", "com.example.app")

            assert result is True
            mock_device.shell.assert_called_once_with(
                "monkey -p com.example.app -c android.intent.category.LAUNCHER 1"
            )

    async def test_launch_app_not_connected(self):
        """Test app launch when not connected."""
        with patch("src.services.adb_service.adb") as mock_adb:
            # Simulate device not found
            mock_adb.device.side_effect = Exception("device not found")

            from src.services.adb_service import ADBService
            service = ADBService()

            result = await service.launch_app("localhost:5555", "com.example.app")

            assert result is False
