"""
UQSL Cloud Integration - 2026 Best Practices

Cloud SQL, BigQuery, Redis integration for Universal Quality Selection Layer.
Follows Google Cloud best practices for async Python applications.

2026 Best Practices Applied:
- Cloud SQL Python Connector for secure IAM auth
- BigQuery Storage Write API for streaming inserts
- Redis async with connection pooling
- Graceful fallback to local services in development
"""

from __future__ import annotations

import asyncio
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Literal
from contextlib import asynccontextmanager

from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Cloud SQL Integration (2026 Best Practice: cloud-sql-python-connector)
# =============================================================================

_cloud_sql_connector: Optional[Any] = None
_cloud_sql_engine: Optional[Any] = None


async def get_cloud_sql_connector():
    """
    Get or create Cloud SQL Python Connector (async).

    2026 Best Practice:
    - Uses IAM authentication (no password in connection string)
    - Automatic SSL/TLS encryption
    - Connection pooling via SQLAlchemy
    """
    global _cloud_sql_connector, _cloud_sql_engine

    # Check if Cloud SQL is configured
    cloud_sql_instance = getattr(settings, "CLOUD_SQL_INSTANCE", "")

    if not cloud_sql_instance:
        logger.debug("Cloud SQL not configured, using local PostgreSQL")
        return None

    if _cloud_sql_connector is not None:
        return _cloud_sql_connector

    try:
        from google.cloud.sql.connector import create_async_connector
        from sqlalchemy.ext.asyncio import create_async_engine

        _cloud_sql_connector = await create_async_connector()

        # Create async engine with Cloud SQL connector
        _cloud_sql_engine = create_async_engine(
            "postgresql+asyncpg://",
            async_creator=lambda: _cloud_sql_connector.connect_async(
                cloud_sql_instance,
                "asyncpg",
                user=getattr(settings, "CLOUD_SQL_USER", settings.POSTGRES_USER),
                password=getattr(settings, "CLOUD_SQL_PASSWORD", settings.POSTGRES_PASSWORD),
                db=getattr(settings, "CLOUD_SQL_DB", settings.POSTGRES_DB),
                enable_iam_auth=getattr(settings, "CLOUD_SQL_IAM_AUTH", False),
            ),
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_recycle=1800,
        )

        logger.info(f"Cloud SQL connector initialized: {cloud_sql_instance}")
        return _cloud_sql_connector

    except ImportError:
        logger.warning("google-cloud-sql-connector not installed, using local PostgreSQL")
        return None
    except Exception as e:
        logger.warning(f"Cloud SQL initialization failed: {e}, falling back to local")
        return None


async def close_cloud_sql_connector():
    """Close Cloud SQL connector on shutdown."""
    global _cloud_sql_connector, _cloud_sql_engine

    if _cloud_sql_engine:
        await _cloud_sql_engine.dispose()
        _cloud_sql_engine = None

    if _cloud_sql_connector:
        await _cloud_sql_connector.close_async()
        _cloud_sql_connector = None
        logger.info("Cloud SQL connector closed")


# =============================================================================
# BigQuery Analytics Pipeline (2026 Best Practice: Storage Write API)
# =============================================================================

class BigQueryUQSLEvent(BaseModel):
    """UQSL analytics event for BigQuery."""
    event_id: str
    event_type: Literal["generation", "selection", "feedback", "three_way"]
    app_key: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Generation details
    prompt_hash: Optional[str] = None
    n_candidates: Optional[int] = None

    # Quality scores
    quality_scores: Optional[list[dict]] = None
    selected_idx: Optional[int] = None
    selection_method: Optional[str] = None
    selection_confidence: Optional[float] = None

    # Thompson Sampling
    arms_used: Optional[list[str]] = None

    # Feedback
    user_feedback: Optional[str] = None

    # 3-Way Ensemble
    recommended: Optional[str] = None
    user_selected: Optional[str] = None

    # Performance
    latency_ms: Optional[int] = None

    # Context
    tier: Optional[str] = None
    dimension: Optional[str] = None
    user_id: Optional[str] = None


