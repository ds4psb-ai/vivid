"""Capsule spec and execution endpoints."""
import asyncio
import json
import time
import uuid
from uuid import UUID
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_is_admin, get_user_id
from app.config import settings
from app.credit_service import deduct_credits, get_or_create_user_credits
from app.database import AsyncSessionLocal, get_db
from app.models import (
    CapsuleSpec,
    CapsuleRun,
    Canvas,
    EvidenceRecord,
    NotebookLibrary,
    Pattern,
    PatternTrace,
    RawAsset,
    VideoSegment,
)
from app.run_events import run_event_hub

router = APIRouter()

DEFAULT_INPUT_VALUES = {
    "emotion_curve": [0.3, 0.5, 0.7, 0.9, 0.6],
    "scene_summary": "",
    "duration_sec": 60,
}
STRICT_CONTRACTS = True
STRICT_EVIDENCE_REFS = True
STRICT_OUTPUT_CONTRACTS = True


class CapsuleSpecResponse(BaseModel):
    id: str
    capsule_key: str
    version: str
    display_name: str
    description: str
    spec: dict
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class CapsuleRunRequest(BaseModel):
    canvas_id: Optional[str] = None
    node_id: Optional[str] = None
    capsule_id: str
    capsule_version: str
    inputs: dict
    params: dict
    upstream_context: Optional[dict] = None
    async_mode: bool = False


class CapsuleRunResponse(BaseModel):
    run_id: str
    status: str
    summary: dict
    evidence_refs: List[str]
    version: str
    token_usage: Optional[dict] = None
    latency_ms: Optional[int] = None
    cost_usd_est: Optional[float] = None
    cached: bool = False


class CapsuleRunHistoryItem(BaseModel):
    run_id: str
    status: str
    summary: dict
    evidence_refs: List[str]
    version: str
    token_usage: Optional[dict] = None
    latency_ms: Optional[int] = None
    cost_usd_est: Optional[float] = None
    created_at: datetime


class CapsuleRunStatusResponse(BaseModel):
    run_id: str
    capsule_id: str
    status: str
    summary: dict
    evidence_refs: List[str]
    version: str
    token_usage: Optional[dict] = None
    latency_ms: Optional[int] = None
    cost_usd_est: Optional[float] = None
    created_at: datetime
    updated_at: datetime


def _to_response(spec: CapsuleSpec) -> CapsuleSpecResponse:
    return CapsuleSpecResponse(
        id=str(spec.id),
        capsule_key=spec.capsule_key,
        version=spec.version,
        display_name=spec.display_name,
        description=spec.description,
        spec=spec.spec,
        is_active=spec.is_active,
    )


def _to_run_history_item(run: CapsuleRun) -> CapsuleRunHistoryItem:
    return CapsuleRunHistoryItem(
        run_id=str(run.id),
        status=run.status,
        summary=run.summary,
        evidence_refs=run.evidence_refs,
        version=run.capsule_version,
        token_usage=run.token_usage,
        latency_ms=run.latency_ms,
        cost_usd_est=run.cost_usd_est,
        created_at=run.created_at,
    )


def _default_for_type(type_name: Optional[str]) -> object:
    if type_name == "number":
        return 0
    if type_name in {"float[]", "number[]"}:
        return []
    if type_name == "string[]":
        return []
    if type_name == "boolean":
        return False
    return ""


def _validate_input_type(value: object, type_name: Optional[str]) -> bool:
    if type_name == "number":
        return isinstance(value, (int, float))
    if type_name in {"float[]", "number[]"}:
        return isinstance(value, list) and all(isinstance(item, (int, float)) for item in value)
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "string[]":
        return isinstance(value, list) and all(isinstance(item, str) for item in value)
    if type_name == "boolean":
        return isinstance(value, bool)
    return True


def _validate_uuid(value: str, label: str) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid {label} format")


def _normalize_allowed_type(value: str) -> Optional[str]:
    if not isinstance(value, str):
        return None
    cleaned = value.strip().lower()
    if not cleaned:
        return None
    if "/" in cleaned:
        prefix = cleaned.split("/", 1)[0]
        if prefix in {"text", "application"}:
            return "doc"
        if prefix in {"video", "image"}:
            return prefix
        return prefix
    if cleaned in {"text", "application"}:
        return "doc"
    return cleaned


async def _validate_allowed_types(
    inputs: dict,
    input_contracts: Optional[dict],
    db: AsyncSession,
    warnings: list[str],
) -> None:
    if not isinstance(input_contracts, dict):
        return
    raw_allowed = input_contracts.get("allowedTypes") or input_contracts.get("allowed_types")
    if not raw_allowed:
        return
    if isinstance(raw_allowed, str):
        raw_allowed = [raw_allowed]
    if not isinstance(raw_allowed, list):
        raise HTTPException(status_code=400, detail="allowedTypes must be a list of strings")
    allowed = {t for t in (_normalize_allowed_type(item) for item in raw_allowed) if t}
    if not allowed:
        raise HTTPException(status_code=400, detail="allowedTypes cannot be empty")
    source_id = inputs.get("source_id") or inputs.get("sourceId")
    if not isinstance(source_id, str) or not source_id.strip():
        raise HTTPException(status_code=400, detail="source_id required when allowedTypes is set")
    cleaned_source_id = source_id.strip()
    result = await db.execute(select(RawAsset).where(RawAsset.source_id == cleaned_source_id))
    asset = result.scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail="Raw asset not found for source_id")
    source_type = _normalize_allowed_type(asset.source_type or "")
    if not source_type:
        raise HTTPException(status_code=400, detail="Raw asset source_type is missing or invalid")
    if source_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"source_type '{source_type}' not allowed (allowed: {sorted(allowed)})",
        )


def _extract_node_payload(node: dict) -> dict:
    data = node.get("data") or {}
    return {
        "id": node.get("id"),
        "type": node.get("type"),
        "label": data.get("label") or data.get("title") or "",
        "subtitle": data.get("subtitle"),
        "params": data.get("params") or {},
        "capsuleId": data.get("capsuleId"),
        "capsuleVersion": data.get("capsuleVersion"),
    }


