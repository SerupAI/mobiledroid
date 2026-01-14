"""Action execution for the AI agent."""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any

from adbutils import AdbDevice
import structlog

logger = structlog.get_logger()


class ActionType(str, Enum):
    """Available action types."""

    TAP = "tap"
    DOUBLE_TAP = "double_tap"
    SWIPE = "swipe"
    TYPE = "type"
    BACK = "back"
    HOME = "home"
    ENTER = "enter"
    WAIT = "wait"
    DONE = "done"
    FAIL = "fail"


@dataclass
class Action:
    """Represents an action to execute."""

    type: ActionType
    params: dict[str, Any]
    reasoning: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Action":
        """Create an Action from a dictionary."""
        action_type = ActionType(data.get("action", "").lower())
        reasoning = data.get("reasoning", "")

        params = {}
        if action_type == ActionType.TAP:
            params = {
                "x": data.get("x", 0), 
                "y": data.get("y", 0),
                "duration": data.get("duration", None),  # Support long press
                "post_delay": data.get("post_delay", 300)  # Wait after tap for response
            }
        elif action_type == ActionType.DOUBLE_TAP:
            params = {
                "x": data.get("x", 0),
                "y": data.get("y", 0),
                "delay": data.get("delay", 300),  # Delay between taps in ms (increased from 150)
                "post_delay": data.get("post_delay", 800)  # Wait after double tap for response
            }
        elif action_type == ActionType.SWIPE:
            params = {
                "x1": data.get("x1", 0),
                "y1": data.get("y1", 0),
                "x2": data.get("x2", 0),
                "y2": data.get("y2", 0),
                "duration": data.get("duration", 300),
            }
        elif action_type == ActionType.TYPE:
            params = {"text": data.get("text", "")}
        elif action_type == ActionType.WAIT:
            params = {"duration": data.get("duration", 1000)}  # Default 1 second
        elif action_type == ActionType.DONE:
            params = {"result": data.get("result", "")}
        elif action_type == ActionType.FAIL:
            params = {"reason": data.get("reason", "")}

        return cls(type=action_type, params=params, reasoning=reasoning)


