"""Feedback Analyzer Service.

Analyzes pipeline execution feedback to detect patterns and trigger improvements.
Implements 2026 MLOps best practices for continuous improvement.

Features:
- Weekly failure pattern detection
- Low-rating prompt analysis
- Automated improvement suggestions
- Admin notification for action items

Usage:
    from app.services.feedback_analyzer import FeedbackAnalyzer

    analyzer = FeedbackAnalyzer()

    # Run weekly analysis
    result = await analyzer.analyze_weekly(db)

    # Analyze specific failure patterns
    patterns = await analyzer.detect_failure_patterns(db, days=7)
"""
from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

FAILURE_THRESHOLD = 0.2  # > 20% failure rate triggers alert
LOW_RATING_THRESHOLD = 3  # Ratings <= 3 are considered low
MIN_SAMPLES_FOR_PATTERN = 10  # Minimum samples to detect a pattern


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class FailurePattern:
    """Detected failure pattern."""
    pattern_type: str  # step_failure, error_category, prompt_pattern
    description: str
    occurrence_count: int
    failure_rate: float
    affected_steps: List[str] = field(default_factory=list)
    sample_trace_ids: List[str] = field(default_factory=list)
    suggested_action: str = ""
    severity: str = "medium"  # low, medium, high, critical


@dataclass
class FeedbackSummary:
    """Summary of feedback analysis."""
    period_start: datetime
    period_end: datetime
    total_runs: int
    success_count: int
    failure_count: int
    partial_success_count: int
    average_rating: Optional[float]
    failure_patterns: List[FailurePattern] = field(default_factory=list)
    low_rating_patterns: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# =============================================================================
# Feedback Analyzer Service
# =============================================================================

