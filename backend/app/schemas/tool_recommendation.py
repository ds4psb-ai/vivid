"""Tool Recommendation Schemas for IP-First Coordination Phase 2.5.

Defines schemas for tool recommendations based on IP context.
Includes confidence levels, reason codes, and evidence references.

SSoT: IP-First Coordination Roadmap v2.1.1 (Phase 2.5).
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.rag.rag_suggestion import ConfidenceLevel, calculate_confidence_level


# =============================================================================
# Reason Code Constants
# =============================================================================

class ReasonCodeCategory(str, Enum):
    """Reason code categories for structured recommendations."""
    GENRE = "genre"
    SHOT = "shot"
    AUTEUR = "auteur"
    DIMENSION = "dimension"
    CONTEXT = "context"
    HISTORY = "history"


REASON_CODE_VALUES = {
    ReasonCodeCategory.GENRE: [
        "romance", "horror", "action", "drama", "comedy",
        "thriller", "fantasy", "sci-fi", "documentary", "animation"
    ],
    ReasonCodeCategory.SHOT: [
        "closeup", "wide", "establishing", "pov", "tracking",
        "aerial", "handheld", "static", "dolly", "crane"
    ],
    ReasonCodeCategory.AUTEUR: [
        "bong", "nolan", "kubrick", "tarantino", "ghibli",
        "villeneuve", "fincher", "wes_anderson", "spielberg", "scorsese"
    ],
    ReasonCodeCategory.DIMENSION: [
        "1D", "2D", "3D", "4D", "QC", "AD", "AI", "VEO", "STORY", "SOUND", "REF", "VIS"
    ],
    ReasonCodeCategory.CONTEXT: [
        "worldbuilding", "character", "setting", "theme", "mood",
        "narrative", "visual_style", "color_palette", "pacing"
    ],
    ReasonCodeCategory.HISTORY: [
        "frequently_used", "recently_used", "workflow_pattern", "similar_project"
    ],
}


def build_reason_code(category: ReasonCodeCategory, value: str) -> str:
    """Build a reason code string.

    Format: {category}:{value}

    Args:
        category: The reason code category
        value: The value within that category

    Returns:
        Formatted reason code string
    """
    return f"{category.value}:{value}"


def parse_reason_code(code: str) -> tuple[str, str]:
    """Parse a reason code into category and value.

    Args:
        code: Reason code string (e.g., "genre:romance")

    Returns:
        Tuple of (category, value)
    """
    parts = code.split(":", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return code, ""


# =============================================================================
# Tool Recommendation Schemas
# =============================================================================

class ToolRecommendation(BaseModel):
    """Single tool recommendation with confidence and evidence.

    Attributes:
        tool_id: Tool identifier (e.g., "generate_aesthetic_analysis")
        display_name: Human-readable tool name
        dimension: Dimension code (e.g., "AD", "4D")
        confidence: Raw confidence score (0.0 - 1.0)
        confidence_level: Confidence level label (HIGH, MEDIUM, LOW)
        reason_codes: List of reason codes explaining the recommendation
        evidence_refs: List of evidence references
        estimated_credits: Estimated credit cost
        priority: Recommendation priority (1 = primary, 2+ = alternatives)
        description: Optional description of why this tool is recommended
    """
    tool_id: str
    display_name: str
    dimension: str
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    reason_codes: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    estimated_credits: int = Field(ge=0)
    priority: int = Field(ge=1, default=1)
    description: Optional[str] = None

    model_config = ConfigDict(extra="ignore")

    @classmethod
    def from_tool_data(
        cls,
        tool_id: str,
        display_name: str,
        dimension: str,
        confidence: float,
        reason_codes: List[str],
        evidence_refs: List[str],
        estimated_credits: int,
        priority: int = 1,
        description: Optional[str] = None,
    ) -> "ToolRecommendation":
        """Create a ToolRecommendation with calculated confidence level."""
        return cls(
            tool_id=tool_id,
            display_name=display_name,
            dimension=dimension,
            confidence=confidence,
            confidence_level=calculate_confidence_level(confidence),
            reason_codes=reason_codes,
            evidence_refs=evidence_refs,
            estimated_credits=estimated_credits,
            priority=priority,
            description=description,
        )


class ToolRecommendationRequest(BaseModel):
    """Request for tool recommendations.

    Attributes:
        ip_id: IP catalog ID (primary context source)
        preset_id: Optional preset ID for workflow context
        scene_type: Scene type hint (establishing, dialogue, action)
        user_history: Recent tool IDs used by the user
        dimension_context: Current dimension being worked on
        max_results: Maximum recommendations to return
    """
    ip_id: Optional[UUID] = None
    preset_id: Optional[UUID] = None
    scene_type: Optional[str] = None
    user_history: Optional[List[str]] = Field(default_factory=list)
    dimension_context: Optional[str] = None
    max_results: int = Field(default=5, ge=1, le=20)

    model_config = ConfigDict(extra="ignore")


class ToolRecommendationResponse(BaseModel):
    """Response containing tool recommendations.

    Attributes:
        recommendations: List of recommended tools
        total_estimated_credits: Sum of all recommended tool credits
        workflow_suggested: Whether a full workflow is suggested
        reason_summary: Human-readable summary of recommendations
        ip_context_used: Whether IP context was available
        trace_id: Optional trace ID for observability
    """
    recommendations: List[ToolRecommendation] = Field(default_factory=list)
    total_estimated_credits: int = 0
    workflow_suggested: bool = False
    reason_summary: str = ""
    ip_context_used: bool = False
    trace_id: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class ToolEvidenceRequest(BaseModel):
    """Request for tool selection evidence.

    Attributes:
        tool_id: Tool identifier
        ip_id: Optional IP context
        include_rag_sources: Whether to include RAG sources
    """
    tool_id: str
    ip_id: Optional[UUID] = None
    include_rag_sources: bool = True

    model_config = ConfigDict(extra="ignore")


class ToolEvidenceResponse(BaseModel):
    """Response containing evidence for a tool selection.

    Attributes:
        tool_id: Tool identifier
        evidence_refs: List of evidence references
        datasets_used: List of dataset IDs used
        reason_codes: Reason codes for this tool
        confidence: Overall confidence score
        confidence_level: Confidence level label
    """
    tool_id: str
    evidence_refs: List[str] = Field(default_factory=list)
    datasets_used: List[str] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW

    model_config = ConfigDict(extra="ignore")


# =============================================================================
# Tool Metadata (for display)
# =============================================================================

class ToolDisplayInfo(BaseModel):
    """Tool display information for frontend.

    Attributes:
        tool_id: Tool identifier
        display_name_ko: Korean display name
        display_name_en: English display name
        dimension: Dimension code
        description_ko: Korean description
        description_en: English description
        icon: Icon identifier
        base_credits: Base credit cost
    """
    tool_id: str
    display_name_ko: str
    display_name_en: str
    dimension: str
    description_ko: str = ""
    description_en: str = ""
    icon: str = "tool"
    base_credits: int = 10

    model_config = ConfigDict(extra="ignore")


# =============================================================================
# Workflow Recommendation (optional future extension)
# =============================================================================

class WorkflowStepRecommendation(BaseModel):
    """Single step in a recommended workflow.

    Attributes:
        step_order: Step order (1-based)
        tool: Recommended tool for this step
        is_optional: Whether this step is optional
        depends_on: Previous step orders this depends on
    """
    step_order: int = Field(ge=1)
    tool: ToolRecommendation
    is_optional: bool = False
    depends_on: List[int] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class WorkflowRecommendationResponse(BaseModel):
    """Full workflow recommendation with steps.

    Attributes:
        workflow_id: Suggested workflow identifier
        workflow_name: Human-readable workflow name
        steps: Ordered list of workflow steps
        total_estimated_credits: Total credit cost
        estimated_duration_seconds: Estimated total duration
        reason_summary: Why this workflow is recommended
    """
    workflow_id: str
    workflow_name: str
    steps: List[WorkflowStepRecommendation] = Field(default_factory=list)
    total_estimated_credits: int = 0
    estimated_duration_seconds: int = 0
    reason_summary: str = ""

    model_config = ConfigDict(extra="ignore")
