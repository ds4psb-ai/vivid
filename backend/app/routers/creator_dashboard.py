"""Creator Dashboard API Router (Phase 7 HITL Enhancement).

크리에이터 전용 대시보드 API 엔드포인트.

Endpoints:
    GET  /api/v1/creator/metrics - RPV 및 요약 메트릭
    GET  /api/v1/creator/pending-approvals - 크리에이터 대기 항목
    GET  /api/v1/creator/engagement - 참여도 시계열
    GET  /api/v1/creator/anomalies - 감지된 이상
    GET  /api/v1/creator/deliveries - 최근 납품 이력
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.services.creator_analytics import (
    CreatorAnalyticsService,
    CreatorMetrics,
    EngagementData,
    DeliveryRecord,
)
from app.services.approval_gate import ApprovalGateService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/creator", tags=["creator-dashboard"])


# =============================================================================
# Response Schemas
# =============================================================================

class CreatorMetricsResponse(BaseModel):
    """크리에이터 메트릭 응답."""
    rpv: float = Field(description="Revenue Per View")
    total_views: int
    total_revenue: float
    engagement_rate: float
    avg_rating: Optional[float]
    total_deliveries: int
    on_time_rate: float
    revision_rate: float
    active_projects: int
    period_days: int

    class Config:
        from_attributes = True


class EngagementDataResponse(BaseModel):
    """참여도 데이터 응답."""
    date: datetime
    views: int
    likes: int
    comments: int
    shares: int
    engagement_rate: float


class EngagementTimelineResponse(BaseModel):
    """참여도 시계열 응답."""
    period: str
    data: List[EngagementDataResponse]


class DeliveryRecordResponse(BaseModel):
    """납품 이력 응답."""
    delivery_id: UUID
    project_title: str
    delivered_at: datetime
    rating: Optional[float]
    credits_earned: int
    revision_count: int
    on_time: bool


class DeliveriesResponse(BaseModel):
    """납품 목록 응답."""
    items: List[DeliveryRecordResponse]
    total: int


class AnomalyAlertResponse(BaseModel):
    """이상 알림 응답."""
    id: str
    type: str
    severity: str
    metric_name: str
    metric_value: float
    expected_range: List[float]
    description: str
    detected_at: str


class AnomaliesResponse(BaseModel):
    """이상 목록 응답."""
    items: List[AnomalyAlertResponse]
    total: int


class PendingApprovalSummary(BaseModel):
    """대기 승인 요약."""
    checkpoint_id: UUID
    execution_id: UUID
    node_id: str
    output_preview: str
    confidence: float
    dimension: Optional[str]
    expires_at: datetime
    created_at: datetime


class PendingApprovalsResponse(BaseModel):
    """대기 승인 목록 응답."""
    items: List[PendingApprovalSummary]
    total: int


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/metrics", response_model=CreatorMetricsResponse)
async def get_creator_metrics(
    period_days: int = Query(30, ge=1, le=365, description="분석 기간 (일)"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> CreatorMetricsResponse:
    """크리에이터 RPV 및 요약 메트릭 조회.

    Args:
        period_days: 분석 기간 (일)

    Returns:
        CreatorMetricsResponse: 메트릭 요약
    """
    service = CreatorAnalyticsService(db)
    user_id = UUID(str(current_user.id))

    metrics = await service.get_creator_metrics(user_id, period_days)

    return CreatorMetricsResponse(
        rpv=metrics.rpv,
        total_views=metrics.total_views,
        total_revenue=metrics.total_revenue,
        engagement_rate=metrics.engagement_rate,
        avg_rating=metrics.avg_rating,
        total_deliveries=metrics.total_deliveries,
        on_time_rate=metrics.on_time_rate,
        revision_rate=metrics.revision_rate,
        active_projects=metrics.active_projects,
        period_days=metrics.period_days,
    )


@router.get("/engagement", response_model=EngagementTimelineResponse)
async def get_engagement_timeline(
    period: str = Query("7d", description="기간 (7d, 30d, 90d)"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> EngagementTimelineResponse:
    """참여도 시계열 조회.

    Args:
        period: 기간 (7d, 30d, 90d)

    Returns:
        EngagementTimelineResponse: 참여도 시계열
    """
    if period not in ["7d", "30d", "90d"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid period. Must be one of: 7d, 30d, 90d"
        )

    service = CreatorAnalyticsService(db)
    user_id = UUID(str(current_user.id))

    data = await service.get_engagement_timeline(user_id, period)

    return EngagementTimelineResponse(
        period=period,
        data=[
            EngagementDataResponse(
                date=d.date,
                views=d.views,
                likes=d.likes,
                comments=d.comments,
                shares=d.shares,
                engagement_rate=d.engagement_rate,
            )
            for d in data
        ],
    )


@router.get("/deliveries", response_model=DeliveriesResponse)
async def get_recent_deliveries(
    limit: int = Query(10, ge=1, le=50, description="결과 제한"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> DeliveriesResponse:
    """최근 납품 이력 조회.

    Args:
        limit: 결과 제한

    Returns:
        DeliveriesResponse: 납품 목록
    """
    service = CreatorAnalyticsService(db)
    user_id = UUID(str(current_user.id))

    deliveries = await service.get_recent_deliveries(user_id, limit)

    return DeliveriesResponse(
        items=[
            DeliveryRecordResponse(
                delivery_id=d.delivery_id,
                project_title=d.project_title,
                delivered_at=d.delivered_at,
                rating=d.rating,
                credits_earned=d.credits_earned,
                revision_count=d.revision_count,
                on_time=d.on_time,
            )
            for d in deliveries
        ],
        total=len(deliveries),
    )


@router.get("/anomalies", response_model=AnomaliesResponse)
async def get_anomalies(
    limit: int = Query(10, ge=1, le=50, description="결과 제한"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> AnomaliesResponse:
    """감지된 이상 목록 조회.

    Args:
        limit: 결과 제한

    Returns:
        AnomaliesResponse: 이상 목록
    """
    service = CreatorAnalyticsService(db)
    user_id = UUID(str(current_user.id))

    anomalies = await service.get_unresolved_anomalies(user_id, limit)

    return AnomaliesResponse(
        items=[
            AnomalyAlertResponse(
                id=a["id"],
                type=a["type"],
                severity=a["severity"],
                metric_name=a["metric_name"],
                metric_value=a["metric_value"],
                expected_range=a["expected_range"],
                description=a["description"],
                detected_at=a["detected_at"],
            )
            for a in anomalies
        ],
        total=len(anomalies),
    )


@router.get("/pending-approvals", response_model=PendingApprovalsResponse)
async def get_pending_approvals(
    limit: int = Query(20, ge=1, le=100, description="결과 제한"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> PendingApprovalsResponse:
    """크리에이터 대기 승인 목록 조회.

    Args:
        limit: 결과 제한

    Returns:
        PendingApprovalsResponse: 대기 승인 목록
    """
    approval_service = ApprovalGateService(db)

    # 현재 사용자의 대기 승인 조회
    # 실제 구현 시 사용자 ID로 필터링 필요
    items, total = await approval_service.get_pending_approvals(limit=limit)

    return PendingApprovalsResponse(
        items=[
            PendingApprovalSummary(
                checkpoint_id=item.checkpoint_id,
                execution_id=item.execution_id,
                node_id=item.node_id,
                output_preview=item.output_preview,
                confidence=item.confidence,
                dimension=item.dimension,
                expires_at=item.expires_at,
                created_at=item.created_at,
            )
            for item in items
        ],
        total=total,
    )


@router.post("/anomalies/{anomaly_id}/resolve")
async def resolve_anomaly(
    anomaly_id: UUID,
    resolution_notes: str = "",
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    """이상 해결 처리.

    Args:
        anomaly_id: 이상 ID
        resolution_notes: 해결 메모

    Returns:
        dict: 처리 결과
    """
    from sqlalchemy import select, update
    from app.models_feedback import CreatorAnomalyLog

    # 이상 조회
    result = await db.execute(
        select(CreatorAnomalyLog).where(CreatorAnomalyLog.id == anomaly_id)
    )
    anomaly = result.scalar_one_or_none()

    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    # 이미 해결된 경우
    if anomaly.resolved:
        raise HTTPException(status_code=400, detail="Anomaly already resolved")

    # 해결 처리
    anomaly.resolved = True
    anomaly.resolved_by = current_user.id
    anomaly.resolved_at = datetime.utcnow()
    anomaly.resolution_notes = resolution_notes

    await db.commit()

    return {
        "success": True,
        "anomaly_id": str(anomaly_id),
        "resolved_at": anomaly.resolved_at.isoformat(),
    }


@router.post("/detect-anomalies")
async def trigger_anomaly_detection(
    lookback_days: int = Query(30, ge=7, le=90, description="분석 기간 (일)"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    """이상 탐지 수동 실행.

    Args:
        lookback_days: 분석 기간 (일)

    Returns:
        dict: 탐지 결과
    """
    service = CreatorAnalyticsService(db)
    user_id = UUID(str(current_user.id))

    anomalies = await service.detect_anomalies(user_id, lookback_days)
    await db.commit()

    return {
        "detected": len(anomalies),
        "anomalies": [
            {
                "type": a.anomaly_type,
                "severity": a.severity,
                "metric_name": a.metric_name,
                "description": a.description,
            }
            for a in anomalies
        ],
    }
