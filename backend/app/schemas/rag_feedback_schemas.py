"""P6: RAG Feedback Pydantic Schemas.

Request/Response schemas for RAG feedback collection API.

Usage:
    from app.schemas.rag_feedback_schemas import (
        ExplicitFeedbackCreate,
        ImplicitFeedbackCreate,
        RAGResponseRead,
        FeedbackMetrics,
    )
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Enums
# =============================================================================


class FeedbackTypeEnum(str, Enum):
    """Explicit feedback types."""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    REPORT = "report"


class ImplicitEventTypeEnum(str, Enum):
    """Implicit feedback event types."""
    SOURCE_CLICK = "source_click"
    TEXT_COPY = "text_copy"
    QUERY_REFORMULATE = "query_reformulate"
    SESSION_END = "session_end"


# =============================================================================
# Request Schemas
# =============================================================================


class ExplicitFeedbackCreate(BaseModel):
    """명시적 피드백 생성 요청.

    사용자가 직접 제공하는 피드백:
    - rating: 1-5 별점
    - feedback_type: thumbs_up, thumbs_down, report
    - comment: 자유 형식 코멘트
    """
    response_id: UUID = Field(..., description="RAG 응답 ID")

    rating: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="1-5 별점 (선택)"
    )

    feedback_type: Optional[FeedbackTypeEnum] = Field(
        None,
        description="피드백 유형 (thumbs_up, thumbs_down, report)"
    )

    comment: Optional[str] = Field(
        None,
        max_length=2000,
        description="사용자 코멘트"
    )

    @field_validator('rating', 'feedback_type', 'comment', mode='before')
    @classmethod
    def at_least_one_field(cls, v, info):
        """At least one feedback field must be provided."""
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "response_id": "550e8400-e29b-41d4-a716-446655440000",
                "rating": 4,
                "feedback_type": "thumbs_up",
                "comment": "정확한 답변이었습니다."
            }
        }


class ImplicitFeedbackCreate(BaseModel):
    """암시적 피드백 생성 요청.

    사용자 행동 기반 피드백:
    - source_click: 소스 클릭
    - text_copy: 텍스트 복사
    - query_reformulate: 쿼리 재검색
    - session_end: 세션 종료
    """
    response_id: UUID = Field(..., description="RAG 응답 ID")

    event_type: ImplicitEventTypeEnum = Field(
        ...,
        description="이벤트 유형"
    )

    # Source click details
    source_id: Optional[str] = Field(
        None,
        description="클릭한 소스 ID"
    )
    source_index: Optional[int] = Field(
        None,
        ge=0,
        description="클릭한 소스 순서 (0-based)"
    )

    # Session details
    duration_ms: Optional[int] = Field(
        None,
        ge=0,
        description="세션/행동 지속 시간 (ms)"
    )

    # Reformulation details
    new_query: Optional[str] = Field(
        None,
        max_length=1000,
        description="재검색 쿼리"
    )

    # Copy details
    copied_length: Optional[int] = Field(
        None,
        ge=0,
        description="복사한 텍스트 길이"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "response_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_type": "source_click",
                "source_id": "notebooklm:bong:abc123",
                "source_index": 0,
                "duration_ms": 5000
            }
        }


class RAGResponseCreate(BaseModel):
    """RAG 응답 저장 요청 (내부용).

    hybrid_query() 호출 시 자동 생성됩니다.
    """
    query: str
    query_hash: str
    answer: Optional[str] = None

    # P5 Classification
    query_type: Optional[str] = None
    classification_confidence: Optional[float] = None
    classifier_used: Optional[str] = None

    # Strategy
    strategy_used: Optional[str] = None
    retrieval_skipped: bool = False

    # Metrics
    latency_ms: Optional[int] = None
    retrieval_count: int = 0
    reranked: bool = False
    rerank_latency_ms: Optional[int] = None
    crag_triggered: bool = False
    grounded: bool = False

    # Sources
    sources: Optional[List[Dict[str, Any]]] = None
    source_scores: Optional[List[float]] = None

    # RRF
    rrf_enabled: bool = False
    keyword_results_count: int = 0
    vector_results_count: int = 0

    # Context
    app_key: Optional[str] = None
    dimension: Optional[str] = None
    auteur_key: Optional[str] = None
    user_id: Optional[UUID] = None
    session_id: Optional[str] = None

    # Error
    error: Optional[str] = None
    error_type: Optional[str] = None


# =============================================================================
# Response Schemas
# =============================================================================


class RAGResponseRead(BaseModel):
    """RAG 응답 조회 응답."""
    id: UUID
    query: str
    query_hash: str
    answer: Optional[str]

    query_type: Optional[str]
    classification_confidence: Optional[float]
    strategy_used: Optional[str]
    retrieval_skipped: bool

    latency_ms: Optional[int]
    retrieval_count: int
    reranked: bool
    crag_triggered: bool
    grounded: bool

    app_key: Optional[str]
    dimension: Optional[str]
    auteur_key: Optional[str]

    created_at: datetime

    # Feedback summary
    feedback_count: int = 0
    avg_rating: Optional[float] = None

    class Config:
        from_attributes = True


class RAGFeedbackRead(BaseModel):
    """RAG 피드백 조회 응답."""
    id: UUID
    response_id: UUID

    # Explicit
    rating: Optional[int]
    feedback_type: Optional[str]
    user_comment: Optional[str]

    # Implicit
    source_clicked: bool
    clicked_source_id: Optional[str]
    query_reformulated: bool
    text_copied: bool

    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackSubmitResponse(BaseModel):
    """피드백 제출 응답."""
    feedback_id: UUID
    response_id: UUID
    message: str = "Feedback submitted successfully"


# =============================================================================
# Analytics Schemas
# =============================================================================


class FeedbackMetrics(BaseModel):
    """앱별 피드백 메트릭."""
    app_key: Optional[str]
    period_days: int

    # Query counts
    total_queries: int
    skip_retrieval_count: int
    skip_retrieval_rate: float

    # Performance
    avg_latency_ms: float
    avg_retrieval_count: float

    # Feedback
    feedback_count: int
    feedback_rate: float
    avg_rating: Optional[float]

    # Explicit feedback breakdown
    thumbs_up_count: int
    thumbs_down_count: int
    report_count: int

    # Implicit signals
    source_click_rate: float
    reformulation_rate: float
    copy_rate: float

    # P5 Classification breakdown
    query_type_distribution: Dict[str, int]
    strategy_distribution: Dict[str, int]

    class Config:
        json_schema_extra = {
            "example": {
                "app_key": "dimension.aesthetic.direct",
                "period_days": 7,
                "total_queries": 1000,
                "skip_retrieval_count": 250,
                "skip_retrieval_rate": 0.25,
                "avg_latency_ms": 150.5,
                "avg_retrieval_count": 5.2,
                "feedback_count": 50,
                "feedback_rate": 0.05,
                "avg_rating": 4.2,
                "thumbs_up_count": 40,
                "thumbs_down_count": 5,
                "report_count": 1,
                "source_click_rate": 0.35,
                "reformulation_rate": 0.08,
                "copy_rate": 0.22,
                "query_type_distribution": {
                    "simple_factual": 250,
                    "domain_specific": 500,
                    "multi_hop": 150,
                    "creative": 50,
                    "recency_required": 50
                },
                "strategy_distribution": {
                    "direct_llm": 250,
                    "ensemble_rrf": 550,
                    "full_pipeline": 150,
                    "grounding_first": 50
                }
            }
        }


class ClassificationAccuracyMetrics(BaseModel):
    """P5 분류 정확도 메트릭 (P7 Self-Correction용)."""
    period_days: int

    # Overall accuracy (based on feedback)
    total_classified: int
    with_feedback: int
    positive_feedback_rate: float  # rating >= 4 or thumbs_up

    # Per query type accuracy
    accuracy_by_type: Dict[str, Dict[str, float]]
    # { "simple_factual": { "positive_rate": 0.9, "skip_success_rate": 0.95 }, ... }

    # Skip retrieval analysis
    skip_retrieval_total: int
    skip_positive_rate: float  # Was skipping the right choice?
    skip_negative_cases: int  # Low rating after skip

    # CRAG trigger analysis
    crag_trigger_rate: float
    crag_success_rate: float  # Rating improvement after CRAG

    # Recommendations for P7
    recommended_threshold_adjustments: Dict[str, float]


class DailyStatsRead(BaseModel):
    """일별 통계 조회 응답."""
    stat_date: datetime
    app_key: Optional[str]
    query_type: Optional[str]
    strategy_used: Optional[str]

    total_queries: int
    skip_retrieval_count: int
    crag_trigger_count: int
    error_count: int

    avg_latency_ms: Optional[float]
    avg_rating: Optional[float]
    thumbs_up_count: int
    thumbs_down_count: int

    source_click_rate: Optional[float]
    reformulation_rate: Optional[float]

    class Config:
        from_attributes = True
