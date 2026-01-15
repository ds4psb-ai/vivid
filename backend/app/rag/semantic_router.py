"""
P5: Semantic Router - Fast Query Classification via Embeddings.

MiniLM-L6 임베딩 기반 빠른 쿼리 라우팅 (목표: 15ms).

Architecture:
    1. Route Examples (_routes.yaml)에서 유형별 예시 로드
    2. 쿼리 임베딩 생성 (MiniLM-L6, 384-dim)
    3. 각 유형 예시와 코사인 유사도 계산
    4. 가장 높은 유사도의 QueryType 반환

Performance:
    - 첫 호출: ~500ms (모델 로딩)
    - 이후 호출: ~10-20ms (임베딩만)
    - 캐싱: Route examples 임베딩 사전 계산

Usage:
    from app.rag.semantic_router import get_semantic_router

    router = get_semantic_router()
    query_type, confidence = await router.classify("봉준호 롱테이크")
    # QueryType.DOMAIN_SPECIFIC, 0.85
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import yaml

from app.rag.query_classifier import QueryType

logger = logging.getLogger(__name__)


# ============================================================================
# Singleton Router Instance
# ============================================================================

_router_instance: Optional["SemanticRouter"] = None


def get_semantic_router() -> "SemanticRouter":
    """SemanticRouter 싱글톤 인스턴스 반환."""
    global _router_instance
    if _router_instance is None:
        _router_instance = SemanticRouter()
    return _router_instance


def reset_semantic_router() -> None:
    """SemanticRouter 인스턴스 리셋 (테스트용)."""
    global _router_instance
    _router_instance = None


# ============================================================================
# Semantic Router Implementation
# ============================================================================


class SemanticRouter:
    """임베딩 기반 Semantic Router (15ms target).

    MiniLM-L6 모델을 사용하여 쿼리를 QueryType으로 분류합니다.
    Route examples는 _routes.yaml에서 로드되며, 임베딩은 캐싱됩니다.

    Attributes:
        _model: SentenceTransformer 모델 인스턴스
        _routes: 로드된 라우트 설정
        _route_embeddings: 캐싱된 라우트 예시 임베딩
    """

    _model = None  # Class-level model cache
    _routes: Optional[dict] = None
    _route_embeddings: Optional[dict] = None

    def __init__(self):
        """SemanticRouter 초기화."""
        self._ensure_model_loaded()
        self._load_routes()

    def _ensure_model_loaded(self) -> None:
        """모델 로딩 (lazy, singleton)."""
        if SemanticRouter._model is None:
            start = time.time()
            try:
                from sentence_transformers import SentenceTransformer

                # MiniLM-L6: 384-dim, fast, good quality
                SemanticRouter._model = SentenceTransformer(
                    "sentence-transformers/all-MiniLM-L6-v2"
                )
                logger.info(
                    f"[SemanticRouter] Model loaded in {(time.time() - start)*1000:.0f}ms"
                )
            except ImportError:
                logger.error(
                    "[SemanticRouter] sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )
                raise

    def _load_routes(self) -> None:
        """Route examples YAML 로드 및 임베딩 사전 계산."""
        if SemanticRouter._routes is not None:
            return

        routes_path = Path(__file__).parent / "manifests" / "_routes.yaml"

        if not routes_path.exists():
            logger.warning(
                f"[SemanticRouter] Routes file not found: {routes_path}. "
                "Using default routes."
            )
            SemanticRouter._routes = self._get_default_routes()
        else:
            with open(routes_path, "r", encoding="utf-8") as f:
                SemanticRouter._routes = yaml.safe_load(f)

        # Pre-compute embeddings for route examples
        self._compute_route_embeddings()

    def _get_default_routes(self) -> dict:
        """기본 라우트 설정 반환 (YAML 없을 때)."""
        return {
            "routes": [
                {
                    "type": "simple_factual",
                    "examples": [
                        "Python이란?",
                        "HTTP 상태코드 200 의미",
                        "API란 무엇인가?",
                        "JSON 형식 설명",
                    ],
                },
                {
                    "type": "domain_specific",
                    "examples": [
                        "봉준호 감독의 롱테이크 기법",
                        "기생충 계단 장면 분석",
                        "왕가위 색감 스타일",
                        "타란티노 대화 스타일",
                    ],
                },
                {
                    "type": "recency_required",
                    "examples": [
                        "2026년 AI 트렌드",
                        "최신 Gemini 기능",
                        "오늘 날씨",
                        "현재 환율",
                    ],
                },
                {
                    "type": "multi_hop",
                    "examples": [
                        "왜 기생충의 계단이 상징적인가 설명해줘",
                        "봉준호와 놀란의 시각 스타일 비교",
                        "한국 영화가 세계 시장에서 성공한 이유 분석",
                    ],
                },
                {
                    "type": "creative",
                    "examples": [
                        "영화 시놉시스 써줘",
                        "캐릭터 이름 추천해줘",
                        "로맨스 영화 아이디어",
                        "대사 작성해줘",
                    ],
                },
            ]
        }

    def _compute_route_embeddings(self) -> None:
        """라우트 예시 임베딩 사전 계산 및 캐싱."""
        if SemanticRouter._route_embeddings is not None:
            return

        start = time.time()
        SemanticRouter._route_embeddings = {}

        for route in SemanticRouter._routes.get("routes", []):
            query_type = route["type"]
            examples = route.get("examples", [])

            if not examples:
                continue

            # Encode all examples at once (batched for efficiency)
            embeddings = SemanticRouter._model.encode(
                examples,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

            SemanticRouter._route_embeddings[query_type] = {
                "examples": examples,
                "embeddings": embeddings,
            }

        logger.info(
            f"[SemanticRouter] Route embeddings computed in {(time.time() - start)*1000:.0f}ms "
            f"({len(SemanticRouter._route_embeddings)} types)"
        )

    async def classify(
        self,
        query: str,
        threshold: float = 0.7,
    ) -> Tuple[QueryType, float]:
        """쿼리를 QueryType으로 분류.

        Args:
            query: 입력 쿼리
            threshold: 최소 유사도 임계값 (이하면 AMBIGUOUS)

        Returns:
            (QueryType, confidence_score) 튜플
        """
        query_type, confidence, _ = await self.classify_with_details(query, threshold)
        return (query_type, confidence)

    async def classify_with_details(
        self,
        query: str,
        threshold: float = 0.7,
    ) -> Tuple[QueryType, float, Optional[str]]:
        """상세 분류 결과 반환 (매칭된 예시 포함).

        Args:
            query: 입력 쿼리
            threshold: 최소 유사도 임계값

        Returns:
            (QueryType, confidence, matched_example) 튜플
        """
        start = time.time()

        # Encode query
        query_embedding = SemanticRouter._model.encode(
            query,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        best_type = QueryType.AMBIGUOUS
        best_score = 0.0
        best_example: Optional[str] = None

        # Compare with each route type
        for type_name, route_data in SemanticRouter._route_embeddings.items():
            embeddings = route_data["embeddings"]
            examples = route_data["examples"]

            # Cosine similarity (normalized vectors → dot product)
            similarities = np.dot(embeddings, query_embedding)

            # Find best match in this type
            max_idx = int(np.argmax(similarities))
            max_sim = float(similarities[max_idx])

            if max_sim > best_score:
                best_score = max_sim
                try:
                    best_type = QueryType(type_name)
                except ValueError:
                    logger.warning(f"[SemanticRouter] Unknown query type: {type_name}")
                    best_type = QueryType.AMBIGUOUS
                best_example = examples[max_idx]

        # Apply threshold
        if best_score < threshold:
            logger.debug(
                f"[SemanticRouter] Below threshold: {best_score:.3f} < {threshold} "
                f"(would be {best_type.value})"
            )
            best_type = QueryType.AMBIGUOUS

        latency_ms = (time.time() - start) * 1000
        logger.debug(
            f"[SemanticRouter] Classified '{query[:30]}...' as {best_type.value} "
            f"(score={best_score:.3f}, latency={latency_ms:.1f}ms)"
        )

        return (best_type, best_score, best_example)

    def get_route_stats(self) -> dict:
        """라우트 통계 반환 (디버깅용)."""
        if SemanticRouter._route_embeddings is None:
            return {"loaded": False}

        return {
            "loaded": True,
            "types": list(SemanticRouter._route_embeddings.keys()),
            "total_examples": sum(
                len(r["examples"]) for r in SemanticRouter._route_embeddings.values()
            ),
            "embedding_dim": SemanticRouter._model.get_sentence_embedding_dimension()
            if SemanticRouter._model
            else None,
        }


# ============================================================================
# Utility Functions
# ============================================================================


def reload_routes() -> int:
    """Route examples 리로드 (hot-reload용).

    Returns:
        로드된 라우트 타입 수
    """
    SemanticRouter._routes = None
    SemanticRouter._route_embeddings = None

    router = get_semantic_router()
    router._load_routes()

    return len(SemanticRouter._route_embeddings or {})
