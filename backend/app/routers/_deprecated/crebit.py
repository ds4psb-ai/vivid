"""Crebit ATC course application endpoints."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import CrebitApplication


router = APIRouter(prefix="/crebit", tags=["crebit"])


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────────────────────────────────────────

class ApplicationCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    track: str  # 'A' or 'B'


class ApplicationResponse(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str
    track: str
    status: str
    cohort: str
    created_at: datetime

    class Config:
        from_attributes = True


class ApplicationDetail(ApplicationResponse):
    payment_id: Optional[str] = None
    paid_amount: Optional[int] = None
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None
    updated_at: datetime


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    payment_id: Optional[str] = None
    paid_amount: Optional[int] = None
    paid_at: Optional[datetime] = None


class ApplicationListResponse(BaseModel):
    items: list[ApplicationResponse]
    total: int
    offset: int
    limit: int


class StatsResponse(BaseModel):
    total: int
    by_status: dict[str, int]
    by_track: dict[str, int]
    by_cohort: dict[str, int]


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/apply", response_model=ApplicationResponse)
async def apply(
    data: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Submit a new Crebit ATC application."""
    # Validate track
    if data.track not in ("A", "B"):
        raise HTTPException(status_code=400, detail="Track must be 'A' or 'B'")
    
    # Create application
    application = CrebitApplication(
        name=data.name,
        email=data.email,
        phone=data.phone,
        track=data.track,
        status="pending",
        cohort="1기",
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    
    return application


@router.get("/applications", response_model=ApplicationListResponse)
async def list_applications(
    status: Optional[str] = Query(None, description="Filter by status"),
    cohort: Optional[str] = Query(None, description="Filter by cohort"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all applications (Admin only)."""
    # Build query
    query = select(CrebitApplication).order_by(CrebitApplication.created_at.desc())
    count_query = select(func.count(CrebitApplication.id))
    
    if status:
        query = query.where(CrebitApplication.status == status)
        count_query = count_query.where(CrebitApplication.status == status)
    
    if cohort:
        query = query.where(CrebitApplication.cohort == cohort)
        count_query = count_query.where(CrebitApplication.cohort == cohort)
    
    # Execute
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return ApplicationListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/applications/{application_id}", response_model=ApplicationDetail)
async def get_application(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single application by ID."""
    result = await db.execute(
        select(CrebitApplication).where(CrebitApplication.id == application_id)
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return application


@router.patch("/applications/{application_id}", response_model=ApplicationDetail)
async def update_application(
    application_id: UUID,
    data: ApplicationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an application (Admin only)."""
    result = await db.execute(
        select(CrebitApplication).where(CrebitApplication.id == application_id)
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(application, key, value)
    
    application.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(application)
    
    return application


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get application statistics (Admin only)."""
    # Total count
    total_result = await db.execute(select(func.count(CrebitApplication.id)))
    total = total_result.scalar() or 0
    
    # By status
    status_result = await db.execute(
        select(CrebitApplication.status, func.count(CrebitApplication.id))
        .group_by(CrebitApplication.status)
    )
    by_status = {row[0]: row[1] for row in status_result.all()}
    
    # By track
    track_result = await db.execute(
        select(CrebitApplication.track, func.count(CrebitApplication.id))
        .group_by(CrebitApplication.track)
    )
    by_track = {row[0]: row[1] for row in track_result.all()}
    
    # By cohort
    cohort_result = await db.execute(
        select(CrebitApplication.cohort, func.count(CrebitApplication.id))
        .group_by(CrebitApplication.cohort)
    )
    by_cohort = {row[0]: row[1] for row in cohort_result.all()}
    
    return StatsResponse(
        total=total,
        by_status=by_status,
        by_track=by_track,
        by_cohort=by_cohort,
    )
