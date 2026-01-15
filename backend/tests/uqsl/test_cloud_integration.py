"""
UQSL Cloud Integration Tests

Tests for Cloud SQL, BigQuery, and Redis integration.
"""

import asyncio
import json
import logging
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.uqsl.cloud_integration import (
    BigQueryUQSLEvent,
    UQSLSessionCache,
    ThompsonSamplingCache,
    get_redis_client,
    log_uqsl_event,
    _memory_cache,
    UQSL_CACHE_PREFIX,
)


@pytest.fixture(autouse=True)
def setup_logging(caplog):
    """Enable log capture for all tests."""
    caplog.set_level(logging.DEBUG)


@pytest.fixture
def clear_memory_cache():
    """Clear in-memory cache before each test."""
    _memory_cache.clear()
    yield
    _memory_cache.clear()


class TestBigQueryUQSLEvent:
    """Test BigQuery event model."""

    def test_event_creation(self):
        """Test basic event creation."""
        event = BigQueryUQSLEvent(
            event_id="test-123",
            event_type="generation",
            app_key="dimension.aesthetic",
        )

        assert event.event_id == "test-123"
        assert event.event_type == "generation"
        assert event.app_key == "dimension.aesthetic"
        assert event.timestamp is not None

    def test_event_with_all_fields(self):
        """Test event with all fields populated."""
        event = BigQueryUQSLEvent(
            event_id="test-456",
            event_type="selection",
            app_key="dimension.aesthetic",
            prompt_hash="abc123",
            n_candidates=3,
            quality_scores=[{"groundedness": 0.8}],
            selected_idx=1,
            selection_method="auto",
            selection_confidence=0.92,
            arms_used=["backend:qdrant_hybrid"],
            user_feedback="positive",
            recommended="ab",
            user_selected="ab",
            latency_ms=1500,
            tier="premium",
            dimension="AD",
            user_id="user-123",
        )

        data = event.model_dump(mode="json")
        assert data["event_id"] == "test-456"
        assert data["n_candidates"] == 3
        assert data["selection_confidence"] == 0.92

    def test_event_serialization(self):
        """Test JSON serialization."""
        event = BigQueryUQSLEvent(
            event_id="test-789",
            event_type="feedback",
            app_key="test.app",
        )

        data = event.model_dump(mode="json")
        assert isinstance(data, dict)
        assert "timestamp" in data


