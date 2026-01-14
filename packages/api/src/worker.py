"""Task queue worker using arq.

Run with: arq src.worker.WorkerSettings
"""

import uuid
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
from src.models.chat import ChatSession, ChatMessage, ChatMessageRole
from src.services.task_queue_service import get_redis_settings

logger = structlog.get_logger()

# Create async engine for worker
engine = create_async_engine(settings.database_url, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def execute_task(ctx: dict[str, Any], task_id: str) -> dict[str, Any]:
    """Execute a task from the queue.

    This is the main worker function that processes tasks.
    Creates a ChatSession to track step-by-step execution.
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

        chat_session = None

        try:
            # Import here to avoid circular imports
            from src.services.profile_service import ProfileService
            from src.services.docker_service import DockerService
            from src.services.adb_service import ADBService
            from src.services.fingerprint_service import get_fingerprint_service
            from src.services.integration_service import IntegrationService
            from src.agent_wrapper import MobileDroidAgent, AgentConfig

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

            # Get LLM configuration
            integration_service = IntegrationService(db)
            chat_config = await integration_service.get_chat_config()
            if not chat_config:
                raise ValueError("No chat integration configured")

            # Create ChatSession to track execution
            chat_session = ChatSession(
                id=str(uuid.uuid4()),
                profile_id=task.profile_id,
                initial_prompt=task.prompt,
                status="active",
            )
            db.add(chat_session)
            await db.commit()
            await db.refresh(chat_session)

            # Link task to chat session
            task.chat_session_id = chat_session.id
            await db.commit()

            # Save user message (task prompt)
            user_message = ChatMessage(
                session_id=chat_session.id,
                role=ChatMessageRole.USER,
                content=task.prompt,
            )
            db.add(user_message)
            await db.commit()

            # Create agent using MobileDroidAgent (same as chat router)
            adb_address = f"mobiledroid-{task.profile_id}:5555"
            host, port = adb_address.split(":")
            agent = await MobileDroidAgent.connect(
                host=host,
                port=int(port),
                anthropic_api_key=chat_config.api_key,
                config=AgentConfig(
                    max_steps=task.max_retries * 10 + 20,  # More steps for tasks
                    llm_model=chat_config.model_name,
                    temperature=chat_config.temperature,
                ),
            )

            # Execute task with step tracking
            step_count = 0
            cumulative_tokens = 0

            async def on_step(step):
                nonlocal step_count, cumulative_tokens
                step_count += 1
                tokens_this_step = agent.total_tokens - cumulative_tokens
                cumulative_tokens = agent.total_tokens

                # Save step to chat session
                step_message = ChatMessage(
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
                db.add(step_message)
                await db.commit()

            task_result = await agent.execute_task(
                task=task.prompt,
                output_format=task.output_format,
                on_step=on_step,
            )

            # Determine result
            if task_result.success:
                result_text = task_result.result or "Task completed successfully"
                final_status = "completed"
                task.status = TaskStatus.COMPLETED
            else:
                result_text = f"Task failed: {task_result.error}"
                final_status = "error"
                task.status = TaskStatus.FAILED
                task.error_message = task_result.error

            # Save completion message
            completion_message = ChatMessage(
                session_id=chat_session.id,
                role=ChatMessageRole.ASSISTANT,
                content=result_text,
                cumulative_tokens=task_result.total_tokens,
            )
            db.add(completion_message)

            # Update chat session totals
            chat_session.total_tokens = task_result.total_tokens
            chat_session.total_input_tokens = task_result.total_tokens // 2
            chat_session.total_output_tokens = task_result.total_tokens // 2
            chat_session.total_steps = len(task_result.steps)
            chat_session.status = final_status
            chat_session.completed_at = datetime.utcnow()

            # Update task metrics
            task.result = result_text
            task.completed_at = datetime.utcnow()
            task.steps_taken = len(task_result.steps)
            task.tokens_used = task_result.total_tokens

            await db.commit()

            logger.info(
                "Task completed",
                task_id=task_id,
                chat_session_id=chat_session.id,
                success=task_result.success,
                steps=task.steps_taken,
                tokens=task.tokens_used,
            )

            return {
                "success": task_result.success,
                "result": result_text,
                "steps_taken": task.steps_taken,
                "tokens_used": task.tokens_used,
                "chat_session_id": chat_session.id,
            }

        except Exception as e:
            logger.error("Task execution failed", task_id=task_id, error=str(e))

            # Update task with failure
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()

            # Update chat session if it was created
            if chat_session:
                chat_session.status = "error"
                chat_session.completed_at = datetime.utcnow()
                # Save error message
                error_message = ChatMessage(
                    session_id=chat_session.id,
                    role=ChatMessageRole.ERROR,
                    content=str(e),
                )
                db.add(error_message)

            await db.commit()

            # Check if we should retry
            if task.retry_count < task.max_retries:
                logger.info(
                    "Task will be retried",
                    task_id=task_id,
                    retry_count=task.retry_count,
                    max_retries=task.max_retries,
                )

            return {
                "success": False,
                "error": str(e),
                "chat_session_id": chat_session.id if chat_session else None,
            }


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
