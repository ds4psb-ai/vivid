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
from app.dependencies import get_current_user
from app.models_ip import IPPayoutLedger, IPPayoutDispute

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ip-payout"])


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
