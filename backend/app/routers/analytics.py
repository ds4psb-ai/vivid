"""Analytics API router for tracking user events."""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import AnalyticsEvent


router = APIRouter(tags=["analytics"])


# --- Pydantic Schemas ---

class EventRequest(BaseModel):
    """Request to track an analytics event."""
    event_type: str  # evidence_ref_opened, template_seeded, template_version_swapped
    template_id: Optional[str] = None
    capsule_id: Optional[str] = None
    run_id: Optional[str] = None
    evidence_ref: Optional[str] = None
    meta: Optional[dict] = None


class EventResponse(BaseModel):
    """Response after tracking an event."""
    id: str
    event_type: str
    created_at: datetime


class MetricsResponse(BaseModel):
    """Pilot metrics for Go/No-Go decision."""
    evidence_click_count: int
    template_seed_count: int
    template_swap_count: int
    evidence_click_rate: Optional[float] = None
    period_start: datetime
    period_end: datetime


# --- API Endpoints ---

@router.post("/events", response_model=EventResponse)
async def track_event(
    request: EventRequest,
    user_id: str = "anonymous",
    db: AsyncSession = Depends(get_db),
):
    """Track an analytics event."""
    valid_events = [
        "evidence_ref_opened",
        "template_seeded",
        "template_version_swapped",
        "template_run_started",
        "template_run_completed",
    ]
    
    if request.event_type not in valid_events:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event_type. Must be one of: {valid_events}"
        )
    
    event = AnalyticsEvent(
        event_type=request.event_type,
        user_id=user_id,
        template_id=uuid.UUID(request.template_id) if request.template_id else None,
        capsule_id=request.capsule_id,
        run_id=uuid.UUID(request.run_id) if request.run_id else None,
        evidence_ref=request.evidence_ref,
        meta=request.meta,
    )
    
    db.add(event)
    await db.commit()
    await db.refresh(event)
    
    return EventResponse(
        id=str(event.id),
        event_type=event.event_type,
        created_at=event.created_at,
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_pilot_metrics(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
):
    """Get pilot metrics for the specified period."""
    from datetime import timedelta
    
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=days)
    
    # Count events by type
    result = await db.execute(
        select(
            AnalyticsEvent.event_type,
            func.count(AnalyticsEvent.id).label("count")
        )
        .where(AnalyticsEvent.created_at >= period_start)
        .group_by(AnalyticsEvent.event_type)
    )
    counts = {row.event_type: row.count for row in result}
    
    evidence_clicks = counts.get("evidence_ref_opened", 0)
    template_seeds = counts.get("template_seeded", 0)
    template_swaps = counts.get("template_version_swapped", 0)
    
    # Calculate click rate (evidence clicks / template views)
    total_template_events = template_seeds + template_swaps
    click_rate = (evidence_clicks / total_template_events) if total_template_events > 0 else None
    
    return MetricsResponse(
        evidence_click_count=evidence_clicks,
        template_seed_count=template_seeds,
        template_swap_count=template_swaps,
        evidence_click_rate=click_rate,
        period_start=period_start,
        period_end=period_end,
    )
