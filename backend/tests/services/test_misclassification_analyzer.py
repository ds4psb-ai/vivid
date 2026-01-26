"""Tests for P7 MisclassificationAnalyzer Service.

Tests for analyzing query classification misclassifications.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

# Skip all tests if dependencies unavailable
try:
    from app.services.misclassification_analyzer import (
        MisclassificationAnalyzer,
        get_misclassification_analyzer,
    )
    from app.schemas.self_correction_schemas import (
        MisclassificationType,
        MisclassifiedQuery,
        MisclassificationReport,
        QueryTypeAccuracy,
    )
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    MisclassificationAnalyzer = None
    MisclassificationType = None
    MisclassifiedQuery = None
    MisclassificationReport = None
    QueryTypeAccuracy = None


pytestmark = pytest.mark.skipif(
    not DEPS_AVAILABLE,
    reason=f"Dependencies not available: {IMPORT_ERROR if not DEPS_AVAILABLE else ''}"
)


class TestMisclassificationAnalyzerInit:
    """Tests for MisclassificationAnalyzer initialization."""

    def test_default_init(self):
        """Should initialize with default thresholds."""
        analyzer = MisclassificationAnalyzer()

        assert analyzer.NEGATIVE_RATING_THRESHOLD == 2
        assert analyzer.POSITIVE_RATING_THRESHOLD == 4
        assert analyzer.LOW_CONFIDENCE_THRESHOLD == 0.6
        assert analyzer.HIGH_LATENCY_THRESHOLD_MS == 500

    def test_singleton_pattern(self):
        """Should return singleton instance."""
        analyzer1 = get_misclassification_analyzer()
        analyzer2 = get_misclassification_analyzer()

        assert analyzer1 is analyzer2


class TestMisclassificationReport:
    """Tests for MisclassificationReport schema."""

    def test_empty_report(self):
        """Should create report with zero values."""
        report = MisclassificationReport(
            period_days=7,
            total_responses=0,
            total_with_feedback=0,
            total_misclassified=0,
            misclassification_rate=0.0,
            misclassifications_by_type={},
            accuracy_by_query_type={},
            crag_trigger_rate=0.0,
            crag_success_rate=0.0,
        )

        assert report.period_days == 7
        assert report.total_responses == 0
        assert report.misclassification_rate == 0.0
        assert report.crag_trigger_rate == 0.0
        assert report.crag_success_rate == 0.0

    def test_report_with_data(self):
        """Should create report with real data."""
        report = MisclassificationReport(
            period_days=7,
            total_responses=1000,
            total_with_feedback=100,
            total_misclassified=10,
            misclassification_rate=0.10,
            misclassifications_by_type={
                MisclassificationType.SKIP_BUT_NEGATIVE: 5,
                MisclassificationType.RETRIEVAL_BUT_CRAG: 3,
                MisclassificationType.LOW_CONFIDENCE_FAILURE: 2,
            },
            accuracy_by_query_type={},
            crag_trigger_rate=0.08,
            crag_success_rate=0.75,
            skip_retrieval_total=200,
            skip_retrieval_negative_rate=0.05,
        )

        assert report.total_responses == 1000
        assert report.total_misclassified == 10
        assert report.misclassification_rate == 0.10
        assert report.crag_trigger_rate == 0.08
        assert report.crag_success_rate == 0.75


class TestMisclassifiedQuery:
    """Tests for MisclassifiedQuery schema."""

    def test_skip_but_negative_query(self):
        """Should create skip_but_negative misclassified query."""
        query = MisclassifiedQuery(
            response_id=uuid4(),
            query="What is Python?",
            query_hash="abc123",
            predicted_type="simple_factual",
            confidence=0.9,
            classifier_used="semantic_router",
            strategy_used="direct_llm",
            retrieval_skipped=True,
            crag_triggered=False,
            latency_ms=50,
            avg_rating=2.0,
            negative_feedback_count=3,
            positive_feedback_count=0,
            misclassification_type=MisclassificationType.SKIP_BUT_NEGATIVE,
            suggested_type="domain_specific",
            analysis_reason="검색 생략 후 부정 피드백 - 검색이 필요했던 쿼리",
            created_at=datetime.utcnow(),
        )

        assert query.misclassification_type == MisclassificationType.SKIP_BUT_NEGATIVE
        assert query.retrieval_skipped is True
        assert query.negative_feedback_count == 3
        assert query.suggested_type == "domain_specific"

    def test_crag_triggered_query(self):
        """Should create retrieval_but_crag misclassified query."""
        query = MisclassifiedQuery(
            response_id=uuid4(),
            query="강주노 감독의 롱테이크 기법",
            query_hash="def456",
            predicted_type="domain_specific",
            confidence=0.85,
            classifier_used="semantic_router",
            strategy_used="ensemble_rrf",
            retrieval_skipped=False,
            crag_triggered=True,
            latency_ms=350,
            misclassification_type=MisclassificationType.RETRIEVAL_BUT_CRAG,
            created_at=datetime.utcnow(),
        )

        assert query.misclassification_type == MisclassificationType.RETRIEVAL_BUT_CRAG
        assert query.crag_triggered is True
        assert query.retrieval_skipped is False


class TestQueryTypeAccuracy:
    """Tests for QueryTypeAccuracy schema."""

    def test_high_accuracy_type(self):
        """Should calculate high accuracy."""
        accuracy = QueryTypeAccuracy(
            query_type="domain_specific",
            total_count=100,
            feedback_count=50,
            positive_count=45,
            negative_count=5,
            accuracy=0.90,
            skip_retrieval_count=0,
            skip_negative_count=0,
            crag_trigger_count=3,
            avg_latency_ms=150.0,
        )

        assert accuracy.query_type == "domain_specific"
        assert accuracy.accuracy == 0.90
        assert accuracy.total_count == 100
        assert accuracy.feedback_count == 50

    def test_low_accuracy_type(self):
        """Should calculate low accuracy with skip issues."""
        accuracy = QueryTypeAccuracy(
            query_type="simple_factual",
            total_count=50,
            feedback_count=20,
            positive_count=10,
            negative_count=10,
            accuracy=0.50,
            skip_retrieval_count=40,
            skip_negative_count=8,
            crag_trigger_count=0,
            avg_latency_ms=30.0,
        )

        assert accuracy.query_type == "simple_factual"
        assert accuracy.accuracy == 0.50
        assert accuracy.skip_retrieval_count == 40
        assert accuracy.skip_negative_count == 8


class TestRecommendationGeneration:
    """Tests for recommendation generation logic."""

    def test_generate_recommendations_high_skip_negative(self):
        """Should recommend increasing skip threshold when skip failure rate is high."""
        analyzer = MisclassificationAnalyzer()

        accuracy_by_type = {
            "simple_factual": QueryTypeAccuracy(
                query_type="simple_factual",
                total_count=100,
                feedback_count=50,
                positive_count=40,
                negative_count=10,
                accuracy=0.80,
                skip_retrieval_count=80,
                skip_negative_count=15,
                crag_trigger_count=0,
                avg_latency_ms=30.0,
            ),
        }

        threshold_changes, type_adjustments = analyzer._generate_recommendations(
            accuracy_by_type=accuracy_by_type,
            crag_trigger_rate=0.05,
            crag_success_rate=0.75,
            skip_negative_rate=0.15,  # 15% > 10% threshold
        )

        # Should recommend increasing skip threshold
        assert "skip_confidence_threshold" in threshold_changes
        assert threshold_changes["skip_confidence_threshold"] > 0

    def test_generate_recommendations_high_crag_rate(self):
        """Should recommend adjustments when CRAG rate is too high."""
        analyzer = MisclassificationAnalyzer()

        threshold_changes, type_adjustments = analyzer._generate_recommendations(
            accuracy_by_type={},
            crag_trigger_rate=0.25,  # 25% > 15% * 1.5
            crag_success_rate=0.75,
            skip_negative_rate=0.05,
        )

        # Should recommend increasing semantic threshold
        assert "semantic_threshold" in threshold_changes
        assert threshold_changes["semantic_threshold"] > 0
        assert any("CRAG 트리거율" in adj for adj in type_adjustments)

    def test_generate_recommendations_low_crag_success(self):
        """Should recommend lowering CRAG threshold when success is low."""
        analyzer = MisclassificationAnalyzer()

        threshold_changes, type_adjustments = analyzer._generate_recommendations(
            accuracy_by_type={},
            crag_trigger_rate=0.10,
            crag_success_rate=0.50,  # 50% < 60% target
            skip_negative_rate=0.05,
        )

        # Should recommend lowering CRAG relevance threshold
        assert "crag_relevance_threshold" in threshold_changes
        assert threshold_changes["crag_relevance_threshold"] < 0


class TestAnalyzePeriodMocked:
    """Tests for analyze_period with mocked database."""

    @pytest.mark.asyncio
    async def test_analyze_period_no_data(self):
        """Should return empty report when no data."""
        analyzer = MisclassificationAnalyzer()

        # Mock database session
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(
            return_value=MagicMock(scalar=MagicMock(return_value=0))
        )

        # Mock all helper methods
        with patch.object(analyzer, '_get_total_responses', return_value=0), \
             patch.object(analyzer, '_get_responses_with_feedback', return_value=0), \
             patch.object(analyzer, 'get_misclassified_queries', return_value=[]), \
             patch.object(analyzer, '_count_by_misclassification_type', return_value={t: 0 for t in MisclassificationType}), \
             patch.object(analyzer, 'calculate_query_type_accuracy', return_value={}), \
             patch.object(analyzer, '_analyze_crag', return_value=(0.0, 0.0)), \
             patch.object(analyzer, '_analyze_skip_retrieval', return_value=(0, 0.0)):

            report = await analyzer.analyze_period(mock_db, days=7)

        assert report.total_responses == 0
        assert report.total_misclassified == 0
        assert report.misclassification_rate == 0.0

    @pytest.mark.asyncio
    async def test_analyze_period_with_data(self):
        """Should return populated report when data exists."""
        analyzer = MisclassificationAnalyzer()

        mock_db = AsyncMock()

        # Create mock misclassified query
        mock_query = MisclassifiedQuery(
            response_id=uuid4(),
            query="Test query",
            query_hash="hash123",
            predicted_type="simple_factual",
            confidence=0.9,
            classifier_used="semantic_router",
            strategy_used="direct_llm",
            retrieval_skipped=True,
            crag_triggered=False,
            latency_ms=50,
            negative_feedback_count=2,
            misclassification_type=MisclassificationType.SKIP_BUT_NEGATIVE,
            created_at=datetime.utcnow(),
        )

        with patch.object(analyzer, '_get_total_responses', return_value=1000), \
             patch.object(analyzer, '_get_responses_with_feedback', return_value=100), \
             patch.object(analyzer, 'get_misclassified_queries', return_value=[mock_query]), \
             patch.object(analyzer, '_count_by_misclassification_type', return_value={
                 MisclassificationType.SKIP_BUT_NEGATIVE: 10,
                 MisclassificationType.RETRIEVAL_BUT_CRAG: 5,
                 MisclassificationType.WRONG_STRATEGY: 0,
                 MisclassificationType.LOW_CONFIDENCE_FAILURE: 3,
                 MisclassificationType.HIGH_LATENCY_SIMPLE: 2,
             }), \
             patch.object(analyzer, 'calculate_query_type_accuracy', return_value={}), \
             patch.object(analyzer, '_analyze_crag', return_value=(0.08, 0.75)), \
             patch.object(analyzer, '_analyze_skip_retrieval', return_value=(200, 0.05)):

            report = await analyzer.analyze_period(mock_db, days=7)

        assert report.total_responses == 1000
        assert report.total_with_feedback == 100
        assert report.total_misclassified == 20  # 10 + 5 + 0 + 3 + 2
        assert report.misclassification_rate == 0.20
        assert report.crag_trigger_rate == 0.08
        assert report.crag_success_rate == 0.75
        assert len(report.top_misclassified_queries) == 1


class TestMisclassificationTypes:
    """Tests for MisclassificationType enum."""

    def test_all_types_defined(self):
        """Should have all expected misclassification types."""
        expected_types = [
            "skip_but_negative",
            "retrieval_but_crag",
            "wrong_strategy",
            "low_confidence_failure",
            "high_latency_simple",
        ]

        actual_types = [t.value for t in MisclassificationType]

        for expected in expected_types:
            assert expected in actual_types, f"Missing type: {expected}"

    def test_type_values(self):
        """Should have correct string values."""
        assert MisclassificationType.SKIP_BUT_NEGATIVE.value == "skip_but_negative"
        assert MisclassificationType.RETRIEVAL_BUT_CRAG.value == "retrieval_but_crag"
        assert MisclassificationType.LOW_CONFIDENCE_FAILURE.value == "low_confidence_failure"
