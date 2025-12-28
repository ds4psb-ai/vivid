"""Shared helpers for pattern version bumps and capsule/template refresh."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, Optional, Set, Tuple

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import CapsuleSpec, PatternVersion, Template, TemplateVersion
from app.patterns import get_latest_pattern_version

PATTERN_VERSION_RE = re.compile(r"^v(\d+)$", re.IGNORECASE)
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def next_pattern_version(current: Optional[str]) -> str:
    if not current:
        return "v1"
    match = PATTERN_VERSION_RE.match(current.strip())
    if not match:
        return "v1"
    return f"v{int(match.group(1)) + 1}"


def _next_capsule_version(version: str, existing_versions: Set[str]) -> str:
    match = SEMVER_RE.match(version.strip())
    if not match:
        raise ValueError(f"CapsuleSpec version must be semver (got '{version}')")
    major, minor, patch = (int(part) for part in match.groups())
    while True:
        patch += 1
        candidate = f"{major}.{minor}.{patch}"
        if candidate not in existing_versions:
            return candidate


async def bump_pattern_version(note: str) -> str:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PatternVersion).order_by(PatternVersion.created_at.desc()).limit(1)
        )
        latest = result.scalars().first()
        next_version = next_pattern_version(latest.version if latest else None)
        snapshot = PatternVersion(version=next_version, note=note)
        session.add(snapshot)
        await session.commit()
        return next_version


async def update_capsule_specs(
    pattern_version: str,
    *,
    dry_run: bool = False,
    only_active: bool = True,
) -> int:
    async with AsyncSessionLocal() as session:
        query = select(CapsuleSpec)
        if only_active:
            query = query.where(CapsuleSpec.is_active.is_(True))
        result = await session.execute(query)
        specs = result.scalars().all()
        updated = 0
        grouped: Dict[str, list[CapsuleSpec]] = {}
        for spec in specs:
            grouped.setdefault(spec.capsule_key, []).append(spec)

        for capsule_key, items in grouped.items():
            active_items = [item for item in items if item.is_active]
            candidates = active_items if active_items else items
            spec = max(
                candidates,
                key=lambda item: item.created_at or datetime.min,
            )
            payload = spec.spec or {}
            current = payload.get("patternVersion") or payload.get("pattern_version")
            if current == pattern_version:
                continue
            versions_result = await session.execute(
                select(CapsuleSpec.version).where(CapsuleSpec.capsule_key == capsule_key)
            )
            existing_versions = {row[0] for row in versions_result.all() if row[0]}
            next_version = _next_capsule_version(spec.version, existing_versions)
            next_payload = dict(payload)
            next_payload.pop("pattern_version", None)
            next_payload["patternVersion"] = pattern_version
            next_active = True if active_items else spec.is_active
            for item in active_items:
                item.is_active = False
            session.add(
                CapsuleSpec(
                    capsule_key=spec.capsule_key,
                    version=next_version,
                    display_name=spec.display_name,
                    description=spec.description,
                    spec=next_payload,
                    is_active=next_active,
                )
            )
            updated += 1
        if dry_run:
            await session.rollback()
        else:
            await session.commit()
        return updated


async def _latest_capsule_versions(session) -> Dict[str, str]:
    result = await session.execute(
        select(CapsuleSpec)
        .where(CapsuleSpec.is_active.is_(True))
        .order_by(CapsuleSpec.created_at.desc())
    )
    versions: Dict[str, str] = {}
    for spec in result.scalars().all():
        if spec.capsule_key not in versions:
            versions[spec.capsule_key] = spec.version
    return versions


def apply_pattern_version_to_graph(
    graph_data: dict,
    pattern_version: str,
    capsule_versions: Optional[Dict[str, str]] = None,
) -> Optional[dict]:
    if not isinstance(graph_data, dict):
        return None
    nodes = graph_data.get("nodes")
    if not isinstance(nodes, list):
        return None
    updated = False
    next_nodes = []
    for node in nodes:
        if not isinstance(node, dict):
            next_nodes.append(node)
            continue
        data = node.get("data")
        if not isinstance(data, dict):
            next_nodes.append(node)
            continue
        if data.get("capsuleId") and data.get("capsuleVersion"):
            patched = dict(data)
            capsule_key = str(data.get("capsuleId"))
            latest_version = capsule_versions.get(capsule_key) if capsule_versions else None
            if latest_version and data.get("capsuleVersion") != latest_version:
                patched["capsuleVersion"] = latest_version
            if data.get("patternVersion") != pattern_version:
                patched["patternVersion"] = pattern_version
            if patched != data:
                next_nodes.append({**node, "data": patched})
                updated = True
                continue
        next_nodes.append(node)
    if not updated:
        return None
    return {**graph_data, "nodes": next_nodes}


async def update_template_versions(pattern_version: str, note: str) -> int:
    async with AsyncSessionLocal() as session:
        capsule_versions = await _latest_capsule_versions(session)
        result = await session.execute(select(Template))
        templates = result.scalars().all()
        updated = 0
        for template in templates:
            updated_graph = apply_pattern_version_to_graph(
                template.graph_data or {},
                pattern_version,
                capsule_versions=capsule_versions,
            )
            if not updated_graph:
                continue
            template.graph_data = updated_graph
            template.version = (template.version or 1) + 1
            session.add(
                TemplateVersion(
                    template_id=template.id,
                    version=template.version,
                    graph_data=updated_graph,
                    notes=note,
                    creator_id=template.creator_id,
                )
            )
            updated += 1
        await session.commit()
        return updated


async def refresh_capsule_specs(
    pattern_version: Optional[str] = None,
    *,
    dry_run: bool = False,
    only_active: bool = True,
) -> Tuple[str, int]:
    async with AsyncSessionLocal() as session:
        resolved = pattern_version.strip() if pattern_version and pattern_version.strip() else ""
        if not resolved:
            resolved = await get_latest_pattern_version(session)
    updated = await update_capsule_specs(
        resolved,
        dry_run=dry_run,
        only_active=only_active,
    )
    return resolved, updated
