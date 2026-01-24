"""
UQSL Test Configuration

Provides fixtures to mock Redis-backed session cache for testing.
"""

import os
import sys

# Set environment variables BEFORE any app imports
# This ensures rate limiter and other Redis-dependent modules use fallback
os.environ["REDIS_URL"] = ""
os.environ["TESTING"] = "1"

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def pytest_configure(config):
    """Configure test environment before collection."""
    # Ensure Redis URL is empty to trigger fallbacks
    os.environ["REDIS_URL"] = ""
    os.environ["TESTING"] = "1"


@pytest.fixture(autouse=True)
def mock_redis():
    """
    Auto-use fixture to mock Redis connections.

    This prevents any Redis connection attempts during tests.
    """
    # Create mock Redis client
    mock_redis_client = AsyncMock()
    mock_redis_client.ping = AsyncMock(return_value=True)
    mock_redis_client.get = AsyncMock(return_value=None)
    mock_redis_client.set = AsyncMock(return_value=True)
    mock_redis_client.setex = AsyncMock(return_value=True)
    mock_redis_client.delete = AsyncMock(return_value=True)
    mock_redis_client.exists = AsyncMock(return_value=0)
    mock_redis_client.hgetall = AsyncMock(return_value={})
    mock_redis_client.close = AsyncMock()

    # Mock redis.asyncio.from_url to return our mock client
    with patch("redis.asyncio.from_url", return_value=mock_redis_client):
        yield mock_redis_client


@pytest.fixture(autouse=True)
def mock_session_cache(mock_redis):
    """
    Auto-use fixture to mock session cache singleton.

    Depends on mock_redis to ensure Redis is mocked first.
    """
    # Reset the singletons before each test
    import app.uqsl.session_cache as session_cache_module
    import app.routers.uqsl as uqsl_router_module
    session_cache_module.reset_session_cache()
    uqsl_router_module._session_cache = None  # Reset lazy-init cache

    # Create mock cache
    mock_cache = AsyncMock()
    mock_cache.get = AsyncMock(return_value=None)
    mock_cache.set = AsyncMock(return_value=True)
    mock_cache.update = AsyncMock(return_value=True)
    mock_cache.delete = AsyncMock(return_value=True)
    mock_cache.exists = AsyncMock(return_value=False)
    mock_cache.get_stats = AsyncMock(return_value={
        "local_cache_size": 0,
        "local_cache_max": 500,
        "fallback_size": 0,
        "redis_healthy": False,
        "ttl_seconds": 1800,
    })

    # Patch _get_session_cache to return our mock (lazy init function)
    with patch.object(uqsl_router_module, "_get_session_cache", return_value=mock_cache), \
         patch.object(session_cache_module, "get_session_cache", return_value=mock_cache):
        yield mock_cache

    # Cleanup: reset singletons after test
    session_cache_module.reset_session_cache()
    uqsl_router_module._session_cache = None
