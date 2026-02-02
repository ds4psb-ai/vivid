"""Settlement API Router.

Complete REST API for settlement management:
- User endpoints: my settlements, summary, disputes
- Admin endpoints: batch processing, resolve disputes
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.utils.error_sanitize import safe_error_detail
from app.models_settlement import (
    SettlementTransaction,
    SettlementPayout,
    SettlementDispute,
    SettlementStatus,
    PayoutStatus,
    DisputeStatus,
)
from app.schemas.settlement_schemas import (
    SettlementResponse,
    SettlementDetailResponse,
    SettlementPreview,
    PayoutResponse,
    DisputeCreate,
    DisputeResolve,
    DisputeResponse,
    UserSettlementSummary,
    AdminSettlementStats,
    BatchProcessRequest,
    BatchProcessResponse,
)
from app.services import fork_revenue_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/settlements", tags=["Settlements"])


# =============================================================================
# User Endpoints
# =============================================================================

@router.get("/my", response_model=list[PayoutResponse])
async def get_my_settlements(
    status: Optional[str] = None,
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get my settlement payouts.
    
    Returns all payouts where the current user is a recipient.
    """
    user_id = current_user["id"]
    since = datetime.utcnow() - timedelta(days=days)
    
    query = (
        select(SettlementPayout)
        .join(SettlementTransaction)
        .where(SettlementPayout.recipient_id == user_id)
        .where(SettlementPayout.created_at >= since)
        .options(selectinload(SettlementPayout.settlement))
    )
    
    if status:
        query = query.where(SettlementPayout.status == status)
    
    query = query.order_by(SettlementPayout.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    payouts = result.scalars().all()
    
    return [PayoutResponse.model_validate(p) for p in payouts]


@router.get("/my/summary", response_model=UserSettlementSummary)
async def get_my_settlement_summary(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get my settlement summary.
    
    Aggregated stats: total earned, average, pending.
    """
    user_id = current_user["id"]
    return await fork_revenue_service.get_user_settlement_summary(db, user_id, days)


@router.get("/{settlement_id}", response_model=SettlementDetailResponse)
async def get_settlement(
    settlement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get settlement details.
    
    Users can only view settlements they participated in.
    """
    settlement = await fork_revenue_service.get_settlement_details(db, settlement_id)
    
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    
    # Check access: must be payer or recipient
    user_id = current_user["id"]
    is_payer = settlement.payer_user_id == user_id
    is_recipient = any(p.recipient_id == user_id for p in settlement.payouts)
    is_admin = current_user.get("is_admin", False)
    
    if not (is_payer or is_recipient or is_admin):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return SettlementDetailResponse(
        id=settlement.id,
        tool_run_id=settlement.tool_run_id,
        tool_id=settlement.tool_id,
        tool_key=settlement.tool_key,
        status=settlement.status,
        total_credits=settlement.total_credits,
        platform_fee=settlement.platform_fee,
        creator_pool=settlement.creator_pool,
        lineage_depth=settlement.lineage_depth,
        attribution_score=settlement.attribution_score,
        payer_user_id=settlement.payer_user_id,
        created_at=settlement.created_at,
        processed_at=settlement.processed_at,
        completed_at=settlement.completed_at,
        retry_count=settlement.retry_count,
        error_message=settlement.error_message,
        payouts=[PayoutResponse.model_validate(p) for p in settlement.payouts],
        disputes=[DisputeResponse.model_validate(d) for d in settlement.disputes],
    )


@router.post("/{settlement_id}/dispute", response_model=DisputeResponse)
async def create_dispute(
    settlement_id: UUID,
    data: DisputeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a dispute for a settlement.
    
    Users can dispute settlements they participated in.
    """
    user_id = current_user["id"]
    
    # Verify user is a recipient
    settlement = await fork_revenue_service.get_settlement_details(db, settlement_id)
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    
    is_recipient = any(p.recipient_id == user_id for p in settlement.payouts)
    if not is_recipient:
        raise HTTPException(status_code=403, detail="Only recipients can dispute")
    
    # Check for existing open dispute
    existing = await db.execute(
        select(SettlementDispute)
        .where(SettlementDispute.settlement_id == settlement_id)
        .where(SettlementDispute.complainant_id == user_id)
        .where(SettlementDispute.status.in_([
            DisputeStatus.OPEN.value,
            DisputeStatus.INVESTIGATING.value,
        ]))
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="You already have an open dispute")
    
    try:
        dispute = await fork_revenue_service.create_dispute(
            db=db,
            settlement_id=settlement_id,
            complainant_id=user_id,
            reason=data.reason,
            expected_amount=data.expected_amount,
            evidence=data.evidence,
        )
        return DisputeResponse.model_validate(dispute)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Settlement operation"))


@router.get("/preview/{tool_id}", response_model=SettlementPreview)
async def preview_settlement(
    tool_id: UUID,
    credits: int = Query(..., ge=1, le=100000, description="Total credits"),
    db: AsyncSession = Depends(get_db),
):
    """Preview how a settlement would be distributed.
    
    Useful for showing users the breakdown before running a tool.
    """
    from app.models_telemetry import ToolManifest
    from decimal import Decimal, ROUND_HALF_UP
    
    tool = await db.get(ToolManifest, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Calculate
    total = Decimal(credits)
    platform_fee = int((total * fork_revenue_service.PLATFORM_FEE_RATE).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    ))
    creator_pool = credits - platform_fee
    
    lineage = await fork_revenue_service.get_tool_lineage(db, tool_id)
    lineage_depth = len(lineage)
    
    attribution_score = None
    if lineage:
        _, current_fork = lineage[-1]
        if current_fork:
            attribution_score = current_fork.attribution_score
    
    payouts = fork_revenue_service.calculate_payouts(creator_pool, lineage)
    
    return SettlementPreview(
        tool_id=tool_id,
        tool_key=tool.tool_key,
        total_credits=credits,
        platform_fee=platform_fee,
        creator_pool=creator_pool,
        lineage_depth=lineage_depth,
        attribution_score=attribution_score,
        payouts=payouts,
    )


# =============================================================================
# Admin Endpoints
# =============================================================================

@router.get("/admin/stats", response_model=AdminSettlementStats)
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get settlement statistics for admin dashboard."""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin only")
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Pending count
    pending = await db.execute(
        select(func.count(SettlementTransaction.id))
        .where(SettlementTransaction.status == SettlementStatus.PENDING.value)
    )
    pending_count = pending.scalar() or 0
    
    # Processing count
    processing = await db.execute(
        select(func.count(SettlementTransaction.id))
        .where(SettlementTransaction.status == SettlementStatus.PROCESSING.value)
    )
    processing_count = processing.scalar() or 0
    
    # Completed today
    completed = await db.execute(
        select(
            func.count(SettlementTransaction.id),
            func.sum(SettlementTransaction.creator_pool),
        )
        .where(SettlementTransaction.status == SettlementStatus.COMPLETED.value)
        .where(SettlementTransaction.completed_at >= today_start)
    )
    completed_row = completed.one()
    
    # Open disputes
    disputes = await fork_revenue_service.get_open_disputes_count(db)
    
    return AdminSettlementStats(
        pending_count=pending_count,
        processing_count=processing_count,
        completed_today=completed_row[0] or 0,
        total_settled_today=completed_row[1] or 0,
        open_disputes=disputes,
    )


@router.get("/admin/list")
async def list_settlements(
    status: Optional[str] = None,
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all settlements (admin only)."""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin only")
    
    since = datetime.utcnow() - timedelta(days=days)
    
    query = (
        select(SettlementTransaction)
        .where(SettlementTransaction.created_at >= since)
    )
    
    if status:
        query = query.where(SettlementTransaction.status == status)
    
    query = query.order_by(SettlementTransaction.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    settlements = result.scalars().all()
    
    return {
        "settlements": [SettlementResponse.model_validate(s) for s in settlements],
        "total": len(settlements),
    }


@router.post("/admin/batch", response_model=BatchProcessResponse)
async def batch_process_settlements(
    data: BatchProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Process pending settlements in batch (admin only)."""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin only")
    
    result = await fork_revenue_service.process_batch_settlements(
        db=db,
        limit=data.limit,
        processed_by=current_user["id"],
    )
    
    return BatchProcessResponse(**result)


@router.post("/admin/{settlement_id}/process")
async def process_single_settlement(
    settlement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Manually process a single settlement (admin only)."""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin only")
    
    success, error = await fork_revenue_service.process_settlement(
        db=db,
        settlement_id=settlement_id,
        processed_by=current_user["id"],
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error or "Processing failed")
    
    return {"status": "completed", "settlement_id": str(settlement_id)}


@router.post("/admin/{settlement_id}/rollback")
async def rollback_settlement(
    settlement_id: UUID,
    reason: str = Query(..., min_length=10),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Rollback a settlement (admin only)."""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin only")
    
    success, error = await fork_revenue_service.rollback_settlement(
        db=db,
        settlement_id=settlement_id,
        reason=reason,
        rolled_back_by=current_user["id"],
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error or "Rollback failed")
    
    return {"status": "reversed", "settlement_id": str(settlement_id)}


@router.get("/admin/disputes")
async def list_disputes(
    status: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List disputes (admin only)."""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin only")
    
    query = select(SettlementDispute).options(
        selectinload(SettlementDispute.settlement)
    )
    
    if status:
        query = query.where(SettlementDispute.status == status)
    
    query = query.order_by(SettlementDispute.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    disputes = result.scalars().all()
    
    return {
        "disputes": [DisputeResponse.model_validate(d) for d in disputes],
        "total": len(disputes),
    }


@router.post("/admin/disputes/{dispute_id}/resolve", response_model=DisputeResponse)
async def resolve_dispute(
    dispute_id: UUID,
    data: DisputeResolve,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Resolve a dispute (admin only)."""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin only")
    
    status_enum = DisputeStatus.RESOLVED if data.status == "resolved" else DisputeStatus.REJECTED
    
    try:
        dispute = await fork_revenue_service.resolve_dispute(
            db=db,
            dispute_id=dispute_id,
            resolution=data.resolution,
            status=status_enum,
            adjustment_amount=data.adjustment_amount,
            resolved_by=current_user["id"],
        )
        return DisputeResponse.model_validate(dispute)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Settlement operation"))
