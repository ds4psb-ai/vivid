"""
UQSL Models - Pydantic v2 Models for Quality Selection

2026 Best Practice:
- Pydantic v2 computed_field for derived values
- Strict typing with Literal types
- JSON Schema compatible for API docs
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field, computed_field


class QualityDimension(str, Enum):
    """Quality evaluation dimensions"""
    GROUNDEDNESS = "groundedness"
    RELEVANCE = "relevance"
    COHERENCE = "coherence"
    CREATIVITY = "creativity"
    SAFETY = "safety"


class QualityScore(BaseModel):
    """
    품질 평가 결과 (2026 Best Practice: Pydantic v2 computed_field)

    Each score is normalized to [0, 1] range.
    """
    groundedness: float = Field(ge=0, le=1, description="거장 DNA 기반 그라운딩")
    relevance: float = Field(ge=0, le=1, description="RAG 관련도")
    coherence: float = Field(ge=0, le=1, description="일관성")
    creativity: float = Field(ge=0, le=1, description="창의성")
    safety: float = Field(ge=0, le=1, description="안전성")

    # Custom weights (can be overridden per-app)
    _weights: dict[str, float] = {
        "groundedness": 0.30,
        "relevance": 0.25,
        "coherence": 0.20,
        "creativity": 0.15,
        "safety": 0.10,
    }

    @computed_field
    @property
    def total_score(self) -> float:
        """가중 평균 총점 (앱별 커스터마이징 가능)"""
        return (
            self.groundedness * self._weights["groundedness"] +
            self.relevance * self._weights["relevance"] +
            self.coherence * self._weights["coherence"] +
            self.creativity * self._weights["creativity"] +
            self.safety * self._weights["safety"]
        )

    def with_weights(self, weights: dict[str, float]) -> "QualityScore":
        """Create a copy with custom weights"""
        new_score = self.model_copy()
        new_score._weights = {**self._weights, **weights}
        return new_score

    class Config:
        json_schema_extra = {
            "example": {
                "groundedness": 0.85,
                "relevance": 0.90,
                "coherence": 0.80,
                "creativity": 0.75,
                "safety": 0.95,
            }
        }


class CandidateResult(BaseModel):
    """생성 후보 결과"""
    idx: int = Field(description="Candidate index (0-based)")
    content: str = Field(description="Generated content")
    metadata: dict = Field(default_factory=dict, description="Generation metadata")
    quality_score: Optional[QualityScore] = Field(default=None, description="Quality evaluation score")
    latency_ms: int = Field(default=0, description="Generation latency in milliseconds")
    backend_used: str = Field(default="default", description="Backend identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "idx": 0,
                "content": "A cinematic shot of a sunset over the ocean...",
                "metadata": {"seed": 42, "run_id": "abc-123"},
                "latency_ms": 1500,
                "backend_used": "qdrant_hybrid",
            }
        }


class SelectionResult(BaseModel):
    """최종 선택 결과"""
    session_id: str = Field(description="Unique session identifier")
    selected: CandidateResult = Field(description="Selected candidate")
    method: Literal["auto", "hitl", "hybrid", "llm_judge"] = Field(description="Selection method used")
    confidence: float = Field(ge=0, le=1, description="Selection confidence score")
    arms_used: list[str] = Field(default_factory=list, description="Thompson Sampling arms used")
    all_candidates: list[CandidateResult] = Field(default_factory=list, description="All generated candidates")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "uqsl-sess-abc123",
                "selected": {
                    "idx": 1,
                    "content": "Best candidate content...",
                    "latency_ms": 1200,
                    "backend_used": "notebooklm",
                },
                "method": "hybrid",
                "confidence": 0.87,
                "arms_used": ["backend:qdrant_hybrid", "backend:notebooklm"],
            }
        }


class UQSLConfig(BaseModel):
    """App-level UQSL Configuration"""
    app_key: str = Field(description="Unique app identifier")
    n_candidates: int = Field(default=3, ge=1, le=5, description="Number of candidates to generate")
    selection_strategy: Literal["auto", "hitl", "hybrid", "llm_judge"] = Field(
        default="auto", description="Selection strategy"
    )
    quality_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "groundedness": 0.30,
            "relevance": 0.25,
            "coherence": 0.20,
            "creativity": 0.15,
            "safety": 0.10,
        },
        description="Quality dimension weights"
    )
    bandit_arms: list[str] = Field(
        default_factory=lambda: ["backend:qdrant_hybrid", "backend:notebooklm"],
        description="Thompson Sampling arms"
    )
    tier: Literal["free", "premium", "dev"] = Field(default="free", description="UQSL tier")
    enabled: bool = Field(default=True, description="Whether UQSL is enabled")
    auto_threshold: float = Field(
        default=0.85, ge=0, le=1, description="Threshold for auto-selection in hybrid mode"
    )
    top_k_for_hitl: int = Field(default=2, ge=2, le=5, description="Top K candidates for HITL")

    class Config:
        json_schema_extra = {
            "example": {
                "app_key": "dimension.aesthetic.direct",
                "n_candidates": 3,
                "selection_strategy": "hybrid",
                "tier": "premium",
                "enabled": True,
            }
        }


class ThreeWayResult(BaseModel):
    """Ensemble++ 3-Way Comparison Result"""
    query: str = Field(description="Original query")
    results: dict[Literal["a", "b", "ab"], CandidateResult] = Field(description="Three-way results")
    recommended: Literal["a", "b", "ab"] = Field(description="Recommended option")
    arms_stats: dict[str, dict[str, float | int]] = Field(description="Thompson Sampling arm statistics")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "봉준호 스타일의 영화 장면",
                "recommended": "ab",
                "arms_stats": {
                    "qdrant_only": {"alpha": 10, "beta": 3},
                    "notebooklm_only": {"alpha": 8, "beta": 5},
                    "ensemble_ab": {"alpha": 15, "beta": 2},
                },
            }
        }


# Request/Response models for API endpoints
class GenerateCandidatesRequest(BaseModel):
    """Request to generate multiple candidates"""
    prompt: str = Field(max_length=5000, description="Input prompt")
    app_key: str = Field(description="App identifier")
    n_candidates: int = Field(default=3, ge=1, le=5, description="Number of candidates")
    strategy: Literal["auto", "hitl", "hybrid", "llm_judge"] = Field(
        default="auto", description="Selection strategy"
    )


class GenerateCandidatesResponse(BaseModel):
    """Response from candidate generation"""
    session_id: str
    candidates: list[CandidateResult]
    quality_scores: list[QualityScore]
    recommended_idx: int
    method: str


class SelectBestRequest(BaseModel):
    """Request to select best candidate (HITL)"""
    session_id: str
    selected_idx: int = Field(ge=0, description="Index of selected candidate")


class SubmitFeedbackRequest(BaseModel):
    """Request to submit feedback"""
    selection_id: str
    feedback: Literal["positive", "negative"]
    quality_override: Optional[QualityScore] = None


class ThreeWayComparisonRequest(BaseModel):
    """Request for Ensemble++ 3-way comparison"""
    query: str
    dimension: str
    auteur_key: Optional[str] = None
