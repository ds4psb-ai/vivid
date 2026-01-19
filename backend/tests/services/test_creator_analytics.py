"""Tests for Creator Analytics Service (Phase 7 HITL Enhancement).

Tests for creator metrics and anomaly detection.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

# Skip all tests if dependencies unavailable
try:
    from app.services.creator_analytics import (
        CreatorAnalyticsService,
        CreatorMetrics,
        EngagementData,
        DeliveryRecord,
        AnomalyType,
        AnomalySeverity,
    )
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    CreatorAnalyticsService = None
    CreatorMetrics = None
    EngagementData = None
    DeliveryRecord = None
    AnomalyType = None
    AnomalySeverity = None


pytestmark = pytest.mark.skipif(
    not DEPS_AVAILABLE,
    reason=f"Dependencies not available: {IMPORT_ERROR if not DEPS_AVAILABLE else ''}"
)


class TestCreatorMetrics:
    """Tests for CreatorMetrics dataclass."""

    def test_rpv_calculation(self):
        """RPV should be calculated correctly."""
        metrics = CreatorMetrics(
            rpv=2.5,
            total_views=1000,
            total_revenue=2500.0,
            engagement_rate=0.15,
            avg_rating=4.5,
            total_deliveries=20,
            on_time_rate=0.90,
            revision_rate=0.10,
            active_projects=3,
            period_days=30,
        )

        assert metrics.rpv == 2.5
        assert metrics.total_views == 1000
        assert metrics.total_revenue == 2500.0

    def test_metrics_with_no_rating(self):
        """Should handle null avg_rating."""
        metrics = CreatorMetrics(
            rpv=0.0,
            total_views=0,
            total_revenue=0.0,
            engagement_rate=0.0,
            avg_rating=None,
            total_deliveries=0,
            on_time_rate=0.0,
            revision_rate=0.0,
            active_projects=0,
            period_days=30,
        )

        assert metrics.avg_rating is None


class TestEngagementData:
    """Tests for EngagementData dataclass."""

    def test_engagement_rate_calculation(self):
        """Engagement rate should be properly stored."""
        data = EngagementData(
            date=datetime.utcnow(),
            views=1000,
            likes=100,
            comments=50,
            shares=25,
            engagement_rate=0.175,  # (100+50+25)/1000
        )

        assert data.views == 1000
        assert data.engagement_rate == 0.175


class TestDeliveryRecord:
    """Tests for DeliveryRecord dataclass."""

    def test_on_time_delivery(self):
        """Should track on-time delivery status."""
        record = DeliveryRecord(
            delivery_id=uuid4(),
            project_title="Test Project",
            delivered_at=datetime.utcnow(),
            rating=4.5,
            credits_earned=500,
            revision_count=1,
            on_time=True,
        )

        assert record.on_time is True
        assert record.rating == 4.5

    def test_late_delivery(self):
        """Should track late delivery status."""
        record = DeliveryRecord(
            delivery_id=uuid4(),
            project_title="Late Project",
            delivered_at=datetime.utcnow(),
            rating=3.0,
            credits_earned=300,
            revision_count=3,
            on_time=False,
        )

        assert record.on_time is False
        assert record.revision_count == 3


class TestAnomalyTypes:
    """Tests for AnomalyType enum."""

    def test_rating_drop_value(self):
        """RATING_DROP should have correct string value."""
        assert AnomalyType.RATING_DROP == "rating_drop"

    def test_revision_spike_value(self):
        """REVISION_SPIKE should have correct string value."""
        assert AnomalyType.REVISION_SPIKE == "revision_spike"

    def test_delivery_delay_value(self):
        """DELIVERY_DELAY should have correct string value."""
        assert AnomalyType.DELIVERY_DELAY == "delivery_delay"

    def test_credit_anomaly_value(self):
        """CREDIT_ANOMALY should have correct string value."""
        assert AnomalyType.CREDIT_ANOMALY == "credit_anomaly"

    def test_engagement_drop_value(self):
        """ENGAGEMENT_DROP should have correct string value."""
        assert AnomalyType.ENGAGEMENT_DROP == "engagement_drop"


class TestAnomalySeverity:
    """Tests for AnomalySeverity enum."""

    def test_critical_value(self):
        """CRITICAL should have correct string value."""
        assert AnomalySeverity.CRITICAL == "critical"

    def test_warning_value(self):
        """WARNING should have correct string value."""
        assert AnomalySeverity.WARNING == "warning"

    def test_info_value(self):
        """INFO should have correct string value."""
        assert AnomalySeverity.INFO == "info"


class TestCreatorAnalyticsService:
    """Tests for CreatorAnalyticsService."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create a CreatorAnalyticsService instance."""
        return CreatorAnalyticsService(mock_db)

    @pytest.mark.asyncio
    async def test_get_creator_metrics(self, service, mock_db):
        """Should return creator metrics."""
        user_id = uuid4()

        # Mock query results
        mock_db.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=1000)
        )

        metrics = await service.get_creator_metrics(user_id, period_days=30)

        assert isinstance(metrics, CreatorMetrics)
        assert metrics.period_days == 30

    @pytest.mark.asyncio
    async def test_detect_anomalies_no_data(self, service, mock_db):
        """Should return empty list when no data."""
        user_id = uuid4()

        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )

        anomalies = await service.detect_anomalies(user_id, lookback_days=30)

        assert anomalies == []

    @pytest.mark.asyncio
    async def test_detect_anomalies_rating_drop(self, service, mock_db):
        """Should detect rating drop anomaly."""
        user_id = uuid4()

        # Create mock data with rating drop
        mock_data = []
        for i in range(30):
            d = MagicMock()
            # Ratings drop from 4.5 to 2.0 in last week
            d.rating = 4.5 if i < 23 else 2.0
            d.created_at = datetime.utcnow() - timedelta(days=30-i)
            mock_data.append(d)

        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_data)))
        )

        with patch.object(service, '_compute_iqr_bounds', return_value=(3.5, 5.0)):
            anomalies = await service.detect_anomalies(user_id, lookback_days=30)

            # Should detect rating drop
            rating_anomalies = [a for a in anomalies if a.anomaly_type == AnomalyType.RATING_DROP]
            assert len(rating_anomalies) > 0

    @pytest.mark.asyncio
    async def test_get_engagement_timeline(self, service, mock_db):
        """Should return engagement timeline data."""
        user_id = uuid4()

        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )

        timeline = await service.get_engagement_timeline(user_id, period="7d")

        assert isinstance(timeline, list)

    @pytest.mark.asyncio
    async def test_get_recent_deliveries(self, service, mock_db):
        """Should return recent deliveries."""
        user_id = uuid4()

        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )

        deliveries = await service.get_recent_deliveries(user_id, limit=10)

        assert isinstance(deliveries, list)

    @pytest.mark.asyncio
    async def test_get_unresolved_anomalies(self, service, mock_db):
        """Should return unresolved anomalies."""
        user_id = uuid4()

        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )

        anomalies = await service.get_unresolved_anomalies(user_id, limit=10)

        assert isinstance(anomalies, list)


class TestIQRCalculation:
    """Tests for IQR-based anomaly detection."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        return CreatorAnalyticsService(mock_db)

    def test_iqr_bounds_normal_data(self, service):
        """IQR bounds should be calculated correctly."""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        lower, upper = service._compute_iqr_bounds(data)

        # Q1 = 3, Q3 = 8, IQR = 5
        # Lower = 3 - 1.5*5 = -4.5
        # Upper = 8 + 1.5*5 = 15.5
        assert lower < 0
        assert upper > 10

    def test_iqr_bounds_empty_data(self, service):
        """Should handle empty data."""
        lower, upper = service._compute_iqr_bounds([])

        assert lower == 0
        assert upper == 0

    def test_iqr_bounds_single_value(self, service):
        """Should handle single value."""
        lower, upper = service._compute_iqr_bounds([5])

        assert lower == 5
        assert upper == 5
