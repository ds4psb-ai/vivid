"""
P5: Strategy Selector - QueryType to Retrieval Strategy Mapping.

QueryType에 따라 최적의 검색 전략을 선택합니다.

Strategy Types:
    1. direct_llm: 검색 생략, LLM 파라메트릭 지식만 사용
    2. minimal_rag: 최소 검색 (창작 쿼리용)
    3. ensemble_rrf: 표준 검색 (P3 Weighted RRF)
    4. grounding_first: Web Grounding 우선 (최신 정보용)
    5. full_pipeline: 전체 파이프라인 (Reranker + CRAG 포함)

Usage:
    from app.rag.strategy_selector import select_strategy, Strategy

    strategy = await select_strategy(
        query="봉준호 롱테이크",
        app_key="dimension.aesthetic.direct"
    )
    # Strategy(
    #     name="ensemble_rrf",
    #     skip_retrieval=False,
    #     use_reranker=True,
    #     ...
    # )
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from app.rag.query_classifier import (
    QueryType,
    RoutingConfig,
    classify_query,
    get_classification_result,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Strategy Dataclass
# ============================================================================


@dataclass
class Strategy:
    """검색 전략 설정.

    Attributes:
        name: 전략 이름
        skip_retrieval: 검색 생략 여부
        backends: 사용할 백엔드 목록
        use_reranker: Reranker 사용 여부
        use_grounding: Web Grounding 사용 여부
        use_crag: CRAG (Corrective RAG) 사용 여부
        max_sources: 최대 소스 수
        min_confidence: 최소 신뢰도 임계값
        estimated_cost: 예상 비용 (USD)
        estimated_latency_ms: 예상 지연 (밀리초)
    """

    name: str
    skip_retrieval: bool = False
    backends: list[str] = field(default_factory=lambda: ["qdrant_hybrid", "notebooklm"])
    use_reranker: bool = True
    use_grounding: bool = False
    use_crag: bool = True
    max_sources: int = 5
    min_confidence: float = 0.6
    estimated_cost: float = 0.005
    estimated_latency_ms: int = 200

    def __str__(self) -> str:
        return (
            f"Strategy({self.name}, "
            f"skip={self.skip_retrieval}, "
            f"backends={self.backends}, "
            f"reranker={self.use_reranker})"
        )


# ============================================================================
# Predefined Strategies
# ============================================================================

STRATEGIES: dict[str, Strategy] = {
    "direct_llm": Strategy(
        name="direct_llm",
        skip_retrieval=True,
        backends=[],
        use_reranker=False,
        use_grounding=False,
        use_crag=False,
        max_sources=0,
        min_confidence=0.0,
        estimated_cost=0.001,
        estimated_latency_ms=100,
    ),
    "minimal_rag": Strategy(
        name="minimal_rag",
        skip_retrieval=False,  # Optional retrieval
        backends=["qdrant_hybrid"],  # Only Qdrant
        use_reranker=False,
        use_grounding=False,
        use_crag=False,
        max_sources=2,
        min_confidence=0.5,
        estimated_cost=0.002,
        estimated_latency_ms=150,
    ),
    "ensemble_rrf": Strategy(
        name="ensemble_rrf",
        skip_retrieval=False,
        backends=["qdrant_hybrid", "notebooklm"],
        use_reranker=True,
        use_grounding=False,
        use_crag=True,
        max_sources=5,
        min_confidence=0.6,
        estimated_cost=0.005,
        estimated_latency_ms=200,
    ),
    "grounding_first": Strategy(
        name="grounding_first",
        skip_retrieval=False,
        backends=["tavily_grounding"],  # Web grounding 우선
        use_reranker=False,
        use_grounding=True,
        use_crag=False,
        max_sources=5,
        min_confidence=0.7,
        estimated_cost=0.008,
        estimated_latency_ms=300,
    ),
    "full_pipeline": Strategy(
        name="full_pipeline",
        skip_retrieval=False,
        backends=["qdrant_hybrid", "notebooklm", "tavily_grounding"],
        use_reranker=True,
        use_grounding=True,
        use_crag=True,
        max_sources=10,
        min_confidence=0.7,
        estimated_cost=0.012,
        estimated_latency_ms=500,
    ),
}

# QueryType → Strategy Name mapping
QUERY_TYPE_TO_STRATEGY: dict[QueryType, str] = {
    QueryType.SIMPLE_FACTUAL: "direct_llm",
    QueryType.CREATIVE: "minimal_rag",
    QueryType.DOMAIN_SPECIFIC: "ensemble_rrf",
    QueryType.RECENCY_REQUIRED: "grounding_first",
    QueryType.MULTI_HOP: "full_pipeline",
    QueryType.AMBIGUOUS: "ensemble_rrf",  # Safe default
}


# ============================================================================
# Strategy Selection Functions
# ============================================================================


def get_strategy_for_query_type(query_type: QueryType) -> Strategy:
    """QueryType에 대한 Strategy 반환.

    Args:
        query_type: 쿼리 유형

    Returns:
        해당 Strategy 객체
    """
    strategy_name = QUERY_TYPE_TO_STRATEGY.get(query_type, "ensemble_rrf")
    return STRATEGIES[strategy_name]


async def select_strategy(
    query: str,
    app_key: Optional[str] = None,
    routing_config: Optional[RoutingConfig] = None,
) -> Strategy:
    """쿼리에 대한 최적 전략 선택.

    1. QueryType 분류
    2. QueryType → Strategy 매핑
    3. App-level override 적용 (optional)

    Args:
        query: 입력 쿼리
        app_key: 앱 키 (매니페스트 기반 override용)
        routing_config: 라우팅 설정 (None이면 기본값)

    Returns:
        선택된 Strategy 객체
    """
    # Step 1: Classify query
    query_type, confidence = await classify_query(query, routing_config)

    # Step 2: Get base strategy
    strategy = get_strategy_for_query_type(query_type)

    # Step 3: Apply app-level overrides (if manifest exists)
    if app_key:
        strategy = _apply_manifest_overrides(strategy, app_key)

    logger.info(
        f"[StrategySelector] Query='{query[:30]}...' → "
        f"Type={query_type.value} (conf={confidence:.2f}) → "
        f"Strategy={strategy.name}"
    )

    return strategy


def _apply_manifest_overrides(strategy: Strategy, app_key: str) -> Strategy:
    """앱 매니페스트 기반 전략 override.

    Args:
        strategy: 기본 전략
        app_key: 앱 키

    Returns:
        Override된 Strategy (변경 없으면 원본)
    """
    try:
        from app.rag.manifest_loader import get_manifest

        manifest = get_manifest(app_key)
        if manifest is None:
            return strategy

        # Reranker override
        if manifest.reranker and not manifest.reranker.enabled:
            strategy.use_reranker = False

        # Backend override
        if manifest.backends:
            enabled_backends = [b.id for b in manifest.backends if b.enabled]
            if enabled_backends:
                strategy.backends = enabled_backends

        # Search limit override
        if manifest.search_limit:
            strategy.max_sources = manifest.search_limit

        # Min score override
        if manifest.min_score:
            strategy.min_confidence = manifest.min_score

        return strategy

    except Exception as e:
        logger.warning(f"[StrategySelector] Manifest override failed: {e}")
        return strategy


# ============================================================================
# Strategy Result with Classification Details
# ============================================================================


@dataclass
class StrategySelectionResult:
    """전략 선택 결과 (분류 상세 정보 포함).

    Attributes:
        strategy: 선택된 전략
        query_type: 분류된 쿼리 유형
        classification_confidence: 분류 신뢰도
        classifier_used: 사용된 분류기
        matched_example: 매칭된 예시 (SemanticRouter 사용 시)
        classification_latency_ms: 분류 지연 시간
    """

    strategy: Strategy
    query_type: QueryType
    classification_confidence: float
    classifier_used: str
    matched_example: Optional[str]
    classification_latency_ms: int


async def select_strategy_with_details(
    query: str,
    app_key: Optional[str] = None,
    routing_config: Optional[RoutingConfig] = None,
) -> StrategySelectionResult:
    """상세 전략 선택 결과 반환.

    Args:
        query: 입력 쿼리
        app_key: 앱 키
        routing_config: 라우팅 설정

    Returns:
        StrategySelectionResult with full details
    """
    # Get detailed classification
    classification = await get_classification_result(query, routing_config)

    # Get strategy
    strategy = get_strategy_for_query_type(classification.query_type)

    # Apply overrides
    if app_key:
        strategy = _apply_manifest_overrides(strategy, app_key)

    return StrategySelectionResult(
        strategy=strategy,
        query_type=classification.query_type,
        classification_confidence=classification.confidence,
        classifier_used=classification.classifier_used,
        matched_example=classification.matched_example,
        classification_latency_ms=classification.latency_ms or 0,
    )


# ============================================================================
# Utility Functions
# ============================================================================


def list_strategies() -> list[str]:
    """사용 가능한 전략 목록 반환."""
    return list(STRATEGIES.keys())


def get_strategy_by_name(name: str) -> Optional[Strategy]:
    """이름으로 Strategy 조회."""
    return STRATEGIES.get(name)


def estimate_cost(query_type: QueryType) -> float:
    """QueryType에 대한 예상 비용 반환 (USD)."""
    strategy = get_strategy_for_query_type(query_type)
    return strategy.estimated_cost


def estimate_latency(query_type: QueryType) -> int:
    """QueryType에 대한 예상 지연 반환 (ms)."""
    strategy = get_strategy_for_query_type(query_type)
    return strategy.estimated_latency_ms
