"""
Security Middleware (2026 OWASP Best Practices)
===============================================

Comprehensive security hardening following OWASP Top 10 2024/2025:
- Security Headers (CSP, HSTS, X-Frame-Options, etc.)
- Request ID tracking
- IP extraction from various headers
- Suspicious activity detection
- Input size limits

References:
- OWASP API Security Top 10 (2023)
- Tavily Research: FastAPI Security 2026
- https://cheatsheetseries.owasp.org/
"""

import time
import hashlib
import logging
from typing import Optional, Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses following 2026 OWASP best practices.

    Headers added:
    - Strict-Transport-Security (HSTS)
    - X-Content-Type-Options
    - X-Frame-Options
    - Content-Security-Policy
    - X-XSS-Protection (legacy browsers)
    - Referrer-Policy
    - Permissions-Policy
    - Cache-Control (for sensitive endpoints)
    """

    def __init__(
        self,
        app: ASGIApp,
        csp_policy: Optional[str] = None,
        hsts_max_age: int = 31536000,  # 1 year
        include_subdomains: bool = True,
        frame_options: str = "DENY",
        referrer_policy: str = "strict-origin-when-cross-origin",
        enable_xss_protection: bool = True,
    ):
        super().__init__(app)
        self.hsts_max_age = hsts_max_age
        self.include_subdomains = include_subdomains
        self.frame_options = frame_options
        self.referrer_policy = referrer_policy
        self.enable_xss_protection = enable_xss_protection

        # Default CSP - restrictive but allows API functionality
        self.csp_policy = csp_policy or self._default_csp_policy()

    def _default_csp_policy(self) -> str:
        """Generate default Content Security Policy."""
        policies = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://vercel.live",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "img-src 'self' data: https:",
            "font-src 'self' https://fonts.gstatic.com",
            "connect-src 'self' https://vercel.live wss://vercel.live",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
            "upgrade-insecure-requests",
        ]
        return "; ".join(policies)

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # HSTS - HTTP Strict Transport Security
        hsts_value = f"max-age={self.hsts_max_age}"
        if self.include_subdomains:
            hsts_value += "; includeSubDomains"
        response.headers["Strict-Transport-Security"] = hsts_value

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = self.frame_options

        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp_policy

        # XSS Protection (for legacy browsers)
        if self.enable_xss_protection:
            response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        response.headers["Referrer-Policy"] = self.referrer_policy

        # Permissions Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=()"
        )

        # Prevent caching of sensitive API responses
        if self._is_sensitive_endpoint(request.url.path):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response

    def _is_sensitive_endpoint(self, path: str) -> bool:
        """Check if endpoint handles sensitive data."""
        sensitive_patterns = [
            "/auth/",
            "/credits/",
            "/payment/",
            "/user/",
            "/admin/",
            "/internal/",
        ]
        return any(pattern in path for pattern in sensitive_patterns)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add unique request ID to all requests for tracing.

    Request ID is available in:
    - X-Request-ID response header
    - request.state.request_id
    - Logs (via logging context)
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next) -> Response:
        # Use existing request ID if provided, otherwise generate new one
        request_id = request.headers.get(self.header_name)
        if not request_id:
            request_id = str(uuid4())

        # Store in request state for access in handlers
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers[self.header_name] = request_id

        return response


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """
    Track request processing time for performance monitoring.

    Adds headers:
    - X-Process-Time: Processing time in seconds
    """

    def __init__(
        self,
        app: ASGIApp,
        slow_request_threshold_ms: float = 1000,
    ):
        super().__init__(app)
        self.slow_threshold = slow_request_threshold_ms

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()

        response = await call_next(request)

        process_time = (time.perf_counter() - start_time) * 1000  # ms
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        # Log slow requests
        if process_time > self.slow_threshold:
            logger.warning(
                f"Slow request detected",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "process_time_ms": process_time,
                    "client_ip": get_client_ip(request),
                }
            )

        return response


class SuspiciousActivityMiddleware(BaseHTTPMiddleware):
    """
    Detect and log suspicious activity patterns.

    Detects:
    - Path traversal attempts (../)
    - SQL injection patterns
    - XSS patterns in query params
    - Unusual User-Agent patterns
    - Excessive request sizes
    """

    SUSPICIOUS_PATTERNS = [
        "../",           # Path traversal
        "..\\",          # Windows path traversal
        "<script",       # XSS
        "javascript:",   # XSS
        "onerror=",      # XSS event handler
        "onload=",       # XSS event handler
        "union select",  # SQL injection
        "' or '1'='1",   # SQL injection
        "; drop table",  # SQL injection
        "eval(",         # Code injection
        "exec(",         # Code injection
    ]

    SUSPICIOUS_USER_AGENTS = [
        "sqlmap",
        "nikto",
        "nessus",
        "burpsuite",
        "acunetix",
        "netsparker",
    ]

    def __init__(
        self,
        app: ASGIApp,
        max_body_size: int = 10 * 1024 * 1024,  # 10MB
        log_suspicious: bool = True,
        block_suspicious: bool = False,  # Set True for strict mode
    ):
        super().__init__(app)
        self.max_body_size = max_body_size
        self.log_suspicious = log_suspicious
        self.block_suspicious = block_suspicious

    async def dispatch(self, request: Request, call_next) -> Response:
        # Check for suspicious patterns
        suspicions = []

        # Check URL path
        path = request.url.path.lower()
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern in path:
                suspicions.append(f"path_pattern:{pattern}")

        # Check query params
        query = str(request.url.query).lower()
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern in query:
                suspicions.append(f"query_pattern:{pattern}")

        # Check User-Agent
        user_agent = (request.headers.get("user-agent") or "").lower()
        for agent in self.SUSPICIOUS_USER_AGENTS:
            if agent in user_agent:
                suspicions.append(f"suspicious_agent:{agent}")

        # Check Content-Length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_body_size:
            suspicions.append(f"oversized_body:{content_length}")

        # Log and potentially block
        if suspicions:
            client_ip = get_client_ip(request)

            if self.log_suspicious:
                logger.warning(
                    "Suspicious activity detected",
                    extra={
                        "suspicions": suspicions,
                        "path": request.url.path,
                        "method": request.method,
                        "client_ip": client_ip,
                        "user_agent": user_agent[:100],
                    }
                )

            if self.block_suspicious:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Bad Request"},
                )

        return await call_next(request)


def get_client_ip(request: Request) -> str:
    """
    Extract real client IP from request.

    Checks headers in order:
    1. CF-Connecting-IP (Cloudflare)
    2. X-Real-IP (Nginx)
    3. X-Forwarded-For (first IP)
    4. client.host (direct connection)
    """
    # Cloudflare
    if cf_ip := request.headers.get("CF-Connecting-IP"):
        return cf_ip

    # Nginx / standard proxy
    if real_ip := request.headers.get("X-Real-IP"):
        return real_ip

    # X-Forwarded-For chain (take first = original client)
    if forwarded := request.headers.get("X-Forwarded-For"):
        return forwarded.split(",")[0].strip()

    # Direct connection
    if request.client:
        return request.client.host

    return "unknown"


def get_request_fingerprint(request: Request) -> str:
    """
    Generate a fingerprint for the request for rate limiting/tracking.

    Combines: IP + User-Agent + Accept-Language
    """
    ip = get_client_ip(request)
    ua = request.headers.get("user-agent", "")
    lang = request.headers.get("accept-language", "")

    combined = f"{ip}:{ua}:{lang}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def setup_security_middleware(
    app,
    enable_security_headers: bool = True,
    enable_request_id: bool = True,
    enable_timing: bool = True,
    enable_suspicious_detection: bool = True,
    csp_policy: Optional[str] = None,
) -> None:
    """
    Setup all security middleware on FastAPI app.

    Usage in main.py:
        from app.middleware.security import setup_security_middleware
        setup_security_middleware(app)

    Args:
        app: FastAPI application
        enable_security_headers: Add OWASP security headers
        enable_request_id: Add request ID tracking
        enable_timing: Add request timing headers
        enable_suspicious_detection: Detect suspicious patterns
        csp_policy: Custom Content-Security-Policy
    """
    # Note: Middleware order matters - last added = first executed

    if enable_suspicious_detection:
        app.add_middleware(SuspiciousActivityMiddleware)
        logger.info("Suspicious activity detection enabled")

    if enable_timing:
        app.add_middleware(RequestTimingMiddleware)
        logger.info("Request timing middleware enabled")

    if enable_request_id:
        app.add_middleware(RequestIDMiddleware)
        logger.info("Request ID middleware enabled")

    if enable_security_headers:
        app.add_middleware(SecurityHeadersMiddleware, csp_policy=csp_policy)
        logger.info("Security headers middleware enabled")

    logger.info("Security middleware setup complete")
