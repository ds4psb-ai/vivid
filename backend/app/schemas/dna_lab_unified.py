"""DNA Lab Unified Schema.

Pydantic models for the unified DNA Lab pipeline results.

Components:
- AestheticGuidelines: AD (Aesthetic Director) output
- PersonaDNA: Mirror output with MBTI + Big Five (OCEAN)
- QualityReport: QC (Quality Controller) output
- DNALabResult: Combined pipeline result

Usage:
    from app.schemas.dna_lab_unified import (
        AestheticGuidelines,
        PersonaDNA,
        QualityReport,
        DNALabResult,
        DNALabPipelineRequest,
    )
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.vpe import LogicVector


# =============================================================================
# Enums
# =============================================================================

class PipelineStatus(str, Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"  # Some steps succeeded
    FAILED = "failed"
    COMPENSATING = "compensating"  # Saga rollback in progress


class PipelineStep(str, Enum):
    """Pipeline step identifiers."""
    VPE = "vpe"
    AD = "ad"
    MIRROR = "mirror"
    QC = "qc"


# =============================================================================
# Component Output Models
# =============================================================================

class AestheticGuidelines(BaseModel):
    """Aesthetic Director (AD) output.

    Defines visual style guidelines for content generation.
    """
    visual_style: str = Field(
        default="",
        description="Primary visual style description"
    )
    color_palette: List[str] = Field(
        default_factory=list,
        description="Color palette descriptors (e.g., ['warm amber', 'deep navy'])"
    )
    mood_keywords: List[str] = Field(
        default_factory=list,
        description="Mood descriptors (e.g., ['melancholic', 'introspective'])"
    )
    auteur_reference: Optional[str] = Field(
        default=None,
        description="Reference auteur style (e.g., 'bong', 'kubrick')"
    )
    composition_notes: str = Field(
        default="",
        description="Composition guidance notes"
    )
    lighting_approach: str = Field(
        default="",
        description="Lighting approach description"
    )
    reference_directors: List[str] = Field(
        default_factory=list,
        description="Reference director names"
    )


class OceanTraits(BaseModel):
    """Big Five (OCEAN) personality traits.

    Each trait is scored from 0.0 to 1.0:
    - 0.0-0.3: Low
    - 0.3-0.7: Average
    - 0.7-1.0: High
    """
    openness: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Creativity, curiosity, openness to experience"
    )
    conscientiousness: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Organization, dependability, self-discipline"
    )
    extraversion: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Sociability, assertiveness, positive emotions"
    )
    agreeableness: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Cooperation, trust, altruism"
    )
    neuroticism: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Emotional instability, anxiety, moodiness"
    )


class PersonaDNA(BaseModel):
    """Mirror (Persona) output with MBTI + Big Five (OCEAN).

    Combines traditional MBTI typing with the scientifically validated
    Big Five personality model for comprehensive persona analysis.
    """
    # MBTI
    mbti: Optional[str] = Field(
        default=None,
        description="MBTI type (e.g., 'INTJ', 'ENFP')"
    )
    archetype: Optional[str] = Field(
        default=None,
        description="Creative archetype (e.g., 'Visionary Storyteller')"
    )

    # Big Five (OCEAN) traits
    openness: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Creativity, curiosity"
    )
    conscientiousness: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Organization, planning"
    )
    extraversion: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Sociability, energy"
    )
    agreeableness: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Cooperation, empathy"
    )
    neuroticism: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Emotional sensitivity"
    )

    # Extended traits
    persona_type: str = Field(
        default="",
        description="Persona type classification"
    )
    creative_tendencies: List[str] = Field(
        default_factory=list,
        description="Creative tendency descriptors"
    )
    visual_preferences: List[str] = Field(
        default_factory=list,
        description="Visual style preferences"
    )
    narrative_style: str = Field(
        default="",
        description="Narrative style preference"
    )
    emotional_range: List[str] = Field(
        default_factory=list,
        description="Emotional range descriptors"
    )

    # Computed metrics
    creativity_index: Optional[float] = Field(
        default=None,
        ge=-4.5,
        le=4.5,
        description="MBTI-based creativity index (CI = 3*SN + JP - EI - 0.5*TF)"
    )
    auteur_affinity: List[str] = Field(
        default_factory=list,
        description="Recommended auteur styles based on persona"
    )

    @property
    def ocean_traits(self) -> OceanTraits:
        """Get OCEAN traits as a structured object."""
        return OceanTraits(
            openness=self.openness,
            conscientiousness=self.conscientiousness,
            extraversion=self.extraversion,
            agreeableness=self.agreeableness,
            neuroticism=self.neuroticism,
        )


class QualityCriterion(BaseModel):
    """Individual quality criterion result."""
    name: str
    score: float = Field(ge=0.0, le=1.0)
    weight: float = Field(default=1.0, ge=0.0)
    passed: bool = True
    details: Optional[str] = None


class QualityReport(BaseModel):
    """Quality Controller (QC) output.

    Provides structured quality assessment with pass/fail criteria.
    """
    passed: bool = Field(
        default=True,
        description="Overall pass/fail status"
    )
    score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall quality score (0.0-1.0)"
    )
    criteria_results: Dict[str, float] = Field(
        default_factory=dict,
        description="Per-criterion scores"
    )
    issues: List[str] = Field(
        default_factory=list,
        description="Identified quality issues"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Improvement suggestions"
    )

    # Detailed breakdown
    technical_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Technical quality score"
    )
    aesthetic_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Aesthetic quality score"
    )
    narrative_coherence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Narrative coherence score"
    )

    # IP-aware context
    ip_context_used: bool = Field(
        default=False,
        description="Whether IP-specific criteria were applied"
    )
    ip_id: Optional[str] = Field(
        default=None,
        description="IP identifier if context-aware evaluation"
    )


# =============================================================================
# Pipeline Result Model
# =============================================================================

class StepResult(BaseModel):
    """Individual step execution result."""
    step: PipelineStep
    status: Literal["pending", "running", "completed", "failed", "skipped"]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    credits_used: int = 0


class DNALabResult(BaseModel):
    """Unified DNA Lab pipeline result.

    Contains outputs from all components (VPE, AD, Mirror, QC)
    with evidence refs and execution metadata.
    """
    success: bool = Field(
        default=False,
        description="Overall pipeline success"
    )
    trace_id: str = Field(
        ...,
        description="Unique trace ID for debugging and correlation"
    )
    status: PipelineStatus = Field(
        default=PipelineStatus.PENDING,
        description="Pipeline execution status"
    )

    # Component outputs
    vpe: Optional[LogicVector] = Field(
        default=None,
        description="VPE (Video Parsing Engine) output"
    )
    ad: Optional[AestheticGuidelines] = Field(
        default=None,
        description="AD (Aesthetic Director) output"
    )
    mirror: Optional[PersonaDNA] = Field(
        default=None,
        description="Mirror (Persona) output"
    )
    qc: Optional[QualityReport] = Field(
        default=None,
        description="QC (Quality Controller) output"
    )

    # Evidence and traceability
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="Evidence references (db:xxx:uuid format)"
    )

    # Execution metadata
    steps: List[StepResult] = Field(
        default_factory=list,
        description="Per-step execution results"
    )
    credits_used: int = Field(
        default=0,
        description="Total credits consumed"
    )
    processing_time_ms: int = Field(
        default=0,
        description="Total processing time in milliseconds"
    )

    # Error tracking
    errors: Dict[str, str] = Field(
        default_factory=dict,
        description="Per-step error messages"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Pipeline start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Pipeline completion timestamp"
    )


# =============================================================================
# Request Models
# =============================================================================

class DNALabPipelineRequest(BaseModel):
    """Request to run the unified DNA Lab pipeline.

    The pipeline executes steps in order: VPE → AD → Mirror → QC
    with Saga pattern compensation on failure.
    """
    video_uri: Optional[str] = Field(
        default=None,
        description="Video URI for VPE analysis (gs:// or https://)"
    )
    concept: Optional[str] = Field(
        default=None,
        description="Creative concept for AD analysis"
    )
    auteur_key: Optional[str] = Field(
        default=None,
        description="Auteur hint for style matching"
    )

    # Component selection
    steps: List[PipelineStep] = Field(
        default_factory=lambda: [
            PipelineStep.VPE,
            PipelineStep.AD,
            PipelineStep.MIRROR,
            PipelineStep.QC,
        ],
        description="Steps to execute (default: all)"
    )

    # Mirror context
    persona_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Context for Mirror persona analysis"
    )

    # QC context
    quality_content: Optional[str] = Field(
        default=None,
        description="Content for QC analysis"
    )
    ip_id: Optional[str] = Field(
        default=None,
        description="IP ID for context-aware QC"
    )

    # Options
    store_to_qdrant: bool = Field(
        default=True,
        description="Store results to Qdrant via Outbox"
    )
    fail_fast: bool = Field(
        default=False,
        description="Stop on first failure (no compensation)"
    )

    @field_validator("video_uri")
    @classmethod
    def validate_video_uri(cls, v: Optional[str]) -> Optional[str]:
        """Validate video URI scheme (security)."""
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if not any(v.startswith(p) for p in ("gs://", "https://")):
            raise ValueError("video_uri must use secure scheme (gs:// or https://)")
        return v


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "PipelineStatus",
    "PipelineStep",
    # Component outputs
    "AestheticGuidelines",
    "OceanTraits",
    "PersonaDNA",
    "QualityCriterion",
    "QualityReport",
    # Pipeline
    "StepResult",
    "DNALabResult",
    "DNALabPipelineRequest",
]
