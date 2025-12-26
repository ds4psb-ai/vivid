"""Update auteur template text (Korean) without overwriting custom graph data."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Dict, Optional

from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import AsyncSessionLocal
from app.fixtures.auteur_templates import TEMPLATES
from app.models import Template, TemplateVersion


def _patch_graph_data(existing: Dict, fixture: Dict) -> Optional[Dict]:
    if not isinstance(existing, dict) or not isinstance(fixture, dict):
        return None
    existing_nodes = existing.get("nodes")
    fixture_nodes = fixture.get("nodes")
    if not isinstance(existing_nodes, list) or not isinstance(fixture_nodes, list):
        return None

    fixture_by_id = {
        node.get("id"): node
        for node in fixture_nodes
        if isinstance(node, dict) and node.get("id")
    }

    updated = False
    next_nodes = []
    for node in existing_nodes:
        if not isinstance(node, dict) or not node.get("id"):
            next_nodes.append(node)
            continue
        fixture_node = fixture_by_id.get(node.get("id"))
        if not fixture_node:
            next_nodes.append(node)
            continue
        data = node.get("data")
        fixture_data = fixture_node.get("data")
        if not isinstance(data, dict) or not isinstance(fixture_data, dict):
            next_nodes.append(node)
            continue

        next_data = dict(data)
        for key in ("label", "subtitle"):
            if key in fixture_data and fixture_data[key] != data.get(key):
                next_data[key] = fixture_data[key]
                updated = True

        if fixture_data.get("locked") and not data.get("locked"):
            next_data["locked"] = True
            updated = True

        if updated and next_data is not data:
            next_nodes.append({**node, "data": next_data})
        else:
            next_nodes.append(node)

    if not updated:
        return None
    return {**existing, "nodes": next_nodes}


async def main() -> None:
    updated = 0
    async with AsyncSessionLocal() as session:
        for template in TEMPLATES:
            slug = template.get("slug")
            if not slug:
                continue
            result = await session.execute(select(Template).where(Template.slug == slug))
            existing = result.scalar_one_or_none()
            if not existing:
                continue

            changed = False
            if template.get("title") and existing.title != template["title"]:
                existing.title = template["title"]
                changed = True
            if template.get("description") and existing.description != template["description"]:
                existing.description = template["description"]
                changed = True
            if template.get("tags") and existing.tags != template["tags"]:
                existing.tags = template["tags"]
                changed = True

            fixture_graph = template.get("graph_data")
            patched_graph = _patch_graph_data(existing.graph_data or {}, fixture_graph or {})
            if patched_graph is not None:
                existing.graph_data = patched_graph
                changed = True
                version_result = await session.execute(
                    select(TemplateVersion).where(
                        TemplateVersion.template_id == existing.id,
                        TemplateVersion.version == existing.version,
                    )
                )
                current_version = version_result.scalar_one_or_none()
                if current_version:
                    current_version.graph_data = patched_graph

            if changed:
                updated += 1

        if updated:
            await session.commit()

    print(f"Updated templates: {updated}")


if __name__ == "__main__":
    asyncio.run(main())
