"""
Kling AI Video Generation API Router

Provides REST endpoints for Kling AI video generation.
Credit-only billing (no BYOK support).

Endpoints:
- POST /api/v1/dimension/kling/generate - Generate video
- GET /api/v1/dimension/kling/status/{task_id} - Get task status

Security:
- XSS sanitization for prompt and negative_prompt
- Enum validation for duration, aspect_ratio, resolution, mode

2026 Best Practices Applied:
- Beat-Matched Prompting (Beat 0-4s: [Action], Beat 5-8s: [Dialogue])
- Native Audio with lip sync and multi-character dialogue
- Tone descriptors: (whispering), (shouting), (breathy), (resigned)
- Audio/Visual negative prompt separation
- trace_id and evidence_refs for RAG Protocol v2
"""
from __future__ import annotations

import html
import logging
import re
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.credit_service import deduct_credits, get_or_create_user_credits, refund_credits
from app.services.kling_service import (
    KlingService,
    KlingVideoRequest,
    KlingVideoResponse,
    KlingDuration,
    KlingAspectRatio,
    KlingResolution,
    KlingMode,
    get_kling_service,
)
from app.services.telemetry_integration import record_tool_run

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kling", tags=["Kling AI"])


# =============================================================================
# 2026 Best Practices: Enums and Models
# =============================================================================

class KlingToneDescriptor(str, Enum):
    """Tone descriptors for dialogue (2026 Best Practice).

    These influence both voice generation and facial expression.
    Reference: creativeaininja, fal.ai
    """
    WHISPERING = "whispering"
    SHOUTING = "shouting"
    BREATHY = "breathy"
    RESIGNED = "resigned"
    EXCITED = "excited"
    CALM = "calm"
    NERVOUS = "nervous"
    ANGRY = "angry"
    WEARY = "weary"
    PLAYFUL = "playful"


class KlingNegativePromptType(str, Enum):
    """Negative prompt types (2026 Best Practice).

    Kling 2.6 supports separate audio and visual negative prompts.
    """
    AUDIO = "audio"
    VISUAL = "visual"
    COMBINED = "combined"


class KlingLipSyncMode(str, Enum):
    """Lip sync modes for Kling 2.6 (2026).

    Reference: fal.ai/models/kling-video
    """
    TEXT_TO_VIDEO = "text_to_video"  # Generate speech from text
    AUDIO_TO_VIDEO = "audio_to_video"  # Sync to uploaded audio
    NONE = "none"  # No lip sync


class KlingCameraMovement(str, Enum):
    """Camera movements supported by Kling 2.6 (2026)."""
    STATIC = "static"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    ORBIT = "orbit"
    TRACKING = "tracking"


class KlingMotionIntensity(str, Enum):
    """Motion intensity presets (2026)."""
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"
    DRAMATIC = "dramatic"


class Kling26Capabilities(BaseModel):
    """Kling 2.6 capabilities (Dec 2025 release)."""
    max_duration_seconds: int = Field(default=10, description="Max duration (5s or 10s)")
    max_resolution: str = Field(default="1080p", description="1080p max")
    native_audio: bool = Field(default=True, description="Supports native audio (2026)")
    lip_sync: bool = Field(default=True, description="Best-in-class lip sync")
    multi_character_dialogue: bool = Field(default=True, description="Supports multiple characters")
    beat_timestamp_format: str = Field(
        default="Beat 0-4s: [Action], Beat 5-8s: [Dialogue]",
        description="Beat-matched prompting format"
    )
    dialogue_format: str = Field(
        default='Beat 5-8s: Close up. Character (Tone): "text"',
        description="Dialogue with beat timestamps"
    )


class KlingPromptQualityScore(BaseModel):
    """Prompt quality assessment for Kling (2026)."""
    has_beat_timestamps: bool = Field(default=False, description="Uses Beat timestamp format")
    has_dialogue: bool = Field(default=False, description="Contains dialogue")
    has_tone_descriptors: bool = Field(default=False, description="Uses tone descriptors")
    has_camera_movement: bool = Field(default=False, description="Specifies camera")
    has_audio_negative: bool = Field(default=False, description="Has audio negative prompts")
    has_visual_negative: bool = Field(default=False, description="Has visual negative prompts")
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall quality")


