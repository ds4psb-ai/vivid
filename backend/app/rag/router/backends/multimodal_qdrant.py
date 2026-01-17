"""Multi-Modal Qdrant Backend Adapter.

multi_rag/ 모듈의 MultiModalRAGService를 래핑하는 어댑터.
Named Vectors 기반 멀티모달 검색을 Multi-RAG Router에 통합.
"""

from __future__ import annotations

import logging
from typing import Any

from app.rag.router.backends.base import BaseRAGBackend
from app.rag.router.types import RAGDocument, RAGSourceType

logger = logging.getLogger(__name__)


class MultiModalQdrantBackend(BaseRAGBackend):
    """Multi-Modal Qdrant RAG 백엔드 (Tier1)."""

    _source_type = RAGSourceType.MULTIMODAL_DIMENSION

    def __init__(self, service: Any = None):
        """Initialize with MultiModalRAGService.

        Args:
            service: MultiModalRAGService 인스턴스
                    None이면 lazy import
        """
        self._service = service
        self._initialized = service is not None

    async def _ensure_service(self) -> Any:
        """서비스 lazy initialization."""
        if self._service is None:
            try:
                from app.rag.multi_rag import MultiModalRAGService

                self._service = await MultiModalRAGService.create()
                self._initialized = True
            except Exception as e:
                logger.warning(
                    f"[MultiModalQdrantBackend] Service init failed: {e}"
                )
                self._service = None
        return self._service

    async def query(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[RAGDocument]:
        """Multi-Modal Qdrant 쿼리 실행.

        Args:
            query: 검색 쿼리
            filters: 필터 조건
                - dimension: 차원 (1D, 2D, 3D, 4D, AD, AI 등)
                - auteur_key: 거장 키 (선택)
                - content_type: 콘텐츠 타입 (선택)
            limit: 최대 결과 수

        Returns:
            RAGDocument 리스트
        """
        service = await self._ensure_service()
        if service is None:
            logger.warning("[MultiModalQdrantBackend] Service not available")
            return []

        dimension = (filters or {}).get("dimension", "4D")
        auteur_key = (filters or {}).get("auteur_key")
        content_type = (filters or {}).get("content_type")

        try:
            # Multi-Modal RAG 서비스 호출
            result = await service.search(
                query_text=query,
                dimension=dimension,
                auteur_key=auteur_key,
                top_k=limit,
            )

            documents = []
            for r in result.results:
                doc = RAGDocument(
                    id=r.doc_id,
                    content=r.text_content or "",
                    score=r.score,
                    metadata={
                        "dimension": r.dimension,
                        "modality": r.modality.value if r.modality else "text",
                        "content_type": (
                            r.content_type.value if r.content_type else None
                        ),
                        "auteur_key": r.auteur_key,
                        **r.metadata,
                    },
                    evidence_ref=r.evidence_ref,
                    source_id="multimodal_qdrant",
                    source_type=RAGSourceType.MULTIMODAL_DIMENSION,
                    modality=r.modality.value if r.modality else "text",
                )
                documents.append(doc)

            return documents

        except Exception as e:
            logger.error(f"[MultiModalQdrantBackend] Query failed: {e}")
            return []

    async def cross_modal_search(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[RAGDocument]:
        """Cross-Modal 검색 (텍스트 → 이미지/비디오).

        텍스트 쿼리로 이미지, 비디오 등 다른 모달리티 검색.
        """
        service = await self._ensure_service()
        if service is None:
            return []

        dimension = (filters or {}).get("dimension", "4D")
        target_modalities = (filters or {}).get(
            "target_modalities", ["image", "video"]
        )

        try:
            result = await service.cross_modal_search(
                query_text=query,
                dimension=dimension,
                target_modalities=target_modalities,
                top_k=limit,
            )

            return [
                RAGDocument(
                    id=r.doc_id,
                    content=r.text_content or "",
                    score=r.score,
                    metadata=r.metadata,
                    evidence_ref=r.evidence_ref,
                    source_id="multimodal_qdrant",
                    source_type=RAGSourceType.MULTIMODAL_DIMENSION,
                    modality=r.modality.value if r.modality else "image",
                )
                for r in result.results
            ]

        except Exception as e:
            logger.error(f"[MultiModalQdrantBackend] Cross-modal failed: {e}")
            return []

    async def health_check(self) -> bool:
        """헬스 체크."""
        service = await self._ensure_service()
        if service is None:
            return False

        try:
            # Collection 존재 확인
            return await service.is_healthy()
        except Exception:
            return False


class MockMultiModalQdrantBackend(BaseRAGBackend):
    """테스트용 Mock Multi-Modal Qdrant 백엔드."""

    _source_type = RAGSourceType.MULTIMODAL_DIMENSION

    def __init__(
        self, mock_responses: dict[str, list[RAGDocument]] | None = None
    ):
        self._mock_responses = mock_responses or {}

    async def query(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[RAGDocument]:
        """Mock 쿼리."""
        dimension = (filters or {}).get("dimension", "4D")

        if dimension in self._mock_responses:
            return self._mock_responses[dimension][:limit]

        # 기본 mock 응답
        return [
            RAGDocument(
                id=f"mock_{dimension}_1",
                content=f"Mock content for {dimension}: {query}",
                score=0.85,
                metadata={"dimension": dimension, "modality": "text"},
                evidence_ref=f"db:rag_docs:multimodal:{dimension}:mock_1",
                source_id="multimodal_qdrant",
                source_type=RAGSourceType.MULTIMODAL_DIMENSION,
            )
        ]

    async def health_check(self) -> bool:
        """항상 True."""
        return True
