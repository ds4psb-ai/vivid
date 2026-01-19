"""Tests for Feedback Loop Service (Phase 7 HITL Enhancement).

Tests for feedback → RAG pipeline processing.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

# Skip all tests if dependencies unavailable
try:
    from app.services.feedback_loop import (
        FeedbackLoopService,
        FeedbackIngestionResult,
        FeedbackActionResult,
        LearningCycleResult,
    )
    from app.models_feedback import CorrectionType
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    FeedbackLoopService = None
    FeedbackIngestionResult = None
    FeedbackActionResult = None
    LearningCycleResult = None
    CorrectionType = None


pytestmark = pytest.mark.skipif(
    not DEPS_AVAILABLE,
    reason=f"Dependencies not available: {IMPORT_ERROR if not DEPS_AVAILABLE else ''}"
)


class TestFeedbackIngestionResult:
    """Tests for FeedbackIngestionResult dataclass."""

    def test_successful_ingestion(self):
        """Should store successful ingestion info."""
        result = FeedbackIngestionResult(
            success=True,
            feedback_id=uuid4(),
            qdrant_point_id="point_123",
            dimension="4D",
            collection_name="test_collection",
        )

        assert result.success is True
        assert result.qdrant_point_id == "point_123"
        assert result.dimension == "4D"
        assert result.error is None

    def test_failed_ingestion(self):
        """Should store error information."""
        result = FeedbackIngestionResult(
            success=False,
            feedback_id=uuid4(),
            error="Connection failed",
        )

        assert result.success is False
        assert result.error == "Connection failed"
        assert result.qdrant_point_id is None


class TestFeedbackActionResult:
    """Tests for FeedbackActionResult dataclass."""

    def test_correction_applied(self):
        """Should track correction details."""
        result = FeedbackActionResult(
            success=True,
            feedback_id=uuid4(),
            correction_type=CorrectionType.SOURCE_FLAGGED,
            correction_id=uuid4(),
            actions_taken=["flagged_source", "notified_admin"],
        )

        assert result.success is True
        assert result.correction_type == CorrectionType.SOURCE_FLAGGED
        assert len(result.actions_taken) == 2


class TestLearningCycleResult:
    """Tests for LearningCycleResult dataclass."""

    def test_complete_cycle(self):
        """Should summarize cycle statistics."""
        result = LearningCycleResult(
            cycle_id="cycle_2026-01-20",
            processed_count=100,
            ingested_count=75,
            corrected_count=10,
            error_count=5,
            duration_seconds=120.5,
        )

        assert result.processed_count == 100
        assert result.ingested_count == 75
        assert result.corrected_count == 10
        assert result.error_count == 5


class TestFeedbackLoopService:
    """Tests for FeedbackLoopService."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create a FeedbackLoopService instance."""
        return FeedbackLoopService(mock_db)

    @pytest.mark.asyncio
    async def test_process_positive_feedback_high_rating(self, service, mock_db):
        """High-rating feedback (>= 4) should be ingested to RAG."""
        mock_feedback = MagicMock()
        mock_feedback.id = uuid4()
        mock_feedback.rating = 5
        mock_feedback.response_id = uuid4()
        mock_feedback.user_id = "user_123"
        mock_feedback.comment = "Great response!"

        mock_response = MagicMock()
        mock_response.id = uuid4()
        mock_response.query = "test query"
        mock_response.response_text = "test response"
        mock_response.dimension = "4D"

        with patch.object(service, '_ingest_to_qdrant', return_value="point_123") as mock_ingest:
            result = await service.process_positive_feedback(
                feedback=mock_feedback,
                rag_response=mock_response,
            )

            assert result.success is True
            mock_ingest.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_positive_feedback_low_rating(self, service, mock_db):
        """Low-rating feedback (< 4) should not be ingested."""
        mock_feedback = MagicMock()
        mock_feedback.id = uuid4()
        mock_feedback.rating = 2
        mock_feedback.response_id = uuid4()

        mock_response = MagicMock()
        mock_response.id = uuid4()

        with patch.object(service, '_ingest_to_qdrant') as mock_ingest:
            result = await service.process_positive_feedback(
                feedback=mock_feedback,
                rag_response=mock_response,
            )

            # Low rating should not trigger ingestion
            mock_ingest.assert_not_called()
            assert result.success is False

    @pytest.mark.asyncio
    async def test_process_negative_feedback(self, service, mock_db):
        """Negative feedback should create correction record."""
        mock_feedback = MagicMock()
        mock_feedback.id = uuid4()
        mock_feedback.rating = 1
        mock_feedback.response_id = uuid4()
        mock_feedback.user_id = "user_123"
        mock_feedback.comment = "Wrong information"

        mock_response = MagicMock()
        mock_response.id = uuid4()
        mock_response.query = "test query"

        result = await service.process_negative_feedback(
            feedback=mock_feedback,
            rag_response=mock_response,
        )

        assert result.success is True
        assert result.correction_type in [
            CorrectionType.SOURCE_FLAGGED,
            CorrectionType.CACHE_INVALIDATED,
            CorrectionType.CRAG_TRIGGERED,
        ]
        mock_db.add.assert_called()

    @pytest.mark.asyncio
    async def test_aggregate_learning_cycle_empty(self, service, mock_db):
        """Empty cycle should report zero counts."""
        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )

        result = await service.aggregate_learning_cycle("cycle_test")

        assert result.processed_count == 0
        assert result.ingested_count == 0
        assert result.corrected_count == 0

    @pytest.mark.asyncio
    async def test_aggregate_learning_cycle_with_data(self, service, mock_db):
        """Cycle with data should process and report counts."""
        # Create mock feedbacks
        mock_feedbacks = []
        for i in range(10):
            f = MagicMock()
            f.id = uuid4()
            f.rating = 5 if i < 7 else 2  # 7 positive, 3 negative
            f.response_id = uuid4()
            mock_feedbacks.append(f)

        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_feedbacks)))
        )

        with patch.object(service, 'process_positive_feedback') as mock_pos:
            with patch.object(service, 'process_negative_feedback') as mock_neg:
                mock_pos.return_value = FeedbackIngestionResult(
                    success=True, feedback_id=uuid4(), qdrant_point_id="point"
                )
                mock_neg.return_value = FeedbackActionResult(
                    success=True, feedback_id=uuid4(), correction_type=CorrectionType.SOURCE_FLAGGED
                )

                result = await service.aggregate_learning_cycle("cycle_test")

                assert result.processed_count == 10


class TestCorrectionType:
    """Tests for CorrectionType enum."""

    def test_source_flagged_value(self):
        """SOURCE_FLAGGED should have correct string value."""
        assert CorrectionType.SOURCE_FLAGGED == "source_flagged"

    def test_cache_invalidated_value(self):
        """CACHE_INVALIDATED should have correct string value."""
        assert CorrectionType.CACHE_INVALIDATED == "cache_invalidated"

    def test_crag_triggered_value(self):
        """CRAG_TRIGGERED should have correct string value."""
        assert CorrectionType.CRAG_TRIGGERED == "crag_triggered"
