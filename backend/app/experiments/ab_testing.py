"""
A/B Testing Service (2026 Best Practice)

Self-hosted experimentation platform with:
- Consistent user assignment (no flip-flopping)
- Exposure tracking and conversion recording
- Integration with feature flags
- CUPED variance reduction support
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.experiments.models import (
    Experiment,
    ExperimentVariant,
    ExperimentExposure,
    ExperimentConversion,
    ExperimentResult,
    ExperimentStatus,
)
from app.experiments.statistics import (
    StatisticalAnalyzer,
    VariantStats,
    SignificanceResult,
)

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger(__name__)


@dataclass
class ExperimentAssignment:
    """Result of experiment assignment."""
    experiment_key: str
    variant_name: str
    is_control: bool
    payload: dict
    already_assigned: bool = False


class ABTestingService:
    """
    Production-ready A/B Testing Service.

    2026 Best Practices:
    - Consistent hashing for deterministic assignment
    - Exposure-based analysis (only count exposed users)
    - Statistical significance with Bayesian and frequentist methods
    - CUPED variance reduction for faster experiments
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6380",
    ):
        self._redis_url = redis_url
        self._redis: Optional["Redis"] = None
        self._analyzer = StatisticalAnalyzer()

    async def _get_redis(self) -> Optional["Redis"]:
        """Get Redis client with lazy initialization."""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_timeout=2.0,
                )
            except Exception as e:
                logger.warning(f"A/B Testing Redis connection failed: {e}")
                return None
        return self._redis

    def _consistent_hash(self, user_id: str, experiment_key: str) -> int:
        """
        Consistent hash for deterministic variant assignment.

        2026 Best Practice:
        - Same user always gets same variant for same experiment
        - No flip-flopping even when traffic allocation changes
        """
        hash_input = f"{experiment_key}:{user_id}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()
        return int(hash_value[:8], 16) % 10000  # 0-9999 for 0.01% precision

    async def get_experiment(
        self,
        experiment_key: str,
        db: AsyncSession,
    ) -> Optional[Experiment]:
        """Get experiment by key."""
        result = await db.execute(
            select(Experiment)
            .where(Experiment.experiment_key == experiment_key)
            .where(Experiment.status == ExperimentStatus.RUNNING)
        )
        return result.scalar_one_or_none()

    async def assign_variant(
        self,
        experiment_key: str,
        user_id: str,
        db: AsyncSession,
        context: Optional[dict] = None,
        pre_experiment_value: Optional[float] = None,
    ) -> Optional[ExperimentAssignment]:
        """
        Assign user to experiment variant.

        Uses consistent hashing for deterministic assignment.
        Records exposure for analysis.

        Args:
            experiment_key: Unique experiment identifier
            user_id: User identifier
            db: Database session
            context: Optional context for targeting
            pre_experiment_value: Pre-experiment metric for CUPED

        Returns:
            ExperimentAssignment or None if experiment not found/running
        """
        # Get experiment
        experiment = await self.get_experiment(experiment_key, db)
        if not experiment:
            return None

        # Check for existing assignment
        existing = await db.execute(
            select(ExperimentExposure)
            .where(ExperimentExposure.experiment_id == experiment.id)
            .where(ExperimentExposure.user_id == user_id)
        )
        existing_exposure = existing.scalar_one_or_none()

        if existing_exposure:
            # Return existing assignment
            variant = next(
                (v for v in experiment.variants if v.name == existing_exposure.variant_name),
                None
            )
            return ExperimentAssignment(
                experiment_key=experiment_key,
                variant_name=existing_exposure.variant_name,
                is_control=variant.is_control if variant else False,
                payload=variant.payload if variant else {},
                already_assigned=True,
            )

        # Check traffic allocation
        hash_value = self._consistent_hash(user_id, experiment_key)
        traffic_threshold = int(experiment.traffic_percentage * 100)  # Convert to 0-10000

        if hash_value >= traffic_threshold:
            # User not in experiment traffic
            return None

        # Assign variant based on weights
        variant = self._select_variant(experiment.variants, user_id, experiment_key)
        if not variant:
            return None

        # Record exposure
        exposure = ExperimentExposure(
            experiment_id=experiment.id,
            user_id=user_id,
            variant_name=variant.name,
            context=context or {},
            pre_experiment_value=pre_experiment_value,
        )
        db.add(exposure)
        await db.flush()

        return ExperimentAssignment(
            experiment_key=experiment_key,
            variant_name=variant.name,
            is_control=variant.is_control,
            payload=variant.payload,
            already_assigned=False,
        )

    def _select_variant(
        self,
        variants: list[ExperimentVariant],
        user_id: str,
        experiment_key: str,
    ) -> Optional[ExperimentVariant]:
        """Select variant using consistent hashing with weights."""
        if not variants:
            return None

        # Use different hash for variant selection (add :variant suffix)
        hash_value = self._consistent_hash(user_id, f"{experiment_key}:variant")
        hash_percentage = hash_value / 100  # Convert to 0-100

        cumulative = 0.0
        for variant in variants:
            cumulative += variant.weight
            if hash_percentage < cumulative:
                return variant

        # Fallback to last variant
        return variants[-1]

    async def record_conversion(
        self,
        experiment_key: str,
        user_id: str,
        metric_name: str,
        db: AsyncSession,
        metric_value: float = 1.0,
        attribution_window_hours: int = 24,
    ) -> bool:
        """
        Record conversion event for experiment.

        Args:
            experiment_key: Unique experiment identifier
            user_id: User identifier
            metric_name: Name of the conversion metric
            db: Database session
            metric_value: Metric value (default 1.0 for binary)
            attribution_window_hours: Attribution window

        Returns:
            True if recorded, False otherwise
        """
        # Get experiment
        experiment = await self.get_experiment(experiment_key, db)
        if not experiment:
            return False

        # Get user's exposure
        exposure = await db.execute(
            select(ExperimentExposure)
            .where(ExperimentExposure.experiment_id == experiment.id)
            .where(ExperimentExposure.user_id == user_id)
        )
        exposure_record = exposure.scalar_one_or_none()

        if not exposure_record:
            # User was not exposed to experiment
            return False

        # Record conversion
        conversion = ExperimentConversion(
            experiment_id=experiment.id,
            user_id=user_id,
            variant_name=exposure_record.variant_name,
            metric_name=metric_name,
            metric_value=metric_value,
            attribution_window_hours=attribution_window_hours,
        )
        db.add(conversion)
        await db.flush()

        return True

    async def get_variant_stats(
        self,
        experiment_id: int,
        variant_name: str,
        metric_name: str,
        db: AsyncSession,
    ) -> VariantStats:
        """Get statistics for a specific variant."""
        # Get sample size (exposures)
        sample_result = await db.execute(
            select(func.count(ExperimentExposure.id))
            .where(ExperimentExposure.experiment_id == experiment_id)
            .where(ExperimentExposure.variant_name == variant_name)
        )
        sample_size = sample_result.scalar() or 0

        # Get conversions
        conv_result = await db.execute(
            select(
                func.count(ExperimentConversion.id),
                func.sum(ExperimentConversion.metric_value),
                func.sum(ExperimentConversion.metric_value * ExperimentConversion.metric_value),
            )
            .where(ExperimentConversion.experiment_id == experiment_id)
            .where(ExperimentConversion.variant_name == variant_name)
            .where(ExperimentConversion.metric_name == metric_name)
        )
        conv_count, sum_values, sum_squared = conv_result.one()

        return VariantStats(
            name=variant_name,
            sample_size=sample_size,
            conversions=conv_count or 0,
            sum_values=sum_values or 0.0,
            sum_squared_values=sum_squared or 0.0,
        )

    async def calculate_results(
        self,
        experiment_key: str,
        db: AsyncSession,
        metric_name: Optional[str] = None,
    ) -> Optional[SignificanceResult]:
        """
        Calculate experiment results with statistical significance.

        Args:
            experiment_key: Unique experiment identifier
            db: Database session
            metric_name: Metric to analyze (default: primary metric)

        Returns:
            SignificanceResult or None
        """
        # Get experiment
        result = await db.execute(
            select(Experiment)
            .where(Experiment.experiment_key == experiment_key)
        )
        experiment = result.scalar_one_or_none()
        if not experiment:
            return None

        metric = metric_name or experiment.primary_metric

        # Get control and treatment variants
        control_variant = next(
            (v for v in experiment.variants if v.is_control),
            experiment.variants[0] if experiment.variants else None
        )
        treatment_variant = next(
            (v for v in experiment.variants if not v.is_control),
            experiment.variants[1] if len(experiment.variants) > 1 else None
        )

        if not control_variant or not treatment_variant:
            return None

        # Get stats
        control_stats = await self.get_variant_stats(
            experiment.id, control_variant.name, metric, db
        )
        treatment_stats = await self.get_variant_stats(
            experiment.id, treatment_variant.name, metric, db
        )

        # Analyze based on metric type
        if metric in ["revenue", "time_on_page", "session_duration"]:
            return self._analyzer.analyze_continuous_metric(
                control_stats, treatment_stats
            )
        else:
            return self._analyzer.analyze_binary_metric(
                control_stats, treatment_stats
            )

    async def update_cached_results(
        self,
        experiment_key: str,
        db: AsyncSession,
    ) -> None:
        """
        Update cached results for dashboard.

        Called periodically by background job.
        """
        # Get experiment
        result = await db.execute(
            select(Experiment)
            .where(Experiment.experiment_key == experiment_key)
        )
        experiment = result.scalar_one_or_none()
        if not experiment:
            return

        metrics = [experiment.primary_metric] + (experiment.secondary_metrics or [])

        for variant in experiment.variants:
            for metric in metrics:
                stats = await self.get_variant_stats(
                    experiment.id, variant.name, metric, db
                )

                # Get or create result record
                existing = await db.execute(
                    select(ExperimentResult)
                    .where(ExperimentResult.experiment_id == experiment.id)
                    .where(ExperimentResult.variant_name == variant.name)
                    .where(ExperimentResult.metric_name == metric)
                )
                cached_result = existing.scalar_one_or_none()

                if cached_result:
                    cached_result.sample_size = stats.sample_size
                    cached_result.conversions = stats.conversions
                    cached_result.conversion_rate = stats.conversion_rate
                    cached_result.mean_value = stats.mean
                    cached_result.std_dev = stats.std_dev
                    cached_result.computed_at = datetime.utcnow()
                else:
                    cached_result = ExperimentResult(
                        experiment_id=experiment.id,
                        variant_name=variant.name,
                        metric_name=metric,
                        sample_size=stats.sample_size,
                        conversions=stats.conversions,
                        conversion_rate=stats.conversion_rate,
                        mean_value=stats.mean,
                        std_dev=stats.std_dev,
                    )
                    db.add(cached_result)

        # Calculate significance for treatment variants
        control_variant = next(
            (v for v in experiment.variants if v.is_control), None
        )
        if control_variant:
            control_stats = await self.get_variant_stats(
                experiment.id, control_variant.name, experiment.primary_metric, db
            )

            for variant in experiment.variants:
                if variant.is_control:
                    continue

                treatment_stats = await self.get_variant_stats(
                    experiment.id, variant.name, experiment.primary_metric, db
                )

                sig_result = self._analyzer.analyze_binary_metric(
                    control_stats, treatment_stats
                )

                # Update result with significance
                result_record = await db.execute(
                    select(ExperimentResult)
                    .where(ExperimentResult.experiment_id == experiment.id)
                    .where(ExperimentResult.variant_name == variant.name)
                    .where(ExperimentResult.metric_name == experiment.primary_metric)
                )
                cached = result_record.scalar_one_or_none()
                if cached:
                    cached.relative_lift = sig_result.relative_lift
                    cached.absolute_lift = sig_result.absolute_lift
                    cached.p_value = sig_result.p_value
                    cached.confidence_interval_lower = sig_result.confidence_interval[0]
                    cached.confidence_interval_upper = sig_result.confidence_interval[1]
                    cached.is_significant = sig_result.is_significant
                    cached.probability_of_being_best = sig_result.probability_of_being_best
                    cached.expected_loss = sig_result.expected_loss

        await db.flush()

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


# Singleton instance
_ab_testing_service: Optional[ABTestingService] = None


def get_ab_testing() -> ABTestingService:
    """Get or create singleton A/B testing service."""
    global _ab_testing_service
    if _ab_testing_service is None:
        from app.config import settings
        _ab_testing_service = ABTestingService(redis_url=settings.REDIS_URL)
    return _ab_testing_service


async def init_ab_testing() -> ABTestingService:
    """Initialize A/B testing service (call at startup)."""
    service = get_ab_testing()
    await service._get_redis()
    return service
