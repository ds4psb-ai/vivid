"""Hybrid RAG Orchestrator.

NotebookLM (거장 DNA, Grounded RAG) + Vertex AI (실시간 검색, Google Search Grounding)
하이브리드 RAG 아키텍처 구현.

Strategy:
- 거장 쿼리: NotebookLM 우선 → Vertex AI 폴백
- 차원 쿼리: Vertex AI + Google Search Grounding
- 일반 쿼리: 병렬 실행 → 결과 병합

Usage:
    from app.rag.hybrid_rag import hybrid_query, get_hybrid_rag_service

    # 거장 DNA 쿼리 (NotebookLM 우선)
    result = await hybrid_query(
        query="봉준호 감독의 계단 상징",
        auteur_key="bong",
    )

    # 차원 쿼리 (Vertex AI + Grounding)
    result = await hybrid_query(
        query="스토리보드 제작 가이드",
        dimension="2D",
    )
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.rag.tier0_notebooklm import (
    get_notebooklm_service,
    NotebookQueryResult,
    NotebookSource,
    NOTEBOOK_REGISTRY,
)
from app.rag.tier0_vertex_rag import (
    get_vertex_rag_service,
    VertexRAGResult,
    RAGSource,
)
from app.rag.observability import trace_rag

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class HybridRAGResult:
    """하이브리드 RAG 검색 결과."""
    answer: str
    # NotebookLM 소스 (거장 DNA, grounded)
    notebooklm_sources: List[NotebookSource] = field(default_factory=list)
    # Vertex AI RAG 소스 (프라이빗 데이터)
    vertex_sources: List[RAGSource] = field(default_factory=list)
    # Google Search Grounding 소스
    grounding_sources: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    strategy_used: str = "unknown"  # "auteur_first" | "dimension" | "parallel" | "fallback"
    query_time_ms: int = 0
    # 메타데이터
    auteur_key: Optional[str] = None
    dimension: Optional[str] = None
    grounded: bool = False
    # === NEW: Reranker & Metrics ===
    reranked: bool = False
    rerank_model: Optional[str] = None
    retrieval_count: int = 0  # 검색된 문서 수
    source_scores: List[float] = field(default_factory=list)  # 각 소스의 점수


# ============================================================================
# Auteur Key Mapping
# ============================================================================

AUTEUR_KEY_TO_NOTEBOOK: Dict[str, str] = {
    # 한글 키
    "봉준호": "DNA_봉준호",
    "왕가위": "DNA_왕가위",
    "드니빌뇌브": "DNA_드니빌뇌브",
    "빌뇌브": "DNA_드니빌뇌브",
    "크리스토퍼놀란": "DNA_크리스토퍼놀란",
    "놀란": "DNA_크리스토퍼놀란",
    "쿠엔틴타란티노": "DNA_쿠엔틴타란티노",
    "타란티노": "DNA_쿠엔틴타란티노",
    "박찬욱": "DNA_박찬욱",
    "신카이": "DNA_신카이",
    # 영문 키
    "bong": "DNA_봉준호",
    "bong-joon-ho": "DNA_봉준호",
    "wong": "DNA_왕가위",
    "wong-kar-wai": "DNA_왕가위",
    "villeneuve": "DNA_드니빌뇌브",
    "denis-villeneuve": "DNA_드니빌뇌브",
    "nolan": "DNA_크리스토퍼놀란",
    "christopher-nolan": "DNA_크리스토퍼놀란",
    "tarantino": "DNA_쿠엔틴타란티노",
    "quentin-tarantino": "DNA_쿠엔틴타란티노",
    "park": "DNA_박찬욱",
    "park-chan-wook": "DNA_박찬욱",
    "shinkai": "DNA_신카이",
    "makoto-shinkai": "DNA_신카이",
}

DIMENSION_TO_CORPUS: Dict[str, str] = {
    "1D": "dim_1d_prompts",
    "2D": "dim_2d_storyboard",
    "3D": "dim_3d_imagery",
    "4D": "dim_4d_analysis",
    "AD": "auteur_dna",
    "QC": "meta_invariants",
}


# ============================================================================
# Hybrid Query Functions
# ============================================================================

@trace_rag(name="hybrid_query", tags=["rag", "hybrid"])
async def hybrid_query(
    query: str,
    auteur_key: Optional[str] = None,
    dimension: Optional[str] = None,
    use_google_search: bool = True,
) -> HybridRAGResult:
    """하이브리드 RAG 쿼리 실행.

    Strategy:
    1. auteur_key 있으면: NotebookLM 우선 → Vertex AI 폴백
    2. dimension 있으면: Vertex AI + Google Search Grounding
    3. 둘 다 없으면: 병렬 실행 → 결과 병합

    Args:
        query: 검색 쿼리
        auteur_key: 거장 키 (예: "bong", "봉준호")
        dimension: 차원 코드 (예: "1D", "2D", "AD")
        use_google_search: Google Search Grounding 사용 여부

    Returns:
        HybridRAGResult with combined answer and sources
    """
    import time
    start_time = time.monotonic()

    # 전략 결정
    if auteur_key:
        result = await _query_auteur_first(query, auteur_key, use_google_search)
    elif dimension:
        result = await _query_dimension(query, dimension, use_google_search)
    else:
        result = await _query_parallel(query, use_google_search)

    result.query_time_ms = int((time.monotonic() - start_time) * 1000)
    result.auteur_key = auteur_key
    result.dimension = dimension
    
    # Calculate retrieval count
    result.retrieval_count = (
        len(result.notebooklm_sources) + 
        len(result.vertex_sources) + 
        len(result.grounding_sources)
    )

    # Enhanced logging with metrics
    logger.info(
        f"[HybridRAG] Query completed | "
        f"strategy={result.strategy_used} | "
        f"confidence={result.confidence:.2f} | "
        f"time={result.query_time_ms}ms | "
        f"sources={result.retrieval_count} | "
        f"reranked={result.reranked}"
    )

    return result


async def _query_auteur_first(
    query: str,
    auteur_key: str,
    use_google_search: bool = True,
) -> HybridRAGResult:
    """거장 쿼리: NotebookLM 우선 → Vertex AI 폴백.

    Args:
        query: 검색 쿼리
        auteur_key: 거장 키
        use_google_search: Google Search Grounding 사용 여부

    Returns:
        HybridRAGResult
    """
    # 거장 키 → 노트북 키 변환
    notebook_key = AUTEUR_KEY_TO_NOTEBOOK.get(auteur_key.lower())
    if not notebook_key:
        logger.warning(f"[HybridRAG] Unknown auteur key: {auteur_key}")
        return await _query_parallel(query, use_google_search)

    # NotebookLM 쿼리
    notebooklm_service = get_notebooklm_service()
    notebooklm_result = await notebooklm_service.query_notebook(
        notebook_id=notebook_key,
        query=query,
    )

    # 신뢰도가 높으면 NotebookLM 결과만 사용
    if notebooklm_result.confidence >= 0.75:
        return HybridRAGResult(
            answer=notebooklm_result.answer,
            notebooklm_sources=notebooklm_result.sources,
            confidence=notebooklm_result.confidence,
            strategy_used="auteur_first",
            grounded=notebooklm_result.grounded,
        )

    # 신뢰도가 낮으면 Vertex AI로 보강
    vertex_service = get_vertex_rag_service()
    vertex_result = await vertex_service.query(
        query=f"{NOTEBOOK_REGISTRY.get(notebook_key, {}).get('description', '')} {query}",
        corpus_name="auteur_dna",
        use_grounding=use_google_search,
    )

    # 결과 병합
    combined_answer = f"{notebooklm_result.answer}\n\n---\n\n**추가 정보 (Vertex AI):**\n{vertex_result.answer}"

    return HybridRAGResult(
        answer=combined_answer,
        notebooklm_sources=notebooklm_result.sources,
        vertex_sources=vertex_result.sources,
        grounding_sources=vertex_result.grounding_sources,
        confidence=(notebooklm_result.confidence + vertex_result.confidence) / 2,
        strategy_used="auteur_first",
        grounded=True,
    )


async def _query_dimension(
    query: str,
    dimension: str,
    use_google_search: bool = True,
) -> HybridRAGResult:
    """차원별 쿼리: Vertex AI + Google Search Grounding.

    Args:
        query: 검색 쿼리
        dimension: 차원 코드
        use_google_search: Google Search Grounding 사용 여부

    Returns:
        HybridRAGResult
    """
    corpus_name = DIMENSION_TO_CORPUS.get(dimension.upper())

    vertex_service = get_vertex_rag_service()
    vertex_result = await vertex_service.query(
        query=query,
        corpus_name=corpus_name,
        use_grounding=use_google_search,
    )

    return HybridRAGResult(
        answer=vertex_result.answer,
        vertex_sources=vertex_result.sources,
        grounding_sources=vertex_result.grounding_sources,
        confidence=vertex_result.confidence,
        strategy_used="dimension",
        grounded=vertex_result.grounded,
    )


async def _query_parallel(
    query: str,
    use_google_search: bool = True,
) -> HybridRAGResult:
    """병렬 쿼리: NotebookLM + Vertex AI 동시 실행.

    Args:
        query: 검색 쿼리
        use_google_search: Google Search Grounding 사용 여부

    Returns:
        HybridRAGResult with merged results
    """
    # 병렬 실행
    notebooklm_service = get_notebooklm_service()
    vertex_service = get_vertex_rag_service()

    # AD 카테고리 노트북들 검색
    auteur_notebooks = notebooklm_service.get_notebooks_by_category("auteur")

    # 가장 관련성 높은 노트북 하나만 선택 (첫 번째)
    if auteur_notebooks:
        notebook_key = auteur_notebooks[0]
    else:
        notebook_key = "DNA_봉준호"  # 기본값

    # 병렬 실행
    notebooklm_task = notebooklm_service.query_notebook(
        notebook_id=notebook_key,
        query=query,
    )
    vertex_task = vertex_service.query(
        query=query,
        use_grounding=use_google_search,
    )

    notebooklm_result, vertex_result = await asyncio.gather(
        notebooklm_task,
        vertex_task,
        return_exceptions=True,
    )

    # 에러 처리
    if isinstance(notebooklm_result, Exception):
        logger.warning(f"[HybridRAG] NotebookLM error: {notebooklm_result}")
        notebooklm_result = None
    if isinstance(vertex_result, Exception):
        logger.warning(f"[HybridRAG] Vertex AI error: {vertex_result}")
        vertex_result = None

    # 결과 병합
    if notebooklm_result and vertex_result:
        # 둘 다 성공 → 병합
        if notebooklm_result.confidence > vertex_result.confidence:
            answer = notebooklm_result.answer
        else:
            answer = vertex_result.answer

        return HybridRAGResult(
            answer=answer,
            notebooklm_sources=notebooklm_result.sources if notebooklm_result else [],
            vertex_sources=vertex_result.sources if vertex_result else [],
            grounding_sources=vertex_result.grounding_sources if vertex_result else [],
            confidence=max(
                notebooklm_result.confidence if notebooklm_result else 0,
                vertex_result.confidence if vertex_result else 0,
            ),
            strategy_used="parallel",
            grounded=True,
        )
    elif notebooklm_result:
        return HybridRAGResult(
            answer=notebooklm_result.answer,
            notebooklm_sources=notebooklm_result.sources,
            confidence=notebooklm_result.confidence,
            strategy_used="fallback",
            grounded=notebooklm_result.grounded,
        )
    elif vertex_result:
        return HybridRAGResult(
            answer=vertex_result.answer,
            vertex_sources=vertex_result.sources,
            grounding_sources=vertex_result.grounding_sources,
            confidence=vertex_result.confidence,
            strategy_used="fallback",
            grounded=vertex_result.grounded,
        )
    else:
        return HybridRAGResult(
            answer="검색 결과를 찾을 수 없습니다.",
            confidence=0.0,
            strategy_used="fallback",
            grounded=False,
        )


# ============================================================================
# Singleton Service
# ============================================================================

class HybridRAGService:
    """하이브리드 RAG 서비스."""

    async def query(
        self,
        query: str,
        auteur_key: Optional[str] = None,
        dimension: Optional[str] = None,
        use_google_search: bool = True,
    ) -> HybridRAGResult:
        """하이브리드 RAG 쿼리 실행."""
        return await hybrid_query(
            query=query,
            auteur_key=auteur_key,
            dimension=dimension,
            use_google_search=use_google_search,
        )

    def get_available_auteurs(self) -> List[str]:
        """사용 가능한 거장 키 목록."""
        return list(set(AUTEUR_KEY_TO_NOTEBOOK.values()))

    def get_available_dimensions(self) -> List[str]:
        """사용 가능한 차원 목록."""
        return list(DIMENSION_TO_CORPUS.keys())


_hybrid_rag_service: Optional[HybridRAGService] = None


def get_hybrid_rag_service() -> HybridRAGService:
    """하이브리드 RAG 서비스 싱글톤 반환."""
    global _hybrid_rag_service
    if _hybrid_rag_service is None:
        _hybrid_rag_service = HybridRAGService()
    return _hybrid_rag_service


def reset_hybrid_rag_service() -> None:
    """서비스 리셋 (테스트용)."""
    global _hybrid_rag_service
    _hybrid_rag_service = None
