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

    async def list_devices(self) -> list[str]:
        """List connected ADB devices."""
        try:
            loop = asyncio.get_event_loop()
            devices = await loop.run_in_executor(None, adb.device_list)
            return [d.serial for d in devices]
        except Exception as e:
            logger.error("List devices error", error=str(e))
            return []

    async def screenshot(self, address: str) -> bytes | None:
        """Take a screenshot of the device."""
        device = self._devices.get(address)

        # Try to get device directly if not in cache
        if not device:
            try:
                device = adb.device(serial=address)
                self._devices[address] = device
            except Exception as e:
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
            # Clear from cache on error
            self._devices.pop(address, None)
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
        
        # Try to get device directly if not in cache
        if not device:
            try:
                device = adb.device(serial=address)
                self._devices[address] = device
            except Exception as e:
                logger.warning("Device not connected", address=address)
                return False

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: device.click(x, y))
            logger.debug("Tap", address=address, x=x, y=y)
            return True
        except Exception as e:
            logger.error("Tap error", error=str(e))
            # Clear from cache on error
            self._devices.pop(address, None)
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
        
        # Try to get device directly if not in cache
        if not device:
            try:
                device = adb.device(serial=address)
                self._devices[address] = device
            except Exception as e:
                logger.warning("Device not connected", address=address)
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
            # Clear from cache on error
            self._devices.pop(address, None)
            return False

    async def input_text(self, address: str, text: str) -> bool:
        """Input text."""
        device = self._devices.get(address)
        
        # Try to get device directly if not in cache
        if not device:
            try:
                device = adb.device(serial=address)
                self._devices[address] = device
            except Exception as e:
                logger.warning("Device not connected", address=address)
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
            # Clear from cache on error
            self._devices.pop(address, None)
            return False

    async def press_key(self, address: str, keycode: str) -> bool:
        """Press a key."""
        device = self._devices.get(address)
        
        # Try to get device directly if not in cache
        if not device:
            try:
                device = adb.device(serial=address)
                self._devices[address] = device
            except Exception as e:
                logger.warning("Device not connected", address=address)
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
            # Clear from cache on error
            self._devices.pop(address, None)
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
        
        # Try to get device directly if not in cache
        if not device:
            try:
                device = adb.device(serial=address)
                self._devices[address] = device
            except Exception as e:
                logger.warning("Device not connected", address=address)
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
            self._devices.pop(address, None)
            return None

    async def shell(self, address: str, command: str) -> str | None:
        """Execute shell command."""
        device = self._devices.get(address)
        
        # Try to get device directly if not in cache
        if not device:
            try:
                device = adb.device(serial=address)
                self._devices[address] = device
            except Exception as e:
                logger.warning("Device not connected", address=address)
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
            self._devices.pop(address, None)
            return None

    async def get_device_info(self, address: str) -> dict[str, Any] | None:
        """Get device information."""
        device = self._devices.get(address)
        
        # Try to get device directly if not in cache
        if not device:
            try:
                device = adb.device(serial=address)
                self._devices[address] = device
            except Exception as e:
                logger.warning("Device not connected", address=address)
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
        
        # Try to get device directly if not in cache
        if not device:
            try:
                device = adb.device(serial=address)
                self._devices[address] = device
            except Exception as e:
                logger.warning("Device not connected", address=address)
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

        # Try to get device directly if not in cache
        if not device:
            try:
                device = adb.device(serial=address)
                self._devices[address] = device
            except Exception as e:
                logger.warning("Device not connected", address=address)
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

    async def set_proxy(
        self,
        address: str,
        proxy_type: str,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> bool:
        """Configure HTTP proxy on the device.

        Note: Android natively supports HTTP proxies. SOCKS5 requires additional
        setup (like redsocks) which is not currently implemented.

        Args:
            address: ADB device address
            proxy_type: 'none', 'http', or 'socks5'
            host: Proxy host
            port: Proxy port
            username: Proxy username (optional)
            password: Proxy password (optional)

        Returns:
            True if proxy was configured successfully
        """
        device = self._devices.get(address)

        # Try to get device directly if not in cache
        if not device:
            try:
                device = adb.device(serial=address)
                self._devices[address] = device
            except Exception as e:
                logger.warning("Device not connected", address=address)
                return False

        loop = asyncio.get_event_loop()

        try:
            if proxy_type == "none" or not host:
                # Clear proxy settings
                await loop.run_in_executor(
                    None,
                    lambda: device.shell("settings put global http_proxy :0"),
                )
                logger.info("Cleared proxy settings", address=address)
                return True

            if proxy_type == "socks5":
                # SOCKS5 not natively supported - would need redsocks
                logger.warning(
                    "SOCKS5 proxy not yet implemented",
                    address=address,
                    host=host,
                    port=port,
                )
                # For now, we'll skip SOCKS5 but log it
                return False

            # HTTP proxy
            proxy_str = f"{host}:{port}"

            # Set global HTTP proxy
            await loop.run_in_executor(
                None,
                lambda: device.shell(f"settings put global http_proxy {proxy_str}"),
            )

            logger.info(
                "Set HTTP proxy",
                address=address,
                proxy=proxy_str,
                has_auth=bool(username),
            )
            return True

        except Exception as e:
            logger.error("Set proxy error", error=str(e), address=address)
            return False

    async def get_proxy(self, address: str) -> dict[str, Any] | None:
        """Get current proxy settings from the device."""
        result = await self.shell(address, "settings get global http_proxy")
        if result:
            result = result.strip()
            if result and result != "null" and result != ":0":
                parts = result.split(":")
                if len(parts) == 2:
                    return {
                        "type": "http",
                        "host": parts[0],
                        "port": int(parts[1]) if parts[1].isdigit() else None,
                    }
        return {"type": "none", "host": None, "port": None}

    async def clear_proxy(self, address: str) -> bool:
        """Clear proxy settings on the device."""
        return await self.set_proxy(address, "none")

    async def set_clipboard(self, address: str, text: str) -> bool:
        """Set clipboard text on the device.

        Uses ADB broadcast to set clipboard. Requires text to be properly escaped.
        Falls back to typing the text if broadcast fails.
        """
        device = self._devices.get(address)

        if not device:
            try:
                device = adb.device(serial=address)
                self._devices[address] = device
            except Exception as e:
                logger.warning("Device not connected", address=address)
                return False

        loop = asyncio.get_event_loop()

        try:
            # Escape the text for shell
            # Replace problematic characters
            escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")
            escaped = escaped.replace("$", "\\$").replace("`", "\\`")

            # Try to set clipboard via am broadcast (works with Clipper app if installed)
            try:
                result = await loop.run_in_executor(
                    None,
                    lambda: device.shell(
                        f'am broadcast -a clipper.set -e text "{escaped}"'
                    ),
                )
                if "Broadcast completed" in result:
                    logger.info("Set clipboard via broadcast", address=address, length=len(text))
                    return True
            except Exception:
                pass

            # Fallback: Use input text (this types the text, not clipboard)
            # This is useful when no clipboard app is available
            logger.debug("Clipboard broadcast not available, using input text", address=address)
            return await self.input_text(address, text)

        except Exception as e:
            logger.error("Set clipboard error", error=str(e), address=address)
            return False

    async def get_clipboard(self, address: str) -> str | None:
        """Get clipboard text from the device.

        Note: This requires either root access or a clipboard helper app.
        Returns None if clipboard cannot be read.
        """
        device = self._devices.get(address)

        if not device:
            try:
                device = adb.device(serial=address)
                self._devices[address] = device
            except Exception as e:
                logger.warning("Device not connected", address=address)
                return None

        loop = asyncio.get_event_loop()

        try:
            # Try to get clipboard via am broadcast (works with Clipper app if installed)
            result = await loop.run_in_executor(
                None,
                lambda: device.shell("am broadcast -a clipper.get"),
            )

            # Parse result for clipboard content
            # Clipper returns: "Broadcast completed: result=0, data="<text>""
            if "data=" in result:
                start = result.find('data="') + 6
                end = result.rfind('"')
                if start > 5 and end > start:
                    return result[start:end]

            logger.debug("Could not read clipboard", address=address)
            return None

        except Exception as e:
            logger.error("Get clipboard error", error=str(e), address=address)
            return None

    async def paste_text(self, address: str, text: str) -> bool:
        """Paste text by typing it on the device.

        This is the most reliable way to "paste" text when clipboard
        access is not available.
        """
        return await self.input_text(address, text)
