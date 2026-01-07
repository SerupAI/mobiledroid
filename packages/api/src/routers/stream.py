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
    """Stream device screen via WebSocket."""
    await websocket.accept()
    
    # Get profile service
    fingerprint_service = get_fingerprint_service()
    docker_service = DockerService(fingerprint_service)
    adb_service = ADBService()
    profile_service = ProfileService(db, docker_service, adb_service)
    
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
        
        # Stream screenshots
        frame_interval = 0.067  # ~15 fps
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
                
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected", profile_id=profile_id)
                break
            except Exception as e:
                logger.error("Stream error", error=str(e), profile_id=profile_id)
                error_count += 1
                if error_count > max_errors:
                    await websocket.send_json({"error": "Stream error"})
                    break
                await asyncio.sleep(frame_interval)
                
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
    finally:
        try:
            await websocket.close()
        except:
            pass
        logger.info("WebSocket stream ended", profile_id=profile_id)