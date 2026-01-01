"""Workflow compilation tools for VividAgent.

Exposes DirectorAgent functionality as callable tools,
enabling chat-first workflow generation.
"""
from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any, Dict, Optional

from app.agents.agent_types import (
    ToolCall,
    ToolContext,
    ToolRegistry,
    ToolResult,
    ToolSpec,
    ToolTaskState,
)
from app.agents.director import DirectorAgent, OutputType, VibeInput
from app.logging_config import get_logger

logger = get_logger("workflow_tools")


async def _compile_workflow_handler(
    context: ToolContext,
    call: ToolCall,
) -> ToolResult:
    """
    자연어 바이브 설명을 워크플로우로 컴파일합니다.
    
    DirectorAgent.interpret_vibe를 래핑하여 노드/엣지/NarrativeDNA를
    포함한 WorkflowPlan을 반환합니다.
    """
    args = call.arguments
    vibe_description = args.get("vibe_description", "")
    output_type_str = args.get("output_type", "short_drama")
    target_length_sec = args.get("target_length_sec", 60)
    capsule_id = args.get("capsule_id")
    
    if not vibe_description:
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.FAILED,
            error="vibe_description is required",
        )
    
    try:
        # Validate output_type
        try:
            output_type = OutputType(output_type_str)
        except ValueError:
            output_type = OutputType.SHORT_DRAMA
        
        # Create VibeInput and run DirectorAgent
        director = DirectorAgent()
        vibe_input = VibeInput(
            type="custom",
            custom_description=vibe_description,
            output_type=output_type,
            target_length_sec=target_length_sec,
            capsule_id=capsule_id,
        )
        
        plan = await director.interpret_vibe(vibe_input)
        
        # Serialize WorkflowPlan to dict
        # Handle nested dataclasses
        plan_dict = {
            "workflow_id": plan.workflow_id,
            "estimated_duration_sec": plan.estimated_duration_sec,
            "agent_assignments": plan.agent_assignments,
            "capsule_id": plan.capsule_id,
            "logic_vector": plan.logic_vector,
            "persona_vector": plan.persona_vector,
            "narrative_dna": asdict(plan.narrative_dna) if plan.narrative_dna else None,
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "category": n.category.value if hasattr(n.category, 'value') else n.category,
                    "label": n.label,
                    "description": n.description,
                    "position": n.position,
                    "ai_model": n.ai_model,
                    "data": n.data,
                }
                for n in plan.nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "source": e.source,
                    "target": e.target,
                    "source_handle": e.source_handle,
                    "target_handle": e.target_handle,
                }
                for e in plan.edges
            ],
        }
        
        logger.info(
            "Workflow compiled successfully",
            extra={
                "session_id": context.session_id,
                "workflow_id": plan.workflow_id,
                "node_count": len(plan.nodes),
            }
        )
        
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.COMPLETED,
            output=plan_dict,
        )
        
    except Exception as e:
        logger.exception(
            "Failed to compile workflow",
            extra={"session_id": context.session_id, "error": str(e)}
        )
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.FAILED,
            error=f"Workflow compilation failed: {str(e)}",
        )


async def _list_vibe_presets_handler(
    context: ToolContext,
    call: ToolCall,
) -> ToolResult:
    """사용 가능한 바이브 프리셋 목록을 반환합니다."""
    try:
        director = DirectorAgent()
        presets = []
        for preset_id, preset in director.presets.items():
            presets.append({
                "id": preset.id,
                "title": preset.title,
                "tone": preset.tone,
                "visual_style": preset.visual_style,
                "emotional_arc": preset.emotional_arc,
                "reference_works": preset.reference_works,
            })
        
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.COMPLETED,
            output={"presets": presets, "count": len(presets)},
        )
    except Exception as e:
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.FAILED,
            error=str(e),
        )


async def _list_capsule_styles_handler(
    context: ToolContext,
    call: ToolCall,
) -> ToolResult:
    """사용 가능한 거장(capsule) 스타일 목록을 반환합니다."""
    # Hardcoded list based on capsule_adapter.py AUTEUR_PALETTES
    styles = [
        {
            "id": "auteur.bong-joon-ho",
            "name": "봉준호",
            "signature": "tension_bias",
            "description": "계급 갈등, 아이러니, 장르 믹싱. 대칭 구도와 수직 블로킹.",
        },
        {
            "id": "auteur.park-chan-wook",
            "name": "박찬욱",
            "signature": "violence_aesthetics",
            "description": "복수, 금지된 욕망, 폭력의 미학. 극단적 클로즈업과 스플릿 디옵터.",
        },
        {
            "id": "auteur.na-hongjin",
            "name": "나홍진",
            "signature": "chaos_bias",
            "description": "악의 실체, 종교적 공포, 혼돈. 핸드헬드와 불안정한 구도.",
        },
        {
            "id": "auteur.hong-sangsoo",
            "name": "홍상수",
            "signature": "stillness",
            "description": "일상, 반복, 술. 정적인 투샷과 느린 줌.",
        },
    ]
    
    return ToolResult(
        tool_call_id=call.id,
        name=call.name,
        status=ToolTaskState.COMPLETED,
        output={"styles": styles, "count": len(styles)},
    )


def register_workflow_tools(registry: ToolRegistry) -> None:
    """Register workflow compilation tools to the registry."""
    
    # 1. compile_workflow - 메인 워크플로우 컴파일 도구
    registry.register(
        ToolSpec(
            name="compile_workflow",
            description=(
                "자연어 바이브 설명을 워크플로우 계획으로 컴파일합니다. "
                "노드, 엣지, NarrativeDNA를 포함한 WorkflowPlan을 생성합니다. "
                "사용자가 영상의 분위기, 스타일, 장르를 설명하면 이 도구를 사용하세요."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "vibe_description": {
                        "type": "string",
                        "description": "원하는 영상의 분위기/스타일 설명 (자연어)",
                    },
                    "output_type": {
                        "type": "string",
                        "enum": ["short_drama", "ad", "animation", "music_video"],
                        "default": "short_drama",
                        "description": "출력 유형",
                    },
                    "target_length_sec": {
                        "type": "integer",
                        "default": 60,
                        "description": "목표 영상 길이 (초)",
                    },
                    "capsule_id": {
                        "type": "string",
                        "description": "거장 스타일 ID (예: auteur.bong-joon-ho). list_capsule_styles로 확인 가능.",
                    },
                },
                "required": ["vibe_description"],
            },
        ),
        _compile_workflow_handler,
    )
    
    # 2. list_vibe_presets - 프리셋 목록 조회
    registry.register(
        ToolSpec(
            name="list_vibe_presets",
            description="사용 가능한 바이브 프리셋 목록을 반환합니다. 사용자가 어떤 스타일을 선택할지 모를 때 추천용으로 사용하세요.",
            input_schema={
                "type": "object",
                "properties": {},
            },
        ),
        _list_vibe_presets_handler,
    )
    
    # 3. list_capsule_styles - 거장 스타일 목록 조회
    registry.register(
        ToolSpec(
            name="list_capsule_styles",
            description="사용 가능한 거장(감독) 스타일 목록을 반환합니다. capsule_id 선택에 참고하세요.",
            input_schema={
                "type": "object",
                "properties": {},
            },
        ),
        _list_capsule_styles_handler,
    )
    
    logger.info("Workflow tools registered: compile_workflow, list_vibe_presets, list_capsule_styles")
