"""Capsule execution and NotebookLM analysis tools for VividAgent.

Exposes capsule execution and source analysis functionality as callable tools,
enabling chat-first content generation.

Refactored to use shared utilities from tool_utils.py.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from functools import partial
from typing import Any, Dict, List, Tuple

from app.agents.agent_types import (
    ToolCall,
    ToolContext,
    ToolRegistry,
    ToolResult,
    ToolSpec,
)
from app.agents.tool_utils import (
    create_emitter,
    error_result,
    extract_evidence_refs,
    extract_first_source_id,
    success_result,
    TokenUsageTracker,
    validation_error,
)
from app.logging_config import get_logger

logger = get_logger("capsule_tools")


# =============================================================================
# Analysis Step Definitions
# =============================================================================

ANALYSIS_STEPS = [
    (1, "logic_vector", 0, 20),
    (2, "persona_vector", 20, 40),
    (3, "variation_guide", 40, 60),
    (4, "claims", 60, 80),
    (5, "storyboard", 80, 100),
]


# =============================================================================
# Tool Handlers
# =============================================================================

async def _run_capsule_handler(
    context: ToolContext,
    call: ToolCall,
) -> ToolResult:
    """캡슐을 실행하고 결과를 반환합니다."""
    args = call.arguments
    capsule_id = args.get("capsule_id", "")
    capsule_version = args.get("capsule_version", "v1")
    inputs = args.get("inputs", {})
    params = args.get("params", {})
    
    if not capsule_id:
        return validation_error(call, "capsule_id")
    
    emitter = create_emitter(context, call)
    
    try:
        from app.capsule_adapter import execute_capsule
        
        emitter.emit("agent.capsule_start", {
            "tool_name": call.name,
            "capsule_id": capsule_id,
        })
        
        def _progress_cb(message: str, progress: int) -> None:
            emitter.emit("agent.capsule_progress", {
                "tool_name": call.name,
                "capsule_id": capsule_id,
                "message": message,
                "progress": progress,
            })
        
        loop = asyncio.get_event_loop()
        summary, evidence_refs = await loop.run_in_executor(
            None,
            partial(
                execute_capsule,
                capsule_id=capsule_id,
                capsule_version=capsule_version,
                inputs=inputs,
                params=params,
                progress_cb=_progress_cb,
            )
        )
        
        emitter.emit("agent.capsule_complete", {
            "tool_name": call.name,
            "capsule_id": capsule_id,
            "progress": 100,
        })
        
        logger.info("Capsule executed successfully", extra={
            "session_id": context.session_id,
            "capsule_id": capsule_id,
            "version": capsule_version,
        })
        
        return success_result(call, {
            "summary": summary,
            "evidence_refs": evidence_refs,
        })
        
    except Exception as e:
        logger.exception("Failed to execute capsule", extra={
            "session_id": context.session_id, "error": str(e)
        })
        return error_result(call, f"Capsule execution failed: {e}")


async def _analyze_sources_handler(
    context: ToolContext,
    call: ToolCall,
) -> ToolResult:
    """NotebookLM 스타일 소스 분석을 수행합니다."""
    source_pack = call.arguments.get("source_pack", {})
    capsule_id = call.arguments.get("capsule_id", "auteur.bong-joon-ho")
    
    if not source_pack:
        return validation_error(call, "source_pack")
    
    emitter = create_emitter(context, call)
    
    try:
        # Run the actual analysis pipeline
        summary, evidence_refs, data_table = await _run_analysis_pipeline(
            source_pack, capsule_id, emitter
        )
        
        logger.info("Source analysis completed", extra={
            "session_id": context.session_id,
            "capsule_id": capsule_id,
            "has_logic_vector": bool(summary.get("logic_vector")),
            "has_persona_vector": bool(summary.get("persona_vector")),
            "claims_count": len(summary.get("claims", [])),
        })
        
        output = {
            "summary": summary,
            "evidence_refs": evidence_refs,
        }
        
        if data_table:
            output["data_table_artifact"] = data_table.model_dump(mode="json")
        
        return success_result(call, output)
        
    except Exception as e:
        logger.exception("Failed to analyze sources", extra={
            "session_id": context.session_id, "error": str(e)
        })
        return error_result(call, f"Source analysis failed: {e}")


async def _run_analysis_pipeline(
    source_pack: Dict[str, Any],
    capsule_id: str,
    emitter: Any,
) -> Tuple[Dict[str, Any], List[str], Any]:
    """
    Run the NotebookLM analysis pipeline.
    
    Extracted for testability and cleaner code flow.
    """
    from app.notebooklm_client import (
        extract_logic_vector,
        extract_persona_vector,
        generate_claims_with_evidence,
        generate_story_beats,
        generate_storyboard_cards,
        generate_variation_guide,
    )
    from app.schemas.artifact_schemas import create_data_table_from_claims
    from app.config import settings
    
    loop = asyncio.get_event_loop()
    tracker = TokenUsageTracker()
    
    # Step 1: Logic Vector
    emitter.progress(1, "logic_vector", 0)
    logic_vector, usage = await loop.run_in_executor(
        None, partial(extract_logic_vector, source_pack, capsule_id)
    )
    tracker.add(usage)
    emitter.progress(1, "logic_vector", 20)
    
    # Step 2: Persona Vector
    emitter.progress(2, "persona_vector", 20)
    persona_vector, usage = await loop.run_in_executor(
        None, partial(extract_persona_vector, source_pack, capsule_id)
    )
    tracker.add(usage)
    emitter.progress(2, "persona_vector", 40)
    
    # Step 3: Variation Guide
    emitter.progress(3, "variation_guide", 40)
    guide, usage = await loop.run_in_executor(
        None, partial(generate_variation_guide, logic_vector, persona_vector, capsule_id)
    )
    tracker.add(usage)
    emitter.progress(3, "variation_guide", 60)
    
    # Step 4: Claims with Evidence
    emitter.progress(4, "claims", 60)
    claims, usage = await loop.run_in_executor(
        None, partial(generate_claims_with_evidence, guide, source_pack)
    )
    tracker.add(usage)
    emitter.progress(4, "claims", 80)
    
    # Step 5: Story Beats & Storyboard
    emitter.progress(5, "storyboard", 80)
    story_beats = await loop.run_in_executor(
        None, partial(generate_story_beats, source_pack, capsule_id, guide, claims)
    )
    storyboard_cards = await loop.run_in_executor(
        None, partial(generate_storyboard_cards, source_pack, capsule_id, guide, claims, story_beats or [])
    )
    emitter.progress(5, "storyboard", 100)
    
    # Build summary
    summary = _build_analysis_summary(
        source_pack, capsule_id, logic_vector, persona_vector,
        guide, claims, story_beats, storyboard_cards, tracker
    )
    
    # Extract evidence refs and generate DataTable
    evidence_refs = extract_evidence_refs(claims)
    data_table = create_data_table_from_claims(summary, f"dt-{id(claims) % 10000:04d}")
    
    return summary, evidence_refs, data_table


def _build_analysis_summary(
    source_pack: Dict[str, Any],
    capsule_id: str,
    logic_vector: Dict[str, Any],
    persona_vector: Dict[str, Any],
    guide: Dict[str, Any],
    claims: List[Dict[str, Any]],
    story_beats: List[Dict[str, Any]],
    storyboard_cards: List[Dict[str, Any]],
    tracker: TokenUsageTracker,
) -> Dict[str, Any]:
    """Build the analysis summary dict."""
    from app.config import settings
    
    return {
        "source_id": extract_first_source_id(source_pack),
        "summary": f"NotebookLM analysis complete for {capsule_id}",
        "output_type": "report",
        "output_language": "und",
        "prompt_version": "notebooklm-gemini-v1",
        "model_version": getattr(settings, "GEMINI_MODEL", "gemini-1.5-pro"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_pack_id": source_pack.get("pack_id"),
        "capsule_id": capsule_id,
        "guide_type": "variation",
        "cluster_id": source_pack.get("cluster_id"),
        "logic_vector": logic_vector,
        "persona_vector": persona_vector,
        "guide": guide,
        "claims": claims,
        "story_beats": story_beats,
        "storyboard_cards": storyboard_cards,
        "source_count": source_pack.get("source_count", 0),
        "token_usage": tracker.to_dict(),
    }


async def _generate_storyboard_handler(
    context: ToolContext,
    call: ToolCall,
) -> ToolResult:
    """캡슐 실행 결과로부터 스토리보드 프리뷰를 생성합니다."""
    args = call.arguments
    summary = args.get("summary", {})
    scene_count = args.get("scene_count", 3)
    capsule_id = args.get("capsule_id") or summary.get("capsule_id")
    
    if not summary:
        return validation_error(call, "summary", "summary (from run_capsule) is required")
    
    try:
        from app.capsule_adapter import generate_storyboard_preview
        from app.schemas.artifact_schemas import create_storyboard_from_preview
        
        loop = asyncio.get_event_loop()
        storyboard = await loop.run_in_executor(
            None,
            partial(generate_storyboard_preview, summary=summary, scene_count=scene_count)
        )
        
        # Create artifact for frontend
        artifact_id = f"sb-{id(storyboard) % 10000:04d}"
        title = summary.get("title") or summary.get("message") or "Storyboard Preview"
        storyboard_artifact = create_storyboard_from_preview(
            preview=storyboard,
            artifact_id=artifact_id,
            title=title,
            capsule_id=capsule_id,
        )
        
        logger.info("Storyboard generated", extra={
            "session_id": context.session_id,
            "scene_count": len(storyboard),
        })
        
        output = {
            "storyboard": storyboard,
            "scene_count": len(storyboard),
        }
        
        if storyboard_artifact:
            output["storyboard_artifact"] = storyboard_artifact.model_dump(mode="json")
        
        return success_result(call, output)
        
    except Exception as e:
        logger.exception("Failed to generate storyboard", extra={
            "session_id": context.session_id, "error": str(e)
        })
        return error_result(call, f"Storyboard generation failed: {e}")


# =============================================================================
# Tool Specifications
# =============================================================================

_SPECS = [
    ToolSpec(
        name="run_capsule",
        description="캡슐을 실행하여 스토리보드, 샷 컨트랙트, 스타일 정보를 생성합니다.",
        input_schema={
            "type": "object",
            "properties": {
                "capsule_id": {"type": "string", "description": "캡슐 ID"},
                "capsule_version": {"type": "string", "default": "v1"},
                "inputs": {"type": "object", "description": "입력 데이터"},
                "params": {"type": "object", "description": "스타일 파라미터"},
            },
            "required": ["capsule_id"],
        },
    ),
    ToolSpec(
        name="analyze_sources",
        description="NotebookLM 스타일 소스 분석. Logic/Persona Vector, Claims를 추출합니다.",
        input_schema={
            "type": "object",
            "properties": {
                "source_pack": {"type": "object", "description": "분석할 소스 팩"},
                "capsule_id": {"type": "string", "default": "auteur.bong-joon-ho"},
            },
            "required": ["source_pack"],
        },
    ),
    ToolSpec(
        name="generate_storyboard",
        description="캡슐 실행 결과로부터 스토리보드 프리뷰를 생성합니다.",
        input_schema={
            "type": "object",
            "properties": {
                "summary": {"type": "object", "description": "run_capsule에서 반환된 summary"},
                "scene_count": {"type": "integer", "default": 3},
            },
            "required": ["summary"],
        },
    ),
]

_HANDLERS = {
    "run_capsule": _run_capsule_handler,
    "analyze_sources": _analyze_sources_handler,
    "generate_storyboard": _generate_storyboard_handler,
}


def register_capsule_tools(registry: ToolRegistry) -> None:
    """Register capsule execution and analysis tools."""
    for spec in _SPECS:
        handler = _HANDLERS.get(spec.name)
        if handler:
            registry.register(spec, handler)
    
    logger.info(f"Registered {len(_SPECS)} capsule tools")
