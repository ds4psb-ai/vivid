"""Routing Node - 통합 라우터.

5개 라우팅 시스템을 통합:
1. app/rag/router/intelligent_router.py - 지능형 라우터
2. app/rag/personalized_router.py - 개인화 라우터
3. app/rag/strategy_selector.py - 전략 선택기
4. app/rag/semantic_router.py (routing part) - 시맨틱 라우터
5. app/workflow/dag_builder.py (routing part) - DAG 라우터

결정 사항:
- selected_sources: 검색할 소스 (notebooklm, qdrant, vertex, web)
- selected_tools: 사용할 도구 (dimension 앱들)
- strategy: 검색 전략
- pattern: 오케스트레이션 패턴

Usage:
    from app.core.nodes.route import route_node

    result_state = await route_node(state)
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from app.core.unified_schemas import (
    Dimension,
    Intent,
    OrchestrationPattern,
    QueryType,
    QUERY_TYPE_STRATEGY_MAP,
    INTENT_PATTERN_MAP,
)
from app.core.unified_state import UnifiedState, state_with_routing

logger = logging.getLogger(__name__)


# 소스 선택 규칙
SOURCE_SELECTION_RULES = {
    QueryType.SIMPLE_FACTUAL: [],  # 검색 생략
    QueryType.CREATIVE: ["qdrant"],  # 최소 검색
    QueryType.DOMAIN_SPECIFIC: ["notebooklm", "qdrant"],  # 앙상블
    QueryType.RECENCY_REQUIRED: ["web", "qdrant"],  # 웹 우선
    QueryType.MULTI_HOP: ["notebooklm", "qdrant", "vertex"],  # 전체
    QueryType.AMBIGUOUS: ["notebooklm", "qdrant"],  # 안전한 기본값
}

# 도구 선택 규칙 (Intent → Dimension 매핑)
TOOL_SELECTION_RULES = {
    Intent.GENERATE: ["1D", "3D", "VEO"],  # 프롬프트, 이미지, 비디오
    Intent.ANALYZE: ["4D", "AD", "AI"],    # 레퍼런스, 미학, 페르소나
    Intent.CREATE: ["2D", "STORY"],        # 스토리보드, 스토리
    Intent.VALIDATE: ["QC"],               # 퀄리티 체크
    Intent.WORKFLOW: [],                   # DAG 빌더가 결정
    Intent.CHAT: [],                       # 도구 불필요
    Intent.UNKNOWN: [],
}


async def route_node(state: UnifiedState) -> UnifiedState:
    """라우팅 노드.

    QueryType과 Intent를 기반으로 소스와 도구를 선택합니다.

    Args:
        state: 현재 상태 (query_type, intent 필수)

    Returns:
        업데이트된 상태 (selected_sources, selected_tools, strategy, pattern)
    """
    start_time = time.perf_counter()

    query_type = state.get("query_type", QueryType.AMBIGUOUS)
    intent = state.get("intent", Intent.UNKNOWN)
    dimension = state.get("dimension")
    auteur_key = state.get("auteur_key")
    query = state.get("query", "")

    try:
        # 1. 소스 선택
        selected_sources = await _select_sources(
            query_type=query_type,
            dimension=dimension,
            auteur_key=auteur_key,
            query=query,
        )

        # 2. 도구 선택
        selected_tools = await _select_tools(
            intent=intent,
            dimension=dimension,
            query=query,
        )

        # 3. 전략 결정
        strategy = QUERY_TYPE_STRATEGY_MAP.get(query_type, "ensemble_rrf")

        # 4. 패턴 결정
        pattern = _determine_pattern(intent, selected_tools)

        # 5. 서브쿼리 분해 (multi-hop인 경우)
        sub_queries = []
        if query_type == QueryType.MULTI_HOP:
            sub_queries = await _decompose_query(query)

        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Routing complete: sources={selected_sources}, "
            f"tools={selected_tools}, strategy={strategy}, "
            f"pattern={pattern.value}, latency={latency_ms:.1f}ms"
        )

        return state_with_routing(
            state,
            selected_sources=selected_sources,
            selected_tools=selected_tools,
            strategy=strategy,
            pattern=pattern,
            sub_queries=sub_queries,
        )

    except Exception as e:
        logger.error(f"Routing failed: {e}")
        # 실패 시 안전한 기본값
        return state_with_routing(
            state,
            selected_sources=["qdrant"],
            selected_tools=[],
            strategy="ensemble_rrf",
            pattern=OrchestrationPattern.DIRECT,
            sub_queries=[],
        )


async def _select_sources(
    *,
    query_type: QueryType,
    dimension: Optional[Dimension],
    auteur_key: Optional[str],
    query: str,
) -> List[str]:
    """검색 소스 선택.

    규칙 기반 + 기존 라우터 결합.
    """
    # 기본 규칙
    base_sources = SOURCE_SELECTION_RULES.get(query_type, ["qdrant"])

    # Dimension 기반 조정
    if dimension:
        # 4D, AD는 NotebookLM 우선
        if dimension in [Dimension.MOMENT, Dimension.AESTHETIC]:
            if "notebooklm" not in base_sources:
                base_sources = ["notebooklm"] + base_sources

    # Auteur 기반 조정
    if auteur_key:
        # 거장 지정 시 NotebookLM 필수
        if "notebooklm" not in base_sources:
            base_sources = ["notebooklm"] + base_sources

    # 기존 라우터 시도
    try:
        from app.rag.router.intelligent_router import route_query

        router_result = await route_query(query)
        if router_result and router_result.sources:
            # 기존 라우터 결과와 병합
            for source in router_result.sources:
                if source not in base_sources:
                    base_sources.append(source)
    except (ImportError, Exception) as e:
        logger.debug(f"Intelligent router not available: {e}")

    return base_sources


async def _select_tools(
    *,
    intent: Intent,
    dimension: Optional[Dimension],
    query: str,
) -> List[str]:
    """도구 선택.

    Intent와 Dimension 기반으로 적절한 도구 선택.
    """
    # 명시적 Dimension이 있으면 해당 도구만
    if dimension:
        return [dimension.value]

    # Intent 기반 선택
    base_tools = TOOL_SELECTION_RULES.get(intent, [])

    # 쿼리 기반 추가 도구 감지
    query_lower = query.lower()

    # 특정 키워드로 도구 추가
    keyword_tool_map = {
        ("프롬프트", "prompt"): "1D",
        ("스토리보드", "storyboard", "씬"): "2D",
        ("이미지", "image", "그림"): "3D",
        ("레퍼런스", "reference", "분석"): "4D",
        ("퀄리티", "quality", "체크"): "QC",
        ("미학", "aesthetic", "스타일"): "AD",
        ("페르소나", "persona", "캐릭터"): "AI",
        ("비디오", "video", "영상", "veo"): "VEO",
        ("스토리", "story", "시나리오"): "STORY",
        ("사운드", "sound", "음악"): "SOUND",
    }

    for keywords, tool in keyword_tool_map.items():
        if any(kw in query_lower for kw in keywords):
            if tool not in base_tools:
                base_tools.append(tool)

    return base_tools


def _determine_pattern(intent: Intent, tools: List[str]) -> OrchestrationPattern:
    """오케스트레이션 패턴 결정."""
    # 기본 패턴
    base_pattern = INTENT_PATTERN_MAP.get(intent, OrchestrationPattern.DIRECT)

    # 도구 수에 따른 조정
    if len(tools) > 2:
        return OrchestrationPattern.LINEAR  # 여러 도구는 순차 실행
    if len(tools) == 0:
        return OrchestrationPattern.DIRECT  # 도구 없으면 직접 응답

    return base_pattern


async def _decompose_query(query: str) -> List[str]:
    """복합 쿼리를 서브쿼리로 분해.

    Multi-hop 쿼리에 대해 단계별 서브쿼리 생성.
    """
    # 간단한 규칙 기반 분해
    # TODO: LLM 기반 분해로 업그레이드

    sub_queries = []

    # "왜" 질문 분해
    if "왜" in query or "why" in query.lower():
        # 1. 사실 확인
        # 2. 원인 분석
        sub_queries.append(query.replace("왜", "").replace("?", "").strip() + "에 대해 설명해주세요")
        sub_queries.append(f"위 내용의 원인과 이유를 분석해주세요")

    # "vs" 비교 분해
    elif "vs" in query.lower() or "비교" in query:
        parts = query.lower().replace("비교", "").split("vs")
        if len(parts) == 2:
            sub_queries.append(f"{parts[0].strip()}에 대해 설명해주세요")
            sub_queries.append(f"{parts[1].strip()}에 대해 설명해주세요")
            sub_queries.append("위 두 가지를 비교해주세요")

    return sub_queries


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    "route_node",
]
