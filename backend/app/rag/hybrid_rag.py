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
from typing import Any, Dict, List, Literal, Optional, Tuple

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
from app.rag.graph_rag import graph_query as _graph_query, GraphRAGResult
from app.rag.query_expansion import expand_query as _expand_query
from app.rag.reranker import VertexReranker, DocumentToRank
from app.rag.bm25_search import (
    BM25Index,
    hybrid_search_with_rrf,
    get_dimension_bm25_index,
    FusedResult,
)
from app.rag.metrics import record_rag_query, record_rag_error, track_rag_operation
from app.rag.semantic_cache import get_semantic_cache

logger = logging.getLogger(__name__)


# ============================================================================
# Type Definitions
# ============================================================================

# PipelineHints simplified version (avoid circular import)
class PipelineHintsDict:
    """Simplified PipelineHints for hybrid_query."""
    pass


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
    strategy_used: str = "unknown"  # "auteur_first" | "dimension" | "parallel" | "fallback" | "rrf_hybrid"
    query_time_ms: int = 0
    # 메타데이터
    auteur_key: Optional[str] = None
    dimension: Optional[str] = None
    grounded: bool = False
    # === Reranker & Metrics ===
    reranked: bool = False
    rerank_model: Optional[str] = None
    retrieval_count: int = 0  # 검색된 문서 수
    source_scores: List[float] = field(default_factory=list)  # 각 소스의 점수
    # === GraphRAG ===
    graph_entities: List[Dict[str, Any]] = field(default_factory=list)
    graph_relationships: List[tuple] = field(default_factory=list)
    # === RRF Hybrid Search (Phase 1) ===
    rrf_enabled: bool = False
    keyword_results_count: int = 0
    vector_results_count: int = 0
    fused_results: List[Dict[str, Any]] = field(default_factory=list)  # RRF fused results


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
# Lightweight Query Router (2025 Best Practice)
# ============================================================================

# 최신성 판단 키워드
RECENCY_KEYWORDS = ["오늘", "최근", "2026", "현재", "뉴스", "latest", "today", "now"]


def _determine_strategy(
    query: str,
    auteur_key: Optional[str],
    dimension: Optional[str],
    use_google_search: bool,
) -> Tuple[str, bool, bool]:
    """경량 Router: 쿼리 복잡도 기반 전략 결정.
    
    LangGraph 없이 heuristic 기반으로 최적 전략 선택.
    
    Args:
        query: 검색 쿼리
        auteur_key: 거장 키
        dimension: 차원 코드
        use_google_search: Google Search 사용 여부
        
    Returns:
        Tuple of (strategy, use_reranker, force_grounding)
        - strategy: "auteur_first" | "hybrid" | "vector"
        - use_reranker: 리랭커 사용 여부
        - force_grounding: Google Grounding 강제 여부
    """
    score = 0
    
    # 길이 기반 복잡도
    if len(query) > 120:
        score += 1
    
    # 최신성 키워드
    query_lower = query.lower()
    if any(kw in query_lower for kw in RECENCY_KEYWORDS):
        score += 1
        
    # dimension 힌트 (Story, 4D는 복잡도 높음)
    if dimension and dimension.lower() in ("story", "4d"):
        score += 1
        
    # 결정 로직
    if auteur_key:
        # 거장 키 있으면 auteur_first, 복잡도에 따라 rerank/grounding
        return ("auteur_first", score >= 2, score >= 3)
    elif score >= 2:
        # 복잡한 쿼리 → hybrid + rerank
        return ("hybrid", True, score >= 3)
    else:
        # 단순 쿼리 → vector only
        return ("vector", False, use_google_search)


# ============================================================================
# Hybrid Query Functions
# ============================================================================

