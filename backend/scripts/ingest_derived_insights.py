import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import AsyncSessionLocal, init_db
from app.ingest_rules import ensure_label, is_mega_notebook_notes
from app.models import EvidenceRecord, NotebookLibrary, RawAsset
from app.routers.ingest import EvidenceRecordRequest


def _load_payload(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _extract_rows(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("derived", "derived_insights", "items", "data", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        return [payload]
    raise ValueError("Input JSON must be an object or list.")


def _pick(row: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return None


def _parse_list_field(value: Any) -> Optional[List[str]]:
    if value in (None, ""):
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        items = [item.strip() for item in value.split(",") if item.strip()]
        return items or None
    return value


def _parse_json_field(value: Any, field_name: str, allow_list: bool = False) -> Any:
    if value in (None, ""):
        return None
    if isinstance(value, (dict, list)):
        if allow_list and isinstance(value, dict):
            return [value]
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return None
        if allow_list and isinstance(parsed, dict):
            return [parsed]
        return parsed
    raise ValueError(f"{field_name} must be JSON")


def _normalize_row(
    row: Dict[str, Any],
    *,
    default_output_language: Optional[str],
    default_prompt_version: Optional[str],
    default_model_version: Optional[str],
) -> Dict[str, Any]:
    template_recommendations = _parse_list_field(_pick(row, "template_recommendations", "templateRecommendations"))
    labels = _parse_list_field(_pick(row, "labels"))
    signature_motifs = _parse_list_field(_pick(row, "signature_motifs", "signatureMotifs"))
    evidence_refs = _parse_list_field(_pick(row, "evidence_refs", "evidenceRefs"))

    camera_motion = _parse_json_field(_pick(row, "camera_motion", "cameraMotion"), "camera_motion")
    color_palette = _parse_json_field(_pick(row, "color_palette", "colorPalette"), "color_palette")
    pacing = _parse_json_field(_pick(row, "pacing"), "pacing")

    story_beats = _parse_json_field(_pick(row, "story_beats", "storyBeats"), "story_beats", allow_list=True)
    storyboard_cards = _parse_json_field(
        _pick(row, "storyboard_cards", "storyboardCards"),
        "storyboard_cards",
        allow_list=True,
    )
    key_patterns = _parse_json_field(_pick(row, "key_patterns", "keyPatterns"), "key_patterns", allow_list=True)

    return {
        "source_id": _pick(row, "source_id", "sourceId"),
        "summary": _pick(row, "summary"),
        "output_type": _pick(row, "output_type", "outputType"),
        "output_language": _pick(row, "output_language", "outputLanguage") or default_output_language,
        "prompt_version": _pick(row, "prompt_version", "promptVersion") or default_prompt_version,
        "model_version": _pick(row, "model_version", "modelVersion") or default_model_version,
        "source_pack_id": _pick(row, "source_pack_id", "sourcePackId"),
        "guide_type": _pick(row, "guide_type", "guideType"),
        "homage_guide": _pick(row, "homage_guide", "homageGuide"),
        "variation_guide": _pick(row, "variation_guide", "variationGuide"),
        "template_recommendations": template_recommendations or [],
        "user_fit_notes": _pick(row, "user_fit_notes", "userFitNotes"),
        "persona_profile": _pick(row, "persona_profile", "personaProfile"),
        "synapse_logic": _pick(row, "synapse_logic", "synapseLogic"),
        "origin_notebook_id": _pick(row, "origin_notebook_id", "originNotebookId"),
        "filter_notebook_id": _pick(row, "filter_notebook_id", "filterNotebookId"),
        "cluster_id": _pick(row, "cluster_id", "clusterId"),
        "cluster_label": _pick(row, "cluster_label", "clusterLabel"),
        "cluster_confidence": _pick(row, "cluster_confidence", "clusterConfidence"),
        "style_logic": _pick(row, "style_logic", "styleLogic"),
        "mise_en_scene": _pick(row, "mise_en_scene", "miseEnScene"),
        "director_intent": _pick(row, "director_intent", "directorIntent"),
        "labels": labels or [],
        "signature_motifs": signature_motifs or [],
        "camera_motion": camera_motion or {},
        "color_palette": color_palette or {},
        "pacing": pacing or {},
        "sound_design": _pick(row, "sound_design", "soundDesign"),
        "editing_rhythm": _pick(row, "editing_rhythm", "editingRhythm"),
        "story_beats": story_beats or [],
        "storyboard_cards": storyboard_cards or [],
        "key_patterns": key_patterns or [],
        "studio_output_id": _pick(row, "studio_output_id", "studioOutputId"),
        "adapter": _pick(row, "adapter"),
        "opal_workflow_id": _pick(row, "opal_workflow_id", "opalWorkflowId"),
        "confidence": _pick(row, "confidence"),
        "notebook_id": _pick(row, "notebook_id", "notebookId"),
        "notebook_ref": _pick(row, "notebook_ref", "notebookRef"),
        "evidence_refs": evidence_refs or [],
        "generated_at": _pick(row, "generated_at", "generatedAt"),
    }


async def _upsert_records(
    rows: Iterable[Dict[str, Any]],
    *,
    dry_run: bool,
    allow_missing_raw: bool,
    mega_notebook_ids: Optional[set[str]] = None,
) -> int:
    if dry_run:
        return 0
    created = 0
    mega_notebook_ids = mega_notebook_ids or set()
    async with AsyncSessionLocal() as session:
        for row in rows:
            raw_result = await session.execute(
                select(RawAsset).where(RawAsset.source_id == row["source_id"])
            )
            raw_asset = raw_result.scalars().first()
            if not raw_asset and not allow_missing_raw:
                continue
            if raw_asset and raw_asset.rights_status == "restricted":
                continue

            result = await session.execute(
                select(EvidenceRecord).where(
                    EvidenceRecord.source_id == row["source_id"],
                    EvidenceRecord.prompt_version == row["prompt_version"],
                    EvidenceRecord.model_version == row["model_version"],
                    EvidenceRecord.output_type == row["output_type"],
                    EvidenceRecord.output_language == row["output_language"],
                )
            )
            record = result.scalars().first()
            if not record:
                record = EvidenceRecord(
                    source_id=row["source_id"],
                    summary=row["summary"],
                    output_type=row["output_type"],
                    output_language=row["output_language"],
                    prompt_version=row["prompt_version"],
                    model_version=row["model_version"],
                )
                session.add(record)
                created += 1

            record.summary = row["summary"]
            record.guide_type = row.get("guide_type")
            record.homage_guide = row.get("homage_guide")
            record.variation_guide = row.get("variation_guide")
            record.template_recommendations = row.get("template_recommendations") or []
            record.user_fit_notes = row.get("user_fit_notes")
            record.persona_profile = row.get("persona_profile")
            record.synapse_logic = row.get("synapse_logic")
            record.origin_notebook_id = row.get("origin_notebook_id")
            record.filter_notebook_id = row.get("filter_notebook_id")
            record.cluster_id = row.get("cluster_id")
            record.cluster_label = row.get("cluster_label")
            record.cluster_confidence = row.get("cluster_confidence")
            record.style_logic = row.get("style_logic")
            record.mise_en_scene = row.get("mise_en_scene")
            record.director_intent = row.get("director_intent")
            labels = row.get("labels") or []
            if row.get("notebook_id") in mega_notebook_ids:
                labels = ensure_label(labels, "ops_only")
            record.labels = labels
            record.signature_motifs = row.get("signature_motifs") or []
            record.camera_motion = row.get("camera_motion") or {}
            record.color_palette = row.get("color_palette") or {}
            record.pacing = row.get("pacing") or {}
            record.sound_design = row.get("sound_design")
            record.editing_rhythm = row.get("editing_rhythm")
            record.story_beats = row.get("story_beats") or []
            record.storyboard_cards = row.get("storyboard_cards") or []
            record.key_patterns = row.get("key_patterns") or []
            record.studio_output_id = row.get("studio_output_id")
            record.adapter = row.get("adapter")
            record.opal_workflow_id = row.get("opal_workflow_id")
            record.confidence = row.get("confidence")
            record.notebook_id = row.get("notebook_id")
            record.notebook_ref = row.get("notebook_ref")
            record.evidence_refs = row.get("evidence_refs") or []
            record.source_pack_id = row.get("source_pack_id")
            record.generated_at = row.get("generated_at")

        await session.commit()
    return created


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest derived insights into DB.")
    parser.add_argument("--input", required=True, help="Path to JSON file.")
    parser.add_argument("--default-output-language", help="Fallback output_language.")
    parser.add_argument("--default-prompt-version", help="Fallback prompt_version.")
    parser.add_argument("--default-model-version", help="Fallback model_version.")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, no DB writes.")
    parser.add_argument("--allow-missing-raw", action="store_true", help="Allow missing RawAsset records.")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        raise SystemExit(f"Input file not found: {path}")

    payload = _load_payload(path)
    raw_rows = _extract_rows(payload)

    await init_db()
    notebook_ids = {
        _pick(row, "notebook_id", "notebookId")
        for row in raw_rows
        if isinstance(row, dict)
    }
    notebook_ids = {value for value in notebook_ids if value}
    mega_notebook_ids: set[str] = set()
    if notebook_ids:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(NotebookLibrary).where(NotebookLibrary.notebook_id.in_(notebook_ids))
            )
            for notebook in result.scalars().all():
                if is_mega_notebook_notes(notebook.curator_notes):
                    mega_notebook_ids.add(notebook.notebook_id)

    normalized_rows: List[Dict[str, Any]] = []
    errors: List[str] = []
    for idx, row in enumerate(raw_rows, start=1):
        if not isinstance(row, dict):
            errors.append(f"Row {idx}: must be an object.")
            continue
        try:
            normalized = _normalize_row(
                row,
                default_output_language=args.default_output_language,
                default_prompt_version=args.default_prompt_version,
                default_model_version=args.default_model_version,
            )
            validated = EvidenceRecordRequest.model_validate(normalized)
            payload = validated.model_dump()
            if payload.get("notebook_id") in mega_notebook_ids:
                payload["labels"] = ensure_label(payload.get("labels") or [], "ops_only")
            generated_at = payload.get("generated_at")
            if isinstance(generated_at, datetime) and generated_at.tzinfo is not None:
                payload["generated_at"] = (
                    generated_at.astimezone(timezone.utc).replace(tzinfo=None)
                )
            normalized_rows.append(payload)
        except Exception as exc:
            errors.append(f"Row {idx}: {exc}")

    if errors:
        for error in errors:
            print(error)
        raise SystemExit(f"Validation failed for {len(errors)} rows.")

    created = await _upsert_records(
        normalized_rows,
        dry_run=args.dry_run,
        allow_missing_raw=args.allow_missing_raw,
        mega_notebook_ids=mega_notebook_ids,
    )
    action = "validated" if args.dry_run else "upserted"
    print(f"Rows {action}: {len(normalized_rows)} (created {created})")


if __name__ == "__main__":
    asyncio.run(main())
