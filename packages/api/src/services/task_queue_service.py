"""Task queue service using arq for background job processing."""

from datetime import datetime, timedelta
from typing import Any
import uuid

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from src.config import settings
from src.models.task import Task, TaskLog, TaskStatus, TaskPriority

logger = structlog.get_logger()

# Global arq pool
_arq_pool: ArqRedis | None = None


def get_redis_settings() -> RedisSettings:
    """Get Redis settings for arq from URL."""
    # Parse redis URL: redis://host:port or redis://host:port/db
    url = settings.redis_url
    if url.startswith("redis://"):
        url = url[8:]

    parts = url.split("/")
    host_port = parts[0]
    database = int(parts[1]) if len(parts) > 1 else 0

    if ":" in host_port:
        host, port = host_port.split(":")
        port = int(port)
    else:
        host = host_port
        port = 6379

    return RedisSettings(host=host, port=port, database=database)


async def init_task_queue() -> None:
    """Initialize arq task queue pool."""
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(get_redis_settings())
        logger.info("Task queue pool initialized")


async def close_task_queue() -> None:
    """Close arq task queue pool."""
    global _arq_pool
    if _arq_pool is not None:
        await _arq_pool.close()
        _arq_pool = None
        logger.info("Task queue pool closed")


def get_arq_pool() -> ArqRedis:
    """Get arq pool."""
    if _arq_pool is None:
        raise RuntimeError("Task queue not initialized. Call init_task_queue() first.")
    return _arq_pool


class TaskQueueService:
    """Service for managing task queue operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(
        self,
        profile_id: str,
        prompt: str,
        output_format: str | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        scheduled_at: datetime | None = None,
        max_retries: int = 3,
    ) -> Task:
        """Create a new task and optionally queue it."""
        task_id = str(uuid.uuid4())

        # Determine initial status
        if scheduled_at and scheduled_at > datetime.utcnow():
            status = TaskStatus.SCHEDULED
        else:
            status = TaskStatus.PENDING

        task = Task(
            id=task_id,
            profile_id=profile_id,
            prompt=prompt,
            output_format=output_format,
            status=status,
            priority=priority,
            scheduled_at=scheduled_at,
            max_retries=max_retries,
        )

        self.db.add(task)
        await self.db.commit()

        # Fetch with eager loading of logs relationship
        result = await self.db.execute(
            select(Task)
            .where(Task.id == task_id)
            .options(selectinload(Task.logs))
        )
        task = result.scalar_one()

        logger.info(
            "Task created",
            task_id=task_id,
            profile_id=profile_id,
            status=status.value,
            scheduled_at=scheduled_at,
        )

        return task

    async def queue_task(self, task: Task) -> str:
        """Add task to Redis queue for processing."""
        pool = get_arq_pool()

        # Calculate defer time if scheduled
        defer_by: timedelta | None = None
        if task.scheduled_at and task.scheduled_at > datetime.utcnow():
            defer_by = task.scheduled_at - datetime.utcnow()

        # Map priority to arq queue name
        queue_name = self._priority_to_queue(task.priority)

        # Enqueue the job
        job = await pool.enqueue_job(
            "execute_task",
            task.id,
            _queue_name=queue_name,
            _defer_by=defer_by,
        )

        # Update task with queue info
        task.status = TaskStatus.QUEUED
        task.queue_job_id = job.job_id
        task.queued_at = datetime.utcnow()
        await self.db.commit()

        logger.info(
            "Task queued",
            task_id=task.id,
            job_id=job.job_id,
            queue=queue_name,
            defer_by=str(defer_by) if defer_by else None,
        )

        return job.job_id

    async def create_and_queue_task(
        self,
        profile_id: str,
        prompt: str,
        output_format: str | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        scheduled_at: datetime | None = None,
        max_retries: int = 3,
    ) -> Task:
        """Create a task and immediately queue it."""
        task = await self.create_task(
            profile_id=profile_id,
            prompt=prompt,
            output_format=output_format,
            priority=priority,
            scheduled_at=scheduled_at,
            max_retries=max_retries,
        )
        await self.queue_task(task)
        return task

    async def cancel_task(self, task_id: str) -> Task | None:
        """Cancel a queued or scheduled task."""
        result = await self.db.execute(
            select(Task)
            .where(Task.id == task_id)
            .options(selectinload(Task.logs))
        )
        task = result.scalar_one_or_none()

        if not task:
            return None

        if task.status not in (TaskStatus.PENDING, TaskStatus.SCHEDULED, TaskStatus.QUEUED):
            logger.warning(
                "Cannot cancel task in current status",
                task_id=task_id,
                status=task.status.value,
            )
            return task

        # Try to abort the arq job if queued
        if task.queue_job_id:
            try:
                pool = get_arq_pool()
                await pool.abort_job(task.queue_job_id)
            except Exception as e:
                logger.warning("Failed to abort arq job", error=str(e))

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()
        await self.db.commit()

        logger.info("Task cancelled", task_id=task_id)
        return task

    async def get_task(self, task_id: str) -> Task | None:
        """Get task by ID."""
        result = await self.db.execute(
            select(Task)
            .where(Task.id == task_id)
            .options(selectinload(Task.logs))
        )
        return result.scalar_one_or_none()

    async def list_tasks(
        self,
        profile_id: str | None = None,
        status: TaskStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Task]:
        """List tasks with optional filters."""
        query = (
            select(Task)
            .options(selectinload(Task.logs))
            .order_by(Task.created_at.desc())
        )

        if profile_id:
            query = query.where(Task.profile_id == profile_id)
        if status:
            query = query.where(Task.status == status)

        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_queue_stats(self) -> dict[str, Any]:
        """Get queue statistics."""
        pool = get_arq_pool()

        # Get job counts by status
        queued = await pool.queued_jobs()

        # Count tasks by status in DB
        stats = {}
        for status in TaskStatus:
            result = await self.db.execute(
                select(Task).where(Task.status == status)
            )
            stats[status.value] = len(result.scalars().all())

        return {
            "queued_jobs": len(queued) if queued else 0,
            "task_counts": stats,
        }

    async def retry_failed_task(self, task_id: str) -> Task | None:
        """Retry a failed task."""
        result = await self.db.execute(
            select(Task)
            .where(Task.id == task_id)
            .options(selectinload(Task.logs))
        )
        task = result.scalar_one_or_none()

        if not task:
            return None

        if task.status != TaskStatus.FAILED:
            logger.warning(
                "Can only retry failed tasks",
                task_id=task_id,
                status=task.status.value,
            )
            return task

        if task.retry_count >= task.max_retries:
            logger.warning(
                "Task has exceeded max retries",
                task_id=task_id,
                retry_count=task.retry_count,
                max_retries=task.max_retries,
            )
            return task

        # Reset task for retry
        task.status = TaskStatus.PENDING
        task.retry_count += 1
        task.error_message = None
        task.result = None
        task.started_at = None
        task.completed_at = None
        await self.db.commit()

        # Re-queue the task
        await self.queue_task(task)

        logger.info(
            "Task queued for retry",
            task_id=task_id,
            retry_count=task.retry_count,
        )

        return task

    def _priority_to_queue(self, priority: TaskPriority) -> str:
        """Map task priority to queue name."""
        return {
            TaskPriority.LOW: "arq:queue:low",
            TaskPriority.NORMAL: "arq:queue",
            TaskPriority.HIGH: "arq:queue:high",
            TaskPriority.URGENT: "arq:queue:urgent",
        }.get(priority, "arq:queue")