class TestUQSLSessionCache:
    """Test UQSL session caching with in-memory fallback."""

    @pytest.mark.asyncio
    async def test_set_and_get_memory_fallback(self, clear_memory_cache):
        """Test set and get with in-memory fallback."""
        # Mock Redis to return None (triggers fallback)
        with patch("app.uqsl.cloud_integration.get_redis_client", new_callable=AsyncMock) as mock_redis:
            mock_redis.return_value = None

            session_id = "test-session-123"
            data = {"candidates": [1, 2, 3], "app_key": "test.app"}

            # Set
            result = await UQSLSessionCache.set(session_id, data, ttl=3600)
            assert result is True

            # Get
            retrieved = await UQSLSessionCache.get(session_id)
            assert retrieved == data

    @pytest.mark.asyncio
    async def test_delete_memory_fallback(self, clear_memory_cache):
        """Test delete with in-memory fallback."""
        with patch("app.uqsl.cloud_integration.get_redis_client", new_callable=AsyncMock) as mock_redis:
            mock_redis.return_value = None

            session_id = "test-session-delete"
            data = {"test": "data"}

            await UQSLSessionCache.set(session_id, data)
            assert await UQSLSessionCache.get(session_id) == data

            await UQSLSessionCache.delete(session_id)
            assert await UQSLSessionCache.get(session_id) is None

    @pytest.mark.asyncio
    async def test_ttl_expiration_memory_fallback(self, clear_memory_cache):
        """Test TTL expiration with in-memory fallback."""
        with patch("app.uqsl.cloud_integration.get_redis_client", new_callable=AsyncMock) as mock_redis:
            mock_redis.return_value = None

            session_id = "test-session-ttl"
            data = {"test": "data"}

            # Set with very short TTL
            await UQSLSessionCache.set(session_id, data, ttl=0)  # Already expired

            # Should be expired
            key = f"{UQSL_CACHE_PREFIX}session:{session_id}"
            if key in _memory_cache:
                _memory_cache[key] = (data, 0)  # Set expiry to past

            retrieved = await UQSLSessionCache.get(session_id)
            assert retrieved is None

    @pytest.mark.asyncio
    async def test_with_mock_redis(self, clear_memory_cache):
        """Test with mocked Redis client."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value='{"test": "data"}')
        mock_redis.delete = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock(return_value=True)

        with patch("app.uqsl.cloud_integration.get_redis_client", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_redis

            session_id = "test-redis"
            data = {"test": "data"}

            # Set
            result = await UQSLSessionCache.set(session_id, data)
            assert result is True
            mock_redis.set.assert_called_once()

            # Get
            retrieved = await UQSLSessionCache.get(session_id)
            assert retrieved == data

            # Delete
            await UQSLSessionCache.delete(session_id)
            mock_redis.delete.assert_called_once()


class TestThompsonSamplingCache:
    """Test Thompson Sampling arm caching."""

    @pytest.mark.asyncio
    async def test_get_arm_stats_no_redis(self):
        """Test get arm stats when Redis is unavailable."""
        with patch("app.uqsl.cloud_integration.get_redis_client", new_callable=AsyncMock) as mock_redis:
            mock_redis.return_value = None

            stats = await ThompsonSamplingCache.get_arm_stats("backend:qdrant_hybrid")
            assert stats is None

    @pytest.mark.asyncio
    async def test_set_arm_stats_no_redis(self):
        """Test set arm stats when Redis is unavailable."""
        with patch("app.uqsl.cloud_integration.get_redis_client", new_callable=AsyncMock) as mock_redis:
            mock_redis.return_value = None

            result = await ThompsonSamplingCache.set_arm_stats(
                "backend:qdrant_hybrid",
                alpha=10,
                beta=5,
                total_trials=15,
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_with_mock_redis(self):
        """Test with mocked Redis client."""
        mock_redis = AsyncMock()
        mock_redis.hgetall = AsyncMock(return_value={
            "alpha": "10",
            "beta": "5",
            "total_trials": "15",
        })
        mock_redis.hset = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock(return_value=True)

        with patch("app.uqsl.cloud_integration.get_redis_client", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_redis

            # Get
            stats = await ThompsonSamplingCache.get_arm_stats("backend:qdrant_hybrid")
            assert stats == {"alpha": 10, "beta": 5, "total_trials": 15}

            # Set
            result = await ThompsonSamplingCache.set_arm_stats(
                "backend:qdrant_hybrid",
                alpha=11,
                beta=6,
                total_trials=17,
            )
            assert result is True
            mock_redis.hset.assert_called_once()

    @pytest.mark.asyncio
    async def test_increment_arm_no_redis(self):
        """Test increment when Redis is unavailable."""
        with patch("app.uqsl.cloud_integration.get_redis_client", new_callable=AsyncMock) as mock_redis:
            mock_redis.return_value = None

            stats = await ThompsonSamplingCache.increment_arm("backend:qdrant_hybrid", success=True)
            assert stats == {"alpha": 1, "beta": 1, "total_trials": 0}


class TestLogUQSLEvent:
    """Test UQSL event logging."""

    @pytest.mark.asyncio
    async def test_log_event_no_bigquery(self):
        """Test logging when BigQuery is not configured."""
        with patch("app.uqsl.cloud_integration.get_bigquery_client", new_callable=AsyncMock) as mock_bq:
            mock_bq.return_value = None

            with patch("app.uqsl.cloud_integration._log_event_locally", new_callable=AsyncMock) as mock_local:
                mock_local.return_value = None

                event = BigQueryUQSLEvent(
                    event_id="test-log",
                    event_type="generation",
                    app_key="test.app",
                )

                result = await log_uqsl_event(event)
                assert result is True
                mock_local.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_event_with_bigquery(self):
        """Test logging with BigQuery client."""
        mock_bq = MagicMock()
        mock_bq.insert_rows_json = MagicMock(return_value=[])

        with patch("app.uqsl.cloud_integration.get_bigquery_client", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_bq

            event = BigQueryUQSLEvent(
                event_id="test-bq",
                event_type="selection",
                app_key="test.app",
            )

            result = await log_uqsl_event(event)
            assert result is True


class TestManifestUQSLConfig:
    """Test UQSL configuration in manifests."""

    def test_load_manifest_with_quality_selection(self):
        """Test loading manifest with quality_selection block."""
        from app.rag.manifest_loader import get_manifest

        manifest = get_manifest("dimension.aesthetic.direct")

        assert manifest is not None
        assert manifest.quality_selection is not None
        assert manifest.quality_selection.enabled is True
        assert manifest.quality_selection.tier == "premium"

    def test_uqsl_multi_generate_config(self):
        """Test multi_generate configuration."""
        from app.rag.manifest_loader import get_manifest

        manifest = get_manifest("dimension.aesthetic.direct")

        mg = manifest.quality_selection.multi_generate
        assert mg is not None
        assert mg.candidates == 3
        assert mg.parallel is True
        assert mg.diversity_factor == 0.3

    def test_uqsl_quality_weights(self):
        """Test quality_weights configuration."""
        from app.rag.manifest_loader import get_manifest

        manifest = get_manifest("dimension.aesthetic.direct")

        weights = manifest.quality_selection.quality_weights
        assert weights is not None
        assert weights.groundedness == 0.35
        assert weights.creativity == 0.15

    def test_uqsl_selection_config(self):
        """Test selection configuration."""
        from app.rag.manifest_loader import get_manifest

        manifest = get_manifest("dimension.aesthetic.direct")

        selection = manifest.quality_selection.selection
        assert selection is not None
        assert selection.strategy == "hybrid"
        assert selection.auto_threshold == 0.85

    def test_uqsl_bandit_config(self):
        """Test bandit configuration."""
        from app.rag.manifest_loader import get_manifest

        manifest = get_manifest("dimension.aesthetic.direct")

        bandit = manifest.quality_selection.bandit
        assert bandit is not None
        assert bandit.enabled is True
        assert "backend:qdrant_hybrid" in bandit.arms

    def test_uqsl_ensemble_plus_plus_config(self):
        """Test ensemble_plus_plus configuration."""
        from app.rag.manifest_loader import get_manifest

        manifest = get_manifest("dimension.aesthetic.direct")

        ensemble = manifest.quality_selection.ensemble_plus_plus
        assert ensemble is not None
        assert ensemble.enabled is True
        assert ensemble.backend_a == "qdrant_hybrid"
        assert ensemble.backend_b == "notebooklm"

    def test_uqsl_feedback_config(self):
        """Test feedback configuration."""
        from app.rag.manifest_loader import get_manifest

        manifest = get_manifest("dimension.aesthetic.direct")

        feedback = manifest.quality_selection.feedback
        assert feedback is not None
        assert feedback.enabled is True
        assert feedback.implicit is True
        assert feedback.explicit is True
        assert feedback.bigquery_sync is False
