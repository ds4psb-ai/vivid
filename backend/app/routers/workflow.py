"""Workflow API Router (IP-First Integration).

SSoT-DEC-001: WorkflowExecution (DB) as SSoT
SSoT-DEC-003: run-token full integration

Endpoints:
- POST /workflow/plan: 워크플로우 계획 + DB 실행 레코드 생성
- POST /workflow/session/{id}/start: run-token 예약 + 실행 시작
- POST /workflow/session/{id}/advance: 스텝 실행 + run-token 차감
- POST /workflow/session/{id}/execute: 전체 자동 실행
- GET /workflow/session/{id}: 상태 조회
"""
from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_flow_enabled
from app.logging_config import get_logger
from app.models_workflow import WorkflowExecution, WorkflowStatus, NodeStatus
from app.routers.dimension._base import get_byok_key, get_credit_cost, _execute_dimension_tool
from app.schemas.ip_context import IPContext
from app.services.workflow_db_service import WorkflowDBService
from app.services.workflow_planner import (
    match_workflow_template,
    WORKFLOW_TEMPLATES,
    TOOL_METADATA,
    WorkflowPlanResult,
)
from app.services.workflow_run_token import (
    WorkflowRunTokenService,
    get_workflow_run_token_service,
)

logger = get_logger("workflow_router")

router = APIRouter(prefix="/workflow", tags=["workflow"])


# =============================================================================
# Request/Response Models
# =============================================================================

class PlanWorkflowRequest(BaseModel):
    """워크플로우 계획 요청."""
    user_request: str
    preferred_template: Optional[str] = None
    ip_id: Optional[str] = None
    preset_id: Optional[str] = None


class PlanWorkflowResponse(BaseModel):
    """워크플로우 계획 응답."""
    success: bool
    template_id: str
    template_name: str
    template_description: str
    confidence: float
    tools: List[str]
    node_chain: List[Dict[str, Any]]
    connections: List[Dict[str, str]]
    estimated_credits: int
    explanation: str
    session_id: Optional[str] = None


class StartWorkflowRequest(BaseModel):
    """워크플로우 시작 요청."""
    session_id: str
    initial_params: Optional[Dict[str, Any]] = None


class WorkflowStatusResponse(BaseModel):
    """워크플로우 상태 응답."""
    session_id: str
    status: str
    current_step: int
    total_steps: int
    nodes: List[Dict[str, Any]]
    consumed_credits: int
    ip_id: Optional[str] = None
    preset_id: Optional[str] = None


# =============================================================================
# WORKFLOW_TOOL_MAP (SSoT for tool execution)
# =============================================================================

from app.dimension_adapter import DimensionCapsuleId

WORKFLOW_TOOL_MAP: Dict[str, Dict[str, Any]] = {
    "prompt_generator": {
        "capsule_id": DimensionCapsuleId.PROMPT_GENERATE,
        "tool_key": "generate_veo_prompt",
        "default_model": "gemini-3-flash-preview",
        "credit_cost": 10,
    },
    "storyboard": {
        "capsule_id": DimensionCapsuleId.STORYBOARD_CREATE,
        "tool_key": "create_storyboard",
        "default_model": "gemini-3-flash-preview",
        "credit_cost": 10,
    },
    "image_tool": {
        "capsule_id": DimensionCapsuleId.IMAGE_GENERATE,
        "tool_key": "generate_image_prompt",
        "default_model": "gemini-3-flash-preview",
        "credit_cost": 10,
    },
    "reference_analyzer": {
        "capsule_id": DimensionCapsuleId.REFERENCE_ANALYZE,
        "tool_key": "analyze_reference",
        "default_model": "gemini-3-flash-preview",
        "credit_cost": 10,
    },
    "quality_check": {
        "capsule_id": DimensionCapsuleId.QUALITY_CHECK,
        "tool_key": "quality_check",
        "default_model": "gemini-3-flash-preview",
        "credit_cost": 10,
    },
    "aesthetic_direct": {
        "capsule_id": DimensionCapsuleId.AESTHETIC_DIRECT,
        "tool_key": "aesthetic_direct",
        "default_model": "gemini-3-flash-preview",
        "credit_cost": 10,
    },
    "veo_generator": {
        "capsule_id": DimensionCapsuleId.VEO_VIDEO_GENERATE,
        "tool_key": "veo_generate",
        "default_model": "veo-3.1-generate-preview",
        "credit_cost": 5000,
    },
    "veo_generate": {
        "capsule_id": DimensionCapsuleId.VEO_VIDEO_GENERATE,
        "tool_key": "veo_generate",
        "default_model": "veo-3.1-generate-preview",
        "credit_cost": 5000,
    },
}


