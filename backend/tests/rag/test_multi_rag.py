"""Multi-Modal RAG Tests.

Multi-Modal RAG 시스템 테스트.
- 타입 정의 테스트
- 임베더 테스트 (mock)
- 컬렉션 매니저 테스트 (mock)
- 검색기 테스트 (mock)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.rag.multi_rag.types import (
    Modality,
    ContentType,
    SearchStrategy,
    DistanceMetric,
    VectorConfig,
    SparseVectorConfig,
    CollectionSchema,
    MultiModalDocument,
    MultiModalQuery,
    RetrievalResult,
    MultiModalSearchResult,
    EmbeddingResult,
    get_modalities_for_dimension,
    get_default_multimodal_schema,
    get_dimension_collection_name,
    DIMENSION_MODALITY_MAP,
    UNIFIED_EMBEDDING_DIM,
)


class TestModality:
    """Modality enum tests."""

    def test_modality_values(self):
        """Test modality enum values."""
        assert Modality.TEXT.value == "text"
        assert Modality.IMAGE.value == "image"
        assert Modality.AUDIO.value == "audio"
        assert Modality.VIDEO.value == "video"

    def test_modality_all(self):
        """Test Modality.all() method."""
        all_modalities = Modality.all()
        assert len(all_modalities) == 4
        assert Modality.TEXT in all_modalities
        assert Modality.IMAGE in all_modalities


class TestContentType:
    """ContentType enum tests."""

    def test_content_type_values(self):
        """Test content type values."""
        assert ContentType.SHOT.value == "shot"
        assert ContentType.TECHNIQUE.value == "technique"
        assert ContentType.AUTEUR_INSIGHT.value == "auteur_insight"


class TestVectorConfig:
    """VectorConfig tests."""

    def test_vector_config_creation(self):
        """Test VectorConfig creation."""
        config = VectorConfig("text_embed", 768, DistanceMetric.COSINE)
        assert config.name == "text_embed"
        assert config.size == 768
        assert config.distance == DistanceMetric.COSINE

    def test_to_qdrant_config(self):
        """Test conversion to Qdrant config."""
        config = VectorConfig("image_embed", 512, DistanceMetric.DOT)
        qdrant_config = config.to_qdrant_config()
        assert qdrant_config["size"] == 512
        assert qdrant_config["distance"] == "Dot"


class TestCollectionSchema:
    """CollectionSchema tests."""

    def test_collection_schema_creation(self):
        """Test CollectionSchema creation."""
        schema = CollectionSchema(
            name="test_collection",
            dense_vectors=[
                VectorConfig("text_embed", 768),
                VectorConfig("image_embed", 768),
            ],
            sparse_vectors=[
                SparseVectorConfig("text_bm25", modifier="idf"),
            ],
        )
        assert schema.name == "test_collection"
        assert len(schema.dense_vectors) == 2
        assert len(schema.sparse_vectors) == 1

    def test_to_qdrant_config(self):
        """Test conversion to Qdrant config."""
        schema = get_default_multimodal_schema("test_multimodal")
        config = schema.to_qdrant_config()
        
        assert config["collection_name"] == "test_multimodal"
        assert "vectors_config" in config
        assert "text_embed" in config["vectors_config"]
        assert "image_embed" in config["vectors_config"]
        assert "sparse_vectors_config" in config


class TestMultiModalDocument:
    """MultiModalDocument tests."""

    def test_document_creation(self):
        """Test document creation."""
        doc = MultiModalDocument(
            doc_id="doc_001",
            dimension="4D",
            modality=Modality.TEXT,
            content_type=ContentType.TECHNIQUE,
            text_content="Cinematic framing technique",
            auteur_key="kubrick",
        )
        assert doc.doc_id == "doc_001"
        assert doc.dimension == "4D"
        assert doc.modality == Modality.TEXT

    def test_evidence_ref_generation(self):
        """Test evidence_ref generation."""
        doc = MultiModalDocument(
            doc_id="doc_123",
            dimension="3D",
            modality=Modality.IMAGE,
            content_type=ContentType.REFERENCE,
            auteur_key="nolan",
        )
        ref = doc.get_evidence_ref()
        assert ref == "db:rag_docs:multimodal:3D:nolan:doc_123"

    def test_evidence_ref_without_auteur(self):
        """Test evidence_ref without auteur_key."""
        doc = MultiModalDocument(
            doc_id="doc_456",
            dimension="AD",
            modality=Modality.AUDIO,
            content_type=ContentType.MUSIC,
        )
        ref = doc.get_evidence_ref()
        assert ref == "db:rag_docs:multimodal:AD:doc_456"

    def test_has_modality_embedding(self):
        """Test has_modality_embedding method."""
        doc = MultiModalDocument(
            doc_id="doc_test",
            dimension="4D",
            modality=Modality.TEXT,
            content_type=ContentType.SHOT,
            embeddings={"text_embed": [0.1, 0.2, 0.3]},
        )
        assert doc.has_modality_embedding(Modality.TEXT)
        assert not doc.has_modality_embedding(Modality.IMAGE)


class TestMultiModalQuery:
    """MultiModalQuery tests."""

    def test_query_creation(self):
        """Test query creation."""
        query = MultiModalQuery(
            query_text="cinematic lighting",
            target_modalities=[Modality.IMAGE, Modality.VIDEO],
            search_strategy=SearchStrategy.CROSS_MODAL,
            top_k=10,
        )
        assert query.query_text == "cinematic lighting"
        assert len(query.target_modalities) == 2
        assert query.search_strategy == SearchStrategy.CROSS_MODAL

    def test_get_query_modality(self):
        """Test get_query_modality method."""
        text_query = MultiModalQuery(query_text="test")
        assert text_query.get_query_modality() == Modality.TEXT

        image_query = MultiModalQuery(query_image=b"image_data")
        assert image_query.get_query_modality() == Modality.IMAGE


class TestDimensionModalityMapping:
    """Dimension-Modality mapping tests."""

    def test_dimension_modality_map(self):
        """Test DIMENSION_MODALITY_MAP."""
        assert Modality.TEXT in DIMENSION_MODALITY_MAP["1D"]
        assert Modality.IMAGE in DIMENSION_MODALITY_MAP["3D"]
        assert Modality.VIDEO in DIMENSION_MODALITY_MAP["4D"]
        assert Modality.AUDIO in DIMENSION_MODALITY_MAP["AD"]

    def test_get_modalities_for_dimension(self):
        """Test get_modalities_for_dimension helper."""
        modalities_4d = get_modalities_for_dimension("4D")
        assert Modality.VIDEO in modalities_4d
        assert Modality.IMAGE in modalities_4d
        assert Modality.TEXT in modalities_4d

        modalities_ad = get_modalities_for_dimension("AD")
        assert Modality.AUDIO in modalities_ad

    def test_get_modalities_unknown_dimension(self):
        """Test fallback for unknown dimension."""
        modalities = get_modalities_for_dimension("UNKNOWN")
        assert modalities == [Modality.TEXT]


class TestDefaultSchema:
    """Default schema tests."""

    def test_get_default_multimodal_schema(self):
        """Test default schema creation."""
        schema = get_default_multimodal_schema()
        assert schema.name == "vivid_multimodal_auteur"
        assert len(schema.dense_vectors) == 4
        assert len(schema.sparse_vectors) == 1

    def test_unified_embedding_dim(self):
        """Test unified embedding dimension."""
        assert UNIFIED_EMBEDDING_DIM == 768

    def test_get_dimension_collection_name(self):
        """Test dimension collection name generation."""
        name = get_dimension_collection_name("4D")
        assert name == "vivid_multimodal_4d"

        name = get_dimension_collection_name("AD")
        assert name == "vivid_multimodal_ad"


class TestEmbeddingResult:
    """EmbeddingResult tests."""

    def test_embedding_result_creation(self):
        """Test EmbeddingResult creation."""
        result = EmbeddingResult(
            vector=[0.1] * 768,
            modality=Modality.TEXT,
            model="text-embedding-004",
            dimensions=768,
            processing_time_ms=50.0,
            tokens_used=100,
        )
        assert len(result.vector) == 768
        assert result.modality == Modality.TEXT
        assert result.dimensions == 768


class TestRetrievalResult:
    """RetrievalResult tests."""

    def test_retrieval_result_creation(self):
        """Test RetrievalResult creation."""
        result = RetrievalResult(
            doc_id="doc_001",
            score=0.95,
            modality=Modality.IMAGE,
            content_type=ContentType.REFERENCE,
            dimension="3D",
            evidence_ref="db:rag_docs:multimodal:3D:doc_001",
        )
        assert result.doc_id == "doc_001"
        assert result.score == 0.95
        assert result.evidence_ref.startswith("db:rag_docs:multimodal")


class TestMultiModalSearchResult:
    """MultiModalSearchResult tests."""

    def test_search_result_creation(self):
        """Test MultiModalSearchResult creation."""
        query = MultiModalQuery(query_text="test")
        result = MultiModalSearchResult(
            query=query,
            results=[],
            total_found=0,
            search_time_ms=10.0,
        )
        assert result.total_found == 0
        assert result.search_time_ms == 10.0


# =============================================================================
# Embedder Tests (with mocks)
# =============================================================================


class TestGeminiEmbedderMock:
    """GeminiMultiModalEmbedder tests with mocks."""

    @pytest.mark.asyncio
    async def test_embed_text_mock(self):
        """Test text embedding with mock (google.genai - new library)."""
        with patch("app.rag.multi_rag.embedders.gemini_embedder._get_genai_client") as mock_client:
            # Setup mock - new API returns embeddings[0].values
            mock_embedding = MagicMock()
            mock_embedding.values = [0.1] * 768
            mock_response = MagicMock()
            mock_response.embeddings = [mock_embedding]
            mock_client.return_value.models.embed_content.return_value = mock_response

            from app.rag.multi_rag.embedders import GeminiMultiModalEmbedder

            embedder = GeminiMultiModalEmbedder()
            embedder._initialized = True  # Skip init check

            result = await embedder.embed_text("test text")

            assert len(result.vector) == 768
            assert result.modality == Modality.TEXT


# =============================================================================
# Integration-style Tests (with mocks for external services)
# =============================================================================


class TestCrossModalRetrieverMock:
    """CrossModalRetriever tests with mocks."""

    @pytest.mark.asyncio
    async def test_reciprocal_rank_fusion(self):
        """Test RRF algorithm."""
        from app.rag.multi_rag.retriever import reciprocal_rank_fusion

        list1 = [("doc1", 0.9), ("doc2", 0.8), ("doc3", 0.7)]
        list2 = [("doc2", 0.95), ("doc1", 0.85), ("doc4", 0.75)]

        fused = reciprocal_rank_fusion([list1, list2], k=60)

        # doc1 and doc2 should be at top due to appearing in both lists
        top_docs = [doc_id for doc_id, _ in fused[:2]]
        assert "doc1" in top_docs
        assert "doc2" in top_docs
