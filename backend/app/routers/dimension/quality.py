"""
Quality Dimension Endpoints - Quality Check & Creative Editor.

- Quality Check: Evaluate content quality across 6 criteria
- Creative Editor: Analyze and rewrite content using an editorial persona

Security:
- XSS sanitization for content, context, persona
- Enum validation for content_type, inspection_mode, criteria

2026 Best Practices:
- VBench/VBench-2.0: 18-dimension video quality evaluation (CVPR 2024, Mar 2025)
- DINOv2/CLIP: Consistency scoring for subject/background
- RAG Protocol v2: trace_id, evidence_refs (List[str]), confidence
"""
from __future__ import annotations

import html
import logging
import re
import uuid
from enum import Enum
from typing import Dict, List

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from ._base import (
    get_db,
    get_current_user,
    get_byok_key,
    _execute_dimension_tool,
    _execute_dimension_tool_stream,
    _validate_model,
    _strip_string,
    DimensionResponse,
    DimensionErrorResponse,
    DimensionCapsuleId,
    get_sse_headers,
    Optional,
)

router = APIRouter()

# Module logger
quality_logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

ALLOWED_CONTENT_TYPES = frozenset({
    "prompt", "scenario", "script", "description", "dialogue", "narration", "ad_copy"
})
ALLOWED_INSPECTION_MODES = frozenset({"comprehensive", "quick", "cinematic", "consistency"})
ALLOWED_CRITERIA = frozenset({
    "aesthetic", "consistency", "safety", "technical", "narrative", "ad_suitability"
})
ALLOWED_PERSONAS = frozenset({
    "Senior Editor", "Script Doctor", "Creative Director", "Copy Editor", "Story Analyst"
})


# ============================================================================
# 2026 VBench Evaluation Dimensions (CVPR 2024 + VBench-2.0 Mar 2025)
# ============================================================================

class VBenchDimension(str, Enum):
    """VBench evaluation dimensions for video quality assessment.

    Source: VBench CVPR 2024 (16 dims) + VBench-2.0 Mar 2025 (18 dims)
    Reference: https://github.com/Vchitect/VBench
    """
    # Superficial Faithfulness (VBench 1.0)
    SUBJECT_CONSISTENCY = "subject_consistency"
    BACKGROUND_CONSISTENCY = "background_consistency"
    TEMPORAL_FLICKERING = "temporal_flickering"
    MOTION_SMOOTHNESS = "motion_smoothness"
    DYNAMIC_DEGREE = "dynamic_degree"
    AESTHETIC_QUALITY = "aesthetic_quality"
    IMAGING_QUALITY = "imaging_quality"
    OBJECT_CLASS = "object_class"
    MULTIPLE_OBJECTS = "multiple_objects"
    HUMAN_ACTION = "human_action"
    COLOR = "color"
    SPATIAL_RELATIONSHIP = "spatial_relationship"
    SCENE = "scene"
    TEMPORAL_STYLE = "temporal_style"
    APPEARANCE_STYLE = "appearance_style"
    OVERALL_CONSISTENCY = "overall_consistency"

    # Intrinsic Faithfulness (VBench-2.0)
    COMPOSITIONAL_CREATIVITY = "compositional_creativity"
    COMMONSENSE_REASONING = "commonsense_reasoning"
    PHYSICS_REALISM = "physics_realism"
    HUMAN_ANATOMY = "human_anatomy"
    COMPLEX_PROMPT_ADHERENCE = "complex_prompt_adherence"


class ConsistencyScoringMethod(str, Enum):
    """Consistency scoring methods (2026 Best Practice: DINOv2 standard)."""
    DINOV2_FEATURE = "dinov2_feature_similarity"  # Primary (Meta AI)
    CLIP_EMBEDDING = "clip_embedding_similarity"  # Secondary (OpenAI)
    ARCFACE_IDENTITY = "arcface_identity_match"  # Face-specific


