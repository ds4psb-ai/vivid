"""Hybrid RAG Orchestrator.

NotebookLM (거장 DNA, Grounded RAG) + Qdrant (차원별 지식)
하이브리드 RAG 아키텍처 구현.

Strategy:
- 거장 쿼리: NotebookLM (Tier 0)
- 차원 쿼리: Qdrant Hybrid (Tier 1)
- 일반 쿼리: NotebookLM → Qdrant 폴백

Usage:
    from app.rag.hybrid_rag import hybrid_query, get_hybrid_rag_service

    # 거장 DNA 쿼리 (NotebookLM)
    result = await hybrid_query(
        query="봉준호 감독의 계단 상징",
        auteur_key="bong",
    )

    # 차원 쿼리 (Qdrant Hybrid)
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


# RAGSource for backward compatibility (previously from tier0_vertex_rag)
@dataclass
class RAGSource:
    """RAG 검색 소스 (backward compat)."""
    source_id: str = ""
    content: str = ""
    relevance_score: float = 0.0
    document_name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

from app.rag.observability import trace_rag
from app.rag.graph_rag import graph_query as _graph_query, GraphRAGResult
from app.rag.query_expansion import expand_query as _expand_query
from app.rag.rerankers import get_reranker, DocumentToRerank
# P0.5: Application-level BM25 deprecated in favor of Qdrant Native Sparse
# See: tier1_dimension_rag.hybrid_search() for new implementation
from app.rag.metrics import record_rag_query, record_rag_error, track_rag_operation, log_router_decision
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
    # === P6: Feedback Tracking ===
    response_id: Optional[str] = None  # UUID string for feedback linking
    query_type: Optional[str] = None  # P5 classification result
    classification_confidence: Optional[float] = None
    retrieval_skipped: bool = False
    crag_triggered: bool = False


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
# P1: Dataset-Level Routing (2026-01-13)
# ============================================================================

import re
from app.rag.manifest_loader import YAMLManifest, get_manifest


def _select_datasets(
    query: str,
    manifest: YAMLManifest,
) -> List[str]:
    """P1: 입력 쿼리 기반으로 dataset 선택.
    
    Same dimension 내에서 1~2개 dataset만 선택하여 검색 범위 축소.
    
    Args:
        query: 검색 쿼리
        manifest: 앱 매니페스트 (dataset_candidates, dataset_selection_rules 포함)
        
    Returns:
        선택된 dataset_id 목록 (최대 max_datasets개)
    """
    if not manifest.dataset_candidates:
        return []  # Dataset routing 미사용
    
    selected = []
    query_lower = query.lower()
    
    # 규칙 기반 매칭
    for pattern, datasets in manifest.dataset_selection_rules.items():
        try:
            if re.search(pattern, query_lower):
                selected.extend(datasets)
        except re.error as e:
            logger.warning(f"[DatasetRouter] Invalid regex pattern '{pattern}': {e}")
    
    # 중복 제거 + 제한
    selected = list(dict.fromkeys(selected))[:manifest.max_datasets]
    
    # Fallback: 매칭 없으면 기본값 (psych_core 또는 첫 번째 후보)
    if not selected:
        fallback = manifest.default_dataset or (
            manifest.dataset_candidates[0] if manifest.dataset_candidates else None
        )
        if fallback:
            selected = [fallback]
            logger.info(f"[DatasetRouter] No rules matched, using fallback: {fallback}")
    
    logger.info(
        f"[DatasetRouter] Selected datasets: {selected} | "
        f"query: '{query[:50]}...' | candidates: {manifest.dataset_candidates}"
    )
    
    return selected


def _apply_dataset_filter(
    metadata_filters: Dict[str, Any],
    selected_datasets: List[str],
) -> Dict[str, Any]:
    """P1: Qdrant 필터에 dataset_id 조건 추가.
    
    Args:
        metadata_filters: 기존 메타데이터 필터
        selected_datasets: 선택된 dataset_id 목록
        
    Returns:
        dataset_id 필터가 추가된 메타데이터 필터
    """
    if not selected_datasets:
        return metadata_filters
    
    filters = metadata_filters.copy() if metadata_filters else {}
    
    if len(selected_datasets) == 1:
        filters["dataset_id"] = selected_datasets[0]
    else:
        filters["dataset_id"] = {"$in": selected_datasets}
    
    return filters


# ============================================================================
# P5: Adaptive RAG - Skip Retrieval Check
# ============================================================================


async def _check_skip_retrieval(
    query: str,
    app_key: Optional[str] = None,
    auteur_key: Optional[str] = None,
    dimension: Optional[str] = None,
) -> Optional[HybridRAGResult]:
    """P5 Skip Retrieval 판단.

    단순 쿼리 (simple_factual, creative)는 검색을 생략하고 LLM 직접 응답.
    단, 도메인 특화 컨텍스트가 있으면 (auteur_key, dimension) skip하지 않음.

    Args:
        query: 검색 쿼리
        app_key: 앱 키 (매니페스트 기반 설정)
        auteur_key: 거장 키가 있으면 skip 안함
        dimension: 차원 코드가 있으면 skip 안함

    Returns:
        HybridRAGResult if skip retrieval, None otherwise
    """
    # 도메인 특화 컨텍스트가 있으면 skip하지 않음
    if auteur_key or dimension:
        logger.debug(
            f"[P5] Skip retrieval disabled: auteur_key={auteur_key}, dimension={dimension}"
        )
        return None

    try:
        # Get routing config from manifest (if available)
        routing_config = None
        if app_key:
            from app.rag.manifest_loader import get_manifest

            manifest = get_manifest(app_key)
            if manifest and manifest.routing:
                routing_config = manifest.routing.to_routing_config()

        # Import P5 modules
        from app.rag.query_classifier import (
            QueryType,
            RoutingConfig,
            classify_query,
            should_skip_retrieval,
        )

        if routing_config is None:
            routing_config = RoutingConfig()

        if not routing_config.enabled:
            logger.debug("[P5] Adaptive RAG disabled in config")
            return None

        # Classify query
        query_type, confidence = await classify_query(query, routing_config)

        # Check if should skip retrieval
        if not should_skip_retrieval(query_type, routing_config):
            logger.debug(
                f"[P5] Not skipping: query_type={query_type.value}, confidence={confidence:.2f}"
            )
            return None

        logger.info(
            f"[P5] Skipping retrieval: query_type={query_type.value}, confidence={confidence:.2f}"
        )

        # Generate direct LLM response
        from app.rag.direct_llm import direct_llm_response

        direct_result = await direct_llm_response(
            query=query,
            query_type=query_type,
        )

        # Convert to HybridRAGResult
        return direct_result.to_hybrid_result()

    except Exception as e:
        logger.warning(f"[P5] Skip retrieval check failed: {e}")
        return None


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
) -> Tuple[str, bool, bool, int]:
    """경량 Router: 쿼리 복잡도 기반 전략 결정.
    
    LangGraph 없이 heuristic 기반으로 최적 전략 선택.
    
    Args:
        query: 검색 쿼리
        auteur_key: 거장 키
        dimension: 차원 코드
        use_google_search: Google Search 사용 여부
        
    Returns:
        Tuple of (strategy, use_reranker, force_grounding, complexity_score)
        - strategy: "auteur_first" | "hybrid" | "vector"
        - use_reranker: 리랭커 사용 여부
        - force_grounding: Web Grounding 강제 여부
        - complexity_score: 복잡도 점수 (0-4, 로깅/메트릭용)
    """
    score = 0
    
    # === Phase 6: Dimension-specific complexity boost (2026 Best Practice) ===
    # Per-dimension scoring to balance strategy distribution
    DIMENSION_COMPLEXITY_BOOST = {
        "STORY": 2,  # Narrative complexity - force higher strategy
        "4D": 2,     # Analysis depth
        "AD": 1,     # Auteur-focused
        "QC": 1,     # Meta invariants
        "1D": 0,     # Standard visual
        "2D": 0,     # Storyboard
        "3D": 0,     # Sequence
    }
    
    # 길이 기반 복잡도 (char count)
    if len(query) > 120:
        score += 1
    
    # 최신성 키워드
    query_lower = query.lower()
    if any(kw in query_lower for kw in RECENCY_KEYWORDS):
        score += 1
        
    # dimension 복잡도 부스트 (Phase 6: per-dimension map)
    if dimension:
        score += DIMENSION_COMPLEXITY_BOOST.get(dimension.upper(), 0)
    
    # auteur 지정 시 +1
    if auteur_key:
        score += 1
        
    # 결정 로직
    if auteur_key:
        # 거장 키 있으면 auteur_first, 복잡도에 따라 rerank/grounding
        return ("auteur_first", score >= 2, score >= 3, score)
    elif score >= 2:
        # 복잡한 쿼리 → hybrid + rerank
        return ("hybrid", True, score >= 3, score)
    else:
        # 단순 쿼리 → vector only
        return ("vector", False, use_google_search, score)


# ============================================================================
# Hybrid Query Functions
# ============================================================================

@trace_rag(name="hybrid_query", tags=["rag", "hybrid"])
async def hybrid_query(
    query: str,
    auteur_key: Optional[str] = None,
    dimension: Optional[str] = None,
    use_google_search: bool = True,
    strategy: Literal["vector", "graph", "hybrid", "ensemble"] = "vector",
    pipeline_hints: Optional[Dict[str, Any]] = None,
    use_semantic_cache: bool = True,  # NEW: Enable semantic caching
    app_key: Optional[str] = None,  # P3: For ensemble retrieval
) -> HybridRAGResult:
    """하이브리드 RAG 쿼리 실행.

    Strategy Options:
    - "vector": Traditional vector similarity search (default)
    - "graph": GraphRAG entity/relationship traversal
    - "hybrid": Combine both vector and graph results
    - "ensemble": P3 Weighted RRF Fusion (requires app_key)

    Pipeline Hints (when provided):
    - use_expansion: bool - Enable query expansion via LLM
    - expansion_strategy: "llm" | "hyde" | "none"
    - use_reranker: bool - Enable vertex reranker
    - reranker_model: "semantic-ranker-default-v1"
    - top_k: int - Number of results to return
    - use_ensemble: bool - Force ensemble retrieval (P3)
    - rrf_k: int - RRF constant (default 60)

    Flow:
    1. Query Expansion (if hints.use_expansion)
    2. strategy="ensemble": Multi-backend parallel + Weighted RRF
    3. auteur_key 있으면: NotebookLM 우선 → Vertex AI 폴백
    4. dimension 있으면: Vertex AI + Google Search Grounding
    5. 둘 다 없으면: 병렬 실행 → 결과 병합
    6. strategy="graph": GraphRAG 엔티티 검색
    7. Reranking (if hints.use_reranker)

    Args:
        query: 검색 쿼리
        auteur_key: 거장 키 (예: "bong", "봉준호")
        dimension: 차원 코드 (예: "1D", "2D", "AD")
        use_google_search: Google Search Grounding 사용 여부
        strategy: 검색 전략 ("vector" | "graph" | "hybrid" | "ensemble")
        pipeline_hints: 파이프라인 힌트 딕셔너리
        app_key: 앱 키 (ensemble 전략 시 필수, e.g., "dimension.aesthetic.direct")

    Returns:
        HybridRAGResult with combined answer and sources
    """

    import time
    start_time = time.monotonic()
    
    # === Step 0: Semantic Cache Check (90%+ hit rate) ===
    cached_result = None  # Initialize for later reference in log_router_decision
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

    # === P5: Adaptive RAG - Skip Retrieval Check ===
    skip_result = await _check_skip_retrieval(
        query=query,
        app_key=app_key,
        auteur_key=auteur_key,
        dimension=dimension,
    )
    if skip_result is not None:
        skip_result.query_time_ms = int((time.monotonic() - start_time) * 1000)
        record_rag_query(
            dimension=dimension or "unknown",
            strategy="direct_llm",
            source_type="skip_retrieval",
            latency_ms=skip_result.query_time_ms,
            results_count=0,
            confidence=skip_result.confidence,
            cache_hit=False,
            auteur_key=auteur_key,
            grounded=False,
            rrf_enabled=False,
        )
        logger.info(
            f"[HybridRAG] P5 SKIP_RETRIEVAL | "
            f"query='{query[:50]}...' | "
            f"strategy={skip_result.strategy_used}"
        )
        return skip_result

    # === Parse Pipeline Hints ===
    hints = pipeline_hints or {}
    use_expansion = hints.get("use_expansion", False)
    expansion_strategy = hints.get("expansion_strategy", "llm")
    use_reranker = hints.get("use_reranker", False)
    reranker_model = hints.get("reranker_model", "semantic-ranker-default-v1@latest")
    top_k = hints.get("top_k", 10)
    
    # === Apply Lightweight Router (2025 Best Practice) ===
    # _determine_strategy를 통해 복잡도 기반 전략 자동 조정
    router_strategy, router_reranker, router_grounding, router_score = _determine_strategy(
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
    
    # === Week 3: Structured Router Decision Log (OTel Best Practice) ===
    # router_score는 _determine_strategy에서 계산됨 (중복 계산 제거)
    log_router_decision(
        query=query,
        dimension=dimension,
        auteur_key=auteur_key,
        router_score=router_score,
        strategy=strategy,
        use_reranker=use_reranker,
        use_grounding=use_google_search,
        cache_hit=cached_result is not None,  # Step 0에서 정의된 변수
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

    # === Strategy: Ensemble (P3: Multi-backend + Weighted RRF) ===
    hints = pipeline_hints or {}
    use_ensemble = hints.get("use_ensemble", False) or strategy == "ensemble"
    if router_grounding and not use_ensemble:
        # Recency-required queries -> force ensemble to include web grounding backend
        use_ensemble = True

    if use_ensemble:
        # app_key 결정: 명시적 전달 > dimension 기반 추론 > auteur 기반 추론
        effective_app_key = app_key
        if not effective_app_key and dimension:
            # dimension에서 app_key 추론 (예: AD -> dimension.aesthetic.direct)
            dimension_to_app = {
                "AD": "dimension.aesthetic.direct",
                "1D": "teaching.prompt.generate",
                "2D": "teaching.storyboard.create",
                "3D": "teaching.image.generate",
                "4D": "teaching.reference.analyze",
                "VEO": "veo.video.generate",
                "AI": "dimension.persona.analyze",
                "QC": "dimension.quality.check",
                "STORY": "dimension.story.architect",
                "PROMPT": "prompt.alchemy.translate",
                "SOUND": "dimension.sound.craft",
            }
            effective_app_key = dimension_to_app.get(dimension.upper())

        if not effective_app_key:
            # 기본값: dimension.aesthetic.direct (가장 일반적)
            effective_app_key = "dimension.aesthetic.direct"
            logger.warning(f"[HybridRAG] No app_key for ensemble, using default: {effective_app_key}")

        rrf_k = hints.get("rrf_k", 60)
        top_k = hints.get("top_k", 5)

        result = await ensemble_retrieve(
            query=effective_query,
            app_key=effective_app_key,
            limit=top_k,
            rrf_k=rrf_k,
            auteur_key=auteur_key,
            filters={"dimension": dimension} if dimension else None,
        )
        result.query_time_ms = int((time.monotonic() - start_time) * 1000)
        result.dimension = dimension
        return result

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
    
    # === Step N: Reranking (P4: Updated to use new rerankers module) ===
    if use_reranker and result.retrieval_count > 0:
        try:
            # P4: Use get_reranker with backend preference
            # Default to vertex for backward compatibility
            reranker = get_reranker("vertex")
            if not reranker:
                reranker = get_reranker("local_cross_encoder")

            if reranker:
                # Prepare documents for reranking
                docs_to_rerank: List[DocumentToRerank] = []

                # Add NotebookLM sources
                for src in result.notebooklm_sources:
                    docs_to_rerank.append(DocumentToRerank(
                        id=f"nlm_{src.source_id}",
                        text=src.text[:1000],  # Truncate for reranker
                        metadata={"source": "notebooklm"}
                    ))

                # Add Vertex sources
                for src in result.vertex_sources:
                    docs_to_rerank.append(DocumentToRerank(
                        id=f"vtx_{src.source_id}",
                        text=src.text[:1000],
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
                    result.rerank_model = rerank_result.model
                    result.source_scores = [doc["rerank_score"] for doc in rerank_result.documents]

                    logger.info(
                        f"[HybridRAG] Reranked {len(docs_to_rerank)} docs | "
                        f"model={rerank_result.model} | "
                        f"top_score={rerank_result.documents[0]['rerank_score'] if rerank_result.documents else 0:.3f}"
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

    # === Load preset for Cache thresholds ===
    from app.rag.rag_presets import get_rag_preset
    preset_dim = dimension or ("AD" if auteur_key else "1D")
    preset = get_rag_preset(preset_dim)

    # === Step N+1: Store in Semantic Cache (preset-based gating) ===
    # P6-1 Refinement: Use dimension-based threshold from YAML SSoT
    if use_semantic_cache and preset.cache_enabled and result.confidence >= preset.confidence_threshold:
        try:
            cache = get_semantic_cache()
            await cache.set(
                query=query,
                response=result,
                auteur_key=auteur_key,
                dimension=dimension,
                min_confidence=preset.confidence_threshold,  # P6-1
                cache_ttl=preset.cache_ttl,                  # P6-4
            )
            logger.debug(
                f"[HybridRAG] Cached result | "
                f"confidence={result.confidence:.2f} | "
                f"threshold={preset.confidence_threshold} | "
                f"ttl={preset.cache_ttl}s"
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
    """거장 쿼리: NotebookLM (Tier 0) 전용.

    Args:
        query: 검색 쿼리
        auteur_key: 거장 키
        use_google_search: (deprecated, ignored)

    Returns:
        HybridRAGResult
    """
    # 거장 키 → 노트북 키 변환
    notebook_key = AUTEUR_KEY_TO_NOTEBOOK.get(auteur_key.lower())
    if not notebook_key:
        logger.warning(f"[HybridRAG] Unknown auteur key: {auteur_key}")
        # Fallback to NotebookLM general query
        return await _query_notebooklm_only(query, dimension=dimension)

    # NotebookLM 쿼리
    notebooklm_service = get_notebooklm_service()
    notebooklm_result = await notebooklm_service.query_notebook(
        notebook_id=notebook_key,
        query=query,
    )

    return HybridRAGResult(
        answer=notebooklm_result.answer,
        notebooklm_sources=notebooklm_result.sources,
        confidence=notebooklm_result.confidence,
        strategy_used="auteur_first",
        grounded=notebooklm_result.grounded,
        auteur_key=auteur_key,
    )


@track_rag_operation("dimension_query")
async def _query_dimension(
    query: str,
    dimension: str,
    use_google_search: bool = True,
) -> HybridRAGResult:
    """차원별 쿼리: Qdrant Hybrid (Tier 1).

    Args:
        query: 검색 쿼리
        dimension: 차원 코드
        use_google_search: (deprecated, ignored)

    Returns:
        HybridRAGResult
    """
    try:
        from app.rag.tier1_dimension_rag import get_dimension_rag

        rag = get_dimension_rag(dimension.upper())
        results = rag.hybrid_search(query=query, limit=10)

        # Convert Qdrant results to RAGSource format
        sources = [
            RAGSource(
                source_id=r.get("doc_id", ""),
                content=r.get("content", ""),
                relevance_score=r.get("score", 0.0),
                document_name=r.get("metadata", {}).get("source", ""),
                metadata=r.get("metadata", {}),
            )
            for r in results
        ]

        # Synthesize answer from top results
        answer = "\n\n".join(
            r.get("content", "")[:500] for r in results[:3]
        ) if results else "검색 결과를 찾을 수 없습니다."

        return HybridRAGResult(
            answer=answer,
            vertex_sources=sources,  # Using vertex_sources for backward compat
            confidence=results[0].get("score", 0.0) if results else 0.0,
            strategy_used="dimension",
            dimension=dimension,
            grounded=False,
        )
    except Exception as e:
        logger.error(f"[HybridRAG] Dimension query error: {e}")
        return HybridRAGResult(
            answer="차원별 검색에 실패했습니다.",
            confidence=0.0,
            strategy_used="dimension",
            dimension=dimension,
            grounded=False,
        )


async def _query_notebooklm_only(
    query: str,
    dimension: str = "general",
) -> HybridRAGResult:
    """NotebookLM 전용 쿼리.

    Args:
        query: 검색 쿼리
        dimension: 차원 코드 (for metric labeling)

    Returns:
        HybridRAGResult
    """
    notebooklm_service = get_notebooklm_service()

    # AD 카테고리 노트북들 검색
    auteur_notebooks = notebooklm_service.get_notebooks_by_category("auteur")

    # 가장 관련성 높은 노트북 하나만 선택 (첫 번째)
    if auteur_notebooks:
        notebook_key = auteur_notebooks[0]
    else:
        notebook_key = "DNA_봉준호"  # 기본값

    try:
        notebooklm_result = await notebooklm_service.query_notebook(
            notebook_id=notebook_key,
            query=query,
        )

        return HybridRAGResult(
            answer=notebooklm_result.answer,
            notebooklm_sources=notebooklm_result.sources,
            confidence=notebooklm_result.confidence,
            strategy_used="notebooklm_only",
            grounded=notebooklm_result.grounded,
            dimension=dimension,
        )
    except Exception as e:
        logger.error(f"[HybridRAG] NotebookLM error: {e}")
        return HybridRAGResult(
            answer="검색 결과를 찾을 수 없습니다.",
            confidence=0.0,
            strategy_used="fallback",
            grounded=False,
            dimension=dimension,
        )


@track_rag_operation("parallel_query")
async def _query_parallel(
    query: str,
    use_google_search: bool = True,
    dimension: str = "general",  # Medium fix: for correct metric labeling
) -> HybridRAGResult:
    """범용 쿼리: NotebookLM 우선.

    Args:
        query: 검색 쿼리
        use_google_search: (deprecated, ignored)
        dimension: 차원 코드 (for metric labeling)

    Returns:
        HybridRAGResult
    """
    return await _query_notebooklm_only(query, dimension=dimension)


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

    # P0.5: rrf_query() removed - use tier1_dimension_rag.hybrid_search() instead

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


# ============================================================================
# P3: Ensemble Retriever (Weighted RRF Fusion)
# ============================================================================

from app.rag.backends.base import RetrievalResult
from app.rag.manifest_loader import BackendConfig


def _weighted_rrf_fusion(
    backend_results: List[Tuple[str, float, List[RetrievalResult]]],
    *,
    k: int = 60,
    limit: int = 10,
    min_score: float = 0.0,
) -> List[RetrievalResult]:
    """Weighted Reciprocal Rank Fusion 알고리즘.

    다중 백엔드 결과를 Weighted RRF로 통합합니다.

    Args:
        backend_results: [(backend_id, weight, results), ...] 형식
        k: RRF 상수 (기본값 60, 순위 차이 완화)
        limit: 반환할 최대 문서 수
        min_score: 최소 RRF 스코어 임계값

    Returns:
        RRF 스코어로 정렬된 RetrievalResult 리스트

    Algorithm:
        Weighted_RRF(d) = Σ w_i / (k + rank_i(d))

        where:
        - w_i = weight of retriever i (from YAML config)
        - rank_i(d) = 1-based rank of document d in retriever i
        - k = smoothing constant (60 by default)

    Note:
        k=60은 empirically proven 값으로:
        - 상위 순위와 하위 순위 사이의 점수 차이 완화
        - 단일 retriever의 지배 방지
        - 여러 retriever에서 일관되게 등장하는 문서 선호
    """
    # doc_id -> {rrf_score, best_result, sources}
    doc_scores: Dict[str, Dict[str, Any]] = {}

    for backend_id, weight, results in backend_results:
        for rank, result in enumerate(results, start=1):
            doc_id = result.doc_id
            rrf_contribution = weight / (k + rank)

            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    "rrf_score": 0.0,
                    "best_result": result,
                    "sources": [],
                    "max_original_score": result.score,
                }

            doc_scores[doc_id]["rrf_score"] += rrf_contribution
            doc_scores[doc_id]["sources"].append(backend_id)

            # 가장 높은 원본 스코어를 가진 결과 보존
            if result.score > doc_scores[doc_id]["max_original_score"]:
                doc_scores[doc_id]["best_result"] = result
                doc_scores[doc_id]["max_original_score"] = result.score

    # RRF 스코어로 정렬
    sorted_docs = sorted(
        doc_scores.items(),
        key=lambda x: x[1]["rrf_score"],
        reverse=True,
    )

    # min_score 필터링 및 limit 적용
    fused_results: List[RetrievalResult] = []
    for doc_id, data in sorted_docs[:limit]:
        if data["rrf_score"] < min_score:
            continue

        best = data["best_result"]
        # 새 RetrievalResult 객체 생성 (원본 수정 방지)
        fused_result = RetrievalResult(
            doc_id=best.doc_id,
            text=best.text,
            score=data["rrf_score"],  # RRF 스코어 사용
            source=best.source,
            rank=0,  # 아래에서 재설정
            metadata={
                **best.metadata,
                "rrf_score": data["rrf_score"],
                "fusion_sources": data["sources"],
                "original_score": data["max_original_score"],
            },
        )
        fused_results.append(fused_result)

    # 최종 순위 재설정
    for i, result in enumerate(fused_results, start=1):
        result.rank = i

    logger.debug(
        f"[RRF] Fused {len(backend_results)} backends -> {len(fused_results)} results | "
        f"unique_docs={len(doc_scores)} | k={k}"
    )

    return fused_results


def _convert_ensemble_to_hybrid_result(
    fused_results: List[RetrievalResult],
    query: str,
) -> HybridRAGResult:
    """RetrievalResult 리스트를 HybridRAGResult로 변환.

    기존 hybrid_query() API와의 하위 호환성을 유지합니다.

    Args:
        fused_results: RRF fusion된 RetrievalResult 리스트
        query: 원본 검색 쿼리

    Returns:
        HybridRAGResult 인스턴스 (기존 API 호환)
    """
    from app.rag.tier0_notebooklm import NotebookSource

    notebooklm_sources: List[NotebookSource] = []
    vertex_sources: List[RAGSource] = []  # Using local RAGSource for backward compat
    grounding_sources: List[Dict[str, Any]] = []

    # 소스별 분류
    for result in fused_results:
        source_type = result.source

        if source_type == "notebooklm":
            notebooklm_sources.append(
                NotebookSource(
                    source_id=result.doc_id,
                    title=result.metadata.get("title", ""),
                    excerpt=result.text[:500] if result.text else "",
                    relevance_score=result.metadata.get("original_score", result.score),
                    citation_text=result.text[:200] if result.text else "",
                )
            )
        elif source_type in ("qdrant_hybrid", "vertex_grounding", "tavily_grounding"):
            vertex_sources.append(
                RAGSource(
                    source_id=result.doc_id,
                    content=result.text,
                    relevance_score=result.metadata.get("original_score", result.score),
                    document_name=result.metadata.get("document_name", ""),
                    metadata=result.metadata,
                )
            )
            # Google Search Grounding 결과 분리
            if result.metadata.get("type") in ("google_search", "web_search"):
                grounding_sources.append({
                    "uri": result.metadata.get("url", ""),
                    "source": result.text,
                })

    # 신뢰도 계산 (RRF 스코어 기반)
    avg_confidence = 0.0
    if fused_results:
        # RRF 스코어는 작으므로 정규화 (0.1 이상이면 높은 신뢰도)
        max_rrf = max(r.score for r in fused_results)
        avg_confidence = min(0.95, max_rrf * 50)  # 스케일 조정

    # Answer 생성 (상위 결과 기반)
    answer_parts = []
    for result in fused_results[:3]:  # 상위 3개
        if result.text:
            answer_parts.append(result.text[:300])
    answer = "\n\n".join(answer_parts) if answer_parts else "검색 결과를 찾을 수 없습니다."

    return HybridRAGResult(
        answer=answer,
        notebooklm_sources=notebooklm_sources,
        vertex_sources=vertex_sources,
        grounding_sources=grounding_sources,
        confidence=avg_confidence,
        strategy_used="ensemble_rrf",
        grounded=bool(notebooklm_sources) or bool(grounding_sources),
        rrf_enabled=True,
        fused_results=[
            {
                "doc_id": r.doc_id,
                "score": r.score,
                "source": r.source,
                "fusion_sources": r.metadata.get("fusion_sources", []),
            }
            for r in fused_results
        ],
    )


async def _fallback_single_backend_query(
    query: str,
    app_key: str,
    limit: int,
    min_score: float,
    filters: Optional[Dict[str, Any]],
) -> HybridRAGResult:
    """backends 설정이 없을 때 기본 Qdrant 검색으로 폴백.

    Args:
        query: 검색 쿼리
        app_key: 앱 식별자
        limit: 최대 결과 수
        min_score: 최소 스코어
        filters: 메타데이터 필터

    Returns:
        HybridRAGResult (단일 백엔드 결과)
    """
    from app.rag.backends import get_backend

    backend = get_backend("qdrant_hybrid")
    if not backend:
        return HybridRAGResult(
            answer="RAG 백엔드를 찾을 수 없습니다.",
            confidence=0.0,
            strategy_used="fallback_error",
        )

    # app_key에서 dimension 추출 (예: dimension.aesthetic.direct -> AD)
    manifest = get_manifest(app_key)
    dimension = manifest.dimensions[0] if manifest and manifest.dimensions else "1D"

    try:
        results = await backend.retrieve(
            query=query,
            limit=limit,
            filters=filters,
            config={"dimension": dimension, "min_score": min_score},
        )

        return _convert_ensemble_to_hybrid_result(results, query)
    except Exception as e:
        logger.error(f"[EnsembleRetriever] Fallback query failed: {e}")
        return HybridRAGResult(
            answer="검색 중 오류가 발생했습니다.",
            confidence=0.0,
            strategy_used="fallback_error",
        )


@trace_rag(name="ensemble_retrieve", tags=["rag", "ensemble", "rrf"])
async def ensemble_retrieve(
    query: str,
    app_key: str,
    *,
    limit: int = 5,
    min_score: float = 0.0,
    filters: Optional[Dict[str, Any]] = None,
    rrf_k: int = 60,
    auteur_key: Optional[str] = None,
) -> HybridRAGResult:
    """P3: Ensemble Retrieval with Weighted RRF Fusion.

    YAML Manifest의 backends 설정에 따라 다중 백엔드를 병렬 실행하고
    Weighted RRF로 결과를 통합합니다.

    Args:
        query: 검색 쿼리
        app_key: 앱 식별자 (e.g., "dimension.aesthetic.direct")
        limit: 최종 반환할 최대 문서 수
        min_score: 최소 RRF 스코어 임계값
        filters: 추가 메타데이터 필터
        rrf_k: RRF 상수 (기본값 60)
        auteur_key: 거장 키 (NotebookLM notebook_id 오버라이드용)

    Returns:
        HybridRAGResult: 통합된 검색 결과

    Example:
        >>> result = await ensemble_retrieve(
        ...     query="봉준호 롱테이크 기법",
        ...     app_key="dimension.aesthetic.direct",
        ...     limit=7,
        ...     auteur_key="bong",
        ... )
        >>> print(result.strategy_used)  # "ensemble_rrf"
        >>> for item in result.fused_results:
        ...     print(f"{item['source']}: {item['doc_id']}")

    Notes:
        - 거장 DNA 외 다른 백엔드 타입도 동일하게 지원
        - 새 백엔드 추가 시 backends/ 디렉토리에 구현체만 추가하면 됨
        - YAML에서 weight, enabled, config 조정으로 튜닝 가능
    """
    import time
    from app.rag.backends import get_backend

    start_time = time.monotonic()

    # 1. Manifest 로드
    manifest = get_manifest(app_key)
    if not manifest or not manifest.backends:
        logger.warning(f"[EnsembleRetriever] No backends configured for {app_key}, falling back to default")
        return await _fallback_single_backend_query(query, app_key, limit, min_score, filters)

    # 2. enabled=true인 백엔드만 필터링
    enabled_backends = [b for b in manifest.backends if b.enabled]
    if not enabled_backends:
        logger.warning(f"[EnsembleRetriever] No enabled backends for {app_key}")
        return HybridRAGResult(
            answer="활성화된 RAG 백엔드가 없습니다.",
            confidence=0.0,
            strategy_used="ensemble_no_backends",
        )

    logger.info(
        f"[EnsembleRetriever] Starting | app={app_key} | "
        f"backends={[b.id for b in enabled_backends]} | "
        f"query='{query[:50]}...'"
    )

    # 3. 병렬 실행 태스크 생성
    async def _execute_backend(
        backend_config: BackendConfig,
    ) -> Tuple[str, float, List[RetrievalResult]]:
        """단일 백엔드 실행 및 결과 반환."""
        try:
            backend = get_backend(backend_config.id)
            if not backend:
                logger.warning(f"[EnsembleRetriever] Backend not found: {backend_config.id}")
                return (backend_config.id, backend_config.weight, [])

            # NotebookLM의 경우 auteur_key로 notebook_id 오버라이드
            config = dict(backend_config.config)
            # Provide app_key for backend-level defaults (e.g., Tavily per-app tuning)
            config.setdefault("app_key", app_key)
            # Provide dimension fallback for defaults when not explicitly set
            if manifest and manifest.dimensions:
                config.setdefault("dimension", manifest.dimensions[0])
            if backend_config.id == "notebooklm" and auteur_key:
                notebook_key = AUTEUR_KEY_TO_NOTEBOOK.get(auteur_key.lower())
                if notebook_key:
                    config["notebook_id"] = notebook_key

            results = await asyncio.wait_for(
                backend.retrieve(
                    query=query,
                    limit=limit * 2,  # Over-fetch for fusion
                    filters=filters,
                    config=config,
                ),
                timeout=10.0,  # 개별 백엔드 타임아웃 10초
            )

            logger.debug(
                f"[EnsembleRetriever] Backend {backend_config.id} returned {len(results)} results"
            )
            return (backend_config.id, backend_config.weight, results)

        except asyncio.TimeoutError:
            logger.warning(f"[EnsembleRetriever] Backend {backend_config.id} timed out")
            return (backend_config.id, backend_config.weight, [])
        except Exception as e:
            logger.error(f"[EnsembleRetriever] Backend {backend_config.id} failed: {e}")
            return (backend_config.id, backend_config.weight, [])

    # 4. asyncio.gather()로 병렬 실행
    tasks = [_execute_backend(b) for b in enabled_backends]
    backend_results = await asyncio.gather(*tasks, return_exceptions=True)

    # 5. 예외 필터링
    valid_results: List[Tuple[str, float, List[RetrievalResult]]] = []
    for result in backend_results:
        if isinstance(result, Exception):
            logger.error(f"[EnsembleRetriever] Unexpected error: {result}")
            continue
        valid_results.append(result)

    if not valid_results:
        logger.warning("[EnsembleRetriever] All backends failed")
        return HybridRAGResult(
            answer="모든 RAG 백엔드가 실패했습니다.",
            confidence=0.0,
            strategy_used="ensemble_all_failed",
        )

    # 총 검색된 문서 수
    total_retrieved = sum(len(r[2]) for r in valid_results)

    # 6. Weighted RRF Fusion
    fused_results = _weighted_rrf_fusion(
        valid_results, k=rrf_k, limit=limit, min_score=min_score
    )

    # 7. P4: Reranker Stage (YAML manifest 설정 기반)
    reranked = False
    rerank_model: Optional[str] = None

    if manifest.reranker and manifest.reranker.enabled and fused_results:
        try:
            reranker = get_reranker(
                manifest.reranker.backend,
                model=manifest.reranker.model,
            )

            if reranker:
                # RetrievalResult -> DocumentToRerank 변환
                docs_to_rerank = [
                    DocumentToRerank(
                        id=r.doc_id,
                        text=r.text[:1000],  # Truncate for reranker
                        metadata=r.metadata,
                    )
                    for r in fused_results
                ]

                rerank_result = await reranker.rerank(
                    query=query,
                    documents=docs_to_rerank,
                    top_k=manifest.reranker.top_k or limit,
                )

                # RRF 결과를 rerank 스코어로 재정렬
                reranked_ids = [doc["id"] for doc in rerank_result.documents]
                reranked_scores = {
                    doc["id"]: doc["rerank_score"]
                    for doc in rerank_result.documents
                }

                # min_score 필터링
                min_rerank_score = manifest.reranker.min_score
                filtered_results = []
                for r in fused_results:
                    if r.doc_id in reranked_scores:
                        score = reranked_scores[r.doc_id]
                        if score >= min_rerank_score:
                            # 새 RetrievalResult 생성 (rerank_score 추가)
                            reranked_r = RetrievalResult(
                                doc_id=r.doc_id,
                                text=r.text,
                                score=r.score,
                                source=r.source,
                                rank=0,
                                metadata={
                                    **r.metadata,
                                    "rerank_score": score,
                                },
                            )
                            filtered_results.append((score, reranked_r))

                # rerank 스코어로 정렬
                filtered_results.sort(key=lambda x: x[0], reverse=True)
                fused_results = [r for _, r in filtered_results]

                # 순위 재설정
                for i, r in enumerate(fused_results, start=1):
                    r.rank = i

                reranked = True
                rerank_model = rerank_result.model

                logger.info(
                    f"[EnsembleRetriever] Reranked {len(docs_to_rerank)} -> {len(fused_results)} docs | "
                    f"model={rerank_model} | "
                    f"min_score={min_rerank_score}"
                )

        except Exception as e:
            logger.warning(f"[EnsembleRetriever] Reranking failed: {e}")

    # 8. HybridRAGResult 형식으로 변환
    result = _convert_ensemble_to_hybrid_result(fused_results, query)
    result.reranked = reranked
    result.rerank_model = rerank_model
    result.query_time_ms = int((time.monotonic() - start_time) * 1000)
    result.auteur_key = auteur_key
    result.retrieval_count = len(fused_results)

    # Prometheus 메트릭 기록
    record_rag_query(
        dimension=manifest.dimensions[0] if manifest.dimensions else "unknown",
        strategy="ensemble_rrf",
        source_type="ensemble",
        latency_ms=result.query_time_ms,
        results_count=result.retrieval_count,
        confidence=result.confidence,
        cache_hit=False,
        auteur_key=auteur_key,
        grounded=result.grounded,
        rrf_enabled=True,
    )

    logger.info(
        f"[EnsembleRetriever] Completed | "
        f"backends={len(valid_results)}/{len(enabled_backends)} | "
        f"retrieved={total_retrieved} -> fused={len(fused_results)} | "
        f"time={result.query_time_ms}ms | "
        f"confidence={result.confidence:.2f}"
    )

    return result
