"""
P1: Prometheus Metrics Endpoint Protection Middleware

Restricts access to /metrics endpoint based on:
1. IP whitelist (PROMETHEUS_ALLOWED_IPS)
2. Bearer token (PROMETHEUS_BEARER_TOKEN)
3. Internal network check (if PROMETHEUS_ALLOWED_IPS="internal")

In development, metrics are accessible without restriction.
"""

import ipaddress
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger(__name__)

# Internal network ranges (RFC 1918 + localhost)
INTERNAL_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),  # IPv6 localhost
]


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    # Check forwarded headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    if request.client:
        return request.client.host
    return ""


def _is_internal_ip(ip_str: str) -> bool:
    """Check if IP is in internal network ranges."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in network for network in INTERNAL_NETWORKS)
    except ValueError:
        return False


def _is_ip_allowed(ip_str: str) -> bool:
    """Check if IP is allowed to access metrics."""
    allowed_ips = settings.PROMETHEUS_ALLOWED_IPS

    # No restriction configured
    if not allowed_ips:
        return True

    # Internal network check
    if allowed_ips.lower() == "internal":
        return _is_internal_ip(ip_str)

    # IP whitelist
    allowed_set = {ip.strip() for ip in allowed_ips.split(",") if ip.strip()}
    return ip_str in allowed_set


def _is_token_valid(request: Request) -> bool:
    """Check if bearer token is valid."""
    expected_token = settings.PROMETHEUS_BEARER_TOKEN.get_secret_value()
    if not expected_token:
        return False  # No token configured, don't use this method

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False

    provided_token = auth_header[7:]  # Remove "Bearer " prefix
    return provided_token == expected_token


class MetricsProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware to protect /metrics endpoint in production."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only protect metrics endpoint
        if request.url.path != settings.PROMETHEUS_METRICS_PATH:
            return await call_next(request)

        # Skip protection in development
        is_production = settings.ENVIRONMENT.lower() in {"production", "prod", "staging"}
        if not is_production:
            return await call_next(request)

        client_ip = _get_client_ip(request)

        # Check bearer token first (if configured)
        token_configured = bool(settings.PROMETHEUS_BEARER_TOKEN.get_secret_value())
        if token_configured and _is_token_valid(request):
            return await call_next(request)

        # Check IP whitelist
        if _is_ip_allowed(client_ip):
            return await call_next(request)

        # Access denied
        logger.warning(f"Metrics access denied for IP: {client_ip}")
        return Response(
            content="Forbidden",
            status_code=403,
            media_type="text/plain",
        )
