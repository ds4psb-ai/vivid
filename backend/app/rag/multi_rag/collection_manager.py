"""Multi-Modal Collection Manager.

Qdrant Named Vectors 기반 멀티모달 컬렉션 관리.
- 모달리티별 독립 벡터 공간 (text_embed, image_embed, audio_embed, video_embed)
- Sparse 벡터 (BM25) 하이브리드 검색 지원
- 자동 컬렉션 생성 및 스키마 검증

References:
    - Qdrant Named Vectors: https://qdrant.tech/documentation/concepts/vectors/
    - Hybrid Search: https://qdrant.tech/documentation/hybrid-search/
"""

from __future__ import annotations

import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings
from app.services.circuit_breaker import QDRANT_BREAKER, CircuitBreakerOpen
from app.rag.multi_rag.types import (
    CollectionSchema,
    DistanceMetric,
    Modality,
    MultiModalDocument,
    SparseVectorConfig,
    VectorConfig,
    get_default_multimodal_schema,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Qdrant Client Singleton
# =============================================================================

_qdrant_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    """Qdrant 클라이언트 싱글톤.

    Returns:
        QdrantClient 인스턴스
    """
    global _qdrant_client

    if _qdrant_client is None:
        qdrant_url = getattr(settings, "QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = getattr(settings, "QDRANT_API_KEY", None)

        _qdrant_client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            timeout=30.0,
        )
        logger.info(f"[CollectionManager] Qdrant client initialized: {qdrant_url}")

    return _qdrant_client


def reset_qdrant_client() -> None:
    """Qdrant 클라이언트 리셋 (테스트용)."""
    global _qdrant_client
    if _qdrant_client:
        _qdrant_client.close()
    _qdrant_client = None


# =============================================================================
# Multi-Modal Collection Manager
# =============================================================================


class MultiModalCollectionManager:
    """멀티모달 컬렉션 매니저.

    Qdrant Named Vectors를 사용한 멀티모달 컬렉션 관리.

    Features:
        - 모달리티별 Named Vectors (text_embed, image_embed, etc.)
        - Sparse Vectors (BM25) 하이브리드 검색
        - 자동 컬렉션 생성/마이그레이션
        - Payload 인덱싱 최적화

    Usage:
        manager = MultiModalCollectionManager()
        await manager.ensure_collection("vivid_multimodal_auteur")
        await manager.upsert_document(doc)
    """

    def __init__(
        self,
        client: QdrantClient | None = None,
        schema: CollectionSchema | None = None,
    ) -> None:
        """Initialize collection manager.

        Args:
            client: Qdrant 클라이언트 (None이면 싱글톤 사용)
            schema: 컬렉션 스키마 (None이면 기본 스키마)
        """
        self._client = client or get_qdrant_client()
        self._schema = schema or get_default_multimodal_schema()
        self._initialized_collections: set[str] = set()

    @property
    def collection_name(self) -> str:
        """기본 컬렉션 이름."""
        return self._schema.name

    # =========================================================================
    # Collection Lifecycle
    # =========================================================================

    async def ensure_collection(
        self,
        collection_name: str | None = None,
        recreate: bool = False,
    ) -> bool:
        """컬렉션 존재 확인 및 생성.

        Args:
            collection_name: 컬렉션 이름 (None이면 기본)
            recreate: True면 기존 컬렉션 삭제 후 재생성

        Returns:
            True if collection ready
        """
        name = collection_name or self._schema.name

        if name in self._initialized_collections and not recreate:
            return True

        try:
            # Circuit breaker check
            if not QDRANT_BREAKER.allow_request():
                logger.warning(f"[CollectionManager] Circuit breaker open, skipping: {name}")
                return False

            # Check if collection exists
            collections = self._client.get_collections().collections
            exists = any(c.name == name for c in collections)

            if exists and recreate:
                logger.warning(f"[CollectionManager] Deleting collection: {name}")
                self._client.delete_collection(name)
                exists = False

            if not exists:
                await self._create_collection(name)
            else:
                logger.info(f"[CollectionManager] Collection exists: {name}")

            self._initialized_collections.add(name)
            QDRANT_BREAKER.record_success()
            return True

        except CircuitBreakerOpen:
            logger.warning(f"[CollectionManager] Circuit breaker open: {name}")
            return False
        except Exception as e:
            QDRANT_BREAKER.record_failure()
            logger.error(f"[CollectionManager] Failed to ensure collection: {e}")
            return False

    async def _create_collection(self, collection_name: str) -> None:
        """컬렉션 생성 (Named Vectors + Sparse).

        Args:
            collection_name: 컬렉션 이름
        """
        logger.info(f"[CollectionManager] Creating collection: {collection_name}")

        # Build Named Vectors config
        vectors_config: dict[str, qdrant_models.VectorParams] = {}
        for vec_config in self._schema.dense_vectors:
            vectors_config[vec_config.name] = qdrant_models.VectorParams(
                size=vec_config.size,
                distance=getattr(qdrant_models.Distance, vec_config.distance.value),
            )

        # Build Sparse Vectors config
        sparse_vectors_config: dict[str, qdrant_models.SparseVectorParams] | None = None
        if self._schema.sparse_vectors:
            sparse_vectors_config = {}
            for sparse_config in self._schema.sparse_vectors:
                params = qdrant_models.SparseVectorParams()
                if sparse_config.modifier:
                    params.modifier = qdrant_models.Modifier.IDF
                sparse_vectors_config[sparse_config.name] = params

        # Create collection
        self._client.create_collection(
            collection_name=collection_name,
            vectors_config=vectors_config,
            sparse_vectors_config=sparse_vectors_config,
            optimizers_config=qdrant_models.OptimizersConfigDiff(
                indexing_threshold=10000,  # Start indexing after 10k points
            ),
        )

        # Create payload indexes for efficient filtering
        await self._create_payload_indexes(collection_name)

        logger.info(
            f"[CollectionManager] Collection created: {collection_name} "
            f"(dense={len(vectors_config)}, sparse={len(sparse_vectors_config or {})})"
        )

    async def _create_payload_indexes(self, collection_name: str) -> None:
        """Payload 필드 인덱스 생성.

        Args:
            collection_name: 컬렉션 이름
        """
        # Keyword indexes for filtering
        keyword_fields = [
            "doc_id",
            "dimension",
            "auteur_key",
            "content_type",
            "modality",
            "source",
        ]

        for field in keyword_fields:
            try:
                self._client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field,
                    field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
                )
            except UnexpectedResponse:
                # Index might already exist
                pass

        # Text index for full-text search
        try:
            self._client.create_payload_index(
                collection_name=collection_name,
                field_name="description",
                field_schema=qdrant_models.TextIndexParams(
                    type="text",
                    tokenizer=qdrant_models.TokenizerType.WORD,
                    min_token_len=2,
                    max_token_len=20,
                ),
            )
        except UnexpectedResponse:
            pass

    async def delete_collection(self, collection_name: str | None = None) -> bool:
        """컬렉션 삭제.

        Args:
            collection_name: 컬렉션 이름 (None이면 기본)

        Returns:
            True if deleted
        """
        name = collection_name or self._schema.name

        try:
            self._client.delete_collection(name)
            self._initialized_collections.discard(name)
            logger.info(f"[CollectionManager] Collection deleted: {name}")
            return True
        except Exception as e:
            logger.error(f"[CollectionManager] Failed to delete collection: {e}")
            return False

    # =========================================================================
    # Document Operations
    # =========================================================================

    async def upsert_document(
        self,
        document: MultiModalDocument,
        collection_name: str | None = None,
    ) -> str:
        """문서 업서트.

        Named Vectors로 각 모달리티 임베딩을 저장.

        Args:
            document: 멀티모달 문서
            collection_name: 컬렉션 이름

        Returns:
            문서 ID

        Raises:
            ValueError: 문서에 임베딩이 없을 때
            RuntimeError: Qdrant 연결 실패 시
        """
        name = collection_name or self._schema.name

        # Ensure collection exists
        if not await self.ensure_collection(name):
            raise RuntimeError(f"Failed to ensure collection: {name}")

        # Build vectors dict (named vectors)
        vectors: dict[str, list[float]] = {}
        for vec_name, vec_values in document.embeddings.items():
            if vec_values and len(vec_values) > 0:
                vectors[vec_name] = vec_values

        if not vectors:
            raise ValueError(f"Document {document.doc_id} has no embeddings")

        # Build sparse vectors if available
        sparse_vectors: dict[str, qdrant_models.SparseVector] | None = None
        if document.sparse_embeddings:
            sparse_vectors = {}
            for sparse_name, sparse_data in document.sparse_embeddings.items():
                if sparse_data:
                    sparse_vectors[sparse_name] = qdrant_models.SparseVector(
                        indices=list(sparse_data.keys()),
                        values=list(sparse_data.values()),
                    )

        # Build payload (filter out None values)
        payload = {
            k: v
            for k, v in {
                "doc_id": document.doc_id,
                "dimension": document.dimension,
                "modality": document.modality.value,
                "content_type": document.content_type.value,
                "auteur_key": document.auteur_key,
                "title": document.title,
                "description": document.description,
                "text_content": document.text_content,
                "content_url": document.content_url,
                "source": document.source,
                "timestamp": document.timestamp,
                "evidence_ref": document.get_evidence_ref(),
                **document.metadata,
            }.items()
            if v is not None
        }

        # Create point with proper vector structure
        point = qdrant_models.PointStruct(
            id=self._generate_point_id(document.doc_id),
            vector=vectors,
            payload=payload,
        )

        try:
            # Circuit breaker check
            if not QDRANT_BREAKER.allow_request():
                raise RuntimeError("Qdrant circuit breaker is open")

            # Upsert
            self._client.upsert(
                collection_name=name,
                points=[point],
            )
            QDRANT_BREAKER.record_success()

            logger.debug(
                f"[CollectionManager] Upserted document: {document.doc_id} "
                f"(vectors={list(vectors.keys())})"
            )

            return document.doc_id

        except CircuitBreakerOpen:
            raise RuntimeError("Qdrant circuit breaker is open")
        except Exception as e:
            QDRANT_BREAKER.record_failure()
            logger.error(f"[CollectionManager] Failed to upsert document: {e}")
            raise RuntimeError(f"Failed to upsert document: {e}") from e

    async def upsert_documents(
        self,
        documents: list[MultiModalDocument],
        collection_name: str | None = None,
        batch_size: int = 100,
    ) -> int:
        """문서 배치 업서트.

        Args:
            documents: 문서 목록
            collection_name: 컬렉션 이름
            batch_size: 배치 크기

        Returns:
            업서트된 문서 수
        """
        name = collection_name or self._schema.name
        await self.ensure_collection(name)

        total = 0
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            points = []

            for doc in batch:
                if not doc.embeddings:
                    continue

                vectors = {
                    k: v for k, v in doc.embeddings.items() if v and len(v) > 0
                }
                if not vectors:
                    continue

                payload = {
                    "doc_id": doc.doc_id,
                    "dimension": doc.dimension,
                    "modality": doc.modality.value,
                    "content_type": doc.content_type.value,
                    "auteur_key": doc.auteur_key,
                    "title": doc.title,
                    "description": doc.description,
                    "text_content": doc.text_content,
                    "source": doc.source,
                    "timestamp": doc.timestamp,
                    "evidence_ref": doc.get_evidence_ref(),
                }

                points.append(
                    qdrant_models.PointStruct(
                        id=self._generate_point_id(doc.doc_id),
                        vector=vectors,
                        payload=payload,
                    )
                )

            if points:
                self._client.upsert(collection_name=name, points=points)
                total += len(points)

        logger.info(f"[CollectionManager] Batch upserted {total} documents")
        return total

    async def delete_document(
        self,
        doc_id: str,
        collection_name: str | None = None,
    ) -> bool:
        """문서 삭제.

        Args:
            doc_id: 문서 ID
            collection_name: 컬렉션 이름

        Returns:
            True if deleted
        """
        name = collection_name or self._schema.name

        try:
            self._client.delete(
                collection_name=name,
                points_selector=qdrant_models.PointIdsList(
                    points=[self._generate_point_id(doc_id)],
                ),
            )
            logger.debug(f"[CollectionManager] Deleted document: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"[CollectionManager] Failed to delete document: {e}")
            return False

    async def get_document(
        self,
        doc_id: str,
        collection_name: str | None = None,
    ) -> dict[str, Any] | None:
        """문서 조회.

        Args:
            doc_id: 문서 ID
            collection_name: 컬렉션 이름

        Returns:
            문서 payload 또는 None
        """
        name = collection_name or self._schema.name

        try:
            result = self._client.retrieve(
                collection_name=name,
                ids=[self._generate_point_id(doc_id)],
                with_payload=True,
                with_vectors=False,
            )
            if result:
                return result[0].payload
            return None
        except Exception as e:
            logger.error(f"[CollectionManager] Failed to get document: {e}")
            return None

    # =========================================================================
    # Collection Info
    # =========================================================================

    async def get_collection_info(
        self,
        collection_name: str | None = None,
    ) -> dict[str, Any]:
        """컬렉션 정보 조회.

        Args:
            collection_name: 컬렉션 이름

        Returns:
            컬렉션 정보 dict
        """
        name = collection_name or self._schema.name

        try:
            info = self._client.get_collection(name)
            return {
                "name": name,
                "points_count": info.points_count,
                # vectors_count/indexed_vectors_count removed in qdrant-client 1.7+
                "status": info.status.value,
                "vectors_config": {
                    vec_name: {
                        "size": vec_params.size,
                        "distance": vec_params.distance.value,
                    }
                    for vec_name, vec_params in (info.config.params.vectors or {}).items()
                },
            }
        except Exception as e:
            logger.error(f"[CollectionManager] Failed to get collection info: {e}")
            return {"error": str(e)}

    async def count_by_modality(
        self,
        collection_name: str | None = None,
    ) -> dict[str, int]:
        """모달리티별 문서 수 조회.

        Args:
            collection_name: 컬렉션 이름

        Returns:
            모달리티별 카운트
        """
        name = collection_name or self._schema.name
        counts = {}

        for modality in Modality.all():
            try:
                result = self._client.count(
                    collection_name=name,
                    count_filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="modality",
                                match=qdrant_models.MatchValue(value=modality.value),
                            )
                        ]
                    ),
                )
                counts[modality.value] = result.count
            except Exception:
                counts[modality.value] = 0

        return counts

    # =========================================================================
    # Utility
    # =========================================================================

    def _generate_point_id(self, doc_id: str) -> int:
        """문서 ID를 Qdrant point ID로 변환.

        Args:
            doc_id: 문서 ID

        Returns:
            양의 정수 ID
        """
        # Use hash to generate consistent integer ID
        import hashlib

        hash_bytes = hashlib.sha256(doc_id.encode()).digest()
        # Use first 8 bytes as integer, ensure positive
        point_id = int.from_bytes(hash_bytes[:8], "big") & 0x7FFFFFFFFFFFFFFF
        return point_id


