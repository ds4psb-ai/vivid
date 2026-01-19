"""IP payout holdback utilities."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_ip import IPPayoutLedger, IPGeneration, IPRights


DEFAULT_IP_OWNER_SHARE = 30
DEFAULT_PLATFORM_SHARE = 20
HOLD_BACK_DAYS = 7


def calculate_payout_split(
    total_credits: int,
    ip_owner_percent: Optional[int] = None,
) -> Tuple[int, int, int]:
    """Calculate payout split (ip_owner, creator, platform)."""
    if total_credits <= 0:
        return 0, 0, 0

    owner_percent = ip_owner_percent if ip_owner_percent and ip_owner_percent > 0 else DEFAULT_IP_OWNER_SHARE
    owner_percent = max(0, min(owner_percent, 100))

    remaining = max(0, 100 - owner_percent)
    platform_percent = min(DEFAULT_PLATFORM_SHARE, remaining)
    creator_percent = max(0, remaining - platform_percent)

    ip_owner_share = int(round(total_credits * owner_percent / 100))
    platform_share = int(round(total_credits * platform_percent / 100))
    creator_share = max(0, total_credits - ip_owner_share - platform_share)

    return ip_owner_share, creator_share, platform_share


async def ensure_payout_ledger(
    db: AsyncSession,
    generation: IPGeneration,
    rights: Optional[IPRights],
) -> Optional[IPPayoutLedger]:
    """Create payout ledger for a generation if missing."""
    if generation.credits_consumed <= 0:
        return None

    existing = await db.execute(
        select(IPPayoutLedger)
        .where(IPPayoutLedger.generation_id == generation.id)
    )
    ledger = existing.scalar_one_or_none()
    if ledger:
        return ledger

    ip_owner_share, creator_share, platform_share = calculate_payout_split(
        generation.credits_consumed,
        rights.revenue_share_percent if rights else None,
    )

    holdback_until = datetime.utcnow() + timedelta(days=HOLD_BACK_DAYS)
    ledger = IPPayoutLedger(
        ip_id=generation.ip_id,
        generation_id=generation.id,
        creator_id=generation.user_id,
        gross_amount=generation.credits_consumed,
        ip_owner_share=ip_owner_share,
        creator_share=creator_share,
        platform_share=platform_share,
        status="holdback",
        holdback_until=holdback_until,
    )
    db.add(ledger)
    await db.flush()
    return ledger


async def release_due_holdbacks(
    db: AsyncSession,
    limit: int = 200,
    processed_by: str = "cron:ip_payout_release",
) -> Dict[str, Any]:
    """Release payout ledgers whose holdback period has elapsed."""
    now = datetime.utcnow()

    result = await db.execute(
        select(IPPayoutLedger)
        .where(IPPayoutLedger.status == "holdback")
        .where(IPPayoutLedger.holdback_until.is_not(None))
        .where(IPPayoutLedger.holdback_until <= now)
        .order_by(IPPayoutLedger.holdback_until.asc())
        .limit(limit)
    )
    ledgers = result.scalars().all()

    released = 0
    for ledger in ledgers:
        ledger.status = "released"
        ledger.updated_at = now
        released += 1

    return {
        "processed": len(ledgers),
        "released": released,
        "processed_by": processed_by,
    }
