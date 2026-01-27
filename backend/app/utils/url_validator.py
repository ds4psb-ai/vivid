"""
SSRF (Server-Side Request Forgery) Protection
==============================================

Validates URLs to prevent SSRF attacks by blocking:
- Internal/private IP addresses
- Cloud metadata endpoints
- Localhost and loopback addresses
- Private network ranges (RFC 1918)

OWASP A10:2021 - Server-Side Request Forgery
"""
from __future__ import annotations

import ipaddress
import logging
import socket
from typing import Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# =============================================================================
# Blocked Hosts and Networks
# =============================================================================

# Cloud metadata endpoints (AWS, GCP, Azure)
BLOCKED_HOSTS = frozenset({
    # Localhost
    "localhost",
    "127.0.0.1",
    "::1",
    "[::1]",
    # AWS metadata
    "169.254.169.254",
    "metadata.aws.internal",
    # GCP metadata
    "metadata.google.internal",
    "metadata.goog",
    # Azure metadata
    "169.254.169.254",
    "metadata.azure.com",
    # Kubernetes
    "kubernetes.default",
    "kubernetes.default.svc",
    "kubernetes.default.svc.cluster.local",
    # Docker
    "host.docker.internal",
    "gateway.docker.internal",
})

# Private network ranges (RFC 1918 + Link-local + Loopback)
BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),       # Private Class A
    ipaddress.ip_network("172.16.0.0/12"),    # Private Class B
    ipaddress.ip_network("192.168.0.0/16"),   # Private Class C
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local (AWS metadata)
    ipaddress.ip_network("0.0.0.0/8"),        # "This" network
    ipaddress.ip_network("100.64.0.0/10"),    # Shared Address Space (CGN)
    ipaddress.ip_network("192.0.0.0/24"),     # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),     # TEST-NET-1
    ipaddress.ip_network("198.51.100.0/24"),  # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),   # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),      # Multicast
    ipaddress.ip_network("240.0.0.0/4"),      # Reserved
    # IPv6
    ipaddress.ip_network("::1/128"),          # Loopback
    ipaddress.ip_network("fc00::/7"),         # Unique Local
    ipaddress.ip_network("fe80::/10"),        # Link-local
    ipaddress.ip_network("ff00::/8"),         # Multicast
]

# Allowed URL schemes
ALLOWED_SCHEMES = frozenset({"http", "https"})


# =============================================================================
# SSRF Exceptions
# =============================================================================

class SSRFError(Exception):
    """Raised when SSRF attack is detected."""
    pass


class SSRFBlockedHostError(SSRFError):
    """Raised when host is in blocked list."""
    pass


class SSRFPrivateIPError(SSRFError):
    """Raised when resolved IP is private."""
    pass


class SSRFInvalidSchemeError(SSRFError):
    """Raised when URL scheme is not allowed."""
    pass


class SSRFDNSResolutionError(SSRFError):
    """Raised when DNS resolution fails."""
    pass


# =============================================================================
# URL Validation Functions
# =============================================================================

def validate_url_for_ssrf(url: str, resolve_dns: bool = True) -> Tuple[bool, str]:
    """
    Validate URL to prevent SSRF attacks.

    Args:
        url: URL to validate
        resolve_dns: Whether to resolve DNS and check IP (default: True)

    Returns:
        Tuple of (is_safe, error_message)

    Raises:
        SSRFError: If URL is potentially dangerous

    Usage:
        is_safe, error = validate_url_for_ssrf(user_provided_url)
        if not is_safe:
            raise HTTPException(400, error)
    """
    try:
        # Parse URL
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme not in ALLOWED_SCHEMES:
            error = f"Invalid URL scheme: {parsed.scheme}. Only http/https allowed."
            logger.warning(f"SSRF blocked - invalid scheme: {url}")
            raise SSRFInvalidSchemeError(error)

        # Extract hostname
        hostname = parsed.hostname
        if not hostname:
            error = "Invalid URL: no hostname found"
            logger.warning(f"SSRF blocked - no hostname: {url}")
            raise SSRFError(error)

        # Normalize hostname
        hostname_lower = hostname.lower()

        # Check against blocked hosts
        if hostname_lower in BLOCKED_HOSTS:
            error = f"Blocked host: {hostname}"
            logger.warning(f"SSRF blocked - blocked host: {url}")
            raise SSRFBlockedHostError(error)

        # Check for suspicious patterns
        if _is_suspicious_hostname(hostname_lower):
            error = f"Suspicious hostname pattern: {hostname}"
            logger.warning(f"SSRF blocked - suspicious pattern: {url}")
            raise SSRFBlockedHostError(error)

        # Resolve DNS and check IP
        if resolve_dns:
            is_safe, ip_error = _validate_resolved_ip(hostname)
            if not is_safe:
                logger.warning(f"SSRF blocked - private IP: {url} -> {ip_error}")
                raise SSRFPrivateIPError(ip_error)

        return True, ""

    except SSRFError:
        raise
    except Exception as e:
        error = f"URL validation failed: {str(e)}"
        logger.error(f"SSRF validation error: {url} - {e}")
        raise SSRFError(error)


