"""Fingerprint service for managing device fingerprints."""

import json
import random
import secrets
import time
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

import structlog

from src.config import settings

logger = structlog.get_logger()


class FingerprintService:
    """Service for loading and managing device fingerprints."""

    def __init__(self):
        self._fingerprints: dict[str, dict[str, Any]] = {}
        self._load_fingerprints()

    def _load_fingerprints(self) -> None:
        """Load fingerprints from JSON file."""
        fingerprints_path = Path(settings.fingerprints_path)

        if not fingerprints_path.exists():
            logger.warning(
                "Fingerprints file not found",
                path=str(fingerprints_path),
            )
            return

        try:
            with open(fingerprints_path) as f:
                data = json.load(f)

            for device in data.get("devices", []):
                device_id = device.get("id")
                if device_id:
                    self._fingerprints[device_id] = device
                    logger.debug("Loaded fingerprint", device_id=device_id)

            logger.info(
                "Loaded device fingerprints",
                count=len(self._fingerprints),
            )
        except Exception as e:
            logger.error(
                "Failed to load fingerprints",
                error=str(e),
            )

    def get_all_fingerprints(self) -> list[dict[str, Any]]:
        """Get all available device fingerprints."""
        return list(self._fingerprints.values())

    def get_fingerprint(self, device_id: str) -> dict[str, Any] | None:
        """Get a specific device fingerprint by ID."""
        return self._fingerprints.get(device_id)

    def get_fingerprint_ids(self) -> list[str]:
        """Get list of all fingerprint IDs."""
        return list(self._fingerprints.keys())

    def search_fingerprints(
        self,
        brand: str | None = None,
        model: str | None = None,
        android_version: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search fingerprints by criteria."""
        results = []

        for fp in self._fingerprints.values():
            if brand and fp.get("brand", "").lower() != brand.lower():
                continue
            if model and model.lower() not in fp.get("model", "").lower():
                continue
            if android_version and fp.get("android_version") != android_version:
                continue
            results.append(fp)

        return results

    def generate_random_fingerprint(self) -> dict[str, Any]:
        """Generate a random fingerprint based on existing device profiles.

        Picks a random device from the loaded profiles and generates unique
        identifiers (Android ID, serial number, MAC addresses) while keeping
        the device-specific parameters consistent.
        """
        fingerprints = self.get_all_fingerprints()
        if not fingerprints:
            # Fallback to a default Pixel fingerprint
            base = {
                "id": "random-pixel-8",
                "name": "Random Pixel 8",
                "model": "Pixel 8",
                "brand": "google",
                "manufacturer": "Google",
                "product": "shiba",
                "device": "shiba",
                "build_fingerprint": "google/shiba/shiba:14/UD1A.231105.004/11010374:user/release-keys",
                "build_id": "UD1A.231105.004",
                "build_display": "UD1A.231105.004",
                "build_incremental": "11010374",
                "build_type": "user",
                "build_tags": "release-keys",
                "android_version": "14",
                "sdk_version": "34",
                "screen": {"width": 1080, "height": 2400, "dpi": 420, "refresh_rate": 120},
                "hardware": "shiba",
                "board": "shiba",
                "platform": "gs201",
                "bootloader": "shiba-14.0.0",
                "cpu_abi": "arm64-v8a",
                "supported_abis": ["arm64-v8a", "armeabi-v7a", "armeabi"],
                "gl_renderer": "Mali-G715 Immortalis MC10",
                "gl_vendor": "ARM",
                "wifi_mac_prefix": "3C:28:6D",
                "bluetooth_mac_prefix": "3C:28:6E",
                "timezone": "America/Los_Angeles",
                "locale": "en_US",
                "language": "en",
                "region": "US",
            }
        else:
            # Pick a random device profile
            base = random.choice(fingerprints).copy()

        # Generate unique identifiers
        base["android_id"] = secrets.token_hex(8)  # 16 char hex string
        base["serial"] = self._generate_serial(base.get("brand", ""))

        # Generate unique MAC addresses based on prefix
        wifi_prefix = base.get("wifi_mac_prefix", "02:00:00")
        bt_prefix = base.get("bluetooth_mac_prefix", "02:00:01")
        base["wifi_mac"] = self._generate_mac(wifi_prefix)
        base["bluetooth_mac"] = self._generate_mac(bt_prefix)

        # P1 Fingerprinting: Google Service IDs
        base["gsf_id"] = self._generate_gsf_id()  # Google Services Framework ID
        base["gaid"] = self._generate_gaid()  # Google Advertising ID

        # P1 Fingerprinting: System uptime (realistic boot time)
        # Set boot time to 1-7 days ago for realism
        days_ago = random.randint(1, 7)
        hours_ago = random.randint(0, 23)
        base["boot_time"] = int(time.time()) - (days_ago * 86400) - (hours_ago * 3600)

        # Mark as randomly generated
        base["id"] = f"random-{secrets.token_hex(4)}"
        base["name"] = f"Random {base.get('name', 'Device')}"

        logger.info(
            "Generated random fingerprint",
            device_id=base["id"],
            model=base.get("model"),
            brand=base.get("brand"),
        )

        return base

    def _generate_serial(self, brand: str) -> str:
        """Generate a realistic serial number based on brand."""
        brand_lower = brand.lower()
        if brand_lower in ("samsung",):
            # Samsung: R5CR30xxxxx format
            return f"R5CR{secrets.token_hex(5).upper()[:10]}"
        elif brand_lower in ("google",):
            # Pixel: 9A2xxxxxxxxxxxxx format
            return f"9A2{secrets.token_hex(7).upper()}"
        elif brand_lower in ("oneplus",):
            # OnePlus: NB2A... format
            return f"NB2A{secrets.token_hex(6).upper()}"
        elif brand_lower in ("xiaomi", "redmi"):
            # Xiaomi: random alphanumeric
            return secrets.token_hex(8).upper()
        else:
            # Generic: uppercase alphanumeric
            return secrets.token_hex(6).upper()

    def _generate_mac(self, prefix: str) -> str:
        """Generate a MAC address with the given 3-byte prefix."""
        # prefix format: "XX:XX:XX"
        suffix = ":".join(f"{random.randint(0, 255):02X}" for _ in range(3))
        return f"{prefix}:{suffix}"

    def _generate_gsf_id(self) -> str:
        """Generate a Google Services Framework ID.

        GSF ID is a 64-bit signed integer stored as decimal string.
        Format: 16-19 digit decimal number (can be negative).
        """
        # Generate a random 64-bit signed integer
        gsf_int = random.randint(-(2**63), (2**63) - 1)
        return str(gsf_int)

    def _generate_gaid(self) -> str:
        """Generate a Google Advertising ID (GAID).

        GAID is a standard UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
        """
        return str(uuid.uuid4())

    def fingerprint_to_env(self, fingerprint: dict[str, Any]) -> dict[str, str]:
        """Convert fingerprint dict to environment variables for Docker.

        Converts 25+ fingerprint parameters to Docker environment variables
        that will be used by inject-fingerprint.sh at container boot.
        """
        screen = fingerprint.get("screen", {})
        supported_abis = fingerprint.get("supported_abis", ["arm64-v8a", "armeabi-v7a", "armeabi"])

        return {
            # Device identity
            "DEVICE_MODEL": fingerprint.get("model", ""),
            "DEVICE_BRAND": fingerprint.get("brand", ""),
            "DEVICE_MANUFACTURER": fingerprint.get("manufacturer", ""),
            "DEVICE_PRODUCT": fingerprint.get("product", fingerprint.get("model", "")),
            "DEVICE_NAME": fingerprint.get("device", fingerprint.get("product", "")),
            # Build info
            "BUILD_FINGERPRINT": fingerprint.get("build_fingerprint", ""),
            "BUILD_ID": fingerprint.get("build_id", ""),
            "BUILD_DISPLAY": fingerprint.get("build_display", ""),
            "BUILD_INCREMENTAL": fingerprint.get("build_incremental", ""),
            "BUILD_TYPE": fingerprint.get("build_type", "user"),
            "BUILD_TAGS": fingerprint.get("build_tags", "release-keys"),
            # Android version
            "SDK_VERSION": fingerprint.get("sdk_version", "34"),
            "ANDROID_VERSION": fingerprint.get("android_version", "14"),
            # Hardware
            "HARDWARE": fingerprint.get("hardware", ""),
            "BOARD": fingerprint.get("board", ""),
            "PLATFORM": fingerprint.get("platform", fingerprint.get("board", "")),
            "BOOTLOADER": fingerprint.get("bootloader", "unknown"),
            "CPU_ABI": fingerprint.get("cpu_abi", "arm64-v8a"),
            "SUPPORTED_ABIS": ",".join(supported_abis),
            # Display
            "DEVICE_WIDTH": str(screen.get("width", 1080)),
            "DEVICE_HEIGHT": str(screen.get("height", 2400)),
            "DEVICE_DPI": str(screen.get("dpi", 420)),
            "REFRESH_RATE": str(screen.get("refresh_rate", 60)),
            # Graphics (WebGL spoofing)
            "GL_RENDERER": fingerprint.get("gl_renderer", ""),
            "GL_VENDOR": fingerprint.get("gl_vendor", ""),
            # Network MAC prefixes (for generating unique MACs)
            "WIFI_MAC_PREFIX": fingerprint.get("wifi_mac_prefix", ""),
            "BLUETOOTH_MAC_PREFIX": fingerprint.get("bluetooth_mac_prefix", ""),
            # Serial/IDs (generated at runtime if not provided)
            "ANDROID_ID": fingerprint.get("android_id", ""),
            "DEVICE_SERIAL": fingerprint.get("serial", ""),
            # Locale/Region
            "TIMEZONE": fingerprint.get("timezone", "America/New_York"),
            "LOCALE": fingerprint.get("locale", "en_US"),
            "LANGUAGE": fingerprint.get("language", "en"),
            "REGION": fingerprint.get("region", "US"),
            # P1: Google Service IDs
            "GSF_ID": fingerprint.get("gsf_id", ""),
            "GAID": fingerprint.get("gaid", ""),
            # P1: System uptime spoofing
            "BOOT_TIME": str(fingerprint.get("boot_time", "")),
        }


@lru_cache
def get_fingerprint_service() -> FingerprintService:
    """Get cached fingerprint service instance."""
    return FingerprintService()
