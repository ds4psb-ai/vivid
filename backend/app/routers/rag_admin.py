"""RAG Admin Router: RAG 파이프라인 관리 API.

RAG 시스템 관리, 모니터링, 수동 인덱싱 API.

Endpoints:
- GET /rag/stats - 전체 RAG 통계
- GET /rag/search - RAG 검색
- POST /rag/index - 수동 문서 인덱싱
- POST /rag/promote - 수동 프로모션 트리거
- GET /rag/notebooks - NotebookLM 노트북 목록
- GET /rag/lightrag/graph - LightRAG 그래프 조회

Vertex AI RAG Endpoints (2-Depth Cascaded RAG):
- GET /rag-pipeline/vertex-rag/stats - Vertex RAG 통계
- POST /rag-pipeline/vertex-rag/query - Vertex RAG 검색
- POST /rag-pipeline/vertex-rag/cascaded - 2-Depth 캐스케이드 검색
- POST /rag-pipeline/vertex-rag/podcast - Deep Podcast 생성
- GET /rag-pipeline/vertex-rag/podcast/{operation_name}/status - 팟캐스트 상태 확인
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag-pipeline", tags=["RAG Pipeline"])


# ============================================================================
# Request/Response Models
# ============================================================================

class RAGSearchRequest(BaseModel):
    """RAG 검색 요청."""
    query: str = Field(..., min_length=1, max_length=2000)
    dimensions: List[str] = Field(default_factory=list)
    app_key: Optional[str] = None
    limit: int = Field(default=5, ge=1, le=50)
    min_score: float = Field(default=0.5, ge=0, le=1)
    include_tier0: bool = Field(default=False, description="NotebookLM 포함 여부")
    include_lightrag: bool = Field(default=False, description="LightRAG 포함 여부")


class RAGSearchResponse(BaseModel):
    """RAG 검색 응답."""
    results: List[Dict[str, Any]]
    total_results: int
    dimensions_searched: List[str]
    query_time_ms: int
    sources: List[str] = Field(default_factory=list)


class RAGIndexRequest(BaseModel):
    """RAG 인덱싱 요청."""
    doc_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    dimension: str = Field(..., description="타겟 차원 (1D, 2D, 3D, 4D, AD, QC)")
    app_key: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGIndexResponse(BaseModel):
    """RAG 인덱싱 응답."""
    success: bool
    doc_id: str
    dimension: str
    indexed_to: List[str] = Field(default_factory=list)
    message: str = ""


class PromotionTriggerRequest(BaseModel):
    """프로모션 트리거 요청."""
    promotion_type: str = Field(..., description="weekly 또는 monthly")
    force: bool = Field(default=False, description="스케줄 무시하고 강제 실행")


class PromotionResponse(BaseModel):
    """프로모션 응답."""
    batch_id: str
    promotion_type: str
    total_candidates: int
    promoted_count: int
    failed_count: int
    duration_seconds: int


class RAGStatsResponse(BaseModel):
    """RAG 통계 응답."""
    tier0_stats: Dict[str, Any]
    tier1_stats: Dict[str, Any]
    tier2_stats: Dict[str, Any]
    lightrag_stats: Dict[str, Any]
    feedback_loop_stats: Dict[str, Any]
    promoter_stats: Dict[str, Any]
    overall_health: str


# ============================================================================
# Vertex AI RAG Request/Response Models
# ============================================================================

class VertexRAGQueryRequest(BaseModel):
    """Vertex RAG 검색 요청."""
    query: str = Field(..., min_length=1, max_length=10000)
    corpus_name: Optional[str] = Field(None, description="단일 코퍼스 이름")
    corpus_names: Optional[List[str]] = Field(None, description="복수 코퍼스 이름")
    use_grounding: bool = Field(True, description="Google Search Grounding 사용")
    top_k: int = Field(5, ge=1, le=100)
    min_score: float = Field(0.5, ge=0, le=1)


class VertexRAGQueryResponse(BaseModel):
    """Vertex RAG 검색 응답."""
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    grounding_sources: List[Dict[str, Any]]
    query_time_ms: int
    corpus_name: str
    model_used: str
    grounded: bool


class CascadedQueryRequest(BaseModel):
    """2-Depth Cascaded RAG 요청."""
    query: str = Field(..., min_length=1, max_length=10000)
    depth1_top_k: int = Field(20, ge=1, le=100, description="Depth 1 핵심 문서 수")
    depth2_sources_limit: int = Field(600, ge=10, le=1000, description="Depth 2 소스 제한")


class CascadedQueryResponse(BaseModel):
    """2-Depth Cascaded RAG 응답."""
    depth1_answer: str
    depth1_confidence: float
    depth1_documents_count: int
    depth2_ready: bool
    podcast_eligible: bool
    query: str


class DeepPodcastRequest(BaseModel):
    """Deep Podcast 생성 요청."""
    topic: str = Field(..., min_length=1, max_length=5000, description="팟캐스트 주제")
    mode: str = Field("deep_dive", description="모드: deep_dive, debate, critique, lecture, brief")
    wait_for_completion: bool = Field(False, description="완료까지 대기 (최대 10분)")
    output_path: Optional[str] = Field(None, description="오디오 저장 경로")


class DeepPodcastResponse(BaseModel):
    """Deep Podcast 응답."""
    status: str
    operation_name: Optional[str] = None
    depth1_summary: Optional[str] = None
    depth1_sources_count: int = 0
    confidence: float = 0.0
    message: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/stats", response_model=RAGStatsResponse)
async def get_rag_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> RAGStatsResponse:
    """전체 RAG 시스템 통계 조회.

    Returns:
        각 계층별 통계 및 전체 상태
    """
    stats = RAGStatsResponse(
        tier0_stats={},
        tier1_stats={},
        tier2_stats={},
        lightrag_stats={},
        feedback_loop_stats={},
        promoter_stats={},
        overall_health="healthy",
    )

    try:
        # Tier 0: NotebookLM
        try:
            from app.rag.tier0_notebooklm import get_notebooklm_service
            service = get_notebooklm_service()
            stats.tier0_stats = {
                "notebooks": len(service.get_all_notebooks()),
                "cache": service.get_cache_stats(),
            }
        except Exception as e:
            stats.tier0_stats = {"error": str(e)}

        # Tier 1: Dimension RAG
        try:
            from app.rag.tier1_dimension_rag import get_dimension_rag
            dimensions = ["1D", "2D", "3D", "4D", "AD", "QC"]
            tier1_total = 0
            for dim in dimensions:
                try:
                    rag = get_dimension_rag(dim)
                    dim_stats = rag.get_collection_stats()
                    tier1_total += dim_stats.get("count", 0)
                except Exception:
                    pass
            stats.tier1_stats = {
                "dimensions": dimensions,
                "total_documents": tier1_total,
            }
        except Exception as e:
            stats.tier1_stats = {"error": str(e)}

        # Tier 2: App Context
        try:
            from app.rag.tier2_app_context import get_app_context_loader
            loader = get_app_context_loader()
            stats.tier2_stats = loader.get_stats()
        except Exception as e:
            stats.tier2_stats = {"error": str(e)}

        # LightRAG
        try:
            from app.rag.lightrag_adapter import get_lightrag_adapter
            adapter = get_lightrag_adapter()
            stats.lightrag_stats = adapter.get_stats()
        except Exception as e:
            stats.lightrag_stats = {"error": str(e)}

        # Feedback Loop
        try:
            from app.rag.feedback_loop import get_feedback_loop
            loop = get_feedback_loop()
            stats.feedback_loop_stats = loop.get_stats()
        except Exception as e:
            stats.feedback_loop_stats = {"error": str(e)}

        # Pattern Promoter
        try:
            from app.rag.pattern_promoter import get_pattern_promoter
            promoter = get_pattern_promoter()
            stats.promoter_stats = promoter.get_stats()
        except Exception as e:
            stats.promoter_stats = {"error": str(e)}

        # Overall health check
        error_count = sum(
            1 for s in [
                stats.tier0_stats,
                stats.tier1_stats,
                stats.tier2_stats,
                stats.lightrag_stats,
            ]
            if "error" in s
        )
        if error_count >= 3:
            stats.overall_health = "critical"
        elif error_count >= 1:
            stats.overall_health = "degraded"

    except Exception as e:
        logger.error(f"[RAG Admin] Stats error: {e}")
        stats.overall_health = "error"

    return stats


@router.post("/search", response_model=RAGSearchResponse)
async def search_rag(
    request: RAGSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> RAGSearchResponse:
    """통합 RAG 검색.

    모든 계층에서 검색 후 결과 병합.

    Args:
        request: 검색 요청

    Returns:
        병합된 검색 결과
    """
    import time
    start_time = time.monotonic()

    all_results: List[Dict[str, Any]] = []
    dimensions_searched: List[str] = []
    sources: List[str] = []

    # 차원 필터
    target_dimensions = request.dimensions or ["1D", "2D", "3D", "4D", "AD", "QC"]

    # Tier 1: Dimension RAG 검색
    try:
        from app.rag.tier1_dimension_rag import get_dimension_rag

        for dim in target_dimensions:
            try:
                rag = get_dimension_rag(dim)
                results = rag.search(
                    query=request.query,
                    limit=request.limit,
                    app_key=request.app_key,
                    min_score=request.min_score,
                )
                for r in results:
                    r["source"] = f"tier1:{dim}"
                all_results.extend(results)
                dimensions_searched.append(dim)
                sources.append(f"Tier1:{dim}")
            except Exception as e:
                logger.warning(f"[RAG Search] Tier1 {dim} error: {e}")

    except ImportError:
        logger.warning("[RAG Search] Tier1 not available")

    # Tier 0: NotebookLM (선택적)
    if request.include_tier0:
        try:
            from app.rag.tier0_notebooklm import get_notebooklm_service

            service = get_notebooklm_service()
            # 관련 노트북 검색
            notebooks = []
            for dim in target_dimensions:
                notebooks.extend(service.get_notebooks_by_dimension(dim))

            for nb_key in notebooks[:3]:  # 최대 3개 노트북
                result = await service.query_notebook(nb_key, request.query)
                if result.confidence > 0.5:
                    all_results.append({
                        "content": result.answer,
                        "score": result.confidence,
                        "source": f"tier0:{nb_key}",
                        "sources": [s.title for s in result.sources],
                    })
                    sources.append(f"Tier0:{nb_key}")

        except Exception as e:
            logger.warning(f"[RAG Search] Tier0 error: {e}")

    # LightRAG (선택적)
    if request.include_lightrag:
        try:
            from app.rag.lightrag_adapter import get_lightrag_adapter

            adapter = get_lightrag_adapter()
            lightrag_result = await adapter.search(
                query=request.query,
                search_level="hybrid",
            )

            if lightrag_result.entities:
                all_results.append({
                    "content": lightrag_result.get_formatted_context(),
                    "score": lightrag_result.confidence,
                    "source": "lightrag",
                    "entities": [e.to_dict() for e in lightrag_result.entities[:5]],
                })
                sources.append("LightRAG")

        except Exception as e:
            logger.warning(f"[RAG Search] LightRAG error: {e}")

    # 점수순 정렬
    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)

    query_time_ms = int((time.monotonic() - start_time) * 1000)

    return RAGSearchResponse(
        results=all_results[:request.limit],
        total_results=len(all_results),
        dimensions_searched=dimensions_searched,
        query_time_ms=query_time_ms,
        sources=sources,
    )


@router.post("/index", response_model=RAGIndexResponse)
async def index_document(
    request: RAGIndexRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> RAGIndexResponse:
    """수동 문서 인덱싱.

    Args:
        request: 인덱싱 요청

    Returns:
        인덱싱 결과
    """
    indexed_to: List[str] = []

    # Tier 1: Dimension RAG
    try:
        from app.rag.tier1_dimension_rag import get_dimension_rag

        rag = get_dimension_rag(request.dimension)
        success = rag.index_document(
            doc_id=request.doc_id,
            content=request.content,
            metadata={
                **request.metadata,
                "app_key": request.app_key,
                "indexed_by": current_user.user_id,
                "indexed_at": datetime.utcnow().isoformat(),
            },
        )

        if success:
            indexed_to.append(f"tier1:{request.dimension}")

    except Exception as e:
        logger.error(f"[RAG Index] Tier1 error: {e}")
        raise HTTPException(status_code=500, detail=f"Tier1 indexing failed: {e}")

    # LightRAG (엔티티/관계 추출)
    try:
        from app.rag.lightrag_adapter import get_lightrag_adapter

        adapter = get_lightrag_adapter()
        result = await adapter.index_document(
            doc_id=request.doc_id,
            content=request.content,
            dimension=request.dimension,
            metadata=request.metadata,
        )

        if result.get("entities_count", 0) > 0:
            indexed_to.append("lightrag")

    except Exception as e:
        logger.warning(f"[RAG Index] LightRAG error: {e}")

    return RAGIndexResponse(
        success=len(indexed_to) > 0,
        doc_id=request.doc_id,
        dimension=request.dimension,
        indexed_to=indexed_to,
        message=f"Indexed to {', '.join(indexed_to)}" if indexed_to else "No indexing performed",
    )


@router.post("/promote", response_model=PromotionResponse)
async def trigger_promotion(
    request: PromotionTriggerRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> PromotionResponse:
    """수동 프로모션 트리거.

    Args:
        request: 프로모션 요청

    Returns:
        프로모션 결과
    """
    from app.rag.pattern_promoter import get_pattern_promoter, PromotionType

    promoter = get_pattern_promoter()

    if request.promotion_type == "weekly":
        result = await promoter.run_weekly_promotion()
    elif request.promotion_type == "monthly":
        result = await promoter.run_monthly_promotion()
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid promotion type: {request.promotion_type}. Use 'weekly' or 'monthly'."
        )

    return PromotionResponse(
        batch_id=result.batch_id,
        promotion_type=result.promotion_type.value,
        total_candidates=result.total_candidates,
        promoted_count=result.promoted_count,
        failed_count=result.failed_count,
        duration_seconds=result.duration_seconds,
    )


@router.get("/notebooks")
async def list_notebooks(
    category: Optional[str] = Query(None, description="auteur, meta, dimension"),
    dimension: Optional[str] = Query(None, description="차원 필터"),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """NotebookLM 노트북 목록 조회.

    Args:
        category: 카테고리 필터
        dimension: 차원 필터

    Returns:
        노트북 목록
    """
    from app.rag.tier0_notebooklm import get_notebooklm_service

    service = get_notebooklm_service()

    if category:
        notebooks = service.get_notebooks_by_category(category)
    elif dimension:
        notebooks = service.get_notebooks_by_dimension(dimension)
    else:
        all_notebooks = service.get_all_notebooks()
        return {
            "notebooks": all_notebooks,
            "total": len(all_notebooks),
        }

    # 노트북 상세 정보 포함
    all_notebooks = service.get_all_notebooks()
    filtered = {k: v for k, v in all_notebooks.items() if k in notebooks}

    return {
        "notebooks": filtered,
        "total": len(filtered),
        "filter": {"category": category, "dimension": dimension},
    }


@router.get("/lightrag/graph")
async def get_lightrag_graph(
    entity_id: str = Query(..., description="시작 엔티티 ID"),
    depth: int = Query(2, ge=1, le=5, description="탐색 깊이"),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """LightRAG 엔티티 그래프 조회.

    Args:
        entity_id: 시작 엔티티 ID
        depth: 탐색 깊이

    Returns:
        그래프 구조 (nodes, edges)
    """
    from app.rag.lightrag_adapter import get_lightrag_adapter

    adapter = get_lightrag_adapter()
    return await adapter.get_entity_graph(entity_id, depth)


@router.get("/lightrag/stats")
async def get_lightrag_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """LightRAG 통계 조회."""
    from app.rag.lightrag_adapter import get_lightrag_adapter

    adapter = get_lightrag_adapter()
    return adapter.get_stats()


@router.post("/lightrag/index")
async def index_to_lightrag(
    doc_id: str,
    content: str,
    dimension: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """LightRAG에 문서 인덱싱 (엔티티/관계 추출).

    Args:
        doc_id: 문서 ID
        content: 문서 내용
        dimension: 차원 코드

    Returns:
        인덱싱 결과
    """
    from app.rag.lightrag_adapter import get_lightrag_adapter

    adapter = get_lightrag_adapter()
    return await adapter.index_document(doc_id, content, dimension)


@router.get("/feedback-loop/stats")
async def get_feedback_loop_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """피드백 루프 통계 조회."""
    from app.rag.feedback_loop import get_feedback_loop

    loop = get_feedback_loop()
    return loop.get_stats()


@router.post("/feedback-loop/reset")
async def reset_feedback_loop_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, str]:
    """피드백 루프 통계 리셋."""
    from app.rag.feedback_loop import get_feedback_loop

    loop = get_feedback_loop()
    loop.reset_stats()
    return {"message": "Feedback loop stats reset"}


@router.get("/promoter/history")
async def get_promotion_history(
    promotion_type: Optional[str] = Query(None, description="weekly 또는 monthly"),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """프로모션 히스토리 조회."""
    from app.rag.pattern_promoter import get_pattern_promoter, PromotionType

    promoter = get_pattern_promoter()

    ptype = None
    if promotion_type:
        ptype = PromotionType(promotion_type)

    history = promoter.get_history(ptype, limit)

    return {
        "history": [r.to_dict() for r in history],
        "total": len(history),
        "filter": {"promotion_type": promotion_type},
    }


# ============================================================================
# Vertex AI RAG Endpoints (2-Depth Cascaded RAG)
# ============================================================================

@router.get("/vertex-rag/stats")
async def get_vertex_rag_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Vertex AI RAG 서비스 통계 조회.

    Returns:
        서비스 상태, 코퍼스 정보, 설정값
    """
    try:
        from app.rag.tier0_vertex_rag import get_vertex_rag_service, CORPUS_REGISTRY

        service = get_vertex_rag_service()
        stats = service.get_stats()
        stats["corpus_registry"] = list(CORPUS_REGISTRY.keys())
        return stats
    except Exception as e:
        logger.error(f"[Vertex RAG] Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Vertex RAG stats failed: {e}")


