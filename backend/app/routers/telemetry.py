"""Telemetry API Router - Endpoints for tool usage tracking.

Complete REST API for telemetry system with proper error handling.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models_telemetry import ToolManifest, ToolRunEvent, ForkEvent, MetricEvent
from app.schemas.telemetry_schemas import (
    ToolManifestCreate,
    ToolManifestUpdate,
    ToolManifestResponse,
    ToolRunEventCreate,
    ToolRunEventComplete,
    ToolRunEventResponse,
    ToolRunFeedback,
    ForkEventCreate,
    ForkEventResponse,
    ForkTestResult,
    AttributionScoreResponse,
    MetricEventResponse,
    ToolAnalytics,
)
from app.services import telemetry_service

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# Tool Manifest Endpoints
# =============================================================================

@router.post("/tools", response_model=ToolManifestResponse, status_code=201)
async def create_tool(
    data: ToolManifestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new tool manifest.
    
    Creates a new tool in the ecosystem. Tools start at EXPERIMENTAL tier
    and can be promoted to VERIFIED and CERTIFIED based on metrics.
    """
    # Check if tool_key already exists
    existing = await telemetry_service.get_tool_manifest(db, data.tool_key)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Tool with key '{data.tool_key}' already exists"
        )
    
    try:
        manifest = await telemetry_service.create_tool_manifest(db, data, current_user["id"])
        return manifest
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tools/{tool_key}", response_model=ToolManifestResponse)
async def get_tool(
    tool_key: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a tool manifest by key."""
    manifest = await telemetry_service.get_tool_manifest(db, tool_key)
    if not manifest:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_key}' not found")
    return manifest


@router.get("/tools", response_model=list[ToolManifestResponse])
async def list_tools(
    category: Optional[str] = None,
    tier: Optional[str] = None,
    created_by: Optional[str] = None,
    is_active: bool = True,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List tools with optional filters."""
    query = select(ToolManifest).where(ToolManifest.is_active == is_active)
    
    if category:
        query = query.where(ToolManifest.category == category.lower())
    if tier:
        query = query.where(ToolManifest.tier == tier.lower())
    if created_by:
        query = query.where(ToolManifest.created_by == created_by)
    
    query = query.order_by(ToolManifest.usage_count.desc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/tools/{tool_id}", response_model=ToolManifestResponse)
async def update_tool(
    tool_id: UUID,
    data: ToolManifestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update a tool manifest (owner only)."""
    manifest = await telemetry_service.get_tool_manifest_by_id(db, tool_id)
    if not manifest:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    if manifest.created_by != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this tool")
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(manifest, key, value)
    
    await db.commit()
    await db.refresh(manifest)
    return manifest


@router.get("/tools/{tool_id}/analytics", response_model=dict)
async def get_tool_analytics(
    tool_id: UUID,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics for a tool."""
    try:
        analytics = await telemetry_service.get_tool_analytics(db, tool_id, days)
        return analytics
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Tool Run Endpoints
# =============================================================================

@router.post("/runs", response_model=ToolRunEventResponse, status_code=201)
async def start_tool_run(
    data: ToolRunEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Record the start of a tool run.
    
    Call this when a tool execution begins. Returns an event ID
    that should be used to complete the run later.
    """
    # Override user_id if provided
    if current_user["id"] and not data.user_id:
        data.user_id = current_user["id"]
    
    event = await telemetry_service.record_tool_run_start(db, data)
    return event


@router.patch("/runs/{event_id}", response_model=ToolRunEventResponse)
async def complete_tool_run(
    event_id: UUID,
    data: ToolRunEventComplete,
    db: AsyncSession = Depends(get_db),
):
    """Complete a tool run with results.
    
    Call this when a tool execution finishes (success or failure).
    """
    try:
        event = await telemetry_service.complete_tool_run(db, event_id, data)
        return event
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/runs/{event_id}/feedback", response_model=ToolRunEventResponse)
async def add_run_feedback(
    event_id: UUID,
    data: ToolRunFeedback,
    db: AsyncSession = Depends(get_db),
):
    """Add user feedback to a tool run."""
    try:
        event = await telemetry_service.add_tool_run_feedback(
            db, event_id, data.rating, data.feedback
        )
        return event
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/runs", response_model=list[ToolRunEventResponse])
async def list_runs(
    tool_key: Optional[str] = None,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List tool runs with optional filters."""
    query = select(ToolRunEvent)
    
    if tool_key:
        query = query.where(ToolRunEvent.tool_key == tool_key)
    if user_id:
        query = query.where(ToolRunEvent.user_id == user_id)
    if status:
        query = query.where(ToolRunEvent.status == status)
    if since:
        query = query.where(ToolRunEvent.created_at >= since)
    
    query = query.order_by(ToolRunEvent.created_at.desc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


# =============================================================================
# Fork Endpoints
# =============================================================================

@router.post("/forks", response_model=ForkEventResponse, status_code=201)
async def create_fork(
    data: ForkEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a fork event.
    
    Records a fork of an existing tool. Includes Sybil attack detection
    that may flag suspicious forks.
    """
    # Override forker_id with authenticated user
    data.forker_id = current_user["id"]
    
    try:
        event = await telemetry_service.create_fork_event(db, data)
        
        # Warn if suspicious
        if event.is_suspicious:
            logger.warning(f"Suspicious fork created by {current_user['id']}: {event.suspicion_reason}")
        
        return event
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/forks/{fork_id}", response_model=ForkEventResponse)
async def get_fork(
    fork_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a fork event by ID."""
    fork = await db.get(ForkEvent, fork_id)
    if not fork:
        raise HTTPException(status_code=404, detail="Fork not found")
    return fork


@router.post("/forks/{fork_id}/test", response_model=ForkEventResponse)
async def submit_fork_test(
    fork_id: UUID,
    data: ForkTestResult,
    db: AsyncSession = Depends(get_db),
):
    """Submit test results for a fork.
    
    Used to update fork with automated test results.
    Test passing is a component of the attribution score.
    """
    try:
        fork = await telemetry_service.update_fork_test_result(
            db, fork_id, data.test_passed, data.test_details
        )
        return fork
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/forks/{fork_id}/attribution", response_model=AttributionScoreResponse)
async def calculate_attribution(
    fork_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Calculate attribution score for a fork.
    
    Computes the attribution score based on:
    - Diff score (20%): How much was changed
    - Test score (15%): Whether tests pass
    - Usage score (25%): How much the fork is used
    - Revenue score (25%): How much revenue generated
    - Quality score (15%): User ratings
    """
    try:
        score = await telemetry_service.calculate_attribution_score(db, fork_id)
        return score
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/forks", response_model=list[ForkEventResponse])
async def list_forks(
    parent_tool_id: Optional[UUID] = None,
    forker_id: Optional[str] = None,
    is_suspicious: Optional[bool] = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List forks with optional filters."""
    query = select(ForkEvent)
    
    if parent_tool_id:
        query = query.where(ForkEvent.parent_tool_id == parent_tool_id)
    if forker_id:
        query = query.where(ForkEvent.forker_id == forker_id)
    if is_suspicious is not None:
        query = query.where(ForkEvent.is_suspicious == is_suspicious)
    
    query = query.order_by(ForkEvent.created_at.desc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


# =============================================================================
# Metrics Endpoints
# =============================================================================

@router.get("/metrics", response_model=list[MetricEventResponse])
async def list_metrics(
    metric_key: Optional[str] = None,
    dimension_type: Optional[str] = None,
    dimension_value: Optional[str] = None,
    period_type: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
):
    """List aggregated metrics."""
    query = select(MetricEvent)
    
    if metric_key:
        query = query.where(MetricEvent.metric_key == metric_key)
    if dimension_type:
        query = query.where(MetricEvent.dimension_type == dimension_type)
    if dimension_value:
        query = query.where(MetricEvent.dimension_value == dimension_value)
    if period_type:
        query = query.where(MetricEvent.period_type == period_type)
    if since:
        query = query.where(MetricEvent.period_start >= since)
    
    query = query.order_by(MetricEvent.period_start.desc()).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/metrics/aggregate/{tool_id}")
async def trigger_metric_aggregation(
    tool_id: UUID,
    period_type: str = Query(default="daily"),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger metric aggregation for a tool.
    
    Normally this runs automatically via background jobs.
    """
    if period_type not in ["hourly", "daily", "weekly"]:
        raise HTTPException(status_code=400, detail="Invalid period_type")
    
    await telemetry_service.aggregate_tool_metrics(db, tool_id, period_type)
    return {"status": "aggregated", "tool_id": str(tool_id), "period_type": period_type}


# =============================================================================
# Dashboard Endpoints
# =============================================================================

@router.get("/dashboard/overview")
async def get_dashboard_overview(
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Get telemetry dashboard overview."""
    since = datetime.utcnow() - timedelta(days=days)
    
    # Tool counts by tier
    tier_result = await db.execute(
        select(ToolManifest.tier, func.count(ToolManifest.id))
        .where(ToolManifest.is_active == True)
        .group_by(ToolManifest.tier)
    )
    tier_counts = dict(tier_result.all())
    
    # Run stats
    run_result = await db.execute(
        select(
            func.count(ToolRunEvent.id).label("total"),
            func.count(ToolRunEvent.id).filter(ToolRunEvent.status == "success").label("success"),
            func.sum(ToolRunEvent.credits_charged).label("revenue"),
        )
        .where(ToolRunEvent.created_at >= since)
    )
    run_stats = run_result.first()
    
    # Fork stats
    fork_result = await db.execute(
        select(
            func.count(ForkEvent.id).label("total"),
            func.count(ForkEvent.id).filter(ForkEvent.is_suspicious == True).label("suspicious"),
        )
        .where(ForkEvent.created_at >= since)
    )
    fork_stats = fork_result.first()
    
    # Top tools
    top_tools_result = await db.execute(
        select(ToolManifest.tool_key, ToolManifest.usage_count)
        .where(ToolManifest.is_active == True)
        .order_by(ToolManifest.usage_count.desc())
        .limit(10)
    )
    top_tools = [{"tool_key": r[0], "usage_count": r[1]} for r in top_tools_result.all()]
    
    return {
        "period_days": days,
        "tools": {
            "by_tier": tier_counts,
            "total": sum(tier_counts.values()),
            "top": top_tools,
        },
        "runs": {
            "total": run_stats.total or 0,
            "successful": run_stats.success or 0,
            "success_rate": ((run_stats.success or 0) / (run_stats.total or 1)) * 100,
            "revenue_credits": run_stats.revenue or 0,
        },
        "forks": {
            "total": fork_stats.total or 0,
            "suspicious": fork_stats.suspicious or 0,
        },
    }


@router.get("/dashboard/categories")
async def get_category_stats(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get stats by category."""
    since = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(
            ToolManifest.category,
            func.count(ToolManifest.id).label("tool_count"),
            func.sum(ToolManifest.usage_count).label("total_usage"),
            func.sum(ToolManifest.total_revenue).label("total_revenue"),
            func.avg(ToolManifest.quality_rating).label("avg_rating"),
        )
        .where(ToolManifest.is_active == True)
        .group_by(ToolManifest.category)
        .order_by(func.sum(ToolManifest.total_revenue).desc())
    )
    
    categories = []
    for row in result.all():
        categories.append({
            "category": row.category,
            "tool_count": row.tool_count,
            "total_usage": row.total_usage or 0,
            "total_revenue": row.total_revenue or 0,
            "avg_rating": round(row.avg_rating, 2) if row.avg_rating else None,
        })
    
    return {"period_days": days, "categories": categories}
