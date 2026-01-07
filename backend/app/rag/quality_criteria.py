"""
Quality Criteria: 7-Dimension Quality Evaluation Framework.

Crebit 콘텐츠 품질을 7개 차원으로 평가하는 프레임워크.
각 차원별 가중치가 정의되어 있으며, 총합은 1.0.

품질 승격 조건 (is_promotion_eligible):
1. overall >= 0.85
2. user_accepted == True

Usage:
    from app.rag.quality_criteria import QualityCriteria, DIMENSION_TECHNICAL_CRITERIA

    criteria = QualityCriteria(
        coherence=0.9,
        completeness=0.85,
        creativity=0.8,
        style_adherence=0.9,
        tone_match=0.85,
        technical_score=0.88,
        user_rating=4.5,
    )

    if criteria.is_promotion_eligible:
        await store_success_pattern(...)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


# ============================================================================
# Quality Dimension Weights
# ============================================================================

QUALITY_WEIGHTS = {
    "coherence": 0.15,        # 논리적 일관성
    "completeness": 0.15,     # 요청 완전 충족
    "creativity": 0.10,       # 창의성/독창성
    "style_adherence": 0.20,  # 스타일 가이드 준수
    "tone_match": 0.10,       # 톤/무드 일치
    "technical_score": 0.20,  # 기술적 품질
    "user_rating": 0.10,      # 사용자 평가 (1-5 → 0-1 정규화)
}

# 가중치 합 검증 (반올림 오차 허용)
assert abs(sum(QUALITY_WEIGHTS.values()) - 1.0) < 0.001, "Weights must sum to 1.0"


# ============================================================================
# Dimension-specific Technical Criteria
# ============================================================================

DIMENSION_TECHNICAL_CRITERIA: Dict[str, Dict[str, str]] = {
    "1D": {
        "name": "Veo Prompt (Origin)",
        "criteria": [
            "프롬프트 명확성 (ambiguity-free)",
            "Veo API 호환 포맷",
            "시각적 디테일 충분성",
            "카메라 무브먼트 명세",
            "시간 흐름 지시 (if applicable)",
        ],
        "min_length": 50,
        "max_length": 2000,
    },
    "2D": {
        "name": "Storyboard (Blueprint)",
        "criteria": [
            "씬 순서 논리성",
            "씬별 목적 명확성",
            "전환 연결성",
            "타이밍 현실성",
            "시각적 연속성",
        ],
        "min_scenes": 3,
        "max_scenes": 20,
    },
    "3D": {
        "name": "Image Prompt (Ambience)",
        "criteria": [
            "스타일 키워드 정확성",
            "색상 팔레트 일관성",
            "조명 디렉션 명확성",
            "구도 지시 구체성",
            "무드 전달력",
        ],
        "required_fields": ["style_tags", "color_palette", "lighting"],
    },
    "4D": {
        "name": "Reference Analysis (Moment)",
        "criteria": [
            "분석 깊이",
            "기법 식별 정확성",
            "시각 언어 해석",
            "적용 가능성",
            "출처 명시",
        ],
        "min_techniques": 2,
    },
    "QC": {
        "name": "Quality Check",
        "criteria": [
            "평가 객관성",
            "개선 제안 구체성",
            "기준 일관성",
            "점수 정당화",
            "VDG 표준 준수",
        ],
        "required_scores": ["aesthetic", "technical", "narrative"],
    },
    "AD": {
        "name": "Aesthetic Director",
        "criteria": [
            "스타일 가이드라인 명확성",
            "Auteur DNA 일치도",
            "실행 가능성",
            "시각적 일관성",
            "창의적 해석",
        ],
        "auteur_match_threshold": 0.7,
    },
    "AI": {
        "name": "Abyss Interpreter (Persona)",
        "criteria": [
            "페르소나 깊이",
            "분석 근거 명확성",
            "통찰 독창성",
            "적용 가능성",
            "프라이버시 존중",
        ],
        "depth_levels": ["quick", "standard", "deep"],
    },
    "VEO": {
        "name": "Veo Video Generation",
        "criteria": [
            "프롬프트 품질",
            "비디오 해상도",
            "모션 자연스러움",
            "오디오 동기화 (if applicable)",
            "아티팩트 최소화",
        ],
        "min_duration_sec": 2,
        "max_duration_sec": 16,
    },
}


# ============================================================================
# Quality Criteria Dataclass
# ============================================================================

@dataclass
class QualityCriteria:
    """7차원 품질 평가 기준.

    Attributes:
        coherence: 논리적 일관성 (0-1)
        completeness: 요청 완전 충족도 (0-1)
        creativity: 창의성/독창성 (0-1)
        style_adherence: 스타일 가이드 준수도 (0-1)
        tone_match: 톤/무드 일치도 (0-1)
        technical_score: 기술적 품질 점수 (0-1)
        user_rating: 사용자 평가 (1-5, 내부적으로 0-1 정규화)
        user_accepted: 사용자 명시적 승인 여부
        dimension: 평가 대상 차원
        evaluated_at: 평가 시간
        metadata: 추가 메타데이터
    """
    coherence: float = 0.0
    completeness: float = 0.0
    creativity: float = 0.0
    style_adherence: float = 0.0
    tone_match: float = 0.0
    technical_score: float = 0.0
    user_rating: float = 0.0  # 1-5 scale, will be normalized
    user_accepted: bool = False
    dimension: Optional[str] = None
    evaluated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and normalize scores."""
        # Clamp all scores to [0, 1]
        self.coherence = max(0.0, min(1.0, self.coherence))
        self.completeness = max(0.0, min(1.0, self.completeness))
        self.creativity = max(0.0, min(1.0, self.creativity))
        self.style_adherence = max(0.0, min(1.0, self.style_adherence))
        self.tone_match = max(0.0, min(1.0, self.tone_match))
        self.technical_score = max(0.0, min(1.0, self.technical_score))

        # Normalize user_rating from 1-5 to 0-1 if needed
        if self.user_rating > 1.0:
            self.user_rating = (self.user_rating - 1) / 4.0  # 1-5 → 0-1
        self.user_rating = max(0.0, min(1.0, self.user_rating))

    @property
    def overall(self) -> float:
        """Calculate weighted overall score.

        Returns:
            Weighted average of all dimensions (0-1)
        """
        return (
            self.coherence * QUALITY_WEIGHTS["coherence"] +
            self.completeness * QUALITY_WEIGHTS["completeness"] +
            self.creativity * QUALITY_WEIGHTS["creativity"] +
            self.style_adherence * QUALITY_WEIGHTS["style_adherence"] +
            self.tone_match * QUALITY_WEIGHTS["tone_match"] +
            self.technical_score * QUALITY_WEIGHTS["technical_score"] +
            self.user_rating * QUALITY_WEIGHTS["user_rating"]
        )

    @property
    def is_promotion_eligible(self) -> bool:
        """Check if this result is eligible for pattern promotion.

        Promotion requires BOTH:
        1. overall >= 0.85
        2. user_accepted == True

        Returns:
            True if eligible for promotion
        """
        return self.overall >= 0.85 and self.user_accepted

    @property
    def is_indexable(self) -> bool:
        """Check if this result should be indexed to RAG.

        Indexing requires:
        - overall >= 0.70 (lower threshold than promotion)

        Returns:
            True if should be indexed
        """
        return self.overall >= 0.70

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "coherence": self.coherence,
            "completeness": self.completeness,
            "creativity": self.creativity,
            "style_adherence": self.style_adherence,
            "tone_match": self.tone_match,
            "technical_score": self.technical_score,
            "user_rating": self.user_rating,
            "user_accepted": self.user_accepted,
            "overall": self.overall,
            "is_promotion_eligible": self.is_promotion_eligible,
            "is_indexable": self.is_indexable,
            "dimension": self.dimension,
            "evaluated_at": self.evaluated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityCriteria":
        """Create from dictionary.

        Args:
            data: Dictionary with quality scores

        Returns:
            QualityCriteria instance
        """
        return cls(
            coherence=data.get("coherence", 0.0),
            completeness=data.get("completeness", 0.0),
            creativity=data.get("creativity", 0.0),
            style_adherence=data.get("style_adherence", 0.0),
            tone_match=data.get("tone_match", 0.0),
            technical_score=data.get("technical_score", 0.0),
            user_rating=data.get("user_rating", 0.0),
            user_accepted=data.get("user_accepted", False),
            dimension=data.get("dimension"),
            metadata=data.get("metadata", {}),
        )

    def get_weakest_dimension(self) -> tuple[str, float]:
        """Get the weakest quality dimension.

        Returns:
            Tuple of (dimension_name, score)
        """
        scores = {
            "coherence": self.coherence,
            "completeness": self.completeness,
            "creativity": self.creativity,
            "style_adherence": self.style_adherence,
            "tone_match": self.tone_match,
            "technical_score": self.technical_score,
            "user_rating": self.user_rating,
        }
        weakest = min(scores.items(), key=lambda x: x[1])
        return weakest

    def get_improvement_suggestions(self) -> list[str]:
        """Get suggestions for improving quality.

        Returns:
            List of improvement suggestions
        """
        suggestions = []
        threshold = 0.7

        if self.coherence < threshold:
            suggestions.append("논리적 흐름과 일관성을 개선하세요")
        if self.completeness < threshold:
            suggestions.append("요청 사항을 더 완전히 충족하세요")
        if self.creativity < threshold:
            suggestions.append("더 독창적인 접근을 시도하세요")
        if self.style_adherence < threshold:
            suggestions.append("스타일 가이드를 더 정확히 따르세요")
        if self.tone_match < threshold:
            suggestions.append("목표 톤과 무드에 맞추세요")
        if self.technical_score < threshold:
            suggestions.append("기술적 품질을 높이세요")

        if not self.user_accepted:
            suggestions.append("사용자 승인이 필요합니다")

        return suggestions


# ============================================================================
# Quality Level Classification
# ============================================================================

def classify_quality_level(overall: float) -> str:
    """Classify quality level based on overall score.

    Args:
        overall: Overall quality score (0-1)

    Returns:
        Quality level string
    """
    if overall >= 0.90:
        return "excellent"
    elif overall >= 0.85:
        return "very_good"
    elif overall >= 0.75:
        return "good"
    elif overall >= 0.60:
        return "acceptable"
    elif overall >= 0.40:
        return "needs_improvement"
    else:
        return "poor"


def get_dimension_criteria(dimension: str) -> Dict[str, Any]:
    """Get technical criteria for a specific dimension.

    Args:
        dimension: Dimension code (1D, 2D, ..., AD, QC, etc.)

    Returns:
        Dictionary with dimension-specific criteria
    """
    return DIMENSION_TECHNICAL_CRITERIA.get(dimension, {})