class ConsistencyThresholds(BaseModel):
    """DINOv2 consistency scoring thresholds (2026 VideoMemory benchmark).

    Reference: Research doc 09_QUALITY_DIRECTOR_RESEARCH.md
    """
    character: float = Field(0.70, ge=0.0, le=1.0, description="Character consistency (DINOv2)")
    prop: float = Field(0.60, ge=0.0, le=1.0, description="Prop consistency")
    background: float = Field(0.65, ge=0.0, le=1.0, description="Background consistency")
    temporal: float = Field(0.80, ge=0.0, le=1.0, description="Temporal consistency (frame-to-frame)")


class VBenchScore(BaseModel):
    """VBench dimension scores for video quality evaluation.

    2026 Best Practice: Multi-dimensional quality scoring.
    """
    dimension: VBenchDimension = Field(..., description="VBench evaluation dimension")
    score: float = Field(0.0, ge=0.0, le=1.0, description="Score (0-1)")
    method: ConsistencyScoringMethod = Field(
        ConsistencyScoringMethod.DINOV2_FEATURE,
        description="Scoring method used"
    )
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence level")


class MultiModalQualityWeight(BaseModel):
    """Multi-modal quality evaluation weights.

    2026 Best Practice: Weighted scoring across modalities.
    Reference: Research doc section 3.3.2
    """
    video: float = Field(0.50, ge=0.0, le=1.0, description="Video quality weight")
    audio: float = Field(0.25, ge=0.0, le=1.0, description="Audio quality weight")
    prompt: float = Field(0.25, ge=0.0, le=1.0, description="Prompt adherence weight")


class QualityEvaluationResult(BaseModel):
    """Comprehensive quality evaluation result (2026 VBench pattern).

    Includes:
    - VBench dimension scores
    - Consistency thresholds
    - RAG Protocol v2 fields
    """
    # Overall scores
    overall_score: float = Field(0.0, ge=0.0, le=100.0, description="Overall quality (0-100)")
    pass_threshold: bool = Field(False, description="Passes quality threshold")

    # VBench dimensions (subset for response)
    subject_consistency: float = Field(0.0, ge=0.0, le=1.0)
    background_consistency: float = Field(0.0, ge=0.0, le=1.0)
    aesthetic_quality: float = Field(0.0, ge=0.0, le=1.0)
    motion_smoothness: float = Field(0.0, ge=0.0, le=1.0)

    # Multi-modal weights applied
    weights: MultiModalQualityWeight = Field(default_factory=MultiModalQualityWeight)

    # RAG Protocol v2 fields
    trace_id: str = Field("", description="Trace ID for auditability")
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="RAG evidence references (format: 'rag:quality:dimension', 'db:quality_check:uuid')"
    )
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="AI confidence score")


# ============================================================================
# Sanitization Helpers
# ============================================================================

def _sanitize_text_field(value: str, default: str = "") -> str:
    """Sanitize text fields to prevent XSS.

    Args:
        value: Raw text input
        default: Default value if empty

    Returns:
        Sanitized string
    """
    if not value:
        return default
    value = value.strip()
    if not value:
        return default
    # Remove HTML tags
    value = re.sub(r"<[^>]+>", "", value)
    # Escape HTML entities
    value = html.escape(value)
    # Remove script/javascript patterns
    value = re.sub(r"(?i)javascript\s*:", "", value)
    value = re.sub(r"(?i)on\w+\s*=", "", value)
    return value or default


def _validate_content_type(value: str) -> str:
    """Validate content_type is in allowed list.

    Args:
        value: Raw content_type

    Returns:
        Validated content_type

    Raises:
        ValueError: If not in allowed list
    """
    value = value.strip().lower()
    if value not in ALLOWED_CONTENT_TYPES:
        raise ValueError(
            f"지원하지 않는 콘텐츠 타입: {value}. Allowed: {sorted(ALLOWED_CONTENT_TYPES)}"
        )
    return value


def _validate_inspection_mode(value: str) -> str:
    """Validate inspection_mode is in allowed list.

    Args:
        value: Raw inspection_mode

    Returns:
        Validated inspection_mode

    Raises:
        ValueError: If not in allowed list
    """
    value = value.strip().lower()
    if value not in ALLOWED_INSPECTION_MODES:
        raise ValueError(
            f"지원하지 않는 검수 모드: {value}. Allowed: {sorted(ALLOWED_INSPECTION_MODES)}"
        )
    return value


