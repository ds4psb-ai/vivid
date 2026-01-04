"""Human Cloud API Router.

Endpoints for the Human Cloud creative marketplace:
- Creator registration and discovery
- Request creation and browsing
- Assignment workflow
- Delivery and payment
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models_humancloud import (
    CreativeRequest,
    CreatorProfile,
    Assignment,
    EvidenceLog,
    Delivery,
    RequestStatus,
    AssignmentStatus,
)
from app.services import humancloud_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/humancloud", tags=["Human Cloud"])


# =============================================================================
# Schemas
# =============================================================================

class CreatorProfileCreate(BaseModel):
    display_name: str = Field(..., max_length=100)
    bio: Optional[str] = None
    categories: List[str] = Field(default=["video_creative"])
    skills: Optional[List[str]] = None
    hourly_rate: Optional[int] = None
    min_budget: int = 100


class CreatorProfileResponse(BaseModel):
    id: UUID
    user_id: str
    display_name: str
    bio: Optional[str]
    categories: List[str]
    skills: List[str]
    completed_count: int
    avg_rating: Optional[float]
    is_available: bool
    is_verified: bool

    class Config:
        from_attributes = True


class RequestCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: str
    budget_credits: int = Field(..., gt=0)
    category: str = "video_creative"
    requirements: Optional[dict] = None
    deadline: Optional[datetime] = None


class RequestResponse(BaseModel):
    id: UUID
    client_id: str
    title: str
    description: str
    category: str
    budget_credits: int
    status: str
    deadline: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AssignmentCreate(BaseModel):
    creator_id: UUID
    agreed_credits: int
    agreed_deadline: Optional[datetime] = None
    agreed_revisions: int = 1


class AssignmentResponse(BaseModel):
    id: UUID
    request_id: UUID
    creator_id: UUID
    status: str
    agreed_credits: int
    agreed_deadline: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class DeliveryCreate(BaseModel):
    files: List[str]
    notes: Optional[str] = None


class DeliveryResponse(BaseModel):
    id: UUID
    assignment_id: UUID
    version: int
    files: List[str]
    status: str
    submitted_at: datetime

    class Config:
        from_attributes = True


class DeliveryApproval(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


class EvidenceLogResponse(BaseModel):
    id: UUID
    event_type: str
    title: str
    description: Optional[str]
    actor_role: str
    attachments: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Creator Endpoints
# =============================================================================

@router.post("/creators", response_model=CreatorProfileResponse)
async def register_as_creator(
    data: CreatorProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Register as a creator on Human Cloud."""
    existing = await humancloud_service.get_creator_profile(db, current_user["id"])
    if existing:
        raise HTTPException(status_code=400, detail="Already registered as creator")
    
    profile = await humancloud_service.create_creator_profile(
        db=db,
        user_id=current_user["id"],
        display_name=data.display_name,
        bio=data.bio,
        categories=data.categories,
        skills=data.skills,
        hourly_rate=data.hourly_rate,
        min_budget=data.min_budget,
    )
    
    return CreatorProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        display_name=profile.display_name,
        bio=profile.bio,
        categories=profile.categories,
        skills=profile.skills,
        completed_count=profile.completed_count,
        avg_rating=float(profile.avg_rating) if profile.avg_rating else None,
        is_available=profile.is_available,
        is_verified=profile.is_verified,
    )


