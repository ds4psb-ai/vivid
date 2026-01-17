"""Cross-Modal Retriever.

멀티모달 하이브리드 검색 시스템.
- 크로스모달 검색 (텍스트로 이미지 검색, 이미지로 비디오 검색 등)
- Named Vectors 기반 모달리티별 검색
- Hybrid RRF (Reciprocal Rank Fusion) 융합
- evidence_refs 자동 생성

References:
    - Qdrant Named Vectors Search: https://qdrant.tech/documentation/concepts/search/
    - RRF: https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from app.rag.multi_rag.collection_manager import get_qdrant_client
from app.rag.multi_rag.embedders.base import BaseMultiModalEmbedder
from app.rag.multi_rag.types import (
    ContentType,
    Modality,
    MultiModalQuery,
    MultiModalSearchResult,
    RetrievalResult,
    SearchStrategy,
)

logger = logging.getLogger(__name__)


# =============================================================================
# RRF Fusion
# =============================================================================


def reciprocal_rank_fusion(
    ranked_lists: list[list[tuple[str, float]]],
    k: int = 60,
) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion 알고리즘.

    여러 랭킹 리스트를 RRF로 융합.

    Args:
        ranked_lists: [(doc_id, score), ...] 리스트의 리스트
        k: RRF 상수 (기본 60)

    Returns:
        융합된 [(doc_id, rrf_score), ...] 리스트 (내림차순)
    """
    rrf_scores: dict[str, float] = {}

    for ranked_list in ranked_lists:
        for rank, (doc_id, _score) in enumerate(ranked_list, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank)

    # Sort by RRF score descending
    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results


# =============================================================================
# Cross-Modal Retriever
# =============================================================================


@dataclass
class SearchContext:
    """검색 컨텍스트."""

    query_vector: list[float] | None = None
    query_sparse: dict[int, float] | None = None
    query_modality: Modality = Modality.TEXT