def _validate_criteria_list(values: List[str]) -> List[str]:
    """Validate criteria list contains only allowed values.

    Args:
        values: Raw criteria list

    Returns:
        Validated criteria list

    Raises:
        ValueError: If any value not in allowed list
    """
    validated = []
    for v in values:
        v_clean = v.strip().lower()
        if v_clean not in ALLOWED_CRITERIA:
            raise ValueError(
                f"지원하지 않는 평가 기준: {v_clean}. Allowed: {sorted(ALLOWED_CRITERIA)}"
            )
        validated.append(v_clean)
    return validated


def _validate_persona(value: str) -> str:
    """Validate persona is in allowed list.

    Args:
        value: Raw persona

    Returns:
        Validated persona (original case preserved)

    Raises:
        ValueError: If not in allowed list
    """
    value_clean = value.strip()
    # Check case-insensitively
    if value_clean.lower() not in {p.lower() for p in ALLOWED_PERSONAS}:
        raise ValueError(
            f"지원하지 않는 페르소나: {value_clean}. Allowed: {sorted(ALLOWED_PERSONAS)}"
        )
    # Return matching persona with original case
    for p in ALLOWED_PERSONAS:
        if p.lower() == value_clean.lower():
            return p
    return value_clean


# ============================================================================
# Request Models
# ============================================================================


class QualityCheckRequest(BaseModel):
    """Request model for Quality Check evaluation.

    Includes:
    - XSS sanitization for content
    - Enum validation for content_type, inspection_mode, criteria
    """
    content: str = Field(..., min_length=1, max_length=10000, description="Content to evaluate (sanitized)")
    content_type: str = Field("prompt", max_length=50, description="Type of content")
    inspection_mode: str = Field("comprehensive", max_length=50, description="Inspection mode (backward compat)")
    inspection_modes: Optional[List[str]] = Field(None, description="Multi-mode list (P3)")
    # P3: Align with engine's DEFAULT_CRITERIA
    criteria: List[str] = Field(
        default=["aesthetic", "consistency", "safety"],
        description="Evaluation criteria (aesthetic, consistency, safety, technical, narrative, ad_suitability)"
    )
    threshold: int = Field(70, ge=0, le=100, description="Quality threshold (0-100)")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("content", mode="before")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        """Sanitize content to prevent XSS."""
        return _sanitize_text_field(v)

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        """Validate content_type is in allowed list."""
        return _validate_content_type(v)

    @field_validator("inspection_mode")
    @classmethod
    def validate_inspection_mode(cls, v: str) -> str:
        """Validate inspection_mode is in allowed list."""
        return _validate_inspection_mode(v)

    @field_validator("criteria")
    @classmethod
    def validate_criteria(cls, v: List[str]) -> List[str]:
        """Validate criteria list contains only allowed values."""
        return _validate_criteria_list(v)

    @field_validator("threshold", mode="before")
    @classmethod
    def normalize_threshold(cls, v) -> int:
        """Normalize threshold: 0-1 scale → 0-100."""
        try:
            val = float(v)
        except (TypeError, ValueError):
            return 70
        if 0 <= val <= 1:
            return int(val * 100)
        return max(0, min(100, int(val)))

    @field_validator("inspection_modes", mode="before")
    @classmethod
    def normalize_modes(cls, v, info) -> Optional[List[str]]:
        """Normalize: filter invalid, NO silent fallback (engine handles error)."""
        if v is None:
            # Use single mode (from inspection_mode field)
            single = info.data.get("inspection_mode", "comprehensive")
            # If single mode is invalid, return empty → engine returns error
            return [single] if single in ALLOWED_INSPECTION_MODES else []
        if isinstance(v, list):
            # Filter to valid modes only, no fallback
            return [m for m in v if m in ALLOWED_INSPECTION_MODES]
        return []

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


