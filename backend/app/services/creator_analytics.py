"""Creator Analytics Service (Phase 7 HITL Enhancement).

크리에이터 분석 및 이상 탐지 서비스.

2026 Best Practices:
- IQR 방법: 이상치 탐지를 위한 사분위수 범위 사용
- AI 이상 탐지: 급격한 평점 하락, 비정상 수정 비율
- Creator Metrics: RPV, 참여도, 납품 시간

Usage:
    from app.services.creator_analytics import CreatorAnalyticsService

    service = CreatorAnalyticsService(db)
    anomalies = await service.detect_anomalies(creator_id)
    metrics = await service.get_creator_metrics(creator_id)
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_feedback import CreatorAnomalyLog, AnomalyType, AnomalySeverity

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class AnomalyAlert:
    """이상 탐지 알림."""
    anomaly_type: str
    severity: str
    metric_name: str
    metric_value: float
    expected_range: tuple[float, float]
    deviation_std: float
    description: str
    detected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CreatorMetrics:
    """크리에이터 메트릭."""
    creator_id: uuid.UUID
    rpv: float  # Revenue Per View
    total_views: int
    total_revenue: float
    engagement_rate: float
    avg_rating: Optional[float]
    total_deliveries: int
    on_time_rate: float
    revision_rate: float
    active_projects: int
    period_days: int


@dataclass
class EngagementData:
    """참여도 시계열 데이터."""
    date: datetime
    views: int
    likes: int
    comments: int
    shares: int
    engagement_rate: float


@dataclass
class DeliveryRecord:
    """납품 이력."""
    delivery_id: uuid.UUID
    project_title: str
    delivered_at: datetime
    rating: Optional[float]
    credits_earned: int
    revision_count: int
    on_time: bool


# =============================================================================
# Creator Analytics Service
# =============================================================================

class CreatorAnalyticsService:
    """크리에이터 분석 및 이상 탐지 서비스.

    IQR(사분위수 범위) 방법을 사용하여 이상치 탐지:
    - rating_drop: 급격한 평점 하락 (Q1 - 1.5*IQR 이하)
    - revision_spike: 비정상 수정 비율 (Q3 + 1.5*IQR 이상)
    - delivery_delay: 비정상 납품 지연
    - credit_anomaly: 크레딧 수익 급등/급락

    Attributes:
        db: 비동기 DB 세션
    """

    # IQR 기반 이상 탐지 임계값
    IQR_MULTIPLIER = 1.5  # 일반 이상치
    SEVERE_IQR_MULTIPLIER = 3.0  # 심각한 이상치

    def __init__(self, db: AsyncSession) -> None:
        """Initialize creator analytics service.

        Args:
            db: 비동기 DB 세션
        """
        self._db = db

    async def detect_anomalies(
        self,
        creator_id: uuid.UUID,
        lookback_days: int = 30,
    ) -> List[AnomalyAlert]:
        """크리에이터 이상 탐지.

        Args:
            creator_id: 크리에이터 ID
            lookback_days: 분석 기간 (일)

        Returns:
            List[AnomalyAlert]: 감지된 이상 목록
        """
        anomalies: List[AnomalyAlert] = []
        since = datetime.utcnow() - timedelta(days=lookback_days)

        # 1. 평점 이상 탐지
        rating_anomaly = await self._detect_rating_anomaly(creator_id, since)
        if rating_anomaly:
            anomalies.append(rating_anomaly)

        # 2. 수정 비율 이상 탐지
        revision_anomaly = await self._detect_revision_anomaly(creator_id, since)
        if revision_anomaly:
            anomalies.append(revision_anomaly)

        # 3. 납품 지연 이상 탐지
        delivery_anomaly = await self._detect_delivery_anomaly(creator_id, since)
        if delivery_anomaly:
            anomalies.append(delivery_anomaly)

        # 4. 크레딧 이상 탐지
        credit_anomaly = await self._detect_credit_anomaly(creator_id, since)
        if credit_anomaly:
            anomalies.append(credit_anomaly)

        # 5. 참여도 이상 탐지
        engagement_anomaly = await self._detect_engagement_anomaly(creator_id, since)
        if engagement_anomaly:
            anomalies.append(engagement_anomaly)

        # 이상 기록 저장
        for anomaly in anomalies:
            await self._log_anomaly(creator_id, anomaly)

        return anomalies

    async def _detect_rating_anomaly(
        self,
        creator_id: uuid.UUID,
        since: datetime,
    ) -> Optional[AnomalyAlert]:
        """평점 이상 탐지."""
        try:
            # Human Cloud 납품 테이블에서 평점 조회 (시뮬레이션)
            # 실제 구현 시 적절한 모델 사용
            ratings = await self._get_recent_ratings(creator_id, since)
            if len(ratings) < 5:
                return None

            current_avg = sum(ratings[-5:]) / 5
            historical_avg = sum(ratings[:-5]) / len(ratings[:-5]) if len(ratings) > 5 else current_avg

            # IQR 계산
            q1, q3 = self._calculate_quartiles(ratings)
            iqr = q3 - q1
            lower_bound = q1 - self.IQR_MULTIPLIER * iqr

            if current_avg < lower_bound:
                deviation = (historical_avg - current_avg) / (iqr or 1)
                severity = self._determine_severity(deviation)

                return AnomalyAlert(
                    anomaly_type=AnomalyType.RATING_DROP.value,
                    severity=severity,
                    metric_name="average_rating",
                    metric_value=current_avg,
                    expected_range=(lower_bound, q3 + self.IQR_MULTIPLIER * iqr),
                    deviation_std=deviation,
                    description=f"평점이 최근 5개 프로젝트에서 {current_avg:.2f}로 하락 (기준: {lower_bound:.2f})",
                )

        except Exception as e:
            logger.warning(f"Rating anomaly detection failed: {e}")

        return None

    async def _detect_revision_anomaly(
        self,
        creator_id: uuid.UUID,
        since: datetime,
    ) -> Optional[AnomalyAlert]:
        """수정 비율 이상 탐지."""
        try:
            revision_rates = await self._get_revision_rates(creator_id, since)
            if len(revision_rates) < 5:
                return None

            current_rate = revision_rates[-1] if revision_rates else 0
            q1, q3 = self._calculate_quartiles(revision_rates)
            iqr = q3 - q1
            upper_bound = q3 + self.IQR_MULTIPLIER * iqr

            if current_rate > upper_bound:
                deviation = (current_rate - q3) / (iqr or 1)
                severity = self._determine_severity(deviation)

                return AnomalyAlert(
                    anomaly_type=AnomalyType.REVISION_SPIKE.value,
                    severity=severity,
                    metric_name="revision_rate",
                    metric_value=current_rate,
                    expected_range=(q1 - self.IQR_MULTIPLIER * iqr, upper_bound),
                    deviation_std=deviation,
                    description=f"수정 비율이 {current_rate:.1%}로 급증 (기준: {upper_bound:.1%})",
                )

        except Exception as e:
            logger.warning(f"Revision anomaly detection failed: {e}")

        return None

    async def _detect_delivery_anomaly(
        self,
        creator_id: uuid.UUID,
        since: datetime,
    ) -> Optional[AnomalyAlert]:
        """납품 지연 이상 탐지."""
        try:
            delivery_times = await self._get_delivery_times(creator_id, since)
            if len(delivery_times) < 5:
                return None

            recent_avg = sum(delivery_times[-3:]) / 3 if len(delivery_times) >= 3 else delivery_times[-1]
            q1, q3 = self._calculate_quartiles(delivery_times)
            iqr = q3 - q1
            upper_bound = q3 + self.IQR_MULTIPLIER * iqr

            if recent_avg > upper_bound:
                deviation = (recent_avg - q3) / (iqr or 1)
                severity = self._determine_severity(deviation)

                return AnomalyAlert(
                    anomaly_type=AnomalyType.DELIVERY_DELAY.value,
                    severity=severity,
                    metric_name="delivery_time_hours",
                    metric_value=recent_avg,
                    expected_range=(q1 - self.IQR_MULTIPLIER * iqr, upper_bound),
                    deviation_std=deviation,
                    description=f"최근 납품 시간이 평균 {recent_avg:.1f}시간으로 지연 (기준: {upper_bound:.1f}시간)",
                )

        except Exception as e:
            logger.warning(f"Delivery anomaly detection failed: {e}")

        return None

    async def _detect_credit_anomaly(
        self,
        creator_id: uuid.UUID,
        since: datetime,
    ) -> Optional[AnomalyAlert]:
        """크레딧 수익 이상 탐지."""
        try:
            credits = await self._get_credit_history(creator_id, since)
            if len(credits) < 10:
                return None

            recent_total = sum(credits[-7:])
            historical_avg = sum(credits[:-7]) / max(len(credits) - 7, 1)

            q1, q3 = self._calculate_quartiles(credits)
            iqr = q3 - q1
            lower_bound = q1 - self.IQR_MULTIPLIER * iqr
            upper_bound = q3 + self.IQR_MULTIPLIER * iqr

            weekly_avg = recent_total / 7

            if weekly_avg < lower_bound or weekly_avg > upper_bound:
                is_drop = weekly_avg < lower_bound
                deviation = abs(weekly_avg - (q1 if is_drop else q3)) / (iqr or 1)
                severity = self._determine_severity(deviation)

                return AnomalyAlert(
                    anomaly_type=AnomalyType.CREDIT_ANOMALY.value,
                    severity=severity,
                    metric_name="daily_credits",
                    metric_value=weekly_avg,
                    expected_range=(lower_bound, upper_bound),
                    deviation_std=deviation,
                    description=f"일일 크레딧 수익이 {weekly_avg:.0f}로 {'급락' if is_drop else '급등'} (기준: {lower_bound:.0f}-{upper_bound:.0f})",
                )

        except Exception as e:
            logger.warning(f"Credit anomaly detection failed: {e}")

        return None

    async def _detect_engagement_anomaly(
        self,
        creator_id: uuid.UUID,
        since: datetime,
    ) -> Optional[AnomalyAlert]:
        """참여도 이상 탐지."""
        try:
            engagement_rates = await self._get_engagement_rates(creator_id, since)
            if len(engagement_rates) < 7:
                return None

            recent_avg = sum(engagement_rates[-7:]) / 7
            q1, q3 = self._calculate_quartiles(engagement_rates)
            iqr = q3 - q1
            lower_bound = q1 - self.IQR_MULTIPLIER * iqr

            if recent_avg < lower_bound:
                deviation = (q1 - recent_avg) / (iqr or 1)
                severity = self._determine_severity(deviation)

                return AnomalyAlert(
                    anomaly_type=AnomalyType.ENGAGEMENT_DROP.value,
                    severity=severity,
                    metric_name="engagement_rate",
                    metric_value=recent_avg,
                    expected_range=(lower_bound, q3 + self.IQR_MULTIPLIER * iqr),
                    deviation_std=deviation,
                    description=f"참여율이 {recent_avg:.2%}로 급감 (기준: {lower_bound:.2%})",
                )

        except Exception as e:
            logger.warning(f"Engagement anomaly detection failed: {e}")

        return None

    async def _log_anomaly(
        self,
        creator_id: uuid.UUID,
        anomaly: AnomalyAlert,
    ) -> CreatorAnomalyLog:
        """이상 탐지 기록 저장."""
        log = CreatorAnomalyLog(
            creator_id=creator_id,
            anomaly_type=anomaly.anomaly_type,
            severity=anomaly.severity,
            metric_name=anomaly.metric_name,
            metric_value=anomaly.metric_value,
            expected_range_low=anomaly.expected_range[0],
            expected_range_high=anomaly.expected_range[1],
            deviation_std=anomaly.deviation_std,
            description=anomaly.description,
            context={},
            detected_at=anomaly.detected_at,
        )

        self._db.add(log)
        await self._db.flush()

        return log

    # =========================================================================
    # Metrics Methods
    # =========================================================================

    async def get_creator_metrics(
        self,
        creator_id: uuid.UUID,
        period_days: int = 30,
    ) -> CreatorMetrics:
        """크리에이터 메트릭 조회.

        Args:
            creator_id: 크리에이터 ID
            period_days: 기간 (일)

        Returns:
            CreatorMetrics: 크리에이터 메트릭
        """
        since = datetime.utcnow() - timedelta(days=period_days)

        # 실제 구현 시 Human Cloud 테이블에서 조회
        # 여기서는 시뮬레이션 데이터 반환
        total_views = await self._get_total_views(creator_id, since)
        total_revenue = await self._get_total_revenue(creator_id, since)
        rpv = total_revenue / total_views if total_views > 0 else 0.0

        avg_rating = await self._get_average_rating(creator_id, since)
        total_deliveries = await self._get_delivery_count(creator_id, since)
        on_time_rate = await self._get_on_time_rate(creator_id, since)
        revision_rate = await self._get_overall_revision_rate(creator_id, since)
        active_projects = await self._get_active_project_count(creator_id)
        engagement_rate = await self._get_overall_engagement_rate(creator_id, since)

        return CreatorMetrics(
            creator_id=creator_id,
            rpv=rpv,
            total_views=total_views,
            total_revenue=total_revenue,
            engagement_rate=engagement_rate,
            avg_rating=avg_rating,
            total_deliveries=total_deliveries,
            on_time_rate=on_time_rate,
            revision_rate=revision_rate,
            active_projects=active_projects,
            period_days=period_days,
        )

    async def get_engagement_timeline(
        self,
        creator_id: uuid.UUID,
        period: str = "7d",
    ) -> List[EngagementData]:
        """참여도 시계열 조회.

        Args:
            creator_id: 크리에이터 ID
            period: 기간 (7d, 30d, 90d)

        Returns:
            List[EngagementData]: 참여도 시계열
        """
        days_map = {"7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(period, 7)

        # 시뮬레이션 데이터
        result = []
        base_date = datetime.utcnow() - timedelta(days=days)

        for i in range(days):
            date = base_date + timedelta(days=i)
            views = 100 + i * 10  # 시뮬레이션
            likes = int(views * 0.1)
            comments = int(views * 0.02)
            shares = int(views * 0.01)
            engagement = (likes + comments + shares) / views if views > 0 else 0

            result.append(EngagementData(
                date=date,
                views=views,
                likes=likes,
                comments=comments,
                shares=shares,
                engagement_rate=engagement,
            ))

        return result

    async def get_recent_deliveries(
        self,
        creator_id: uuid.UUID,
        limit: int = 10,
    ) -> List[DeliveryRecord]:
        """최근 납품 이력 조회.

        Args:
            creator_id: 크리에이터 ID
            limit: 결과 제한

        Returns:
            List[DeliveryRecord]: 납품 이력
        """
        # 시뮬레이션 데이터
        # 실제 구현 시 Human Cloud 테이블에서 조회
        result = []
        for i in range(min(limit, 5)):
            result.append(DeliveryRecord(
                delivery_id=uuid.uuid4(),
                project_title=f"프로젝트 {i + 1}",
                delivered_at=datetime.utcnow() - timedelta(days=i * 3),
                rating=4.5 - i * 0.2 if i < 3 else None,
                credits_earned=1000 - i * 100,
                revision_count=i % 3,
                on_time=i % 2 == 0,
            ))

        return result

    async def get_unresolved_anomalies(
        self,
        creator_id: uuid.UUID,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """미해결 이상 목록 조회."""
        result = await self._db.execute(
            select(CreatorAnomalyLog)
            .where(
                and_(
                    CreatorAnomalyLog.creator_id == creator_id,
                    CreatorAnomalyLog.resolved == False,
                )
            )
            .order_by(desc(CreatorAnomalyLog.detected_at))
            .limit(limit)
        )

        anomalies = list(result.scalars())
        return [
            {
                "id": str(a.id),
                "type": a.anomaly_type,
                "severity": a.severity,
                "metric_name": a.metric_name,
                "metric_value": a.metric_value,
                "expected_range": [a.expected_range_low, a.expected_range_high],
                "description": a.description,
                "detected_at": a.detected_at.isoformat(),
            }
            for a in anomalies
        ]

    # =========================================================================
    # Helper Methods (시뮬레이션 데이터)
    # =========================================================================

    def _calculate_quartiles(self, data: List[float]) -> tuple[float, float]:
        """사분위수 계산."""
        if not data:
            return 0.0, 0.0

        sorted_data = sorted(data)
        n = len(sorted_data)
        q1_idx = int(n * 0.25)
        q3_idx = int(n * 0.75)

        return sorted_data[q1_idx], sorted_data[q3_idx]

    def _determine_severity(self, deviation: float) -> str:
        """이상 심각도 결정."""
        if deviation >= 3.0:
            return AnomalySeverity.CRITICAL.value
        elif deviation >= 2.0:
            return AnomalySeverity.HIGH.value
        elif deviation >= 1.5:
            return AnomalySeverity.MEDIUM.value
        return AnomalySeverity.LOW.value

    async def _get_recent_ratings(self, creator_id: uuid.UUID, since: datetime) -> List[float]:
        """최근 평점 조회 (시뮬레이션)."""
        # 실제 구현 시 Human Cloud 테이블에서 조회
        return [4.5, 4.2, 4.8, 4.0, 4.3, 3.5, 3.8, 4.1]

    async def _get_revision_rates(self, creator_id: uuid.UUID, since: datetime) -> List[float]:
        """수정 비율 조회 (시뮬레이션)."""
        return [0.1, 0.15, 0.12, 0.08, 0.2, 0.25, 0.18]

    async def _get_delivery_times(self, creator_id: uuid.UUID, since: datetime) -> List[float]:
        """납품 시간 조회 (시뮬레이션)."""
        return [24, 36, 28, 32, 48, 72, 24, 36]

    async def _get_credit_history(self, creator_id: uuid.UUID, since: datetime) -> List[float]:
        """크레딧 수익 이력 조회 (시뮬레이션)."""
        return [100, 150, 120, 180, 90, 110, 140, 130, 160, 170, 50, 60]

    async def _get_engagement_rates(self, creator_id: uuid.UUID, since: datetime) -> List[float]:
        """참여율 조회 (시뮬레이션)."""
        return [0.08, 0.09, 0.07, 0.10, 0.06, 0.05, 0.04, 0.03, 0.02]

    async def _get_total_views(self, creator_id: uuid.UUID, since: datetime) -> int:
        """총 조회수 (시뮬레이션)."""
        return 10000

    async def _get_total_revenue(self, creator_id: uuid.UUID, since: datetime) -> float:
        """총 수익 (시뮬레이션)."""
        return 5000.0

    async def _get_average_rating(self, creator_id: uuid.UUID, since: datetime) -> Optional[float]:
        """평균 평점 (시뮬레이션)."""
        return 4.2

    async def _get_delivery_count(self, creator_id: uuid.UUID, since: datetime) -> int:
        """납품 수 (시뮬레이션)."""
        return 15

    async def _get_on_time_rate(self, creator_id: uuid.UUID, since: datetime) -> float:
        """정시 납품률 (시뮬레이션)."""
        return 0.87

    async def _get_overall_revision_rate(self, creator_id: uuid.UUID, since: datetime) -> float:
        """전체 수정률 (시뮬레이션)."""
        return 0.15

    async def _get_active_project_count(self, creator_id: uuid.UUID) -> int:
        """진행 중 프로젝트 수 (시뮬레이션)."""
        return 3

    async def _get_overall_engagement_rate(self, creator_id: uuid.UUID, since: datetime) -> float:
        """전체 참여율 (시뮬레이션)."""
        return 0.065
