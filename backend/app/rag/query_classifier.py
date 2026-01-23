"""
P5: Query Classifier - Adaptive RAG Query Type Classification.

쿼리를 유형별로 분류하여 최적의 검색 전략을 선택합니다.

Architecture:
    1. SemanticRouter (Fast Path, ~15ms)
       - MiniLM 임베딩 기반 KNN 매칭
       - Route Examples YAML에서 유사도 계산

    2. LLM Classifier (Fallback)
       - SemanticRouter confidence < threshold 시
       - Gemini 기반 분류 (~200ms)

Usage:
    from app.rag.query_classifier import classify_query, QueryType

    query_type, confidence = await classify_query("봉준호 롱테이크")
    # QueryType.DOMAIN_SPECIFIC, 0.85

Strategy Mapping:
    - simple_factual → direct_llm (Skip Retrieval)
    - creative → minimal_rag (Optional Retrieval)
    - domain_specific → ensemble_rrf (Standard)
    - recency_required → grounding_first (Web Grounding)
    - multi_hop → full_pipeline (All backends)
    - ambiguous → ensemble_rrf (Safe default)
"""
from __future__ import annotations

import logging
from enum import Enum
from typing import Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Query Type Enum
# ============================================================================


class QueryType(str, Enum):
    """쿼리 유형 분류.

    각 유형은 검색 전략과 비용에 영향을 미칩니다.
    """

    # Skip Retrieval 가능 (LLM parametric knowledge 활용)
    SIMPLE_FACTUAL = "simple_factual"
    """일반적인 사실 쿼리.

    예: "Python이란?", "HTTP 상태코드 200 의미"
    전략: direct_llm (검색 생략)
    비용: ~$0.001
    """

    CREATIVE = "creative"
    """창작/생성 쿼리.

    예: "영화 시놉시스 써줘", "캐릭터 이름 추천"
    전략: minimal_rag (선택적 검색)
    비용: ~$0.002
    """

    # Standard Retrieval (Ensemble RRF)
    DOMAIN_SPECIFIC = "domain_specific"
    """도메인 특화 지식 쿼리 (Vivid 영화/감독 지식).

    예: "봉준호 롱테이크", "기생충 계단 장면"
    전략: ensemble_rrf (NotebookLM + Qdrant)
    비용: ~$0.005
    """

    RECENCY_REQUIRED = "recency_required"
    """최신 정보 필요 쿼리.

    예: "2026년 AI 트렌드", "최신 Gemini 기능"
    전략: grounding_first (Web Grounding 우선)
    비용: ~$0.008
    """

    # Full Pipeline (Most expensive)
    MULTI_HOP = "multi_hop"
    """복합 추론/비교 쿼리.

    예: "왜 기생충의 계단이 상징적인가?", "봉준호 vs 놀란 비교"
    전략: full_pipeline (전체 파이프라인 + Reranker)
    비용: ~$0.012
    """

    # Fallback
    AMBIGUOUS = "ambiguous"
    """분류 불확실 (SemanticRouter confidence < threshold).

    전략: ensemble_rrf (안전한 기본값)
    비용: ~$0.006
    """


# ============================================================================
# Pydantic Schemas
# ============================================================================


class QueryClassificationResult(BaseModel):
    """쿼리 분류 결과."""

    query_type: QueryType
    """분류된 쿼리 유형."""

    confidence: float = Field(ge=0.0, le=1.0)
    """분류 신뢰도 (0.0 ~ 1.0)."""

    classifier_used: str
    """사용된 분류기 ("semantic_router" or "llm_classifier")."""

    matched_example: Optional[str] = None
    """매칭된 라우트 예시 (SemanticRouter 사용 시)."""

    latency_ms: Optional[int] = None
    """분류 지연 시간 (밀리초)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query_type": "domain_specific",
                "confidence": 0.87,
                "classifier_used": "semantic_router",
                "matched_example": "봉준호 감독의 롱테이크 기법",
                "latency_ms": 12,
            }
        }
    )


class RoutingConfig(BaseModel):
    """P5 라우팅 설정 (YAML Manifest용).

    dimension.aesthetic.yaml 예시:
        routing:
          enabled: true
          semantic_threshold: 0.7
          llm_fallback: true
          skip_retrieval_types:
            - simple_factual
            - creative
    """

    enabled: bool = True
    """P5 Adaptive RAG 활성화 여부."""

    semantic_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    """SemanticRouter 최소 신뢰도 임계값.

    이 값보다 낮으면 LLM Classifier 폴백.
    """

    llm_fallback: bool = True
    """LLM Classifier 폴백 활성화 여부.

    False면 threshold 미만 시 AMBIGUOUS 반환.
    """

    skip_retrieval_types: list[QueryType] = Field(
        default_factory=lambda: [QueryType.SIMPLE_FACTUAL, QueryType.CREATIVE]
    )
    """검색을 생략할 쿼리 유형 목록."""

    cache_embeddings: bool = True
    """Route examples 임베딩 캐싱 여부 (성능 최적화)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "enabled": True,
                "semantic_threshold": 0.7,
                "llm_fallback": True,
                "skip_retrieval_types": ["simple_factual", "creative"],
                "cache_embeddings": True,
            }
        }
    )


