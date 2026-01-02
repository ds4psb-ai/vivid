"""
Feedback Loop Schemas

프로덕션 결과 기반 자동 학습 및 신뢰도 갱신 스키마.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class FeedbackType(str, Enum):
    """피드백 유형"""
    PRODUCTION_RESULT = "production_result"  # 영상 제작 결과
    USER_RATING = "user_rating"              # 사용자 평가
    METRIC_UPDATE = "metric_update"          # 메트릭 업데이트
    AB_TEST_RESULT = "ab_test_result"        # A/B 테스트 결과
    EXPERT_REVIEW = "expert_review"          # 전문가 리뷰


class ResultOutcome(str, Enum):
    """결과 유형"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"


class ProductionResult(BaseModel):
    """
    프로덕션 결과
    
    영상 제작/캡슐 실행 결과
    """
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # 관련 엔티티
    capsule_id: Optional[str] = None
    run_id: Optional[str] = None
    pack_id: Optional[str] = None
    rule_ids: List[str] = Field(default_factory=list)
    
    # 결과
    outcome: ResultOutcome = ResultOutcome.SUCCESS
    score: Optional[float] = Field(None, ge=0.0, le=100.0)
    
    # 메트릭
    metrics: Dict[str, float] = Field(default_factory=dict)
    # 예: {"view_count": 1000, "engagement_rate": 0.05, "ctr": 0.02}
    
    # 메타
    created_at: datetime = Field(default_factory=datetime.utcnow)
    meta: Dict[str, Any] = Field(default_factory=dict)


class UserFeedback(BaseModel):
    """사용자 피드백"""
    feedback_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # 관련 엔티티
    capsule_id: Optional[str] = None
    run_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # 피드백
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # 타임스탬프
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FeedbackEvent(BaseModel):
    """
    피드백 이벤트 (통합)
    
    모든 유형의 피드백을 처리하는 통합 이벤트
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    feedback_type: FeedbackType
    
    # 페이로드
    production_result: Optional[ProductionResult] = None
    user_feedback: Optional[UserFeedback] = None
    raw_data: Optional[Dict[str, Any]] = None
    
    # 처리 상태
    processed: bool = False
    processed_at: Optional[datetime] = None
    
    # 결과
    confidence_updates: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 타임스탬프
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LearningCycle(BaseModel):
    """
    학습 싸이클
    
    일정 기간의 피드백을 수집하여 배치 갱신
    """
    cycle_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # 기간
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # 수집된 이벤트
    events: List[FeedbackEvent] = Field(default_factory=list)
    event_count: int = 0
    
    # 갱신 결과
    rules_updated: int = 0
    total_delta: float = 0.0
    avg_confidence_change: float = 0.0
    
    # 상태
    status: Literal["collecting", "processing", "completed", "failed"] = "collecting"


class FeedbackProcessorConfig(BaseModel):
    """피드백 프로세서 설정"""
    # 싸이클 설정
    cycle_duration_hours: int = Field(default=24, ge=1, le=168)
    min_events_per_cycle: int = Field(default=10, ge=1)
    
    # 신뢰도 갱신 설정
    max_confidence_change_per_event: float = Field(default=0.1, ge=0.01, le=0.5)
    require_multiple_sources: bool = Field(default=True)
    
    # 필터링
    min_rating_to_support: int = Field(default=4, ge=1, le=5)
    min_score_to_support: float = Field(default=70.0, ge=0.0, le=100.0)


class FeedbackSummary(BaseModel):
    """피드백 요약"""
    total_events: int
    events_by_type: Dict[str, int]
    avg_rating: Optional[float] = None
    avg_score: Optional[float] = None
    success_rate: float
    rules_affected: int
    confidence_trend: Literal["up", "down", "stable"]
