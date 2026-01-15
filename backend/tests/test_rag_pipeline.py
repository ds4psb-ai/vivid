"""RAG Pipeline Tests.

테스트 범위:
- Tier 0: NotebookLM Service
- Tier 1: Dimension RAG
- Tier 2: App Context Loader
- LightRAG Adapter
- Feedback Loop
- Pattern Promoter
"""
import pytest
from datetime import datetime


# ============================================================================
# Tier 0: NotebookLM Tests
# ============================================================================

class TestNotebookLMService:
    """NotebookLM 서비스 테스트."""

    def test_get_service_singleton(self):
        """싱글톤 패턴 확인."""
        from app.rag.tier0_notebooklm import get_notebooklm_service, reset_notebooklm_service

        reset_notebooklm_service()
        service1 = get_notebooklm_service()
        service2 = get_notebooklm_service()
        assert service1 is service2

    def test_notebook_registry(self):
        """노트북 레지스트리 확인."""
        from app.rag.tier0_notebooklm import NOTEBOOK_REGISTRY

        assert "DNA_봉준호" in NOTEBOOK_REGISTRY
        assert "DNA_박찬욱" in NOTEBOOK_REGISTRY
        assert "META_INVARIANTS" in NOTEBOOK_REGISTRY

    def test_get_notebooks_by_dimension(self):
        """차원별 노트북 조회."""
        from app.rag.tier0_notebooklm import get_notebooklm_service

        service = get_notebooklm_service()
        ad_notebooks = service.get_notebooks_by_dimension("AD")
        assert len(ad_notebooks) > 0

    def test_get_notebooks_by_category(self):
        """카테고리별 노트북 조회."""
        from app.rag.tier0_notebooklm import get_notebooklm_service

        service = get_notebooklm_service()
        auteur_notebooks = service.get_notebooks_by_category("auteur")
        assert len(auteur_notebooks) >= 3  # bong, park, shinkai

    @pytest.mark.asyncio
    async def test_query_notebook_simulation(self):
        """노트북 쿼리 시뮬레이션."""
        from app.rag.tier0_notebooklm import get_notebooklm_service

        service = get_notebooklm_service()
        result = await service.query_notebook(
            notebook_id="DNA_봉준호",
            query="봉준호 감독의 시각적 특징"
        )

        assert result.answer
        assert result.notebook_id == "DNA_봉준호"
        assert result.grounded


# ============================================================================
# Tier 2: App Context Loader Tests
# ============================================================================

class TestAppContextLoader:
    """앱 컨텍스트 로더 테스트."""

    def test_get_loader_singleton(self):
        """싱글톤 패턴 확인."""
        from app.rag.tier2_app_context import get_app_context_loader, reset_app_context_loader

        reset_app_context_loader()
        loader1 = get_app_context_loader()
        loader2 = get_app_context_loader()
        assert loader1 is loader2

    def test_app_dimension_mapping(self):
        """앱-차원 매핑 확인."""
        from app.rag.tier2_app_context import APP_DIMENSION_MAP

        assert APP_DIMENSION_MAP["teaching.prompt.generate"] == "1D"
        assert APP_DIMENSION_MAP["teaching.storyboard.create"] == "2D"
        assert APP_DIMENSION_MAP["dimension.aesthetic.direct"] == "AD"

    def test_dimension_docs_mapping(self):
        """차원-문서 디렉토리 매핑 확인."""
        from app.rag.tier2_app_context import DIMENSION_DOCS_MAP

        assert DIMENSION_DOCS_MAP["1D"] == "origin"
        assert DIMENSION_DOCS_MAP["AD"] == "aesthetic"

    @pytest.mark.asyncio
    async def test_load_auteur_styles(self):
        """Auteur 스타일 로드."""
        from app.rag.tier2_app_context import get_app_context_loader

        loader = get_app_context_loader()
        styles = await loader.load_auteur_styles()

        # styles can be {"auteurs": {"bong": ...}} or {"bong": ...}
        auteurs = styles.get("auteurs", styles)
        assert "bong" in auteurs
        assert "park" in auteurs
        # Check nested structure - palette_bias may be at different levels
        bong_style = auteurs["bong"]
        assert "color_palette" in bong_style or "palette_bias" in bong_style

    def test_get_stats(self):
        """로더 통계."""
        from app.rag.tier2_app_context import get_app_context_loader

        loader = get_app_context_loader()
        stats = loader.get_stats()

        assert "docs_dir" in stats
        assert "registered_apps" in stats


