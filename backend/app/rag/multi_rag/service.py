"""Multi-Modal RAG Service.

멀티모달 RAG 시스템의 통합 서비스.
- 문서 인덱싱 (텍스트, 이미지, 오디오, 비디오)
- 크로스모달 검색
- Dimension별 컬렉션 관리
- evidence_refs 생성

Usage:
    service = await MultiModalRAGService.create()
    
    # Index document
    await service.index_document(
        text="cinematic lighting technique",
        dimension="3D",
        auteur_key="prism",
    )
    
    # Search
    results = await service.search("dramatic shadows", dimension="3D")
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from app.rag.multi_rag.collection_manager import (
    MultiModalCollectionManager,
    create_collection_manager,
)
from app.rag.multi_rag.embedders import GeminiMultiModalEmbedder
from app.rag.multi_rag.embedders.base import BaseMultiModalEmbedder
from app.rag.multi_rag.retriever import CrossModalRetriever, create_retriever
from app.rag.multi_rag.types import (
    ContentType,
    Modality,
    MultiModalDocument,
    MultiModalQuery,
    MultiModalSearchResult,
    RetrievalResult,
    SearchStrategy,
    get_modalities_for_dimension,
)

logger = logging.getLogger(__name__)


class MultiModalRAGService:
    """멀티모달 RAG 통합 서비스.

    Features:
        - 통합 문서 인덱싱 API
        - 크로스모달 검색 API
        - Dimension별 자동 모달리티 선택
        - evidence_refs 자동 생성

    Usage:
        # 서비스 생성
        service = await MultiModalRAGService.create()

        # 문서 인덱싱
        doc_id = await service.index_text(
            text="강주노 감독의 수직적 프레이밍",
            dimension="4D",
            auteur_key="bong",
            content_type=ContentType.TECHNIQUE,
        )

        # 검색
        results = await service.search(
            query_text="수직 구도",
            dimension="4D",
            auteur_key="bong",
        )

        # evidence_refs 추출
        refs = [r.evidence_ref for r in results.results]
    """

    def __init__(
        self,
        embedder: BaseMultiModalEmbedder,
        collection_manager: MultiModalCollectionManager,
        retriever: CrossModalRetriever,
    ) -> None:
        """Initialize service.

        Use create() classmethod for async initialization.
        """
        self._embedder = embedder
        self._collection_manager = collection_manager
        self._retriever = retriever

    @classmethod
    async def create(
        cls,
        collection_name: str = "vivid_multimodal_auteur",
        embedder: BaseMultiModalEmbedder | None = None,
    ) -> MultiModalRAGService:
        """서비스 비동기 생성.

        Args:
            collection_name: Qdrant 컬렉션 이름
            embedder: 커스텀 임베더 (None이면 Gemini 사용)

        Returns:
            초기화된 MultiModalRAGService 인스턴스
        """
        # Create embedder
        if embedder is None:
            embedder = GeminiMultiModalEmbedder()

        # Create collection manager
        collection_manager = create_collection_manager(collection_name)
        await collection_manager.ensure_collection()

        # Create retriever
        retriever = create_retriever(embedder, collection_name)

        logger.info(
            f"[MultiModalRAG] Service created: collection={collection_name}, "
            f"embedder={embedder.model_name}"
        )

        return cls(embedder, collection_manager, retriever)

    # =========================================================================
    # Indexing API
    # =========================================================================

    async def index_text(
        self,
        text: str,
        dimension: str,
        content_type: ContentType = ContentType.REFERENCE,
        auteur_key: str | None = None,
        title: str | None = None,
        source: str = "api",
        doc_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """텍스트 문서 인덱싱.

        Args:
            text: 인덱싱할 텍스트
            dimension: Dimension (3D, 4D, AD 등)
            content_type: 콘텐츠 유형
            auteur_key: 거장 키
            title: 문서 제목
            source: 소스 (api, notebooklm, upload 등)
            doc_id: 문서 ID (None이면 자동 생성)
            metadata: 추가 메타데이터

        Returns:
            문서 ID
        """
        doc_id = doc_id or str(uuid.uuid4())

        # Generate embeddings
        text_embedding = await self._embedder.embed_text(text)

        # Generate sparse embedding if available
        sparse_embeddings = {}
        if hasattr(self._embedder, "embed_sparse"):
            sparse_result = await self._embedder.embed_sparse(text)
            sparse_embeddings["text_bm25"] = sparse_result.to_dict()

        # Create document
        doc = MultiModalDocument(
            doc_id=doc_id,
            dimension=dimension,
            modality=Modality.TEXT,
            content_type=content_type,
            text_content=text,
            embeddings={"text_embed": text_embedding.vector},
            sparse_embeddings=sparse_embeddings,
            auteur_key=auteur_key,
            title=title,
            description=text[:500],
            source=source,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )

        # Upsert to collection
        await self._collection_manager.upsert_document(doc)

        logger.debug(f"[MultiModalRAG] Indexed text document: {doc_id}")
        return doc_id

    async def index_image(
        self,
        image_data: bytes,
        dimension: str,
        content_type: ContentType = ContentType.REFERENCE,
        auteur_key: str | None = None,
        title: str | None = None,
        description: str | None = None,
        content_url: str | None = None,
        doc_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """이미지 문서 인덱싱.

        Args:
            image_data: 이미지 바이트 데이터
            dimension: Dimension
            content_type: 콘텐츠 유형
            auteur_key: 거장 키
            title: 제목
            description: 설명 (이미지 분석 결과로 자동 생성됨)
            content_url: 이미지 URL
            doc_id: 문서 ID
            metadata: 추가 메타데이터

        Returns:
            문서 ID
        """
        doc_id = doc_id or str(uuid.uuid4())

        # Generate image embedding (includes description generation)
        image_embedding = await self._embedder.embed_image(image_data)

        # Use generated description if not provided
        if not description and "description_length" in image_embedding.metadata:
            description = f"[Auto-generated image description - {image_embedding.metadata.get('description_length', 0)} chars]"

        # Create document
        doc = MultiModalDocument(
            doc_id=doc_id,
            dimension=dimension,
            modality=Modality.IMAGE,
            content_type=content_type,
            image_data=image_data if len(image_data) < 1_000_000 else None,  # Store small images only
            content_url=content_url,
            embeddings={"image_embed": image_embedding.vector},
            auteur_key=auteur_key,
            title=title,
            description=description,
            source="api",
            timestamp=datetime.utcnow().isoformat(),
            metadata={
                "image_size_bytes": len(image_data),
                **(metadata or {}),
            },
        )

        await self._collection_manager.upsert_document(doc)

        logger.debug(f"[MultiModalRAG] Indexed image document: {doc_id}")
        return doc_id

    async def index_document(
        self,
        document: MultiModalDocument,
    ) -> str:
        """문서 직접 인덱싱.

        임베딩이 이미 계산된 문서를 인덱싱.

        Args:
            document: 멀티모달 문서

        Returns:
            문서 ID
        """
        # Generate missing embeddings
        if not document.embeddings:
            if document.text_content:
                result = await self._embedder.embed_text(document.text_content)
                document.embeddings["text_embed"] = result.vector
            elif document.image_data:
                result = await self._embedder.embed_image(document.image_data)
                document.embeddings["image_embed"] = result.vector

        await self._collection_manager.upsert_document(document)
        return document.doc_id

    async def index_batch(
        self,
        documents: list[MultiModalDocument],
    ) -> int:
        """문서 배치 인덱싱.

        Args:
            documents: 문서 목록

        Returns:
            인덱싱된 문서 수
        """
        # Generate embeddings for documents without them
        for doc in documents:
            if not doc.embeddings:
                if doc.text_content:
                    result = await self._embedder.embed_text(doc.text_content)
                    doc.embeddings["text_embed"] = result.vector

        return await self._collection_manager.upsert_documents(documents)

    # =========================================================================
    # Search API
    # =========================================================================

    async def search(
        self,
        query_text: str,
        dimension: str | None = None,
        auteur_key: str | None = None,
        content_types: list[ContentType] | None = None,
        top_k: int = 10,
        strategy: SearchStrategy = SearchStrategy.HYBRID_RRF,
    ) -> MultiModalSearchResult:
        """텍스트 기반 검색.

        Args:
            query_text: 검색 쿼리
            dimension: Dimension 필터
            auteur_key: Auteur 필터
            content_types: 콘텐츠 타입 필터
            top_k: 결과 수
            strategy: 검색 전략

        Returns:
            검색 결과
        """
        # Determine target modalities based on dimension
        target_modalities = [Modality.TEXT]
        if dimension:
            target_modalities = get_modalities_for_dimension(dimension)

        query = MultiModalQuery(
            query_text=query_text,
            target_modalities=target_modalities,
            search_strategy=strategy,
            top_k=top_k,
            dimension_filter=dimension,
            auteur_filter=auteur_key,
            content_type_filter=content_types,
        )

        return await self._retriever.search(query)

    async def cross_modal_search(
        self,
        query_text: str,
        target_modality: Modality,
        dimension: str | None = None,
        auteur_key: str | None = None,
        top_k: int = 10,
    ) -> MultiModalSearchResult:
        """크로스모달 검색.

        텍스트로 다른 모달리티 검색.

        Args:
            query_text: 검색 쿼리
            target_modality: 검색 대상 모달리티
            dimension: Dimension 필터
            auteur_key: Auteur 필터
            top_k: 결과 수

        Returns:
            검색 결과
        """
        query = MultiModalQuery(
            query_text=query_text,
            target_modalities=[target_modality],
            search_strategy=SearchStrategy.CROSS_MODAL,
            top_k=top_k,
            dimension_filter=dimension,
            auteur_filter=auteur_key,
        )

        return await self._retriever.search(query)

    async def search_images(
        self,
        query_text: str,
        dimension: str | None = None,
        auteur_key: str | None = None,
        top_k: int = 10,
    ) -> MultiModalSearchResult:
        """이미지 검색 (텍스트 쿼리).

        Args:
            query_text: 검색 쿼리
            dimension: Dimension 필터
            auteur_key: Auteur 필터
            top_k: 결과 수

        Returns:
            이미지 검색 결과
        """
        return await self.cross_modal_search(
            query_text=query_text,
            target_modality=Modality.IMAGE,
            dimension=dimension,
            auteur_key=auteur_key,
            top_k=top_k,
        )

    async def search_videos(
        self,
        query_text: str,
        dimension: str | None = None,
        auteur_key: str | None = None,
        top_k: int = 10,
    ) -> MultiModalSearchResult:
        """비디오 검색 (텍스트 쿼리).

        Args:
            query_text: 검색 쿼리
            dimension: Dimension 필터
            auteur_key: Auteur 필터
            top_k: 결과 수

        Returns:
            비디오 검색 결과
        """
        return await self.cross_modal_search(
            query_text=query_text,
            target_modality=Modality.VIDEO,
            dimension=dimension,
            auteur_key=auteur_key,
            top_k=top_k,
        )

    # =========================================================================
    # Utility API
    # =========================================================================

    async def get_evidence_refs(
        self,
        query_text: str,
        dimension: str,
        auteur_key: str | None = None,
        top_k: int = 5,
    ) -> list[str]:
        """evidence_refs 생성.

        검색 결과에서 evidence_ref 문자열 목록 추출.

        Args:
            query_text: 검색 쿼리
            dimension: Dimension
            auteur_key: Auteur 키
            top_k: 결과 수

        Returns:
            evidence_ref 문자열 목록 (List[str])
        """
        results = await self.search(
            query_text=query_text,
            dimension=dimension,
            auteur_key=auteur_key,
            top_k=top_k,
        )

        return [r.evidence_ref for r in results.results if r.evidence_ref]

    async def delete_document(self, doc_id: str) -> bool:
        """문서 삭제.

        Args:
            doc_id: 문서 ID

        Returns:
            삭제 성공 여부
        """
        return await self._collection_manager.delete_document(doc_id)

    async def get_collection_stats(self) -> dict[str, Any]:
        """컬렉션 통계 조회.

        Returns:
            컬렉션 정보 및 모달리티별 문서 수
        """
        info = await self._collection_manager.get_collection_info()
        modality_counts = await self._collection_manager.count_by_modality()

        return {
            **info,
            "modality_counts": modality_counts,
            "embedder": self._embedder.model_name,
            "embedding_dim": self._embedder.embedding_dim,
        }


# =============================================================================
# Factory Functions
# =============================================================================


async def create_multimodal_rag_service(
    collection_name: str = "vivid_multimodal_auteur",
) -> MultiModalRAGService:
    """멀티모달 RAG 서비스 생성.

    Args:
        collection_name: 컬렉션 이름

    Returns:
        MultiModalRAGService 인스턴스
    """
    return await MultiModalRAGService.create(collection_name)


async def get_multimodal_rag_service() -> MultiModalRAGService:
    """기본 멀티모달 RAG 서비스 가져오기.

    싱글톤 패턴으로 서비스 인스턴스 관리.

    Returns:
        MultiModalRAGService 인스턴스
    """
    global _default_service
    if _default_service is None:
        _default_service = await MultiModalRAGService.create()
    return _default_service


_default_service: MultiModalRAGService | None = None
