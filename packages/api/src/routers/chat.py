"""Simple AI chat interface for device control."""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Annotated, AsyncGenerator, List
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog

from src.db import get_db
from src.models.profile import ProfileStatus
from src.models.chat import ChatSession, ChatMessage, ChatMessageRole
from src.services.profile_service import ProfileService
from src.services.docker_service import DockerService
from src.services.adb_service import ADBService
from src.services.fingerprint_service import get_fingerprint_service
from src.services.integration_service import IntegrationService, get_integration_service
from src.models.integration import IntegrationPurpose
from src.config import settings
from src.schemas.chat import (
    ChatSessionSchema,
    ChatSessionSummarySchema,
    ChatHistoryResponse,
    ChatMessageSchema,
)
from src.models.chat import ChatSession as ChatSessionModel, ChatMessage as ChatMessageModel, ChatMessageRole

# Import agent from the wrapper module
from src.agent_wrapper import MobileDroidAgent, AgentConfig

logger = structlog.get_logger()

router = APIRouter(prefix="/chat", tags=["chat"])

# Store active chat sessions for cancellation
active_sessions: dict[str, asyncio.Task] = {}


async def create_chat_session(
    db: AsyncSession,
    profile_id: str,
    initial_prompt: str,
) -> ChatSessionModel:
    """Create a new chat session in the database."""
    session = ChatSessionModel(
        id=str(uuid.uuid4()),
        profile_id=profile_id,
        initial_prompt=initial_prompt,
        status="active",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def save_chat_message(
    db: AsyncSession,
    session_id: str,
    role: ChatMessageRole,
    content: str,
    step_number: int | None = None,
    action_type: str | None = None,
    action_params: dict | None = None,
    action_reasoning: str | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cumulative_tokens: int = 0,
) -> ChatMessageModel:
    """Save a chat message to the database."""
    message = ChatMessageModel(
        session_id=session_id,
        role=role,
        content=content,
        step_number=step_number,
        action_type=action_type,
        action_params=action_params,
        action_reasoning=action_reasoning,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cumulative_tokens=cumulative_tokens,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def update_chat_session_totals(
    db: AsyncSession,
    session_id: str,
    total_tokens: int,
    total_input_tokens: int,
    total_output_tokens: int,
    total_steps: int,
    status: str = "completed",
) -> None:
    """Update chat session with final totals."""
    result = await db.execute(
        select(ChatSessionModel).where(ChatSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session:
        session.total_tokens = total_tokens
        session.total_input_tokens = total_input_tokens
        session.total_output_tokens = total_output_tokens
        session.total_steps = total_steps
        session.status = status
        session.completed_at = datetime.utcnow()
        await db.commit()


class ChatMessage(BaseModel):
    """Chat message request."""
    message: str
    max_steps: int = 50  # Increased from 20


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
    db: Annotated[AsyncSession, Depends(get_db)],
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

    # Get integration configuration for chat
    integration_service = IntegrationService(db)
    chat_config = await integration_service.get_chat_config()

    if not chat_config:
        raise HTTPException(
            status_code=500,
            detail="No chat integration configured. Please set up LLM provider configuration."
        )

    # Get ADB address
    adb_address = f"mobiledroid-{profile_id}:5555"

    # Create chat session in database for tracking
    chat_session = await create_chat_session(
        db=db,
        profile_id=profile_id,
        initial_prompt=chat_message.message,
    )

    # Save user message
    await save_chat_message(
        db=db,
        session_id=chat_session.id,
        role=ChatMessageRole.USER,
        content=chat_message.message,
    )

    try:
        # Connect to device
        host, port = adb_address.split(":")
        agent = await MobileDroidAgent.connect(
            host=host,
            port=int(port),
            anthropic_api_key=chat_config.api_key,
            config=AgentConfig(
                max_steps=chat_message.max_steps,
                llm_model=chat_config.model_name,
                temperature=chat_config.temperature,
            ),
        )

        # Execute the task with step tracking
        logger.info("Executing chat command", message=chat_message.message, session_id=chat_session.id)

        step_count = 0
        cumulative_tokens = 0

        async def on_step(step):
            nonlocal step_count, cumulative_tokens
            step_count += 1
            tokens_this_step = agent.total_tokens - cumulative_tokens
            cumulative_tokens = agent.total_tokens

            # Save step to database
            await save_chat_message(
                db=db,
                session_id=chat_session.id,
                role=ChatMessageRole.STEP,
                content=step.action.reasoning,
                step_number=step.step_number,
                action_type=step.action.type.value,
                action_params=step.action.params,
                action_reasoning=step.action.reasoning,
                input_tokens=tokens_this_step // 2,
                output_tokens=tokens_this_step // 2,
                cumulative_tokens=cumulative_tokens,
            )

        result = await agent.execute_task(
            task=chat_message.message,
            output_format=None,
            on_step=on_step,
        )

        if result.success:
            response_text = result.result or "Task completed successfully"
            if len(result.steps) > 1:
                response_text += f"\n\n(Completed in {len(result.steps)} steps)"
            final_status = "completed"
        else:
            response_text = f"Task failed: {result.error}"
            final_status = "error"

        # Save completion message
        await save_chat_message(
            db=db,
            session_id=chat_session.id,
            role=ChatMessageRole.ASSISTANT,
            content=response_text,
            cumulative_tokens=result.total_tokens,
        )

        # Update session totals
        await update_chat_session_totals(
            db=db,
            session_id=chat_session.id,
            total_tokens=result.total_tokens,
            total_input_tokens=result.total_tokens // 2,
            total_output_tokens=result.total_tokens // 2,
            total_steps=len(result.steps),
            status=final_status,
        )

        return ChatResponse(
            success=result.success,
            response=response_text,
            steps_taken=len(result.steps),
            error=result.error,
        )

    except Exception as e:
        logger.error("Chat execution error", error=str(e), session_id=chat_session.id)

        # Update session as error
        await update_chat_session_totals(
            db=db,
            session_id=chat_session.id,
            total_tokens=0,
            total_input_tokens=0,
            total_output_tokens=0,
            total_steps=0,
            status="error",
        )

        return ChatResponse(
            success=False,
            response="An error occurred while executing your command",
            error=str(e),
        )


class StreamingChatAgent:
    """Wrapper to enable real-time streaming of agent steps."""
    
    def __init__(self, agent: MobileDroidAgent):
        self.agent = agent
        self.event_queue = asyncio.Queue()
        
    async def execute_with_streaming(self, task: str, debug: bool = False):
        """Execute task and stream events in real-time."""
        
        def step_callback(step):
            # Create step message with reasoning
            step_msg = {
                'type': 'step',
                'number': len(self.agent.history) // 2 + 1,  # Estimate step number
                'action': step.action.type.value,
                'reasoning': step.action.reasoning,
                'tokens_so_far': self.agent.total_tokens,  # Cumulative tokens used
            }
            
            # Add action details if in debug mode
            if debug and step.action.params:
                if step.action.type.value == 'tap':
                    step_msg['details'] = f"Tapping at ({step.action.params.get('x')}, {step.action.params.get('y')})"
                elif step.action.type.value == 'double_tap':
                    delay = step.action.params.get('delay', 150)
                    step_msg['details'] = f"Double tapping at ({step.action.params.get('x')}, {step.action.params.get('y')}) with {delay}ms delay"
                elif step.action.type.value == 'swipe':
                    step_msg['details'] = f"Swiping from ({step.action.params.get('x1')}, {step.action.params.get('y1')}) to ({step.action.params.get('x2')}, {step.action.params.get('y2')})"
                elif step.action.type.value == 'type':
                    step_msg['details'] = f"Typing: {step.action.params.get('text', '')}"
            
            # Add screenshot if available and in debug mode
            if debug and hasattr(step, 'screenshot_b64') and step.screenshot_b64:
                step_msg['screenshot'] = step.screenshot_b64
            
            # Queue the step for streaming
            asyncio.create_task(self.event_queue.put(step_msg))
        
        # Start the task execution
        task_result = await self.agent.execute_task(
            task=task,
            output_format=None,
            on_step=step_callback
        )
        
        # Signal completion
        await self.event_queue.put({
            'type': 'complete',
            'success': task_result.success,
            'message': task_result.result or task_result.error or 'Task completed',
            'steps': len(task_result.steps),
            'total_tokens': task_result.total_tokens,
        })


async def _chat_event_generator(
    profile_id: str,
    message: str, 
    agent: MobileDroidAgent,
    debug: bool = False
) -> AsyncGenerator[str, None]:
    """Generate SSE events for chat streaming."""
    try:
        # Initial thinking message
        yield f"data: {json.dumps({'type': 'thinking', 'message': 'Analyzing the screen...'})}\n\n"
        
        # Create streaming wrapper
        streaming_agent = StreamingChatAgent(agent)
        
        # Start task execution in background
        task = asyncio.create_task(
            streaming_agent.execute_with_streaming(message, debug)
        )
        
        # Stream events as they arrive
        while True:
            try:
                # Wait for next event with short timeout
                event = await asyncio.wait_for(streaming_agent.event_queue.get(), timeout=1.0)
                
                # Yield the event
                yield f"data: {json.dumps(event)}\n\n"
                
                # Check if this is the completion event
                if event.get('type') == 'complete':
                    break
                    
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                
                # Check if task is done
                if task.done():
                    try:
                        await task  # This will raise any exception
                        # Task completed without sending completion event
                        yield f"data: {json.dumps({'type': 'complete', 'success': False, 'message': 'Task completed unexpectedly', 'steps': 0})}\n\n"
                    except Exception as e:
                        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                    break
                    
    except Exception as e:
        logger.error("Chat stream error", error=str(e))
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    finally:
        yield "data: [DONE]\n\n"


async def _chat_event_generator_with_cancellation(
    profile_id: str,
    message: str,
    agent: MobileDroidAgent,
    session_key: str,
    chat_session_id: str,
    debug: bool = False
) -> AsyncGenerator[str, None]:
    """Generate SSE events for chat streaming with cancellation support and persistence."""
    from src.db import AsyncSessionLocal

    step_count = 0
    total_tokens = 0
    final_status = "completed"

    try:
        # Initial thinking message
        yield f"data: {json.dumps({'type': 'thinking', 'message': 'Analyzing the screen...'})}\n\n"

        # Create streaming wrapper with cancellation support
        streaming_agent = StreamingChatAgent(agent)

        # Start task execution in background
        task = asyncio.create_task(
            streaming_agent.execute_with_streaming(message, debug)
        )

        # Register task for cancellation
        active_sessions[session_key] = task

        # Stream events as they arrive
        while True:
            try:
                # Wait for next event with short timeout
                event = await asyncio.wait_for(streaming_agent.event_queue.get(), timeout=1.0)

                # Persist step messages
                if event.get('type') == 'step':
                    step_count += 1
                    tokens_this_step = event.get('tokens_so_far', 0) - total_tokens
                    total_tokens = event.get('tokens_so_far', 0)

                    # Save step to database
                    try:
                        async with AsyncSessionLocal() as db:
                            await save_chat_message(
                                db=db,
                                session_id=chat_session_id,
                                role=ChatMessageRole.STEP,
                                content=event.get('reasoning', ''),
                                step_number=event.get('number'),
                                action_type=event.get('action'),
                                action_reasoning=event.get('reasoning'),
                                input_tokens=tokens_this_step // 2,
                                output_tokens=tokens_this_step // 2,
                                cumulative_tokens=total_tokens,
                            )
                    except Exception as e:
                        logger.error("Failed to save step message", error=str(e))

                # Yield the event
                yield f"data: {json.dumps(event)}\n\n"

                # Check if this is the completion event
                if event.get('type') == 'complete':
                    total_tokens = event.get('total_tokens', total_tokens)
                    # Save completion message
                    try:
                        async with AsyncSessionLocal() as db:
                            await save_chat_message(
                                db=db,
                                session_id=chat_session_id,
                                role=ChatMessageRole.ASSISTANT,
                                content=event.get('message', 'Task completed'),
                                cumulative_tokens=total_tokens,
                            )
                    except Exception as e:
                        logger.error("Failed to save completion message", error=str(e))
                    break

            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

                # Check if task was cancelled
                if task.cancelled():
                    final_status = "cancelled"
                    yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Chat session was stopped by user'})}\n\n"
                    break

                # Check if task is done
                if task.done():
                    try:
                        await task  # This will raise any exception
                        # Task completed without sending completion event
                        yield f"data: {json.dumps({'type': 'complete', 'success': False, 'message': 'Task completed unexpectedly', 'steps': 0})}\n\n"
                    except asyncio.CancelledError:
                        final_status = "cancelled"
                        yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Chat session was stopped by user'})}\n\n"
                    except Exception as e:
                        final_status = "error"
                        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                    break

    except asyncio.CancelledError:
        final_status = "cancelled"
        yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Chat session was stopped by user'})}\n\n"
    except Exception as e:
        final_status = "error"
        logger.error("Chat stream error", error=str(e))
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    finally:
        # Update session totals
        try:
            async with AsyncSessionLocal() as db:
                await update_chat_session_totals(
                    db=db,
                    session_id=chat_session_id,
                    total_tokens=total_tokens,
                    total_input_tokens=total_tokens // 2,
                    total_output_tokens=total_tokens // 2,
                    total_steps=step_count,
                    status=final_status,
                )
        except Exception as e:
            logger.error("Failed to update chat session totals", error=str(e))

        # Clean up session
        if session_key in active_sessions:
            del active_sessions[session_key]
        yield "data: [DONE]\n\n"


@router.post("/profiles/{profile_id}/stream")
async def chat_with_profile_stream(
    profile_id: str,
    chat_message: ChatMessage,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Chat with a profile using Server-Sent Events for real-time updates."""
    try:
        # Get profile service
        fingerprint_service = get_fingerprint_service()
        docker_service = DockerService(fingerprint_service)
        adb_service = ADBService()
        profile_service = ProfileService(db, docker_service, adb_service)
        
        # Get profile
        profile = await profile_service.get(profile_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
            
        if profile.status != ProfileStatus.RUNNING:
            raise HTTPException(status_code=400, detail="Profile must be running to chat")
        
        # Get ADB address - containers use internal Docker network
        # Container name follows pattern: mobiledroid-{profile_id}
        container_name = f"mobiledroid-{profile_id}"
        adb_address = f"{container_name}:5555"
        
        # Get LLM configuration
        integration_service = IntegrationService(db)
        chat_config = await integration_service.get_chat_config()
        if not chat_config:
            raise HTTPException(status_code=500, detail="Chat not configured. Please set up an LLM provider.")
        
        # Connect to device and create agent
        host, port = adb_address.split(":")
        agent = await MobileDroidAgent.connect(
            host=host,
            port=int(port),
            anthropic_api_key=chat_config.api_key,
            config=AgentConfig(
                max_steps=chat_message.max_steps,
                llm_model=chat_config.model_name,
                temperature=chat_config.temperature,
            ),
        )
        
        # Create session key and register task for cancellation
        session_key = f"chat_{profile_id}"

        # Clean up any existing session
        if session_key in active_sessions:
            old_task = active_sessions[session_key]
            if not old_task.done():
                old_task.cancel()
            del active_sessions[session_key]

        # Create chat session in database
        chat_session = await create_chat_session(
            db=db,
            profile_id=profile_id,
            initial_prompt=chat_message.message,
        )

        # Save user message
        await save_chat_message(
            db=db,
            session_id=chat_session.id,
            role=ChatMessageRole.USER,
            content=chat_message.message,
        )

        # Return streaming response with cancellation support
        return StreamingResponse(
            _chat_event_generator_with_cancellation(
                profile_id=profile_id,
                message=chat_message.message,
                agent=agent,
                session_key=session_key,
                chat_session_id=chat_session.id,
                debug=settings.debug,
            ),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error("Chat stream setup error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profiles/{profile_id}/stop")
async def stop_chat(profile_id: str):
    """Stop the active chat session for a profile."""
    session_key = f"chat_{profile_id}"
    
    if session_key in active_sessions:
        task = active_sessions[session_key]
        if not task.done():
            task.cancel()
            logger.info("Cancelled active chat session", profile_id=profile_id)
            try:
                await task
            except asyncio.CancelledError:
                pass
        del active_sessions[session_key]
        return {"success": True, "message": "Chat session stopped"}
    
    return {"success": False, "message": "No active chat session found"}


@router.get("/profiles/{profile_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    profile_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
    offset: int = 0,
):
    """Get chat history for a specific profile."""
    # Get total count
    count_result = await db.execute(
        select(func.count(ChatSessionModel.id)).where(
            ChatSessionModel.profile_id == profile_id
        )
    )
    total_sessions = count_result.scalar() or 0

    # Get sessions with message counts
    result = await db.execute(
        select(ChatSessionModel)
        .where(ChatSessionModel.profile_id == profile_id)
        .order_by(ChatSessionModel.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    sessions = result.scalars().all()

    # Calculate message counts and total tokens
    session_summaries = []
    total_tokens = 0

    for session in sessions:
        # Count messages for this session
        msg_count_result = await db.execute(
            select(func.count(ChatMessageModel.id)).where(
                ChatMessageModel.session_id == session.id
            )
        )
        message_count = msg_count_result.scalar() or 0

        session_summaries.append(
            ChatSessionSummarySchema(
                id=session.id,
                profile_id=session.profile_id,
                initial_prompt=session.initial_prompt,
                status=session.status,
                total_tokens=session.total_tokens,
                total_steps=session.total_steps,
                created_at=session.created_at,
                completed_at=session.completed_at,
                message_count=message_count,
            )
        )
        total_tokens += session.total_tokens

    return ChatHistoryResponse(
        sessions=session_summaries,
        total_tokens=total_tokens,
        total_sessions=total_sessions,
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionSchema)
async def get_chat_session(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific chat session with all its messages."""
    result = await db.execute(
        select(ChatSessionModel).where(ChatSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Get messages
    msg_result = await db.execute(
        select(ChatMessageModel)
        .where(ChatMessageModel.session_id == session_id)
        .order_by(ChatMessageModel.created_at)
    )
    messages = msg_result.scalars().all()

    return ChatSessionSchema(
        id=session.id,
        profile_id=session.profile_id,
        initial_prompt=session.initial_prompt,
        status=session.status,
        total_tokens=session.total_tokens,
        total_input_tokens=session.total_input_tokens,
        total_output_tokens=session.total_output_tokens,
        total_steps=session.total_steps,
        created_at=session.created_at,
        completed_at=session.completed_at,
        messages=[
            ChatMessageSchema(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                step_number=msg.step_number,
                action_type=msg.action_type,
                action_reasoning=msg.action_reasoning,
                input_tokens=msg.input_tokens,
                output_tokens=msg.output_tokens,
                cumulative_tokens=msg.cumulative_tokens,
                created_at=msg.created_at,
            )
            for msg in messages
        ],
    )


@router.get("/history", response_model=ChatHistoryResponse)
async def get_all_chat_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 100,
    offset: int = 0,
):
    """Get chat history across all profiles (for cost tracking)."""
    # Get total count
    count_result = await db.execute(select(func.count(ChatSessionModel.id)))
    total_sessions = count_result.scalar() or 0

    # Get total tokens
    tokens_result = await db.execute(
        select(func.sum(ChatSessionModel.total_tokens))
    )
    total_tokens = tokens_result.scalar() or 0

    # Get sessions
    result = await db.execute(
        select(ChatSessionModel)
        .order_by(ChatSessionModel.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    sessions = result.scalars().all()

    session_summaries = []
    for session in sessions:
        # Count messages for this session
        msg_count_result = await db.execute(
            select(func.count(ChatMessageModel.id)).where(
                ChatMessageModel.session_id == session.id
            )
        )
        message_count = msg_count_result.scalar() or 0

        session_summaries.append(
            ChatSessionSummarySchema(
                id=session.id,
                profile_id=session.profile_id,
                initial_prompt=session.initial_prompt,
                status=session.status,
                total_tokens=session.total_tokens,
                total_steps=session.total_steps,
                created_at=session.created_at,
                completed_at=session.completed_at,
                message_count=message_count,
            )
        )

    return ChatHistoryResponse(
        sessions=session_summaries,
        total_tokens=total_tokens,
        total_sessions=total_sessions,
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