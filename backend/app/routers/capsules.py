"""Capsule spec and execution endpoints."""
import asyncio
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_is_admin
from app.config import settings
from app.database import AsyncSessionLocal, get_db
from app.models import CapsuleSpec, CapsuleRun

router = APIRouter()

DEFAULT_INPUT_VALUES = {
    "emotion_curve": [0.3, 0.5, 0.7, 0.9, 0.6],
    "scene_summary": "",
    "duration_sec": 60,
}


class CapsuleSpecResponse(BaseModel):
    id: str
    capsule_key: str
    version: str
    display_name: str
    description: str
    spec: dict
    is_active: bool

    class Config:
        from_attributes = True


class CapsuleRunRequest(BaseModel):
    canvas_id: Optional[str] = None
    node_id: Optional[str] = None
    capsule_id: str
    capsule_version: str
    inputs: dict
    params: dict
    async_mode: bool = False


class CapsuleRunResponse(BaseModel):
    run_id: str
    status: str
    summary: dict
    evidence_refs: List[str]
    version: str
    cached: bool = False


class CapsuleRunHistoryItem(BaseModel):
    run_id: str
    status: str
    summary: dict
    evidence_refs: List[str]
    version: str
    created_at: datetime


class CapsuleRunStatusResponse(BaseModel):
    run_id: str
    capsule_id: str
    status: str
    summary: dict
    evidence_refs: List[str]
    version: str
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


def _validate_inputs(
    spec_inputs: dict,
    inputs: dict,
    allow_fallbacks: bool,
) -> tuple[dict, list[str]]:
    if not isinstance(inputs, dict):
        raise HTTPException(status_code=400, detail="inputs must be a dictionary")

    sanitized: dict = {}
    warnings: list[str] = []
    for key, meta in (spec_inputs or {}).items():
        type_name = (meta or {}).get("type")
        required = bool((meta or {}).get("required"))
        if key not in inputs:
            if required:
                if allow_fallbacks:
                    fallback = DEFAULT_INPUT_VALUES.get(key, _default_for_type(type_name))
                    sanitized[key] = fallback
                    warnings.append(f"fallback:{key}")
                else:
                    raise HTTPException(status_code=400, detail=f"Missing required input: {key}")
            continue
        value = inputs.get(key)
        if not _validate_input_type(value, type_name):
            raise HTTPException(status_code=400, detail=f"Invalid input type for {key}")
        sanitized[key] = value

    return sanitized, warnings


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


async def _execute_capsule_run(
    run_id: uuid.UUID,
    capsule_id: str,
    capsule_version: str,
    inputs: dict,
    params: dict,
    spec_payload: dict,
    warnings: list[str],
) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(CapsuleRun).where(CapsuleRun.id == run_id))
        run = result.scalars().first()
        if not run:
            return
        try:
            run.status = "running"
            await session.commit()

            from app.capsule_adapter import execute_capsule

            summary, evidence_refs = execute_capsule(
                capsule_id=capsule_id,
                capsule_version=capsule_version,
                inputs=inputs,
                params=params,
                capsule_spec=spec_payload,
            )
            if warnings:
                summary = {**summary, "input_warnings": warnings}

            run.status = "done"
            run.summary = summary
            run.evidence_refs = evidence_refs
            await session.commit()
        except Exception as exc:
            run.status = "failed"
            run.summary = {"error": str(exc)}
            run.evidence_refs = []
            await session.commit()


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
    exposed_params = spec_payload.get("exposedParams", {})
    policy = spec_payload.get("policy", {})
    sanitized_inputs, warnings = _validate_inputs(
        spec_inputs,
        data.inputs or {},
        settings.ALLOW_INPUT_FALLBACKS,
    )
    sanitized_params = _validate_params(exposed_params, data.params or {}, is_admin)

    cached_result = await db.execute(
        select(CapsuleRun)
        .where(
            CapsuleRun.capsule_key == data.capsule_id,
            CapsuleRun.capsule_version == resolved_version,
            CapsuleRun.params == sanitized_params,
            CapsuleRun.inputs == sanitized_inputs,
            CapsuleRun.status == "done",
        )
        .order_by(CapsuleRun.created_at.desc())
    )
    cached_run = cached_result.scalars().first()
    if cached_run:
        summary, evidence_refs = _apply_policy(
            cached_run.summary,
            cached_run.evidence_refs,
            policy,
            is_admin,
        )
        return CapsuleRunResponse(
            run_id=str(cached_run.id),
            status="cached",
            summary=summary,
            evidence_refs=evidence_refs,
            version=cached_run.capsule_version,
            cached=True,
        )

    if data.async_mode:
        run = CapsuleRun(
            capsule_key=data.capsule_id,
            capsule_version=resolved_version,
            status="queued",
            inputs=sanitized_inputs,
            params=sanitized_params,
            summary={},
            evidence_refs=[],
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)

        asyncio.create_task(
            _execute_capsule_run(
                run.id,
                data.capsule_id,
                resolved_version,
                sanitized_inputs,
                sanitized_params,
                spec_payload,
                warnings,
            )
        )
        return CapsuleRunResponse(
            run_id=str(run.id),
            status=run.status,
            summary={},
            evidence_refs=[],
            version=run.capsule_version,
            cached=False,
        )

    # Use the capsule adapter for real style generation
    from app.capsule_adapter import execute_capsule
    
    summary, evidence_refs = execute_capsule(
        capsule_id=data.capsule_id,
        capsule_version=resolved_version,
        inputs=sanitized_inputs,
        params=sanitized_params,
        capsule_spec=spec_payload,
    )
    if warnings:
        summary = {**summary, "input_warnings": warnings}

    response_summary, response_refs = _apply_policy(summary, evidence_refs, policy, is_admin)
    
    run = CapsuleRun(
        capsule_key=data.capsule_id,
        capsule_version=resolved_version,
        status="done",
        inputs=sanitized_inputs,
        params=sanitized_params,
        summary=summary,
        evidence_refs=evidence_refs,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    return CapsuleRunResponse(
        run_id=str(run.id),
        status=run.status,
        summary=response_summary,
        evidence_refs=response_refs,
        version=run.capsule_version,
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
    policy = (spec.spec or {}).get("policy", {}) if spec else {}
    summary, evidence_refs = _apply_policy(run.summary, run.evidence_refs, policy, is_admin)

    return CapsuleRunStatusResponse(
        run_id=str(run.id),
        capsule_id=run.capsule_key,
        status=run.status,
        summary=summary,
        evidence_refs=evidence_refs,
        version=run.capsule_version,
        created_at=run.created_at,
        updated_at=run.updated_at,
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
    evidence_refs: List[str]


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

    return StoryboardPreviewResponse(
        run_id=str(run.id),
        capsule_id=run.capsule_key,
        scenes=scenes,
        palette=run.summary.get("palette", []),
        style_vector=run.summary.get("style_vector", []),
        evidence_refs=run.evidence_refs,
    )
