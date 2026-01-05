"""Workflow Orchestration Tools for VividAgent.

Agent가 차원 워크플로우를 생성하고 실행할 수 있는 도구들.

사용 가능한 도구:
- create_workflow: 차원 워크플로우 구조 생성
- execute_workflow: 생성된 워크플로우 순차 실행
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from app.agents.agent_types import (
    TieredContext,
    ToolCall,
    ToolContext,
    ToolRegistry,
    ToolResult,
    ToolSpec,
    ToolTaskState,
)
from app.agents.tool_utils import create_emitter, error_result, success_result
from app.logging_config import get_logger
from datetime import datetime

logger = get_logger("workflow_tools")


# =============================================================================
# Constants
# =============================================================================

DIMENSION_TO_TOOL: Dict[str, str] = {
    "1D": "generate_veo_prompt",
    "2D": "create_storyboard",
    "3D": "generate_image_prompt",
    "4D": "analyze_reference",
}

DIMENSION_NAMES: Dict[str, str] = {
    "1D": "Origin (프롬프트 생성)",
    "2D": "Blueprint (스토리보드)",
    "3D": "Ambience (이미지 생성)",
    "4D": "Moment (레퍼런스 분석)",
}

DIMENSION_COLORS: Dict[str, str] = {
    "1D": "#8B5CF6",  # Violet
    "2D": "#10B981",  # Emerald
    "3D": "#F59E0B",  # Amber
    "4D": "#06B6D4",  # Cyan
}


# =============================================================================
# Workflow Creation Tool
# =============================================================================

CREATE_WORKFLOW_SPEC = ToolSpec(
    name="create_workflow",
    description="차원 워크플로우를 생성합니다. 여러 차원을 순서대로 연결하여 완성된 워크플로우 구조를 만듭니다.",
    input_schema={
        "type": "object",
        "properties": {
            "workflow_name": {
                "type": "string",
                "description": "워크플로우 이름 (예: '시네마틱 카페 브이로그')",
            },
            "topic": {
                "type": "string",
                "description": "워크플로우 주제/컨셉 (예: '감성적인 도시 야경 영상')",
            },
            "dimensions": {
                "type": "array",
                "items": {"type": "string", "enum": ["1D", "2D", "3D", "4D"]},
                "description": "실행할 차원 순서 (기본값: ['1D', '2D', '3D'])",
                "default": ["1D", "2D", "3D"],
            },
            "auto_execute": {
                "type": "boolean",
                "description": "워크플로우 생성 후 자동 실행 여부",
                "default": True,
            },
        },
        "required": ["topic"],
    },
)


async def _create_workflow_handler(
    context: ToolContext,
    call: ToolCall,
) -> ToolResult:
    """워크플로우 생성 핸들러."""
    emitter = create_emitter(context, call)
    args = call.arguments or {}
    
    topic = args.get("topic", "")
    dimensions = args.get("dimensions", ["1D", "2D", "3D"])
    workflow_name = args.get("workflow_name", topic[:30] if topic else "새 워크플로우")
    auto_execute = args.get("auto_execute", True)
    
    if not topic:
        return error_result(call, "워크플로우 주제(topic)를 지정해주세요.")
    
    if not dimensions:
        return error_result(call, "최소 하나 이상의 차원을 지정해주세요.")
    
    # Validate dimensions
    invalid_dims = [d for d in dimensions if d not in DIMENSION_TO_TOOL]
    if invalid_dims:
        return error_result(call, f"유효하지 않은 차원: {invalid_dims}. 사용 가능: 1D, 2D, 3D, 4D")
    
    workflow_id = str(uuid.uuid4())
    
    # Build workflow structure
    nodes = []
    edges = []
    prev_node_id = None
    
    for idx, dim in enumerate(dimensions):
        node_id = f"node_{dim}_{idx}"
        tool_name = DIMENSION_TO_TOOL[dim]
        
        node = {
            "id": node_id,
            "dimension": dim,
            "dimension_name": DIMENSION_NAMES.get(dim, dim),
            "tool_name": tool_name,
            "color": DIMENSION_COLORS.get(dim, "#888888"),
            "order": idx,
            "status": "pending",
            "inputs": {},
            "output": None,
        }
        nodes.append(node)
        
        # Connect to previous node
        if prev_node_id:
            edges.append({
                "id": f"edge_{idx}",
                "source": prev_node_id,
                "target": node_id,
            })
        prev_node_id = node_id
    
    workflow_spec = {
        "workflow_id": workflow_id,
        "name": workflow_name,
        "topic": topic,
        "dimensions": dimensions,
        "nodes": nodes,
        "edges": edges,
        "auto_execute": auto_execute,
        "status": "created",
        "created_at": None,  # Will be set when saved
    }
    
    # Emit workflow created event
    emitter.emit("agent.workflow_created", {
        "workflow_id": workflow_id,
        "name": workflow_name,
        "topic": topic,
        "dimensions": dimensions,
        "node_count": len(nodes),
        "auto_execute": auto_execute,
    })
    
    logger.info(
        "Workflow created",
        extra={
            "session_id": context.session_id,
            "workflow_id": workflow_id,
            "dimensions": dimensions,
        },
    )
    
    # Generate dimension flow description
    flow_desc = " → ".join([
        f"{dim} {DIMENSION_NAMES.get(dim, dim)}"
        for dim in dimensions
    ])
    
    return success_result(call, {
        "workflow_id": workflow_id,
        "workflow_spec": workflow_spec,
        "flow_description": flow_desc,
        "message": f"워크플로우 '{workflow_name}'가 생성되었습니다! ({len(nodes)}개 차원: {flow_desc})",
    })


# =============================================================================
# Workflow Execution Tool
# =============================================================================

EXECUTE_WORKFLOW_SPEC = ToolSpec(
    name="execute_workflow",
    description="워크플로우를 순차적으로 실행합니다. 각 차원 도구를 순서대로 호출하고 결과를 연결합니다.",
    input_schema={
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "워크플로우 주제/컨셉 (예: '시네마틱 도시 야경')",
            },
            "dimensions": {
                "type": "array",
                "items": {"type": "string", "enum": ["1D", "2D", "3D", "4D"]},
                "description": "실행할 차원 순서 (기본값: ['1D', '2D', '3D'])",
                "default": ["1D", "2D", "3D"],
            },
            "model": {
                "type": "string",
                "description": "AI 모델 선택",
                "default": "gemini-3-flash-preview",
            },
        },
        "required": ["topic"],
    },
)


async def _execute_workflow_handler(
    context: ToolContext,
    call: ToolCall,
) -> ToolResult:
    """워크플로우 실행 핸들러.

    각 차원 도구를 순차적으로 실행하고 결과를 체이닝합니다.
    TieredContext를 사용하여 session/step/history를 분리 관리합니다.
    DB에서 동적으로 도구를 로딩하여 커뮤니티 도구도 지원합니다.
    """
    from app.services.dynamic_adapter import execute_tool_by_key
    from app.database import get_db_context

    emitter = create_emitter(context, call)
    args = call.arguments or {}

    topic = args.get("topic", "") or ""
    dimensions = args.get("dimensions") or ["1D", "2D", "3D"]
    model = args.get("model") or "gemini-3-flash-preview"

    # Validate topic
    if not topic or not isinstance(topic, str):
        return error_result(call, "워크플로우 주제(topic)를 지정해주세요.")
    topic = topic.strip()
    if len(topic) < 2:
        return error_result(call, "주제는 최소 2글자 이상이어야 합니다.")

    # Validate dimensions
    if not dimensions or not isinstance(dimensions, list):
        return error_result(call, "실행할 차원을 지정해주세요.")

    # Filter valid dimensions only
    valid_dimensions = [d for d in dimensions if isinstance(d, str) and d in DIMENSION_TO_TOOL]
    if not valid_dimensions:
        return error_result(call, f"유효한 차원이 없습니다. 사용 가능: {list(DIMENSION_TO_TOOL.keys())}")

    workflow_id = str(uuid.uuid4())

    # Initialize TieredContext for this workflow
    tiered = context.state.get_or_create_tiered_context()

    # Set session-level values (persist across all steps)
    tiered.set_session_value("workflow_id", workflow_id)
    tiered.set_session_value("topic", topic)
    tiered.set_session_value("model", model)
    tiered.set_session_value("style", args.get("style", "cinematic"))
    tiered.set_session_value("started_at", datetime.utcnow().isoformat() + "Z")

    emitter.emit("agent.workflow_start", {
        "workflow_id": workflow_id,
        "topic": topic,
        "dimensions": valid_dimensions,
        "total_steps": len(valid_dimensions),
    })

    results: List[Dict[str, Any]] = []
    total_credits = 0
    prev_output: Dict[str, Any] = {"topic": topic}

    for idx, dim in enumerate(valid_dimensions):
        tool_name = DIMENSION_TO_TOOL.get(dim)
        if not tool_name:
            emitter.emit("agent.workflow_step_error", {
                "step": idx,
                "dimension": dim,
                "error": f"Unknown dimension: {dim}",
            })
            continue

        # Advance to new step (archives previous step to history)
        tiered.advance_step(dimension=dim)

        # Set step-level context
        tiered.step["tool_name"] = tool_name
        tiered.step["dimension"] = dim
        tiered.step["started_at"] = datetime.utcnow().isoformat() + "Z"

        # Prepare inputs using tiered context + backward compatible method
        inputs = _prepare_dimension_inputs_tiered(tiered, dim, topic, prev_output)

        emitter.emit("agent.workflow_step_start", {
            "step": idx + 1,
            "total_steps": len(dimensions),
            "dimension": dim,
            "dimension_name": DIMENSION_NAMES.get(dim, dim),
            "tool_name": tool_name,
        })

        try:
            # Execute using dynamic adapter (loads from DB)
            async with get_db_context() as db:
                result = await execute_tool_by_key(
                    tool_key=tool_name,
                    inputs=inputs,
                    params={"model": model},
                    db_session=db,
                )

            if result.success:
                # Defensive: ensure output is a dict
                output = result.output if isinstance(result.output, dict) else {}

                # Safe metrics access
                credit_cost = 1
                if result.metrics and isinstance(result.metrics, dict):
                    credit_cost = result.metrics.get("credit_cost", 1)
                    if not isinstance(credit_cost, (int, float)):
                        credit_cost = 1
                total_credits += credit_cost

                # Store in tiered context step
                tiered.step["success"] = True
                tiered.step["output"] = output
                tiered.step["credit_cost"] = credit_cost

                # Store large outputs as handles (optional optimization)
                if _should_use_handle(output):
                    try:
                        from app.agents.handle_storage import get_handle_storage
                        storage = get_handle_storage()
                        handle_key = f"{workflow_id}:{dim}:{idx}"
                        handle_ref = await storage.store(
                            key=handle_key,
                            data=output,
                            metadata={"dimension": dim, "session_id": context.session_id},
                        )
                        tiered.register_handle(f"{dim}_output", handle_ref)
                        tiered.step["output_handle"] = handle_ref
                    except Exception as he:
                        logger.warning(f"Failed to store handle: {he}")

                step_result: Dict[str, Any] = {
                    "dimension": dim,
                    "dimension_name": DIMENSION_NAMES.get(dim, dim),
                    "tool_name": tool_name,
                    "status": "success",
                    "output": output,
                    "credit_cost": credit_cost,
                }
                results.append(step_result)

                # Update prev_output only if output is valid dict
                if output:
                    prev_output = output

                emitter.emit("agent.workflow_step_complete", {
                    "step": idx + 1,
                    "dimension": dim,
                    "credit_cost": credit_cost,
                    "output_preview": _get_output_preview(output),
                })
            else:
                error_msg = result.error or "Unknown error"
                tiered.step["success"] = False
                tiered.step["error"] = error_msg

                results.append({
                    "dimension": dim,
                    "status": "failed",
                    "error": error_msg,
                })
                emitter.emit("agent.workflow_step_error", {
                    "step": idx + 1,
                    "dimension": dim,
                    "error": error_msg,
                })

        except Exception as e:
            logger.exception(f"Workflow step {dim} failed", extra={"error": str(e)})
            tiered.step["success"] = False
            tiered.step["error"] = str(e)

            results.append({
                "dimension": dim,
                "status": "error",
                "error": str(e),
            })
            emitter.emit("agent.workflow_step_error", {
                "step": idx + 1,
                "dimension": dim,
                "error": str(e),
            })

    # Final step archival
    if tiered.step:
        tiered.advance_step(dimension="complete")

    # Workflow complete
    success_count = sum(1 for r in results if r.get("status") == "success")

    emitter.emit("agent.workflow_complete", {
        "workflow_id": workflow_id,
        "total_steps": len(valid_dimensions),
        "success_count": success_count,
        "total_credits": total_credits,
    })

    logger.info(
        "Workflow execution complete",
        extra={
            "session_id": context.session_id,
            "workflow_id": workflow_id,
            "success_count": success_count,
            "total_credits": total_credits,
            "history_count": len(tiered.history),
        },
    )

    return success_result(call, {
        "workflow_id": workflow_id,
        "topic": topic,
        "dimensions": valid_dimensions,
        "results": results,
        "total_credits": total_credits,
        "success_count": success_count,
        "message": f"워크플로우 완료! {success_count}/{len(valid_dimensions)}개 차원 성공, 총 {total_credits}크레딧 소모",
    })


def _prepare_dimension_inputs(
    dimension: str,
    topic: str,
    prev_output: Dict[str, Any],
) -> Dict[str, Any]:
    """차원별 입력 준비.
    
    이전 단계의 출력을 현재 단계의 입력으로 변환합니다.
    NOTE: 필드명은 teaching_adapter.py의 각 run_* 함수와 일치해야 함.
    
    Args:
        dimension: 차원 ID (1D, 2D, 3D, 4D)
        topic: 원본 주제
        prev_output: 이전 단계의 출력 (빈 dict일 수 있음)
        
    Returns:
        해당 차원 도구에 맞는 입력 딕셔너리
    """
    # Defensive: ensure prev_output is a dict
    if not isinstance(prev_output, dict):
        prev_output = {"topic": topic}
    
    # Ensure topic is valid
    topic = str(topic) if topic else "untitled"
    
    if dimension == "1D":
        # Veo Prompt Generator - expects: topic, style, mood
        style = prev_output.get("style")
        if not isinstance(style, str):
            style = "cinematic"
        mood = prev_output.get("mood")
        if not isinstance(mood, str):
            mood = "neutral"
        return {
            "topic": topic,
            "style": style,
            "mood": mood,
        }
    
    elif dimension == "2D":
        # Storyboard - expects: concept, scene_count
        concept = prev_output.get("prompt") or prev_output.get("description") or topic
        if not isinstance(concept, str):
            concept = str(concept) if concept else topic
        
        scene_count = prev_output.get("scene_count", 5)
        if not isinstance(scene_count, int) or scene_count < 1:
            scene_count = 5
        scene_count = min(scene_count, 20)  # Cap at 20 scenes
        
        return {
            "concept": concept,
            "scene_count": scene_count,
        }
    
    elif dimension == "3D":
        # Image Prompt Generator - expects: description (NOT topic!)
        description = topic  # Default fallback
        
        scenes = prev_output.get("scenes")
        if isinstance(scenes, list) and len(scenes) > 0:
            first_scene = scenes[0]
            if isinstance(first_scene, dict):
                scene_desc = first_scene.get("description")
                if isinstance(scene_desc, str) and scene_desc.strip():
                    description = scene_desc
        else:
            # Use previous prompt output or topic
            prompt = prev_output.get("prompt")
            desc = prev_output.get("description")
            if isinstance(prompt, str) and prompt.strip():
                description = prompt
            elif isinstance(desc, str) and desc.strip():
                description = desc
        
        # Handle style - could be string or dict
        style_val = prev_output.get("style")
        style = "photorealistic"
        if isinstance(style_val, dict):
            cinematography = style_val.get("cinematography")
            if isinstance(cinematography, str):
                style = cinematography
        elif isinstance(style_val, str):
            style = style_val
        
        return {
            "description": description,
            "style": style,
            "aspect_ratio": "16:9",
        }
    
    elif dimension == "4D":
        # Reference Analyzer - expects: video_description, focus_areas
        video_desc = topic  # Default fallback
        desc = prev_output.get("description")
        prompt = prev_output.get("prompt")
        if isinstance(desc, str) and desc.strip():
            video_desc = desc
        elif isinstance(prompt, str) and prompt.strip():
            video_desc = prompt
            
        return {
            "video_description": video_desc,
            "focus_areas": ["composition", "color", "mood", "lighting"],
        }
    
    return {"topic": topic}


def _prepare_dimension_inputs_tiered(
    tiered: TieredContext,
    dimension: str,
    fallback_topic: str,
    prev_output: Dict[str, Any],
) -> Dict[str, Any]:
    """Prepare inputs using tiered context.

    Uses session values for global preferences and falls back to prev_output.
    This function is a wrapper that enhances _prepare_dimension_inputs with
    TieredContext session values.

    Args:
        tiered: TieredContext instance
        dimension: Dimension ID (1D, 2D, 3D, 4D)
        fallback_topic: Fallback topic if not in session
        prev_output: Previous step output for chaining

    Returns:
        Input dictionary for the dimension tool
    """
    # Get session-level values
    topic = tiered.get_session_value("topic", fallback_topic)
    style = tiered.get_session_value("style", "cinematic")

    # Merge session values into prev_output for backward compatibility
    enhanced_prev = dict(prev_output) if prev_output else {}
    if "style" not in enhanced_prev:
        enhanced_prev["style"] = style

    # Use the original function for actual input preparation
    inputs = _prepare_dimension_inputs(dimension, topic, enhanced_prev)

    return inputs


def _should_use_handle(output: Dict[str, Any]) -> bool:
    """Determine if output should be stored as handle.

    Criteria:
    - Contains many scenes (storyboard with > 3 scenes)
    - Large JSON size (> 5KB)

    Args:
        output: Tool output dictionary

    Returns:
        True if output should be stored as handle
    """
    if not output or not isinstance(output, dict):
        return False

    # Check for large storyboard
    if "scenes" in output and isinstance(output["scenes"], list):
        if len(output["scenes"]) > 3:
            return True

    # Check total size (rough estimate)
    try:
        import json
        size = len(json.dumps(output, ensure_ascii=False))
        return size > 5000  # 5KB threshold
    except Exception:
        return False


def _get_output_preview(output: Dict[str, Any], max_length: int = 100) -> str:
    """출력 미리보기 생성.
    
    Args:
        output: 도구 출력 (dict일 수 있고 None일 수 있음)
        max_length: 최대 미리보기 길이
        
    Returns:
        사람이 읽을 수 있는 미리보기 문자열
    """
    # Defensive: ensure output is a dict
    if not isinstance(output, dict):
        return "(결과 없음)"
    
    if not output:
        return "(빈 결과)"
    
    preview = ""
    
    try:
        if "prompt" in output:
            val = output["prompt"]
            preview = str(val) if val else ""
        elif "description" in output:
            val = output["description"]
            preview = str(val) if val else ""
        elif "scenes" in output:
            scenes = output["scenes"]
            if isinstance(scenes, list):
                preview = f"{len(scenes)}개 씬 생성됨"
            else:
                preview = "씬 데이터 생성됨"
        elif "analysis" in output:
            val = output["analysis"]
            preview = str(val) if val else ""
        else:
            # Try to get first string value
            for key, val in output.items():
                if isinstance(val, str) and val.strip():
                    preview = val
                    break
            if not preview:
                preview = f"{len(output)}개 필드"
    except Exception:
        preview = "(미리보기 생성 실패)"
    
    # Ensure preview is a string
    if not isinstance(preview, str):
        preview = str(preview)
    
    # Truncate if needed
    max_length = max(10, min(max_length, 500))  # Clamp between 10-500
    if len(preview) > max_length:
        preview = preview[:max_length] + "..."
    
    return preview


# =============================================================================
# Registration
# =============================================================================

def get_workflow_tool_specs() -> List[ToolSpec]:
    """워크플로우 도구 스펙 목록 반환."""
    return [CREATE_WORKFLOW_SPEC, EXECUTE_WORKFLOW_SPEC]


def register_workflow_tools(registry: ToolRegistry) -> None:
    """워크플로우 도구들을 ToolRegistry에 등록."""
    registry.register(CREATE_WORKFLOW_SPEC, _create_workflow_handler)
    registry.register(EXECUTE_WORKFLOW_SPEC, _execute_workflow_handler)
    logger.info("Registered 2 workflow tools")
