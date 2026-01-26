"""Multi-Modal RAG Module (2026 Best Practices).

멀티모달 임베딩 기반 RAG 시스템.
- Named Vectors 기반 Qdrant 컬렉션
- 크로스모달 검색 (텍스트 → 이미지/비디오)
- Hybrid RRF 검색 (Dense + Sparse)
- Dimension별 모달리티 매핑

Architecture:
    - types.py: 타입 정의 (Modality, ContentType, MultiModalDocument, etc.)
    - embedders/: 멀티모달 임베더 (Gemini, future: ImageBind, Voyage)
    - collection_manager.py: Qdrant Named Vectors 컬렉션 관리
    - retriever.py: 크로스모달 하이브리드 검색
    - service.py: 통합 서비스 API

Usage:
    from app.rag.multi_rag import (
        MultiModalRAGService,
        Modality,
        ContentType,
        SearchStrategy,
    )

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
    )

    # evidence_refs 추출
    refs = [r.evidence_ref for r in results.results]
    # ['db:rag_docs:multimodal:4D:bong:doc_id', ...]

References:
    - Qdrant Named Vectors: https://qdrant.tech/documentation/concepts/vectors/
    - Google Gemini Embedding: https://ai.google.dev/gemini-api/docs/embeddings
    - RRF Fusion: https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
"""

from app.rag.multi_rag.types import (
    # Enums
    Modality,
    ContentType,
    SearchStrategy,
    DistanceMetric,
    # Vector Config
    VectorConfig,
    SparseVectorConfig,
    CollectionSchema,
    # Documents
    MultiModalDocument,
    EmbeddingResult,
    SparseEmbeddingResult,
    # Query/Result
    MultiModalQuery,
    RetrievalResult,
    MultiModalSearchResult,
    # Protocol
    MultiModalEmbedder,
    # Constants
    DIMENSION_MODALITY_MAP,
    UNIFIED_EMBEDDING_DIM,
    # Helpers
    get_modalities_for_dimension,
    get_default_multimodal_schema,
    get_dimension_collection_name,
)

from app.rag.multi_rag.embedders import (
    BaseMultiModalEmbedder,
    GeminiMultiModalEmbedder,
    EmbedderError,
    ModalityNotSupportedError,
)

from app.rag.multi_rag.collection_manager import (
    MultiModalCollectionManager,
    create_collection_manager,
    create_dimension_collection,
    get_qdrant_client,
    reset_qdrant_client,
)

from app.rag.multi_rag.retriever import (
    CrossModalRetriever,
    create_retriever,
    reciprocal_rank_fusion,
)

from app.rag.multi_rag.service import (
    MultiModalRAGService,
    create_multimodal_rag_service,
    get_multimodal_rag_service,
)

__all__ = [
    # === Types ===
    # Enums
    "Modality",
    "ContentType",
    "SearchStrategy",
    "DistanceMetric",
    # Vector Config
    "VectorConfig",
    "SparseVectorConfig",
    "CollectionSchema",
    # Documents
    "MultiModalDocument",
    "EmbeddingResult",
    "SparseEmbeddingResult",
    # Query/Result
    "MultiModalQuery",
    "RetrievalResult",
    "MultiModalSearchResult",
    # Protocol
    "MultiModalEmbedder",
    # Constants
    "DIMENSION_MODALITY_MAP",
    "UNIFIED_EMBEDDING_DIM",
    # Helpers
    "get_modalities_for_dimension",
    "get_default_multimodal_schema",
    "get_dimension_collection_name",
    # === Embedders ===
    "BaseMultiModalEmbedder",
    "GeminiMultiModalEmbedder",
    "EmbedderError",
    "ModalityNotSupportedError",
    # === Collection Manager ===
    "MultiModalCollectionManager",
    "create_collection_manager",
    "create_dimension_collection",
    "get_qdrant_client",
    "reset_qdrant_client",
    # === Retriever ===
    "CrossModalRetriever",
    "create_retriever",
    "reciprocal_rank_fusion",
    # === Service ===
    "MultiModalRAGService",
    "create_multimodal_rag_service",
    "get_multimodal_rag_service",
]
