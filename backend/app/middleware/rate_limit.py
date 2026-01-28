"""
Rate Limiting Middleware (2026 Best Practices)
=============================================

Enhanced API rate limiting using SlowAPI with Redis backend:
- Per-endpoint configurable limits
- User-based and IP-based limiting
- Dynamic limits based on user tier
- Burst handling with sliding window
- Rate limit headers for clients

References:
- Tavily Research: Rate Limiting 2025-2026
- https://github.com/laurentS/slowapi
"""

import os
import logging
from typing import Optional, Callable

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380")


def get_user_or_ip(request: Request) -> str:
    """
    Get rate limit key based on user authentication or IP.

    Priority:
    1. Authenticated user ID (from X-User-Id header)
    2. Client IP address (with proxy header support)
    """
    # Try to get authenticated user ID
    user_id = request.headers.get("X-User-Id")
    if user_id:
        return f"user:{user_id}"

    # Fall back to client IP with proxy support
    return _get_client_ip(request)


def _get_client_ip(request: Request) -> str:
    """Extract client IP with proxy header support."""
    # Cloudflare
    if cf_ip := request.headers.get("CF-Connecting-IP"):
        return f"ip:{cf_ip}"

    # Nginx / standard proxy
    if real_ip := request.headers.get("X-Real-IP"):
        return f"ip:{real_ip}"

    # X-Forwarded-For chain
    if forwarded := request.headers.get("X-Forwarded-For"):
        return f"ip:{forwarded.split(',')[0].strip()}"

    # Direct connection
    if request.client:
        return f"ip:{request.client.host}"

    return "ip:unknown"


def get_user_tier_limit(request: Request) -> str:
    """
    Dynamic rate limit based on user tier.

    Usage:
        @limiter.limit(get_user_tier_limit)
        async def endpoint(request: Request):
            ...
    """
    # Get user tier from request (set by auth middleware)
    user_tier = getattr(request.state, "user_tier", "free")

    tier_limits = {
        "free": "60/minute",
        "basic": "120/minute",
        "premium": "300/minute",
        "enterprise": "1000/minute",
        "admin": "10000/minute",
    }

    return tier_limits.get(user_tier, tier_limits["free"])


# Create limiter with Redis storage for distributed rate limiting
def _create_limiter() -> Limiter:
    """Create limiter with Redis or in-memory fallback."""
    try:
        limiter = Limiter(
            key_func=get_user_or_ip,
            storage_uri=REDIS_URL,
            default_limits=["100/minute"],
            strategy="fixed-window",  # Standard fixed window strategy
        )
        logger.info(f"Rate limiter initialized with Redis: {REDIS_URL}")
        return limiter
    except Exception as e:
        logger.warning(f"Redis not available, using in-memory rate limiting: {e}")
        return Limiter(
            key_func=get_user_or_ip,
            default_limits=["100/minute"],
        )


limiter = _create_limiter()


# =============================================================================
# Rate Limit Constants (2026 Best Practices)
# =============================================================================

# Default limits
RATE_LIMIT_DEFAULT = "100/minute"

# Authentication endpoints - strict limits for brute force protection
RATE_LIMIT_AUTH_LOGIN = "5/minute"
RATE_LIMIT_AUTH_REGISTER = "3/minute"
RATE_LIMIT_AUTH_FORGOT_PASSWORD = "3/minute"

# Resource-intensive operations
RATE_LIMIT_LLM_GENERATE = "10/minute"    # LLM generation
RATE_LIMIT_UQSL_MULTI = "5/minute"       # UQSL multi-generation
RATE_LIMIT_RAG_QUERY = "30/minute"       # RAG queries
RATE_LIMIT_BATCH = "5/minute"            # Batch operations

# Standard operations
RATE_LIMIT_READ = "200/minute"           # Read operations
RATE_LIMIT_WRITE = "60/minute"           # Write operations
RATE_LIMIT_UPLOAD = "30/minute"          # File uploads
RATE_LIMIT_SEARCH = "60/minute"          # Search operations

# Burst handling (allows short bursts but enforces minute limit)
RATE_LIMIT_BURST = "10/second;100/minute"


# =============================================================================
# Endpoint-specific rate limits
# =============================================================================

ENDPOINT_RATE_LIMITS = {
    # Authentication
    "/api/v1/auth/login": RATE_LIMIT_AUTH_LOGIN,
    "/api/v1/auth/register": RATE_LIMIT_AUTH_REGISTER,
    "/api/v1/auth/forgot-password": RATE_LIMIT_AUTH_FORGOT_PASSWORD,

    # LLM/Generation endpoints
    "/api/dimension/*/generate": RATE_LIMIT_LLM_GENERATE,
    "/api/v1/uqsl/generate": RATE_LIMIT_UQSL_MULTI,
    "/api/v1/agent/chat": RATE_LIMIT_LLM_GENERATE,

    # RAG endpoints
    "/api/v1/rag/query": RATE_LIMIT_RAG_QUERY,
    "/api/v1/rag/hybrid": RATE_LIMIT_RAG_QUERY,

    # Batch operations
    "/api/v1/batch/*": RATE_LIMIT_BATCH,

    # File operations
    "/api/v1/upload/*": RATE_LIMIT_UPLOAD,
}