def _build_upstream_sequence(nodes: list[dict], edges: list[dict]) -> list[dict]:
    node_ids = [node.get("id") for node in nodes if isinstance(node, dict) and node.get("id")]
    if not node_ids:
        return []

    node_set = set(node_ids)
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_set}
    indegree: dict[str, int] = {node_id: 0 for node_id in node_set}

    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source = edge.get("source")
        target = edge.get("target")
        if source in node_set and target in node_set:
            adjacency[source].append(target)
            indegree[target] += 1

    ordered: list[str] = []
    queue = sorted([node_id for node_id in node_set if indegree[node_id] == 0])
    while queue:
        current = queue.pop(0)
        ordered.append(current)
        for neighbor in sorted(adjacency.get(current, [])):
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    if len(ordered) < len(node_set):
        for node_id in node_ids:
            if node_id not in ordered:
                ordered.append(node_id)

    payload_map = {node.get("id"): node for node in nodes if isinstance(node, dict)}
    return [payload_map[node_id] for node_id in ordered if node_id in payload_map]


async def _build_upstream_context(
    canvas_id: Optional[str],
    node_id: Optional[str],
    db: AsyncSession,
    context_mode: Optional[str] = None,
) -> tuple[dict, Optional[str]]:
    if not canvas_id or not node_id:
        return {}, "context:missing_canvas_or_node"
    canvas_uuid = _validate_uuid(canvas_id, "canvas_id")
    result = await db.execute(select(Canvas).where(Canvas.id == canvas_uuid))
    canvas = result.scalar_one_or_none()
    if not canvas:
        return {}, "context:canvas_not_found"
    graph_data = canvas.graph_data or {}
    nodes = graph_data.get("nodes")
    edges = graph_data.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return {}, "context:invalid_graph"
    node_ids = {node.get("id") for node in nodes if isinstance(node, dict) and node.get("id")}
    if node_id not in node_ids:
        return {}, "context:node_not_found"

    incoming: dict[str, list[str]] = {}
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            continue
        incoming.setdefault(target, []).append(source)

    visited: set[str] = set()
    stack = [node_id]
    while stack:
        current = stack.pop()
        parents = incoming.get(current, [])
        for parent in parents:
            if parent not in visited:
                visited.add(parent)
                stack.append(parent)

    upstream_nodes = [
        _extract_node_payload(node)
        for node in nodes
        if isinstance(node, dict) and node.get("id") in visited
    ]
    upstream_edges = [
        {
            "id": edge.get("id"),
            "source": edge.get("source"),
            "target": edge.get("target"),
        }
        for edge in edges
        if isinstance(edge, dict)
        and edge.get("source") in visited
        and edge.get("target") in visited
    ]

    if context_mode == "sequential":
        sequence = _build_upstream_sequence(upstream_nodes, upstream_edges)
        return {
            "nodes": upstream_nodes,
            "edges": upstream_edges,
            "mode": "sequential",
            "sequence": sequence,
        }, None
    if context_mode == "aggregate":
        return {"nodes": upstream_nodes, "edges": upstream_edges, "mode": "aggregate"}, None
    return {"nodes": upstream_nodes, "edges": upstream_edges}, None


def _requires_upstream_context(input_contracts: Optional[dict]) -> bool:
    if not isinstance(input_contracts, dict):
        return False
    raw_mode = input_contracts.get("contextMode") or input_contracts.get("context_mode")
    if isinstance(raw_mode, str) and raw_mode.strip() in {"aggregate", "sequential"}:
        return True
    raw_max = input_contracts.get("maxUpstream") or input_contracts.get("max_upstream")
    if raw_max in (None, "", 0):
        return False
    try:
        return int(raw_max) > 0
    except (TypeError, ValueError):
        return True


def _validate_inputs(
    spec_inputs: dict,
    inputs: dict,
    allow_fallbacks: bool,
    input_contracts: Optional[dict] = None,
) -> tuple[dict, list[str]]:
    if not isinstance(inputs, dict):
        raise HTTPException(status_code=400, detail="inputs must be a dictionary")

    input_values = dict(inputs)
    sanitized: dict = {}
    warnings: list[str] = []
    contract = input_contracts or {}
    required_keys = set(contract.get("required") or [])
    optional_keys = set(contract.get("optional") or [])
    contract_keys = required_keys | optional_keys
    if STRICT_CONTRACTS and spec_inputs and contract_keys:
        missing_defs = contract_keys - set(spec_inputs.keys())
        if missing_defs:
            raise HTTPException(
                status_code=400,
                detail=f"inputContracts keys missing from inputs: {', '.join(sorted(missing_defs))}",
            )

    for key in sorted(required_keys):
        if key in input_values:
            continue
        if allow_fallbacks:
            type_name = (spec_inputs or {}).get(key, {}).get("type")
            fallback = DEFAULT_INPUT_VALUES.get(key, _default_for_type(type_name))
            input_values[key] = fallback
            warnings.append(f"fallback:{key}")
        else:
            raise HTTPException(status_code=400, detail=f"Missing required input: {key}")
    for key, meta in (spec_inputs or {}).items():
        type_name = (meta or {}).get("type")
        required = bool((meta or {}).get("required"))
        if key not in input_values:
            if required:
                if allow_fallbacks:
                    fallback = DEFAULT_INPUT_VALUES.get(key, _default_for_type(type_name))
                    sanitized[key] = fallback
                    warnings.append(f"fallback:{key}")
                else:
                    raise HTTPException(status_code=400, detail=f"Missing required input: {key}")
            continue
        value = input_values.get(key)
        if not _validate_input_type(value, type_name):
            raise HTTPException(status_code=400, detail=f"Invalid input type for {key}")
        sanitized[key] = value

    if not spec_inputs and contract_keys:
        for key in sorted(contract_keys):
            if key in input_values:
                sanitized[key] = input_values.get(key)

    if STRICT_CONTRACTS:
        known_keys = set((spec_inputs or {}).keys()) | contract_keys
        if known_keys:
            extra_keys = set(input_values.keys()) - known_keys
            if extra_keys:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown inputs: {', '.join(sorted(extra_keys))}",
                )

    return sanitized, warnings


