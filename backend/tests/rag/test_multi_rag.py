"""Multi-RAG System Tests (P0 2026).

Tests for the Multi-RAG Router, Registry, and Orchestrator.

Coverage:
    - RAGSourceRegistry: register, unregister, query methods
    - IntelligentRAGRouter: rule-based routing, context-based routing
    - MultiRAGOrchestrator: parallel execution, RRF fusion
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rag.multi_rag import (
    RAGSourceType,
    RAGSourceSpec,
    RAGSourceRegistry,
    IntelligentRAGRouter,
    MultiRAGOrchestrator,
    MultiRAGDocument,
    MultiRAGResult,
    RouteDecision,
    get_registry,
    reset_registry,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_backend():
    """Mock RAGSourceBackend."""
    backend = AsyncMock()
    backend.query.return_value = [
        {"id": "doc_1", "content": "Test content 1", "score": 0.9},
        {"id": "doc_2", "content": "Test content 2", "score": 0.8},
        {"id": "doc_3", "content": "Test content 3", "score": 0.7},
    ]
    backend.health_check.return_value = True
    return backend


@pytest.fixture
def auteur_spec():
    """Sample auteur DNA source spec."""
    return RAGSourceSpec(
        source_id="test_notebooklm_bong",
        source_type=RAGSourceType.AUTEUR_DNA,
        display_name="봉준호 DNA (Test)",
        description="Test auteur DNA source",
        keywords=["봉준호", "bong", "기생충", "계단"],
        priority=10,
        latency_ms_avg=2000,
        backend_type="notebooklm",
        connection_config={"notebook_id": "DNA_봉준호"},
        auteur_keys=["bong", "봉준호"],
    )


@pytest.fixture
def dimension_spec():
    """Sample dimension knowledge source spec."""
    return RAGSourceSpec(
        source_id="test_qdrant_4d",
        source_type=RAGSourceType.DIMENSION_KNOWLEDGE,
        display_name="4D 분석 지식 (Test)",
        description="Test dimension knowledge source",
        keywords=["분석", "analysis", "레퍼런스", "구도"],
        priority=8,
        latency_ms_avg=500,
        backend_type="qdrant",
        connection_config={"dimension": "4D"},
        dimensions=["4D"],
    )


@pytest.fixture
def registry_with_sources(mock_backend, auteur_spec, dimension_spec):
    """Registry with pre-registered sources."""
    reset_registry()
    registry = get_registry()
    registry.register_sync(auteur_spec, mock_backend)
    registry.register_sync(dimension_spec, mock_backend)
    return registry


# =============================================================================
# RAGSourceRegistry Tests
# =============================================================================

class TestRAGSourceRegistry:
    """RAGSourceRegistry tests."""

    def test_register_sync(self, mock_backend, auteur_spec):
        """Test synchronous registration."""
        reset_registry()
        registry = get_registry()

        registry.register_sync(auteur_spec, mock_backend)

        assert auteur_spec.source_id in registry
        assert len(registry) == 1
        assert registry.get_spec(auteur_spec.source_id) == auteur_spec
        assert registry.get_backend(auteur_spec.source_id) == mock_backend

    @pytest.mark.asyncio
    async def test_register_async(self, mock_backend, auteur_spec):
        """Test asynchronous registration."""
        reset_registry()
        registry = get_registry()

        await registry.register(auteur_spec, mock_backend)

        assert auteur_spec.source_id in registry

    @pytest.mark.asyncio
    async def test_register_duplicate_raises(self, mock_backend, auteur_spec):
        """Test duplicate registration raises error."""
        reset_registry()
        registry = get_registry()

        await registry.register(auteur_spec, mock_backend)

        with pytest.raises(ValueError, match="already registered"):
            await registry.register(auteur_spec, mock_backend)

    @pytest.mark.asyncio
    async def test_unregister(self, mock_backend, auteur_spec):
        """Test unregistration."""
        reset_registry()
        registry = get_registry()

        await registry.register(auteur_spec, mock_backend)
        result = await registry.unregister(auteur_spec.source_id)

        assert result is True
        assert auteur_spec.source_id not in registry

    def test_get_enabled_sources(self, registry_with_sources):
        """Test get enabled sources."""
        sources = registry_with_sources.get_enabled_sources()

        assert len(sources) == 2
        # Sorted by priority descending
        assert sources[0].priority >= sources[1].priority

    def test_get_by_type(self, registry_with_sources):
        """Test filter by type."""
        auteur_sources = registry_with_sources.get_by_type(RAGSourceType.AUTEUR_DNA)
        dimension_sources = registry_with_sources.get_by_type(RAGSourceType.DIMENSION_KNOWLEDGE)

        assert len(auteur_sources) == 1
        assert auteur_sources[0].source_id == "test_notebooklm_bong"
        assert len(dimension_sources) == 1
        assert dimension_sources[0].source_id == "test_qdrant_4d"

    def test_get_by_dimension(self, registry_with_sources):
        """Test filter by dimension."""
        sources_4d = registry_with_sources.get_by_dimension("4D")

        # 4D dimension source should be included
        assert any(s.source_id == "test_qdrant_4d" for s in sources_4d)

    def test_get_by_auteur(self, registry_with_sources):
        """Test filter by auteur key."""
        sources_bong = registry_with_sources.get_by_auteur("bong")

        assert len(sources_bong) >= 1
        assert any(s.source_id == "test_notebooklm_bong" for s in sources_bong)

    @pytest.mark.asyncio
    async def test_health_check(self, registry_with_sources, mock_backend):
        """Test health check."""
        is_healthy = await registry_with_sources.check_health("test_notebooklm_bong")

        assert is_healthy is True
        mock_backend.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_failure(self, registry_with_sources, mock_backend):
        """Test health check failure."""
        mock_backend.health_check.side_effect = Exception("Connection failed")

        is_healthy = await registry_with_sources.check_health("test_notebooklm_bong")

        assert is_healthy is False

    def test_stats(self, registry_with_sources):
        """Test registry statistics."""
        stats = registry_with_sources.stats()

        assert stats["total"] == 2
        assert stats["enabled"] == 2
        assert stats["type_auteur_dna"] == 1
        assert stats["type_dimension"] == 1


# =============================================================================
# IntelligentRAGRouter Tests
# =============================================================================

class TestIntelligentRAGRouter:
    """IntelligentRAGRouter tests."""

    @pytest.mark.asyncio
    async def test_route_auteur_query(self, registry_with_sources):
        """Test routing auteur-related query."""
        router = IntelligentRAGRouter(registry_with_sources)

        decision = await router.route(
            query="봉준호 감독의 계단 연출",
            context={"auteur_key": "bong"},
        )

        assert "test_notebooklm_bong" in decision.selected_sources
        assert decision.confidence > 0.5
        assert decision.routing_strategy == "rule_based"

    @pytest.mark.asyncio
    async def test_route_dimension_query(self, registry_with_sources):
        """Test routing dimension-related query."""
        router = IntelligentRAGRouter(registry_with_sources)

        decision = await router.route(
            query="레퍼런스 분석 방법",
            context={"dimension": "4D"},
        )

        assert "test_qdrant_4d" in decision.selected_sources
        assert decision.confidence > 0

    @pytest.mark.asyncio
    async def test_route_with_keywords(self, registry_with_sources):
        """Test routing with keyword matching."""
        router = IntelligentRAGRouter(registry_with_sources)

        decision = await router.route(
            query="기생충 영화의 구도 분석",
            context={},
        )

        # Should match both auteur (기생충) and dimension (구도, 분석) keywords
        assert len(decision.selected_sources) >= 1

    @pytest.mark.asyncio
    async def test_route_max_sources(self, registry_with_sources):
        """Test max sources limit."""
        router = IntelligentRAGRouter(registry_with_sources, max_sources=1)

        decision = await router.route(
            query="봉준호 분석",
            context={},
            max_sources=1,
        )

        assert len(decision.selected_sources) <= 1

    @pytest.mark.asyncio
    async def test_route_empty_query(self, registry_with_sources):
        """Test routing with empty result."""
        router = IntelligentRAGRouter(registry_with_sources)

        # Query with no matching keywords
        decision = await router.route(
            query="xyz123 completely unrelated",
            context={},
        )

        # Should still return some results based on priority
        # (or empty if no matches at all)
        assert isinstance(decision.selected_sources, list)

    @pytest.mark.asyncio
    async def test_route_confidence_calculation(self, registry_with_sources):
        """Test confidence calculation."""
        router = IntelligentRAGRouter(registry_with_sources)

        # High confidence: exact auteur match + keywords
        high_conf_decision = await router.route(
            query="봉준호 기생충 계단",
            context={"auteur_key": "bong"},
        )

        # Lower confidence: generic query
        low_conf_decision = await router.route(
            query="영화 분석",
            context={},
        )

        assert high_conf_decision.confidence >= low_conf_decision.confidence


# =============================================================================
# MultiRAGOrchestrator Tests
# =============================================================================

class TestMultiRAGOrchestrator:
    """MultiRAGOrchestrator tests."""

    @pytest.mark.asyncio
    async def test_query_parallel_execution(self, registry_with_sources, mock_backend):
        """Test parallel query execution."""
        orchestrator = MultiRAGOrchestrator(registry_with_sources)

        result = await orchestrator.query(
            query="봉준호 분석",
            context={"auteur_key": "bong"},
            limit=5,
        )

        assert isinstance(result, MultiRAGResult)
        assert len(result.documents) > 0
        assert len(result.sources_used) > 0
        assert result.query_time_ms >= 0  # Can be 0 for fast mock backends

    @pytest.mark.asyncio
    async def test_rrf_fusion(self, registry_with_sources, mock_backend):
        """Test RRF fusion algorithm."""
        # Setup different results for each backend call
        results_call_count = [0]

        async def mock_query(query, filters=None, limit=10):
            results_call_count[0] += 1
            if results_call_count[0] == 1:
                return [
                    {"id": "doc_a", "content": "Content A", "score": 0.9},
                    {"id": "doc_b", "content": "Content B", "score": 0.8},
                ]
            else:
                return [
                    {"id": "doc_b", "content": "Content B", "score": 0.85},  # Same doc
                    {"id": "doc_c", "content": "Content C", "score": 0.7},
                ]

        mock_backend.query = mock_query

        orchestrator = MultiRAGOrchestrator(registry_with_sources)

        result = await orchestrator.query(
            query="봉준호 분석",
            context={"auteur_key": "bong", "dimension": "4D"},
            limit=5,
        )

        # doc_b should have higher score due to appearing in both results
        doc_ids = [doc.doc_id for doc in result.documents]
        assert "doc_b" in doc_ids

    @pytest.mark.asyncio
    async def test_timeout_handling(self, registry_with_sources, mock_backend):
        """Test timeout handling for slow backends."""
        async def slow_query(*args, **kwargs):
            await asyncio.sleep(20)  # Longer than timeout
            return []

        mock_backend.query = slow_query

        orchestrator = MultiRAGOrchestrator(
            registry_with_sources,
            default_timeout=0.1,  # Very short timeout
        )

        # Should not raise, but return empty or partial results
        result = await orchestrator.query(
            query="test query",
            context={},
        )

        assert isinstance(result, MultiRAGResult)

    @pytest.mark.asyncio
    async def test_empty_sources(self, mock_backend):
        """Test with no sources registered."""
        reset_registry()
        registry = get_registry()
        orchestrator = MultiRAGOrchestrator(registry)

        result = await orchestrator.query(
            query="test query",
            context={},
        )

        assert result.documents == []
        assert result.sources_used == []

    @pytest.mark.asyncio
    async def test_result_metadata(self, registry_with_sources, mock_backend):
        """Test result metadata preservation."""
        mock_backend.query.return_value = [
            {
                "id": "doc_1",
                "content": "Test content",
                "score": 0.9,
                "metadata": {"custom_field": "custom_value"},
            },
        ]

        orchestrator = MultiRAGOrchestrator(registry_with_sources)

        result = await orchestrator.query(
            query="test",
            context={"auteur_key": "bong"},
            limit=5,
        )

        if result.documents:
            assert "rrf_score" in result.documents[0].metadata


# =============================================================================
# Integration Tests
# =============================================================================

class TestMultiRAGIntegration:
    """Integration tests for the full Multi-RAG pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, mock_backend):
        """Test full pipeline: register → route → query."""
        reset_registry()
        registry = get_registry()

        # 1. Register sources
        auteur_spec = RAGSourceSpec(
            source_id="integ_auteur",
            source_type=RAGSourceType.AUTEUR_DNA,
            display_name="Integration Test Auteur",
            description="Test source",
            keywords=["test", "auteur"],
            priority=10,
            backend_type="mock",
            connection_config={},
        )

        registry.register_sync(auteur_spec, mock_backend)

        # 2. Create router and orchestrator
        router = IntelligentRAGRouter(registry)
        orchestrator = MultiRAGOrchestrator(registry, router)

        # 3. Execute query
        result = await orchestrator.query(
            query="test auteur query",
            context={},
            limit=5,
        )

        # 4. Verify results
        assert isinstance(result, MultiRAGResult)
        assert result.routing_decision is not None
        assert "integ_auteur" in result.sources_used

    @pytest.mark.asyncio
    async def test_backward_compatibility(self, mock_backend):
        """Test backward compatibility with HybridRAGResult interface."""
        reset_registry()
        registry = get_registry()

        spec = RAGSourceSpec(
            source_id="compat_test",
            source_type=RAGSourceType.DIMENSION_KNOWLEDGE,
            display_name="Compatibility Test",
            description="Test",
            keywords=["test"],
            priority=5,
            backend_type="mock",
            connection_config={},
        )

        registry.register_sync(spec, mock_backend)

        orchestrator = MultiRAGOrchestrator(registry)

        result = await orchestrator.query(
            query="test query",
            context={},
        )

        # HybridRAGResult compatible properties
        assert hasattr(result, "confidence")
        assert hasattr(result, "answer")
        assert isinstance(result.confidence, float)
        assert isinstance(result.answer, str)
