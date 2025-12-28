"""Run Guide Generation Pipeline.

This script connects:
1. DB VideoSegments → Source Pack
2. Source Pack → NotebookLM (Gemini) Guide
3. Guide → Derived Outputs (story/beat/storyboard)
4. Derived Outputs → Evidence Records (DB) or CSV
5. (Optional) CSV → Promote → DB
6. (Optional) Evidence → Template Seed

Usage:
    python scripts/run_guide_generation.py --source-id bong-2019-parasite --capsule-id auteur.bong-joon-ho
    python scripts/run_guide_generation.py --cluster-id CL_BONG_01 --temporal-phase HOOK
    python scripts/run_guide_generation.py --source-id bong-2019-parasite --notebook-id nlb-001 --emit-derived-csv data/derived_outputs.csv --promote-derived --seed-template --template-slug bong-template --template-title "Bong Template" --capsule-version 1.0.0
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import importlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import settings
from app.database import AsyncSessionLocal, init_db
from app.ingest_rules import DERIVED_EVIDENCE_REF_RE
from app.models import EvidenceRecord, NotebookLibrary, RawAsset, SourcePack, VideoSegment
from app.source_pack import build_source_pack
from app.template_seeding import seed_template_from_evidence
from app.notebooklm_client import (
    NotebookLMClientError,
    generate_story_beats,
    generate_storyboard_cards,
    run_notebooklm_analysis,
)
from app.narrative_utils import normalize_story_beats, normalize_storyboard_cards
from app.routers.ingest import EvidenceRecordRequest


async def fetch_segments(
    source_id: Optional[str] = None,
    cluster_id: Optional[str] = None,
    temporal_phase: Optional[str] = None,
    limit: int = 50,
) -> List[VideoSegment]:
    """Fetch segments from DB for source pack building."""
    async with AsyncSessionLocal() as db:
        query = select(VideoSegment)
        
        if source_id:
            query = query.where(VideoSegment.source_id == source_id)
        
        # Note: cluster_id and temporal_phase would normally be in a separate table
        # For now, filter by segment_id pattern if needed
        
        query = query.limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if cleaned.endswith("Z"):
        cleaned = cleaned.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def _normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    if not isinstance(value, str):
        value = str(value)
    cleaned = value.strip()
    return cleaned


def _serialize_list(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, list):
        cleaned = [_normalize_text(item) for item in value]
        cleaned = [item for item in cleaned if item]
        return ",".join(cleaned)
    return _normalize_text(value)


def _serialize_json(value: Any) -> str:
    if value in (None, ""):
        return ""
    return json.dumps(value, ensure_ascii=True)


def _suffix_prompt_version(base: str, suffix: str) -> str:
    cleaned_base = _normalize_text(base) or "notebooklm-gemini-v1"
    cleaned_suffix = _normalize_text(suffix)
    combined = f"{cleaned_base}-{cleaned_suffix}" if cleaned_suffix else cleaned_base
    return combined[:64]


async def upsert_source_pack(source_pack: Dict[str, Any]) -> None:
    pack_id = str(source_pack.get("pack_id") or "").strip()
    if not pack_id:
        raise ValueError("source_pack.pack_id is required")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(SourcePack).where(SourcePack.pack_id == pack_id))
        record = result.scalars().first()
        if not record:
            record = SourcePack(
                pack_id=pack_id,
                cluster_id=source_pack.get("cluster_id") or "unknown",
                temporal_phase=source_pack.get("temporal_phase") or "UNKNOWN",
                bundle_hash=source_pack.get("bundle_hash") or "",
            )
            db.add(record)

        record.source_snapshot_at = _parse_datetime(source_pack.get("source_snapshot_at"))
        record.source_sync_at = _parse_datetime(source_pack.get("source_sync_at"))
        record.source_count = int(source_pack.get("source_count") or 0)
        record.source_manifest = source_pack.get("source_manifest") or []
        record.source_ids = source_pack.get("source_ids") or []
        record.segment_refs = source_pack.get("segment_refs") or []
        record.metrics_snapshot = source_pack.get("metrics_snapshot") or {}
        record.bundle_hash = source_pack.get("bundle_hash") or record.bundle_hash
        record.notes = source_pack.get("notes")
        await db.commit()


def _resolve_source_id(
    source_id: Optional[str],
    source_pack: Dict[str, Any],
) -> Optional[str]:
    if isinstance(source_id, str) and source_id.strip():
        return source_id.strip()
    source_ids = source_pack.get("source_ids")
    if isinstance(source_ids, list):
        for item in source_ids:
            if isinstance(item, str) and item.strip():
                return item.strip()
    return None


async def _resolve_notebook_from_source_id(
    db: AsyncSession,
    source_id: Optional[str],
    cluster_id: Optional[str],
) -> tuple[Optional[str], Optional[str]]:
    if not source_id:
        return None, None
    try:
        result = await db.execute(
            select(NotebookLibrary).where(NotebookLibrary.source_ids.contains([source_id]))
        )
        candidates = list(result.scalars().all())
    except Exception:
        candidates = []
    if not candidates and cluster_id:
        result = await db.execute(
            select(NotebookLibrary).where(NotebookLibrary.cluster_id == cluster_id)
        )
        candidates = [
            item
            for item in result.scalars().all()
            if isinstance(item.source_ids, list) and source_id in item.source_ids
        ]
    if cluster_id:
        cluster_matches = [item for item in candidates if item.cluster_id == cluster_id]
        if cluster_matches:
            candidates = cluster_matches
    if len(candidates) != 1:
        return None, None
    notebook = candidates[0]
    return notebook.notebook_id, notebook.notebook_ref


def _collect_evidence_refs(claims: List[Dict[str, Any]]) -> List[str]:
    refs: List[str] = []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_refs = claim.get("evidence_refs")
        if not isinstance(claim_refs, list):
            continue
        for ref in claim_refs:
            if not isinstance(ref, str):
                continue
            cleaned = ref.strip()
            if cleaned and DERIVED_EVIDENCE_REF_RE.match(cleaned):
                refs.append(cleaned)
    return sorted(set(refs))


def _build_summary_text(guide: Dict[str, Any], summary: Dict[str, Any]) -> str:
    logic_summary = guide.get("logic_summary") if isinstance(guide, dict) else None
    persona_summary = guide.get("persona_summary") if isinstance(guide, dict) else None
    parts = [text for text in (logic_summary, persona_summary) if isinstance(text, str) and text.strip()]
    if parts:
        return " / ".join(parts)
    fallback = summary.get("summary") if isinstance(summary, dict) else None
    if isinstance(fallback, str) and fallback.strip():
        return fallback.strip()
    return "NotebookLM guide"


def _coerce_text(value: Any) -> Optional[str]:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    if isinstance(value, (int, float)):
        return str(value)
    return None


def _format_list(value: Any) -> Optional[str]:
    if not isinstance(value, list):
        return _coerce_text(value)
    cleaned = [_normalize_text(item) for item in value]
    cleaned = [item for item in cleaned if item]
    if not cleaned:
        return None
    return ", ".join(cleaned)


def _compact_json(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    except TypeError:
        return None


def _build_persona_profile(guide: Dict[str, Any], summary: Dict[str, Any]) -> Optional[str]:
    if isinstance(summary, dict):
        direct = _coerce_text(summary.get("persona_profile"))
        if direct:
            return direct
    if isinstance(guide, dict):
        persona_summary = _coerce_text(guide.get("persona_summary"))
        if persona_summary:
            return persona_summary
    persona_vector = summary.get("persona_vector") if isinstance(summary, dict) else None
    if not isinstance(persona_vector, dict):
        return None
    tone = _format_list(persona_vector.get("tone"))
    frame = _format_list(persona_vector.get("interpretation_frame"))
    rhythm = persona_vector.get("sentence_rhythm")
    rhythm_parts: List[str] = []
    if isinstance(rhythm, dict):
        avg_len = rhythm.get("avg_len")
        pause_bias = rhythm.get("pause_bias")
        if avg_len is not None:
            rhythm_parts.append(f"avg_len={avg_len}")
        if pause_bias is not None:
            rhythm_parts.append(f"pause_bias={pause_bias}")
    rhythm_text = ", ".join(rhythm_parts) if rhythm_parts else None
    parts = [part for part in (tone, frame, rhythm_text) if part]
    if not parts:
        return None
    return "; ".join(parts)


def _build_synapse_logic(guide: Dict[str, Any], summary: Dict[str, Any]) -> Optional[str]:
    if isinstance(summary, dict):
        direct = _coerce_text(summary.get("synapse_logic"))
        if direct:
            return direct
    if isinstance(guide, dict):
        logic_summary = _coerce_text(guide.get("logic_summary"))
        if logic_summary:
            return logic_summary
    logic_vector = summary.get("logic_vector") if isinstance(summary, dict) else None
    if not isinstance(logic_vector, dict):
        return None
    parts: List[str] = []
    for key in ("cadence", "composition", "camera_motion", "motif_rules"):
        value = logic_vector.get(key)
        payload = _compact_json(value) if value is not None else None
        if payload:
            parts.append(f"{key}={payload}")
    if not parts:
        return None
    return "; ".join(parts)


def _build_variation_guide_text(guide: Dict[str, Any]) -> Optional[str]:
    rules = guide.get("variation_rules") if isinstance(guide, dict) else None
    if isinstance(rules, list):
        cleaned = [str(item).strip() for item in rules if isinstance(item, (str, int, float))]
        cleaned = [item for item in cleaned if item]
        if cleaned:
            return "\n".join(cleaned)
    return None


def _extract_template_recommendations(
    guide: Dict[str, Any],
    summary: Dict[str, Any],
) -> List[str]:
    candidates = None
    if isinstance(guide, dict):
        candidates = guide.get("template_recommendations")
    if candidates is None and isinstance(summary, dict):
        candidates = summary.get("template_recommendations")
    if not isinstance(candidates, list):
        return []
    cleaned = [str(item).strip() for item in candidates if isinstance(item, (str, int, float))]
    return [item for item in cleaned if item]


def _build_user_fit_notes(guide: Dict[str, Any]) -> Optional[str]:
    notes = guide.get("template_fit_notes") if isinstance(guide, dict) else None
    if isinstance(notes, list):
        cleaned = [str(item).strip() for item in notes if isinstance(item, (str, int, float))]
        cleaned = [item for item in cleaned if item]
        if cleaned:
            return "; ".join(cleaned)
    if isinstance(notes, str) and notes.strip():
        return notes.strip()
    return None


def _pick_text_field(summary: Dict[str, Any], guide: Dict[str, Any], key: str) -> Optional[str]:
    for payload in (summary, guide):
        if not isinstance(payload, dict):
            continue
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _pick_list_field(summary: Dict[str, Any], guide: Dict[str, Any], key: str) -> list:
    for payload in (summary, guide):
        if not isinstance(payload, dict):
            continue
        value = payload.get(key)
        if isinstance(value, list) and value:
            return value
    return []


def _pick_list_or_dict_field(summary: Dict[str, Any], guide: Dict[str, Any], key: str) -> list:
    for payload in (summary, guide):
        if not isinstance(payload, dict):
            continue
        value = payload.get(key)
        if isinstance(value, list) and value:
            return value
        if isinstance(value, dict) and value:
            return [value]
    return []


def _pick_dict_field(summary: Dict[str, Any], guide: Dict[str, Any], key: str) -> dict:
    for payload in (summary, guide):
        if not isinstance(payload, dict):
            continue
        value = payload.get(key)
        if isinstance(value, dict) and value:
            return value
    return {}


def _clean_string_list(value: Any) -> list:
    if not isinstance(value, list):
        return []
    cleaned = [_normalize_text(item) for item in value]
    return [item for item in cleaned if item]


def _build_derived_output(
    summary: Dict[str, Any],
    guide: Dict[str, Any],
    claims: List[Dict[str, Any]],
    source_pack: Dict[str, Any],
    *,
    source_id: Optional[str],
    output_language: str,
    guide_type: str,
    prompt_version: str,
    output_type: str,
    summary_override: Optional[str] = None,
    persona_profile: Optional[str] = None,
    synapse_logic: Optional[str] = None,
    story_beats: Optional[List[Dict[str, Any]]] = None,
    storyboard_cards: Optional[List[Dict[str, Any]]] = None,
    notebook_id: Optional[str] = None,
    persona_source: Optional[str] = None,  # Script Persona Policy: script | user | auteur | blended
) -> Dict[str, Any]:
    model_version = summary.get("model_version") or settings.GEMINI_MODEL
    generated_at = summary.get("generated_at") or datetime.now(timezone.utc).isoformat()
    evidence_refs = _collect_evidence_refs(claims)
    resolved_summary = _normalize_text(summary_override) or _build_summary_text(guide, summary)
    origin_notebook_id = _pick_text_field(summary, guide, "origin_notebook_id")
    filter_notebook_id = _pick_text_field(summary, guide, "filter_notebook_id")
    style_logic = _pick_text_field(summary, guide, "style_logic")
    mise_en_scene = _pick_text_field(summary, guide, "mise_en_scene")
    director_intent = _pick_text_field(summary, guide, "director_intent")
    labels = _clean_string_list(_pick_list_field(summary, guide, "labels"))
    signature_motifs = _clean_string_list(_pick_list_field(summary, guide, "signature_motifs"))
    camera_motion = _pick_dict_field(summary, guide, "camera_motion")
    color_palette = _pick_dict_field(summary, guide, "color_palette")
    pacing = _pick_dict_field(summary, guide, "pacing")
    sound_design = _pick_text_field(summary, guide, "sound_design")
    editing_rhythm = _pick_text_field(summary, guide, "editing_rhythm")
    studio_output_id = _pick_text_field(summary, guide, "studio_output_id")
    opal_workflow_id = _pick_text_field(summary, guide, "opal_workflow_id")
    raw_key_patterns = _pick_list_or_dict_field(summary, guide, "key_patterns")
    key_patterns = [
        item.strip() if isinstance(item, str) else item
        for item in raw_key_patterns
        if isinstance(item, (dict, str)) and (not isinstance(item, str) or item.strip())
    ]
    return {
        "derived_id": str(uuid.uuid4()),
        "source_id": source_id,
        "summary": resolved_summary,
        "guide_type": guide_type,
        "persona_profile": persona_profile,
        "synapse_logic": synapse_logic,
        "origin_notebook_id": origin_notebook_id,
        "filter_notebook_id": filter_notebook_id,
        "variation_guide": _build_variation_guide_text(guide) if guide_type == "variation" else None,
        "user_fit_notes": _build_user_fit_notes(guide) if guide_type == "variation" else None,
        "template_recommendations": _extract_template_recommendations(guide, summary),
        "cluster_id": source_pack.get("cluster_id"),
        "cluster_label": summary.get("cluster_label") if isinstance(summary, dict) else None,
        "cluster_confidence": summary.get("cluster_confidence") if isinstance(summary, dict) else None,
        "style_logic": style_logic,
        "mise_en_scene": mise_en_scene,
        "director_intent": director_intent,
        "labels": labels,
        "signature_motifs": signature_motifs,
        "camera_motion": camera_motion,
        "color_palette": color_palette,
        "pacing": pacing,
        "sound_design": sound_design,
        "editing_rhythm": editing_rhythm,
        "output_type": output_type,
        "output_language": output_language,
        "prompt_version": prompt_version,
        "model_version": model_version,
        "source_pack_id": source_pack.get("pack_id"),
        "generated_at": generated_at,
        "evidence_refs": evidence_refs,
        "adapter": "notebooklm",
        "confidence": 0.85,
        "story_beats": story_beats or [],
        "storyboard_cards": storyboard_cards or [],
        "key_patterns": key_patterns,
        "studio_output_id": studio_output_id,
        "opal_workflow_id": opal_workflow_id,
        "notebook_id": notebook_id,
        "claims": claims,
        "persona_source": persona_source,  # Script Persona Policy tracking
    }


def _write_derived_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _write_derived_csv(path: Path, payload: Any) -> None:
    columns = [
        "derived_id",
        "source_id",
        "notebook_id",
        "source_pack_id",
        "summary",
        "guide_type",
        "persona_source",  # Script Persona Policy tracking
        "persona_profile",
        "synapse_logic",
        "origin_notebook_id",
        "filter_notebook_id",
        "homage_guide",
        "variation_guide",
        "template_recommendations",
        "user_fit_notes",
        "style_logic",
        "mise_en_scene",
        "director_intent",
        "labels",
        "signature_motifs",
        "camera_motion",
        "color_palette",
        "pacing",
        "sound_design",
        "editing_rhythm",
        "story_beats",
        "storyboard_cards",
        "key_patterns",
        "cluster_id",
        "cluster_label",
        "cluster_confidence",
        "output_type",
        "output_language",
        "studio_output_id",
        "adapter",
        "opal_workflow_id",
        "confidence",
        "prompt_version",
        "model_version",
        "notebook_ref",
        "evidence_refs",
        "generated_at",
    ]
    rows = payload if isinstance(payload, list) else [payload]
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        if is_new:
            writer.writeheader()
        for row_payload in rows:
            row = {
                "derived_id": row_payload.get("derived_id") or "",
                "source_id": row_payload.get("source_id") or "",
                "notebook_id": row_payload.get("notebook_id") or "",
                "source_pack_id": row_payload.get("source_pack_id") or "",
                "summary": row_payload.get("summary") or "",
                "guide_type": row_payload.get("guide_type") or "",
                "persona_source": row_payload.get("persona_source") or "",  # Script Persona Policy
                "persona_profile": row_payload.get("persona_profile") or "",
                "synapse_logic": row_payload.get("synapse_logic") or "",
                "origin_notebook_id": row_payload.get("origin_notebook_id") or "",
                "filter_notebook_id": row_payload.get("filter_notebook_id") or "",
                "homage_guide": row_payload.get("homage_guide") or "",
                "variation_guide": row_payload.get("variation_guide") or "",
                "template_recommendations": _serialize_list(row_payload.get("template_recommendations")),
                "user_fit_notes": row_payload.get("user_fit_notes") or "",
                "style_logic": row_payload.get("style_logic") or "",
                "mise_en_scene": row_payload.get("mise_en_scene") or "",
                "director_intent": row_payload.get("director_intent") or "",
                "labels": _serialize_list(row_payload.get("labels")),
                "signature_motifs": _serialize_list(row_payload.get("signature_motifs")),
                "camera_motion": _serialize_json(row_payload.get("camera_motion")),
                "color_palette": _serialize_json(row_payload.get("color_palette")),
                "pacing": _serialize_json(row_payload.get("pacing")),
                "sound_design": row_payload.get("sound_design") or "",
                "editing_rhythm": row_payload.get("editing_rhythm") or "",
                "story_beats": _serialize_json(row_payload.get("story_beats")),
                "storyboard_cards": _serialize_json(row_payload.get("storyboard_cards")),
                "key_patterns": _serialize_json(row_payload.get("key_patterns")),
                "cluster_id": row_payload.get("cluster_id") or "",
                "cluster_label": row_payload.get("cluster_label") or "",
                "cluster_confidence": row_payload.get("cluster_confidence")
                if row_payload.get("cluster_confidence") is not None
                else "",
                "output_type": row_payload.get("output_type") or "",
                "output_language": row_payload.get("output_language") or "",
                "studio_output_id": row_payload.get("studio_output_id") or "",
                "adapter": row_payload.get("adapter") or "",
                "opal_workflow_id": row_payload.get("opal_workflow_id") or "",
                "confidence": row_payload.get("confidence")
                if row_payload.get("confidence") is not None
                else "",
                "prompt_version": row_payload.get("prompt_version") or "",
                "model_version": row_payload.get("model_version") or "",
                "notebook_ref": row_payload.get("notebook_ref") or "",
                "evidence_refs": _serialize_list(row_payload.get("evidence_refs")),
                "generated_at": row_payload.get("generated_at") or "",
            }
            writer.writerow(row)


def _file_url(path: Path) -> str:
    return f"file://{path.resolve()}"


async def _promote_from_csv(csv_path: Path) -> None:
    scripts_dir = ROOT_DIR / "scripts"
    scripts_dir_str = str(scripts_dir)
    if scripts_dir_str not in sys.path:
        sys.path.insert(0, scripts_dir_str)
    os.environ["SHEETS_MODE"] = "csv"
    os.environ["CREBIT_DERIVED_INSIGHTS_CSV_URL"] = _file_url(csv_path)
    if "promote_from_sheets" in sys.modules:
        importlib.reload(sys.modules["promote_from_sheets"])
    else:
        import promote_from_sheets  # noqa: F401
    promote_module = importlib.import_module("promote_from_sheets")
    await promote_module.main()


async def _seed_template(
    *,
    slug: str,
    title: str,
    description: str,
    capsule_key: str,
    capsule_version: str,
    notebook_id: str,
    tags: Optional[str],
    is_public: bool,
) -> None:
    parsed_tags = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    async with AsyncSessionLocal() as session:
        await seed_template_from_evidence(
            session,
            slug=slug,
            title=title,
            description=description,
            capsule_key=capsule_key,
            capsule_version=capsule_version,
            notebook_id=notebook_id,
            tags=parsed_tags,
            is_public=is_public,
        )


async def save_evidence_records(
    derived_outputs: List[Dict[str, Any]],
) -> List[str]:
    """Save derived outputs as evidence records (local QA)."""
    saved_ids: List[str] = []
    if not derived_outputs:
        return saved_ids
    async with AsyncSessionLocal() as db:
        for payload in derived_outputs:
            source_id = payload.get("source_id")
            if not isinstance(source_id, str) or not source_id.strip():
                raise ValueError("source_id is required for evidence record")
            source_id = source_id.strip()
            pack_id = payload.get("source_pack_id")
            if not isinstance(pack_id, str) or not pack_id.strip():
                raise ValueError("source_pack_id is required for evidence record")
            pack_id = pack_id.strip()

            pack_result = await db.execute(select(SourcePack).where(SourcePack.pack_id == pack_id))
            if not pack_result.scalars().first():
                raise ValueError(f"source_pack_id not found: {pack_id}")

            parsed_at = _parse_datetime(payload.get("generated_at"))
            if parsed_at:
                # Strip tzinfo for naive datetime compatibility with PostgreSQL
                generated_at = parsed_at.replace(tzinfo=None) if parsed_at.tzinfo else parsed_at
            else:
                generated_at = datetime.utcnow()

            request = EvidenceRecordRequest(
                source_id=source_id,
                summary=payload.get("summary") or "",
                output_type=payload.get("output_type") or "report",
                output_language=payload.get("output_language") or "und",
                prompt_version=payload.get("prompt_version") or "notebooklm-gemini-v1",
                model_version=payload.get("model_version") or settings.GEMINI_MODEL,
                source_pack_id=pack_id,
                guide_type=payload.get("guide_type"),
                homage_guide=payload.get("homage_guide"),
                variation_guide=payload.get("variation_guide"),
                template_recommendations=payload.get("template_recommendations") or [],
                user_fit_notes=payload.get("user_fit_notes"),
                persona_profile=payload.get("persona_profile"),
                synapse_logic=payload.get("synapse_logic"),
                origin_notebook_id=payload.get("origin_notebook_id"),
                filter_notebook_id=payload.get("filter_notebook_id"),
                cluster_id=payload.get("cluster_id"),
                cluster_label=payload.get("cluster_label"),
                cluster_confidence=payload.get("cluster_confidence"),
                style_logic=payload.get("style_logic"),
                mise_en_scene=payload.get("mise_en_scene"),
                director_intent=payload.get("director_intent"),
                labels=payload.get("labels") or [],
                signature_motifs=payload.get("signature_motifs") or [],
                camera_motion=payload.get("camera_motion") or {},
                color_palette=payload.get("color_palette") or {},
                pacing=payload.get("pacing") or {},
                sound_design=payload.get("sound_design"),
                editing_rhythm=payload.get("editing_rhythm"),
                story_beats=payload.get("story_beats") or [],
                storyboard_cards=payload.get("storyboard_cards") or [],
                key_patterns=payload.get("key_patterns") or [],
                studio_output_id=payload.get("studio_output_id"),
                notebook_id=payload.get("notebook_id"),
                notebook_ref=payload.get("notebook_ref"),
                evidence_refs=payload.get("evidence_refs") or [],
                adapter=payload.get("adapter"),
                opal_workflow_id=payload.get("opal_workflow_id"),
                confidence=payload.get("confidence"),
                persona_source=payload.get("persona_source"),  # Script Persona Policy
                generated_at=generated_at,
            )

            result = await db.execute(
                select(EvidenceRecord).where(
                    EvidenceRecord.source_id == request.source_id,
                    EvidenceRecord.prompt_version == request.prompt_version,
                    EvidenceRecord.model_version == request.model_version,
                    EvidenceRecord.output_type == request.output_type,
                    EvidenceRecord.output_language == request.output_language,
                )
            )
            record = result.scalars().first()
            if not record:
                record = EvidenceRecord(
                    source_id=request.source_id,
                    summary=request.summary,
                    output_type=request.output_type,
                    output_language=request.output_language,
                    prompt_version=request.prompt_version,
                    model_version=request.model_version,
                )
                db.add(record)

            record.summary = request.summary
            record.guide_type = request.guide_type
            record.homage_guide = request.homage_guide
            record.variation_guide = request.variation_guide
            if request.template_recommendations:
                record.template_recommendations = request.template_recommendations
            record.user_fit_notes = request.user_fit_notes
            record.persona_profile = request.persona_profile or record.persona_profile
            record.synapse_logic = request.synapse_logic or record.synapse_logic
            record.origin_notebook_id = request.origin_notebook_id or record.origin_notebook_id
            record.filter_notebook_id = request.filter_notebook_id or record.filter_notebook_id
            record.cluster_id = request.cluster_id
            if request.cluster_confidence is not None:
                record.cluster_confidence = request.cluster_confidence
            if request.cluster_label:
                record.cluster_label = request.cluster_label
            record.style_logic = request.style_logic or record.style_logic
            record.mise_en_scene = request.mise_en_scene or record.mise_en_scene
            record.director_intent = request.director_intent or record.director_intent
            if request.labels:
                record.labels = request.labels
            if request.signature_motifs:
                record.signature_motifs = request.signature_motifs
            if request.camera_motion:
                record.camera_motion = request.camera_motion
            if request.color_palette:
                record.color_palette = request.color_palette
            if request.pacing:
                record.pacing = request.pacing
            record.sound_design = request.sound_design or record.sound_design
            record.editing_rhythm = request.editing_rhythm or record.editing_rhythm
            record.source_pack_id = request.source_pack_id
            record.story_beats = request.story_beats
            record.storyboard_cards = request.storyboard_cards
            record.key_patterns = request.key_patterns
            record.studio_output_id = request.studio_output_id or record.studio_output_id
            record.notebook_id = request.notebook_id
            record.notebook_ref = request.notebook_ref
            record.evidence_refs = request.evidence_refs
            record.adapter = request.adapter
            record.opal_workflow_id = request.opal_workflow_id or record.opal_workflow_id
            record.confidence = request.confidence
            record.persona_source = request.persona_source or record.persona_source  # Script Persona Policy
            record.generated_at = request.generated_at

            await db.commit()
            await db.refresh(record)
            saved_ids.append(str(record.id))

    return saved_ids


async def run_pipeline(
    source_id: Optional[str] = None,
    cluster_id: Optional[str] = None,
    temporal_phase: str = "HOOK",
    capsule_id: str = "auteur.bong-joon-ho",
    notebook_id: Optional[str] = None,
    dry_run: bool = False,
    skip_evidence_save: bool = False,
    emit_derived_json: Optional[Path] = None,
    emit_derived_csv: Optional[Path] = None,
    promote_derived: bool = False,
    seed_template: bool = False,
    template_slug: Optional[str] = None,
    template_title: Optional[str] = None,
    template_description: str = "Seeded template",
    template_tags: Optional[str] = None,
    template_public: bool = False,
    capsule_version: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the full guide generation pipeline."""
    print(f"\n{'='*60}")
    print(f"🚀 Guide Generation Pipeline")
    print(f"{'='*60}")
    print(f"Source ID: {source_id or '(all)'}")
    print(f"Cluster ID: {cluster_id or '(auto)'}")
    print(f"Temporal Phase: {temporal_phase}")
    print(f"Capsule ID: {capsule_id}")
    if notebook_id:
        print(f"Notebook ID: {notebook_id}")
    print(f"Dry Run: {dry_run}")
    print(f"{'='*60}\n")
    
    await init_db()
    if promote_derived:
        skip_evidence_save = True
    
    # Step 1: Fetch segments
    print("📊 Step 1: Fetching segments from DB...")
    segments = await fetch_segments(source_id=source_id)
    print(f"   Found {len(segments)} segments")
    
    if not segments:
        print("   ❌ No segments found!")
        return {"status": "error", "message": "No segments found"}
    
    # Step 2: Build Source Pack
    print("\n📦 Step 2: Building Source Pack...")
    source_pack = build_source_pack(
        segments,
        cluster_id=cluster_id or f"CL_{capsule_id.split('.')[-1].upper()}",
        temporal_phase=temporal_phase,
    )
    print(f"   Pack ID: {source_pack.get('pack_id')}")
    print(f"   Segment count: {len(source_pack.get('segment_refs', []))}")
    print(f"   Bundle hash: {source_pack.get('bundle_hash', '')[:16]}...")
    if not dry_run:
        await upsert_source_pack(source_pack)
    
    # Step 3: Run NotebookLM Analysis
    print("\n🧠 Step 3: Running NotebookLM Analysis (Gemini)...")
    try:
        summary, evidence_refs = run_notebooklm_analysis(source_pack, capsule_id)
        print(f"   ✅ Analysis complete")
        print(f"   Logic Vector: {bool(summary.get('logic_vector'))}")
        print(f"   Persona Vector: {bool(summary.get('persona_vector'))}")
        print(f"   Guide: {bool(summary.get('guide'))}")
        print(f"   Claims: {len(summary.get('claims', []))}")
        print(f"   Token Usage: {summary.get('token_usage', {}).get('total', 0)}")
    except NotebookLMClientError as e:
        print(f"   ❌ Analysis failed: {e}")
        return {"status": "error", "message": str(e)}

    resolved_source_id = _resolve_source_id(source_id, source_pack)
    resolved_output_language = "und"
    if isinstance(summary, dict):
        summary_lang = summary.get("output_language")
        if isinstance(summary_lang, str) and summary_lang.strip():
            resolved_output_language = summary_lang.strip()
    if not resolved_source_id and isinstance(summary, dict):
        summary_source = summary.get("source_id")
        if isinstance(summary_source, str) and summary_source.strip():
            resolved_source_id = summary_source.strip()
    if not resolved_source_id:
        raise ValueError("source_id is required to build derived outputs")
    resolved_notebook_id = notebook_id
    if not resolved_notebook_id and isinstance(summary, dict):
        summary_notebook = summary.get("notebook_id")
        if isinstance(summary_notebook, str) and summary_notebook.strip():
            resolved_notebook_id = summary_notebook.strip()
    resolved_notebook_ref = None
    if isinstance(summary, dict):
        summary_ref = summary.get("notebook_ref")
        if isinstance(summary_ref, str) and summary_ref.strip():
            resolved_notebook_ref = summary_ref.strip()
    async with AsyncSessionLocal() as db:
        raw_result = await db.execute(select(RawAsset).where(RawAsset.source_id == resolved_source_id))
        raw_asset = raw_result.scalars().first()
        if raw_asset and isinstance(raw_asset.language, str) and raw_asset.language.strip():
            resolved_output_language = raw_asset.language.strip()
        if not resolved_notebook_id:
            notebook_id_from_db, notebook_ref_from_db = await _resolve_notebook_from_source_id(
                db,
                resolved_source_id,
                source_pack.get("cluster_id"),
            )
            if notebook_id_from_db:
                resolved_notebook_id = notebook_id_from_db
            if not resolved_notebook_ref and notebook_ref_from_db:
                resolved_notebook_ref = notebook_ref_from_db

    claims = summary.get("claims", []) if isinstance(summary, dict) else []
    guide = summary.get("guide", {}) if isinstance(summary, dict) else {}
    persona_profile = _build_persona_profile(guide, summary if isinstance(summary, dict) else {})
    synapse_logic = _build_synapse_logic(guide, summary if isinstance(summary, dict) else {})
    raw_story_beats = None
    if isinstance(summary, dict):
        raw_story_beats = summary.get("story_beats")
    if raw_story_beats is None and isinstance(guide, dict):
        raw_story_beats = guide.get("story_beats")
    if isinstance(raw_story_beats, list) and raw_story_beats:
        story_beats = normalize_story_beats(raw_story_beats)
    else:
        story_beats = generate_story_beats(source_pack, capsule_id, guide, claims)

    raw_storyboard_cards = None
    if isinstance(summary, dict):
        raw_storyboard_cards = summary.get("storyboard_cards")
    if raw_storyboard_cards is None and isinstance(guide, dict):
        raw_storyboard_cards = guide.get("storyboard_cards")
    if isinstance(raw_storyboard_cards, list) and raw_storyboard_cards:
        storyboard_cards = normalize_storyboard_cards(raw_storyboard_cards)
    else:
        storyboard_cards = generate_storyboard_cards(
            source_pack,
            capsule_id,
            guide,
            claims,
            story_beats,
        )
    base_prompt_version = (
        summary.get("prompt_version")
        if isinstance(summary, dict)
        else None
    ) or "notebooklm-gemini-v1"
    output_type = (
        summary.get("output_type")
        if isinstance(summary, dict)
        else None
    ) or "report"
    persona_prompt_version = _suffix_prompt_version(base_prompt_version, "persona")
    synapse_prompt_version = _suffix_prompt_version(base_prompt_version, "synapse")

    derived_outputs = [
        _build_derived_output(
            summary,
            guide,
            claims,
            source_pack,
            source_id=resolved_source_id,
            output_language=resolved_output_language,
            guide_type="variation",
            prompt_version=base_prompt_version,
            output_type=output_type,
            persona_profile=persona_profile,
            synapse_logic=synapse_logic,
            notebook_id=resolved_notebook_id,
            persona_source="auteur",  # Script Persona Policy: default to auteur for capsule-based generation
        ),
        _build_derived_output(
            summary,
            guide,
            claims,
            source_pack,
            source_id=resolved_source_id,
            output_language=resolved_output_language,
            guide_type="persona",
            prompt_version=persona_prompt_version,
            output_type=output_type,
            summary_override=persona_profile,
            persona_profile=persona_profile,
            notebook_id=resolved_notebook_id,
            persona_source="auteur",
        ),
        _build_derived_output(
            summary,
            guide,
            claims,
            source_pack,
            source_id=resolved_source_id,
            output_language=resolved_output_language,
            guide_type="synapse",
            prompt_version=synapse_prompt_version,
            output_type=output_type,
            summary_override=synapse_logic,
            synapse_logic=synapse_logic,
            notebook_id=resolved_notebook_id,
            persona_source="auteur",
        ),
        _build_derived_output(
            summary,
            guide,
            claims,
            source_pack,
            source_id=resolved_source_id,
            output_language=resolved_output_language,
            guide_type="story",
            prompt_version=_suffix_prompt_version(base_prompt_version, "story"),
            output_type=output_type,
            story_beats=story_beats,
            persona_profile=persona_profile,
            synapse_logic=synapse_logic,
            notebook_id=resolved_notebook_id,
            persona_source="auteur",
        ),
        _build_derived_output(
            summary,
            guide,
            claims,
            source_pack,
            source_id=resolved_source_id,
            output_language=resolved_output_language,
            guide_type="beat_sheet",
            prompt_version=_suffix_prompt_version(base_prompt_version, "beat"),
            output_type=output_type,
            story_beats=story_beats,
            persona_profile=persona_profile,
            synapse_logic=synapse_logic,
            notebook_id=resolved_notebook_id,
            persona_source="auteur",
        ),
        _build_derived_output(
            summary,
            guide,
            claims,
            source_pack,
            source_id=resolved_source_id,
            output_language=resolved_output_language,
            guide_type="storyboard",
            prompt_version=_suffix_prompt_version(base_prompt_version, "storyboard"),
            output_type=output_type,
            storyboard_cards=storyboard_cards,
            persona_profile=persona_profile,
            synapse_logic=synapse_logic,
            notebook_id=resolved_notebook_id,
            persona_source="auteur",
        ),
    ]
    if resolved_notebook_ref:
        for payload in derived_outputs:
            payload["notebook_ref"] = resolved_notebook_ref
    if emit_derived_json:
        _write_derived_json(emit_derived_json, derived_outputs)
        print(f"   Derived JSON emitted: {emit_derived_json}")
    if emit_derived_csv:
        _write_derived_csv(emit_derived_csv, derived_outputs)
        print(f"   Derived CSV appended: {emit_derived_csv}")
    
    # Step 4: Save Evidence Records
    if not dry_run and not skip_evidence_save:
        print("\n💾 Step 4: Saving Evidence Records to DB...")
        saved_ids = await save_evidence_records(derived_outputs)
        print(f"   Saved {len(saved_ids)} evidence records")
    elif dry_run:
        print("\n⏭️  Step 4: Skipped (dry run)")
        saved_ids = []
    else:
        print("\n⏭️  Step 4: Skipped (skip_evidence_save)")
        saved_ids = []

    if promote_derived:
        if not emit_derived_csv:
            raise ValueError("--promote-derived requires --emit-derived-csv")
        print("\n📈 Step 5: Promoting derived outputs...")
        await _promote_from_csv(emit_derived_csv)

    if seed_template:
        if not resolved_notebook_id:
            raise ValueError("--seed-template requires --notebook-id")
        if not template_slug or not template_title:
            raise ValueError("--seed-template requires --template-slug and --template-title")
        if not capsule_version:
            raise ValueError("--seed-template requires --capsule-version")
        print("\n🧩 Step 6: Seeding template from evidence...")
        await _seed_template(
            slug=template_slug,
            title=template_title,
            description=template_description,
            capsule_key=capsule_id,
            capsule_version=capsule_version,
            notebook_id=resolved_notebook_id,
            tags=template_tags,
            is_public=template_public,
        )
    
    # Summary
    print(f"\n{'='*60}")
    print("✅ Pipeline Complete!")
    print(f"{'='*60}")
    
    result = {
        "status": "success",
        "source_pack_id": source_pack.get("pack_id"),
        "segment_count": len(segments),
        "claims_generated": len(claims),
        "derived_outputs_generated": len(derived_outputs),
        "evidence_records_saved": len(saved_ids),
        "promotion_run": promote_derived,
        "template_seeded": seed_template,
        "token_usage": summary.get("token_usage", {}),
        "summary": summary,
    }
    
    print(json.dumps({k: v for k, v in result.items() if k != "summary"}, indent=2, ensure_ascii=False))
    
    return result


