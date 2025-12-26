"""Pattern-related helpers."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.fixtures.auteur_capsules import PATTERN_VERSION
from app.models import PatternVersion


async def get_latest_pattern_version(db: AsyncSession) -> str:
    result = await db.execute(
        select(PatternVersion).order_by(PatternVersion.created_at.desc())
    )
    record = result.scalars().first()
    if record and record.version:
        return record.version
    return PATTERN_VERSION
