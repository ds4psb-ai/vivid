"""Handle Pattern storage interface for large artifacts.

The Handle Pattern allows tools to reference large data (images, video, storyboards)
without embedding them in context. This keeps agent context lean while allowing
retrieval when needed.

Storage backends can be swapped without changing tool code.

Hardening (T1):
- Redis connection retry with exponential backoff
- Atomic store operations using pipeline
- Graceful error handling with fallback
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Protocol

from app.logging_config import get_logger

logger = get_logger("handle_storage")


# =============================================================================
# Constants
# =============================================================================

MAX_RETRY_ATTEMPTS = 3
RETRY_BASE_DELAY_MS = 100  # 100ms, 200ms, 400ms exponential backoff


@dataclass(frozen=True)
class HandleMetadata:
    """Metadata for a stored handle."""
    key: str
    storage_type: str  # "redis", "s3", etc.
    content_type: str  # "json", "image", etc.
    size_bytes: int
    created_at: str  # ISO timestamp
    expires_at: Optional[str] = None
    dimension: Optional[str] = None
    session_id: Optional[str] = None


class HandleStorage(Protocol):
    """Protocol for handle storage backends."""

    async def store(
        self,
        key: str,
        data: Any,
        content_type: str = "json",
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store data and return handle reference."""
        ...

    async def retrieve(self, handle_ref: str) -> Optional[Any]:
        """Retrieve data by handle reference."""
        ...

    async def exists(self, handle_ref: str) -> bool:
        """Check if handle exists."""
        ...

    async def delete(self, handle_ref: str) -> bool:
        """Delete handle and data."""
        ...

    async def get_metadata(self, handle_ref: str) -> Optional[HandleMetadata]:
        """Get metadata for handle."""
        ...


