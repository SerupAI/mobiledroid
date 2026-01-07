"""WebSocket streaming endpoints for real-time device screen."""

import asyncio
import base64
from typing import Annotated

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.db import get_db
from src.models.profile import ProfileStatus
from src.services.profile_service import ProfileService
from src.services.docker_service import DockerService
from src.services.adb_service import ADBService
from src.services.fingerprint_service import get_fingerprint_service

logger = structlog.get_logger()

router = APIRouter(prefix="/ws", tags=["websocket"])


async def get_profile_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProfileService:
    """Get profile service dependency."""
    fingerprint_service = get_fingerprint_service()
    docker_service = DockerService(fingerprint_service)
    adb_service = ADBService()
    return ProfileService(db, docker_service, adb_service)


@router.websocket("/profiles/{profile_id}/stream")
async def stream_device_screen(
    websocket: WebSocket,
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Stream device screen via WebSocket with bidirectional command support."""
    await websocket.accept()
    
    # Get profile service
    fingerprint_service = get_fingerprint_service()
    docker_service = DockerService(fingerprint_service)
    adb_service = ADBService()
    profile_service = ProfileService(db, docker_service, adb_service)
    
    # Create tasks for concurrent handling
    send_task = None
    receive_task = None
    
    try:
        # Verify profile exists and is running
        profile = await profile_service.get(profile_id)
        if not profile:
            await websocket.send_json({"error": "Profile not found"})
            await websocket.close()
            return
            
        if profile.status != ProfileStatus.RUNNING:
            await websocket.send_json({"error": "Profile not running"})
            await websocket.close()
            return
        
        # Get ADB address
        adb_address = f"mobiledroid-{profile_id}:5555"
        
        logger.info("WebSocket stream started", profile_id=profile_id)
        
        # Create send and receive tasks for concurrent operation
        async def send_frames():
            """Send screenshot frames to client."""
            frame_interval = 0.033  # ~30 fps for better responsiveness
            error_count = 0
            max_errors = 5
            
            while True:
                try:
                    # Take screenshot
                    screenshot = await adb_service.screenshot(adb_address)
                    
                    if screenshot:
                        # Send as base64 to avoid binary WebSocket complexity
                        base64_data = base64.b64encode(screenshot).decode('utf-8')
                        await websocket.send_json({
                            "type": "frame",
                            "data": base64_data,
                            "timestamp": asyncio.get_event_loop().time()
                        })
                        error_count = 0
                    else:
                        error_count += 1
                        if error_count > max_errors:
                            await websocket.send_json({"error": "Screenshot failed"})
                            break
                    
                    # Wait for next frame
                    await asyncio.sleep(frame_interval)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("Send frame error", error=str(e))
                    error_count += 1
                    if error_count > max_errors:
                        break
                    await asyncio.sleep(frame_interval)
        
        async def receive_commands():
            """Receive and process commands from client."""
            while True:
                try:
                    data = await websocket.receive_json()
                    command = data.get("command")
                    
                    if command == "tap":
                        x = data.get("x")
                        y = data.get("y")
                        if x is not None and y is not None:
                            success = await adb_service.tap(adb_address, x, y)
                            await websocket.send_json({
                                "type": "command_result",
                                "command": "tap",
                                "success": success
                            })
                    
                    elif command == "swipe":
                        x1, y1 = data.get("x1"), data.get("y1")
                        x2, y2 = data.get("x2"), data.get("y2")
                        duration = data.get("duration", 300)
                        if all(v is not None for v in [x1, y1, x2, y2]):
                            success = await adb_service.swipe(adb_address, x1, y1, x2, y2, duration)
                            await websocket.send_json({
                                "type": "command_result",
                                "command": "swipe",
                                "success": success
                            })
                    
                    elif command == "key":
                        keycode = data.get("keycode")
                        if keycode:
                            success = await adb_service.press_key(adb_address, keycode)
                            await websocket.send_json({
                                "type": "command_result",
                                "command": "key",
                                "success": success
                            })
                    
                    elif command == "text":
                        text = data.get("text")
                        if text:
                            success = await adb_service.input_text(adb_address, text)
                            await websocket.send_json({
                                "type": "command_result",
                                "command": "text",
                                "success": success
                            })
                            
                except asyncio.CancelledError:
                    break
                except WebSocketDisconnect:
                    logger.info("WebSocket disconnected during receive")
                    break
                except Exception as e:
                    logger.error("Receive command error", error=str(e))
                    # Continue receiving commands even if one fails
        
        # Run send and receive concurrently
        send_task = asyncio.create_task(send_frames())
        receive_task = asyncio.create_task(receive_commands())
        
        # Wait for either task to complete
        done, pending = await asyncio.wait(
            [send_task, receive_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel remaining tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
                
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
    finally:
        try:
            await websocket.close()
        except:
            pass
        logger.info("WebSocket stream ended", profile_id=profile_id)