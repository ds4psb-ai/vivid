"""Pattern Lift calculation service.

Calculates lift metrics for patterns based on performance data.
Lift formula: Lift = (variant - parent) / parent

Reference: 07_EXECUTION_PLAN_2025-12.md Phase 2.1
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, select

from app.database import AsyncSessionLocal
from app.models import (
    CapsuleRun,
    GenerationRun,
    Pattern,
    PatternTrace,
    TemplateLearningRun,
)


@dataclass
class PatternLiftResult:
    """Result of pattern lift calculation."""
    pattern_id: str
    pattern_name: str
    pattern_type: str
    parent_metric: float
    variant_metric: float
    lift: float
    lift_pct: float
    sample_size: int
    source_ids: List[str]
    calculated_at: datetime


def calculate_lift(parent: float, variant: float) -> Tuple[float, float]:
    """
    Calculate lift value and percentage.
    
    Args:
        parent: Parent/baseline metric value
        variant: Variant/treatment metric value
    
    Returns:
        Tuple of (lift_value, lift_percentage)
    
    Example:
        >>> calculate_lift(0.5, 0.7)
        (0.4, 40.0)  # 40% improvement
    """
    if parent == 0:
        return (0.0, 0.0) if variant == 0 else (float('inf'), float('inf'))
    
    lift = (variant - parent) / parent
    lift_pct = lift * 100
    return (round(lift, 4), round(lift_pct, 2))


async def get_pattern_performance_metrics(
    pattern_id: str,
    *,
    metric_key: str = "reward_score",
) -> Dict[str, float]:
    """
    Get aggregated performance metrics for a pattern from learning runs.
    
    Uses TemplateLearningRun.reward_score as primary metric.
    """
    async with AsyncSessionLocal() as session:
        # Get all traces for this pattern
        traces_result = await session.execute(
            select(PatternTrace.source_id).where(PatternTrace.pattern_id == pattern_id)
        )
        source_ids = [row[0] for row in traces_result.all()]
        
        if not source_ids:
            return {"mean": 0.0, "count": 0, "source_ids": []}
        
        # Get learning runs that used these sources
        runs_result = await session.execute(
            select(
                func.avg(TemplateLearningRun.reward_score),
                func.count(TemplateLearningRun.id),
            ).where(
                TemplateLearningRun.reward_score.isnot(None),
            )
        )
        row = runs_result.first()
        mean_score = float(row[0]) if row and row[0] else 0.0
        count = int(row[1]) if row and row[1] else 0
        
        return {
            "mean": round(mean_score, 4),
            "count": count,
            "source_ids": source_ids,
        }


async def calculate_pattern_lift_report(
    *,
    parent_pattern_id: Optional[str] = None,
    metric_key: str = "reward_score",
    min_sample_size: int = 3,
) -> List[PatternLiftResult]:
    """
    Calculate lift report for all patterns.
    
    If parent_pattern_id is provided, calculates lift relative to that parent.
    Otherwise, calculates lift relative to global average.
    
    Args:
        parent_pattern_id: Optional pattern ID to use as baseline
        metric_key: Which metric to use for comparison (default: reward_score)
        min_sample_size: Minimum samples required for valid lift calculation
    
    Returns:
        List of PatternLiftResult objects
    """
    async with AsyncSessionLocal() as session:
        # Get all promoted patterns
        patterns_result = await session.execute(
            select(Pattern).where(Pattern.status == "promoted")
        )
        patterns = patterns_result.scalars().all()
        
        if not patterns:
            # Fall back to validated patterns
            patterns_result = await session.execute(
                select(Pattern).where(Pattern.status == "validated")
            )
            patterns = patterns_result.scalars().all()
        
        # Calculate parent baseline
        if parent_pattern_id:
            parent_metrics = await get_pattern_performance_metrics(
                parent_pattern_id,
                metric_key=metric_key,
            )
            parent_mean = parent_metrics["mean"]
        else:
            # Use global average as baseline
            global_result = await session.execute(
                select(func.avg(TemplateLearningRun.reward_score)).where(
                    TemplateLearningRun.reward_score.isnot(None)
                )
            )
            row = global_result.first()
            parent_mean = float(row[0]) if row and row[0] else 0.0
        
        results: List[PatternLiftResult] = []
        
        for pattern in patterns:
            metrics = await get_pattern_performance_metrics(
                str(pattern.id),
                metric_key=metric_key,
            )
            
            if metrics["count"] < min_sample_size:
                continue
            
            lift, lift_pct = calculate_lift(parent_mean, metrics["mean"])
            
            results.append(
                PatternLiftResult(
                    pattern_id=str(pattern.id),
                    pattern_name=pattern.name,
                    pattern_type=pattern.pattern_type,
                    parent_metric=parent_mean,
                    variant_metric=metrics["mean"],
                    lift=lift,
                    lift_pct=lift_pct,
                    sample_size=metrics["count"],
                    source_ids=metrics["source_ids"],
                    calculated_at=datetime.utcnow(),
                )
            )
        
        # Sort by lift descending
        results.sort(key=lambda x: x.lift, reverse=True)
        
        return results


async def get_top_patterns_by_lift(
    limit: int = 10,
    *,
    min_lift: float = 0.0,
) -> List[PatternLiftResult]:
    """
    Get top patterns ranked by lift.
    
    Args:
        limit: Maximum number of patterns to return
        min_lift: Minimum lift threshold to include
    
    Returns:
        Top N patterns by lift
    """
    results = await calculate_pattern_lift_report()
    filtered = [r for r in results if r.lift >= min_lift]
    return filtered[:limit]
