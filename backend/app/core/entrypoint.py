"""Unified Query Entrypoint.

통합 오케스트레이션 시스템의 메인 진입점.

기존 hybrid_query()를 대체할 수 있는 단일 함수.

Usage:
    from app.core.entrypoint import unified_query

    # 기본 사용
    result = await unified_query("봉준호 롱테이크 분석")

    # 옵션 지정
    result = await unified_query(
        query="기생충 계단 장면 분석",
        user_id="user_123",
        dimension="4D",
        auteur_key="bong",
    )

    # 결과
    print(result["final_response"])
    print(result["evidence_refs"])
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from app.core.unified_schemas import (
    UnifiedQueryRequest,
    UnifiedQueryResponse,
)
from app.core.unified_state import UnifiedState, create_initial_state
from app.core.graph import get_unified_graph

logger = logging.getLogger(__name__)


async def unified_query(
    query: str,
    *,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    dimension: Optional[str] = None,
    auteur_key: Optional[str] = None,
    skip_cache: bool = False,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """통합 쿼리 실행.

    LangGraph StateGraph를 사용하여 쿼리를 처리합니다.

    Args:
        query: 쿼리 텍스트
        user_id: 사용자 ID (개인화에 사용)
        session_id: 세션 ID (컨텍스트 유지에 사용)
        dimension: 명시적 차원 지정 (1D, 2D, 3D, 4D, QC, AD, AI, VEO, STORY, SOUND)
        auteur_key: 명시적 거장 지정 (bong, kubrick, nolan, tarantino 등)
        skip_cache: 캐시 우회 여부
        request_id: 요청 ID (없으면 자동 생성)

    Returns:
        처리 결과 딕셔너리:
        - final_response: 생성된 응답
        - query_type: 쿼리 유형
        - intent: 사용자 의도
        - confidence: 분류 신뢰도
        - evidence_refs: Evidence references (List[str])
        - sources_used: 사용된 소스 목록
        - dimension: 연관 차원
        - auteur_key: 연관 거장
        - latency_ms: 총 소요 시간
        - cache_hit: 캐시 히트 여부

    Example:
        >>> result = await unified_query("봉준호 롱테이크 분석")
        >>> print(result["final_response"])
        "봉준호 감독의 롱테이크는..."
        >>> print(result["evidence_refs"])
        ["db:notebooklm:doc_123", "db:qdrant:doc_456"]
    """
    start_time = time.perf_counter()

    # 캐시 체크 (skip_cache=False인 경우)
    if not skip_cache:
        cached_result = await _check_cache(query, user_id)
        if cached_result:
            logger.info(f"Cache hit for query: {query[:50]}...")
            cached_result["cache_hit"] = True
            return cached_result

    # 초기 상태 생성
    initial_state = create_initial_state(
        query=query,
        user_id=user_id,
        session_id=session_id,
        dimension=dimension,
        auteur_key=auteur_key,
        request_id=request_id,
    )

    try:
        # 그래프 실행
        graph = get_unified_graph()
        final_state = await graph.ainvoke(initial_state)

        # 결과 변환
        result = _state_to_response(final_state)
        result["latency_ms"] = (time.perf_counter() - start_time) * 1000
        result["cache_hit"] = False

        # 캐시 저장
        if not skip_cache:
            await _save_to_cache(query, user_id, result)

        logger.info(
            f"Unified query complete: query_type={result.get('query_type')}, "
            f"latency={result['latency_ms']:.1f}ms"
        )

        return result

    except Exception as e:
        logger.error(f"Unified query failed: {e}")
        return {
            "final_response": f"요청 처리 중 오류가 발생했습니다: {str(e)}",
            "query_type": "ambiguous",
            "intent": "unknown",
            "confidence": 0.0,
            "evidence_refs": [],
            "sources_used": [],
            "dimension": dimension,
            "auteur_key": auteur_key,
            "latency_ms": (time.perf_counter() - start_time) * 1000,
            "cache_hit": False,
            "error": str(e),
        }


async def unified_query_from_request(
    request: UnifiedQueryRequest,
) -> UnifiedQueryResponse:
    """UnifiedQueryRequest에서 쿼리 실행.

    API 엔드포인트에서 사용하기 위한 래퍼.

    Args:
        request: UnifiedQueryRequest 객체

    Returns:
        UnifiedQueryResponse 객체
    """
    result = await unified_query(
        query=request.query,
        user_id=request.user_id,
        session_id=request.session_id,
        dimension=request.dimension,
        auteur_key=request.auteur_key,
        skip_cache=request.skip_cache,
    )

    return UnifiedQueryResponse(
        response=result.get("final_response", ""),
        query_type=result.get("query_type", "ambiguous"),
        intent=result.get("intent", "unknown"),
        confidence=result.get("confidence", 0.0),
        evidence_refs=result.get("evidence_refs", []),
        sources_used=result.get("sources_used", []),
        dimension=result.get("dimension"),
        auteur_key=result.get("auteur_key"),
        latency_ms=result.get("latency_ms", 0.0),
        cache_hit=result.get("cache_hit", False),
    )


def _state_to_response(state: UnifiedState) -> Dict[str, Any]:
    """UnifiedState → 응답 딕셔너리 변환."""
    # QueryType/Intent enum 값 추출
    query_type = state.get("query_type")
    if hasattr(query_type, "value"):
        query_type = query_type.value

    intent = state.get("intent")
    if hasattr(intent, "value"):
        intent = intent.value

    dimension = state.get("dimension")
    if hasattr(dimension, "value"):
        dimension = dimension.value

    return {
        "final_response": state.get("final_response", ""),
        "query_type": query_type or "ambiguous",
        "intent": intent or "unknown",
        "confidence": state.get("confidence", 0.0),
        "evidence_refs": state.get("evidence_refs", []),
        "sources_used": state.get("selected_sources", []),
        "dimension": dimension,
        "auteur_key": state.get("auteur_key"),
        "retrieved_docs": state.get("retrieved_docs", []),
        "node_outputs": state.get("node_outputs", {}),
        "execution_order": state.get("execution_order", []),
        "request_id": state.get("request_id"),
        "error": state.get("error"),
    }


# =============================================================================
# Cache Integration
# =============================================================================


async def _check_cache(query: str, user_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """시맨틱 캐시 체크.

    기존 semantic_cache.py와 통합.
    """
    try:
        from app.rag.semantic_cache import get_cached_response

        cached = await get_cached_response(query, user_id=user_id)
        if cached:
            return cached
    except ImportError:
        logger.debug("Semantic cache not available")
    except Exception as e:
        logger.warning(f"Cache check failed: {e}")

    return None


async def _save_to_cache(
    query: str,
    user_id: Optional[str],
    result: Dict[str, Any],
) -> None:
    """결과를 캐시에 저장."""
    try:
        from app.rag.semantic_cache import save_to_cache

        await save_to_cache(
            query=query,
            response=result,
            user_id=user_id,
        )
    except ImportError:
        logger.debug("Semantic cache not available")
    except Exception as e:
        logger.warning(f"Cache save failed: {e}")


# =============================================================================
# Backward Compatibility
# =============================================================================


async def unified_query_compat(
    query: str,
    *,
    dimension: Optional[str] = None,
    auteur_key: Optional[str] = None,
    strategy: str = "ensemble_rrf",
    top_k: int = 10,
    **kwargs,
) -> Dict[str, Any]:
    """hybrid_query() 호환 래퍼.

    기존 hybrid_query() 시그니처와 호환되는 인터페이스.

    Args:
        query: 쿼리 텍스트
        dimension: 차원 코드
        auteur_key: 거장 키
        strategy: 검색 전략 (무시됨, 자동 결정)
        top_k: 검색 결과 수 (무시됨, 기본값 사용)
        **kwargs: 추가 인자 (무시됨)

    Returns:
        HybridRAGResult 호환 딕셔너리
    """
    result = await unified_query(
        query=query,
        dimension=dimension,
        auteur_key=auteur_key,
    )

    # HybridRAGResult 형식으로 변환
    return {
        "response": result.get("final_response", ""),
        "sources": result.get("retrieved_docs", []),
        "evidence_refs": result.get("evidence_refs", []),
        "confidence": result.get("confidence", 0.0),
        "metadata": {
            "query_type": result.get("query_type"),
            "intent": result.get("intent"),
            "strategy": "unified_graph",
            "sources_used": result.get("sources_used", []),
            "latency_ms": result.get("latency_ms", 0.0),
        },
    }


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    "unified_query",
    "unified_query_from_request",
    "unified_query_compat",
]
