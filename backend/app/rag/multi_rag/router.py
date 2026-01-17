"""Intelligent RAG Router (P0 2026).

쿼리 분석 기반 최적 RAG 소스 선택.

Strategy:
    1. Rule-based Pre-filtering: 키워드, 컨텍스트 기반 빠른 필터링
    2. LLM-assisted Selection: 복잡한 쿼리에 대해 LLM으로 소스 선택
    3. Hybrid: Rule-based → LLM fallback

Reference:
    - RAGRouter Paper (3.61% improvement): https://arxiv.org/abs/2505.23052
    - LlamaIndex Router: https://docs.llamaindex.ai/en/stable/examples/low_level/router/

Usage:
    from app.rag.multi_rag.router import IntelligentRAGRouter

    router = IntelligentRAGRouter(registry)
    decision = await router.route(
        query="봉준호 감독의 계단 연출 분석",
        context={"auteur_key": "bong", "dimension": "4D"},
    )
"""
from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.rag.multi_rag.registry import RAGSourceRegistry
from app.rag.multi_rag.types import (
    QueryContext,
    RAGSourceSpec,
    RAGSourceType,
    RouteDecision,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Routing Rules
# =============================================================================

# Auteur 키워드 (거장 DNA 소스 선택 트리거)
AUTEUR_KEYWORDS = {
    "봉준호", "bong", "기생충", "살인의추억", "옥자", "괴물", "마더",
    "왕가위", "wong", "화양연화", "중경삼림", "아비정전",
    "놀란", "nolan", "인셉션", "인터스텔라", "다크나이트", "테넷",
    "타란티노", "tarantino", "펄프픽션", "킬빌",
    "드니빌뇌브", "villeneuve", "듄", "도착", "블레이드러너",
    "박찬욱", "park", "올드보이", "친절한금자씨",
    "신카이", "shinkai", "너의이름은", "날씨의아이",
}

# 차원 키워드 (차원별 지식 소스 선택 트리거)
DIMENSION_KEYWORDS = {
    "1D": {"프롬프트", "prompt", "텍스트", "text", "스크립트", "script"},
    "2D": {"스토리보드", "storyboard", "컷", "shot", "장면구성"},
    "3D": {"이미지", "image", "비주얼", "visual", "사진", "photo"},
    "4D": {"분석", "analysis", "레퍼런스", "reference", "해석", "구도", "조명"},
    "AD": {"미학", "aesthetic", "스타일", "style", "연출"},
    "STORY": {"스토리", "story", "시나리오", "scenario", "서사", "narrative"},
    "VEO": {"비디오", "video", "영상", "동영상"},
}

# 사용자 히스토리 키워드 (과거 작업 참조 트리거)
USER_HISTORY_KEYWORDS = {
    "이전", "previous", "지난번", "last time", "비슷한", "similar",
    "다시", "again", "같은", "same", "과거", "history",
}

# 템플릿 키워드 (워크플로우 템플릿 참조 트리거)
TEMPLATE_KEYWORDS = {
    "템플릿", "template", "워크플로우", "workflow", "튜토리얼", "tutorial",
    "가이드", "guide", "방법", "how to", "절차", "process",
}


# =============================================================================
# Intelligent Router
# =============================================================================

class IntelligentRAGRouter:
    """지능형 RAG 라우터.

    쿼리와 컨텍스트를 분석하여 최적의 RAG 소스를 선택합니다.

    Routing Strategy:
        1. Rule-based Pre-filtering
           - 키워드 매칭
           - 컨텍스트 기반 부스트 (auteur_key, dimension)
           - Priority 기반 정렬

        2. LLM-assisted Selection (복잡 쿼리용)
           - 후보 소스가 max_sources 초과 시
           - LLM으로 최종 선택

    Attributes:
        registry: RAG 소스 레지스트리
        llm_client: LLM 클라이언트 (선택적)
        max_sources: 최대 선택 소스 수
        llm_threshold: LLM 선택 트리거 후보 수

    Example:
        >>> router = IntelligentRAGRouter(registry, llm_client=gemini)
        >>> decision = await router.route(
        ...     query="봉준호 계단 연출",
        ...     context={"auteur_key": "bong"},
        ...     max_sources=3,
        ... )
        >>> print(decision.selected_sources)
        ["notebooklm_bong", "qdrant_4d"]
    """

    def __init__(
        self,
        registry: RAGSourceRegistry,
        llm_client: Optional[Any] = None,
        max_sources: int = 3,
        llm_threshold: int = 5,
    ) -> None:
        """라우터 초기화.

        Args:
            registry: RAG 소스 레지스트리
            llm_client: LLM 클라이언트 (선택적, generate 메서드 필요)
            max_sources: 기본 최대 선택 소스 수
            llm_threshold: LLM 선택 트리거 후보 수 임계값
        """
        self.registry = registry
        self.llm_client = llm_client
        self.max_sources = max_sources
        self.llm_threshold = llm_threshold

    async def route(
        self,
        query: str,
        context: Optional[QueryContext] = None,
        max_sources: Optional[int] = None,
    ) -> RouteDecision:
        """쿼리 라우팅.

        Args:
            query: 검색 쿼리
            context: 추가 컨텍스트 (auteur_key, dimension, user_id 등)
            max_sources: 최대 선택 소스 수 (기본값 사용 시 None)

        Returns:
            RouteDecision with selected sources and reasoning
        """
        ctx = context or {}
        max_src = max_sources or self.max_sources

        # 1. Rule-based pre-filtering
        candidates = self._prefilter(query, ctx)

        if not candidates:
            logger.warning(f"[RAGRouter] No candidates found for query: {query[:50]}...")
            return RouteDecision(
                selected_sources=[],
                reasoning="No matching sources found",
                confidence=0.0,
                estimated_latency_ms=0,
                routing_strategy="rule_based",
            )

        # 2. LLM selection (if needed)
        routing_strategy = "rule_based"
        if len(candidates) > max_src and self.llm_client:
            try:
                candidates = await self._llm_select(query, ctx, candidates, max_src)
                routing_strategy = "llm_assisted"
            except Exception as e:
                logger.warning(f"[RAGRouter] LLM selection failed: {e}, using top candidates")
                candidates = candidates[:max_src]
                routing_strategy = "rule_based_fallback"
        else:
            candidates = candidates[:max_src]

        # 3. Build decision
        selected_ids = [c[0].source_id for c in candidates]
        reasoning = self._build_reasoning(candidates, ctx)
        confidence = self._calculate_confidence(candidates)
        latency = max(c[0].latency_ms_avg for c in candidates) if candidates else 0

        logger.info(
            f"[RAGRouter] Route completed | "
            f"query='{query[:50]}...' | "
            f"sources={selected_ids} | "
            f"strategy={routing_strategy} | "
            f"confidence={confidence:.2f}"
        )

        return RouteDecision(
            selected_sources=selected_ids,
            reasoning=reasoning,
            confidence=confidence,
            estimated_latency_ms=latency,
            routing_strategy=routing_strategy,
        )

    # =========================================================================
    # Rule-based Pre-filtering
    # =========================================================================

    def _prefilter(
        self,
        query: str,
        context: QueryContext,
    ) -> List[Tuple[RAGSourceSpec, float]]:
        """규칙 기반 사전 필터링.

        Args:
            query: 검색 쿼리
            context: 추가 컨텍스트

        Returns:
            (RAGSourceSpec, score) 튜플 리스트 (점수 내림차순)
        """
        sources = self.registry.get_healthy_sources()
        query_lower = query.lower()

        candidates: List[Tuple[RAGSourceSpec, float]] = []

        for source in sources:
            score = self._calculate_source_score(source, query_lower, context)
            if score > 0:
                candidates.append((source, score))

        # 점수 내림차순 → priority 내림차순
        candidates.sort(key=lambda x: (-x[1], -x[0].priority))

        return candidates

    def _calculate_source_score(
        self,
        source: RAGSourceSpec,
        query_lower: str,
        context: QueryContext,
    ) -> float:
        """소스별 점수 계산.

        Scoring Rules:
            - 소스 키워드 매칭: +1 per match
            - Auteur 컨텍스트 + AUTEUR_DNA 타입: +5
            - Dimension 컨텍스트 + 해당 차원: +3
            - User ID + USER_HISTORY 타입: +2
            - Auteur 키워드 감지: +2
            - Dimension 키워드 감지: +2
            - User history 키워드 감지: +1
            - Template 키워드 감지: +1
            - 기본 priority 반영: +priority/10
        """
        score = 0.0

        # 1. 소스 키워드 매칭
        for keyword in source.keywords:
            if keyword.lower() in query_lower:
                score += 1.0

        # 2. 컨텍스트 기반 부스트
        auteur_key = context.get("auteur_key", "").lower()
        dimension = context.get("dimension", "").upper()
        user_id = context.get("user_id")

        # Auteur 컨텍스트 매칭
        if auteur_key and source.source_type == RAGSourceType.AUTEUR_DNA:
            if not source.auteur_keys or auteur_key in [a.lower() for a in source.auteur_keys]:
                score += 5.0

        # Dimension 컨텍스트 매칭
        if dimension and source.source_type == RAGSourceType.DIMENSION_KNOWLEDGE:
            if not source.dimensions or dimension in [d.upper() for d in source.dimensions]:
                score += 3.0

        # User ID 컨텍스트 매칭
        if user_id and source.source_type == RAGSourceType.USER_HISTORY:
            score += 2.0

        # 3. 쿼리 키워드 기반 타입 매칭
        # Auteur 키워드 감지
        if any(kw.lower() in query_lower for kw in AUTEUR_KEYWORDS):
            if source.source_type == RAGSourceType.AUTEUR_DNA:
                score += 2.0

        # Dimension 키워드 감지
        for dim, keywords in DIMENSION_KEYWORDS.items():
            if any(kw.lower() in query_lower for kw in keywords):
                if source.source_type == RAGSourceType.DIMENSION_KNOWLEDGE:
                    if not source.dimensions or dim in source.dimensions:
                        score += 2.0
                        break

        # User history 키워드 감지
        if any(kw.lower() in query_lower for kw in USER_HISTORY_KEYWORDS):
            if source.source_type == RAGSourceType.USER_HISTORY:
                score += 1.0

        # Template 키워드 감지
        if any(kw.lower() in query_lower for kw in TEMPLATE_KEYWORDS):
            if source.source_type == RAGSourceType.TEMPLATE_WORKFLOW:
                score += 1.0

        # 4. Priority 반영 (0.1-1.0)
        score += source.priority / 10.0

        return score

    # =========================================================================
    # LLM-assisted Selection
    # =========================================================================

    async def _llm_select(
        self,
        query: str,
        context: QueryContext,
        candidates: List[Tuple[RAGSourceSpec, float]],
        max_sources: int,
    ) -> List[Tuple[RAGSourceSpec, float]]:
        """LLM 기반 소스 선택.

        Args:
            query: 검색 쿼리
            context: 컨텍스트
            candidates: 후보 소스 목록
            max_sources: 최대 선택 수

        Returns:
            선택된 소스 목록
        """
        if not self.llm_client:
            return candidates[:max_sources]

        prompt = self._build_selection_prompt(query, context, candidates, max_sources)

        response = await self.llm_client.generate(prompt)
        selected_ids = self._parse_selection_response(response)

        # 선택된 ID로 후보 필터링
        selected = [
            (spec, score) for spec, score in candidates
            if spec.source_id in selected_ids
        ]

        # 선택되지 않은 경우 fallback
        if not selected:
            logger.warning("[RAGRouter] LLM selected no valid sources, using top candidates")
            return candidates[:max_sources]

        return selected

    def _build_selection_prompt(
        self,
        query: str,
        context: QueryContext,
        candidates: List[Tuple[RAGSourceSpec, float]],
        max_sources: int,
    ) -> str:
        """LLM 선택 프롬프트 생성."""
        sources_desc = "\n".join(
            f"- {spec.source_id}: {spec.display_name} ({spec.source_type.value})\n"
            f"  설명: {spec.description}\n"
            f"  키워드: {', '.join(spec.keywords[:5])}"
            for spec, _ in candidates[:10]  # 최대 10개만
        )

        return f"""사용자 쿼리: {query}

컨텍스트:
- Dimension: {context.get('dimension', 'N/A')}
- Auteur: {context.get('auteur_key', 'N/A')}
- User ID: {context.get('user_id', 'N/A')}

사용 가능한 지식 소스:
{sources_desc}

이 쿼리에 가장 적합한 지식 소스를 {max_sources}개 선택하세요.
JSON 형식으로 source_id 목록만 반환: ["source_1", "source_2"]"""

    def _parse_selection_response(self, response: str) -> List[str]:
        """LLM 응답 파싱."""
        try:
            # JSON 배열 추출
            import re
            match = re.search(r'\[.*?\]', response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            logger.warning(f"[RAGRouter] Failed to parse LLM response: {e}")
        return []

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _build_reasoning(
        self,
        candidates: List[Tuple[RAGSourceSpec, float]],
        context: QueryContext,
    ) -> str:
        """선택 이유 문자열 생성."""
        if not candidates:
            return "No sources matched"

        reasons = []

        for spec, score in candidates[:3]:
            type_name = spec.source_type.value
            reasons.append(f"{spec.display_name}({type_name}, score={score:.1f})")

        ctx_parts = []
        if context.get("auteur_key"):
            ctx_parts.append(f"auteur={context['auteur_key']}")
        if context.get("dimension"):
            ctx_parts.append(f"dim={context['dimension']}")

        ctx_str = f" [{', '.join(ctx_parts)}]" if ctx_parts else ""

        return f"Selected: {', '.join(reasons)}{ctx_str}"

    def _calculate_confidence(
        self,
        candidates: List[Tuple[RAGSourceSpec, float]],
    ) -> float:
        """선택 신뢰도 계산.

        신뢰도 = min(0.95, top_score / 10)
        - 최고 점수 10 이상: 0.95
        - 최고 점수 5: 0.50
        - 최고 점수 1: 0.10
        """
        if not candidates:
            return 0.0

        top_score = candidates[0][1]
        return min(0.95, top_score / 10.0)


# =============================================================================
# Factory Function
# =============================================================================

def create_router(
    registry: Optional[RAGSourceRegistry] = None,
    llm_client: Optional[Any] = None,
) -> IntelligentRAGRouter:
    """라우터 팩토리 함수.

    Args:
        registry: RAG 소스 레지스트리 (없으면 글로벌 사용)
        llm_client: LLM 클라이언트 (선택적)

    Returns:
        IntelligentRAGRouter 인스턴스
    """
    from app.rag.multi_rag.registry import get_registry

    reg = registry or get_registry()
    return IntelligentRAGRouter(reg, llm_client=llm_client)
