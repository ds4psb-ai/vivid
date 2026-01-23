"""Execution Node - 통합 실행기.

3개 실행 오케스트레이터를 통합:
1. app/workflow/executor.py - HITL Workflow Executor
2. app/agents/orchestrator.py - Agent Orchestrator
3. app/services/capsule_executor.py - Capsule Executor

실행 흐름:
1. 선택된 도구 실행 (순차/병렬)
2. HITL 체크포인트 처리
3. 결과 통합

Usage:
    from app.core.nodes.execute import execute_node

    result_state = await execute_node(state)
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from app.core.unified_schemas import (
    CheckpointAction,
    Dimension,
    Intent,
    OrchestrationPattern,
)
from app.core.unified_state import UnifiedState

logger = logging.getLogger(__name__)


async def execute_node(state: UnifiedState) -> UnifiedState:
    """실행 노드.

    선택된 도구를 실행하고 결과를 상태에 저장합니다.

    Args:
        state: 현재 상태 (selected_tools, pattern 필수)

    Returns:
        업데이트된 상태 (node_outputs, execution_order)
    """
    start_time = time.perf_counter()

    tools = state.get("selected_tools", [])
    pattern = state.get("pattern", OrchestrationPattern.DIRECT)
    intent = state.get("intent", Intent.UNKNOWN)

    # 도구 없으면 스킵
    if not tools:
        logger.info("No tools to execute, skipping execution node")
        return state

    try:
        # 패턴에 따른 실행
        if pattern == OrchestrationPattern.PARALLEL:
            node_outputs, execution_order = await _execute_parallel(state, tools)
        elif pattern == OrchestrationPattern.LINEAR:
            node_outputs, execution_order = await _execute_linear(state, tools)
        elif pattern == OrchestrationPattern.HITL_LOOP:
            node_outputs, execution_order = await _execute_with_hitl(state, tools)
        else:  # DIRECT or CONDITIONAL
            node_outputs, execution_order = await _execute_direct(state, tools)

        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Execution complete: {len(execution_order)} tools, "
            f"pattern={pattern.value}, latency={latency_ms:.1f}ms"
        )

        # 상태 업데이트
        return {
            **state,
            "node_outputs": {**state.get("node_outputs", {}), **node_outputs},
            "execution_order": state.get("execution_order", []) + execution_order,
            "current_node": execution_order[-1] if execution_order else state.get("current_node", ""),
        }

    except Exception as e:
        logger.error(f"Execution failed: {e}")
        return {
            **state,
            "error": str(e),
        }


async def _execute_direct(
    state: UnifiedState,
    tools: List[str],
) -> tuple[Dict[str, Any], List[str]]:
    """직접 실행 (단일 도구).

    첫 번째 도구만 실행합니다.
    """
    if not tools:
        return {}, []

    tool = tools[0]
    output = await _execute_single_tool(state, tool)

    return {tool: output}, [tool]


async def _execute_linear(
    state: UnifiedState,
    tools: List[str],
) -> tuple[Dict[str, Any], List[str]]:
    """순차 실행 (파이프라인).

    도구를 순서대로 실행하며, 이전 결과를 다음 입력으로 전달합니다.
    """
    node_outputs = {}
    execution_order = []
    current_state = state

    for tool in tools:
        try:
            output = await _execute_single_tool(current_state, tool)
            node_outputs[tool] = output
            execution_order.append(tool)

            # 다음 도구를 위해 상태 업데이트
            current_state = {
                **current_state,
                "node_outputs": {**current_state.get("node_outputs", {}), tool: output},
            }

        except Exception as e:
            logger.error(f"Tool {tool} failed: {e}")
            node_outputs[tool] = {"error": str(e)}
            # 실패 시 중단
            break

    return node_outputs, execution_order


async def _execute_parallel(
    state: UnifiedState,
    tools: List[str],
) -> tuple[Dict[str, Any], List[str]]:
    """병렬 실행 (fan-out).

    모든 도구를 동시에 실행합니다.
    """
    tasks = {tool: _execute_single_tool(state, tool) for tool in tools}

    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    node_outputs = {}
    execution_order = []

    for tool, result in zip(tasks.keys(), results):
        if isinstance(result, Exception):
            logger.error(f"Tool {tool} failed: {result}")
            node_outputs[tool] = {"error": str(result)}
        else:
            node_outputs[tool] = result
        execution_order.append(tool)

    return node_outputs, execution_order


async def _execute_with_hitl(
    state: UnifiedState,
    tools: List[str],
) -> tuple[Dict[str, Any], List[str]]:
    """HITL 루프 실행.

    각 도구 실행 후 HITL 체크포인트를 설정합니다.
    """
    node_outputs = {}
    execution_order = []
    current_state = state

    for tool in tools:
        # 도구 실행
        output = await _execute_single_tool(current_state, tool)
        node_outputs[tool] = output
        execution_order.append(tool)

        # HITL 필요 여부 확인
        if await _requires_hitl(tool, output):
            # 체크포인트 설정
            checkpoint_id = f"hitl_{tool}_{int(time.time())}"
            return {
                **node_outputs,
                "__hitl_checkpoint": checkpoint_id,
                "__hitl_tool": tool,
            }, execution_order

        # 다음 도구를 위해 상태 업데이트
        current_state = {
            **current_state,
            "node_outputs": {**current_state.get("node_outputs", {}), tool: output},
        }

    return node_outputs, execution_order


async def _execute_single_tool(
    state: UnifiedState,
    tool_id: str,
) -> Dict[str, Any]:
    """단일 도구 실행.

    Args:
        state: 현재 상태
        tool_id: 도구 ID (Dimension 코드)

    Returns:
        도구 실행 결과
    """
    query = state.get("query", "")
    auteur_key = state.get("auteur_key")
    retrieved_docs = state.get("retrieved_docs", [])

    # RAG 컨텍스트 구성
    context = _build_context(retrieved_docs)

    try:
        # Dimension 도구 매핑
        dimension_handlers = {
            "1D": _execute_prompt_generator,
            "2D": _execute_storyboard_creator,
            "3D": _execute_image_generator,
            "4D": _execute_reference_analyzer,
            "QC": _execute_quality_checker,
            "AD": _execute_aesthetic_director,
            "AI": _execute_abyss_interpreter,
            "VEO": _execute_veo_generator,
            "STORY": _execute_story_architect,
            "SOUND": _execute_sound_crafter,
        }

        handler = dimension_handlers.get(tool_id)
        if handler:
            return await handler(query, context, auteur_key)

        logger.warning(f"Unknown tool: {tool_id}")
        return {"error": f"Unknown tool: {tool_id}"}

    except Exception as e:
        logger.error(f"Tool {tool_id} execution failed: {e}")
        return {"error": str(e)}


def _build_context(retrieved_docs: List[Dict[str, Any]]) -> str:
    """검색된 문서로 컨텍스트 구성."""
    if not retrieved_docs:
        return ""

    context_parts = []
    for i, doc in enumerate(retrieved_docs[:10], 1):
        content = doc.get("content", "")
        source = doc.get("source", "unknown")
        context_parts.append(f"[{i}] ({source})\n{content}")

    return "\n\n---\n\n".join(context_parts)


async def _requires_hitl(tool_id: str, output: Dict[str, Any]) -> bool:
    """HITL 필요 여부 확인.

    특정 도구나 결과에 대해 인간 검토가 필요한지 결정합니다.
    """
    # HITL이 필요한 도구 목록
    hitl_required_tools = {"QC", "2D", "STORY"}

    if tool_id in hitl_required_tools:
        return True

    # 결과에 따른 HITL 판단
    if output.get("confidence", 1.0) < 0.7:
        return True

    return False


# =============================================================================
# Dimension Tool Handlers (Stub implementations)
# =============================================================================


async def _execute_prompt_generator(
    query: str,
    context: str,
    auteur_key: Optional[str],
) -> Dict[str, Any]:
    """1D - 프롬프트 생성."""
    try:
        from app.dimension_adapter import run_prompt_generate

        result = await run_prompt_generate(
            topic=query,
            style_hint=context,
            auteur_key=auteur_key,
        )
        return {"output": result, "tool": "1D"}
    except ImportError:
        return {"output": f"[Stub] 프롬프트 생성: {query}", "tool": "1D"}


async def _execute_storyboard_creator(
    query: str,
    context: str,
    auteur_key: Optional[str],
) -> Dict[str, Any]:
    """2D - 스토리보드 생성."""
    try:
        from app.dimension_adapter import run_storyboard_create

        result = await run_storyboard_create(
            topic=query,
            style_hint=context,
            auteur_key=auteur_key,
        )
        return {"output": result, "tool": "2D"}
    except ImportError:
        return {"output": f"[Stub] 스토리보드 생성: {query}", "tool": "2D"}


async def _execute_image_generator(
    query: str,
    context: str,
    auteur_key: Optional[str],
) -> Dict[str, Any]:
    """3D - 이미지 생성."""
    try:
        from app.dimension_adapter import run_image_generate

        result = await run_image_generate(
            prompt=query,
            style_hint=context,
            auteur_key=auteur_key,
        )
        return {"output": result, "tool": "3D"}
    except ImportError:
        return {"output": f"[Stub] 이미지 생성: {query}", "tool": "3D"}


async def _execute_reference_analyzer(
    query: str,
    context: str,
    auteur_key: Optional[str],
) -> Dict[str, Any]:
    """4D - 레퍼런스 분석."""
    try:
        from app.dimension_adapter import run_reference_analyze

        result = await run_reference_analyze(
            query=query,
            context=context,
            auteur_key=auteur_key,
        )
        return {"output": result, "tool": "4D"}
    except ImportError:
        return {"output": f"[Stub] 레퍼런스 분석: {query}", "tool": "4D"}


async def _execute_quality_checker(
    query: str,
    context: str,
    auteur_key: Optional[str],
) -> Dict[str, Any]:
    """QC - 퀄리티 체크."""
    try:
        from app.dimension_adapter import run_quality_check

        result = await run_quality_check(
            content=query,
            criteria=context,
        )
        return {"output": result, "tool": "QC"}
    except ImportError:
        return {"output": f"[Stub] 퀄리티 체크: {query}", "tool": "QC"}


async def _execute_aesthetic_director(
    query: str,
    context: str,
    auteur_key: Optional[str],
) -> Dict[str, Any]:
    """AD - 미학 디렉터."""
    try:
        from app.dimension_adapter import run_aesthetic_direct

        result = await run_aesthetic_direct(
            content=query,
            style_hint=context,
            auteur_key=auteur_key,
        )
        return {"output": result, "tool": "AD"}
    except ImportError:
        return {"output": f"[Stub] 미학 분석: {query}", "tool": "AD"}


async def _execute_abyss_interpreter(
    query: str,
    context: str,
    auteur_key: Optional[str],
) -> Dict[str, Any]:
    """AI - 심연의 거울 (페르소나 분석)."""
    try:
        from app.dimension_adapter import run_abyss_interpret

        result = await run_abyss_interpret(
            content=query,
            context=context,
        )
        return {"output": result, "tool": "AI"}
    except ImportError:
        return {"output": f"[Stub] 페르소나 분석: {query}", "tool": "AI"}


async def _execute_veo_generator(
    query: str,
    context: str,
    auteur_key: Optional[str],
) -> Dict[str, Any]:
    """VEO - 비디오 생성."""
    try:
        from app.dimension_adapter import run_veo_generate

        result = await run_veo_generate(
            prompt=query,
            style_hint=context,
            auteur_key=auteur_key,
        )
        return {"output": result, "tool": "VEO"}
    except ImportError:
        return {"output": f"[Stub] 비디오 생성: {query}", "tool": "VEO"}


async def _execute_story_architect(
    query: str,
    context: str,
    auteur_key: Optional[str],
) -> Dict[str, Any]:
    """STORY - 스토리 아키텍트."""
    try:
        from app.dimension_adapter import run_story_create

        result = await run_story_create(
            topic=query,
            context=context,
            auteur_key=auteur_key,
        )
        return {"output": result, "tool": "STORY"}
    except ImportError:
        return {"output": f"[Stub] 스토리 생성: {query}", "tool": "STORY"}


async def _execute_sound_crafter(
    query: str,
    context: str,
    auteur_key: Optional[str],
) -> Dict[str, Any]:
    """SOUND - 사운드 크래프터."""
    try:
        from app.dimension_adapter import run_sound_craft

        result = await run_sound_craft(
            description=query,
            context=context,
            auteur_key=auteur_key,
        )
        return {"output": result, "tool": "SOUND"}
    except ImportError:
        return {"output": f"[Stub] 사운드 생성: {query}", "tool": "SOUND"}


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    "execute_node",
]
