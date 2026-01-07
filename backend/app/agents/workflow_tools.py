"""Workflow Orchestration Tools for VividAgent.

Agent가 차원 워크플로우를 생성하고 실행할 수 있는 도구들.

사용 가능한 도구:
- create_workflow: 차원 워크플로우 구조 생성
- execute_workflow: 생성된 워크플로우 순차 실행

Hardening (T2):
- Handle cleanup on workflow failure
- Parallel workflow isolation via execution lock
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, List, Optional, Set

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
# T2-2: Workflow Execution Lock (per session)
# =============================================================================

_workflow_locks: Dict[str, asyncio.Lock] = {}
_active_workflows: Set[str] = set()  # Track workflow_ids currently executing


def _get_workflow_lock(session_id: str) -> asyncio.Lock:
    """Get or create a lock for the given session."""
    if session_id not in _workflow_locks:
        _workflow_locks[session_id] = asyncio.Lock()
    return _workflow_locks[session_id]


async def _cleanup_handles(handle_refs: List[str]) -> int:
    """Clean up orphaned handles on workflow failure.

    Returns number of handles successfully deleted.
    """
    if not handle_refs:
        return 0

    try:
        from app.agents.handle_storage import get_handle_storage
        storage = get_handle_storage()
        deleted = 0
        for ref in handle_refs:
            try:
                if await storage.delete(ref):
                    deleted += 1
                    logger.debug(f"Cleaned up orphan handle: {ref}")
            except Exception as e:
                logger.warning(f"Failed to cleanup handle {ref}: {e}")
        return deleted
    except Exception as e:
        logger.error(f"Handle cleanup failed: {e}")
        return 0


# =============================================================================
# Constants
# =============================================================================

DIMENSION_TO_TOOL: Dict[str, str] = {
    "1D": "generate_veo_prompt",
    "2D": "create_storyboard",
    "3D": "generate_image_prompt",
    "4D": "analyze_reference",
    # Extended Dimension Capsules
    "QC": "quality_check",
    "AD": "aesthetic_direct",
    "AI": "persona_analyze",
    "VEO": "veo_generate",
}

DIMENSION_NAMES: Dict[str, str] = {
    "1D": "Origin (프롬프트 생성)",
    "2D": "Blueprint (스토리보드)",
    "3D": "Ambience (이미지 생성)",
    "4D": "Moment (레퍼런스 분석)",
    # Extended Dimension Capsules
    "QC": "Quality (품질 검수)",
    "AD": "Aesthetic (미학 디렉터)",
    "AI": "Abyss (심연 해석)",
    "VEO": "Video (Veo 비디오)",
}

DIMENSION_COLORS: Dict[str, str] = {
    "1D": "#8B5CF6",  # Violet
    "2D": "#10B981",  # Emerald
    "3D": "#F59E0B",  # Amber
    "4D": "#06B6D4",  # Cyan
    # Extended Dimension Capsules
    "QC": "#F43F5E",  # Rose
    "AD": "#D946EF",  # Fuchsia
    "AI": "#6366F1",  # Indigo
    "VEO": "#0EA5E9",  # Sky
}

# T2 Hardening: Dimension to capsule mapping for quality checks
DIMENSION_TO_CAPSULE: Dict[str, str] = {
    "1D": "teaching.prompt.generate",
    "2D": "teaching.storyboard.create",
    "3D": "teaching.image.generate",
    "4D": "teaching.reference.analyze",
    "QC": "dimension.quality.check",
    "AD": "dimension.aesthetic.direct",
    "AI": "dimension.persona.analyze",
    "VEO": "veo.video.generate",
}

# T3 Hardening: Auteur style definitions for propagation across dimensions
AUTEUR_STYLES: Dict[str, Dict[str, str]] = {
    "bong": {
        "name": "봉준호 (Bong Joon-ho)",
        "signature": "Structural tension, genre mixing, controlled camera, cool tones",
        "palette_bias": "cool",
        "pacing": "medium",
        "camera": "controlled",
    },
    "park": {
        "name": "박찬욱 (Park Chan-wook)",
        "signature": "Symmetry, high contrast, warm colors, precise framing",
        "palette_bias": "warm",
        "pacing": "medium",
        "camera": "controlled",
    },
    "shinkai": {
        "name": "신카이 마코토 (Shinkai Makoto)",
        "signature": "Light diffusion, lyrical colors, emotional atmosphere",
        "palette_bias": "warm",
        "pacing": "slow",
        "camera": "controlled",
    },
    "lee": {
        "name": "이준호 (Lee Jun-ho)",
        "signature": "Music sync, rhythmic editing, dynamic camera",
        "palette_bias": "neutral",
        "pacing": "medium",
        "camera": "dynamic",
    },
    "na": {
        "name": "나홍진 (Na Hong-jin)",
        "signature": "Raw realism, suspense, chaotic camera, cool tones",
        "palette_bias": "cool",
        "pacing": "fast",
        "camera": "dynamic",
    },
    "hong": {
        "name": "홍상수 (Hong Sang-soo)",
        "signature": "Static camera, dialogue-driven, neutral palette",
        "palette_bias": "neutral",
        "pacing": "slow",
        "camera": "static",
    },
}


def _get_auteur_context(auteur_style: Optional[str]) -> str:
    """Build auteur context string for T3 propagation.

    Args:
        auteur_style: Auteur style key (e.g., "bong", "park")

    Returns:
        Formatted auteur context string
    """
    if not auteur_style:
        return ""

    style_key = auteur_style.lower().strip()
    auteur = AUTEUR_STYLES.get(style_key)
    if not auteur:
        return ""

    return f"""
