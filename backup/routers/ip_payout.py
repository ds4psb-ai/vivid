"""IP Payout Ledger API router.

Endpoints for creator payout holdback/dispute flows.
"""
import logging
from datetime import datetime
from uuid import UUID

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_user_id
from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models import OpsActionLog
from app.models_ip import IPPayoutLedger, IPPayoutDispute

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ip-payout"])


def record_ops_action(
    db: AsyncSession,
    action_type: str,
    status: str,
    actor_id: str,
    note: Optional[str] = None,
    payload: Optional[dict] = None,
    stats: Optional[dict] = None,
) -> None:
    db.add(
        OpsActionLog(
            action_type=action_type,
            status=status,
            note=note,
            payload=payload or {},
            stats=stats or {},
            actor_id=actor_id,
        )
    )


class PayoutDisputeRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=2000)
    evidence: list[str] = Field(default_factory=list)


class PayoutDisputeResponse(BaseModel):
    dispute_id: str
    ledger_id: str
    status: str
    created_at: datetime


class PayoutLedgerResponse(BaseModel):
    id: str
    ip_id: str
    creator_id: str
    gross_amount: int
    ip_owner_share: int
    creator_share: int
    platform_share: int
    status: str
    holdback_until: Optional[datetime] = None
    dispute_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PayoutDisputeDetailResponse(BaseModel):
    id: str
    ledger_id: str
    complainant_id: str
    reason: str
    evidence: list[str] = Field(default_factory=list)
    status: str
    admin_notes: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AdminHoldbackRequest(BaseModel):
    holdback_until: Optional[datetime] = None


class AdminDisputeResolveRequest(BaseModel):
    status: str = Field(..., pattern="^(resolved|rejected)$")
    admin_notes: Optional[str] = None