class FeedbackAnalyzer:
    """Analyzes pipeline feedback for improvement opportunities."""

    async def analyze_weekly(
        self,
        db: AsyncSession,
        end_date: Optional[datetime] = None,
    ) -> FeedbackSummary:
        """Run weekly feedback analysis.

        Args:
            db: Database session
            end_date: End of analysis period (default: now)

        Returns:
            FeedbackSummary with patterns and recommendations
        """
        end_date = end_date or datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        logger.info(f"[FeedbackAnalyzer] Analyzing period {start_date} to {end_date}")

        # Get basic metrics
        metrics = await self._get_period_metrics(db, start_date, end_date)

        # Detect failure patterns
        failure_patterns = await self.detect_failure_patterns(db, start_date, end_date)

        # Detect low rating patterns
        low_rating_patterns = await self._detect_low_rating_patterns(db, start_date, end_date)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            metrics,
            failure_patterns,
            low_rating_patterns,
        )

        summary = FeedbackSummary(
            period_start=start_date,
            period_end=end_date,
            total_runs=metrics["total"],
            success_count=metrics["success"],
            failure_count=metrics["failure"],
            partial_success_count=metrics["partial"],
            average_rating=metrics["avg_rating"],
            failure_patterns=failure_patterns,
            low_rating_patterns=low_rating_patterns,
            recommendations=recommendations,
        )

        # Notify if critical patterns found
        if any(p.severity == "critical" for p in failure_patterns):
            await self._notify_admin(summary)

        # Mark analyzed records
        await self._mark_analyzed(db, start_date, end_date)

        return summary

    async def detect_failure_patterns(
        self,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days: int = 7,
    ) -> List[FailurePattern]:
        """Detect failure patterns in recent runs.

        Args:
            db: Database session
            start_date: Start of analysis period
            end_date: End of analysis period
            days: Days to analyze if dates not provided

        Returns:
            List of detected FailurePattern
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=days)

        patterns = []

        try:
            from app.models_pipeline import PipelineResult

            # Query failed runs
            query = (
                select(PipelineResult)
                .where(PipelineResult.created_at >= start_date)
                .where(PipelineResult.created_at <= end_date)
                .where(PipelineResult.success == False)
            )

            result = await db.execute(query)
            failures = result.scalars().all()

            if len(failures) < MIN_SAMPLES_FOR_PATTERN:
                return patterns

            # Group by failure step
            step_failures = defaultdict(list)
            for f in failures:
                if f.failure_step:
                    step_failures[f.failure_step].append(f)

            # Detect step-specific patterns
            for step, step_runs in step_failures.items():
                if len(step_runs) >= 3:  # At least 3 failures
                    # Categorize errors
                    error_counts = Counter(r.error_category for r in step_runs)
                    most_common = error_counts.most_common(1)

                    if most_common:
                        error_cat, count = most_common[0]
                        pattern = FailurePattern(
                            pattern_type="step_failure",
                            description=f"Step '{step}' failing with {error_cat} errors",
                            occurrence_count=count,
                            failure_rate=count / len(failures),
                            affected_steps=[step],
                            sample_trace_ids=[r.trace_id for r in step_runs[:5]],
                            suggested_action=self._suggest_action_for_step(step, error_cat),
                            severity=self._calculate_severity(count, len(failures)),
                        )
                        patterns.append(pattern)

            # Group by error category
            category_failures = defaultdict(list)
            for f in failures:
                if f.error_category:
                    category_failures[f.error_category].append(f)

            for category, cat_runs in category_failures.items():
                if len(cat_runs) >= MIN_SAMPLES_FOR_PATTERN:
                    pattern = FailurePattern(
                        pattern_type="error_category",
                        description=f"High frequency of '{category}' errors",
                        occurrence_count=len(cat_runs),
                        failure_rate=len(cat_runs) / len(failures),
                        affected_steps=list(set(r.failure_step for r in cat_runs if r.failure_step)),
                        sample_trace_ids=[r.trace_id for r in cat_runs[:5]],
                        suggested_action=self._suggest_action_for_category(category),
                        severity=self._calculate_severity(len(cat_runs), len(failures)),
                    )
                    patterns.append(pattern)

        except ImportError:
            logger.warning("[FeedbackAnalyzer] PipelineResult model not found")
        except Exception as e:
            logger.error(f"[FeedbackAnalyzer] Pattern detection failed: {e}")

        return patterns

    async def _get_period_metrics(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Get metrics for a time period."""
        try:
            from app.models_pipeline import PipelineResult

            # Count query
            query = select(
                func.count(PipelineResult.id).label("total"),
                func.sum(func.cast(PipelineResult.success, sa.Integer)).label("success"),
                func.sum(func.cast(PipelineResult.partial_success, sa.Integer)).label("partial"),
                func.avg(PipelineResult.user_rating).label("avg_rating"),
            ).where(
                PipelineResult.created_at >= start_date,
                PipelineResult.created_at <= end_date,
            )

            result = await db.execute(query)
            row = result.fetchone()

            total = row.total or 0
            success = row.success or 0
            partial = row.partial or 0

            return {
                "total": total,
                "success": success,
                "partial": partial,
                "failure": total - success - partial,
                "avg_rating": float(row.avg_rating) if row.avg_rating else None,
            }

        except ImportError:
            logger.warning("[FeedbackAnalyzer] PipelineResult model not found")
            return {
                "total": 0,
                "success": 0,
                "partial": 0,
                "failure": 0,
                "avg_rating": None,
            }

    async def _detect_low_rating_patterns(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """Detect patterns in low-rated runs."""
        patterns = []

        try:
            from app.models_pipeline import PipelineResult

            query = (
                select(PipelineResult)
                .where(PipelineResult.created_at >= start_date)
                .where(PipelineResult.created_at <= end_date)
                .where(PipelineResult.user_rating != None)
                .where(PipelineResult.user_rating <= LOW_RATING_THRESHOLD)
            )

            result = await db.execute(query)
            low_rated = result.scalars().all()

            if len(low_rated) < 3:
                return patterns

            # Group by feedback tags
            tag_counts = Counter()
            for run in low_rated:
                if run.feedback_tags:
                    for tag in run.feedback_tags:
                        tag_counts[tag] += 1

            for tag, count in tag_counts.most_common(5):
                if count >= 3:
                    patterns.append({
                        "type": "feedback_tag",
                        "tag": tag,
                        "count": count,
                        "percentage": count / len(low_rated) * 100,
                    })

            # Group by steps completed
            step_counts = Counter()
            for run in low_rated:
                if run.steps_completed:
                    step_key = ",".join(sorted(run.steps_completed))
                    step_counts[step_key] += 1

            for steps, count in step_counts.most_common(3):
                if count >= 3:
                    patterns.append({
                        "type": "step_combination",
                        "steps": steps.split(","),
                        "count": count,
                        "percentage": count / len(low_rated) * 100,
                    })

        except ImportError:
            logger.warning("[FeedbackAnalyzer] PipelineResult model not found")

        return patterns

    def _generate_recommendations(
        self,
        metrics: Dict[str, Any],
        failure_patterns: List[FailurePattern],
        low_rating_patterns: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Overall failure rate
        if metrics["total"] > 0:
            failure_rate = metrics["failure"] / metrics["total"]
            if failure_rate > FAILURE_THRESHOLD:
                recommendations.append(
                    f"High failure rate ({failure_rate:.1%}). "
                    f"Review most common failure patterns below."
                )

        # Step-specific recommendations
        for pattern in failure_patterns:
            if pattern.severity in ("high", "critical"):
                recommendations.append(pattern.suggested_action)

        # Rating-based recommendations
        if metrics["avg_rating"] and metrics["avg_rating"] < 3.5:
            recommendations.append(
                f"Average rating is low ({metrics['avg_rating']:.1f}/5). "
                f"Review low-rating feedback tags for improvement areas."
            )

        # Low rating pattern recommendations
        for pattern in low_rating_patterns:
            if pattern["type"] == "feedback_tag":
                recommendations.append(
                    f"Address '{pattern['tag']}' feedback "
                    f"(mentioned in {pattern['percentage']:.0f}% of low ratings)"
                )

        return recommendations

    def _suggest_action_for_step(self, step: str, error_category: str) -> str:
        """Suggest action for step-specific failures."""
        suggestions = {
            ("vpe", "timeout"): "Increase VPE timeout or optimize video processing",
            ("vpe", "api_error"): "Check Gemini API quota and rate limits",
            ("ad", "validation"): "Review AD prompt templates for edge cases",
            ("mirror", "timeout"): "Optimize Mirror persona analysis prompts",
            ("qc", "api_error"): "Review QC evaluation criteria thresholds",
        }

        key = (step, error_category)
        if key in suggestions:
            return suggestions[key]

        return f"Review {step} step configuration for {error_category} errors"

    def _suggest_action_for_category(self, category: str) -> str:
        """Suggest action for error category."""
        suggestions = {
            "timeout": "Consider increasing timeouts or optimizing processing",
            "api_error": "Review API configurations and rate limits",
            "validation": "Update input validation rules",
            "rate_limit": "Implement better request throttling",
            "credit_error": "Review credit deduction logic",
        }

        return suggestions.get(
            category,
            f"Investigate root cause of {category} errors"
        )

    def _calculate_severity(self, count: int, total_failures: int) -> str:
        """Calculate pattern severity."""
        if total_failures == 0:
            return "low"

        rate = count / total_failures

        if rate > 0.5:
            return "critical"
        elif rate > 0.3:
            return "high"
        elif rate > 0.1:
            return "medium"
        else:
            return "low"

    async def _notify_admin(self, summary: FeedbackSummary) -> None:
        """Notify admin of critical patterns."""
        try:
            from app.services.notification_service import NotificationService

            notification = NotificationService()
            await notification.send_admin_alert(
                title="DNA Lab Pipeline: Critical Pattern Detected",
                message=f"Weekly analysis found {len(summary.failure_patterns)} failure patterns. "
                f"Failure rate: {summary.failure_count}/{summary.total_runs}",
                data={
                    "period_start": summary.period_start.isoformat(),
                    "period_end": summary.period_end.isoformat(),
                    "patterns": [p.description for p in summary.failure_patterns],
                    "recommendations": summary.recommendations,
                },
            )
        except ImportError:
            logger.info("[FeedbackAnalyzer] NotificationService not available")
        except Exception as e:
            logger.error(f"[FeedbackAnalyzer] Admin notification failed: {e}")

    async def _mark_analyzed(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
    ) -> None:
        """Mark records as analyzed."""
        try:
            from app.models_pipeline import PipelineResult

            await db.execute(
                update(PipelineResult)
                .where(PipelineResult.created_at >= start_date)
                .where(PipelineResult.created_at <= end_date)
                .where(PipelineResult.analyzed == False)
                .values(analyzed=True, analyzed_at=datetime.utcnow())
            )

        except ImportError:
            pass


# =============================================================================
# Import fix
# =============================================================================

import sqlalchemy as sa


# =============================================================================
# Module-level convenience
# =============================================================================

_default_analyzer: Optional[FeedbackAnalyzer] = None


def get_feedback_analyzer() -> FeedbackAnalyzer:
    """Get or create the default analyzer instance."""
    global _default_analyzer
    if _default_analyzer is None:
        _default_analyzer = FeedbackAnalyzer()
    return _default_analyzer


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "FeedbackAnalyzer",
    "FailurePattern",
    "FeedbackSummary",
    "get_feedback_analyzer",
]
