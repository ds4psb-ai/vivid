"""VPE (Video Parsing Engine) Schemas.

Pydantic models for VPE requests/responses and Logic Vector structure.
VPE analyzes video content using Gemini 3 Pro to extract cinematographic DNA.

Usage:
    from app.schemas.vpe import VPEParseRequest, VPEParseResponse, LogicVector
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Enums
# =============================================================================

class CompositionStrategy(str, Enum):
    """Primary composition strategies used by auteurs."""
    VERTICAL_BLOCKING = "vertical_blocking"
    RULE_OF_THIRDS = "rule_of_thirds"
    CENTRAL_FRAMING = "central_framing"
    DIAGONAL_TENSION = "diagonal_tension"
    FRAME_WITHIN_FRAME = "frame_within_frame"
    NEGATIVE_SPACE = "negative_space"
    SYMMETRY = "symmetry"
    ASYMMETRY = "asymmetry"


class LightingStyle(str, Enum):
    """Key lighting styles."""
    HIGH_KEY = "high_key"
    LOW_KEY = "low_key"
    NATURAL = "natural"
    CHIAROSCURO = "chiaroscuro"
    SILHOUETTE = "silhouette"
    PRACTICAL = "practical"
    MIXED = "mixed"


class CameraMovement(str, Enum):
    """Camera movement types."""
    STATIC = "static"
    DOLLY = "dolly"
    HANDHELD = "handheld"
    PUSH_IN = "push_in"
    PULL_OUT = "pull_out"
    PAN = "pan"
    TILT = "tilt"
    CRANE = "crane"
    TRACKING = "tracking"
    STEADICAM = "steadicam"


# =============================================================================
# Logic Vector Components
# =============================================================================

class Cadence(BaseModel):
    """Shot rhythm and timing patterns."""
    hook: float = Field(
        default=0.0,
        ge=0.0,
        description="Timestamp (seconds) for hook moment"
    )
    build: float = Field(
        default=0.0,
        ge=0.0,
        description="Timestamp (seconds) for build moment"
    )
    climax: float = Field(
        default=0.0,
        ge=0.0,
        description="Timestamp (seconds) for climax moment"
    )
    avg_shot_length: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Average shot length in seconds"
    )
    rhythm_pattern: Optional[str] = Field(
        default=None,
        description="Rhythm pattern description (e.g., 'slow_build', 'staccato')"
    )
    tempo: Optional[str] = Field(
        default=None,
        description="Overall tempo (e.g., 'deliberate', 'frenetic', 'meditative')"
    )


class Composition(BaseModel):
    """Visual composition analysis."""
    primary_strategy: str = Field(
        default="rule_of_thirds",
        description="Primary composition strategy"
    )
    symmetry_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Symmetry score (0-1)"
    )
    depth_staging: Optional[str] = Field(
        default=None,
        description="Depth staging approach (e.g., 'deep_focus', 'shallow')"
    )
    aspect_ratio_preference: Optional[str] = Field(
        default=None,
        description="Preferred aspect ratio"
    )


class CameraGrammar(BaseModel):
    """Camera movement ratios and patterns."""
    static: float = Field(default=0.0, ge=0.0, le=1.0)
    dolly: float = Field(default=0.0, ge=0.0, le=1.0)
    handheld: float = Field(default=0.0, ge=0.0, le=1.0)
    push_in: float = Field(default=0.0, ge=0.0, le=1.0)
    pull_out: float = Field(default=0.0, ge=0.0, le=1.0)
    pan: float = Field(default=0.0, ge=0.0, le=1.0)
    tilt: float = Field(default=0.0, ge=0.0, le=1.0)
    crane: float = Field(default=0.0, ge=0.0, le=1.0)
    tracking: float = Field(default=0.0, ge=0.0, le=1.0)
    steadicam: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("*", mode="before")
    @classmethod
    def clamp_ratio(cls, v: Any) -> float:
        """Clamp values between 0 and 1."""
        if isinstance(v, (int, float)):
            return max(0.0, min(1.0, float(v)))
        return 0.0


class LightingPhysics(BaseModel):
    """Lighting characteristics."""
    key_light: str = Field(
        default="natural",
        description="Primary lighting style"
    )
    color_temp_range: List[int] = Field(
        default_factory=lambda: [3200, 5600],
        description="Color temperature range in Kelvin [min, max]"
    )
    contrast_ratio: Optional[str] = Field(
        default=None,
        description="Contrast ratio description (e.g., 'high', 'low', '4:1')"
    )
    shadow_quality: Optional[str] = Field(
        default=None,
        description="Shadow quality (e.g., 'hard', 'soft', 'diffused')"
    )


class ColorScience(BaseModel):
    """Color grading and palette analysis."""
    lut_reference: Optional[str] = Field(
        default=None,
        description="Reference LUT or color grade (e.g., 'Kodak_2383', 'Fuji_3510')"
    )
    palette: List[str] = Field(
        default_factory=list,
        description="Color palette descriptors"
    )
    saturation_level: Optional[str] = Field(
        default=None,
        description="Saturation level (e.g., 'desaturated', 'vibrant', 'muted')"
    )
    dominant_hue: Optional[str] = Field(
        default=None,
        description="Dominant color hue"
    )


# =============================================================================
# Logic Vector (Main Output)
# =============================================================================

class LogicVector(BaseModel):
    """VPE core output - Auteur DNA structure.

    Represents the extracted cinematographic DNA from video analysis.
    Can be used to generate system prompts for video generation.
    """
    auteur_id: str = Field(
        ...,
        description="Auteur identifier (e.g., 'bong', 'nolan', 'kubrick')"
    )
    cadence: Cadence = Field(
        default_factory=Cadence,
        description="Shot rhythm and timing patterns"
    )
    composition: Composition = Field(
        default_factory=Composition,
        description="Visual composition analysis"
    )
    camera_grammar: CameraGrammar = Field(
        default_factory=CameraGrammar,
        description="Camera movement ratios"
    )
    lighting_physics: LightingPhysics = Field(
        default_factory=LightingPhysics,
        description="Lighting characteristics"
    )
    color_science: ColorScience = Field(
        default_factory=ColorScience,
        description="Color grading analysis"
    )

    # Metadata
    source_video: Optional[str] = Field(
        default=None,
        description="Source video URI or identifier"
    )
    analysis_timestamp: Optional[datetime] = Field(
        default=None,
        description="When the analysis was performed"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall analysis confidence"
    )

    def to_system_prompt_context(self) -> str:
        """Convert Logic Vector to system prompt context string."""
        lines = [
            f"Director Style: {self.auteur_id.upper()}",
            f"Camera Movement: {self._format_camera_grammar()}",
            f"Lighting: {self.lighting_physics.key_light}, {self.lighting_physics.color_temp_range[0]}-{self.lighting_physics.color_temp_range[1]}K",
            f"Composition: {self.composition.primary_strategy} with {self.composition.symmetry_score:.2f} symmetry",
        ]
        if self.cadence.hook > 0:
            lines.append(f"Pacing: hook at {self.cadence.hook}s, build at {self.cadence.build}s, climax at {self.cadence.climax}s")
        if self.color_science.lut_reference:
            lines.append(f"Color Grade: {self.color_science.lut_reference}")
        return "\n".join(lines)

    def _format_camera_grammar(self) -> str:
        """Format camera grammar as percentage string."""
        movements = []
        grammar = self.camera_grammar.model_dump()
        for k, v in sorted(grammar.items(), key=lambda x: -x[1]):
            if v >= 0.05:  # Only include movements >= 5%
                movements.append(f"{int(v*100)}% {k}")
        return ", ".join(movements[:4]) if movements else "static"


# =============================================================================
# Shot Analysis
# =============================================================================

class ShotAnalysis(BaseModel):
    """Individual shot analysis result."""
    shot_number: int = Field(..., ge=1, description="Shot number in sequence")
    start_time: float = Field(..., ge=0, description="Start timestamp in seconds")
    end_time: float = Field(..., ge=0, description="End timestamp in seconds")
    duration: float = Field(..., ge=0, description="Shot duration in seconds")

    # Visual elements
    camera_movement: Optional[str] = None
    camera_angle: Optional[str] = None
    shot_size: Optional[str] = None  # e.g., "wide", "medium", "close-up"
    composition_notes: Optional[str] = None

    # Lighting
    lighting_style: Optional[str] = None
    color_temperature: Optional[int] = None

    # Content
    subjects: List[str] = Field(default_factory=list)
    action_description: Optional[str] = None
    emotional_tone: Optional[str] = None

    # Technical
    lens_type: Optional[str] = None  # e.g., "wide", "telephoto", "anamorphic"
    focus_technique: Optional[str] = None  # e.g., "rack_focus", "deep_focus"


# =============================================================================
# Request/Response Models
# =============================================================================

class VPEParseRequest(BaseModel):
    """Request to parse video and extract Logic Vector."""
    video_uri: str = Field(
        ...,
        description="Video URI (gs:// for GCS, https:// for URLs, or YouTube URL)"
    )
    auteur_hint: Optional[str] = Field(
        default=None,
        description="Optional auteur hint for style matching"
    )
    extract_shots: bool = Field(
        default=True,
        description="Whether to extract shot-by-shot analysis"
    )
    store_to_qdrant: bool = Field(
        default=True,
        description="Whether to store Logic Vector to Qdrant"
    )
    max_shots: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of shots to analyze"
    )

    @field_validator("video_uri")
    @classmethod
    def validate_video_uri(cls, v: str) -> str:
        """Validate video URI format."""
        v = v.strip()
        if not v:
            raise ValueError("video_uri cannot be empty")

        valid_prefixes = ("gs://", "https://", "http://")
        youtube_patterns = ("youtube.com", "youtu.be")

        if not any(v.startswith(p) for p in valid_prefixes):
            raise ValueError(f"video_uri must start with one of: {valid_prefixes}")

        # Allow YouTube URLs
        if any(p in v for p in youtube_patterns):
            return v

        # For GCS/HTTP, basic validation
        if v.startswith("gs://") and len(v) < 10:
            raise ValueError("Invalid GCS URI")

        return v


class VPEParseResponse(BaseModel):
    """Response from VPE video parsing."""
    success: bool = Field(..., description="Whether parsing succeeded")
    trace_id: str = Field(..., description="Trace ID for debugging")
    logic_vector: Optional[LogicVector] = Field(
        default=None,
        description="Extracted Logic Vector"
    )
    shots: Optional[List[ShotAnalysis]] = Field(
        default=None,
        description="Shot-by-shot analysis (if extract_shots=True)"
    )
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="Evidence references (db:vpe_results:uuid format)"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall parsing confidence"
    )
    qdrant_doc_id: Optional[str] = Field(
        default=None,
        description="Qdrant document ID if stored"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if parsing failed"
    )

    # Metrics
    processing_time_ms: Optional[int] = Field(
        default=None,
        description="Processing time in milliseconds"
    )
    video_duration: Optional[float] = Field(
        default=None,
        description="Video duration in seconds"
    )
    shot_count: Optional[int] = Field(
        default=None,
        description="Number of shots analyzed"
    )


# =============================================================================
# Batch Operations
# =============================================================================

class VPEBatchParseRequest(BaseModel):
    """Request to parse multiple videos."""
    videos: List[VPEParseRequest] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of videos to parse (max 10)"
    )
    merge_logic_vectors: bool = Field(
        default=False,
        description="Whether to merge results into single Logic Vector"
    )


class VPEBatchParseResponse(BaseModel):
    """Response from batch video parsing."""
    success: bool
    trace_id: str
    results: List[VPEParseResponse] = Field(default_factory=list)
    merged_logic_vector: Optional[LogicVector] = Field(
        default=None,
        description="Merged Logic Vector (if merge_logic_vectors=True)"
    )
    total_processing_time_ms: Optional[int] = None


# =============================================================================
# Query/Search Models
# =============================================================================

class VPEQueryRequest(BaseModel):
    """Request to query similar Logic Vectors."""
    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Natural language query"
    )
    auteur_filter: Optional[str] = Field(
        default=None,
        description="Filter by specific auteur"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of results to return"
    )


class VPEQueryResult(BaseModel):
    """Single query result."""
    logic_vector: LogicVector
    score: float = Field(ge=0.0, le=1.0)
    doc_id: str


class VPEQueryResponse(BaseModel):
    """Response from Logic Vector query."""
    success: bool
    trace_id: str
    results: List[VPEQueryResult] = Field(default_factory=list)
    total_found: int = 0


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "CompositionStrategy",
    "LightingStyle",
    "CameraMovement",
    # Components
    "Cadence",
    "Composition",
    "CameraGrammar",
    "LightingPhysics",
    "ColorScience",
    # Core
    "LogicVector",
    "ShotAnalysis",
    # Request/Response
    "VPEParseRequest",
    "VPEParseResponse",
    "VPEBatchParseRequest",
    "VPEBatchParseResponse",
    "VPEQueryRequest",
    "VPEQueryResult",
    "VPEQueryResponse",
]
