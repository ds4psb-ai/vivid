"""Workflow Input Adapters with Decorator Registration (Phase 2-3).

All workflow tool input adapters registered via @workflow_tool decorator.
These adapters transform node inputs + session context into tool-ready inputs.

Priority order for input values:
1. node_inputs (user-provided for this node)
2. session.extracted_params (extracted from original request)
3. Defaults (hardcoded fallbacks)
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from app.dimension_adapter import DimensionCapsuleId
from app.services.workflow_tool_registry import workflow_tool

if TYPE_CHECKING:
    from app.schemas.workflow_session import WorkflowSession


# =============================================================================
# Core Dimension Tools (1D-4D)
# =============================================================================


@workflow_tool(
    tool_id="prompt_generator",
    capsule_id=DimensionCapsuleId.PROMPT_GENERATE,
    tool_key="generate_veo_prompt",
    display_name="Prompt Generator",
    credit_cost=10,
    aliases=["1d_prompt"],
    tags=["core", "1D"],
)
def build_prompt_inputs(
    node_inputs: Dict[str, Any], session: "WorkflowSession"
) -> Dict[str, Any]:
    """1D Prompt Generator input adapter."""
    params = session.extracted_params
    return {
        "topic": node_inputs.get("topic") or params.get("topic", ""),
        "style": node_inputs.get("style") or params.get("style", "cinematic"),
        "mood": node_inputs.get("mood") or params.get("mood", "dramatic"),
        "duration": node_inputs.get("duration") or params.get("duration", "8 seconds"),
        "language": node_inputs.get("language") or params.get("language", "ko"),
    }


@workflow_tool(
    tool_id="storyboard",
    capsule_id=DimensionCapsuleId.STORYBOARD_CREATE,
    tool_key="create_storyboard",
    display_name="Storyboard",
    credit_cost=10,
    aliases=["2d_storyboard"],
    tags=["core", "2D"],
)
def build_storyboard_inputs(
    node_inputs: Dict[str, Any], session: "WorkflowSession"
) -> Dict[str, Any]:
    """2D Storyboard input adapter."""
    params = session.extracted_params
    # Fallback chain for concept
    concept = (
        node_inputs.get("concept")
        or node_inputs.get("prompt")
        or node_inputs.get("script")
        or params.get("topic", "")
    )
    return {
        "concept": concept,
        "prompt": node_inputs.get("prompt") or node_inputs.get("script"),
        "scene_count": int(node_inputs.get("scene_count") or params.get("scene_count", 6)),
        "language": node_inputs.get("language") or params.get("language", "ko"),
    }


@workflow_tool(
    tool_id="image_tool",
    capsule_id=DimensionCapsuleId.IMAGE_GENERATE,
    tool_key="generate_image",
    display_name="Image Generator",
    credit_cost=50,
    aliases=["3d_image", "image_generator"],
    tags=["core", "3D"],
)
def build_image_inputs(
    node_inputs: Dict[str, Any], session: "WorkflowSession"
) -> Dict[str, Any]:
    """3D Image Generator input adapter."""
    params = session.extracted_params
    # Fallback chain for description
    description = (
        node_inputs.get("description")
        or node_inputs.get("prompt")
        or params.get("prompt", "")
    )
    return {
        "description": description,
        "style": node_inputs.get("style") or params.get("style", "cinematic"),
        "aspect_ratio": node_inputs.get("aspect_ratio") or params.get("aspect_ratio", "16:9"),
    }


@workflow_tool(
    tool_id="reference_analyzer",
    capsule_id=DimensionCapsuleId.REFERENCE_ANALYZE,
    tool_key="analyze_reference",
    display_name="Reference Analyzer",
    credit_cost=30,
    aliases=["4d_reference"],
    tags=["core", "4D"],
)
def build_reference_inputs(
    node_inputs: Dict[str, Any], session: "WorkflowSession"
) -> Dict[str, Any]:
    """4D Reference Analyzer input adapter."""
    params = session.extracted_params
    # Fallback chain for video_description
    video_description = (
        node_inputs.get("video_description")
        or node_inputs.get("description")
        or params.get("video_description", "")
    )
    return {
        "video_description": video_description,
        "focus_areas": node_inputs.get("focus_areas")
        or params.get("focus_areas", ["composition", "lighting", "color"]),
        "analysis_depth": node_inputs.get("analysis_depth")
        or params.get("analysis_depth", "standard"),
        "output_format": node_inputs.get("output_format")
        or params.get("output_format", "structured"),
    }


# =============================================================================
# Extended Dimension Tools (QC, AD, AI, SA, SC)
# =============================================================================


@workflow_tool(
    tool_id="quality_check",
    capsule_id=DimensionCapsuleId.QUALITY_CHECK,
    tool_key="check_quality",
    display_name="Quality Check",
    credit_cost=20,
    aliases=["qc_check"],
    tags=["extended", "QC"],
)
def build_quality_check_inputs(
    node_inputs: Dict[str, Any], session: "WorkflowSession"
) -> Dict[str, Any]:
    """QC Quality Check input adapter."""
    params = session.extracted_params
    # Fallback chain for content
    content = (
        node_inputs.get("content")
        or node_inputs.get("prompt")
        or node_inputs.get("script")
        or params.get("content", "")
    )
    return {
        "content": content,
        "criteria": node_inputs.get("criteria") or params.get("criteria", []),
        "check_type": node_inputs.get("check_type") or params.get("check_type", "general"),
    }


@workflow_tool(
    tool_id="aesthetic_direct",
    capsule_id=DimensionCapsuleId.AESTHETIC_DIRECT,
    tool_key="direct_aesthetic",
    display_name="Aesthetic Director",
    credit_cost=30,
    aliases=["ad_direct"],
    tags=["extended", "AD"],
)
def build_aesthetic_inputs(
    node_inputs: Dict[str, Any], session: "WorkflowSession"
) -> Dict[str, Any]:
    """AD Aesthetic Director input adapter."""
    params = session.extracted_params
    return {
        "prompt": node_inputs.get("prompt") or params.get("prompt", ""),
        "style": node_inputs.get("style") or params.get("style", ""),
        "auteur_key": node_inputs.get("auteur_key") or params.get("auteur_key"),
        "mood": node_inputs.get("mood") or params.get("mood", ""),
    }


@workflow_tool(
    tool_id="persona_analyze",
    capsule_id=DimensionCapsuleId.PERSONA_ANALYZE,
    tool_key="analyze_persona",
    display_name="Persona Analyzer",
    credit_cost=25,
    aliases=["ai_persona"],
    tags=["extended", "AI"],
)
def build_persona_inputs(
    node_inputs: Dict[str, Any], session: "WorkflowSession"
) -> Dict[str, Any]:
    """AI Persona Analyzer input adapter."""
    params = session.extracted_params
    # Fallback chain for character_description
    character_description = (
        node_inputs.get("character_description")
        or node_inputs.get("description")
        or params.get("character_description", "")
    )
    return {
        "character_description": character_description,
        "depth": node_inputs.get("depth") or params.get("depth", "standard"),
    }


@workflow_tool(
    tool_id="story_architect",
    capsule_id=DimensionCapsuleId.STORY_ARCHITECT,
    tool_key="architect_story",
    display_name="Story Architect",
    credit_cost=30,
    aliases=["sa_architect"],
    tags=["extended", "SA"],
)
def build_story_architect_inputs(
    node_inputs: Dict[str, Any], session: "WorkflowSession"
) -> Dict[str, Any]:
    """SA Story Architect input adapter."""
    params = session.extracted_params
    return {
        "prompt": node_inputs.get("prompt") or params.get("prompt", ""),
        "genre": node_inputs.get("genre") or params.get("genre"),
        "structure": node_inputs.get("structure") or params.get("structure", "3act"),
        "language": node_inputs.get("language") or params.get("language", "ko"),
    }


@workflow_tool(
    tool_id="sound_craft",
    capsule_id=DimensionCapsuleId.SOUND_CRAFT,
    tool_key="craft_sound",
    display_name="Sound Crafter",
    credit_cost=25,
    aliases=["sc_craft", "sound_crafter"],
    tags=["extended", "SC"],
)
def build_sound_craft_inputs(
    node_inputs: Dict[str, Any], session: "WorkflowSession"
) -> Dict[str, Any]:
    """SC Sound Crafter input adapter."""
    params = session.extracted_params
    # Fallback chain for scene_description
    scene_description = (
        node_inputs.get("scene_description")
        or node_inputs.get("description")
        or params.get("scene_description", "")
    )
    return {
        "scene_description": scene_description,
        "mood": node_inputs.get("mood") or params.get("mood"),
        "target_platform": node_inputs.get("target_platform")
        or params.get("target_platform", "suno"),
    }


# =============================================================================
# VEO Video Generator
# =============================================================================


@workflow_tool(
    tool_id="veo_generator",
    capsule_id=DimensionCapsuleId.VEO_VIDEO_GENERATE,
    tool_key="veo_generate",
    display_name="Veo Video Generator",
    default_model="veo-3.1-generate-preview",
    credit_cost=5000,
    aliases=["veo_generate"],
    tags=["video", "VEO"],
)
def build_veo_inputs(
    node_inputs: Dict[str, Any], session: "WorkflowSession"
) -> Dict[str, Any]:
    """VEO Video Generator input adapter."""
    params = session.extracted_params
    return {
        "prompt": node_inputs.get("prompt") or params.get("prompt", ""),
        "negative_prompt": node_inputs.get("negative_prompt", ""),
        "aspect_ratio": node_inputs.get("aspect_ratio", "16:9"),
        "duration": int(node_inputs.get("duration", 6)),
        "style": node_inputs.get("style") or params.get("style", "cinematic"),
    }
