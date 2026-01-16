"""Quick App Install service for Aurora Store automation."""

import asyncio
from typing import Any
from enum import Enum

import structlog

from src.services.adb_service import ADBService

logger = structlog.get_logger()


class AppCategory(str, Enum):
    SOCIAL = "social"
    MESSAGING = "messaging"
    PRODUCTIVITY = "productivity"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"


# Popular apps with their package names
POPULAR_APPS: dict[str, dict[str, Any]] = {
    # Social Media
    "instagram": {
        "package": "com.instagram.android",
        "name": "Instagram",
        "category": AppCategory.SOCIAL,
    },
    "threads": {
        "package": "com.instagram.barcelona",
        "name": "Threads",
        "category": AppCategory.SOCIAL,
    },
    "tiktok": {
        "package": "com.zhiliaoapp.musically",
        "name": "TikTok",
        "category": AppCategory.SOCIAL,
    },
    "twitter": {
        "package": "com.twitter.android",
        "name": "X (Twitter)",
        "category": AppCategory.SOCIAL,
    },
    "facebook": {
        "package": "com.facebook.katana",
        "name": "Facebook",
        "category": AppCategory.SOCIAL,
    },
    "snapchat": {
        "package": "com.snapchat.android",
        "name": "Snapchat",
        "category": AppCategory.SOCIAL,
    },
    "reddit": {
        "package": "com.reddit.frontpage",
        "name": "Reddit",
        "category": AppCategory.SOCIAL,
    },
    "linkedin": {
        "package": "com.linkedin.android",
        "name": "LinkedIn",
        "category": AppCategory.SOCIAL,
    },
    # Messaging
    "whatsapp": {
        "package": "com.whatsapp",
        "name": "WhatsApp",
        "category": AppCategory.MESSAGING,
    },
    "telegram": {
        "package": "org.telegram.messenger",
        "name": "Telegram",
        "category": AppCategory.MESSAGING,
    },
    "signal": {
        "package": "org.thoughtcrime.securesms",
        "name": "Signal",
        "category": AppCategory.MESSAGING,
    },
    "messenger": {
        "package": "com.facebook.orca",
        "name": "Messenger",
        "category": AppCategory.MESSAGING,
    },
    "discord": {
        "package": "com.discord",
        "name": "Discord",
        "category": AppCategory.MESSAGING,
    },
    # Productivity
    "gmail": {
        "package": "com.google.android.gm",
        "name": "Gmail",
        "category": AppCategory.PRODUCTIVITY,
    },
    "chrome": {
        "package": "com.android.chrome",
        "name": "Chrome",
        "category": AppCategory.PRODUCTIVITY,
    },
    "drive": {
        "package": "com.google.android.apps.docs",
        "name": "Google Drive",
        "category": AppCategory.PRODUCTIVITY,
    },
    "sheets": {
        "package": "com.google.android.apps.docs.editors.sheets",
        "name": "Google Sheets",
        "category": AppCategory.PRODUCTIVITY,
    },
    # Entertainment
    "youtube": {
        "package": "com.google.android.youtube",
        "name": "YouTube",
        "category": AppCategory.ENTERTAINMENT,
    },
    "spotify": {
        "package": "com.spotify.music",
        "name": "Spotify",
        "category": AppCategory.ENTERTAINMENT,
    },
    "netflix": {
        "package": "com.netflix.mediaclient",
        "name": "Netflix",
        "category": AppCategory.ENTERTAINMENT,
    },
    # Utilities
    "aurora": {
        "package": "com.aurora.store",
        "name": "Aurora Store",
        "category": AppCategory.UTILITIES,
    },
}

# App bundles for one-click multi-app install
APP_BUNDLES: dict[str, dict[str, Any]] = {
    "social_media": {
        "name": "Social Media Pack",
        "description": "Instagram, Threads, TikTok, Twitter",
        "apps": ["instagram", "threads", "tiktok", "twitter"],
    },
    "meta_suite": {
        "name": "Meta Suite",
        "description": "Instagram, Threads, Facebook, WhatsApp, Messenger",
        "apps": ["instagram", "threads", "facebook", "whatsapp", "messenger"],
    },
    "messaging": {
        "name": "Messaging Pack",
        "description": "WhatsApp, Telegram, Signal, Discord",
        "apps": ["whatsapp", "telegram", "signal", "discord"],
    },
    "google_essentials": {
        "name": "Google Essentials",
        "description": "Gmail, Chrome, Drive, YouTube",
        "apps": ["gmail", "chrome", "drive", "youtube"],
    },
    "content_creator": {
        "name": "Content Creator Pack",
        "description": "Instagram, TikTok, YouTube, Twitter",
        "apps": ["instagram", "tiktok", "youtube", "twitter"],
    },
}


