"""Tests for app.core.unified_schemas."""
import pytest

from app.core.unified_schemas import (
    QueryType,
    Intent,
    Dimension,
    DataType,
    CheckpointAction,
    OrchestrationPattern,
    RetrievedDoc,
    EvidenceRef,
    SourceResult,
    ClassificationResult,
    RoutingDecision,
    RetrievalResult,
    ExecutionResult,
    UnifiedQueryRequest,
    UnifiedQueryResponse,
    QUERY_TYPE_STRATEGY_MAP,
    SKIP_RETRIEVAL_TYPES,
    INTENT_PATTERN_MAP,
)


class TestEnums:
    """Enum 타입 테스트."""

    def test_query_type_values(self):
        """QueryType 값 검증."""
        assert QueryType.SIMPLE_FACTUAL.value == "simple_factual"
        assert QueryType.CREATIVE.value == "creative"
        assert QueryType.DOMAIN_SPECIFIC.value == "domain_specific"
        assert QueryType.RECENCY_REQUIRED.value == "recency_required"
        assert QueryType.MULTI_HOP.value == "multi_hop"
        assert QueryType.AMBIGUOUS.value == "ambiguous"

    def test_intent_values(self):
        """Intent 값 검증."""
        assert Intent.GENERATE.value == "generate"
        assert Intent.ANALYZE.value == "analyze"
        assert Intent.CREATE.value == "create"
        assert Intent.VALIDATE.value == "validate"
        assert Intent.WORKFLOW.value == "workflow"
        assert Intent.CHAT.value == "chat"
        assert Intent.UNKNOWN.value == "unknown"

    def test_dimension_values(self):
        """Dimension 값 검증."""
        assert Dimension.ORIGIN.value == "1D"
        assert Dimension.BLUEPRINT.value == "2D"
        assert Dimension.AMBIENCE.value == "3D"
        assert Dimension.MOMENT.value == "4D"
        assert Dimension.QUALITY.value == "QC"
        assert Dimension.AESTHETIC.value == "AD"

    def test_data_type_values(self):
        """DataType 값 검증."""
        assert DataType.TEXT.value == "text"
        assert DataType.IMAGE_URL.value == "image_url"
        assert DataType.STYLE_HINT.value == "style_hint"

    def test_checkpoint_action_values(self):
        """CheckpointAction 값 검증."""
        assert CheckpointAction.APPROVE.value == "approve"
        assert CheckpointAction.REJECT.value == "reject"
        assert CheckpointAction.MODIFY.value == "modify"
        assert CheckpointAction.SKIP.value == "skip"

    def test_orchestration_pattern_values(self):
        """OrchestrationPattern 값 검증."""
        assert OrchestrationPattern.DIRECT.value == "direct"
        assert OrchestrationPattern.LINEAR.value == "linear"
        assert OrchestrationPattern.PARALLEL.value == "parallel"


