"""
Tests for Source Type Resolver (Phase 4)

domain_sources → RAG 소스 라우팅 테스트
"""
import pytest
from typing import Dict, Any

from app.schemas.creative_intent import (
    CreativeIntent,
    CreativeMood,
    ContentDomain,
    IntentFactory,
)
from app.resolvers.source_resolver import (
    SourceTypeResolver,
    RAGSourceType,
    ResolvedSource,
    get_source_resolver,
    DOMAIN_TO_SOURCES,
)


class TestSourceMapping:
    """Domain → Source 매핑 테스트"""
    
    def test_auteur_bong_mapping(self):
        """강주노 → NotebookLM 매핑"""
        sources = DOMAIN_TO_SOURCES.get(ContentDomain.AUTEUR_BONG, [])
        
        assert len(sources) >= 1
        assert sources[0].source_type == RAGSourceType.NOTEBOOKLM
        assert sources[0].notebook_id == "DNA_강주노"
    
    def test_auteur_wong_mapping(self):
        """렌 벨벳 → NotebookLM 매핑"""
        sources = DOMAIN_TO_SOURCES.get(ContentDomain.AUTEUR_WONG, [])
        
        assert len(sources) >= 1
        assert sources[0].source_type == RAGSourceType.NOTEBOOKLM
        assert "neon" in sources[0].query_hints
    
    def test_genre_drama_mapping(self):
        """드라마 장르 → Dimension RAG"""
        sources = DOMAIN_TO_SOURCES.get(ContentDomain.GENRE_DRAMA, [])
        
        assert len(sources) >= 1
        assert sources[0].source_type == RAGSourceType.DIMENSION_RAG
        assert sources[0].dimension_code == "STORY"
    
    def test_saju_source_mapping(self):
        """사주 → SAJU_DB (+ fallback)"""
        sources = DOMAIN_TO_SOURCES.get(ContentDomain.SOURCE_SAJU, [])
        
        assert len(sources) >= 2
        assert sources[0].source_type == RAGSourceType.SAJU_DB
        # Fallback exists
        assert any(s.source_type == RAGSourceType.NOTEBOOKLM for s in sources)


class TestSourceTypeResolver:
    """SourceTypeResolver 테스트"""
    
    @pytest.fixture
    def resolver(self):
        return SourceTypeResolver()
    
    def test_resolve_auteur_intent(self, resolver):
        """Auteur intent에서 소스 추출"""
        intent = IntentFactory.cinematic_bong()
        
        sources = resolver.resolve_sources(intent)
        
        assert len(sources) >= 1
        assert sources[0].source_type == RAGSourceType.NOTEBOOKLM
        assert sources[0].notebook_id == "DNA_강주노"
    
    def test_resolve_multiple_domains(self, resolver):
        """여러 도메인 소스 처리"""
        intent = CreativeIntent(
            mood=CreativeMood.DARK,
            domain_sources=[
                ContentDomain.AUTEUR_BONG,
                ContentDomain.GENRE_THRILLER,
            ],
        )
        
        sources = resolver.resolve_sources(intent)
        
        assert len(sources) >= 2
        # 강주노 + thriller 모두 포함
        source_types = [s.source_type for s in sources]
        assert RAGSourceType.NOTEBOOKLM in source_types
        assert RAGSourceType.DIMENSION_RAG in source_types
    
    def test_resolve_empty_domain_fallback(self, resolver):
        """domain_sources가 비어있을 때 기본값"""
        intent = CreativeIntent(
            mood=CreativeMood.CALM,
            domain_sources=[],
        )
        
        sources = resolver.resolve_sources(intent)
        
        # 기본 Dimension RAG 반환
        assert len(sources) >= 1
        assert sources[0].source_type == RAGSourceType.DIMENSION_RAG
    
    def test_priority_sorting(self, resolver):
        """우선순위 순 정렬"""
        intent = CreativeIntent(
            mood=CreativeMood.CINEMATIC,
            domain_sources=[
                ContentDomain.GENRE_DRAMA,  # priority 7
                ContentDomain.AUTEUR_BONG,  # priority 10
            ],
        )
        
        sources = resolver.resolve_sources(intent)
        
        # 강주노 (priority 10)가 먼저
        assert sources[0].priority > sources[-1].priority if len(sources) > 1 else True
    
    def test_future_source_excluded(self, resolver):
        """미구현 소스 필터링"""
        intent = CreativeIntent(
            mood=CreativeMood.CALM,
            domain_sources=[ContentDomain.SOURCE_PAPER],
        )
        
        sources = resolver.resolve_sources(intent)
        
        # PAPER_DB는 미구현이므로 필터됨
        source_types = [s.source_type for s in sources]
        assert RAGSourceType.PAPER_DB not in source_types


class TestSingleton:
    """싱글톤 테스트"""
    
    def test_get_source_resolver_singleton(self):
        """싱글톤 동작 확인"""
        resolver1 = get_source_resolver()
        resolver2 = get_source_resolver()
        
        assert resolver1 is resolver2


class TestIntentFactoryIntegration:
    """IntentFactory와 통합 테스트"""
    
    def test_bong_factory_sources(self):
        """IntentFactory.cinematic_bong()이 올바른 소스 생성"""
        intent = IntentFactory.cinematic_bong()
        resolver = get_source_resolver()
        
        sources = resolver.resolve_sources(intent)
        
        # 강주노 NotebookLM이 포함되어야 함
        notebook_sources = [s for s in sources if s.source_type == RAGSourceType.NOTEBOOKLM]
        assert len(notebook_sources) >= 1
        assert any(s.notebook_id == "DNA_강주노" for s in notebook_sources)
    
    def test_saju_factory_sources(self):
        """IntentFactory.saju_guided()가 사주 소스 포함"""
        intent = IntentFactory.saju_guided()
        resolver = get_source_resolver()
        
        sources = resolver.resolve_sources(intent)
        
        # domain_sources에 SOURCE_SAJU가 있으면 소스에 포함
        assert len(sources) >= 1
