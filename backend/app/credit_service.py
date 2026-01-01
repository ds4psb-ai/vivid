"""Credit balance helpers shared across routers."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CreditLedger, UserCredits


async def get_or_create_user_credits(
    db: AsyncSession,
    user_id: str,
    seed_balance: int = 1000,
) -> UserCredits:
    """Fetch user credits or initialize with a default balance."""
    result = await db.execute(select(UserCredits).where(UserCredits.user_id == user_id))
    user_credits = result.scalar_one_or_none()

    if not user_credits:
        user_credits = UserCredits(
            user_id=user_id,
            balance=seed_balance,
            subscription_credits=0,
            topup_credits=seed_balance,
            promo_credits=0,
        )
        db.add(user_credits)
        await db.commit()
        await db.refresh(user_credits)

        entry = CreditLedger(
            user_id=user_id,
            event_type="promo",
            amount=seed_balance,
            balance_snapshot=seed_balance,
            description="Welcome bonus credits",
        )
        db.add(entry)
        await db.commit()

    return user_credits


async def record_transaction(
    db: AsyncSession,
    user_id: str,
    event_type: str,
    amount: int,
    new_balance: int,
    description: Optional[str] = None,
    capsule_run_id: Optional[uuid.UUID] = None,
    meta: Optional[dict] = None,
) -> CreditLedger:
    """Record a credit transaction in the ledger."""
    entry = CreditLedger(
        user_id=user_id,
        event_type=event_type,
        amount=amount,
        balance_snapshot=new_balance,
        description=description,
        capsule_run_id=capsule_run_id,
        meta=meta or {},
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def deduct_credits(
    db: AsyncSession,
    user_id: str,
    amount: int,
    description: str,
    capsule_run_id: Optional[uuid.UUID] = None,
    meta: Optional[dict] = None,
) -> CreditLedger:
    """Deduct credits using promo -> subscription -> topup order."""
    if amount <= 0:
        raise ValueError("Amount must be positive")

    user_credits = await get_or_create_user_credits(db, user_id)

    if user_credits.balance < amount:
        raise ValueError("Insufficient credits")

    remaining = amount
    promo_used = 0
    subscription_used = 0
    topup_used = 0

    if user_credits.promo_credits > 0:
        if user_credits.promo_expires_at is None or user_credits.promo_expires_at > datetime.utcnow():
            promo_used = min(remaining, user_credits.promo_credits)
            user_credits.promo_credits -= promo_used
            remaining -= promo_used

    if remaining > 0 and user_credits.subscription_credits > 0:
        subscription_used = min(remaining, user_credits.subscription_credits)
        user_credits.subscription_credits -= subscription_used
        remaining -= subscription_used

    if remaining > 0 and user_credits.topup_credits > 0:
        topup_used = min(remaining, user_credits.topup_credits)
        user_credits.topup_credits -= topup_used
        remaining -= topup_used

    user_credits.balance -= amount
    await db.commit()

    breakdown = {
        "promo": promo_used,
        "subscription": subscription_used,
        "topup": topup_used,
    }
    ledger_meta = {**(meta or {}), "breakdown": breakdown}
    entry = await record_transaction(
        db=db,
        user_id=user_id,
        event_type="usage",
        amount=-amount,
        new_balance=user_credits.balance,
        description=description,
        capsule_run_id=capsule_run_id,
        meta=ledger_meta,
    )
    return entry


async def grant_promo_credits(
    db: AsyncSession,
    user_id: str,
    amount: int,
    description: str,
    expires_in_days: int = 90,
    meta: Optional[dict] = None,
    event_type: str = "reward",
) -> CreditLedger:
    """Grant promo credits to a user with optional expiry."""
    if amount <= 0:
        raise ValueError("Amount must be positive")

    user_credits = await get_or_create_user_credits(db, user_id)
    user_credits.balance += amount
    user_credits.promo_credits += amount
    if expires_in_days > 0:
        next_expiry = datetime.utcnow() + timedelta(days=expires_in_days)
        if user_credits.promo_expires_at is None or user_credits.promo_expires_at < next_expiry:
            user_credits.promo_expires_at = next_expiry
    await db.commit()

    entry = await record_transaction(
        db=db,
        user_id=user_id,
        event_type=event_type,
        amount=amount,
        new_balance=user_credits.balance,
        description=description,
        capsule_run_id=None,
        meta=meta or {},
    )
    return entry


async def refund_credits(
    db: AsyncSession,
    user_id: str,
    amount: int,
    description: str,
    capsule_run_id: Optional[uuid.UUID] = None,
    meta: Optional[dict] = None,
) -> CreditLedger:
    """
    Refund credits for failed or cancelled capsule runs.
    
    Credits are restored to topup_credits bucket (simplest refund strategy).
    A ledger entry is recorded with event_type='refund' for audit trail.
    """
    if amount <= 0:
        raise ValueError("Refund amount must be positive")

    user_credits = await get_or_create_user_credits(db, user_id)
    
    # Add back to topup bucket and total balance
    user_credits.topup_credits += amount
    user_credits.balance += amount
    await db.commit()

    refund_meta = {
        **(meta or {}),
        "refund_reason": description,
        "refund_to_bucket": "topup",
    }
    
    entry = await record_transaction(
        db=db,
        user_id=user_id,
        event_type="refund",
        amount=amount,
        new_balance=user_credits.balance,
        description=f"Refund: {description}",
        capsule_run_id=capsule_run_id,
        meta=refund_meta,
    )
    return entry
