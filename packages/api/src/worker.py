"""Task queue worker using arq.

Run with: arq src.worker.WorkerSettings
"""

from datetime import datetime
from typing import Any

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import structlog

from src.config import settings
from src.models.task import Task, TaskStatus
from src.services.task_queue_service import get_redis_settings

logger = structlog.get_logger()

# Create async engine for worker
engine = create_async_engine(settings.database_url, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def execute_task(ctx: dict[str, Any], task_id: str) -> dict[str, Any]:
    """Execute a task from the queue.

    This is the main worker function that processes tasks.
    """
    logger.info("Worker picking up task", task_id=task_id)

    async with async_session() as db:
        # Get the task
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            logger.error("Task not found", task_id=task_id)
            return {"success": False, "error": "Task not found"}

        # Check if task was cancelled
        if task.status == TaskStatus.CANCELLED:
            logger.info("Task was cancelled, skipping", task_id=task_id)
            return {"success": False, "error": "Task cancelled"}

        # Mark as running
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        await db.commit()

        try:
            # Import here to avoid circular imports
            from src.services.profile_service import ProfileService
            from src.services.docker_service import DockerService
            from src.services.adb_service import ADBService
            from src.services.fingerprint_service import get_fingerprint_service
            from src.agent.agent import MobileAgent

            # Get profile
            profile_result = await db.execute(
                select(Task.profile).where(Task.id == task_id)
            )

            # Re-fetch task with profile
            result = await db.execute(
                select(Task).where(Task.id == task_id)
            )
            task = result.scalar_one_or_none()

            if not task:
                raise ValueError("Task disappeared during execution")

            # Setup services
            fingerprint_service = get_fingerprint_service()
            docker_service = DockerService(fingerprint_service)
            adb_service = ADBService()
            profile_service = ProfileService(db, docker_service, adb_service)

            # Get profile
            profile = await profile_service.get(task.profile_id)
            if not profile:
                raise ValueError(f"Profile {task.profile_id} not found")

            if profile.status.value != "running":
                raise ValueError(f"Profile {task.profile_id} is not running")

            # Create agent and execute
            adb_address = f"mobiledroid-{task.profile_id}:5555"
            agent = MobileAgent(adb_service, adb_address)

            # Execute the task
            result_text = await agent.execute(task.prompt, max_steps=20)

            # Update task with success
            task.status = TaskStatus.COMPLETED
            task.result = result_text
            task.completed_at = datetime.utcnow()
            task.steps_taken = agent.steps_taken if hasattr(agent, 'steps_taken') else 0
            task.tokens_used = agent.tokens_used if hasattr(agent, 'tokens_used') else 0
            await db.commit()

            logger.info(
                "Task completed successfully",
                task_id=task_id,
                steps=task.steps_taken,
                tokens=task.tokens_used,
            )

            return {
                "success": True,
                "result": result_text,
                "steps_taken": task.steps_taken,
                "tokens_used": task.tokens_used,
            }

        except Exception as e:
            logger.error("Task execution failed", task_id=task_id, error=str(e))

            # Update task with failure
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            await db.commit()

            # Check if we should retry
            if task.retry_count < task.max_retries:
                logger.info(
                    "Task will be retried",
                    task_id=task_id,
                    retry_count=task.retry_count,
                    max_retries=task.max_retries,
                )
                # The retry logic is handled by task_queue_service.retry_failed_task
                # or can be auto-retried by arq with job_retry setting

            return {"success": False, "error": str(e)}


async def check_scheduled_tasks(ctx: dict[str, Any]) -> None:
    """Cron job to check for scheduled tasks that need to be queued.

    Runs every minute to find tasks with scheduled_at in the past
    that haven't been queued yet.
    """
    logger.debug("Checking for scheduled tasks")

    async with async_session() as db:
        # Find scheduled tasks that are due
        now = datetime.utcnow()
        result = await db.execute(
            select(Task).where(
                Task.status == TaskStatus.SCHEDULED,
                Task.scheduled_at <= now,
            )
        )
        tasks = result.scalars().all()

        if not tasks:
            return

        logger.info("Found scheduled tasks to queue", count=len(tasks))

        # Import here to avoid circular imports
        from src.services.task_queue_service import TaskQueueService

        queue_service = TaskQueueService(db)
        for task in tasks:
            try:
                await queue_service.queue_task(task)
            except Exception as e:
                logger.error(
                    "Failed to queue scheduled task",
                    task_id=task.id,
                    error=str(e),
                )


async def startup(ctx: dict[str, Any]) -> None:
    """Worker startup hook."""
    logger.info("Task worker starting up")


async def shutdown(ctx: dict[str, Any]) -> None:
    """Worker shutdown hook."""
    logger.info("Task worker shutting down")
    await engine.dispose()


class WorkerSettings:
    """arq worker settings."""

    functions = [execute_task]
    cron_jobs = [
        cron(check_scheduled_tasks, minute={0, 15, 30, 45}),  # Every 15 minutes
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = get_redis_settings()
    max_jobs = 10
    job_timeout = 600  # 10 minutes max per task
    keep_result = 3600  # Keep results for 1 hour
    health_check_interval = 30
    queue_read_limit = 10
