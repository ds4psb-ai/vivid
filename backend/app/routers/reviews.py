"""Review API Router.

Endpoints for tool review workflow and tier management.
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models_telemetry import ToolManifest
from app.models_versioning import ToolVersion
from app.models_review import (
    ToolReview,
    ReviewCheckResult,
    TierPromotion,
    ReviewStatus,
    ReviewType,
)
from app.services import review_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reviews", tags=["Reviews"])


# =============================================================================
# Schemas
# =============================================================================

class ReviewCreate(BaseModel):
    """Create review request."""
    tool_id: UUID
    version_id: Optional[UUID] = None
    review_type: str = Field(default="fork_submission")
    notes: Optional[str] = Field(None, max_length=1000)


class ReviewResponse(BaseModel):
    """Review response."""
    id: UUID
    tool_id: UUID
    version_id: Optional[UUID]
    review_type: str
    status: str
    priority: int
    submitted_by: str
    submission_notes: Optional[str]
    assigned_to: Optional[str]
    decision_by: Optional[str]
    decision_notes: Optional[str]
    rejection_reason: Optional[str]
    auto_checks_passed: bool
    auto_checks_score: float
    created_at: str

    class Config:
        from_attributes = True


class ReviewDecision(BaseModel):
    """Review decision request."""
    notes: Optional[str] = Field(None, max_length=1000)


class ReviewRejection(BaseModel):
    """Review rejection request."""
    reason: str = Field(..., min_length=10, max_length=1000)
    notes: Optional[str] = Field(None, max_length=1000)


class TierPromotionRequest(BaseModel):
    """Tier promotion request."""
    to_tier: str = Field(..., pattern="^(verified|certified)$")
    reason: Optional[str] = None


# =============================================================================
# User Endpoints
# =============================================================================

@router.post("", response_model=ReviewResponse)
async def submit_review(
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Submit a tool for review.
    
    Used when submitting a fork or requesting tier promotion.
    """
    # Verify tool exists and user owns it
    tool = await db.get(ToolManifest, data.tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    if tool.created_by != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not tool owner")
    
    # Check for existing pending review
    existing = await db.execute(
        select(ToolReview)
        .where(ToolReview.tool_id == data.tool_id)
        .where(ToolReview.status == ReviewStatus.PENDING.value)
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Tool already has pending review")
    
    review = await review_service.create_review(
        db=db,
        tool_id=data.tool_id,
        version_id=data.version_id,
        review_type=data.review_type,
        submitted_by=current_user["id"],
        notes=data.notes,
    )
    
    return ReviewResponse(
        id=review.id,
        tool_id=review.tool_id,
        version_id=review.version_id,
        review_type=review.review_type,
        status=review.status,
        priority=review.priority,
        submitted_by=review.submitted_by,
        submission_notes=review.submission_notes,
        assigned_to=review.assigned_to,
        decision_by=review.decision_by,
        decision_notes=review.decision_notes,
        rejection_reason=review.rejection_reason,
        auto_checks_passed=review.auto_checks_passed,
        auto_checks_score=review.auto_checks_score,
        created_at=review.created_at.isoformat(),
    )


@router.get("/my-reviews", response_model=list[ReviewResponse])
async def my_reviews(
    status: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get reviews for current user's tools."""
    query = (
        select(ToolReview)
        .where(ToolReview.submitted_by == current_user["id"])
    )
    
    if status:
        query = query.where(ToolReview.status == status)
    
    query = query.order_by(ToolReview.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    reviews = result.scalars().all()
    
    return [
        ReviewResponse(
            id=r.id,
            tool_id=r.tool_id,
            version_id=r.version_id,
            review_type=r.review_type,
            status=r.status,
            priority=r.priority,
            submitted_by=r.submitted_by,
            submission_notes=r.submission_notes,
            assigned_to=r.assigned_to,
            decision_by=r.decision_by,
            decision_notes=r.decision_notes,
            rejection_reason=r.rejection_reason,
            auto_checks_passed=r.auto_checks_passed,
            auto_checks_score=r.auto_checks_score,
            created_at=r.created_at.isoformat(),
        )
        for r in reviews
    ]


@router.get("/tools/{tool_id}/tier-eligibility")
async def check_tier_eligibility(
    tool_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Check if a tool is eligible for tier promotion."""
    try:
        result = await review_service.check_tier_eligibility(db, tool_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Admin Endpoints
# =============================================================================

@router.get("/stats")
async def review_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get review queue statistics (admin only)."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    
    return await review_service.get_review_stats(db)


@router.get("/queue", response_model=list[ReviewResponse])
async def review_queue(
    review_type: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get pending reviews (admin only)."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    
    reviews = await review_service.get_pending_reviews(db, limit, review_type)
    
    return [
        ReviewResponse(
            id=r.id,
            tool_id=r.tool_id,
            version_id=r.version_id,
            review_type=r.review_type,
            status=r.status,
            priority=r.priority,
            submitted_by=r.submitted_by,
            submission_notes=r.submission_notes,
            assigned_to=r.assigned_to,
            decision_by=r.decision_by,
            decision_notes=r.decision_notes,
            rejection_reason=r.rejection_reason,
            auto_checks_passed=r.auto_checks_passed,
            auto_checks_score=r.auto_checks_score,
            created_at=r.created_at.isoformat(),
        )
        for r in reviews
    ]


@router.get("/{review_id}")
async def get_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get review details with check results."""
    review = await db.get(ToolReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Only owner or admin can view
    if review.submitted_by != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get check results
    results = await db.execute(
        select(ReviewCheckResult)
        .where(ReviewCheckResult.review_id == review_id)
    )
    checks = results.scalars().all()
    
    # Get tool info
    tool = await db.get(ToolManifest, review.tool_id)
    
    return {
        "review": {
            "id": str(review.id),
            "tool_id": str(review.tool_id),
            "version_id": str(review.version_id) if review.version_id else None,
            "review_type": review.review_type,
            "status": review.status,
            "priority": review.priority,
            "submitted_by": review.submitted_by,
            "submission_notes": review.submission_notes,
            "assigned_to": review.assigned_to,
            "decision_by": review.decision_by,
            "decision_notes": review.decision_notes,
            "rejection_reason": review.rejection_reason,
            "auto_checks_passed": review.auto_checks_passed,
            "auto_checks_score": review.auto_checks_score,
            "created_at": review.created_at.isoformat(),
        },
        "tool": {
            "tool_key": tool.tool_key if tool else None,
            "display_name": tool.display_name if tool else None,
            "tier": tool.tier if tool else None,
        },
        "checks": [
            {
                "id": str(c.id),
                "category": c.category,
                "check_name": c.check_name,
                "description": c.description,
                "passed": c.passed,
                "score": c.score,
                "details": c.details,
                "error_message": c.error_message,
                "is_automated": c.is_automated,
            }
            for c in checks
        ],
    }


@router.post("/{review_id}/assign")
async def assign_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Assign review to current admin."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    
    try:
        review = await review_service.assign_review(db, review_id, current_user["id"])
        return {"status": "assigned", "assigned_to": current_user["id"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{review_id}/approve")
async def approve_review(
    review_id: UUID,
    data: ReviewDecision,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Approve a review (admin only)."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    
    try:
        review = await review_service.approve_review(
            db, review_id, current_user["id"], data.notes
        )
        return {
            "status": "approved",
            "review_id": str(review.id),
            "tool_id": str(review.tool_id),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{review_id}/reject")
async def reject_review(
    review_id: UUID,
    data: ReviewRejection,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Reject a review (admin only)."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    
    try:
        review = await review_service.reject_review(
            db, review_id, current_user["id"], data.reason, data.notes
        )
        return {
            "status": "rejected",
            "review_id": str(review.id),
            "reason": data.reason,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tools/{tool_id}/promote")
async def promote_tool(
    tool_id: UUID,
    data: TierPromotionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Promote a tool to a new tier (admin only)."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    
    try:
        promotion = await review_service.promote_tier(
            db=db,
            tool_id=tool_id,
            to_tier=data.to_tier,
            decided_by=current_user["id"],
            reason=data.reason,
        )
        return {
            "status": "promoted",
            "from_tier": promotion.from_tier,
            "to_tier": promotion.to_tier,
            "promotion_id": str(promotion.id),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
