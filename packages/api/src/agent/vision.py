"""Vision utilities for the AI agent."""

import asyncio
import base64
import re
from io import BytesIO
from typing import Any

from adbutils import AdbDevice
from lxml import etree
from PIL import Image
import structlog

logger = structlog.get_logger()


class VisionService:
    """Service for capturing and processing device screen."""

    def __init__(self, device: AdbDevice):
        self.device = device

    async def capture_screenshot(self) -> tuple[bytes, int, int]:
        """Capture a screenshot from the device.

        Returns:
            Tuple of (png_bytes, width, height)
        """
        loop = asyncio.get_event_loop()
        image = await loop.run_in_executor(None, self.device.screenshot)

        # Get actual image dimensions
        width, height = image.size

        # Convert PIL Image to PNG bytes
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue(), width, height

    async def capture_screenshot_base64(self) -> tuple[str, int, int]:
        """Capture a screenshot and return as base64.

        Returns:
            Tuple of (base64_string, width, height)
        """
        screenshot_bytes, width, height = await self.capture_screenshot()
        return base64.standard_b64encode(screenshot_bytes).decode("utf-8"), width, height

    async def get_screen_size(self) -> tuple[int, int]:
        """Get the device screen dimensions."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, lambda: self.device.shell("wm size")
        )

        # Parse output like "Physical size: 1080x2400"
        match = re.search(r"(\d+)x(\d+)", result)
        if match:
            return int(match.group(1)), int(match.group(2))

        # Default fallback
        return 1080, 2400

    async def get_ui_hierarchy(self) -> str:
        """Get the UI hierarchy XML."""
        loop = asyncio.get_event_loop()

        # Dump UI hierarchy to a file, then read it
        # /dev/tty doesn't work reliably across all Android versions
        await loop.run_in_executor(
            None, lambda: self.device.shell("uiautomator dump /sdcard/ui_hierarchy.xml")
        )

        # Read the dumped file
        result = await loop.run_in_executor(
            None, lambda: self.device.shell("cat /sdcard/ui_hierarchy.xml")
        )

        return result

    async def get_ui_hierarchy_parsed(self) -> list[dict[str, Any]]:
        """Get a parsed and simplified UI hierarchy."""
        xml_str = await self.get_ui_hierarchy()

        try:
            # Parse the XML
            # Remove the "UI hierarch dumped to:" prefix if present
            xml_start = xml_str.find("<?xml")
            if xml_start == -1:
                xml_start = xml_str.find("<hierarchy")
            if xml_start == -1:
                return []

            xml_content = xml_str[xml_start:]
            root = etree.fromstring(xml_content.encode("utf-8"))

            elements = []
            self._parse_element(root, elements)
            return elements

        except Exception as e:
            logger.warning("Failed to parse UI hierarchy", error=str(e))
            return []

    def _parse_element(
        self, element: etree._Element, elements: list[dict[str, Any]]
    ) -> None:
        """Recursively parse UI elements."""
        # Extract relevant attributes
        bounds = element.get("bounds", "")
        text = element.get("text", "")
        content_desc = element.get("content-desc", "")
        resource_id = element.get("resource-id", "")
        class_name = element.get("class", "")
        clickable = element.get("clickable", "false") == "true"
        enabled = element.get("enabled", "true") == "true"
        focused = element.get("focused", "false") == "true"

        # Parse bounds [left,top][right,bottom]
        parsed_bounds = None
        if bounds:
            match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
            if match:
                parsed_bounds = {
                    "left": int(match.group(1)),
                    "top": int(match.group(2)),
                    "right": int(match.group(3)),
                    "bottom": int(match.group(4)),
                }

        # Only include meaningful elements
        if (text or content_desc or resource_id) and parsed_bounds:
            elements.append({
                "text": text,
                "content_desc": content_desc,
                "resource_id": resource_id,
                "class": class_name,
                "bounds": parsed_bounds,
                "center": {
                    "x": (parsed_bounds["left"] + parsed_bounds["right"]) // 2,
                    "y": (parsed_bounds["top"] + parsed_bounds["bottom"]) // 2,
                },
                "clickable": clickable,
                "enabled": enabled,
                "focused": focused,
            })

        # Recurse into children
        for child in element:
            self._parse_element(child, elements)

    async def get_state(self) -> dict[str, Any]:
        """Get the complete current state of the device."""
        # Capture screenshot and UI hierarchy in parallel
        screenshot_task = asyncio.create_task(self.capture_screenshot_base64())
        hierarchy_task = asyncio.create_task(self.get_ui_hierarchy_parsed())

        screenshot_result, ui_elements = await asyncio.gather(
            screenshot_task, hierarchy_task
        )

        # Unpack screenshot result (base64, width, height)
        screenshot_b64, img_width, img_height = screenshot_result

        return {
            "screenshot": screenshot_b64,
            "ui_elements": ui_elements,
            "screen_width": img_width,
            "screen_height": img_height,
        }

    def format_ui_for_prompt(
        self, ui_elements: list[dict[str, Any]], screen_width: int, screen_height: int
    ) -> str:
        """Format UI elements for inclusion in the prompt with percentage coordinates.

        Args:
            ui_elements: List of UI element dictionaries
            screen_width: Screen width in pixels for percentage calculation
            screen_height: Screen height in pixels for percentage calculation
        """
        if not ui_elements:
            return "No UI elements detected. Use visual estimation for coordinates."

        lines = [
            "UI Elements (USE THESE COORDINATES - they are more accurate than visual estimation):",
            ""
        ]

        for elem in ui_elements:
            bounds = elem["bounds"]
            center = elem["center"]

            # Calculate percentage coordinates
            x_percent = round(center["x"] / screen_width, 3)
            y_percent = round(center["y"] / screen_height, 3)

            # Build description
            parts = []
            if elem["text"]:
                parts.append(f'text="{elem["text"]}"')
            if elem["content_desc"]:
                parts.append(f'desc="{elem["content_desc"]}"')
            if elem["resource_id"]:
                # Simplify resource ID (remove package prefix)
                rid = elem["resource_id"].split("/")[-1]
                parts.append(f"id={rid}")

            # Element type
            class_name = elem["class"].split(".")[-1] if elem["class"] else "View"

            # Flags
            flags = []
            if elem["clickable"]:
                flags.append("clickable")
            if elem["focused"]:
                flags.append("focused")
            if not elem["enabled"]:
                flags.append("disabled")

            flags_str = f" [{', '.join(flags)}]" if flags else ""

            # Show percentage coordinates prominently for Claude to use directly
            line = (
                f"- {class_name}: {' '.join(parts)}"
                f" -> TAP at x={x_percent}, y={y_percent}"
                f"{flags_str}"
            )
            lines.append(line)

        return "\n".join(lines)