@router.get("/creators", response_model=List[CreatorProfileResponse])
async def find_creators(
    category: str = Query(default="video_creative"),
    max_budget: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Find available creators by category."""
    creators = await humancloud_service.find_available_creators(
        db=db,
        category=category,
        max_budget=max_budget,
    )
    
    return [
        CreatorProfileResponse(
            id=c.id,
            user_id=c.user_id,
            display_name=c.display_name,
            bio=c.bio,
            categories=c.categories,
            skills=c.skills,
            completed_count=c.completed_count,
            avg_rating=float(c.avg_rating) if c.avg_rating else None,
            is_available=c.is_available,
            is_verified=c.is_verified,
        )
        for c in creators
    ]


@router.get("/creators/me", response_model=CreatorProfileResponse)
async def get_my_creator_profile(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get my creator profile."""
    profile = await humancloud_service.get_creator_profile(db, current_user["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Not registered as creator")
    
    return CreatorProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        display_name=profile.display_name,
        bio=profile.bio,
        categories=profile.categories,
        skills=profile.skills,
        completed_count=profile.completed_count,
        avg_rating=float(profile.avg_rating) if profile.avg_rating else None,
        is_available=profile.is_available,
        is_verified=profile.is_verified,
    )


# =============================================================================
# Request Endpoints
# =============================================================================

@router.post("/requests", response_model=RequestResponse)
async def create_request(
    data: RequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new creative request (draft)."""
    request = await humancloud_service.create_request(
        db=db,
        client_id=current_user["id"],
        title=data.title,
        description=data.description,
        budget_credits=data.budget_credits,
        category=data.category,
        requirements=data.requirements,
        deadline=data.deadline,
    )
    
    return RequestResponse(
        id=request.id,
        client_id=request.client_id,
        title=request.title,
        description=request.description,
        category=request.category,
        budget_credits=request.budget_credits,
        status=request.status,
        deadline=request.deadline,
        created_at=request.created_at,
    )


@router.post("/requests/{request_id}/publish", response_model=RequestResponse)
async def publish_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Publish request and escrow credits."""
    try:
        request = await humancloud_service.publish_request(
            db=db,
            request_id=request_id,
            client_id=current_user["id"],
        )
        
        return RequestResponse(
            id=request.id,
            client_id=request.client_id,
            title=request.title,
            description=request.description,
            category=request.category,
            budget_credits=request.budget_credits,
            status=request.status,
            deadline=request.deadline,
            created_at=request.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/requests/open", response_model=List[RequestResponse])
async def list_open_requests(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List open requests for creators to browse."""
    requests = await humancloud_service.list_open_requests(db, category)
    
    return [
        RequestResponse(
            id=r.id,
            client_id=r.client_id,
            title=r.title,
            description=r.description,
            category=r.category,
            budget_credits=r.budget_credits,
            status=r.status,
            deadline=r.deadline,
            created_at=r.created_at,
        )
        for r in requests
    ]


# =============================================================================
# Assignment Endpoints
# =============================================================================

@router.post("/requests/{request_id}/assign", response_model=AssignmentResponse)
async def create_assignment(
    request_id: UUID,
    data: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Assign a creator to a request."""
    try:
        assignment = await humancloud_service.create_assignment(
            db=db,
            request_id=request_id,
            creator_id=data.creator_id,
            agreed_credits=data.agreed_credits,
            agreed_deadline=data.agreed_deadline,
            agreed_revisions=data.agreed_revisions,
        )
        
        return AssignmentResponse(
            id=assignment.id,
            request_id=assignment.request_id,
            creator_id=assignment.creator_id,
            status=assignment.status,
            agreed_credits=assignment.agreed_credits,
            agreed_deadline=assignment.agreed_deadline,
            created_at=assignment.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/assignments/{assignment_id}/accept", response_model=AssignmentResponse)
async def accept_assignment(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Creator accepts an assignment."""
    try:
        assignment = await humancloud_service.accept_assignment(
            db=db,
            assignment_id=assignment_id,
            creator_user_id=current_user["id"],
        )
        
        return AssignmentResponse(
            id=assignment.id,
            request_id=assignment.request_id,
            creator_id=assignment.creator_id,
            status=assignment.status,
            agreed_credits=assignment.agreed_credits,
            agreed_deadline=assignment.agreed_deadline,
            created_at=assignment.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/assignments/{assignment_id}/start", response_model=AssignmentResponse)
async def start_work(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Creator starts working."""
    try:
        assignment = await humancloud_service.start_work(
            db=db,
            assignment_id=assignment_id,
            creator_user_id=current_user["id"],
        )
        
        return AssignmentResponse(
            id=assignment.id,
            request_id=assignment.request_id,
            creator_id=assignment.creator_id,
            status=assignment.status,
            agreed_credits=assignment.agreed_credits,
            agreed_deadline=assignment.agreed_deadline,
            created_at=assignment.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Delivery Endpoints
# =============================================================================

@router.get("/assignments/{assignment_id}/deliveries", response_model=List[DeliveryResponse])
async def get_deliveries(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all deliveries for an assignment."""
    deliveries = await humancloud_service.get_deliveries(db, assignment_id)
    
    return [
        DeliveryResponse(
            id=d.id,
            assignment_id=d.assignment_id,
            version=d.version,
            files=d.files,
            status=d.status,
            submitted_at=d.submitted_at,
        )
        for d in deliveries
    ]



@router.post("/assignments/{assignment_id}/deliver", response_model=DeliveryResponse)
async def submit_delivery(
    assignment_id: UUID,
    data: DeliveryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Creator submits a delivery."""
    try:
        delivery = await humancloud_service.submit_delivery(
            db=db,
            assignment_id=assignment_id,
            creator_user_id=current_user["id"],
            files=data.files,
            notes=data.notes,
        )
        
        return DeliveryResponse(
            id=delivery.id,
            assignment_id=delivery.assignment_id,
            version=delivery.version,
            files=delivery.files,
            status=delivery.status,
            submitted_at=delivery.submitted_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/deliveries/{delivery_id}/approve")
async def approve_delivery(
    delivery_id: UUID,
    data: DeliveryApproval,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Client approves delivery and releases payment."""
    try:
        delivery, creator_share, platform_share = await humancloud_service.approve_delivery(
            db=db,
            delivery_id=delivery_id,
            client_id=current_user["id"],
            rating=data.rating,
            feedback=data.feedback,
        )
        
        return {
            "id": delivery.id,
            "status": delivery.status,
            "payment": {
                "creator_share": creator_share,
                "platform_share": platform_share,
                "split": "75/25",
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Evidence Endpoints
# =============================================================================

@router.get("/assignments/{assignment_id}/evidence", response_model=List[EvidenceLogResponse])
async def get_evidence_timeline(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get evidence timeline for an assignment."""
    logs = await humancloud_service.get_evidence_timeline(db, assignment_id)
    
    return [
        EvidenceLogResponse(
            id=log.id,
            event_type=log.event_type,
            title=log.title,
            description=log.description,
            actor_role=log.actor_role,
            attachments=log.attachments,
            created_at=log.created_at,
        )
        for log in logs
    ]


# =============================================================================
# Stats
# =============================================================================

@router.get("/stats")
async def marketplace_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get Human Cloud marketplace statistics."""
    return await humancloud_service.get_marketplace_stats(db)
