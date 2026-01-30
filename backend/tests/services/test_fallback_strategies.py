"""
Tests for fallback_strategies module.

Tests cover:
- LRU cache with TTL
- FallbackStrategy static methods
- FallbackManager caching and retrieval
- call_with_fallback integration
"""
import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.fallback_strategies import (
    LRUCache,
    FallbackStrategy,
    FallbackManager,
    FallbackResponse,
    FallbackType,
    call_with_fallback,
    get_fallback_manager,
)


# =============================================================================
# LRU Cache Tests
# =============================================================================

class TestLRUCache:
    """Tests for LRU cache implementation."""

    def test_set_and_get_value(self):
        """Should store and retrieve values."""
        cache = LRUCache(max_size=10, ttl_seconds=3600)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_returns_none_for_missing_key(self):
        """Should return None for missing keys."""
        cache = LRUCache(max_size=10, ttl_seconds=3600)
        assert cache.get("nonexistent") is None

    def test_evicts_oldest_when_at_capacity(self):
        """Should evict oldest entry when at capacity."""
        cache = LRUCache(max_size=3, ttl_seconds=3600)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should evict key1

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_access_updates_lru_order(self):
        """Accessing an entry should update its LRU order."""
        cache = LRUCache(max_size=3, ttl_seconds=3600)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 to make it most recently used
        cache.get("key1")

        # Add new entry - should evict key2 (oldest unused)
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"  # Still exists
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_expired_entries_return_none(self):
        """Expired entries should return None."""
        cache = LRUCache(max_size=10, ttl_seconds=1)
        cache.set("key1", "value1")

        # Manually expire the entry
        cache._cache["key1"].created_at = time.time() - 2

        assert cache.get("key1") is None

    def test_clear_removes_all_entries(self):
        """Clear should remove all entries."""
        cache = LRUCache(max_size=10, ttl_seconds=3600)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.size == 0

    def test_cleanup_expired_removes_old_entries(self):
        """cleanup_expired should remove expired entries."""
        cache = LRUCache(max_size=10, ttl_seconds=1)
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Manually expire key1
        cache._cache["key1"].created_at = time.time() - 2

        removed = cache.cleanup_expired()
        assert removed == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_stats_returns_cache_info(self):
        """stats should return cache statistics."""
        cache = LRUCache(max_size=100, ttl_seconds=3600)
        cache.set("key1", "value1")
        cache.get("key1")  # Access to increment count

        stats = cache.stats()
        assert stats["size"] == 1
        assert stats["max_size"] == 100
        assert stats["ttl_seconds"] == 3600


# =============================================================================
# FallbackStrategy Tests
# =============================================================================

class TestFallbackStrategy:
    """Tests for static fallback strategies."""

    def test_gemini_fallback_returns_message(self):
        """Gemini fallback should return service unavailable message."""
        result = FallbackStrategy.gemini_fallback()
        assert result["fallback"] is True
        assert result["provider"] == "gemini"
        assert "서비스 일시 중단" in result["text"]

    def test_rag_fallback_includes_dimension(self):
        """RAG fallback should include dimension in message."""
        result = FallbackStrategy.rag_fallback(dimension="4D")
        assert result["fallback"] is True
        assert result["provider"] == "rag"
        assert result["sources"] == []
        assert "4D" in result["message"]

    def test_veo_fallback_has_retry_after(self):
        """Veo fallback should include retry_after_seconds."""
        result = FallbackStrategy.veo_fallback()
        assert result["fallback"] is True
        assert result["provider"] == "veo"
        assert "retry_after_seconds" in result
        assert result["video_url"] is None

    def test_kling_fallback_has_retry_after(self):
        """Kling fallback should include retry_after_seconds."""
        result = FallbackStrategy.kling_fallback()
        assert result["fallback"] is True
        assert result["provider"] == "kling"
        assert "retry_after_seconds" in result

    def test_qdrant_fallback_returns_empty_results(self):
        """Qdrant fallback should return empty results."""
        result = FallbackStrategy.qdrant_fallback()
        assert result["fallback"] is True
        assert result["provider"] == "qdrant"
        assert result["results"] == []
        assert result["total"] == 0

    def test_notebooklm_fallback_returns_empty_answer(self):
        """NotebookLM fallback should return empty answer."""
        result = FallbackStrategy.notebooklm_fallback(notebook_id="test")
        assert result["fallback"] is True
        assert result["provider"] == "notebooklm"
        assert result["answer"] == ""
        assert result["sources"] == []
        assert result["confidence"] == 0.0


# =============================================================================
# FallbackManager Tests
# =============================================================================