def _is_suspicious_hostname(hostname: str) -> bool:
    """
    Check for suspicious hostname patterns that might bypass validation.

    Detects:
    - Decimal IP encoding (e.g., 2130706433 = 127.0.0.1)
    - Hex IP encoding (e.g., 0x7f.0x0.0x0.0x1)
    - Octal IP encoding (e.g., 0177.0.0.01)
    - URL-encoded chars
    - Unicode tricks
    """
    # Decimal IP (single number that could be an IP)
    if hostname.isdigit():
        try:
            num = int(hostname)
            # Convert decimal to IP and check
            if 0 <= num <= 4294967295:  # Valid IPv4 range
                ip_str = str(ipaddress.IPv4Address(num))
                return _is_private_ip(ip_str)
        except (ValueError, ipaddress.AddressValueError):
            pass

    # Hex/Octal encoded
    if hostname.startswith("0x") or hostname.startswith("0"):
        return True

    # URL-encoded localhost patterns
    suspicious_patterns = [
        "localtest.me",
        "lvh.me",
        "vcap.me",
        ".internal",
        ".local",
        ".localhost",
        "spoofed.",
        "xip.io",
        "nip.io",
        "sslip.io",
    ]

    for pattern in suspicious_patterns:
        if pattern in hostname:
            return True

    return False


def _validate_resolved_ip(hostname: str) -> Tuple[bool, str]:
    """
    Resolve hostname and validate the IP address is not private.

    Args:
        hostname: Hostname to resolve

    Returns:
        Tuple of (is_safe, error_message)
    """
    try:
        # Get all IP addresses for hostname
        _, _, ip_list = socket.gethostbyname_ex(hostname)

        for ip_str in ip_list:
            if _is_private_ip(ip_str):
                return False, f"Hostname {hostname} resolves to private IP: {ip_str}"

        return True, ""

    except socket.gaierror as e:
        # DNS resolution failed - could be intentional attack
        return False, f"DNS resolution failed for {hostname}: {e}"
    except socket.herror as e:
        return False, f"Host error for {hostname}: {e}"
    except socket.timeout:
        return False, f"DNS resolution timeout for {hostname}"


def _is_private_ip(ip_str: str) -> bool:
    """
    Check if IP address is in private/blocked ranges.

    Args:
        ip_str: IP address string

    Returns:
        True if IP is private/blocked
    """
    try:
        ip = ipaddress.ip_address(ip_str)

        # Check against blocked networks
        for network in BLOCKED_NETWORKS:
            if ip in network:
                return True

        # Use built-in checks as well
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return True

        return False

    except ValueError:
        # Invalid IP - treat as suspicious
        return True


def is_safe_external_url(url: str) -> bool:
    """
    Simple boolean check for URL safety.

    Args:
        url: URL to check

    Returns:
        True if URL is safe for external requests
    """
    try:
        is_safe, _ = validate_url_for_ssrf(url)
        return is_safe
    except SSRFError:
        return False


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "validate_url_for_ssrf",
    "is_safe_external_url",
    "SSRFError",
    "SSRFBlockedHostError",
    "SSRFPrivateIPError",
    "SSRFInvalidSchemeError",
    "SSRFDNSResolutionError",
    "BLOCKED_HOSTS",
    "BLOCKED_NETWORKS",
]
