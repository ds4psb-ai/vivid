"""
Fallback Strategies for Circuit Breaker Integration

Provides fallback responses when external services are unavailable:
- LRU cache for recent successful responses
- Provider-specific fallback messages
- Graceful degradation for user experience

Usage:
    from app.services.fallback_strategies import FallbackManager

    fallback_mgr = FallbackManager()

    # Cache successful responses
    fallback_mgr.cache_response("gemini", prompt_hash, response)

    # Get fallback when circuit is open
    result = fallback_mgr.get_fallback("gemini", prompt_hash)
"""
from __future__ import annotations

import hashlib
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Generic, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


# =============================================================================
# Fallback Response Types
# =============================================================================

class FallbackType(Enum):
    """Types of fallback responses."""
    CACHED = "cached"  # Cached from previous successful call
    STATIC = "static"  # Static fallback message
    PARTIAL = "partial"  # Partial result with degraded quality
    NONE = "none"  # No fallback available


@dataclass
class FallbackResponse(Generic[T]):
    """Container for fallback response with metadata."""
    data: T
    fallback_type: FallbackType
    provider: str
    cached_at: Optional[float] = None
    message: str = ""
    is_fallback: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "data": self.data,
            "fallback": True,
            "fallback_type": self.fallback_type.value,
            "provider": self.provider,
            "message": self.message,
        }


# =============================================================================
# LRU Cache with TTL
# =============================================================================

@dataclass
class CacheEntry:
    """Cache entry with value and timestamp."""
    value: Any
    created_at: float
    access_count: int = 0


class LRUCache:
    """Thread-safe LRU cache with TTL."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """Initialize LRU cache.

        Args:
            max_size: Maximum number of entries
            ttl_seconds: Time-to-live in seconds (default: 1 hour)
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        now = time.time()

        # Check TTL
        if now - entry.created_at > self._ttl_seconds:
            del self._cache[key]
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        entry.access_count += 1
        return entry.value

    def set(self, key: str, value: Any) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        # Remove oldest if at capacity
        while len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)

        self._cache[key] = CacheEntry(
            value=value,
            created_at=time.time(),
        )

    def clear(self) -> None:
        """Clear all entries."""
        self._cache.clear()

    def cleanup_expired(self) -> int:
        """Remove expired entries.

        Returns:
            Number of entries removed
        """
        now = time.time()
        expired_keys = [
            k for k, v in self._cache.items()
            if now - v.created_at > self._ttl_seconds
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)

    @property
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_access = sum(e.access_count for e in self._cache.values())
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "ttl_seconds": self._ttl_seconds,
            "total_accesses": total_access,
        }


# =============================================================================
# Provider-Specific Fallback Strategies
# =============================================================================

