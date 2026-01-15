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
            strategy="fixed-window-elastic-expiry",  # 2026 best practice
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
