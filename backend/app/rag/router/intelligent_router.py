"""Intelligent RAG Router.

쿼리를 분석하고 최적의 RAG 소스를 선택하는 지능형 라우터.

2단계 Hybrid Approach:
1. Rule-based Pre-filter (빠름, 확실한 케이스)
2. LLM-based Selection (복잡한 쿼리용)

References:
    - LlamaIndex RouterQueryEngine + LLMSingleSelector
    - LangChain classify_query + route_to_agents
    - RAGRouter Paper (arxiv.org/abs/2505.23052)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.rag.router.registry import RAGSourceRegistry
from app.rag.router.types import (
    QueryIntent,
    RAGSourceSpec,
    RAGSourceType,
    RouteDecision,
    AUTEUR_KEYWORDS,
    HISTORY_KEYWORDS,
    TREND_KEYWORDS,
    get_default_sources_for_dimension,
)

logger = logging.getLogger(__name__)


class IntelligentRAGRouter:
    """지능형 RAG 라우터 - 2단계 Hybrid Approach.

    1. Rule-based Pre-filter: 키워드, 컨텍스트 기반 빠른 필터링
    2. LLM-based Selection: 복잡한 쿼리에 대한 LLM 기반 선택
    """

    def __init__(
        self,
        registry: RAGSourceRegistry,
        llm_client: Any = None,
    ) -> None:
        """Initialize router.

        Args:
            registry: RAG 소스 레지스트리
            llm_client: LLM 클라이언트 (Gemini)
        """
        self.registry = registry
        self.llm = llm_client
        self._use_llm = llm_client is not None

    async def route(
        self,
        query: str,
        context: dict[str, Any] | None = None,
        max_sources: int = 3,
    ) -> RouteDecision:
        """쿼리를 분석하고 최적의 RAG 소스 선택.

        Args:
            query: 사용자 쿼리
            context: 추가 컨텍스트 (dimension, auteur_key, user_id 등)
            max_sources: 최대 선택 소스 수

        Returns:
            RouteDecision with selected sources
        """
        context = context or {}
        sources = self.registry.get_enabled_sources()

        if not sources:
            logger.warning("[RAGRouter] No enabled sources")
            return RouteDecision(
                selected_sources=[],
                query_intent=QueryIntent.GENERAL,
                reasoning="No sources available",
            )

        # 1. Rule-based Pre-filtering
        candidates, intent = self._prefilter(query, context, sources)
        logger.debug(
            f"[RAGRouter] Pre-filter: {len(candidates)} candidates, intent={intent}"
        )

        # 2. LLM-based Selection (복잡한 쿼리용)
        sub_queries: dict[str, str] = {}
        reasoning = "Rule-based selection"

        if self._use_llm and len(candidates) > max_sources:
            try:
                candidates, sub_queries, reasoning = await self._llm_select(
                    query, context, candidates, max_sources
                )
            except Exception as e:
                logger.warning(f"[RAGRouter] LLM selection failed: {e}")
                # Fallback to priority-based selection
                candidates = sorted(
                    candidates, key=lambda s: -s.priority
                )[:max_sources]
                reasoning = "Fallback to priority-based (LLM failed)"

        # 최종 선택
        selected = candidates[:max_sources]

        # 각 소스에 대한 sub-query 생성 (없으면 원본 쿼리)
        for source in selected:
            if source.source_id not in sub_queries:
                sub_queries[source.source_id] = query

        return RouteDecision(
            selected_sources=[s.source_id for s in selected],
            query_intent=intent,
            sub_queries=sub_queries,
            reasoning=reasoning,
            confidence=self._calculate_confidence(selected, intent),
            estimated_latency_ms=max(
                (s.latency_ms_avg for s in selected), default=500
            ),
        )

    def _prefilter(
        self,
        query: str,
        context: dict[str, Any],
        sources: list[RAGSourceSpec],
    ) -> tuple[list[RAGSourceSpec], QueryIntent]:
        """규칙 기반 사전 필터링.

        Returns:
            (filtered_sources, inferred_intent)
        """
        candidates: list[tuple[RAGSourceSpec, float]] = []
        query_lower = query.lower()
        intent = QueryIntent.GENERAL

        # Intent 추론
        if any(kw in query_lower for kw in AUTEUR_KEYWORDS):
            intent = QueryIntent.STYLE_REFERENCE
        elif any(kw in query_lower for kw in HISTORY_KEYWORDS):
            intent = QueryIntent.HISTORY_RECALL
        elif any(kw in query_lower for kw in TREND_KEYWORDS):
            intent = QueryIntent.TREND_ANALYSIS
        elif any(kw in query_lower for kw in ["어떻게", "how", "방법", "만들"]):
            intent = QueryIntent.TECHNICAL_HOW
        elif any(kw in query_lower for kw in ["아이디어", "idea", "영감", "창작"]):
            intent = QueryIntent.CREATIVE_IDEA

        for source in sources:
            score = 0.0

            # 1. 키워드 매칭
            for kw in source.keywords:
                if kw.lower() in query_lower:
                    score += 1.0

            # 2. 컨텍스트 기반 부스트
            if context.get("auteur_key"):
                if source.source_type == RAGSourceType.AUTEUR_DNA:
                    score += 3.0

            if context.get("dimension"):
                dimension = context["dimension"]
                default_types = get_default_sources_for_dimension(dimension)
                if source.source_type in default_types:
                    score += 2.0

            if context.get("user_id"):
                if source.source_type == RAGSourceType.USER_HISTORY:
                    score += 1.0

            # 3. Intent 기반 부스트
            if intent == QueryIntent.STYLE_REFERENCE:
                if source.source_type == RAGSourceType.AUTEUR_DNA:
                    score += 2.0
            elif intent == QueryIntent.HISTORY_RECALL:
                if source.source_type == RAGSourceType.USER_HISTORY:
                    score += 2.0
            elif intent == QueryIntent.TREND_ANALYSIS:
                if source.source_type == RAGSourceType.TREND_DATA:
                    score += 2.0

            # 4. Priority 기반 기본 점수
            score += source.priority * 0.1

            if score > 0:
                candidates.append((source, score))

        # Fallback: 점수 없으면 모든 소스
        if not candidates:
            candidates = [(s, s.priority * 0.1) for s in sources]

        # 점수순 정렬
        candidates.sort(key=lambda x: -x[1])
        return [c[0] for c in candidates], intent

    async def _llm_select(
        self,
        query: str,
        context: dict[str, Any],
        candidates: list[RAGSourceSpec],
        max_sources: int,
    ) -> tuple[list[RAGSourceSpec], dict[str, str], str]:
        """LLM 기반 소스 선택.

        Returns:
            (selected_sources, sub_queries, reasoning)
        """
        prompt = f"""사용자 쿼리를 분석하고 최적의 지식 소스를 선택하세요.