def _validate_upstream_contract(
    upstream_context: dict,
    input_contracts: Optional[dict],
) -> None:
    if not isinstance(input_contracts, dict):
        return
    raw_mode = input_contracts.get("contextMode") or input_contracts.get("context_mode")
    context_mode = raw_mode.strip() if isinstance(raw_mode, str) else None
    if context_mode and context_mode not in {"aggregate", "sequential"}:
        raise HTTPException(status_code=400, detail="contextMode must be aggregate or sequential")
    if context_mode:
        if not isinstance(upstream_context, dict):
            raise HTTPException(status_code=400, detail="upstream_context must be a dictionary")
        nodes = upstream_context.get("nodes")
        if not isinstance(nodes, list):
            raise HTTPException(status_code=400, detail="upstream_context.nodes must be a list")
        if context_mode == "sequential":
            sequence = upstream_context.get("sequence")
            if not isinstance(sequence, list):
                raise HTTPException(
                    status_code=400, detail="upstream_context.sequence must be a list"
                )
    raw_max = input_contracts.get("maxUpstream") or input_contracts.get("max_upstream")
    if raw_max in (None, "", 0):
        return
    try:
        max_upstream = int(raw_max)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="maxUpstream must be an integer")
    if max_upstream <= 0:
        raise HTTPException(status_code=400, detail="maxUpstream must be greater than 0")
    if not isinstance(upstream_context, dict):
        raise HTTPException(status_code=400, detail="upstream_context must be a dictionary")
    nodes = upstream_context.get("nodes")
    if not isinstance(nodes, list):
        raise HTTPException(status_code=400, detail="upstream_context.nodes must be a list")
    count = len(nodes)
    if count > max_upstream:
        raise HTTPException(
            status_code=400,
            detail=f"upstream_context exceeds maxUpstream ({count} > {max_upstream})",
        )


def _validate_params(
    exposed_params: dict,
    params: dict,
    is_admin: bool,
) -> dict:
    if not isinstance(params, dict):
        raise HTTPException(status_code=400, detail="params must be a dictionary")

    sanitized: dict = {}
    allowed_keys = set((exposed_params or {}).keys())
    extra_keys = set(params.keys()) - allowed_keys
    if extra_keys:
        raise HTTPException(status_code=400, detail=f"Unknown params: {', '.join(sorted(extra_keys))}")

    for key, meta in (exposed_params or {}).items():
        meta = meta or {}
        visibility = meta.get("visibility", "public")
        if visibility == "admin" and not is_admin:
            if key in params:
                raise HTTPException(status_code=403, detail=f"Admin param not allowed: {key}")
            continue

        if key in params:
            value = params.get(key)
        elif "default" in meta:
            value = meta.get("default")
        else:
            continue

        param_type = meta.get("type")
        if param_type == "number":
            if not isinstance(value, (int, float)):
                raise HTTPException(status_code=400, detail=f"Invalid number param: {key}")
            min_value = meta.get("min")
            max_value = meta.get("max")
            if isinstance(min_value, (int, float)) and value < min_value:
                raise HTTPException(status_code=400, detail=f"Param out of range: {key}")
            if isinstance(max_value, (int, float)) and value > max_value:
                raise HTTPException(status_code=400, detail=f"Param out of range: {key}")
        elif param_type == "enum":
            options = meta.get("options", [])
            if value not in options:
                raise HTTPException(status_code=400, detail=f"Invalid enum param: {key}")
        elif param_type == "boolean":
            if not isinstance(value, bool):
                raise HTTPException(status_code=400, detail=f"Invalid boolean param: {key}")
        elif param_type == "string":
            if not isinstance(value, str):
                raise HTTPException(status_code=400, detail=f"Invalid string param: {key}")

        sanitized[key] = value

    return sanitized


def _apply_output_contracts(summary: dict, output_contracts: Optional[dict]) -> list[str]:
    if not output_contracts or not isinstance(summary, dict):
        return []
    types = output_contracts.get("types")
    if not isinstance(types, list):
        return []
    missing = [entry for entry in types if entry not in summary]
    if not missing:
        return []
    return [f"missing_outputs:{','.join(missing)}"]


def _enforce_output_contracts(summary: dict, output_contracts: Optional[dict]) -> None:
    missing = _apply_output_contracts(summary, output_contracts)
    if missing:
        raise HTTPException(
            status_code=400, detail=f"Output contracts not satisfied: {', '.join(missing)}"
        )


def _enforce_evidence_refs(warnings: list[str]) -> None:
    if warnings:
        raise HTTPException(
            status_code=400, detail=f"Invalid evidence_refs: {', '.join(warnings)}"
        )


def _apply_policy(
    summary: dict,
    evidence_refs: list[str],
    policy: dict,
    is_admin: bool,
) -> tuple[dict, list[str]]:
    if not policy:
        return summary, evidence_refs

    filtered = dict(summary)
    allow_raw_logs = bool(policy.get("allowRawLogs", False))
    if not is_admin or not allow_raw_logs:
        for key in ("raw_logs", "debug", "trace"):
            filtered.pop(key, None)

    evidence_policy = policy.get("evidence", "summary_only")
    if evidence_policy == "references_only":
        filtered = {
            "message": "references_only",
            "capsule_id": summary.get("capsule_id"),
            "version": summary.get("version"),
        }

    return filtered, evidence_refs


async def _db_ref_exists(table: str, raw_id: str, db: AsyncSession) -> bool:
    if not table or not raw_id:
        return False
    if table == "evidence_records":
        try:
            record_id = uuid.UUID(raw_id)
        except ValueError:
            return False
        result = await db.execute(select(EvidenceRecord.id).where(EvidenceRecord.id == record_id))
        return result.scalar_one_or_none() is not None
    if table == "raw_assets":
        result = await db.execute(select(RawAsset.id).where(RawAsset.source_id == raw_id))
        return result.scalar_one_or_none() is not None
    if table == "video_segments":
        result = await db.execute(select(VideoSegment.id).where(VideoSegment.segment_id == raw_id))
        return result.scalar_one_or_none() is not None
    if table == "pattern_trace":
        try:
            trace_id = uuid.UUID(raw_id)
        except ValueError:
            return False
        result = await db.execute(select(PatternTrace.id).where(PatternTrace.id == trace_id))
        return result.scalar_one_or_none() is not None
    if table == "patterns":
        try:
            pattern_id = uuid.UUID(raw_id)
        except ValueError:
            return False
        result = await db.execute(select(Pattern.id).where(Pattern.id == pattern_id))
        return result.scalar_one_or_none() is not None
    if table == "notebook_library":
        result = await db.execute(
            select(NotebookLibrary.id).where(NotebookLibrary.notebook_id == raw_id)
        )
        return result.scalar_one_or_none() is not None
    return False


