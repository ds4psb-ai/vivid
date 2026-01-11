"""P2: Workflow Step Executor Service.

실제 Dimension 도구 실행을 담당하는 서비스 레이어.
워크플로우 라우터에서 호출하여 단일 책임 원칙 유지.

Key Features:
- WORKFLOW_TOOL_MAP: tool_id → capsule_id/tool_key 매핑 (SSoT)
- Input Adapters: 우선순위 기반 입력 변환 (user > node > session > defaults)
- Idempotency: node.status 체크로 중복 실행 방지
- Credits: _execute_dimension_tool 재사용 + consumed_credits 집계
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.dimension_adapter import DimensionCapsuleId
from app.logging_config import get_logger
from app.routers.dimension._base import _execute_dimension_tool, get_credit_cost
from app.schemas.workflow_session import (
    WorkflowSession,
    WorkflowStatus,
    workflow_session_manager,
)

logger = get_logger("workflow_executor")


# =============================================================================
# WorkflowStepResult Dataclass
# =============================================================================

@dataclass
class WorkflowStepResult:
    """단일 워크플로우 스텝 실행 결과."""
    
    success: bool
    node_id: str
    tool_id: str
    capsule_id: Optional[DimensionCapsuleId]
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    credits_used: int = 0
    latency_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "node_id": self.node_id,
            "tool_id": self.tool_id,
            "capsule_id": self.capsule_id.value if self.capsule_id else None,
            "output": self.output,
            "error": self.error,
            "credits_used": self.credits_used,
            "latency_ms": self.latency_ms,
        }


# =============================================================================
# WORKFLOW_TOOL_MAP (SSoT: tool_id → Dimension Capsule)
# =============================================================================

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
    # VEO (optional P2 extension)
    "veo_generator": {
        "capsule_id": DimensionCapsuleId.VEO_VIDEO_GENERATE,
        "tool_key": "veo_generate",
        "default_model": "veo-3.1-generate-preview",
        "credit_cost": 5000,  # VEO is expensive
    },
}


# =============================================================================
# Input Adapters (Priority: user > node > session.extracted_params > defaults)
# =============================================================================

def _build_prompt_inputs(
    node_inputs: Dict[str, Any],
    session: WorkflowSession,
) -> Dict[str, Any]:
    """1D Prompt Generator 입력 변환."""
    params = session.extracted_params
    return {
        "topic": node_inputs.get("topic") or params.get("topic", ""),
        "style": node_inputs.get("style") or params.get("style", "cinematic"),
        "mood": node_inputs.get("mood") or params.get("mood", "dramatic"),
        "duration": node_inputs.get("duration") or params.get("duration", "8 seconds"),
        "language": node_inputs.get("language") or params.get("language", "ko"),
    }


def _build_storyboard_inputs(
    node_inputs: Dict[str, Any],
    session: WorkflowSession,
) -> Dict[str, Any]:
    """2D Storyboard 입력 변환.
    
    Note: API requires 'concept' (required) + 'prompt' (optional).
    Old 'script' key is mapped to 'prompt' for backwards compatibility.
    """
    params = session.extracted_params
    
    # Priority: node.concept > node.prompt > node.script > session.topic
    concept = (
        node_inputs.get("concept") or 
        node_inputs.get("prompt") or 
        node_inputs.get("script") or 
        params.get("topic", "")
    )
    
    return {
        "concept": concept,
        "prompt": node_inputs.get("prompt") or node_inputs.get("script"),
        "scene_count": int(node_inputs.get("scene_count") or params.get("scene_count", 6)),
        "language": node_inputs.get("language") or params.get("language", "ko"),
    }


def _build_image_inputs(
    node_inputs: Dict[str, Any],
    session: WorkflowSession,
) -> Dict[str, Any]:
    """3D Image Generator 입력 변환."""
    params = session.extracted_params
    return {
        "description": (
            node_inputs.get("description") or 
            node_inputs.get("prompt") or 
            params.get("description", "")
        ),
        "style": node_inputs.get("style") or params.get("style", "cinematic"),
        "aspect_ratio": node_inputs.get("aspect_ratio", "16:9"),
    }


def _build_reference_inputs(
    node_inputs: Dict[str, Any],
    session: WorkflowSession,
) -> Dict[str, Any]:
    """4D Reference Analyzer 입력 변환.
    
    Note: API uses 'video_description' not 'video_url'.
    """
    params = session.extracted_params
    return {
        "video_description": (
            node_inputs.get("video_description") or 
            node_inputs.get("video_url") or  # backwards compat
            params.get("video_description", "")
        ),
        "focus_areas": node_inputs.get("focus_areas", ["composition", "lighting", "color"]),
        "analysis_depth": node_inputs.get("analysis_depth", "standard"),
        "output_format": node_inputs.get("output_format", "structured"),
    }


def _build_veo_inputs(
    node_inputs: Dict[str, Any],
    session: WorkflowSession,
) -> Dict[str, Any]:
    """VEO Video Generator 입력 변환."""
    params = session.extracted_params
    return {
        "prompt": node_inputs.get("prompt") or params.get("prompt", ""),
        "negative_prompt": node_inputs.get("negative_prompt", ""),
        "aspect_ratio": node_inputs.get("aspect_ratio", "16:9"),
        "duration": int(node_inputs.get("duration", 6)),
        "style": node_inputs.get("style") or params.get("style", "cinematic"),
    }


# Input adapter registry
INPUT_ADAPTERS: Dict[str, callable] = {
    "prompt_generator": _build_prompt_inputs,
    "storyboard": _build_storyboard_inputs,
    "image_tool": _build_image_inputs,
    "reference_analyzer": _build_reference_inputs,
    "veo_generator": _build_veo_inputs,
}


# =============================================================================
# Core Executor Functions
# =============================================================================

async def execute_step(
    session_id: str,
    user: dict,
    db: AsyncSession,
    byok_key: Optional[str] = None,
) -> WorkflowStepResult:
    """단일 워크플로우 스텝 실행.
    
    Args:
        session_id: 워크플로우 세션 ID
        user: 인증된 사용자 정보 (id, email 등)
        db: 비동기 DB 세션
        byok_key: BYOK API 키 (있으면 크레딧 차감 안 함)
        
    Returns:
        WorkflowStepResult with success/error info
        
    Raises:
        ValueError: 세션 없음 또는 잘못된 상태
    """
    start_time = time.monotonic()
    
    # 1. 세션 조회
    session = workflow_session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Workflow session not found: {session_id}")
    
    # 2. 상태 검증
    if session.status == WorkflowStatus.COMPLETED:
        raise ValueError("Workflow already completed")
    if session.status == WorkflowStatus.FAILED:
        raise ValueError("Workflow has failed, cannot continue")
    
    # 3. 현재 노드 가져오기
    if session.current_step >= len(session.nodes):
        raise ValueError("No more steps to execute")
    
    node = session.nodes[session.current_step]
    
    # 4. Idempotency Guard: 이미 완료된 노드 재실행 방지
    if node.status == "completed":
        logger.warning(f"Node {node.node_id} already completed, skipping")
        return WorkflowStepResult(
            success=True,
            node_id=node.node_id,
            tool_id=node.tool_id,
            capsule_id=None,
            output=node.output or {},
            error=None,
            credits_used=0,
            latency_ms=0,
        )
    
    if node.status == "executing":
        logger.warning(f"Node {node.node_id} already executing (duplicate call?)")
        raise ValueError(f"Node {node.node_id} is already executing")
    
    # 5. 도구 매핑 조회
    spec = WORKFLOW_TOOL_MAP.get(node.tool_id)
    if not spec:
        node.status = "failed"
        node.error = f"Unknown tool_id: {node.tool_id}"
        session.status = WorkflowStatus.FAILED
        workflow_session_manager.update_session(session)
        return WorkflowStepResult(
            success=False,
            node_id=node.node_id,
            tool_id=node.tool_id,
            capsule_id=None,
            error=node.error,
        )
    
    # 6. 상태 업데이트: executing
    node.status = "executing"
    session.status = WorkflowStatus.EXECUTING
    workflow_session_manager.update_session(session)
    
    # 7. 입력 변환 (adapter 사용)
    adapter = INPUT_ADAPTERS.get(node.tool_id)
    if adapter:
        inputs = adapter(node.inputs, session)
    else:
        inputs = node.inputs
    
    logger.info(
        f"Executing step {session.current_step + 1}/{session.total_steps}: "
        f"{node.tool_id} with inputs: {list(inputs.keys())}"
    )
    
    # 8. 실제 Dimension 도구 실행
    try:
        result = await _execute_dimension_tool(
            capsule_id=spec["capsule_id"],
            tool_key=spec["tool_key"],
            inputs=inputs,
            model=spec["default_model"],
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={"tool_id": node.tool_id, "session_id": session_id},
        )
    except Exception as e:
        # 실행 실패
        latency_ms = int((time.monotonic() - start_time) * 1000)
        error_msg = str(e)
        
        # 402 INSUFFICIENT_CREDITS 처리
        if "402" in error_msg or "insufficient" in error_msg.lower():
            error_msg = "크레딧 부족 - 충전이 필요합니다"
        
        node.status = "failed"
        node.error = error_msg
        session.status = WorkflowStatus.FAILED
        workflow_session_manager.update_session(session)
        
        logger.error(f"Step execution failed: {error_msg}")
        
        return WorkflowStepResult(
            success=False,
            node_id=node.node_id,
            tool_id=node.tool_id,
            capsule_id=spec["capsule_id"],
            error=error_msg,
            latency_ms=latency_ms,
        )
    
    # 9. 결과 처리
    latency_ms = int((time.monotonic() - start_time) * 1000)
    
    if result.success:
        # 성공: 노드 완료 + 출력 전파
        if result.metrics:
            credits_used = result.metrics.credits_charged
        else:
            # Fallback (should not happen on success)
            credits_used = 0
            logger.warning(f"Step {node.tool_id} succeeded but missing metrics")
        
        workflow_session_manager.mark_node_completed(
            session_id=session.id,
            node_id=node.node_id,
            output=result.output,
        )
        
        # consumed_credits 업데이트
        session = workflow_session_manager.get_session(session_id)  # refresh
        session.consumed_credits += credits_used
        
        # 다음 스텝으로 진행
        workflow_session_manager.advance_step(session_id)
        
        logger.info(
            f"Step completed: {node.tool_id}, "
            f"credits={credits_used}, latency={latency_ms}ms"
        )
        
        return WorkflowStepResult(
            success=True,
            node_id=node.node_id,
            tool_id=node.tool_id,
            capsule_id=spec["capsule_id"],
            output=result.output,
            credits_used=credits_used,
            latency_ms=latency_ms,
        )
    else:
        # API 반환은 성공이지만 success: false
        node.status = "failed"
        node.error = result.error or "Unknown error"
        session.status = WorkflowStatus.FAILED
        workflow_session_manager.update_session(session)
        
        return WorkflowStepResult(
            success=False,
            node_id=node.node_id,
            tool_id=node.tool_id,
            capsule_id=spec["capsule_id"],
            error=node.error,
            latency_ms=latency_ms,
        )


async def execute_all_steps(
    session_id: str,
    user: dict,
    db: AsyncSession,
    byok_key: Optional[str] = None,
) -> Dict[str, Any]:
    """전체 워크플로우 자동 실행 (1D → 2D → 3D → ...).
    
    모든 스텝을 순차적으로 실행하고 결과 요약을 반환.
    중간 실패 시 이전 결과는 보존됨.
    
    Args:
        session_id: 워크플로우 세션 ID
        user: 인증된 사용자 정보
        db: 비동기 DB 세션
        byok_key: BYOK API 키
        
    Returns:
        실행 요약 (steps_executed, total_credits, outputs, status)
    """
    results: list[WorkflowStepResult] = []
    total_credits = 0
    
    session = workflow_session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Workflow session not found: {session_id}")
    
    logger.info(f"Starting auto-execute for session {session_id} ({session.total_steps} steps)")
    
    while True:
        session = workflow_session_manager.get_session(session_id)
        
        # 완료 또는 실패 시 중단
        if session.status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED):
            break
        
        # 스텝 실행
        try:
            result = await execute_step(session_id, user, db, byok_key)
            results.append(result)
            total_credits += result.credits_used
            
            if not result.success:
                logger.error(f"Auto-execute stopped at step {len(results)}: {result.error}")
                break
                
        except ValueError as e:
            logger.error(f"Auto-execute error: {e}")
            break
    
    # 최종 세션 상태
    session = workflow_session_manager.get_session(session_id)
    
    return {
        "session_id": session_id,
        "status": session.status.value if isinstance(session.status, WorkflowStatus) else session.status,
        "steps_executed": len(results),
        "total_steps": session.total_steps,
        "total_credits": total_credits,
        "outputs": [r.output for r in results if r.success],
        "errors": [r.error for r in results if not r.success],
    }


def seed_first_node_inputs(
    session_id: str,
    initial_params: Dict[str, Any],
) -> bool:
    """첫 번째 노드에 초기 입력값 주입.
    
    워크플로우 생성 후, 첫 노드 실행 전에 호출해야 함.
    extracted_params는 세션 전체에 적용되고,
    이 함수는 첫 노드의 inputs에 직접 값을 설정함.
    
    Args:
        session_id: 워크플로우 세션 ID
        initial_params: 주입할 초기 파라미터 (topic, style 등)
        
    Returns:
        성공 여부
    """
    session = workflow_session_manager.get_session(session_id)
    if not session or len(session.nodes) == 0:
        return False
    
    first_node = session.nodes[0]
    
    # 기존 inputs에 초기 파라미터 병합 (user > initial)
    merged = {**initial_params, **first_node.inputs}
    first_node.inputs = merged
    
    # extracted_params도 업데이트 (초기 파라미터가 우선)
    session.extracted_params = {**session.extracted_params, **initial_params}
    
    workflow_session_manager.update_session(session)
    
    logger.info(f"Seeded first node with params: {list(initial_params.keys())}")
    return True
