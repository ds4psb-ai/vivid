"""Workflow Input Validation with Pydantic TypeAdapter (Phase 2).

2026 Best Practice: Use TypeAdapter for runtime validation of dynamic tool inputs.
Each tool has a strongly-typed input schema with validation rules.

Usage:
    from app.services.workflow_inputs import validate_tool_inputs

    validated = validate_tool_inputs("prompt_generator", raw_inputs, session)
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from app.logging_config import get_logger

if TYPE_CHECKING:
    from app.schemas.workflow_session import WorkflowSession

logger = get_logger("workflow_inputs")


# =============================================================================
# Input Schemas (Pydantic Models)
# =============================================================================

class PromptGeneratorInput(BaseModel):
    """1D Prompt Generator input schema."""

    topic: str = Field(min_length=1, max_length=1000, description="주제")
    style: str = Field(default="cinematic", max_length=100, description="스타일")
    mood: str = Field(default="dramatic", max_length=100, description="분위기")
    duration: str = Field(default="8 seconds", max_length=50, description="영상 길이")
    language: Literal["ko", "en", "ja", "zh"] = Field(default="ko", description="언어")

    model_config = ConfigDict(str_strip_whitespace=True)


class StoryboardInput(BaseModel):
    """2D Storyboard input schema."""

    concept: str = Field(min_length=1, max_length=5000, description="스토리보드 컨셉")
    prompt: Optional[str] = Field(default=None, max_length=2000, description="추가 프롬프트")
    scene_count: int = Field(default=6, ge=1, le=20, description="장면 수")
    language: Literal["ko", "en", "ja", "zh"] = Field(default="ko", description="언어")

    model_config = ConfigDict(str_strip_whitespace=True)


class ImageToolInput(BaseModel):
    """3D Image Generator input schema."""

    description: str = Field(min_length=1, max_length=2000, description="이미지 설명")
    style: str = Field(default="cinematic", max_length=100, description="스타일")
    aspect_ratio: Literal["16:9", "9:16", "1:1", "4:3", "3:4"] = Field(
        default="16:9", description="가로세로 비율"
    )

    model_config = ConfigDict(str_strip_whitespace=True)


class ReferenceAnalyzerInput(BaseModel):
    """4D Reference Analyzer input schema."""

    video_description: str = Field(min_length=1, max_length=5000, description="영상 설명")
    focus_areas: List[str] = Field(
        default=["composition", "lighting", "color"],
        max_length=10,
        description="분석 초점 영역",
    )
    analysis_depth: Literal["quick", "standard", "deep"] = Field(
        default="standard", description="분석 깊이"
    )
    output_format: Literal["structured", "narrative", "technical"] = Field(
        default="structured", description="출력 형식"
    )

    model_config = ConfigDict(str_strip_whitespace=True)


class VeoGeneratorInput(BaseModel):
    """VEO Video Generator input schema."""

    prompt: str = Field(min_length=1, max_length=2000, description="영상 프롬프트")
    negative_prompt: str = Field(default="", max_length=1000, description="제외할 요소")
    aspect_ratio: Literal["16:9", "9:16", "1:1"] = Field(
        default="16:9", description="가로세로 비율"
    )
    duration: int = Field(default=6, ge=2, le=30, description="영상 길이(초)")
    style: str = Field(default="cinematic", max_length=100, description="스타일")

    model_config = ConfigDict(str_strip_whitespace=True)


class QualityCheckInput(BaseModel):
    """QC Quality Check input schema."""

    content: str = Field(min_length=1, max_length=10000, description="검토할 콘텐츠")
    criteria: List[str] = Field(default_factory=list, max_length=20, description="검토 기준")
    check_type: Literal["general", "technical", "creative", "consistency"] = Field(
        default="general", description="검토 유형"
    )

    model_config = ConfigDict(str_strip_whitespace=True)


class AestheticDirectInput(BaseModel):
    """AD Aesthetic Director input schema."""

    prompt: str = Field(min_length=1, max_length=2000, description="미학적 프롬프트")
    style: str = Field(default="", max_length=100, description="스타일")
    auteur_key: Optional[str] = Field(default=None, max_length=50, description="작가 키")
    mood: str = Field(default="", max_length=100, description="분위기")

    model_config = ConfigDict(str_strip_whitespace=True)


class PersonaAnalyzeInput(BaseModel):
    """AI Persona Analyze input schema."""

    character_description: str = Field(
        min_length=1, max_length=5000, description="캐릭터 설명"
    )
    depth: Literal["quick", "standard", "deep"] = Field(
        default="standard", description="분석 깊이"
    )

    model_config = ConfigDict(str_strip_whitespace=True)


class StoryArchitectInput(BaseModel):
    """SA Story Architect input schema."""

    prompt: str = Field(min_length=1, max_length=3000, description="스토리 프롬프트")
    genre: Optional[str] = Field(default=None, max_length=50, description="장르")
    structure: Literal["3act", "5act", "hero_journey", "kishotenketsu"] = Field(
        default="3act", description="구조"
    )
    language: Literal["ko", "en", "ja", "zh"] = Field(default="ko", description="언어")

    model_config = ConfigDict(str_strip_whitespace=True)


class SoundCraftInput(BaseModel):
    """SC Sound Crafter input schema."""

    scene_description: str = Field(min_length=1, max_length=3000, description="장면 설명")
    mood: Optional[str] = Field(default=None, max_length=100, description="분위기")
    target_platform: Literal["suno", "udio", "generic"] = Field(
        default="suno", description="타겟 플랫폼"
    )

    model_config = ConfigDict(str_strip_whitespace=True)


# =============================================================================
# TypeAdapter Registry
# =============================================================================

INPUT_ADAPTERS: Dict[str, TypeAdapter] = {
    # Core Dimensions (1D-4D)
    "prompt_generator": TypeAdapter(PromptGeneratorInput),
    "storyboard": TypeAdapter(StoryboardInput),
    "image_tool": TypeAdapter(ImageToolInput),
    "reference_analyzer": TypeAdapter(ReferenceAnalyzerInput),
    # Extended Dimensions (QC, AD, AI, SA, SC)
    "quality_check": TypeAdapter(QualityCheckInput),
    "aesthetic_direct": TypeAdapter(AestheticDirectInput),
    "persona_analyze": TypeAdapter(PersonaAnalyzeInput),
    "story_architect": TypeAdapter(StoryArchitectInput),
    "sound_craft": TypeAdapter(SoundCraftInput),
    # VEO (both aliases)
    "veo_generator": TypeAdapter(VeoGeneratorInput),
    "veo_generate": TypeAdapter(VeoGeneratorInput),
}


# =============================================================================
# Validation Functions
# =============================================================================

def validate_tool_inputs(
    tool_id: str,
    raw_inputs: Dict[str, Any],
    session: Optional["WorkflowSession"] = None,
) -> Dict[str, Any]:
    """Validate and transform tool inputs using TypeAdapter.

    Args:
        tool_id: The tool identifier (e.g., "prompt_generator")
        raw_inputs: Raw input dictionary from user/node
        session: Optional workflow session for fallback values

    Returns:
        Validated and transformed input dictionary

    Raises:
        WorkflowValidationError: If validation fails
    """
    from app.services.workflow_exceptions import WorkflowValidationError

    adapter = INPUT_ADAPTERS.get(tool_id)
    if not adapter:
        # No adapter = no validation (for backwards compatibility)
        logger.warning(f"No input adapter for tool_id={tool_id}, skipping validation")
        return raw_inputs

    # Merge with session extracted_params for fallback
    merged_inputs = dict(raw_inputs)
    if session and hasattr(session, "extracted_params"):
        for key, value in session.extracted_params.items():
            if key not in merged_inputs or merged_inputs[key] is None:
                merged_inputs[key] = value

    try:
        validated = adapter.validate_python(merged_inputs)
        return validated.model_dump()
    except ValidationError as e:
        # Convert Pydantic errors to workflow-specific errors
        field_errors = []
        for error in e.errors():
            field_errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })

        logger.warning(
            f"Input validation failed for {tool_id}: {len(field_errors)} errors"
        )

        raise WorkflowValidationError(
            message=f"Invalid inputs for {tool_id}",
            field_errors=field_errors,
            details={"tool_id": tool_id, "raw_inputs": raw_inputs},
        )


def get_required_fields(tool_id: str) -> List[str]:
    """Get list of required fields for a tool.

    Args:
        tool_id: The tool identifier

    Returns:
        List of required field names
    """
    adapter = INPUT_ADAPTERS.get(tool_id)
    if not adapter:
        return []

    # Get the model class from TypeAdapter
    model = adapter.core_schema.get("cls")
    if not model:
        return []

    required = []
    for field_name, field_info in model.model_fields.items():
        if field_info.is_required():
            required.append(field_name)

    return required