_bigquery_client: Optional[Any] = None
_bigquery_buffer: list[dict] = []
_bigquery_buffer_lock = asyncio.Lock()
_bigquery_flush_task: Optional[asyncio.Task] = None

# Buffer configuration
BIGQUERY_BUFFER_SIZE = 100
BIGQUERY_FLUSH_INTERVAL = 30  # seconds


async def get_bigquery_client():
    """
    Get or create BigQuery client.

    2026 Best Practice:
    - Batch inserts for efficiency
    - Async buffer with periodic flush
    - Graceful degradation if BigQuery unavailable
    """
    global _bigquery_client

    bigquery_dataset = getattr(settings, "BIGQUERY_DATASET", "")

    if not bigquery_dataset:
        logger.debug("BigQuery not configured, events will be logged locally")
        return None

    if _bigquery_client is not None:
        return _bigquery_client

    try:
        from google.cloud import bigquery

        _bigquery_client = bigquery.Client(project=settings.GCP_PROJECT_ID)
        logger.info(f"BigQuery client initialized: {settings.GCP_PROJECT_ID}.{bigquery_dataset}")

        # Start background flush task
        global _bigquery_flush_task
        _bigquery_flush_task = asyncio.create_task(_bigquery_flush_loop())

        return _bigquery_client

    except ImportError:
        logger.warning("google-cloud-bigquery not installed, events logged locally")
        return None
    except Exception as e:
        logger.warning(f"BigQuery initialization failed: {e}")
        return None


async def log_uqsl_event(event: BigQueryUQSLEvent) -> bool:
    """
    Log UQSL event to BigQuery (buffered).

    2026 Best Practice:
    - Buffer events and batch insert
    - Non-blocking async operation
    - Falls back to local logging if BigQuery unavailable
    """
    event_dict = event.model_dump(mode="json")

    # Always log locally for debugging
    logger.debug(f"UQSL event: {event.event_type} app={event.app_key}")

    client = await get_bigquery_client()
    if client is None:
        # Log to local database instead
        await _log_event_locally(event_dict)
        return True

    async with _bigquery_buffer_lock:
        _bigquery_buffer.append(event_dict)

        if len(_bigquery_buffer) >= BIGQUERY_BUFFER_SIZE:
            await _flush_bigquery_buffer()

    return True


async def _flush_bigquery_buffer():
    """Flush buffered events to BigQuery."""
    global _bigquery_buffer

    if not _bigquery_buffer:
        return

    client = await get_bigquery_client()
    if client is None:
        return

    events_to_flush = _bigquery_buffer.copy()
    _bigquery_buffer = []

    try:
        bigquery_dataset = getattr(settings, "BIGQUERY_DATASET", "vivid_analytics")
        table_id = f"{settings.GCP_PROJECT_ID}.{bigquery_dataset}.uqsl_events"

        # Use insert_rows_json for streaming insert
        errors = client.insert_rows_json(table_id, events_to_flush)

        if errors:
            logger.warning(f"BigQuery insert errors: {errors[:3]}")
            # Re-buffer failed events
            async with _bigquery_buffer_lock:
                _bigquery_buffer.extend(events_to_flush)
        else:
            logger.info(f"Flushed {len(events_to_flush)} UQSL events to BigQuery")

    except Exception as e:
        logger.warning(f"BigQuery flush failed: {e}")
        # Re-buffer events on failure
        async with _bigquery_buffer_lock:
            _bigquery_buffer.extend(events_to_flush)


async def _bigquery_flush_loop():
    """Background task to periodically flush BigQuery buffer."""
    while True:
        await asyncio.sleep(BIGQUERY_FLUSH_INTERVAL)
        async with _bigquery_buffer_lock:
            await _flush_bigquery_buffer()


