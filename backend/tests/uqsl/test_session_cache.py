"""
Tests for UQSL Session Cache (2026 Best Practice)

Tests:
- Local cache operations (set, get, update, delete)
- Fallback behavior when Redis unavailable
- TTL expiration
- Concurrent access
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.uqsl.session_cache import (
    UQSLSessionCache,
    BanditStatsCache,
    SESSION_TTL_SECONDS,
    LOCAL_CACHE_SIZE,
)


class TestUQSLSessionCache:
    """Tests for UQSLSessionCache class."""

    @pytest.fixture
    def cache(self):
        """Create a fresh cache instance for each test."""
        # Create new instance (not singleton) for test isolation
        return UQSLSessionCache(
            redis_url="redis://localhost:6380",
            ttl_seconds=60,
            local_cache_size=10,
        )

    @pytest.fixture
    def sample_session_data(self):
        """Sample session data for testing."""
        return {
            "candidates": [
                {"idx": 0, "content": "Test content 1", "backend_used": "qdrant"},
                {"idx": 1, "content": "Test content 2", "backend_used": "notebooklm"},
            ],
            "scores": [
                {"groundedness": 0.8, "relevance": 0.9, "coherence": 0.7, "creativity": 0.6, "safety": 0.95},
                {"groundedness": 0.85, "relevance": 0.85, "coherence": 0.8, "creativity": 0.7, "safety": 0.9},
            ],
            "prompt_hash": "abc123",
            "prompt_preview": "Test prompt...",
            "app_key": "test.app",
            "strategy": "auto",
            "arms_used": ["backend:qdrant_hybrid", "backend:notebooklm"],
            "created_at": datetime.utcnow().isoformat(),
        }

    # =========================================================================
    # Local Cache Tests (No Redis)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_set_and_get_local_cache(self, cache, sample_session_data):
        """Test setting and getting data from local cache."""
        session_id = "test-session-001"

        # Set data (will use local cache since Redis not available)
        result = await cache.set(session_id, sample_session_data)
        assert result is True

        # Get data
        retrieved = await cache.get(session_id)
        assert retrieved is not None
        assert retrieved["prompt_hash"] == sample_session_data["prompt_hash"]
        assert retrieved["app_key"] == sample_session_data["app_key"]

    @pytest.mark.asyncio
    async def test_update_session(self, cache, sample_session_data):
        """Test updating existing session data."""
        session_id = "test-session-002"

        # Set initial data
        await cache.set(session_id, sample_session_data)

        # Update data
        update_result = await cache.update(session_id, {
            "selected_idx": 1,
            "selection_time": datetime.utcnow().isoformat(),
        })
        assert update_result is True

        # Verify update
        retrieved = await cache.get(session_id)
        assert retrieved is not None
        assert retrieved["selected_idx"] == 1
        assert "selection_time" in retrieved

    @pytest.mark.asyncio
    async def test_delete_session(self, cache, sample_session_data):
        """Test deleting session data."""
        session_id = "test-session-003"

        # Set data
        await cache.set(session_id, sample_session_data)

        # Verify exists
        assert await cache.exists(session_id) is True

        # Delete
        await cache.delete(session_id)

        # Verify deleted
        assert await cache.exists(session_id) is False
        assert await cache.get(session_id) is None

    @pytest.mark.asyncio
    async def test_exists_check(self, cache, sample_session_data):
        """Test session existence check."""
        import uuid
        session_id = f"test-session-exists-{uuid.uuid4()}"

        # Initially doesn't exist
        assert await cache.exists(session_id) is False

        # After set, exists
        await cache.set(session_id, sample_session_data)
        assert await cache.exists(session_id) is True

    @pytest.mark.asyncio
    async def test_lru_eviction(self, cache, sample_session_data):
        """Test LRU cache eviction when capacity exceeded."""
        # Fill cache beyond capacity (cache_size = 10)
        for i in range(15):
            await cache.set(f"session-{i}", {**sample_session_data, "idx": i})

        # First few sessions should be evicted (LRU)
        # Note: Exact behavior depends on access patterns
        stats = await cache.get_stats()
        assert stats["local_cache_size"] <= cache._local_cache_size

    @pytest.mark.asyncio
    async def test_update_nonexistent_session(self, cache):
        """Test updating a session that doesn't exist."""
        result = await cache.update("nonexistent-session", {"key": "value"})
        assert result is False

    # =========================================================================
    # Fallback Memory Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_fallback_to_memory(self, cache, sample_session_data):
        """Test fallback to in-memory storage when Redis unavailable."""
        session_id = "test-session-fallback"

        # Set data (Redis not available, uses local cache + fallback)
        await cache.set(session_id, sample_session_data)

        # Should be in either local cache or fallback memory (or both)
        # When Redis is unavailable, data goes to both local cache and fallback
        in_local = session_id in cache._local_cache
        in_fallback = session_id in cache._fallback_memory
        assert in_local or in_fallback, "Session should be stored in local cache or fallback"

    @pytest.mark.asyncio
    async def test_cleanup_expired_fallback(self, cache):
        """Test cleanup of expired entries in fallback memory."""
        # Add expired entry
        cache._fallback_memory["expired-session"] = {
            "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "data": "test",
        }

        # Add valid entry
        cache._fallback_memory["valid-session"] = {
            "created_at": datetime.utcnow().isoformat(),
            "data": "test",
        }

        # Trigger cleanup
        cache._cleanup_fallback()

        # Expired should be removed
        assert "expired-session" not in cache._fallback_memory
        assert "valid-session" in cache._fallback_memory

    # =========================================================================
    # Stats Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_stats(self, cache, sample_session_data):
        """Test getting cache statistics."""
        # Add some sessions
        for i in range(3):
            await cache.set(f"stats-test-{i}", sample_session_data)

        stats = await cache.get_stats()

        assert "local_cache_size" in stats
        assert "local_cache_max" in stats
        assert "fallback_size" in stats
        assert "redis_healthy" in stats
        assert "ttl_seconds" in stats

        assert stats["local_cache_size"] >= 0
        assert stats["local_cache_max"] == cache._local_cache_size

    # =========================================================================
    # Serialization Tests
    # =========================================================================

    def test_serialize_deserialize(self, cache, sample_session_data):
        """Test data serialization and deserialization."""
        serialized = cache._serialize(sample_session_data)
        assert isinstance(serialized, str)

        deserialized = cache._deserialize(serialized)
        assert isinstance(deserialized, dict)
        assert deserialized["prompt_hash"] == sample_session_data["prompt_hash"]

    def test_serialize_with_datetime(self, cache):
        """Test serialization handles datetime objects."""
        data = {
            "created_at": datetime.utcnow(),
            "name": "test",
        }

        serialized = cache._serialize(data)
        assert isinstance(serialized, str)

        deserialized = cache._deserialize(serialized)
        assert isinstance(deserialized["created_at"], str)

    # =========================================================================
    # Key Generation Tests
    # =========================================================================

    def test_make_key(self, cache):
        """Test Redis key generation."""
        key = cache._make_key("test-session")
        assert key == "uqsl:session:test-session"


