"""Approval Gate Schemas (Phase 7 HITL Enhancement).

Pydantic schemas for confidence-based approval routing.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ApprovalDecision(str, Enum):
    """승인 결정 유형."""
    AUTO_APPROVED = "auto_approved"
    PENDING_REVIEW = "pending_review"
    ESCALATED = "escalated"
    TIMEOUT = "timeout"


class ApprovalGateConfig(BaseModel):
    """차원별 승인 임계값 설정."""
    auto_approve_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="고신뢰도 자동승인 임계값"
    )
    escalate_threshold: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description="저신뢰도 에스컬레이션 임계값"
    )
    timeout_seconds: int = Field(
        default=3600,
        ge=60,
        description="승인 대기 타임아웃 (초)"
    )
    notification_channels: List[str] = Field(
        default=["email"],
        description="알림 채널 목록"
    )

    # Dimension-specific overrides
    dimension_overrides: Dict[str, "DimensionApprovalConfig"] = Field(
        default_factory=dict,
        description="차원별 설정 오버라이드"
    )


class DimensionApprovalConfig(BaseModel):
    """차원별 승인 설정."""
    auto_approve_threshold: Optional[float] = None
    escalate_threshold: Optional[float] = None
    timeout_seconds: Optional[int] = None
    requires_manual_review: bool = Field(
        default=False,
        description="항상 수동 검토 필요"
    )


class PendingApproval(BaseModel):
    """대기 중인 승인 정보."""
    checkpoint_id: UUID
    execution_id: UUID
    node_id: str
    tool_id: str
    output_preview: str = Field(
        description="출력물 미리보기 (500자 제한)"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="신뢰도 점수"
    )
    dimension: Optional[str] = None
    auteur_key: Optional[str] = None
    decision: ApprovalDecision
    expires_at: datetime
    created_at: datetime

    # Additional context
    node_output: Optional[Dict[str, Any]] = None
    reviewer_id: Optional[str] = None

    class Config:
        from_attributes = True


class ApprovalResult(BaseModel):
    """승인 처리 결과."""
    checkpoint_id: UUID
    action: str  # approve, reject, modify, skip
    reviewer_id: str
    feedback: Optional[str] = None
    quality_rating: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="품질 평점 (1-5)"
    )
    processed_at: datetime
    workflow_resumed: bool = False


class ApprovalEvaluationResult(BaseModel):
    """승인 평가 결과."""
    execution_id: UUID
    node_id: str
    confidence: float
    decision: ApprovalDecision
    checkpoint_id: Optional[UUID] = None
    auto_approved: bool = False
    reason: str


class ApprovalStatsResponse(BaseModel):
    """승인 통계 응답."""
    total_checkpoints: int
    auto_approved_count: int
    pending_count: int
    escalated_count: int
    timeout_count: int
    rejected_count: int

    auto_approve_rate: float
    avg_review_time_seconds: Optional[float] = None
    avg_confidence_score: Optional[float] = None

    by_dimension: Dict[str, "DimensionApprovalStats"] = Field(
        default_factory=dict
    )

    period_start: datetime
    period_end: datetime


class DimensionApprovalStats(BaseModel):
    """차원별 승인 통계."""
    total: int
    auto_approved: int
    pending: int
    escalated: int
    auto_approve_rate: float


# Request/Response schemas for API endpoints

class ResolveApprovalRequest(BaseModel):
    """승인 해결 요청."""
    action: str = Field(
        description="액션: approve, reject, modify, skip"
    )
    feedback: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="검토자 피드백"
    )
    quality_rating: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="품질 평점"
    )
    modified_output: Optional[Dict[str, Any]] = Field(
        default=None,
        description="수정된 출력 (action=modify 시)"
    )


class ListPendingApprovalsRequest(BaseModel):
    """대기 승인 목록 요청."""
    dimension: Optional[str] = None
    status: Optional[str] = Field(
        default="pending_review",
        description="상태 필터"
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=200
    )
    offset: int = Field(
        default=0,
        ge=0
    )


class ListPendingApprovalsResponse(BaseModel):
    """대기 승인 목록 응답."""
    items: List[PendingApproval]
    total: int
    limit: int
    offset: int


# Notification schemas

class ApprovalNotification(BaseModel):
    """승인 알림."""
    notification_type: str  # new_pending, escalated, expiring_soon
    checkpoint_id: UUID
    execution_id: UUID
    confidence: float
    dimension: Optional[str] = None
    expires_at: datetime
    message: str
