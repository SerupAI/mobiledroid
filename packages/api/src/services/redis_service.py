"""Redis connection and utilities."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

import redis.asyncio as redis
import structlog

from src.config import settings

logger = structlog.get_logger()

# Global Redis pool
_redis_pool: redis.ConnectionPool | None = None


async def init_redis() -> None:
    """Initialize Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            max_connections=20,
            decode_responses=True,
        )
        logger.info("Redis connection pool initialized", url=settings.redis_url)


async def close_redis() -> None:
    """Close Redis connection pool."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.disconnect()
        _redis_pool = None
        logger.info("Redis connection pool closed")


def get_redis_pool() -> redis.ConnectionPool:
    """Get Redis connection pool."""
    if _redis_pool is None:
        raise RuntimeError("Redis pool not initialized. Call init_redis() first.")
    return _redis_pool


async def get_redis() -> redis.Redis:
    """Get Redis client from pool."""
    return redis.Redis(connection_pool=get_redis_pool())


@asynccontextmanager
async def redis_client() -> AsyncIterator[redis.Redis]:
    """Context manager for Redis client."""
    client = await get_redis()
    try:
        yield client
    finally:
        await client.aclose()


async def check_redis_health() -> bool:
    """Check Redis connectivity."""
    try:
        async with redis_client() as client:
            await client.ping()
            return True
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        return False