class ActionExecutor:
    """Executes actions on an Android device."""

    def __init__(self, device: AdbDevice):
        self.device = device
        self.screen_width: int = 1080  # Default, will be updated
        self.screen_height: int = 2400  # Default, will be updated

    def set_screen_size(self, width: int, height: int) -> None:
        """Set the screen dimensions for coordinate conversion."""
        self.screen_width = width
        self.screen_height = height

    def _to_pixels(self, x_percent: float, y_percent: float) -> tuple[int, int]:
        """Convert percentage coordinates (0.0-1.0) to pixel coordinates.

        Clamps values to valid range to prevent out-of-bounds taps.
        """
        # Warn if out of range before clamping
        if x_percent > 1.0 or y_percent > 1.0 or x_percent < 0.0 or y_percent < 0.0:
            logger.warning("Coordinates out of range, clamping to valid range",
                          x_percent=x_percent, y_percent=y_percent)

        # Clamp to valid range (0.0-1.0)
        x_clamped = max(0.0, min(1.0, x_percent))
        y_clamped = max(0.0, min(1.0, y_percent))

        x = int(x_clamped * self.screen_width)
        y = int(y_clamped * self.screen_height)
        return x, y

    async def execute(self, action: Action) -> dict[str, Any]:
        """Execute an action and return the result."""
        logger.info(
            "Executing action",
            action_type=action.type.value,
            params=action.params,
            reasoning=action.reasoning,
        )

        try:
            match action.type:
                case ActionType.TAP:
                    return await self._tap(action.params)
                case ActionType.DOUBLE_TAP:
                    return await self._double_tap(action.params)
                case ActionType.SWIPE:
                    return await self._swipe(action.params)
                case ActionType.TYPE:
                    return await self._type(action.params)
                case ActionType.BACK:
                    return await self._back()
                case ActionType.HOME:
                    return await self._home()
                case ActionType.ENTER:
                    return await self._enter()
                case ActionType.WAIT:
                    return await self._wait(action.params)
                case ActionType.DONE:
                    return {"completed": True, "result": action.params.get("result")}
                case ActionType.FAIL:
                    return {"completed": True, "failed": True, "reason": action.params.get("reason")}
                case _:
                    return {"error": f"Unknown action type: {action.type}"}

        except Exception as e:
            logger.error("Action execution failed", error=str(e))
            return {"error": str(e)}

    async def _tap(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a tap action (supports long press with duration)."""
        # Convert percentage coordinates (0.0-1.0) to pixel coordinates
        x_percent = float(params["x"])
        y_percent = float(params["y"])
        x, y = self._to_pixels(x_percent, y_percent)

        duration = params.get("duration")  # Duration in milliseconds
        post_delay = params.get("post_delay", 300)  # Wait after tap for response

        logger.debug("Executing tap action",
                    x_percent=x_percent, y_percent=y_percent,
                    x_pixels=x, y_pixels=y,
                    screen=f"{self.screen_width}x{self.screen_height}",
                    duration=duration, post_delay=post_delay)
        
        loop = asyncio.get_event_loop()
        
        if duration and duration > 500:  # Long press if duration > 500ms
            # Use shell input for long press
            cmd = f"input touchscreen swipe {x} {y} {x} {y} {int(duration)}"
            logger.debug("Executing long press via shell", command=cmd)
            await loop.run_in_executor(
                None, 
                lambda: self.device.shell(cmd)
            )
            result_type = "long_press"
        else:
            # Regular tap - use shell command for consistency
            cmd = f"input tap {x} {y}"
            logger.debug("Executing tap via shell", command=cmd)
            await loop.run_in_executor(None, lambda: self.device.shell(cmd))
            result_type = "tap"
        
        # Wait for UI response after tap
        if post_delay > 0:
            logger.debug(f"Waiting {post_delay}ms for UI response after {result_type}")
            await asyncio.sleep(post_delay / 1000.0)
        
        return {"success": True, "x": x, "y": y, "x_percent": x_percent, "y_percent": y_percent, "type": result_type, "duration": duration, "post_delay": post_delay}

    async def _double_tap(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a double tap action."""
        # Convert percentage coordinates (0.0-1.0) to pixel coordinates
        x_percent = float(params["x"])
        y_percent = float(params["y"])
        x, y = self._to_pixels(x_percent, y_percent)

        delay = params.get("delay", 300)  # Delay between taps in milliseconds (increased from 150)
        post_delay = params.get("post_delay", 800)  # Wait after double tap for app response

        logger.debug("Executing double tap action",
                    x_percent=x_percent, y_percent=y_percent,
                    x_pixels=x, y_pixels=y,
                    screen=f"{self.screen_width}x{self.screen_height}",
                    delay=delay, post_delay=post_delay)
        
        loop = asyncio.get_event_loop()
        
        # First tap
        cmd1 = f"input tap {x} {y}"
        logger.debug("Executing first tap via shell", command=cmd1)
        await loop.run_in_executor(None, lambda: self.device.shell(cmd1))
        
        # Wait between taps
        await asyncio.sleep(delay / 1000.0)  # Convert ms to seconds
        
        # Second tap
        cmd2 = f"input tap {x} {y}"
        logger.debug("Executing second tap via shell", command=cmd2)
        await loop.run_in_executor(None, lambda: self.device.shell(cmd2))
        
        # Wait for app response (especially important for app launches)
        if post_delay > 0:
            logger.debug(f"Waiting {post_delay}ms for app response after double tap")
            await asyncio.sleep(post_delay / 1000.0)
        
        return {"success": True, "x": x, "y": y, "x_percent": x_percent, "y_percent": y_percent, "type": "double_tap", "delay": delay, "post_delay": post_delay}

    async def _swipe(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a swipe action."""
        # Convert percentage coordinates (0.0-1.0) to pixel coordinates
        x1_percent = float(params["x1"])
        y1_percent = float(params["y1"])
        x2_percent = float(params["x2"])
        y2_percent = float(params["y2"])

        x1, y1 = self._to_pixels(x1_percent, y1_percent)
        x2, y2 = self._to_pixels(x2_percent, y2_percent)

        duration = float(params.get("duration", 300)) / 1000  # Convert to seconds

        logger.debug("Executing swipe action",
                    start_percent=f"({x1_percent}, {y1_percent})",
                    end_percent=f"({x2_percent}, {y2_percent})",
                    start_pixels=f"({x1}, {y1})",
                    end_pixels=f"({x2}, {y2})",
                    screen=f"{self.screen_width}x{self.screen_height}")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: self.device.swipe(x1, y1, x2, y2, duration)
        )

        return {"success": True, "x1": x1, "y1": y1, "x2": x2, "y2": y2}

    async def _type(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a text input action."""
        text = params["text"]

        # Escape special characters for shell
        escaped = text.replace("'", "'\\''")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: self.device.shell(f"input text '{escaped}'")
        )

        return {"success": True, "text": text}

    async def _back(self) -> dict[str, Any]:
        """Press the back button."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: self.device.shell("input keyevent KEYCODE_BACK")
        )
        return {"success": True}

    async def _home(self) -> dict[str, Any]:
        """Press the home button."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: self.device.shell("input keyevent KEYCODE_HOME")
        )
        return {"success": True}

    async def _enter(self) -> dict[str, Any]:
        """Press the enter key."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: self.device.shell("input keyevent KEYCODE_ENTER")
        )
        return {"success": True}

    async def _wait(self, params: dict[str, Any]) -> dict[str, Any]:
        """Wait for a specified duration (for loading states, animations, etc.)."""
        duration_ms = params.get("duration", 1000)
        duration_s = duration_ms / 1000.0

        logger.debug(f"Waiting {duration_ms}ms for UI to settle")
        await asyncio.sleep(duration_s)

        return {"success": True, "duration": duration_ms}