=== Auteur Style Guide ===
Reference Director: {auteur['name']}
Visual Signature: {auteur['signature']}
Color Palette Bias: {auteur['palette_bias']}
Pacing: {auteur['pacing']}
Camera Style: {auteur['camera']}
===========================
"""


# =============================================================================
# Smart Workflow Composition
# =============================================================================

def compose_smart_workflow(
    topic: str,
    attachments: Optional[List[Dict[str, Any]]] = None,
    full_workflow: bool = False,
    style_keywords: Optional[List[str]] = None,
    user_message: Optional[str] = None,
) -> List[str]:
    """Compose an intelligent workflow based on context.

    Analyzes attachments, keywords, and user intent to determine
    the optimal sequence of dimension capsules.

    Args:
        topic: Workflow topic/concept
        attachments: Optional file attachments from user
        full_workflow: If True, include all 8 capsules strategically
        style_keywords: Optional style/quality keywords extracted from user message
        user_message: Full user message for additional context

    Returns:
        List of dimension IDs in execution order (e.g., ["4D", "1D", "2D", "3D"])
    """
    from app.agents.attachment_analyzer import AttachmentAnalyzer

    # 1. Attachment-based starting point
    if attachments:
        suggestion = AttachmentAnalyzer.analyze(attachments)
        base_dims = suggestion.dimensions
        logger.info(
            f"Attachment analysis: {suggestion.reason}",
            extra={"start": suggestion.start_dimension, "dims": base_dims}
        )
    else:
        base_dims = ["1D", "2D", "3D"]

    # 2. Full workflow: Include all strategic capsules
    if full_workflow:
        # Full pipeline: Reference(if attached) → Aesthetic → Prompt → Storyboard → Image → QC → VEO
        if attachments:
            full_dims = ["4D", "AD", "1D", "2D", "3D", "QC", "VEO"]
        else:
            full_dims = ["AD", "1D", "2D", "3D", "QC", "VEO"]
        logger.info(f"Full workflow requested: {full_dims}")
        return full_dims

    # 3. Keyword-based additions
    extended = list(base_dims)
    kw_text = topic.lower() if topic else ""  # Always include topic

    if style_keywords:
        kw_text = f"{kw_text} {' '.join(style_keywords).lower()}"
    if user_message:
        kw_text = f"{kw_text} {user_message.lower()}"

    if kw_text:
        # AD: Style/aesthetic mentions → Add at beginning
        if any(k in kw_text for k in ("스타일", "미학", "톤", "색감", "감독", "미적")):
            if "AD" not in extended:
                # Insert after 4D if present, otherwise at start
                if "4D" in extended:
                    idx = extended.index("4D") + 1
                    extended.insert(idx, "AD")
                else:
                    extended.insert(0, "AD")
                logger.debug("Added AD based on style keywords")

        # QC: Quality mentions → Add after main creative steps
        if any(k in kw_text for k in ("검수", "품질", "퀄리티", "검사", "확인")):
            if "QC" not in extended:
                extended.append("QC")
                logger.debug("Added QC based on quality keywords")

        # VEO: Video generation mentions → Add at end
        if any(k in kw_text for k in ("비디오", "영상 생성", "veo", "최종 영상", "동영상")):
            if "VEO" not in extended:
                extended.append("VEO")
                logger.debug("Added VEO based on video keywords")

        # AI (Abyss): Persona mentions → Add at beginning
        if any(k in kw_text for k in ("페르소나", "심연", "성향", "캐릭터", "분석")):
            if "AI" not in extended:
                extended.insert(0, "AI")
                logger.debug("Added AI based on persona keywords")

    logger.info(f"Composed workflow: {extended}", extra={"topic": topic[:50] if topic else ""})
    return extended


# =============================================================================
# T2 Hardening: Quality Check Integration
# =============================================================================

async def _run_quality_check(
    dimension: str,
    output: Dict[str, Any],
    model: str,
    db_context_func,
) -> Optional[int]:
    """Run quality check on dimension output.

    Args:
        dimension: Dimension ID (2D, 3D, 4D)
        output: Dimension output to check
        model: Model to use for quality check
        db_context_func: Database context function

    Returns:
        Quality score (0-100) or None if check failed
    """
    try:
        from app.services.dynamic_adapter import execute_tool_by_key
        import json

        # Prepare content for quality check
        content = ""
        content_type = "text"

        if dimension == "2D":
            # Storyboard: check scenes
            scenes = output.get("scenes", [])
            if isinstance(scenes, list):
                content = "\n".join([
                    f"Scene {i+1}: {s.get('description', '')}"
                    for i, s in enumerate(scenes) if isinstance(s, dict)
                ])
            content_type = "storyboard"
        elif dimension == "3D":
            # Image prompt
            content = output.get("prompt", "") or json.dumps(output, ensure_ascii=False)[:2000]
            content_type = "image_prompt"
        elif dimension == "4D":
            # Analysis
            content = output.get("analysis", "") or json.dumps(output, ensure_ascii=False)[:2000]
            content_type = "analysis"
        else:
            content = json.dumps(output, ensure_ascii=False)[:2000]

        if not content or len(content) < 20:
            logger.debug(f"[T2] Skipping quality check for {dimension}: insufficient content")
            return None

        # Run quality check with light criteria (aesthetic + consistency only for speed)
        async with db_context_func() as db:
            result = await execute_tool_by_key(
                tool_key="quality_check",
                inputs={
                    "content": content,
                    "content_type": content_type,
                    "criteria": ["aesthetic", "consistency"],
                },
                params={"model": model, "threshold": 70},
                db_session=db,
            )

        if result.success and result.output:
            score = result.output.get("score")
            if isinstance(score, (int, float)):
                return int(score)

        return None

    except Exception as e:
        logger.warning(f"[T2] Quality check failed for {dimension}: {e}")
        return None


async def _index_to_feedback_loop(
    capsule_id: Optional[str],
    inputs: Dict[str, Any],
    output: Dict[str, Any],
    quality_score: float,
) -> bool:
    """Index successful result to RAG feedback loop.

    Args:
        capsule_id: Capsule identifier
        inputs: Capsule inputs
        output: Capsule output
        quality_score: Quality score (0-1)

    Returns:
        True if indexed successfully
    """
    if not capsule_id:
        return False

    try:
        from app.rag.feedback_loop import index_successful_result
        return index_successful_result(
            capsule_id=capsule_id,
            inputs=inputs,
            output=output,
            quality_score=quality_score,
        )
    except ImportError:
        logger.debug("[T2] RAG feedback loop not available")
        return False
    except Exception as e:
        logger.warning(f"[T2] Feedback loop indexing failed: {e}")
        return False


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
    description="""워크플로우를 순차적으로 실행합니다. 각 차원 도구를 순서대로 호출하고 결과를 연결합니다.

