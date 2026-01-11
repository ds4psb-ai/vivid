"""
Workflow API Router

Endpoints for workflow planning and session management.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.workflow_planner import (
    match_workflow_template,
    WORKFLOW_TEMPLATES,
    TOOL_METADATA,
    WorkflowPlanResult,
)
from app.schemas.workflow_session import (
    WorkflowSession,
    WorkflowStatus,
    workflow_session_manager,
)
from app.dependencies import get_current_user_optional, get_current_user, get_db
from app.routers.dimension._base import get_byok_key



router = APIRouter(prefix="/workflow", tags=["workflow"])


# =============================================================================
# Request/Response Models
# =============================================================================

class PlanWorkflowRequest(BaseModel):
    """워크플로우 계획 요청"""
    user_request: str
    preferred_template: Optional[str] = None


class PlanWorkflowResponse(BaseModel):
    """워크플로우 계획 응답"""
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
    """워크플로우 시작 요청"""
    session_id: str
    initial_params: Optional[Dict[str, Any]] = None


class WorkflowStatusResponse(BaseModel):
    """워크플로우 상태 응답"""
    session_id: str
    status: str
    current_step: int
    total_steps: int
    nodes: List[Dict[str, Any]]
    consumed_credits: int


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/plan", response_model=PlanWorkflowResponse)
async def plan_workflow(
    request: PlanWorkflowRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    사용자 요청을 분석하고 워크플로우를 계획합니다.
    
    - 의도에 맞는 템플릿 매칭
    - 연결된 노드 체인 생성
    - (로그인 시) 세션 생성
    """
    
    # 1. 워크플로우 매칭
    if request.preferred_template and request.preferred_template in WORKFLOW_TEMPLATES:
        # 사용자가 템플릿을 직접 지정한 경우
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
        # 자동 매칭
        plan = match_workflow_template(request.user_request)
    
    if not plan:
        raise HTTPException(status_code=400, detail="워크플로우를 계획할 수 없습니다.")
    
    # 2. 세션 생성 (로그인 사용자만)
    session_id = None
    if user:
        session = workflow_session_manager.create_session(
            user_id=user.get("id", user.get("sub", "anonymous")),
            template_id=plan.template_id,
            template_name=plan.template.name_ko,
            template_description=plan.template.description_ko,
            nodes=plan.node_chain,
            connections=plan.template.connections,
            original_request=request.user_request,
            extracted_params=plan.suggested_params,
            estimated_credits=plan.total_credits,
        )
        session_id = session.id
    
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
async def list_workflow_templates():
    """사용 가능한 워크플로우 템플릿 목록"""
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
async def list_available_tools():
    """사용 가능한 도구(차원문) 목록"""
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
    user: dict = Depends(get_current_user),  # P0 BOLA: Auth required
):
    """워크플로우 세션 상태 조회"""
    session = workflow_session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    # P0 BOLA: Owner verification
    user_id = user.get("id") or user.get("sub")
    if session.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    return WorkflowStatusResponse(
        session_id=session.id,
        status=session.status.value if isinstance(session.status, WorkflowStatus) else session.status,
        current_step=session.current_step,
        total_steps=session.total_steps,
        nodes=[
            {
                "node_id": n.node_id,
                "tool_id": n.tool_id,
                "order": n.order,
                "status": n.status,
                "inputs": n.inputs,
                "output": n.output,
            }
            for n in session.nodes
        ],
        consumed_credits=session.consumed_credits,
    )