쿼리: {query}

컨텍스트:
- Dimension: {context.get('dimension', 'N/A')}
- Auteur: {context.get('auteur_key', 'N/A')}
- User ID: {context.get('user_id', 'N/A')}

사용 가능한 지식 소스:
{self._format_sources(candidates)}

최대 {max_sources}개 소스를 선택하고, 각 소스에 최적화된 sub-query를 생성하세요.

JSON 형식으로 응답:
{{
    "selections": [
        {{"source_id": "소스ID", "sub_query": "최적화된 쿼리", "relevance": 0.9}}
    ],
    "reasoning": "선택 이유"
}}
"""

        response = await self.llm.generate(prompt)
        parsed = self._parse_llm_response(response)

        # 선택된 소스 추출
        selected_ids = [s["source_id"] for s in parsed.get("selections", [])]
        sub_queries = {
            s["source_id"]: s.get("sub_query", query)
            for s in parsed.get("selections", [])
        }
        reasoning = parsed.get("reasoning", "LLM-based selection")

        selected = [c for c in candidates if c.source_id in selected_ids]

        # 선택 없으면 상위 후보
        if not selected:
            selected = candidates[:max_sources]

        return selected, sub_queries, reasoning

    def _format_sources(self, sources: list[RAGSourceSpec]) -> str:
        """LLM 프롬프트용 소스 포맷."""
        lines = []
        for s in sources:
            lines.append(
                f"- {s.source_id} ({s.source_type.value}): {s.description}"
            )
        return "\n".join(lines)

    def _parse_llm_response(self, response: str) -> dict[str, Any]:
        """LLM 응답 파싱."""
        try:
            # JSON 블록 추출
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("[RAGRouter] Failed to parse LLM response")
            return {}

    def _calculate_confidence(
        self,
        selected: list[RAGSourceSpec],
        intent: QueryIntent,
    ) -> float:
        """선택 신뢰도 계산."""
        if not selected:
            return 0.0

        # 기본 신뢰도
        confidence = 0.5

        # Intent가 명확하면 +0.2
        if intent != QueryIntent.GENERAL:
            confidence += 0.2

        # 고우선순위 소스 선택 시 +0.2
        if any(s.priority >= 8 for s in selected):
            confidence += 0.2

        # 소스 수 기반 조정
        if len(selected) == 1:
            confidence += 0.1  # 확실한 선택

        return min(confidence, 1.0)


# =============================================================================
# Factory Function
# =============================================================================


def create_intelligent_router(
    registry: RAGSourceRegistry | None = None,
    llm_client: Any = None,
) -> IntelligentRAGRouter:
    """IntelligentRAGRouter 생성 팩토리.

    Args:
        registry: RAG 소스 레지스트리 (없으면 전역 사용)
        llm_client: LLM 클라이언트

    Returns:
        IntelligentRAGRouter 인스턴스
    """
    if registry is None:
        from app.rag.router.registry import get_rag_registry

        registry = get_rag_registry()

    return IntelligentRAGRouter(registry, llm_client)
