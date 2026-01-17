"""Multi-RAG Orchestrator.

여러 RAG 소스에 병렬 쿼리하고 결과를 융합하는 오케스트레이터.

워크플로우:
1. Router가 최적 소스 선택
2. 선택된 소스에 병렬 쿼리 (asyncio.gather)
3. RRF (Reciprocal Rank Fusion)로 결과 융합
4. Reranker로 최종 정렬 (선택적)

References:
    - LangGraph Send pattern (parallel fan-out)
    - RAG Fusion paper
    - multi_rag/retriever.py RRF implementation
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from app.rag.router.intelligent_router import IntelligentRAGRouter
from app.rag.router.registry import RAGSourceRegistry
from app.rag.router.types import (
    MultiRAGResult,
    RAGDocument,
    RouteDecision,
    SourceResult,
)

logger = logging.getLogger(__name__)

# Circuit Breaker timeout
DEFAULT_QUERY_TIMEOUT = 10.0  # seconds


class MultiRAGOrchestrator:
    """Multi-RAG 오케스트레이터 - 병렬 실행 및 융합.

    여러 RAG 소스에 병렬로 쿼리하고, RRF로 결과를 융합합니다.
    """

    def __init__(
        self,
        registry: RAGSourceRegistry,
        router: IntelligentRAGRouter,
        reranker: Any = None,
        query_timeout: float = DEFAULT_QUERY_TIMEOUT,
    ) -> None:
        """Initialize orchestrator.

        Args:
            registry: RAG 소스 레지스트리
            router: 지능형 라우터
            reranker: Reranker 인스턴스 (선택)
            query_timeout: 개별 쿼리 타임아웃 (초)
        """
        self.registry = registry
        self.router = router
        self.reranker = reranker
        self.query_timeout = query_timeout

    async def query(
        self,
        query: str,
        context: dict[str, Any] | None = None,
        top_k: int = 10,
        max_sources: int = 3,
    ) -> MultiRAGResult:
        """Multi-RAG 쿼리 실행.

        Args:
            query: 검색 쿼리
            context: 컨텍스트 (dimension, auteur_key, user_id 등)
            top_k: 최종 반환할 문서 수
            max_sources: 최대 사용 소스 수

        Returns:
            MultiRAGResult with fused documents
        """
        start = time.time()
        context = context or {}

        # 1. Route - 최적 소스 선택
        decision = await self.router.route(query, context, max_sources)
        logger.info(
            f"[Orchestrator] Routing decision: {decision.selected_sources} "
            f"(intent={decision.query_intent.value})"
        )

        if not decision.selected_sources:
            return MultiRAGResult(
                documents=[],
                sources_used=[],
                routing_decision=decision,
                total_latency_ms=(time.time() - start) * 1000,
            )

        # 2. Parallel Query
        tasks = []
        for source_id in decision.selected_sources:
            backend = self.registry.get_backend(source_id)
            if backend:
                # 소스별 최적화 쿼리 사용
                sub_query = decision.sub_queries.get(source_id, query)
                tasks.append(
                    self._query_with_timeout(
                        source_id, backend, sub_query, context
                    )
                )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 3. Error Handling
        source_results: list[SourceResult] = []
        for source_id, result in zip(decision.selected_sources, results):
            if isinstance(result, Exception):
                logger.warning(
                    f"[Orchestrator] Source {source_id} failed: {result}"
                )
                source_results.append(
                    SourceResult(
                        source_id=source_id,
                        source_type=self.registry.get_spec(source_id).source_type
                        if self.registry.get_spec(source_id)
                        else None,
                        success=False,
                        error=str(result),
                    )
                )
            else:
                source_results.append(result)

        # 4. RRF Fusion
        valid_results = [r for r in source_results if r.success]
        fused = self._rrf_fusion(valid_results)
        logger.debug(f"[Orchestrator] RRF fused {len(fused)} documents")

        # 5. Rerank (선택적)
        if self.reranker and fused:
            try:
                fused = await self._rerank(query, fused)
            except Exception as e:
                logger.warning(f"[Orchestrator] Rerank failed: {e}")

        # 6. Top-K 선택
        final_docs = fused[:top_k]

        # 7. Evidence refs 생성
        evidence_refs = [doc.evidence_ref for doc in final_docs if doc.evidence_ref]

        return MultiRAGResult(
            documents=final_docs,
            sources_used=[r.source_id for r in valid_results],
            routing_decision=decision,
            total_latency_ms=(time.time() - start) * 1000,
            evidence_refs=evidence_refs,
        )

    async def _query_with_timeout(
        self,
        source_id: str,
        backend: Any,
        query: str,
        context: dict[str, Any],
    ) -> SourceResult:
        """개별 소스 쿼리 (타임아웃 포함).

        Args:
            source_id: 소스 ID
            backend: 백엔드 인스턴스
            query: 쿼리
            context: 컨텍스트

        Returns:
            SourceResult
        """
        start = time.time()
        spec = self.registry.get_spec(source_id)

        try:
            # 타임아웃 적용
            documents = await asyncio.wait_for(
                backend.query(query, filters=context, limit=10),
                timeout=self.query_timeout,
            )

            return SourceResult(
                source_id=source_id,
                source_type=spec.source_type if spec else None,
                documents=documents,
                latency_ms=(time.time() - start) * 1000,
                success=True,
            )

        except asyncio.TimeoutError:
            return SourceResult(
                source_id=source_id,
                source_type=spec.source_type if spec else None,
                latency_ms=(time.time() - start) * 1000,
                success=False,
                error="Query timeout",
            )

        except Exception as e:
            return SourceResult(
                source_id=source_id,
                source_type=spec.source_type if spec else None,
                latency_ms=(time.time() - start) * 1000,
                success=False,
                error=str(e),
            )

    def _rrf_fusion(
        self,
        results: list[SourceResult],
        k: int = 60,
    ) -> list[RAGDocument]:
        """Reciprocal Rank Fusion.

        Score = Σ 1 / (k + rank_i)

        Args:
            results: 소스별 결과
            k: RRF 파라미터 (기본 60)

        Returns:
            융합된 문서 리스트 (점수순)
        """
        scores: dict[str, float] = {}
        docs: dict[str, RAGDocument] = {}

        for source_result in results:
            if not source_result.success:
                continue

            for rank, doc in enumerate(source_result.documents):
                doc_id = doc.id

                # RRF 점수 누적
                scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)

                # 문서 저장 (최고 점수 문서 유지)
                if doc_id not in docs or doc.score > docs[doc_id].score:
                    docs[doc_id] = doc

        # 점수순 정렬
        sorted_ids = sorted(scores.keys(), key=lambda x: -scores[x])

        # RRF 점수로 업데이트
        result = []
        for doc_id in sorted_ids:
            doc = docs[doc_id]
            # RRF 점수를 새 점수로 설정
            result.append(
                RAGDocument(
                    id=doc.id,
                    content=doc.content,
                    score=scores[doc_id],  # RRF score
                    metadata={**doc.metadata, "original_score": doc.score},
                    evidence_ref=doc.evidence_ref,
                    source_id=doc.source_id,
                    source_type=doc.source_type,
                    modality=doc.modality,
                )
            )

        return result

    async def _rerank(
        self,
        query: str,
        documents: list[RAGDocument],
    ) -> list[RAGDocument]:
        """Reranker로 최종 정렬.

        Args:
            query: 원본 쿼리
            documents: RRF 후 문서

        Returns:
            Reranked 문서 리스트
        """
        if not self.reranker:
            return documents

        # Reranker 호출
        reranked = await self.reranker.rerank(
            query=query,
            documents=[(doc.id, doc.content) for doc in documents],
        )

        # ID → 문서 매핑
        doc_map = {doc.id: doc for doc in documents}

        result = []
        for doc_id, new_score in reranked:
            if doc_id in doc_map:
                doc = doc_map[doc_id]
                result.append(
                    RAGDocument(
                        id=doc.id,
                        content=doc.content,
                        score=new_score,
                        metadata={
                            **doc.metadata,
                            "rrf_score": doc.score,
                        },
                        evidence_ref=doc.evidence_ref,
                        source_id=doc.source_id,
                        source_type=doc.source_type,
                        modality=doc.modality,
                    )
                )

        return result


# =============================================================================
# Factory Function
# =============================================================================


async def create_orchestrator(
    db_session_factory: Any = None,
    llm_client: Any = None,
    reranker: Any = None,
) -> MultiRAGOrchestrator:
    """MultiRAGOrchestrator 생성 팩토리.

    Args:
        db_session_factory: DB 세션 팩토리
        llm_client: LLM 클라이언트
        reranker: Reranker 인스턴스

    Returns:
        설정된 MultiRAGOrchestrator
    """
    from app.rag.router.registry import setup_default_registry
    from app.rag.router.intelligent_router import IntelligentRAGRouter

    # Registry 설정
    registry = await setup_default_registry(db_session_factory)

    # Router 생성
    router = IntelligentRAGRouter(registry, llm_client)

    # Orchestrator 생성
    return MultiRAGOrchestrator(
        registry=registry,
        router=router,
        reranker=reranker,
    )


# =============================================================================
# Convenience Function (hybrid_rag.py 대체)
# =============================================================================


async def multi_rag_query(
    query: str,
    dimension: str | None = None,
    auteur_key: str | None = None,
    user_id: str | None = None,
    top_k: int = 10,
) -> MultiRAGResult:
    """간편한 Multi-RAG 쿼리 함수.

    기존 hybrid_query() 대체용.

    Args:
        query: 검색 쿼리
        dimension: Dimension (1D, 2D, 3D, 4D, AD 등)
        auteur_key: 거장 키
        user_id: 사용자 ID
        top_k: 최종 문서 수

    Returns:
        MultiRAGResult

    Example:
        >>> result = await multi_rag_query(
        ...     query="봉준호 감독의 계단 상징",
        ...     dimension="4D",
        ...     auteur_key="bong",
        ... )
        >>> print(result.documents[0].content)
    """
    orchestrator = await create_orchestrator()

    context = {}
    if dimension:
        context["dimension"] = dimension
    if auteur_key:
        context["auteur_key"] = auteur_key
    if user_id:
        context["user_id"] = user_id

    return await orchestrator.query(query, context, top_k)
