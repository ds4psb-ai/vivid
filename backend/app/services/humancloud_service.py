"""Human Cloud Service.

Business logic for the Human Cloud marketplace:
- Request creation and lifecycle
- Creator matching
- Assignment management
- Evidence logging
- Payment processing (75/25 split)
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_humancloud import (
    CreatorProfile,
    CreativeRequest,
    Assignment,
    EvidenceLog,
    Delivery,
    RequestStatus,
    AssignmentStatus,
    EvidenceType,
    HUMAN_CLOUD_REVENUE_SHARE,
)
from app.credit_service import deduct_credits, refund_credits

logger = logging.getLogger(__name__)


# =============================================================================
# Creator Profile
# =============================================================================

async def create_creator_profile(
    db: AsyncSession,
    user_id: str,
    display_name: str,
    categories: List[str],
    bio: Optional[str] = None,
    skills: Optional[List[str]] = None,
    hourly_rate: Optional[int] = None,
    min_budget: int = 100,
) -> CreatorProfile:
    """Create a new creator profile."""
    profile = CreatorProfile(
        id=uuid4(),
        user_id=user_id,
        display_name=display_name,
        bio=bio,
        categories=categories,
        skills=skills or [],
        hourly_rate=hourly_rate,
        min_budget=min_budget,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def get_creator_profile(
    db: AsyncSession,
    user_id: str,
) -> Optional[CreatorProfile]:
    """Get creator profile by user ID."""
    result = await db.execute(
        select(CreatorProfile).where(CreatorProfile.user_id == user_id)
    )
    return result.scalars().first()


async def find_available_creators(
    db: AsyncSession,
    category: str,
    max_budget: Optional[int] = None,
    limit: int = 20,
) -> List[CreatorProfile]:
    """Find available creators matching criteria."""
    query = (
        select(CreatorProfile)
        .where(CreatorProfile.is_available == True)
        .where(CreatorProfile.categories.contains([category]))
    )
    
    if max_budget:
        query = query.where(CreatorProfile.min_budget <= max_budget)
    
    # Order by rating and completed count
    query = (
        query
        .order_by(CreatorProfile.avg_rating.desc().nullsfirst())
        .order_by(CreatorProfile.completed_count.desc())
        .limit(limit)
    )
    
    result = await db.execute(query)
    return list(result.scalars().all())


# =============================================================================
# Creative Request
# =============================================================================

async def create_request(
    db: AsyncSession,
    client_id: str,
    title: str,
    description: str,
    budget_credits: int,
    category: str = "video_creative",
    requirements: Optional[Dict] = None,
    deadline: Optional[datetime] = None,
) -> CreativeRequest:
    """Create a new creative request."""
    request = CreativeRequest(
        id=uuid4(),
        client_id=client_id,
        title=title,
        description=description,
        budget_credits=budget_credits,
        category=category,
        requirements=requirements or {},
        deadline=deadline,
        status=RequestStatus.DRAFT.value,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)
    return request


async def publish_request(
    db: AsyncSession,
    request_id: UUID,
    client_id: str,
) -> CreativeRequest:
    """Publish a request and escrow credits."""
    request = await db.get(CreativeRequest, request_id)
    if not request:
        raise ValueError("Request not found")
    if request.client_id != client_id:
        raise ValueError("Not your request")
    if request.status != RequestStatus.DRAFT.value:
        raise ValueError(f"Cannot publish request in status: {request.status}")
    
    # Escrow credits from client
    success, error = await deduct_credits(
        db=db,
        user_id=client_id,
        amount=request.budget_credits,
        reason=f"Escrow for request: {request.title}",
        reference_id=str(request_id),
    )
    
    if not success:
        raise ValueError(f"Failed to escrow credits: {error}")
    
    request.status = RequestStatus.OPEN.value
    request.credits_escrowed = request.budget_credits
    request.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(request)
    return request


async def list_open_requests(
    db: AsyncSession,
    category: Optional[str] = None,
    limit: int = 20,
) -> List[CreativeRequest]:
    """List open requests for creators to browse."""
    query = (
        select(CreativeRequest)
        .where(CreativeRequest.status == RequestStatus.OPEN.value)
    )
    
    if category:
        query = query.where(CreativeRequest.category == category)
    
    query = query.order_by(CreativeRequest.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    return list(result.scalars().all())


# =============================================================================
# Assignment
# =============================================================================

async def create_assignment(
    db: AsyncSession,
    request_id: UUID,
    creator_id: UUID,
    agreed_credits: int,
    agreed_deadline: Optional[datetime] = None,
    agreed_revisions: int = 1,
) -> Assignment:
    """Create an assignment (offer to creator)."""
    # Get request
    request = await db.get(CreativeRequest, request_id)
    if not request:
        raise ValueError("Request not found")
    if request.status != RequestStatus.OPEN.value:
        raise ValueError("Request is not open")
    
    assignment = Assignment(
        id=uuid4(),
        request_id=request_id,
        creator_id=creator_id,
        status=AssignmentStatus.PENDING.value,
        agreed_credits=agreed_credits,
        agreed_deadline=agreed_deadline,
        agreed_revisions=agreed_revisions,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    
    # Log evidence
    await log_evidence(
        db=db,
        assignment_id=assignment.id,
        event_type=EvidenceType.STATUS_UPDATE.value,
        title="Assignment created",
        actor_id=str(request.client_id),
        actor_role="client",
        metadata={"agreed_credits": agreed_credits},
    )
    
    return assignment


async def accept_assignment(
    db: AsyncSession,
    assignment_id: UUID,
    creator_user_id: str,
) -> Assignment:
    """Creator accepts an assignment."""
    assignment = await db.get(Assignment, assignment_id)
    if not assignment:
        raise ValueError("Assignment not found")
    
    # Verify creator
    creator = await db.get(CreatorProfile, assignment.creator_id)
    if not creator or creator.user_id != creator_user_id:
        raise ValueError("Not your assignment")
    
    if assignment.status != AssignmentStatus.PENDING.value:
        raise ValueError(f"Cannot accept assignment in status: {assignment.status}")
    
    # Update assignment
    assignment.status = AssignmentStatus.ACCEPTED.value
    assignment.updated_at = datetime.utcnow()
    
    # Update request
    request = await db.get(CreativeRequest, assignment.request_id)
    if request:
        request.status = RequestStatus.ASSIGNED.value
        request.assigned_creator_id = assignment.creator_id
        request.assigned_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(assignment)
    
    # Log evidence
    await log_evidence(
        db=db,
        assignment_id=assignment_id,
        event_type=EvidenceType.STATUS_UPDATE.value,
        title="Assignment accepted",
        actor_id=creator_user_id,
        actor_role="creator",
    )
    
    return assignment


async def start_work(
    db: AsyncSession,
    assignment_id: UUID,
    creator_user_id: str,
) -> Assignment:
    """Creator starts working on assignment."""
    assignment = await db.get(Assignment, assignment_id)
    if not assignment:
        raise ValueError("Assignment not found")
    
    creator = await db.get(CreatorProfile, assignment.creator_id)
    if not creator or creator.user_id != creator_user_id:
        raise ValueError("Not your assignment")
    
    if assignment.status != AssignmentStatus.ACCEPTED.value:
        raise ValueError("Assignment must be accepted first")
    
    assignment.status = AssignmentStatus.ACTIVE.value
    assignment.updated_at = datetime.utcnow()
    
    request = await db.get(CreativeRequest, assignment.request_id)
    if request:
        request.status = RequestStatus.IN_PROGRESS.value
    
    await db.commit()
    await db.refresh(assignment)
    
    await log_evidence(
        db=db,
        assignment_id=assignment_id,
        event_type=EvidenceType.STATUS_UPDATE.value,
        title="Work started",
        actor_id=creator_user_id,
        actor_role="creator",
    )
    
    return assignment


async def get_deliveries(
    db: AsyncSession,
    assignment_id: UUID,
) -> List[Delivery]:
    """Get all deliveries for an assignment."""
    result = await db.execute(
        select(Delivery)
        .where(Delivery.assignment_id == assignment_id)
        .order_by(Delivery.version.desc())
    )
    return list(result.scalars().all())


# =============================================================================
# Delivery & Completion
# =============================================================================

async def submit_delivery(
    db: AsyncSession,
    assignment_id: UUID,
    creator_user_id: str,
    files: List[str],
    notes: Optional[str] = None,
) -> Delivery:
    """Creator submits a delivery."""
    assignment = await db.get(Assignment, assignment_id)
    if not assignment:
        raise ValueError("Assignment not found")
    
    creator = await db.get(CreatorProfile, assignment.creator_id)
    if not creator or creator.user_id != creator_user_id:
        raise ValueError("Not your assignment")
    
    if assignment.status != AssignmentStatus.ACTIVE.value:
        raise ValueError("Assignment must be active")
    
    # Count existing versions
    existing = await db.execute(
        select(func.count()).where(Delivery.assignment_id == assignment_id)
    )
    version = (existing.scalar() or 0) + 1
    
    delivery = Delivery(
        id=uuid4(),
        assignment_id=assignment_id,
        version=version,
        files=files,
        notes=notes,
        status="pending",
        submitted_at=datetime.utcnow(),
    )
    db.add(delivery)
    
    assignment.delivered_at = datetime.utcnow()
    
    request = await db.get(CreativeRequest, assignment.request_id)
    if request:
        request.status = RequestStatus.REVIEW.value
    
    await db.commit()
    await db.refresh(delivery)
    
    await log_evidence(
        db=db,
        assignment_id=assignment_id,
        event_type=EvidenceType.FILE_UPLOAD.value,
        title=f"Delivery v{version} submitted",
        actor_id=creator_user_id,
        actor_role="creator",
        attachments=files,
        file_version=version,
    )
    
    return delivery


async def approve_delivery(
    db: AsyncSession,
    delivery_id: UUID,
    client_id: str,
    rating: int = 5,
    feedback: Optional[str] = None,
) -> Tuple[Delivery, int, int]:
    """Client approves delivery and releases payment."""
    delivery = await db.get(Delivery, delivery_id)
    if not delivery:
        raise ValueError("Delivery not found")
    
    assignment = await db.get(Assignment, delivery.assignment_id)
    if not assignment:
        raise ValueError("Assignment not found")
    
    request = await db.get(CreativeRequest, assignment.request_id)
    if not request or request.client_id != client_id:
        raise ValueError("Not your request")
    
    if delivery.status != "pending":
        raise ValueError("Delivery already reviewed")
    
    # Calculate payment split
    total_credits = assignment.agreed_credits
    creator_share = int(total_credits * HUMAN_CLOUD_REVENUE_SHARE["creator_share"])
    platform_share = total_credits - creator_share
    
    # Update delivery
    delivery.status = "approved"
    delivery.reviewed_at = datetime.utcnow()
    delivery.review_notes = feedback
    
    # Update assignment
    assignment.status = AssignmentStatus.COMPLETED.value
    assignment.accepted_at = datetime.utcnow()
    assignment.client_rating = rating
    
    # Update request
    request.status = RequestStatus.COMPLETED.value
    request.completed_at = datetime.utcnow()
    request.client_rating = rating
    request.client_feedback = feedback
    request.credits_released = creator_share
    request.platform_fee = platform_share
    
    # Update creator stats
    creator = await db.get(CreatorProfile, assignment.creator_id)
    if creator:
        creator.completed_count += 1
        creator.total_earned += creator_share
        # Recalculate average rating
        if creator.avg_rating:
            new_avg = (float(creator.avg_rating) * (creator.completed_count - 1) + rating) / creator.completed_count
            creator.avg_rating = Decimal(str(round(new_avg, 2)))
        else:
            creator.avg_rating = Decimal(str(rating))
    
    await db.commit()
    await db.refresh(delivery)
    
    # Log evidence
    await log_evidence(
        db=db,
        assignment_id=assignment.id,
        event_type=EvidenceType.APPROVAL.value,
        title="Delivery approved",
        actor_id=client_id,
        actor_role="client",
        metadata={
            "rating": rating,
            "creator_payment": creator_share,
            "platform_fee": platform_share,
        },
    )
    
    logger.info(f"Request {request.id} completed: creator={creator_share}, platform={platform_share}")
    
    return delivery, creator_share, platform_share


# =============================================================================
# Evidence Logging
# =============================================================================

async def log_evidence(
    db: AsyncSession,
    assignment_id: UUID,
    event_type: str,
    title: str,
    actor_id: str,
    actor_role: str,
    description: Optional[str] = None,
    attachments: Optional[List[str]] = None,
    metadata: Optional[Dict] = None,
    file_version: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> EvidenceLog:
    """Create an evidence log entry."""
    log = EvidenceLog(
        id=uuid4(),
        assignment_id=assignment_id,
        event_type=event_type,
        title=title,
        description=description,
        actor_id=actor_id,
        actor_role=actor_role,
        attachments=attachments or [],
        extra=metadata or {},
        file_version=file_version,
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=datetime.utcnow(),
    )
    db.add(log)
    await db.commit()
    return log


async def get_evidence_timeline(
    db: AsyncSession,
    assignment_id: UUID,
) -> List[EvidenceLog]:
    """Get all evidence logs for an assignment."""
    result = await db.execute(
        select(EvidenceLog)
        .where(EvidenceLog.assignment_id == assignment_id)
        .order_by(EvidenceLog.created_at.asc())
    )
    return list(result.scalars().all())


# =============================================================================
# Statistics
# =============================================================================

async def get_marketplace_stats(db: AsyncSession) -> Dict[str, Any]:
    """Get Human Cloud marketplace statistics."""
    # Open requests
    open_count = await db.execute(
        select(func.count())
        .where(CreativeRequest.status == RequestStatus.OPEN.value)
    )
    
    # Active creators
    active_creators = await db.execute(
        select(func.count())
        .where(CreatorProfile.is_available == True)
    )
    
    # Total completed
    completed = await db.execute(
        select(func.count())
        .where(CreativeRequest.status == RequestStatus.COMPLETED.value)
    )
    
    # Total volume
    volume = await db.execute(
        select(func.sum(CreativeRequest.credits_released))
        .where(CreativeRequest.status == RequestStatus.COMPLETED.value)
    )
    
    return {
        "open_requests": open_count.scalar() or 0,
        "active_creators": active_creators.scalar() or 0,
        "completed_requests": completed.scalar() or 0,
        "total_volume_credits": volume.scalar() or 0,
    }