사용 가능한 차원:
- 1D (Origin): Veo 프롬프트 생성
- 2D (Blueprint): 스토리보드 생성
- 3D (Ambience): 이미지 프롬프트 생성
- 4D (Moment): 레퍼런스 분석
- QC (Quality): 품질 검수 (6가지 기준)
- AD (Aesthetic): 미학 디렉터 (감독 스타일 가이드)
- AI (Abyss): 심연 해석 (페르소나 분석)
- VEO (Video): Veo 3.1 비디오 생성

dimensions를 지정하지 않으면 첨부파일/키워드 기반으로 자동 구성됩니다.
full_workflow=true 시 전체 8개 캡슐을 전략적으로 배치합니다.""",
    input_schema={
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "워크플로우 주제/컨셉 (예: '시네마틱 도시 야경')",
            },
            "dimensions": {
                "type": "array",
                "items": {"type": "string", "enum": ["1D", "2D", "3D", "4D", "QC", "AD", "AI", "VEO"]},
                "description": "실행할 차원 순서. 미지정 시 자동 구성됨.",
            },
            "full_workflow": {
                "type": "boolean",
                "description": "전체 워크플로우 실행 (모든 캡슐 포함)",
                "default": False,
            },
            "attachments": {
                "type": "array",
                "items": {"type": "object"},
                "description": "첨부파일 목록 (MIME type 기반 워크플로우 추론)",
            },
            "user_message": {
                "type": "string",
                "description": "원본 사용자 메시지 (키워드 기반 차원 추가)",
            },
            "model": {
                "type": "string",
                "description": "AI 모델 선택",
                "default": "gemini-3-flash-preview",
            },
            "style": {
                "type": "string",
                "description": "영상 스타일 (예: 'cinematic', 'anime', 'documentary')",
                "default": "cinematic",
            },
            "mood": {
                "type": "string",
                "description": "분위기 (예: 'neutral', 'dark', 'upbeat')",
                "default": "neutral",
            },
            "duration": {
                "type": "string",
                "description": "영상 길이 (예: '15 seconds', '30 seconds')",
                "default": "15 seconds",
            },
            "language": {
                "type": "string",
                "description": "출력 언어",
                "enum": ["ko", "en"],
                "default": "ko",
            },
            "scene_count": {
                "type": "integer",
                "description": "스토리보드 장면 수",
                "minimum": 1,
                "maximum": 20,
                "default": 5,
            },
            "aspect_ratio": {
                "type": "string",
                "description": "화면 비율 (예: '16:9', '9:16', '1:1')",
                "default": "16:9",
            },
            "focus_areas": {
                "type": "array",
                "items": {"type": "string"},
                "description": "4D 분석 초점 영역",
                "default": ["composition", "lighting", "color", "movement"],
            },
            "auteur_style": {
                "type": "string",
                "description": "거장 감독 스타일 참조 (T3 하드닝: 모든 차원에 스타일 전파)",
                "enum": ["bong", "park", "shinkai", "lee", "na", "hong"],
            },
            "reference_style": {
                "type": "string",
                "description": "auteur_style의 별칭 (레거시 호환)",
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

    Hardening (T2):
    - Parallel workflow isolation via per-session lock
    - Handle cleanup on workflow failure
    """
    from app.services.dynamic_adapter import execute_tool_by_key
    from app.database import get_db_context

    emitter = create_emitter(context, call)
    args = call.arguments or {}

    topic = args.get("topic", "") or ""
    dimensions = args.get("dimensions")  # None if not explicitly set
    model = args.get("model") or "gemini-3-flash-preview"
    attachments = args.get("attachments")
    full_workflow = args.get("full_workflow", False)
    user_message = args.get("user_message") or topic

    # Validate topic
    if not topic or not isinstance(topic, str):
        return error_result(call, "워크플로우 주제(topic)를 지정해주세요.")
    topic = topic.strip()
    if len(topic) < 2:
        return error_result(call, "주제는 최소 2글자 이상이어야 합니다.")

    # Smart workflow composition if dimensions not explicitly set
    if dimensions is None:
        dimensions = compose_smart_workflow(
            topic=topic,
            attachments=attachments,
            full_workflow=full_workflow,
            user_message=user_message,
        )
        logger.info(f"Auto-composed workflow: {dimensions}")

    # Validate dimensions
    if not dimensions or not isinstance(dimensions, list):
        return error_result(call, "실행할 차원을 지정해주세요.")

    # Filter valid dimensions only
    valid_dimensions = [d for d in dimensions if isinstance(d, str) and d in DIMENSION_TO_TOOL]
    if not valid_dimensions:
        return error_result(call, f"유효한 차원이 없습니다. 사용 가능: {list(DIMENSION_TO_TOOL.keys())}")

    workflow_id = str(uuid.uuid4())

    # T2-2: Acquire per-session lock to prevent parallel workflow conflicts
    session_lock = _get_workflow_lock(context.session_id)

    # Non-blocking check: if already locked, return error instead of waiting
    if session_lock.locked():
        logger.warning(f"Workflow rejected: session {context.session_id} already executing")
        return error_result(call, "이미 실행 중인 워크플로우가 있습니다. 완료 후 다시 시도해주세요.")

    # T2-1: Track handles for cleanup on failure
    created_handles: List[str] = []
    workflow_failed = False

    async with session_lock:
        _active_workflows.add(workflow_id)

        try:
            # Initialize TieredContext for this workflow
            tiered = context.state.get_or_create_tiered_context()

            # Set session-level values (persist across all steps)
            tiered.set_session_value("workflow_id", workflow_id)
            tiered.set_session_value("topic", topic)
            tiered.set_session_value("model", model)
            tiered.set_session_value("style", args.get("style", "cinematic"))
            tiered.set_session_value("mood", args.get("mood", "neutral"))
            tiered.set_session_value("duration", args.get("duration", "15 seconds"))
            tiered.set_session_value("language", args.get("language", "ko"))
            tiered.set_session_value("scene_count", args.get("scene_count", 5))
            tiered.set_session_value("aspect_ratio", args.get("aspect_ratio", "16:9"))
            # T3 Hardening: Auteur style propagation
            auteur_style = args.get("auteur_style") or args.get("reference_style")
            if auteur_style:
                tiered.set_session_value("auteur_style", auteur_style)
                logger.info(f"[T3] Auteur style set: {auteur_style}")
            tiered.set_session_value("focus_areas", args.get("focus_areas",
                ["composition", "lighting", "color", "movement"]))
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
                                # T2-1: Track handle for cleanup
                                created_handles.append(handle_ref)
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

                        # ===========================================================
                        # T2 Hardening: Quality verification loop
                        # Run quality check on content-producing dimensions
                        # ===========================================================
                        quality_score = None
                        if dim in ("2D", "3D", "4D") and output:
                            quality_score = await _run_quality_check(
                                dimension=dim,
                                output=output,
                                model=model,
                                db_context_func=get_db_context,
                            )
                            if quality_score is not None:
                                tiered.step["quality_score"] = quality_score
                                step_result["quality_score"] = quality_score
                                logger.info(f"[T2] {dim} quality score: {quality_score}")

                                # Index to RAG feedback loop if quality is high
                                if quality_score >= 70:
                                    await _index_to_feedback_loop(
                                        capsule_id=DIMENSION_TO_CAPSULE.get(dim),
                                        inputs=inputs,
                                        output=output,
                                        quality_score=quality_score / 100.0,
                                    )

                        results.append(step_result)

                        # Store output preview for history context (T1)
                        tiered.step["output_preview"] = _get_output_preview(output)

                        # Update prev_output only if output is valid dict
                        if output:
                            prev_output = output

                        emitter.emit("agent.workflow_step_complete", {
                            "step": idx + 1,
                            "dimension": dim,
                            "credit_cost": credit_cost,
                            "output_preview": _get_output_preview(output),
                            "quality_score": quality_score,
                        })
                    else:
                        error_msg = result.error or "Unknown error"
                        tiered.step["success"] = False
                        tiered.step["error"] = error_msg
                        workflow_failed = True

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
                    workflow_failed = True

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

        except Exception as e:
            # Unexpected workflow-level error
            workflow_failed = True
            logger.exception(f"Workflow {workflow_id} failed unexpectedly", extra={"error": str(e)})
            return error_result(call, f"워크플로우 실행 중 오류가 발생했습니다: {str(e)}")

        finally:
            # T2-1: Cleanup orphaned handles on workflow failure
            _active_workflows.discard(workflow_id)
            if workflow_failed and created_handles:
                cleaned = await _cleanup_handles(created_handles)
                logger.info(f"Cleaned up {cleaned}/{len(created_handles)} orphan handles for failed workflow {workflow_id}")


