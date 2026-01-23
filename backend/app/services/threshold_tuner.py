"""P7: Threshold Tuner Service.

피드백 기반으로 P5 분류 임계값을 자동 조정합니다.

Tunable Thresholds:
- semantic_threshold: SemanticRouter 최소 신뢰도
- skip_confidence_threshold: 검색 생략 최소 신뢰도
- reranker_min_score: Reranker 최소 점수
- crag_relevance_threshold: CRAG 트리거 임계값
- llm_fallback_threshold: LLM 분류기 폴백 임계값

Usage:
    from app.services.threshold_tuner import ThresholdTuner

    tuner = ThresholdTuner()
    new_config = await tuner.optimize_thresholds(db, feedback_data)
    experiment_key = await tuner.run_threshold_experiment(db, new_config)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_feedback import RAGResponse, RAGFeedback
from app.schemas.self_correction_schemas import (
    MisclassificationReport,
    ThresholdConfig,
    ThresholdTuningResult,
)

logger = logging.getLogger(__name__)


class ThresholdTuner:
    """임계값 튜닝 서비스.

    P6 피드백 데이터와 오분류 분석 결과를 기반으로
    P5 분류 임계값을 자동 조정합니다.

    Optimization Strategy:
    1. Skip Retrieval Failures → 증가 skip_confidence_threshold
    2. High CRAG Trigger Rate → 조정 semantic_threshold
    3. Low CRAG Success → 조정 crag_relevance_threshold
    4. Low Confidence Failures → 조정 llm_fallback_threshold
    """

    # Default thresholds
    DEFAULT_CONFIG = ThresholdConfig(
        semantic_threshold=0.7,
        skip_confidence_threshold=0.85,
        reranker_min_score=0.5,
        crag_relevance_threshold=0.6,
        llm_fallback_threshold=0.5,
    )

    # Tuning parameters
    MAX_ADJUSTMENT = 0.10  # Maximum adjustment per tuning cycle
    MIN_THRESHOLD = 0.3
    MAX_THRESHOLD = 0.95

    # Target metrics
    TARGET_SKIP_NEGATIVE_RATE = 0.05  # < 5% negative after skip
    TARGET_CRAG_TRIGGER_RATE = 0.08  # ~8% CRAG triggers
    TARGET_CRAG_SUCCESS_RATE = 0.75  # > 75% positive after CRAG

    def __init__(
        self,
        current_config: Optional[ThresholdConfig] = None,
    ):
        self._current_config = current_config or ThresholdConfig()

    async def optimize_thresholds(
        self,
        db: AsyncSession,
        days: int = 7,
        app_key: Optional[str] = None,
        report: Optional[MisclassificationReport] = None,
    ) -> ThresholdConfig:
        """피드백 기반 최적 임계값 계산.

        Args:
            db: Database session
            days: 분석 기간
            app_key: 앱 키 필터
            report: 이미 계산된 MisclassificationReport (선택)

        Returns:
            최적화된 ThresholdConfig
        """
        # Get metrics if report not provided
        if report is None:
            metrics = await self._gather_metrics(db, days, app_key)
        else:
            metrics = {
                "skip_negative_rate": report.skip_retrieval_negative_rate,
                "crag_trigger_rate": report.crag_trigger_rate,
                "crag_success_rate": report.crag_success_rate,
                "total_responses": report.total_responses,
                "total_with_feedback": report.total_with_feedback,
            }

        # Calculate adjustments
        adjustments = self._calculate_adjustments(metrics)

        # Apply adjustments to create new config
        new_config = self._apply_adjustments(adjustments)

        logger.info(f"[ThresholdTuner] Optimized thresholds: {adjustments}")
        return new_config

    async def run_threshold_experiment(
        self,
        db: AsyncSession,
        new_config: ThresholdConfig,
        experiment_traffic: float = 0.1,
    ) -> Optional[str]:
        """새 임계값으로 A/B 테스트 시작.

        Args:
            db: Database session
            new_config: 새 임계값 설정
            experiment_traffic: 트래픽 비율 (0.0-1.0)

        Returns:
            Experiment key if created, None otherwise
        """
        try:
            from app.experiments.models import (
                Experiment,
                ExperimentVariant,
                ExperimentStatus,
            )

            # Generate experiment key
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            experiment_key = f"p7_threshold_tuning_{timestamp}"

            # Create experiment
            experiment = Experiment(
                experiment_key=experiment_key,
                name=f"P7 Threshold Tuning {timestamp}",
                description="Automated threshold tuning experiment from P7 Self-Correction",
                hypothesis="Optimized thresholds will improve classification accuracy",
                status=ExperimentStatus.RUNNING,
                start_date=datetime.utcnow(),
                traffic_percentage=experiment_traffic * 100,
                primary_metric="classification_accuracy",
                secondary_metrics=[
                    "skip_negative_rate",
                    "crag_trigger_rate",
                    "crag_success_rate",
                    "avg_latency_ms",
                ],
                min_sample_size=200,
                confidence_level=0.95,
                min_detectable_effect=0.03,
                owner="p7_self_correction",
                tags=["p7", "threshold_tuning", "automated"],
            )
            db.add(experiment)
            await db.flush()

            # Create control variant (current config)
            control = ExperimentVariant(
                experiment_id=experiment.id,
                name="control",
                description="Current threshold configuration",
                weight=50.0,
                is_control=True,
                payload=self._current_config.model_dump(),
            )
            db.add(control)

            # Create treatment variant (new config)
            treatment = ExperimentVariant(
                experiment_id=experiment.id,
                name="treatment",
                description="Optimized threshold configuration",
                weight=50.0,
                is_control=False,
                payload=new_config.model_dump(),
            )
            db.add(treatment)

            await db.commit()
            logger.info(f"[ThresholdTuner] Created A/B experiment: {experiment_key}")
            return experiment_key

        except Exception as e:
            logger.error(f"[ThresholdTuner] Failed to create experiment: {e}")
            await db.rollback()
            return None

    async def run_full_tuning(
        self,
        db: AsyncSession,
        days: int = 7,
        app_key: Optional[str] = None,
        report: Optional[MisclassificationReport] = None,
        auto_experiment: bool = True,
        experiment_traffic: float = 0.1,
    ) -> ThresholdTuningResult:
        """전체 튜닝 파이프라인 실행.

        Args:
            db: Database session
            days: 분석 기간
            app_key: 앱 키 필터
            report: 이미 계산된 MisclassificationReport
            auto_experiment: 자동 A/B 테스트 시작 여부
            experiment_traffic: 트래픽 비율

        Returns:
            ThresholdTuningResult with full details
        """
        # 1. Optimize thresholds
        new_config = await self.optimize_thresholds(db, days, app_key, report)

        # 2. Calculate changes
        changes = self._calculate_changes(self._current_config, new_config)

        # 3. Generate rationale
        rationale = self._generate_rationale(changes, report)

        # 4. Estimate expected improvement
        expected_improvement = self._estimate_improvement(changes, report)

        # 5. Optionally run experiment
        experiment_key = None
        if auto_experiment:
            experiment_key = await self.run_threshold_experiment(
                db, new_config, experiment_traffic
            )

        return ThresholdTuningResult(
            previous_config=self._current_config,
            new_config=new_config,
            changes=changes,
            rationale=rationale,
            expected_improvement=expected_improvement,
            experiment_key=experiment_key,
        )

    def apply_config(self, config: ThresholdConfig) -> None:
        """새 설정 적용 (성공적인 실험 후).

        Args:
            config: 적용할 ThresholdConfig
        """
        self._current_config = config
        logger.info(f"[ThresholdTuner] Applied new config: {config.model_dump()}")

    def get_current_config(self) -> ThresholdConfig:
        """현재 임계값 설정 반환."""
        return self._current_config

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    async def _gather_metrics(
        self,
        db: AsyncSession,
        days: int,
        app_key: Optional[str],
    ) -> Dict[str, float]:
        """Gather metrics from database."""
        since = datetime.utcnow() - timedelta(days=days)

        base_filter = RAGResponse.created_at >= since
        if app_key:
            base_filter = and_(base_filter, RAGResponse.app_key == app_key)

        # Total responses
        total_result = await db.execute(
            select(func.count(RAGResponse.id)).where(base_filter)
        )
        total_responses = total_result.scalar() or 0

        # Skip retrieval metrics
        skip_result = await db.execute(
            select(func.count(RAGResponse.id))
            .where(and_(base_filter, RAGResponse.retrieval_skipped == True))  # noqa
        )
        skip_total = skip_result.scalar() or 0

        # Skip with negative feedback
        skip_negative_result = await db.execute(
            select(func.count(func.distinct(RAGResponse.id)))
            .select_from(RAGResponse)
            .join(RAGFeedback, RAGFeedback.response_id == RAGResponse.id)
            .where(
                and_(
                    base_filter,
                    RAGResponse.retrieval_skipped == True,  # noqa
                    or_(
                        RAGFeedback.rating <= 2,
                        RAGFeedback.feedback_type == "thumbs_down",
                    ),
                )
            )
        )
        skip_negative_count = skip_negative_result.scalar() or 0

        # Skip with any feedback
        skip_feedback_result = await db.execute(
            select(func.count(func.distinct(RAGResponse.id)))
            .select_from(RAGResponse)
            .join(RAGFeedback, RAGFeedback.response_id == RAGResponse.id)
            .where(and_(base_filter, RAGResponse.retrieval_skipped == True))  # noqa
        )
        skip_with_feedback = skip_feedback_result.scalar() or 0

        skip_negative_rate = (
            skip_negative_count / skip_with_feedback
            if skip_with_feedback > 0
            else 0.0
        )

        # CRAG metrics
        retrieval_result = await db.execute(
            select(func.count(RAGResponse.id))
            .where(and_(base_filter, RAGResponse.retrieval_skipped == False))  # noqa
        )
        retrieval_total = retrieval_result.scalar() or 0

        crag_result = await db.execute(
            select(func.count(RAGResponse.id))
            .where(and_(base_filter, RAGResponse.crag_triggered == True))  # noqa
        )
        crag_count = crag_result.scalar() or 0

        crag_trigger_rate = (
            crag_count / retrieval_total if retrieval_total > 0 else 0.0
        )

        # CRAG success (positive feedback after CRAG)
        crag_positive_result = await db.execute(
            select(func.count(func.distinct(RAGResponse.id)))
            .select_from(RAGResponse)
            .join(RAGFeedback, RAGFeedback.response_id == RAGResponse.id)
            .where(
                and_(
                    base_filter,
                    RAGResponse.crag_triggered == True,  # noqa
                    or_(
                        RAGFeedback.rating >= 4,
                        RAGFeedback.feedback_type == "thumbs_up",
                    ),
                )
            )
        )
        crag_positive = crag_positive_result.scalar() or 0

        crag_feedback_result = await db.execute(
            select(func.count(func.distinct(RAGResponse.id)))
            .select_from(RAGResponse)
            .join(RAGFeedback, RAGFeedback.response_id == RAGResponse.id)
            .where(and_(base_filter, RAGResponse.crag_triggered == True))  # noqa
        )
        crag_with_feedback = crag_feedback_result.scalar() or 0

        crag_success_rate = (
            crag_positive / crag_with_feedback if crag_with_feedback > 0 else 0.0
        )

        # Low confidence metrics
        low_conf_result = await db.execute(
            select(func.count(RAGResponse.id))
            .where(
                and_(
                    base_filter,
                    RAGResponse.classification_confidence < 0.6,
                )
            )
        )
        low_conf_total = low_conf_result.scalar() or 0

        low_conf_failure_result = await db.execute(
            select(func.count(func.distinct(RAGResponse.id)))
            .select_from(RAGResponse)
            .join(RAGFeedback, RAGFeedback.response_id == RAGResponse.id)
            .where(
                and_(
                    base_filter,
                    RAGResponse.classification_confidence < 0.6,
                    or_(
                        RAGFeedback.rating <= 2,
                        RAGFeedback.feedback_type == "thumbs_down",
                    ),
                )
            )
        )
        low_conf_failures = low_conf_failure_result.scalar() or 0

        low_conf_failure_rate = (
            low_conf_failures / low_conf_total if low_conf_total > 0 else 0.0
        )

        # With feedback count
        with_feedback_result = await db.execute(
            select(func.count(func.distinct(RAGFeedback.response_id)))
            .select_from(RAGFeedback)
            .join(RAGResponse)
            .where(base_filter)
        )
        total_with_feedback = with_feedback_result.scalar() or 0

        return {
            "total_responses": total_responses,
            "total_with_feedback": total_with_feedback,
            "skip_total": skip_total,
            "skip_negative_rate": skip_negative_rate,
            "retrieval_total": retrieval_total,
            "crag_trigger_rate": crag_trigger_rate,
            "crag_success_rate": crag_success_rate,
            "low_conf_failure_rate": low_conf_failure_rate,
        }

    def _calculate_adjustments(
        self,
        metrics: Dict[str, float],
    ) -> Dict[str, float]:
        """Calculate threshold adjustments based on metrics."""
        adjustments: Dict[str, float] = {}

        # 1. Skip confidence threshold
        skip_negative_rate = metrics.get("skip_negative_rate", 0.0)
        if skip_negative_rate > self.TARGET_SKIP_NEGATIVE_RATE:
            # Negative feedback too high → increase threshold
            delta = min(
                self.MAX_ADJUSTMENT,
                (skip_negative_rate - self.TARGET_SKIP_NEGATIVE_RATE) * 0.5,
            )
            adjustments["skip_confidence_threshold"] = delta
        elif skip_negative_rate < self.TARGET_SKIP_NEGATIVE_RATE * 0.5:
            # Very low negative rate → can slightly decrease threshold
            adjustments["skip_confidence_threshold"] = -0.02

        # 2. Semantic threshold (affects CRAG trigger rate)
        crag_trigger_rate = metrics.get("crag_trigger_rate", 0.0)
        if crag_trigger_rate > self.TARGET_CRAG_TRIGGER_RATE * 1.5:
            # Too many CRAG triggers → increase semantic threshold
            delta = min(
                self.MAX_ADJUSTMENT,
                (crag_trigger_rate - self.TARGET_CRAG_TRIGGER_RATE) * 0.3,
            )
            adjustments["semantic_threshold"] = delta
        elif crag_trigger_rate < self.TARGET_CRAG_TRIGGER_RATE * 0.5:
            # Too few CRAG triggers → may need lower threshold
            adjustments["semantic_threshold"] = -0.02

        # 3. CRAG relevance threshold (affects CRAG success)
        crag_success_rate = metrics.get("crag_success_rate", 0.0)
        if crag_success_rate < self.TARGET_CRAG_SUCCESS_RATE:
            # CRAG not effective → lower relevance threshold
            delta = min(
                self.MAX_ADJUSTMENT,
                (self.TARGET_CRAG_SUCCESS_RATE - crag_success_rate) * 0.3,
            )
            adjustments["crag_relevance_threshold"] = -delta
        elif crag_success_rate > 0.9:
            # CRAG very effective → can slightly increase threshold
            adjustments["crag_relevance_threshold"] = 0.02

        # 4. LLM fallback threshold
        low_conf_failure_rate = metrics.get("low_conf_failure_rate", 0.0)
        if low_conf_failure_rate > 0.2:
            # Many low-confidence failures → increase fallback threshold
            adjustments["llm_fallback_threshold"] = 0.05

        return adjustments

    def _apply_adjustments(
        self,
        adjustments: Dict[str, float],
    ) -> ThresholdConfig:
        """Apply adjustments to create new config."""
        new_values = self._current_config.model_dump()

        for key, delta in adjustments.items():
            if key in new_values:
                new_value = new_values[key] + delta
                # Clamp to valid range
                new_value = max(self.MIN_THRESHOLD, min(self.MAX_THRESHOLD, new_value))
                new_values[key] = round(new_value, 3)

        return ThresholdConfig(**new_values)

    def _calculate_changes(
        self,
        old_config: ThresholdConfig,
        new_config: ThresholdConfig,
    ) -> Dict[str, Dict[str, float]]:
        """Calculate detailed changes between configs."""
        changes = {}
        old_dict = old_config.model_dump()
        new_dict = new_config.model_dump()

        for key in old_dict:
            old_val = old_dict[key]
            new_val = new_dict[key]
            if old_val != new_val:
                changes[key] = {
                    "old": old_val,
                    "new": new_val,
                    "delta": round(new_val - old_val, 4),
                }

        return changes

    def _generate_rationale(
        self,
        changes: Dict[str, Dict[str, float]],
        report: Optional[MisclassificationReport],
    ) -> str:
        """Generate human-readable rationale for changes."""
        if not changes:
            return "No threshold changes needed based on current metrics."

        parts = []

        if "skip_confidence_threshold" in changes:
            delta = changes["skip_confidence_threshold"]["delta"]
            if delta > 0:
                parts.append(f"검색 생략 임계값 상향 (+{delta:.2f}): 검색 생략 후 부정 피드백 비율이 높음")
            else:
                parts.append(f"검색 생략 임계값 하향 ({delta:.2f}): 검색 생략 성공률이 충분히 높음")

        if "semantic_threshold" in changes:
            delta = changes["semantic_threshold"]["delta"]
            if delta > 0:
                parts.append(f"시맨틱 임계값 상향 (+{delta:.2f}): CRAG 트리거율이 높음")
            else:
                parts.append(f"시맨틱 임계값 하향 ({delta:.2f}): CRAG 트리거율이 낮음")

        if "crag_relevance_threshold" in changes:
            delta = changes["crag_relevance_threshold"]["delta"]
            if delta < 0:
                parts.append(f"CRAG 임계값 하향 ({delta:.2f}): CRAG 성공률이 낮음")
            else:
                parts.append(f"CRAG 임계값 상향 (+{delta:.2f}): CRAG 성공률이 높음")

        if "llm_fallback_threshold" in changes:
            delta = changes["llm_fallback_threshold"]["delta"]
            parts.append(f"LLM 폴백 임계값 조정 ({delta:+.2f}): 저신뢰도 분류 실패율 개선")

        return "; ".join(parts) if parts else "기본 최적화 적용"

    def _estimate_improvement(
        self,
        changes: Dict[str, Dict[str, float]],
        report: Optional[MisclassificationReport],
    ) -> Dict[str, float]:
        """Estimate expected improvement from changes."""
        expected = {}

        if not changes:
            return expected

        # Estimate based on change magnitudes
        if "skip_confidence_threshold" in changes:
            delta = abs(changes["skip_confidence_threshold"]["delta"])
            expected["skip_negative_rate"] = -delta * 0.5  # Expect reduction

        if "semantic_threshold" in changes:
            delta = abs(changes["semantic_threshold"]["delta"])
            expected["crag_trigger_rate"] = -delta * 0.3  # Expect reduction

        if "crag_relevance_threshold" in changes:
            delta = abs(changes["crag_relevance_threshold"]["delta"])
            expected["crag_success_rate"] = delta * 0.4  # Expect improvement

        # Overall accuracy estimate
        if report and report.misclassification_rate > 0:
            total_delta = sum(abs(c["delta"]) for c in changes.values())
            expected["accuracy"] = min(0.05, total_delta * 0.3)

        return expected


# =============================================================================
# Singleton Instance
# =============================================================================


_tuner: Optional[ThresholdTuner] = None


def get_threshold_tuner() -> ThresholdTuner:
    """Get or create singleton ThresholdTuner."""
    global _tuner
    if _tuner is None:
        _tuner = ThresholdTuner()
    return _tuner
