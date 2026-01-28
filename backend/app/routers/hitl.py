"""HITL (Human-in-the-Loop) Router.

API endpoints for HITL review dashboard and workflow management.

Endpoints:
- GET /api/hitl/pending - Get pending review items
- POST /api/hitl/{item_id}/approve - Approve and auto-apply
- POST /api/hitl/{item_id}/reject - Reject review item
- POST /api/hitl/{item_id}/assign - Assign to admin
- GET /api/hitl/counts - Get counts by type
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hitl", tags=["HITL"])


# =============================================================================
# Request/Response Models
# =============================================================================

class HITLItemResponse(BaseModel):
    """Single HITL review item response."""
    id: str
    review_type: str
    severity: str
    ip_id: Optional[str] = None
    trace_id: Optional[str] = None
    payload: Dict[str, Any]
    suggested_action: Optional[Dict[str, Any]] = None
    status: str
    assigned_to: Optional[str] = None
    decision: Optional[str] = None
    decision_by: Optional[str] = None
    decision_at: Optional[str] = None
    decision_notes: Optional[str] = None
    auto_applied: bool = False
    applied_at: Optional[str] = None
    apply_result: Optional[Dict[str, Any]] = None
    created_at: str
    expires_at: Optional[str] = None


class HITLPendingResponse(BaseModel):
    """Response with pending review items."""
    items: List[HITLItemResponse]
    counts: Dict[str, int]
    total_pending: int


class HITLApproveRequest(BaseModel):
    """Request to approve a review item."""
    notes: Optional[str] = Field(default=None, description="Decision notes")
    modified_action: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Modified action (overrides suggested)",
    )


class HITLRejectRequest(BaseModel):
    """Request to reject a review item."""
    reason: str = Field(..., description="Rejection reason")


class HITLAssignRequest(BaseModel):
    """Request to assign a review item."""
    assigned_to: str = Field(..., description="Admin user ID")


class HITLCountsResponse(BaseModel):
    """Response with counts by type."""
    counts: Dict[str, int]


# =============================================================================
# Admin Dependency
# =============================================================================

async def require_admin(
    user: dict = Depends(get_current_user),
) -> dict:
    """Require admin role for HITL operations."""
    # Check if user has admin role
    roles = user.get("roles", [])
    if "admin" not in roles and user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ADMIN_REQUIRED", "message": "Admin access required"},
        )
    return user


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/pending", response_model=HITLPendingResponse)
async def get_pending_reviews(
    review_type: Optional[str] = None,
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> HITLPendingResponse:
    """Get pending review items.

    Args:
        review_type: Filter by type (vector_drift, qc_failure, prompt_pattern)
        user: Authenticated admin user
        db: Database session

    Returns:
        HITLPendingResponse with items and counts
    """
    from app.services.hitl_workflow import get_hitl_service

    service = get_hitl_service()

    items = await service.get_pending_by_type(review_type, db)
    counts = await service.get_counts_by_type(db)

    return HITLPendingResponse(
        items=[
            HITLItemResponse(
                id=str(item.id),
                review_type=item.review_type,
                severity=item.severity,
                ip_id=item.ip_id,
                trace_id=item.trace_id,
                payload=item.payload,
                suggested_action=item.suggested_action,
                status=item.status,
                assigned_to=item.assigned_to,
                decision=item.decision,
                decision_by=item.decision_by,
                decision_at=item.decision_at.isoformat() if item.decision_at else None,
                decision_notes=item.decision_notes,
                auto_applied=item.auto_applied,
                applied_at=item.applied_at.isoformat() if item.applied_at else None,
                apply_result=item.apply_result,
                created_at=item.created_at.isoformat(),
                expires_at=item.expires_at.isoformat() if item.expires_at else None,
            )
            for item in items
        ],
        counts=counts,
        total_pending=counts.get("total", 0),
    )


@router.post("/{item_id}/approve")
async def approve_review(
    item_id: str,
    request: HITLApproveRequest,
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Approve a review item and auto-apply the action.

    Args:
        item_id: Review item ID
        request: Approval request with optional notes and modified action
        user: Authenticated admin user
        db: Database session

    Returns:
        Approval result with apply status
    """
    from app.services.hitl_workflow import get_hitl_service

    service = get_hitl_service()

    try:
        item = await service.approve_and_apply(
            item_id=item_id,
            decision_by=user.get("id"),
            decision_notes=request.notes,
            modified_action=request.modified_action,
            db=db,
        )

        await db.commit()

        return {
            "success": True,
            "item_id": str(item.id),
            "status": item.status,
            "auto_applied": item.auto_applied,
            "apply_result": item.apply_result,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": str(e)},
        )
    except Exception as e:
        logger.exception(f"[HITL] Approve failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "Approval failed"},
        )


@router.post("/{item_id}/reject")
async def reject_review(
    item_id: str,
    request: HITLRejectRequest,
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Reject a review item.

    Args:
        item_id: Review item ID
        request: Rejection request with reason
        user: Authenticated admin user
        db: Database session

    Returns:
        Rejection result
    """
    from app.services.hitl_workflow import get_hitl_service

    service = get_hitl_service()

    try:
        item = await service.reject(
            item_id=item_id,
            decision_by=user.get("id"),
            reason=request.reason,
            db=db,
        )

        await db.commit()

        return {
            "success": True,
            "item_id": str(item.id),
            "status": item.status,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": str(e)},
        )


@router.post("/{item_id}/assign")
async def assign_review(
    item_id: str,
    request: HITLAssignRequest,
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Assign a review item to an admin.

    Args:
        item_id: Review item ID
        request: Assignment request
        user: Authenticated admin user
        db: Database session

    Returns:
        Assignment result
    """
    from app.services.hitl_workflow import get_hitl_service

    service = get_hitl_service()

    try:
        item = await service.assign(
            item_id=item_id,
            assigned_to=request.assigned_to,
            db=db,
        )

        await db.commit()

        return {
            "success": True,
            "item_id": str(item.id),
            "assigned_to": item.assigned_to,
            "status": item.status,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": str(e)},
        )


@router.get("/counts", response_model=HITLCountsResponse)
async def get_review_counts(
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> HITLCountsResponse:
    """Get pending review counts by type.

    Args:
        user: Authenticated admin user
        db: Database session

    Returns:
        HITLCountsResponse with counts
    """
    from app.services.hitl_workflow import get_hitl_service

    service = get_hitl_service()
    counts = await service.get_counts_by_type(db)

    return HITLCountsResponse(counts=counts)


@router.post("/expire")
async def expire_old_items(
    user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Expire old review items past their deadline.

    Args:
        user: Authenticated admin user
        db: Database session

    Returns:
        Number of expired items
    """
    from app.services.hitl_workflow import get_hitl_service

    service = get_hitl_service()
    count = await service.expire_old_items(db)

    await db.commit()

    return {
        "success": True,
        "expired_count": count,
    }