def _estimate_scene_count(duration_str: str) -> int:
    """duration 문자열에서 씬 수 추론 (5초당 1씬).

    Args:
        duration_str: 영상 길이 문자열 (예: "15 seconds", "1 minute", "30s")

    Returns:
        추정된 씬 수 (최소 3, 최대 20)
    """
    import re

    if not duration_str or not isinstance(duration_str, str):
        return 5  # default

    duration_lower = duration_str.lower().strip()

    # Extract numeric value
    match = re.search(r"(\d+(?:\.\d+)?)", duration_lower)
    if not match:
        return 5  # default

    seconds = float(match.group(1))

    # Convert to seconds if needed
    if "minute" in duration_lower or "min" in duration_lower:
        seconds *= 60
    elif "hour" in duration_lower or "hr" in duration_lower:
        seconds *= 3600

    # Calculate scene count (5 seconds per scene)
    scene_count = int(seconds / 5)

    # Clamp to valid range [3, 20]
    return max(3, min(20, scene_count))


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

        # P0 Gap Fix: Dynamic scene_count based on duration
        # Priority: explicit scene_count > duration-based > default 5
        scene_count = prev_output.get("scene_count")
        if not isinstance(scene_count, int) or scene_count < 1:
            # Try to estimate from duration (from 1D output or session)
            duration = prev_output.get("duration") or prev_output.get("technical", {}).get("duration")
            if duration:
                scene_count = _estimate_scene_count(str(duration))
            else:
                scene_count = 5  # default
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
        
        # Get aspect_ratio from prev_output (injected by tiered wrapper)
        aspect_ratio = prev_output.get("aspect_ratio", "16:9")
        if not isinstance(aspect_ratio, str):
            aspect_ratio = "16:9"

        return {
            "description": description,
            "style": style,
            "aspect_ratio": aspect_ratio,
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

        # Get focus_areas from prev_output (injected by tiered wrapper)
        focus_areas = prev_output.get("focus_areas",
            ["composition", "lighting", "color", "movement"])
        if not isinstance(focus_areas, list):
            focus_areas = ["composition", "lighting", "color", "movement"]

        return {
            "video_description": video_desc,
            "focus_areas": focus_areas,
        }

    # === Extended Dimension Capsules ===

    elif dimension == "QC":
        # Quality Checker - expects: content, content_type, criteria
        # Chain: 이전 출력 전체를 검증 대상으로 사용
        import json

        # 이전 출력에서 주요 콘텐츠 추출
        content = ""
        if isinstance(prev_output, dict):
            # 주요 필드 우선순위로 콘텐츠 추출
            if "prompt" in prev_output:
                content = str(prev_output["prompt"])
            elif "description" in prev_output:
                content = str(prev_output["description"])
            elif "scenes" in prev_output:
                scenes = prev_output.get("scenes", [])
                if isinstance(scenes, list):
                    content = "\n".join([
                        s.get("description", "") for s in scenes
                        if isinstance(s, dict)
                    ])
            else:
                # 전체 출력을 JSON으로
                content = json.dumps(prev_output, ensure_ascii=False, indent=2)

        if not content:
            content = topic

        # 콘텐츠 타입 추론
        content_type = "prompt"
        if "scenes" in prev_output:
            content_type = "storyboard"
        elif "image" in str(prev_output.get("style", "")):
            content_type = "image_prompt"

        return {
            "content": content[:5000],  # 최대 5000자
            "content_type": content_type,
            "criteria": ["aesthetic", "consistency", "narrative"],
        }

    elif dimension == "AD":
        # Aesthetic Director - expects: concept, reference_style, mood, target_medium
        # Chain: 이전 프롬프트/설명 → 컨셉으로 변환
        concept = topic
        if isinstance(prev_output, dict):
            concept = (
                prev_output.get("prompt") or
                prev_output.get("description") or
                prev_output.get("concept") or
                topic
            )
        if not isinstance(concept, str):
            concept = str(concept) if concept else topic

        # 무드 추출
        mood = "neutral"
        if isinstance(prev_output, dict):
            mood_val = prev_output.get("mood")
            if isinstance(mood_val, str):
                mood = mood_val

        # 스타일 추출 → reference_style로 변환
        reference_style = ""
        if isinstance(prev_output, dict):
            style_val = prev_output.get("style")
            if isinstance(style_val, str):
                reference_style = style_val
            elif isinstance(style_val, dict):
                reference_style = style_val.get("cinematography", "")

        return {
            "concept": concept[:1000],
            "reference_style": reference_style,
            "mood": mood,
            "target_medium": "video",
        }

    elif dimension == "AI":
        # Persona Analyzer (Abyss Interpreter) - expects: user_message, analysis_stage
        # Chain: 주제를 초기 자기소개로 사용
        user_message = topic
        if isinstance(prev_output, dict):
            # 이전 프롬프트를 페르소나 분석 대상으로
            desc = prev_output.get("description") or prev_output.get("prompt")
            if isinstance(desc, str) and desc.strip():
                user_message = f"다음 콘텐츠의 창작자 페르소나를 분석해줘: {desc[:500]}"

        return {
            "user_message": user_message,
            "analysis_stage": "intro",
            "persona_data": {},
            "birth_info": {},
        }

    elif dimension == "VEO":
        # Veo 3.1 Video Generator - expects: prompt, aspect_ratio, duration, style
        # Chain: 스토리보드 씬들을 영상 프롬프트로 조합
        prompt = topic

        if isinstance(prev_output, dict):
            # 스토리보드 씬 조합
            scenes = prev_output.get("scenes", [])
            if isinstance(scenes, list) and len(scenes) > 0:
                scene_descs = []
                for i, s in enumerate(scenes[:5]):  # 최대 5개 씬
                    if isinstance(s, dict):
                        desc = s.get("description", "")
                        if desc:
                            scene_descs.append(f"Scene {i+1}: {desc}")
                if scene_descs:
                    prompt = "\n".join(scene_descs)
            else:
                # 단일 프롬프트 사용
                prompt = (
                    prev_output.get("prompt") or
                    prev_output.get("description") or
                    topic
                )

        if not isinstance(prompt, str):
            prompt = str(prompt) if prompt else topic

        # 스타일 추출
        style = "cinematic"
        if isinstance(prev_output, dict):
            style_val = prev_output.get("style")
            if isinstance(style_val, str):
                style = style_val

        return {
            "prompt": prompt[:1000],
            "aspect_ratio": "16:9",
            "duration": 5,
            "style": style,
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

    **T1 Hardening**: Now includes history context from previous steps for
    quality amplification across dimension chain.

    Args:
        tiered: TieredContext instance
        dimension: Dimension ID (1D, 2D, 3D, 4D, QC, AD, AI, VEO)
        fallback_topic: Fallback topic if not in session
        prev_output: Previous step output for chaining

    Returns:
        Input dictionary for the dimension tool
    """
    # Get session-level values
    topic = tiered.get_session_value("topic", fallback_topic)
    style = tiered.get_session_value("style", "cinematic")
    mood = tiered.get_session_value("mood", "neutral")
    duration = tiered.get_session_value("duration", "15 seconds")
    language = tiered.get_session_value("language", "ko")
    scene_count = tiered.get_session_value("scene_count", 5)
    aspect_ratio = tiered.get_session_value("aspect_ratio", "16:9")
    focus_areas = tiered.get_session_value("focus_areas",
        ["composition", "lighting", "color", "movement"])

    # Merge session values into prev_output for backward compatibility
    # Session values are injected with lower priority (prev_output wins)
    enhanced_prev = dict(prev_output) if prev_output else {}
    session_defaults = {
        "style": style,
        "mood": mood,
        "duration": duration,
        "language": language,
        "scene_count": scene_count,
        "aspect_ratio": aspect_ratio,
        "focus_areas": focus_areas,
    }
    for key, value in session_defaults.items():
        if key not in enhanced_prev:
            enhanced_prev[key] = value

    # =======================================================================
    # T1 Hardening: History-based prompt enhancement
    # Extract context from previous 2 steps for quality amplification
    # =======================================================================
    history_context = _build_history_context(tiered, max_steps=2)
    if history_context:
        enhanced_prev["_history_context"] = history_context
        logger.debug(f"[T1] Injected history context for {dimension}: {len(history_context)} chars")

    # =======================================================================
    # T3 Hardening: Auteur style propagation across all dimensions
    # Inject consistent style guide to maintain visual coherence
    # =======================================================================
    auteur_style = tiered.get_session_value("auteur_style")
    if auteur_style:
        auteur_context = _get_auteur_context(auteur_style)
        if auteur_context:
            enhanced_prev["_auteur_context"] = auteur_context
            enhanced_prev["reference_style"] = auteur_style  # For AD dimension
            logger.debug(f"[T3] Injected auteur style for {dimension}: {auteur_style}")

    # Use the original function for actual input preparation
    inputs = _prepare_dimension_inputs(dimension, topic, enhanced_prev)

    return inputs


def _build_history_context(tiered: TieredContext, max_steps: int = 2) -> str:
    """Build history context from previous steps for T1 hardening.

    Extracts key information from recent steps to amplify quality in subsequent
    dimension executions.

    Args:
        tiered: TieredContext instance
        max_steps: Maximum number of previous steps to include

    Returns:
        Formatted history context string
    """
    if not tiered.history:
        return ""

    context_parts = []
    recent_steps = tiered.history[-max_steps:] if len(tiered.history) > max_steps else tiered.history

    for step in recent_steps:
        dim = step.get("dimension", "unknown")
        success = step.get("success", False)
        quality_score = step.get("quality_score")
        output_preview = step.get("output_preview", "")

        # Build step summary
        step_info = f"Previous {dim}:"
        if success:
            step_info += " [SUCCESS]"
            if quality_score is not None:
                step_info += f" Quality: {quality_score:.0f}/100"
        else:
            step_info += " [FAILED]"

        if output_preview:
            step_info += f"\n  Preview: {output_preview[:200]}"

        context_parts.append(step_info)

    if not context_parts:
        return ""

    return "\n---\n".join(context_parts)


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