# Regex patterns for prompt quality assessment
BEAT_TIMESTAMP_PATTERN = re.compile(r"Beat\s*\d+-\d+s:", re.IGNORECASE)
DIALOGUE_PATTERN = re.compile(r'\([^)]+\):\s*"[^"]*"', re.IGNORECASE)
TONE_DESCRIPTOR_PATTERN = re.compile(r"\((" + "|".join([t.value for t in KlingToneDescriptor]) + r")\)", re.IGNORECASE)

# Recommended negative prompts (2026)
RECOMMENDED_AUDIO_NEGATIVE = "No background music, no mumble, no overlapping speech, no distortion, no electronic interference"
RECOMMENDED_VISUAL_NEGATIVE = "No text overlay, no watermark, no distortion, blurry, low quality"

# Camera movement keywords for detection
CAMERA_MOVEMENT_KEYWORDS = [
    "pan", "tilt", "zoom", "dolly", "track", "orbit", "crane", "steady",
    "aerial", "handheld", "close-up", "wide shot", "static", "following"
]


def assess_kling_prompt_quality(prompt: str, negative_prompt: str | None = None) -> KlingPromptQualityScore:
    """Assess Kling prompt quality using 2026 best practices.

    Checks for:
    - Beat timestamps (Beat 0-4s: format)
    - Dialogue with tone descriptors
    - Camera movement specifications
    - Audio/visual negative prompts

    Args:
        prompt: The main video generation prompt
        negative_prompt: Optional negative prompt

    Returns:
        KlingPromptQualityScore with component flags and overall score
    """
    prompt_lower = prompt.lower()
    neg_lower = (negative_prompt or "").lower()

    # Check for beat timestamps
    has_beat_timestamps = bool(BEAT_TIMESTAMP_PATTERN.search(prompt))

    # Check for dialogue (Speaker (Tone): "text" format)
    has_dialogue = bool(DIALOGUE_PATTERN.search(prompt))

    # Check for tone descriptors
    has_tone_descriptors = bool(TONE_DESCRIPTOR_PATTERN.search(prompt))

    # Check for camera movement
    has_camera_movement = any(kw in prompt_lower for kw in CAMERA_MOVEMENT_KEYWORDS)

    # Check for audio negative prompts
    audio_negative_keywords = ["background music", "mumble", "overlapping speech", "distortion", "audio"]
    has_audio_negative = any(kw in neg_lower for kw in audio_negative_keywords)

    # Check for visual negative prompts
    visual_negative_keywords = ["watermark", "text overlay", "blurry", "low quality", "distortion"]
    has_visual_negative = any(kw in neg_lower for kw in visual_negative_keywords)

    # Calculate overall score (0.0 - 1.0)
    score_components = [
        has_beat_timestamps,      # 0.20 - Beat timestamps are important for Kling 2.6
        has_dialogue,             # 0.20 - Dialogue with proper format
        has_tone_descriptors,     # 0.15 - Tone descriptors improve lip sync
        has_camera_movement,      # 0.15 - Camera specifications
        has_audio_negative,       # 0.15 - Audio negative prompts
        has_visual_negative,      # 0.15 - Visual negative prompts
    ]
    weights = [0.20, 0.20, 0.15, 0.15, 0.15, 0.15]
    overall_score = sum(w for w, c in zip(weights, score_components) if c)

    return KlingPromptQualityScore(
        has_beat_timestamps=has_beat_timestamps,
        has_dialogue=has_dialogue,
        has_tone_descriptors=has_tone_descriptors,
        has_camera_movement=has_camera_movement,
        has_audio_negative=has_audio_negative,
        has_visual_negative=has_visual_negative,
        overall_score=round(overall_score, 2),
    )


# =============================================================================
# Sanitization Helpers
# =============================================================================

def _sanitize_prompt(value: str) -> str:
    """Sanitize prompt field to prevent XSS.

    Args:
        value: Raw prompt input

    Returns:
        Sanitized string
    """
    if not value:
        return value
    value = value.strip()
    # Remove HTML tags
    value = re.sub(r"<[^>]+>", "", value)
    # Escape HTML entities
    value = html.escape(value)
    # Remove script/javascript patterns
    value = re.sub(r"(?i)javascript\s*:", "", value)
    value = re.sub(r"(?i)on\w+\s*=", "", value)
    return value


def _validate_duration(value: str) -> str:
    """Validate duration is 5 or 10.

    Args:
        value: Raw duration

    Returns:
        Validated duration

    Raises:
        ValueError: If not 5 or 10
    """
    allowed = ["5", "10"]
    if value not in allowed:
        raise ValueError(f"Invalid duration: {value}. Allowed: {allowed}")
    return value


