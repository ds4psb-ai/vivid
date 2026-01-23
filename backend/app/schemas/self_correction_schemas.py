"""P7: Self-Correction Pydantic Schemas.

Schemas for RAG query classification self-correction system.

Components:
- MisclassificationAnalyzer: 오분류 분석 결과
- PromptTuner: 프롬프트 튜닝 결과
- ThresholdTuner: 임계값 조정 결과
- Weekly Self-Correction: 주간 자동 실행 결과

Usage:
    from app.schemas.self_correction_schemas import (
        MisclassifiedQuery,
        MisclassificationReport,
        PromptIssue,
        PromptTuningResult,
        ThresholdConfig,
        SelfCorrectionResult,
    )
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Enums
# =============================================================================


class MisclassificationType(str, Enum):
    """오분류 유형."""
    SKIP_BUT_NEGATIVE = "skip_but_negative"
    """검색 생략했지만 부정 피드백 (rating < 3)."""

    RETRIEVAL_BUT_CRAG = "retrieval_but_crag"
    """검색 수행했지만 CRAG 트리거됨 (품질 불충분)."""

    WRONG_STRATEGY = "wrong_strategy"
    """잘못된 전략 선택 (피드백 기반 추론)."""

    LOW_CONFIDENCE_FAILURE = "low_confidence_failure"
    """낮은 신뢰도로 분류 후 실패."""

    HIGH_LATENCY_SIMPLE = "high_latency_simple"
    """단순 쿼리인데 고지연 (오분류 가능성)."""


class PromptIssueType(str, Enum):
    """프롬프트 이슈 유형."""
    BOUNDARY_AMBIGUITY = "boundary_ambiguity"
    """경계 조건 모호성 (예: 창작 vs 도메인 특화)."""

    MISSING_EXAMPLES = "missing_examples"
    """예시 부족."""

    CONFLICTING_RULES = "conflicting_rules"
    """상충하는 규칙."""

    DOMAIN_GAP = "domain_gap"
    """도메인 지식 갭."""

    RECENCY_DETECTION = "recency_detection"
    """최신 정보 요구 탐지 실패."""


class ExperimentType(str, Enum):
    """Self-Correction 실험 유형."""
    PROMPT_TUNING = "prompt_tuning"
    """프롬프트 개선 A/B 테스트."""

    THRESHOLD_TUNING = "threshold_tuning"
    """임계값 조정 A/B 테스트."""

    ROUTE_EXAMPLES = "route_examples"
    """SemanticRouter 예시 추가 테스트."""


class SelfCorrectionStatus(str, Enum):
    """Self-Correction 상태."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    TUNING = "tuning"
    EXPERIMENTING = "experimenting"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


# =============================================================================
# MisclassificationAnalyzer Schemas
# =============================================================================


class MisclassifiedQuery(BaseModel):
    """오분류된 쿼리 정보."""
    response_id: UUID
    query: str
    query_hash: str

    # Classification
    predicted_type: str
    """예측된 QueryType."""

    confidence: float
    """분류 신뢰도."""

    classifier_used: str
    """사용된 분류기 (semantic_router, llm_classifier)."""

    # Execution
    strategy_used: str
    """사용된 검색 전략."""

    retrieval_skipped: bool
    """검색 생략 여부."""

    crag_triggered: bool
    """CRAG 트리거 여부."""

    latency_ms: int
    """지연 시간."""

    # Feedback
    avg_rating: Optional[float] = None
    """평균 평점."""

    negative_feedback_count: int = 0
    """부정 피드백 수."""

    positive_feedback_count: int = 0
    """긍정 피드백 수."""

    # Analysis
    misclassification_type: MisclassificationType
    """오분류 유형."""

    suggested_type: Optional[str] = None
    """제안된 QueryType (분석 결과)."""

    analysis_reason: str = ""
    """분석 근거."""

    # Context
    dimension: Optional[str] = None
    auteur_key: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QueryTypeAccuracy(BaseModel):
    """QueryType별 정확도."""
    query_type: str
    total_count: int
    feedback_count: int
    positive_count: int
    negative_count: int
    accuracy: float = Field(ge=0.0, le=1.0, description="정확도 (긍정/전체)")
    skip_retrieval_count: int = 0
    skip_negative_count: int = 0
    """검색 생략 후 부정 피드백."""

    crag_trigger_count: int = 0
    avg_latency_ms: float = 0.0