async def _filter_evidence_refs(
    refs: list[str],
    db: AsyncSession,
) -> tuple[list[str], list[str]]:
    if not refs:
        return [], []

    filtered: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()

    for ref in refs:
        if not isinstance(ref, str):
            warnings.append("evidence_ref_filtered:invalid_type")
            continue
        cleaned = ref.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)

        if cleaned.startswith("sheet:"):
            parts = cleaned.split(":", 2)
            if len(parts) == 3 and parts[1] and parts[2]:
                filtered.append(cleaned)
            else:
                warnings.append("evidence_ref_filtered:invalid_sheet_format")
            continue
        if cleaned.startswith("db:"):
            parts = cleaned.split(":", 2)
            if len(parts) != 3 or not parts[1] or not parts[2]:
                warnings.append("evidence_ref_filtered:invalid_db_format")
                continue
            table = parts[1]
            raw_id = parts[2]
            if await _db_ref_exists(table, raw_id, db):
                filtered.append(cleaned)
            else:
                warnings.append(f"evidence_ref_filtered:db_missing:{table}")
            continue

        prefix = cleaned.split(":", 1)[0]
        warnings.append(f"evidence_ref_filtered:disallowed_prefix:{prefix}")

    return filtered, warnings


def _extract_metrics(summary: dict) -> tuple[dict, Optional[float]]:
    if not isinstance(summary, dict):
        return {"input": 0, "output": 0, "total": 0}, None
    usage = summary.get("token_usage")
    if not isinstance(usage, dict):
        usage = {"input": 0, "output": 0, "total": 0}
    cost = summary.get("cost_usd_est")
    if isinstance(cost, (int, float)):
        return usage, float(cost)
    return usage, None


def _estimate_capsule_credits(spec_payload: dict) -> int:
    if not isinstance(spec_payload, dict):
        return 10
    raw_cost = (
        spec_payload.get("creditCost")
        or spec_payload.get("credit_cost")
        or spec_payload.get("credits")
    )
    if isinstance(raw_cost, (int, float)):
        base = max(1, int(round(raw_cost)))
    else:
        base = 10
    adapter = spec_payload.get("adapter") or {}
    adapter_type = adapter.get("type", "internal")
    multiplier = {
        "notebooklm": 1.0,
        "opal": 1.2,
        "hybrid": 1.5,
        "internal": 1.0,
    }.get(str(adapter_type), 1.0)
    return max(1, int(round(base * multiplier)))


def _apply_pattern_version(summary: dict, pattern_version: Optional[str]) -> dict:
    if not isinstance(summary, dict) or not pattern_version:
        return summary
    if "pattern_version" in summary:
        return summary
    return {**summary, "pattern_version": pattern_version}


def _apply_source_id(summary: dict, inputs: dict) -> dict:
    if not isinstance(summary, dict):
        return summary
    if "source_id" in summary:
        return summary
    if not isinstance(inputs, dict):
        return summary
    source_id = inputs.get("source_id") or inputs.get("sourceId")
    if not isinstance(source_id, str):
        return summary
    cleaned = source_id.strip()
    if not cleaned:
        return summary
    return {**summary, "source_id": cleaned}


def _apply_sequence_len(summary: dict, upstream_context: dict) -> dict:
    if not isinstance(summary, dict):
        return summary
    if not isinstance(upstream_context, dict):
        return summary
    if "sequence_len" in summary:
        return summary
    sequence = upstream_context.get("sequence")
    if not isinstance(sequence, list):
        return summary
    return {**summary, "sequence_len": len(sequence)}


def _apply_context_mode(summary: dict, upstream_context: dict) -> dict:
    if not isinstance(summary, dict):
        return summary
    if not isinstance(upstream_context, dict):
        return summary
    if "context_mode" in summary:
        return summary
    mode = upstream_context.get("mode")
    if isinstance(mode, str) and mode in {"aggregate", "sequential"}:
        return {**summary, "context_mode": mode}
    return summary


def _build_partial_messages(summary: dict) -> list[dict]:
    if not isinstance(summary, dict):
        return [{"message": "Synthesizing summary", "progress": 90}]

    partials: list[dict] = []
    palette = summary.get("palette")
    if isinstance(palette, list) and palette:
        preview = ", ".join(str(color) for color in palette[:2])
        partials.append({"message": f"Palette: {preview}…", "progress": 82})

    composition = summary.get("composition_hints")
    if isinstance(composition, list) and composition:
        partials.append({"message": f"Composition: {composition[0]}", "progress": 86})

    pacing = summary.get("pacing_hints")
    if isinstance(pacing, list) and pacing:
        partials.append({"message": f"Pacing: {pacing[0]}", "progress": 90})

    external_insights = summary.get("external_insights")
    if isinstance(external_insights, list) and external_insights:
        first = external_insights[0] if isinstance(external_insights[0], dict) else None
        insight = first.get("summary") if first else None
        if isinstance(insight, str) and insight.strip():
            snippet = insight.strip()
            if len(snippet) > 120:
                snippet = f"{snippet[:117]}..."
            partials.append({"message": f"Insight: {snippet}", "progress": 92})

    if not partials:
        partials.append({"message": "Synthesizing summary", "progress": 90})

    return partials[:3]


async def _mark_run_cancelled(run: CapsuleRun, reason: str) -> None:
    run.status = "cancelled"
    run.summary = {"message": reason}
    run.evidence_refs = []