def _validate_aspect_ratio(value: str) -> str:
    """Validate aspect ratio is supported.

    Args:
        value: Raw aspect ratio

    Returns:
        Validated aspect ratio

    Raises:
        ValueError: If not supported
    """
    allowed = ["16:9", "9:16", "1:1"]
    if value not in allowed:
        raise ValueError(f"Invalid aspect_ratio: {value}. Allowed: {allowed}")
    return value


def _validate_resolution(value: str) -> str:
    """Validate resolution is 720p or 1080p.

    Args:
        value: Raw resolution

    Returns:
        Validated resolution

    Raises:
        ValueError: If not 720p or 1080p
    """
    allowed = ["720p", "1080p"]
    if value not in allowed:
        raise ValueError(f"Invalid resolution: {value}. Allowed: {allowed}")
    return value


def _validate_mode(value: str) -> str:
    """Validate mode is std or pro.

    Args:
        value: Raw mode

    Returns:
        Validated mode

    Raises:
        ValueError: If not std or pro
    """
    allowed = ["std", "pro"]
    if value not in allowed:
        raise ValueError(f"Invalid mode: {value}. Allowed: {allowed}")
    return value


# =============================================================================
# Request/Response Models
# =============================================================================

class KlingElementInput(BaseModel):
    """Element input for character/style reference (Kling 2.6)."""
    image_url: str = Field(..., description="Reference image URL")
    element_type: str = Field(default="character", description="Element type: character, style, scene")
    weight: float = Field(default=1.0, ge=0.0, le=2.0, description="Element weight")


