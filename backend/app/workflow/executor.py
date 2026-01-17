"""HITL Workflow Executor (P0 Phase 3 2026).

인간 개입 지점(HITL)이 포함된 워크플로우 실행기.

Features:
    - DAG 기반 워크플로우 실행
    - HITL 체크포인트에서 자동 일시정지
    - 사용자 피드백 기반 재개/수정
    - 실행 상태 영속화

Reference:
    - Temporal Human-in-the-Loop: https://temporal.io/human-in-the-loop
    - LangGraph Checkpoints: https://docs.langchain.com/oss/python/langchain

Usage:
    from app.workflow.executor import (
        CheckpointService,
        HITLWorkflowExecutor,
        create_executor,
    )

    executor = await create_executor(db)
    execution_id = await executor.start_workflow(dag, user_id)

    # HITL 체크포인트 도달 시 자동 일시정지
    # 사용자가 검토 후 재개
    await executor.resume_workflow(execution_id, checkpoint_id, action="approve")
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_workflow import (
    WorkflowExecution,
    WorkflowCheckpoint,
    WorkflowNodeResult,
    WorkflowStatus,
    NodeStatus,
    CheckpointAction,
)
from app.workflow.types import (
    ExecutableDAG,
    ExecutableDAGV2,
    DAGNode,
    ConditionalEdge,
    RouterNode,
    WorkflowState,
    RoutingDecision,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Exceptions
# =============================================================================

class WorkflowExecutionError(Exception):
    """워크플로우 실행 예외."""
    pass


class CheckpointNotFoundError(WorkflowExecutionError):
    """체크포인트를 찾을 수 없음."""
    pass


class WorkflowNotPausedError(WorkflowExecutionError):
    """워크플로우가 일시정지 상태가 아님."""
    pass


class InvalidCheckpointActionError(WorkflowExecutionError):
    """유효하지 않은 체크포인트 액션."""
    pass


# =============================================================================
# Tool Executor Protocol
# =============================================================================

class ToolExecutor(Protocol):
    """도구 실행기 프로토콜.

    실제 도구 실행은 이 프로토콜을 구현하는 클래스에서 처리합니다.
    """

    async def execute(
        self,
        tool_id: str,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """도구 실행.

        Args:
            tool_id: 도구 ID
            inputs: 입력 데이터
            context: 실행 컨텍스트

        Returns:
            출력 데이터
        """
        ...


# =============================================================================
# Checkpoint Service
# =============================================================================

class CheckpointService:
    """체크포인트 서비스.

    HITL 체크포인트 CRUD 및 상태 관리.

    Features:
        - 체크포인트 생성/조회/업데이트
        - 타임아웃 관리
        - 사용자 피드백 처리
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize checkpoint service.

        Args:
            db: 비동기 DB 세션
        """
        self._db = db

    async def create_checkpoint(
        self,
        execution_id: uuid.UUID,
        node_id: str,
        tool_id: str,
        node_output: Dict[str, Any],
        checkpoint_index: int = 0,
        timeout_seconds: int = 3600,
    ) -> WorkflowCheckpoint:
        """체크포인트 생성.

        Args:
            execution_id: 워크플로우 실행 ID
            node_id: 노드 ID
            tool_id: 도구 ID
            node_output: 노드 실행 결과
            checkpoint_index: 체크포인트 순서
            timeout_seconds: 타임아웃 (초)

        Returns:
            생성된 체크포인트
        """
        checkpoint = WorkflowCheckpoint(
            execution_id=execution_id,
            node_id=node_id,
            tool_id=tool_id,
            checkpoint_index=checkpoint_index,
            status=NodeStatus.WAITING_REVIEW.value,
            node_output=node_output,
            timeout_seconds=timeout_seconds,
            expires_at=datetime.utcnow() + timedelta(seconds=timeout_seconds),
        )

        self._db.add(checkpoint)
        await self._db.flush()

        logger.info(
            f"[Checkpoint] Created | execution={execution_id} | "
            f"node={node_id} | checkpoint_id={checkpoint.id}"
        )

        return checkpoint

    async def get_checkpoint(
        self,
        checkpoint_id: uuid.UUID,
    ) -> Optional[WorkflowCheckpoint]:
        """체크포인트 조회.

        Args:
            checkpoint_id: 체크포인트 ID

        Returns:
            체크포인트 또는 None
        """
        result = await self._db.execute(
            select(WorkflowCheckpoint).where(
                WorkflowCheckpoint.id == checkpoint_id
            )
        )
        return result.scalar_one_or_none()

    async def get_pending_checkpoints(
        self,
        execution_id: uuid.UUID,
    ) -> List[WorkflowCheckpoint]:
        """대기 중인 체크포인트 조회.

        Args:
            execution_id: 워크플로우 실행 ID

        Returns:
            대기 중인 체크포인트 목록
        """
        result = await self._db.execute(
            select(WorkflowCheckpoint)
            .where(
                WorkflowCheckpoint.execution_id == execution_id,
                WorkflowCheckpoint.status == NodeStatus.WAITING_REVIEW.value,
            )
            .order_by(WorkflowCheckpoint.checkpoint_index)
        )
        return list(result.scalars().all())

    async def resolve_checkpoint(
        self,
        checkpoint_id: uuid.UUID,
        action: CheckpointAction,
        reviewer_id: str,
        feedback: Optional[str] = None,
        modified_output: Optional[Dict[str, Any]] = None,
    ) -> WorkflowCheckpoint:
        """체크포인트 해결.

        Args:
            checkpoint_id: 체크포인트 ID
            action: 사용자 액션
            reviewer_id: 검토자 ID
            feedback: 피드백 텍스트
            modified_output: 수정된 출력 (modify 액션 시)

        Returns:
            업데이트된 체크포인트

        Raises:
            CheckpointNotFoundError: 체크포인트 없음
        """
        checkpoint = await self.get_checkpoint(checkpoint_id)
        if not checkpoint:
            raise CheckpointNotFoundError(f"Checkpoint not found: {checkpoint_id}")

        # 상태 결정
        if action == CheckpointAction.APPROVE:
            new_status = NodeStatus.COMPLETED.value
        elif action == CheckpointAction.REJECT:
            new_status = NodeStatus.FAILED.value
        elif action == CheckpointAction.MODIFY:
            new_status = NodeStatus.COMPLETED.value
        elif action == CheckpointAction.SKIP:
            new_status = NodeStatus.SKIPPED.value
        else:
            raise InvalidCheckpointActionError(f"Invalid action: {action}")

        # 업데이트
        checkpoint.status = new_status
        checkpoint.user_action = action.value
        checkpoint.user_feedback = feedback
        checkpoint.reviewer_id = reviewer_id
        checkpoint.reviewed_at = datetime.utcnow()

        if action == CheckpointAction.MODIFY and modified_output:
            checkpoint.modified_output = modified_output

        await self._db.flush()

        logger.info(
            f"[Checkpoint] Resolved | checkpoint_id={checkpoint_id} | "
            f"action={action.value} | reviewer={reviewer_id}"
        )

        return checkpoint

    async def check_expired_checkpoints(
        self,
        execution_id: uuid.UUID,
    ) -> List[WorkflowCheckpoint]:
        """만료된 체크포인트 확인.

        Args:
            execution_id: 워크플로우 실행 ID

        Returns:
            만료된 체크포인트 목록
        """
        result = await self._db.execute(
            select(WorkflowCheckpoint)
            .where(
                WorkflowCheckpoint.execution_id == execution_id,
                WorkflowCheckpoint.status == NodeStatus.WAITING_REVIEW.value,
                WorkflowCheckpoint.expires_at < datetime.utcnow(),
            )
        )
        return list(result.scalars().all())


# =============================================================================
# HITL Workflow Executor
# =============================================================================

class HITLWorkflowExecutor:
    """HITL 워크플로우 실행기.

    DAG 기반 워크플로우를 실행하며, HITL 체크포인트에서 자동으로
    일시정지하고 사용자 피드백을 기다립니다.

    Lifecycle:
        1. start_workflow(): DAG 실행 시작
        2. (자동) execute_next_node(): 다음 노드 실행
        3. (HITL) pause_at_checkpoint(): 체크포인트에서 일시정지
        4. resume_workflow(): 사용자 피드백 후 재개
        5. (반복 2-4)
        6. complete_workflow(): 모든 노드 완료 시

    Example:
        >>> executor = HITLWorkflowExecutor(db, tool_executor)
        >>> execution_id = await executor.start_workflow(dag, user_id)
        >>> # 워크플로우가 HITL 체크포인트에서 자동 일시정지
        >>> # 사용자 검토 후
        >>> await executor.resume_workflow(
        ...     execution_id,
        ...     checkpoint_id,
        ...     action=CheckpointAction.APPROVE,
        ... )
    """

    def __init__(
        self,
        db: AsyncSession,
        tool_executor: Optional[ToolExecutor] = None,
        checkpoint_service: Optional[CheckpointService] = None,
    ) -> None:
        """Initialize executor.

        Args:
            db: 비동기 DB 세션
            tool_executor: 도구 실행기
            checkpoint_service: 체크포인트 서비스
        """
        self._db = db
        self._tool_executor = tool_executor or MockToolExecutor()
        self._checkpoint_service = checkpoint_service or CheckpointService(db)

        # 노드 출력 캐시 (execution_id -> node_id -> outputs)
        self._output_cache: Dict[uuid.UUID, Dict[str, Dict[str, Any]]] = {}

    async def start_workflow(
        self,
        dag: ExecutableDAG,
        user_id: str,
        initial_inputs: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> uuid.UUID:
        """워크플로우 실행 시작.

        Args:
            dag: 실행할 DAG
            user_id: 사용자 ID
            initial_inputs: 초기 입력
            user_context: 사용자 컨텍스트

        Returns:
            실행 ID
        """
        initial_inputs = initial_inputs or {}
        user_context = user_context or {}

        # 실행 레코드 생성
        execution = WorkflowExecution(
            dag_id=dag.dag_id,
            user_id=user_id,
            status=WorkflowStatus.PENDING.value,
            dag_snapshot=dag.to_dict(),
            initial_inputs=initial_inputs,
            user_context=user_context,
            estimated_credits=dag.estimated_credits,
        )

        self._db.add(execution)
        await self._db.flush()

        execution_id = execution.id

        logger.info(
            f"[Executor] Started workflow | execution_id={execution_id} | "
            f"dag_id={dag.dag_id} | user_id={user_id}"
        )

        # 실행 시작
        await self._run_workflow(execution_id, dag, initial_inputs, user_context)

        return execution_id

    async def resume_workflow(
        self,
        execution_id: uuid.UUID,
        checkpoint_id: uuid.UUID,
        action: CheckpointAction,
        reviewer_id: str,
        feedback: Optional[str] = None,
        modified_output: Optional[Dict[str, Any]] = None,
    ) -> None:
        """워크플로우 재개.

        HITL 체크포인트 해결 후 워크플로우를 계속 실행합니다.

        Args:
            execution_id: 실행 ID
            checkpoint_id: 체크포인트 ID
            action: 사용자 액션
            reviewer_id: 검토자 ID
            feedback: 피드백
            modified_output: 수정된 출력
        """
        # 실행 조회
        execution = await self._get_execution(execution_id)
        if not execution:
            raise WorkflowExecutionError(f"Execution not found: {execution_id}")

        if execution.status != WorkflowStatus.PAUSED.value:
            raise WorkflowNotPausedError(
                f"Workflow is not paused: {execution.status}"
            )

        # 체크포인트 해결
        checkpoint = await self._checkpoint_service.resolve_checkpoint(
            checkpoint_id=checkpoint_id,
            action=action,
            reviewer_id=reviewer_id,
            feedback=feedback,
            modified_output=modified_output,
        )

        # 수정된 출력이 있으면 캐시 업데이트
        if action == CheckpointAction.MODIFY and modified_output:
            if execution_id not in self._output_cache:
                self._output_cache[execution_id] = {}
            self._output_cache[execution_id][checkpoint.node_id] = modified_output

        # 거부 시 워크플로우 실패 처리
        if action == CheckpointAction.REJECT:
            await self._fail_workflow(execution, checkpoint.node_id, "Rejected by user")
            return

        # 완료된 노드 목록 업데이트
        completed_nodes = list(execution.completed_nodes)
        if checkpoint.node_id not in completed_nodes:
            completed_nodes.append(checkpoint.node_id)
        execution.completed_nodes = completed_nodes

        logger.info(
            f"[Executor] Resuming workflow | execution_id={execution_id} | "
            f"checkpoint_id={checkpoint_id} | action={action.value}"
        )

        # DAG 복원 및 계속 실행
        dag = self._restore_dag(execution.dag_snapshot)
        await self._continue_workflow(
            execution_id,
            dag,
            execution.initial_inputs,
            execution.user_context,
            completed_nodes,
        )

    async def get_execution_status(
        self,
        execution_id: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        """실행 상태 조회.

        Args:
            execution_id: 실행 ID

        Returns:
            실행 상태 정보
        """
        execution = await self._get_execution(execution_id)
        if not execution:
            return None

        pending_checkpoints = await self._checkpoint_service.get_pending_checkpoints(
            execution_id
        )

        return {
            "execution_id": str(execution.id),
            "dag_id": execution.dag_id,
            "status": execution.status,
            "current_node_id": execution.current_node_id,
            "completed_nodes": execution.completed_nodes,
            "failed_node_id": execution.failed_node_id,
            "error_message": execution.error_message,
            "estimated_credits": execution.estimated_credits,
            "actual_credits": execution.actual_credits,
            "pending_checkpoints": [
                {
                    "checkpoint_id": str(cp.id),
                    "node_id": cp.node_id,
                    "tool_id": cp.tool_id,
                    "node_output": cp.node_output,
                    "expires_at": cp.expires_at.isoformat() if cp.expires_at else None,
                }
                for cp in pending_checkpoints
            ],
            "created_at": execution.created_at.isoformat(),
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        }

    async def cancel_workflow(self, execution_id: uuid.UUID) -> bool:
        """워크플로우 취소.

        Args:
            execution_id: 실행 ID

        Returns:
            취소 성공 여부
        """
        execution = await self._get_execution(execution_id)
        if not execution:
            return False

        if execution.status in [
            WorkflowStatus.COMPLETED.value,
            WorkflowStatus.FAILED.value,
            WorkflowStatus.CANCELLED.value,
        ]:
            return False

        execution.status = WorkflowStatus.CANCELLED.value
        await self._db.flush()

        logger.info(f"[Executor] Workflow cancelled | execution_id={execution_id}")
        return True

    # -------------------------------------------------------------------------
    # Internal Methods
    # -------------------------------------------------------------------------

    async def _run_workflow(
        self,
        execution_id: uuid.UUID,
        dag: ExecutableDAG,
        initial_inputs: Dict[str, Any],
        user_context: Dict[str, Any],
    ) -> None:
        """워크플로우 실행."""
        execution = await self._get_execution(execution_id)
        if not execution:
            return

        execution.status = WorkflowStatus.RUNNING.value
        execution.started_at = datetime.utcnow()
        await self._db.flush()

        # 출력 캐시 초기화
        self._output_cache[execution_id] = {}

        await self._continue_workflow(
            execution_id,
            dag,
            initial_inputs,
            user_context,
            [],
        )

    async def _continue_workflow(
        self,
        execution_id: uuid.UUID,
        dag: ExecutableDAG,
        initial_inputs: Dict[str, Any],
        user_context: Dict[str, Any],
        completed_nodes: List[str],
    ) -> None:
        """워크플로우 계속 실행."""
        execution = await self._get_execution(execution_id)
        if not execution:
            return

        execution.status = WorkflowStatus.RUNNING.value
        await self._db.flush()

        completed_set = set(completed_nodes)

        for node_id in dag.execution_order:
            # 이미 완료된 노드 스킵
            if node_id in completed_set:
                continue

            node = dag.nodes.get(node_id)
            if not node:
                continue

            # 노드 실행
            execution.current_node_id = node_id
            await self._db.flush()

            try:
                # 입력 준비 (이전 노드 출력 + 초기 입력)
                node_inputs = self._prepare_inputs(
                    execution_id,
                    node,
                    dag,
                    initial_inputs,
                )

                # 노드 실행
                outputs = await self._execute_node(
                    execution_id,
                    node,
                    node_inputs,
                    user_context,
                )

                # 출력 캐시 저장
                if execution_id not in self._output_cache:
                    self._output_cache[execution_id] = {}
                self._output_cache[execution_id][node_id] = outputs

                # HITL 체크포인트 확인
                if node.requires_human_review:
                    checkpoint_index = len([
                        nid for nid in dag.execution_order[:dag.execution_order.index(node_id)]
                        if dag.nodes[nid].requires_human_review
                    ])

                    checkpoint = await self._checkpoint_service.create_checkpoint(
                        execution_id=execution_id,
                        node_id=node_id,
                        tool_id=node.tool_id,
                        node_output=outputs,
                        checkpoint_index=checkpoint_index,
                    )

                    # 워크플로우 일시정지
                    execution.status = WorkflowStatus.PAUSED.value
                    await self._db.flush()

                    logger.info(
                        f"[Executor] Workflow paused at HITL checkpoint | "
                        f"execution_id={execution_id} | node_id={node_id}"
                    )
                    return

                # 완료된 노드 추가
                completed_nodes_list = list(execution.completed_nodes)
                completed_nodes_list.append(node_id)
                execution.completed_nodes = completed_nodes_list
                await self._db.flush()

            except Exception as e:
                await self._fail_workflow(execution, node_id, str(e))
                return

        # 모든 노드 완료
        await self._complete_workflow(execution)

    async def _execute_node(
        self,
        execution_id: uuid.UUID,
        node: DAGNode,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """노드 실행."""
        # 노드 결과 레코드 생성
        node_result = WorkflowNodeResult(
            execution_id=execution_id,
            node_id=node.node_id,
            tool_id=node.tool_id,
            status=NodeStatus.RUNNING.value,
            inputs=inputs,
            started_at=datetime.utcnow(),
        )
        self._db.add(node_result)
        await self._db.flush()

        start_time = datetime.utcnow()

        try:
            # 도구 실행
            outputs = await self._tool_executor.execute(
                tool_id=node.tool_id,
                inputs=inputs,
                context=context,
            )

            # 성공 기록
            latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            node_result.status = NodeStatus.COMPLETED.value
            node_result.outputs = outputs
            node_result.latency_ms = latency_ms
            node_result.completed_at = datetime.utcnow()
            await self._db.flush()

            logger.debug(
                f"[Executor] Node completed | node_id={node.node_id} | "
                f"tool_id={node.tool_id} | latency_ms={latency_ms}"
            )

            return outputs

        except Exception as e:
            # 실패 기록
            node_result.status = NodeStatus.FAILED.value
            node_result.error_message = str(e)
            node_result.completed_at = datetime.utcnow()
            await self._db.flush()
            raise

    def _prepare_inputs(
        self,
        execution_id: uuid.UUID,
        node: DAGNode,
        dag: ExecutableDAG,
        initial_inputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """노드 입력 준비."""
        inputs = dict(node.inputs)

        # 이전 노드 출력에서 입력 수집
        for edge in dag.edges:
            if edge.to_node_id == node.node_id:
                from_outputs = self._output_cache.get(execution_id, {}).get(
                    edge.from_node_id, {}
                )
                if edge.from_port in from_outputs:
                    inputs[edge.to_port] = from_outputs[edge.from_port]

        # 초기 입력 병합 (노드 입력으로 덮어쓰지 않음)
        for key, value in initial_inputs.items():
            if key not in inputs:
                inputs[key] = value

        return inputs

    async def _complete_workflow(self, execution: WorkflowExecution) -> None:
        """워크플로우 완료 처리."""
        execution.status = WorkflowStatus.COMPLETED.value
        execution.completed_at = datetime.utcnow()
        execution.current_node_id = None
        await self._db.flush()

        # 캐시 정리
        if execution.id in self._output_cache:
            del self._output_cache[execution.id]

        logger.info(
            f"[Executor] Workflow completed | execution_id={execution.id}"
        )

    async def _fail_workflow(
        self,
        execution: WorkflowExecution,
        node_id: str,
        error_message: str,
    ) -> None:
        """워크플로우 실패 처리."""
        execution.status = WorkflowStatus.FAILED.value
        execution.failed_node_id = node_id
        execution.error_message = error_message
        execution.completed_at = datetime.utcnow()
        await self._db.flush()

        # 캐시 정리
        if execution.id in self._output_cache:
            del self._output_cache[execution.id]

        logger.error(
            f"[Executor] Workflow failed | execution_id={execution.id} | "
            f"node_id={node_id} | error={error_message}"
        )

    async def _get_execution(
        self,
        execution_id: uuid.UUID,
    ) -> Optional[WorkflowExecution]:
        """실행 조회."""
        result = await self._db.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.id == execution_id
            )
        )
        return result.scalar_one_or_none()

    def _restore_dag(self, dag_snapshot: Dict[str, Any]) -> ExecutableDAG:
        """DAG 스냅샷에서 복원."""
        from app.workflow.types import DAGEdge, DataType

        nodes = {}
        for node_id, node_data in dag_snapshot.get("nodes", {}).items():
            nodes[node_id] = DAGNode(
                node_id=node_data["node_id"],
                tool_id=node_data["tool_id"],
                inputs=node_data.get("inputs", {}),
                dependencies=set(node_data.get("dependencies", [])),
                requires_human_review=node_data.get("requires_human_review", False),
                status=node_data.get("status", "pending"),
            )

        edges = []
        for edge_data in dag_snapshot.get("edges", []):
            data_type = None
            if edge_data.get("data_type"):
                data_type = DataType(edge_data["data_type"])
            edges.append(DAGEdge(
                from_node_id=edge_data["from_node_id"],
                from_port=edge_data["from_port"],
                to_node_id=edge_data["to_node_id"],
                to_port=edge_data["to_port"],
                data_type=data_type,
            ))

        return ExecutableDAG(
            dag_id=dag_snapshot["dag_id"],
            nodes=nodes,
            edges=edges,
            execution_order=dag_snapshot.get("execution_order", []),
            human_review_points=dag_snapshot.get("human_review_points", []),
            estimated_credits=dag_snapshot.get("estimated_credits", 0),
            estimated_latency_ms=dag_snapshot.get("estimated_latency_ms", 0),
            metadata=dag_snapshot.get("metadata", {}),
        )


# =============================================================================
# Mock Tool Executor (for testing)
# =============================================================================

class MockToolExecutor:
    """Mock 도구 실행기 (테스트용)."""

    async def execute(
        self,
        tool_id: str,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Mock 실행 - 입력을 그대로 출력으로 반환."""
        # 시뮬레이션 딜레이
        await asyncio.sleep(0.01)

        return {
            "result": f"Mock output from {tool_id}",
            "inputs_received": inputs,
            "tool_id": tool_id,
        }