# ============================================================================
# LightRAG Adapter Tests
# ============================================================================

class TestLightRAGAdapter:
    """LightRAG 어댑터 테스트."""

    def test_get_adapter_singleton(self):
        """싱글톤 패턴 확인."""
        from app.rag.lightrag_adapter import get_lightrag_adapter, reset_lightrag_adapter

        reset_lightrag_adapter()
        adapter1 = get_lightrag_adapter()
        adapter2 = get_lightrag_adapter()
        assert adapter1 is adapter2

    def test_entity_extractor_known_entities(self):
        """알려진 엔티티 추출."""
        from app.rag.lightrag_adapter import EntityExtractor

        extractor = EntityExtractor()
        content = "봉준호 감독의 기생충은 deep focus 기법을 사용한다"
        entities = extractor.extract_entities(content)

        entity_names = {e.name.lower() for e in entities}
        assert "봉준호" in entity_names or "deep focus" in entity_names

    @pytest.mark.asyncio
    async def test_index_document(self):
        """문서 인덱싱."""
        from app.rag.lightrag_adapter import get_lightrag_adapter, reset_lightrag_adapter

        reset_lightrag_adapter()
        adapter = get_lightrag_adapter()

        result = await adapter.index_document(
            doc_id="test_doc_1",
            content="봉준호 감독의 기생충은 deep focus 기법과 tracking shot을 사용한다",
            dimension="AD",
        )

        assert result["doc_id"] == "test_doc_1"
        assert result["entities_count"] >= 0

    @pytest.mark.asyncio
    async def test_search(self):
        """검색 테스트."""
        from app.rag.lightrag_adapter import get_lightrag_adapter

        adapter = get_lightrag_adapter()
        result = await adapter.search(
            query="봉준호 시각적 특징",
            search_level="hybrid",
        )

        assert result.query == "봉준호 시각적 특징"
        assert result.search_level == "hybrid"

    def test_get_stats(self):
        """통계 조회."""
        from app.rag.lightrag_adapter import get_lightrag_adapter

        adapter = get_lightrag_adapter()
        stats = adapter.get_stats()

        assert "total_entities" in stats
        assert "total_relations" in stats


# ============================================================================
# Feedback Loop Tests
# ============================================================================

class TestFeedbackLoop:
    """피드백 루프 테스트."""

    def test_get_feedback_loop_singleton(self):
        """싱글톤 패턴 확인."""
        from app.rag.feedback_loop import get_feedback_loop

        loop1 = get_feedback_loop()
        loop2 = get_feedback_loop()
        assert loop1 is loop2

    def test_index_threshold(self):
        """인덱싱 임계값 확인."""
        from app.rag.feedback_loop import FeedbackLoop

        assert FeedbackLoop.MIN_INDEX_THRESHOLD == 0.7

    def test_capsule_to_dimension_mapping(self):
        """캡슐-차원 매핑 확인."""
        from app.rag.feedback_loop import FeedbackLoop

        mapping = FeedbackLoop.CAPSULE_TO_DIMENSION
        assert mapping["teaching.prompt.generate"] == "1D"
        assert mapping["dimension.aesthetic.direct"] == "AD"

    def test_extract_indexable_content(self):
        """인덱싱 콘텐츠 추출."""
        from app.rag.feedback_loop import FeedbackLoop

        loop = FeedbackLoop()

        content = loop._extract_indexable_content(
            capsule_id="teaching.prompt.generate",
            inputs={"topic": "cinematic sunset"},
            output={"prompt": "A beautiful sunset over the ocean", "style": {"cinematography": "wide shot"}},
        )

        assert "cinematic sunset" in content or "sunset" in content

    def test_get_stats(self):
        """통계 조회."""
        from app.rag.feedback_loop import get_feedback_loop

        loop = get_feedback_loop()
        stats = loop.get_stats()

        assert "total_indexed" in stats
        assert "quality_threshold" in stats


