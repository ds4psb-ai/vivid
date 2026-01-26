"""Unified State for LangGraph StateGraph.

LangGraph TypedDict 기반 단일 상태 정의.

2026 Best Practices:
1. Single TypedDict State - 모든 컨텍스트가 하나의 typed state로 흐름
2. Reducers Only Where Needed - 결과 누적이 필요한 곳만 Annotated[list, add] 사용
3. Immutable by Convention - state는 변경하지 않고 새로운 dict 반환

References:
- LangGraph Low-Level Concepts: https://langchain-ai.github.io/langgraph/concepts/low_level/
- LangGraph Best Practices: https://www.swarnendu.de/blog/langgraph-best-practices/

Usage:
    from app.core.unified_state import UnifiedState, create_initial_state

    # 초기 상태 생성
    state = create_initial_state(
        query="강주노 롱테이크 분석",
        user_id="user_123",
    )

    # 그래프 실행
    result = await graph.ainvoke(state)
"""
from __future__ import annotations

from operator import add
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict
import uuid

from app.core.unified_schemas import (
    CheckpointAction,
    Dimension,
    Intent,
    OrchestrationPattern,
    QueryType,
)


# =============================================================================
# Reducer Functions
# =============================================================================


def merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """두 딕셔너리 병합 (b가 a를 덮어씀)."""
    result = dict(a)
    result.update(b)
    return result


# =============================================================================
# Unified State TypedDict
# =============================================================================


class UnifiedState(TypedDict, total=False):
    """통합 상태 (LangGraph StateGraph용).

    모든 노드가 공유하는 단일 상태 객체.

    Sections:
    - Input: 사용자 입력
    - Classification: 분류 결과 (4개 시스템 통합)
    - Routing: 라우팅 결정 (5개 라우터 통합)
    - Retrieval: 검색 결과 (Reducer로 누적)
    - Execution: 실행 상태
    - Response: 최종 응답
    - Metadata: 추적/디버깅용
    """

    # =========================================================================
    # Input Section
    # =========================================================================

    query: str
    """원본 쿼리 텍스트."""

    user_id: Optional[str]
    """사용자 ID (개인화에 사용)."""

    session_id: Optional[str]
    """세션 ID (컨텍스트 유지에 사용)."""

    # =========================================================================
    # Classification Section (4개 시스템 → 1개로 통합)
    # =========================================================================

    query_type: QueryType
    """쿼리 유형 (simple_factual, creative, domain_specific, etc.)."""

    intent: Intent
    """사용자 의도 (generate, analyze, create, etc.)."""

    confidence: float
    """분류 신뢰도 (0.0 ~ 1.0)."""

    skip_retrieval: bool
    """검색 생략 여부 (simple_factual, creative)."""

    # =========================================================================
    # Routing Section (5개 라우터 → 1개로 통합)
    # =========================================================================

    selected_sources: List[str]
    """선택된 소스 목록 (notebooklm, qdrant, vertex, web)."""

    selected_tools: List[str]
    """선택된 도구 목록 (도구 ID)."""

    dimension: Optional[Dimension]
    """연관 차원."""

    auteur_key: Optional[str]
    """연관 거장 키."""

    strategy: str
    """검색 전략 (direct_llm, minimal_rag, ensemble_rrf, etc.)."""

    pattern: OrchestrationPattern
    """오케스트레이션 패턴."""

    sub_queries: List[str]
    """분해된 서브쿼리 (multi-hop)."""

    # =========================================================================
    # Retrieval Section (Reducer로 누적)
    # =========================================================================

    retrieved_docs: Annotated[List[Dict[str, Any]], add]
    """검색된 문서 목록 (Reducer: 누적)."""

    evidence_refs: Annotated[List[str], add]
    """Evidence references (Reducer: 누적, Vivid 규칙: List[str])."""

    source_results: Dict[str, Any]
    """소스별 원시 결과."""

    rrf_scores: Dict[str, float]
    """RRF 융합 점수."""

    # =========================================================================
    # Execution Section
    # =========================================================================

    current_node: str
    """현재 실행 중인 노드."""

    node_outputs: Annotated[Dict[str, Any], merge_dicts]
    """노드별 출력 (Reducer: 병합)."""

    execution_order: List[str]
    """실행된 노드 순서."""

    # =========================================================================
    # HITL Section
    # =========================================================================

    hitl_checkpoint: Optional[str]
    """현재 HITL 체크포인트 ID."""

    hitl_action: Optional[CheckpointAction]
    """HITL 액션 (approve, reject, modify, skip)."""

    hitl_modified_output: Optional[Any]
    """수정된 출력 (modify 액션 시)."""

    # =========================================================================
    # Response Section
    # =========================================================================

    final_response: Optional[str]
    """최종 생성된 응답."""

    error: Optional[str]
    """에러 메시지 (있는 경우)."""

    # =========================================================================
    # Metadata Section
    # =========================================================================

    request_id: str
    """요청 고유 ID (추적용)."""

    cache_hit: bool
    """캐시 히트 여부."""

    total_latency_ms: float
    """총 소요 시간."""

    node_latencies: Dict[str, float]
    """노드별 소요 시간."""