# ============================================================================
# Default Routing Config
# ============================================================================

DEFAULT_ROUTING_CONFIG = RoutingConfig()

# ============================================================================
# Strategy Mapping
# ============================================================================

STRATEGY_MAP: dict[QueryType, str] = {
    QueryType.SIMPLE_FACTUAL: "direct_llm",
    QueryType.CREATIVE: "minimal_rag",
    QueryType.DOMAIN_SPECIFIC: "ensemble_rrf",
    QueryType.RECENCY_REQUIRED: "grounding_first",
    QueryType.MULTI_HOP: "full_pipeline",
    QueryType.AMBIGUOUS: "ensemble_rrf",
}

COST_ESTIMATE: dict[QueryType, float] = {
    QueryType.SIMPLE_FACTUAL: 0.001,
    QueryType.CREATIVE: 0.002,
    QueryType.DOMAIN_SPECIFIC: 0.005,
    QueryType.RECENCY_REQUIRED: 0.008,
    QueryType.MULTI_HOP: 0.012,
    QueryType.AMBIGUOUS: 0.006,
}


def get_strategy(query_type: QueryType) -> str:
    """QueryType에 대한 검색 전략 반환.

    Args:
        query_type: 쿼리 유형

    Returns:
        전략 이름 (direct_llm, minimal_rag, ensemble_rrf, grounding_first, full_pipeline)
    """
    return STRATEGY_MAP.get(query_type, "ensemble_rrf")


def get_cost_estimate(query_type: QueryType) -> float:
    """QueryType에 대한 예상 비용 반환 (USD).

    Args:
        query_type: 쿼리 유형

    Returns:
        예상 비용 (USD)
    """
    return COST_ESTIMATE.get(query_type, 0.006)


def should_skip_retrieval(
    query_type: QueryType,
    config: Optional[RoutingConfig] = None,
) -> bool:
    """해당 쿼리 유형에서 검색을 생략해야 하는지 판단.

    Args:
        query_type: 쿼리 유형
        config: 라우팅 설정 (None이면 기본값 사용)

    Returns:
        True면 검색 생략 (Direct LLM)
    """
    if config is None:
        config = DEFAULT_ROUTING_CONFIG

    return query_type in config.skip_retrieval_types


# ============================================================================
# High-level Classification Function (will use SemanticRouter + LLM Classifier)
# ============================================================================

# Import will be added after semantic_router.py is created
_semantic_router = None
_llm_classifier = None


async def classify_query(
    query: str,
    config: Optional[RoutingConfig] = None,
) -> Tuple[QueryType, float]:
    """쿼리를 QueryType으로 분류.

    SemanticRouter를 먼저 시도하고, 신뢰도가 낮으면 LLM Classifier 폴백.

    Args:
        query: 입력 쿼리
        config: 라우팅 설정 (None이면 기본값 사용)

    Returns:
        (QueryType, confidence_score) 튜플
    """
    if config is None:
        config = DEFAULT_ROUTING_CONFIG

    if not config.enabled:
        # P5 비활성화 시 기본값 반환
        logger.debug("[QueryClassifier] Routing disabled, returning DOMAIN_SPECIFIC")
        return (QueryType.DOMAIN_SPECIFIC, 1.0)

    # Lazy import to avoid circular dependencies
    from app.rag.semantic_router import get_semantic_router

    router = get_semantic_router()

    # Step 1: SemanticRouter (Fast Path)
    query_type, confidence = await router.classify(
        query=query,
        threshold=config.semantic_threshold,
    )

    if query_type != QueryType.AMBIGUOUS:
        logger.debug(
            f"[QueryClassifier] SemanticRouter: {query_type.value} (confidence={confidence:.2f})"
        )
        return (query_type, confidence)

    # Step 2: LLM Classifier Fallback
    if config.llm_fallback:
        from app.rag.llm_classifier import classify_with_llm

        query_type, confidence = await classify_with_llm(query)
        logger.debug(
            f"[QueryClassifier] LLM Classifier: {query_type.value} (confidence={confidence:.2f})"
        )
        return (query_type, confidence)

    # Fallback to AMBIGUOUS if LLM classifier disabled
    logger.debug(
        f"[QueryClassifier] Fallback to AMBIGUOUS (SemanticRouter confidence={confidence:.2f})"
    )
    return (QueryType.AMBIGUOUS, confidence)