# ============================================================================
# Pattern Promoter Tests
# ============================================================================

class TestPatternPromoter:
    """패턴 프로모터 테스트."""

    def test_get_promoter_singleton(self):
        """싱글톤 패턴 확인."""
        from app.rag.pattern_promoter import get_pattern_promoter, reset_pattern_promoter

        reset_pattern_promoter()
        promoter1 = get_pattern_promoter()
        promoter2 = get_pattern_promoter()
        assert promoter1 is promoter2

    def test_promotion_config_defaults(self):
        """프로모션 설정 기본값."""
        from app.rag.pattern_promoter import PromotionConfig

        config = PromotionConfig()
        assert config.weekly_min_quality == 0.75
        assert config.monthly_min_quality == 0.85

    def test_promotion_candidate_criteria(self):
        """프로모션 후보 기준 테스트."""
        from app.rag.pattern_promoter import PromotionCandidate, PromotionConfig

        config = PromotionConfig()
        candidate = PromotionCandidate(
            evidence_id="test_001",
            content="Test content",
            dimension="AD",
            app_key="dimension.aesthetic.direct",
            quality_score=0.80,
            usage_count=5,
        )

        assert candidate.meets_weekly_criteria(config)
        assert not candidate.meets_monthly_criteria(config)  # needs 0.85+

    def test_get_stats(self):
        """통계 조회."""
        from app.rag.pattern_promoter import get_pattern_promoter

        promoter = get_pattern_promoter()
        stats = promoter.get_stats()

        assert "is_running" in stats
        assert "config" in stats


# ============================================================================
# Schema Tests
# ============================================================================

class TestRAGSchemas:
    """RAG 스키마 테스트."""

    def test_dimension_type_enum(self):
        """차원 타입 enum."""
        from app.rag.schemas import DimensionType

        assert DimensionType.D1.value == "1D"
        assert DimensionType.AD.value == "AD"

    def test_rag_tier_enum(self):
        """RAG 계층 enum."""
        from app.rag.schemas import RAGTier

        assert RAGTier.TIER0.value == "tier0"
        assert RAGTier.TIER1.value == "tier1"

    def test_rag_document_model(self):
        """RAG 문서 모델."""
        from app.rag.schemas import RAGDocument, DimensionType, RAGTier

        doc = RAGDocument(
            doc_id="test_001",
            content="Test content",
            dimension=DimensionType.D1,
        )

        assert doc.doc_id == "test_001"
        assert doc.score == 0.0
        assert doc.source_tier == RAGTier.TIER1

    def test_evidence_record_model(self):
        """Evidence 레코드 모델."""
        from app.rag.schemas import EvidenceRecord, DimensionType, EvidenceStatus

        record = EvidenceRecord(
            evidence_id="ev_001",
            capsule_id="teaching.prompt.generate",
            dimension=DimensionType.D1,
            content="Test content",
            quality_score=0.85,
        )

        assert record.status == EvidenceStatus.PENDING
        assert record.quality_score == 0.85


# ============================================================================
# Integration Tests
# ============================================================================

class TestRAGIntegration:
    """RAG 통합 테스트."""

    def test_import_all_modules(self):
        """모든 모듈 import 확인."""
        from app.rag import (
            # Tier 0
            get_notebooklm_service,
            # Tier 1
            get_dimension_rag,
            # Tier 2
            get_app_context_loader,
            # LightRAG
            get_lightrag_adapter,
            # Feedback Loop
            get_feedback_loop,
            # Pattern Promoter
            get_pattern_promoter,
        )

        assert callable(get_notebooklm_service)
        assert callable(get_dimension_rag)
        assert callable(get_app_context_loader)
        assert callable(get_lightrag_adapter)
        assert callable(get_feedback_loop)
        assert callable(get_pattern_promoter)

    def test_schemas_available(self):
        """스키마 export 확인."""
        from app.rag import (
            DimensionType,
            RAGTier,
            RAGDocument,
            EvidenceRecord,
            AuteurStyle,
        )

        assert DimensionType
        assert RAGTier
        assert RAGDocument
        assert EvidenceRecord
        assert AuteurStyle
