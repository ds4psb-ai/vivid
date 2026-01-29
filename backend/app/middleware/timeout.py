"""
Request Timeout Middleware

Prevents slow requests from holding resources indefinitely.
Configurable timeout per route pattern.

Based on: Production Readiness Score 8.3 → 9.0+ Plan
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Callable, Dict, List, Tuple

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.schemas.problem_details import ProblemDetail, ProblemTypes

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

# Default timeout in seconds
DEFAULT_TIMEOUT = 30.0

# Route-specific timeouts (regex pattern -> timeout in seconds)
# Longer timeouts for LLM/video generation endpoints
ROUTE_TIMEOUTS: List[Tuple[str, float]] = [
    # Video generation - very slow operations
    (r"^/api/v1/production/", 300.0),  # 5 minutes for video generation
    (r"^/api/dimension/veo", 300.0),   # 5 minutes for Veo

    # LLM operations - can be slow
    (r"^/api/dimension/", 120.0),      # 2 minutes for dimension apps
    (r"^/api/v1/agent/", 120.0),       # 2 minutes for agent chat

    # RAG operations
    (r"^/api/v1/rag/", 60.0),          # 1 minute for RAG queries

    # Batch operations
    (r"^/api/v1/batch/", 600.0),       # 10 minutes for batch jobs

    # Standard API operations
    (r"^/api/", 30.0),                 # 30 seconds for general API

    # Health checks - should be fast
    (r"^/health", 5.0),                # 5 seconds for health checks
]


def get_timeout_for_path(path: str) -> float:
    """Get timeout for a given request path.

    Args:
        path: Request URL path

    Returns:
        Timeout in seconds
    """
    for pattern, timeout in ROUTE_TIMEOUTS:
        if re.match(pattern, path):
            return timeout
    return DEFAULT_TIMEOUT


# =============================================================================
# Middleware
# =============================================================================

class TimeoutMiddleware(BaseHTTPMiddleware):
    """Request timeout middleware.

    Cancels requests that exceed the configured timeout.
    Returns a 504 Gateway Timeout response.

    Usage:
        app.add_middleware(TimeoutMiddleware)

    Note:
        - Timeout is per-request, not total connection time
        - Long-running SSE streams should be excluded or have very long timeouts
        - The middleware uses asyncio.timeout (Python 3.11+) or asyncio.wait_for
    """

    def __init__(
        self,
        app,
        default_timeout: float = DEFAULT_TIMEOUT,
        route_timeouts: List[Tuple[str, float]] | None = None,
    ):
        super().__init__(app)
        self.default_timeout = default_timeout
        self.route_timeouts = route_timeouts or ROUTE_TIMEOUTS

    def _get_timeout(self, path: str) -> float:
        """Get timeout for request path."""
        for pattern, timeout in self.route_timeouts:
            if re.match(pattern, path):
                return timeout
        return self.default_timeout

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with timeout."""
        path = request.url.path
        timeout = self._get_timeout(path)

        # Skip timeout for SSE endpoints (they stream indefinitely)
        if "text/event-stream" in request.headers.get("accept", ""):
            return await call_next(request)

        try:
            # Use asyncio.timeout for Python 3.11+ (cleaner cancellation)
            async with asyncio.timeout(timeout):
                return await call_next(request)

        except asyncio.TimeoutError:
            logger.warning(
                f"Request timeout: path={path} timeout={timeout}s "
                f"method={request.method}"
            )

            # Return RFC 9457 compliant error response
            problem = ProblemDetail(
                type=ProblemTypes.TIMEOUT,
                title="Request Timeout",
                status=504,
                detail=f"Request exceeded timeout of {timeout} seconds",
                error_code="REQUEST_TIMEOUT",
            )

            return JSONResponse(
                status_code=504,
                content=problem.model_dump(mode="json", exclude_none=True),
                media_type="application/problem+json",
            )

        except Exception as e:
            # Let other exceptions propagate normally
            raise


# =============================================================================
# Fallback for Python < 3.11
# =============================================================================

class TimeoutMiddlewareLegacy(BaseHTTPMiddleware):
    """Legacy timeout middleware using asyncio.wait_for.

    For Python versions < 3.11 that don't have asyncio.timeout.
    """

    def __init__(
        self,
        app,
        default_timeout: float = DEFAULT_TIMEOUT,
        route_timeouts: List[Tuple[str, float]] | None = None,
    ):
        super().__init__(app)
        self.default_timeout = default_timeout
        self.route_timeouts = route_timeouts or ROUTE_TIMEOUTS

    def _get_timeout(self, path: str) -> float:
        """Get timeout for request path."""
        for pattern, timeout in self.route_timeouts:
            if re.match(pattern, path):
                return timeout
        return self.default_timeout

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with timeout using wait_for."""
        path = request.url.path
        timeout = self._get_timeout(path)

        # Skip timeout for SSE endpoints
        if "text/event-stream" in request.headers.get("accept", ""):
            return await call_next(request)

        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=timeout,
            )

        except asyncio.TimeoutError:
            logger.warning(
                f"Request timeout: path={path} timeout={timeout}s "
                f"method={request.method}"
            )

            problem = ProblemDetail(
                type=ProblemTypes.TIMEOUT,
                title="Request Timeout",
                status=504,
                detail=f"Request exceeded timeout of {timeout} seconds",
                error_code="REQUEST_TIMEOUT",
            )

            return JSONResponse(
                status_code=504,
                content=problem.model_dump(mode="json", exclude_none=True),
                media_type="application/problem+json",
            )
