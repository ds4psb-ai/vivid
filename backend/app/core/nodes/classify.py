"""Classification Node - 통합 분류기.

4개 분류 시스템을 통합:
1. app/rag/query_classifier.py - QueryType 분류
2. app/rag/semantic_router.py - SemanticRouter (Fast Path)
3. app/agents/intent_router.py - Intent 분류
4. app/workflow/dag_builder.py:IntentAnalyzer - DAG 빌더

Pipeline:
1. Input Sanitization (P0 Security - OWASP 2025)
2. SemanticRouter (Fast Path, ~15ms)
3. 신뢰도 낮으면 LLM Fallback (~200ms)
4. Intent 분류 병행
5. 결과 통합

Usage:
    from app.core.nodes.classify import classify_node

    # LangGraph에서 사용
    result_state = await classify_node(state)
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from app.core.unified_schemas import (
    Dimension,
    Intent,
    QueryType,
    SKIP_RETRIEVAL_TYPES,
)
from app.core.unified_state import UnifiedState, state_with_classification
from app.core.utils.sanitize import (
    sanitize_query,
    detect_injection_attempt,
    calculate_risk_score,
)

logger = logging.getLogger(__name__)

# 신뢰도 임계값
SEMANTIC_ROUTER_THRESHOLD = 0.7
LLM_FALLBACK_THRESHOLD = 0.6

# P0: 위험도 임계값 (이 값 이상이면 처리 거부)
RISK_SCORE_THRESHOLD = 0.8


async def classify_node(state: UnifiedState) -> UnifiedState:
    """쿼리 분류 노드.

    P0 Security → SemanticRouter (Fast Path) → LLM Fallback → Intent 분류.

    Args:
        state: 현재 상태 (query 필수)

    Returns:
        업데이트된 상태 (query_type, intent, confidence 등)
    """
    start_time = time.perf_counter()
    raw_query = state.get("query", "")

    if not raw_query:
        return state_with_classification(
            state,
            query_type=QueryType.AMBIGUOUS,
            intent=Intent.UNKNOWN,
            confidence=0.0,
        )

    # =========================================================================
    # P0 Security: Input Sanitization (OWASP 2025/2026)
    # =========================================================================

    # 1. 위험도 점수 계산
    risk_score = calculate_risk_score(raw_query)

    # 2. 프롬프트 주입 시도 탐지
    is_suspicious, matched_patterns = detect_injection_attempt(raw_query)

    if is_suspicious:
        logger.warning(
            f"[P0 Security] Injection attempt detected: patterns={matched_patterns}, "
            f"risk_score={risk_score:.2f}, query_preview='{raw_query[:80]}...'"
        )

    # 3. 위험도가 임계값 이상이면 안전하게 거부
    if risk_score >= RISK_SCORE_THRESHOLD:
        logger.error(
            f"[P0 Security] Query rejected due to high risk: score={risk_score:.2f}"
        )
        return state_with_classification(
            state,
            query_type=QueryType.AMBIGUOUS,
            intent=Intent.UNKNOWN,
            confidence=0.0,
            skip_retrieval=True,  # 검색도 수행하지 않음
        )

    # 4. 쿼리 정제 (위험 패턴 중화)
    query = sanitize_query(raw_query)

    # 5. 정제 후 빈 쿼리면 거부
    if not query.strip():
        logger.warning("[P0 Security] Query became empty after sanitization")
        return state_with_classification(
            state,
            query_type=QueryType.AMBIGUOUS,
            intent=Intent.UNKNOWN,
            confidence=0.0,
        )

    # =========================================================================
    # 쿼리 분류 (기존 로직)
    # =========================================================================

    try:
        # 1. 기존 분류기 호출 시도
        query_type, confidence, dimension, auteur_key = await _classify_with_existing(
            query,
            explicit_dimension=state.get("dimension"),
            explicit_auteur=state.get("auteur_key"),
        )

        # 2. Intent 분류
        intent = await _classify_intent(query, query_type)

        # 3. Skip retrieval 결정
        skip_retrieval = query_type in SKIP_RETRIEVAL_TYPES

        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Classification complete: query_type={query_type.value}, "
            f"intent={intent.value}, confidence={confidence:.3f}, "
            f"skip_retrieval={skip_retrieval}, latency={latency_ms:.1f}ms"
        )

        return state_with_classification(
            state,
            query_type=query_type,
            intent=intent,
            confidence=confidence,
            skip_retrieval=skip_retrieval,
            dimension=dimension,
            auteur_key=auteur_key,
        )

    except Exception as e:
        logger.error(f"Classification failed: {e}")
        # 실패 시 안전한 기본값
        return state_with_classification(
            state,
            query_type=QueryType.AMBIGUOUS,
            intent=Intent.UNKNOWN,
            confidence=0.0,
            skip_retrieval=False,
        )


async def _classify_with_existing(
    query: str,
    *,
    explicit_dimension: Optional[Dimension] = None,
    explicit_auteur: Optional[str] = None,
) -> tuple[QueryType, float, Optional[Dimension], Optional[str]]:
    """기존 분류기 호출.

    P5 Query Classifier가 있으면 사용, 없으면 폴백.
    """
    dimension = explicit_dimension
    auteur_key = explicit_auteur

    try:
        # SemanticRouter 시도 (Fast Path)
        from app.rag.semantic_router import SemanticRouter

        router = SemanticRouter()
        route_result = await router.classify(query)

        if route_result and route_result.confidence >= SEMANTIC_ROUTER_THRESHOLD:
            query_type = _map_route_to_query_type(route_result.route_type)
            return query_type, route_result.confidence, dimension, auteur_key

    except ImportError:
        logger.debug("SemanticRouter not available, using fallback")
    except Exception as e:
        logger.warning(f"SemanticRouter failed: {e}")

    try:
        # P5 Query Classifier 시도
        from app.rag.query_classifier import classify_query

        result = await classify_query(query)
        if result:
            query_type = QueryType(result.query_type.value)
            return query_type, result.confidence, dimension, auteur_key

    except ImportError:
        logger.debug("Query classifier not available, using fallback")
    except Exception as e:
        logger.warning(f"Query classifier failed: {e}")

    # 폴백: 휴리스틱 분류
    return _heuristic_classify(query), 0.5, dimension, auteur_key


def _map_route_to_query_type(route_type: str) -> QueryType:
    """SemanticRouter route_type → QueryType 매핑."""
    mapping = {
        "simple_factual": QueryType.SIMPLE_FACTUAL,
        "creative": QueryType.CREATIVE,
        "domain_specific": QueryType.DOMAIN_SPECIFIC,
        "recency_required": QueryType.RECENCY_REQUIRED,
        "multi_hop": QueryType.MULTI_HOP,
        "ambiguous": QueryType.AMBIGUOUS,
    }
    return mapping.get(route_type, QueryType.AMBIGUOUS)


def _heuristic_classify(query: str) -> QueryType:
    """휴리스틱 기반 쿼리 분류.

    분류기 실패 시 폴백용.
    패턴 우선순위: multi-hop > recency > creative > domain > simple_factual
    """
    query_lower = query.lower()

    # Multi-hop 패턴 (최우선 - 복합 질문) - 영어/한국어 모두 지원
    multihop_patterns = [
        "왜", "비교", "차이", "차이점", "vs", "versus", "compare",
        "why", "how come", "어떻게 다른", "무엇이 다른",
    ]
    if any(p in query_lower for p in multihop_patterns):
        return QueryType.MULTI_HOP

    # Recency 패턴 (두 번째 우선순위 - 최신 정보 필요)
    recency_patterns = [
        "2023", "2024", "2025", "2026", "최근", "최신", "올해",
        "latest", "recent", "현재", "요즘",
    ]
    if any(p in query_lower for p in recency_patterns):
        return QueryType.RECENCY_REQUIRED

    # Simple factual 패턴
    simple_patterns = [
        "이란?", "란?", "뭐야?", "무엇인가요?", "무엇인가", "뭔가요",
        "what is", "who is", "when was", "what are", "how does",
    ]
    if any(p in query_lower for p in simple_patterns):
        return QueryType.SIMPLE_FACTUAL

    # Creative 패턴
    creative_patterns = ["만들어", "생성해", "써줘", "작성해", "create", "generate", "write"]
    if any(p in query_lower for p in creative_patterns):
        return QueryType.CREATIVE

    # Domain specific 패턴 (Vivid 관련) - 가장 넓은 범위
    domain_patterns = [
        "강주노", "쿠브릭", "테오 에포크", "렉스 볼티지", "감독", "영화",
        "촬영", "카메라", "조명", "미장센", "롱테이크", "컷",
        "기생충", "인셉션", "샤이닝", "킬빌", "장면", "씬",
        "스타일", "연출", "편집", "프레임", "앵글",
    ]
    if any(p in query_lower for p in domain_patterns):
        return QueryType.DOMAIN_SPECIFIC

    return QueryType.AMBIGUOUS


async def _classify_intent(query: str, query_type: QueryType) -> Intent:
    """Intent 분류.

    QueryType과 쿼리 내용을 기반으로 Intent 결정.
    """
    try:
        # 기존 Intent Router 시도
        from app.agents.intent_router import classify

        result = classify(query)
        if result:
            return _map_intent_result(result)

    except ImportError:
        logger.debug("Intent router not available, using fallback")
    except Exception as e:
        logger.warning(f"Intent router failed: {e}")

    # QueryType 기반 폴백
    return _intent_from_query_type(query_type, query)


def _map_intent_result(result: Any) -> Intent:
    """기존 intent_router 결과 → Intent 매핑."""
    intent_str = str(result.intent.value) if hasattr(result.intent, "value") else str(result.intent)

    mapping = {
        "generate_prompt": Intent.GENERATE,
        "create_storyboard": Intent.CREATE,
        "generate_image": Intent.GENERATE,
        "analyze_reference": Intent.ANALYZE,
        "general_chat": Intent.CHAT,
        "workflow_request": Intent.WORKFLOW,
        "quality_check": Intent.VALIDATE,
        "aesthetic_direct": Intent.ANALYZE,
        "persona_analyze": Intent.ANALYZE,
        "veo_generate": Intent.GENERATE,
    }
    return mapping.get(intent_str, Intent.UNKNOWN)


def _intent_from_query_type(query_type: QueryType, query: str) -> Intent:
    """QueryType과 쿼리 내용으로 Intent 추론."""
    query_lower = query.lower()

    # 생성 관련 키워드
    if any(k in query_lower for k in ["만들어", "생성", "프롬프트", "이미지", "비디오"]):
        return Intent.GENERATE

    # 분석 관련 키워드
    if any(k in query_lower for k in ["분석", "해석", "설명", "왜", "어떻게"]):
        return Intent.ANALYZE

    # 검증 관련 키워드
    if any(k in query_lower for k in ["확인", "검토", "체크", "퀄리티"]):
        return Intent.VALIDATE

    # QueryType 기반 폴백
    if query_type == QueryType.CREATIVE:
        return Intent.CREATE
    if query_type == QueryType.SIMPLE_FACTUAL:
        return Intent.CHAT
    if query_type == QueryType.DOMAIN_SPECIFIC:
        return Intent.ANALYZE

    return Intent.UNKNOWN


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    "classify_node",
]
