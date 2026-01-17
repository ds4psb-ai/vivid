"""Multi-RAG Orchestrator (P0 2026).

다중 RAG 소스 병렬 실행 및 RRF (Reciprocal Rank Fusion) 결과 통합.

Features:
    - 병렬 쿼리 실행 (asyncio.gather)
    - RRF (Reciprocal Rank Fusion) 알고리즘
    - 개별 백엔드 타임아웃 및 fallback
    - Reranker 통합 (선택적)

Reference:
    - RRF Paper: "Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods"
    - k=60 is empirically proven optimal

Usage:
    from app.rag.multi_rag.orchestrator import MultiRAGOrchestrator

    orchestrator = MultiRAGOrchestrator(registry, router)
    result = await orchestrator.query(
        query="봉준호 계단 연출",
        context={"auteur_key": "bong"},
    )
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from app.rag.multi_rag.registry import RAGSourceRegistry
from app.rag.multi_rag.router import IntelligentRAGRouter
from app.rag.multi_rag.types import (
    MultiRAGDocument,
    MultiRAGResult,
    QueryContext,
    RAGSourceSpec,
    RAGSourceType,
    RouteDecision,
)

logger = logging.getLogger(__name__)


class MultiRAGOrchestrator:
    """Multi-RAG 오케스트레이터.

    다중 RAG 소스에서 병렬로 검색하고 RRF로 결과를 통합합니다.

    Architecture:
        1. Router가 최적 소스 선택
        2. 선택된 소스에 병렬 쿼리 (asyncio.gather)
        3. RRF (Reciprocal Rank Fusion)로 결과 융합
        4. (선택) Reranker로 최종 정렬

    Attributes:
        registry: RAG 소스 레지스트리
        router: 지능형 RAG 라우터
        reranker: Reranker 인스턴스 (선택적)
        default_timeout: 개별 백엔드 타임아웃 (초)
        rrf_k: RRF 상수 (기본 60)

    Example:
        >>> orchestrator = MultiRAGOrchestrator(registry, router)
        >>> result = await orchestrator.query(
        ...     query="봉준호 계단 연출 분석",
        ...     context={"auteur_key": "bong", "dimension": "4D"},
        ...     limit=10,
        ... )
        >>> print(f"Found {len(result.documents)} documents from {result.sources_used}")
    """

    def __init__(
        self,
        registry: RAGSourceRegistry,
        router: Optional[IntelligentRAGRouter] = None,
        reranker: Optional[Any] = None,
        default_timeout: float = 10.0,
        rrf_k: int = 60,
    ) -> None:
        """오케스트레이터 초기화.

        Args:
            registry: RAG 소스 레지스트리
            router: 지능형 RAG 라우터 (없으면 자동 생성)
            reranker: Reranker 인스턴스 (선택적)
            default_timeout: 개별 백엔드 타임아웃 (초)
            rrf_k: RRF 상수 (기본 60, 경험적 최적값)
        """
        self.registry = registry
        self.router = router or IntelligentRAGRouter(registry)
        self.reranker = reranker
        self.default_timeout = default_timeout
        self.rrf_k = rrf_k

    async def query(
        self,
        query: str,
        context: Optional[QueryContext] = None,
        limit: int = 10,
        max_sources: Optional[int] = None,
        use_reranker: bool = True,
    ) -> MultiRAGResult:
        """Multi-RAG 쿼리 실행.

        Args:
            query: 검색 쿼리
            context: 추가 컨텍스트 (auteur_key, dimension, user_id 등)
            limit: 최종 반환할 최대 문서 수
            max_sources: 최대 사용 소스 수 (router 기본값 사용 시 None)
            use_reranker: Reranker 사용 여부

        Returns:
            MultiRAGResult with fused documents
        """
        start_time = time.monotonic()
        ctx = context or {}

        # 1. Route: 최적 소스 선택
        decision = await self.router.route(query, ctx, max_sources)

        if not decision.selected_sources:
            return MultiRAGResult(
                documents=[],
                sources_used=[],
                routing_decision=decision,
                total_retrieved=0,
                query_time_ms=int((time.monotonic() - start_time) * 1000),
            )

        # 2. Parallel Query: 선택된 소스에 병렬 쿼리
        backend_results = await self._execute_parallel(
            query=query,
            source_ids=decision.selected_sources,
            filters=self._build_filters(ctx),
            limit=limit * 2,  # Over-fetch for fusion
        )

        # 3. RRF Fusion: 결과 통합
        total_retrieved = sum(len(results) for _, results in backend_results)
        fused_documents = self._rrf_fusion(backend_results, limit=limit)

        # 4. Rerank (선택적)
        reranked = False
        rerank_model: Optional[str] = None

        if use_reranker and self.reranker and fused_documents:
            try:
                fused_documents, rerank_model = await self._rerank(query, fused_documents)
                reranked = True
            except Exception as e:
                logger.warning(f"[MultiRAG] Reranking failed: {e}")

        # 5. Build result
        query_time_ms = int((time.monotonic() - start_time) * 1000)

        logger.info(
            f"[MultiRAG] Query completed | "
            f"sources={decision.selected_sources} | "
            f"retrieved={total_retrieved} -> fused={len(fused_documents)} | "
            f"time={query_time_ms}ms | "
            f"reranked={reranked}"
        )

        return MultiRAGResult(
            documents=fused_documents,
            sources_used=decision.selected_sources,
            routing_decision=decision,
            total_retrieved=total_retrieved,
            query_time_ms=query_time_ms,
            reranked=reranked,
            rerank_model=rerank_model,
        )

    # =========================================================================
    # Parallel Execution
    # =========================================================================

    async def _execute_parallel(
        self,
        query: str,
        source_ids: List[str],
        filters: Optional[Dict[str, Any]],
        limit: int,
    ) -> List[Tuple[str, List[Dict[str, Any]]]]:
        """병렬 쿼리 실행.

        Args:
            query: 검색 쿼리
            source_ids: 쿼리할 소스 ID 목록
            filters: 메타데이터 필터
            limit: 소스당 최대 결과 수

        Returns:
            (source_id, results) 튜플 리스트
        """
        tasks = [
            self._query_source(source_id, query, filters, limit)
            for source_id in source_ids
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 에러 필터링
        valid_results: List[Tuple[str, List[Dict[str, Any]]]] = []
        for source_id, result in zip(source_ids, results):
            if isinstance(result, Exception):
                logger.warning(f"[MultiRAG] Source {source_id} failed: {result}")
                continue
            valid_results.append((source_id, result))

        return valid_results

    async def _query_source(
        self,
        source_id: str,
        query: str,
        filters: Optional[Dict[str, Any]],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """단일 소스 쿼리.

        Args:
            source_id: 소스 ID
            query: 검색 쿼리
            filters: 메타데이터 필터
            limit: 최대 결과 수

        Returns:
            검색 결과 리스트

        Raises:
            asyncio.TimeoutError: 타임아웃 발생 시
            Exception: 쿼리 실패 시
        """
        backend = self.registry.get_backend(source_id)
        if not backend:
            logger.warning(f"[MultiRAG] Backend not found: {source_id}")
            return []

        try:
            results = await asyncio.wait_for(
                backend.query(query, filters=filters, limit=limit),
                timeout=self.default_timeout,
            )

            logger.debug(
                f"[MultiRAG] Source {source_id} returned {len(results)} results"
            )

            return results

        except asyncio.TimeoutError:
            logger.warning(f"[MultiRAG] Source {source_id} timed out")
            raise
        except Exception as e:
            logger.error(f"[MultiRAG] Source {source_id} query failed: {e}")
            raise

    # =========================================================================
    # RRF Fusion
    # =========================================================================

    def _rrf_fusion(
        self,
        backend_results: List[Tuple[str, List[Dict[str, Any]]]],
        limit: int,
    ) -> List[MultiRAGDocument]:
        """Reciprocal Rank Fusion 알고리즘.

        Score = Σ 1 / (k + rank_i)

        Args:
            backend_results: (source_id, results) 튜플 리스트
            limit: 최종 반환할 최대 문서 수

        Returns:
            RRF 스코어로 정렬된 MultiRAGDocument 리스트
        """
        # doc_id -> {rrf_score, best_result, sources, source_type}
        doc_scores: Dict[str, Dict[str, Any]] = {}

        for source_id, results in backend_results:
            spec = self.registry.get_spec(source_id)
            source_type = spec.source_type if spec else RAGSourceType.CUSTOM

            for rank, doc in enumerate(results, start=1):
                doc_id = doc.get("id") or str(hash(doc.get("content", "")))
                rrf_contribution = 1.0 / (self.rrf_k + rank)

                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {
                        "rrf_score": 0.0,
                        "best_result": doc,
                        "sources": [],
                        "source_type": source_type,
                        "max_original_score": doc.get("score", 0.0),
                    }

                doc_scores[doc_id]["rrf_score"] += rrf_contribution
                doc_scores[doc_id]["sources"].append(source_id)

                # 최고 원본 스코어 보존
                original_score = doc.get("score", 0.0)
                if original_score > doc_scores[doc_id]["max_original_score"]:
                    doc_scores[doc_id]["best_result"] = doc
                    doc_scores[doc_id]["max_original_score"] = original_score

        # RRF 스코어로 정렬
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1]["rrf_score"],
            reverse=True,
        )

        # MultiRAGDocument 변환
        fused_documents: List[MultiRAGDocument] = []
        for rank, (doc_id, data) in enumerate(sorted_docs[:limit], start=1):
            best = data["best_result"]
            fused_documents.append(
                MultiRAGDocument(
                    doc_id=doc_id,
                    content=best.get("content", ""),
                    score=data["rrf_score"],
                    source_id=data["sources"][0],  # Primary source
                    source_type=data["source_type"],
                    rank=rank,
                    metadata={
                        **best.get("metadata", {}),
                        "rrf_score": data["rrf_score"],
                        "original_score": data["max_original_score"],
                        "fusion_sources": data["sources"],
                    },
                )
            )

        return fused_documents

    # =========================================================================
    # Reranking
    # =========================================================================

    async def _rerank(
        self,
        query: str,
        documents: List[MultiRAGDocument],
    ) -> Tuple[List[MultiRAGDocument], str]:
        """문서 리랭킹.

        Args:
            query: 검색 쿼리
            documents: 리랭킹할 문서 목록

        Returns:
            (리랭킹된 문서 목록, 모델명)
        """
        # 기존 reranker 인터페이스 사용
        from app.rag.rerankers import DocumentToRerank

        docs_to_rerank = [
            DocumentToRerank(
                id=doc.doc_id,
                text=doc.content[:1000],  # Truncate for reranker
                metadata=doc.metadata,
            )
            for doc in documents
        ]

        rerank_result = await self.reranker.rerank(
            query=query,
            documents=docs_to_rerank,
            top_k=len(documents),
        )

        # Rerank 스코어로 재정렬
        reranked_scores = {
            doc["id"]: doc["rerank_score"]
            for doc in rerank_result.documents
        }

        reranked_docs = sorted(
            documents,
            key=lambda d: reranked_scores.get(d.doc_id, 0.0),
            reverse=True,
        )

        # 순위 재설정 및 rerank_score 추가
        for rank, doc in enumerate(reranked_docs, start=1):
            doc.rank = rank
            doc.metadata["rerank_score"] = reranked_scores.get(doc.doc_id, 0.0)

        return reranked_docs, rerank_result.model

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _build_filters(self, context: QueryContext) -> Optional[Dict[str, Any]]:
        """컨텍스트에서 필터 생성.

        Args:
            context: 쿼리 컨텍스트

        Returns:
            메타데이터 필터 (없으면 None)
        """
        filters: Dict[str, Any] = {}

        if user_id := context.get("user_id"):
            filters["user_id"] = user_id

        if dimension := context.get("dimension"):
            filters["dimension"] = dimension.upper()

        if auteur_key := context.get("auteur_key"):
            filters["auteur_key"] = auteur_key.lower()

        return filters or None


# =============================================================================
# Factory Function
# =============================================================================

def create_orchestrator(
    registry: Optional[RAGSourceRegistry] = None,
    router: Optional[IntelligentRAGRouter] = None,
    reranker: Optional[Any] = None,
) -> MultiRAGOrchestrator:
    """오케스트레이터 팩토리 함수.

    Args:
        registry: RAG 소스 레지스트리 (없으면 글로벌 사용)
        router: 지능형 RAG 라우터 (없으면 자동 생성)
        reranker: Reranker 인스턴스 (선택적)

    Returns:
        MultiRAGOrchestrator 인스턴스
    """
    from app.rag.multi_rag.registry import get_registry

    reg = registry or get_registry()
    rtr = router or IntelligentRAGRouter(reg)

    return MultiRAGOrchestrator(reg, rtr, reranker=reranker)
