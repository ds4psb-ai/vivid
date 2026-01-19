"""IP payout holdback utilities."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_ip import IPPayoutLedger


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