class KlingGenerateRequest(BaseModel):
    """API request for Kling video generation.

    Includes:
    - XSS sanitization for prompt and negative_prompt
    - Enum validation for duration, aspect_ratio, resolution, mode
    - Kling 2.6: Elements, Motion Control, Camera Control, End Frame
    """

    prompt: str = Field(..., min_length=1, max_length=2500, description="Video description (sanitized)")
    negative_prompt: Optional[str] = Field(None, max_length=500, description="Elements to avoid (sanitized)")
    duration: str = Field(default="5", description="Duration: 5 or 10 seconds")
    aspect_ratio: str = Field(default="16:9", description="Aspect ratio: 16:9, 9:16, 1:1")
    resolution: str = Field(default="1080p", description="Resolution: 720p or 1080p")
    mode: str = Field(default="std", description="Mode: std or pro")
    enable_audio: bool = Field(default=False, description="Enable audio generation")
    image_url: Optional[str] = Field(None, description="Initial image for image-to-video")

    # Kling 2.6: New features
    end_image_url: Optional[str] = Field(None, description="End frame image (for shot sequencing)")
    elements: Optional[list[KlingElementInput]] = Field(
        None,
        max_length=4,
        description="Reference images for character/style consistency (max 4)"
    )
    motion_preset: Optional[str] = Field(
        None,
        description="Motion intensity: slow, normal, fast, dramatic"
    )
    camera_preset: Optional[str] = Field(
        None,
        description="Camera movement: static, pan_left, pan_right, tilt_up, tilt_down, zoom_in, zoom_out, dolly_in, dolly_out, orbit"
    )

    @field_validator("prompt", mode="before")
    @classmethod
    def sanitize_prompt(cls, v: str) -> str:
        """Sanitize prompt to prevent XSS."""
        return _sanitize_prompt(v)

    @field_validator("negative_prompt", mode="before")
    @classmethod
    def sanitize_negative_prompt(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize negative_prompt to prevent XSS."""
        if v is None:
            return None
        return _sanitize_prompt(v)

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: str) -> str:
        """Validate duration is 5 or 10."""
        return _validate_duration(v)

    @field_validator("aspect_ratio")
    @classmethod
    def validate_aspect_ratio(cls, v: str) -> str:
        """Validate aspect_ratio is supported."""
        return _validate_aspect_ratio(v)

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, v: str) -> str:
        """Validate resolution is 720p or 1080p."""
        return _validate_resolution(v)

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """Validate mode is std or pro."""
        return _validate_mode(v)


class KlingGenerateResponse(BaseModel):
    """API response for Kling video generation.

    2026 Best Practices:
    - trace_id: Unique request identifier for debugging
    - evidence_refs: RAG Protocol v2 references (List[str])
    - prompt_quality: Quality assessment of the input prompt
    """

    success: bool
    task_id: str
    status: str
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    credits_used: int = 0
    error: Optional[str] = None
    # 2026: RAG Protocol v2 fields
    trace_id: str = Field(default="", description="Unique trace identifier")
    evidence_refs: List[str] = Field(default_factory=list, description="RAG evidence references")
    prompt_quality: Optional[KlingPromptQualityScore] = Field(None, description="Prompt quality assessment")


class KlingStatusResponse(BaseModel):
    """API response for task status."""

    task_id: str
    status: str
    video_url: Optional[str] = None
    error: Optional[str] = None
    trace_id: str = Field(default="", description="Unique trace identifier")


# =============================================================================
# Credit Cost Calculation
# =============================================================================

def get_credit_cost(duration: str, resolution: str) -> int:
    """Calculate credit cost based on duration and resolution."""
    costs = {
        ("5", "720p"): 35,
        ("5", "1080p"): 50,
        ("10", "720p"): 70,
        ("10", "1080p"): 100,
    }
    return costs.get((duration, resolution), 50)


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/generate",
    response_model=KlingGenerateResponse,
    summary="Generate Video with Kling AI",
    description="Generate a video using Kling AI. Always uses platform credits (no BYOK).",
)
async def generate_video(
    request: KlingGenerateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KlingGenerateResponse:
    """Generate video using Kling AI."""
    import time
    start_time = time.time()

    # 2026: Generate trace_id for RAG Protocol v2
    trace_id = f"kling-{uuid.uuid4().hex[:12]}"

    user_id = user.get("id")
    logger.info(
        f"[KLING_GENERATE] trace_id={trace_id} user={user_id} prompt_len={len(request.prompt)} "
        f"duration={request.duration}s resolution={request.resolution} mode={request.mode}"
    )

    # 2026: Assess prompt quality
    prompt_quality = assess_kling_prompt_quality(request.prompt, request.negative_prompt)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )
    
    # Calculate credit cost
    credit_cost = get_credit_cost(request.duration, request.resolution)
    
    # Check and deduct credits (always required for Kling - no BYOK)
    user_credits = await get_or_create_user_credits(db, user_id)
    if user_credits.balance < credit_cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "INSUFFICIENT_CREDITS",
                "message": "크레딧이 부족합니다.",
                "required": credit_cost,
                "balance": user_credits.balance,
            },
        )
    
    await deduct_credits(
        db, user_id, credit_cost,
        description="Kling AI: Video Generation",
        meta={"duration": request.duration, "resolution": request.resolution},
    )
    
    try:
        # Build service request with Kling 2.6 features
        elements_data = None
        if request.elements:
            elements_data = [
                {
                    "image_url": elem.image_url,
                    "element_type": elem.element_type,
                    "weight": elem.weight,
                }
                for elem in request.elements
            ]

        service_request = KlingVideoRequest(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            duration=KlingDuration(request.duration),
            aspect_ratio=KlingAspectRatio(request.aspect_ratio),
            resolution=KlingResolution(request.resolution),
            mode=KlingMode(request.mode),
            enable_audio=request.enable_audio,
            image_url=request.image_url,
            # Kling 2.6 features
            end_image_url=request.end_image_url,
            elements=elements_data,
            motion_preset=request.motion_preset,
            camera_preset=request.camera_preset,
        )
        
        # Generate video
        service = get_kling_service()
        result = await service.generate_video(service_request, wait_for_completion=True)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        if not result.success:
            # Refund on failure
            await refund_credits(
                db, user_id, credit_cost,
                description="Refund: Kling generation failed",
                meta={"error": result.error[:200] if result.error else "Unknown"},
            )
            
            await record_tool_run(
                db=db,
                tool_key="kling_video_generate",
                user_id=user_id,
                inputs_summary={"prompt": request.prompt[:100]},
                outputs_summary={},
                status="failed",
                latency_ms=latency_ms,
                credits_charged=0,
                error_message=result.error,
            )
            
            return KlingGenerateResponse(
                success=False,
                task_id=result.task_id,
                status="failed",
                error=result.error,
                trace_id=trace_id,
                evidence_refs=[f"db:kling:task:{result.task_id}"],
                prompt_quality=prompt_quality,
            )
        
        await record_tool_run(
            db=db,
            tool_key="kling_video_generate",
            user_id=user_id,
            inputs_summary={"prompt": request.prompt[:100], "duration": request.duration},
            outputs_summary={"has_video": bool(result.video_url)},
            status="success",
            latency_ms=latency_ms,
            credits_charged=credit_cost,
        )
        
        # 2026: Build evidence_refs
        evidence_refs = [
            f"db:kling:task:{result.task_id}",
            f"db:kling:model:v2.6",
        ]
        if request.enable_audio:
            evidence_refs.append("db:kling:feature:native_audio")
        if request.elements:
            evidence_refs.append(f"db:kling:elements:{len(request.elements)}")

        return KlingGenerateResponse(
            success=True,
            task_id=result.task_id,
            status="completed",
            video_url=result.video_url,
            credits_used=credit_cost,
            trace_id=trace_id,
            evidence_refs=evidence_refs,
            prompt_quality=prompt_quality,
        )
        
    except Exception as e:
        logger.error(f"Kling generation error: {e}")
        
        # Refund on error
        await refund_credits(
            db, user_id, credit_cost,
            description="Refund: Kling generation error",
            meta={"error": str(e)[:200]},
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/status/{task_id}",
    response_model=KlingStatusResponse,
    summary="Get Generation Status",
    description="Get the status of a Kling video generation task.",
)
async def get_status(
    task_id: str,
    user: dict = Depends(get_current_user),
) -> KlingStatusResponse:
    """Get status of a generation task."""
    # 2026: Generate trace_id for this status check
    trace_id = f"kling-status-{uuid.uuid4().hex[:8]}"

    service = get_kling_service()
    result = await service.get_task_status(task_id)

    return KlingStatusResponse(
        task_id=result.task_id,
        status=result.status,
        video_url=result.video_url,
        error=result.error,
        trace_id=trace_id,
    )


@router.get(
    "/pricing",
    summary="Get Pricing Information",
    description="Get Kling AI pricing information in credits.",
)
async def get_pricing() -> Dict[str, Any]:
    """Get pricing information with 2026 capabilities."""
    # 2026: Include capabilities model
    capabilities = Kling26Capabilities()

    return {
        "service": "Kling AI",
        "provider": "kling",
        "credit_only": True,
        "byok_supported": False,
        "pricing": {
            "5s_720p": {"credits": 35, "usd": 0.25},
            "5s_1080p": {"credits": 50, "usd": 0.35},
            "10s_720p": {"credits": 70, "usd": 0.50},
            "10s_1080p": {"credits": 100, "usd": 0.70},
        },
        "supported_models": ["kling-v2.6", "kling-v2.5", "kling-v2.2"],
        "features": [
            "Text-to-video",
            "Image-to-video",
            "Audio generation (v2.6+)",
            "720p / 1080p resolution",
            "5s / 10s duration",
            "Native lip sync (v2.6+)",  # 2026
            "Multi-character dialogue (v2.6+)",  # 2026
            "Beat-matched prompting (v2.6+)",  # 2026
            "End frame control (v2.6+)",  # 2026
            "Element references (max 4)",  # 2026
        ],
        # 2026: Kling 2.6 capabilities
        "capabilities_v26": {
            "max_duration_seconds": capabilities.max_duration_seconds,
            "native_audio": capabilities.native_audio,
            "lip_sync": capabilities.lip_sync,
            "multi_character_dialogue": capabilities.multi_character_dialogue,
            "beat_timestamp_format": capabilities.beat_timestamp_format,
            "dialogue_format": capabilities.dialogue_format,
        },
        # 2026: Prompt writing tips
        "prompt_tips": {
            "beat_timestamps": "Use 'Beat 0-4s: [Action], Beat 5-8s: [Dialogue]' format",
            "dialogue_format": 'Use Speaker (Tone): "text" format for dialogue',
            "tone_descriptors": [t.value for t in KlingToneDescriptor],
            "camera_movements": [c.value for c in KlingCameraMovement],
            "motion_intensities": [m.value for m in KlingMotionIntensity],
            "recommended_audio_negative": RECOMMENDED_AUDIO_NEGATIVE,
            "recommended_visual_negative": RECOMMENDED_VISUAL_NEGATIVE,
        },
        # 2026: Lip sync best practices
        "lip_sync_tips": {
            "dialogue_length": "3-5 seconds per line for best results",
            "tone_importance": "Tone descriptors affect facial expressions",
            "multiple_speakers": "Label speakers clearly: 'John (excited):', 'Mary (calm):'",
        },
    }
