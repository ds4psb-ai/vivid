"""Generation run endpoints."""
from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_user_id
from app.credit_service import deduct_credits, get_or_create_user_credits
from app.database import AsyncSessionLocal, get_db
from app.models import Canvas, GenerationRun
from app.affiliate_service import activate_referrals_for_user
from app.spec_engine import compute_graph
from app.template_learning import (
    AUTO_PROMOTE_TEMPLATES,
    compute_reward,
    extract_capsule_params,
    extract_evidence_refs,
    extract_template_origin,
    maybe_promote_template_version,
    record_learning_run,
)

router = APIRouter()


class RunCreate(BaseModel):
    canvas_id: str


class ShotFeedback(BaseModel):
    shot_id: str
    rating: Optional[int] = None
    note: Optional[str] = None
    tags: List[str] = []


class RunFeedbackRequest(BaseModel):
    shots: List[ShotFeedback] = []
    overall_note: Optional[str] = None


class RunResponse(BaseModel):
    id: str
    canvas_id: str
    spec: dict
    status: str
    outputs: dict
    owner_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


def _to_response(run: GenerationRun) -> RunResponse:
    return RunResponse(
        id=str(run.id),
        canvas_id=str(run.canvas_id),
        spec=run.spec,
        status=run.status,
        outputs=run.outputs,
        owner_id=run.owner_id,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


@router.get("/", response_model=List[RunResponse])
async def list_runs(
    canvas_id: Optional[str] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[RunResponse]:
    query = select(GenerationRun).order_by(GenerationRun.created_at.desc()).limit(limit)

    if canvas_id:
        try:
            canvas_uuid = uuid.UUID(canvas_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid canvas ID format") from exc
        canvas_result = await db.execute(select(Canvas).where(Canvas.id == canvas_uuid))
        canvas = canvas_result.scalar_one_or_none()
        if not canvas:
            raise HTTPException(status_code=404, detail="Canvas not found")
        if canvas.owner_id is not None:
            if not user_id or canvas.owner_id != user_id:
                raise HTTPException(status_code=403, detail="Not authorized to access this canvas")
        query = query.where(GenerationRun.canvas_id == canvas_uuid)
    elif not user_id:
        return []
    else:
        query = query.where(GenerationRun.owner_id == user_id)

    result = await db.execute(query)
    runs = result.scalars().all()
    return [_to_response(run) for run in runs]


def _estimate_generation_credits(spec: dict) -> int:
    if not isinstance(spec, dict):
        return 50
    quality = str(spec.get("render_quality", "preview")).lower()
    if quality in {"final", "high"}:
        return 120
    if quality in {"preview", "draft"}:
        return 20
    return 50


def _estimate_generation_credits_from_graph(graph: dict) -> int:
    if not isinstance(graph, dict):
        return _estimate_generation_credits({})
    nodes = graph.get("nodes", [])
    quality = "preview"
    if isinstance(nodes, list):
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if node.get("type") != "output":
                continue
            data = node.get("data", {}) if isinstance(node.get("data"), dict) else {}
            raw_quality = data.get("quality") or data.get("render_quality")
            if isinstance(raw_quality, str) and raw_quality.strip():
                quality = raw_quality.strip()
                break
    return _estimate_generation_credits({"render_quality": quality})


def _format_script(beat_sheet: list) -> str:
    if not isinstance(beat_sheet, list):
        return ""
    lines = []
    for idx, beat in enumerate(beat_sheet, start=1):
        if isinstance(beat, str):
            label = f"Beat {idx}"
            note = beat
        elif isinstance(beat, dict):
            label = str(beat.get("beat") or f"Beat {idx}")
            note = str(beat.get("note") or "")
        else:
            continue
        if note:
            lines.append(f"{label}: {note}")
        else:
            lines.append(label)
    return "\n".join(lines)


async def _execute_run(
    run_id: uuid.UUID,
    canvas_id: uuid.UUID,
    user_id: Optional[str],
    credit_cost: int,
) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(GenerationRun).where(GenerationRun.id == run_id)
        )
        run = result.scalar_one_or_none()
        if not run:
            return
        try:
            run.status = "running"
            await session.commit()

            canvas_result = await session.execute(
                select(Canvas).where(Canvas.id == canvas_id)
            )
            canvas = canvas_result.scalar_one_or_none()
            if not canvas:
                run.status = "failed"
                run.outputs = {"error": "Canvas not found"}
                await session.commit()
                return

            graph = canvas.graph_data or {"nodes": [], "edges": []}
            start_time = time.perf_counter()
            spec = compute_graph(
                graph.get("nodes", []),
                graph.get("edges", []),
                graph.get("meta") if isinstance(graph, dict) else None,
            )
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            if isinstance(spec, dict):
                spec = {**spec, "credit_cost": credit_cost, "latency_ms": latency_ms}
            run.spec = spec
            beat_sheet = spec.get("beat_sheet") if isinstance(spec, dict) else []
            storyboard = spec.get("storyboard") if isinstance(spec, dict) else []
            shot_contracts = spec.get("shot_contracts") if isinstance(spec, dict) else []
            prompt_contracts = spec.get("prompt_contracts") if isinstance(spec, dict) else []
            prompt_contract_version = (
                spec.get("prompt_contract_version") if isinstance(spec, dict) else None
            )
            production_contract = spec.get("production_contract") if isinstance(spec, dict) else None
            script_text = _format_script(beat_sheet)
            run.outputs = {
                "previewUrl": None,
                "videoUrl": None,
                "audioUrl": None,
                "metadataUrl": None,
                "script_text": script_text,
                "storyboard_cards": storyboard if isinstance(storyboard, list) else [],
                "shot_contracts": shot_contracts if isinstance(shot_contracts, list) else [],
                "prompt_contracts": prompt_contracts if isinstance(prompt_contracts, list) else [],
                "prompt_contract_version": (
                    prompt_contract_version if isinstance(prompt_contract_version, str) else None
                ),
                "production_contract": production_contract if isinstance(production_contract, dict) else None,
                "metrics": {"latency_ms": latency_ms},
            }
            run.status = "done"
            await session.commit()

            if user_id:
                try:
                    await activate_referrals_for_user(session, user_id)
                except Exception:
                    pass

            if user_id and credit_cost > 0:
                try:
                    await deduct_credits(
                        db=session,
                        user_id=user_id,
                        amount=credit_cost,
                        description=f"Generation run: {canvas_id}",
                        capsule_run_id=None,
                        meta={
                            "run_type": "generation",
                            "canvas_id": str(canvas_id),
                            "credit_cost": credit_cost,
                            "latency_ms": latency_ms,
                        },
                    )
                except ValueError:
                    run.outputs = {
                        **run.outputs,
                        "billing_warning": "credit_deduction_failed",
                    }
                    await session.commit()
        except Exception as exc:
            run.status = "failed"
            run.outputs = {"error": str(exc)}
            await session.commit()


@router.post("/", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def create_run(
    data: RunCreate,
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    try:
        canvas_uuid = uuid.UUID(data.canvas_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid canvas ID format") from exc

    result = await db.execute(select(Canvas).where(Canvas.id == canvas_uuid))
    canvas = result.scalar_one_or_none()
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    if not canvas.is_public and canvas.owner_id is not None:
        if not user_id or canvas.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to run this canvas")

    graph = canvas.graph_data or {"nodes": [], "edges": []}
    credit_cost = _estimate_generation_credits_from_graph(graph)
    billing_user_id = user_id or canvas.owner_id
    if billing_user_id and credit_cost > 0:
        user_credits = await get_or_create_user_credits(db, billing_user_id)
        if user_credits.balance < credit_cost:
            raise HTTPException(status_code=402, detail="Insufficient credits")

    run = GenerationRun(
        canvas_id=canvas_uuid,
        status="queued",
        spec={},
        outputs={},
        owner_id=canvas.owner_id or user_id,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    asyncio.create_task(_execute_run(run.id, canvas_uuid, billing_user_id, credit_cost))
    return _to_response(run)


@router.post("/{run_id}/feedback", response_model=RunResponse)
async def update_run_feedback(
    run_id: str,
    data: RunFeedbackRequest,
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid run id") from exc

    result = await db.execute(select(GenerationRun).where(GenerationRun.id == run_uuid))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.owner_id and user_id and run.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this run")

    outputs = run.outputs if isinstance(run.outputs, dict) else {}
    existing = outputs.get("shot_feedback")
    feedback_map = {}
    if isinstance(existing, list):
        for item in existing:
            if isinstance(item, dict) and item.get("shot_id"):
                feedback_map[str(item["shot_id"])] = dict(item)

    for shot in data.shots or []:
        record = feedback_map.get(shot.shot_id, {})
        record.update(
            {
                "shot_id": shot.shot_id,
                "rating": shot.rating,
                "note": shot.note,
                "tags": shot.tags or [],
                "updated_at": datetime.utcnow().isoformat() + "Z",
            }
        )
        feedback_map[shot.shot_id] = record

    outputs["shot_feedback"] = list(feedback_map.values())
    if isinstance(data.overall_note, str) and data.overall_note.strip():
        outputs["overall_note"] = data.overall_note.strip()
    outputs["feedback_updated_at"] = datetime.utcnow().isoformat() + "Z"

    canvas_result = await db.execute(select(Canvas).where(Canvas.id == run.canvas_id))
    canvas = canvas_result.scalar_one_or_none()
    if canvas and isinstance(canvas.graph_data, dict):
        template_id, template_version, _ = extract_template_origin(canvas.graph_data)
        if template_id and template_version:
            try:
                template_uuid = uuid.UUID(str(template_id))
            except ValueError:
                template_uuid = None
            if template_uuid:
                evidence_refs = extract_evidence_refs(canvas.graph_data)
                capsule_params = extract_capsule_params(canvas.graph_data)
                shot_contracts = outputs.get("shot_contracts")
                shot_count = len(shot_contracts) if isinstance(shot_contracts, list) else 0
                credit_cost = None
                if isinstance(run.spec, dict):
                    raw_cost = run.spec.get("credit_cost")
                    if isinstance(raw_cost, int):
                        credit_cost = raw_cost
                latency_ms = None
                if isinstance(run.outputs, dict):
                    metrics = run.outputs.get("metrics")
                    if isinstance(metrics, dict):
                        metric_latency = metrics.get("latency_ms")
                        if isinstance(metric_latency, int):
                            latency_ms = metric_latency
                feedback_payload = {
                    "shots": outputs.get("shot_feedback", []),
                    "overall_note": outputs.get("overall_note"),
                }
                reward = compute_reward(
                    feedback_shots=feedback_payload["shots"],
                    evidence_refs=evidence_refs,
                    credit_cost=credit_cost,
                    latency_ms=latency_ms,
                    shot_count=shot_count,
                )
                outputs["learning_reward"] = reward
                await record_learning_run(
                    db,
                    template_id=template_uuid,
                    template_version=template_version,
                    canvas_id=run.canvas_id,
                    run_id=run.id,
                    reward=reward,
                    evidence_refs=evidence_refs,
                    feedback=feedback_payload,
                    capsule_params=capsule_params,
                )
                await db.flush()
                if AUTO_PROMOTE_TEMPLATES:
                    promotion = await maybe_promote_template_version(
                        db,
                        template_id=template_uuid,
                        template_version=template_version,
                        canvas_graph=canvas.graph_data,
                    )
                    if promotion:
                        outputs["template_promotion"] = promotion

    run.outputs = outputs
    await db.commit()
    await db.refresh(run)
    return _to_response(run)


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid run ID format") from exc

    result = await db.execute(select(GenerationRun).where(GenerationRun.id == run_uuid))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.owner_id is not None:
        if not user_id or run.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this run")
    return _to_response(run)


class VideoGenerateRequest(BaseModel):
    """Request for video generation from storyboard."""
    provider: str = "veo"  # veo, kling, mock
    shot_indices: Optional[List[int]] = None  # Optional: specific shots to generate


class VideoGenerateResponse(BaseModel):
    """Response from video generation."""
    run_id: str
    status: str
    shots_generated: int
    shots_total: int
    results: List[dict]
    metrics: dict


@router.post("/{run_id}/video", response_model=VideoGenerateResponse)
async def generate_video(
    run_id: str,
    data: VideoGenerateRequest,
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> VideoGenerateResponse:
    """Generate video from run's storyboard cards using Veo 3.1 or other providers."""
    from app.generation_client import (
        GenProvider,
        run_generation_pipeline,
    )
    
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid run ID format") from exc

    result = await db.execute(select(GenerationRun).where(GenerationRun.id == run_uuid))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.owner_id is not None:
        if not user_id or run.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this run")
    
    # Get storyboard cards from run outputs
    outputs = run.outputs if isinstance(run.outputs, dict) else {}
    storyboard_cards = outputs.get("storyboard_cards", [])
    
    if not storyboard_cards:
        storyboard_cards = outputs.get("storyboard", [])
    if not storyboard_cards:
        raise HTTPException(
            status_code=400,
            detail="No storyboard cards found. Run generation first."
        )
    
    # Filter specific shots if requested
    if data.shot_indices:
        storyboard_cards = [
            card for i, card in enumerate(storyboard_cards) 
            if i in data.shot_indices
        ]
    
    # Map provider string to enum
    try:
        provider = GenProvider(data.provider.lower())
    except ValueError:
        provider = GenProvider.MOCK
    
    # Run generation pipeline
    gen_results, metrics = await run_generation_pipeline(
        storyboard_cards,
        provider=provider,
        sequence_id=f"seq-{run_id[:8]}",
        scene_id=f"scene-{run_id[:8]}",
    )
    
    # Update run outputs with video results
    video_outputs = [
        {
            "shot_id": r.shot_id,
            "status": r.status,
            "video_url": r.output_url,
            "iteration": r.iteration,
            "latency_ms": r.latency_ms,
            "model_version": r.model_version,
            "error": r.error,
        }
        for r in gen_results
    ]
    
    outputs["video_results"] = video_outputs
    outputs["video_metrics"] = metrics
    outputs["video_generated_at"] = datetime.utcnow().isoformat() + "Z"
    run.outputs = outputs
    await db.commit()
    
    return VideoGenerateResponse(
        run_id=str(run.id),
        status="done" if metrics.get("success_rate", 0) == 1.0 else "partial",
        shots_generated=metrics.get("success_count", 0),
        shots_total=metrics.get("total_shots", 0),
        results=video_outputs,
        metrics=metrics,
    )
