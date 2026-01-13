"""Task execution API routes."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.db import get_db
from src.models.profile import Profile, ProfileStatus
from src.models.task import Task, TaskStatus, TaskPriority
from src.schemas.task import (
    TaskCreate,
    TaskResponse,
    TaskListResponse,
    QueueStatsResponse,
)
from src.services.task_queue_service import TaskQueueService

router = APIRouter(prefix="/tasks", tags=["tasks"])

logger = structlog.get_logger()


def get_task_queue_service(db: AsyncSession) -> TaskQueueService:
    """Get task queue service instance."""
    return TaskQueueService(db)


@router.post(
    "/profiles/{profile_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    profile_id: str,
    data: TaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    """Create a new AI task for a profile.

    The task can be:
    - Queued immediately for execution
    - Scheduled for future execution
    - Created as pending (manual queue later)
    """
    # Check profile exists
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )

    # For immediate execution, profile must be running
    # For scheduled tasks, we'll check at execution time
    if data.queue_immediately and not data.scheduled_at:
        if profile.status != ProfileStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile must be running for immediate task execution",
            )

    # Map priority string to enum
    priority = TaskPriority(data.priority)

    queue_service = get_task_queue_service(db)

    if data.queue_immediately:
        task = await queue_service.create_and_queue_task(
            profile_id=profile_id,
            prompt=data.prompt,
            output_format=data.output_format,
            priority=priority,
            scheduled_at=data.scheduled_at,
            max_retries=data.max_retries,
        )
    else:
        task = await queue_service.create_task(
            profile_id=profile_id,
            prompt=data.prompt,
            output_format=data.output_format,
            priority=priority,
            scheduled_at=data.scheduled_at,
            max_retries=data.max_retries,
        )

    logger.info(
        "Created task",
        task_id=task.id,
        profile_id=profile_id,
        queued=data.queue_immediately,
        scheduled_at=data.scheduled_at,
    )

    return TaskResponse.model_validate(task)


@router.get("/profiles/{profile_id}", response_model=TaskListResponse)
async def list_tasks(
    profile_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: TaskStatus | None = Query(None, alias="status"),
    skip: int = 0,
    limit: int = 50,
) -> TaskListResponse:
    """List tasks for a profile."""
    # Check profile exists
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )

    queue_service = get_task_queue_service(db)
    tasks = await queue_service.list_tasks(
        profile_id=profile_id,
        status=status_filter,
        limit=limit,
        offset=skip,
    )

    # Get total count
    count_result = await db.execute(
        select(Task.id).where(Task.profile_id == profile_id)
    )
    total = len(count_result.all())

    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
    )


@router.get("/queue/stats", response_model=QueueStatsResponse)
async def get_queue_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QueueStatsResponse:
    """Get task queue statistics."""
    queue_service = get_task_queue_service(db)
    stats = await queue_service.get_queue_stats()
    return QueueStatsResponse(**stats)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    """Get a task by ID."""
    queue_service = get_task_queue_service(db)
    task = await queue_service.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    return TaskResponse.model_validate(task)


@router.post("/{task_id}/queue", response_model=TaskResponse)
async def queue_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    """Queue a pending task for execution."""
    queue_service = get_task_queue_service(db)
    task = await queue_service.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    if task.status not in (TaskStatus.PENDING, TaskStatus.SCHEDULED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task is {task.status.value}, expected pending or scheduled",
        )

    # Check profile is running
    profile_result = await db.execute(
        select(Profile).where(Profile.id == task.profile_id)
    )
    profile = profile_result.scalar_one_or_none()

    if not profile or profile.status != ProfileStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile must be running to queue tasks",
        )

    await queue_service.queue_task(task)
    await db.refresh(task)

    logger.info("Queued task", task_id=task.id)

    return TaskResponse.model_validate(task)


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    """Cancel a pending, scheduled, or queued task."""
    queue_service = get_task_queue_service(db)
    task = await queue_service.cancel_task(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    return TaskResponse.model_validate(task)


@router.post("/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    """Retry a failed task."""
    queue_service = get_task_queue_service(db)
    task = await queue_service.retry_failed_task(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    if task.status == TaskStatus.FAILED and task.retry_count >= task.max_retries:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task has exceeded max retries ({task.max_retries})",
        )

    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a task."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    if task.status == TaskStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a running task",
        )

    await db.delete(task)
    await db.commit()

    logger.info("Deleted task", task_id=task_id)