# =============================================================================
# Helper: Get client fingerprint
# =============================================================================

def _get_fingerprint(request: Request) -> str:
    """클라이언트 fingerprint 생성."""
    from app.services.run_token_service import FingerprintGenerator
    forwarded = request.headers.get("x-forwarded-for", "")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    return FingerprintGenerator.generate(
        user_agent=request.headers.get("user-agent", ""),
        client_ip=client_ip,
        accept_language=request.headers.get("accept-language", ""),
    )


def _get_client_ip(request: Request) -> str:
    """클라이언트 IP 추출."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# =============================================================================
# Helper: Output Propagation (노드 간 데이터 전달)
# =============================================================================

def _propagate_outputs(
    dag_snapshot: dict,
    completed_outputs: Dict[str, Dict[str, Any]],
    next_node_id: str,
) -> Dict[str, Any]:
    """완료된 노드들의 출력을 다음 노드 입력으로 전파.

    Args:
        dag_snapshot: DAG 스냅샷 (connections 포함)
        completed_outputs: {node_id: output} 맵
        next_node_id: 다음 노드 ID

    Returns:
        다음 노드의 입력 딕셔너리
    """
    connections = dag_snapshot.get("connections", [])
    nodes = dag_snapshot.get("nodes", [])
    inputs = {}

    # 노드 기본 inputs 가져오기
    for node in nodes:
        if node.get("id") == next_node_id:
            inputs = dict(node.get("data", {}).get("inputs", {}))
            break

    # 연결된 출력 전파
    for conn in connections:
        if conn.get("to_node_id") == next_node_id:
            from_node_id = conn.get("from_node_id")
            from_port = conn.get("from_port", "output")
            to_port = conn.get("to_port", "input")

            if from_node_id in completed_outputs:
                output = completed_outputs[from_node_id]
                # 포트 경로로 값 추출
                value = _extract_port_value(output, from_port)
                if value is not None:
                    inputs[to_port] = value

    return inputs


def _extract_port_value(output: Dict[str, Any], port_path: str) -> Any:
    """출력에서 포트 경로에 해당하는 값 추출.

    예: "scenes[0].description" → output["scenes"][0]["description"]
    """
    import re

    current = output
    parts = re.split(r'\.|\[|\]', port_path)
    parts = [p for p in parts if p]

    try:
        for part in parts:
            if part.isdigit():
                current = current[int(part)]
            else:
                current = current[part]
        return current
    except (KeyError, IndexError, TypeError):
        return None


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/plan", response_model=PlanWorkflowResponse)
async def plan_workflow(
    request: PlanWorkflowRequest,
    http_request: Request,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_flow_enabled),
):
    """워크플로우 계획 + DB 실행 레코드 생성.

    run-token은 /start에서 예약됩니다 (여기서는 estimate만).
    """
    # 1. 워크플로우 매칭
    if request.preferred_template and request.preferred_template in WORKFLOW_TEMPLATES:
        from app.services.workflow_planner import build_node_chain, extract_params_from_message
        template = WORKFLOW_TEMPLATES[request.preferred_template]
        plan = WorkflowPlanResult(
            template_id=template.id,
            template=template,
            confidence=1.0,
            suggested_params=extract_params_from_message(request.user_request, template),
            node_chain=build_node_chain(template),
            total_credits=template.estimated_credits,
            explanation=f"Selected workflow: {template.name}",
            explanation_ko=f"선택된 워크플로우: {template.name_ko}",
        )
    else:
        plan = match_workflow_template(request.user_request)

    if not plan:
        raise HTTPException(status_code=400, detail="워크플로우를 계획할 수 없습니다.")

    # 2. DB 실행 레코드 생성 (SSoT)
    session_id = None
    if user:
        user_id = user.get("id") or user.get("sub") or "anonymous"
        db_service = WorkflowDBService(db)

        # IP Context 처리
        ip_id = uuid.UUID(request.ip_id) if request.ip_id else None
        preset_id = uuid.UUID(request.preset_id) if request.preset_id else None

        execution = await db_service.create_from_plan(
            plan=plan,
            user_id=user_id,
            original_request=request.user_request,
            ip_id=ip_id,
            preset_id=preset_id,
        )
        session_id = str(execution.id)

        await db.commit()

        logger.info(f"[Workflow] Plan created | session={session_id} | template={plan.template_id}")

    return PlanWorkflowResponse(
        success=True,
        template_id=plan.template_id,
        template_name=plan.template.name_ko,
        template_description=plan.template.description_ko,
        confidence=plan.confidence,
        tools=plan.template.tools,
        node_chain=plan.node_chain,
        connections=plan.template.connections,
        estimated_credits=plan.total_credits,
        explanation=plan.explanation_ko,
        session_id=session_id,
    )


@router.get("/templates")
async def list_workflow_templates(
    _: None = Depends(require_flow_enabled),
):
    """사용 가능한 워크플로우 템플릿 목록."""
    return {
        "templates": [
            {
                "id": t.id,
                "name": t.name_ko,
                "description": t.description_ko,
                "tools": t.tools,
                "estimated_credits": t.estimated_credits,
            }
            for t in WORKFLOW_TEMPLATES.values()
        ]
    }


@router.get("/tools")
async def list_available_tools(
    _: None = Depends(require_flow_enabled),
):
    """사용 가능한 도구(차원문) 목록."""
    return {
        "tools": [
            {
                "id": tool_id,
                "display_name": tool["display_name_ko"],
                "icon": tool["icon"],
                "color": tool["color"],
                "input_ports": tool["input_ports"],
                "output_ports": tool["output_ports"],
            }
            for tool_id, tool in TOOL_METADATA.items()
        ]
    }


@router.get("/session/{session_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    session_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_flow_enabled),
):
    """워크플로우 세션 상태 조회 (DB SSoT)."""
    db_service = WorkflowDBService(db)
    execution = await db_service.get_execution_by_session_id(session_id)

    if not execution:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    # BOLA: Owner verification
    user_id = user.get("id") or user.get("sub")
    if execution.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    node_results = await db_service.get_node_results(execution.id)
    response = db_service.to_session_response(execution, node_results)

    return WorkflowStatusResponse(**response)


@router.post("/session/{session_id}/start")
async def start_workflow(
    session_id: str,
    request: StartWorkflowRequest,
    http_request: Request,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_flow_enabled),
):
    """워크플로우 시작: run-token 예약 + 초기 파라미터 주입.

    SSoT-DEC-003: run-token reserve
    """
    db_service = WorkflowDBService(db)
    execution = await db_service.get_execution_by_session_id(session_id)

    if not execution:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    user_id = user.get("id") or user.get("sub")
    if execution.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    if execution.status != WorkflowStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"이미 시작된 워크플로우입니다. (status={execution.status})")

    # 1. run-token 예약
    run_token_service = get_workflow_run_token_service()
    fingerprint = _get_fingerprint(http_request)

    success, token_info, error = await run_token_service.reserve_for_workflow(
        user_id=user_id,
        execution_id=execution.id,
        estimated_credits=execution.estimated_credits,
        fingerprint=fingerprint,
    )

    if not success:
        raise HTTPException(
            status_code=402,
            detail={"code": "CREDIT_RESERVE_FAILED", "message": error},
        )

    # 2. run_token_id 저장
    execution.run_token_id = token_info.run_id

    # 3. 초기 파라미터 병합
    if request.initial_params:
        merged_inputs = {**execution.initial_inputs, **request.initial_params}
        execution.initial_inputs = merged_inputs

    # 4. 실행 시작
    await db_service.start_execution(execution.id, request.initial_params)
    await db.commit()

    logger.info(f"[Workflow] Started | session={session_id} | run_id={token_info.run_id}")

    return {
        "success": True,
        "session_id": session_id,
        "status": WorkflowStatus.RUNNING.value,
        "run_token_id": token_info.run_id,
        "credits_reserved": token_info.credits_reserved,
    }


@router.post("/session/{session_id}/advance")
async def advance_workflow_step(
    session_id: str,
    http_request: Request,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    byok_key: Optional[str] = Depends(get_byok_key),
    _: None = Depends(require_flow_enabled),
):
    """워크플로우 현재 단계 실행 + run-token 차감.

    SSoT-DEC-003: run-token deduct per step
    """
    start_time = time.monotonic()

    db_service = WorkflowDBService(db)
    execution = await db_service.get_execution_by_session_id(session_id)

    if not execution:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    user_id = user.get("id") or user.get("sub")
    if execution.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    # 상태 검증
    if execution.status == WorkflowStatus.COMPLETED.value:
        return {
            "success": True,
            "message": "워크플로우가 이미 완료되었습니다.",
            "current_step": db_service.get_current_step_index(execution),
            "status": "completed",
        }

    if execution.status == WorkflowStatus.FAILED.value:
        raise HTTPException(status_code=400, detail="워크플로우가 실패 상태입니다.")

    if execution.status == WorkflowStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="워크플로우가 시작되지 않았습니다. /start를 먼저 호출하세요.")

    # 다음 노드 가져오기
    next_node = db_service.get_next_node(execution)
    if not next_node:
        # 모든 노드 완료
        await db_service.complete_execution(execution.id)

        # Finalize run-token (refund unused credits)
        if execution.run_token_id:
            advance_run_token_service = get_workflow_run_token_service()
            await advance_run_token_service.finalize_workflow(
                run_id=execution.run_token_id,
                success=True,
            )

        await db.commit()
        return {
            "success": True,
            "message": "모든 단계가 완료되었습니다.",
            "status": "completed",
        }

    node_id = next_node.get("id")
    tool_id = next_node.get("tool_id", node_id)

    # 도구 매핑 조회
    spec = WORKFLOW_TOOL_MAP.get(tool_id)
    if not spec:
        await db_service.record_node_failure(
            execution_id=execution.id,
            node_id=node_id,
            tool_id=tool_id,
            inputs={},
            error_message=f"Unknown tool_id: {tool_id}",
        )
        await db.commit()
        raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_id}")

    # 현재 노드 설정
    await db_service.update_current_node(execution.id, node_id)

    # 이전 노드 출력 수집
    node_results = await db_service.get_node_results(execution.id)
    completed_outputs = {nr.node_id: nr.outputs for nr in node_results}

    # 입력 전파
    inputs = _propagate_outputs(
        dag_snapshot=execution.dag_snapshot,
        completed_outputs=completed_outputs,
        next_node_id=node_id,
    )

    # 초기 입력 병합
    inputs = {**execution.initial_inputs, **inputs}

    step_credits = spec.get("credit_cost", 10)

    # run-token 차감 (byok가 아닌 경우)
    skip_credit_deduction = bool(byok_key)
    if not byok_key and execution.run_token_id:
        run_token_service = get_workflow_run_token_service()
        client_ip = _get_client_ip(http_request)

        deduct_success, remaining, error = await run_token_service.deduct_for_step(
            run_id=execution.run_token_id,
            step_credits=step_credits,
            step_id=node_id,
            client_ip=client_ip,
        )

        if not deduct_success:
            await db_service.record_node_failure(
                execution_id=execution.id,
                node_id=node_id,
                tool_id=tool_id,
                inputs=inputs,
                error_message=f"Credit deduction failed: {error}",
            )
            await db.commit()
            raise HTTPException(status_code=402, detail={"code": "CREDIT_DEDUCT_FAILED", "message": error})

        skip_credit_deduction = True  # run-token이 차감했으므로 _execute_dimension_tool에서 스킵

    # 도구 실행
    try:
        result = await _execute_dimension_tool(
            capsule_id=spec["capsule_id"],
            tool_key=spec["tool_key"],
            inputs=inputs,
            model=spec["default_model"],
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={"tool_id": tool_id, "session_id": session_id},
            skip_credit_deduction=skip_credit_deduction,
        )
    except Exception as e:
        latency_ms = int((time.monotonic() - start_time) * 1000)
        error_msg = str(e)

        await db_service.record_node_failure(
            execution_id=execution.id,
            node_id=node_id,
            tool_id=tool_id,
            inputs=inputs,
            error_message=error_msg,
        )
        await db.commit()

        logger.error(f"[Workflow] Step failed | session={session_id} | node={node_id} | error={error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

    latency_ms = int((time.monotonic() - start_time) * 1000)

    if result.success:
        # 성공: 노드 결과 기록
        await db_service.record_node_result(
            execution_id=execution.id,
            node_id=node_id,
            tool_id=tool_id,
            inputs=inputs,
            outputs=result.output,
            credits_used=step_credits if not byok_key else 0,
            latency_ms=latency_ms,
        )

        # Refresh execution to get updated completed_nodes
        execution = await db_service.get_execution(execution.id)

        # 다음 노드 확인
        next_next = db_service.get_next_node(execution)
        if not next_next:
            await db_service.complete_execution(execution.id)

            # Finalize run-token (refund unused credits)
            if execution.run_token_id:
                await run_token_service.finalize_workflow(
                    run_id=execution.run_token_id,
                    success=True,
                )

        await db.commit()

        logger.info(f"[Workflow] Step completed | session={session_id} | node={node_id}")

        return {
            "success": True,
            "node_id": node_id,
            "tool_id": tool_id,
            "output": result.output,
            "credits_used": step_credits if not byok_key else 0,
            "latency_ms": latency_ms,
            "current_step": db_service.get_current_step_index(execution),
            "total_steps": db_service.get_total_steps(execution),
            "status": execution.status,
        }
    else:
        await db_service.record_node_failure(
            execution_id=execution.id,
            node_id=node_id,
            tool_id=tool_id,
            inputs=inputs,
            error_message=result.error or "Unknown error",
        )

        # Finalize run-token on failure (refund all unused credits)
        if execution.run_token_id:
            await run_token_service.finalize_workflow(
                run_id=execution.run_token_id,
                success=False,
            )

        await db.commit()

        return {
            "success": False,
            "node_id": node_id,
            "tool_id": tool_id,
            "error": result.error,
            "latency_ms": latency_ms,
            "status": WorkflowStatus.FAILED.value,
        }


@router.post("/session/{session_id}/execute")
async def execute_workflow_all(
    session_id: str,
    http_request: Request,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    byok_key: Optional[str] = Depends(get_byok_key),
    _: None = Depends(require_flow_enabled),
):
    """워크플로우 전체 자동 실행.

    모든 스텝을 순차 실행하고 결과 요약 반환.
    """
    db_service = WorkflowDBService(db)
    execution = await db_service.get_execution_by_session_id(session_id)

    if not execution:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    user_id = user.get("id") or user.get("sub")
    if execution.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    results = []
    total_credits = 0
    run_token_service = get_workflow_run_token_service()
    client_ip = _get_client_ip(http_request)

    # 시작되지 않았으면 시작
    if execution.status == WorkflowStatus.PENDING.value:
        fingerprint = _get_fingerprint(http_request)
        success, token_info, error = await run_token_service.reserve_for_workflow(
            user_id=user_id,
            execution_id=execution.id,
            estimated_credits=execution.estimated_credits,
            fingerprint=fingerprint,
        )
        if not success:
            raise HTTPException(status_code=402, detail={"code": "CREDIT_RESERVE_FAILED", "message": error})

        execution.run_token_id = token_info.run_id
        await db_service.start_execution(execution.id)
        await db.commit()
        await db.refresh(execution)

    logger.info(f"[Workflow] Auto-execute started | session={session_id}")

    while True:
        # 상태 갱신
        execution = await db_service.get_execution(execution.id)

        if execution.status in (WorkflowStatus.COMPLETED.value, WorkflowStatus.FAILED.value):
            break

        next_node = db_service.get_next_node(execution)
        if not next_node:
            await db_service.complete_execution(execution.id)
            await db.commit()
            break

        node_id = next_node.get("id")
        tool_id = next_node.get("tool_id", node_id)
        spec = WORKFLOW_TOOL_MAP.get(tool_id)

        if not spec:
            await db_service.record_node_failure(
                execution_id=execution.id,
                node_id=node_id,
                tool_id=tool_id,
                inputs={},
                error_message=f"Unknown tool_id: {tool_id}",
            )
            await db.commit()
            break

        await db_service.update_current_node(execution.id, node_id)

        # 입력 전파
        node_results = await db_service.get_node_results(execution.id)
        completed_outputs = {nr.node_id: nr.outputs for nr in node_results}
        inputs = _propagate_outputs(execution.dag_snapshot, completed_outputs, node_id)
        inputs = {**execution.initial_inputs, **inputs}

        step_credits = spec.get("credit_cost", 10)
        skip_credit_deduction = bool(byok_key)

        # run-token 차감
        if not byok_key and execution.run_token_id:
            deduct_success, remaining, error = await run_token_service.deduct_for_step(
                run_id=execution.run_token_id,
                step_credits=step_credits,
                step_id=node_id,
                client_ip=client_ip,
            )
            if not deduct_success:
                await db_service.record_node_failure(
                    execution_id=execution.id,
                    node_id=node_id,
                    tool_id=tool_id,
                    inputs=inputs,
                    error_message=f"Credit deduction failed: {error}",
                )
                await db.commit()
                break
            skip_credit_deduction = True

        start_time = time.monotonic()

        try:
            result = await _execute_dimension_tool(
                capsule_id=spec["capsule_id"],
                tool_key=spec["tool_key"],
                inputs=inputs,
                model=spec["default_model"],
                user=user,
                byok_key=byok_key,
                db=db,
                inputs_summary={"tool_id": tool_id, "session_id": session_id},
                skip_credit_deduction=skip_credit_deduction,
            )
        except Exception as e:
            await db_service.record_node_failure(
                execution_id=execution.id,
                node_id=node_id,
                tool_id=tool_id,
                inputs=inputs,
                error_message=str(e),
            )
            await db.commit()
            break

        latency_ms = int((time.monotonic() - start_time) * 1000)

        if result.success:
            await db_service.record_node_result(
                execution_id=execution.id,
                node_id=node_id,
                tool_id=tool_id,
                inputs=inputs,
                outputs=result.output,
                credits_used=step_credits if not byok_key else 0,
                latency_ms=latency_ms,
            )
            results.append({"node_id": node_id, "output": result.output})
            total_credits += step_credits if not byok_key else 0
            await db.commit()
        else:
            await db_service.record_node_failure(
                execution_id=execution.id,
                node_id=node_id,
                tool_id=tool_id,
                inputs=inputs,
                error_message=result.error or "Unknown error",
            )
            await db.commit()
            break

    # 환불 (미사용 크레딧)
    if execution.run_token_id:
        await run_token_service.finalize_workflow(
            run_id=execution.run_token_id,
            success=(execution.status == WorkflowStatus.COMPLETED.value),
        )

    execution = await db_service.get_execution(execution.id)

    return {
        "session_id": session_id,
        "status": execution.status,
        "steps_executed": len(results),
        "total_steps": db_service.get_total_steps(execution),
        "total_credits": total_credits,
        "outputs": [r["output"] for r in results],
    }


@router.get("/user/sessions")
async def get_user_workflow_sessions(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_flow_enabled),
):
    """현재 사용자의 워크플로우 세션 목록 (DB SSoT)."""
    user_id = user.get("id") or user.get("sub") or "anonymous"
    db_service = WorkflowDBService(db)
    executions = await db_service.get_user_executions(user_id)

    return {
        "sessions": [
            {
                "id": str(e.id),
                "template_name": e.dag_snapshot.get("template_name", ""),
                "status": e.status,
                "current_step": db_service.get_current_step_index(e),
                "total_steps": db_service.get_total_steps(e),
                "consumed_credits": e.actual_credits or 0,
                "created_at": e.created_at.isoformat(),
            }
            for e in executions
        ]
    }
