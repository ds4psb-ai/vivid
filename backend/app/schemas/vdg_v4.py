"""
VDG v4.0 Schema Definitions

Core schemas for the 2-Pass Video Analysis Pipeline:
- Pass 1: Semantic Analysis (meaning, structure, intent)
- Pass 2: Visual Analysis (metrics, entity tracking)
- Merger: Quality validation and combination

License: arkain.info@gmail.com (Gemini Enterprise)
"""
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


# =============================================================================
# Enums
# =============================================================================

class HookPattern(str, Enum):
    """Hook pattern types for viral content."""
    QUESTION = "question"
    SHOCK = "shock"
    PROMISE = "promise"
    CURIOSITY_GAP = "curiosity_gap"
    CONFLICT = "conflict"
    TRANSFORMATION = "transformation"
    EMOTION = "emotion"
    UNKNOWN = "unknown"


class SceneRole(str, Enum):
    """Narrative role of a scene."""
    HOOK = "hook"
    SETUP = "setup"
    DEVELOPMENT = "development"
    BUILD = "build"
    CLIMAX = "climax"
    RESOLUTION = "resolution"
    CTA = "cta"
    OUTRO = "outro"


class Priority(str, Enum):
    """Priority levels for analysis points."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class QualityTier(str, Enum):
    """Quality tiers for VDG output."""
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"
    FAIL = "fail"


# =============================================================================
# Microbeat & Hook Genome (Pass 1)
# =============================================================================

class Microbeat(BaseModel):
    """Single unit of hook structure (0.5-2s typically)."""
    id: str = Field(description="Unique beat ID, e.g. 'beat_001'")
    t_start: float = Field(description="Start time in seconds")
    t_end: float = Field(description="End time in seconds")
    role: str = Field(description="Beat role: 'attention_grab', 'context_set', 'hook_trigger', 'promise'")
    description: str = Field(default="", description="What happens in this beat")
    visual_element: Optional[str] = Field(default=None, description="Key visual element")
    audio_element: Optional[str] = Field(default=None, description="Key audio element")


class HookGenome(BaseModel):
    """Detailed breakdown of the hook (first 3-5 seconds)."""
    pattern: HookPattern = Field(description="Primary hook pattern type")
    strength: float = Field(ge=0.0, le=1.0, description="Hook effectiveness score")
    microbeats: List[Microbeat] = Field(default_factory=list, description="Hook microstructure")
    trigger_element: Optional[str] = Field(default=None, description="What specifically triggers attention")
    emotional_target: Optional[str] = Field(default=None, description="Target emotion: curiosity, fear, excitement, etc.")


# =============================================================================
# Scene & Entity (Pass 1)
# =============================================================================

class Scene(BaseModel):
    """Time-coded scene with narrative role."""
    id: str = Field(description="Unique scene ID, e.g. 'scene_001'")
    t_start: float = Field(description="Start time in seconds")
    t_end: float = Field(description="End time in seconds")
    role: SceneRole = Field(description="Narrative role of this scene")
    description: str = Field(default="", description="What happens in this scene")
    key_elements: List[str] = Field(default_factory=list, description="Important visual/audio elements")


class EntityHint(BaseModel):
    """Entity hint from Pass 1 for Pass 2 resolution."""
    hint_key: str = Field(description="Stable key, e.g. 'main_speaker', 'product_A'")
    description: str = Field(description="Visual description for tracking")
    first_appearance: Optional[float] = Field(default=None, description="First seen at timestamp")
    role: Optional[str] = Field(default=None, description="Role in content: 'subject', 'object', 'environment'")


class MiseEnSceneSignal(BaseModel):
    """Visual/audio element mentioned in audience comments."""
    element: str = Field(description="Element name, e.g. 'blue dress', 'background music'")
    value: Optional[str] = Field(default=None, description="Specific value if applicable")
    sentiment: str = Field(description="'positive', 'negative', or 'neutral'")
    source_comment: Optional[str] = Field(default=None, description="Original comment text")
    likes: int = Field(default=0, description="Comment likes/engagement")


# =============================================================================
# Capsule Brief (Pass 1)
# =============================================================================

class CapsuleBrief(BaseModel):
    """High-level do's and don'ts extracted from content."""
    dos: List[str] = Field(default_factory=list, description="Things to replicate")
    donts: List[str] = Field(default_factory=list, description="Things to avoid")
    key_insight: Optional[str] = Field(default=None, description="Main takeaway")


# =============================================================================
# Semantic Pass Result (Pass 1 Output)
# =============================================================================

class SemanticPassResult(BaseModel):
    """Output from Pass 1: Semantic Analysis."""
    hook_genome: Optional[HookGenome] = Field(default=None, description="Hook breakdown")
    scenes: List[Scene] = Field(default_factory=list, description="Scene structure")
    entity_hints: Dict[str, EntityHint] = Field(default_factory=dict, description="Entity hints for Pass 2")
    mise_en_scene_signals: List[MiseEnSceneSignal] = Field(default_factory=list, description="Audience-mentioned elements")
    capsule_brief: Optional[CapsuleBrief] = Field(default=None, description="High-level brief")
    narrative_summary: Optional[str] = Field(default=None, description="One-line summary")


# =============================================================================
# Analysis Plan (Bridge: Pass 1 → Pass 2)
# =============================================================================

class MetricRequest(BaseModel):
    """Request for a specific metric measurement."""
    metric_id: str = Field(description="Metric ID from registry, e.g. 'composition_rule_of_thirds'")
    measurement_method: str = Field(default="llm", description="'llm', 'cv', or 'hybrid'")
    priority: Priority = Field(default=Priority.MEDIUM, description="Measurement priority")


class AnalysisPoint(BaseModel):
    """Single point of analysis for Visual Pass."""
    id: str = Field(description="Unique point ID, e.g. 'ap_001'")
    t_center: float = Field(description="Center timestamp in seconds")
    t_window: Tuple[float, float] = Field(description="Time window (start, end)")
    reason: str = Field(description="Why analyze here: 'hook_beat', 'scene_boundary', 'entity_track'")
    priority: str = Field(default="medium", description="critical, high, medium, low")
    target_hint_key: Optional[str] = Field(default=None, description="Entity hint key to track")
    source_ref: str = Field(default="", description="Source reference for traceability")
    metrics_requested: List[MetricRequest] = Field(default_factory=list)
    measurement_method: str = Field(default="llm", description="llm, cv, hybrid")


class SamplingConfig(BaseModel):
    """Frame sampling configuration."""
    target_fps: float = Field(default=2.0, description="Target frames per second")
    max_frames_per_window: int = Field(default=5, description="Max frames per analysis window")


# Alias for backward compatibility
SamplingPolicy = SamplingConfig


class AnalysisPlan(BaseModel):
    """Full plan for Visual Pass execution."""
    points: List[AnalysisPoint] = Field(default_factory=list)
    sampling: Optional[SamplingConfig] = Field(default=None)
    max_points_total: int = Field(default=20, description="Max analysis points")
    total_metrics_requested: int = Field(default=0)
    coverage_sec: float = Field(default=0.0, description="Total video seconds covered")


# =============================================================================
# Visual Pass Result (Pass 2 Output)
# =============================================================================

class MetricResult(BaseModel):
    """Result for a single metric measurement."""
    metric_id: str = Field(description="Metric ID that was measured")
    value: Optional[Any] = Field(default=None, description="Measured value")
    unit: Optional[str] = Field(default=None, description="Unit of measurement")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Measurement confidence")
    samples: List[Any] = Field(default_factory=list, description="Raw samples/observations")
    t: Optional[float] = Field(default=None, description="Timestamp of measurement")
    missing_reason: Optional[str] = Field(default=None, description="Why measurement failed")
    original_metric_id: Optional[str] = Field(default=None, description="Original ID if aliased")


class AnalysisPointResult(BaseModel):
    """Result for a single analysis point."""
    point_id: str = Field(description="ID of the analysis point")
    t: float = Field(description="Actual timestamp analyzed")
    metrics: Dict[str, MetricResult] = Field(default_factory=dict, description="Measured metrics")
    entity_observations: Dict[str, str] = Field(default_factory=dict, description="Entity observations")
    notes: Optional[str] = Field(default=None, description="Additional observations")


class EntityResolution(BaseModel):
    """Resolution of entity hint to stable ID."""
    hint_key: str = Field(description="Original hint key from Pass 1")
    resolved_id: str = Field(description="Resolved stable ID, e.g. 'person_1'")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    visual_description: Optional[str] = Field(default=None)


class VisualPassResult(BaseModel):
    """Output from Pass 2: Visual Analysis."""
    entity_resolutions: Dict[str, str] = Field(default_factory=dict, description="{hint_key: resolved_id}")
    analysis_results: Dict[str, AnalysisPointResult] = Field(default_factory=dict, description="{point_id: result}")
    frame_evidence_ids: List[str] = Field(default_factory=list, description="Evidence IDs for extracted frames")
    total_frames_analyzed: int = Field(default=0)
    processing_time_sec: float = Field(default=0.0)


# =============================================================================
# Merger Quality & Contract Candidates
# =============================================================================

class MergerQuality(BaseModel):
    """Quality metrics from the merger."""
    data_quality_tier: str = Field(default="bronze", description="gold, silver, bronze, reject")
    overall_alignment: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall quality score")
    point_coverage: float = Field(default=0.0, ge=0.0, le=1.0, description="% of plan points with results")
    entity_resolution_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="% of hints resolved")
    metric_coverage: float = Field(default=0.0, ge=0.0, le=1.0, description="% of requested metrics measured")
    time_sanity: bool = Field(default=True, description="All timestamps valid")
    mismatch_flags: List[str] = Field(default_factory=list, description="Issues found during merge")


class DNAInvariantCandidate(BaseModel):
    """Candidate DNA invariant for DirectorCompiler."""
    rule_id: str
    rule_type: str = Field(description="'timing', 'composition', 'engagement', 'audio'")
    condition: str
    value: Any
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source: str = Field(default="", description="Where this came from")


class MutationSlotCandidate(BaseModel):
    """Candidate mutation slot."""
    slot_id: str
    slot_type: str
    allowed_range: Optional[Tuple[Any, Any]] = None
    default_value: Optional[Any] = None


class ForbiddenMutationCandidate(BaseModel):
    """Candidate forbidden mutation."""
    mutation_id: str
    description: str
    severity: str = Field(default="major", description="'critical', 'major', 'minor'")


class ContractCandidates(BaseModel):
    """Contract candidates for DirectorCompiler."""
    dna_invariants_candidates: List[Dict[str, Any]] = Field(default_factory=list, description="Raw dict candidates")
    mutation_slots_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    forbidden_mutations_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    weights_candidates: Dict[str, float] = Field(default_factory=dict, description="Rule weights")


# =============================================================================
# VDG v4.0 Final Output
# =============================================================================

class VDGv4(BaseModel):
    """
    VDG v4.0: Complete Video DNA Graph
    
    The Single Source of Record for video analysis.
    Contains all data from both passes plus quality metrics.
    """
    # Identity
    content_id: str = Field(description="Unique content identifier")
    video_url: Optional[str] = Field(default=None, description="Source video URL")
    duration_sec: Optional[float] = Field(default=None, description="Video duration")
    
    # Pass Results
    semantic: SemanticPassResult = Field(description="Pass 1 results")
    visual: VisualPassResult = Field(description="Pass 2 results")
    plan: AnalysisPlan = Field(description="Analysis plan that was executed")
    
    # Quality & Contract
    quality: MergerQuality = Field(description="Merge quality metrics")
    contract_candidates: Optional[ContractCandidates] = Field(default=None, description="For DirectorCompiler")
    
    # Metadata
    schema_version: str = Field(default="4.0.0")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_sec: float = Field(default=0.0)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
