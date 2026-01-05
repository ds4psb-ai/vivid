"""Handle Pattern storage interface for large artifacts.

The Handle Pattern allows tools to reference large data (images, video, storyboards)
without embedding them in context. This keeps agent context lean while allowing
retrieval when needed.

Storage backends can be swapped without changing tool code.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Protocol

from app.logging_config import get_logger

logger = get_logger("handle_storage")


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
    """

    PREFIX = "handle:vivid:"
    METADATA_PREFIX = "handle:meta:"
    DEFAULT_TTL = 3600 * 24  # 24 hours

    def __init__(self, redis_client=None):
        self._redis = redis_client

    async def _get_redis(self):
        """Lazy load Redis client."""
        if self._redis is None:
            from app.redis_client import get_redis_client
            self._redis = get_redis_client()
        return self._redis

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
        """Store data in Redis with handle reference."""
        redis = await self._get_redis()
        ttl = ttl_seconds or self.DEFAULT_TTL

        # Serialize data
        if content_type == "json":
            serialized = json.dumps(data, ensure_ascii=False)
        else:
            serialized = str(data)

        # Store data
        storage_key = f"{self.PREFIX}{key}"
        await redis.setex(storage_key, ttl, serialized)

        # Store metadata
        meta = HandleMetadata(
            key=key,
            storage_type="redis",
            content_type=content_type,
            size_bytes=len(serialized.encode("utf-8")),
            created_at=datetime.utcnow().isoformat() + "Z",
            expires_at=(datetime.utcnow() + timedelta(seconds=ttl)).isoformat() + "Z",
            dimension=metadata.get("dimension") if metadata else None,
            session_id=metadata.get("session_id") if metadata else None,
        )
        meta_key = f"{self.METADATA_PREFIX}{key}"
        await redis.setex(meta_key, ttl, json.dumps(meta.__dict__))

        handle_ref = self._make_handle_ref(key)
        logger.info(f"Stored handle: {handle_ref}", extra={"size_bytes": meta.size_bytes})

        return handle_ref

    async def retrieve(self, handle_ref: str) -> Optional[Any]:
        """Retrieve data by handle reference."""
        key = self._parse_handle_ref(handle_ref)
        if not key:
            logger.warning(f"Invalid handle ref format: {handle_ref}")
            return None

        redis = await self._get_redis()
        storage_key = f"{self.PREFIX}{key}"
        data = await redis.get(storage_key)

        if data is None:
            logger.warning(f"Handle not found: {handle_ref}")
            return None

        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data

    async def exists(self, handle_ref: str) -> bool:
        """Check if handle exists."""
        key = self._parse_handle_ref(handle_ref)
        if not key:
            return False

        redis = await self._get_redis()
        storage_key = f"{self.PREFIX}{key}"
        return await redis.exists(storage_key) > 0

    async def delete(self, handle_ref: str) -> bool:
        """Delete handle and associated data."""
        key = self._parse_handle_ref(handle_ref)
        if not key:
            return False

        redis = await self._get_redis()
        storage_key = f"{self.PREFIX}{key}"
        meta_key = f"{self.METADATA_PREFIX}{key}"

        deleted = await redis.delete(storage_key, meta_key)
        return deleted > 0

    async def get_metadata(self, handle_ref: str) -> Optional[HandleMetadata]:
        """Get metadata for handle."""
        key = self._parse_handle_ref(handle_ref)
        if not key:
            return None

        redis = await self._get_redis()
        meta_key = f"{self.METADATA_PREFIX}{key}"
        data = await redis.get(meta_key)

        if data is None:
            return None

        try:
            return HandleMetadata(**json.loads(data))
        except (json.JSONDecodeError, TypeError):
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
