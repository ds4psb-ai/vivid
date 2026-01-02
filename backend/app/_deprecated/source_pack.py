"""Source pack builder for NotebookLM inputs."""
from __future__ import annotations

import hashlib
import json
from typing import Iterable, List, Dict, Optional

from app.models import VideoSegment


def _segment_ref(segment: VideoSegment) -> Dict[str, Optional[str]]:
    return {
        "segment_id": segment.segment_id,
        "source_id": segment.source_id,
        "segment_type": segment.segment_type,  # video | script | text
        "work_id": segment.work_id,
        "sequence_id": segment.sequence_id,
        "scene_id": segment.scene_id,
        "shot_id": segment.shot_id,
        "time_start": segment.time_start,
        "time_end": segment.time_end,
    }


def hash_source_pack(payload: Dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _with_shard_suffix(
    pack_id: str,
    shard_index: Optional[int],
    shard_total: Optional[int],
) -> str:
    if not shard_total or shard_total <= 1 or shard_index is None:
        return pack_id
    suffix = f"p{shard_index:02d}"
    if pack_id.endswith(f"_{suffix}"):
        return pack_id
    return f"{pack_id}_{suffix}"


def _manifest_for_sources(
    source_manifest: Optional[List[Dict[str, object]]],
    source_ids: List[str],
) -> List[Dict[str, object]]:
    if not source_manifest:
        return []
    allowed = set(source_ids)
    filtered: List[Dict[str, object]] = []
    for item in source_manifest:
        source_id = str(
            item.get("source_id")
            or item.get("sourceId")
            or item.get("id")
            or ""
        )
        if source_id and source_id in allowed:
            filtered.append(item)
    return filtered or list(source_manifest)


def build_source_pack(
    segments: Iterable[VideoSegment],
    *,
    cluster_id: str,
    temporal_phase: str,
    pack_id: Optional[str] = None,
    notes: Optional[str] = None,
    source_snapshot_at: Optional[str] = None,
    source_sync_at: Optional[str] = None,
    source_manifest: Optional[List[Dict[str, object]]] = None,
    shard_index: Optional[int] = None,
    shard_total: Optional[int] = None,
) -> Dict[str, object]:
    ordered = sorted(segments, key=lambda seg: (seg.time_start or "", seg.segment_id))
    segment_refs = [_segment_ref(segment) for segment in ordered]
    source_ids = sorted({segment.source_id for segment in ordered if segment.source_id})
    shot_ids = {segment.shot_id for segment in ordered if segment.shot_id}
    metrics_snapshot = {
        "segment_count": len(segment_refs),
        "source_count": len(source_ids),
        "shot_count": len(shot_ids),
    }
    payload = {
        "cluster_id": cluster_id,
        "temporal_phase": temporal_phase,
        "segment_refs": segment_refs,
        "metrics_snapshot": metrics_snapshot,
    }
    bundle_hash = hash_source_pack(payload)
    base_pack_id = pack_id or f"sp_{cluster_id}_{temporal_phase}_{bundle_hash[:8]}"
    resolved_pack_id = _with_shard_suffix(base_pack_id, shard_index, shard_total)
    resolved_manifest = _manifest_for_sources(source_manifest, source_ids)
    source_count = len(resolved_manifest) if resolved_manifest else len(source_ids)
    return {
        "pack_id": resolved_pack_id,
        "cluster_id": cluster_id,
        "temporal_phase": temporal_phase,
        "source_snapshot_at": source_snapshot_at,
        "source_sync_at": source_sync_at,
        "source_count": source_count,
        "source_manifest": resolved_manifest,
        "source_ids": source_ids,
        "segment_refs": segment_refs,
        "metrics_snapshot": metrics_snapshot,
        "bundle_hash": bundle_hash,
        "notes": notes,
    }


def build_source_packs(
    segments: Iterable[VideoSegment],
    *,
    cluster_id: str,
    temporal_phase: str,
    pack_id: Optional[str] = None,
    notes: Optional[str] = None,
    max_sources: int = 50,
    source_snapshot_at: Optional[str] = None,
    source_sync_at: Optional[str] = None,
    source_manifest: Optional[List[Dict[str, object]]] = None,
) -> List[Dict[str, object]]:
    ordered = sorted(segments, key=lambda seg: (seg.time_start or "", seg.segment_id))
    if max_sources <= 0:
        max_sources = 50
    by_source: Dict[str, List[VideoSegment]] = {}
    for segment in ordered:
        if not segment.source_id:
            continue
        by_source.setdefault(segment.source_id, []).append(segment)
    source_ids = sorted(by_source.keys())
    if not source_ids:
        return [
            build_source_pack(
                ordered,
                cluster_id=cluster_id,
                temporal_phase=temporal_phase,
                pack_id=pack_id,
                notes=notes,
                source_snapshot_at=source_snapshot_at,
                source_sync_at=source_sync_at,
                source_manifest=source_manifest,
            )
        ]
    shards = [
        source_ids[i : i + max_sources]
        for i in range(0, len(source_ids), max_sources)
    ]
    packs: List[Dict[str, object]] = []
    for idx, shard in enumerate(shards, start=1):
        shard_segments: List[VideoSegment] = []
        for source_id in shard:
            shard_segments.extend(by_source.get(source_id, []))
        pack = build_source_pack(
            shard_segments,
            cluster_id=cluster_id,
            temporal_phase=temporal_phase,
            pack_id=pack_id,
            notes=notes,
            source_snapshot_at=source_snapshot_at,
            source_sync_at=source_sync_at,
            source_manifest=_manifest_for_sources(source_manifest, shard),
            shard_index=idx,
            shard_total=len(shards),
        )
        packs.append(pack)
    return packs
