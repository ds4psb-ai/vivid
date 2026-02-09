"""
Centralized Timeout Configuration

Single source of truth for all timeout settings across the application.
Replaces scattered timeout values with unified configuration.

Usage:
    from app.core.timeouts import TimeoutConfig, TimeoutCategory

    # Get timeout for a category
    timeout = TimeoutConfig.get(TimeoutCategory.LLM_GENERATION)

    # Get timeout for a route
    timeout = TimeoutConfig.get_for_route("/api/dimension/veo/generate")

    # Get timeout for a provider
    timeout = TimeoutConfig.get_for_provider("veo")
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Dict, List, Optional, Tuple


class TimeoutCategory(Enum):
    """Timeout categories for different operation types."""
    # Fast operations (< 10s)
    HEALTH = 5.0            # Health checks, readiness probes
    CACHE = 2.0             # Redis cache operations
    DATABASE = 10.0         # Database queries

    # Standard operations (10-60s)
    FAST_API = 15.0         # Quick API calls
    STANDARD_API = 30.0     # Standard API operations
    RAG_QUERY = 60.0        # RAG search operations

    # LLM operations (60-300s)
    LLM_GENERATION = 120.0  # Gemini text generation
    LLM_AGENT = 180.0       # Agent chat with tool use

    # Video/Media operations (>300s)
    VIDEO_GENERATION = 300.0  # Veo/Kling video generation
    LONG_VIDEO = 600.0        # Long-form video (10 min)
    BATCH_OPERATION = 900.0   # Batch processing jobs


class TimeoutConfig:
    """
    Centralized timeout configuration.

    Provides timeouts organized by:
    1. Category (operation type)
    2. Route pattern (URL matching)
    3. Provider name (external service)
    """

    # Category-based timeouts (in seconds)
    CATEGORY_TIMEOUTS: Dict[TimeoutCategory, float] = {
        TimeoutCategory.HEALTH: 5.0,
        TimeoutCategory.CACHE: 2.0,
        TimeoutCategory.DATABASE: 10.0,
        TimeoutCategory.FAST_API: 15.0,
        TimeoutCategory.STANDARD_API: 30.0,
        TimeoutCategory.RAG_QUERY: 60.0,
        TimeoutCategory.LLM_GENERATION: 120.0,
        TimeoutCategory.LLM_AGENT: 180.0,
        TimeoutCategory.VIDEO_GENERATION: 300.0,
        TimeoutCategory.LONG_VIDEO: 600.0,
        TimeoutCategory.BATCH_OPERATION: 900.0,
    }

    # Route pattern to timeout mapping (regex, timeout_seconds)
    # Evaluated in order, first match wins
    ROUTE_TIMEOUTS: List[Tuple[str, float]] = [
        # Health checks - very fast
        (r"^/health", 5.0),
        (r"^/metrics", 5.0),
        (r"^/ready", 5.0),

        # Video generation - very slow
        (r"^/api/v1/production/", 300.0),     # Veo/Kling production
        (r"^/api/dimension/veo", 300.0),      # Veo dimension app
        (r"^/api/dimension/video", 300.0),    # Video dimension apps

        # Batch operations - longest
        (r"^/api/v1/batch/", 600.0),          # Batch jobs
        (r"^/api/v1/scene-detect/", 600.0),   # Academy video upload + ffmpeg

        # LLM operations - slow
        (r"^/api/dimension/", 120.0),         # Dimension apps (LLM)
        (r"^/api/v1/agent/", 180.0),          # Agent chat
        (r"^/api/v1/capsules/", 120.0),       # Capsule execution

        # RAG operations - medium
        (r"^/api/v1/rag/", 60.0),             # RAG queries
        (r"^/api/v1/context/", 60.0),         # Context library

        # Standard API operations
        (r"^/api/", 30.0),                    # Default API
        (r"^/graphql", 30.0),                 # GraphQL

        # Default fallback
        (r".*", 30.0),
    ]

    # Provider-specific timeouts
    PROVIDER_TIMEOUTS: Dict[str, float] = {
        # LLM providers
        "gemini": 120.0,
        "gemini_agent": 180.0,

        # Video providers
        "veo": 300.0,
        "kling": 600.0,
        "suno": 180.0,

        # RAG providers
        "notebooklm": 60.0,
        "qdrant": 30.0,

        # Infrastructure
        "redis": 2.0,
        "postgres": 10.0,
    }

    # Client-side timeouts for HTTP clients
    CLIENT_TIMEOUTS: Dict[str, Dict[str, float]] = {
        "gemini": {
            "connect": 10.0,
            "read": 120.0,
            "write": 30.0,
            "pool": 5.0,
        },
        "veo": {
            "connect": 10.0,
            "read": 300.0,
            "write": 60.0,
            "pool": 5.0,
        },
        "kling": {
            "connect": 10.0,
            "read": 600.0,
            "write": 60.0,
            "pool": 5.0,
        },
        "qdrant": {
            "connect": 5.0,
            "read": 30.0,
            "write": 30.0,
            "pool": 5.0,
        },
        "default": {
            "connect": 10.0,
            "read": 30.0,
            "write": 30.0,
            "pool": 5.0,
        },
    }

    @classmethod
    def get(cls, category: TimeoutCategory) -> float:
        """Get timeout for a category.

        Args:
            category: TimeoutCategory enum value

        Returns:
            Timeout in seconds
        """
        return cls.CATEGORY_TIMEOUTS.get(category, 30.0)

    @classmethod
    def get_for_route(cls, path: str) -> float:
        """Get timeout for a route path.

        Args:
            path: URL path (e.g., "/api/dimension/veo/generate")

        Returns:
            Timeout in seconds
        """
        for pattern, timeout in cls.ROUTE_TIMEOUTS:
            if re.match(pattern, path):
                return timeout
        return 30.0  # Default fallback

    @classmethod
    def get_for_provider(cls, provider: str) -> float:
        """Get timeout for a provider.

        Args:
            provider: Provider name (e.g., "gemini", "veo")

        Returns:
            Timeout in seconds
        """
        return cls.PROVIDER_TIMEOUTS.get(provider.lower(), 30.0)

    @classmethod
    def get_client_timeouts(cls, provider: str) -> Dict[str, float]:
        """Get HTTP client timeouts for a provider.

        Args:
            provider: Provider name

        Returns:
            Dict with connect, read, write, pool timeouts
        """
        return cls.CLIENT_TIMEOUTS.get(
            provider.lower(),
            cls.CLIENT_TIMEOUTS["default"]
        )

    @classmethod
    def get_route_timeout_list(cls) -> List[Tuple[str, float]]:
        """Get all route timeouts for middleware configuration.

        Returns:
            List of (pattern, timeout) tuples
        """
        return cls.ROUTE_TIMEOUTS.copy()


# =============================================================================
# Convenience Functions
# =============================================================================

def get_timeout(category: TimeoutCategory) -> float:
    """Shorthand for TimeoutConfig.get()."""
    return TimeoutConfig.get(category)


def get_route_timeout(path: str) -> float:
    """Shorthand for TimeoutConfig.get_for_route()."""
    return TimeoutConfig.get_for_route(path)


def get_provider_timeout(provider: str) -> float:
    """Shorthand for TimeoutConfig.get_for_provider()."""
    return TimeoutConfig.get_for_provider(provider)


# =============================================================================
# Timeout Context Manager
# =============================================================================

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator


class TimeoutError(Exception):
    """Custom timeout error with context."""

    def __init__(self, operation: str, timeout: float, provider: Optional[str] = None):
        self.operation = operation
        self.timeout = timeout
        self.provider = provider
        message = f"Operation '{operation}' timed out after {timeout}s"
        if provider:
            message += f" (provider: {provider})"
        super().__init__(message)


@asynccontextmanager
async def with_timeout(
    timeout: float,
    operation: str = "operation",
    provider: Optional[str] = None,
) -> AsyncGenerator[None, None]:
    """
    Context manager for timeout-protected operations.

    Args:
        timeout: Timeout in seconds
        operation: Operation name for error message
        provider: Optional provider name

    Usage:
        async with with_timeout(60.0, "rag_query", "qdrant"):
            result = await perform_search()

    Raises:
        TimeoutError: If operation exceeds timeout
    """
    try:
        async with asyncio.timeout(timeout):
            yield
    except asyncio.TimeoutError:
        raise TimeoutError(operation, timeout, provider) from None


@asynccontextmanager
async def with_category_timeout(
    category: TimeoutCategory,
    operation: str = "operation",
    provider: Optional[str] = None,
) -> AsyncGenerator[None, None]:
    """
    Context manager using category-based timeout.

    Args:
        category: TimeoutCategory for the operation
        operation: Operation name for error message
        provider: Optional provider name

    Usage:
        async with with_category_timeout(TimeoutCategory.RAG_QUERY, "search"):
            result = await perform_search()
    """
    timeout = TimeoutConfig.get(category)
    async with with_timeout(timeout, operation, provider):
        yield


@asynccontextmanager
async def with_provider_timeout(
    provider: str,
    operation: str = "operation",
) -> AsyncGenerator[None, None]:
    """
    Context manager using provider-based timeout.

    Args:
        provider: Provider name
        operation: Operation name for error message

    Usage:
        async with with_provider_timeout("gemini", "generate"):
            result = await call_gemini()
    """
    timeout = TimeoutConfig.get_for_provider(provider)
    async with with_timeout(timeout, operation, provider):
        yield