class MisclassificationReport(BaseModel):
    """오분류 분석 리포트."""
    period_days: int
    analysis_date: datetime = Field(default_factory=datetime.utcnow)

    # Summary
    total_responses: int
    total_with_feedback: int
    total_misclassified: int
    misclassification_rate: float = Field(ge=0.0, le=1.0)

    # By Type
    misclassifications_by_type: Dict[MisclassificationType, int]
    accuracy_by_query_type: Dict[str, QueryTypeAccuracy]

    # Top Issues
    top_misclassified_queries: List[MisclassifiedQuery] = Field(
        default_factory=list,
        max_length=100,
    )

    # CRAG Analysis
    crag_trigger_rate: float = Field(ge=0.0, le=1.0)
    crag_success_rate: float = Field(ge=0.0, le=1.0)
    """CRAG 후 긍정 피드백 비율."""

    # Skip Retrieval Analysis
    skip_retrieval_total: int = 0
    skip_retrieval_negative_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    """검색 생략 후 부정 피드백 비율."""

    # Recommendations
    suggested_threshold_changes: Dict[str, float] = Field(default_factory=dict)
    suggested_query_type_adjustments: List[str] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "period_days": 7,
                "total_responses": 10000,
                "total_with_feedback": 500,
                "total_misclassified": 45,
                "misclassification_rate": 0.09,
                "misclassifications_by_type": {
                    "skip_but_negative": 20,
                    "retrieval_but_crag": 15,
                    "wrong_strategy": 10,
                },
                "crag_trigger_rate": 0.05,
                "crag_success_rate": 0.72,
                "skip_retrieval_negative_rate": 0.08,
                "suggested_threshold_changes": {
                    "semantic_threshold": 0.05,
                    "skip_confidence_threshold": 0.03,
                },
            }
        }
    )


# =============================================================================
# PromptTuner Schemas
# =============================================================================


class PromptIssue(BaseModel):
    """프롬프트 이슈 분석 결과."""
    issue_type: PromptIssueType
    severity: str = Field(description="low, medium, high, critical")
    description: str
    affected_query_types: List[str] = Field(default_factory=list)
    example_queries: List[str] = Field(default_factory=list, max_length=10)
    suggested_fix: str = ""


class PromptAnalysis(BaseModel):
    """프롬프트 분석 결과."""
    current_prompt: str
    issues: List[PromptIssue] = Field(default_factory=list)
    overall_score: float = Field(ge=0.0, le=1.0, description="현재 프롬프트 점수")
    improvement_potential: float = Field(ge=0.0, le=1.0, description="개선 가능성")


class PromptTuningResult(BaseModel):
    """프롬프트 튜닝 결과."""
    tuning_id: str = Field(default_factory=lambda: f"tune_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Analysis
    analysis: PromptAnalysis

    # New Prompt
    improved_prompt: str
    changes_summary: str
    expected_improvement: float = Field(ge=0.0, le=1.0)

    # A/B Test
    experiment_key: Optional[str] = None
    variant_name: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tuning_id": "tune_20260123_100000",
                "improved_prompt": "Classify the query into...",
                "changes_summary": "Added boundary examples for creative vs domain_specific queries",
                "expected_improvement": 0.15,
                "experiment_key": "p7_prompt_tuning_20260123",
            }
        }
    )


# =============================================================================
# ThresholdTuner Schemas
# =============================================================================


class ThresholdConfig(BaseModel):
    """분류 임계값 설정."""
    # SemanticRouter
    semantic_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="SemanticRouter 최소 신뢰도",
    )

    # Skip Retrieval
    skip_confidence_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="검색 생략 최소 신뢰도",
    )

    # Reranker
    reranker_min_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Reranker 최소 점수",
    )

    # CRAG
    crag_relevance_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="CRAG 트리거 임계값",
    )

    # LLM Classifier
    llm_fallback_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="LLM 분류기 폴백 임계값",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "semantic_threshold": 0.7,
                "skip_confidence_threshold": 0.85,
                "reranker_min_score": 0.5,
                "crag_relevance_threshold": 0.6,
                "llm_fallback_threshold": 0.5,
            }
        }
    )


class ThresholdTuningResult(BaseModel):
    """임계값 튜닝 결과."""
    tuning_id: str = Field(default_factory=lambda: f"thresh_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Before/After
    previous_config: ThresholdConfig
    new_config: ThresholdConfig

    # Changes
    changes: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    """{ "semantic_threshold": { "old": 0.7, "new": 0.75, "delta": 0.05 } }"""

    # Rationale
    rationale: str
    expected_improvement: Dict[str, float] = Field(default_factory=dict)
    """{ "skip_negative_rate": -0.05, "crag_success_rate": 0.10 }"""

    # A/B Test
    experiment_key: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tuning_id": "thresh_20260123_100000",
                "changes": {
                    "semantic_threshold": {"old": 0.7, "new": 0.75, "delta": 0.05},
                    "skip_confidence_threshold": {"old": 0.85, "new": 0.88, "delta": 0.03},
                },
                "rationale": "Increased thresholds due to 8% skip_but_negative rate",
                "expected_improvement": {
                    "skip_negative_rate": -0.05,
                    "accuracy": 0.03,
                },
            }
        }
    )


