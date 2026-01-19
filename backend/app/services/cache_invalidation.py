"""
Cache Invalidation Service for Next.js Frontend

Phase 6: Next.js 16 Cache Components

This service provides methods to invalidate cached data in the Next.js frontend
when content changes in the backend (e.g., IP updates, new presets, etc.)

Usage:
    from app.services.cache_invalidation import get_cache_invalidation

    cache_service = get_cache_invalidation()
    await cache_service.invalidate_ip("my-ip-slug")
    await cache_service.invalidate_ip_catalog()
"""

import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Cache Tag Constants (mirrors frontend/src/lib/cache-tags.ts)
# =============================================================================

class CacheTags:
    """Cache tag constants matching frontend definitions."""

    # IP-related tags
    IP_RAILS = "ip-rails"
    IP_GENRES = "ip-genres"
    IP_CATALOG = "ip-catalog"
    IP_POPULAR = "ip-popular"

    @staticmethod
    def ip_detail(slug: str) -> str:
        """Get tag for IP detail page."""
        return f"ip:{slug}"

    @staticmethod
    def ip_presets(slug: str) -> str:
        """Get tag for IP presets."""
        return f"ip:{slug}:presets"

    @staticmethod
    def ip_recommendations(slug: str) -> str:
        """Get tag for IP recommendations."""
        return f"ip:{slug}:recommendations"

    @staticmethod
    def ip_rights(slug: str) -> str:
        """Get tag for IP rights."""
        return f"ip:{slug}:rights"

    @staticmethod
    def user_profile(user_id: str) -> str:
        """Get tag for user profile."""
        return f"user:{user_id}"

    @staticmethod
    def user_history(user_id: str) -> str:
        """Get tag for user history."""
        return f"user:{user_id}:history"


# =============================================================================
# Cache Invalidation Service
# =============================================================================

class CacheInvalidationService:
    """
    Service to invalidate Next.js frontend cache.

    Calls the /api/revalidate endpoint on the frontend to trigger
    cache invalidation for specific tags or paths.
    """

    def __init__(self):
        self.frontend_url = settings.FRONTEND_URL
        self.secret = settings.REVALIDATE_SECRET
        self._enabled = bool(self.secret)

        if not self._enabled:
            logger.warning(
                "Cache invalidation disabled: REVALIDATE_SECRET not configured"
            )

    @property
    def enabled(self) -> bool:
        """Check if cache invalidation is enabled."""
        return self._enabled

    async def invalidate_tags(self, tags: list[str]) -> bool:
        """
        Invalidate cache by tags.

        Args:
            tags: List of cache tags to invalidate

        Returns:
            True if successful, False otherwise
        """
        if not self._enabled:
            logger.debug("Cache invalidation skipped (disabled)")
            return True

        if not tags:
            return True

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.frontend_url}/api/revalidate",
                    json={"tags": tags},
                    headers={"Authorization": f"Bearer {self.secret}"},
                    timeout=5.0,
                )
                response.raise_for_status()

                result = response.json()
                logger.info(
                    f"Cache invalidated: {result.get('revalidated', [])}"
                )
                return True

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"Cache invalidation failed (HTTP {e.response.status_code}): {e}"
            )
            return False
        except httpx.TimeoutException:
            logger.warning("Cache invalidation timed out")
            return False
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")
            return False

    async def invalidate_paths(self, paths: list[str]) -> bool:
        """
        Invalidate cache by paths.

        Args:
            paths: List of page paths to invalidate (e.g., ["/ip", "/ip/my-slug"])

        Returns:
            True if successful, False otherwise
        """
        if not self._enabled:
            logger.debug("Cache invalidation skipped (disabled)")
            return True

        if not paths:
            return True

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.frontend_url}/api/revalidate",
                    json={"paths": paths},
                    headers={"Authorization": f"Bearer {self.secret}"},
                    timeout=5.0,
                )
                response.raise_for_status()

                result = response.json()
                logger.info(
                    f"Paths invalidated: {result.get('revalidated', [])}"
                )
                return True

        except Exception as e:
            logger.warning(f"Path invalidation failed: {e}")
            return False

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    async def invalidate_ip(self, slug: str) -> bool:
        """
        Invalidate all cache related to a specific IP.

        Args:
            slug: IP slug to invalidate

        Returns:
            True if successful, False otherwise
        """
        tags = [
            CacheTags.ip_detail(slug),
            CacheTags.ip_presets(slug),
            CacheTags.ip_recommendations(slug),
            CacheTags.ip_rights(slug),
        ]
        return await self.invalidate_tags(tags)

    async def invalidate_ip_catalog(self) -> bool:
        """
        Invalidate the entire IP catalog cache.

        Call this when:
        - New IP is added
        - IP is deleted
        - IP metadata changes that affects listing

        Returns:
            True if successful, False otherwise
        """
        tags = [
            CacheTags.IP_RAILS,
            CacheTags.IP_CATALOG,
            CacheTags.IP_POPULAR,
        ]
        return await self.invalidate_tags(tags)

    async def invalidate_genres(self) -> bool:
        """
        Invalidate the genres cache.

        Call this when genre list changes.

        Returns:
            True if successful, False otherwise
        """
        return await self.invalidate_tags([CacheTags.IP_GENRES])

    async def invalidate_user(self, user_id: str) -> bool:
        """
        Invalidate user-specific cache.

        Args:
            user_id: User ID to invalidate

        Returns:
            True if successful, False otherwise
        """
        tags = [
            CacheTags.user_profile(user_id),
            CacheTags.user_history(user_id),
        ]
        return await self.invalidate_tags(tags)

    async def invalidate_all_ips(self) -> bool:
        """
        Invalidate all IP-related cache (nuclear option).

        Use sparingly - this clears all IP cache.

        Returns:
            True if successful, False otherwise
        """
        tags = [
            CacheTags.IP_RAILS,
            CacheTags.IP_GENRES,
            CacheTags.IP_CATALOG,
            CacheTags.IP_POPULAR,
        ]
        # Also invalidate the /ip path
        await self.invalidate_paths(["/ip"])
        return await self.invalidate_tags(tags)


# =============================================================================
# Singleton
# =============================================================================

_cache_invalidation: Optional[CacheInvalidationService] = None


def get_cache_invalidation() -> CacheInvalidationService:
    """
    Get the cache invalidation service singleton.

    Returns:
        CacheInvalidationService instance
    """
    global _cache_invalidation
    if _cache_invalidation is None:
        _cache_invalidation = CacheInvalidationService()
    return _cache_invalidation
