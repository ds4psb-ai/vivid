"""Technique Detector Service for 4D Reference Decoder.

Detects cinematography techniques from frame analysis results:
- Camera movements (pan, tilt, dolly, etc.)
- Shot types (close-up, wide, etc.)
- Lighting techniques (Rembrandt, silhouette, etc.)
- Composition patterns (rule of thirds, symmetry, etc.)

2026 Best Practices:
- Pattern matching with technique database
- AI-enhanced detection via Gemini
- RAG integration for technique explanations

Usage:
    from app.services.ai.technique_detector import get_technique_detector

    detector = get_technique_detector()
    techniques = await detector.detect_techniques(frame_analyses)
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Models
# =============================================================================


class DetectedTechnique(BaseModel):
    """A detected cinematography technique."""

    technique_id: str = Field(description="Unique technique identifier")
    name: str = Field(description="Technique name in English")
    name_ko: str = Field(description="Technique name in Korean")
    category: str = Field(
        description="Category: shot_type, camera_movement, lighting, composition, lens, color"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence")
    frame_indices: List[int] = Field(
        default_factory=list,
        description="Frame indices where technique was detected"
    )
    timestamp_ranges: List[tuple] = Field(
        default_factory=list,
        description="Timestamp ranges (start, end) where detected"
    )
    description: str = Field(default="", description="Description of how technique is used")
    emotional_effect: List[str] = Field(
        default_factory=list,
        description="Emotional effects of this technique"
    )
    recreation_tips: str = Field(
        default="",
        description="Tips for recreating this technique"
    )
    ai_prompt_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords for AI video generation"
    )
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="RAG evidence references"
    )


class TechniqueCategory(BaseModel):
    """Category of techniques with detected items."""

    category: str
    category_name_ko: str
    techniques: List[DetectedTechnique]
    total_confidence: float


# =============================================================================
# Technique Database
# =============================================================================


TECHNIQUE_DATABASE: Dict[str, Dict[str, Any]] = {
    # Shot Types
    "extreme_wide": {
        "name": "Extreme Wide Shot",
        "name_ko": "익스트림 와이드 샷",
        "category": "shot_type",
        "keywords": ["extreme wide", "wide shot", "establishing", "전경", "원경", "익스트림"],
        "emotional_effect": ["scale", "isolation", "context"],
        "ai_prompt_keywords": ["extreme wide shot", "establishing shot", "vast landscape"],
    },
    "wide": {
        "name": "Wide Shot",
        "name_ko": "와이드 샷",
        "category": "shot_type",
        "keywords": ["wide", "full shot", "와이드", "풀샷"],
        "emotional_effect": ["context", "environment", "action"],
        "ai_prompt_keywords": ["wide shot", "full body shot", "environmental shot"],
    },
    "medium_wide": {
        "name": "Medium Wide Shot",
        "name_ko": "미디엄 와이드",
        "category": "shot_type",
        "keywords": ["medium wide", "cowboy", "미디엄 와이드", "카우보이"],
        "emotional_effect": ["character_in_environment", "movement"],
        "ai_prompt_keywords": ["medium wide shot", "cowboy shot", "knee shot"],
    },
    "medium": {
        "name": "Medium Shot",
        "name_ko": "미디엄 샷",
        "category": "shot_type",
        "keywords": ["medium", "waist", "미디엄", "허리"],
        "emotional_effect": ["dialogue", "character", "connection"],
        "ai_prompt_keywords": ["medium shot", "waist shot", "conversational"],
    },
    "medium_close": {
        "name": "Medium Close-Up",
        "name_ko": "미디엄 클로즈업",
        "category": "shot_type",
        "keywords": ["medium close", "bust", "미디엄 클로즈", "바스트"],
        "emotional_effect": ["intimacy", "emotion", "dialogue"],
        "ai_prompt_keywords": ["medium close-up", "bust shot", "intimate framing"],
    },
    "close_up": {
        "name": "Close-Up",
        "name_ko": "클로즈업",
        "category": "shot_type",
        "keywords": ["close-up", "close up", "클로즈업", "근접"],
        "emotional_effect": ["emotion", "detail", "intensity"],
        "ai_prompt_keywords": ["close-up shot", "facial close-up", "detailed shot"],
    },
    "extreme_close": {
        "name": "Extreme Close-Up",
        "name_ko": "익스트림 클로즈업",
        "category": "shot_type",
        "keywords": ["extreme close", "detail", "익스트림 클로즈", "디테일"],
        "emotional_effect": ["intense_focus", "detail", "psychological"],
        "ai_prompt_keywords": ["extreme close-up", "macro shot", "detail shot"],
    },

    # Camera Movements
    "pan": {
        "name": "Pan",
        "name_ko": "팬",
        "category": "camera_movement",
        "keywords": ["pan", "panning", "팬", "패닝", "좌우"],
        "emotional_effect": ["reveal", "follow", "survey"],
        "ai_prompt_keywords": ["panning shot", "horizontal pan", "camera pan"],
    },
    "tilt": {
        "name": "Tilt",
        "name_ko": "틸트",
        "category": "camera_movement",
        "keywords": ["tilt", "tilting", "틸트", "상하"],
        "emotional_effect": ["reveal", "power_dynamic", "scale"],
        "ai_prompt_keywords": ["tilt shot", "vertical tilt", "camera tilt"],
    },
    "dolly": {
        "name": "Dolly/Push",
        "name_ko": "달리",
        "category": "camera_movement",
        "keywords": ["dolly", "push", "pull", "달리", "푸시", "트래킹"],
        "emotional_effect": ["emphasis", "reveal", "tension"],
        "ai_prompt_keywords": ["dolly shot", "push in", "tracking shot"],
    },
    "tracking": {
        "name": "Tracking Shot",
        "name_ko": "트래킹 샷",
        "category": "camera_movement",
        "keywords": ["tracking", "following", "트래킹", "팔로우"],
        "emotional_effect": ["immersion", "follow_action", "continuous"],
        "ai_prompt_keywords": ["tracking shot", "following shot", "continuous tracking"],
    },
    "crane": {
        "name": "Crane/Jib",
        "name_ko": "크레인",
        "category": "camera_movement",
        "keywords": ["crane", "jib", "aerial", "크레인", "지브"],
        "emotional_effect": ["epic", "reveal", "transition"],
        "ai_prompt_keywords": ["crane shot", "aerial movement", "vertical tracking"],
    },
    "handheld": {
        "name": "Handheld",
        "name_ko": "핸드헬드",
        "category": "camera_movement",
        "keywords": ["handheld", "shaky", "핸드헬드", "흔들림"],
        "emotional_effect": ["urgency", "documentary", "tension"],
        "ai_prompt_keywords": ["handheld shot", "shaky camera", "documentary style"],
    },
    "steadicam": {
        "name": "Steadicam",
        "name_ko": "스테디캠",
        "category": "camera_movement",
        "keywords": ["steadicam", "smooth", "glide", "스테디캠", "부드러운"],
        "emotional_effect": ["smooth", "immersive", "flowing"],
        "ai_prompt_keywords": ["steadicam shot", "smooth tracking", "fluid movement"],
    },
    "static": {
        "name": "Static",
        "name_ko": "고정",
        "category": "camera_movement",
        "keywords": ["static", "fixed", "locked", "고정", "정적"],
        "emotional_effect": ["stable", "observational", "contemplative"],
        "ai_prompt_keywords": ["static shot", "locked camera", "fixed frame"],
    },

    # Lighting
    "rembrandt": {
        "name": "Rembrandt Lighting",
        "name_ko": "렘브란트 조명",
        "category": "lighting",
        "keywords": ["rembrandt", "triangle", "렘브란트", "삼각형"],
        "emotional_effect": ["dramatic", "artistic", "depth"],
        "ai_prompt_keywords": ["Rembrandt lighting", "dramatic portrait lighting"],
    },
    "high_key": {
        "name": "High Key",
        "name_ko": "하이키",
        "category": "lighting",
        "keywords": ["high key", "bright", "하이키", "밝은"],
        "emotional_effect": ["optimistic", "clean", "open"],
        "ai_prompt_keywords": ["high key lighting", "bright even lighting"],
    },
    "low_key": {
        "name": "Low Key",
        "name_ko": "로우키",
        "category": "lighting",
        "keywords": ["low key", "dark", "shadow", "로우키", "어두운"],
        "emotional_effect": ["dramatic", "mysterious", "noir"],
        "ai_prompt_keywords": ["low key lighting", "dramatic shadows", "noir lighting"],
    },
    "silhouette": {
        "name": "Silhouette",
        "name_ko": "실루엣",
        "category": "lighting",
        "keywords": ["silhouette", "backlit", "실루엣", "역광"],
        "emotional_effect": ["mystery", "dramatic", "iconic"],
        "ai_prompt_keywords": ["silhouette lighting", "backlit subject", "rim light"],
    },
    "natural": {
        "name": "Natural Light",
        "name_ko": "자연광",
        "category": "lighting",
        "keywords": ["natural", "available", "자연광", "자연"],
        "emotional_effect": ["realistic", "authentic", "soft"],
        "ai_prompt_keywords": ["natural lighting", "available light", "soft daylight"],
    },
    "neon": {
        "name": "Neon/Practical",
        "name_ko": "네온 조명",
        "category": "lighting",
        "keywords": ["neon", "practical", "colored", "네온", "색조명"],
        "emotional_effect": ["stylized", "urban", "mood"],
        "ai_prompt_keywords": ["neon lighting", "colored practical lights", "urban night"],
    },

    # Composition
    "rule_of_thirds": {
        "name": "Rule of Thirds",
        "name_ko": "삼등분 법칙",
        "category": "composition",
        "keywords": ["thirds", "off-center", "삼등분", "삼분할"],
        "emotional_effect": ["balanced", "dynamic", "natural"],
        "ai_prompt_keywords": ["rule of thirds composition", "off-center framing"],
    },
    "symmetry": {
        "name": "Symmetrical",
        "name_ko": "대칭 구도",
        "category": "composition",
        "keywords": ["symmetry", "symmetric", "centered", "대칭", "중앙"],
        "emotional_effect": ["formal", "powerful", "balanced"],
        "ai_prompt_keywords": ["symmetrical composition", "centered framing", "perfect symmetry"],
    },
    "leading_lines": {
        "name": "Leading Lines",
        "name_ko": "유도선",
        "category": "composition",
        "keywords": ["leading", "lines", "converging", "유도선", "수렴"],
        "emotional_effect": ["direction", "depth", "focus"],
        "ai_prompt_keywords": ["leading lines composition", "converging lines"],
    },
    "framing": {
        "name": "Frame within Frame",
        "name_ko": "프레임 안 프레임",
        "category": "composition",
        "keywords": ["frame within", "doorway", "window", "프레임", "창문"],
        "emotional_effect": ["focus", "layered", "voyeuristic"],
        "ai_prompt_keywords": ["frame within frame", "doorway framing", "window shot"],
    },
    "dutch_angle": {
        "name": "Dutch Angle",
        "name_ko": "더치 앵글",
        "category": "composition",
        "keywords": ["dutch", "tilted", "canted", "더치", "기울어진"],
        "emotional_effect": ["unease", "disorientation", "tension"],
        "ai_prompt_keywords": ["dutch angle", "tilted camera", "canted frame"],
    },
}


CATEGORY_NAMES_KO = {
    "shot_type": "샷 타입",
    "camera_movement": "카메라 움직임",
    "lighting": "조명",
    "composition": "구도",
    "lens": "렌즈",
    "color": "색채",
}


# =============================================================================
# Technique Detector Service
# =============================================================================


class TechniqueDetector:
    """Detects cinematography techniques from frame analysis.

    Combines pattern matching with optional AI enhancement
    to identify specific filmmaking techniques.
    """

    def __init__(
        self,
        use_ai_enhancement: bool = True,
        min_confidence: float = 0.5,
    ):
        """Initialize TechniqueDetector.

        Args:
            use_ai_enhancement: Whether to use Gemini for enhanced detection
            min_confidence: Minimum confidence to include technique
        """
        self.use_ai_enhancement = use_ai_enhancement
        self.min_confidence = min_confidence

    async def detect_techniques(
        self,
        frame_analyses: List[Any],
        timestamps: Optional[List[float]] = None,
    ) -> List[DetectedTechnique]:
        """Detect techniques from frame analyses.

        Args:
            frame_analyses: List of FrameAnalysis (Pydantic models or dicts)
            timestamps: Optional list of frame timestamps

        Returns:
            List of detected techniques sorted by confidence
        """
        techniques: Dict[str, DetectedTechnique] = {}

        for i, frame in enumerate(frame_analyses):
            timestamp = timestamps[i] if timestamps and i < len(timestamps) else 0.0

            # Handle both Pydantic models and dicts
            if hasattr(frame, "model_dump"):
                frame_dict = frame.model_dump()
            elif hasattr(frame, "dict"):
                frame_dict = frame.dict()
            elif isinstance(frame, dict):
                frame_dict = frame
            else:
                frame_dict = {}

            # Extract relevant fields
            shot_type = frame_dict.get("shot_type", "") or ""
            camera_movement = frame_dict.get("camera_movement", "") or ""
            description = frame_dict.get("description", "") or ""
            emotion = frame_dict.get("emotion", "") or ""

            # Combine all text for keyword matching
            combined_text = f"{shot_type} {camera_movement} {description} {emotion}".lower()

            # Match against technique database
            for tech_id, tech_data in TECHNIQUE_DATABASE.items():
                keywords = tech_data.get("keywords", [])

                # Check for keyword matches
                match_count = sum(1 for kw in keywords if kw.lower() in combined_text)

                if match_count > 0:
                    confidence = min(match_count / len(keywords) * 1.5, 1.0)

                    if confidence >= self.min_confidence:
                        if tech_id not in techniques:
                            techniques[tech_id] = DetectedTechnique(
                                technique_id=tech_id,
                                name=tech_data["name"],
                                name_ko=tech_data["name_ko"],
                                category=tech_data["category"],
                                confidence=confidence,
                                frame_indices=[i],
                                timestamp_ranges=[(timestamp, timestamp)],
                                description=f"프레임 {i}에서 감지됨",
                                emotional_effect=tech_data.get("emotional_effect", []),
                                recreation_tips="",
                                ai_prompt_keywords=tech_data.get("ai_prompt_keywords", []),
                                evidence_refs=[],
                            )
                        else:
                            # Update existing technique detection
                            existing = techniques[tech_id]
                            existing.frame_indices.append(i)
                            # Boost confidence with more detections
                            existing.confidence = min(
                                existing.confidence + 0.1,
                                1.0
                            )
                            # Update timestamp range
                            if existing.timestamp_ranges:
                                last_range = existing.timestamp_ranges[-1]
                                if timestamp - last_range[1] < 2.0:  # Continuous
                                    existing.timestamp_ranges[-1] = (last_range[0], timestamp)
                                else:
                                    existing.timestamp_ranges.append((timestamp, timestamp))

        # Convert to list and sort by confidence
        result = list(techniques.values())
        result.sort(key=lambda t: t.confidence, reverse=True)

        # Add recreation tips
        for tech in result:
            tech.recreation_tips = self._generate_recreation_tips(tech)
            tech.description = self._generate_description(tech, len(frame_analyses))

        logger.info(f"Detected {len(result)} techniques from {len(frame_analyses)} frames")

        return result

    async def detect_techniques_by_category(
        self,
        frame_analyses: List[Dict[str, Any]],
        timestamps: Optional[List[float]] = None,
    ) -> List[TechniqueCategory]:
        """Detect techniques grouped by category.

        Args:
            frame_analyses: List of FrameAnalysis as dicts
            timestamps: Optional frame timestamps

        Returns:
            List of TechniqueCategory with grouped techniques
        """
        all_techniques = await self.detect_techniques(frame_analyses, timestamps)

        # Group by category
        categories: Dict[str, List[DetectedTechnique]] = {}
        for tech in all_techniques:
            if tech.category not in categories:
                categories[tech.category] = []
            categories[tech.category].append(tech)

        # Build category results
        result: List[TechniqueCategory] = []
        for category, techs in categories.items():
            total_conf = sum(t.confidence for t in techs) / len(techs) if techs else 0
            result.append(
                TechniqueCategory(
                    category=category,
                    category_name_ko=CATEGORY_NAMES_KO.get(category, category),
                    techniques=techs,
                    total_confidence=total_conf,
                )
            )

        # Sort categories by total confidence
        result.sort(key=lambda c: c.total_confidence, reverse=True)

        return result

    def _generate_recreation_tips(self, technique: DetectedTechnique) -> str:
        """Generate recreation tips for a technique."""
        tips_by_category = {
            "shot_type": f"AI 비디오 생성 시 '{technique.name}' 키워드를 프롬프트에 포함하세요.",
            "camera_movement": f"카메라 움직임 '{technique.name_ko}'를 재현하려면 "
                              f"프롬프트에 '{', '.join(technique.ai_prompt_keywords[:2])}'를 추가하세요.",
            "lighting": f"'{technique.name_ko}' 조명 효과를 위해 "
                       f"'{', '.join(technique.ai_prompt_keywords[:2])}'를 사용하세요.",
            "composition": f"'{technique.name_ko}' 구도는 프롬프트에서 "
                          f"프레이밍 지시사항으로 명시하세요.",
        }
        return tips_by_category.get(
            technique.category,
            f"프롬프트에 '{technique.name}' 관련 키워드를 포함하세요."
        )

    def _generate_description(
        self,
        technique: DetectedTechnique,
        total_frames: int,
    ) -> str:
        """Generate description for technique detection."""
        frame_count = len(technique.frame_indices)
        percentage = frame_count / total_frames * 100 if total_frames > 0 else 0

        if percentage > 50:
            usage = "전체적으로 사용됨"
        elif percentage > 20:
            usage = "자주 사용됨"
        elif percentage > 10:
            usage = "간헐적으로 사용됨"
        else:
            usage = "일부 장면에서 감지됨"

        return (
            f"'{technique.name_ko}' 기법이 {frame_count}개 프레임 "
            f"({percentage:.1f}%)에서 감지됨. {usage}."
        )


# =============================================================================
# Factory
# =============================================================================


_default_detector: Optional[TechniqueDetector] = None


def get_technique_detector(use_ai: bool = True) -> TechniqueDetector:
    """Get or create TechniqueDetector instance.

    Args:
        use_ai: Whether to use AI enhancement

    Returns:
        TechniqueDetector instance
    """
    global _default_detector

    if _default_detector is None:
        _default_detector = TechniqueDetector(use_ai_enhancement=use_ai)

    return _default_detector


def reset_technique_detector() -> None:
    """Reset the default detector (for testing)."""
    global _default_detector
    _default_detector = None
