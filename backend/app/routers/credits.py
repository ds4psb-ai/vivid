"""Credits API router for balance and transaction management."""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.credit_service import (
    deduct_credits as apply_credit_usage,
    get_or_create_user_credits,
    record_transaction,
)
from app.database import get_db
from app.models import CreditLedger


router = APIRouter(tags=["credits"])


# --- Pydantic Schemas ---

class BalanceResponse(BaseModel):
    """User credit balance response."""
    user_id: str
    balance: int
    subscription_credits: int
    topup_credits: int
    promo_credits: int
    promo_expires_at: Optional[datetime] = None


class TransactionResponse(BaseModel):
    """Single transaction in ledger."""
    id: str
    event_type: str
    amount: int
    balance_snapshot: int
    description: Optional[str] = None
    capsule_run_id: Optional[str] = None
    meta: dict = {}
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionsListResponse(BaseModel):
    """List of transactions response."""
    transactions: list[TransactionResponse]
    total: int


class TopupRequest(BaseModel):
    """Credit top-up request."""
    amount: int
    pack_id: Optional[str] = None


class TopupResponse(BaseModel):
    """Credit top-up response."""
    success: bool
    new_balance: int
    transaction_id: str


class DeductRequest(BaseModel):
    """Credit deduction request (for internal use)."""
    user_id: str
    amount: int
    description: str
    capsule_run_id: Optional[str] = None


# --- API Endpoints ---

@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    user_id: str = "demo-user",
    db: AsyncSession = Depends(get_db),
):
    """Get user's current credit balance."""
    user_credits = await get_or_create_user_credits(db, user_id)
    
    return BalanceResponse(
        user_id=user_credits.user_id,
        balance=user_credits.balance,
        subscription_credits=user_credits.subscription_credits,
        topup_credits=user_credits.topup_credits,
        promo_credits=user_credits.promo_credits,
        promo_expires_at=user_credits.promo_expires_at,
    )


@router.get("/transactions", response_model=TransactionsListResponse)
async def get_transactions(
    user_id: str = "demo-user",
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get user's transaction history."""
    # Ensure user exists
    await get_or_create_user_credits(db, user_id)
    
    # Get transactions
    result = await db.execute(
        select(CreditLedger)
        .where(CreditLedger.user_id == user_id)
        .order_by(desc(CreditLedger.created_at))
        .limit(limit)
        .offset(offset)
    )
    transactions = result.scalars().all()
    
    # Count total
    count_result = await db.execute(
        select(CreditLedger).where(CreditLedger.user_id == user_id)
    )
    total = len(count_result.scalars().all())
    
    return TransactionsListResponse(
        transactions=[
            TransactionResponse(
                id=str(tx.id),
                event_type=tx.event_type,
                amount=tx.amount,
                balance_snapshot=tx.balance_snapshot,
                description=tx.description,
                capsule_run_id=str(tx.capsule_run_id) if tx.capsule_run_id else None,
                meta=tx.meta or {},
                created_at=tx.created_at,
            )
            for tx in transactions
        ],
        total=total,
    )


@router.post("/topup", response_model=TopupResponse)
async def topup_credits(
    request: TopupRequest,
    user_id: str = "demo-user",
    db: AsyncSession = Depends(get_db),
):
    """Top up user credits (mock payment)."""
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    user_credits = await get_or_create_user_credits(db, user_id)
    
    # Update balance
    user_credits.balance += request.amount
    user_credits.topup_credits += request.amount
    await db.commit()
    
    # Record transaction
    entry = await record_transaction(
        db=db,
        user_id=user_id,
        event_type="topup",
        amount=request.amount,
        new_balance=user_credits.balance,
        description=f"Credit top-up: {request.pack_id or 'custom'}",
        meta={"pack_id": request.pack_id} if request.pack_id else None,
    )
    
    return TopupResponse(
        success=True,
        new_balance=user_credits.balance,
        transaction_id=str(entry.id),
    )


@router.post("/deduct")
async def deduct_credits(
    request: DeductRequest,
    db: AsyncSession = Depends(get_db),
):
    """Deduct credits for a capsule run (internal API)."""
    capsule_run_uuid = uuid.UUID(request.capsule_run_id) if request.capsule_run_id else None
    try:
        entry = await apply_credit_usage(
            db=db,
            user_id=request.user_id,
            amount=request.amount,
            description=request.description,
            capsule_run_id=capsule_run_uuid,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"success": True, "new_balance": entry.balance_snapshot}
