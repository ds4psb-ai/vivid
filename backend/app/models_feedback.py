"""P6/P7: RAG Feedback Collection & HITL Enhancement DB Models.

Tracks RAG responses and user feedback for:
- P5 classification accuracy analysis
- P7 self-correction data foundation
- P7 HITL enhancement (approval gates, feedback→RAG pipeline)
- P8 continual learning training data

Tables:
    - rag_responses: RAG 응답 저장 (피드백 연결용)
    - rag_feedbacks: 명시적/암시적 피드백 수집
    - feedback_corrections: 부정 피드백 교정 추적
    - feedback_ingestions: 긍정 피드백 RAG 수집 추적
    - creator_anomaly_logs: 크리에이터 이상 탐지 기록
"""
import uuid
import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, DateTime, Integer, Float, Text, Index, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


# =============================================================================
# Enums
# =============================================================================


class FeedbackType(str, enum.Enum):
    """Explicit feedback types."""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    REPORT = "report"


class ImplicitEventType(str, enum.Enum):
    """Implicit feedback event types."""
    SOURCE_CLICK = "source_click"
    TEXT_COPY = "text_copy"
    QUERY_REFORMULATE = "query_reformulate"
    SESSION_END = "session_end"


# =============================================================================
# RAGResponse - Stores RAG query results for feedback linking
# =============================================================================


