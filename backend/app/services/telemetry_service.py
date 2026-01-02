"""Telemetry Service - Business logic for tool usage tracking.

Handles:
- Tool run event recording
- Fork event management
- Attribution score calculation
- Metric aggregation
- Sybil attack detection
"""
import hashlib
import logging
import math
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_telemetry import (
    ToolManifest,
    ToolRunEvent,
    ForkEvent,
    MetricEvent,
    ToolWorkflowPattern,
    ToolTier,
)
from app.schemas.telemetry_schemas import (
    ToolManifestCreate,
    ToolRunEventCreate,
    ToolRunEventComplete,
    ForkEventCreate,
    AttributionScoreResponse,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Attribution Score Weights (configurable)
# =============================================================================

ATTRIBUTION_WEIGHTS = {
    "diff": 0.20,      # How much was changed
    "test": 0.15,      # Did tests pass
    "usage": 0.25,     # How much is it used
    "revenue": 0.25,   # How much revenue generated
    "quality": 0.15,   # User ratings
}

# Sybil detection thresholds
SYBIL_MIN_DIFF_SCORE = 5.0  # Minimum diff score to not be suspicious
SYBIL_MAX_FORKS_PER_DAY = 10  # Max forks per user per day
SYBIL_MIN_TIME_BETWEEN_FORKS = 60  # Seconds


# =============================================================================
# Tool Manifest Service
# =============================================================================

async def create_tool_manifest(
    db: AsyncSession,
    data: ToolManifestCreate,
    user_id: str,
) -> ToolManifest:
    """Create a new tool manifest."""
    # Check if parent exists for forks
    fork_depth = 0
    if data.parent_tool_id:
        parent = await db.get(ToolManifest, data.parent_tool_id)
        if not parent:
            raise ValueError(f"Parent tool {data.parent_tool_id} not found")
        fork_depth = parent.fork_depth + 1
    
    manifest = ToolManifest(
        tool_key=data.tool_key,
        display_name=data.display_name,
        description=data.description,
        category=data.category,
        input_schema=data.input_schema,
        output_schema=data.output_schema,
        credit_cost=data.credit_cost,
        parent_tool_id=data.parent_tool_id,
        fork_depth=fork_depth,
        created_by=user_id,
        tier=ToolTier.EXPERIMENTAL.value,
    )
    
    db.add(manifest)
    await db.commit()
    await db.refresh(manifest)
    
    logger.info(f"Created tool manifest: {data.tool_key} by {user_id}")
    return manifest


async def get_tool_manifest(
    db: AsyncSession,
    tool_key: str,
) -> Optional[ToolManifest]:
    """Get a tool manifest by key."""
    result = await db.execute(
        select(ToolManifest).where(ToolManifest.tool_key == tool_key)
    )
    return result.scalars().first()


async def get_tool_manifest_by_id(
    db: AsyncSession,
    tool_id: UUID,
) -> Optional[ToolManifest]:
    """Get a tool manifest by ID."""
    return await db.get(ToolManifest, tool_id)


async def increment_tool_usage(
    db: AsyncSession,
    tool_id: UUID,
    credits_earned: int = 0,
) -> None:
    """Increment usage count and revenue for a tool."""
    await db.execute(
        update(ToolManifest)
        .where(ToolManifest.id == tool_id)
        .values(
            usage_count=ToolManifest.usage_count + 1,
            total_revenue=ToolManifest.total_revenue + credits_earned,
        )
    )
    await db.commit()


async def promote_tool_tier(
    db: AsyncSession,
    tool_id: UUID,
    new_tier: ToolTier,
    approved_by: str,
) -> ToolManifest:
    """Promote a tool to a higher tier."""
    manifest = await db.get(ToolManifest, tool_id)
    if not manifest:
        raise ValueError(f"Tool {tool_id} not found")
    
    manifest.tier = new_tier.value
    manifest.approved_at = datetime.utcnow()
    manifest.approved_by = approved_by
    
    await db.commit()
    await db.refresh(manifest)
    
    logger.info(f"Promoted tool {manifest.tool_key} to {new_tier.value}")
    return manifest


# =============================================================================
# Tool Run Event Service
# =============================================================================

async def record_tool_run_start(
    db: AsyncSession,
    data: ToolRunEventCreate,
) -> ToolRunEvent:
    """Record the start of a tool run."""
    # Hash inputs for deduplication
    inputs_hash = hashlib.sha256(
        str(sorted(data.inputs_summary.items())).encode()
    ).hexdigest()[:64]
    
    event = ToolRunEvent(
        tool_id=data.tool_id,
        tool_key=data.tool_key,
        tool_version=data.tool_version,
        user_id=data.user_id,
        session_id=data.session_id,
        status="started",
        inputs_hash=inputs_hash,
        inputs_summary=data.inputs_summary,
        canvas_id=data.canvas_id,
        workflow_position=data.workflow_position,
        previous_tool_id=data.previous_tool_id,
    )
    
    db.add(event)
    await db.commit()
    await db.refresh(event)
    
    logger.debug(f"Started tool run: {event.id} for {data.tool_key}")
    return event


async def complete_tool_run(
    db: AsyncSession,
    event_id: UUID,
    data: ToolRunEventComplete,
) -> ToolRunEvent:
    """Complete a tool run with results."""
    event = await db.get(ToolRunEvent, event_id)
    if not event:
        raise ValueError(f"Tool run event {event_id} not found")
    
    event.status = data.status
    event.outputs_summary = data.outputs_summary
    event.error_message = data.error_message
    event.latency_ms = data.latency_ms
    event.token_usage = data.token_usage
    event.cost_usd_est = data.cost_usd_est
    event.credits_charged = data.credits_charged
    event.credits_refunded = data.credits_refunded
    event.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(event)
    
    # Increment tool usage if successful
    if data.status == "success":
        await increment_tool_usage(db, event.tool_id, data.credits_charged)
    
    logger.debug(f"Completed tool run: {event_id} with status {data.status}")
    return event


async def add_tool_run_feedback(
    db: AsyncSession,
    event_id: UUID,
    rating: int,
    feedback: Optional[str] = None,
) -> ToolRunEvent:
    """Add user feedback to a tool run."""
    event = await db.get(ToolRunEvent, event_id)
    if not event:
        raise ValueError(f"Tool run event {event_id} not found")
    
    event.user_rating = rating
    event.user_feedback = feedback
    
    await db.commit()
    await db.refresh(event)
    
    # Update tool quality rating
    await update_tool_quality_rating(db, event.tool_id)
    
    return event


async def update_tool_quality_rating(
    db: AsyncSession,
    tool_id: UUID,
) -> None:
    """Recalculate average quality rating for a tool."""
    result = await db.execute(
        select(func.avg(ToolRunEvent.user_rating))
        .where(ToolRunEvent.tool_id == tool_id)
        .where(ToolRunEvent.user_rating.is_not(None))
    )
    avg_rating = result.scalar()
    
    if avg_rating is not None:
        await db.execute(
            update(ToolManifest)
            .where(ToolManifest.id == tool_id)
            .values(quality_rating=float(avg_rating))
        )
        await db.commit()


# =============================================================================
# Fork Event Service
# =============================================================================

async def create_fork_event(
    db: AsyncSession,
    data: ForkEventCreate,
) -> ForkEvent:
    """Create a new fork event with Sybil detection."""
    # Get parent tool to determine fork depth
    parent = await db.get(ToolManifest, data.parent_tool_id)
    if not parent:
        raise ValueError(f"Parent tool {data.parent_tool_id} not found")
    
    # Calculate diff score
    total_changes = data.diff_lines_added + data.diff_lines_removed + data.diff_lines_modified
    diff_score = min(100, 100 * (1 - math.exp(-total_changes / 50))) if total_changes > 0 else 0
    
    # Check for Sybil attack patterns
    is_suspicious, suspicion_reason = await check_sybil_patterns(
        db, data.forker_id, diff_score
    )
    
    event = ForkEvent(
        parent_tool_id=data.parent_tool_id,
        child_tool_id=data.child_tool_id,
        fork_depth=parent.fork_depth + 1,
        forker_id=data.forker_id,
        fork_reason=data.fork_reason,
        diff_lines_added=data.diff_lines_added,
        diff_lines_removed=data.diff_lines_removed,
        diff_lines_modified=data.diff_lines_modified,
        diff_score=diff_score,
        is_suspicious=is_suspicious,
        suspicion_reason=suspicion_reason,
    )
    
    db.add(event)
    
    # Increment parent's fork count
    parent.fork_count += 1
    
    await db.commit()
    await db.refresh(event)
    
    if is_suspicious:
        logger.warning(f"Suspicious fork detected: {event.id} - {suspicion_reason}")
    else:
        logger.info(f"Created fork event: {event.id}")
    
    return event


async def check_sybil_patterns(
    db: AsyncSession,
    forker_id: str,
    diff_score: float,
) -> tuple[bool, Optional[str]]:
    """Check for Sybil attack patterns."""
    # Check 1: Minimum diff score
    if diff_score < SYBIL_MIN_DIFF_SCORE:
        return True, f"Diff score {diff_score:.1f} below minimum {SYBIL_MIN_DIFF_SCORE}"
    
    # Check 2: Too many forks in a day
    day_ago = datetime.utcnow() - timedelta(days=1)
    result = await db.execute(
        select(func.count(ForkEvent.id))
        .where(ForkEvent.forker_id == forker_id)
        .where(ForkEvent.created_at >= day_ago)
    )
    fork_count = result.scalar() or 0
    
    if fork_count >= SYBIL_MAX_FORKS_PER_DAY:
        return True, f"Too many forks ({fork_count}) in 24 hours"
    
    # Check 3: Forks too quick in succession
    result = await db.execute(
        select(ForkEvent.created_at)
        .where(ForkEvent.forker_id == forker_id)
        .order_by(ForkEvent.created_at.desc())
        .limit(1)
    )
    last_fork = result.scalar()
    
    if last_fork:
        time_diff = (datetime.utcnow() - last_fork).total_seconds()
        if time_diff < SYBIL_MIN_TIME_BETWEEN_FORKS:
            return True, f"Fork created too quickly ({time_diff:.0f}s) after last fork"
    
    return False, None


async def update_fork_test_result(
    db: AsyncSession,
    fork_id: UUID,
    test_passed: bool,
    test_details: dict = None,
) -> ForkEvent:
    """Update fork with test results."""
    event = await db.get(ForkEvent, fork_id)
    if not event:
        raise ValueError(f"Fork event {fork_id} not found")
    
    event.test_passed = test_passed
    event.test_run_at = datetime.utcnow()
    event.test_details = test_details or {}
    
    # Also update the child tool's test_pass_rate
    child = await db.get(ToolManifest, event.child_tool_id)
    if child:
        child.test_pass_rate = 100.0 if test_passed else 0.0
    
    await db.commit()
    await db.refresh(event)
    
    return event


# =============================================================================
# Attribution Score Calculation
# =============================================================================

async def calculate_attribution_score(
    db: AsyncSession,
    fork_id: UUID,
) -> AttributionScoreResponse:
    """Calculate attribution score for a fork.
    
    Score = weighted combination of:
    - diff_score: How much was changed (20%)
    - test_score: Did tests pass (15%)
    - usage_score: How much is the forked tool used (25%)
    - revenue_score: How much revenue generated (25%)
    - quality_score: User ratings (15%)
    """
    fork = await db.get(ForkEvent, fork_id)
    if not fork:
        raise ValueError(f"Fork {fork_id} not found")
    
    child = await db.get(ToolManifest, fork.child_tool_id)
    if not child:
        raise ValueError(f"Child tool {fork.child_tool_id} not found")
    
    # Calculate component scores
    diff_score = fork.diff_score  # Already 0-100
    test_score = 100.0 if fork.test_passed else 0.0
    
    # Usage score (normalized with sigmoid)
    usage_score = min(100, 100 * (1 - math.exp(-child.usage_count / 100)))
    
    # Revenue score (normalized with sigmoid)
    revenue_score = min(100, 100 * (1 - math.exp(-child.total_revenue / 1000)))
    
    # Quality score (1-5 stars → 0-100)
    quality_score = (child.quality_rating or 3.0) * 20
    
    # Calculate weighted total
    total_score = (
        diff_score * ATTRIBUTION_WEIGHTS["diff"] +
        test_score * ATTRIBUTION_WEIGHTS["test"] +
        usage_score * ATTRIBUTION_WEIGHTS["usage"] +
        revenue_score * ATTRIBUTION_WEIGHTS["revenue"] +
        quality_score * ATTRIBUTION_WEIGHTS["quality"]
    )
    
    # Update fork with calculated score
    fork.attribution_score = total_score
    fork.attribution_calculated_at = datetime.utcnow()
    await db.commit()
    
    logger.info(f"Calculated attribution score for fork {fork_id}: {total_score:.2f}")
    
    return AttributionScoreResponse(
        fork_id=fork_id,
        tool_id=fork.child_tool_id,
        diff_score=diff_score,
        test_score=test_score,
        usage_score=usage_score,
        revenue_score=revenue_score,
        quality_score=quality_score,
        total_score=total_score,
        weights=ATTRIBUTION_WEIGHTS,
        calculated_at=datetime.utcnow(),
    )


# =============================================================================
# Metric Aggregation Service
# =============================================================================

async def aggregate_tool_metrics(
    db: AsyncSession,
    tool_id: UUID,
    period_type: str = "daily",
) -> None:
    """Aggregate metrics for a tool for the given period."""
    now = datetime.utcnow()
    
    if period_type == "hourly":
        period_start = now.replace(minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(hours=1)
    elif period_type == "daily":
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=1)
    elif period_type == "weekly":
        # Start of week (Monday)
        period_start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        period_end = period_start + timedelta(weeks=1)
    else:
        raise ValueError(f"Invalid period_type: {period_type}")
    
    # Get tool info
    tool = await db.get(ToolManifest, tool_id)
    if not tool:
        return
    
    # Aggregate runs
    result = await db.execute(
        select(
            func.count(ToolRunEvent.id).label("count"),
            func.sum(ToolRunEvent.credits_charged).label("revenue"),
            func.avg(ToolRunEvent.latency_ms).label("avg_latency"),
        )
        .where(ToolRunEvent.tool_id == tool_id)
        .where(ToolRunEvent.created_at >= period_start)
        .where(ToolRunEvent.created_at < period_end)
    )
    row = result.first()
    
    if row and row.count > 0:
        metric = MetricEvent(
            metric_key="tool_usage",
            metric_type="counter",
            period_start=period_start,
            period_end=period_end,
            period_type=period_type,
            dimension_type="tool",
            dimension_value=tool.tool_key,
            count=row.count,
            sum_value=row.revenue or 0,
            avg_value=row.avg_latency,
            meta={"tool_id": str(tool_id), "category": tool.category},
        )
        db.add(metric)
        await db.commit()
        
        logger.debug(f"Aggregated metrics for tool {tool.tool_key}: {row.count} runs")


async def get_tool_analytics(
    db: AsyncSession,
    tool_id: UUID,
    days: int = 30,
) -> dict:
    """Get analytics summary for a tool."""
    tool = await db.get(ToolManifest, tool_id)
    if not tool:
        raise ValueError(f"Tool {tool_id} not found")
    
    since = datetime.utcnow() - timedelta(days=days)
    
    # Get run stats
    result = await db.execute(
        select(
            func.count(ToolRunEvent.id).label("total"),
            func.count(ToolRunEvent.id).filter(ToolRunEvent.status == "success").label("success"),
            func.count(ToolRunEvent.id).filter(ToolRunEvent.status == "failed").label("failed"),
            func.avg(ToolRunEvent.latency_ms).label("avg_latency"),
            func.sum(ToolRunEvent.credits_charged).label("credits"),
            func.avg(ToolRunEvent.user_rating).label("avg_rating"),
            func.count(ToolRunEvent.user_rating).label("rating_count"),
        )
        .where(ToolRunEvent.tool_id == tool_id)
        .where(ToolRunEvent.created_at >= since)
    )
    row = result.first()
    
    total = row.total or 0
    success = row.success or 0
    
    return {
        "tool_id": str(tool_id),
        "tool_key": tool.tool_key,
        "period_days": days,
        "total_runs": total,
        "successful_runs": success,
        "failed_runs": row.failed or 0,
        "success_rate": (success / total * 100) if total > 0 else 0,
        "avg_latency_ms": row.avg_latency,
        "total_credits": row.credits or 0,
        "avg_rating": row.avg_rating,
        "rating_count": row.rating_count or 0,
        "fork_count": tool.fork_count,
        "tier": tool.tier,
    }


# =============================================================================
# Workflow Pattern Detection
# =============================================================================

async def record_workflow_pattern(
    db: AsyncSession,
    tool_sequence: list[str],
    completion_rate: float = 1.0,
    user_rating: Optional[float] = None,
) -> None:
    """Record or update a workflow pattern."""
    if len(tool_sequence) < 2:
        return
    
    # Create pattern key from sequence
    pattern_key = hashlib.sha256(
        ",".join(tool_sequence).encode()
    ).hexdigest()[:64]
    
    # Check if pattern exists
    result = await db.execute(
        select(ToolWorkflowPattern).where(ToolWorkflowPattern.pattern_key == pattern_key)
    )
    pattern = result.scalars().first()
    
    if pattern:
        # Update existing
        pattern.frequency += 1
        # Running average of completion rate
        pattern.avg_completion_rate = (
            (pattern.avg_completion_rate * (pattern.frequency - 1) + completion_rate)
            / pattern.frequency
        )
        if user_rating is not None:
            if pattern.avg_user_rating is not None:
                pattern.avg_user_rating = (
                    (pattern.avg_user_rating * (pattern.frequency - 1) + user_rating)
                    / pattern.frequency
                )
            else:
                pattern.avg_user_rating = user_rating
    else:
        # Create new
        pattern = ToolWorkflowPattern(
            pattern_key=pattern_key,
            tool_sequence=tool_sequence,
            frequency=1,
            avg_completion_rate=completion_rate,
            avg_user_rating=user_rating,
        )
        db.add(pattern)
    
    await db.commit()
