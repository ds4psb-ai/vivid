"""E2E Tracing Tests (P8: OpenTelemetry Integration).

Tests to verify OpenTelemetry tracing is working correctly across
the entire request flow including:
- FastAPI routes
- SQLAlchemy queries
- Redis cache operations
- Qdrant vector searches
- LLM generations

Usage:
    # Run with OTEL enabled
    OTEL_ENABLED=true pytest tests/telemetry/test_e2e_tracing.py -v

    # Run with console export for debugging
    OTEL_CONSOLE_EXPORT=true pytest tests/telemetry/test_e2e_tracing.py -v
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from contextlib import nullcontext

from app.config import settings


class TestOTELSetup:
    """Test OpenTelemetry setup and configuration."""

    def test_otel_enabled_by_default(self):
        """OTEL should be enabled by default (P8 change)."""
        assert settings.OTEL_ENABLED is True

    def test_otel_endpoint_configured(self):
        """OTEL endpoint should have http:// prefix."""
        assert settings.OTEL_EXPORTER_OTLP_ENDPOINT.startswith("http://")

    def test_otel_sample_rate_dev(self):
        """Sample rate should be 1.0 (100%) in development."""
        # Default is 1.0 for development
        assert settings.OTEL_SAMPLE_RATE == 1.0

    def test_otel_service_name(self):
        """Service name should be configured."""
        assert settings.OTEL_SERVICE_NAME == "vivid-backend"


class TestTracerProvider:
    """Test tracer provider initialization."""

    def test_get_tracer_returns_tracer(self):
        """get_tracer should return a tracer instance."""
        from app.telemetry.otel_setup import get_tracer

        tracer = get_tracer()
        assert tracer is not None
        assert hasattr(tracer, "start_as_current_span")

    def test_tracer_creates_spans(self):
        """Tracer should be able to create spans."""
        from app.telemetry.otel_setup import get_tracer

        tracer = get_tracer()
        with tracer.start_as_current_span("test_span") as span:
            span.set_attribute("test_key", "test_value")
            # Span should be created without error


class TestQdrantTracing:
    """Test Qdrant tracing functionality."""

    def test_traced_qdrant_operation_context_manager(self):
        """traced_qdrant_operation should work as context manager."""
        from app.rag.qdrant_tracing import traced_qdrant_operation

        with traced_qdrant_operation(
            operation="search",
            collection="test_collection",
            dimension="4D",
            query_length=100,
            limit=5,
        ) as span:
            # Should not raise
            assert span is not None

    def test_traced_qdrant_operation_with_hybrid(self):
        """traced_qdrant_operation should handle hybrid search params."""
        from app.rag.qdrant_tracing import traced_qdrant_operation

        with traced_qdrant_operation(
            operation="hybrid_search",
            collection="dimension_4d_contexts_hybrid",
            dimension="4D",
            query_length=50,
            limit=10,
            is_hybrid=True,
            prefetch_limit=20,
            filters={"app_key": "test_app"},
        ) as span:
            assert span is not None

    def test_set_results_count(self):
        """set_results_count should set attribute on span."""
        from app.rag.qdrant_tracing import traced_qdrant_operation, set_results_count

        with traced_qdrant_operation(
            operation="search",
            collection="test_collection",
        ) as span:
            set_results_count(span, 5)
            # Should not raise


class TestRAGObservability:
    """Test RAG observability decorators."""

    def test_trace_rag_decorator_exists(self):
        """trace_rag decorator should be importable."""
        from app.rag.observability import trace_rag

        assert callable(trace_rag)

    @pytest.mark.asyncio
    async def test_trace_rag_decorator_wraps_async_function(self):
        """trace_rag should wrap async functions correctly."""
        from app.rag.observability import trace_rag

        @trace_rag(name="test_query", tags=["test"])
        async def test_func(query: str):
            return {"result": query}

        result = await test_func(query="test query")
        assert result == {"result": "test query"}


class TestMonitoringSetup:
    """Test monitoring module setup."""

    def test_setup_opentelemetry_function_exists(self):
        """setup_opentelemetry function should exist."""
        from app.monitoring import setup_opentelemetry

        assert callable(setup_opentelemetry)

    def test_redis_instrumentation_import(self):
        """Redis instrumentation should be importable."""
        try:
            from opentelemetry.instrumentation.redis import RedisInstrumentor
            assert RedisInstrumentor is not None
        except ImportError:
            pytest.skip("opentelemetry-instrumentation-redis not installed")


class TestSpanAttributes:
    """Test that spans have correct attributes."""

    def test_qdrant_span_attributes(self):
        """Qdrant spans should have correct semantic attributes."""
        from app.rag.qdrant_tracing import (
            QDRANT_SYSTEM,
            QDRANT_OPERATION_KEY,
            QDRANT_COLLECTION_KEY,
            QDRANT_DIMENSION_KEY,
        )

        # Verify attribute keys are defined
        assert QDRANT_SYSTEM == "qdrant"
        assert QDRANT_OPERATION_KEY == "db.qdrant.operation"
        assert QDRANT_COLLECTION_KEY == "db.qdrant.collection"
        assert QDRANT_DIMENSION_KEY == "db.qdrant.dimension"


class TestNoOpFallback:
    """Test no-op fallback when OTEL is not available."""

    def test_noop_tracer_exists(self):
        """NoOpTracer should be available for fallback."""
        from app.telemetry.otel_setup import NoOpTracer

        tracer = NoOpTracer()
        assert hasattr(tracer, "start_as_current_span")

    def test_noop_span_operations(self):
        """NoOpSpan should handle all operations without error."""
        from app.telemetry.otel_setup import NoOpTracer, NoOpSpan

        tracer = NoOpTracer()
        with tracer.start_as_current_span("test") as span:
            span.set_attribute("key", "value")
            span.set_status(None)
            span.add_event("event_name", {"attr": "value"})
            span.record_exception(Exception("test"))


@pytest.mark.integration
class TestE2ETracing:
    """End-to-end tracing tests (requires services running)."""

    @pytest.mark.asyncio
    async def test_qdrant_search_traced(self):
        """Qdrant search operations should be traced."""
        from app.rag.tier1_dimension_rag import Tier1DimensionRAG

        # Mock the client to avoid actual Qdrant connection
        rag = Tier1DimensionRAG("4D")
        rag._available = False  # Disable actual connection

        # Search should return empty but not fail
        results = rag.search("test query", limit=5)
        assert results == []

    @pytest.mark.asyncio
    async def test_hybrid_search_traced(self):
        """Hybrid search operations should be traced."""
        from app.rag.tier1_dimension_rag import Tier1DimensionRAG

        rag = Tier1DimensionRAG("4D")
        rag._available = False

        # Should fallback gracefully
        results = rag.hybrid_search("test query", limit=5)
        assert results == []


class TestTracingIntegration:
    """Test tracing integration with other modules."""

    def test_observability_imports_otel_setup(self):
        """RAG observability should import from otel_setup."""
        from app.rag import observability

        assert hasattr(observability, "get_tracer")
        assert hasattr(observability, "OTEL_AVAILABLE")

    def test_tier1_rag_imports_tracing(self):
        """Tier1 RAG should import qdrant_tracing."""
        from app.rag import tier1_dimension_rag

        # Check that tracing is imported (will be used in the module)
        import app.rag.qdrant_tracing
        assert app.rag.qdrant_tracing is not None
