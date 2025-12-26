"""Seed data for auteur templates and capsule specs."""
from __future__ import annotations

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.fixtures.auteur_capsules import CAPSULE_SPECS
from app.fixtures.auteur_templates import TEMPLATES
from app.database import AsyncSessionLocal
from app.models import CapsuleSpec, Template, TemplateVersion
from app.patterns import get_latest_pattern_version


async def seed_capsules(session: AsyncSession) -> int:
    created = 0
    for spec in CAPSULE_SPECS:
        result = await session.execute(
            select(CapsuleSpec).where(
                CapsuleSpec.capsule_key == spec["capsule_key"],
                CapsuleSpec.version == spec["version"],
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            if existing.display_name != spec["display_name"]:
                existing.display_name = spec["display_name"]
            if existing.description != spec["description"]:
                existing.description = spec["description"]
            desired_spec = spec.get("spec") or {}
            desired_pattern_version = desired_spec.get("patternVersion")
            current_spec = existing.spec or {}
            if desired_pattern_version and not current_spec.get("patternVersion"):
                current_spec["patternVersion"] = desired_pattern_version

            desired_inputs = desired_spec.get("inputs") or {}
            current_inputs = current_spec.get("inputs") or {}
            if "source_id" in desired_inputs and "source_id" not in current_inputs:
                current_inputs = {**current_inputs, "source_id": desired_inputs["source_id"]}
                current_spec["inputs"] = current_inputs

            desired_contracts = desired_spec.get("inputContracts") or {}
            current_contracts = current_spec.get("inputContracts") or {}
            desired_optional = set(desired_contracts.get("optional") or [])
            current_optional = set(current_contracts.get("optional") or [])
            if desired_optional - current_optional:
                current_contracts["optional"] = sorted(current_optional | desired_optional)
                if current_contracts:
                    current_spec["inputContracts"] = current_contracts

            existing.spec = current_spec
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
    pattern_version = await get_latest_pattern_version(session)
    for template in TEMPLATES:
        result = await session.execute(
            select(Template).where(Template.slug == template["slug"])
        )
        existing = result.scalar_one_or_none()
        if existing:
            graph_data = existing.graph_data or {}
            updated = False
            if existing.title != template["title"]:
                existing.title = template["title"]
                updated = True
            if existing.description != template["description"]:
                existing.description = template["description"]
                updated = True
            if existing.tags != template["tags"]:
                existing.tags = template["tags"]
                updated = True
            if existing.preview_video_url != template.get("preview_video_url"):
                existing.preview_video_url = template.get("preview_video_url")
                updated = True
            patched_graph = _ensure_pattern_version(graph_data, pattern_version)
            if patched_graph is not None:
                graph_data = patched_graph
                updated = True

            pipeline_graph = _ensure_processing_pipeline(graph_data)
            if pipeline_graph is not None:
                graph_data = pipeline_graph
                updated = True

            desired_meta = None
            fixture_graph = template.get("graph_data")
            if isinstance(fixture_graph, dict):
                desired_meta = fixture_graph.get("meta")
            meta_graph = _ensure_graph_meta(graph_data, desired_meta)
            if meta_graph is not None:
                graph_data = meta_graph
                updated = True
            else:
                merged_graph = _merge_graph_meta(graph_data, desired_meta)
                if merged_graph is not None:
                    graph_data = merged_graph
                    updated = True

            if updated:
                existing.graph_data = graph_data
                version_result = await session.execute(
                    select(TemplateVersion).where(
                        TemplateVersion.template_id == existing.id,
                        TemplateVersion.version == existing.version,
                    )
                )
                current_version = version_result.scalar_one_or_none()
                if current_version:
                    current_version.graph_data = graph_data
            continue

        item = Template(
            slug=template["slug"],
            title=template["title"],
            description=template["description"],
            tags=template["tags"],
            graph_data=_ensure_pattern_version(template["graph_data"], pattern_version) or template["graph_data"],
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


def _ensure_pattern_version(graph_data: dict, pattern_version: str) -> Optional[dict]:
    nodes = graph_data.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        return None
    updated = False
    next_nodes = []
    for node in nodes:
        if not isinstance(node, dict):
            next_nodes.append(node)
            continue
        data = node.get("data")
        if not isinstance(data, dict) or data.get("patternVersion"):
            next_nodes.append(node)
            continue
        if data.get("capsuleId") and data.get("capsuleVersion"):
            patched = {**data, "patternVersion": pattern_version}
            next_nodes.append({**node, "data": patched})
            updated = True
        else:
            next_nodes.append(node)
    if not updated:
        return None
    return {**graph_data, "nodes": next_nodes}


def _ensure_processing_pipeline(graph_data: dict) -> Optional[dict]:
    nodes = graph_data.get("nodes")
    edges = graph_data.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return None
    if any(isinstance(node, dict) and node.get("type") == "processing" for node in nodes):
        return None
    if len(nodes) != 3:
        return None

    input_node = next((node for node in nodes if isinstance(node, dict) and node.get("type") == "input"), None)
    capsule_node = next((node for node in nodes if isinstance(node, dict) and node.get("type") == "capsule"), None)
    output_node = next((node for node in nodes if isinstance(node, dict) and node.get("type") == "output"), None)
    if not input_node or not capsule_node or not output_node:
        return None
    if not input_node.get("id") or not capsule_node.get("id") or not output_node.get("id"):
        return None

    capsule_pos = capsule_node.get("position") or {}
    base_x = capsule_pos.get("x", 360)
    base_y = capsule_pos.get("y", 220)
    script_node = {
        "id": "script-1",
        "type": "processing",
        "position": {"x": base_x + 260, "y": base_y - 20},
        "data": {
            "label": "Script / Beat",
            "subtitle": "story beats",
            "seed": {"story_beats": []},
        },
    }
    storyboard_node = {
        "id": "storyboard-1",
        "type": "processing",
        "position": {"x": base_x + 520, "y": base_y - 20},
        "data": {
            "label": "Storyboard",
            "subtitle": "scene cards",
            "seed": {"storyboard_cards": []},
        },
    }
    updated_output = {
        **output_node,
        "position": {"x": base_x + 760, "y": base_y},
    }

    upgraded_nodes = [input_node, capsule_node, script_node, storyboard_node, updated_output]
    upgraded_edges = [
        {"id": "e-input-capsule", "source": input_node["id"], "target": capsule_node["id"]},
        {"id": "e-capsule-script", "source": capsule_node["id"], "target": script_node["id"]},
        {"id": "e-script-storyboard", "source": script_node["id"], "target": storyboard_node["id"]},
        {"id": "e-storyboard-output", "source": storyboard_node["id"], "target": updated_output["id"]},
    ]

    return {**graph_data, "nodes": upgraded_nodes, "edges": upgraded_edges}


def _ensure_graph_meta(graph_data: dict, desired_meta: Optional[dict]) -> Optional[dict]:
    if not isinstance(graph_data, dict) or not isinstance(desired_meta, dict):
        return None
    if isinstance(graph_data.get("meta"), dict):
        return None
    return {**graph_data, "meta": desired_meta}


def _merge_graph_meta(graph_data: dict, desired_meta: Optional[dict]) -> Optional[dict]:
    if not isinstance(graph_data, dict) or not isinstance(desired_meta, dict):
        return None
    meta = graph_data.get("meta")
    if not isinstance(meta, dict):
        return None
    updated = False
    next_meta = dict(meta)
    if "production_contract" in desired_meta and "production_contract" not in next_meta:
        next_meta["production_contract"] = desired_meta["production_contract"]
        updated = True
    if not updated:
        return None
    return {**graph_data, "meta": next_meta}


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
