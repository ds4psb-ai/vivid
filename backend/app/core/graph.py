"""Unified StateGraph Definition.

LangGraph StateGraph 기반 통합 오케스트레이션 그래프.

2026 Best Practices:
1. Compile Once, Invoke Many - 그래프 컴파일은 비용이 높음
2. Conditional Edges - state 기반 동적 라우팅
3. Nodes as Pure Functions - 부수효과 없는 함수

Graph Structure:
    START → classify → route → retrieve → execute → generate → END
                                    ↓
                              (skip_retrieval)
                                    ↓
                              execute → generate → END

Usage:
    from app.core.graph import get_unified_graph

    # 싱글톤 그래프 조회
    graph = get_unified_graph()

    # 실행
    result = await graph.ainvoke(initial_state)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Literal, Optional

from langgraph.graph import END, StateGraph

from app.core.unified_state import UnifiedState
from app.core.nodes import (
    classify_node,
    route_node,
    retrieve_node,
    execute_node,
    generate_node,
)

logger = logging.getLogger(__name__)

# 컴파일된 그래프 캐시
_compiled_graph: Optional[Any] = None


def build_unified_graph() -> StateGraph:
    """통합 그래프 빌드.

    Returns:
        컴파일되지 않은 StateGraph 인스턴스
    """
    graph = StateGraph(UnifiedState)

    # 노드 추가
    graph.add_node("classify", classify_node)
    graph.add_node("route", route_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("execute", execute_node)
    graph.add_node("generate", generate_node)

    # 기본 엣지
    graph.add_edge("classify", "route")

    # Conditional Edge: route → retrieve 또는 execute
    graph.add_conditional_edges(
        "route",
        _should_skip_retrieval,
        {
            "retrieve": "retrieve",
            "execute": "execute",
        },
    )

    # Conditional Edge: retrieve → execute 또는 generate
    graph.add_conditional_edges(
        "retrieve",
        _should_execute_tools,
        {
            "execute": "execute",
            "generate": "generate",
        },
    )

    # Conditional Edge: execute → generate 또는 hitl_wait
    graph.add_conditional_edges(
        "execute",
        _check_hitl_required,
        {
            "generate": "generate",
            "hitl_wait": "generate",  # HITL은 별도 처리 (MVP에서는 generate로)
        },
    )

    # 최종 노드
    graph.add_edge("generate", END)

    # 시작점
    graph.set_entry_point("classify")

    return graph


def _should_skip_retrieval(state: UnifiedState) -> Literal["retrieve", "execute"]:
    """검색 스킵 여부 결정.

    skip_retrieval=True이거나 도구만 필요한 경우 execute로 직행.
    """
    if state.get("skip_retrieval", False):
        logger.info("Skipping retrieval based on query classification")
        return "execute"

    return "retrieve"


def _should_execute_tools(state: UnifiedState) -> Literal["execute", "generate"]:
    """도구 실행 필요 여부 결정.

    선택된 도구가 있으면 execute, 없으면 generate.
    """
    selected_tools = state.get("selected_tools", [])

    if selected_tools:
        logger.info(f"Executing tools: {selected_tools}")
        return "execute"

    logger.info("No tools selected, proceeding to generate")
    return "generate"


def _check_hitl_required(state: UnifiedState) -> Literal["generate", "hitl_wait"]:
    """HITL 체크포인트 필요 여부 확인.

    node_outputs에 __hitl_checkpoint가 있으면 대기.
    """
    node_outputs = state.get("node_outputs", {})

    if node_outputs.get("__hitl_checkpoint"):
        logger.info(f"HITL checkpoint: {node_outputs['__hitl_checkpoint']}")
        return "hitl_wait"

    return "generate"


def get_unified_graph() -> Any:
    """컴파일된 그래프 싱글톤 조회.

    그래프 컴파일은 비용이 높으므로 한 번만 수행합니다.

    Returns:
        컴파일된 그래프 인스턴스
    """
    global _compiled_graph

    if _compiled_graph is None:
        logger.info("Compiling unified graph...")
        graph = build_unified_graph()
        _compiled_graph = graph.compile()
        logger.info("Unified graph compiled successfully")

    return _compiled_graph


def reset_graph() -> None:
    """그래프 리셋 (테스트용).

    Warning: 프로덕션에서 사용 금지.
    """
    global _compiled_graph
    _compiled_graph = None
    logger.warning("Unified graph reset")


# =============================================================================
# Graph Visualization
# =============================================================================


def get_graph_mermaid() -> str:
    """Mermaid 다이어그램 문자열 생성.

    Returns:
        Mermaid 형식의 그래프 다이어그램
    """
    return """
graph TD
    START((START)) --> classify[classify]
    classify --> route[route]
    route -->|skip_retrieval=false| retrieve[retrieve]
    route -->|skip_retrieval=true| execute[execute]
    retrieve -->|has_tools| execute
    retrieve -->|no_tools| generate[generate]
    execute -->|no_hitl| generate
    execute -->|hitl_required| hitl_wait[hitl_wait]
    hitl_wait --> generate
    generate --> END((END))

    classDef nodeStyle fill:#f9f,stroke:#333,stroke-width:2px
    class classify,route,retrieve,execute,generate nodeStyle
"""


def print_graph_structure() -> None:
    """그래프 구조 출력 (디버깅용)."""
    print("=" * 60)
    print("Unified Graph Structure")
    print("=" * 60)
    print(get_graph_mermaid())
    print("=" * 60)


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    "build_unified_graph",
    "get_unified_graph",
    "reset_graph",
    "get_graph_mermaid",
    "print_graph_structure",
]