# =============================================================================
# Factory Functions
# =============================================================================


def create_collection_manager(
    collection_name: str = "vivid_multimodal_auteur",
    vector_dim: int = 768,
) -> MultiModalCollectionManager:
    """컬렉션 매니저 팩토리 함수.

    Args:
        collection_name: 컬렉션 이름
        vector_dim: 벡터 차원

    Returns:
        MultiModalCollectionManager 인스턴스
    """
    schema = CollectionSchema(
        name=collection_name,
        dense_vectors=[
            VectorConfig("text_embed", vector_dim, DistanceMetric.COSINE),
            VectorConfig("image_embed", vector_dim, DistanceMetric.COSINE),
            VectorConfig("audio_embed", vector_dim, DistanceMetric.COSINE),
            VectorConfig("video_embed", vector_dim, DistanceMetric.COSINE),
        ],
        sparse_vectors=[
            SparseVectorConfig("text_bm25", modifier="idf"),
        ],
    )

    return MultiModalCollectionManager(schema=schema)


async def create_dimension_collection(
    dimension: str,
    vector_dim: int = 768,
) -> MultiModalCollectionManager:
    """Dimension별 컬렉션 매니저 생성.

    Args:
        dimension: Dimension 이름 (3D, 4D, AD 등)
        vector_dim: 벡터 차원

    Returns:
        MultiModalCollectionManager 인스턴스 (컬렉션 초기화됨)
    """
    collection_name = f"vivid_multimodal_{dimension.lower()}"
    manager = create_collection_manager(collection_name, vector_dim)
    await manager.ensure_collection()
    return manager
