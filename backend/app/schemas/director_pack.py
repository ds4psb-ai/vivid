"""
Director Pack Schema Definitions

DirectorPack: Compressed coaching rules for real-time Gemini Live sessions.

Philosophy:
- VDG = Brain (SoR), Pack = Script (compressed rules)
- DNA Invariants = What to KEEP (불변 규칙)
- Mutation Slots = What CAN change (가변 요소)
- Forbidden Mutations = What to NEVER do (금지 규칙)

License: arkain.info@gmail.com (Gemini Enterprise)
"""
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


# =============================================================================
# Enums
# =============================================================================

class RulePriority(str, Enum):
    """Priority levels for rules."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class InvariantType(str, Enum):
    """Types of DNA invariants."""
    TIMING = "timing"
    COMPOSITION = "composition"
    ENGAGEMENT = "engagement"
    AUDIO = "audio"
    NARRATIVE = "narrative"
    TECHNICAL = "technical"


class SlotType(str, Enum):
    """Types of mutation slots."""
    STYLE = "style"
    TONE = "tone"
    PACING = "pacing"
    COLOR = "color"
    MUSIC = "music"
    TEXT = "text"


class Severity(str, Enum):
    """Severity levels for forbidden mutations."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


# =============================================================================
# Source Reference & Evidence
# =============================================================================

class SourceRef(BaseModel):
    """Reference to source evidence."""
    source_type: str = Field(description="'vdg', 'metric', 'entity', 'frame'")
    source_id: str = Field(description="ID of the source")
    timestamp: Optional[float] = Field(default=None, description="Relevant timestamp")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


# =============================================================================
# DNA Invariants (What to KEEP)
# =============================================================================

class RuleSpec(BaseModel):
    """Specification for a coaching rule."""
    operator: str = Field(description="'eq', 'gt', 'lt', 'gte', 'lte', 'between', 'in', 'pattern', 'exists', '~='")
    value: Any = Field(description="Target value or range")
    tolerance: Optional[float] = Field(default=None, description="Acceptable deviation")
    unit: Optional[str] = Field(default=None, description="Unit of measurement, e.g. 'sec', 'percent'")
    context_filter: Optional[List[str]] = Field(
        default=None,
        description="Contexts where this rule applies, e.g. ['sequence_start', 'shortform_start']"
    )



class TimeScope(BaseModel):
    """Time scope for rule application."""
    t_start: float = Field(description="Start time in seconds")
    t_end: float = Field(description="End time in seconds")
    relative: bool = Field(default=False, description="If true, relative to video start")


class DNAInvariant(BaseModel):
    """
    단일 불변 규칙 (DNA Invariant)
    
    Example: "Hook must appear within first 2 seconds"
    """
    rule_id: str = Field(description="Unique rule ID, e.g. 'inv_hook_timing_001'")
    rule_type: InvariantType = Field(description="Type of invariant")
    name: str = Field(description="Human-readable name")
    description: str = Field(default="", description="Detailed description")
    
    # Rule specification
    condition: str = Field(description="What to check, e.g. 'hook_start_time'")
    spec: RuleSpec = Field(description="Rule specification")
    
    # Scope & Priority
    time_scope: Optional[TimeScope] = Field(default=None, description="When this applies")
    priority: RulePriority = Field(default=RulePriority.MEDIUM)
    
    # Evidence
    source_refs: List[SourceRef] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Coaching
    coach_line: Optional[str] = Field(default=None, description="What to say when violated")
    coach_line_ko: Optional[str] = Field(default=None, description="Korean version")


# =============================================================================
# Mutation Slots (What CAN change)
# =============================================================================

class MutationSlot(BaseModel):
    """
    가변 요소 슬롯 (Mutation Slot)
    
    Example: "Background music style can be energetic, calm, or dramatic"
    """
    slot_id: str = Field(description="Unique slot ID, e.g. 'slot_music_style'")
    slot_type: SlotType = Field(description="Type of slot")
    name: str = Field(description="Human-readable name")
    description: str = Field(default="")
    
    # Allowed values
    allowed_values: Optional[List[Any]] = Field(default=None, description="Discrete options")
    allowed_range: Optional[Tuple[float, float]] = Field(default=None, description="Numeric range")
    default_value: Optional[Any] = Field(default=None)
    
    # Persona binding
    persona_presets: Dict[str, Any] = Field(default_factory=dict, description="{persona: recommended_value}")
    
    # Evidence
    source_refs: List[SourceRef] = Field(default_factory=list)


# =============================================================================
# Forbidden Mutations (What to NEVER do)
# =============================================================================

class ForbiddenMutation(BaseModel):
    """
    금지 규칙 (Forbidden Mutation)
    
    Example: "Never use vertical video for landscape scenes"
    """
    mutation_id: str = Field(description="Unique mutation ID")
    name: str = Field(description="Human-readable name")
    description: str
    
    # What's forbidden
    forbidden_condition: str = Field(description="What to prevent")
    severity: Severity = Field(default=Severity.MAJOR)
    
    # When it applies
    time_scope: Optional[TimeScope] = Field(default=None)
    
    # Coaching
    coach_line: Optional[str] = Field(default=None, description="Warning message")
    coach_line_ko: Optional[str] = Field(default=None)
    
    # Evidence
    source_refs: List[SourceRef] = Field(default_factory=list)


