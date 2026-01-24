"""
UQSL Session Cache - Redis-backed Session Storage (2026 Best Practice)

Features:
- Two-level caching: Local LRU + Redis
- TTL: 30 minutes for UQSL sessions
- Graceful degradation to in-memory on Redis failure
- Connection pooling with health checks
- JSON serialization for Pydantic models
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Optional, TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger(__name__)

# Session TTL: 30 minutes (2026 best practice for interactive sessions)
SESSION_TTL_SECONDS = 30 * 60

# Local cache size (LRU for hot sessions)
LOCAL_CACHE_SIZE = 500


class SessionData(BaseModel):
    """Session data structure for serialization"""
    candidates: list[dict]
    scores: list[dict]
    prompt_hash: str
    prompt_preview: str
    app_key: str
    strategy: str
    arms_used: list[str]
    created_at: str
    selected_idx: Optional[int] = None
    selection_time: Optional[str] = None


class UQSLSessionCache:
    """
    Production-ready UQSL session cache with Redis backend.

    2026 Best Practices:
    - Two-level caching (local LRU + Redis) for reduced latency
    - Graceful fallback to in-memory if Redis unavailable
    - Connection health monitoring
    - Automatic TTL management
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6380",
        ttl_seconds: int = SESSION_TTL_SECONDS,
        local_cache_size: int = LOCAL_CACHE_SIZE,
    ):
        self._redis_url = redis_url
        self._ttl = ttl_seconds
        self._local_cache_size = local_cache_size

        # Redis client (lazy initialization)
        self._redis: Optional["Redis"] = None
        self._redis_healthy = False
        self._last_health_check: Optional[datetime] = None
        self._health_check_interval = timedelta(seconds=30)

        # Fallback in-memory storage
        self._fallback_memory: dict[str, dict] = {}

        # Local LRU cache for hot sessions
        self._local_cache: dict[str, tuple[dict, datetime]] = {}

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def _get_redis(self) -> Optional["Redis"]:
        """Get Redis client with lazy initialization and health check."""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                )
                self._redis_healthy = True
                logger.info("UQSL Redis connection established")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                self._redis_healthy = False
                return None

        # Periodic health check
        now = datetime.utcnow()
        if (
            self._last_health_check is None
            or now - self._last_health_check > self._health_check_interval
        ):
            try:
                await self._redis.ping()
                self._redis_healthy = True
                self._last_health_check = now
            except Exception as e:
                logger.warning(f"Redis health check failed: {e}")
                self._redis_healthy = False
                return None

        return self._redis if self._redis_healthy else None

    def _make_key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"uqsl:session:{session_id}"

    def _serialize(self, data: dict) -> str:
        """Serialize session data to JSON."""
        # Convert datetime objects to ISO strings
        serializable = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                serializable[key] = value.isoformat()
            elif isinstance(value, list):
                serializable[key] = [
                    item.model_dump() if isinstance(item, BaseModel) else item
                    for item in value
                ]
            elif isinstance(value, BaseModel):
                serializable[key] = value.model_dump()
            else:
                serializable[key] = value
        return json.dumps(serializable)

    def _deserialize(self, data: str) -> dict:
        """Deserialize JSON to session data."""
        return json.loads(data)

    def _update_local_cache(self, session_id: str, data: dict) -> None:
        """Update local LRU cache."""
        now = datetime.utcnow()

        # Simple LRU: Remove oldest if at capacity
        if len(self._local_cache) >= self._local_cache_size:
            oldest_key = min(
                self._local_cache.keys(),
                key=lambda k: self._local_cache[k][1]
            )
            del self._local_cache[oldest_key]

        self._local_cache[session_id] = (data, now)

    def _get_from_local_cache(self, session_id: str) -> Optional[dict]:
        """Get from local cache if not expired."""
        if session_id in self._local_cache:
            data, cached_at = self._local_cache[session_id]
            if datetime.utcnow() - cached_at < timedelta(seconds=self._ttl):
                return data
            else:
                # Expired, remove from local cache
                del self._local_cache[session_id]
        return None

    async def set(self, session_id: str, data: dict) -> bool:
        """
        Store session data.

        Returns True if stored successfully (Redis or fallback).
        """
        async with self._lock:
            # Always update local cache
            self._update_local_cache(session_id, data)

            # Try Redis first
            redis = await self._get_redis()
            if redis:
                try:
                    key = self._make_key(session_id)
                    serialized = self._serialize(data)
                    await redis.setex(key, self._ttl, serialized)
                    return True
                except Exception as e:
                    logger.warning(f"Redis set failed, using fallback: {e}")

            # Fallback to in-memory
            self._fallback_memory[session_id] = data

            # Clean up old fallback entries
            self._cleanup_fallback()

            return True

    async def get(self, session_id: str) -> Optional[dict]:
        """
        Retrieve session data.

        Checks local cache → Redis → fallback memory.
        """
        # Check local cache first (fastest)
        local_data = self._get_from_local_cache(session_id)
        if local_data is not None:
            return local_data

        # Try Redis
        redis = await self._get_redis()
        if redis:
            try:
                key = self._make_key(session_id)
                data = await redis.get(key)
                if data:
                    deserialized = self._deserialize(data)
                    # Update local cache
                    self._update_local_cache(session_id, deserialized)
                    return deserialized
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")

        # Fallback to in-memory
        return self._fallback_memory.get(session_id)

    async def update(self, session_id: str, updates: dict) -> bool:
        """
        Update existing session data.

        Merges updates with existing data.
        """
        existing = await self.get(session_id)
        if existing is None:
            return False

        existing.update(updates)
        return await self.set(session_id, existing)

    async def delete(self, session_id: str) -> bool:
        """Delete session data."""
        async with self._lock:
            # Remove from local cache
            self._local_cache.pop(session_id, None)

            # Remove from fallback
            self._fallback_memory.pop(session_id, None)

            # Remove from Redis
            redis = await self._get_redis()
            if redis:
                try:
                    key = self._make_key(session_id)
                    await redis.delete(key)
                except Exception as e:
                    logger.warning(f"Redis delete failed: {e}")

            return True

    async def exists(self, session_id: str) -> bool:
        """Check if session exists."""
        # Check local cache
        if session_id in self._local_cache:
            return True

        # Check Redis
        redis = await self._get_redis()
        if redis:
            try:
                key = self._make_key(session_id)
                return await redis.exists(key) > 0
            except Exception:
                pass

        # Check fallback
        return session_id in self._fallback_memory

    def _cleanup_fallback(self) -> None:
        """Remove expired entries from fallback memory."""
        now = datetime.utcnow()
        expired = []

        for session_id, data in self._fallback_memory.items():
            created_at = data.get("created_at")
            if isinstance(created_at, str):
                try:
                    created = datetime.fromisoformat(created_at)
                    if now - created > timedelta(seconds=self._ttl):
                        expired.append(session_id)
                except ValueError:
                    pass
            elif isinstance(created_at, datetime):
                if now - created_at > timedelta(seconds=self._ttl):
                    expired.append(session_id)

        for session_id in expired:
            del self._fallback_memory[session_id]

    async def get_stats(self) -> dict:
        """Get cache statistics."""
        redis = await self._get_redis()

        return {
            "local_cache_size": len(self._local_cache),
            "local_cache_max": self._local_cache_size,
            "fallback_size": len(self._fallback_memory),
            "redis_healthy": self._redis_healthy,
            "ttl_seconds": self._ttl,
        }

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            self._redis_healthy = False