async def _stream_run_events(run_id: str):
    queue = run_event_hub.subscribe(run_id)
    try:
        while True:
            event = await queue.get()
            payload = {
                "event_id": event.event_id,
                "run_id": event.run_id,
                "type": event.type,
                "seq": event.seq,
                "ts": event.ts,
                "payload": event.payload,
            }
            yield f"id: {event.event_id}\n"
            yield f"event: {event.type}\n"
            yield f"data: {json.dumps(payload)}\n\n"
            if event.type in {"run.completed", "run.failed", "run.cancelled"}:
                break
    finally:
        run_event_hub.unsubscribe(run_id, queue)


async def _execute_capsule_run(
    run_id: uuid.UUID,
    capsule_id: str,
    capsule_version: str,
    inputs: dict,
    params: dict,
    spec_payload: dict,
    warnings: list[str],
    policy: dict,
    is_admin: bool,
    user_id: Optional[str],
    credit_cost: int,
) -> None:
    output_contracts = spec_payload.get("outputContracts") or spec_payload.get("output_contracts") or {}
    pattern_version = spec_payload.get("patternVersion") or spec_payload.get("pattern_version")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(CapsuleRun).where(CapsuleRun.id == run_id))
        run = result.scalars().first()
        if not run:
            return
        try:
            run_id_str = str(run_id)
            if run_event_hub.is_cancelled(run_id_str):
                await _mark_run_cancelled(run, "Cancelled before execution")
                await session.commit()
                await run_event_hub.publish(
                    run_id_str,
                    "run.cancelled",
                    {"status": "cancelled", "message": "Cancelled before execution"},
                )
                run_event_hub.clear_cancelled(run_id_str)
                return
            run.status = "running"
            await session.commit()
            await run_event_hub.publish(
                run_id_str,
                "run.started",
                {"status": "running", "message": "Capsule execution started"},
            )
            await run_event_hub.publish(
                run_id_str,
                "run.progress",
                {"progress": 20, "message": "Initializing execution"},
            )

            from app.capsule_adapter import execute_capsule

            loop = asyncio.get_running_loop()

            def _progress_cb(message: str, progress: int) -> None:
                loop.create_task(
                    run_event_hub.publish(
                        run_id_str,
                        "run.progress",
                        {"progress": progress, "message": message},
                    )
                )

            start_time = time.perf_counter()
            summary, evidence_refs = execute_capsule(
                capsule_id=capsule_id,
                capsule_version=capsule_version,
                inputs=inputs,
                params=params,
                capsule_spec=spec_payload,
                progress_cb=_progress_cb,
            )
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            token_usage, cost_usd = _extract_metrics(summary)
            filtered_refs, evidence_warnings = await _filter_evidence_refs(
                list(evidence_refs or []),
                session,
            )
            if STRICT_EVIDENCE_REFS and evidence_warnings:
                _enforce_evidence_refs(evidence_warnings)
            if STRICT_OUTPUT_CONTRACTS:
                _enforce_output_contracts(summary, output_contracts)
            if warnings:
                summary = {**summary, "input_warnings": warnings}
            summary = _apply_pattern_version(summary, pattern_version)
            summary = _apply_source_id(summary, inputs)
            summary = _apply_sequence_len(summary, run.upstream_context or {})
            summary = _apply_context_mode(summary, run.upstream_context or {})
            if credit_cost > 0:
                summary = {**summary, "credit_cost": credit_cost}

            if run_event_hub.is_cancelled(run_id_str):
                await _mark_run_cancelled(run, "Cancelled during execution")
                await session.commit()
                await run_event_hub.publish(
                    run_id_str,
                    "run.cancelled",
                    {"status": "cancelled", "message": "Cancelled during execution"},
                )
                run_event_hub.clear_cancelled(run_id_str)
                return

            run.status = "done"
            run.summary = summary
            run.evidence_refs = filtered_refs
            run.token_usage = token_usage
            run.latency_ms = latency_ms
            run.cost_usd_est = cost_usd
            await session.commit()

            if user_id and credit_cost > 0:
                try:
                    await deduct_credits(
                        db=session,
                        user_id=user_id,
                        amount=credit_cost,
                        description=f"Capsule run: {capsule_id}@{capsule_version}",
                        capsule_run_id=run.id,
                        meta={
                            "capsule_id": capsule_id,
                            "capsule_version": capsule_version,
                            "run_type": "capsule",
                        },
                    )
                except ValueError:
                    summary = {**summary, "billing_warning": "credit_deduction_failed"}
                    run.summary = summary
                    await session.commit()

            response_summary, response_refs = _apply_policy(
                summary,
                filtered_refs,
                policy,
                is_admin,
            )
            for partial in _build_partial_messages(response_summary):
                await run_event_hub.publish(
                    run_id_str,
                    "run.partial",
                    {
                        "progress": partial.get("progress", 90),
                        "message": partial.get("message", "Working..."),
                    },
                )
            await run_event_hub.publish(
                run_id_str,
                "run.completed",
                {
                    "status": "done",
                    "summary": response_summary,
                    "evidence_refs": response_refs,
                    "version": capsule_version,
                    "token_usage": token_usage,
                    "latency_ms": latency_ms,
                    "cost_usd_est": cost_usd,
                },
            )
            run_event_hub.clear_cancelled(run_id_str)
        except Exception as exc:
            run.status = "failed"
            run.summary = {"error": str(exc)}
            run.evidence_refs = []
            await session.commit()
            await run_event_hub.publish(
                str(run_id),
                "run.failed",
                {"status": "failed", "error": str(exc)},
            )
            run_event_hub.clear_cancelled(str(run_id))


@router.get("/", response_model=List[CapsuleSpecResponse])
async def list_capsules(
    db: AsyncSession = Depends(get_db),
) -> List[CapsuleSpecResponse]:
    result = await db.execute(
        select(CapsuleSpec).where(CapsuleSpec.is_active.is_(True))
    )
    return [_to_response(item) for item in result.scalars().all()]