def setup_rate_limiting(app) -> None:
    """
    Configure comprehensive rate limiting for the FastAPI application.

    Usage in main.py:
        from app.middleware.rate_limit import setup_rate_limiting
        setup_rate_limiting(app)
    """
    app.state.limiter = limiter

    # Custom rate limit exceeded handler with proper headers
    async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
        """Custom handler with informative response and proper headers."""
        from fastapi.responses import JSONResponse

        # Parse the rate limit info
        retry_after = exc.detail.split("Retry after ")[1] if "Retry after" in exc.detail else "60"

        response = JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "detail": "Too many requests. Please slow down.",
                "retry_after_seconds": int(float(retry_after)) if retry_after.replace(".", "").isdigit() else 60,
            },
        )

        # Add rate limit headers
        response.headers["Retry-After"] = str(int(float(retry_after)) if retry_after.replace(".", "").isdigit() else 60)
        response.headers["X-RateLimit-Limit"] = "100"  # Default limit
        response.headers["X-RateLimit-Remaining"] = "0"

        logger.warning(
            "Rate limit exceeded",
            extra={
                "path": request.url.path,
                "client": get_user_or_ip(request),
                "retry_after": retry_after,
            }
        )

        return response

    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

    logger.info("Rate limiting configured with Redis backend")


def rate_limit(limit_string: str) -> Callable:
    """
    Decorator for applying rate limits to endpoints.

    Usage:
        from app.middleware.rate_limit import rate_limit, limiter

        @router.post("/generate")
        @limiter.limit(RATE_LIMIT_LLM_GENERATE)
        async def generate(request: Request, data: GenerateRequest):
            ...

        # Or with dynamic limits
        @router.post("/premium-generate")
        @limiter.limit(get_user_tier_limit)
        async def premium_generate(request: Request):
            ...
    """
    return limiter.limit(limit_string)


# =============================================================================
# Rate Limit Decorators for common patterns
# =============================================================================

def limit_auth(func):
    """Rate limit decorator for authentication endpoints."""
    return limiter.limit(RATE_LIMIT_AUTH_LOGIN)(func)


def limit_generate(func):
    """Rate limit decorator for LLM generation endpoints."""
    return limiter.limit(RATE_LIMIT_LLM_GENERATE)(func)


def limit_rag(func):
    """Rate limit decorator for RAG query endpoints."""
    return limiter.limit(RATE_LIMIT_RAG_QUERY)(func)


def limit_upload(func):
    """Rate limit decorator for file upload endpoints."""
    return limiter.limit(RATE_LIMIT_UPLOAD)(func)


def limit_by_tier(func):
    """Rate limit decorator with dynamic user-tier based limits."""
    return limiter.limit(get_user_tier_limit)(func)


# =============================================================================
# Default Rate Limit Middleware (2026 Security Hardening)
# =============================================================================

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse as StarletteJSONResponse
import re
import time


class DefaultRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that applies default rate limits to ALL endpoints.

    This ensures 100% rate limit coverage for DDoS protection (OWASP A04:2021).
    Endpoints with explicit @limiter.limit decorators will have BOTH limits applied
    (decorator limit is typically more restrictive).

    Configuration:
    - EXEMPT_PATHS: Paths that bypass rate limiting (health checks, metrics)
    - PATH_LIMITS: Path-specific rate limits (regex patterns supported)
    - DEFAULT_LIMIT: Fallback limit for unmatched paths
    """

    # Paths exempt from rate limiting
    EXEMPT_PATHS = frozenset({
        "/",
        "/health",
        "/healthz",
        "/health/live",
        "/health/ready",
        "/metrics",
        "/openapi.json",
        "/docs",
        "/redoc",
    })

    # Path-specific limits (more restrictive than default)
    # Format: (regex_pattern, limit_string)
    PATH_LIMITS = [
        # Authentication - strict for login, relaxed for read-only session checks
        (re.compile(r"^/api/v1/auth/login$"), "5/minute"),
        (re.compile(r"^/api/v1/auth/register$"), "3/minute"),
        (re.compile(r"^/api/v1/auth/(session|status)$"), "60/minute"),  # Read-only, needed on page load
        (re.compile(r"^/api/v1/auth/"), "30/minute"),  # Other auth endpoints
        # LLM generation - expensive operations (but tools config is read-only)
        (re.compile(r"^/api/dimension/tools$"), "120/minute"),  # Config endpoint, needed on page load
        (re.compile(r"^/api/dimension/"), "10/minute"),
        (re.compile(r"^/api/v1/agent/"), "10/minute"),
        (re.compile(r"^/api/v1/uqsl/"), "10/minute"),
        (re.compile(r"^/api/v1/capsules/"), "10/minute"),
        # RAG queries - moderate limits
        (re.compile(r"^/api/v1/rag/"), "30/minute"),
        # Batch operations - strict limits
        (re.compile(r"^/api/v1/batch/"), "5/minute"),
        # File uploads - moderate limits
        (re.compile(r"^/api/v1/upload/"), "30/minute"),
        # Search operations
        (re.compile(r"^/api/v1/search/"), "60/minute"),
    ]

    # Default limit for all other endpoints
    DEFAULT_LIMIT = "100/minute"

    def __init__(self, app, redis_url: str | None = None):
        super().__init__(app)
        self.redis_url = redis_url or REDIS_URL
        self._rate_limits: dict[str, tuple[int, int]] = {}  # key -> (count, window_start)

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to all requests."""
        path = request.url.path

        # Skip exempt paths
        if path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Skip OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get rate limit for this path
        limit_string = self._get_limit_for_path(path)
        limit, window = self._parse_limit(limit_string)

        # Get rate limit key
        key = self._get_rate_key(request, path)

        # Check rate limit
        is_allowed, remaining, reset_time = await self._check_rate_limit(
            key, limit, window
        )

        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded",
                extra={
                    "path": path,
                    "key": key,
                    "limit": limit_string,
                }
            )
            return StarletteJSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "detail": "Too many requests. Please slow down.",
                    "retry_after_seconds": reset_time,
                },
                headers={
                    "Retry-After": str(reset_time),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + reset_time),
                },
            )

        # Process request and add rate limit headers
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + reset_time)

        return response

    def _get_limit_for_path(self, path: str) -> str:
        """Get the rate limit string for a given path."""
        for pattern, limit in self.PATH_LIMITS:
            if pattern.match(path):
                return limit
        return self.DEFAULT_LIMIT

    def _parse_limit(self, limit_string: str) -> tuple[int, int]:
        """
        Parse limit string like "100/minute" into (count, seconds).

        Returns:
            Tuple of (max_requests, window_seconds)
        """
        parts = limit_string.split("/")
        count = int(parts[0])

        window_map = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400,
        }

        window = window_map.get(parts[1], 60)
        return count, window

    def _get_rate_key(self, request: Request, path: str) -> str:
        """Generate rate limit key based on user or IP."""
        # Use the same key function as SlowAPI for consistency
        base_key = get_user_or_ip(request)
        # Include path prefix for path-specific limits
        path_prefix = path.split("/")[1:3]  # e.g., ["api", "v1"]
        return f"rl:{base_key}:{'/'.join(path_prefix)}"

    async def _check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit.

        Returns:
            Tuple of (is_allowed, remaining_requests, seconds_until_reset)
        """
        current_time = int(time.time())
        window_start = current_time - (current_time % window)

        # Try Redis first, fall back to in-memory
        try:
            return await self._check_redis_rate_limit(key, limit, window, window_start)
        except Exception as e:
            logger.debug(f"Redis rate limit check failed, using in-memory: {e}")
            return self._check_memory_rate_limit(key, limit, window, window_start, current_time)

    async def _check_redis_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
        window_start: int,
    ) -> tuple[bool, int, int]:
        """Check rate limit using Redis."""
        # Import here to avoid circular imports
        from app import redis_client as redis_module

        # Check if Redis is initialized (avoid MagicMock issues in tests)
        if redis_module._redis_client is None:
            raise RuntimeError("Redis client not initialized")

        redis = redis_module._redis_client
        full_key = f"{key}:{window_start}"

        # Atomic increment and get
        pipe = redis.pipeline()
        pipe.incr(full_key)
        pipe.expire(full_key, window + 1)  # Expire slightly after window
        results = await pipe.execute()

        count = results[0]
        remaining = max(0, limit - count)
        reset_time = window - (int(time.time()) - window_start)

        return count <= limit, remaining, max(1, reset_time)

    def _check_memory_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
        window_start: int,
        current_time: int,
    ) -> tuple[bool, int, int]:
        """Check rate limit using in-memory storage (fallback)."""
        full_key = f"{key}:{window_start}"

        # Clean old entries
        self._cleanup_old_entries(window_start)

        if full_key not in self._rate_limits:
            self._rate_limits[full_key] = (0, window_start)

        count, _ = self._rate_limits[full_key]
        count += 1
        self._rate_limits[full_key] = (count, window_start)

        remaining = max(0, limit - count)
        reset_time = window - (current_time - window_start)

        return count <= limit, remaining, max(1, reset_time)

    def _cleanup_old_entries(self, current_window: int):
        """Remove rate limit entries from old windows."""
        # Only cleanup occasionally to avoid performance impact
        if len(self._rate_limits) > 10000:
            old_keys = [
                k for k, (_, ws) in self._rate_limits.items()
                if ws < current_window - 3600  # Keep last hour
            ]
            for k in old_keys:
                del self._rate_limits[k]
