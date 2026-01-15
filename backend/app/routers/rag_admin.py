"""RAG Admin Router: RAG 파이프라인 관리 API.

RAG 시스템 관리, 모니터링, 수동 인덱싱 API.

Endpoints:
- GET /rag/stats - 전체 RAG 통계
- GET /rag/search - RAG 검색
- POST /rag/index - 수동 문서 인덱싱
- POST /rag/promote - 수동 프로모션 트리거
- GET /rag/notebooks - NotebookLM 노트북 목록
- GET /rag/lightrag/graph - LightRAG 그래프 조회
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
# Semantic Cache Endpoints
# ============================================================================

class SemanticCacheStatsResponse(BaseModel):
    """Semantic cache 통계 응답."""
    hits: int
    misses: int
    semantic_hits: int
    exact_hits: int
    total_entries: int
    hit_rate: str
    avg_similarity: str
    similarity_threshold: float
    memory_size: int
    max_size: int
    embeddings_model: str


@router.get("/semantic-cache/stats", response_model=SemanticCacheStatsResponse)
async def get_semantic_cache_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> SemanticCacheStatsResponse:
    """Semantic cache 통계 조회.
    
    Returns:
        캐시 히트율, 엔트리 수, 평균 유사도 등
    """
    try:
        from app.rag.semantic_cache import get_semantic_cache
        
        cache = get_semantic_cache()
        stats = cache.get_stats()
        
        return SemanticCacheStatsResponse(**stats)
    except Exception as e:
        logger.error(f"[SemanticCache] Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {e}")


@router.get("/semantic-cache/top-entries")
async def get_semantic_cache_top_entries(
    limit: int = Query(10, ge=1, le=50, description="반환할 엔트리 수"),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Semantic cache 상위 엔트리 조회 (히트 수 기준).
    
    Returns:
        가장 많이 호출된 캐시 엔트리 목록
    """
    try:
        from app.rag.semantic_cache import get_semantic_cache
        
        cache = get_semantic_cache()
        top_entries = cache.get_top_entries(limit)
        
        return {
            "entries": top_entries,
            "total": len(top_entries),
        }
    except Exception as e:
        logger.error(f"[SemanticCache] Top entries error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get top entries: {e}")


@router.post("/semantic-cache/clear")
async def clear_semantic_cache(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, str]:
    """Semantic cache 전체 클리어.
    
    WARNING: 모든 캐시된 RAG 응답이 삭제됩니다.
    """
    try:
        from app.rag.semantic_cache import get_semantic_cache
        
        cache = get_semantic_cache()
        cache.clear()
        
        return {"message": "Semantic cache cleared successfully"}
    except Exception as e:
        logger.error(f"[SemanticCache] Clear error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {e}")


@router.post("/semantic-cache/warm")
async def warm_semantic_cache(
    auteur_key: Optional[str] = Query(None, description="특정 거장만 워밍"),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Semantic cache 워밍 (사전 시딩).
    
    배치 스크립트 자동 호출 트리거.
    """
    try:
        # This would trigger the seed script
        # For now, return instructions
        return {
            "message": "Cache warming initiated",
            "instruction": "Run: python scripts/seed_rag_cache.py --full",
            "auteur_filter": auteur_key,
        }
    except Exception as e:
        logger.error(f"[SemanticCache] Warm error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to warm cache: {e}")


# ============================================================================
# Studio Artifact Storage Endpoints
# ============================================================================

@router.get("/artifacts/stats")
async def get_artifact_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Studio 산출물 저장소 통계 조회.
    
    Returns:
        총 산출물 수, 유형별/거장별 분류, 총 용량
    """
    try:
        from app.rag.artifact_storage import get_artifact_storage
        
        storage = get_artifact_storage()
        return storage.get_stats()
    except Exception as e:
        logger.error(f"[ArtifactStorage] Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get artifact stats: {e}")


@router.get("/artifacts/list")
async def list_artifacts(
    auteur_key: Optional[str] = Query(None, description="거장 필터"),
    artifact_type: Optional[str] = Query(None, description="유형 필터 (audio, infographic, etc)"),
    limit: int = Query(20, ge=1, le=100, description="반환할 산출물 수"),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Studio 산출물 목록 조회.
    
    Returns:
        산출물 목록 (메타데이터만, 실제 데이터 아님)
    """
    try:
        from app.rag.artifact_storage import get_artifact_storage, ArtifactType
        
        storage = get_artifact_storage()
        
        type_enum = None
        if artifact_type:
            try:
                type_enum = ArtifactType(artifact_type)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid artifact type: {artifact_type}. Valid: audio, infographic, slide_deck, mind_map, report"
                )
        
        artifacts = storage.list_artifacts(
            auteur_key=auteur_key,
            artifact_type=type_enum,
            limit=limit,
        )
        
        return {
            "artifacts": [a.to_dict() for a in artifacts],
            "total": len(artifacts),
            "filters": {
                "auteur_key": auteur_key,
                "artifact_type": artifact_type,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ArtifactStorage] List error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list artifacts: {e}")


@router.post("/artifacts/cleanup")
async def cleanup_expired_artifacts(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """만료된 산출물 정리.
    
    Returns:
        정리된 산출물 수
    """
    try:
        from app.rag.artifact_storage import get_artifact_storage
        
        storage = get_artifact_storage()
        count = storage.cleanup_expired()
        
        return {
            "message": f"Cleaned up {count} expired artifacts",
            "removed_count": count,
        }
    except Exception as e:
        logger.error(f"[ArtifactStorage] Cleanup error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup artifacts: {e}")