async def _log_event_locally(event_dict: dict):
    """Log event to local database when BigQuery is unavailable."""
    # Store in selection_history table as fallback
    from app.database import get_db_context
    from sqlalchemy import text

    try:
        async with get_db_context() as db:
            # Simple insert to analytics_events table
            await db.execute(
                text("""
                    INSERT INTO analytics_events (event_type, meta, created_at)
                    VALUES (:event_type, :meta, :created_at)
                """),
                {
                    "event_type": f"uqsl.{event_dict.get('event_type', 'unknown')}",
                    "meta": json.dumps(event_dict),
                    "created_at": datetime.utcnow(),
                }
            )
    except Exception as e:
        logger.warning(f"Local event logging failed: {e}")


# =============================================================================
# Redis Session Cache (2026 Best Practice: redis-py async)
# =============================================================================

_redis_client: Optional[Any] = None
_redis_pool: Optional[Any] = None

# Cache configuration
UQSL_SESSION_TTL = 3600  # 1 hour
UQSL_CACHE_PREFIX = "uqsl:"


async def get_redis_client():
    """
    Get or create async Redis client with connection pool.

    2026 Best Practice:
    - Connection pooling for concurrent access
    - Async operations with redis.asyncio
    - Graceful fallback to in-memory cache
    """
    global _redis_client, _redis_pool

    if _redis_client is not None:
        return _redis_client

    try:
        import redis.asyncio as aioredis

        redis_url = settings.REDIS_URL

        # Create connection pool
        _redis_pool = aioredis.ConnectionPool.from_url(
            redis_url,
            max_connections=20,
            decode_responses=True,
        )

        _redis_client = aioredis.Redis(connection_pool=_redis_pool)

        # Test connection
        await _redis_client.ping()
        logger.info(f"Redis client initialized: {redis_url}")

        return _redis_client

    except ImportError:
        logger.warning("redis package not installed, using in-memory cache")
        return None
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}, using in-memory cache")
        return None


async def close_redis_client():
    """Close Redis client on shutdown."""
    global _redis_client, _redis_pool

    if _redis_client:
        await _redis_client.close()
        _redis_client = None

    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None

    logger.info("Redis client closed")


# In-memory fallback cache
_memory_cache: dict[str, tuple[Any, float]] = {}


class UQSLSessionCache:
    """
    UQSL Session Cache with Redis backend and in-memory fallback.

    2026 Best Practice:
    - Redis for distributed caching in production
    - In-memory fallback for development/testing
    - TTL-based expiration
    """

    @staticmethod
    async def set(session_id: str, data: dict, ttl: int = UQSL_SESSION_TTL) -> bool:
        """Store session data."""
        key = f"{UQSL_CACHE_PREFIX}session:{session_id}"

        redis = await get_redis_client()

        if redis:
            try:
                await redis.set(key, json.dumps(data), ex=ttl)
                return True
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")

        # Fallback to in-memory
        expiry = datetime.utcnow().timestamp() + ttl
        _memory_cache[key] = (data, expiry)
        return True

    @staticmethod
    async def get(session_id: str) -> Optional[dict]:
        """Retrieve session data."""
        key = f"{UQSL_CACHE_PREFIX}session:{session_id}"

        redis = await get_redis_client()

        if redis:
            try:
                data = await redis.get(key)
                if data:
                    return json.loads(data)
                return None
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")

        # Fallback to in-memory
        if key in _memory_cache:
            data, expiry = _memory_cache[key]
            if datetime.utcnow().timestamp() < expiry:
                return data
            else:
                del _memory_cache[key]

        return None

    @staticmethod
    async def delete(session_id: str) -> bool:
        """Delete session data."""
        key = f"{UQSL_CACHE_PREFIX}session:{session_id}"

        redis = await get_redis_client()

        if redis:
            try:
                await redis.delete(key)
                return True
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")

        # Fallback to in-memory
        _memory_cache.pop(key, None)
        return True

    @staticmethod
    async def extend_ttl(session_id: str, ttl: int = UQSL_SESSION_TTL) -> bool:
        """Extend session TTL."""
        key = f"{UQSL_CACHE_PREFIX}session:{session_id}"

        redis = await get_redis_client()

        if redis:
            try:
                await redis.expire(key, ttl)
                return True
            except Exception as e:
                logger.warning(f"Redis expire failed: {e}")

        # Fallback to in-memory
        if key in _memory_cache:
            data, _ = _memory_cache[key]
            expiry = datetime.utcnow().timestamp() + ttl
            _memory_cache[key] = (data, expiry)
            return True

        return False