class TestFallbackManager:
    """Tests for FallbackManager."""

    def setup_method(self):
        """Reset singleton for each test."""
        # Reset singleton
        FallbackManager._instance = None

    def test_caches_response(self):
        """Should cache successful responses."""
        manager = FallbackManager()
        params = {"prompt": "test prompt"}
        response = {"text": "test response"}

        manager.cache_response("gemini", params, response)

        # Retrieve cached response
        fallback = manager.get_fallback("gemini", params)
        assert fallback.fallback_type == FallbackType.CACHED
        assert fallback.data == response

    def test_returns_static_fallback_when_no_cache(self):
        """Should return static fallback when no cached response."""
        manager = FallbackManager()
        params = {"prompt": "uncached prompt"}

        fallback = manager.get_fallback("gemini", params)
        assert fallback.fallback_type == FallbackType.STATIC
        assert fallback.data["fallback"] is True
        assert fallback.data["provider"] == "gemini"

    def test_returns_none_type_for_unknown_provider(self):
        """Should return NONE type for unknown provider."""
        manager = FallbackManager()
        fallback = manager.get_fallback("unknown_provider", {})
        assert fallback.fallback_type == FallbackType.NONE
        assert "error" in fallback.data

    def test_register_custom_strategy(self):
        """Should allow registering custom fallback strategies."""
        manager = FallbackManager()

        def custom_fallback(**kwargs):
            return {"custom": True, "fallback": True}

        manager.register_strategy("custom_provider", custom_fallback)

        fallback = manager.get_fallback("custom_provider")
        assert fallback.data["custom"] is True

    def test_clear_cache(self):
        """Should clear cached responses."""
        manager = FallbackManager()
        manager.cache_response("gemini", {"key": "1"}, {"response": 1})
        manager.cache_response("gemini", {"key": "2"}, {"response": 2})

        cleared = manager.clear_cache()
        assert cleared >= 0

    def test_stats_returns_info(self):
        """Should return statistics."""
        manager = FallbackManager()
        stats = manager.stats()
        assert "cache" in stats
        assert "registered_providers" in stats
        assert "gemini" in stats["registered_providers"]


# =============================================================================
# FallbackResponse Tests
# =============================================================================

class TestFallbackResponse:
    """Tests for FallbackResponse dataclass."""

    def test_to_dict_includes_fallback_flag(self):
        """to_dict should include fallback=True."""
        response = FallbackResponse(
            data={"text": "test"},
            fallback_type=FallbackType.CACHED,
            provider="gemini",
        )
        result = response.to_dict()
        assert result["fallback"] is True
        assert result["fallback_type"] == "cached"
        assert result["provider"] == "gemini"


# =============================================================================
# call_with_fallback Integration Tests
# =============================================================================

class TestCallWithFallback:
    """Tests for call_with_fallback function."""

    @pytest.mark.asyncio
    async def test_returns_operation_result_on_success(self):
        """Should return operation result when successful."""
        async def successful_operation():
            return {"result": "success"}

        result = await call_with_fallback(
            operation=successful_operation,
            provider="gemini",
            params={"test": "params"},
        )
        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_returns_fallback_on_circuit_open(self):
        """Should return fallback when circuit is open."""
        from app.services.circuit_breaker import CircuitBreakerOpen

        mock_breaker = MagicMock()
        mock_breaker.check_state = MagicMock(
            side_effect=CircuitBreakerOpen("test", 30.0)
        )

        async def operation():
            return {"result": "success"}

        result = await call_with_fallback(
            operation=operation,
            provider="gemini",
            breaker=mock_breaker,
        )
        assert isinstance(result, FallbackResponse)
        assert result.is_fallback is True

    @pytest.mark.asyncio
    async def test_returns_fallback_on_operation_failure(self):
        """Should return fallback when operation fails."""
        mock_breaker = MagicMock()
        mock_breaker.check_state = MagicMock()
        mock_breaker.record_failure = MagicMock()

        async def failing_operation():
            raise ConnectionError("Failed")

        result = await call_with_fallback(
            operation=failing_operation,
            provider="gemini",
            breaker=mock_breaker,
        )
        assert isinstance(result, FallbackResponse)
        mock_breaker.record_failure.assert_called()

    @pytest.mark.asyncio
    async def test_records_success_in_circuit_breaker(self):
        """Should record success in circuit breaker."""
        mock_breaker = MagicMock()
        mock_breaker.check_state = MagicMock()
        mock_breaker.record_success = MagicMock()

        async def successful_operation():
            return {"result": "success"}

        await call_with_fallback(
            operation=successful_operation,
            provider="gemini",
            breaker=mock_breaker,
        )
        mock_breaker.record_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_caches_successful_response(self):
        """Should cache successful responses for later fallback."""
        manager = FallbackManager()
        FallbackManager._instance = manager  # Reset singleton

        params = {"unique": "test_cache"}

        async def successful_operation():
            return {"cached_result": "data"}

        # First call - should succeed and cache
        result1 = await call_with_fallback(
            operation=successful_operation,
            provider="gemini",
            params=params,
            fallback_manager=manager,
        )
        assert result1 == {"cached_result": "data"}

        # Now get fallback - should use cached response
        fallback = manager.get_fallback("gemini", params)
        assert fallback.fallback_type == FallbackType.CACHED
        assert fallback.data == {"cached_result": "data"}


# =============================================================================
# get_fallback_manager Tests
# =============================================================================

class TestGetFallbackManager:
    """Tests for get_fallback_manager function."""

    def setup_method(self):
        """Reset singleton for each test."""
        FallbackManager._instance = None

    def test_returns_singleton_instance(self):
        """Should return same instance on multiple calls."""
        manager1 = get_fallback_manager()
        manager2 = get_fallback_manager()
        assert manager1 is manager2

    def test_manager_is_initialized(self):
        """Returned manager should be initialized."""
        manager = get_fallback_manager()
        assert manager._initialized is True
        assert len(manager._fallback_strategies) > 0