@router.get("/payout/my", response_model=list[PayoutLedgerResponse])
async def list_my_payouts(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List payout ledger entries for the current creator."""
    user_id = current_user["id"]
    result = await db.execute(
        select(IPPayoutLedger)
        .where(IPPayoutLedger.creator_id == user_id)
        .order_by(IPPayoutLedger.created_at.desc())
        .limit(limit)
    )
    ledgers = result.scalars().all()

    return [
        PayoutLedgerResponse(
            id=str(ledger.id),
            ip_id=str(ledger.ip_id),
            creator_id=ledger.creator_id,
            gross_amount=ledger.gross_amount,
            ip_owner_share=ledger.ip_owner_share,
            creator_share=ledger.creator_share,
            platform_share=ledger.platform_share,
            status=ledger.status,
            holdback_until=ledger.holdback_until,
            dispute_id=str(ledger.dispute_id) if ledger.dispute_id else None,
            created_at=ledger.created_at,
            updated_at=ledger.updated_at,
        )
        for ledger in ledgers
    ]


@router.get("/payout/{ledger_id}", response_model=PayoutLedgerResponse)
async def get_payout_ledger(
    ledger_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a payout ledger entry."""
    ledger = await db.get(IPPayoutLedger, ledger_id)
    if not ledger:
        raise HTTPException(status_code=404, detail="Payout ledger not found")

    user_id = current_user["id"]
    if ledger.creator_id != user_id and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to view this payout")

    return PayoutLedgerResponse(
        id=str(ledger.id),
        ip_id=str(ledger.ip_id),
        creator_id=ledger.creator_id,
        gross_amount=ledger.gross_amount,
        ip_owner_share=ledger.ip_owner_share,
        creator_share=ledger.creator_share,
        platform_share=ledger.platform_share,
        status=ledger.status,
        holdback_until=ledger.holdback_until,
        dispute_id=str(ledger.dispute_id) if ledger.dispute_id else None,
        created_at=ledger.created_at,
        updated_at=ledger.updated_at,
    )


@router.get("/payout/admin/ledgers", response_model=list[PayoutLedgerResponse])
async def list_all_ledgers(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(require_admin),
):
    """Admin: list payout ledgers."""
    query = select(IPPayoutLedger)
    if status:
        query = query.where(IPPayoutLedger.status == status)

    result = await db.execute(
        query.order_by(IPPayoutLedger.created_at.desc()).limit(limit)
    )
    ledgers = result.scalars().all()

    return [
        PayoutLedgerResponse(
            id=str(ledger.id),
            ip_id=str(ledger.ip_id),
            creator_id=ledger.creator_id,
            gross_amount=ledger.gross_amount,
            ip_owner_share=ledger.ip_owner_share,
            creator_share=ledger.creator_share,
            platform_share=ledger.platform_share,
            status=ledger.status,
            holdback_until=ledger.holdback_until,
            dispute_id=str(ledger.dispute_id) if ledger.dispute_id else None,
            created_at=ledger.created_at,
            updated_at=ledger.updated_at,
        )
        for ledger in ledgers
    ]


@router.post("/payout/admin/{ledger_id}/holdback", response_model=PayoutLedgerResponse)
async def admin_holdback_payout(
    ledger_id: UUID,
    payload: AdminHoldbackRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(require_admin),
):
    """Admin: place payout on holdback."""
    ledger = await db.get(IPPayoutLedger, ledger_id)
    if not ledger:
        raise HTTPException(status_code=404, detail="Payout ledger not found")

    ledger.status = "holdback"
    ledger.holdback_until = payload.holdback_until or ledger.holdback_until or datetime.utcnow()
    ledger.updated_at = datetime.utcnow()

    record_ops_action(
        db=db,
        action_type="ip_payout_holdback",
        status=ledger.status,
        actor_id=admin_user["id"],
        payload={
            "ledger_id": str(ledger.id),
            "holdback_until": ledger.holdback_until.isoformat() if ledger.holdback_until else None,
        },
    )

    return PayoutLedgerResponse(
        id=str(ledger.id),
        ip_id=str(ledger.ip_id),
        creator_id=ledger.creator_id,
        gross_amount=ledger.gross_amount,
        ip_owner_share=ledger.ip_owner_share,
        creator_share=ledger.creator_share,
        platform_share=ledger.platform_share,
        status=ledger.status,
        holdback_until=ledger.holdback_until,
        dispute_id=str(ledger.dispute_id) if ledger.dispute_id else None,
        created_at=ledger.created_at,
        updated_at=ledger.updated_at,
    )


@router.post("/payout/admin/{ledger_id}/release", response_model=PayoutLedgerResponse)
async def admin_release_payout(
    ledger_id: UUID,
    force: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(require_admin),
):
    """Admin: release payout from holdback."""
    ledger = await db.get(IPPayoutLedger, ledger_id)
    if not ledger:
        raise HTTPException(status_code=404, detail="Payout ledger not found")

    now = datetime.utcnow()
    if (
        not force
        and ledger.holdback_until
        and ledger.holdback_until > now
        and ledger.status == "holdback"
    ):
        raise HTTPException(status_code=400, detail="Holdback period not yet elapsed")

    ledger.status = "released"
    ledger.holdback_until = ledger.holdback_until or now
    ledger.updated_at = now

    record_ops_action(
        db=db,
        action_type="ip_payout_release",
        status=ledger.status,
        actor_id=admin_user["id"],
        payload={
            "ledger_id": str(ledger.id),
            "forced": force,
        },
    )

    return PayoutLedgerResponse(
        id=str(ledger.id),
        ip_id=str(ledger.ip_id),
        creator_id=ledger.creator_id,
        gross_amount=ledger.gross_amount,
        ip_owner_share=ledger.ip_owner_share,
        creator_share=ledger.creator_share,
        platform_share=ledger.platform_share,
        status=ledger.status,
        holdback_until=ledger.holdback_until,
        dispute_id=str(ledger.dispute_id) if ledger.dispute_id else None,
        created_at=ledger.created_at,
        updated_at=ledger.updated_at,
    )


@router.get("/payout/admin/disputes", response_model=list[PayoutDisputeDetailResponse])
async def list_payout_disputes(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(require_admin),
):
    """Admin: list payout disputes."""
    query = select(IPPayoutDispute)
    if status:
        query = query.where(IPPayoutDispute.status == status)

    result = await db.execute(
        query.order_by(IPPayoutDispute.created_at.desc()).limit(limit)
    )
    disputes = result.scalars().all()

    return [
        PayoutDisputeDetailResponse(
            id=str(dispute.id),
            ledger_id=str(dispute.ledger_id),
            complainant_id=dispute.complainant_id,
            reason=dispute.reason,
            evidence=dispute.evidence or [],
            status=dispute.status,
            admin_notes=dispute.admin_notes,
            resolved_by=dispute.resolved_by,
            resolved_at=dispute.resolved_at,
            created_at=dispute.created_at,
            updated_at=dispute.updated_at,
        )
        for dispute in disputes
    ]


@router.post("/payout/admin/disputes/{dispute_id}/resolve", response_model=PayoutDisputeDetailResponse)
async def resolve_payout_dispute(
    dispute_id: UUID,
    payload: AdminDisputeResolveRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(require_admin),
):
    """Admin: resolve payout dispute (resolved or rejected)."""
    dispute = await db.get(IPPayoutDispute, dispute_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    if dispute.status not in {"open", "in_review"}:
        raise HTTPException(status_code=400, detail="Dispute already resolved")

    ledger = await db.get(IPPayoutLedger, dispute.ledger_id)
    if not ledger:
        raise HTTPException(status_code=404, detail="Payout ledger not found")

    now = datetime.utcnow()
    dispute.status = payload.status
    dispute.admin_notes = payload.admin_notes
    dispute.resolved_by = admin_user["id"]
    dispute.resolved_at = now
    dispute.updated_at = now

    if payload.status == "resolved":
        ledger.status = "released"
        ledger.holdback_until = ledger.holdback_until or now
    else:
        ledger.status = "holdback"
        ledger.holdback_until = ledger.holdback_until or now

    ledger.updated_at = now

    record_ops_action(
        db=db,
        action_type="ip_payout_dispute_resolve",
        status=payload.status,
        actor_id=admin_user["id"],
        note=payload.admin_notes,
        payload={
            "dispute_id": str(dispute.id),
            "ledger_id": str(ledger.id),
            "ledger_status": ledger.status,
        },
    )

    return PayoutDisputeDetailResponse(
        id=str(dispute.id),
        ledger_id=str(dispute.ledger_id),
        complainant_id=dispute.complainant_id,
        reason=dispute.reason,
        evidence=dispute.evidence or [],
        status=dispute.status,
        admin_notes=dispute.admin_notes,
        resolved_by=dispute.resolved_by,
        resolved_at=dispute.resolved_at,
        created_at=dispute.created_at,
        updated_at=dispute.updated_at,
    )


@router.post("/payout/{ledger_id}/dispute", response_model=PayoutDisputeResponse)
async def file_payout_dispute(
    ledger_id: UUID,
    payload: PayoutDisputeRequest,
    user_id: str = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Submit a payout dispute for IP revenue share."""
    ledger = await db.get(IPPayoutLedger, ledger_id)
    if not ledger:
        raise HTTPException(status_code=404, detail="Payout ledger not found")

    if ledger.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to dispute this payout")

    if ledger.status == "disputed":
        raise HTTPException(status_code=400, detail="Payout already under dispute")

    existing = await db.execute(
        select(IPPayoutDispute)
        .where(IPPayoutDispute.ledger_id == ledger_id)
        .where(IPPayoutDispute.status.in_(["open", "in_review"]))
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Existing dispute already open")

    dispute = IPPayoutDispute(
        ledger_id=ledger.id,
        complainant_id=user_id,
        reason=payload.reason,
        evidence=payload.evidence,
        status="open",
    )
    db.add(dispute)
    await db.flush()

    ledger.status = "disputed"
    ledger.dispute_id = dispute.id
    ledger.updated_at = datetime.utcnow()

    logger.info(
        "IP payout dispute created",
        extra={"ledger_id": str(ledger.id), "dispute_id": str(dispute.id), "user_id": user_id},
    )

    return PayoutDisputeResponse(
        dispute_id=str(dispute.id),
        ledger_id=str(ledger.id),
        status=dispute.status,
        created_at=dispute.created_at,
    )