# =============================================================================
# Factory Functions
# =============================================================================

async def create_executor(
    db: AsyncSession,
    tool_executor: Optional[ToolExecutor] = None,
) -> HITLWorkflowExecutor:
    """HITL 워크플로우 실행기 생성.

    Args:
        db: 비동기 DB 세션
        tool_executor: 도구 실행기 (None이면 Mock 사용)

    Returns:
        HITLWorkflowExecutor 인스턴스
    """
    return HITLWorkflowExecutor(
        db=db,
        tool_executor=tool_executor,
    )


# =============================================================================
# HITL Workflow Executor V2 (2026 Extension - Conditional Edges)
# =============================================================================

class HITLWorkflowExecutorV2(HITLWorkflowExecutor):
    """HITL 워크플로우 실행기 V2.

    2026 확장:
    - ConditionalEdge 지원 (상태 기반 동적 라우팅)
    - RouterNode 지원 (LLM 기반 라우팅)
    - WorkflowState 관리
    - ExecutableDAGV2 처리

    ConditionalEdge 실행 흐름:
        1. 현재 노드 실행 완료
        2. 해당 노드에서 출발하는 ConditionalEdge 확인
        3. 조건 함수(condition) 실행하여 라우트 결정
        4. route_map에서 다음 노드 선택
        5. 다음 노드로 점프 (선형 순서 무시)

    Example:
        >>> executor = HITLWorkflowExecutorV2(db, tool_executor)
        >>> dag_v2 = await analyzer.build_dag_v2(intent, user_context)
        >>> execution_id = await executor.start_workflow_v2(dag_v2, user_id)
    """

    def __init__(
        self,
        db: AsyncSession,
        tool_executor: Optional[ToolExecutor] = None,
        checkpoint_service: Optional[CheckpointService] = None,
    ) -> None:
        """Initialize V2 executor."""
        super().__init__(db, tool_executor, checkpoint_service)

        # 워크플로우 상태 캐시 (execution_id -> WorkflowState)
        self._state_cache: Dict[uuid.UUID, WorkflowState] = {}

        # 조건부 엣지 매핑 (execution_id -> from_node_id -> ConditionalEdge)
        self._conditional_edges: Dict[uuid.UUID, Dict[str, ConditionalEdge]] = {}

    async def start_workflow_v2(
        self,
        dag: ExecutableDAGV2,
        user_id: str,
        initial_inputs: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> uuid.UUID:
        """V2 워크플로우 실행 시작.

        Args:
            dag: ExecutableDAGV2 (조건부 엣지 포함)
            user_id: 사용자 ID
            initial_inputs: 초기 입력
            user_context: 사용자 컨텍스트

        Returns:
            실행 ID
        """
        initial_inputs = initial_inputs or {}
        user_context = user_context or {}

        # 기본 DAG로 실행 시작
        base_dag = ExecutableDAG(
            dag_id=dag.dag_id,
            nodes=dag.nodes,
            edges=dag.edges,
            execution_order=dag.execution_order,
            human_review_points=dag.human_review_points,
            estimated_credits=dag.estimated_credits,
            estimated_latency_ms=dag.estimated_latency_ms,
            metadata=dag.metadata,
        )

        # 실행 레코드 생성
        execution = WorkflowExecution(
            dag_id=dag.dag_id,
            user_id=user_id,
            status=WorkflowStatus.PENDING.value,
            dag_snapshot=dag.to_dict(),  # V2 스냅샷 저장
            initial_inputs=initial_inputs,
            user_context=user_context,
            estimated_credits=dag.estimated_credits,
        )

        self._db.add(execution)
        await self._db.flush()

        execution_id = execution.id

        # 조건부 엣지 캐싱
        self._conditional_edges[execution_id] = {
            edge.from_node_id: edge
            for edge in dag.conditional_edges
        }

        # 워크플로우 상태 초기화
        self._state_cache[execution_id] = WorkflowState(
            query=initial_inputs.get("query", initial_inputs.get("intent", "")),
            intent_type="unknown",
            selected_tools=[node.tool_id for node in dag.nodes.values()],
            current_step="start",
            accumulated_outputs={},
            user_context=user_context,
            confidence=dag.orchestration_plan.confidence if dag.orchestration_plan else 0.7,
        )

        logger.info(
            f"[ExecutorV2] Started workflow | execution_id={execution_id} | "
            f"dag_id={dag.dag_id} | conditional_edges={len(dag.conditional_edges)}"
        )

        # 실행 시작
        await self._run_workflow_v2(
            execution_id,
            dag,
            initial_inputs,
            user_context,
        )

        return execution_id

    async def _run_workflow_v2(
        self,
        execution_id: uuid.UUID,
        dag: ExecutableDAGV2,
        initial_inputs: Dict[str, Any],
        user_context: Dict[str, Any],
    ) -> None:
        """V2 워크플로우 실행."""
        execution = await self._get_execution(execution_id)
        if not execution:
            return

        execution.status = WorkflowStatus.RUNNING.value
        execution.started_at = datetime.utcnow()
        await self._db.flush()

        # 출력 캐시 초기화
        self._output_cache[execution_id] = {}

        await self._continue_workflow_v2(
            execution_id,
            dag,
            initial_inputs,
            user_context,
            [],
        )

    async def _continue_workflow_v2(
        self,
        execution_id: uuid.UUID,
        dag: ExecutableDAGV2,
        initial_inputs: Dict[str, Any],
        user_context: Dict[str, Any],
        completed_nodes: List[str],
    ) -> None:
        """V2 워크플로우 계속 실행 (조건부 라우팅 지원)."""
        execution = await self._get_execution(execution_id)
        if not execution:
            return

        execution.status = WorkflowStatus.RUNNING.value
        await self._db.flush()

        state = self._state_cache.get(execution_id, WorkflowState())
        completed_set = set(completed_nodes)
        conditional_edges = self._conditional_edges.get(execution_id, {})

        # 실행 순서 (조건부 점프 가능)
        current_index = 0
        execution_order = dag.execution_order

        while current_index < len(execution_order):
            node_id = execution_order[current_index]

            # 이미 완료된 노드 스킵
            if node_id in completed_set:
                current_index += 1
                continue

            node = dag.nodes.get(node_id)
            if not node:
                current_index += 1
                continue

            # 노드 실행
            execution.current_node_id = node_id
            state.current_step = node_id
            await self._db.flush()

            try:
                # 입력 준비
                node_inputs = self._prepare_inputs(
                    execution_id,
                    node,
                    dag,
                    initial_inputs,
                )

                # RouterNode인 경우 특별 처리
                if isinstance(node, RouterNode):
                    routing_result = await self._execute_router_node(
                        execution_id,
                        node,
                        node_inputs,
                        user_context,
                        state,
                    )
                    outputs = {"route": routing_result.route, "confidence": routing_result.confidence}
                    state.route = routing_result.route
                    state.confidence = routing_result.confidence
                else:
                    # 일반 노드 실행
                    outputs = await self._execute_node(
                        execution_id,
                        node,
                        node_inputs,
                        user_context,
                    )

                # 상태 업데이트
                state.accumulated_outputs[node_id] = outputs

                # 출력 캐시 저장
                if execution_id not in self._output_cache:
                    self._output_cache[execution_id] = {}
                self._output_cache[execution_id][node_id] = outputs

                # HITL 체크포인트 확인
                if node.requires_human_review:
                    checkpoint_index = len([
                        nid for nid in execution_order[:current_index]
                        if dag.nodes[nid].requires_human_review
                    ])

                    checkpoint = await self._checkpoint_service.create_checkpoint(
                        execution_id=execution_id,
                        node_id=node_id,
                        tool_id=node.tool_id,
                        node_output=outputs,
                        checkpoint_index=checkpoint_index,
                    )

                    execution.status = WorkflowStatus.PAUSED.value
                    await self._db.flush()

                    logger.info(
                        f"[ExecutorV2] Paused at HITL | execution_id={execution_id} | "
                        f"node_id={node_id}"
                    )
                    return

                # 조건부 엣지 확인 및 점프
                if node_id in conditional_edges:
                    conditional_edge = conditional_edges[node_id]
                    next_node_id = self._resolve_conditional_edge(
                        conditional_edge,
                        state,
                    )

                    logger.info(
                        f"[ExecutorV2] Conditional routing | from={node_id} | "
                        f"to={next_node_id} | route={state.route}"
                    )

                    # 다음 노드가 'end'면 워크플로우 종료
                    if next_node_id == "end":
                        completed_set.add(node_id)
                        break

                    # 다음 노드 인덱스로 점프
                    if next_node_id in execution_order:
                        next_index = execution_order.index(next_node_id)
                        completed_set.add(node_id)
                        current_index = next_index
                        continue

                # 완료된 노드 추가
                completed_set.add(node_id)
                completed_nodes_list = list(execution.completed_nodes)
                completed_nodes_list.append(node_id)
                execution.completed_nodes = completed_nodes_list
                await self._db.flush()

                current_index += 1

            except Exception as e:
                await self._fail_workflow(execution, node_id, str(e))
                return

        # 모든 노드 완료
        await self._complete_workflow(execution)

        # 캐시 정리
        if execution_id in self._state_cache:
            del self._state_cache[execution_id]
        if execution_id in self._conditional_edges:
            del self._conditional_edges[execution_id]

    def _resolve_conditional_edge(
        self,
        edge: ConditionalEdge,
        state: WorkflowState,
    ) -> str:
        """조건부 엣지 해결.

        Args:
            edge: 조건부 엣지
            state: 현재 워크플로우 상태

        Returns:
            다음 노드 ID
        """
        return edge.resolve(state)

    async def _execute_router_node(
        self,
        execution_id: uuid.UUID,
        node: RouterNode,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
        state: WorkflowState,
    ) -> RoutingDecision:
        """RouterNode 실행 (LLM 기반 라우팅).

        Args:
            execution_id: 실행 ID
            node: 라우터 노드
            inputs: 입력
            context: 컨텍스트
            state: 워크플로우 상태

        Returns:
            라우팅 결정
        """
        # TODO: 실제 LLM 호출 구현 (Phase 2)
        # 현재는 휴리스틱 기반

        query = inputs.get("query", state.query)
        query_lower = query.lower()

        # 가능한 라우트에서 선택
        selected_route = node.fallback_route
        confidence = 0.6

        for route in node.possible_routes:
            if route in query_lower:
                selected_route = route
                confidence = 0.8
                break

        # 신뢰도 기반 fallback
        if state.confidence < 0.5:
            selected_route = node.fallback_route
            confidence = 0.5

        logger.debug(
            f"[ExecutorV2] Router decision | node_id={node.node_id} | "
            f"route={selected_route} | confidence={confidence}"
        )

        return RoutingDecision(
            route=selected_route,
            confidence=confidence,
            reasoning=f"Selected '{selected_route}' based on query analysis",
        )

    async def resume_workflow_v2(
        self,
        execution_id: uuid.UUID,
        checkpoint_id: uuid.UUID,
        action: CheckpointAction,
        reviewer_id: str,
        feedback: Optional[str] = None,
        modified_output: Optional[Dict[str, Any]] = None,
    ) -> None:
        """V2 워크플로우 재개."""
        # 기본 체크포인트 처리는 상위 클래스 사용
        execution = await self._get_execution(execution_id)
        if not execution:
            raise WorkflowExecutionError(f"Execution not found: {execution_id}")

        if execution.status != WorkflowStatus.PAUSED.value:
            raise WorkflowNotPausedError(f"Workflow is not paused: {execution.status}")

        # 체크포인트 해결
        checkpoint = await self._checkpoint_service.resolve_checkpoint(
            checkpoint_id=checkpoint_id,
            action=action,
            reviewer_id=reviewer_id,
            feedback=feedback,
            modified_output=modified_output,
        )

        # 상태 업데이트
        if action == CheckpointAction.MODIFY and modified_output:
            if execution_id not in self._output_cache:
                self._output_cache[execution_id] = {}
            self._output_cache[execution_id][checkpoint.node_id] = modified_output

            # WorkflowState도 업데이트
            if execution_id in self._state_cache:
                self._state_cache[execution_id].accumulated_outputs[checkpoint.node_id] = modified_output

        if action == CheckpointAction.REJECT:
            await self._fail_workflow(execution, checkpoint.node_id, "Rejected by user")
            return

        # 완료된 노드 업데이트
        completed_nodes = list(execution.completed_nodes)
        if checkpoint.node_id not in completed_nodes:
            completed_nodes.append(checkpoint.node_id)
        execution.completed_nodes = completed_nodes

        logger.info(
            f"[ExecutorV2] Resuming | execution_id={execution_id} | "
            f"checkpoint={checkpoint_id}"
        )

        # V2 DAG 복원 및 계속 실행
        dag_v2 = self._restore_dag_v2(execution.dag_snapshot)
        await self._continue_workflow_v2(
            execution_id,
            dag_v2,
            execution.initial_inputs,
            execution.user_context,
            completed_nodes,
        )

    def _restore_dag_v2(self, dag_snapshot: Dict[str, Any]) -> ExecutableDAGV2:
        """DAG V2 스냅샷에서 복원."""
        from app.workflow.types import DAGEdge, DataType

        # 노드 복원
        nodes = {}
        for node_id, node_data in dag_snapshot.get("nodes", {}).items():
            if node_data.get("routing_prompt"):
                # RouterNode
                nodes[node_id] = RouterNode(
                    node_id=node_data["node_id"],
                    tool_id=node_data["tool_id"],
                    inputs=node_data.get("inputs", {}),
                    dependencies=set(node_data.get("dependencies", [])),
                    requires_human_review=node_data.get("requires_human_review", False),
                    status=node_data.get("status", "pending"),
                    routing_prompt=node_data.get("routing_prompt", ""),
                    possible_routes=node_data.get("possible_routes", []),
                    llm_model=node_data.get("llm_model", "gemini-2.5-flash"),
                    fallback_route=node_data.get("fallback_route", "general"),
                )
            else:
                # 일반 DAGNode
                nodes[node_id] = DAGNode(
                    node_id=node_data["node_id"],
                    tool_id=node_data["tool_id"],
                    inputs=node_data.get("inputs", {}),
                    dependencies=set(node_data.get("dependencies", [])),
                    requires_human_review=node_data.get("requires_human_review", False),
                    status=node_data.get("status", "pending"),
                )

        # 엣지 복원
        edges = []
        for edge_data in dag_snapshot.get("edges", []):
            data_type = None
            if edge_data.get("data_type"):
                data_type = DataType(edge_data["data_type"])
            edges.append(DAGEdge(
                from_node_id=edge_data["from_node_id"],
                from_port=edge_data["from_port"],
                to_node_id=edge_data["to_node_id"],
                to_port=edge_data["to_port"],
                data_type=data_type,
            ))

        # 조건부 엣지 복원
        conditional_edges = []
        for ce_data in dag_snapshot.get("conditional_edges", []):
            # 주의: condition 함수는 직렬화 불가, 기본 라우터 사용
            def default_condition(state: WorkflowState) -> str:
                if state.confidence >= 0.8:
                    return "condition_true"
                elif state.confidence >= 0.5:
                    return "option_a"
                else:
                    return "condition_false"

            conditional_edges.append(ConditionalEdge(
                from_node_id=ce_data["from_node_id"],
                condition=default_condition,
                route_map=ce_data.get("route_map", {}),
                default_route=ce_data.get("default_route", "end"),
            ))

        # OrchestrationPlan 복원 (있으면)
        orchestration_plan = None
        if dag_snapshot.get("orchestration_plan"):
            from app.workflow.types import QueryComplexity, OrchestrationPattern, CompoundOrchestrationPlan
            op = dag_snapshot["orchestration_plan"]
            orchestration_plan = CompoundOrchestrationPlan(
                complexity=QueryComplexity(op.get("complexity", "moderate")),
                pattern=OrchestrationPattern(op.get("pattern", "linear")),
                primary_tools=op.get("primary_tools", []),
                optional_tools=op.get("optional_tools", []),
                conditional_branches=op.get("conditional_branches", {}),
                estimated_steps=op.get("estimated_steps", 1),
                confidence=op.get("confidence", 0.7),
                reasoning=op.get("reasoning", ""),
            )

        return ExecutableDAGV2(
            dag_id=dag_snapshot["dag_id"],
            nodes=nodes,
            edges=edges,
            execution_order=dag_snapshot.get("execution_order", []),
            human_review_points=dag_snapshot.get("human_review_points", []),
            estimated_credits=dag_snapshot.get("estimated_credits", 0),
            estimated_latency_ms=dag_snapshot.get("estimated_latency_ms", 0),
            metadata=dag_snapshot.get("metadata", {}),
            conditional_edges=conditional_edges,
            router_nodes=dag_snapshot.get("router_nodes", []),
            orchestration_plan=orchestration_plan,
        )


# =============================================================================
# Factory Functions V2
# =============================================================================

async def create_executor_v2(
    db: AsyncSession,
    tool_executor: Optional[ToolExecutor] = None,
) -> HITLWorkflowExecutorV2:
    """HITL 워크플로우 실행기 V2 생성.

    Args:
        db: 비동기 DB 세션
        tool_executor: 도구 실행기

    Returns:
        HITLWorkflowExecutorV2 인스턴스
    """
    return HITLWorkflowExecutorV2(
        db=db,
        tool_executor=tool_executor,
    )