async def main():
    parser = argparse.ArgumentParser(description="Run Guide Generation Pipeline")
    parser.add_argument("--source-id", "-s", help="Source ID to filter segments")
    parser.add_argument("--cluster-id", "-c", help="Cluster ID for source pack")
    parser.add_argument("--temporal-phase", "-p", default="HOOK", help="Temporal phase (HOOK, BUILD, PAYOFF)")
    parser.add_argument("--capsule-id", "-i", default="auteur.bong-joon-ho", help="Capsule ID for auteur style")
    parser.add_argument("--notebook-id", help="Notebook ID for derived outputs")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Don't save to DB")
    parser.add_argument("--skip-evidence-save", action="store_true", help="Skip evidence DB writes")
    parser.add_argument("--emit-derived-json", type=Path, help="Write derived output JSON to file.")
    parser.add_argument("--emit-derived-csv", type=Path, help="Append derived output to CSV file.")
    parser.add_argument("--promote-derived", action="store_true", help="Promote derived CSV to DB.")
    parser.add_argument("--seed-template", action="store_true", help="Seed a template after promotion.")
    parser.add_argument("--template-slug", help="Template slug for seeding.")
    parser.add_argument("--template-title", help="Template title for seeding.")
    parser.add_argument("--template-description", default="Seeded template", help="Template description.")
    parser.add_argument("--template-tags", help="Comma-separated template tags.")
    parser.add_argument("--template-public", action="store_true", help="Publish the template.")
    parser.add_argument("--capsule-version", help="Capsule version for seeding.")
    
    args = parser.parse_args()
    
    await run_pipeline(
        source_id=args.source_id,
        cluster_id=args.cluster_id,
        temporal_phase=args.temporal_phase,
        capsule_id=args.capsule_id,
        notebook_id=args.notebook_id,
        dry_run=args.dry_run,
        skip_evidence_save=args.skip_evidence_save,
        emit_derived_json=args.emit_derived_json,
        emit_derived_csv=args.emit_derived_csv,
        promote_derived=args.promote_derived,
        seed_template=args.seed_template,
        template_slug=args.template_slug,
        template_title=args.template_title,
        template_description=args.template_description,
        template_tags=args.template_tags,
        template_public=args.template_public,
        capsule_version=args.capsule_version,
    )


if __name__ == "__main__":
    asyncio.run(main())
