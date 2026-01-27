"""
CSRF (Cross-Site Request Forgery) Protection Middleware
========================================================

Provides CSRF protection for cookie-based authentication sessions.

OWASP A01:2021 - Broken Access Control
OWASP recommends Double Submit Cookie pattern for SPA + API architectures.

Design:
- API Key authentication: CSRF check SKIPPED (stateless, no cookies)
- Cookie session authentication: CSRF check REQUIRED
- Webhooks and internal routes: EXEMPT (verified by signature/mTLS)

Pattern: Double Submit Cookie
1. Server sets HttpOnly csrf_token cookie
2. Client sends same token in X-CSRF-Token header
3. Middleware validates cookie == header

Note: This middleware is for cookie-based web sessions only.
API key authentication is inherently CSRF-safe.
"""
from __future__ import annotations

import logging
import secrets
from typing import FrozenSet

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection for cookie-based sessions.

    Configuration:
    - CSRF_COOKIE_NAME: Name of the CSRF cookie (default: csrf_token)
    - CSRF_HEADER_NAME: Name of the CSRF header (default: X-CSRF-Token)
    - EXEMPT_PATHS: Paths that bypass CSRF check (webhooks, internal APIs)
    - SAFE_METHODS: HTTP methods that don't require CSRF (GET, HEAD, OPTIONS)
    """

    CSRF_COOKIE_NAME = "csrf_token"
    CSRF_HEADER_NAME = "X-CSRF-Token"
    SESSION_COOKIE_NAME = "crebit_session"

    # HTTP methods that don't modify state (safe methods)
    SAFE_METHODS: FrozenSet[str] = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})

    # Paths exempt from CSRF protection
    # - Webhooks: Use signature verification (Stripe, GitHub)
    # - Internal S2S: Uses mTLS authentication
    # - Health checks: No state modification
    EXEMPT_PATHS: FrozenSet[str] = frozenset({
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

    # Path prefixes exempt from CSRF
    # These use alternative authentication mechanisms
    EXEMPT_PATH_PREFIXES = (
        "/api/v1/stripe/webhook",     # Stripe webhook (signature verification)
        "/api/v1/internal/",          # S2S internal APIs (mTLS)
        "/api/v1/payment/webhook",    # Payment webhooks (signature)
        "/graphql",                   # GraphQL (uses API key or separate auth)
    )

    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Check CSRF token for cookie-authenticated requests.

        Flow:
        1. Skip if disabled or safe method
        2. Skip if exempt path
        3. Skip if API key authentication (no cookies)
        4. Require CSRF token for cookie sessions
        """
        if not self.enabled:
            return await call_next(request)

        # Safe methods don't need CSRF protection
        if request.method in self.SAFE_METHODS:
            return await call_next(request)

        path = request.url.path

        # Check exempt paths
        if path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Check exempt path prefixes
        for prefix in self.EXEMPT_PATH_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        # API Key authentication bypasses CSRF (stateless)
        if request.headers.get("X-API-Key"):
            return await call_next(request)

        # Authorization header (Bearer token) also bypasses CSRF
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return await call_next(request)

        # Check for cookie-based session
        session_cookie = request.cookies.get(self.SESSION_COOKIE_NAME)
        if not session_cookie:
            # No session cookie = not using cookie auth, proceed
            return await call_next(request)

        # Cookie session exists - CSRF validation required
        csrf_cookie = request.cookies.get(self.CSRF_COOKIE_NAME)
        csrf_header = request.headers.get(self.CSRF_HEADER_NAME)

        # Both must be present and match
        if not csrf_cookie or not csrf_header:
            logger.warning(
                f"CSRF token missing",
                extra={
                    "path": path,
                    "method": request.method,
                    "has_cookie": bool(csrf_cookie),
                    "has_header": bool(csrf_header),
                    "client_ip": self._get_client_ip(request),
                }
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "csrf_validation_failed",
                    "detail": "CSRF token is required for this request",
                    "hint": "Include the csrf_token cookie value in the X-CSRF-Token header",
                },
            )

        # Constant-time comparison to prevent timing attacks
        if not secrets.compare_digest(csrf_cookie, csrf_header):
            logger.warning(
                f"CSRF token mismatch",
                extra={
                    "path": path,
                    "method": request.method,
                    "client_ip": self._get_client_ip(request),
                }
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "csrf_validation_failed",
                    "detail": "CSRF token validation failed",
                },
            )

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        if cf_ip := request.headers.get("CF-Connecting-IP"):
            return cf_ip
        if real_ip := request.headers.get("X-Real-IP"):
            return real_ip
        if forwarded := request.headers.get("X-Forwarded-For"):
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"


def generate_csrf_token() -> str:
    """
    Generate a secure CSRF token.

    Returns:
        32-byte URL-safe token
    """
    return secrets.token_urlsafe(32)


# =============================================================================
# Exports
# =============================================================================

__all__ = ["CSRFMiddleware", "generate_csrf_token"]
