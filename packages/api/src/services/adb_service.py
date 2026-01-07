"""ADB service for Android device control."""

import asyncio
import base64
from io import BytesIO
from typing import Any

from adbutils import adb, AdbDevice
from PIL import Image
import structlog

from src.config import settings

logger = structlog.get_logger()


class ADBService:
    """Service for ADB device control."""

    def __init__(self):
        self._devices: dict[str, AdbDevice] = {}

    async def connect(self, host: str, port: int, timeout: int = 30) -> bool:
        """Connect to an ADB device."""
        address = f"{host}:{port}"

        try:
            # Run connect in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: adb.connect(address, timeout=timeout),
            )

            if result:
                device = adb.device(serial=address)
                self._devices[address] = device
                logger.info("Connected to device", address=address)
                return True
            else:
                logger.warning("Failed to connect", address=address)
                return False

        except Exception as e:
            logger.error("ADB connect error", error=str(e), address=address)
            return False

    async def disconnect(self, address: str) -> bool:
        """Disconnect from an ADB device."""
        try:
            adb.disconnect(address)
            self._devices.pop(address, None)
            logger.info("Disconnected from device", address=address)
            return True
        except Exception as e:
            logger.error("ADB disconnect error", error=str(e))
            return False

    def get_device(self, address: str) -> AdbDevice | None:
        """Get a connected device."""
        return self._devices.get(address)

    async def screenshot(self, address: str) -> bytes | None:
        """Take a screenshot of the device."""
        device = self._devices.get(address)
        if not device:
            logger.warning("Device not connected", address=address)
            return None

        try:
            loop = asyncio.get_event_loop()
            image = await loop.run_in_executor(None, device.screenshot)

            # Convert PIL Image to bytes
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            return buffer.getvalue()

        except Exception as e:
            logger.error("Screenshot error", error=str(e), address=address)
            return None

    async def screenshot_base64(self, address: str) -> str | None:
        """Take a screenshot and return as base64."""
        screenshot = await self.screenshot(address)
        if screenshot:
            return base64.b64encode(screenshot).decode("utf-8")
        return None

    async def tap(self, address: str, x: int, y: int) -> bool:
        """Tap at coordinates."""
        device = self._devices.get(address)
        if not device:
            return False

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: device.click(x, y))
            logger.debug("Tap", address=address, x=x, y=y)
            return True
        except Exception as e:
            logger.error("Tap error", error=str(e))
            return False

    async def swipe(
        self,
        address: str,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration: int = 300,
    ) -> bool:
        """Swipe gesture."""
        device = self._devices.get(address)
        if not device:
            return False

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: device.swipe(x1, y1, x2, y2, duration / 1000),
            )
            logger.debug("Swipe", address=address, x1=x1, y1=y1, x2=x2, y2=y2)
            return True
        except Exception as e:
            logger.error("Swipe error", error=str(e))
            return False

    async def input_text(self, address: str, text: str) -> bool:
        """Input text."""
        device = self._devices.get(address)
        if not device:
            return False

        try:
            # Escape special characters for shell
            escaped = text.replace("'", "'\\''")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: device.shell(f"input text '{escaped}'"),
            )
            logger.debug("Input text", address=address, length=len(text))
            return True
        except Exception as e:
            logger.error("Input text error", error=str(e))
            return False

    async def press_key(self, address: str, keycode: str) -> bool:
        """Press a key."""
        device = self._devices.get(address)
        if not device:
            return False

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: device.shell(f"input keyevent {keycode}"),
            )
            logger.debug("Key press", address=address, keycode=keycode)
            return True
        except Exception as e:
            logger.error("Key press error", error=str(e))
            return False

    async def press_back(self, address: str) -> bool:
        """Press back button."""
        return await self.press_key(address, "KEYCODE_BACK")

    async def press_home(self, address: str) -> bool:
        """Press home button."""
        return await self.press_key(address, "KEYCODE_HOME")

    async def press_enter(self, address: str) -> bool:
        """Press enter key."""
        return await self.press_key(address, "KEYCODE_ENTER")

    async def get_ui_hierarchy(self, address: str) -> str | None:
        """Get UI hierarchy XML."""
        device = self._devices.get(address)
        if not device:
            return None

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: device.shell("uiautomator dump /dev/tty"),
            )
            return result
        except Exception as e:
            logger.error("UI hierarchy error", error=str(e))
            return None

    async def shell(self, address: str, command: str) -> str | None:
        """Execute shell command."""
        device = self._devices.get(address)
        if not device:
            return None

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: device.shell(command),
            )
            return result
        except Exception as e:
            logger.error("Shell command error", error=str(e))
            return None

    async def get_device_info(self, address: str) -> dict[str, Any] | None:
        """Get device information."""
        device = self._devices.get(address)
        if not device:
            return None

        try:
            loop = asyncio.get_event_loop()

            async def get_prop(prop: str) -> str:
                result = await loop.run_in_executor(
                    None,
                    lambda: device.shell(f"getprop {prop}"),
                )
                return result.strip()

            model = await get_prop("ro.product.model")
            brand = await get_prop("ro.product.brand")
            manufacturer = await get_prop("ro.product.manufacturer")
            android_version = await get_prop("ro.build.version.release")
            sdk_version = await get_prop("ro.build.version.sdk")
            fingerprint = await get_prop("ro.build.fingerprint")

            return {
                "model": model,
                "brand": brand,
                "manufacturer": manufacturer,
                "android_version": android_version,
                "sdk_version": sdk_version,
                "fingerprint": fingerprint,
            }

        except Exception as e:
            logger.error("Get device info error", error=str(e))
            return None

    async def install_apk(self, address: str, apk_path: str) -> bool:
        """Install an APK."""
        device = self._devices.get(address)
        if not device:
            return False

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: device.install(apk_path))
            logger.info("Installed APK", address=address, path=apk_path)
            return True
        except Exception as e:
            logger.error("Install APK error", error=str(e))
            return False

    async def launch_app(self, address: str, package: str) -> bool:
        """Launch an app by package name."""
        device = self._devices.get(address)
        if not device:
            return False

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: device.shell(
                    f"monkey -p {package} -c android.intent.category.LAUNCHER 1"
                ),
            )
            logger.info("Launched app", address=address, package=package)
            return True
        except Exception as e:
            logger.error("Launch app error", error=str(e))
            return False
