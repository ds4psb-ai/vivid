"""Affiliate referral helpers."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AffiliateReferral


async def activate_referrals_for_user(db: AsyncSession, user_id: str) -> int:
    """Mark referrals as activated when a referee completes their first run."""
    result = await db.execute(
        select(AffiliateReferral).where(
            AffiliateReferral.referee_user_id == user_id,
            AffiliateReferral.status.in_(["signed_up", "clicked"]),
            AffiliateReferral.reward_status == "pending",
        )
    )
    referrals = result.scalars().all()
    if not referrals:
        return 0

    updated = 0
    for referral in referrals:
        if referral.status != "activated":
            referral.status = "activated"
            updated += 1
    if updated:
        await db.commit()
    return updated
