"""Vertex AI RAG + Google Search Grounding Backend.

Vertex AI RAG Engine + Google Search Grounding.
tier0_vertex_rag.py를 래핑.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .base import BaseBackend, RetrievalResult

if TYPE_CHECKING:
    from app.rag.tier0_vertex_rag import VertexRAGService

logger = logging.getLogger(__name__)


class VertexGroundingBackend(BaseBackend):
    """Vertex AI RAG + Google Search Grounding Backend.

    Features:
    - Vertex AI RAG Engine (프라이빗 데이터)
    - Google Search Grounding (실시간 정보)
    """

    backend_id = "vertex_grounding"

    def __init__(self) -> None:
        self._service: Optional["VertexRAGService"] = None

    def _get_service(self) -> "VertexRAGService":
        """Vertex RAG 서비스 (lazy load)."""
        if self._service is None:
            from app.rag.tier0_vertex_rag import get_vertex_rag_service

            self._service = get_vertex_rag_service()
        return self._service

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """Vertex AI RAG + Grounding 검색.

        Config options:
            corpus_name: Corpus 이름 (예: "auteur_dna")
            use_grounding: Google Search Grounding 사용 여부 (기본: True)
        """
        config = config or {}

        corpus_name = config.get("corpus_name")
        use_grounding = config.get("use_grounding", True)

        try:
            service = self._get_service()
            result = await service.query(
                query=query,
                corpus_name=corpus_name,
                use_grounding=use_grounding,
                top_k=limit,
            )

            results: List[RetrievalResult] = []
            current_rank = 1

            # Vertex AI RAG 결과
            for src in result.sources[:limit]:
                results.append(
                    RetrievalResult(
                        doc_id=src.source_id,
                        text=src.content,
                        score=result.confidence * (1.0 - (current_rank - 1) * 0.03),
                        source=self.backend_id,
                        rank=current_rank,
                        metadata={
                            "corpus_name": corpus_name,
                            "type": "vertex_rag",
                            "document_name": src.document_name,
                        },
                    )
                )
                current_rank += 1

            # Google Search Grounding 결과 (남은 limit 채우기)
            remaining = limit - len(results)
            for idx, src in enumerate(result.grounding_sources[:remaining]):
                results.append(
                    RetrievalResult(
                        doc_id=f"grounding_{idx}",
                        text=src.get("source", "") or src.get("uri", ""),
                        score=result.confidence * 0.85 * (1.0 - idx * 0.05),
                        source=self.backend_id,
                        rank=current_rank,
                        metadata={
                            "url": src.get("uri", ""),
                            "type": "google_search",
                        },
                    )
                )
                current_rank += 1

            return results[:limit]
        except Exception as e:
            logger.error(f"[VertexGroundingBackend] Retrieve failed: {e}")
            return []

    async def health_check(self) -> bool:
        """Vertex AI 연결 상태 확인."""
        try:
            service = self._get_service()
            return service is not None and service._initialized
        except Exception:
            return False
