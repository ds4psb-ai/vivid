"""Generation run endpoints."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_user_id
from app.database import AsyncSessionLocal, get_db
from app.models import Canvas, GenerationRun
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

    class Config:
        from_attributes = True


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


async def _execute_run(run_id: uuid.UUID, canvas_id: uuid.UUID) -> None:
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
            spec = compute_graph(graph.get("nodes", []), graph.get("edges", []))
            run.spec = spec
            run.outputs = {
                "previewUrl": None,
                "videoUrl": None,
                "audioUrl": None,
                "metadataUrl": None,
            }
            run.status = "done"
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

    asyncio.create_task(_execute_run(run.id, canvas_uuid))
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
