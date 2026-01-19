"""Approval Gate Service (Phase 7 HITL Enhancement).

신뢰도 기반 자동/수동 승인 라우팅 서비스.

2026 Best Practices:
- Confidence-Based Routing: 고신뢰도 → 자동승인, 저신뢰도 → 수동검토
- Durable Promises: 외부 신호 대기 패턴
- NIST AI RMF: 고위험 결정에 명시적 인간 감독
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_workflow import (
    WorkflowCheckpoint,
    WorkflowExecution,
    NodeStatus,
    CheckpointAction,
    WorkflowStatus,
)
from app.schemas.approval_gate_schemas import (
    ApprovalDecision,
    ApprovalGateConfig,
    DimensionApprovalConfig,
    PendingApproval,
    ApprovalResult,
    ApprovalEvaluationResult,
    ApprovalStatsResponse,
    DimensionApprovalStats,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Default Configuration
# =============================================================================

DEFAULT_GATE_CONFIG = ApprovalGateConfig(
    auto_approve_threshold=0.85,
    escalate_threshold=0.50,
    timeout_seconds=3600,
    notification_channels=["email"],
    dimension_overrides={
        # 고위험 차원은 수동 검토 강화
        "4D": DimensionApprovalConfig(
            auto_approve_threshold=0.90,
            requires_manual_review=False,
        ),
        "VEO": DimensionApprovalConfig(
            auto_approve_threshold=0.88,
            timeout_seconds=7200,  # 2시간
        ),
    },
)


# =============================================================================
# Approval Gate Service
# =============================================================================

class ApprovalGateService:
    """신뢰도 기반 승인 라우팅 서비스.

    출력물의 신뢰도에 따라:
    - confidence >= 0.85: 자동승인 (사용자 개입 없이 진행)
    - confidence < 0.50: 수동검토 에스컬레이션 (알림 발송)
    - 그 외: 단축 타임아웃 체크포인트 (검토 대기)

    Attributes:
        db: 비동기 DB 세션
        config: 승인 게이트 설정
    """

    def __init__(
        self,
        db: AsyncSession,
        config: Optional[ApprovalGateConfig] = None,
    ) -> None:
        """Initialize approval gate service.

        Args:
            db: 비동기 DB 세션
            config: 승인 게이트 설정 (기본값 사용 시 None)
        """
        self._db = db
        self._config = config or DEFAULT_GATE_CONFIG

    def _get_threshold_for_dimension(
        self,
        dimension: Optional[str],
        threshold_type: str,
    ) -> float:
        """차원별 임계값 조회.

        Args:
            dimension: 차원 키 (예: "4D", "VEO")
            threshold_type: 임계값 유형 (auto_approve, escalate)

        Returns:
            해당 차원의 임계값
        """
        if dimension and dimension in self._config.dimension_overrides:
            override = self._config.dimension_overrides[dimension]
            if threshold_type == "auto_approve" and override.auto_approve_threshold:
                return override.auto_approve_threshold
            if threshold_type == "escalate" and override.escalate_threshold:
                return override.escalate_threshold

        if threshold_type == "auto_approve":
            return self._config.auto_approve_threshold
        return self._config.escalate_threshold

    def _get_timeout_for_dimension(self, dimension: Optional[str]) -> int:
        """차원별 타임아웃 조회."""
        if dimension and dimension in self._config.dimension_overrides:
            override = self._config.dimension_overrides[dimension]
            if override.timeout_seconds:
                return override.timeout_seconds
        return self._config.timeout_seconds

    def _requires_manual_review(self, dimension: Optional[str]) -> bool:
        """차원이 항상 수동 검토를 필요로 하는지 확인."""
        if dimension and dimension in self._config.dimension_overrides:
            override = self._config.dimension_overrides[dimension]
            return override.requires_manual_review
        return False

    async def evaluate_for_approval(
        self,
        execution_id: uuid.UUID,
        node_id: str,
        output: Dict[str, Any],
        confidence: float,
        dimension: Optional[str] = None,
        tool_id: Optional[str] = None,
        checkpoint_index: int = 0,
    ) -> ApprovalEvaluationResult:
        """출력물 승인 평가.

        신뢰도에 따라 자동승인, 대기검토, 에스컬레이션을 결정합니다.

        Args:
            execution_id: 워크플로우 실행 ID
            node_id: 노드 ID
            output: 노드 출력
            confidence: 신뢰도 점수 (0.0-1.0)
            dimension: 차원 키
            tool_id: 도구 ID
            checkpoint_index: 체크포인트 순서

        Returns:
            ApprovalEvaluationResult: 평가 결과

        Raises:
            ValueError: 유효하지 않은 신뢰도 점수
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {confidence}")

        auto_threshold = self._get_threshold_for_dimension(dimension, "auto_approve")
        escalate_threshold = self._get_threshold_for_dimension(dimension, "escalate")
        requires_review = self._requires_manual_review(dimension)

        # 1. 수동 검토 필수 차원
        if requires_review:
            decision = ApprovalDecision.PENDING_REVIEW
            reason = f"Dimension {dimension} requires manual review"
            auto_approved = False

        # 2. 고신뢰도 → 자동승인
        elif confidence >= auto_threshold:
            decision = ApprovalDecision.AUTO_APPROVED
            reason = f"Confidence {confidence:.3f} >= threshold {auto_threshold:.3f}"
            auto_approved = True

        # 3. 저신뢰도 → 에스컬레이션
        elif confidence < escalate_threshold:
            decision = ApprovalDecision.ESCALATED
            reason = f"Confidence {confidence:.3f} < escalation threshold {escalate_threshold:.3f}"
            auto_approved = False

        # 4. 중간 신뢰도 → 대기 검토
        else:
            decision = ApprovalDecision.PENDING_REVIEW
            reason = f"Confidence {confidence:.3f} requires review"
            auto_approved = False

        # 체크포인트 생성 (자동승인이 아닌 경우)
        checkpoint_id = None
        if not auto_approved:
            checkpoint = await self._create_checkpoint(
                execution_id=execution_id,
                node_id=node_id,
                tool_id=tool_id or "unknown",
                output=output,
                confidence=confidence,
                decision=decision,
                checkpoint_index=checkpoint_index,
                dimension=dimension,
            )
            checkpoint_id = checkpoint.id

        logger.info(
            f"[ApprovalGate] Evaluated | execution={execution_id} | node={node_id} | "
            f"confidence={confidence:.3f} | decision={decision.value} | "
            f"auto_approved={auto_approved}"
        )

        return ApprovalEvaluationResult(
            execution_id=execution_id,
            node_id=node_id,
            confidence=confidence,
            decision=decision,
            checkpoint_id=checkpoint_id,
            auto_approved=auto_approved,
            reason=reason,
        )

    async def _create_checkpoint(
        self,
        execution_id: uuid.UUID,
        node_id: str,
        tool_id: str,
        output: Dict[str, Any],
        confidence: float,
        decision: ApprovalDecision,
        checkpoint_index: int,
        dimension: Optional[str],
    ) -> WorkflowCheckpoint:
        """승인 대기 체크포인트 생성."""
        timeout = self._get_timeout_for_dimension(dimension)

        checkpoint = WorkflowCheckpoint(
            execution_id=execution_id,
            node_id=node_id,
            tool_id=tool_id,
            checkpoint_index=checkpoint_index,
            status=NodeStatus.WAITING_REVIEW.value,
            node_output=output,
            timeout_seconds=timeout,
            expires_at=datetime.utcnow() + timedelta(seconds=timeout),
            confidence_score=confidence,
            auto_approved=False,
            approval_decision=decision.value,
        )

        self._db.add(checkpoint)
        await self._db.flush()

        return checkpoint

    async def approve_with_feedback(
        self,
        checkpoint_id: uuid.UUID,
        action: CheckpointAction,
        reviewer_id: str,
        feedback: Optional[str] = None,
        quality_rating: Optional[int] = None,
        modified_output: Optional[Dict[str, Any]] = None,
    ) -> ApprovalResult:
        """피드백과 함께 승인 처리.

        Args:
            checkpoint_id: 체크포인트 ID
            action: 승인 액션 (approve, reject, modify, skip)
            reviewer_id: 검토자 ID
            feedback: 검토자 피드백
            quality_rating: 품질 평점 (1-5)
            modified_output: 수정된 출력 (action=modify 시)

        Returns:
            ApprovalResult: 처리 결과

        Raises:
            ValueError: 체크포인트를 찾을 수 없는 경우
        """
        # 체크포인트 조회
        result = await self._db.execute(
            select(WorkflowCheckpoint).where(
                WorkflowCheckpoint.id == checkpoint_id
            )
        )
        checkpoint = result.scalar_one_or_none()

        if not checkpoint:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        # 이미 처리된 경우
        if checkpoint.status != NodeStatus.WAITING_REVIEW.value:
            raise ValueError(f"Checkpoint already processed: {checkpoint.status}")

        # 체크포인트 업데이트
        now = datetime.utcnow()
        checkpoint.user_action = action.value
        checkpoint.user_feedback = feedback
        checkpoint.reviewer_id = reviewer_id
        checkpoint.reviewed_at = now
        checkpoint.quality_rating = quality_rating

        if action == CheckpointAction.MODIFY and modified_output:
            checkpoint.modified_output = modified_output

        if action in (CheckpointAction.APPROVE, CheckpointAction.MODIFY):
            checkpoint.status = NodeStatus.COMPLETED.value
        elif action == CheckpointAction.REJECT:
            checkpoint.status = NodeStatus.FAILED.value
        elif action == CheckpointAction.SKIP:
            checkpoint.status = NodeStatus.SKIPPED.value

        await self._db.flush()

        # 워크플로우 재개 시도
        workflow_resumed = False
        if action in (CheckpointAction.APPROVE, CheckpointAction.MODIFY, CheckpointAction.SKIP):
            workflow_resumed = await self._try_resume_workflow(checkpoint.execution_id)

        logger.info(
            f"[ApprovalGate] Resolved | checkpoint={checkpoint_id} | "
            f"action={action.value} | reviewer={reviewer_id} | "
            f"rating={quality_rating} | resumed={workflow_resumed}"
        )

        return ApprovalResult(
            checkpoint_id=checkpoint_id,
            action=action.value,
            reviewer_id=reviewer_id,
            feedback=feedback,
            quality_rating=quality_rating,
            processed_at=now,
            workflow_resumed=workflow_resumed,
        )

    async def _try_resume_workflow(self, execution_id: uuid.UUID) -> bool:
        """워크플로우 재개 시도."""
        # 워크플로우 상태 확인
        result = await self._db.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.id == execution_id
            )
        )
        execution = result.scalar_one_or_none()

        if not execution or execution.status != WorkflowStatus.PAUSED.value:
            return False

        # 대기 중인 체크포인트가 없으면 재개
        pending_result = await self._db.execute(
            select(func.count()).select_from(WorkflowCheckpoint).where(
                and_(
                    WorkflowCheckpoint.execution_id == execution_id,
                    WorkflowCheckpoint.status == NodeStatus.WAITING_REVIEW.value,
                )
            )
        )
        pending_count = pending_result.scalar() or 0

        if pending_count == 0:
            execution.status = WorkflowStatus.RUNNING.value
            await self._db.flush()
            return True

        return False

    async def get_pending_approvals(
        self,
        dimension: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[PendingApproval], int]:
        """대기 중인 승인 목록 조회.

        Args:
            dimension: 차원 필터
            status: 상태 필터
            limit: 결과 제한
            offset: 결과 오프셋

        Returns:
            (승인 목록, 전체 개수) 튜플
        """
        # 기본 쿼리
        conditions = [
            WorkflowCheckpoint.status == NodeStatus.WAITING_REVIEW.value,
        ]

        # 차원 필터 (node_output에서 추출)
        if dimension:
            conditions.append(
                WorkflowCheckpoint.node_output["dimension"].astext == dimension
            )

        # 카운트 쿼리
        count_query = select(func.count()).select_from(WorkflowCheckpoint).where(
            and_(*conditions)
        )
        total = (await self._db.execute(count_query)).scalar() or 0

        # 메인 쿼리
        query = (
            select(WorkflowCheckpoint)
            .where(and_(*conditions))
            .order_by(WorkflowCheckpoint.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self._db.execute(query)
        checkpoints = list(result.scalars())

        # PendingApproval 변환
        items = []
        for cp in checkpoints:
            output_preview = str(cp.node_output)[:500] if cp.node_output else ""
            dim = cp.node_output.get("dimension") if cp.node_output else None

            items.append(PendingApproval(
                checkpoint_id=cp.id,
                execution_id=cp.execution_id,
                node_id=cp.node_id,
                tool_id=cp.tool_id,
                output_preview=output_preview,
                confidence=cp.confidence_score or 0.0,
                dimension=dim,
                auteur_key=cp.node_output.get("auteur_key") if cp.node_output else None,
                decision=ApprovalDecision(cp.approval_decision) if cp.approval_decision else ApprovalDecision.PENDING_REVIEW,
                expires_at=cp.expires_at or datetime.utcnow() + timedelta(hours=1),
                created_at=cp.created_at,
                node_output=cp.node_output,
                reviewer_id=cp.reviewer_id,
            ))

        return items, total

    async def get_approval_stats(
        self,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> ApprovalStatsResponse:
        """승인 통계 조회.

        Args:
            period_start: 기간 시작 (기본: 30일 전)
            period_end: 기간 종료 (기본: 현재)

        Returns:
            ApprovalStatsResponse: 승인 통계
        """
        if not period_end:
            period_end = datetime.utcnow()
        if not period_start:
            period_start = period_end - timedelta(days=30)

        # 기간 조건
        period_condition = and_(
            WorkflowCheckpoint.created_at >= period_start,
            WorkflowCheckpoint.created_at <= period_end,
        )

        # 전체 통계
        total_result = await self._db.execute(
            select(func.count()).select_from(WorkflowCheckpoint).where(period_condition)
        )
        total = total_result.scalar() or 0

        # 자동승인 통계
        auto_result = await self._db.execute(
            select(func.count()).select_from(WorkflowCheckpoint).where(
                and_(
                    period_condition,
                    WorkflowCheckpoint.auto_approved == True,
                )
            )
        )
        auto_count = auto_result.scalar() or 0

        # 대기 중
        pending_result = await self._db.execute(
            select(func.count()).select_from(WorkflowCheckpoint).where(
                and_(
                    period_condition,
                    WorkflowCheckpoint.status == NodeStatus.WAITING_REVIEW.value,
                )
            )
        )
        pending_count = pending_result.scalar() or 0

        # 에스컬레이션
        escalated_result = await self._db.execute(
            select(func.count()).select_from(WorkflowCheckpoint).where(
                and_(
                    period_condition,
                    WorkflowCheckpoint.approval_decision == ApprovalDecision.ESCALATED.value,
                )
            )
        )
        escalated_count = escalated_result.scalar() or 0

        # 거부
        rejected_result = await self._db.execute(
            select(func.count()).select_from(WorkflowCheckpoint).where(
                and_(
                    period_condition,
                    WorkflowCheckpoint.user_action == CheckpointAction.REJECT.value,
                )
            )
        )
        rejected_count = rejected_result.scalar() or 0

        # 타임아웃
        timeout_result = await self._db.execute(
            select(func.count()).select_from(WorkflowCheckpoint).where(
                and_(
                    period_condition,
                    WorkflowCheckpoint.expires_at < datetime.utcnow(),
                    WorkflowCheckpoint.status == NodeStatus.WAITING_REVIEW.value,
                )
            )
        )
        timeout_count = timeout_result.scalar() or 0

        # 평균 신뢰도
        avg_conf_result = await self._db.execute(
            select(func.avg(WorkflowCheckpoint.confidence_score))
            .where(period_condition)
        )
        avg_confidence = avg_conf_result.scalar()

        # 자동승인률
        auto_rate = auto_count / total if total > 0 else 0.0

        return ApprovalStatsResponse(
            total_checkpoints=total,
            auto_approved_count=auto_count,
            pending_count=pending_count,
            escalated_count=escalated_count,
            timeout_count=timeout_count,
            rejected_count=rejected_count,
            auto_approve_rate=auto_rate,
            avg_confidence_score=avg_confidence,
            period_start=period_start,
            period_end=period_end,
        )

    async def process_expired_checkpoints(self) -> int:
        """만료된 체크포인트 처리.

        Returns:
            처리된 체크포인트 수
        """
        now = datetime.utcnow()

        # 만료된 대기 체크포인트 조회
        result = await self._db.execute(
            select(WorkflowCheckpoint).where(
                and_(
                    WorkflowCheckpoint.status == NodeStatus.WAITING_REVIEW.value,
                    WorkflowCheckpoint.expires_at < now,
                )
            )
        )
        expired = list(result.scalars())

        for checkpoint in expired:
            checkpoint.status = NodeStatus.FAILED.value
            checkpoint.approval_decision = ApprovalDecision.TIMEOUT.value
            checkpoint.user_feedback = "Checkpoint expired without review"

        await self._db.flush()

        if expired:
            logger.warning(
                f"[ApprovalGate] Processed {len(expired)} expired checkpoints"
            )

        return len(expired)
