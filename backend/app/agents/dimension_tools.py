"""Dimension Tools for VividAgent.

Agent가 사용할 수 있는 Dimension 캡슐 도구들.
Single Source of Truth: DIMENSION_CAPSULES에서 ToolSpec을 동적으로 생성.

사용 가능한 도구:
- generate_veo_prompt: Veo 비디오 프롬프트 생성 (1D)
- create_storyboard: 스토리보드 생성 (2D)
- generate_image_prompt: 이미지 프롬프트 생성 (3D)
- analyze_reference: 레퍼런스 분석 (4D)
- quality_check: 퀄리티 검수기 (QC) - 콘텐츠 품질 평가
- aesthetic_direct: 미학디렉터 (AD) - 스타일 가이드 생성
- persona_analyze: 심연해석기 (AI) - 페르소나 분석
- veo_generate: Veo 3.1 비디오 생성 (VEO)
- story_architect: 시나리오 생성기 (STORY) - 스토리 구조 설계
- sound_crafter: 사운드 크래프터 (SOUND) - 음악/효과음 프롬프트
- reference_decoder: 레퍼런스 해석기 (REF) - 참조 이미지 분석
- visual_realizer: 비주얼 리얼라이저 (VIS) - 이미지 생성
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from app.agents.agent_types import (
    ToolCall,
    ToolContext,
    ToolRegistry,
    ToolResult,
    ToolSpec,
    ToolTaskState,
)
from app.agents.tool_utils import create_emitter, error_result, success_result
from app.agents.evidence_loop import (
    record_tool_start,
    record_tool_success,
    record_tool_failure,
)
from app.fixtures.dimension_capsules import DIMENSION_CAPSULES
from app.logging_config import get_logger

logger = get_logger("dimension_tools")


# =============================================================================
# Tool Name <-> Capsule Key Mapping
# =============================================================================

# Agent 도구 이름과 캡슐 키 간의 매핑
TOOL_TO_CAPSULE: Dict[str, str] = {
    # Original 4 dimensions
    "generate_veo_prompt": "teaching.prompt.generate",
    "create_storyboard": "teaching.storyboard.create",
    "generate_image_prompt": "teaching.image.generate",
    "analyze_reference": "teaching.reference.analyze",
    # Extended Dimension Capsules
    "quality_check": "dimension.quality.check",
    "aesthetic_direct": "dimension.aesthetic.direct",
    "persona_analyze": "dimension.persona.analyze",
    "veo_generate": "veo.video.generate",
    # 4-Stage Workflow Capsules
    "story_architect": "dimension.story.architect",
    "sound_crafter": "dimension.sound.craft",
    # Aliases for 4-Stage Workflow (map to existing capsules)
    "reference_decoder": "teaching.reference.analyze",  # REF → 4D capsule
    "visual_realizer": "teaching.image.generate",  # VIS → 3D capsule
}

CAPSULE_TO_TOOL: Dict[str, str] = {v: k for k, v in TOOL_TO_CAPSULE.items()}

# Tool → Dimension 매핑 (Evidence Loop용)
TOOL_TO_DIMENSION: Dict[str, str] = {
    # Original 4 dimensions
    "generate_veo_prompt": "1D",
    "create_storyboard": "2D",
    "generate_image_prompt": "3D",
    "analyze_reference": "4D",
    # Extended Dimension Capsules
    "quality_check": "QC",
    "aesthetic_direct": "AD",
    "persona_analyze": "AI",
    "veo_generate": "VEO",
    # 4-Stage Workflow Dimensions
    "story_architect": "STORY",
    "sound_crafter": "SOUND",
    "reference_decoder": "REF",
    "visual_realizer": "VIS",
}


def _get_tool_dimension(tool_name: str) -> Optional[str]:
    """도구 이름으로 차원 반환."""
    return TOOL_TO_DIMENSION.get(tool_name)


def get_capsule_by_key(capsule_key: str) -> Optional[Dict[str, Any]]:
    """캡슐 키로 캡슐 정의 조회."""
    for capsule in DIMENSION_CAPSULES:
        if capsule["capsule_key"] == capsule_key:
            return capsule
    return None


def get_credit_cost(capsule_key: str, model: str) -> int:
    """캡슐과 모델에 따른 크레딧 비용 계산.
    
    Single Source of Truth: DIMENSION_CAPSULES에서 credit_costs 조회.
    
    Args:
        capsule_key: 캡슐 식별자 (예: "teaching.prompt.generate")
        model: AI 모델명 (예: "gemini-3-flash-preview")
        
    Returns:
        크레딧 비용 (정수)
    """
    capsule = get_capsule_by_key(capsule_key)
    if not capsule:
        logger.warning(f"Unknown capsule key: {capsule_key}, using default cost 5")
        return 5
    
    credit_costs = capsule.get("credit_costs", {})
    cost = credit_costs.get(model)
    
    if cost is not None:
        return cost
    
    # Fallback to default model cost
    default_cost = credit_costs.get("gemini-3-flash-preview", 5)
    logger.debug(f"Model '{model}' not in credit_costs, using default: {default_cost}")
    return default_cost


# =============================================================================
# ToolSpec Generation from Capsule Definition
# =============================================================================

def _convert_capsule_input_to_json_schema(
    input_name: str,
    input_def: Dict[str, Any],
) -> Dict[str, Any]:
    """캡슐 입력 정의를 JSON Schema 형식으로 변환.
    
    Args:
        input_name: 입력 필드 이름
        input_def: 캡슐에서 정의된 입력 스펙
        
    Returns:
        JSON Schema 호환 딕셔너리
    """
    type_mapping = {
        "string": "string",
        "integer": "integer",
        "number": "number",
        "boolean": "boolean",
        "array": "array",
        "object": "object",
    }
    
    capsule_type = input_def.get("type", "string")
    json_type = type_mapping.get(capsule_type, "string")
    
    schema: Dict[str, Any] = {
        "type": json_type,
        "description": input_def.get("description", input_name),
    }
    
    # Optional default value
    if "default" in input_def:
        schema["default"] = input_def["default"]
    
    # Enum options
    if "options" in input_def:
        schema["enum"] = input_def["options"]
    
    # Array items
    if json_type == "array" and "items" in input_def:
        schema["items"] = {"type": input_def["items"].get("type", "string")}
    
    return schema


def _capsule_to_tool_spec(capsule: Dict[str, Any]) -> ToolSpec:
    """캡슐 정의를 Agent ToolSpec으로 변환.
    
    Args:
        capsule: DIMENSION_CAPSULES의 캡슐 정의
        
    Returns:
        Agent가 사용할 수 있는 ToolSpec
    """
    spec = capsule["spec"]
    capsule_key = capsule["capsule_key"]
    
    # 캡슐 키를 도구 이름으로 변환
    tool_name = CAPSULE_TO_TOOL.get(capsule_key, capsule_key.replace(".", "_"))
    
    # Input properties 생성
    properties: Dict[str, Any] = {}
    required: List[str] = []
    
    for input_name, input_def in spec.get("inputs", {}).items():
        properties[input_name] = _convert_capsule_input_to_json_schema(
            input_name, input_def
        )
        if input_def.get("required", False):
            required.append(input_name)
    
    # Model parameter 추가 (params에서)
    params = spec.get("params", {})
    if "model" in params:
        model_def = params["model"]
        properties["model"] = {
            "type": "string",
            "description": "AI 모델 선택 (비용이 다름)",
            "default": model_def.get("default", "gemini-3-flash-preview"),
        }
        if "options" in model_def:
            properties["model"]["enum"] = model_def["options"]
    
    input_schema = {
        "type": "object",
        "properties": properties,
        "required": required,
    }
    
    # Description에 크레딧 정보 추가
    description = spec.get("description", spec.get("name", tool_name))
    credit_costs = capsule.get("credit_costs", {})
    if credit_costs:
        costs_str = ", ".join(f"{m}: {c}크레딧" for m, c in credit_costs.items())
        description = f"{description} (비용: {costs_str})"
    
    return ToolSpec(
        name=tool_name,
        description=description,
        input_schema=input_schema,
    )


# =============================================================================
# Node Spec Builder (for Canvas Integration)
# =============================================================================

def build_dimension_node_spec(
    capsule: Dict[str, Any],
    inputs: Dict[str, Any],
    output: Dict[str, Any],
    credit_cost: int = 0,
) -> Dict[str, Any]:
    """Teaching 결과를 Canvas 노드 스펙으로 변환.
    
    Agent가 Teaching 도구를 실행한 후, Canvas에 노드로 추가할 수 있는
    스펙을 생성합니다.
    
    Args:
        capsule: 캡슐 정의
        inputs: 실행에 사용된 입력 값
        output: 실행 결과 출력
        credit_cost: 소비된 크레딧
        
    Returns:
        React Flow 노드로 변환 가능한 스펙
    """
    spec = capsule["spec"]
    capsule_key = capsule["capsule_key"]
    
    # 입력/출력 포트 추출
    input_ports = list(spec.get("inputs", {}).keys())
    output_ports = list(spec.get("outputs", {}).keys())
    
    return {
        "id": str(uuid.uuid4()),
        "capsule_id": capsule_key,
        "type": "teaching_capsule",
        "display_name": spec.get("name", capsule_key),
        "version": capsule.get("version", "1.0.0"),
        "position": {"x": 0, "y": 0},  # Canvas에서 자동 배치
        "data": {
            "capsule_key": capsule_key,
            "category": "teaching",
            "input_schema": spec.get("inputs", {}),
            "output_schema": spec.get("outputs", {}),
            "params_schema": spec.get("params", {}),
            "inputs": inputs,
            "locked_inputs": list(inputs.keys()),  # 채팅에서 채운 값 표시
            "output": output,
            "editable": True,
            "credit_cost": credit_cost,
        },
        "input_ports": input_ports,
        "output_ports": output_ports,
        "executed": True,
        "execution_time": None,
    }


# =============================================================================
# Tool Handler
# =============================================================================

async def _dimension_tool_handler(
    context: ToolContext,
    call: ToolCall,
) -> ToolResult:
    """Teaching 캡슐 도구 실행 핸들러.
    
    Agent가 Teaching 도구를 호출하면 이 핸들러가 실행됩니다.
    
    1. 도구 이름으로 캡슐 식별
    2. 입력 검증 및 모델 추출
    3. Teaching 캡슐 실행
    4. 노드 스펙 생성 및 이벤트 발행
    
    Args:
        context: 도구 실행 컨텍스트
        call: 도구 호출 정보
        
    Returns:
        도구 실행 결과
    """
    from app.dimension_adapter import execute_dimension_capsule
    
    tool_name = call.name
    capsule_key = TOOL_TO_CAPSULE.get(tool_name)
    
    if not capsule_key:
        logger.error(f"Unknown tool name: {tool_name}")
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.FAILED,
            error=f"Unknown teaching tool: {tool_name}",
        )
    
    capsule = get_capsule_by_key(capsule_key)
    if not capsule:
        logger.error(f"Capsule not found for key: {capsule_key}")
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.FAILED,
            error=f"Capsule definition not found: {capsule_key}",
        )
    
    # 이벤트 에미터 생성
    emitter = create_emitter(context, call)
    args = call.arguments or {}
    
    # 모델 추출 (기본값 처리)
    spec = capsule["spec"]
    default_model = spec.get("params", {}).get("model", {}).get(
        "default", "gemini-3-flash-preview"
    )
    model = args.get("model", default_model)
    
    # 크레딧 비용 계산
    credit_cost = get_credit_cost(capsule_key, model)
    
    # Evidence Loop: 시작 기록
    evidence_event_id = record_tool_start(
        session_id=context.session_id or "unknown",
        tool_name=tool_name,
        dimension=_get_tool_dimension(tool_name),
    )
    
    # SSE 시작 이벤트
    emitter.emit("agent.teaching_start", {
        "tool_name": tool_name,
        "capsule_key": capsule_key,
        "model": model,
        "credit_cost": credit_cost,
    })
    
    logger.info(
        f"Teaching tool started: {tool_name}",
        extra={
            "session_id": context.session_id,
            "capsule_key": capsule_key,
            "model": model,
            "credit_cost": credit_cost,
        },
    )
    
    try:
        # 입력 준비 (model은 params로 분리)
        inputs = {k: v for k, v in args.items() if k != "model"}
        params = {"model": model}
        
        # === Phase 3: Intent-Resolver Integration ===
        # 템플릿에서 input_preset이 전달되면 Intent 기반으로 params 확장
        template_preset = args.get("_template_preset")  # 내부 전달용
        if template_preset:
            try:
                from app.resolvers.integration import prepare_dimension_params
                dimension_code = TOOL_TO_DIMENSION.get(tool_name)
                if dimension_code:
                    inputs, params = await prepare_dimension_params(
                        dimension_code=dimension_code,
                        inputs=inputs,
                        params={**params, **template_preset},
                    )
                    logger.debug(f"[{tool_name}] Intent-resolved params applied from template")
            except ImportError:
                logger.debug(f"[{tool_name}] Resolver integration not available")
            except Exception as e:
                logger.warning(f"[{tool_name}] Resolver integration failed: {e}")
        
        # Teaching 캡슐 실행
        result = await execute_dimension_capsule(
            capsule_id=capsule_key,
            inputs=inputs,
            params=params,
            user_api_key=None,  # Agent는 서버 키 사용
        )
        
        if not result.get("success"):
            error_msg = result.get("error", "Execution failed")
            
            # Evidence Loop: 실패 기록
            record_tool_failure(
                event_id=evidence_event_id,
                session_id=context.session_id or "unknown",
                tool_name=tool_name,
                error_code="EXECUTION_FAILED",
                error_message=error_msg,
            )
            
            emitter.emit("agent.teaching_error", {
                "tool_name": tool_name,
                "capsule_key": capsule_key,
                "error": error_msg,
            })
            logger.warning(
                f"Teaching tool failed: {tool_name}",
                extra={
                    "session_id": context.session_id,
                    "error": error_msg,
                },
            )
            return error_result(call, error_msg)
        
        # 노드 스펙 생성
        output = result.get("output", {})
        node_spec = build_dimension_node_spec(
            capsule=capsule,
            inputs=inputs,
            output=output,
            credit_cost=credit_cost,
        )
        
        # Evidence Loop: 성공 기록
        record_tool_success(
            event_id=evidence_event_id,
            session_id=context.session_id or "unknown",
            tool_name=tool_name,
            credit_cost=credit_cost,
        )
        
        # SSE 완료 이벤트
        emitter.emit("agent.teaching_complete", {
            "tool_name": tool_name,
            "capsule_key": capsule_key,
            "model": model,
            "credit_cost": credit_cost,
            "latency_ms": result.get("metrics", {}).get("latency_ms"),
        })
        
        # 노드 생성 이벤트 (Canvas 연동용)
        emitter.emit("agent.node_created", {
            "node_type": "teaching_capsule",
            "node_spec": node_spec,
            "action": "add_to_canvas",
        })
        
        logger.info(
            f"Teaching tool completed: {tool_name}",
            extra={
                "session_id": context.session_id,
                "capsule_key": capsule_key,
                "model": model,
                "credit_cost": credit_cost,
                "latency_ms": result.get("metrics", {}).get("latency_ms"),
            },
        )
        
        return success_result(call, {
            "capsule_id": capsule_key,
            "output": output,
            "node_spec": node_spec,
            "credit_cost": credit_cost,
            "metrics": result.get("metrics"),
        })
        
    except Exception as e:
        # Evidence Loop: 예외 실패 기록
        record_tool_failure(
            event_id=evidence_event_id,
            session_id=context.session_id or "unknown",
            tool_name=tool_name,
            error_code="EXCEPTION",
            error_message=str(e),
        )
        
        emitter.emit("agent.teaching_error", {
            "tool_name": tool_name,
            "capsule_key": capsule_key,
            "error": str(e),
        })
        logger.exception(
            f"Teaching tool error: {tool_name}",
            extra={
                "session_id": context.session_id,
                "error": str(e),
            },
        )
        return error_result(call, f"Teaching tool failed: {e}")


# =============================================================================
# Registration
# =============================================================================

def get_dimension_tool_specs() -> List[ToolSpec]:
    """등록 가능한 Teaching 도구 스펙 목록 반환.
    
    테스트 및 디버깅에 유용.
    """
    specs = []
    for capsule in DIMENSION_CAPSULES:
        specs.append(_capsule_to_tool_spec(capsule))
    return specs


def register_dimension_tools(registry: ToolRegistry) -> None:
    """Teaching 도구들을 ToolRegistry에 등록.
    
    DIMENSION_CAPSULES에서 동적으로 ToolSpec을 생성하여
    캡슐 정의 변경 시 자동으로 반영됩니다.
    
    Args:
        registry: 도구를 등록할 ToolRegistry 인스턴스
    """
    registered_count = 0
    
    for capsule in DIMENSION_CAPSULES:
        try:
            spec = _capsule_to_tool_spec(capsule)
            registry.register(spec, _dimension_tool_handler)
            registered_count += 1
            logger.debug(f"Registered teaching tool: {spec.name}")
        except Exception as e:
            logger.error(
                f"Failed to register teaching tool for capsule: {capsule.get('capsule_key')}",
                extra={"error": str(e)},
            )
    
    logger.info(f"Registered {registered_count} dimension tools from DIMENSION_CAPSULES")
