"""Main AI agent for Android automation."""

import asyncio
import json
import hashlib
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Callable

from adbutils import adb, AdbDevice
from anthropic import Anthropic
import structlog

from actions import Action, ActionExecutor, ActionType
from prompts import AGENT_SYSTEM_PROMPT, get_task_prompt
from vision import VisionService

logger = structlog.get_logger()


@dataclass
class AgentConfig:
    """Configuration for the AI agent."""

    max_steps: int = 50
    step_delay: float = 1.0  # Seconds to wait between steps
    llm_model: str = "claude-sonnet-4-5-20250929"
    temperature: float = 0.0
    stuck_detection_threshold: int = 3  # Max identical screenshots before stuck
    max_recovery_attempts: int = 2  # Max recovery attempts per stuck state


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
        
        # Stuck detection state
        self.screenshot_history: list[str] = []  # Store screenshot hashes
        self.recovery_attempts = 0

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
        self.screenshot_history = []
        self.recovery_attempts = 0
        steps: list[AgentStep] = []

        task_prompt = get_task_prompt(task, output_format)

        for step_number in range(1, self.config.max_steps + 1):
            logger.info("Executing step", step=step_number)

            try:
                # Capture current state
                state = await self.vision.get_state()
                screenshot_hash = hashlib.md5(state["screenshot"].encode()).hexdigest()

                # Check for stuck state (identical screenshots)
                is_stuck = await self._check_stuck_state(screenshot_hash, step_number)
                
                if is_stuck:
                    # Try recovery action
                    recovery_action = await self._get_recovery_action(state, steps)
                    if recovery_action:
                        logger.info("Executing recovery action", action=recovery_action.type)
                        result = await self.executor.execute(recovery_action)
                        
                        # Create recovery step
                        step = AgentStep(
                            step_number=step_number,
                            action=recovery_action,
                            result=result,
                            screenshot_b64=state["screenshot"],
                        )
                        steps.append(step)
                        
                        if on_step:
                            on_step(step)
                            
                        # Wait and continue
                        await asyncio.sleep(self.config.step_delay)
                        continue
                    else:
                        # No recovery possible, fail the task
                        return AgentResult(
                            success=False,
                            result=None,
                            error=f"Task stuck after {step_number} steps. No recovery strategy available.",
                            steps=steps,
                            total_tokens=self.total_tokens,
                        )

                # Format UI hierarchy for the prompt
                ui_description = self.vision.format_ui_for_prompt(state["ui_elements"])

                # Build the message for this step
                user_content = self._build_step_message(
                    task_prompt=task_prompt,
                    step_number=step_number,
                    screenshot_b64=state["screenshot"],
                    ui_description=ui_description,
                    screen_size=(state["screen_width"], state["screen_height"]),
                    is_recovery=(self.recovery_attempts > 0),
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

    async def _check_stuck_state(self, screenshot_hash: str, step_number: int) -> bool:
        """Check if the agent is stuck based on identical screenshots."""
        self.screenshot_history.append(screenshot_hash)
        
        # Keep only recent screenshots for comparison
        if len(self.screenshot_history) > self.config.stuck_detection_threshold:
            self.screenshot_history = self.screenshot_history[-self.config.stuck_detection_threshold:]
        
        # Check if we have enough screenshots to detect stuck state
        if len(self.screenshot_history) < self.config.stuck_detection_threshold:
            return False
        
        # Check if all recent screenshots are identical
        if len(set(self.screenshot_history)) == 1:
            if self.recovery_attempts < self.config.max_recovery_attempts:
                logger.warning("Stuck state detected", 
                              step=step_number, 
                              recovery_attempts=self.recovery_attempts,
                              threshold=self.config.stuck_detection_threshold)
                return True
            else:
                logger.error("Max recovery attempts reached", 
                           recovery_attempts=self.recovery_attempts)
                return False
        
        # Reset recovery attempts if screen changed
        if len(set(self.screenshot_history)) > 1:
            self.recovery_attempts = 0
        
        return False

    async def _get_recovery_action(self, state: dict[str, Any], steps: list[AgentStep]) -> Action | None:
        """Generate a recovery action when stuck state is detected."""
        self.recovery_attempts += 1
        
        # Analyze recent actions to determine recovery strategy
        recent_actions = [step.action for step in steps[-3:] if steps]
        
        # Recovery strategies based on recent actions
        if recent_actions:
            last_action = recent_actions[-1]
            
            # If stuck tapping, try different recovery strategies
            if last_action.type == ActionType.TAP:
                if self.recovery_attempts == 1:
                    # Try long press on the same coordinates
                    return Action(
                        type=ActionType.TAP,
                        params={**last_action.params, "duration": 1000},
                        reasoning="Recovery: Long press instead of tap"
                    )
                elif self.recovery_attempts == 2:
                    # Try going back and then forward
                    return Action(
                        type=ActionType.BACK,
                        params={},
                        reasoning="Recovery: Go back to reset state"
                    )
            
            # If stuck swiping, try tap or back
            elif last_action.type == ActionType.SWIPE:
                return Action(
                    type=ActionType.BACK,
                    params={},
                    reasoning="Recovery: Go back after stuck swipe"
                )
        
        # Default recovery actions
        if self.recovery_attempts == 1:
            # Try going back
            return Action(
                type=ActionType.BACK,
                params={},
                reasoning="Recovery: Navigate back to unstick"
            )
        elif self.recovery_attempts == 2:
            # Try going to home screen
            return Action(
                type=ActionType.HOME,
                params={},
                reasoning="Recovery: Go to home screen to reset"
            )
        
        # No recovery strategy available
        return None

    def _build_step_message(
        self,
        task_prompt: str,
        step_number: int,
        screenshot_b64: str,
        ui_description: str,
        screen_size: tuple[int, int],
        is_recovery: bool = False,
    ) -> list[dict[str, Any]]:
        """Build the message content for a step."""
        recovery_note = ""
        if is_recovery:
            recovery_note = f"\n\nIMPORTANT: This is a recovery attempt #{self.recovery_attempts}. Previous attempts may have failed. Consider alternative approaches or different coordinates."
        
        content = [
            {
                "type": "text",
                "text": f"""Step {step_number}

{task_prompt}

Screen size: {screen_size[0]}x{screen_size[1]}

{ui_description}{recovery_note}

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

        # Call LLM with debug logging
        loop = asyncio.get_event_loop()
        try:
            logger.debug("Calling Anthropic API", model=self.config.llm_model, api_key_length=len(self.llm.api_key))
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
            logger.debug("Anthropic API call successful")
        except Exception as e:
            logger.error("Anthropic API call failed", error=str(e), error_type=type(e).__name__)
            # Log more details about the error
            if hasattr(e, 'response'):
                logger.error("API response details", response=str(e.response))
            if hasattr(e, 'body'):
                logger.error("API body details", body=str(e.body))
            raise

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
