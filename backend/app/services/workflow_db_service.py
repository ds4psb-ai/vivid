"""Workflow DB Service - Bridge between router and DB-based executor.

이 서비스는 기존 in-memory 워크플로우 API를 DB 기반 실행기로 연결합니다.

SSoT Decision:
- WorkflowExecution (DB): IP/Flow 워크플로우의 SSoT
- WorkflowSessionManager (in-memory): Phase 1 이후 deprecated

Features:
- /plan, /start, /advance, /execute API를 DB 기반으로 처리
- IP Context 지원 (ip_id, preset_id)
- run-token 통합 준비

Usage:
    from app.services.workflow_db_service import WorkflowDBService

    service = WorkflowDBService(db)
    execution_id = await service.create_from_plan(plan, user_id, ip_context)
    await service.advance_step(execution_id, user)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models_workflow import (
    WorkflowExecution,
    WorkflowNodeResult,
    WorkflowStatus,
    NodeStatus,
)
from app.models_ip import IPGeneration
from app.schemas.ip_context import IPContext
from app.services.workflow_planner import WorkflowPlanResult

logger = get_logger("workflow_db_service")


class WorkflowDBService:
    """DB 기반 워크플로우 서비스.

    기존 in-memory 세션 매니저의 역할을 DB로 이관합니다.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service.

        Args:
            db: 비동기 DB 세션
        """
        self._db = db

    # -------------------------------------------------------------------------
    # Create (from /plan)
    # -------------------------------------------------------------------------

    async def create_from_plan(
        self,
        plan: WorkflowPlanResult,
        user_id: str,
        original_request: str,
        ip_id: Optional[uuid.UUID] = None,
        preset_id: Optional[uuid.UUID] = None,
        ip_context: Optional[IPContext] = None,
        initial_params: Optional[Dict[str, Any]] = None,
    ) -> WorkflowExecution:
        """워크플로우 계획에서 실행 레코드 생성.

        Args:
            plan: 매칭된 워크플로우 계획
            user_id: 사용자 ID
            original_request: 원본 요청 텍스트
            ip_id: IP 카탈로그 ID (Optional)
            preset_id: IP 프리셋 ID (Optional)
            ip_context: IP 컨텍스트 (Optional)
            initial_params: 초기 입력 파라미터

        Returns:
            생성된 WorkflowExecution
        """
        initial_params = initial_params or {}

        # DAG 스냅샷 생성
        dag_snapshot = {
            "template_id": plan.template_id,
            "template_name": plan.template.name,
            "template_name_ko": plan.template.name_ko,
            "template_description": plan.template.description_ko,
            "tools": plan.template.tools,
            "nodes": plan.node_chain,
            "connections": plan.template.connections,
            "execution_order": [n["id"] for n in plan.node_chain],
        }

        # 실행 레코드 생성
        execution = WorkflowExecution(
            dag_id=plan.template_id,
            user_id=user_id,
            status=WorkflowStatus.PENDING.value,
            dag_snapshot=dag_snapshot,
            initial_inputs={
                "original_request": original_request,
                "extracted_params": plan.suggested_params,
                **initial_params,
            },
            user_context={},
            estimated_credits=plan.total_credits,
            ip_id=ip_id,
            preset_id=preset_id,
            ip_context=ip_context.model_dump() if ip_context else {},
        )

        self._db.add(execution)
        await self._db.flush()

        logger.info(
            f"[WorkflowDB] Created execution | id={execution.id} | "
            f"template={plan.template_id} | ip_id={ip_id}"
        )

        return execution

    # -------------------------------------------------------------------------
    # Read
    # -------------------------------------------------------------------------

    async def get_execution(
        self,
        execution_id: uuid.UUID,
    ) -> Optional[WorkflowExecution]:
        """실행 조회.

        Args:
            execution_id: 실행 ID

        Returns:
            WorkflowExecution 또는 None
        """
        result = await self._db.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.id == execution_id
            )
        )
        return result.scalar_one_or_none()

    async def get_execution_by_session_id(
        self,
        session_id: str,
    ) -> Optional[WorkflowExecution]:
        """세션 ID로 실행 조회 (하위 호환).

        기존 API에서 session_id는 문자열 UUID입니다.

        Args:
            session_id: 세션 ID (UUID 문자열)

        Returns:
            WorkflowExecution 또는 None
        """
        try:
            execution_id = uuid.UUID(session_id)
        except ValueError:
            return None

        return await self.get_execution(execution_id)

    async def get_user_executions(
        self,
        user_id: str,
        limit: int = 20,
    ) -> List[WorkflowExecution]:
        """사용자의 실행 목록 조회.

        Args:
            user_id: 사용자 ID
            limit: 최대 개수

        Returns:
            WorkflowExecution 목록
        """
        result = await self._db.execute(
            select(WorkflowExecution)
            .where(WorkflowExecution.user_id == user_id)
            .order_by(WorkflowExecution.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_node_results(
        self,
        execution_id: uuid.UUID,
    ) -> List[WorkflowNodeResult]:
        """실행의 노드 결과 조회.

        Args:
            execution_id: 실행 ID

        Returns:
            WorkflowNodeResult 목록
        """
        result = await self._db.execute(
            select(WorkflowNodeResult)
            .where(WorkflowNodeResult.execution_id == execution_id)
            .order_by(WorkflowNodeResult.started_at)
        )
        return list(result.scalars().all())

    # -------------------------------------------------------------------------
    # Update Status
    # -------------------------------------------------------------------------

    async def start_execution(
        self,
        execution_id: uuid.UUID,
        initial_params: Optional[Dict[str, Any]] = None,
    ) -> WorkflowExecution:
        """실행 시작.

        Args:
            execution_id: 실행 ID
            initial_params: 추가 초기 파라미터

        Returns:
            업데이트된 WorkflowExecution
        """
        execution = await self.get_execution(execution_id)
        if not execution:
            raise ValueError(f"Execution not found: {execution_id}")

        # 초기 파라미터 병합
        if initial_params:
            merged_inputs = {**execution.initial_inputs, **initial_params}
            execution.initial_inputs = merged_inputs

        execution.status = WorkflowStatus.RUNNING.value
        execution.started_at = datetime.utcnow()

        await self._db.flush()

        logger.info(f"[WorkflowDB] Started execution | id={execution_id}")
        return execution

    async def update_current_node(
        self,
        execution_id: uuid.UUID,
        node_id: str,
    ) -> None:
        """현재 실행 중인 노드 업데이트.

        Args:
            execution_id: 실행 ID
            node_id: 노드 ID
        """
        await self._db.execute(
            update(WorkflowExecution)
            .where(WorkflowExecution.id == execution_id)
            .values(current_node_id=node_id)
        )
        await self._db.flush()

    async def record_node_result(
        self,
        execution_id: uuid.UUID,
        node_id: str,
        tool_id: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        credits_used: int = 0,
        latency_ms: int = 0,
    ) -> WorkflowNodeResult:
        """노드 실행 결과 기록.

        Args:
            execution_id: 실행 ID
            node_id: 노드 ID
            tool_id: 도구 ID
            inputs: 입력
            outputs: 출력
            credits_used: 사용 크레딧
            latency_ms: 지연시간

        Returns:
            생성된 WorkflowNodeResult
        """
        node_result = WorkflowNodeResult(
            execution_id=execution_id,
            node_id=node_id,
            tool_id=tool_id,
            status=NodeStatus.COMPLETED.value,
            inputs=inputs,
            outputs=outputs,
            credit_cost=credits_used,
            latency_ms=latency_ms,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

        self._db.add(node_result)

        # completed_nodes 업데이트
        execution = await self.get_execution(execution_id)
        if execution:
            completed = list(execution.completed_nodes)
            if node_id not in completed:
                completed.append(node_id)
            execution.completed_nodes = completed
            execution.actual_credits = (execution.actual_credits or 0) + credits_used

        await self._db.flush()

        logger.debug(
            f"[WorkflowDB] Node completed | execution={execution_id} | "
            f"node={node_id} | credits={credits_used}"
        )

        return node_result

    async def record_node_failure(
        self,
        execution_id: uuid.UUID,
        node_id: str,
        tool_id: str,
        inputs: Dict[str, Any],
        error_message: str,
    ) -> WorkflowNodeResult:
        """노드 실패 기록.

        Args:
            execution_id: 실행 ID
            node_id: 노드 ID
            tool_id: 도구 ID
            inputs: 입력
            error_message: 에러 메시지

        Returns:
            생성된 WorkflowNodeResult
        """
        node_result = WorkflowNodeResult(
            execution_id=execution_id,
            node_id=node_id,
            tool_id=tool_id,
            status=NodeStatus.FAILED.value,
            inputs=inputs,
            error_message=error_message,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

        self._db.add(node_result)

        # 실행 상태도 실패로
        execution = await self.get_execution(execution_id)
        if execution:
            execution.status = WorkflowStatus.FAILED.value
            execution.failed_node_id = node_id
            execution.error_message = error_message
            execution.completed_at = datetime.utcnow()

        await self._db.flush()

        logger.error(
            f"[WorkflowDB] Node failed | execution={execution_id} | "
            f"node={node_id} | error={error_message}"
        )

        return node_result

    async def complete_execution(
        self,
        execution_id: uuid.UUID,
    ) -> WorkflowExecution:
        """실행 완료.

        Args:
            execution_id: 실행 ID

        Returns:
            업데이트된 WorkflowExecution
        """
        execution = await self.get_execution(execution_id)
        if not execution:
            raise ValueError(f"Execution not found: {execution_id}")

        execution.status = WorkflowStatus.COMPLETED.value
        execution.completed_at = datetime.utcnow()
        execution.current_node_id = None

        await self._db.flush()

        logger.info(
            f"[WorkflowDB] Execution completed | id={execution_id} | "
            f"credits={execution.actual_credits}"
        )

        return execution

    async def fail_execution(
        self,
        execution_id: uuid.UUID,
        node_id: Optional[str] = None,
        error_message: str = "Unknown error",
    ) -> WorkflowExecution:
        """실행 실패.

        Args:
            execution_id: 실행 ID
            node_id: 실패한 노드 ID
            error_message: 에러 메시지

        Returns:
            업데이트된 WorkflowExecution
        """
        execution = await self.get_execution(execution_id)
        if not execution:
            raise ValueError(f"Execution not found: {execution_id}")

        execution.status = WorkflowStatus.FAILED.value
        execution.failed_node_id = node_id
        execution.error_message = error_message
        execution.completed_at = datetime.utcnow()

        await self._db.flush()

        logger.error(
            f"[WorkflowDB] Execution failed | id={execution_id} | "
            f"node={node_id} | error={error_message}"
        )

        return execution

    # -------------------------------------------------------------------------
    # IP Generation Linking
    # -------------------------------------------------------------------------

    async def link_ip_generation(
        self,
        execution_id: uuid.UUID,
        ip_generation_id: uuid.UUID,
    ) -> None:
        """IP Generation을 워크플로우 실행에 연결.

        Args:
            execution_id: 워크플로우 실행 ID
            ip_generation_id: IP Generation ID
        """
        await self._db.execute(
            update(IPGeneration)
            .where(IPGeneration.id == ip_generation_id)
            .values(workflow_execution_id=execution_id)
        )
        await self._db.flush()

        logger.info(
            f"[WorkflowDB] Linked IP generation | "
            f"execution={execution_id} | ip_gen={ip_generation_id}"
        )

    # -------------------------------------------------------------------------
    # Status Helpers
    # -------------------------------------------------------------------------

    def get_current_step_index(
        self,
        execution: WorkflowExecution,
    ) -> int:
        """현재 스텝 인덱스 계산.

        Args:
            execution: 워크플로우 실행

        Returns:
            현재 스텝 인덱스 (0-based)
        """
        return len(execution.completed_nodes)

    def get_total_steps(
        self,
        execution: WorkflowExecution,
    ) -> int:
        """전체 스텝 수 계산.

        Args:
            execution: 워크플로우 실행

        Returns:
            전체 스텝 수
        """
        dag = execution.dag_snapshot or {}
        return len(dag.get("execution_order", dag.get("nodes", [])))

    def get_next_node(
        self,
        execution: WorkflowExecution,
    ) -> Optional[Dict[str, Any]]:
        """다음 실행할 노드 정보 반환.

        Args:
            execution: 워크플로우 실행

        Returns:
            다음 노드 정보 또는 None (완료 시)
        """
        dag = execution.dag_snapshot or {}
        nodes = dag.get("nodes", [])
        execution_order = dag.get("execution_order", [n.get("id") for n in nodes])
        completed_set = set(execution.completed_nodes)

        for node_id in execution_order:
            if node_id not in completed_set:
                # nodes 리스트에서 해당 노드 찾기
                for node in nodes:
                    if node.get("id") == node_id:
                        return node
                # 못 찾으면 기본 구조 반환
                return {"id": node_id, "tool_id": node_id}

        return None

    def to_session_response(
        self,
        execution: WorkflowExecution,
        node_results: Optional[List[WorkflowNodeResult]] = None,
    ) -> Dict[str, Any]:
        """API 응답용 세션 정보 변환.

        기존 WorkflowSession 응답 형식과 호환됩니다.

        Args:
            execution: 워크플로우 실행
            node_results: 노드 결과 목록

        Returns:
            API 응답 형식의 딕셔너리
        """
        dag = execution.dag_snapshot or {}
        nodes = dag.get("nodes", [])

        # 노드 상태 구성
        node_results_map = {}
        if node_results:
            for nr in node_results:
                node_results_map[nr.node_id] = nr

        node_states = []
        for i, node in enumerate(nodes):
            node_id = node.get("id", f"node_{i}")
            nr = node_results_map.get(node_id)

            if nr:
                status = nr.status
                output = nr.outputs
                error = nr.error_message
            elif node_id in execution.completed_nodes:
                status = "completed"
                output = None
                error = None
            elif node_id == execution.current_node_id:
                status = "executing"
                output = None
                error = None
            else:
                status = "pending"
                output = None
                error = None

            node_states.append({
                "node_id": node_id,
                "tool_id": node.get("tool_id", ""),
                "order": i,
                "status": status,
                "inputs": node.get("data", {}).get("inputs", {}),
                "output": output,
                "error": error,
            })

        return {
            "session_id": str(execution.id),
            "status": execution.status,
            "current_step": self.get_current_step_index(execution),
            "total_steps": self.get_total_steps(execution),
            "nodes": node_states,
            "consumed_credits": execution.actual_credits or 0,
            "ip_id": str(execution.ip_id) if execution.ip_id else None,
            "preset_id": str(execution.preset_id) if execution.preset_id else None,
        }
