"""Task execution API routes."""

from datetime import datetime
from typing import Annotated, Any
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7
import structlog

from src.db import get_db
from src.models.profile import Profile, ProfileStatus
from src.models.task import Task, TaskStatus, TaskLog, TaskLogLevel
from src.schemas.task import TaskCreate, TaskResponse, TaskListResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])

logger = structlog.get_logger()


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
    """Create a new AI task for a profile."""
    # Check profile exists and is running
    result = await db.execute(
        select(Profile).where(Profile.id == profile_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )

    if profile.status != ProfileStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile must be running to execute tasks",
        )

    # Create task
    task = Task(
        id=str(uuid7()),
        profile_id=profile_id,
        prompt=data.prompt,
        output_format=data.output_format,
        status=TaskStatus.PENDING,
    )

    db.add(task)
    await db.flush()
    await db.refresh(task)

    logger.info("Created task", task_id=task.id, profile_id=profile_id)

    return TaskResponse.model_validate(task)


@router.get("/profiles/{profile_id}", response_model=TaskListResponse)
async def list_tasks(
    profile_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 50,
) -> TaskListResponse:
    """List tasks for a profile."""
    # Check profile exists
    result = await db.execute(
        select(Profile).where(Profile.id == profile_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )

    # Get tasks
    result = await db.execute(
        select(Task)
        .where(Task.profile_id == profile_id)
        .order_by(Task.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    tasks = list(result.scalars().all())

    # Get total count
    count_result = await db.execute(
        select(Task.id).where(Task.profile_id == profile_id)
    )
    total = len(count_result.all())

    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    """Get a task by ID."""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    # Load logs
    logs_result = await db.execute(
        select(TaskLog)
        .where(TaskLog.task_id == task_id)
        .order_by(TaskLog.created_at)
    )
    task.logs = list(logs_result.scalars().all())

    return TaskResponse.model_validate(task)


@router.post("/{task_id}/execute", response_model=TaskResponse)
async def execute_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    """Execute a pending task.

    This starts the AI agent to perform the task.
    For real-time updates, use the /stream endpoint.
    """
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    if task.status != TaskStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task is {task.status.value}, expected pending",
        )

    # Check profile is running
    profile_result = await db.execute(
        select(Profile).where(Profile.id == task.profile_id)
    )
    profile = profile_result.scalar_one_or_none()

    if not profile or profile.status != ProfileStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile must be running to execute tasks",
        )

    # Mark as running
    task.status = TaskStatus.RUNNING
    task.started_at = datetime.utcnow()
    await db.flush()

    # Add log entry
    log = TaskLog(
        task_id=task.id,
        level=TaskLogLevel.INFO,
        message="Task execution started",
    )
    db.add(log)
    await db.flush()

    logger.info("Started task execution", task_id=task.id)

    # Note: The actual AI agent execution would happen here
    # For now, return the task with running status
    # Real implementation would use background task or streaming

    await db.refresh(task)
    return TaskResponse.model_validate(task)


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    """Cancel a running task."""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel task with status {task.status.value}",
        )

    task.status = TaskStatus.CANCELLED
    task.completed_at = datetime.utcnow()

    log = TaskLog(
        task_id=task.id,
        level=TaskLogLevel.INFO,
        message="Task cancelled by user",
    )
    db.add(log)
    await db.flush()
    await db.refresh(task)

    logger.info("Cancelled task", task_id=task.id)

    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a task."""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
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
    await db.flush()

    logger.info("Deleted task", task_id=task_id)