@router.get("/vertex-rag/corpora")
async def list_vertex_rag_corpora(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """등록된 Vertex RAG 코퍼스 목록 조회.

    Returns:
        코퍼스 목록 및 상세 정보
    """
    try:
        from app.rag.tier0_vertex_rag import get_vertex_rag_service, CORPUS_REGISTRY

        service = get_vertex_rag_service()
        corpora_list = service.list_corpora()

        corpora_details = {}
        for name in corpora_list:
            info = service.get_corpus_info(name)
            if info:
                corpora_details[name] = info

        return {
            "corpora": corpora_details,
            "total": len(corpora_details),
        }
    except Exception as e:
        logger.error(f"[Vertex RAG] List corpora error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list corpora: {e}")


@router.post("/vertex-rag/query", response_model=VertexRAGQueryResponse)
async def query_vertex_rag(
    request: VertexRAGQueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> VertexRAGQueryResponse:
    """Vertex AI RAG 검색.

    프라이빗 데이터 검색 + Gemini Grounding 하이브리드.

    Args:
        request: 검색 요청

    Returns:
        검색 결과 (answer, sources, grounding)
    """
    try:
        from app.rag.tier0_vertex_rag import get_vertex_rag_service

        service = get_vertex_rag_service()
        result = await service.query(
            query=request.query,
            corpus_name=request.corpus_name,
            corpus_names=request.corpus_names,
            use_grounding=request.use_grounding,
            top_k=request.top_k,
            min_score=request.min_score,
        )

        return VertexRAGQueryResponse(
            answer=result.answer,
            confidence=result.confidence,
            sources=[
                {
                    "source_id": s.source_id,
                    "content": s.content[:500],
                    "relevance_score": s.relevance_score,
                    "document_name": s.document_name,
                }
                for s in result.sources
            ],
            grounding_sources=result.grounding_sources,
            query_time_ms=result.query_time_ms,
            corpus_name=result.corpus_name,
            model_used=result.model_used,
            grounded=result.grounded,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Vertex RAG] Query error: {e}")
        raise HTTPException(status_code=500, detail=f"Vertex RAG query failed: {e}")


@router.post("/vertex-rag/cascaded", response_model=CascadedQueryResponse)
async def cascaded_rag_query(
    request: CascadedQueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> CascadedQueryResponse:
    """2-Depth Cascaded RAG 검색.

    Depth 1: Vertex AI RAG (환각률 0.7%) → 핵심 지식 추출
    Depth 2: Discovery Engine → 심층 분석/팟캐스트 준비

    Args:
        request: Cascaded 검색 요청

    Returns:
        Depth 1 결과 및 Depth 2 준비 상태
    """
    try:
        from app.rag.tier0_vertex_rag import cascaded_query

        result = await cascaded_query(
            query=request.query,
            depth1_top_k=request.depth1_top_k,
            depth2_sources_limit=request.depth2_sources_limit,
        )

        depth1_result = result.get("depth1_results")

        return CascadedQueryResponse(
            depth1_answer=depth1_result.answer if depth1_result else "",
            depth1_confidence=depth1_result.confidence if depth1_result else 0.0,
            depth1_documents_count=len(result.get("depth1_documents", [])),
            depth2_ready=result.get("depth2_ready", False),
            podcast_eligible=result.get("podcast_eligible", False),
            query=result.get("query", request.query),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Vertex RAG] Cascaded query error: {e}")
        raise HTTPException(status_code=500, detail=f"Cascaded query failed: {e}")


@router.post("/vertex-rag/podcast", response_model=DeepPodcastResponse)
async def create_deep_podcast_endpoint(
    request: DeepPodcastRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> DeepPodcastResponse:
    """Deep Podcast 생성 (2-Depth Cascaded RAG 기반).

    Depth 1: Vertex AI RAG → 핵심 지식 추출
    Depth 2: Discovery Engine Podcast API → 오디오 생성

    Args:
        request: 팟캐스트 생성 요청

    Returns:
        생성 상태 및 operation_name (비동기 추적용)
    """
    # Validate mode
    valid_modes = {"deep_dive", "debate", "critique", "lecture", "brief"}
    if request.mode not in valid_modes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {request.mode}. Valid modes: {', '.join(valid_modes)}"
        )

    try:
        from app.rag.tier0_vertex_rag import create_deep_podcast

        result = await create_deep_podcast(
            topic=request.topic,
            mode=request.mode,
            wait_for_completion=request.wait_for_completion,
            output_path=request.output_path,
        )

        return DeepPodcastResponse(
            status=result.get("status", "unknown"),
            operation_name=result.get("operation_name"),
            depth1_summary=result.get("depth1_summary"),
            depth1_sources_count=result.get("depth1_sources_count", 0),
            confidence=result.get("confidence", 0.0),
            message=result.get("message"),
            error=result.get("error"),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Vertex RAG] Deep podcast error: {e}")
        raise HTTPException(status_code=500, detail=f"Deep podcast creation failed: {e}")


@router.get("/vertex-rag/podcast/{operation_name}/status")
async def get_podcast_status(
    operation_name: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """팟캐스트 생성 상태 확인.

    Args:
        operation_name: Operation name from create_deep_podcast

    Returns:
        생성 상태 (pending, processing, completed, failed)
    """
    if not operation_name or len(operation_name) < 10:
        raise HTTPException(status_code=400, detail="Invalid operation name")

    try:
        from app.rag.podcast_service import get_podcast_service

        service = get_podcast_service()
        result = await service.check_status(operation_name)

        return {
            "operation_name": result.operation_name,
            "status": result.status.value,
            "title": result.title,
            "error_message": result.error_message,
        }

    except Exception as e:
        logger.error(f"[Podcast] Status check error: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {e}")


@router.post("/vertex-rag/podcast/{operation_name}/download")
async def download_podcast(
    operation_name: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """완료된 팟캐스트 다운로드.

    Args:
        operation_name: Completed operation name

    Returns:
        Base64 encoded audio data
    """
    import base64

    if not operation_name or len(operation_name) < 10:
        raise HTTPException(status_code=400, detail="Invalid operation name")

    try:
        from app.rag.podcast_service import get_podcast_service, PodcastStatus

        service = get_podcast_service()

        # Check status first
        status_result = await service.check_status(operation_name)
        if status_result.status != PodcastStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Podcast not ready: {status_result.status.value}"
            )

        # Download audio
        audio_bytes = await service.download_podcast(operation_name)

        return {
            "operation_name": operation_name,
            "audio_base64": base64.b64encode(audio_bytes).decode() if isinstance(audio_bytes, bytes) else None,
            "audio_path": audio_bytes if isinstance(audio_bytes, str) else None,
            "size_bytes": len(audio_bytes) if isinstance(audio_bytes, bytes) else 0,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Podcast] Download error: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {e}")
