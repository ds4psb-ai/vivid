"""Template seeding helpers."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.graph_utils import collect_storyboard_refs
from app.template_graph import build_template_graph
from app.models import EvidenceRecord, Template, TemplateVersion
from app.patterns import get_latest_pattern_version


def _unique_tags(tags: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for tag in tags:
        cleaned = tag.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result



def _select_story_beats(records: List[EvidenceRecord]) -> List[dict]:
    for record in records:
        if record.guide_type in {"story", "beat_sheet"} and record.story_beats:
            return list(record.story_beats)
    return []


def _select_storyboard_cards(records: List[EvidenceRecord]) -> List[dict]:
    for record in records:
        if record.guide_type == "storyboard" and record.storyboard_cards:
            return list(record.storyboard_cards)
    return []


def _derive_tags(records: List[EvidenceRecord]) -> List[str]:
    tags: List[str] = []
    for record in records:
        tags.extend([t for t in (record.labels or []) if isinstance(t, str)])
        tags.extend([t for t in (record.signature_motifs or []) if isinstance(t, str)])
        for entry in record.key_patterns or []:
            if isinstance(entry, dict):
                name = entry.get("pattern_name") or entry.get("name")
            elif isinstance(entry, str):
                name = entry
            else:
                name = None
            if isinstance(name, str):
                cleaned = name.strip()
                if cleaned:
                    tags.append(cleaned)
    return _unique_tags(tags)


def _collect_guide_types(records: List[EvidenceRecord]) -> List[str]:
    guide_types = []
    for record in records:
        if not record.guide_type:
            continue
        guide_types.append(record.guide_type)
    return _unique_tags(guide_types)


def _collect_evidence_refs(records: List[EvidenceRecord]) -> List[str]:
    refs: List[str] = []
    for record in records:
        for ref in record.evidence_refs or []:
            if not isinstance(ref, str):
                continue
            cleaned = ref.strip()
            if not cleaned:
                continue
            lowered = cleaned.lower()
            if lowered.startswith("sheet:") or lowered.startswith("db:"):
                refs.append(cleaned)
    return _unique_tags(refs)



def _select_capsule_record(records: List[EvidenceRecord]) -> Optional[EvidenceRecord]:
    for record in records:
        if record.guide_type in {"homage", "variation"}:
            return record
    return None


def _derive_capsule_params(record: Optional[EvidenceRecord]) -> dict:
    if not record:
        return {}
    params: dict = {}
    camera_motion = record.camera_motion or {}
    if isinstance(camera_motion, dict):
        mode = camera_motion.get("mode") or camera_motion.get("value")
        if isinstance(mode, str) and mode.strip():
            params["camera_motion"] = mode.strip()
    color_palette = record.color_palette or {}
    if isinstance(color_palette, dict):
        bias = color_palette.get("bias")
        if isinstance(bias, str) and bias.strip():
            params["color_bias"] = bias.strip()
    pacing = record.pacing or {}
    if isinstance(pacing, dict):
        tempo = pacing.get("tempo") or pacing.get("speed")
        if isinstance(tempo, str) and tempo.strip():
            params["pacing"] = tempo.strip()
    confidence = record.cluster_confidence or record.confidence
    if confidence is not None:
        try:
            value = float(confidence)
            if 0 <= value <= 1:
                params["style_intensity"] = round(max(0.4, min(value, 0.9)), 2)
        except (TypeError, ValueError):
            pass
    return params


async def seed_template_from_evidence(
    db: AsyncSession,
    *,
    slug: str,
    title: str,
    description: str,
    capsule_key: str,
    capsule_version: str,
    notebook_id: str,
    tags: Optional[List[str]] = None,
    is_public: bool = False,
    creator_id: Optional[str] = None,
) -> Template:
    result = await db.execute(select(Template).where(Template.slug == slug))
    existing = result.scalars().first()
    if existing:
        raise ValueError(f"Template slug already exists: {slug}")

    result = await db.execute(
        select(EvidenceRecord)
        .where(EvidenceRecord.notebook_id == notebook_id)
        .order_by(EvidenceRecord.generated_at.desc().nullslast(), EvidenceRecord.updated_at.desc())
    )
    records = result.scalars().all()
    story_beats = _select_story_beats(records)
    storyboard_cards = _select_storyboard_cards(records)
    derived_tags = _derive_tags(records)
    resolved_tags = _unique_tags([*(tags or []), *derived_tags])
    capsule_record = _select_capsule_record(records)
    capsule_params = _derive_capsule_params(capsule_record)
    guide_types = _collect_guide_types(records)
    evidence_refs = _collect_evidence_refs(records)
    meta = {
        "guide_sources": [
            {
                "notebook_id": notebook_id,
                "guide_types": guide_types,
            }
        ],
        "narrative_seeds": {
            "story_beats": story_beats,
            "storyboard_cards": storyboard_cards,
        },
        "production_contract": {
            "shot_contracts": [],
            "prompt_contracts": [],
            "prompt_contract_version": "v1",
            "storyboard_refs": _unique_tags(collect_storyboard_refs(storyboard_cards)),
        },
        "evidence_refs": evidence_refs,
    }

    pattern_version = await get_latest_pattern_version(db)
    graph_data = build_template_graph(
        capsule_key,
        capsule_version,
        capsule_params,
        pattern_version=pattern_version,
        story_beats=story_beats,
        storyboard_cards=storyboard_cards,
        meta=meta,
    )

    template = Template(
        slug=slug,
        title=title,
        description=description,
        tags=resolved_tags,
        graph_data=graph_data,
        is_public=is_public,
        creator_id=creator_id,
        version=1,
    )
    db.add(template)
    await db.flush()
    db.add(
        TemplateVersion(
            template_id=template.id,
            version=template.version,
            graph_data=graph_data,
            notes=f"seeded from {notebook_id} at {datetime.utcnow().isoformat()}Z",
            creator_id=template.creator_id,
        )
    )
    await db.commit()
    await db.refresh(template)
    return template