# =============================================================================
# Weekly Self-Correction Schemas
# =============================================================================


class SelfCorrectionCycleResult(BaseModel):
    """주간 Self-Correction 실행 결과."""
    cycle_id: str = Field(default_factory=lambda: f"cycle_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: SelfCorrectionStatus = SelfCorrectionStatus.PENDING

    # Analysis Phase
    misclassification_report: Optional[MisclassificationReport] = None

    # Tuning Phase
    prompt_tuning: Optional[PromptTuningResult] = None
    threshold_tuning: Optional[ThresholdTuningResult] = None

    # Experiment Phase
    experiments_started: List[str] = Field(default_factory=list)
    """A/B 테스트 experiment_key 목록."""

    # Evaluation Phase (이전 실험 결과)
    previous_experiments_evaluated: List[str] = Field(default_factory=list)
    adoptions: List[str] = Field(default_factory=list)
    """채택된 실험 ID 목록."""

    rollbacks: List[str] = Field(default_factory=list)
    """롤백된 실험 ID 목록."""

    # Summary
    summary: str = ""
    metrics_before: Dict[str, float] = Field(default_factory=dict)
    metrics_after: Dict[str, float] = Field(default_factory=dict)
    improvement: Dict[str, float] = Field(default_factory=dict)

    # Error
    error: Optional[str] = None
    error_details: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cycle_id": "cycle_20260123_100000",
                "status": "completed",
                "experiments_started": ["p7_prompt_tune_20260123", "p7_thresh_tune_20260123"],
                "adoptions": ["p7_prompt_tune_20260116"],
                "summary": "Analyzed 500 feedbacks, started 2 experiments, adopted 1 previous",
                "improvement": {
                    "accuracy": 0.03,
                    "skip_negative_rate": -0.02,
                },
            }
        }
    )


class ExperimentEvaluation(BaseModel):
    """실험 평가 결과."""
    experiment_key: str
    experiment_type: ExperimentType
    started_at: datetime
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

    # Results
    control_sample_size: int
    treatment_sample_size: int
    control_accuracy: float
    treatment_accuracy: float
    relative_lift: float
    """(treatment - control) / control"""

    p_value: float
    is_significant: bool
    confidence_interval: tuple[float, float]

    # Decision
    should_adopt: bool
    adoption_reason: str
    risk_level: str = Field(description="low, medium, high")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "experiment_key": "p7_prompt_tune_20260116",
                "experiment_type": "prompt_tuning",
                "control_sample_size": 500,
                "treatment_sample_size": 50,
                "control_accuracy": 0.85,
                "treatment_accuracy": 0.89,
                "relative_lift": 0.047,
                "p_value": 0.02,
                "is_significant": True,
                "confidence_interval": [0.01, 0.08],
                "should_adopt": True,
                "adoption_reason": "Significant improvement with low risk",
                "risk_level": "low",
            }
        }
    )


# =============================================================================
# API Schemas
# =============================================================================


class AnalyzeRequest(BaseModel):
    """오분류 분석 요청."""
    days: int = Field(default=7, ge=1, le=90)
    app_key: Optional[str] = None
    min_feedback_count: int = Field(default=3, ge=1)


class TunePromptRequest(BaseModel):
    """프롬프트 튜닝 요청."""
    days: int = Field(default=7, ge=1, le=90)
    max_failures: int = Field(default=100, ge=10, le=500)
    auto_experiment: bool = Field(default=True, description="자동 A/B 테스트 시작")
    experiment_traffic: float = Field(default=0.1, ge=0.01, le=0.5)


class TuneThresholdRequest(BaseModel):
    """임계값 튜닝 요청."""
    days: int = Field(default=7, ge=1, le=90)
    auto_experiment: bool = Field(default=True)
    experiment_traffic: float = Field(default=0.1, ge=0.01, le=0.5)


class SelfCorrectionTriggerRequest(BaseModel):
    """Self-Correction 수동 트리거 요청."""
    days: int = Field(default=7, ge=1, le=90)
    skip_analysis: bool = Field(default=False)
    skip_tuning: bool = Field(default=False)
    skip_experiment: bool = Field(default=False)
    evaluate_previous: bool = Field(default=True)


class SelfCorrectionResponse(BaseModel):
    """Self-Correction API 응답."""
    success: bool
    message: str
    cycle_id: Optional[str] = None
    result: Optional[SelfCorrectionCycleResult] = None