# =============================================================================
# Checkpoints (Time-based rule activation)
# =============================================================================

class Checkpoint(BaseModel):
    """
    Time-based checkpoint for rule monitoring.
    
    Example: "At t=2s, check if hook has fired"
    """
    checkpoint_id: str = Field(description="Unique checkpoint ID")
    t: float = Field(description="Timestamp in seconds")
    
    # What to check
    check_rule_ids: List[str] = Field(default_factory=list, description="Rules to verify")
    
    # Coaching
    coach_prompt: Optional[str] = Field(default=None, description="What to ask/remind")
    coach_prompt_ko: Optional[str] = Field(default=None)


# =============================================================================
# Policy & Runtime Contract
# =============================================================================

class Policy(BaseModel):
    """Coaching policy settings."""
    interrupt_on_violation: bool = Field(default=True, description="Interrupt for critical violations")
    suggest_on_medium: bool = Field(default=True, description="Suggest for medium violations")
    log_all_checks: bool = Field(default=False)
    language: str = Field(default="ko", description="Primary coaching language")


class RuntimeContract(BaseModel):
    """Runtime settings for Gemini Live session."""
    max_session_sec: int = Field(default=300, description="Max session length")
    checkpoint_interval_sec: float = Field(default=5.0, description="Check interval")
    enable_realtime_feedback: bool = Field(default=True)
    enable_audio_coach: bool = Field(default=True)


# =============================================================================
# Coach Line Templates
# =============================================================================

class CoachLineTemplates(BaseModel):
    """Template library for coaching messages."""
    violation_critical: str = Field(default="⚠️ 중요: {rule_name} 위반. {coach_line}")
    violation_major: str = Field(default="💡 개선점: {rule_name}. {coach_line}")
    violation_minor: str = Field(default="참고: {coach_line}")
    encouragement: str = Field(default="✅ 좋아요! {positive_note}")
    checkpoint_reminder: str = Field(default="⏱️ {t}초 체크포인트: {coach_prompt}")


# =============================================================================
# Scoring
# =============================================================================

class Scoring(BaseModel):
    """Scoring weights for coaching evaluation."""
    weights: Dict[str, float] = Field(default_factory=dict, description="{rule_id: weight}")
    total_possible: float = Field(default=100.0)
    pass_threshold: float = Field(default=70.0)


# =============================================================================
# Pack Metadata
# =============================================================================

class PackMeta(BaseModel):
    """Director Pack metadata."""
    pack_id: str = Field(description="Unique pack ID")
    pattern_id: str = Field(description="Source pattern/content ID")
    version: str = Field(default="1.0.0")
    
    # Source
    source_vdg_id: Optional[str] = Field(default=None, description="Source VDG content_id")
    source_quality_tier: Optional[str] = Field(default=None)
    
    # Compilation
    compiled_at: datetime = Field(default_factory=datetime.utcnow)
    compiled_by: str = Field(default="DirectorCompiler")
    
    # Stats
    invariant_count: int = Field(default=0)
    slot_count: int = Field(default=0)
    forbidden_count: int = Field(default=0)
    checkpoint_count: int = Field(default=0)


# =============================================================================
# Director Pack (Main Output)
# =============================================================================

class DirectorPack(BaseModel):
    """
    Director Pack: Compressed rules for real-time AI coaching.
    
    Used by Gemini Live to provide director-style feedback.
    
    Structure:
    - dna_invariants: Rules that MUST be followed
    - mutation_slots: Elements that CAN vary
    - forbidden_mutations: Things to NEVER do
    - checkpoints: Time-based monitoring points
    """
    # Metadata
    meta: PackMeta
    
    # Core Rules
    dna_invariants: List[DNAInvariant] = Field(default_factory=list)
    mutation_slots: List[MutationSlot] = Field(default_factory=list)
    forbidden_mutations: List[ForbiddenMutation] = Field(default_factory=list)
    checkpoints: List[Checkpoint] = Field(default_factory=list)
    
    # Policy & Config
    policy: Policy = Field(default_factory=Policy)
    runtime_contract: RuntimeContract = Field(default_factory=RuntimeContract)
    
    # Templates & Scoring
    coach_templates: CoachLineTemplates = Field(default_factory=CoachLineTemplates)
    scoring: Optional[Scoring] = Field(default=None)
    
    # Quick access
    @property
    def critical_invariants(self) -> List[DNAInvariant]:
        """Get critical priority invariants."""
        return [i for i in self.dna_invariants if i.priority == RulePriority.CRITICAL]
    
    @property
    def rule_count(self) -> int:
        """Total rule count."""
        return len(self.dna_invariants) + len(self.forbidden_mutations)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
