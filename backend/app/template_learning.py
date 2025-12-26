"""Template learning helpers (GA/RL reward + auto-promotion)."""
from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Template, TemplateLearningRun, TemplateVersion


def _safe_int(value: Optional[str], default: Optional[int]) -> Optional[int]:
    if value is None:
        return default
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _safe_float(value: Optional[str], default: float) -> float:
    if value is None:
        return default
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


MIN_EVIDENCE_REFS = _safe_int(os.getenv("TEMPLATE_REWARD_MIN_EVIDENCE"), 3) or 3
MAX_CREDIT_COST = _safe_int(os.getenv("TEMPLATE_REWARD_MAX_CREDITS"), 120) or 120
MAX_LATENCY_MS = _safe_int(os.getenv("TEMPLATE_REWARD_MAX_LATENCY_MS"), 5000) or 5000
PROMOTION_THRESHOLD = _safe_float(os.getenv("TEMPLATE_PROMOTION_THRESHOLD"), 0.75)
PROMOTION_MIN_SAMPLES = _safe_int(os.getenv("TEMPLATE_PROMOTION_MIN_SAMPLES"), 3) or 3
AUTO_PROMOTE_TEMPLATES = os.getenv("AUTO_PROMOTE_TEMPLATES", "false").lower() in {
    "1",
    "true",
    "yes",
}


