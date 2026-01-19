"""Approval Gate API Router (Phase 7 HITL Enhancement).

승인 게이트 관련 API 엔드포인트.

Endpoints:
    GET  /api/v1/approval-gate/pending - 대기 중 승인 목록
    POST /api/v1/approval-gate/{id}/resolve - 피드백과 함께 승인
    GET  /api/v1/approval-gate/stats - 승인 통계
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models_workflow import CheckpointAction
from app.services.approval_gate import ApprovalGateService
from app.schemas.approval_gate_schemas import (
    ApprovalResult,
    ApprovalStatsResponse,
    ListPendingApprovalsResponse,
    PendingApproval,
    ResolveApprovalRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/approval-gate", tags=["approval-gate"])


# =============================================================================
# Helper
# =============================================================================

def _get_approval_service(db: AsyncSession) -> ApprovalGateService:
    """Get approval gate service instance."""
    return ApprovalGateService(db=db)


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/pending", response_model=ListPendingApprovalsResponse)
async def list_pending_approvals(
    dimension: Optional[str] = Query(None, description="차원 필터"),
    status: Optional[str] = Query("pending_review", description="상태 필터"),
    limit: int = Query(50, ge=1, le=200, description="결과 제한"),
    offset: int = Query(0, ge=0, description="오프셋"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ListPendingApprovalsResponse:
    """대기 중인 승인 목록 조회.

    Returns:
        ListPendingApprovalsResponse: 대기 승인 목록
    """
    service = _get_approval_service(db)

    items, total = await service.get_pending_approvals(
        dimension=dimension,
        status=status,
        limit=limit,
        offset=offset,
    )

    return ListPendingApprovalsResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{checkpoint_id}", response_model=PendingApproval)
async def get_approval(
    checkpoint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> PendingApproval:
    """특정 승인 항목 조회.

    Args:
        checkpoint_id: 체크포인트 ID

    Returns:
        PendingApproval: 승인 정보

    Raises:
        HTTPException: 체크포인트를 찾을 수 없는 경우
    """
    service = _get_approval_service(db)

    items, _ = await service.get_pending_approvals(limit=1000)

    for item in items:
        if item.checkpoint_id == checkpoint_id:
            return item

    raise HTTPException(
        status_code=404,
        detail=f"Checkpoint not found: {checkpoint_id}"
    )


@router.post("/{checkpoint_id}/resolve", response_model=ApprovalResult)
async def resolve_approval(
    checkpoint_id: UUID,
    request: ResolveApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ApprovalResult:
    """피드백과 함께 승인 처리.

    Args:
        checkpoint_id: 체크포인트 ID
        request: 승인 해결 요청

    Returns:
        ApprovalResult: 처리 결과

    Raises:
        HTTPException: 유효하지 않은 액션 또는 체크포인트
    """
    # 액션 검증
    try:
        action = CheckpointAction(request.action)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action: {request.action}. Must be one of: approve, reject, modify, skip"
        )

    service = _get_approval_service(db)

    try:
        result = await service.approve_with_feedback(
            checkpoint_id=checkpoint_id,
            action=action,
            reviewer_id=str(current_user.id),
            feedback=request.feedback,
            quality_rating=request.quality_rating,
            modified_output=request.modified_output,
        )
        await db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to resolve approval: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to process approval")


@router.get("/stats", response_model=ApprovalStatsResponse)
async def get_approval_stats(
    period_start: Optional[datetime] = Query(None, description="기간 시작"),
    period_end: Optional[datetime] = Query(None, description="기간 종료"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ApprovalStatsResponse:
    """승인 통계 조회.

    Args:
        period_start: 기간 시작 (기본: 30일 전)
        period_end: 기간 종료 (기본: 현재)

    Returns:
        ApprovalStatsResponse: 승인 통계
    """
    service = _get_approval_service(db)

    stats = await service.get_approval_stats(
        period_start=period_start,
        period_end=period_end,
    )

    return stats


@router.post("/process-expired")
async def process_expired_checkpoints(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """만료된 체크포인트 처리 (관리자 전용).

    Returns:
        dict: 처리 결과
    """
    service = _get_approval_service(db)

    processed_count = await service.process_expired_checkpoints()
    await db.commit()

    return {
        "processed": processed_count,
        "message": f"Processed {processed_count} expired checkpoints",
    }
