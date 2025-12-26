"""Generation run endpoints."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_user_id
from app.credit_service import deduct_credits, get_or_create_user_credits
from app.database import AsyncSessionLocal, get_db
from app.models import Canvas, GenerationRun
from app.affiliate_service import activate_referrals_for_user
from app.spec_engine import compute_graph

router = APIRouter()


class RunCreate(BaseModel):
    canvas_id: str


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
            spec = compute_graph(
                graph.get("nodes", []),
                graph.get("edges", []),
                graph.get("meta") if isinstance(graph, dict) else None,
            )
            if isinstance(spec, dict):
                spec = {**spec, "credit_cost": credit_cost}
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
                        meta={"run_type": "generation", "canvas_id": str(canvas_id)},
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
