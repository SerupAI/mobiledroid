"""Fingerprint service for managing device fingerprints."""

import json
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

    def fingerprint_to_env(self, fingerprint: dict[str, Any]) -> dict[str, str]:
        """Convert fingerprint dict to environment variables for Docker."""
        screen = fingerprint.get("screen", {})

        return {
            "DEVICE_MODEL": fingerprint.get("model", ""),
            "DEVICE_BRAND": fingerprint.get("brand", ""),
            "DEVICE_MANUFACTURER": fingerprint.get("manufacturer", ""),
            "DEVICE_PRODUCT": fingerprint.get("product", fingerprint.get("model", "")),
            "BUILD_FINGERPRINT": fingerprint.get("build_fingerprint", ""),
            "ANDROID_ID": fingerprint.get("android_id", ""),
            "DEVICE_SERIAL": fingerprint.get("serial", ""),
            "DEVICE_WIDTH": str(screen.get("width", 1080)),
            "DEVICE_HEIGHT": str(screen.get("height", 2400)),
            "DEVICE_DPI": str(screen.get("dpi", 420)),
            "SDK_VERSION": fingerprint.get("sdk_version", "34"),
            "ANDROID_VERSION": fingerprint.get("android_version", "14"),
            "HARDWARE": fingerprint.get("hardware", ""),
            "BOARD": fingerprint.get("board", ""),
            "TIMEZONE": fingerprint.get("timezone", "America/New_York"),
            "LOCALE": fingerprint.get("locale", "en_US"),
        }


@lru_cache
def get_fingerprint_service() -> FingerprintService:
    """Get cached fingerprint service instance."""
    return FingerprintService()
