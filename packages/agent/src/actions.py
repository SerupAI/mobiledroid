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
    SWIPE = "swipe"
    TYPE = "type"
    BACK = "back"
    HOME = "home"
    ENTER = "enter"
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
            params = {"x": data.get("x", 0), "y": data.get("y", 0)}
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
        elif action_type == ActionType.DONE:
            params = {"result": data.get("result", "")}
        elif action_type == ActionType.FAIL:
            params = {"reason": data.get("reason", "")}

        return cls(type=action_type, params=params, reasoning=reasoning)


class ActionExecutor:
    """Executes actions on an Android device."""

    def __init__(self, device: AdbDevice):
        self.device = device

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
        """Execute a tap action."""
        x = int(params["x"])
        y = int(params["y"])

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self.device.click(x, y))

        return {"success": True, "x": x, "y": y}

    async def _swipe(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a swipe action."""
        x1 = int(params["x1"])
        y1 = int(params["y1"])
        x2 = int(params["x2"])
        y2 = int(params["y2"])
        duration = float(params.get("duration", 300)) / 1000  # Convert to seconds

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
