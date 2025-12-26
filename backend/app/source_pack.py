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


def build_source_pack(
    segments: Iterable[VideoSegment],
    *,
    cluster_id: str,
    temporal_phase: str,
    pack_id: Optional[str] = None,
    notes: Optional[str] = None,
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
    resolved_pack_id = pack_id or f"sp_{cluster_id}_{temporal_phase}_{bundle_hash[:8]}"
    return {
        "pack_id": resolved_pack_id,
        "cluster_id": cluster_id,
        "temporal_phase": temporal_phase,
        "source_ids": source_ids,
        "segment_refs": segment_refs,
        "metrics_snapshot": metrics_snapshot,
        "bundle_hash": bundle_hash,
        "notes": notes,
    }