class CreativeEditorRequest(BaseModel):
    """Request model for Creative Editor.

    Includes:
    - XSS sanitization for content, context
    - Enum validation for persona
    """
    content: str = Field(..., min_length=1, max_length=10000, description="Content to improve (sanitized)")
    context: str = Field(..., min_length=1, max_length=1000, description="Context/Genre/Audience (sanitized)")
    persona: str = Field("Senior Editor", max_length=100, description="Editorial persona")
    use_rag: bool = Field(True, description="Use RAG for editing principles")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("content", mode="before")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        """Sanitize content to prevent XSS."""
        return _sanitize_text_field(v)

    @field_validator("context", mode="before")
    @classmethod
    def sanitize_context(cls, v: str) -> str:
        """Sanitize context to prevent XSS."""
        return _sanitize_text_field(v)

    @field_validator("persona")
    @classmethod
    def validate_persona(cls, v: str) -> str:
        """Validate persona is in allowed list."""
        return _validate_persona(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


# ============================================================================
# Quality Check
# ============================================================================

@router.post(
    "/quality/check",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Quality Checker: Evaluate Content",
    description="Evaluate content quality across 6 criteria.",
    tags=["Dimension Extended"],
)
async def check_quality(
    request: QualityCheckRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Check content quality with Intent-Resolver integration (P3: multi-mode support).

    2026 Best Practice: VBench-aligned multi-dimensional evaluation with
    DINOv2 consistency scoring and RAG Protocol v2 trace fields.
    """
    user_id = user.get("id", "unknown")
    trace_id = f"qc-{uuid.uuid4().hex[:12]}"

    quality_logger.info(
        f"[QUALITY_CHECK] trace={trace_id} user={user_id} content_len={len(request.content)} "
        f"type={request.content_type} mode={request.inspection_mode} threshold={request.threshold}"
    )

    from app.routers.intent_helpers import infer_intent_from_request
    intent = infer_intent_from_request()

    # P3: Calculate credit multiplier based on mode count
    modes = request.inspection_modes or [request.inspection_mode]
    mode_count = len(modes)
    credit_multiplier = 1 + 0.5 * (mode_count - 1)  # 1→1.0, 2→1.5, 3→2.0, 4→2.5

    # 2026 VBench: Build evidence_refs for traceability
    evidence_refs = [
        f"rag:quality_check:{request.content_type}",
        f"config:inspection_mode:{request.inspection_mode}",
    ]
    for criterion in request.criteria:
        evidence_refs.append(f"criteria:{criterion}")

    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.QUALITY_CHECK,
        tool_key="quality_check",
        inputs={
            "content": request.content,
            "content_type": request.content_type,
            "inspection_mode": request.inspection_mode,  # Legacy
            "inspection_modes": modes,  # P3: multi-mode
            "criteria": request.criteria,
            # 2026 VBench: RAG Protocol v2 trace fields
            "trace_id": trace_id,
            "evidence_refs": evidence_refs,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={
            "content_type": request.content_type,
            "inspection_modes": modes,
            "mode_count": mode_count,
            "criteria": request.criteria,
            "trace_id": trace_id,
        },
        params={
            "threshold": request.threshold,
            "credit_multiplier": credit_multiplier,
        },
        intent=intent,
    )



@router.post(
    "/quality/check/stream",
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Quality Checker: Evaluate Content (SSE Stream)",
    description="Evaluate content quality with real-time progress updates via SSE.",
    tags=["Dimension Extended"],
)
async def check_quality_stream(
    request: QualityCheckRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Check content quality with SSE streaming (P3: multi-mode support).

    2026 Best Practice: VBench-aligned multi-dimensional evaluation with
    DINOv2 consistency scoring and RAG Protocol v2 trace fields.
    """
    user_id = user.get("id", "unknown")
    trace_id = f"qcs-{uuid.uuid4().hex[:12]}"

    quality_logger.info(
        f"[QUALITY_CHECK_STREAM] trace={trace_id} user={user_id} content_len={len(request.content)} "
        f"type={request.content_type} mode={request.inspection_mode}"
    )

    from app.routers.intent_helpers import infer_intent_from_request
    intent = infer_intent_from_request()

    # P3: Calculate credit multiplier based on mode count
    modes = request.inspection_modes or [request.inspection_mode]
    mode_count = len(modes)
    credit_multiplier = 1 + 0.5 * (mode_count - 1)

    # 2026 VBench: Build evidence_refs for traceability
    evidence_refs = [
        f"rag:quality_check:{request.content_type}",
        f"config:inspection_mode:{request.inspection_mode}",
    ]
    for criterion in request.criteria:
        evidence_refs.append(f"criteria:{criterion}")

    return StreamingResponse(
        _execute_dimension_tool_stream(
            capsule_id=DimensionCapsuleId.QUALITY_CHECK,
            tool_key="quality_check",
            operation_name="품질 검수",
            inputs={
                "content": request.content,
                "content_type": request.content_type,
                "inspection_mode": request.inspection_mode,  # Legacy
                "inspection_modes": modes,  # P3: multi-mode
                "criteria": request.criteria,
                # 2026 VBench: RAG Protocol v2 trace fields
                "trace_id": trace_id,
                "evidence_refs": evidence_refs,
            },
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={
                "content_type": request.content_type,
                "inspection_modes": modes,
                "mode_count": mode_count,
                "criteria": request.criteria,
                "trace_id": trace_id,
            },
            params={
                "threshold": request.threshold,
                "credit_multiplier": credit_multiplier,
            },
            intent=intent,
        ),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )



# ============================================================================
# Creative Editor
# ============================================================================

@router.post(
    "/quality/editor",
    response_model=DimensionResponse,
    summary="Creative Editor: Improve Content",
    description="Analyze and rewrite content using an editorial persona.",
    tags=["Dimension Quality"],
)
async def run_creative_editor(
    request: CreativeEditorRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Run Creative Editor with Intent-Resolver integration.

    2026 Best Practice: RAG Protocol v2 trace fields for auditability.
    """
    user_id = user.get("id", "unknown")
    trace_id = f"ce-{uuid.uuid4().hex[:12]}"

    quality_logger.info(
        f"[CREATIVE_EDITOR] trace={trace_id} user={user_id} content_len={len(request.content)} "
        f"persona={request.persona} use_rag={request.use_rag}"
    )

    from app.routers.intent_helpers import infer_intent_from_request
    intent = infer_intent_from_request()

    # 2026: Build evidence_refs for traceability
    evidence_refs = [
        f"rag:creative_editor:persona:{request.persona.lower().replace(' ', '_')}",
        f"config:use_rag:{request.use_rag}",
    ]

    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.CREATIVE_EDITOR,
        tool_key="run_creative_editor",
        inputs={
            "content": request.content,
            "context": request.context,
            "persona": request.persona,
            # 2026: RAG Protocol v2 trace fields
            "trace_id": trace_id,
            "evidence_refs": evidence_refs,
        },
        params={"use_rag": request.use_rag},
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={
            "content_len": len(request.content),
            "persona": request.persona,
            "trace_id": trace_id,
        },
        intent=intent,
    )


@router.post(
    "/quality/editor/stream",
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Creative Editor: Improve Content (SSE Stream)",
    description="Improve content with real-time progress updates via SSE.",
    tags=["Dimension Quality"],
)
async def run_creative_editor_stream(
    request: CreativeEditorRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Run Creative Editor with SSE streaming.

    2026 Best Practice: RAG Protocol v2 trace fields for auditability.
    """
    user_id = user.get("id", "unknown")
    trace_id = f"ces-{uuid.uuid4().hex[:12]}"

    quality_logger.info(
        f"[CREATIVE_EDITOR_STREAM] trace={trace_id} user={user_id} content_len={len(request.content)} "
        f"persona={request.persona}"
    )

    from app.routers.intent_helpers import infer_intent_from_request
    intent = infer_intent_from_request()

    # 2026: Build evidence_refs for traceability
    evidence_refs = [
        f"rag:creative_editor:persona:{request.persona.lower().replace(' ', '_')}",
        f"config:use_rag:{request.use_rag}",
    ]

    return StreamingResponse(
        _execute_dimension_tool_stream(
            capsule_id=DimensionCapsuleId.CREATIVE_EDITOR,
            tool_key="run_creative_editor",
            operation_name="콘텐츠 개선",
            inputs={
                "content": request.content,
                "context": request.context,
                "persona": request.persona,
                # 2026: RAG Protocol v2 trace fields
                "trace_id": trace_id,
                "evidence_refs": evidence_refs,
            },
            params={"use_rag": request.use_rag},
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={
                "content_len": len(request.content),
                "persona": request.persona,
                "trace_id": trace_id,
            },
            intent=intent,
        ),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )
