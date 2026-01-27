"""
HTTP Client Utilities

Provides secure HTTP client with:
- Timeout handling
- Size limits
- Content-type validation
- Async support
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Optional, Tuple

import httpx

logger = logging.getLogger(__name__)


# =============================================================================
# Exceptions
# =============================================================================


class DownloadTooLargeError(Exception):
    """Raised when download exceeds size limit."""
    pass


class InvalidContentTypeError(Exception):
    """Raised when content type is not allowed."""
    pass


# =============================================================================
# Async Client Builder
# =============================================================================


@asynccontextmanager
async def build_async_client(
    timeout: float = 30.0,
    follow_redirects: bool = True,
    headers: Optional[dict] = None,
):
    """
    Build an async HTTP client with sensible defaults.

    Args:
        timeout: Request timeout in seconds
        follow_redirects: Whether to follow redirects
        headers: Optional headers to include

    Yields:
        httpx.AsyncClient
    """
    client = httpx.AsyncClient(
        timeout=httpx.Timeout(timeout),
        follow_redirects=follow_redirects,
        headers=headers or {},
    )
    try:
        yield client
    finally:
        await client.aclose()


# =============================================================================
# Fetch with Limits
# =============================================================================


async def fetch_bytes_limited(
    client: httpx.AsyncClient,
    url: str,
    max_bytes: int = 100 * 1024 * 1024,  # 100MB default
    allowed_content_types: Tuple[str, ...] = ("*/*",),
) -> bytes:
    """
    Fetch URL content with size and content-type limits.

    Args:
        client: httpx.AsyncClient instance
        url: URL to fetch
        max_bytes: Maximum allowed download size
        allowed_content_types: Allowed content types (wildcards supported)

    Returns:
        Downloaded bytes

    Raises:
        DownloadTooLargeError: If content exceeds max_bytes
        InvalidContentTypeError: If content type not allowed
    """
    # First, do a HEAD request to check size and content-type
    try:
        head_response = await client.head(url)
        head_response.raise_for_status()

        # Check content-length if available
        content_length = head_response.headers.get("content-length")
        if content_length:
            size = int(content_length)
            if size > max_bytes:
                raise DownloadTooLargeError(
                    f"Content-Length {size} exceeds max {max_bytes}"
                )

        # Check content-type
        content_type = head_response.headers.get("content-type", "")
        if not _is_content_type_allowed(content_type, allowed_content_types):
            raise InvalidContentTypeError(
                f"Content-Type '{content_type}' not in allowed: {allowed_content_types}"
            )

    except httpx.HTTPError as e:
        # HEAD failed, proceed with GET and check during download
        logger.debug(f"HEAD request failed, proceeding with GET: {e}")

    # Stream download with size check
    chunks = []
    total_size = 0

    async with client.stream("GET", url) as response:
        response.raise_for_status()

        # Check content-type again
        content_type = response.headers.get("content-type", "")
        if not _is_content_type_allowed(content_type, allowed_content_types):
            raise InvalidContentTypeError(
                f"Content-Type '{content_type}' not in allowed: {allowed_content_types}"
            )

        async for chunk in response.aiter_bytes():
            total_size += len(chunk)
            if total_size > max_bytes:
                raise DownloadTooLargeError(
                    f"Download size {total_size} exceeds max {max_bytes}"
                )
            chunks.append(chunk)

    return b"".join(chunks)


def _is_content_type_allowed(
    content_type: str,
    allowed: Tuple[str, ...],
) -> bool:
    """
    Check if content type matches allowed list.

    Supports wildcards like "video/*" and "*/*".
    """
    if "*/*" in allowed:
        return True

    content_type_lower = content_type.lower().split(";")[0].strip()

    for pattern in allowed:
        pattern_lower = pattern.lower()

        if pattern_lower == content_type_lower:
            return True

        # Handle wildcards like "video/*"
        if pattern_lower.endswith("/*"):
            prefix = pattern_lower[:-1]  # "video/"
            if content_type_lower.startswith(prefix):
                return True

    return False


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "build_async_client",
    "fetch_bytes_limited",
    "DownloadTooLargeError",
    "InvalidContentTypeError",
]