@trace_rag(name="hybrid_query", tags=["rag", "hybrid"])
async def hybrid_query(
    query: str,
    auteur_key: Optional[str] = None,
    dimension: Optional[str] = None,
    use_google_search: bool = True,
    strategy: Literal["vector", "graph", "hybrid"] = "vector",
    pipeline_hints: Optional[Dict[str, Any]] = None,
    use_semantic_cache: bool = True,  # NEW: Enable semantic caching
) -> HybridRAGResult:
    """하이브리드 RAG 쿼리 실행.

    Strategy Options:
    - "vector": Traditional vector similarity search (default)
    - "graph": GraphRAG entity/relationship traversal
    - "hybrid": Combine both vector and graph results

    Pipeline Hints (when provided):
    - use_expansion: bool - Enable query expansion via LLM
    - expansion_strategy: "llm" | "hyde" | "none"
    - use_reranker: bool - Enable vertex reranker
    - reranker_model: "semantic-ranker-default-v1"
    - top_k: int - Number of results to return

    Flow:
    1. Query Expansion (if hints.use_expansion)
    2. auteur_key 있으면: NotebookLM 우선 → Vertex AI 폴백
    3. dimension 있으면: Vertex AI + Google Search Grounding
    4. 둘 다 없으면: 병렬 실행 → 결과 병합
    5. strategy="graph": GraphRAG 엔티티 검색
    6. Reranking (if hints.use_reranker)

    Args:
        query: 검색 쿼리
        auteur_key: 거장 키 (예: "bong", "봉준호")
        dimension: 차원 코드 (예: "1D", "2D", "AD")
        use_google_search: Google Search Grounding 사용 여부
        strategy: 검색 전략 ("vector" | "graph" | "hybrid")
        pipeline_hints: 파이프라인 힌트 딕셔너리

    Returns:
        HybridRAGResult with combined answer and sources
    """

    import time
    start_time = time.monotonic()
    
    # === Step 0: Semantic Cache Check (90%+ hit rate) ===
    if use_semantic_cache:
        try:
            cache = get_semantic_cache()
            cached_result = await cache.get(
                query=query,
                auteur_key=auteur_key,
                dimension=dimension,
            )
            if cached_result:
                cached_result.strategy_used = "semantic_cache"
                cached_result.query_time_ms = int((time.monotonic() - start_time) * 1000)
                record_rag_query(
                    dimension=dimension or "unknown",
                    strategy="semantic_cache",
                    source_type="cache",
                    latency_ms=cached_result.query_time_ms,
                    results_count=cached_result.retrieval_count,
                    confidence=cached_result.confidence,
                    cache_hit=True,
                    auteur_key=auteur_key,
                    grounded=cached_result.grounded,
                    rrf_enabled=False,
                )
                logger.info(
                    f"[HybridRAG] SEMANTIC_CACHE HIT | "
                    f"query='{query[:50]}...' | "
                    f"confidence={cached_result.confidence:.2f}"
                )
                return cached_result
        except Exception as e:
            logger.warning(f"[HybridRAG] Semantic cache error: {e}")
    
    # === Parse Pipeline Hints ===
    hints = pipeline_hints or {}
    use_expansion = hints.get("use_expansion", False)
    expansion_strategy = hints.get("expansion_strategy", "llm")
    use_reranker = hints.get("use_reranker", False)
    reranker_model = hints.get("reranker_model", "semantic-ranker-default-v1@latest")
    top_k = hints.get("top_k", 10)
    
    # === Apply Lightweight Router (2025 Best Practice) ===
    # _determine_strategy를 통해 복잡도 기반 전략 자동 조정
    router_strategy, router_reranker, router_grounding = _determine_strategy(
        query=query,
        auteur_key=auteur_key,
        dimension=dimension,
        use_google_search=use_google_search,
    )
    
    # Router 결과 반영
    # HIGH FIX: router_strategy도 실제 strategy에 반영 (기본값일 때)
    if strategy == "vector":  # default 값이면 router 결정 사용
        # auteur_first → auteur가 있으면 auteur_first 경로로
        # hybrid → hybrid 전략 사용
        # vector → 그대로 유지
        if router_strategy == "auteur_first" and auteur_key:
            # auteur_first는 실제 hybrid를 쓰지 않고 auteur 경로로 감
            pass  # auteur_key가 있으면 자동으로 auteur 경로 선택됨
        elif router_strategy == "hybrid":
            strategy = "hybrid"  # 복잡한 쿼리 → hybrid 전략 사용
    
    if not hints.get("use_reranker"):
        use_reranker = router_reranker
    if router_grounding:
        use_google_search = True
    
    logger.debug(
        f"[HybridRAG] Router: router_strategy={router_strategy}, "
        f"effective_strategy={strategy}, reranker={use_reranker}, grounding={use_google_search}"
    )
    
    # === Step 1: Query Expansion ===
    effective_query = query
    expanded_queries: List[str] = []
    if use_expansion and strategy != "graph":
        try:
            expanded_queries = await _expand_query(
                query=query,
                strategy=expansion_strategy,
                max_expansions=3,
            )
            logger.info(f"[HybridRAG] Expanded query: {len(expanded_queries)} variations")
            # Use first expansion as effective query (original is included)
            effective_query = expanded_queries[0] if expanded_queries else query
        except Exception as e:
            logger.warning(f"[HybridRAG] Query expansion failed: {e}")
            expanded_queries = [query]

    # === Strategy: Graph-only ===

    if strategy == "graph":
        auteur_keys = [auteur_key] if auteur_key else None
        graph_result = await _graph_query(query, auteur_keys=auteur_keys)
        result = HybridRAGResult(
            answer=graph_result.answer,
            strategy_used="graph",
            graph_entities=[{"id": e.id, "type": e.type, "name": e.name} for e in graph_result.entities],
            graph_relationships=list(graph_result.relationships),
            retrieval_count=len(graph_result.entities),
        )
        result.query_time_ms = int((time.monotonic() - start_time) * 1000)
        result.auteur_key = auteur_key
        result.dimension = dimension
        return result
    
    # === Strategy: Hybrid (graph + vector) ===
    if strategy == "hybrid":
        auteur_keys = [auteur_key] if auteur_key else None
        # Run graph and vector in parallel
        graph_task = _graph_query(query, auteur_keys=auteur_keys)
        if auteur_key:
            vector_task = _query_auteur_first(query, auteur_key, use_google_search)
        elif dimension:
            vector_task = _query_dimension(query, dimension, use_google_search)
        else:
            vector_task = _query_parallel(query, use_google_search)
        
        graph_result, result = await asyncio.gather(graph_task, vector_task)
        
        # Merge graph results into vector result
        result.graph_entities = [{"id": e.id, "type": e.type, "name": e.name} for e in graph_result.entities]
        result.graph_relationships = list(graph_result.relationships)
        result.strategy_used = "hybrid"
        result.query_time_ms = int((time.monotonic() - start_time) * 1000)
        result.auteur_key = auteur_key
        result.dimension = dimension
        result.retrieval_count = (
            len(result.notebooklm_sources) + 
            len(result.vertex_sources) + 
            len(result.grounding_sources) +
            len(graph_result.entities)
        )
        return result

    # === Strategy: Vector (default) ===
    if auteur_key:
        result = await _query_auteur_first(query, auteur_key, use_google_search, dimension=dimension or "AD")
    elif dimension:
        result = await _query_dimension(query, dimension, use_google_search)
    else:
        result = await _query_parallel(query, use_google_search, dimension="general")

    result.query_time_ms = int((time.monotonic() - start_time) * 1000)
    result.auteur_key = auteur_key
    result.dimension = dimension
    
    # Calculate retrieval count
    result.retrieval_count = (
        len(result.notebooklm_sources) + 
        len(result.vertex_sources) + 
        len(result.grounding_sources)
    )
    
    # === Step N: Reranking ===
    if use_reranker and result.retrieval_count > 0:
        try:
            reranker = VertexReranker(model=reranker_model)
            
            # Prepare documents for reranking
            docs_to_rerank: List[DocumentToRank] = []
            
            # Add NotebookLM sources
            for src in result.notebooklm_sources:
                docs_to_rerank.append(DocumentToRank(
                    id=f"nlm_{src.source_id}",
                    content=src.text[:1000],  # Truncate for reranker
                    metadata={"source": "notebooklm"}
                ))
            
            # Add Vertex sources
            for src in result.vertex_sources:
                docs_to_rerank.append(DocumentToRank(
                    id=f"vtx_{src.source_id}",
                    content=src.text[:1000],
                    metadata={"source": "vertex"}
                ))
            
            if docs_to_rerank:
                rerank_result = await reranker.rerank(
                    query=effective_query,
                    documents=docs_to_rerank,
                    top_k=min(top_k, len(docs_to_rerank))
                )
                
                # Update result metadata
                result.reranked = True
                result.rerank_model = reranker_model
                result.source_scores = [doc.score for doc in rerank_result.documents]
                
                logger.info(
                    f"[HybridRAG] Reranked {len(docs_to_rerank)} docs | "
                    f"top_score={rerank_result.documents[0].score if rerank_result.documents else 0:.3f}"
                )
        except Exception as e:
            logger.warning(f"[HybridRAG] Reranking failed: {e}")

    # Enhanced logging with metrics
    logger.info(
        f"[HybridRAG] Query completed | "
        f"strategy={result.strategy_used} | "
        f"confidence={result.confidence:.2f} | "
        f"time={result.query_time_ms}ms | "
        f"sources={result.retrieval_count} | "
        f"reranked={result.reranked}"
    )
    
    # Record Prometheus metrics
    source_type = "notebooklm" if result.notebooklm_sources else (
        "vertex" if result.vertex_sources else "grounding"
    )
    record_rag_query(
        dimension=dimension or "unknown",
        strategy=result.strategy_used,
        source_type=source_type,
        latency_ms=result.query_time_ms,
        results_count=result.retrieval_count,
        confidence=result.confidence,
        cache_hit=False,
        auteur_key=result.auteur_key,
        grounded=result.grounded,
        rrf_enabled=result.rrf_enabled,
    )

    # === CRAG Pattern: Corrective RAG (2025 Best Practice) ===
    # If confidence is low, automatically trigger Google Search Grounding as fallback
    CRAG_CONFIDENCE_THRESHOLD = 0.5
    if result.confidence < CRAG_CONFIDENCE_THRESHOLD and not result.grounding_sources:
        logger.info(
            f"[HybridRAG] CRAG triggered | confidence={result.confidence:.2f} < {CRAG_CONFIDENCE_THRESHOLD} | "
            f"Falling back to Google Search Grounding"
        )
        try:
            from app.rag.tier0_vertex_rag import query_with_google_grounding
            
            grounding_result = await query_with_google_grounding(
                query=query,
                model="gemini-2.0-flash",
            )
            
            if grounding_result and hasattr(grounding_result, 'sources'):
                # Merge grounding sources into result
                result.grounding_sources.extend(grounding_result.sources)
                result.retrieval_count += len(grounding_result.sources)
                
                # Boost confidence if we got good grounding results
                if len(grounding_result.sources) > 0:
                    result.confidence = min(result.confidence + 0.2, 0.9)
                    result.grounded = True
                    
                    # Append grounding answer if primary answer is weak
                    if len(result.answer) < 100 and grounding_result.answer:
                        result.answer = f"{result.answer}\n\n[Grounding 보완]\n{grounding_result.answer}"
                
                logger.info(
                    f"[HybridRAG] CRAG success | "
                    f"grounding_sources={len(grounding_result.sources)} | "
                    f"new_confidence={result.confidence:.2f}"
                )
        except Exception as e:
            logger.warning(f"[HybridRAG] CRAG grounding failed: {e}")

    # === Step N+1: Store in Semantic Cache (high confidence only) ===
    if use_semantic_cache and result.confidence >= 0.5:
        try:
            cache = get_semantic_cache()
            await cache.set(
                query=query,
                response=result,
                auteur_key=auteur_key,
                dimension=dimension,
            )
            logger.debug(
                f"[HybridRAG] Cached result | "
                f"confidence={result.confidence:.2f}"
            )
        except Exception as e:
            logger.warning(f"[HybridRAG] Cache storage failed: {e}")

    return result