class TestDataClasses:
    """데이터 클래스 테스트."""

    def test_retrieved_doc_creation(self):
        """RetrievedDoc 생성 테스트."""
        doc = RetrievedDoc(
            id="doc_123",
            content="테스트 내용",
            score=0.95,
            source="qdrant",
            metadata={"author": "bong"},
        )

        assert doc.id == "doc_123"
        assert doc.content == "테스트 내용"
        assert doc.score == 0.95
        assert doc.source == "qdrant"
        assert doc.metadata["author"] == "bong"

    def test_evidence_ref_from_doc(self):
        """EvidenceRef.from_doc 테스트."""
        doc = RetrievedDoc(
            id="doc_123",
            content="내용",
            score=0.9,
            source="notebooklm",
        )

        ref = EvidenceRef.from_doc(doc)
        assert ref.ref == "db:notebooklm:doc_123"
        assert str(ref) == "db:notebooklm:doc_123"

    def test_source_result_creation(self):
        """SourceResult 생성 테스트."""
        docs = [
            RetrievedDoc(id="1", content="a", score=0.9, source="qdrant"),
            RetrievedDoc(id="2", content="b", score=0.8, source="qdrant"),
        ]

        result = SourceResult(
            source="qdrant",
            docs=docs,
            latency_ms=150.0,
        )

        assert result.source == "qdrant"
        assert len(result.docs) == 2
        assert result.latency_ms == 150.0
        assert result.error is None

    def test_classification_result(self):
        """ClassificationResult 테스트."""
        result = ClassificationResult(
            query_type=QueryType.DOMAIN_SPECIFIC,
            intent=Intent.ANALYZE,
            confidence=0.85,
            dimension=Dimension.MOMENT,
            auteur_key="bong",
        )

        assert result.query_type == QueryType.DOMAIN_SPECIFIC
        assert result.intent == Intent.ANALYZE
        assert result.confidence == 0.85
        assert result.dimension == Dimension.MOMENT
        assert result.auteur_key == "bong"
        assert result.skip_retrieval is False

    def test_routing_decision(self):
        """RoutingDecision 테스트."""
        decision = RoutingDecision(
            selected_sources=["notebooklm", "qdrant"],
            selected_tools=["4D"],
            dimension=Dimension.MOMENT,
            strategy="ensemble_rrf",
            pattern=OrchestrationPattern.DIRECT,
        )

        assert "notebooklm" in decision.selected_sources
        assert "4D" in decision.selected_tools
        assert decision.dimension == Dimension.MOMENT


class TestPydanticModels:
    """Pydantic 모델 테스트."""

    def test_unified_query_request(self):
        """UnifiedQueryRequest 검증."""
        request = UnifiedQueryRequest(
            query="봉준호 롱테이크 분석",
            user_id="user_123",
            dimension="4D",
            auteur_key="bong",
        )

        assert request.query == "봉준호 롱테이크 분석"
        assert request.user_id == "user_123"
        assert request.dimension == "4D"
        assert request.auteur_key == "bong"
        assert request.skip_cache is False

    def test_unified_query_request_min_query_length(self):
        """쿼리 최소 길이 검증."""
        with pytest.raises(ValueError):
            UnifiedQueryRequest(query="")

    def test_unified_query_response(self):
        """UnifiedQueryResponse 검증."""
        response = UnifiedQueryResponse(
            response="봉준호 감독의 롱테이크는...",
            query_type="domain_specific",
            intent="analyze",
            confidence=0.85,
            evidence_refs=["db:notebooklm:doc_1"],
            sources_used=["notebooklm", "qdrant"],
        )

        assert "롱테이크" in response.response
        assert response.query_type == "domain_specific"
        assert len(response.evidence_refs) == 1


class TestMappings:
    """매핑 테이블 테스트."""

    def test_query_type_strategy_map(self):
        """QueryType → Strategy 매핑 테스트."""
        assert QUERY_TYPE_STRATEGY_MAP[QueryType.SIMPLE_FACTUAL] == "direct_llm"
        assert QUERY_TYPE_STRATEGY_MAP[QueryType.DOMAIN_SPECIFIC] == "ensemble_rrf"
        assert QUERY_TYPE_STRATEGY_MAP[QueryType.MULTI_HOP] == "full_pipeline"

    def test_skip_retrieval_types(self):
        """Skip Retrieval 타입 테스트."""
        assert QueryType.SIMPLE_FACTUAL in SKIP_RETRIEVAL_TYPES
        assert QueryType.CREATIVE in SKIP_RETRIEVAL_TYPES
        assert QueryType.DOMAIN_SPECIFIC not in SKIP_RETRIEVAL_TYPES

    def test_intent_pattern_map(self):
        """Intent → Pattern 매핑 테스트."""
        assert INTENT_PATTERN_MAP[Intent.GENERATE] == OrchestrationPattern.DIRECT
        assert INTENT_PATTERN_MAP[Intent.WORKFLOW] == OrchestrationPattern.CONDITIONAL
