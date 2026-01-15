"""Qdrant Hybrid Search Backend.

Qdrant Native Dense + Sparse + RRF Fusion.
tier1_dimension_rag.py의 hybrid_search()를 래핑.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .base import BaseBackend, RetrievalResult

if TYPE_CHECKING:
    from app.rag.tier1_dimension_rag import Tier1DimensionRAG

logger = logging.getLogger(__name__)


class QdrantHybridBackend(BaseBackend):
    """Qdrant Dense + Sparse Hybrid Search Backend.

    Features:
    - Dense vector search (all-MiniLM-L6-v2)
    - Sparse vector search (Qdrant/bm25 + Server-side IDF)
    - RRF Fusion (Qdrant Native)
    - Dimension별 컬렉션 자동 선택
    """

    backend_id = "qdrant_hybrid"

    def __init__(self) -> None:
        self._rag_cache: Dict[str, "Tier1DimensionRAG"] = {}

    def _get_rag(self, dimension: str) -> "Tier1DimensionRAG":
        """차원별 RAG 인스턴스 (캐시)."""
        if dimension not in self._rag_cache:
            from app.rag.tier1_dimension_rag import get_dimension_rag

            self._rag_cache[dimension] = get_dimension_rag(dimension)
        return self._rag_cache[dimension]

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """Qdrant Hybrid Search 실행.

        Config options:
            dimension: 차원 코드 (1D, AD, VEO 등) - 필수
            prefetch_limit: Dense/Sparse 각각의 prefetch 수 (기본: 20)
            min_score: 최소 점수 (기본: 0.0)
        """
        config = config or {}
        filters = filters or {}

        dimension = config.get("dimension", "1D")
        prefetch_limit = config.get("prefetch_limit", 20)
        min_score = config.get("min_score", 0.0)

        rag = self._get_rag(dimension)

        try:
            # tier1_dimension_rag.hybrid_search() 호출
            results = rag.hybrid_search(
                query=query,
                limit=limit,
                prefetch_limit=prefetch_limit,
                app_key=filters.get("app_key"),
                min_score=min_score,
                metadata_filters={k: v for k, v in filters.items() if k != "app_key"},
            )

            return [
                RetrievalResult(
                    doc_id=r.get("doc_id") or f"qdrant_{idx}",
                    text=r.get("content", ""),
                    score=r.get("score", 0.0),
                    source=self.backend_id,
                    rank=idx + 1,
                    metadata={
                        "dimension": dimension,
                        **r.get("metadata", {}),
                    },
                )
                for idx, r in enumerate(results)
            ]
        except Exception as e:
            logger.error(f"[QdrantHybridBackend] Retrieve failed: {e}")
            return []

    async def health_check(self) -> bool:
        """Qdrant 연결 상태 확인."""
        try:
            rag = self._get_rag("1D")
            stats = rag.get_collection_stats()
            return stats.get("available", False)
        except Exception:
            return False

    async def index_document(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """문서 인덱싱."""
        metadata = metadata or {}
        dimension = metadata.get("dimension", "1D")

        try:
            rag = self._get_rag(dimension)
            return rag.index_document(doc_id, text, metadata)
        except Exception as e:
            logger.error(f"[QdrantHybridBackend] Index failed: {e}")
            return False