@router.get("/{capsule_key}", response_model=CapsuleSpecResponse)
async def get_capsule(
    capsule_key: str,
    version: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> CapsuleSpecResponse:
    query = select(CapsuleSpec).where(CapsuleSpec.capsule_key == capsule_key)
    if version:
        query = query.where(CapsuleSpec.version == version)
    query = query.order_by(CapsuleSpec.created_at.desc())
    result = await db.execute(query)
    spec = result.scalars().first()
    if not spec:
        raise HTTPException(status_code=404, detail="Capsule spec not found")
    return _to_response(spec)


@router.get("/{capsule_key}/runs", response_model=List[CapsuleRunHistoryItem])
async def list_capsule_runs(
    capsule_key: str,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> List[CapsuleRunHistoryItem]:
    result = await db.execute(
        select(CapsuleRun)
        .where(CapsuleRun.capsule_key == capsule_key)
        .order_by(CapsuleRun.created_at.desc())
        .limit(limit)
    )
    return [_to_run_history_item(run) for run in result.scalars().all()]


@router.post("/run", response_model=CapsuleRunResponse, status_code=status.HTTP_201_CREATED)
async def run_capsule(
    data: CapsuleRunRequest,
    is_admin: bool = Depends(get_is_admin),
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> CapsuleRunResponse:
    requested_version = (data.capsule_version or "").strip()
    if not requested_version or requested_version == "latest":
        result = await db.execute(
            select(CapsuleSpec)
            .where(
                CapsuleSpec.capsule_key == data.capsule_id,
                CapsuleSpec.is_active.is_(True),
            )
            .order_by(CapsuleSpec.created_at.desc())
        )
        spec = result.scalars().first()
        if not spec:
            raise HTTPException(status_code=404, detail="Capsule spec not found")
        resolved_version = spec.version
    else:
        result = await db.execute(
            select(CapsuleSpec).where(
                CapsuleSpec.capsule_key == data.capsule_id,
                CapsuleSpec.version == requested_version,
            )
        )
        spec = result.scalars().first()
        if not spec:
            raise HTTPException(status_code=404, detail="Capsule spec not found")
        resolved_version = requested_version

    spec_payload = spec.spec or {}
    spec_inputs = spec_payload.get("inputs", {})
    input_contracts = spec_payload.get("inputContracts") or spec_payload.get("input_contracts") or {}
    output_contracts = spec_payload.get("outputContracts") or spec_payload.get("output_contracts") or {}
    pattern_version = spec_payload.get("patternVersion") or spec_payload.get("pattern_version")
    exposed_params = spec_payload.get("exposedParams", {})
    policy = spec_payload.get("policy", {})
    sanitized_inputs, warnings = _validate_inputs(
        spec_inputs,
        data.inputs or {},
        settings.ALLOW_INPUT_FALLBACKS,
        input_contracts,
    )
    sanitized_params = _validate_params(exposed_params, data.params or {}, is_admin)
    await _validate_allowed_types(sanitized_inputs, input_contracts, db, warnings)

    if data.upstream_context is not None and not isinstance(data.upstream_context, dict):
        raise HTTPException(status_code=400, detail="upstream_context must be a dictionary")

    upstream_context = data.upstream_context
    context_mode = input_contracts.get("contextMode") or input_contracts.get("context_mode")
    if isinstance(context_mode, str):
        cleaned_mode = context_mode.strip()
        if cleaned_mode not in {"aggregate", "sequential"}:
            raise HTTPException(status_code=400, detail="contextMode must be aggregate or sequential")
        else:
            context_mode = cleaned_mode
    else:
        context_mode = None
    if upstream_context is None:
        upstream_context, context_warning = await _build_upstream_context(
            data.canvas_id,
            data.node_id,
            db,
            context_mode=context_mode,
        )
        if context_warning and _requires_upstream_context(input_contracts):
            raise HTTPException(status_code=400, detail=f"upstream_context error: {context_warning}")
    if upstream_context is None:
        upstream_context = {}
    _validate_upstream_contract(upstream_context, input_contracts)
    credit_cost = _estimate_capsule_credits(spec_payload)
    cached_result = await db.execute(
        select(CapsuleRun)
        .where(
            CapsuleRun.capsule_key == data.capsule_id,
            CapsuleRun.capsule_version == resolved_version,
            CapsuleRun.params == sanitized_params,
            CapsuleRun.inputs == sanitized_inputs,
            CapsuleRun.upstream_context == upstream_context,
            CapsuleRun.status == "done",
        )
        .order_by(CapsuleRun.created_at.desc())
    )
    cached_run = cached_result.scalars().first()
    if cached_run:
        filtered_refs, evidence_warnings = await _filter_evidence_refs(
            list(cached_run.evidence_refs or []),
            db,
        )
        cached_summary = _apply_pattern_version(cached_run.summary, pattern_version)
        output_warnings = _apply_output_contracts(cached_summary, output_contracts)
        if STRICT_EVIDENCE_REFS and evidence_warnings:
            if filtered_refs != list(cached_run.evidence_refs or []):
                cached_run.evidence_refs = filtered_refs
                await db.commit()
            cached_run = None
        if cached_run and STRICT_OUTPUT_CONTRACTS and output_warnings:
            cached_run = None
        if cached_run:
            if evidence_warnings:
                cached_summary = {**cached_summary, "evidence_warnings": evidence_warnings}
            if output_warnings:
                cached_summary = {**cached_summary, "output_warnings": output_warnings}
            cached_summary = _apply_source_id(cached_summary, sanitized_inputs)
            cached_summary = _apply_sequence_len(cached_summary, cached_run.upstream_context or {})
            cached_summary = _apply_context_mode(cached_summary, cached_run.upstream_context or {})
            if credit_cost > 0:
                cached_summary = {**cached_summary, "credit_cost": credit_cost}
            summary, evidence_refs = _apply_policy(
                cached_summary,
                filtered_refs,
                policy,
                is_admin,
            )
            return CapsuleRunResponse(
                run_id=str(cached_run.id),
                status="cached",
                summary=summary,
                evidence_refs=evidence_refs,
                version=cached_run.capsule_version,
                token_usage=cached_run.token_usage,
                latency_ms=cached_run.latency_ms,
                cost_usd_est=cached_run.cost_usd_est,
                cached=True,
            )

    if user_id and credit_cost > 0:
        user_credits = await get_or_create_user_credits(db, user_id)
        if user_credits.balance < credit_cost:
            raise HTTPException(status_code=402, detail="Insufficient credits")

    if data.async_mode:
        run = CapsuleRun(
            capsule_key=data.capsule_id,
            capsule_version=resolved_version,
            status="queued",
            inputs=sanitized_inputs,
            params=sanitized_params,
            upstream_context=upstream_context,
            summary={},
            evidence_refs=[],
            token_usage={},
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)

        await run_event_hub.publish(
            str(run.id),
            "run.queued",
            {
                "status": "queued",
                "capsule_id": data.capsule_id,
                "version": resolved_version,
            },
        )

        asyncio.create_task(
            _execute_capsule_run(
                run.id,
                data.capsule_id,
                resolved_version,
                sanitized_inputs,
                sanitized_params,
                spec_payload,
                warnings,
                policy,
                is_admin,
                user_id,
                credit_cost,
            )
        )
        return CapsuleRunResponse(
            run_id=str(run.id),
            status=run.status,
            summary={},
            evidence_refs=[],
            version=run.capsule_version,
            token_usage=run.token_usage,
            latency_ms=run.latency_ms,
            cost_usd_est=run.cost_usd_est,
            cached=False,
        )

    # Use the capsule adapter for real style generation
    from app.capsule_adapter import execute_capsule
    
    start_time = time.perf_counter()
    summary, evidence_refs = execute_capsule(
        capsule_id=data.capsule_id,
        capsule_version=resolved_version,
        inputs=sanitized_inputs,
        params=sanitized_params,
        capsule_spec=spec_payload,
    )
    latency_ms = int((time.perf_counter() - start_time) * 1000)
    token_usage, cost_usd = _extract_metrics(summary)
    filtered_refs, evidence_warnings = await _filter_evidence_refs(
        list(evidence_refs or []),
        db,
    )
    if STRICT_EVIDENCE_REFS and evidence_warnings:
        _enforce_evidence_refs(evidence_warnings)
    if STRICT_OUTPUT_CONTRACTS:
        _enforce_output_contracts(summary, output_contracts)
    if warnings:
        summary = {**summary, "input_warnings": warnings}

    summary = _apply_pattern_version(summary, pattern_version)
    summary = _apply_source_id(summary, sanitized_inputs)
    summary = _apply_sequence_len(summary, upstream_context)
    summary = _apply_context_mode(summary, upstream_context)
    if credit_cost > 0:
        summary = {**summary, "credit_cost": credit_cost}

    response_summary, response_refs = _apply_policy(summary, filtered_refs, policy, is_admin)
    
    run = CapsuleRun(
        capsule_key=data.capsule_id,
        capsule_version=resolved_version,
        status="done",
        inputs=sanitized_inputs,
        params=sanitized_params,
        upstream_context=upstream_context,
        summary=summary,
        evidence_refs=filtered_refs,
        token_usage=token_usage,
        latency_ms=latency_ms,
        cost_usd_est=cost_usd,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    if user_id and credit_cost > 0:
        try:
            await deduct_credits(
                db=db,
                user_id=user_id,
                amount=credit_cost,
                description=f"Capsule run: {data.capsule_id}@{resolved_version}",
                capsule_run_id=run.id,
                meta={
                    "capsule_id": data.capsule_id,
                    "capsule_version": resolved_version,
                    "run_type": "capsule",
                },
            )
        except ValueError:
            summary = {**summary, "billing_warning": "credit_deduction_failed"}
            run.summary = summary
            await db.commit()

    return CapsuleRunResponse(
        run_id=str(run.id),
        status=run.status,
        summary=response_summary,
        evidence_refs=response_refs,
        version=run.capsule_version,
        token_usage=run.token_usage,
        latency_ms=run.latency_ms,
        cost_usd_est=run.cost_usd_est,
        cached=False,
    )


@router.get("/run/{run_id}", response_model=CapsuleRunStatusResponse)
async def get_capsule_run(
    run_id: str,
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> CapsuleRunStatusResponse:
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid run id") from exc

    result = await db.execute(select(CapsuleRun).where(CapsuleRun.id == run_uuid))
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="Capsule run not found")

    spec_result = await db.execute(
        select(CapsuleSpec).where(
            CapsuleSpec.capsule_key == run.capsule_key,
            CapsuleSpec.version == run.capsule_version,
        )
    )
    spec = spec_result.scalars().first()
    spec_payload = (spec.spec or {}) if spec else {}
    policy = spec_payload.get("policy", {})
    output_contracts = spec_payload.get("outputContracts") or spec_payload.get("output_contracts") or {}
    filtered_refs, _ = await _filter_evidence_refs(list(run.evidence_refs or []), db)
    summary = _apply_pattern_version(
        run.summary,
        spec_payload.get("patternVersion") or spec_payload.get("pattern_version"),
    )
    summary = _apply_source_id(summary, run.inputs or {})
    output_warnings = _apply_output_contracts(summary, output_contracts)
    if output_warnings:
        summary = {**summary, "output_warnings": output_warnings}
    summary, evidence_refs = _apply_policy(summary, filtered_refs, policy, is_admin)

    return CapsuleRunStatusResponse(
        run_id=str(run.id),
        capsule_id=run.capsule_key,
        status=run.status,
        summary=summary,
        evidence_refs=evidence_refs,
        version=run.capsule_version,
        token_usage=run.token_usage,
        latency_ms=run.latency_ms,
        cost_usd_est=run.cost_usd_est,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


@router.post("/run/{run_id}/cancel", response_model=CapsuleRunStatusResponse)
async def cancel_capsule_run(
    run_id: str,
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> CapsuleRunStatusResponse:
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid run id") from exc

    result = await db.execute(select(CapsuleRun).where(CapsuleRun.id == run_uuid))
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="Capsule run not found")

    spec_result = await db.execute(
        select(CapsuleSpec).where(
            CapsuleSpec.capsule_key == run.capsule_key,
            CapsuleSpec.version == run.capsule_version,
        )
    )
    spec = spec_result.scalars().first()
    policy = (spec.spec or {}).get("policy", {}) if spec else {}
    pattern_version = (
        (spec.spec or {}).get("patternVersion") or (spec.spec or {}).get("pattern_version")
        if spec
        else None
    )

    if run.status in {"done", "failed", "cancelled"}:
        filtered_refs, _ = await _filter_evidence_refs(list(run.evidence_refs or []), db)
        summary = _apply_pattern_version(run.summary, pattern_version)
        summary = _apply_source_id(summary, run.inputs or {})
        summary, evidence_refs = _apply_policy(summary, filtered_refs, policy, is_admin)
        return CapsuleRunStatusResponse(
            run_id=str(run.id),
            capsule_id=run.capsule_key,
            status=run.status,
            summary=summary,
            evidence_refs=evidence_refs,
            version=run.capsule_version,
            token_usage=run.token_usage,
            latency_ms=run.latency_ms,
            cost_usd_est=run.cost_usd_est,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    run_event_hub.cancel(str(run.id))
    await _mark_run_cancelled(run, "Cancelled by user")
    await db.commit()
    await run_event_hub.publish(
        str(run.id),
        "run.cancelled",
        {"status": "cancelled", "message": "Cancelled by user"},
    )

    filtered_refs, _ = await _filter_evidence_refs(list(run.evidence_refs or []), db)
    summary = _apply_pattern_version(run.summary, pattern_version)
    summary = _apply_source_id(summary, run.inputs or {})
    summary, evidence_refs = _apply_policy(summary, filtered_refs, policy, is_admin)
    return CapsuleRunStatusResponse(
        run_id=str(run.id),
        capsule_id=run.capsule_key,
        status=run.status,
        summary=summary,
        evidence_refs=evidence_refs,
        version=run.capsule_version,
        token_usage=run.token_usage,
        latency_ms=run.latency_ms,
        cost_usd_est=run.cost_usd_est,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


@router.get("/run/{run_id}/stream")
async def stream_capsule_run(
    run_id: str,
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid run id") from exc

    result = await db.execute(select(CapsuleRun).where(CapsuleRun.id == run_uuid))
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="Capsule run not found")

    spec_result = await db.execute(
        select(CapsuleSpec).where(
            CapsuleSpec.capsule_key == run.capsule_key,
            CapsuleSpec.version == run.capsule_version,
        )
    )
    spec = spec_result.scalars().first()
    policy = (spec.spec or {}).get("policy", {}) if spec else {}
    pattern_version = (
        (spec.spec or {}).get("patternVersion") or (spec.spec or {}).get("pattern_version")
        if spec
        else None
    )

    if run.status in {"done", "failed", "cancelled"}:
        filtered_refs, _ = await _filter_evidence_refs(list(run.evidence_refs or []), db)
        summary = _apply_pattern_version(run.summary, pattern_version)
        summary = _apply_source_id(summary, run.inputs or {})
        summary, evidence_refs = _apply_policy(summary, filtered_refs, policy, is_admin)
        if run.status == "done":
            event_type = "run.completed"
        elif run.status == "failed":
            event_type = "run.failed"
        else:
            event_type = "run.cancelled"
        payload = {
            "status": run.status,
            "summary": summary,
            "evidence_refs": evidence_refs,
            "version": run.capsule_version,
            "token_usage": run.token_usage,
            "latency_ms": run.latency_ms,
            "cost_usd_est": run.cost_usd_est,
        }

        async def _single_event():
            data = {
                "event_id": f"{run_id}:final",
                "run_id": str(run.id),
                "type": event_type,
                "seq": 0,
                "ts": f"{datetime.utcnow().isoformat()}Z",
                "payload": payload,
            }
            yield f"id: {data['event_id']}\n"
            yield f"event: {event_type}\n"
            yield f"data: {json.dumps(data)}\n\n"

        return StreamingResponse(
            _single_event(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return StreamingResponse(
        _stream_run_events(str(run.id)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


class ScenePreview(BaseModel):
    scene_number: int
    composition: str
    dominant_color: str
    accent_color: str
    pacing_note: str
    duration_hint: str


class StoryboardPreviewResponse(BaseModel):
    run_id: str
    capsule_id: str
    scenes: List[ScenePreview]
    palette: List[str]
    style_vector: List[float]
    pattern_version: Optional[str] = None
    source_id: Optional[str] = None
    sequence_len: Optional[int] = None
    context_mode: Optional[str] = None
    credit_cost: Optional[int] = None
    evidence_refs: List[str]
    evidence_warnings: List[str] = []


@router.get("/{capsule_key}/runs/{run_id}/preview", response_model=StoryboardPreviewResponse)
async def get_storyboard_preview(
    capsule_key: str,
    run_id: str,
    scene_count: int = 3,
    db: AsyncSession = Depends(get_db),
) -> StoryboardPreviewResponse:
    """Generate a storyboard preview from a capsule run."""
    from app.capsule_adapter import generate_storyboard_preview

    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid run id") from exc

    result = await db.execute(select(CapsuleRun).where(CapsuleRun.id == run_uuid))
    run = result.scalars().first()

    if not run:
        raise HTTPException(status_code=404, detail="Capsule run not found")

    if run.capsule_key != capsule_key:
        raise HTTPException(status_code=400, detail="Run does not match capsule key")

    scenes_data = generate_storyboard_preview(run.summary, scene_count)
    scenes = [ScenePreview(**s) for s in scenes_data]

    filtered_refs, evidence_warnings = await _filter_evidence_refs(
        list(run.evidence_refs or []),
        db,
    )
    return StoryboardPreviewResponse(
        run_id=str(run.id),
        capsule_id=run.capsule_key,
        scenes=scenes,
        palette=run.summary.get("palette", []),
        style_vector=run.summary.get("style_vector", []),
        pattern_version=run.summary.get("pattern_version") or run.summary.get("patternVersion"),
        source_id=run.summary.get("source_id") or run.inputs.get("source_id") or run.inputs.get("sourceId"),
        sequence_len=run.summary.get("sequence_len"),
        context_mode=run.summary.get("context_mode") or run.upstream_context.get("mode"),
        credit_cost=run.summary.get("credit_cost") if isinstance(run.summary, dict) else None,
        evidence_refs=filtered_refs,
        evidence_warnings=evidence_warnings,
    )