class RedisHandleStorage:
    """Redis-based handle storage implementation.

    Format: handle:redis:{key}
    Storage: JSON serialized with metadata prefix

    Hardening:
    - Retry with exponential backoff on connection errors
    - Atomic store using pipeline
    - Graceful degradation on failures
    """

    PREFIX = "handle:vivid:"
    METADATA_PREFIX = "handle:meta:"
    DEFAULT_TTL = 3600 * 24  # 24 hours

    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._connection_failed = False

    async def _get_redis(self):
        """Lazy load Redis client with retry logic."""
        if self._redis is not None:
            return self._redis

        last_error = None
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                from app.redis_client import get_redis_client
                self._redis = get_redis_client()
                # Test connection
                await self._redis.ping()
                self._connection_failed = False
                return self._redis
            except RuntimeError as e:
                # Redis not initialized
                last_error = e
                logger.warning(f"Redis not initialized (attempt {attempt + 1}): {e}")
            except Exception as e:
                last_error = e
                logger.warning(f"Redis connection failed (attempt {attempt + 1}): {e}")

            if attempt < MAX_RETRY_ATTEMPTS - 1:
                delay = (RETRY_BASE_DELAY_MS * (2 ** attempt)) / 1000
                await asyncio.sleep(delay)

        self._connection_failed = True
        logger.error(f"Redis connection failed after {MAX_RETRY_ATTEMPTS} attempts: {last_error}")
        raise ConnectionError(f"Redis unavailable: {last_error}")

    def _is_available(self) -> bool:
        """Check if Redis is available without raising."""
        return self._redis is not None and not self._connection_failed

    def _make_handle_ref(self, key: str) -> str:
        """Create handle reference from key."""
        return f"handle:redis:{key}"

    def _parse_handle_ref(self, handle_ref: str) -> Optional[str]:
        """Extract key from handle reference."""
        if not handle_ref.startswith("handle:redis:"):
            return None
        return handle_ref[len("handle:redis:"):]

    async def store(
        self,
        key: str,
        data: Any,
        content_type: str = "json",
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store data in Redis with handle reference.

        Uses pipeline for atomic storage of data + metadata.
        """
        try:
            redis = await self._get_redis()
        except ConnectionError as e:
            logger.error(f"Cannot store handle, Redis unavailable: {e}")
            raise

        ttl = ttl_seconds or self.DEFAULT_TTL

        # Serialize data
        try:
            if content_type == "json":
                serialized = json.dumps(data, ensure_ascii=False)
            else:
                serialized = str(data)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize data: {e}")
            raise ValueError(f"Data serialization failed: {e}")

        # Prepare keys
        storage_key = f"{self.PREFIX}{key}"
        meta_key = f"{self.METADATA_PREFIX}{key}"

        # Build metadata with defensive null checks
        meta = HandleMetadata(
            key=key,
            storage_type="redis",
            content_type=content_type,
            size_bytes=len(serialized.encode("utf-8")),
            created_at=datetime.utcnow().isoformat() + "Z",
            expires_at=(datetime.utcnow() + timedelta(seconds=ttl)).isoformat() + "Z",
            dimension=metadata.get("dimension") if metadata and isinstance(metadata, dict) else None,
            session_id=metadata.get("session_id") if metadata and isinstance(metadata, dict) else None,
        )
        meta_serialized = json.dumps(meta.__dict__)

        # Atomic store using pipeline
        try:
            async with redis.pipeline(transaction=True) as pipe:
                pipe.setex(storage_key, ttl, serialized)
                pipe.setex(meta_key, ttl, meta_serialized)
                await pipe.execute()
        except Exception as e:
            logger.error(f"Failed to store handle atomically: {e}")
            raise

        handle_ref = self._make_handle_ref(key)
        logger.info(f"Stored handle: {handle_ref}", extra={"size_bytes": meta.size_bytes})

        return handle_ref

    async def retrieve(self, handle_ref: str) -> Optional[Any]:
        """Retrieve data by handle reference."""
        key = self._parse_handle_ref(handle_ref)
        if not key:
            logger.warning(f"Invalid handle ref format: {handle_ref}")
            return None

        try:
            redis = await self._get_redis()
        except ConnectionError:
            logger.error(f"Cannot retrieve handle, Redis unavailable")
            return None

        try:
            storage_key = f"{self.PREFIX}{key}"
            data = await redis.get(storage_key)
        except Exception as e:
            logger.error(f"Redis get failed for {handle_ref}: {e}")
            return None

        if data is None:
            logger.warning(f"Handle not found: {handle_ref}")
            return None

        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode failed for {handle_ref}, returning raw: {e}")
            return data

    async def exists(self, handle_ref: str) -> bool:
        """Check if handle exists."""
        key = self._parse_handle_ref(handle_ref)
        if not key:
            return False

        try:
            redis = await self._get_redis()
            storage_key = f"{self.PREFIX}{key}"
            return await redis.exists(storage_key) > 0
        except Exception as e:
            logger.error(f"Redis exists check failed for {handle_ref}: {e}")
            return False

    async def delete(self, handle_ref: str) -> bool:
        """Delete handle and associated data (atomic)."""
        key = self._parse_handle_ref(handle_ref)
        if not key:
            return False

        try:
            redis = await self._get_redis()
        except ConnectionError:
            logger.error(f"Cannot delete handle, Redis unavailable")
            return False

        storage_key = f"{self.PREFIX}{key}"
        meta_key = f"{self.METADATA_PREFIX}{key}"

        try:
            # Atomic delete using pipeline
            async with redis.pipeline(transaction=True) as pipe:
                pipe.delete(storage_key)
                pipe.delete(meta_key)
                results = await pipe.execute()
            return sum(results) > 0
        except Exception as e:
            logger.error(f"Redis delete failed for {handle_ref}: {e}")
            return False

    async def get_metadata(self, handle_ref: str) -> Optional[HandleMetadata]:
        """Get metadata for handle."""
        key = self._parse_handle_ref(handle_ref)
        if not key:
            return None

        try:
            redis = await self._get_redis()
        except ConnectionError:
            logger.error(f"Cannot get metadata, Redis unavailable")
            return None

        try:
            meta_key = f"{self.METADATA_PREFIX}{key}"
            data = await redis.get(meta_key)
        except Exception as e:
            logger.error(f"Redis get metadata failed for {handle_ref}: {e}")
            return None

        if data is None:
            return None

        try:
            parsed = json.loads(data)
            # Validate required fields before creating HandleMetadata
            required_fields = ["key", "storage_type", "content_type", "size_bytes", "created_at"]
            for field in required_fields:
                if field not in parsed:
                    logger.warning(f"Missing required field '{field}' in metadata for {handle_ref}")
                    return None
            return HandleMetadata(**parsed)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode failed for metadata {handle_ref}: {e}")
            return None
        except TypeError as e:
            logger.error(f"Invalid metadata structure for {handle_ref}: {e}")
            return None


# =============================================================================
# Global storage instance (pluggable)
# =============================================================================

_handle_storage: Optional[HandleStorage] = None


def get_handle_storage() -> HandleStorage:
    """Get the global handle storage instance."""
    global _handle_storage
    if _handle_storage is None:
        _handle_storage = RedisHandleStorage()
    return _handle_storage


def set_handle_storage(storage: HandleStorage) -> None:
    """Set custom handle storage backend."""
    global _handle_storage
    _handle_storage = storage
