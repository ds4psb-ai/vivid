"""Redis client for application-wide caching."""
from typing import Optional
from redis.asyncio import Redis, from_url as redis_from_url
from app.config import settings

_redis_client: Optional[Redis] = None

async def init_redis() -> None:
    """Initialize Redis client."""
    global _redis_client
    _redis_client = redis_from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )

async def close_redis() -> None:
    """Close Redis client."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None

def get_redis_client() -> Redis:
    """Get Redis client instance."""
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return _redis_client