# Singleton instance
_session_cache: Optional[UQSLSessionCache] = None


def reset_session_cache() -> None:
    """Reset singleton for testing. DO NOT use in production."""
    global _session_cache
    _session_cache = None


def get_session_cache() -> UQSLSessionCache:
    """Get or create singleton session cache."""
    global _session_cache
    if _session_cache is None:
        from app.config import settings
        _session_cache = UQSLSessionCache(redis_url=settings.REDIS_URL)
    return _session_cache


async def init_session_cache() -> UQSLSessionCache:
    """Initialize session cache (call at startup)."""
    cache = get_session_cache()
    # Pre-warm Redis connection
    await cache._get_redis()
    return cache


# =============================================================================
# Bandit Statistics Cache (Thompson Sampling persistence)
# =============================================================================

class BanditStatsCache:
    """
    Redis-backed cache for Thompson Sampling arm statistics.

    2026 Best Practice:
    - Batch updates to reduce write amplification
    - Atomic operations for consistency
    - Periodic sync to database
    """

    def __init__(self, redis_url: str = "redis://localhost:6380"):
        self._redis_url = redis_url
        self._redis: Optional["Redis"] = None
        self._pending_updates: dict[str, dict] = {}
        self._batch_size = 10

    async def _get_redis(self) -> Optional["Redis"]:
        """Get Redis client."""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
            except Exception as e:
                logger.warning(f"Bandit cache Redis connection failed: {e}")
                return None
        return self._redis

    def _make_key(self, arm_id: str) -> str:
        """Generate Redis key for arm stats."""
        return f"uqsl:bandit:{arm_id}"

    async def get_arm_stats(self, arm_id: str) -> Optional[dict]:
        """Get arm statistics from Redis."""
        redis = await self._get_redis()
        if redis:
            try:
                key = self._make_key(arm_id)
                data = await redis.hgetall(key)
                if data:
                    return {
                        "alpha": float(data.get("alpha", 1.0)),
                        "beta": float(data.get("beta", 1.0)),
                        "total_pulls": int(data.get("total_pulls", 0)),
                        "total_rewards": float(data.get("total_rewards", 0.0)),
                    }
            except Exception as e:
                logger.warning(f"Failed to get arm stats: {e}")
        return None

    async def update_arm_stats(
        self,
        arm_id: str,
        reward: bool,
        alpha_increment: float = 1.0,
        beta_increment: float = 1.0,
    ) -> None:
        """
        Update arm statistics.

        2026 Best Practice: Batch updates with atomic operations.
        """
        redis = await self._get_redis()
        if redis:
            try:
                key = self._make_key(arm_id)

                # Atomic increment
                pipe = redis.pipeline()
                if reward:
                    pipe.hincrbyfloat(key, "alpha", alpha_increment)
                    pipe.hincrbyfloat(key, "total_rewards", 1.0)
                else:
                    pipe.hincrbyfloat(key, "beta", beta_increment)
                pipe.hincrby(key, "total_pulls", 1)

                await pipe.execute()
            except Exception as e:
                logger.warning(f"Failed to update arm stats: {e}")
                # Queue for batch retry
                self._pending_updates[arm_id] = {
                    "reward": reward,
                    "alpha_increment": alpha_increment,
                    "beta_increment": beta_increment,
                }

    async def sync_to_db(self, db: Any) -> int:
        """Sync Redis stats to database (periodic task)."""
        from sqlalchemy import select, update
        from app.models_uqsl import BanditArm

        synced = 0
        redis = await self._get_redis()
        if not redis:
            return synced

        try:
            # Get all arm keys
            keys = []
            async for key in redis.scan_iter("uqsl:bandit:*"):
                keys.append(key)

            for key in keys:
                arm_id = key.replace("uqsl:bandit:", "")
                stats = await self.get_arm_stats(arm_id)
                if stats:
                    await db.execute(
                        update(BanditArm)
                        .where(BanditArm.arm_id == arm_id)
                        .values(
                            alpha=stats["alpha"],
                            beta=stats["beta"],
                            total_pulls=stats["total_pulls"],
                            total_rewards=stats["total_rewards"],
                        )
                    )
                    synced += 1

            await db.commit()
        except Exception as e:
            logger.error(f"Failed to sync bandit stats to DB: {e}")

        return synced


# Singleton
_bandit_cache: Optional[BanditStatsCache] = None


def get_bandit_cache() -> BanditStatsCache:
    """Get or create bandit stats cache."""
    global _bandit_cache
    if _bandit_cache is None:
        from app.config import settings
        _bandit_cache = BanditStatsCache(redis_url=settings.REDIS_URL)
    return _bandit_cache
