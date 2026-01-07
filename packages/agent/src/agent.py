"""Main AI agent for Android automation."""

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Callable

from adbutils import adb, AdbDevice
from anthropic import Anthropic
import structlog

from src.actions import Action, ActionExecutor, ActionType
from src.prompts import AGENT_SYSTEM_PROMPT, get_task_prompt
from src.vision import VisionService

logger = structlog.get_logger()


@dataclass
class AgentConfig:
    """Configuration for the AI agent."""

    max_steps: int = 50
    step_delay: float = 1.0  # Seconds to wait between steps
    llm_model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.0


@dataclass
class AgentStep:
    """Represents a single step in task execution."""

    step_number: int
    action: Action
    result: dict[str, Any]
    screenshot_b64: str | None = None


@dataclass
class AgentResult:
    """Result of task execution."""

    success: bool
    result: str | None
    error: str | None
    steps: list[AgentStep] = field(default_factory=list)
    total_tokens: int = 0


class MobileDroidAgent:
    """AI agent for controlling Android devices via natural language."""

    def __init__(
        self,
        device: AdbDevice,
        anthropic_api_key: str,
        config: AgentConfig | None = None,
    ):
        self.device = device
        self.llm = Anthropic(api_key=anthropic_api_key)
        self.config = config or AgentConfig()

        self.vision = VisionService(device)
        self.executor = ActionExecutor(device)

        self.history: list[dict[str, Any]] = []
        self.total_tokens = 0

    @classmethod
    async def connect(
        cls,
        host: str,
        port: int,
        anthropic_api_key: str,
        config: AgentConfig | None = None,
    ) -> "MobileDroidAgent":
        """Connect to a device and create an agent."""
        address = f"{host}:{port}"

        # Connect to device
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: adb.connect(address, timeout=10))

        device = adb.device(serial=address)
        logger.info("Connected to device", address=address)

        return cls(device, anthropic_api_key, config)

    async def execute_task(
        self,
        task: str,
        output_format: str | None = None,
        on_step: Callable[[AgentStep], None] | None = None,
    ) -> AgentResult:
        """Execute a natural language task on the device.

        Args:
            task: Natural language description of the task
            output_format: Optional expected output format
            on_step: Optional callback for each step

        Returns:
            AgentResult with success status and result
        """
        logger.info("Starting task execution", task=task)

        self.history = []
        self.total_tokens = 0
        steps: list[AgentStep] = []

        task_prompt = get_task_prompt(task, output_format)

        for step_number in range(1, self.config.max_steps + 1):
            logger.info("Executing step", step=step_number)

            try:
                # Capture current state
                state = await self.vision.get_state()

                # Format UI hierarchy for the prompt
                ui_description = self.vision.format_ui_for_prompt(state["ui_elements"])

                # Build the message for this step
                user_content = self._build_step_message(
                    task_prompt=task_prompt,
                    step_number=step_number,
                    screenshot_b64=state["screenshot"],
                    ui_description=ui_description,
                    screen_size=(state["screen_width"], state["screen_height"]),
                )

                # Get action from LLM
                action = await self._get_action(user_content)

                # Execute the action
                result = await self.executor.execute(action)

                # Create step record
                step = AgentStep(
                    step_number=step_number,
                    action=action,
                    result=result,
                    screenshot_b64=state["screenshot"],
                )
                steps.append(step)

                # Callback
                if on_step:
                    on_step(step)

                # Check if task is complete
                if action.type == ActionType.DONE:
                    logger.info("Task completed", result=action.params.get("result"))
                    return AgentResult(
                        success=True,
                        result=action.params.get("result"),
                        error=None,
                        steps=steps,
                        total_tokens=self.total_tokens,
                    )

                if action.type == ActionType.FAIL:
                    logger.warning("Task failed", reason=action.params.get("reason"))
                    return AgentResult(
                        success=False,
                        result=None,
                        error=action.params.get("reason"),
                        steps=steps,
                        total_tokens=self.total_tokens,
                    )

                # Wait for UI to settle
                await asyncio.sleep(self.config.step_delay)

            except Exception as e:
                logger.error("Step execution error", step=step_number, error=str(e))
                return AgentResult(
                    success=False,
                    result=None,
                    error=f"Step {step_number} failed: {str(e)}",
                    steps=steps,
                    total_tokens=self.total_tokens,
                )

        # Max steps reached
        logger.warning("Max steps reached", max_steps=self.config.max_steps)
        return AgentResult(
            success=False,
            result=None,
            error=f"Task did not complete within {self.config.max_steps} steps",
            steps=steps,
            total_tokens=self.total_tokens,
        )

    async def execute_task_stream(
        self,
        task: str,
        output_format: str | None = None,
    ) -> AsyncGenerator[AgentStep, None]:
        """Execute a task and yield steps as they complete."""
        steps: list[AgentStep] = []

        async def collect_step(step: AgentStep):
            steps.append(step)

        # Run execution with callback
        result = await self.execute_task(
            task=task,
            output_format=output_format,
            on_step=lambda s: collect_step(s),
        )

        # Yield all steps
        for step in steps:
            yield step

    def _build_step_message(
        self,
        task_prompt: str,
        step_number: int,
        screenshot_b64: str,
        ui_description: str,
        screen_size: tuple[int, int],
    ) -> list[dict[str, Any]]:
        """Build the message content for a step."""
        content = [
            {
                "type": "text",
                "text": f"""Step {step_number}

{task_prompt}

Screen size: {screen_size[0]}x{screen_size[1]}

{ui_description}

Current screen:""",
            },
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": screenshot_b64,
                },
            },
            {
                "type": "text",
                "text": "\nWhat action should I take next? Respond with a JSON object.",
            },
        ]

        return content

    async def _get_action(self, user_content: list[dict[str, Any]]) -> Action:
        """Get the next action from the LLM."""
        # Build messages
        messages = [
            *self.history,
            {"role": "user", "content": user_content},
        ]

        # Call LLM
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.llm.messages.create(
                model=self.config.llm_model,
                max_tokens=1024,
                temperature=self.config.temperature,
                system=AGENT_SYSTEM_PROMPT,
                messages=messages,
            ),
        )

        # Track token usage
        self.total_tokens += response.usage.input_tokens + response.usage.output_tokens

        # Extract response text
        response_text = response.content[0].text

        # Parse the JSON action
        action_data = self._parse_action_json(response_text)
        action = Action.from_dict(action_data)

        # Update history
        self.history.append({"role": "user", "content": user_content})
        self.history.append({"role": "assistant", "content": response_text})

        return action

    def _parse_action_json(self, text: str) -> dict[str, Any]:
        """Parse JSON action from LLM response."""
        # Try to find JSON in the response
        text = text.strip()

        # Handle markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                text = text[start:end].strip()

        # Try to find a JSON object
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            text = text[json_start:json_end]

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse action JSON", error=str(e), text=text)
            # Return a fail action
            return {
                "action": "fail",
                "reason": f"Failed to parse LLM response: {str(e)}",
            }