# =============================================================================
# State Factories
# =============================================================================


def create_initial_state(
    query: str,
    *,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    dimension: Optional[str] = None,
    auteur_key: Optional[str] = None,
    request_id: Optional[str] = None,
) -> UnifiedState:
    """초기 상태 생성.

    Args:
        query: 쿼리 텍스트
        user_id: 사용자 ID
        session_id: 세션 ID
        dimension: 명시적 차원 지정
        auteur_key: 명시적 거장 지정
        request_id: 요청 ID (없으면 자동 생성)

    Returns:
        초기화된 UnifiedState
    """
    dim = None
    if dimension:
        try:
            dim = Dimension(dimension)
        except ValueError:
            pass

    return UnifiedState(
        # Input
        query=query,
        user_id=user_id,
        session_id=session_id,
        # Classification (will be set by classify node)
        query_type=QueryType.AMBIGUOUS,
        intent=Intent.UNKNOWN,
        confidence=0.0,
        skip_retrieval=False,
        # Routing (will be set by route node)
        selected_sources=[],
        selected_tools=[],
        dimension=dim,
        auteur_key=auteur_key,
        strategy="ensemble_rrf",
        pattern=OrchestrationPattern.DIRECT,
        sub_queries=[],
        # Retrieval (will accumulate)
        retrieved_docs=[],
        evidence_refs=[],
        source_results={},
        rrf_scores={},
        # Execution
        current_node="",
        node_outputs={},
        execution_order=[],
        # HITL
        hitl_checkpoint=None,
        hitl_action=None,
        hitl_modified_output=None,
        # Response
        final_response=None,
        error=None,
        # Metadata
        request_id=request_id or str(uuid.uuid4()),
        cache_hit=False,
        total_latency_ms=0.0,
        node_latencies={},
    )


def state_with_classification(
    state: UnifiedState,
    *,
    query_type: QueryType,
    intent: Intent,
    confidence: float,
    skip_retrieval: bool = False,
    dimension: Optional[Dimension] = None,
    auteur_key: Optional[str] = None,
) -> UnifiedState:
    """분류 결과로 상태 업데이트.

    Args:
        state: 현재 상태
        query_type: 쿼리 유형
        intent: 사용자 의도
        confidence: 분류 신뢰도
        skip_retrieval: 검색 생략 여부
        dimension: 연관 차원
        auteur_key: 연관 거장

    Returns:
        업데이트된 상태 (새 dict)
    """
    return {
        **state,
        "query_type": query_type,
        "intent": intent,
        "confidence": confidence,
        "skip_retrieval": skip_retrieval,
        "dimension": dimension or state.get("dimension"),
        "auteur_key": auteur_key or state.get("auteur_key"),
    }