class AppInstallService:
    """Service for quick app installation via Aurora Store."""

    # Aurora Store package name
    AURORA_PACKAGE = "com.aurora.store"

    def __init__(self, adb_service: ADBService):
        self.adb = adb_service

    def list_apps(self, category: AppCategory | None = None) -> list[dict[str, Any]]:
        """List available apps, optionally filtered by category."""
        apps = []
        for app_id, app_info in POPULAR_APPS.items():
            if category is None or app_info["category"] == category:
                apps.append({
                    "id": app_id,
                    "package": app_info["package"],
                    "name": app_info["name"],
                    "category": app_info["category"].value,
                })
        return apps

    def list_bundles(self) -> list[dict[str, Any]]:
        """List available app bundles."""
        bundles = []
        for bundle_id, bundle_info in APP_BUNDLES.items():
            bundles.append({
                "id": bundle_id,
                "name": bundle_info["name"],
                "description": bundle_info["description"],
                "apps": bundle_info["apps"],
                "app_count": len(bundle_info["apps"]),
            })
        return bundles

    def get_bundle(self, bundle_id: str) -> dict[str, Any] | None:
        """Get bundle details with full app info."""
        bundle = APP_BUNDLES.get(bundle_id)
        if not bundle:
            return None

        apps = []
        for app_id in bundle["apps"]:
            if app_id in POPULAR_APPS:
                app_info = POPULAR_APPS[app_id]
                apps.append({
                    "id": app_id,
                    "package": app_info["package"],
                    "name": app_info["name"],
                })

        return {
            "id": bundle_id,
            "name": bundle["name"],
            "description": bundle["description"],
            "apps": apps,
        }

    async def is_aurora_installed(self, adb_address: str) -> bool:
        """Check if Aurora Store is installed."""
        result = await self.adb.shell(
            adb_address,
            f"pm list packages | grep {self.AURORA_PACKAGE}"
        )
        return result is not None and self.AURORA_PACKAGE in result

    async def is_app_installed(self, adb_address: str, package_name: str) -> bool:
        """Check if an app is installed."""
        result = await self.adb.shell(
            adb_address,
            f"pm list packages | grep {package_name}"
        )
        return result is not None and package_name in result

    async def open_in_aurora(self, adb_address: str, package_name: str) -> bool:
        """Open app details page in Aurora Store.

        This opens the Aurora Store app to the specific app's page,
        where the user (or AI agent) can click Install.
        """
        # Check if Aurora Store is installed
        if not await self.is_aurora_installed(adb_address):
            logger.error("Aurora Store not installed", address=adb_address)
            return False

        # Launch Aurora Store with market intent
        # This opens the app details page directly
        cmd = (
            f"am start -a android.intent.action.VIEW "
            f"-d 'market://details?id={package_name}' "
            f"-n {self.AURORA_PACKAGE}/.ui.main.AuroraActivity"
        )

        result = await self.adb.shell(adb_address, cmd)

        if result is not None:
            logger.info(
                "Opened app in Aurora Store",
                address=adb_address,
                package=package_name,
            )
            return True
        return False

    async def open_app_by_id(self, adb_address: str, app_id: str) -> bool:
        """Open app in Aurora Store by our app ID (e.g., 'instagram')."""
        app_info = POPULAR_APPS.get(app_id)
        if not app_info:
            logger.error("Unknown app ID", app_id=app_id)
            return False

        return await self.open_in_aurora(adb_address, app_info["package"])

    async def install_app(
        self,
        adb_address: str,
        app_id: str,
        wait_for_install: bool = True,
        timeout: int = 120,
    ) -> dict[str, Any]:
        """Install an app via Aurora Store with automated clicking.

        This opens Aurora Store, waits for page load, and clicks Install.

        Args:
            adb_address: ADB device address
            app_id: App ID (e.g., 'instagram')
            wait_for_install: Wait for installation to complete
            timeout: Timeout in seconds

        Returns:
            Dict with success status and details
        """
        app_info = POPULAR_APPS.get(app_id)
        if not app_info:
            return {"success": False, "error": f"Unknown app ID: {app_id}"}

        package_name = app_info["package"]

        # Check if already installed
        if await self.is_app_installed(adb_address, package_name):
            return {
                "success": True,
                "already_installed": True,
                "app": app_info["name"],
                "package": package_name,
            }

        # Open in Aurora Store
        if not await self.open_in_aurora(adb_address, package_name):
            return {"success": False, "error": "Failed to open Aurora Store"}

        # Wait for Aurora Store to load the app page
        await asyncio.sleep(3)

        # Try to click the Install button
        # Aurora Store's Install button is typically in the upper right area
        # We'll try a few common positions
        install_clicked = False

        # Common Install button positions (varies by screen resolution)
        # These are approximate for 1080p screens
        install_positions = [
            (900, 400),   # Upper right area
            (540, 500),   # Center area
            (800, 350),   # Alternative upper right
        ]

        for x, y in install_positions:
            # First, let's try to find "Install" text in UI dump
            ui_dump = await self.adb.get_ui_hierarchy(adb_address)
            if ui_dump and "Install" in ui_dump:
                # Found install button, try clicking
                await self.adb.tap(adb_address, x, y)
                install_clicked = True
                logger.info("Clicked Install button", x=x, y=y)
                break

        if not install_clicked:
            # Fallback: just tap likely position
            await self.adb.tap(adb_address, 900, 400)
            logger.warning("Install button not found, tapped fallback position")

        if wait_for_install:
            # Wait and check if installation succeeded
            for _ in range(timeout // 5):
                await asyncio.sleep(5)
                if await self.is_app_installed(adb_address, package_name):
                    return {
                        "success": True,
                        "installed": True,
                        "app": app_info["name"],
                        "package": package_name,
                    }

            return {
                "success": False,
                "error": "Installation timed out",
                "app": app_info["name"],
                "package": package_name,
            }

        return {
            "success": True,
            "install_initiated": True,
            "app": app_info["name"],
            "package": package_name,
        }

    async def install_bundle(
        self,
        adb_address: str,
        bundle_id: str,
        sequential: bool = True,
    ) -> dict[str, Any]:
        """Install all apps in a bundle.

        Args:
            adb_address: ADB device address
            bundle_id: Bundle ID (e.g., 'social_media')
            sequential: Install one at a time (recommended)

        Returns:
            Dict with results for each app
        """
        bundle = APP_BUNDLES.get(bundle_id)
        if not bundle:
            return {"success": False, "error": f"Unknown bundle: {bundle_id}"}

        results = {
            "bundle": bundle["name"],
            "apps": [],
            "success_count": 0,
            "fail_count": 0,
            "skip_count": 0,
        }

        for app_id in bundle["apps"]:
            result = await self.install_app(
                adb_address,
                app_id,
                wait_for_install=sequential,
            )

            results["apps"].append({
                "app_id": app_id,
                **result,
            })

            if result.get("success"):
                if result.get("already_installed"):
                    results["skip_count"] += 1
                else:
                    results["success_count"] += 1
            else:
                results["fail_count"] += 1

            # Small delay between apps
            if sequential:
                await asyncio.sleep(2)

        results["success"] = results["fail_count"] == 0
        return results

    async def launch_app(self, adb_address: str, app_id: str) -> bool:
        """Launch an installed app."""
        app_info = POPULAR_APPS.get(app_id)
        if not app_info:
            logger.error("Unknown app ID", app_id=app_id)
            return False

        package_name = app_info["package"]

        # Use monkey to launch the app (works without knowing main activity)
        cmd = f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
        result = await self.adb.shell(adb_address, cmd)

        if result is not None:
            logger.info("Launched app", app_id=app_id, package=package_name)
            return True
        return False

    async def get_installed_apps(
        self,
        adb_address: str,
        known_only: bool = True,
    ) -> list[dict[str, Any]]:
        """Get list of installed apps.

        Args:
            adb_address: ADB device address
            known_only: Only return apps we know about

        Returns:
            List of installed apps
        """
        result = await self.adb.shell(adb_address, "pm list packages")
        if not result:
            return []

        installed_packages = set(
            line.replace("package:", "").strip()
            for line in result.strip().split("\n")
            if line.startswith("package:")
        )

        apps = []
        for app_id, app_info in POPULAR_APPS.items():
            if app_info["package"] in installed_packages:
                apps.append({
                    "id": app_id,
                    "package": app_info["package"],
                    "name": app_info["name"],
                    "category": app_info["category"].value,
                    "installed": True,
                })

        return apps
