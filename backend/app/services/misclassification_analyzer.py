"""P7: Misclassification Analyzer Service.

P6 피드백 데이터에서 오분류 패턴을 분석합니다.

Features:
- Skip Retrieval 했는데 rating < 3인 케이스 탐지
- CRAG 트리거율 분석
- QueryType별 성공률 계산
- 오분류 원인 분석

Usage:
    from app.services.misclassification_analyzer import MisclassificationAnalyzer

    analyzer = MisclassificationAnalyzer()
    report = await analyzer.analyze_period(db, days=7)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_feedback import RAGResponse, RAGFeedback
from app.schemas.self_correction_schemas import (
    MisclassifiedQuery,
    MisclassificationReport,
    MisclassificationType,
    QueryTypeAccuracy,
)

logger = logging.getLogger(__name__)


class MisclassificationAnalyzer:
    """오분류 분석 서비스.

    P6에서 수집한 피드백 데이터를 분석하여 P5 분류기의 오분류 패턴을 탐지합니다.

    분석 기준:
    1. skip_but_negative: 검색 생략 + 부정 피드백 (rating <= 2 or thumbs_down)
    2. retrieval_but_crag: 검색 수행 + CRAG 트리거 (검색 품질 불충분)
    3. wrong_strategy: 피드백 기반 전략 추론 오류
    4. low_confidence_failure: 낮은 신뢰도 분류 + 실패
    5. high_latency_simple: 단순 쿼리 + 고지연
    """

    # Thresholds for analysis
    NEGATIVE_RATING_THRESHOLD = 2  # rating <= 2 is negative
    POSITIVE_RATING_THRESHOLD = 4  # rating >= 4 is positive
    LOW_CONFIDENCE_THRESHOLD = 0.6
    HIGH_LATENCY_THRESHOLD_MS = 500  # ms
    SIMPLE_QUERY_TYPES = {"simple_factual", "creative"}

    def __init__(self):
        pass

    async def analyze_period(
        self,
        db: AsyncSession,
        days: int = 7,
        app_key: Optional[str] = None,
        min_feedback_count: int = 1,
    ) -> MisclassificationReport:
        """지정 기간의 오분류 분석.

        Args:
            db: Database session
            days: 분석 기간 (일)
            app_key: 앱 키 필터 (None이면 전체)
            min_feedback_count: 최소 피드백 수 (필터링)

        Returns:
            MisclassificationReport with detailed analysis
        """
        since = datetime.utcnow() - timedelta(days=days)

        # Base filter
        base_filter = RAGResponse.created_at >= since
        if app_key:
            base_filter = and_(base_filter, RAGResponse.app_key == app_key)

        # 1. Get total counts
        total_responses = await self._get_total_responses(db, base_filter)
        total_with_feedback = await self._get_responses_with_feedback(db, base_filter)

        # 2. Get misclassified queries
        misclassified_queries = await self.get_misclassified_queries(
            db, days=days, app_key=app_key, limit=100
        )

        # 3. Count by misclassification type
        misclassifications_by_type = await self._count_by_misclassification_type(
            db, base_filter
        )

        # 4. Calculate accuracy by query type
        accuracy_by_query_type = await self.calculate_query_type_accuracy(
            db, days=days, app_key=app_key
        )

        # 5. CRAG analysis
        crag_trigger_rate, crag_success_rate = await self._analyze_crag(db, base_filter)

        # 6. Skip retrieval analysis
        skip_retrieval_total, skip_negative_rate = await self._analyze_skip_retrieval(
            db, base_filter
        )

        # 7. Generate recommendations
        threshold_changes, type_adjustments = self._generate_recommendations(
            accuracy_by_query_type,
            crag_trigger_rate,
            crag_success_rate,
            skip_negative_rate,
        )

        total_misclassified = sum(misclassifications_by_type.values())

        return MisclassificationReport(
            period_days=days,
            analysis_date=datetime.utcnow(),
            total_responses=total_responses,
            total_with_feedback=total_with_feedback,
            total_misclassified=total_misclassified,
            misclassification_rate=(
                total_misclassified / total_with_feedback
                if total_with_feedback > 0
                else 0.0
            ),
            misclassifications_by_type=misclassifications_by_type,
            accuracy_by_query_type={
                qt: acc for qt, acc in accuracy_by_query_type.items()
            },
            top_misclassified_queries=misclassified_queries,
            crag_trigger_rate=crag_trigger_rate,
            crag_success_rate=crag_success_rate,
            skip_retrieval_total=skip_retrieval_total,
            skip_retrieval_negative_rate=skip_negative_rate,
            suggested_threshold_changes=threshold_changes,
            suggested_query_type_adjustments=type_adjustments,
        )

    async def get_misclassified_queries(
        self,
        db: AsyncSession,
        days: int = 7,
        app_key: Optional[str] = None,
        limit: int = 100,
    ) -> List[MisclassifiedQuery]:
        """오분류된 쿼리 목록 조회.

        Args:
            db: Database session
            days: 분석 기간 (일)
            app_key: 앱 키 필터
            limit: 최대 반환 개수

        Returns:
            List of MisclassifiedQuery objects
        """
        since = datetime.utcnow() - timedelta(days=days)
        misclassified: List[MisclassifiedQuery] = []

        # 1. Skip retrieval + negative feedback
        skip_negative = await self._get_skip_but_negative(db, since, app_key, limit // 3)
        misclassified.extend(skip_negative)

        # 2. Retrieval + CRAG triggered
        crag_triggered = await self._get_retrieval_but_crag(db, since, app_key, limit // 3)
        misclassified.extend(crag_triggered)

        # 3. Low confidence failures
        low_confidence = await self._get_low_confidence_failures(db, since, app_key, limit // 3)
        misclassified.extend(low_confidence)

        # Sort by negative feedback count (descending)
        misclassified.sort(key=lambda x: x.negative_feedback_count, reverse=True)

        return misclassified[:limit]

    async def calculate_query_type_accuracy(
        self,
        db: AsyncSession,
        days: int = 7,
        app_key: Optional[str] = None,
    ) -> Dict[str, QueryTypeAccuracy]:
        """QueryType별 정확도 계산.

        Args:
            db: Database session
            days: 분석 기간
            app_key: 앱 키 필터

        Returns:
            Dict of query_type -> QueryTypeAccuracy
        """
        since = datetime.utcnow() - timedelta(days=days)

        base_filter = RAGResponse.created_at >= since
        if app_key:
            base_filter = and_(base_filter, RAGResponse.app_key == app_key)

        # Query with feedback aggregation
        result = await db.execute(
            select(
                RAGResponse.query_type,
                func.count(func.distinct(RAGResponse.id)).label("total"),
                func.count(func.distinct(RAGFeedback.id)).label("feedback_count"),
                func.count(
                    func.distinct(
                        case(
                            (
                                or_(
                                    RAGFeedback.rating >= self.POSITIVE_RATING_THRESHOLD,
                                    RAGFeedback.feedback_type == "thumbs_up",
                                ),
                                RAGFeedback.id,
                            )
                        )
                    )
                ).label("positive_count"),
                func.count(
                    func.distinct(
                        case(
                            (
                                or_(
                                    RAGFeedback.rating <= self.NEGATIVE_RATING_THRESHOLD,
                                    RAGFeedback.feedback_type == "thumbs_down",
                                ),
                                RAGFeedback.id,
                            )
                        )
                    )
                ).label("negative_count"),
                func.count(
                    func.distinct(
                        case(
                            (RAGResponse.retrieval_skipped == True, RAGResponse.id)  # noqa
                        )
                    )
                ).label("skip_count"),
                func.count(
                    func.distinct(
                        case(
                            (RAGResponse.crag_triggered == True, RAGResponse.id)  # noqa
                        )
                    )
                ).label("crag_count"),
                func.avg(RAGResponse.latency_ms).label("avg_latency"),
            )
            .select_from(RAGResponse)
            .outerjoin(RAGFeedback, RAGFeedback.response_id == RAGResponse.id)
            .where(base_filter)
            .group_by(RAGResponse.query_type)
        )

        accuracy_by_type: Dict[str, QueryTypeAccuracy] = {}

        for row in result.all():
            query_type = row.query_type or "unknown"
            total = row.total or 0
            feedback_count = row.feedback_count or 0
            positive_count = row.positive_count or 0
            negative_count = row.negative_count or 0

            # Calculate skip_negative_count separately for accuracy
            skip_negative = await self._count_skip_negative_for_type(
                db, query_type, since, app_key
            )

            accuracy_by_type[query_type] = QueryTypeAccuracy(
                query_type=query_type,
                total_count=total,
                feedback_count=feedback_count,
                positive_count=positive_count,
                negative_count=negative_count,
                accuracy=(
                    positive_count / feedback_count
                    if feedback_count > 0
                    else 0.0
                ),
                skip_retrieval_count=row.skip_count or 0,
                skip_negative_count=skip_negative,
                crag_trigger_count=row.crag_count or 0,
                avg_latency_ms=float(row.avg_latency or 0),
            )

        return accuracy_by_type

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    async def _get_total_responses(
        self,
        db: AsyncSession,
        base_filter,
    ) -> int:
        """Get total response count."""
        result = await db.execute(
            select(func.count(RAGResponse.id)).where(base_filter)
        )
        return result.scalar() or 0

    async def _get_responses_with_feedback(
        self,
        db: AsyncSession,
        base_filter,
    ) -> int:
        """Get count of responses with at least one feedback."""
        result = await db.execute(
            select(func.count(func.distinct(RAGFeedback.response_id)))
            .select_from(RAGFeedback)
            .join(RAGResponse)
            .where(base_filter)
        )
        return result.scalar() or 0

    async def _count_by_misclassification_type(
        self,
        db: AsyncSession,
        base_filter,
    ) -> Dict[MisclassificationType, int]:
        """Count misclassifications by type."""
        counts: Dict[MisclassificationType, int] = {
            t: 0 for t in MisclassificationType
        }

        # Skip but negative
        skip_neg_result = await db.execute(
            select(func.count(func.distinct(RAGResponse.id)))
            .select_from(RAGResponse)
            .join(RAGFeedback, RAGFeedback.response_id == RAGResponse.id)
            .where(
                and_(
                    base_filter,
                    RAGResponse.retrieval_skipped == True,  # noqa
                    or_(
                        RAGFeedback.rating <= self.NEGATIVE_RATING_THRESHOLD,
                        RAGFeedback.feedback_type == "thumbs_down",
                    ),
                )
            )
        )
        counts[MisclassificationType.SKIP_BUT_NEGATIVE] = skip_neg_result.scalar() or 0

        # Retrieval but CRAG
        crag_result = await db.execute(
            select(func.count(func.distinct(RAGResponse.id)))
            .where(
                and_(
                    base_filter,
                    RAGResponse.retrieval_skipped == False,  # noqa
                    RAGResponse.crag_triggered == True,  # noqa
                )
            )
        )
        counts[MisclassificationType.RETRIEVAL_BUT_CRAG] = crag_result.scalar() or 0

        # Low confidence failures
        low_conf_result = await db.execute(
            select(func.count(func.distinct(RAGResponse.id)))
            .select_from(RAGResponse)
            .join(RAGFeedback, RAGFeedback.response_id == RAGResponse.id)
            .where(
                and_(
                    base_filter,
                    RAGResponse.classification_confidence < self.LOW_CONFIDENCE_THRESHOLD,
                    or_(
                        RAGFeedback.rating <= self.NEGATIVE_RATING_THRESHOLD,
                        RAGFeedback.feedback_type == "thumbs_down",
                    ),
                )
            )
        )
        counts[MisclassificationType.LOW_CONFIDENCE_FAILURE] = low_conf_result.scalar() or 0

        # High latency simple
        latency_result = await db.execute(
            select(func.count(func.distinct(RAGResponse.id)))
            .where(
                and_(
                    base_filter,
                    RAGResponse.query_type.in_(self.SIMPLE_QUERY_TYPES),
                    RAGResponse.latency_ms > self.HIGH_LATENCY_THRESHOLD_MS,
                )
            )
        )
        counts[MisclassificationType.HIGH_LATENCY_SIMPLE] = latency_result.scalar() or 0

        return counts

    async def _analyze_crag(
        self,
        db: AsyncSession,
        base_filter,
    ) -> Tuple[float, float]:
        """Analyze CRAG trigger rate and success rate."""
        # Total with retrieval
        total_result = await db.execute(
            select(func.count(RAGResponse.id))
            .where(and_(base_filter, RAGResponse.retrieval_skipped == False))  # noqa
        )
        total_with_retrieval = total_result.scalar() or 0

        # CRAG triggered count
        crag_result = await db.execute(
            select(func.count(RAGResponse.id))
            .where(and_(base_filter, RAGResponse.crag_triggered == True))  # noqa
        )
        crag_count = crag_result.scalar() or 0

        crag_trigger_rate = (
            crag_count / total_with_retrieval
            if total_with_retrieval > 0
            else 0.0
        )

        # CRAG success rate (positive feedback after CRAG)
        crag_positive = await db.execute(
            select(func.count(func.distinct(RAGResponse.id)))
            .select_from(RAGResponse)
            .join(RAGFeedback, RAGFeedback.response_id == RAGResponse.id)
            .where(
                and_(
                    base_filter,
                    RAGResponse.crag_triggered == True,  # noqa
                    or_(
                        RAGFeedback.rating >= self.POSITIVE_RATING_THRESHOLD,
                        RAGFeedback.feedback_type == "thumbs_up",
                    ),
                )
            )
        )
        crag_positive_count = crag_positive.scalar() or 0

        crag_feedback_result = await db.execute(
            select(func.count(func.distinct(RAGResponse.id)))
            .select_from(RAGResponse)
            .join(RAGFeedback, RAGFeedback.response_id == RAGResponse.id)
            .where(and_(base_filter, RAGResponse.crag_triggered == True))  # noqa
        )
        crag_feedback_count = crag_feedback_result.scalar() or 0

        crag_success_rate = (
            crag_positive_count / crag_feedback_count
            if crag_feedback_count > 0
            else 0.0
        )

        return crag_trigger_rate, crag_success_rate

    async def _analyze_skip_retrieval(
        self,
        db: AsyncSession,
        base_filter,
    ) -> Tuple[int, float]:
        """Analyze skip retrieval negative rate."""
        # Total skip retrieval
        total_result = await db.execute(
            select(func.count(RAGResponse.id))
            .where(and_(base_filter, RAGResponse.retrieval_skipped == True))  # noqa
        )
        skip_total = total_result.scalar() or 0

        # Skip with negative feedback
        negative_result = await db.execute(
            select(func.count(func.distinct(RAGResponse.id)))
            .select_from(RAGResponse)
            .join(RAGFeedback, RAGFeedback.response_id == RAGResponse.id)
            .where(
                and_(
                    base_filter,
                    RAGResponse.retrieval_skipped == True,  # noqa
                    or_(
                        RAGFeedback.rating <= self.NEGATIVE_RATING_THRESHOLD,
                        RAGFeedback.feedback_type == "thumbs_down",
                    ),
                )
            )
        )
        negative_count = negative_result.scalar() or 0

        # Skip with any feedback (denominator)
        with_feedback_result = await db.execute(
            select(func.count(func.distinct(RAGResponse.id)))
            .select_from(RAGResponse)
            .join(RAGFeedback, RAGFeedback.response_id == RAGResponse.id)
            .where(and_(base_filter, RAGResponse.retrieval_skipped == True))  # noqa
        )
        with_feedback = with_feedback_result.scalar() or 0

        negative_rate = (
            negative_count / with_feedback
            if with_feedback > 0
            else 0.0
        )

        return skip_total, negative_rate

    async def _get_skip_but_negative(
        self,
        db: AsyncSession,
        since: datetime,
        app_key: Optional[str],
        limit: int,
    ) -> List[MisclassifiedQuery]:
        """Get queries that skipped retrieval but got negative feedback."""
        base_filter = RAGResponse.created_at >= since
        if app_key:
            base_filter = and_(base_filter, RAGResponse.app_key == app_key)

        result = await db.execute(
            select(
                RAGResponse,
                func.avg(RAGFeedback.rating).label("avg_rating"),
                func.count(
                    case(
                        (
                            or_(
                                RAGFeedback.rating <= self.NEGATIVE_RATING_THRESHOLD,
                                RAGFeedback.feedback_type == "thumbs_down",
                            ),
                            RAGFeedback.id,
                        )
                    )
                ).label("neg_count"),
                func.count(
                    case(
                        (
                            or_(
                                RAGFeedback.rating >= self.POSITIVE_RATING_THRESHOLD,
                                RAGFeedback.feedback_type == "thumbs_up",
                            ),
                            RAGFeedback.id,
                        )
                    )
                ).label("pos_count"),
            )
            .select_from(RAGResponse)
            .join(RAGFeedback, RAGFeedback.response_id == RAGResponse.id)
            .where(
                and_(
                    base_filter,
                    RAGResponse.retrieval_skipped == True,  # noqa
                    or_(
                        RAGFeedback.rating <= self.NEGATIVE_RATING_THRESHOLD,
                        RAGFeedback.feedback_type == "thumbs_down",
                    ),
                )
            )
            .group_by(RAGResponse.id)
            .order_by(func.count(RAGFeedback.id).desc())
            .limit(limit)
        )

        queries = []
        for row in result.all():
            resp = row[0]
            queries.append(
                MisclassifiedQuery(
                    response_id=resp.id,
                    query=resp.query,
                    query_hash=resp.query_hash,
                    predicted_type=resp.query_type or "unknown",
                    confidence=resp.classification_confidence or 0.0,
                    classifier_used=resp.classifier_used or "unknown",
                    strategy_used=resp.strategy_used or "unknown",
                    retrieval_skipped=resp.retrieval_skipped,
                    crag_triggered=resp.crag_triggered,
                    latency_ms=resp.latency_ms or 0,
                    avg_rating=float(row.avg_rating) if row.avg_rating else None,
                    negative_feedback_count=row.neg_count or 0,
                    positive_feedback_count=row.pos_count or 0,
                    misclassification_type=MisclassificationType.SKIP_BUT_NEGATIVE,
                    suggested_type="domain_specific",  # Should have retrieved
                    analysis_reason="검색 생략 후 부정 피드백 - 검색이 필요했던 쿼리",
                    dimension=resp.dimension,
                    auteur_key=resp.auteur_key,
                    created_at=resp.created_at,
                )
            )

        return queries

    async def _get_retrieval_but_crag(
        self,
        db: AsyncSession,
        since: datetime,
        app_key: Optional[str],
        limit: int,
    ) -> List[MisclassifiedQuery]:
        """Get queries that performed retrieval but triggered CRAG."""
        base_filter = RAGResponse.created_at >= since
        if app_key:
            base_filter = and_(base_filter, RAGResponse.app_key == app_key)

        result = await db.execute(
            select(
                RAGResponse,
                func.avg(RAGFeedback.rating).label("avg_rating"),
                func.count(
                    case(
                        (
                            or_(
                                RAGFeedback.rating <= self.NEGATIVE_RATING_THRESHOLD,
                                RAGFeedback.feedback_type == "thumbs_down",
                            ),
                            RAGFeedback.id,
                        )
                    )
                ).label("neg_count"),
                func.count(
                    case(
                        (
                            or_(
                                RAGFeedback.rating >= self.POSITIVE_RATING_THRESHOLD,
                                RAGFeedback.feedback_type == "thumbs_up",
                            ),
                            RAGFeedback.id,
                        )
                    )
                ).label("pos_count"),
            )
            .select_from(RAGResponse)
            .outerjoin(RAGFeedback, RAGFeedback.response_id == RAGResponse.id)
            .where(
                and_(
                    base_filter,
                    RAGResponse.retrieval_skipped == False,  # noqa
                    RAGResponse.crag_triggered == True,  # noqa
                )
            )
            .group_by(RAGResponse.id)
            .order_by(RAGResponse.created_at.desc())
            .limit(limit)
        )

        queries = []
        for row in result.all():
            resp = row[0]
            queries.append(
                MisclassifiedQuery(
                    response_id=resp.id,
                    query=resp.query,
                    query_hash=resp.query_hash,
                    predicted_type=resp.query_type or "unknown",
                    confidence=resp.classification_confidence or 0.0,
                    classifier_used=resp.classifier_used or "unknown",
                    strategy_used=resp.strategy_used or "unknown",
                    retrieval_skipped=resp.retrieval_skipped,
                    crag_triggered=resp.crag_triggered,
                    latency_ms=resp.latency_ms or 0,
                    avg_rating=float(row.avg_rating) if row.avg_rating else None,
                    negative_feedback_count=row.neg_count or 0,
                    positive_feedback_count=row.pos_count or 0,
                    misclassification_type=MisclassificationType.RETRIEVAL_BUT_CRAG,
                    suggested_type="multi_hop",  # May need full pipeline
                    analysis_reason="검색 수행 후 CRAG 트리거 - 검색 품질 불충분 또는 전략 불일치",
                    dimension=resp.dimension,
                    auteur_key=resp.auteur_key,
                    created_at=resp.created_at,
                )
            )

        return queries

    async def _get_low_confidence_failures(
        self,
        db: AsyncSession,
        since: datetime,
        app_key: Optional[str],
        limit: int,
    ) -> List[MisclassifiedQuery]:
        """Get queries with low confidence that got negative feedback."""
        base_filter = RAGResponse.created_at >= since
        if app_key:
            base_filter = and_(base_filter, RAGResponse.app_key == app_key)

        result = await db.execute(
            select(
                RAGResponse,
                func.avg(RAGFeedback.rating).label("avg_rating"),
                func.count(
                    case(
                        (
                            or_(
                                RAGFeedback.rating <= self.NEGATIVE_RATING_THRESHOLD,
                                RAGFeedback.feedback_type == "thumbs_down",
                            ),
                            RAGFeedback.id,
                        )
                    )
                ).label("neg_count"),
                func.count(
                    case(
                        (
                            or_(
                                RAGFeedback.rating >= self.POSITIVE_RATING_THRESHOLD,
                                RAGFeedback.feedback_type == "thumbs_up",
                            ),
                            RAGFeedback.id,
                        )
                    )
                ).label("pos_count"),
            )
            .select_from(RAGResponse)
            .join(RAGFeedback, RAGFeedback.response_id == RAGResponse.id)
            .where(
                and_(
                    base_filter,
                    RAGResponse.classification_confidence < self.LOW_CONFIDENCE_THRESHOLD,
                    or_(
                        RAGFeedback.rating <= self.NEGATIVE_RATING_THRESHOLD,
                        RAGFeedback.feedback_type == "thumbs_down",
                    ),
                )
            )
            .group_by(RAGResponse.id)
            .order_by(RAGResponse.classification_confidence)
            .limit(limit)
        )

        queries = []
        for row in result.all():
            resp = row[0]
            queries.append(
                MisclassifiedQuery(
                    response_id=resp.id,
                    query=resp.query,
                    query_hash=resp.query_hash,
                    predicted_type=resp.query_type or "unknown",
                    confidence=resp.classification_confidence or 0.0,
                    classifier_used=resp.classifier_used or "unknown",
                    strategy_used=resp.strategy_used or "unknown",
                    retrieval_skipped=resp.retrieval_skipped,
                    crag_triggered=resp.crag_triggered,
                    latency_ms=resp.latency_ms or 0,
                    avg_rating=float(row.avg_rating) if row.avg_rating else None,
                    negative_feedback_count=row.neg_count or 0,
                    positive_feedback_count=row.pos_count or 0,
                    misclassification_type=MisclassificationType.LOW_CONFIDENCE_FAILURE,
                    suggested_type=None,  # Needs manual analysis
                    analysis_reason=f"낮은 분류 신뢰도({resp.classification_confidence:.2f}) + 부정 피드백",
                    dimension=resp.dimension,
                    auteur_key=resp.auteur_key,
                    created_at=resp.created_at,
                )
            )

        return queries

    async def _count_skip_negative_for_type(
        self,
        db: AsyncSession,
        query_type: str,
        since: datetime,
        app_key: Optional[str],
    ) -> int:
        """Count skip retrieval + negative feedback for a specific query type."""
        base_filter = and_(
            RAGResponse.created_at >= since,
            RAGResponse.query_type == query_type,
        )
        if app_key:
            base_filter = and_(base_filter, RAGResponse.app_key == app_key)

        result = await db.execute(
            select(func.count(func.distinct(RAGResponse.id)))
            .select_from(RAGResponse)
            .join(RAGFeedback, RAGFeedback.response_id == RAGResponse.id)
            .where(
                and_(
                    base_filter,
                    RAGResponse.retrieval_skipped == True,  # noqa
                    or_(
                        RAGFeedback.rating <= self.NEGATIVE_RATING_THRESHOLD,
                        RAGFeedback.feedback_type == "thumbs_down",
                    ),
                )
            )
        )
        return result.scalar() or 0

    def _generate_recommendations(
        self,
        accuracy_by_type: Dict[str, QueryTypeAccuracy],
        crag_trigger_rate: float,
        crag_success_rate: float,
        skip_negative_rate: float,
    ) -> Tuple[Dict[str, float], List[str]]:
        """Generate threshold and type adjustment recommendations."""
        threshold_changes: Dict[str, float] = {}
        type_adjustments: List[str] = []

        # Skip retrieval is failing too often
        if skip_negative_rate > 0.10:  # > 10% failure
            threshold_changes["skip_confidence_threshold"] = 0.05  # Increase
            type_adjustments.append(
                "검색 생략 실패율이 높음 - skip_confidence_threshold 상향 권장"
            )

        # CRAG triggering too often (inefficient retrieval)
        if crag_trigger_rate > 0.15:  # > 15%
            threshold_changes["semantic_threshold"] = 0.03
            type_adjustments.append(
                "CRAG 트리거율이 높음 - 검색 전략 개선 또는 semantic_threshold 상향 권장"
            )

        # CRAG success rate low (CRAG not helping)
        if crag_success_rate < 0.60 and crag_trigger_rate > 0.05:
            threshold_changes["crag_relevance_threshold"] = -0.05  # Lower
            type_adjustments.append(
                "CRAG 성공률이 낮음 - CRAG relevance threshold 하향 권장"
            )

        # Check individual query types
        for query_type, acc in accuracy_by_type.items():
            if acc.feedback_count < 10:
                continue  # Not enough data

            if acc.accuracy < 0.70:  # < 70% accuracy
                type_adjustments.append(
                    f"'{query_type}' 정확도 낮음({acc.accuracy:.0%}) - "
                    "분류 예시 추가 또는 프롬프트 개선 권장"
                )

            if acc.skip_negative_count > 0 and acc.skip_retrieval_count > 0:
                skip_fail_rate = acc.skip_negative_count / acc.skip_retrieval_count
                if skip_fail_rate > 0.15:
                    type_adjustments.append(
                        f"'{query_type}' 검색 생략 실패율 높음({skip_fail_rate:.0%}) - "
                        "해당 타입 검색 생략 제외 고려"
                    )

        return threshold_changes, type_adjustments


# =============================================================================
# Singleton Instance
# =============================================================================


_analyzer: Optional[MisclassificationAnalyzer] = None


def get_misclassification_analyzer() -> MisclassificationAnalyzer:
    """Get or create singleton MisclassificationAnalyzer."""
    global _analyzer
    if _analyzer is None:
        _analyzer = MisclassificationAnalyzer()
    return _analyzer
