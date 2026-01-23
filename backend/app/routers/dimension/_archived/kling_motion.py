"""
Kling Motion Transfer Endpoints - Character Animation.

- POST /kling/motion-transfer: Transfer motion from video to character image
- GET /kling/motion/{task_id}/status: Get motion transfer status

2026 Best Practices:
- Kling 2.6 Motion Control: 30s continuous motion (video orientation)
- Dance/action sequence generation
- Hand/finger precision control
- Audio preservation from reference video
"""
from __future__ import annotations

import json
import logging
import uuid as uuid_lib
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ._base import (
    get_db,
    get_current_user,
    get_byok_key,
    DimensionResponse,
    DimensionErrorResponse,
    logger,
)

router = APIRouter()

# Module logger
motion_logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class MotionTransferRequest(BaseModel):
    """Request model for motion transfer."""
    image_url: str = Field(..., description="Character/subject image URL")
    motion_video_url: str = Field(..., description="Reference video with motion to transfer")
    prompt: str = Field("", max_length=2500, description="Scene/background description")
    character_orientation: str = Field(
        "video",
        description="Orientation mode: 'video' (30s max) or 'image' (10s max)"
    )
    keep_original_sound: bool = Field(True, description="Preserve audio from reference video")
    mode: str = Field("pro", description="Quality mode: 'std' or 'pro'")
    negative_prompt: Optional[str] = Field(None, max_length=500, description="Elements to avoid")


class MotionTransferResponse(BaseModel):
    """Response model for motion transfer."""
    success: bool
    task_id: str
    video_url: Optional[str] = None
    duration_seconds: float = 0
    credits_used: int = 0
    error: Optional[str] = None


class MotionStatusResponse(BaseModel):
    """Response model for motion transfer status."""
    task_id: str
    status: str
    video_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/kling/motion-transfer",
    response_model=MotionTransferResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Kling 2.6: Motion Transfer",
    description="Transfer motion from reference video to character image. Ideal for dance videos and action sequences.",
    tags=["Dimension Kling Motion"],
)
async def motion_transfer(
    request: MotionTransferRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> MotionTransferResponse:
    """Transfer motion from reference video to character image.
    
    Features:
    - Full-body motion transfer (dance, action, gestures)
    - Hand/finger precision
    - Audio preservation from reference video
    - Up to 30 seconds continuous motion
    """
    from app.services.kling_service import (
        MotionTransferConfig,
        CharacterOrientation,
        KlingMode,
        get_kling_service,
    )
    
    user_id = user.get("id", "anonymous")
    trace_id = f"motion-{uuid_lib.uuid4().hex[:12]}"
    
    motion_logger.info(
        f"[MOTION_TRANSFER] trace={trace_id} user={user_id} "
        f"orientation={request.character_orientation} audio={request.keep_original_sound}"
    )
    
    # Build config
    orientation = (
        CharacterOrientation.VIDEO
        if request.character_orientation == "video"
        else CharacterOrientation.IMAGE
    )
    mode = KlingMode.PROFESSIONAL if request.mode == "pro" else KlingMode.STANDARD
    
    config = MotionTransferConfig(
        image_url=request.image_url,
        motion_video_url=request.motion_video_url,
        prompt=request.prompt,
        character_orientation=orientation,
        keep_original_sound=request.keep_original_sound,
        mode=mode,
        negative_prompt=request.negative_prompt,
    )
    
    # Get service
    service = get_kling_service(api_key=byok_key)
    
    # Execute motion transfer
    result = await service.transfer_motion(config=config, wait_for_completion=True)
    
    if result.success:
        motion_logger.info(
            f"[MOTION_TRANSFER] Success: task={result.task_id} "
            f"duration={result.duration_seconds}s credits={result.credits_used}"
        )
    else:
        motion_logger.warning(f"[MOTION_TRANSFER] Failed: {result.error}")
    
    return MotionTransferResponse(
        success=result.success,
        task_id=result.task_id,
        video_url=result.video_url,
        duration_seconds=result.duration_seconds,
        credits_used=result.credits_used,
        error=result.error,
    )


@router.get(
    "/kling/motion/{task_id}/status",
    response_model=MotionStatusResponse,
    responses={
        404: {"model": DimensionErrorResponse, "description": "Task not found"},
    },
    summary="Get Motion Transfer Status",
    description="Get status of a motion transfer task.",
    tags=["Dimension Kling Motion"],
)
async def get_motion_status(
    task_id: str,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
) -> MotionStatusResponse:
    """Get status of a motion transfer task."""
    from app.services.kling_service import get_kling_service
    
    service = get_kling_service(api_key=byok_key)
    result = await service.get_task_status(task_id)
    
    return MotionStatusResponse(
        task_id=result.task_id,
        status=result.status,
        video_url=result.video_url,
        duration_seconds=result.duration_seconds,
        error=result.error,
    )
