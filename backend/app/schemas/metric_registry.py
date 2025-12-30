"""
Metric Registry - Single Source of Truth (SSoT)

All metric definitions for VDG v4.0 Visual Pass.
Visual Pass MUST use these exact metric_ids and follow unit/range specifications.

H-1 Hardening: Centralized definitions prevent metric drift.

License: arkain.info@gmail.com (Gemini Enterprise)
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import json


# =============================================================================
# Metric Definition Schema
# =============================================================================

class MetricDefinition(BaseModel):
    """Single metric definition."""
    metric_id: str = Field(description="Canonical metric ID")
    name: str = Field(description="Human-readable name")
    name_ko: Optional[str] = Field(default=None, description="Korean name")
    description: str = Field(default="")
    
    # Measurement spec
    unit: str = Field(description="Unit of measurement")
    value_type: str = Field(default="float", description="'float', 'int', 'bool', 'enum', 'string'")
    range: Optional[tuple] = Field(default=None, description="(min, max) for numeric")
    enum_values: Optional[List[str]] = Field(default=None, description="Valid values for enum type")
    
    # Aggregation
    aggregation: str = Field(default="mean", description="'mean', 'max', 'min', 'mode', 'sum'")
    
    # Category
    category: str = Field(default="visual", description="'visual', 'audio', 'timing', 'engagement'")
    
    # Aliases
    aliases: List[str] = Field(default_factory=list, description="Alternative IDs")


# =============================================================================
# Metric Definitions (Authoritative)
# =============================================================================

METRIC_DEFINITIONS: Dict[str, MetricDefinition] = {
    # =========================================================================
    # COMPOSITION METRICS
    # =========================================================================
    "composition_rule_of_thirds": MetricDefinition(
        metric_id="composition_rule_of_thirds",
        name="Rule of Thirds Adherence",
        name_ko="삼분할 법칙 준수",
        description="How well the key subject aligns with rule of thirds grid lines",
        unit="score",
        value_type="float",
        range=(0.0, 1.0),
        aggregation="mean",
        category="visual",
        aliases=["rule_of_thirds", "rot_score", "thirds_alignment"]
    ),
    
    "composition_center_weight": MetricDefinition(
        metric_id="composition_center_weight",
        name="Center Composition Weight",
        name_ko="중앙 구도 비중",
        description="Visual weight concentration in center region",
        unit="ratio",
        value_type="float",
        range=(0.0, 1.0),
        aggregation="mean",
        category="visual",
        aliases=["center_weight", "center_composition"]
    ),
    
    "composition_symmetry": MetricDefinition(
        metric_id="composition_symmetry",
        name="Symmetry Score",
        name_ko="대칭 점수",
        description="Degree of horizontal/vertical symmetry",
        unit="score",
        value_type="float",
        range=(0.0, 1.0),
        aggregation="mean",
        category="visual",
        aliases=["symmetry", "symmetry_score"]
    ),
    
    "composition_headroom": MetricDefinition(
        metric_id="composition_headroom",
        name="Headroom",
        name_ko="헤드룸",
        description="Space above subject's head (portrait framing)",
        unit="ratio",
        value_type="float",
        range=(0.0, 0.5),
        aggregation="mean",
        category="visual",
        aliases=["headroom", "head_space"]
    ),
    
    "composition_lead_room": MetricDefinition(
        metric_id="composition_lead_room",
        name="Lead Room",
        name_ko="리드 스페이스",
        description="Space in direction subject is facing/moving",
        unit="ratio",
        value_type="float",
        range=(0.0, 1.0),
        aggregation="mean",
        category="visual",
        aliases=["lead_room", "looking_room", "nose_room"]
    ),
    
    # =========================================================================
    # CAMERA METRICS
    # =========================================================================
    "camera_shot_type": MetricDefinition(
        metric_id="camera_shot_type",
        name="Shot Type",
        name_ko="샷 타입",
        description="Classification of shot framing",
        unit="enum",
        value_type="enum",
        enum_values=["extreme_close_up", "close_up", "medium_close_up", "medium", "medium_long", "long", "extreme_long", "establishing"],
        aggregation="mode",
        category="visual",
        aliases=["shot_type", "framing"]
    ),
    
    "camera_angle": MetricDefinition(
        metric_id="camera_angle",
        name="Camera Angle",
        name_ko="카메라 앵글",
        description="Vertical angle of camera",
        unit="enum",
        value_type="enum",
        enum_values=["birds_eye", "high", "eye_level", "low", "worms_eye", "dutch"],
        aggregation="mode",
        category="visual",
        aliases=["angle", "camera_height"]
    ),
    
    "camera_movement": MetricDefinition(
        metric_id="camera_movement",
        name="Camera Movement",
        name_ko="카메라 무브먼트",
        description="Type of camera motion",
        unit="enum",
        value_type="enum",
        enum_values=["static", "pan", "tilt", "zoom", "dolly", "truck", "crane", "handheld", "steadicam", "drone"],
        aggregation="mode",
        category="visual",
        aliases=["movement", "motion_type"]
    ),
    
    "camera_stability": MetricDefinition(
        metric_id="camera_stability",
        name="Camera Stability",
        name_ko="카메라 안정성",
        description="Steadiness of the shot (1=rock solid, 0=very shaky)",
        unit="score",
        value_type="float",
        range=(0.0, 1.0),
        aggregation="mean",
        category="visual",
        aliases=["stability", "shake_score"]
    ),
    
    # =========================================================================
    # LIGHTING METRICS
    # =========================================================================
    "lighting_brightness": MetricDefinition(
        metric_id="lighting_brightness",
        name="Overall Brightness",
        name_ko="전체 밝기",
        description="Average luminance of the frame",
        unit="ratio",
        value_type="float",
        range=(0.0, 1.0),
        aggregation="mean",
        category="visual",
        aliases=["brightness", "luminance", "exposure"]
    ),
    
    "lighting_contrast": MetricDefinition(
        metric_id="lighting_contrast",
        name="Contrast Ratio",
        name_ko="명암비",
        description="Dynamic range between brightest and darkest areas",
        unit="ratio",
        value_type="float",
        range=(0.0, 1.0),
        aggregation="mean",
        category="visual",
        aliases=["contrast", "dynamic_range"]
    ),
    
    "lighting_key": MetricDefinition(
        metric_id="lighting_key",
        name="Lighting Key",
        name_ko="조명 키",
        description="High key (bright, even) vs low key (dark, dramatic)",
        unit="enum",
        value_type="enum",
        enum_values=["high_key", "mid_key", "low_key"],
        aggregation="mode",
        category="visual",
        aliases=["key", "lighting_style"]
    ),
    
    "lighting_direction": MetricDefinition(
        metric_id="lighting_direction",
        name="Primary Light Direction",
        name_ko="주 광원 방향",
        description="Direction of the main light source",
        unit="enum",
        value_type="enum",
        enum_values=["front", "side", "back", "top", "bottom", "ambient"],
        aggregation="mode",
        category="visual",
        aliases=["light_direction", "key_light_position"]
    ),
    
    # =========================================================================
    # COLOR METRICS
    # =========================================================================
    "color_temperature": MetricDefinition(
        metric_id="color_temperature",
        name="Color Temperature",
        name_ko="색온도",
        description="Warm (low K) to cool (high K)",
        unit="kelvin",
        value_type="float",
        range=(2000, 10000),
        aggregation="mean",
        category="visual",
        aliases=["temperature", "white_balance"]
    ),
    
    "color_saturation": MetricDefinition(
        metric_id="color_saturation",
        name="Color Saturation",
        name_ko="채도",
        description="Intensity of colors (0=grayscale, 1=fully saturated)",
        unit="ratio",
        value_type="float",
        range=(0.0, 1.0),
        aggregation="mean",
        category="visual",
        aliases=["saturation", "chroma"]
    ),
    
    "color_dominant": MetricDefinition(
        metric_id="color_dominant",
        name="Dominant Color",
        name_ko="주조색",
        description="Primary color in the frame",
        unit="color",
        value_type="string",
        aggregation="mode",
        category="visual",
        aliases=["dominant_color", "primary_color"]
    ),
    
    # =========================================================================
    # TIMING METRICS
    # =========================================================================
    "timing_hook_start": MetricDefinition(
        metric_id="timing_hook_start",
        name="Hook Start Time",
        name_ko="훅 시작 시간",
        description="When the hook element first appears",
        unit="seconds",
        value_type="float",
        range=(0.0, 10.0),
        aggregation="min",
        category="timing",
        aliases=["hook_start", "first_hook"]
    ),
    
    "timing_cut_frequency": MetricDefinition(
        metric_id="timing_cut_frequency",
        name="Cut Frequency",
        name_ko="컷 빈도",
        description="Average cuts per minute",
        unit="cuts/min",
        value_type="float",
        range=(0.0, 120.0),
        aggregation="mean",
        category="timing",
        aliases=["cut_rate", "edit_frequency"]
    ),
    
    "timing_shot_duration": MetricDefinition(
        metric_id="timing_shot_duration",
        name="Average Shot Duration",
        name_ko="평균 샷 길이",
        description="Mean duration of shots",
        unit="seconds",
        value_type="float",
        range=(0.1, 60.0),
        aggregation="mean",
        category="timing",
        aliases=["shot_length", "asl"]
    ),
    
    # =========================================================================
    # AUDIO METRICS
    # =========================================================================
    "audio_loudness": MetricDefinition(
        metric_id="audio_loudness",
        name="Audio Loudness",
        name_ko="오디오 라우드니스",
        description="Perceived loudness (LUFS)",
        unit="LUFS",
        value_type="float",
        range=(-60.0, 0.0),
        aggregation="mean",
        category="audio",
        aliases=["loudness", "volume"]
    ),
    
    "audio_music_presence": MetricDefinition(
        metric_id="audio_music_presence",
        name="Music Presence",
        name_ko="음악 존재 여부",
        description="Whether background music is present",
        unit="bool",
        value_type="bool",
        aggregation="mode",
        category="audio",
        aliases=["has_music", "music_detected"]
    ),
    
    "audio_speech_clarity": MetricDefinition(
        metric_id="audio_speech_clarity",
        name="Speech Clarity",
        name_ko="음성 명료도",
        description="How clear and understandable speech is",
        unit="score",
        value_type="float",
        range=(0.0, 1.0),
        aggregation="mean",
        category="audio",
        aliases=["speech_quality", "voice_clarity"]
    ),
    
    # =========================================================================
    # ENGAGEMENT METRICS
    # =========================================================================
    "engagement_attention_score": MetricDefinition(
        metric_id="engagement_attention_score",
        name="Attention Score",
        name_ko="주목도 점수",
        description="Predicted attention-grabbing power",
        unit="score",
        value_type="float",
        range=(0.0, 1.0),
        aggregation="mean",
        category="engagement",
        aliases=["attention", "hook_power"]
    ),
    
    "engagement_emotion_intensity": MetricDefinition(
        metric_id="engagement_emotion_intensity",
        name="Emotion Intensity",
        name_ko="감정 강도",
        description="Strength of emotional content",
        unit="score",
        value_type="float",
        range=(0.0, 1.0),
        aggregation="max",
        category="engagement",
        aliases=["emotion_score", "emotional_impact"]
    ),
}


# =============================================================================
# Alias Mapping
# =============================================================================

def _build_alias_map() -> Dict[str, str]:
    """Build reverse alias lookup."""
    alias_map = {}
    for metric_id, definition in METRIC_DEFINITIONS.items():
        for alias in definition.aliases:
            alias_map[alias.lower()] = metric_id
    return alias_map


METRIC_ALIASES: Dict[str, str] = _build_alias_map()


# =============================================================================
# Utility Functions
# =============================================================================

def validate_metric_id(metric_id: str) -> str:
    """
    Validate and normalize a metric ID.
    
    Returns:
        Canonical metric_id (resolves aliases)
        
    Raises:
        ValueError: If metric_id is unknown
    """
    metric_id_lower = metric_id.lower()
    
    # Check if it's a canonical ID
    if metric_id in METRIC_DEFINITIONS:
        return metric_id
    
    # Check aliases
    if metric_id_lower in METRIC_ALIASES:
        return METRIC_ALIASES[metric_id_lower]
    
    # Unknown metric - return as-is but log warning
    # (Phase 2 will track unknown metrics for potential addition)
    return metric_id


def get_preset_metrics(preset: str = "core") -> List[str]:
    """
    Get a preset list of metric IDs.
    
    Presets:
        - core: Essential metrics for most analyses
        - composition: Composition-focused metrics
        - timing: Timing/pacing metrics
        - full: All defined metrics
    """
    presets = {
        "core": [
            "composition_rule_of_thirds",
            "camera_shot_type",
            "lighting_brightness",
            "timing_hook_start",
        ],
        "composition": [
            "composition_rule_of_thirds",
            "composition_center_weight",
            "composition_symmetry",
            "composition_headroom",
            "composition_lead_room",
        ],
        "timing": [
            "timing_hook_start",
            "timing_cut_frequency",
            "timing_shot_duration",
        ],
        "visual_full": [
            "composition_rule_of_thirds",
            "composition_center_weight",
            "camera_shot_type",
            "camera_angle",
            "camera_movement",
            "camera_stability",
            "lighting_brightness",
            "lighting_contrast",
            "lighting_key",
            "color_temperature",
            "color_saturation",
        ],
        "full": list(METRIC_DEFINITIONS.keys()),
    }
    
    return presets.get(preset, presets["core"])


def get_metric_definition(metric_id: str) -> Optional[MetricDefinition]:
    """Get definition for a metric ID (resolves aliases)."""
    canonical = validate_metric_id(metric_id)
    return METRIC_DEFINITIONS.get(canonical)


def to_prompt_json(metric_ids: List[str] = None) -> str:
    """
    Generate JSON string of metric definitions for LLM prompt injection.
    
    Used by Visual Pass to tell the model exactly how to measure each metric.
    
    Args:
        metric_ids: Specific metrics to include (None = all)
        
    Returns:
        JSON string for prompt injection
    """
    if metric_ids is None:
        metric_ids = list(METRIC_DEFINITIONS.keys())
    
    prompt_defs = {}
    for mid in metric_ids:
        canonical = validate_metric_id(mid)
        if canonical in METRIC_DEFINITIONS:
            defn = METRIC_DEFINITIONS[canonical]
            prompt_defs[canonical] = {
                "name": defn.name,
                "description": defn.description,
                "unit": defn.unit,
                "type": defn.value_type,
                "range": defn.range,
                "enum_values": defn.enum_values,
                "aggregation": defn.aggregation,
            }
    
    return json.dumps(prompt_defs, indent=2, ensure_ascii=False)


def get_metrics_by_category(category: str) -> List[str]:
    """Get all metric IDs in a category."""
    return [
        mid for mid, defn in METRIC_DEFINITIONS.items()
        if defn.category == category
    ]