@track_rag_operation("auteur_first")
async def _query_auteur_first(
    query: str,
    auteur_key: str,
    use_google_search: bool = True,
    dimension: str = "AD",  # Medium fix: for correct metric labeling
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
        # LOW FIX: dimension 전달하여 메트릭에서 "general" 대신 실제 dimension 기록
        return await _query_parallel(query, use_google_search, dimension=dimension)

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


@track_rag_operation("dimension_query")
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


@track_rag_operation("parallel_query")
async def _query_parallel(
    query: str,
    use_google_search: bool = True,
    dimension: str = "general",  # Medium fix: for correct metric labeling
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

    async def rrf_query(
        self,
        query: str,
        dimension: Optional[str] = None,
        use_bm25: bool = True,
        use_vector: bool = True,
        rrf_k: int = 60,
        top_k: int = 10,
    ) -> HybridRAGResult:
        """BM25 + 벡터 검색 RRF 융합 쿼리.
        
        Args:
            query: 검색 쿼리
            dimension: 차원 코드 (예: "1D", "AD")
            use_bm25: BM25 키워드 검색 사용
            use_vector: 벡터 시맨틱 검색 사용
            rrf_k: RRF 상수 (높을수록 상위 결과 보정 약화)
            top_k: 반환할 최대 결과 수
            
        Returns:
            HybridRAGResult with RRF fused results
        """
        import time
        start_time = time.monotonic()
        
        keyword_results = []
        vector_results = []
        
        # BM25 키워드 검색
        if use_bm25 and dimension:
            try:
                bm25_index = get_dimension_bm25_index(dimension)
                if bm25_index.size > 0:
                    bm25_results = bm25_index.search(query, top_k=top_k * 2)
                    keyword_results = [
                        {"id": r.id, "text": r.text, "score": r.score}
                        for r in bm25_results
                    ]
                    logger.info(f"[RRF] BM25 returned {len(keyword_results)} results")
            except Exception as e:
                logger.warning(f"[RRF] BM25 search failed: {e}")
        
        # 벡터 시맨틱 검색
        if use_vector:
            try:
                vertex_service = get_vertex_rag_service()
                corpus_name = DIMENSION_TO_CORPUS.get(dimension.upper()) if dimension else None
                vertex_result = await vertex_service.query(
                    query=query,
                    corpus_name=corpus_name,
                    use_grounding=False,  # RRF에서는 grounding 비활성화
                )
                vector_results = [
                    {"id": src.source_id, "text": src.text, "score": src.score}
                    for src in vertex_result.sources
                ]
                logger.info(f"[RRF] Vector returned {len(vector_results)} results")
            except Exception as e:
                logger.warning(f"[RRF] Vector search failed: {e}")
        
        # RRF 융합
        fused_results = []
        if keyword_results or vector_results:
            from app.rag.bm25_search import reciprocal_rank_fusion
            
            result_lists = []
            if keyword_results:
                result_lists.append(keyword_results)
            if vector_results:
                result_lists.append(vector_results)
            
            fused = reciprocal_rank_fusion(result_lists, k=rrf_k)
            fused_results = [
                {
                    "id": f.id,
                    "text": f.text,
                    "rrf_score": f.rrf_score,
                    "keyword_score": f.keyword_score,
                    "vector_score": f.vector_score,
                }
                for f in fused[:top_k]
            ]
        
        # 결과 생성
        query_time_ms = int((time.monotonic() - start_time) * 1000)
        
        # 답변 생성 (상위 결과 기반)
        if fused_results:
            context = "\n".join([f["text"][:500] for f in fused_results[:3]])
            answer = f"검색 결과 {len(fused_results)}건을 찾았습니다.\n\n{context[:1000]}"
        else:
            answer = "검색 결과를 찾을 수 없습니다."
        
        return HybridRAGResult(
            answer=answer,
            strategy_used="rrf_hybrid",
            query_time_ms=query_time_ms,
            dimension=dimension,
            retrieval_count=len(fused_results),
            rrf_enabled=True,
            keyword_results_count=len(keyword_results),
            vector_results_count=len(vector_results),
            fused_results=fused_results,
            confidence=fused_results[0]["rrf_score"] if fused_results else 0.0,
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

