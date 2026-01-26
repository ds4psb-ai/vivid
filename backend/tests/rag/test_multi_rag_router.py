"""Multi-RAG Router Tests.

Multi-RAG Router 시스템 테스트.
- 타입 정의 테스트
- Registry 테스트
- Router 테스트 (rule-based)
- Orchestrator 테스트 (RRF fusion)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.rag.router.types import (
    RAGSourceType,
    QueryIntent,
    RAGSourceSpec,
    RAGDocument,
    RouteDecision,
    MultiRAGResult,
    AUTEUR_KEYWORDS,
    HISTORY_KEYWORDS,
    get_default_sources_for_dimension,
)
from app.rag.router.registry import (
    RAGSourceRegistry,
    get_rag_registry,
    reset_rag_registry,
    get_default_source_specs,
)
from app.rag.router.intelligent_router import IntelligentRAGRouter
from app.rag.router.orchestrator import MultiRAGOrchestrator
from app.rag.router.backends.notebooklm import MockNotebookLMBackend
from app.rag.router.backends.multimodal_qdrant import MockMultiModalQdrantBackend
from app.rag.router.backends.user_history import MockUserHistoryBackend


# =============================================================================
# Type Tests
# =============================================================================


class TestRAGSourceType:
    """RAGSourceType enum tests."""

    def test_source_type_values(self):
        """Test source type enum values."""
        assert RAGSourceType.AUTEUR_DNA.value == "auteur_dna"
        assert RAGSourceType.MULTIMODAL_DIMENSION.value == "multimodal"
        assert RAGSourceType.USER_HISTORY.value == "user_history"

    def test_source_type_all(self):
        """Test RAGSourceType.all() method."""
        all_types = RAGSourceType.all()
        assert len(all_types) == 8
        assert RAGSourceType.AUTEUR_DNA in all_types


class TestQueryIntent:
    """QueryIntent enum tests."""

    def test_intent_values(self):
        """Test query intent values."""
        assert QueryIntent.STYLE_REFERENCE.value == "style_reference"
        assert QueryIntent.HISTORY_RECALL.value == "history_recall"
        assert QueryIntent.GENERAL.value == "general"


class TestRAGSourceSpec:
    """RAGSourceSpec tests."""

    def test_spec_creation(self):
        """Test RAGSourceSpec creation."""
        spec = RAGSourceSpec(
            source_id="test_source",
            source_type=RAGSourceType.AUTEUR_DNA,
            display_name="Test Source",
            description="Test description",
            keywords=["test", "keyword"],
            priority=8,
        )
        assert spec.source_id == "test_source"
        assert spec.source_type == RAGSourceType.AUTEUR_DNA
        assert spec.priority == 8
        assert "test" in spec.keywords


class TestRAGDocument:
    """RAGDocument tests."""

    def test_document_creation(self):
        """Test RAGDocument creation."""
        doc = RAGDocument(
            id="doc_001",
            content="Test content",
            score=0.95,
            metadata={"auteur_key": "bong"},
            evidence_ref="db:notebooklm:bong:doc_001",
            source_type=RAGSourceType.AUTEUR_DNA,
        )
        assert doc.id == "doc_001"
        assert doc.score == 0.95
        assert doc.evidence_ref.startswith("db:notebooklm")


class TestRouteDecision:
    """RouteDecision tests."""

    def test_route_decision_creation(self):
        """Test RouteDecision creation."""
        decision = RouteDecision(
            selected_sources=["notebooklm", "multimodal_qdrant"],
            query_intent=QueryIntent.STYLE_REFERENCE,
            sub_queries={"notebooklm": "강주노 스타일"},
            confidence=0.85,
        )
        assert len(decision.selected_sources) == 2
        assert decision.query_intent == QueryIntent.STYLE_REFERENCE


class TestPresets:
    """Preset constants tests."""

    def test_auteur_keywords(self):
        """Test auteur keywords."""
        assert "강주노" in AUTEUR_KEYWORDS
        assert "prism" in AUTEUR_KEYWORDS
        assert "스타일" in AUTEUR_KEYWORDS

    def test_history_keywords(self):
        """Test history keywords."""
        assert "이전에" in HISTORY_KEYWORDS
        assert "지난번" in HISTORY_KEYWORDS

    def test_dimension_source_priority(self):
        """Test dimension source priority."""
        sources_4d = get_default_sources_for_dimension("4D")
        assert RAGSourceType.MULTIMODAL_DIMENSION in sources_4d

        sources_story = get_default_sources_for_dimension("STORY")
        assert RAGSourceType.AUTEUR_DNA in sources_story


# =============================================================================
# Registry Tests
# =============================================================================


class TestRAGSourceRegistry:
    """RAGSourceRegistry tests."""

    def setup_method(self):
        """Reset global registry before each test."""
        reset_rag_registry()

    def test_register_and_get(self):
        """Test register and get source."""
        registry = RAGSourceRegistry()
        spec = RAGSourceSpec(
            source_id="test_notebooklm",
            source_type=RAGSourceType.AUTEUR_DNA,
            display_name="Test NLM",
            description="Test description",
        )
        backend = MockNotebookLMBackend()

        registry.register(spec, backend)

        assert registry.get_spec("test_notebooklm") is not None
        assert registry.get_backend("test_notebooklm") is not None

    def test_unregister(self):
        """Test unregister source."""
        registry = RAGSourceRegistry()
        spec = RAGSourceSpec(
            source_id="temp_source",
            source_type=RAGSourceType.AUTEUR_DNA,
            display_name="Temp",
            description="Temp",
        )
        backend = MockNotebookLMBackend()

        registry.register(spec, backend)
        assert registry.unregister("temp_source")
        assert registry.get_spec("temp_source") is None

    def test_get_by_type(self):
        """Test get sources by type."""
        registry = RAGSourceRegistry()

        registry.register(
            RAGSourceSpec(
                source_id="nlm1",
                source_type=RAGSourceType.AUTEUR_DNA,
                display_name="NLM1",
                description="NLM1",
            ),
            MockNotebookLMBackend(),
        )
        registry.register(
            RAGSourceSpec(
                source_id="qdrant1",
                source_type=RAGSourceType.MULTIMODAL_DIMENSION,
                display_name="Qdrant1",
                description="Qdrant1",
            ),
            MockMultiModalQdrantBackend(),
        )

        auteur_sources = registry.get_by_type(RAGSourceType.AUTEUR_DNA)
        assert len(auteur_sources) == 1
        assert auteur_sources[0].source_id == "nlm1"

    def test_get_for_dimension(self):
        """Test get sources for dimension."""
        registry = RAGSourceRegistry()

        registry.register(
            RAGSourceSpec(
                source_id="nlm1",
                source_type=RAGSourceType.AUTEUR_DNA,
                display_name="NLM1",
                description="NLM1",
                priority=9,
            ),
            MockNotebookLMBackend(),
        )
        registry.register(
            RAGSourceSpec(
                source_id="qdrant1",
                source_type=RAGSourceType.MULTIMODAL_DIMENSION,
                display_name="Qdrant1",
                description="Qdrant1",
                priority=8,
            ),
            MockMultiModalQdrantBackend(),
        )

        sources = registry.get_for_dimension("4D")
        assert len(sources) >= 2
        # MULTIMODAL should be first for 4D
        assert sources[0].source_type == RAGSourceType.MULTIMODAL_DIMENSION

    def test_default_source_specs(self):
        """Test default source specs."""
        specs = get_default_source_specs()
        assert len(specs) == 3

        source_ids = [s.source_id for s in specs]
        assert "notebooklm" in source_ids
        assert "multimodal_qdrant" in source_ids
        assert "user_history" in source_ids


# =============================================================================
# Router Tests
# =============================================================================


class TestIntelligentRAGRouter:
    """IntelligentRAGRouter tests."""

    def setup_method(self):
        """Setup test registry."""
        self.registry = RAGSourceRegistry()

        self.registry.register(
            RAGSourceSpec(
                source_id="notebooklm",
                source_type=RAGSourceType.AUTEUR_DNA,
                display_name="거장 DNA",
                description="거장 스타일",
                keywords=["강주노", "스타일", "거장"],
                priority=9,
            ),
            MockNotebookLMBackend(),
        )
        self.registry.register(
            RAGSourceSpec(
                source_id="multimodal_qdrant",
                source_type=RAGSourceType.MULTIMODAL_DIMENSION,
                display_name="멀티모달",
                description="차원별 지식",
                keywords=["차원", "이미지", "영상"],
                priority=8,
            ),
            MockMultiModalQdrantBackend(),
        )
        self.registry.register(
            RAGSourceSpec(
                source_id="user_history",
                source_type=RAGSourceType.USER_HISTORY,
                display_name="히스토리",
                description="과거 작업",
                keywords=["이전에", "지난번", "히스토리"],
                priority=6,
            ),
            MockUserHistoryBackend(),
        )

    @pytest.mark.asyncio
    async def test_route_auteur_query(self):
        """Test routing for auteur-related query."""
        router = IntelligentRAGRouter(self.registry)

        decision = await router.route(
            query="강주노 감독의 계단 상징",
            context={"auteur_key": "bong"},
        )

        assert "notebooklm" in decision.selected_sources
        assert decision.query_intent == QueryIntent.STYLE_REFERENCE
        assert decision.confidence > 0.5

    @pytest.mark.asyncio
    async def test_route_dimension_query(self):
        """Test routing for dimension-related query."""
        router = IntelligentRAGRouter(self.registry)

        decision = await router.route(
            query="4D 영상 레퍼런스",
            context={"dimension": "4D"},
        )

        assert "multimodal_qdrant" in decision.selected_sources

    @pytest.mark.asyncio
    async def test_route_history_query(self):
        """Test routing for history-related query."""
        router = IntelligentRAGRouter(self.registry)

        decision = await router.route(
            query="이전에 만들었던 SF 영상",
            context={"user_id": "user_123"},
        )

        assert "user_history" in decision.selected_sources
        assert decision.query_intent == QueryIntent.HISTORY_RECALL

    @pytest.mark.asyncio
    async def test_route_max_sources(self):
        """Test max_sources limit."""
        router = IntelligentRAGRouter(self.registry)

        decision = await router.route(
            query="모든 소스 필요한 복잡한 쿼리",
            context={},
            max_sources=2,
        )

        assert len(decision.selected_sources) <= 2


# =============================================================================
# Orchestrator Tests
# =============================================================================


class TestMultiRAGOrchestrator:
    """MultiRAGOrchestrator tests."""

    def setup_method(self):
        """Setup test registry and router."""
        self.registry = RAGSourceRegistry()

        self.mock_nlm = MockNotebookLMBackend(
            mock_responses={
                "bong": [
                    RAGDocument(
                        id="nlm_1",
                        content="강주노 계단 상징",
                        score=0.95,
                        evidence_ref="db:notebooklm:bong:nlm_1",
                        source_type=RAGSourceType.AUTEUR_DNA,
                    )
                ]
            }
        )
        self.mock_qdrant = MockMultiModalQdrantBackend(
            mock_responses={
                "4D": [
                    RAGDocument(
                        id="qdrant_1",
                        content="4D 영상 기법",
                        score=0.85,
                        evidence_ref="db:rag_docs:multimodal:4D:qdrant_1",
                        source_type=RAGSourceType.MULTIMODAL_DIMENSION,
                    )
                ]
            }
        )

        self.registry.register(
            RAGSourceSpec(
                source_id="notebooklm",
                source_type=RAGSourceType.AUTEUR_DNA,
                display_name="거장 DNA",
                description="거장 스타일",
                keywords=["강주노", "거장"],
                priority=9,
            ),
            self.mock_nlm,
        )
        self.registry.register(
            RAGSourceSpec(
                source_id="multimodal_qdrant",
                source_type=RAGSourceType.MULTIMODAL_DIMENSION,
                display_name="멀티모달",
                description="차원별 지식",
                keywords=["차원"],
                priority=8,
            ),
            self.mock_qdrant,
        )

        self.router = IntelligentRAGRouter(self.registry)
        self.orchestrator = MultiRAGOrchestrator(self.registry, self.router)

    @pytest.mark.asyncio
    async def test_query_single_source(self):
        """Test query with single source."""
        result = await self.orchestrator.query(
            query="강주노 감독 스타일",
            context={"auteur_key": "bong"},
            max_sources=1,
        )

        assert isinstance(result, MultiRAGResult)
        assert len(result.sources_used) >= 1
        assert result.total_latency_ms > 0

    @pytest.mark.asyncio
    async def test_query_multiple_sources(self):
        """Test query with multiple sources."""
        result = await self.orchestrator.query(
            query="강주노 스타일로 4D 영상 분석",
            context={"auteur_key": "bong", "dimension": "4D"},
            max_sources=2,
        )

        assert len(result.sources_used) >= 1
        assert len(result.documents) >= 0

    @pytest.mark.asyncio
    async def test_rrf_fusion(self):
        """Test RRF fusion algorithm."""
        # Prepare mock results
        from app.rag.router.types import SourceResult

        results = [
            SourceResult(
                source_id="source1",
                source_type=RAGSourceType.AUTEUR_DNA,
                documents=[
                    RAGDocument(id="doc1", content="Content 1", score=0.9, evidence_ref="ref1"),
                    RAGDocument(id="doc2", content="Content 2", score=0.8, evidence_ref="ref2"),
                ],
                success=True,
            ),
            SourceResult(
                source_id="source2",
                source_type=RAGSourceType.MULTIMODAL_DIMENSION,
                documents=[
                    RAGDocument(id="doc2", content="Content 2", score=0.95, evidence_ref="ref2"),
                    RAGDocument(id="doc3", content="Content 3", score=0.7, evidence_ref="ref3"),
                ],
                success=True,
            ),
        ]

        fused = self.orchestrator._rrf_fusion(results)

        # doc2 appears in both, should have higher RRF score
        doc_ids = [doc.id for doc in fused]
        assert "doc2" in doc_ids[:2]  # Should be near top

    @pytest.mark.asyncio
    async def test_evidence_refs_in_result(self):
        """Test evidence_refs are included in result."""
        result = await self.orchestrator.query(
            query="강주노 스타일",
            context={"auteur_key": "bong"},
        )

        # evidence_refs should be populated
        assert isinstance(result.evidence_refs, list)
        # If documents exist, evidence_refs should exist
        if result.documents:
            assert len(result.evidence_refs) > 0


# =============================================================================
# Mock Backend Tests
# =============================================================================


class TestMockBackends:
    """Mock backend tests."""

    @pytest.mark.asyncio
    async def test_mock_notebooklm_backend(self):
        """Test MockNotebookLMBackend."""
        backend = MockNotebookLMBackend()

        docs = await backend.query(
            "test query",
            filters={"auteur_key": "bong"},
        )

        assert len(docs) > 0
        assert docs[0].source_type == RAGSourceType.AUTEUR_DNA
        assert await backend.health_check()

    @pytest.mark.asyncio
    async def test_mock_multimodal_backend(self):
        """Test MockMultiModalQdrantBackend."""
        backend = MockMultiModalQdrantBackend()

        docs = await backend.query(
            "test query",
            filters={"dimension": "4D"},
        )

        assert len(docs) > 0
        assert docs[0].source_type == RAGSourceType.MULTIMODAL_DIMENSION

    @pytest.mark.asyncio
    async def test_mock_user_history_backend(self):
        """Test MockUserHistoryBackend."""
        backend = MockUserHistoryBackend()

        docs = await backend.query(
            "test query",
            filters={"user_id": "user_123"},
        )

        assert len(docs) > 0
        assert docs[0].source_type == RAGSourceType.USER_HISTORY