def extract_template_origin(graph_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    if not isinstance(graph_data, dict):
        return None, None, None
    meta = graph_data.get("meta")
    if not isinstance(meta, dict):
        meta = {}
    origin = meta.get("template_origin")
    if not isinstance(origin, dict):
        origin = {}
    template_id = origin.get("template_id") or meta.get("template_id")
    template_version = origin.get("template_version") or meta.get("template_version")
    template_slug = origin.get("template_slug") or meta.get("template_slug")
    if isinstance(template_version, str):
        template_version = _safe_int(template_version, None)  # type: ignore[arg-type]
    if isinstance(template_id, str):
        template_id = template_id.strip() or None
    if isinstance(template_slug, str):
        template_slug = template_slug.strip() or None
    return template_id, template_version, template_slug


def extract_evidence_refs(graph_data: Dict[str, Any]) -> List[str]:
    if not isinstance(graph_data, dict):
        return []
    meta = graph_data.get("meta")
    if not isinstance(meta, dict):
        return []
    refs = meta.get("evidence_refs")
    if not isinstance(refs, list):
        return []
    cleaned: List[str] = []
    for ref in refs:
        if not isinstance(ref, str):
            continue
        value = ref.strip()
        if not value:
            continue
        lowered = value.lower()
        if lowered.startswith("sheet:") or lowered.startswith("db:"):
            cleaned.append(value)
    return cleaned


def extract_capsule_params(graph_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(graph_data, dict):
        return []
    nodes = graph_data.get("nodes")
    if not isinstance(nodes, list):
        return []
    result: List[Dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if node.get("type") != "capsule":
            continue
        data = node.get("data")
        if not isinstance(data, dict):
            continue
        params = data.get("params") if isinstance(data.get("params"), dict) else {}
        result.append(
            {
                "node_id": node.get("id"),
                "capsule_id": data.get("capsuleId"),
                "capsule_version": data.get("capsuleVersion"),
                "params": params,
            }
        )
    return result


def summarize_feedback(shots: List[Dict[str, Any]]) -> Dict[str, Any]:
    ratings: List[int] = []
    for shot in shots:
        if not isinstance(shot, dict):
            continue
        rating = shot.get("rating")
        if isinstance(rating, int):
            ratings.append(rating)
    if ratings:
        avg_rating = sum(ratings) / len(ratings)
    else:
        avg_rating = 0.0
    return {
        "rating_count": len(ratings),
        "avg_rating": round(avg_rating, 2),
        "min_rating": min(ratings) if ratings else None,
        "max_rating": max(ratings) if ratings else None,
    }


def compute_reward(
    *,
    feedback_shots: List[Dict[str, Any]],
    evidence_refs: List[str],
    credit_cost: Optional[int],
    latency_ms: Optional[int] = None,
    cost_usd_est: Optional[float] = None,
    shot_count: int,
) -> Dict[str, Any]:
    feedback_summary = summarize_feedback(feedback_shots)
    rating_score = (feedback_summary["avg_rating"] or 0.0) / 5.0
    feedback_coverage = 0.0
    if shot_count > 0:
        feedback_coverage = feedback_summary["rating_count"] / shot_count
    evidence_score = 0.0
    if MIN_EVIDENCE_REFS > 0:
        evidence_score = min(len(evidence_refs) / MIN_EVIDENCE_REFS, 1.0)

    cost_score = 0.5
    if cost_usd_est is not None:
        max_cost = max(1.0, float(MAX_CREDIT_COST))
        cost_score = 1.0 - min(float(cost_usd_est) / max_cost, 1.0)
    elif credit_cost is not None:
        max_cost = max(1, MAX_CREDIT_COST)
        cost_score = 1.0 - min(float(credit_cost) / max_cost, 1.0)

    latency_score = 0.5
    if isinstance(latency_ms, int) and latency_ms > 0:
        baseline = max(1, MAX_LATENCY_MS)
        latency_score = min(float(baseline) / float(latency_ms), 1.0)

    feedback_weight = 0.45
    evidence_weight = 0.25
    cost_weight = 0.15
    latency_weight = 0.15
    reward_score = (
        rating_score * feedback_weight
        + evidence_score * evidence_weight
        + cost_score * cost_weight
        + latency_score * latency_weight
    )

    return {
        "score": round(max(0.0, min(reward_score, 1.0)), 4),
        "components": {
            "rating_score": round(rating_score, 4),
            "feedback_coverage": round(min(feedback_coverage, 1.0), 4),
            "evidence_score": round(evidence_score, 4),
            "cost_score": round(cost_score, 4),
            "latency_score": round(latency_score, 4),
        },
        "weights": {
            "feedback": feedback_weight,
            "evidence": evidence_weight,
            "cost": cost_weight,
            "latency": latency_weight,
        },
        "feedback_summary": feedback_summary,
        "shot_count": shot_count,
        "evidence_count": len(evidence_refs),
        "latency_ms": latency_ms,
    }


async def record_learning_run(
    db: AsyncSession,
    *,
    template_id: uuid.UUID,
    template_version: int,
    canvas_id: uuid.UUID,
    run_id: uuid.UUID,
    reward: Dict[str, Any],
    evidence_refs: List[str],
    feedback: Dict[str, Any],
    capsule_params: List[Dict[str, Any]],
) -> TemplateLearningRun:
    result = await db.execute(
        select(TemplateLearningRun).where(
            TemplateLearningRun.template_id == template_id,
            TemplateLearningRun.run_id == run_id,
        )
    )
    existing = result.scalars().first()
    payload = {
        "template_id": template_id,
        "template_version": template_version,
        "canvas_id": canvas_id,
        "run_id": run_id,
        "reward_score": reward.get("score"),
        "reward_breakdown": reward,
        "feedback": feedback,
        "evidence_refs": evidence_refs,
        "params": {"capsules": capsule_params},
        "status": "recorded",
    }
    if existing:
        existing.template_version = template_version
        existing.reward_score = payload["reward_score"]
        existing.reward_breakdown = payload["reward_breakdown"]
        existing.feedback = payload["feedback"]
        existing.evidence_refs = payload["evidence_refs"]
        existing.params = payload["params"]
        existing.status = payload["status"]
        return existing
    record = TemplateLearningRun(**payload)
    db.add(record)
    return record


async def maybe_promote_template_version(
    db: AsyncSession,
    *,
    template_id: uuid.UUID,
    template_version: int,
    canvas_graph: Dict[str, Any],
    reward_threshold: Optional[float] = None,
    min_samples: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    resolved_threshold = PROMOTION_THRESHOLD if reward_threshold is None else reward_threshold
    resolved_min_samples = PROMOTION_MIN_SAMPLES if min_samples is None else min_samples

    template_result = await db.execute(select(Template).where(Template.id == template_id))
    template = template_result.scalars().first()
    if not template:
        return None
    if template.version != template_version:
        return None

    summary_result = await db.execute(
        select(
            func.count(TemplateLearningRun.id),
            func.avg(TemplateLearningRun.reward_score),
        ).where(
            TemplateLearningRun.template_id == template_id,
            TemplateLearningRun.template_version == template_version,
            TemplateLearningRun.reward_score.is_not(None),
        )
    )
    sample_count, avg_score = summary_result.one()
    sample_count = int(sample_count or 0)
    avg_score = float(avg_score or 0.0)
    if sample_count < resolved_min_samples:
        return None
    if avg_score < resolved_threshold:
        return None
    evidence_result = await db.execute(
        select(TemplateLearningRun.evidence_refs).where(
            TemplateLearningRun.template_id == template_id,
            TemplateLearningRun.template_version == template_version,
        )
    )
    evidence_rows = evidence_result.scalars().all()
    evidence_counts: List[int] = []
    for refs in evidence_rows:
        if isinstance(refs, list):
            evidence_counts.append(len(refs))
    if evidence_counts:
        avg_evidence = sum(evidence_counts) / len(evidence_counts)
        if avg_evidence < MIN_EVIDENCE_REFS:
            return None

    template.version = (template.version or 1) + 1
    template.graph_data = canvas_graph
    note = (
        "auto-promotion "
        f"avg_reward={avg_score:.2f} "
        f"samples={sample_count}"
    )
    db.add(
        TemplateVersion(
            template_id=template.id,
            version=template.version,
            graph_data=canvas_graph,
            notes=note,
            creator_id=template.creator_id,
        )
    )
    await db.execute(
        TemplateLearningRun.__table__.update()
        .where(
            TemplateLearningRun.template_id == template_id,
            TemplateLearningRun.template_version == template_version,
        )
        .values(status="promoted", updated_at=datetime.utcnow())
    )

    return {
        "template_id": template_id,
        "template_version": template.version,
        "avg_reward": round(avg_score, 4),
        "samples": sample_count,
        "note": note,
    }