@router.post("/session/{session_id}/advance")
async def advance_workflow_step(
    session_id: str,
    user: dict = Depends(get_current_user),  # P0 BOLA: Auth required
    db: AsyncSession = Depends(get_db),
    byok_key: Optional[str] = Depends(get_byok_key),
):
    """워크플로우 현재 단계 실행 후 다음 단계로 진행.
    
    P2: 실제 Dimension 도구 실행 + 크레딧 차감.
    """
    from app.services.workflow_executor import execute_step
    
    # P0 BOLA: Check ownership first
    existing_session = workflow_session_manager.get_session(session_id)
    if not existing_session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    user_id = user.get("id") or user.get("sub")
    if existing_session.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    # 세션 상태 검증
    if existing_session.status == WorkflowStatus.COMPLETED:
        return {
            "success": True,
            "message": "워크플로우가 이미 완료되었습니다.",
            "current_step": existing_session.current_step,
            "status": "completed",
        }
    
    if existing_session.status == WorkflowStatus.FAILED:
        raise HTTPException(status_code=400, detail="워크플로우가 실패 상태입니다. 새 세션을 시작하세요.")
    
    # P2: 실제 도구 실행
    try:
        result = await execute_step(
            session_id=session_id,
            user=user,
            db=db,
            byok_key=byok_key,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # 업데이트된 세션 조회
    session = workflow_session_manager.get_session(session_id)
    
    return {
        "success": result.success,
        "node_id": result.node_id,
        "tool_id": result.tool_id,
        "output": result.output if result.success else None,
        "error": result.error,
        "credits_used": result.credits_used,
        "latency_ms": result.latency_ms,
        "current_step": session.current_step,
        "total_steps": session.total_steps,
        "status": session.status.value if isinstance(session.status, WorkflowStatus) else session.status,
    }


@router.post("/session/{session_id}/execute")
async def execute_workflow_all(
    session_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    byok_key: Optional[str] = Depends(get_byok_key),
):
    """워크플로우 전체 자동 실행 (1D → 2D → 3D → ...).
    
    모든 남은 스텝을 순차 실행. 중간 실패 시 이전 결과 보존.
    """
    from app.services.workflow_executor import execute_all_steps
    
    # P0 BOLA: Check ownership
    existing_session = workflow_session_manager.get_session(session_id)
    if not existing_session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    user_id = user.get("id") or user.get("sub")
    if existing_session.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    # 실행
    try:
        summary = await execute_all_steps(
            session_id=session_id,
            user=user,
            db=db,
            byok_key=byok_key,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return summary


@router.post("/session/{session_id}/start")
async def start_workflow(
    session_id: str,
    request: StartWorkflowRequest,
    user: dict = Depends(get_current_user),
):
    """워크플로우 시작: 첫 노드에 초기 파라미터 주입.
    
    /plan으로 세션 생성 후, /advance 전에 호출하여 초기값 설정.
    """
    from app.services.workflow_executor import seed_first_node_inputs
    
    # P0 BOLA: Check ownership
    existing_session = workflow_session_manager.get_session(session_id)
    if not existing_session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    user_id = user.get("id") or user.get("sub")
    if existing_session.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    # 초기 파라미터 주입
    if request.initial_params:
        success = seed_first_node_inputs(session_id, request.initial_params)
        if not success:
            raise HTTPException(status_code=400, detail="초기 파라미터 주입 실패")
    
    session = workflow_session_manager.get_session(session_id)
    
    return {
        "success": True,
        "session_id": session_id,
        "status": session.status.value if isinstance(session.status, WorkflowStatus) else session.status,
        "first_node_inputs": session.nodes[0].inputs if session.nodes else {},
    }


@router.get("/user/sessions")
async def get_user_workflow_sessions(
    user: dict = Depends(get_current_user_optional),
):
    """현재 사용자의 워크플로우 세션 목록"""
    if not user:
        return {"sessions": []}
    
    user_id = user.get("id", user.get("sub", "anonymous"))
    sessions = workflow_session_manager.get_user_sessions(user_id)
    
    return {
        "sessions": [
            {
                "id": s.id,
                "template_name": s.workflow_name,
                "status": s.status.value if isinstance(s.status, WorkflowStatus) else s.status,
                "current_step": s.current_step,
                "total_steps": s.total_steps,
                "consumed_credits": s.consumed_credits,
                "created_at": s.created_at.isoformat(),
            }
            for s in sessions
        ]
    }

