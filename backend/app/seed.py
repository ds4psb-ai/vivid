"""Seed data for auteur templates and capsule specs."""
from __future__ import annotations

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.fixtures.auteur_capsules import CAPSULE_SPECS
from app.fixtures.auteur_templates import TEMPLATES
from app.database import AsyncSessionLocal
from app.models import CapsuleSpec, Template, TemplateVersion


async def seed_capsules(session: AsyncSession) -> int:
    created = 0
    for spec in CAPSULE_SPECS:
        result = await session.execute(
            select(CapsuleSpec).where(
                CapsuleSpec.capsule_key == spec["capsule_key"],
                CapsuleSpec.version == spec["version"],
            )
        )
        if result.scalar_one_or_none():
            continue

        session.add(
            CapsuleSpec(
                capsule_key=spec["capsule_key"],
                version=spec["version"],
                display_name=spec["display_name"],
                description=spec["description"],
                spec=spec["spec"],
                is_active=True,
            )
        )
        created += 1

    return created


async def seed_templates(session: AsyncSession) -> int:
    created = 0
    for template in TEMPLATES:
        result = await session.execute(
            select(Template).where(Template.slug == template["slug"])
        )
        if result.scalar_one_or_none():
            continue

        item = Template(
            slug=template["slug"],
            title=template["title"],
            description=template["description"],
            tags=template["tags"],
            graph_data=template["graph_data"],
            is_public=True,
            preview_video_url=template.get("preview_video_url"),
            version=1,
        )
        session.add(item)
        await session.flush()
        session.add(
            TemplateVersion(
                template_id=item.id,
                version=item.version,
                graph_data=item.graph_data,
                notes="seed",
                creator_id=item.creator_id,
            )
        )
        created += 1

    return created


async def seed_auteur_data(session: Optional[AsyncSession] = None) -> dict:
    if session is None:
        async with AsyncSessionLocal() as new_session:
            return await _seed_with_session(new_session)
    return await _seed_with_session(session)


async def _seed_with_session(session: AsyncSession) -> dict:
    created_capsules = await seed_capsules(session)
    created_templates = await seed_templates(session)
    await session.commit()
    return {
        "capsules": created_capsules,
        "templates": created_templates,
    }
