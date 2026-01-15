"""
P5: Direct LLM - Skip Retrieval Path.

단순 쿼리에 대해 검색을 생략하고 LLM의 파라메트릭 지식으로 직접 응답합니다.

When to Use:
    - QueryType.SIMPLE_FACTUAL: "Python이란?", "HTTP 200 의미"
    - QueryType.CREATIVE: "영화 시놉시스 써줘" (선택적)

Benefits:
    - 지연 시간 감소: ~200ms → ~100ms
    - 비용 절감: $0.005 → $0.001
    - 불필요한 검색 제거

Usage:
    from app.rag.direct_llm import direct_llm_response

    result = await direct_llm_response(
        query="Python이란?",
        query_type=QueryType.SIMPLE_FACTUAL,
    )
"""
from __future__ import annotations

import logging
import time
from typing import Optional

from app.rag.query_classifier import QueryType

logger = logging.getLogger(__name__)


# ============================================================================
# System Prompts by QueryType
# ============================================================================

SYSTEM_PROMPTS = {
    QueryType.SIMPLE_FACTUAL: """You are a helpful assistant answering factual questions.
Provide clear, concise, and accurate answers based on your training knowledge.
If you're uncertain about something, indicate that clearly.
Format your response in a readable way with bullet points if appropriate.""",
    QueryType.CREATIVE: """You are a creative writing assistant for film and storytelling.
Help users with their creative requests such as:
- Writing synopses, dialogue, or character descriptions
- Brainstorming ideas for films, stories, or scenes
- Suggesting names, titles, or concepts

Be creative, engaging, and helpful. Match the tone and style requested by the user.""",
}


# ============================================================================
# Direct LLM Response Function
# ============================================================================


async def direct_llm_response(
    query: str,
    query_type: QueryType = QueryType.SIMPLE_FACTUAL,
    model_name: str = "gemini-2.0-flash",
    max_tokens: int = 1024,
    temperature: Optional[float] = None,
) -> "DirectLLMResult":
    """검색 없이 LLM 직접 응답 생성.

    Args:
        query: 사용자 쿼리
        query_type: 쿼리 유형 (프롬프트 선택에 사용)
        model_name: Gemini 모델 ID
        max_tokens: 최대 토큰 수
        temperature: 생성 온도 (None이면 유형별 기본값)

    Returns:
        DirectLLMResult with answer and metadata
    """
    start = time.time()

    try:
        import google.generativeai as genai

        model = genai.GenerativeModel(model_name)

        # Get system prompt for query type
        system_prompt = SYSTEM_PROMPTS.get(
            query_type,
            SYSTEM_PROMPTS[QueryType.SIMPLE_FACTUAL],
        )

        # Set temperature based on query type
        if temperature is None:
            temperature = 0.7 if query_type == QueryType.CREATIVE else 0.3

        # Build prompt
        full_prompt = f"{system_prompt}\n\nUser Query: {query}"

        # Generate response
        response = await model.generate_content_async(
            full_prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )

        latency_ms = int((time.time() - start) * 1000)

        logger.info(
            f"[DirectLLM] Generated response for '{query[:30]}...' "
            f"(type={query_type.value}, latency={latency_ms}ms)"
        )

        return DirectLLMResult(
            answer=response.text,
            query_type=query_type,
            model=model_name,
            latency_ms=latency_ms,
            skip_retrieval=True,
            confidence=0.9,  # High confidence for direct LLM
        )

    except Exception as e:
        logger.error(f"[DirectLLM] Generation failed: {e}")
        latency_ms = int((time.time() - start) * 1000)

        return DirectLLMResult(
            answer="",
            query_type=query_type,
            model=model_name,
            latency_ms=latency_ms,
            skip_retrieval=True,
            confidence=0.0,
            error=str(e),
        )


# ============================================================================
# Result Dataclass
# ============================================================================

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class DirectLLMResult:
    """Direct LLM 응답 결과.

    HybridRAGResult와 호환 가능한 필드 구조.
    """

    answer: str
    query_type: QueryType
    model: str
    latency_ms: int
    skip_retrieval: bool = True
    confidence: float = 0.9
    error: Optional[str] = None

    # HybridRAGResult 호환 필드 (빈 값)
    notebooklm_sources: List[Any] = field(default_factory=list)
    vertex_sources: List[Any] = field(default_factory=list)
    grounding_sources: List[Dict[str, Any]] = field(default_factory=list)
    strategy_used: str = "direct_llm"
    query_time_ms: int = 0
    auteur_key: Optional[str] = None
    dimension: Optional[str] = None
    grounded: bool = False
    reranked: bool = False
    rerank_model: Optional[str] = None
    retrieval_count: int = 0
    source_scores: List[float] = field(default_factory=list)
    graph_entities: List[Dict[str, Any]] = field(default_factory=list)
    graph_relationships: List[tuple] = field(default_factory=list)
    rrf_enabled: bool = False
    keyword_results_count: int = 0
    vector_results_count: int = 0
    fused_results: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Set query_time_ms from latency_ms."""
        self.query_time_ms = self.latency_ms

    def to_hybrid_result(self) -> "HybridRAGResult":
        """HybridRAGResult로 변환."""
        from app.rag.hybrid_rag import HybridRAGResult

        return HybridRAGResult(
            answer=self.answer,
            notebooklm_sources=self.notebooklm_sources,
            vertex_sources=self.vertex_sources,
            grounding_sources=self.grounding_sources,
            confidence=self.confidence,
            strategy_used=self.strategy_used,
            query_time_ms=self.query_time_ms,
            auteur_key=self.auteur_key,
            dimension=self.dimension,
            grounded=self.grounded,
            reranked=self.reranked,
            rerank_model=self.rerank_model,
            retrieval_count=self.retrieval_count,
            source_scores=self.source_scores,
            graph_entities=self.graph_entities,
            graph_relationships=self.graph_relationships,
            rrf_enabled=self.rrf_enabled,
            keyword_results_count=self.keyword_results_count,
            vector_results_count=self.vector_results_count,
            fused_results=self.fused_results,
        )


# ============================================================================
# Mock Direct LLM (for testing)
# ============================================================================


class MockDirectLLM:
    """테스트용 Mock Direct LLM."""

    def __init__(self):
        self.call_count = 0
        self.last_query: Optional[str] = None

    async def generate(
        self,
        query: str,
        query_type: QueryType = QueryType.SIMPLE_FACTUAL,
    ) -> DirectLLMResult:
        """Mock 응답 생성."""
        self.call_count += 1
        self.last_query = query

        return DirectLLMResult(
            answer=f"[Mock Response for: {query[:50]}]",
            query_type=query_type,
            model="mock-model",
            latency_ms=50,
            skip_retrieval=True,
            confidence=0.85,
        )


# Global mock instance for testing
_mock_direct_llm: Optional[MockDirectLLM] = None


def set_mock_direct_llm(mock: Optional[MockDirectLLM]) -> None:
    """Mock Direct LLM 설정 (테스트용)."""
    global _mock_direct_llm
    _mock_direct_llm = mock


async def direct_llm_response_or_mock(
    query: str,
    query_type: QueryType = QueryType.SIMPLE_FACTUAL,
    **kwargs,
) -> DirectLLMResult:
    """Direct LLM 또는 Mock 사용."""
    if _mock_direct_llm is not None:
        return await _mock_direct_llm.generate(query, query_type)
    return await direct_llm_response(query, query_type, **kwargs)