class CrossModalRetriever:
    """크로스모달 검색기.

    Named Vectors를 사용한 멀티모달 하이브리드 검색.

    Features:
        - 크로스모달 검색 (텍스트 → 이미지, 이미지 → 비디오 등)
        - 모달리티별 Named Vector 검색
        - Hybrid Search (Dense + Sparse RRF)
        - 다중 모달리티 동시 검색

    Usage:
        retriever = CrossModalRetriever(embedder, "vivid_multimodal_auteur")
        results = await retriever.search(
            query=MultiModalQuery(
                query_text="cinematic lighting",
                target_modalities=[Modality.IMAGE, Modality.VIDEO],
            )
        )
    """

    def __init__(
        self,
        embedder: BaseMultiModalEmbedder,
        collection_name: str = "vivid_multimodal_auteur",
        client: QdrantClient | None = None,
    ) -> None:
        """Initialize retriever.

        Args:
            embedder: 멀티모달 임베더
            collection_name: Qdrant 컬렉션 이름
            client: Qdrant 클라이언트 (None이면 싱글톤)
        """
        self._embedder = embedder
        self._collection_name = collection_name
        self._client = client or get_qdrant_client()

    # =========================================================================
    # Main Search Methods
    # =========================================================================

    async def search(
        self,
        query: MultiModalQuery,
    ) -> MultiModalSearchResult:
        """멀티모달 검색 실행.

        Args:
            query: 멀티모달 쿼리

        Returns:
            MultiModalSearchResult with results
        """
        start_time = time.time()

        # 1. Generate query embedding
        ctx = await self._embed_query(query)

        # 2. Execute search based on strategy
        if query.search_strategy == SearchStrategy.DENSE_ONLY:
            results = await self._search_dense(query, ctx)
        elif query.search_strategy == SearchStrategy.SPARSE_ONLY:
            results = await self._search_sparse(query, ctx)
        elif query.search_strategy == SearchStrategy.HYBRID_RRF:
            results = await self._search_hybrid_rrf(query, ctx)
        elif query.search_strategy == SearchStrategy.CROSS_MODAL:
            results = await self._search_cross_modal(query, ctx)
        elif query.search_strategy == SearchStrategy.MULTI_MODAL:
            results = await self._search_multi_modal(query, ctx)
        else:
            # Default to hybrid
            results = await self._search_hybrid_rrf(query, ctx)

        search_time = (time.time() - start_time) * 1000

        return MultiModalSearchResult(
            query=query,
            results=results,
            total_found=len(results),
            search_time_ms=search_time,
            strategy_used=query.search_strategy,
            modalities_searched=query.target_modalities,
        )

    async def search_by_text(
        self,
        text: str,
        target_modalities: list[Modality] | None = None,
        top_k: int = 10,
        dimension_filter: str | None = None,
        auteur_filter: str | None = None,
    ) -> MultiModalSearchResult:
        """텍스트 기반 검색 (편의 메서드).

        Args:
            text: 검색 텍스트
            target_modalities: 검색 대상 모달리티
            top_k: 결과 수
            dimension_filter: Dimension 필터
            auteur_filter: Auteur 필터

        Returns:
            검색 결과
        """
        query = MultiModalQuery(
            query_text=text,
            target_modalities=target_modalities or [Modality.TEXT],
            search_strategy=SearchStrategy.HYBRID_RRF,
            top_k=top_k,
            dimension_filter=dimension_filter,
            auteur_filter=auteur_filter,
        )
        return await self.search(query)

    async def cross_modal_search(
        self,
        text: str,
        target_modality: Modality,
        top_k: int = 10,
        auteur_filter: str | None = None,
    ) -> MultiModalSearchResult:
        """크로스모달 검색 (편의 메서드).

        텍스트로 다른 모달리티 검색.

        Args:
            text: 검색 텍스트
            target_modality: 검색 대상 모달리티 (IMAGE, VIDEO 등)
            top_k: 결과 수
            auteur_filter: Auteur 필터

        Returns:
            검색 결과
        """
        query = MultiModalQuery(
            query_text=text,
            target_modalities=[target_modality],
            search_strategy=SearchStrategy.CROSS_MODAL,
            top_k=top_k,
            auteur_filter=auteur_filter,
        )
        return await self.search(query)

    # =========================================================================
    # Query Embedding
    # =========================================================================

    async def _embed_query(self, query: MultiModalQuery) -> SearchContext:
        """쿼리 임베딩 생성.

        Args:
            query: 멀티모달 쿼리

        Returns:
            SearchContext with vectors
        """
        ctx = SearchContext()

        # Text query embedding
        if query.query_text:
            result = await self._embedder.embed_text(query.query_text)
            ctx.query_vector = result.vector
            ctx.query_modality = Modality.TEXT

            # Sparse embedding for hybrid search
            if hasattr(self._embedder, "embed_sparse"):
                sparse_result = await self._embedder.embed_sparse(query.query_text)
                ctx.query_sparse = sparse_result.to_dict()

        # Image query embedding
        elif query.query_image:
            result = await self._embedder.embed_image(query.query_image)
            ctx.query_vector = result.vector
            ctx.query_modality = Modality.IMAGE

        # Audio query embedding
        elif query.query_audio:
            result = await self._embedder.embed_audio(query.query_audio)
            ctx.query_vector = result.vector
            ctx.query_modality = Modality.AUDIO

        return ctx

    # =========================================================================
    # Search Strategies
    # =========================================================================

    async def _search_dense(
        self,
        query: MultiModalQuery,
        ctx: SearchContext,
    ) -> list[RetrievalResult]:
        """Dense vector 검색.

        각 target modality의 Named Vector에서 검색.
        """
        if not ctx.query_vector:
            return []

        all_results: list[RetrievalResult] = []

        for modality in query.target_modalities:
            vector_name = f"{modality.value}_embed"

            # Build filter
            qdrant_filter = self._build_filter(query)

            try:
                results = self._client.search(
                    collection_name=self._collection_name,
                    query_vector=qdrant_models.NamedVector(
                        name=vector_name,
                        vector=ctx.query_vector,
                    ),
                    query_filter=qdrant_filter,
                    limit=query.top_k,
                    with_payload=True,
                )

                for point in results:
                    all_results.append(self._point_to_result(point, modality, vector_name))

            except Exception as e:
                logger.warning(f"[Retriever] Dense search failed for {vector_name}: {e}")

        # Sort by score and limit
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[: query.top_k]

    async def _search_sparse(
        self,
        query: MultiModalQuery,
        ctx: SearchContext,
    ) -> list[RetrievalResult]:
        """Sparse vector (BM25) 검색."""
        if not ctx.query_sparse:
            return []

        qdrant_filter = self._build_filter(query)

        try:
            results = self._client.search(
                collection_name=self._collection_name,
                query_vector=qdrant_models.NamedSparseVector(
                    name="text_bm25",
                    vector=qdrant_models.SparseVector(
                        indices=list(ctx.query_sparse.keys()),
                        values=list(ctx.query_sparse.values()),
                    ),
                ),
                query_filter=qdrant_filter,
                limit=query.top_k,
                with_payload=True,
            )

            return [
                self._point_to_result(point, Modality.TEXT, "text_bm25")
                for point in results
            ]

        except Exception as e:
            logger.warning(f"[Retriever] Sparse search failed: {e}")
            return []

    async def _search_hybrid_rrf(
        self,
        query: MultiModalQuery,
        ctx: SearchContext,
    ) -> list[RetrievalResult]:
        """Hybrid RRF 검색 (Dense + Sparse 융합)."""
        # Get dense results
        dense_results = await self._search_dense(query, ctx)

        # Get sparse results
        sparse_results = await self._search_sparse(query, ctx)

        if not dense_results and not sparse_results:
            return []

        # Prepare ranked lists for RRF
        ranked_lists: list[list[tuple[str, float]]] = []

        if dense_results:
            ranked_lists.append([(r.doc_id, r.score) for r in dense_results])

        if sparse_results:
            ranked_lists.append([(r.doc_id, r.score) for r in sparse_results])

        # RRF fusion
        if len(ranked_lists) < 2:
            return dense_results or sparse_results

        fused = reciprocal_rank_fusion(ranked_lists)

        # Rebuild results with RRF scores
        result_map = {r.doc_id: r for r in dense_results + sparse_results}
        final_results: list[RetrievalResult] = []

        for doc_id, rrf_score in fused[: query.top_k]:
            if doc_id in result_map:
                result = result_map[doc_id]
                result.score = rrf_score  # Update with RRF score
                final_results.append(result)

        return final_results

    async def _search_cross_modal(
        self,
        query: MultiModalQuery,
        ctx: SearchContext,
    ) -> list[RetrievalResult]:
        """크로스모달 검색.

        쿼리 모달리티와 다른 모달리티에서 검색.
        예: 텍스트 쿼리로 이미지/비디오 검색
        """
        if not ctx.query_vector:
            return []

        all_results: list[RetrievalResult] = []
        qdrant_filter = self._build_filter(query)

        for target_modality in query.target_modalities:
            # Skip if same as query modality (unless explicitly requested)
            vector_name = f"{target_modality.value}_embed"

            try:
                # Use query vector to search in target modality's vector space
                # This works because all modalities are in unified embedding space
                results = self._client.search(
                    collection_name=self._collection_name,
                    query_vector=qdrant_models.NamedVector(
                        name=vector_name,
                        vector=ctx.query_vector,
                    ),
                    query_filter=qdrant_filter,
                    limit=query.top_k,
                    with_payload=True,
                )

                for point in results:
                    result = self._point_to_result(point, target_modality, vector_name)
                    # Apply cross-modal boost
                    result.score *= query.cross_modal_boost
                    all_results.append(result)

            except Exception as e:
                logger.warning(
                    f"[Retriever] Cross-modal search failed for {vector_name}: {e}"
                )

        # Sort and limit
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[: query.top_k]

    async def _search_multi_modal(
        self,
        query: MultiModalQuery,
        ctx: SearchContext,
    ) -> list[RetrievalResult]:
        """다중 모달리티 동시 검색.

        모든 target modality에서 동시 검색 후 RRF 융합.
        """
        if not ctx.query_vector:
            return []

        ranked_lists: list[list[tuple[str, float]]] = []
        all_results: list[RetrievalResult] = []
        qdrant_filter = self._build_filter(query)

        for target_modality in query.target_modalities:
            vector_name = f"{target_modality.value}_embed"

            try:
                results = self._client.search(
                    collection_name=self._collection_name,
                    query_vector=qdrant_models.NamedVector(
                        name=vector_name,
                        vector=ctx.query_vector,
                    ),
                    query_filter=qdrant_filter,
                    limit=query.top_k * 2,  # Get more for fusion
                    with_payload=True,
                )

                modality_results = [
                    self._point_to_result(point, target_modality, vector_name)
                    for point in results
                ]

                ranked_lists.append([(r.doc_id, r.score) for r in modality_results])
                all_results.extend(modality_results)

            except Exception as e:
                logger.warning(f"[Retriever] Multi-modal search failed: {e}")

        if not ranked_lists:
            return []

        # RRF fusion across modalities
        fused = reciprocal_rank_fusion(ranked_lists)

        # Rebuild with RRF scores
        result_map = {r.doc_id: r for r in all_results}
        final_results: list[RetrievalResult] = []

        for doc_id, rrf_score in fused[: query.top_k]:
            if doc_id in result_map:
                result = result_map[doc_id]
                result.score = rrf_score
                final_results.append(result)

        return final_results

    # =========================================================================
    # Helpers
    # =========================================================================

    def _build_filter(
        self,
        query: MultiModalQuery,
    ) -> qdrant_models.Filter | None:
        """Qdrant 필터 빌드."""
        conditions: list[qdrant_models.Condition] = []

        if query.dimension_filter:
            conditions.append(
                qdrant_models.FieldCondition(
                    key="dimension",
                    match=qdrant_models.MatchValue(value=query.dimension_filter),
                )
            )

        if query.auteur_filter:
            conditions.append(
                qdrant_models.FieldCondition(
                    key="auteur_key",
                    match=qdrant_models.MatchValue(value=query.auteur_filter),
                )
            )

        if query.content_type_filter:
            conditions.append(
                qdrant_models.FieldCondition(
                    key="content_type",
                    match=qdrant_models.MatchAny(
                        any=[ct.value for ct in query.content_type_filter]
                    ),
                )
            )

        if not conditions:
            return None

        return qdrant_models.Filter(must=conditions)

    def _point_to_result(
        self,
        point: Any,
        modality: Modality,
        matched_vector: str,
    ) -> RetrievalResult:
        """Qdrant point를 RetrievalResult로 변환."""
        payload = point.payload or {}

        # Parse content type
        content_type_str = payload.get("content_type", "reference")
        try:
            content_type = ContentType(content_type_str)
        except ValueError:
            content_type = ContentType.REFERENCE

        return RetrievalResult(
            doc_id=payload.get("doc_id", str(point.id)),
            score=point.score,
            modality=modality,
            content_type=content_type,
            dimension=payload.get("dimension", ""),
            text_preview=payload.get("text_content", payload.get("description", ""))[:200],
            content_url=payload.get("content_url"),
            evidence_ref=payload.get("evidence_ref", ""),
            auteur_key=payload.get("auteur_key"),
            title=payload.get("title"),
            source=payload.get("source"),
            matched_vector=matched_vector,
            metadata={
                k: v
                for k, v in payload.items()
                if k
                not in {
                    "doc_id",
                    "dimension",
                    "modality",
                    "content_type",
                    "auteur_key",
                    "title",
                    "description",
                    "text_content",
                    "content_url",
                    "source",
                    "evidence_ref",
                }
            },
        )


# =============================================================================
# Factory Function
# =============================================================================


def create_retriever(
    embedder: BaseMultiModalEmbedder,
    collection_name: str = "vivid_multimodal_auteur",
) -> CrossModalRetriever:
    """Retriever 팩토리 함수.

    Args:
        embedder: 멀티모달 임베더
        collection_name: 컬렉션 이름

    Returns:
        CrossModalRetriever 인스턴스
    """
    return CrossModalRetriever(
        embedder=embedder,
        collection_name=collection_name,
    )