class RAGResponse(Base):
    """RAG 응답 저장 (피드백 연결용).

    모든 hybrid_query() 호출 결과를 저장하여:
    1. P5 분류 정확도 추적
    2. P7 오분류 분석을 위한 데이터 축적
    3. P8 학습 데이터 생성
    """
    __tablename__ = "rag_responses"
    __table_args__ = (
        Index("ix_rag_responses_query_hash", "query_hash"),
        Index("ix_rag_responses_app_key", "app_key"),
        Index("ix_rag_responses_user_id", "user_id"),
        Index("ix_rag_responses_query_type", "query_type"),
        Index("ix_rag_responses_created_at", "created_at"),
        Index("ix_rag_responses_strategy_used", "strategy_used"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Query & Answer
    query: Mapped[str] = mapped_column(Text, nullable=False)
    query_hash: Mapped[str] = mapped_column(String(64))  # SHA256 for grouping
    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # P5 Classification Results
    query_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # simple_factual, domain_specific, recency_required, multi_hop, creative, ambiguous
    classification_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    classifier_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # semantic_router, llm_classifier

    # Strategy & Execution
    strategy_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # direct_llm, minimal_rag, ensemble_rrf, grounding_first, full_pipeline
    retrieval_skipped: Mapped[bool] = mapped_column(Boolean, default=False)

    # Performance Metrics
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    retrieval_count: Mapped[int] = mapped_column(Integer, default=0)
    reranked: Mapped[bool] = mapped_column(Boolean, default=False)
    rerank_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    crag_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    grounded: Mapped[bool] = mapped_column(Boolean, default=False)

    # Source Information
    sources: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # [{source_id, type, score, title}, ...]
    source_scores: Mapped[Optional[List[float]]] = mapped_column(JSONB, nullable=True)

    # RRF Fusion Details (P3)
    rrf_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    keyword_results_count: Mapped[int] = mapped_column(Integer, default=0)
    vector_results_count: Mapped[int] = mapped_column(Integer, default=0)

    # Context
    app_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    dimension: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    auteur_key: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Error tracking
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    feedbacks: Mapped[List["RAGFeedback"]] = relationship(
        "RAGFeedback", back_populates="response", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<RAGResponse {self.id} query='{self.query[:30]}...'>"


# =============================================================================
# RAGFeedback - Collects explicit and implicit feedback
# =============================================================================


class RAGFeedback(Base):
    """RAG 피드백 수집.

    두 가지 피드백 유형:
    1. Explicit: 사용자가 직접 제공 (평점, 좋아요/싫어요, 신고)
    2. Implicit: 행동 기반 추론 (클릭, 복사, 재검색)
    """
    __tablename__ = "rag_feedbacks"
    __table_args__ = (
        Index("ix_rag_feedbacks_response_id", "response_id"),
        Index("ix_rag_feedbacks_user_id", "user_id"),
        Index("ix_rag_feedbacks_feedback_type", "feedback_type"),
        Index("ix_rag_feedbacks_created_at", "created_at"),
        Index("ix_rag_feedbacks_rating", "rating"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    response_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rag_responses.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ==========================================================================
    # Explicit Feedback
    # ==========================================================================

    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # 1-5 stars (nullable - not all feedback includes rating)

    feedback_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # thumbs_up, thumbs_down, report

    user_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Free-form user comment

    # ==========================================================================
    # Implicit Feedback
    # ==========================================================================

    # Source interaction
    source_clicked: Mapped[bool] = mapped_column(Boolean, default=False)
    clicked_source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    clicked_source_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Session behavior
    session_duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Time from response to next action

    # Query reformulation (indicates dissatisfaction)
    query_reformulated: Mapped[bool] = mapped_column(Boolean, default=False)
    reformulated_query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_to_reformulate_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Text copy (indicates usefulness)
    text_copied: Mapped[bool] = mapped_column(Boolean, default=False)
    copied_length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Characters copied

    # Event type for implicit tracking
    implicit_event_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    # source_click, text_copy, query_reformulate, session_end

    # ==========================================================================
    # Metadata
    # ==========================================================================

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    client_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    # IPv6 compatible

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # ==========================================================================
    # P7 HITL Enhancement Columns
    # ==========================================================================

    # Feedback → RAG Pipeline tracking
    ingested_to_rag: Mapped[bool] = mapped_column(Boolean, default=False)
    correction_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_for_learning: Mapped[bool] = mapped_column(Boolean, default=False)
    learning_cycle_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationship
    response: Mapped["RAGResponse"] = relationship(
        "RAGResponse", back_populates="feedbacks"
    )
    corrections: Mapped[List["FeedbackCorrection"]] = relationship(
        "FeedbackCorrection", back_populates="feedback", cascade="all, delete-orphan"
    )
    ingestions: Mapped[List["FeedbackIngestion"]] = relationship(
        "FeedbackIngestion", back_populates="feedback", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<RAGFeedback {self.id} response={self.response_id}>"


# =============================================================================
# Aggregate Views (for analytics queries)
# =============================================================================


class RAGResponseDailyStats(Base):
    """일별 RAG 응답 통계 (materialized view 대용).

    P7 Self-Correction에서 사용할 일별 집계 데이터.
    실제 프로덕션에서는 PostgreSQL materialized view로 대체 권장.
    """
    __tablename__ = "rag_response_daily_stats"
    __table_args__ = (
        Index("ix_rag_daily_stats_date", "stat_date"),
        Index("ix_rag_daily_stats_app_key", "app_key"),
        Index("ix_rag_daily_stats_query_type", "query_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    stat_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    app_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    query_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    strategy_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Counts
    total_queries: Mapped[int] = mapped_column(Integer, default=0)
    skip_retrieval_count: Mapped[int] = mapped_column(Integer, default=0)
    crag_trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)

    # Averages
    avg_latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_retrieval_count: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Feedback aggregates
    feedback_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    thumbs_up_count: Mapped[int] = mapped_column(Integer, default=0)
    thumbs_down_count: Mapped[int] = mapped_column(Integer, default=0)

    # Implicit metrics
    source_click_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reformulation_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    copy_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<RAGResponseDailyStats {self.stat_date} app={self.app_key}>"


# =============================================================================
# P7 HITL Enhancement Models
# =============================================================================


class CorrectionType(str, enum.Enum):
    """Feedback correction types."""
    SOURCE_FLAGGED = "source_flagged"
    CACHE_INVALIDATED = "cache_invalidated"
    CRAG_TRIGGERED = "crag_triggered"
    MANUAL_OVERRIDE = "manual_override"


class AnomalyType(str, enum.Enum):
    """Creator anomaly types."""
    RATING_DROP = "rating_drop"
    REVISION_SPIKE = "revision_spike"
    DELIVERY_DELAY = "delivery_delay"
    CREDIT_ANOMALY = "credit_anomaly"
    ENGAGEMENT_DROP = "engagement_drop"


class AnomalySeverity(str, enum.Enum):
    """Anomaly severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackCorrection(Base):
    """부정 피드백 교정 추적.

    부정 피드백이 발생했을 때 수행된 교정 작업을 기록합니다.

    Correction Types:
    - source_flagged: 원본 소스 문서에 검토 플래그
    - cache_invalidated: 시맨틱 캐시 항목 무효화
    - crag_triggered: CRAG 교정 워크플로우 트리거
    - manual_override: 수동 교정
    """
    __tablename__ = "feedback_corrections"
    __table_args__ = (
        Index("ix_feedback_corrections_response_id", "response_id"),
        Index("ix_feedback_corrections_feedback_id", "feedback_id"),
        Index("ix_feedback_corrections_correction_type", "correction_type"),
        Index("ix_feedback_corrections_dimension", "dimension"),
        Index("ix_feedback_corrections_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    response_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rag_responses.id", ondelete="CASCADE"),
        nullable=False,
    )
    feedback_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rag_feedbacks.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Correction Details
    correction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    original_query: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    correction_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    dimension: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    auteur_key: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Review Status
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    response: Mapped["RAGResponse"] = relationship("RAGResponse")
    feedback: Mapped["RAGFeedback"] = relationship(
        "RAGFeedback", back_populates="corrections"
    )

    def __repr__(self) -> str:
        return f"<FeedbackCorrection {self.id} type={self.correction_type}>"


class FeedbackIngestion(Base):
    """긍정 피드백 RAG 수집 추적.

    긍정 피드백(평점 >= 4)이 발생했을 때 RAG 지식베이스로의 수집을 기록합니다.
    """
    __tablename__ = "feedback_ingestions"
    __table_args__ = (
        Index("ix_feedback_ingestions_feedback_id", "feedback_id"),
        Index("ix_feedback_ingestions_dimension", "dimension"),
        Index("ix_feedback_ingestions_qdrant_point_id", "qdrant_point_id"),
        Index("ix_feedback_ingestions_collection_name", "collection_name"),
        Index("ix_feedback_ingestions_ingested_at", "ingested_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    feedback_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rag_feedbacks.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Qdrant Indexing
    dimension: Mapped[str] = mapped_column(String(10), nullable=False)
    qdrant_point_id: Mapped[str] = mapped_column(String(100), nullable=False)
    collection_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Content Info
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    content_preview: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Embedding Info
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    embedding_dim: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Metadata
    auteur_key: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_validated: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    feedback: Mapped["RAGFeedback"] = relationship(
        "RAGFeedback", back_populates="ingestions"
    )

    def __repr__(self) -> str:
        return f"<FeedbackIngestion {self.id} dim={self.dimension}>"


class CreatorAnomalyLog(Base):
    """크리에이터 이상 탐지 기록.

    IQR 방법을 사용하여 감지된 크리에이터 행동 이상을 기록합니다.

    Anomaly Types:
    - rating_drop: 급격한 평점 하락 (평균 대비 2 std 이하)
    - revision_spike: 비정상 수정 비율
    - delivery_delay: 비정상 납품 지연
    - credit_anomaly: 크레딧 수익 급등/급락
    - engagement_drop: 참여도 급감
    """
    __tablename__ = "creator_anomaly_logs"
    __table_args__ = (
        Index("ix_creator_anomaly_logs_creator_id", "creator_id"),
        Index("ix_creator_anomaly_logs_anomaly_type", "anomaly_type"),
        Index("ix_creator_anomaly_logs_severity", "severity"),
        Index("ix_creator_anomaly_logs_resolved", "resolved"),
        Index("ix_creator_anomaly_logs_detected_at", "detected_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Anomaly Details
    anomaly_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    expected_range_low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    expected_range_high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    deviation_std: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Context
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Resolution
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<CreatorAnomalyLog {self.id} type={self.anomaly_type} severity={self.severity}>"