def state_with_routing(
    state: UnifiedState,
    *,
    selected_sources: List[str],
    selected_tools: List[str],
    strategy: str,
    pattern: OrchestrationPattern,
    sub_queries: Optional[List[str]] = None,
) -> UnifiedState:
    """라우팅 결정으로 상태 업데이트.

    Args:
        state: 현재 상태
        selected_sources: 선택된 소스
        selected_tools: 선택된 도구
        strategy: 검색 전략
        pattern: 오케스트레이션 패턴
        sub_queries: 분해된 서브쿼리

    Returns:
        업데이트된 상태 (새 dict)
    """
    return {
        **state,
        "selected_sources": selected_sources,
        "selected_tools": selected_tools,
        "strategy": strategy,
        "pattern": pattern,
        "sub_queries": sub_queries or [],
    }


def state_with_retrieval(
    state: UnifiedState,
    *,
    retrieved_docs: List[Dict[str, Any]],
    evidence_refs: List[str],
    source_results: Optional[Dict[str, Any]] = None,
    rrf_scores: Optional[Dict[str, float]] = None,
) -> UnifiedState:
    """검색 결과로 상태 업데이트.

    Note: retrieved_docs와 evidence_refs는 Reducer로 누적됨.

    Args:
        state: 현재 상태
        retrieved_docs: 검색된 문서
        evidence_refs: Evidence references
        source_results: 소스별 원시 결과
        rrf_scores: RRF 융합 점수

    Returns:
        업데이트된 상태 (새 dict)
    """
    return {
        **state,
        "retrieved_docs": retrieved_docs,  # Reducer가 누적
        "evidence_refs": evidence_refs,    # Reducer가 누적
        "source_results": source_results or state.get("source_results", {}),
        "rrf_scores": rrf_scores or {},
    }


def state_with_response(
    state: UnifiedState,
    *,
    final_response: str,
    total_latency_ms: float = 0.0,
) -> UnifiedState:
    """최종 응답으로 상태 업데이트.

    Args:
        state: 현재 상태
        final_response: 생성된 응답
        total_latency_ms: 총 소요 시간

    Returns:
        업데이트된 상태 (새 dict)
    """
    return {
        **state,
        "final_response": final_response,
        "total_latency_ms": total_latency_ms,
    }


def state_with_error(
    state: UnifiedState,
    *,
    error: str,
) -> UnifiedState:
    """에러로 상태 업데이트.

    Args:
        state: 현재 상태
        error: 에러 메시지

    Returns:
        업데이트된 상태 (새 dict)
    """
    return {
        **state,
        "error": error,
    }


# =============================================================================
# State Utilities
# =============================================================================


def get_context_for_llm(state: UnifiedState) -> str:
    """LLM 호출용 컨텍스트 문자열 생성.

    Args:
        state: 현재 상태

    Returns:
        검색된 문서를 포함한 컨텍스트 문자열
    """
    docs = state.get("retrieved_docs", [])
    if not docs:
        return ""

    context_parts = []
    for i, doc in enumerate(docs[:10], 1):  # 최대 10개
        content = doc.get("content", "")
        source = doc.get("source", "unknown")
        context_parts.append(f"[{i}] ({source})\n{content}")

    return "\n\n---\n\n".join(context_parts)


def should_skip_node(state: UnifiedState, node_name: str) -> bool:
    """노드 실행 스킵 여부 확인.

    Args:
        state: 현재 상태
        node_name: 노드 이름

    Returns:
        스킵 여부
    """
    # 검색 노드는 skip_retrieval이면 스킵
    if node_name == "retrieve" and state.get("skip_retrieval", False):
        return True

    # 에러 발생 시 모든 노드 스킵 (generate 제외)
    if state.get("error") and node_name != "generate":
        return True

    return False


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    "UnifiedState",
    "create_initial_state",
    "state_with_classification",
    "state_with_routing",
    "state_with_retrieval",
    "state_with_response",
    "state_with_error",
    "get_context_for_llm",
    "should_skip_node",
]