async def get_classification_result(
    query: str,
    config: Optional[RoutingConfig] = None,
) -> QueryClassificationResult:
    """상세 분류 결과 반환 (latency, matched_example 포함).

    Args:
        query: 입력 쿼리
        config: 라우팅 설정

    Returns:
        QueryClassificationResult with full details
    """
    import time

    start_time = time.time()

    if config is None:
        config = DEFAULT_ROUTING_CONFIG

    if not config.enabled:
        return QueryClassificationResult(
            query_type=QueryType.DOMAIN_SPECIFIC,
            confidence=1.0,
            classifier_used="disabled",
            latency_ms=0,
        )

    from app.rag.semantic_router import get_semantic_router

    router = get_semantic_router()

    # SemanticRouter with full result
    query_type, confidence, matched_example = await router.classify_with_details(
        query=query,
        threshold=config.semantic_threshold,
    )

    classifier_used = "semantic_router"

    if query_type == QueryType.AMBIGUOUS and config.llm_fallback:
        from app.rag.llm_classifier import classify_with_llm

        query_type, confidence = await classify_with_llm(query)
        classifier_used = "llm_classifier"
        matched_example = None

    latency_ms = int((time.time() - start_time) * 1000)

    return QueryClassificationResult(
        query_type=query_type,
        confidence=confidence,
        classifier_used=classifier_used,
        matched_example=matched_example,
        latency_ms=latency_ms,
    )


# ============================================================================
# P7 Self-Correction Hooks
# ============================================================================


async def get_experiment_config(
    user_id: str,
    db: "AsyncSession",  # type: ignore
) -> Optional[RoutingConfig]:
    """P7 A/B 테스트에서 사용자별 라우팅 설정 조회.

    A/B 테스트가 실행 중이면 실험 variant에 따라 다른 설정 반환.

    Args:
        user_id: 사용자 ID (해싱용)
        db: Database session

    Returns:
        실험 variant의 RoutingConfig 또는 None (실험 없음)
    """
    try:
        from app.experiments.ab_testing import get_ab_testing

        ab_service = get_ab_testing()

        # Check threshold tuning experiment
        assignment = await ab_service.assign_variant(
            experiment_key="p7_threshold_tuning_active",
            user_id=user_id,
            db=db,
        )

        if assignment and not assignment.is_control:
            # Treatment variant - use tuned thresholds
            payload = assignment.payload
            if payload:
                return RoutingConfig(
                    enabled=True,
                    semantic_threshold=payload.get("semantic_threshold", 0.7),
                    llm_fallback=True,
                    skip_retrieval_types=[
                        QueryType(t) for t in payload.get(
                            "skip_retrieval_types",
                            ["simple_factual", "creative"]
                        )
                    ],
                )

        return None  # Use default config

    except Exception as e:
        logger.debug(f"[QueryClassifier] Experiment config lookup failed: {e}")
        return None


def get_classification_prompt_for_experiment(
    experiment_key: str,
    variant_name: str = "treatment",
) -> Optional[str]:
    """P7 A/B 테스트 variant의 분류 프롬프트 조회.

    PromptTuner 실험에서 사용할 개선된 프롬프트를 조회합니다.

    Args:
        experiment_key: 실험 키
        variant_name: variant 이름 (기본: treatment)

    Returns:
        프롬프트 문자열 또는 None
    """
    try:
        from app.services.prompt_tuner import get_prompt_tuner

        tuner = get_prompt_tuner()

        # If this experiment's treatment is active, return improved prompt
        # This is a simplified version - in production, would query DB
        return tuner.get_current_prompt()

    except Exception as e:
        logger.debug(f"[QueryClassifier] Experiment prompt lookup failed: {e}")
        return None


async def classify_query_with_experiment(
    query: str,
    user_id: str,
    db: "AsyncSession",  # type: ignore
    config: Optional[RoutingConfig] = None,
) -> Tuple[QueryType, float]:
    """P7 A/B 테스트를 고려한 쿼리 분류.

    실험 중인 경우 실험 설정을 사용하여 분류합니다.

    Args:
        query: 입력 쿼리
        user_id: 사용자 ID
        db: Database session
        config: 기본 설정 (실험 없을 때 사용)

    Returns:
        (QueryType, confidence) 튜플
    """
    # Check for experiment config
    experiment_config = await get_experiment_config(user_id, db)

    if experiment_config:
        return await classify_query(query, experiment_config)

    return await classify_query(query, config)
