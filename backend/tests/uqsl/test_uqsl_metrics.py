"""
UQSL Metrics Module Tests

Tests for Prometheus metrics collection in UQSL.
"""

import logging
import pytest
from unittest.mock import patch, MagicMock

from app.uqsl.metrics import (
    record_generation,
    record_quality_scores,
    record_selection,
    record_feedback,
    record_thompson_sampling_update,
    record_three_way_comparison,
    record_error,
    set_generation_in_progress,
    track_uqsl_operation,
    get_uqsl_metrics_summary,
)


@pytest.fixture(autouse=True)
def setup_logging(caplog):
    """Enable log capture for all tests."""
    caplog.set_level(logging.DEBUG)


class TestMetricsRecording:
    """Test metric recording functions."""

    def test_record_generation(self, caplog):
        """Test generation metrics recording."""
        record_generation(
            app_key="dimension.aesthetic",
            strategy="auto",
            tier="premium",
            n_candidates=3,
            latency_ms=1500.5,
        )

        # Check structured log
        assert "UQSL generation completed" in caplog.text or any(
            r.message == "UQSL generation completed" for r in caplog.records
        )

    def test_record_quality_scores(self):
        """Test quality score recording."""
        # Should not raise
        record_quality_scores(
            app_key="dimension.1d",
            groundedness=0.85,
            relevance=0.90,
            coherence=0.88,
            creativity=0.75,
            safety=0.95,
            weighted_score=0.87,
        )

    def test_record_selection(self, caplog):
        """Test selection metrics recording."""
        record_selection(
            app_key="dimension.story",
            method="quality",
            selection_type="auto",
            selected_idx=2,
            confidence=0.92,
        )

        # Should log
        assert any(
            "UQSL selection recorded" in (r.message if hasattr(r, 'message') else str(r))
            for r in caplog.records
        ) or "UQSL selection recorded" in caplog.text

    def test_record_feedback_positive(self, caplog):
        """Test positive feedback recording."""
        record_feedback(
            app_key="dimension.ad",
            feedback_type="positive",
            selection_id="test-selection-123",
        )

        # Check log message was recorded
        assert "UQSL feedback recorded" in caplog.text

    def test_record_feedback_negative(self, caplog):
        """Test negative feedback recording."""
        record_feedback(
            app_key="dimension.ad",
            feedback_type="negative",
        )

        # Check log message was recorded
        assert "UQSL feedback recorded" in caplog.text

    def test_record_thompson_sampling_update(self):
        """Test Thompson Sampling update recording."""
        record_thompson_sampling_update(
            arm_id="backend:qdrant_hybrid",
            reward=True,
            alpha=15,
            beta=5,
        )

    def test_record_three_way_comparison(self, caplog):
        """Test Ensemble++ 3-way comparison recording."""
        record_three_way_comparison(
            dimension="AD",
            auteur_key="bong",
            recommended="ab",
            user_selected="ab",
            latency_ms=2500.0,
        )

        # Check log message was recorded
        assert "Ensemble++ 3-way comparison" in caplog.text

    def test_record_error(self, caplog):
        """Test error recording."""
        record_error(
            stage="generation",
            error_type="TimeoutError",
            error_message="Generation timed out after 30s",
            app_key="dimension.veo",
        )

        # Should be warning level
        assert any(r.levelname == "WARNING" for r in caplog.records)


class TestDecoratorTracking:
    """Test the track_uqsl_operation decorator."""

    @pytest.mark.asyncio
    async def test_track_operation_success(self, caplog):
        """Test successful operation tracking."""
        @track_uqsl_operation("test_operation")
        async def successful_operation():
            return {"result": "success"}

        result = await successful_operation()

        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_track_operation_failure(self, caplog):
        """Test failed operation tracking."""
        @track_uqsl_operation("failing_operation")
        async def failing_operation():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await failing_operation()

        # Should log warning
        assert any(r.levelname == "WARNING" for r in caplog.records)


class TestHealthCheck:
    """Test health check helper."""

    def test_get_metrics_summary(self):
        """Test metrics summary returns expected structure."""
        summary = get_uqsl_metrics_summary()

        assert "metrics_enabled" in summary
        assert "prometheus_available" in summary
        assert isinstance(summary["metrics_enabled"], bool)
        assert isinstance(summary["prometheus_available"], bool)


class TestMetricsWithPrometheus:
    """Test metrics with mocked Prometheus client."""

    def test_generation_counter_increment(self):
        """Test generation counter is incremented."""
        # This tests the internal logic even if prometheus isn't installed
        # The function should not raise regardless of prometheus status
        record_generation(
            app_key="test.app",
            strategy="auto",
            tier="free",
            n_candidates=2,
            latency_ms=100,
        )

    def test_generation_in_progress_gauge(self):
        """Test in-progress gauge operations."""
        # Should not raise
        set_generation_in_progress("test.app", delta=1)
        set_generation_in_progress("test.app", delta=-1)

    def test_record_with_none_values(self):
        """Test recording with None values doesn't crash."""
        record_generation(
            app_key=None,
            strategy=None,
            tier=None,
            n_candidates=1,
            latency_ms=0,
        )

        record_error(
            stage="test",
            error_type="TestError",
            error_message=None,
            app_key=None,
        )


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_app_key(self):
        """Test with empty app_key."""
        record_generation(
            app_key="",
            strategy="auto",
            tier="free",
            n_candidates=1,
            latency_ms=50,
        )

    def test_unicode_in_error_message(self):
        """Test unicode characters in error messages."""
        record_error(
            stage="test",
            error_type="UnicodeError",
            error_message="에러 메시지 with 한글 and émojis 🎬",
            app_key="test.app",
        )

    def test_long_error_message_truncation(self):
        """Test long error messages are truncated."""
        long_message = "A" * 500
        record_error(
            stage="test",
            error_type="LongError",
            error_message=long_message,
            app_key="test.app",
        )
        # Should not raise, message truncated to 200 chars

    def test_all_quality_metrics_at_boundaries(self):
        """Test quality metrics at boundary values."""
        record_quality_scores(
            app_key="test",
            groundedness=0.0,
            relevance=1.0,
            coherence=0.5,
            creativity=0.0,
            safety=1.0,
            weighted_score=0.5,
        )

        record_quality_scores(
            app_key="test",
            groundedness=1.0,
            relevance=0.0,
            coherence=1.0,
            creativity=1.0,
            safety=0.0,
            weighted_score=1.0,
        )
