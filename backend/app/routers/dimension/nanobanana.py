"""Nanobanana Editor Router.

Converts Nanobanana Editor state (lighting/camera presets) to ShotContract.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.dimension_adapter import DimensionCapsuleId
from app.routers.dimension._base import (
    _execute_dimension_tool,
    get_byok_key,
    DimensionResponse,
)


router = APIRouter(prefix="/nanobanana", tags=["nanobanana"])


class ConvertRequest(BaseModel):
    """Nanobanana Editor state → ShotContract request."""
    editor_state: Dict[str, Any] = Field(
        ...,
        description="Nanobanana editor state with lightingPreset, lightingDirection, cameraDistance, cameraLens, cubeRotation, selectedRatio"
    )
    shot_id: str = Field(..., description="Shot ID (e.g., seq-01-shot-001)")
    sequence_id: str = Field(default="seq-01", description="Sequence ID")
    scene_id: str = Field(default="scene-01", description="Scene ID")
    model: str = Field(default="gemini-3-flash-preview", description="Model (unused - no LLM call)")


@router.post("/convert", response_model=DimensionResponse)
async def convert_nanobanana_to_shot(
    request: ConvertRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
):
    """Convert Nanobanana Editor state to ShotContract.
    
    This is a lightweight transformation that doesn't call LLM.
    Preserves camera angle/direction in pose_motion field.
    Uses full lighting descriptions instead of just preset keys.
    Credit cost is minimal (10 credits per run).
    
    Returns:
        DimensionResponse with shot_contract and evidence_refs
    """
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.NANOBANANA_CONVERT,
        tool_key="nanobanana.convert",
        inputs={
            "editor_state": request.editor_state,
            "shot_id": request.shot_id,
            "sequence_id": request.sequence_id,
            "scene_id": request.scene_id,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"shot_id": request.shot_id},
    )
