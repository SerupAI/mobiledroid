"""Simple AI chat interface for device control."""

import asyncio
from typing import Annotated
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.db import get_db
from src.models.profile import ProfileStatus
from src.services.profile_service import ProfileService
from src.services.docker_service import DockerService
from src.services.adb_service import ADBService
from src.services.fingerprint_service import get_fingerprint_service
from src.config import settings

# Import agent from the agent package
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../agent"))
from src.agent import MobileDroidAgent, AgentConfig

logger = structlog.get_logger()

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    """Chat message request."""
    message: str
    max_steps: int = 20


class ChatResponse(BaseModel):
    """Chat response."""
    success: bool
    response: str
    steps_taken: int = 0
    error: str | None = None


async def get_profile_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProfileService:
    """Get profile service dependency."""
    fingerprint_service = get_fingerprint_service()
    docker_service = DockerService(fingerprint_service)
    adb_service = ADBService()
    return ProfileService(db, docker_service, adb_service)


@router.post("/profiles/{profile_id}", response_model=ChatResponse)
async def chat_with_device(
    profile_id: str,
    chat_message: ChatMessage,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ChatResponse:
    """Send a natural language command to control the device.
    
    Examples:
    - "Open the settings app"
    - "Take a screenshot"
    - "What's on the screen?"
    - "Click on the Search button"
    - "Type 'hello world' in the text field"
    """
    # Verify profile exists and is running
    profile = await service.get(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    if profile.status != ProfileStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Profile not running")
    
    # Check API key
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=500,
            detail="Anthropic API key not configured. Please set ANTHROPIC_API_KEY environment variable."
        )
    
    # Get ADB address
    adb_address = f"mobiledroid-{profile_id}:5555"
    
    try:
        # Connect to device
        host, port = adb_address.split(":")
        agent = await MobileDroidAgent.connect(
            host=host,
            port=int(port),
            anthropic_api_key=settings.anthropic_api_key,
            config=AgentConfig(
                max_steps=chat_message.max_steps,
                llm_model="claude-3-5-sonnet-20241022",  # Use cheaper, faster model
                temperature=0.0,
            ),
        )
        
        # Execute the task
        logger.info("Executing chat command", message=chat_message.message)
        result = await agent.execute_task(
            task=chat_message.message,
            output_format=None,
        )
        
        if result.success:
            response_text = result.result or "Task completed successfully"
            # Add step summary if multiple steps
            if len(result.steps) > 1:
                response_text += f"\n\n(Completed in {len(result.steps)} steps)"
        else:
            response_text = f"Task failed: {result.error}"
        
        return ChatResponse(
            success=result.success,
            response=response_text,
            steps_taken=len(result.steps),
            error=result.error,
        )
        
    except Exception as e:
        logger.error("Chat execution error", error=str(e))
        return ChatResponse(
            success=False,
            response="An error occurred while executing your command",
            error=str(e),
        )


@router.get("/examples")
async def get_chat_examples():
    """Get example chat commands."""
    return {
        "examples": [
            {
                "category": "Navigation",
                "commands": [
                    "Open the settings app",
                    "Go to the home screen",
                    "Open the app drawer",
                    "Go back to the previous screen",
                ]
            },
            {
                "category": "Interaction",
                "commands": [
                    "Click on the Search button",
                    "Tap the menu icon",
                    "Swipe up on the screen",
                    "Long press on the app icon",
                ]
            },
            {
                "category": "Text Input",
                "commands": [
                    "Type 'hello world' in the text field",
                    "Clear the text field",
                    "Enter your email address",
                    "Search for 'weather'",
                ]
            },
            {
                "category": "Information",
                "commands": [
                    "What's on the screen?",
                    "What apps are visible?",
                    "Read the notification",
                    "What's the current time shown?",
                ]
            },
            {
                "category": "Complex Tasks",
                "commands": [
                    "Turn on airplane mode",
                    "Set an alarm for 7 AM",
                    "Take a screenshot and tell me what you see",
                    "Install the app from Play Store",
                ]
            }
        ]
    }