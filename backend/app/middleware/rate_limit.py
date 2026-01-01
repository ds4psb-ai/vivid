"""
Rate Limiting Middleware
========================
Implements API rate limiting using SlowAPI with Redis backend for distributed limiting.

Limits:
- Default: 100 requests/minute per IP
- Auth endpoints: 10 requests/minute per IP (stricter for login attempts)
- Capsule execution: 20 requests/minute per user (resource-intensive)
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import Response
import os

# Use Redis if available, otherwise in-memory
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

def get_user_or_ip(request: Request) -> str:
    """Get user ID from session cookie or fall back to IP address."""
    # Try to get user from session (if authenticated)
    user_id = request.headers.get("X-User-Id")
    if user_id:
        return f"user:{user_id}"
    # Fall back to IP address
    return get_remote_address(request)


# Create limiter with Redis storage for distributed rate limiting
# Falls back to in-memory if Redis is not available
try:
    limiter = Limiter(
        key_func=get_user_or_ip,
        storage_uri=REDIS_URL,
        default_limits=["100/minute"],  # Default limit for all endpoints
    )
except Exception:
    # Fallback to in-memory storage
    limiter = Limiter(
        key_func=get_user_or_ip,
        default_limits=["100/minute"],
    )


def setup_rate_limiting(app):
    """
    Configure rate limiting for the FastAPI application.
    
    Usage in main.py:
        from app.middleware.rate_limit import setup_rate_limiting
        setup_rate_limiting(app)
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Decorator shortcuts for common rate limits
# Usage in routers:
#   from app.middleware.rate_limit import limiter
#
#   @router.post("/login")
#   @limiter.limit("10/minute")  # Stricter for auth
#   async def login(request: Request):
#       ...
#
#   @router.post("/execute")
#   @limiter.limit("20/minute")  # For resource-intensive operations
#   async def execute(request: Request):
#       ...

# Rate limit constants for consistency
RATE_LIMIT_DEFAULT = "100/minute"
RATE_LIMIT_AUTH = "10/minute"       # Login, register attempts
RATE_LIMIT_EXECUTE = "20/minute"    # Capsule runs, generation
RATE_LIMIT_UPLOAD = "30/minute"     # File uploads
RATE_LIMIT_SEARCH = "60/minute"     # Search/filter operations