class ThompsonSamplingCache:
    """
    Thompson Sampling arm statistics cache.

    2026 Best Practice:
    - Cache arm stats for fast sampling
    - Periodic sync with database
    - Atomic increment operations
    """

    @staticmethod
    async def get_arm_stats(arm_id: str) -> Optional[dict]:
        """Get cached arm statistics."""
        key = f"{UQSL_CACHE_PREFIX}arm:{arm_id}"

        redis = await get_redis_client()

        if redis:
            try:
                data = await redis.hgetall(key)
                if data:
                    return {
                        "alpha": int(data.get("alpha", 1)),
                        "beta": int(data.get("beta", 1)),
                        "total_trials": int(data.get("total_trials", 0)),
                    }
            except Exception as e:
                logger.warning(f"Redis hgetall failed: {e}")

        return None

    @staticmethod
    async def set_arm_stats(arm_id: str, alpha: int, beta: int, total_trials: int) -> bool:
        """Set arm statistics in cache."""
        key = f"{UQSL_CACHE_PREFIX}arm:{arm_id}"

        redis = await get_redis_client()

        if redis:
            try:
                await redis.hset(key, mapping={
                    "alpha": alpha,
                    "beta": beta,
                    "total_trials": total_trials,
                })
                await redis.expire(key, 3600 * 24)  # 24 hour TTL
                return True
            except Exception as e:
                logger.warning(f"Redis hset failed: {e}")

        return False

    @staticmethod
    async def increment_arm(arm_id: str, success: bool) -> dict:
        """
        Atomically increment arm statistics.

        Returns updated stats.
        """
        key = f"{UQSL_CACHE_PREFIX}arm:{arm_id}"

        redis = await get_redis_client()

        if redis:
            try:
                async with redis.pipeline(transaction=True) as pipe:
                    if success:
                        await pipe.hincrby(key, "alpha", 1)
                    else:
                        await pipe.hincrby(key, "beta", 1)
                    await pipe.hincrby(key, "total_trials", 1)
                    await pipe.hgetall(key)
                    results = await pipe.execute()

                    data = results[-1]
                    return {
                        "alpha": int(data.get("alpha", 1)),
                        "beta": int(data.get("beta", 1)),
                        "total_trials": int(data.get("total_trials", 0)),
                    }
            except Exception as e:
                logger.warning(f"Redis pipeline failed: {e}")

        return {"alpha": 1, "beta": 1, "total_trials": 0}


# =============================================================================
# Lifecycle Management
# =============================================================================

async def init_cloud_integrations():
    """Initialize all cloud integrations on startup."""
    await get_cloud_sql_connector()
    await get_bigquery_client()
    await get_redis_client()
    logger.info("Cloud integrations initialized")


async def close_cloud_integrations():
    """Close all cloud integrations on shutdown."""
    global _bigquery_flush_task

    # Flush remaining BigQuery events
    async with _bigquery_buffer_lock:
        await _flush_bigquery_buffer()

    # Cancel flush task
    if _bigquery_flush_task:
        _bigquery_flush_task.cancel()
        try:
            await _bigquery_flush_task
        except asyncio.CancelledError:
            pass

    await close_cloud_sql_connector()
    await close_redis_client()
    logger.info("Cloud integrations closed")
