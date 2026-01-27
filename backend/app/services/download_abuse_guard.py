"""
Download Abuse Guard (P1 Stub)

Rate limiting and abuse prevention for downloads.

TODO (P2): Implement full abuse detection with Redis.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class GuardState:
    """State returned by guard checks."""
    blocked: bool = False
    host: str = ""
    key_hash: str = ""
    key_type: str = "url"
    cooldown_seconds: int = 0
    count: int = 0
    threshold: int = 10
    window_seconds: int = 3600


class DownloadAbuseGuard:
    """
    Download abuse prevention guard.

    P1 Stub: Always allows downloads.
    P2 TODO: Implement Redis-backed rate limiting.
    """

    async def check_blocked(
        self,
        url: str,
        user_id: Optional[str] = None,
    ) -> GuardState:
        """
        Check if download is blocked.

        P1 Stub: Always returns not blocked.

        Args:
            url: URL to check
            user_id: User ID if available

        Returns:
            GuardState with blocked=False
        """
        host = urlparse(url).netloc if url else ""
        return GuardState(
            blocked=False,
            host=host,
        )

    async def record_oversize(
        self,
        url: str,
        user_id: Optional[str] = None,
    ) -> GuardState:
        """
        Record an oversized download attempt.

        P1 Stub: Just logs and returns state.

        Args:
            url: URL that exceeded size
            user_id: User ID if available

        Returns:
            GuardState
        """
        host = urlparse(url).netloc if url else ""
        logger.warning(f"[ABUSE_GUARD] Oversized download: {host}")
        return GuardState(
            blocked=False,
            host=host,
            count=1,
        )

    async def record_download(
        self,
        url: str,
        user_id: Optional[str] = None,
        size_bytes: int = 0,
    ) -> GuardState:
        """
        Record a successful download.

        P1 Stub: Just returns state.

        Args:
            url: Downloaded URL
            user_id: User ID if available
            size_bytes: Download size

        Returns:
            GuardState
        """
        host = urlparse(url).netloc if url else ""
        return GuardState(
            blocked=False,
            host=host,
        )


# Singleton instance
download_abuse_guard = DownloadAbuseGuard()


__all__ = [
    "DownloadAbuseGuard",
    "GuardState",
    "download_abuse_guard",
]