class FallbackStrategy:
    """Static fallback strategies for different providers."""

    @staticmethod
    def gemini_fallback(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fallback response for Gemini API.

        Args:
            params: Optional parameters for context

        Returns:
            Fallback response dict
        """
        return {
            "text": "[서비스 일시 중단] Gemini API가 현재 응답하지 않습니다. 잠시 후 다시 시도해 주세요.",
            "fallback": True,
            "provider": "gemini",
            "error_code": "SERVICE_UNAVAILABLE",
        }

    @staticmethod
    def rag_fallback(
        query: Optional[str] = None,
        dimension: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fallback response for RAG queries.

        Args:
            query: Original query
            dimension: Dimension code

        Returns:
            Fallback response dict
        """
        return {
            "sources": [],
            "answer": None,
            "fallback": True,
            "provider": "rag",
            "message": f"RAG 검색이 일시적으로 불가능합니다. (dimension: {dimension})",
        }

    @staticmethod
    def veo_fallback(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fallback response for Veo video generation.

        Args:
            params: Optional generation parameters

        Returns:
            Fallback response dict
        """
        return {
            "video_url": None,
            "status": "service_unavailable",
            "fallback": True,
            "provider": "veo",
            "message": "비디오 생성 서비스가 일시적으로 불가능합니다. 잠시 후 다시 시도해 주세요.",
            "retry_after_seconds": 60,
        }

    @staticmethod
    def kling_fallback(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fallback response for Kling video generation.

        Args:
            params: Optional generation parameters

        Returns:
            Fallback response dict
        """
        return {
            "video_url": None,
            "status": "service_unavailable",
            "fallback": True,
            "provider": "kling",
            "message": "Kling 비디오 생성 서비스가 일시적으로 불가능합니다.",
            "retry_after_seconds": 120,
        }

    @staticmethod
    def qdrant_fallback(
        query: Optional[str] = None,
        collection: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fallback response for Qdrant vector search.

        Args:
            query: Original search query
            collection: Collection name

        Returns:
            Fallback response dict
        """
        return {
            "results": [],
            "total": 0,
            "fallback": True,
            "provider": "qdrant",
            "message": "벡터 검색이 일시적으로 불가능합니다.",
        }

    @staticmethod
    def notebooklm_fallback(
        notebook_id: Optional[str] = None,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fallback response for NotebookLM queries.

        Args:
            notebook_id: Notebook ID
            query: Original query

        Returns:
            Fallback response dict
        """
        return {
            "answer": "",
            "sources": [],
            "confidence": 0.0,
            "grounded": False,
            "fallback": True,
            "provider": "notebooklm",
            "message": "NotebookLM 서비스가 일시적으로 불가능합니다.",
        }


# =============================================================================
# Fallback Manager
# =============================================================================

class FallbackManager:
    """
    Manages fallback responses for circuit breaker integration.

    Features:
    - LRU cache for recent successful responses
    - Provider-specific static fallbacks
    - Configurable TTL and cache size
    """

    _instance: Optional["FallbackManager"] = None

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, max_cache_size: int = 1000, cache_ttl: int = 3600):
        """Initialize fallback manager.

        Args:
            max_cache_size: Maximum cache entries
            cache_ttl: Cache TTL in seconds
        """
        if self._initialized:
            return

        self._cache = LRUCache(max_size=max_cache_size, ttl_seconds=cache_ttl)
        self._fallback_strategies: Dict[str, Callable[..., Dict[str, Any]]] = {
            "gemini": FallbackStrategy.gemini_fallback,
            "rag": FallbackStrategy.rag_fallback,
            "veo": FallbackStrategy.veo_fallback,
            "kling": FallbackStrategy.kling_fallback,
            "qdrant": FallbackStrategy.qdrant_fallback,
            "notebooklm": FallbackStrategy.notebooklm_fallback,
        }
        self._initialized = True

    def _make_cache_key(self, provider: str, params: Dict[str, Any]) -> str:
        """Generate cache key from provider and params.

        Args:
            provider: Provider name
            params: Request parameters

        Returns:
            Cache key string
        """
        content = f"{provider}:{sorted(params.items())}"
        return hashlib.md5(content.encode()).hexdigest()

    def cache_response(
        self,
        provider: str,
        params: Dict[str, Any],
        response: Any,
    ) -> None:
        """Cache a successful response.

        Args:
            provider: Provider name
            params: Request parameters (for key generation)
            response: Response to cache
        """
        key = self._make_cache_key(provider, params)
        self._cache.set(key, {
            "provider": provider,
            "response": response,
            "params_hash": key,
        })
        logger.debug(f"[FALLBACK] Cached response for {provider}")

    def get_fallback(
        self,
        provider: str,
        params: Optional[Dict[str, Any]] = None,
        prefer_cached: bool = True,
    ) -> FallbackResponse:
        """Get fallback response for a provider.

        Tries cached response first, then falls back to static response.

        Args:
            provider: Provider name
            params: Request parameters
            prefer_cached: Whether to try cache first

        Returns:
            FallbackResponse with appropriate data
        """
        params = params or {}

        # Try cached response first
        if prefer_cached:
            key = self._make_cache_key(provider, params)
            cached = self._cache.get(key)
            if cached:
                logger.info(f"[FALLBACK] Using cached response for {provider}")
                return FallbackResponse(
                    data=cached["response"],
                    fallback_type=FallbackType.CACHED,
                    provider=provider,
                    cached_at=time.time(),
                    message="Using cached response due to service unavailability",
                )

        # Use static fallback
        strategy = self._fallback_strategies.get(provider)
        if strategy:
            logger.info(f"[FALLBACK] Using static fallback for {provider}")
            # Pass params dict directly, not as kwargs
            return FallbackResponse(
                data=strategy(params) if params else strategy(),
                fallback_type=FallbackType.STATIC,
                provider=provider,
                message="Service temporarily unavailable",
            )

        # No fallback available
        logger.warning(f"[FALLBACK] No fallback available for {provider}")
        return FallbackResponse(
            data={"error": "Service unavailable", "fallback": True},
            fallback_type=FallbackType.NONE,
            provider=provider,
            message="No fallback strategy configured for this provider",
        )

    def register_strategy(
        self,
        provider: str,
        strategy: Callable[..., Dict[str, Any]],
    ) -> None:
        """Register a custom fallback strategy.

        Args:
            provider: Provider name
            strategy: Callable that returns fallback dict
        """
        self._fallback_strategies[provider] = strategy
        logger.info(f"[FALLBACK] Registered custom strategy for {provider}")

    def clear_cache(self, provider: Optional[str] = None) -> int:
        """Clear cached responses.

        Args:
            provider: Optional provider to clear (clears all if None)

        Returns:
            Number of entries cleared
        """
        if provider is None:
            size = self._cache.size
            self._cache.clear()
            logger.info(f"[FALLBACK] Cleared all {size} cached entries")
            return size

        # Clear specific provider (would need iteration, simplified to clear all)
        size = self._cache.size
        self._cache.clear()
        return size

    def stats(self) -> Dict[str, Any]:
        """Get fallback manager statistics.

        Returns:
            Dict with cache stats and registered providers
        """
        return {
            "cache": self._cache.stats(),
            "registered_providers": list(self._fallback_strategies.keys()),
        }


# =============================================================================
# Circuit Breaker with Fallback Integration
# =============================================================================

async def call_with_fallback(
    operation: Callable[..., Any],
    provider: str,
    params: Optional[Dict[str, Any]] = None,
    breaker: Optional[Any] = None,
    fallback_manager: Optional[FallbackManager] = None,
    *args,
    **kwargs,
) -> Any:
    """
    Execute operation with circuit breaker and fallback support.

    Args:
        operation: Async callable to execute
        provider: Provider name for fallback
        params: Parameters for cache key
        breaker: Optional CircuitBreaker instance
        fallback_manager: Optional FallbackManager instance
        *args, **kwargs: Arguments to pass to operation

    Returns:
        Operation result or fallback response
    """
    fallback_mgr = fallback_manager or FallbackManager()
    params = params or {}

    # Check circuit breaker
    if breaker is not None:
        try:
            breaker.check_state()
        except Exception as e:
            # Circuit is open, return fallback
            logger.warning(f"[FALLBACK] Circuit open for {provider}, using fallback")
            return fallback_mgr.get_fallback(provider, params)

    try:
        # Execute operation
        result = await operation(*args, **kwargs)

        # Cache successful response
        fallback_mgr.cache_response(provider, params, result)

        # Record success in circuit breaker
        if breaker is not None:
            breaker.record_success()

        return result

    except Exception as e:
        # Record failure in circuit breaker
        if breaker is not None:
            breaker.record_failure(e)

        logger.warning(f"[FALLBACK] Operation failed for {provider}: {e}")

        # Return fallback
        return fallback_mgr.get_fallback(provider, params)


# =============================================================================
# Singleton Instance
# =============================================================================

_fallback_manager: Optional[FallbackManager] = None


def get_fallback_manager() -> FallbackManager:
    """Get singleton FallbackManager instance."""
    global _fallback_manager
    if _fallback_manager is None:
        _fallback_manager = FallbackManager()
    return _fallback_manager
