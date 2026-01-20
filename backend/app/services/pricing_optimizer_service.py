"""Pricing Optimizer Service (Phase 9 Monetization & Analytics).

ML-based dynamic pricing and A/B testing for tool pricing.

2026 Best Practices:
- Price Elasticity: Demand sensitivity to price changes
- A/B Testing: Statistical significance for pricing experiments
- Dynamic Pricing: Context-aware price optimization

Usage:
    from app.services.pricing_optimizer_service import PricingOptimizerService

    service = PricingOptimizerService(db)
    suggestion = await service.get_price_suggestion(tool_key, context)
    analysis = await service.analyze_experiment(experiment_id)
"""
from __future__ import annotations

import hashlib
import logging
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_analytics import (
    PricingExperiment,
    PricingExperimentAssignment,
    ExperimentStatus,
)
from app.models_telemetry import ToolRunEvent, ToolManifest

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Default price elasticity (10% price increase -> 12% demand decrease)
DEFAULT_ELASTICITY = -1.2

# Price multiplier bounds
MIN_PRICE_MULTIPLIER = 0.5
MAX_PRICE_MULTIPLIER = 2.0

# Minimum sample size for statistical significance
MIN_SAMPLE_SIZE = 100

# Z-scores for confidence levels
Z_SCORES = {
    0.90: 1.645,
    0.95: 1.96,
    0.99: 2.576,
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class PriceSuggestion:
    """ML-based price suggestion."""
    tool_key: str
    base_price: int
    suggested_multiplier: float
    suggested_price: int
    confidence: float
    factors: List[Dict[str, Any]]
    computed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExperimentVariant:
    """Pricing experiment variant."""
    name: str
    price_multiplier: float
    weight: float = 0.5  # Traffic allocation weight


@dataclass
class VariantMetrics:
    """Metrics for an experiment variant."""
    variant_name: str
    sample_size: int
    conversions: int
    conversion_rate: float
    revenue: int
    revenue_per_user: float
    avg_rating: Optional[float]


@dataclass
class ExperimentAnalysis:
    """Complete experiment analysis with statistical significance."""
    experiment_id: uuid.UUID
    experiment_name: str
    status: str
    variants: List[VariantMetrics]
    is_significant: bool
    p_value: Optional[float]
    winner: Optional[str]
    lift_pct: Optional[float]
    recommendation: str


# =============================================================================
# Pricing Optimizer Service
# =============================================================================

class PricingOptimizerService:
    """ML-based dynamic pricing and A/B testing.

    Features:
    - Price suggestions based on demand elasticity
    - A/B experiment creation and analysis
    - Deterministic user-variant assignment

    Attributes:
        db: Async database session
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize pricing optimizer service.

        Args:
            db: Async database session
        """
        self._db = db

    async def get_price_suggestion(
        self,
        tool_key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> PriceSuggestion:
        """Get ML-based price recommendation.

        Considers:
        - Historical demand elasticity
        - Time of day/week patterns
        - User segment pricing
        - Competition pricing

        Args:
            tool_key: Tool key
            context: Additional context (user segment, time, etc.)

        Returns:
            PriceSuggestion with recommended price
        """
        context = context or {}

        # Get tool manifest
        result = await self._db.execute(
            select(ToolManifest).where(ToolManifest.tool_key == tool_key)
        )
        manifest = result.scalar_one_or_none()

        if not manifest:
            raise ValueError(f"Tool not found: {tool_key}")

        base_price = manifest.credit_cost

        # Calculate price factors
        factors: List[Dict[str, Any]] = []
        multiplier = 1.0

        # 1. Demand-based adjustment
        demand_factor = await self._calculate_demand_factor(tool_key)
        factors.append({
            "name": "demand",
            "value": demand_factor,
            "description": "Based on recent usage patterns",
        })
        multiplier *= demand_factor

        # 2. Quality-based adjustment
        if manifest.quality_rating:
            quality_factor = 0.9 + (manifest.quality_rating / 5.0) * 0.2
            factors.append({
                "name": "quality",
                "value": quality_factor,
                "description": f"Quality rating: {manifest.quality_rating:.1f}/5",
            })
            multiplier *= quality_factor

        # 3. Time-based adjustment (off-peak discount)
        time_factor = self._calculate_time_factor(context.get("hour"))
        if time_factor != 1.0:
            factors.append({
                "name": "time",
                "value": time_factor,
                "description": "Off-peak discount",
            })
            multiplier *= time_factor

        # 4. User segment adjustment
        segment_factor = self._calculate_segment_factor(context.get("user_segment"))
        if segment_factor != 1.0:
            factors.append({
                "name": "segment",
                "value": segment_factor,
                "description": f"User segment: {context.get('user_segment')}",
            })
            multiplier *= segment_factor

        # Apply bounds
        multiplier = max(MIN_PRICE_MULTIPLIER, min(MAX_PRICE_MULTIPLIER, multiplier))
        suggested_price = max(1, int(base_price * multiplier))

        # Calculate confidence based on data quality
        confidence = await self._calculate_confidence(tool_key)

        return PriceSuggestion(
            tool_key=tool_key,
            base_price=base_price,
            suggested_multiplier=round(multiplier, 3),
            suggested_price=suggested_price,
            confidence=confidence,
            factors=factors,
        )

    async def create_experiment(
        self,
        experiment_name: str,
        tool_key: Optional[str],
        variants: List[ExperimentVariant],
        min_sample_size: int = MIN_SAMPLE_SIZE,
        confidence_level: float = 0.95,
    ) -> uuid.UUID:
        """Create A/B pricing experiment.

        Args:
            experiment_name: Unique experiment name
            tool_key: Tool to experiment on (None for global)
            variants: Experiment variants
            min_sample_size: Minimum sample per variant
            confidence_level: Required confidence (0.90, 0.95, 0.99)

        Returns:
            UUID: Created experiment ID
        """
        # Validate variants
        if len(variants) < 2:
            raise ValueError("Need at least 2 variants")

        total_weight = sum(v.weight for v in variants)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError("Variant weights must sum to 1.0")

        # Create experiment
        experiment = PricingExperiment(
            experiment_name=experiment_name,
            tool_key=tool_key,
            status=ExperimentStatus.DRAFT.value,
            variants=[
                {
                    "name": v.name,
                    "price_multiplier": v.price_multiplier,
                    "weight": v.weight,
                }
                for v in variants
            ],
            min_sample_size=min_sample_size,
            confidence_level=confidence_level,
        )

        self._db.add(experiment)
        await self._db.flush()

        logger.info(f"Created experiment {experiment_name} with ID {experiment.id}")
        return experiment.id

    async def start_experiment(
        self,
        experiment_id: uuid.UUID,
        end_at: Optional[datetime] = None,
    ) -> bool:
        """Start a pricing experiment.

        Args:
            experiment_id: Experiment ID
            end_at: Optional end time

        Returns:
            True if started successfully
        """
        result = await self._db.execute(
            select(PricingExperiment).where(PricingExperiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")

        if experiment.status != ExperimentStatus.DRAFT.value:
            raise ValueError(f"Experiment is not in draft status: {experiment.status}")

        experiment.status = ExperimentStatus.RUNNING.value
        experiment.start_at = datetime.utcnow()
        experiment.end_at = end_at

        await self._db.flush()
        logger.info(f"Started experiment {experiment.experiment_name}")

        return True

    async def get_user_variant(
        self,
        experiment_id: uuid.UUID,
        user_id: str,
    ) -> Tuple[str, float]:
        """Get user's assigned variant (deterministic hash).

        Uses consistent hashing to ensure same user always gets same variant.

        Args:
            experiment_id: Experiment ID
            user_id: User ID

        Returns:
            Tuple of (variant_name, price_multiplier)
        """
        # Check for existing assignment
        result = await self._db.execute(
            select(PricingExperimentAssignment).where(
                and_(
                    PricingExperimentAssignment.experiment_id == experiment_id,
                    PricingExperimentAssignment.user_id == user_id,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            return existing.variant_name, existing.price_multiplier

        # Get experiment
        exp_result = await self._db.execute(
            select(PricingExperiment).where(PricingExperiment.id == experiment_id)
        )
        experiment = exp_result.scalar_one_or_none()

        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")

        if experiment.status != ExperimentStatus.RUNNING.value:
            # Return control variant for non-running experiments
            control = experiment.variants[0]
            return control["name"], control["price_multiplier"]

        # Deterministic hash assignment
        hash_input = f"{experiment_id}:{user_id}".encode()
        hash_value = int(hashlib.sha256(hash_input).hexdigest(), 16)
        bucket = (hash_value % 1000) / 1000.0  # 0.0 - 0.999

        # Find variant by weight
        cumulative = 0.0
        selected_variant = experiment.variants[0]

        for variant in experiment.variants:
            cumulative += variant["weight"]
            if bucket < cumulative:
                selected_variant = variant
                break

        # Save assignment
        assignment = PricingExperimentAssignment(
            experiment_id=experiment_id,
            user_id=user_id,
            variant_name=selected_variant["name"],
            price_multiplier=selected_variant["price_multiplier"],
        )
        self._db.add(assignment)
        await self._db.flush()

        return selected_variant["name"], selected_variant["price_multiplier"]

    async def analyze_experiment(
        self,
        experiment_id: uuid.UUID,
    ) -> ExperimentAnalysis:
        """Analyze experiment with statistical significance.

        Calculates conversion rates, revenue impact, and significance.

        Args:
            experiment_id: Experiment ID

        Returns:
            ExperimentAnalysis with results
        """
        # Get experiment
        exp_result = await self._db.execute(
            select(PricingExperiment).where(PricingExperiment.id == experiment_id)
        )
        experiment = exp_result.scalar_one_or_none()

        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")

        # Get metrics for each variant
        variant_metrics: List[VariantMetrics] = []
        control_metrics = None

        for variant in experiment.variants:
            metrics = await self._get_variant_metrics(
                experiment_id, variant["name"]
            )
            variant_metrics.append(metrics)

            if variant["name"] == "control":
                control_metrics = metrics

        # Statistical significance test
        is_significant = False
        p_value = None
        winner = None
        lift_pct = None

        if control_metrics and len(variant_metrics) >= 2:
            # Find best performing variant
            best_variant = max(
                variant_metrics,
                key=lambda v: v.revenue_per_user,
            )

            if best_variant.variant_name != "control":
                # Calculate z-score and p-value
                z_score = self._calculate_z_score(control_metrics, best_variant)
                p_value = self._z_to_p_value(z_score)

                if p_value and p_value < (1 - experiment.confidence_level):
                    is_significant = True
                    winner = best_variant.variant_name

                    # Calculate lift
                    if control_metrics.revenue_per_user > 0:
                        lift_pct = (
                            (best_variant.revenue_per_user - control_metrics.revenue_per_user)
                            / control_metrics.revenue_per_user
                            * 100
                        )

        # Generate recommendation
        recommendation = self._generate_recommendation(
            experiment, variant_metrics, is_significant, winner, lift_pct
        )

        return ExperimentAnalysis(
            experiment_id=experiment_id,
            experiment_name=experiment.experiment_name,
            status=experiment.status,
            variants=variant_metrics,
            is_significant=is_significant,
            p_value=p_value,
            winner=winner,
            lift_pct=round(lift_pct, 2) if lift_pct else None,
            recommendation=recommendation,
        )

    async def complete_experiment(
        self,
        experiment_id: uuid.UUID,
        winning_variant: Optional[str] = None,
    ) -> bool:
        """Complete an experiment and record winner.

        Args:
            experiment_id: Experiment ID
            winning_variant: Winner variant name

        Returns:
            True if completed successfully
        """
        result = await self._db.execute(
            select(PricingExperiment).where(PricingExperiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")

        experiment.status = ExperimentStatus.COMPLETED.value
        experiment.winning_variant = winning_variant
        experiment.end_at = datetime.utcnow()

        await self._db.flush()
        logger.info(f"Completed experiment {experiment.experiment_name}, winner: {winning_variant}")

        return True

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _calculate_demand_factor(self, tool_key: str) -> float:
        """Calculate demand-based price factor.

        Uses recent usage trends vs historical average.
        """
        now = datetime.utcnow()
        recent = now - timedelta(days=7)
        historical = now - timedelta(days=30)

        # Recent usage
        recent_result = await self._db.execute(
            select(func.count())
            .where(
                and_(
                    ToolRunEvent.tool_key == tool_key,
                    ToolRunEvent.created_at >= recent,
                )
            )
        )
        recent_count = recent_result.scalar() or 0

        # Historical average (per 7 days)
        historical_result = await self._db.execute(
            select(func.count())
            .where(
                and_(
                    ToolRunEvent.tool_key == tool_key,
                    ToolRunEvent.created_at >= historical,
                    ToolRunEvent.created_at < recent,
                )
            )
        )
        historical_count = historical_result.scalar() or 0
        historical_avg = historical_count / 3.28  # ~23 days / 7 days

        if historical_avg == 0:
            return 1.0

        # High demand = higher price, bounded
        demand_ratio = recent_count / historical_avg
        factor = 0.8 + 0.4 * min(1.5, demand_ratio / 1.5)

        return round(factor, 3)

    def _calculate_time_factor(self, hour: Optional[int]) -> float:
        """Calculate time-based price factor.

        Off-peak hours get discount.
        """
        if hour is None:
            return 1.0

        # Off-peak: 00:00 - 08:00 UTC
        if 0 <= hour < 8:
            return 0.9

        return 1.0

    def _calculate_segment_factor(self, segment: Optional[str]) -> float:
        """Calculate user segment price factor."""
        segment_factors = {
            "new": 0.9,        # New user discount
            "power": 1.0,     # Regular price
            "enterprise": 1.1, # Premium pricing
        }
        return segment_factors.get(segment or "", 1.0)

    async def _calculate_confidence(self, tool_key: str) -> float:
        """Calculate confidence in price suggestion.

        Based on data quality and sample size.
        """
        # Count recent data points
        result = await self._db.execute(
            select(func.count())
            .where(
                and_(
                    ToolRunEvent.tool_key == tool_key,
                    ToolRunEvent.created_at >= datetime.utcnow() - timedelta(days=30),
                )
            )
        )
        count = result.scalar() or 0

        # More data = higher confidence, max 0.95
        if count < 10:
            return 0.3
        elif count < 50:
            return 0.5
        elif count < 200:
            return 0.7
        elif count < 500:
            return 0.85
        else:
            return 0.95

    async def _get_variant_metrics(
        self,
        experiment_id: uuid.UUID,
        variant_name: str,
    ) -> VariantMetrics:
        """Get metrics for a specific variant."""
        # Get assignments for this variant
        result = await self._db.execute(
            select(PricingExperimentAssignment)
            .where(
                and_(
                    PricingExperimentAssignment.experiment_id == experiment_id,
                    PricingExperimentAssignment.variant_name == variant_name,
                )
            )
        )
        assignments = list(result.scalars())
        user_ids = [a.user_id for a in assignments]

        sample_size = len(user_ids)
        if sample_size == 0:
            return VariantMetrics(
                variant_name=variant_name,
                sample_size=0,
                conversions=0,
                conversion_rate=0.0,
                revenue=0,
                revenue_per_user=0.0,
                avg_rating=None,
            )

        # Get conversion and revenue data
        exp_result = await self._db.execute(
            select(PricingExperiment).where(PricingExperiment.id == experiment_id)
        )
        experiment = exp_result.scalar_one_or_none()

        tool_key = experiment.tool_key if experiment else None

        query = select(
            func.count().label("conversions"),
            func.sum(ToolRunEvent.credits_charged - ToolRunEvent.credits_refunded).label("revenue"),
            func.avg(ToolRunEvent.user_rating).label("avg_rating"),
        ).where(ToolRunEvent.user_id.in_(user_ids))

        if tool_key:
            query = query.where(ToolRunEvent.tool_key == tool_key)

        if experiment and experiment.start_at:
            query = query.where(ToolRunEvent.created_at >= experiment.start_at)

        metrics_result = await self._db.execute(query)
        row = metrics_result.one()

        conversions = int(row.conversions or 0)
        revenue = int(row.revenue or 0)
        avg_rating = float(row.avg_rating) if row.avg_rating else None

        return VariantMetrics(
            variant_name=variant_name,
            sample_size=sample_size,
            conversions=conversions,
            conversion_rate=conversions / sample_size if sample_size > 0 else 0.0,
            revenue=revenue,
            revenue_per_user=revenue / sample_size if sample_size > 0 else 0.0,
            avg_rating=avg_rating,
        )

    def _calculate_z_score(
        self,
        control: VariantMetrics,
        variant: VariantMetrics,
    ) -> float:
        """Calculate z-score for A/B test."""
        n1 = control.sample_size
        n2 = variant.sample_size

        if n1 == 0 or n2 == 0:
            return 0.0

        p1 = control.conversion_rate
        p2 = variant.conversion_rate

        # Pooled proportion
        p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)

        if p_pool == 0 or p_pool == 1:
            return 0.0

        # Standard error
        se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))

        if se == 0:
            return 0.0

        return (p2 - p1) / se

    def _z_to_p_value(self, z: float) -> float:
        """Convert z-score to p-value (two-tailed)."""
        # Approximation using error function
        x = abs(z) / math.sqrt(2)
        # Taylor series approximation
        t = 1.0 / (1.0 + 0.3275911 * x)
        a = [0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429]
        erf = 1 - (a[0]*t + a[1]*t**2 + a[2]*t**3 + a[3]*t**4 + a[4]*t**5) * math.exp(-x*x)

        return 1 - erf

    def _generate_recommendation(
        self,
        experiment: PricingExperiment,
        variants: List[VariantMetrics],
        is_significant: bool,
        winner: Optional[str],
        lift_pct: Optional[float],
    ) -> str:
        """Generate human-readable recommendation."""
        # Check sample size
        total_samples = sum(v.sample_size for v in variants)
        min_required = experiment.min_sample_size * len(variants)

        if total_samples < min_required:
            return (
                f"Insufficient data. Need {min_required - total_samples} more samples "
                f"for statistical significance."
            )

        if is_significant and winner:
            return (
                f"Statistically significant result. "
                f"Recommend adopting '{winner}' variant with {lift_pct:+.1f}% lift."
            )

        return "No statistically significant winner yet. Continue running the experiment."