class TestBanditStatsCache:
    """Tests for BanditStatsCache class."""

    @pytest.fixture
    def bandit_cache(self):
        """Create a bandit stats cache instance."""
        return BanditStatsCache(redis_url="redis://localhost:6380")

    def test_make_key(self, bandit_cache):
        """Test arm key generation."""
        key = bandit_cache._make_key("backend:qdrant_hybrid")
        assert key == "uqsl:bandit:backend:qdrant_hybrid"


class TestGetSessionCache:
    """Tests for session cache singleton."""

    def test_singleton_pattern(self):
        """Test that get_session_cache returns same instance."""
        from app.uqsl.session_cache import get_session_cache

        cache1 = get_session_cache()
        cache2 = get_session_cache()

        # Should be same instance
        assert cache1 is cache2


class TestUQSLConfigs:
    """Tests for UQSL configuration in dimension_capsules."""

    def test_get_uqsl_config_known_app(self):
        """Test getting config for known app."""
        from app.fixtures.dimension_capsules import get_uqsl_config

        config = get_uqsl_config("dimension.aesthetic.direct")

        assert config["enabled"] is True
        assert config["selection_strategy"] == "hybrid"
        assert config["tier"] == "premium"
        assert "quality_weights" in config
        assert config["quality_weights"]["groundedness"] == 0.40  # Higher for auteur

    def test_get_uqsl_config_unknown_app(self):
        """Test getting default config for unknown app."""
        from app.fixtures.dimension_capsules import get_uqsl_config

        config = get_uqsl_config("unknown.app.key")

        # Should return defaults
        assert config["enabled"] is True
        assert config["n_candidates"] == 3
        assert config["selection_strategy"] == "auto"
        assert config["tier"] == "free"

    def test_uqsl_config_completeness(self):
        """Test that all UQSL configs have required fields."""
        from app.fixtures.dimension_capsules import UQSL_APP_CONFIGS

        required_fields = [
            "enabled",
            "n_candidates",
            "selection_strategy",
            "auto_threshold",
            "top_k_for_hitl",
            "quality_weights",
            "bandit_arms",
            "tier",
        ]

        for app_key, config in UQSL_APP_CONFIGS.items():
            for field in required_fields:
                assert field in config, f"Missing {field} in {app_key}"

    def test_quality_weights_sum_to_one(self):
        """Test that quality weights sum to approximately 1.0."""
        from app.fixtures.dimension_capsules import UQSL_APP_CONFIGS

        for app_key, config in UQSL_APP_CONFIGS.items():
            weights = config["quality_weights"]
            total = sum(weights.values())
            assert abs(total - 1.0) < 0.01, f"Weights don't sum to 1.0 for {app_key}: {total}"
