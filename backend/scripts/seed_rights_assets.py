#!/usr/bin/env python3
"""Seed initial RightsAsset records for Foundry rights evaluation.

Usage:
    cd backend && python -m scripts.seed_rights_assets
"""
from __future__ import annotations

import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


SEED_ASSETS = [
    {
        "asset_id": "cc_film_chaplin_001",
        "source_type": "film_clip",
        "license_type": "PUBLIC_DOMAIN",
        "source_license": "Public Domain (pre-1928)",
        "allowed_actions": ["reference", "style_transfer", "educational", "commercial"],
        "blocked_elements": [],
        "attribution_required": False,
        "derivative_allowed": True,
        "notes": "Charlie Chaplin silent era clips - public domain",
    },
    {
        "asset_id": "cc_film_archive_002",
        "source_type": "film_clip",
        "license_type": "CC_BY",
        "source_license": "Creative Commons Attribution 4.0",
        "allowed_actions": ["reference", "style_transfer", "educational"],
        "blocked_elements": [],
        "attribution_required": True,
        "derivative_allowed": True,
        "notes": "Open Culture Film Archive - CC-BY",
    },
    {
        "asset_id": "cc_film_archive_003",
        "source_type": "film_clip",
        "license_type": "CC_BY_SA",
        "source_license": "Creative Commons Attribution-ShareAlike 4.0",
        "allowed_actions": ["reference", "educational"],
        "blocked_elements": ["commercial_use"],
        "attribution_required": True,
        "derivative_allowed": True,
        "notes": "CC-BY-SA archive - share alike required",
    },
    {
        "asset_id": "cc_film_cc0_004",
        "source_type": "film_clip",
        "license_type": "CC0",
        "source_license": "CC0 1.0 Universal Public Domain Dedication",
        "allowed_actions": ["reference", "style_transfer", "educational", "commercial"],
        "blocked_elements": [],
        "attribution_required": False,
        "derivative_allowed": True,
        "notes": "CC0 - no rights reserved",
    },
    {
        "asset_id": "stock_footage_mit_005",
        "source_type": "stock_footage",
        "license_type": "MIT_MEDIA",
        "source_license": "MIT Open Documentary Lab License",
        "allowed_actions": ["reference", "educational", "research"],
        "blocked_elements": ["commercial_use", "broadcast"],
        "attribution_required": True,
        "derivative_allowed": True,
        "notes": "MIT Media Lab documentary clips",
    },
    {
        "asset_id": "archive_org_film_006",
        "source_type": "film_clip",
        "license_type": "PUBLIC_DOMAIN",
        "source_license": "Public Domain (Archive.org)",
        "allowed_actions": ["reference", "style_transfer", "educational", "commercial"],
        "blocked_elements": [],
        "attribution_required": False,
        "derivative_allowed": True,
        "notes": "Archive.org public domain film collection",
    },
    {
        "asset_id": "nfb_canada_007",
        "source_type": "documentary",
        "license_type": "CC_BY_NC",
        "source_license": "Creative Commons Attribution-NonCommercial 4.0",
        "allowed_actions": ["reference", "educational"],
        "blocked_elements": ["commercial_use"],
        "attribution_required": True,
        "derivative_allowed": True,
        "notes": "National Film Board of Canada - educational use",
    },
    {
        "asset_id": "wikimedia_commons_008",
        "source_type": "film_clip",
        "license_type": "CC_BY_SA",
        "source_license": "Wikimedia Commons CC-BY-SA",
        "allowed_actions": ["reference", "educational", "style_transfer"],
        "blocked_elements": [],
        "attribution_required": True,
        "derivative_allowed": True,
        "notes": "Wikimedia Commons historical footage",
    },
    {
        "asset_id": "prelinger_archive_009",
        "source_type": "industrial_film",
        "license_type": "PUBLIC_DOMAIN",
        "source_license": "Prelinger Archives - Public Domain",
        "allowed_actions": ["reference", "style_transfer", "educational", "commercial"],
        "blocked_elements": [],
        "attribution_required": False,
        "derivative_allowed": True,
        "notes": "Prelinger Archives industrial/educational films",
    },
    {
        "asset_id": "openverse_clip_010",
        "source_type": "film_clip",
        "license_type": "CC_BY",
        "source_license": "Openverse CC Attribution 4.0",
        "allowed_actions": ["reference", "style_transfer", "educational"],
        "blocked_elements": ["adult_content"],
        "attribution_required": True,
        "derivative_allowed": True,
        "notes": "WordPress Openverse curated clips",
    },
]


async def seed():
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.config import settings
    from app.models_rights_graph import RightsAsset

    database_url = settings.DATABASE_URL
    if not database_url:
        print("ERROR: DATABASE_URL not set", flush=True)
        sys.exit(1)

    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        inserted = 0
        skipped = 0
        for asset_data in SEED_ASSETS:
            result = await db.execute(
                select(RightsAsset).where(RightsAsset.asset_id == asset_data["asset_id"])
            )
            if result.scalar_one_or_none() is None:
                db.add(RightsAsset(**asset_data))
                inserted += 1
            else:
                skipped += 1
        await db.commit()
        print(f"Seed complete: {inserted} inserted, {skipped} skipped", flush=True)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
