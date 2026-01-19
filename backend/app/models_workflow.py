"""Workflow Checkpoint Models (P0 Phase 3 2026).

HITL 워크플로우 체크포인트 및 실행 상태 모델.

Tables:
    - workflow_executions: DAG 실행 인스턴스
    - workflow_checkpoints: HITL 체크포인트 상태
    - workflow_node_results: 노드별 실행 결과

Usage:
    from app.models_workflow import (
        WorkflowExecution,
        WorkflowCheckpoint,
        WorkflowNodeResult,
    )
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    String,
    DateTime,
    Integer,
    Float,
    Boolean,
    Text,
    Index,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# =============================================================================
# Enums
# =============================================================================

class WorkflowStatus(str, Enum):
    """워크플로우 실행 상태."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"  # HITL 대기
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeStatus(str, Enum):
    """노드 실행 상태."""
    PENDING = "pending"
    RUNNING = "running"
    WAITING_REVIEW = "waiting_review"  # HITL 대기
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CheckpointAction(str, Enum):
    """체크포인트 액션."""
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    SKIP = "skip"


# =============================================================================
# Models
# =============================================================================

class WorkflowExecution(Base):
    """워크플로우 실행 인스턴스.

    DAG 전체 실행의 상태와 메타데이터를 저장합니다.

    Attributes:
        id: 실행 고유 ID
        dag_id: DAG 정의 ID
        user_id: 실행 사용자 ID
        status: 실행 상태
        dag_snapshot: DAG 정의 스냅샷 (JSON)
        initial_inputs: 초기 입력 데이터
        user_context: 사용자 컨텍스트
        current_node_id: 현재 실행 중인 노드 ID
        completed_nodes: 완료된 노드 ID 목록
        failed_node_id: 실패한 노드 ID (있는 경우)
        error_message: 에러 메시지
        estimated_credits: 예상 크레딧
        actual_credits: 실제 사용 크레딧
        started_at: 실행 시작 시간
        completed_at: 실행 완료 시간
    """
    __tablename__ = "workflow_executions"
    __table_args__ = (
        Index("ix_workflow_executions_user_id", "user_id"),
        Index("ix_workflow_executions_status", "status"),
        Index("ix_workflow_executions_dag_id", "dag_id"),
        Index("ix_workflow_executions_ip_id", "ip_id"),
        Index("ix_workflow_executions_preset_id", "preset_id"),
        Index("ix_workflow_executions_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    dag_id: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default=WorkflowStatus.PENDING.value,
    )

    # IP Context (IP-First SSoT)
    ip_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ip_catalog.id"),
        nullable=True,
    )
    preset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ip_workflow_presets.id"),
        nullable=True,
    )
    ip_context: Mapped[dict] = mapped_column(JSONB, default=dict)

    # DAG Snapshot
    dag_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict)
    initial_inputs: Mapped[dict] = mapped_column(JSONB, default=dict)
    user_context: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Execution State
    current_node_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    completed_nodes: Mapped[list] = mapped_column(JSONB, default=list)
    failed_node_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cost Tracking
    estimated_credits: Mapped[int] = mapped_column(Integer, default=0)
    actual_credits: Mapped[int] = mapped_column(Integer, default=0)

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class WorkflowCheckpoint(Base):
    """워크플로우 체크포인트.

    HITL 체크포인트 상태와 사용자 피드백을 저장합니다.

    Attributes:
        id: 체크포인트 고유 ID
        execution_id: 워크플로우 실행 ID
        node_id: 노드 ID
        tool_id: 도구 ID
        checkpoint_index: 체크포인트 순서 (0-based)
        status: 체크포인트 상태
        node_output: 노드 실행 결과 (검토 대상)
        user_action: 사용자 액션 (approve/reject/modify/skip)
        user_feedback: 사용자 피드백 텍스트
        modified_output: 수정된 출력 (modify 액션 시)
        reviewer_id: 검토자 ID
        reviewed_at: 검토 시간
        timeout_seconds: 타임아웃 (초)
        expires_at: 만료 시간
    """
    __tablename__ = "workflow_checkpoints"
    __table_args__ = (
        Index("ix_workflow_checkpoints_execution_id", "execution_id"),
        Index("ix_workflow_checkpoints_status", "status"),
        Index("ix_workflow_checkpoints_node_id", "node_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="CASCADE"),
        nullable=False,
    )
    node_id: Mapped[str] = mapped_column(String(64), nullable=False)
    tool_id: Mapped[str] = mapped_column(String(64), nullable=False)
    checkpoint_index: Mapped[int] = mapped_column(Integer, default=0)

    # Checkpoint State
    status: Mapped[str] = mapped_column(
        String(32),
        default=NodeStatus.WAITING_REVIEW.value,
    )
    node_output: Mapped[dict] = mapped_column(JSONB, default=dict)

    # User Feedback
    user_action: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    user_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    modified_output: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Reviewer
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timeout
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=3600)  # 1 hour
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class WorkflowNodeResult(Base):
    """노드별 실행 결과.

    각 노드의 입출력과 실행 메트릭을 저장합니다.

    Attributes:
        id: 결과 고유 ID
        execution_id: 워크플로우 실행 ID
        node_id: 노드 ID
        tool_id: 도구 ID
        execution_index: 실행 순서
        status: 노드 상태
        inputs: 노드 입력
        outputs: 노드 출력
        error_message: 에러 메시지
        credit_cost: 크레딧 비용
        latency_ms: 실행 시간 (ms)
        retry_count: 재시도 횟수
        metadata: 추가 메타데이터
    """
    __tablename__ = "workflow_node_results"
    __table_args__ = (
        Index("ix_workflow_node_results_execution_id", "execution_id"),
        Index("ix_workflow_node_results_node_id", "node_id"),
        Index("ix_workflow_node_results_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="CASCADE"),
        nullable=False,
    )
    node_id: Mapped[str] = mapped_column(String(64), nullable=False)
    tool_id: Mapped[str] = mapped_column(String(64), nullable=False)
    execution_index: Mapped[int] = mapped_column(Integer, default=0)

    # Execution State
    status: Mapped[str] = mapped_column(
        String(32),
        default=NodeStatus.PENDING.value,
    )
    inputs: Mapped[dict] = mapped_column(JSONB, default=dict)
    outputs: Mapped[dict] = mapped_column(JSONB, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metrics
    credit_cost: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Extra Data
    extra_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
