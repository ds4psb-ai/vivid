"""Auteur Matcher Service for 4D Reference Decoder.

Matches visual styles and techniques to known auteur (director) styles
using the Vivid RAG system and auteur knowledge base.

2026 Best Practices:
- Hybrid RAG integration (NotebookLM + Qdrant)
- Style vector similarity matching
- Evidence-backed recommendations

Usage:
    from app.services.ai.auteur_matcher import get_auteur_matcher

    matcher = get_auteur_matcher()
    matches = await matcher.match_style_to_auteurs(style_result)
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Models
# =============================================================================


class AuteurMatch(BaseModel):
    """A matched auteur (director) with similarity details."""

    auteur_key: str = Field(description="Auteur identifier (e.g., 'bong', 'nolan')")
    auteur_name: str = Field(description="Full name (e.g., 'Bong Joon-ho')")
    similarity_score: float = Field(ge=0.0, le=1.0, description="Style similarity score")
    matching_techniques: List[str] = Field(
        default_factory=list,
        description="Techniques that match this auteur's style"
    )
    matching_moods: List[str] = Field(
        default_factory=list,
        description="Moods that match this auteur's films"
    )
    signature_elements: List[str] = Field(
        default_factory=list,
        description="Signature visual elements of this auteur"
    )
    recommended_films: List[str] = Field(
        default_factory=list,
        description="Films to reference for this style"
    )
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="RAG evidence references"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        default=0.0,
        description="Match confidence"
    )


class AuteurTechnique(BaseModel):
    """A technique associated with an auteur."""

    technique_id: str = Field(description="Technique identifier")
    name: str = Field(description="Technique name")
    category: str = Field(description="Category (camera, lighting, etc.)")
    auteur_key: str = Field(default="", description="Auteur this technique belongs to")
    description: str = Field(default="", description="How this auteur uses it")
    frequency: str = Field(
        default="common",
        description="How often used: signature, common, occasional"
    )
    example_films: List[str] = Field(
        default_factory=list,
        description="Films featuring this technique"
    )


# =============================================================================
# Auteur Registry
# =============================================================================


# AI Auteur Persona Registry (법적 안전성 + 창의적 자유)
AUTEUR_REGISTRY: Dict[str, Dict[str, Any]] = {
    "kang": {
        "name": "Kang Juno",
        "name_ko": "강주노",
        "signature_techniques": [
            "staircase_symbolism", "class_contrast", "genre_mixing",
            "long_take", "deep_focus", "dutch_angle"
        ],
        "signature_moods": [
            "satirical", "dark_comedy", "suspenseful", "social_commentary"
        ],
        "signature_elements": [
            "계층 상징", "계단 모티프", "반전 장치", "현실적 대사"
        ],
        "color_palettes": [
            ["#2C3E50", "#BDC3C7", "#95A5A6"],
            ["#F1C40F", "#E74C3C", "#2ECC71"],
        ],
        "films": ["The Vertical Divide", "Threshold Society", "Mirrored Class"],
    },
    "epoch": {
        "name": "Theo Epoch",
        "name_ko": "테오 에포크",
        "signature_techniques": [
            "practical_effects", "imax_cinematography", "non_linear_narrative",
            "extreme_close_up", "cross_cutting", "natural_lighting"
        ],
        "signature_moods": [
            "cerebral", "epic", "tense", "philosophical"
        ],
        "signature_elements": [
            "시간 조작", "실제 촬영", "IMAX 대형 포맷", "웅장한 스코어"
        ],
        "color_palettes": [
            ["#1A1A2E", "#16213E", "#0F3460"],
            ["#E8D5B7", "#B8860B", "#8B7355"],
        ],
        "films": ["Temporal Fold", "The Fifth Dimension", "Gravity's Edge"],
    },
    "velvet": {
        "name": "Ren Velvet",
        "name_ko": "렌 벨벳",
        "signature_techniques": [
            "step_printing", "slow_motion", "handheld_camera",
            "neon_lighting", "reflections", "window_framing"
        ],
        "signature_moods": [
            "melancholic", "romantic", "nostalgic", "dreamlike"
        ],
        "signature_elements": [
            "네온 조명", "비 내리는 거리", "담배 연기", "거울/창문 반사"
        ],
        "color_palettes": [
            ["#FF6B6B", "#4ECDC4", "#2C3E50"],
            ["#C0392B", "#1ABC9C", "#9B59B6"],
        ],
        "films": ["Neon Corridor", "Midnight Rain", "2AM Stories"],
    },
    "voltage": {
        "name": "Rex Voltage",
        "name_ko": "렉스 볼티지",
        "signature_techniques": [
            "trunk_shot", "mexican_standoff", "chapter_structure",
            "long_dialogue", "feet_shot", "low_angle"
        ],
        "signature_moods": [
            "stylized_violence", "dark_humor", "retro", "tense_dialogue"
        ],
        "signature_elements": [
            "챕터 구조", "긴 대화 씬", "팝컬처 레퍼런스", "비선형 서사"
        ],
        "color_palettes": [
            ["#8B0000", "#FFD700", "#000000"],
            ["#2F4F4F", "#8B4513", "#DAA520"],
        ],
        "films": ["Voltage Rising", "Chapter Zero", "Blood Dialogue"],
    },
    "yoon": {
        "name": "Yoon Suha",
        "name_ko": "윤수하",
        "signature_techniques": [
            "symmetrical_composition", "long_take_violence", "color_coding",
            "tracking_shot", "split_screen", "mirror_shots"
        ],
        "signature_moods": [
            "revenge", "grotesque_beauty", "operatic", "psychological"
        ],
        "signature_elements": [
            "대칭 구도", "색채 코드", "복수 서사", "오페라틱 폭력"
        ],
        "color_palettes": [
            ["#006400", "#8B0000", "#FFD700"],
            ["#4B0082", "#800020", "#2F4F4F"],
        ],
        "films": ["Obsidian Mirror", "The Elegant Revenge", "Crimson Silk"],
    },
    "abyss": {
        "name": "Orion Abyss",
        "name_ko": "오리온 어비스",
        "signature_techniques": [
            "aerial_shots", "minimal_dialogue", "deakins_lighting",
            "wide_angle", "symmetry", "slow_reveal"
        ],
        "signature_moods": [
            "atmospheric", "meditative", "ominous", "epic_scale"
        ],
        "signature_elements": [
            "광활한 공간", "미니멀 대사", "시네마틱 촬영", "앰비언트 스코어"
        ],
        "color_palettes": [
            ["#C19A6B", "#8B7355", "#696969"],
            ["#2F4F4F", "#708090", "#A9A9A9"],
        ],
        "films": ["The Void Protocol", "Sand Empire", "First Contact"],
    },
    "azure": {
        "name": "Sora Azure",
        "name_ko": "소라 아주르",
        "signature_techniques": [
            "lens_flare", "rain_animation", "cloud_timelapse",
            "light_beam", "reflection_detail", "train_scenes"
        ],
        "signature_moods": [
            "bittersweet", "romantic_longing", "nostalgic", "magical_realism"
        ],
        "signature_elements": [
            "빛 표현", "구름 묘사", "비 애니메이션", "거리와 시간"
        ],
        "color_palettes": [
            ["#87CEEB", "#FFB6C1", "#FFA07A"],
            ["#4169E1", "#00CED1", "#FFFFFF"],
        ],
        "films": ["Azure Crossing", "Light Years Apart", "Cloud Memories"],
    },
    "prism": {
        "name": "Milo Prism",
        "name_ko": "마일로 프리즘",
        "signature_techniques": [
            "one_point_perspective", "long_take", "symmetrical_composition",
            "wide_angle", "steadicam", "practical_lighting"
        ],
        "signature_moods": [
            "cold_observation", "human_nature", "perfectionist", "unsettling"
        ],
        "signature_elements": [
            "원포인트 원근법", "롱 테이크", "대칭 구도", "불안한 정적"
        ],
        "color_palettes": [
            ["#FFFFFF", "#FF0000", "#000000"],
            ["#2D3436", "#636E72", "#B2BEC3"],
        ],
        "films": ["Geometric Madness", "The Perfect Frame", "Symmetry"],
    },
    "seoyeon": {
        "name": "Min Seoyeon",
        "name_ko": "민서연",
        "signature_techniques": [
            "handheld_camera", "natural_lighting", "intense_editing",
            "close_up", "long_take", "real_locations"
        ],
        "signature_moods": [
            "raw_realism", "suspenseful", "psychological_horror", "relentless"
        ],
        "signature_elements": [
            "핸드헬드 카메라", "자연광", "긴박한 편집", "로케이션 촬영"
        ],
        "color_palettes": [
            ["#1A1A1A", "#2D2D2D", "#4A4A4A"],
            ["#8B0000", "#2F2F2F", "#5C5C5C"],
        ],
        "films": ["Tempest Village", "The Chase", "Raw Tension"],
    },
}


# =============================================================================
# Auteur Matcher Service
# =============================================================================


class AuteurMatcher:
    """Matches visual styles to auteur (director) signatures.

    Uses style analysis results to find matching auteurs through:
    1. Technique matching (camera, lighting, composition)
    2. Mood/tone alignment
    3. Color palette similarity
    4. RAG-enhanced knowledge lookup
    """

    def __init__(
        self,
        use_rag: bool = True,
        min_similarity_threshold: float = 0.3,
    ):
        """Initialize AuteurMatcher.

        Args:
            use_rag: Whether to use RAG for enhanced matching
            min_similarity_threshold: Minimum score to include match
        """
        self.use_rag = use_rag
        self.min_similarity_threshold = min_similarity_threshold
        self._rag_cache: Dict[str, Any] = {}

    async def match_style_to_auteurs(
        self,
        style_result: Dict[str, Any],
        max_matches: int = 3,
    ) -> List[AuteurMatch]:
        """Match a style extraction result to auteurs.

        Args:
            style_result: StyleExtractionResult (Pydantic model or dict)
            max_matches: Maximum number of matches to return

        Returns:
            List of AuteurMatch sorted by similarity score
        """
        matches: List[AuteurMatch] = []

        # Handle both Pydantic models and dicts
        if hasattr(style_result, "model_dump"):
            style_dict = style_result.model_dump()
        elif hasattr(style_result, "dict"):
            style_dict = style_result.dict()
        elif isinstance(style_result, dict):
            style_dict = style_result
        else:
            style_dict = {}

        # Extract style attributes
        style_tags = style_dict.get("style_tags", []) or []
        color_palette = style_dict.get("color_palette", []) or []
        lighting = style_dict.get("lighting_style", "") or style_dict.get("lighting", "") or ""
        mood = style_dict.get("mood", "") or ""
        composition = style_dict.get("composition_style", "") or style_dict.get("composition", "") or ""

        # Score each auteur
        for auteur_key, auteur_data in AUTEUR_REGISTRY.items():
            score = 0.0
            matching_techniques: List[str] = []
            matching_moods: List[str] = []

            # Technique matching (40% weight)
            signature_techniques = auteur_data.get("signature_techniques", [])
            for technique in signature_techniques:
                # Check if any style tag matches the technique
                technique_words = technique.replace("_", " ").lower().split()
                for tag in style_tags:
                    if any(word in tag.lower() for word in technique_words):
                        matching_techniques.append(technique)
                        score += 0.4 / len(signature_techniques)
                        break

            # Mood matching (30% weight)
            signature_moods = auteur_data.get("signature_moods", [])
            mood_lower = mood.lower() if mood else ""
            for sig_mood in signature_moods:
                sig_mood_words = sig_mood.replace("_", " ").lower().split()
                if any(word in mood_lower for word in sig_mood_words):
                    matching_moods.append(sig_mood)
                    score += 0.3 / len(signature_moods)

            # Color palette similarity (20% weight)
            if color_palette:
                color_score = self._calculate_color_similarity(
                    color_palette,
                    auteur_data.get("color_palettes", []),
                )
                score += color_score * 0.2

            # Lighting/composition bonus (10% weight)
            signature_elements = auteur_data.get("signature_elements", [])
            lighting_lower = lighting.lower() if lighting else ""
            composition_lower = composition.lower() if composition else ""
            for element in signature_elements:
                element_lower = element.lower()
                if element_lower in lighting_lower or element_lower in composition_lower:
                    score += 0.1 / len(signature_elements)

            # Only include if above threshold
            if score >= self.min_similarity_threshold:
                match = AuteurMatch(
                    auteur_key=auteur_key,
                    auteur_name=auteur_data.get("name", auteur_key),
                    similarity_score=min(score, 1.0),
                    matching_techniques=matching_techniques[:5],
                    matching_moods=matching_moods[:3],
                    signature_elements=auteur_data.get("signature_elements", [])[:4],
                    recommended_films=auteur_data.get("films", [])[:3],
                    evidence_refs=[],
                    confidence=min(score, 1.0),
                )
                matches.append(match)

        # Sort by score descending
        matches.sort(key=lambda m: m.similarity_score, reverse=True)
        matches = matches[:max_matches]

        # Enhance with RAG if enabled
        if self.use_rag and matches:
            matches = await self._enhance_with_rag(matches, style_result)

        logger.info(
            f"Matched style to {len(matches)} auteurs | "
            f"top_match={matches[0].auteur_name if matches else 'none'}"
        )

        return matches

    async def get_auteur_techniques(
        self,
        auteur_key: str,
        category: Optional[str] = None,
    ) -> List[AuteurTechnique]:
        """Get techniques associated with an auteur.

        Args:
            auteur_key: Auteur identifier
            category: Optional category filter

        Returns:
            List of AuteurTechnique
        """
        auteur_data = AUTEUR_REGISTRY.get(auteur_key)
        if not auteur_data:
            return []

        techniques: List[AuteurTechnique] = []
        signature_techniques = auteur_data.get("signature_techniques", [])
        films = auteur_data.get("films", [])

        for i, technique_id in enumerate(signature_techniques):
            # Determine category from technique name
            if any(x in technique_id for x in ["shot", "angle", "tracking"]):
                tech_category = "camera_movement"
            elif any(x in technique_id for x in ["lighting", "color"]):
                tech_category = "lighting"
            elif any(x in technique_id for x in ["composition", "framing", "symmetry"]):
                tech_category = "composition"
            else:
                tech_category = "technique"

            if category and tech_category != category:
                continue

            technique = AuteurTechnique(
                technique_id=technique_id,
                name=technique_id.replace("_", " ").title(),
                category=tech_category,
                auteur_key=auteur_key,
                description=f"{auteur_data['name']}의 시그니처 기법",
                frequency="signature" if i < 3 else "common",
                example_films=films[:2],
            )
            techniques.append(technique)

        return techniques

    def _calculate_color_similarity(
        self,
        input_colors: List[str],
        auteur_palettes: List[List[str]],
    ) -> float:
        """Calculate color palette similarity.

        Args:
            input_colors: Input color palette (hex codes)
            auteur_palettes: Auteur's signature palettes

        Returns:
            Similarity score 0.0-1.0
        """
        if not input_colors or not auteur_palettes:
            return 0.0

        max_similarity = 0.0

        for palette in auteur_palettes:
            # Simple color distance calculation
            similarity = 0.0
            matches = 0

            for input_color in input_colors[:3]:
                for palette_color in palette:
                    try:
                        # Convert hex to RGB and calculate distance
                        r1, g1, b1 = self._hex_to_rgb(input_color)
                        r2, g2, b2 = self._hex_to_rgb(palette_color)

                        # Euclidean distance normalized
                        distance = (
                            (r1 - r2) ** 2 +
                            (g1 - g2) ** 2 +
                            (b1 - b2) ** 2
                        ) ** 0.5

                        # Convert distance to similarity (max distance ~441)
                        color_sim = max(0, 1 - distance / 441)
                        if color_sim > 0.7:  # Consider it a match if > 70% similar
                            matches += 1
                            similarity += color_sim
                            break
                    except (ValueError, TypeError):
                        continue

            if matches > 0:
                palette_similarity = similarity / max(len(input_colors), 1)
                max_similarity = max(max_similarity, palette_similarity)

        return max_similarity

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    async def _enhance_with_rag(
        self,
        matches: List[AuteurMatch],
        style_result: Dict[str, Any],
    ) -> List[AuteurMatch]:
        """Enhance matches with RAG evidence.

        Args:
            matches: Initial auteur matches
            style_result: Original style result

        Returns:
            Enhanced matches with evidence_refs
        """
        try:
            from app.rag.hybrid_rag import hybrid_query

            for match in matches:
                # Query RAG for auteur style information
                query = (
                    f"{match.auteur_name} 감독 스타일 특징 "
                    f"{' '.join(match.matching_techniques[:2])}"
                )

                result = await hybrid_query(
                    query=query,
                    auteur_key=match.auteur_key,
                    dimension="AD",
                    use_semantic_cache=True,
                )

                if result.notebooklm_sources:
                    # Add evidence refs
                    for source in result.notebooklm_sources[:2]:
                        ref = f"rag:notebooklm:auteur:{match.auteur_key}:{source.source_id}"
                        match.evidence_refs.append(ref)

                    # Boost confidence based on RAG grounding
                    if result.grounded:
                        match.confidence = min(1.0, match.confidence + 0.1)

        except Exception as e:
            logger.warning(f"RAG enhancement failed: {e}")

        return matches


# =============================================================================
# Factory
# =============================================================================


_default_matcher: Optional[AuteurMatcher] = None


def get_auteur_matcher(use_rag: bool = True) -> AuteurMatcher:
    """Get or create AuteurMatcher instance.

    Args:
        use_rag: Whether to use RAG enhancement

    Returns:
        AuteurMatcher instance
    """
    global _default_matcher

    if _default_matcher is None:
        _default_matcher = AuteurMatcher(use_rag=use_rag)

    return _default_matcher


def reset_auteur_matcher() -> None:
    """Reset the default matcher (for testing)."""
    global _default_matcher
    _default_matcher = None
