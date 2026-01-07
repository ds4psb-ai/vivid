"""2-Depth Cascaded RAG Pipeline E2E Tests.

Tests the complete pipeline:
- Depth 1: Vertex AI RAG Engine (core knowledge extraction)
- Depth 2: Discovery Engine Podcast API (audio generation)

Run with:
    pytest tests/test_2depth_pipeline.py -v

For live API tests (requires GCP auth):
    pytest tests/test_2depth_pipeline.py -v -m live
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ============================================================================
# Unit Tests (No API calls)
# ============================================================================

class TestCascadedQuery:
    """Cascaded Query 단위 테스트."""

    def test_cascaded_query_import(self):
        """cascaded_query 함수 import 확인."""
        from app.rag import cascaded_query
        assert callable(cascaded_query)

    def test_create_deep_podcast_import(self):
        """create_deep_podcast 함수 import 확인."""
        from app.rag import create_deep_podcast
        assert callable(create_deep_podcast)

    def test_podcast_service_imports(self):
        """Podcast 서비스 imports 확인."""
        from app.rag import (
            PodcastService,
            PodcastConfig,
            PodcastFormat,
            PodcastLength,
            PodcastStatus,
            get_podcast_service,
        )
        assert PodcastFormat.DEEP_DIVE.value == "deep_dive"
        assert PodcastFormat.DEBATE.value == "debate"
        assert PodcastLength.SHORT.value == "SHORT"
        assert PodcastLength.STANDARD.value == "STANDARD"

    def test_podcast_format_mapping(self):
        """Podcast format 매핑 테스트."""
        from app.rag.podcast_service import PodcastFormat

        formats = {
            "deep_dive": PodcastFormat.DEEP_DIVE,
            "debate": PodcastFormat.DEBATE,
            "critique": PodcastFormat.CRITIQUE,
            "lecture": PodcastFormat.LECTURE,
            "brief": PodcastFormat.BRIEF,
        }

        for mode, expected in formats.items():
            assert expected.value == mode

    def test_podcast_config_defaults(self):
        """PodcastConfig 기본값 테스트."""
        from app.rag import PodcastConfig

        config = PodcastConfig()
        assert config.location == "global"
        assert config.default_language == "ko"

    def test_podcast_service_singleton(self):
        """Podcast 서비스 싱글톤 테스트."""
        from app.rag import get_podcast_service, reset_podcast_service

        reset_podcast_service()
        service1 = get_podcast_service()
        service2 = get_podcast_service()
        assert service1 is service2


class TestVertexRAGHardening:
    """Vertex RAG 하드닝 테스트."""

    def test_validation_functions_exist(self):
        """Validation 함수 존재 확인."""
        from app.rag.tier0_vertex_rag import (
            validate_query,
            validate_corpus_name,
            validate_document_paths,
        )
        assert callable(validate_query)
        assert callable(validate_corpus_name)
        assert callable(validate_document_paths)

    def test_validate_query_empty(self):
        """빈 쿼리 검증."""
        from app.rag.tier0_vertex_rag import validate_query

        with pytest.raises(ValueError, match="cannot be empty"):
            validate_query("")
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_query("   ")

    def test_validate_query_too_long(self):
        """쿼리 길이 초과 검증."""
        from app.rag.tier0_vertex_rag import validate_query, MAX_QUERY_LENGTH

        long_query = "a" * (MAX_QUERY_LENGTH + 1)
        with pytest.raises(ValueError, match="maximum length"):
            validate_query(long_query)

    def test_validate_query_null_bytes(self):
        """Null 바이트 검증."""
        from app.rag.tier0_vertex_rag import validate_query

        with pytest.raises(ValueError, match="null bytes"):
            validate_query("test\x00query")

    def test_validate_corpus_name_empty(self):
        """빈 코퍼스 이름 검증."""
        from app.rag.tier0_vertex_rag import validate_corpus_name

        with pytest.raises(ValueError, match="cannot be empty"):
            validate_corpus_name("")

    def test_validate_corpus_name_invalid_chars(self):
        """잘못된 코퍼스 이름 문자 검증."""
        from app.rag.tier0_vertex_rag import validate_corpus_name

        with pytest.raises(ValueError, match="invalid characters"):
            validate_corpus_name("corpus/name")
        with pytest.raises(ValueError, match="invalid characters"):
            validate_corpus_name("corpus name")

    def test_validate_document_paths_empty(self):
        """빈 경로 목록 검증."""
        from app.rag.tier0_vertex_rag import validate_document_paths

        with pytest.raises(ValueError, match="At least one"):
            validate_document_paths([])

    def test_validate_document_paths_traversal(self):
        """경로 순회 공격 검증."""
        from app.rag.tier0_vertex_rag import validate_document_paths

        with pytest.raises(ValueError, match="traversal"):
            validate_document_paths(["../../../etc/passwd"])

    def test_constants_defined(self):
        """상수 정의 확인."""
        from app.rag.tier0_vertex_rag import (
            VERTEX_INIT_TIMEOUT,
            CORPUS_CREATE_TIMEOUT,
            FILE_IMPORT_TIMEOUT,
            QUERY_TIMEOUT,
            MAX_RETRIES,
            MAX_QUERY_LENGTH,
            MAX_CORPUS_COUNT,
            MAX_TOP_K,
        )

        assert VERTEX_INIT_TIMEOUT > 0
        assert CORPUS_CREATE_TIMEOUT > 0
        assert FILE_IMPORT_TIMEOUT > 0
        assert QUERY_TIMEOUT > 0
        assert MAX_RETRIES >= 1
        assert MAX_QUERY_LENGTH > 0
        assert MAX_CORPUS_COUNT > 0
        assert MAX_TOP_K > 0


class TestPodcastServiceFocusPrompt:
    """Podcast focus prompt 테스트."""

    def test_focus_prompt_deep_dive(self):
        """Deep dive focus prompt."""
        from app.rag.podcast_service import PodcastService, PodcastFormat

        service = PodcastService()
        prompt = service._build_focus_prompt(PodcastFormat.DEEP_DIVE)
        assert "심층" in prompt or "분석" in prompt

    def test_focus_prompt_debate(self):
        """Debate focus prompt."""
        from app.rag.podcast_service import PodcastService, PodcastFormat

        service = PodcastService()
        prompt = service._build_focus_prompt(PodcastFormat.DEBATE)
        assert "토론" in prompt or "관점" in prompt

    def test_focus_prompt_custom(self):
        """Custom focus prompt."""
        from app.rag.podcast_service import PodcastService, PodcastFormat

        service = PodcastService()
        prompt = service._build_focus_prompt(
            PodcastFormat.DEEP_DIVE,
            custom_focus="봉준호 감독 스타일에 집중"
        )
        assert "봉준호" in prompt


# ============================================================================
# Integration Tests (Mock API calls)
# ============================================================================

class TestCascadedQueryMocked:
    """Mocked cascaded query 테스트."""

    @pytest.mark.asyncio
    async def test_cascaded_query_structure(self):
        """cascaded_query 반환 구조 테스트."""
        from app.rag.tier0_vertex_rag import cascaded_query, VertexRAGResult

        # Mock the query method
        mock_result = VertexRAGResult(
            answer="봉준호 감독의 시각적 특징은 deep focus와 tracking shot입니다.",
            confidence=0.85,
            sources=[],
            grounding_sources=[],
        )

        with patch("app.rag.tier0_vertex_rag.get_vertex_rag_service") as mock_service:
            mock_service.return_value.query = AsyncMock(return_value=mock_result)

            result = await cascaded_query("봉준호 감독의 시각적 특징")

            assert "depth1_results" in result
            assert "depth2_ready" in result
            assert "podcast_eligible" in result
            assert "query" in result

    @pytest.mark.asyncio
    async def test_create_deep_podcast_structure(self):
        """create_deep_podcast 반환 구조 테스트."""
        from app.rag.tier0_vertex_rag import create_deep_podcast, VertexRAGResult
        from app.rag.podcast_service import PodcastResult, PodcastStatus

        # Mock cascaded query
        mock_rag_result = VertexRAGResult(
            answer="봉준호 감독의 시각적 특징은...",
            confidence=0.85,
            sources=[],
        )

        mock_podcast_result = PodcastResult(
            operation_name="projects/test/locations/global/operations/123",
            status=PodcastStatus.PROCESSING,
            title="Test",
        )

        with patch("app.rag.tier0_vertex_rag.cascaded_query") as mock_cascaded:
            mock_cascaded.return_value = {
                "depth1_results": mock_rag_result,
                "depth1_documents": [{"content": "doc1"}, {"content": "doc2"}],
                "depth2_ready": True,
                "podcast_eligible": True,
            }

            with patch("app.rag.podcast_service.get_podcast_service") as mock_ps:
                mock_ps.return_value.generate_podcast = AsyncMock(
                    return_value=mock_podcast_result
                )

                result = await create_deep_podcast("거장 분석", mode="debate")

                assert "status" in result
                assert "operation_name" in result or "error" in result


# ============================================================================
# Live API Tests (Requires GCP auth)
# ============================================================================

@pytest.mark.live
class TestLiveVertexRAG:
    """Live Vertex AI RAG 테스트 (GCP 인증 필요)."""

    @pytest.mark.asyncio
    async def test_live_query(self):
        """Live RAG 쿼리 테스트."""
        from app.rag import get_vertex_rag_service

        service = get_vertex_rag_service()
        result = await service.query(
            query="봉준호 감독의 시각적 특징",
            use_grounding=False,
            top_k=5,
        )

        # Just check that it returns something
        assert result is not None
        assert hasattr(result, "answer")
        assert hasattr(result, "confidence")


@pytest.mark.live
class TestLivePodcast:
    """Live Podcast API 테스트 (GCP 인증 필요)."""

    @pytest.mark.asyncio
    async def test_live_podcast_generation(self):
        """Live 팟캐스트 생성 테스트 (async start only)."""
        from app.rag import get_podcast_service, PodcastFormat, PodcastLength

        service = get_podcast_service()
        result = await service.generate_podcast(
            sources=["테스트 콘텐츠입니다. 봉준호 감독의 영화적 특징을 분석합니다."],
            title="테스트 팟캐스트",
            format=PodcastFormat.BRIEF,
            length=PodcastLength.SHORT,
            language="ko",
        )

        # Should return operation name (even if API fails)
        assert result is not None
        assert hasattr(result, "status")


# ============================================================================
# Setup Script Tests
# ============================================================================

class TestSetupScript:
    """Setup 스크립트 테스트."""

    def test_script_exists(self):
        """스크립트 파일 존재 확인."""
        from pathlib import Path
        script_path = Path(__file__).parent.parent / "scripts" / "setup_rag_corpus.py"
        assert script_path.exists()

    def test_corpus_definitions(self):
        """Corpus 정의 확인."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

        from setup_rag_corpus import CORPUS_DEFINITIONS

        assert "auteur_dna" in CORPUS_DEFINITIONS
        assert "meta_invariants" in CORPUS_DEFINITIONS
        assert "meta_vdg" in CORPUS_DEFINITIONS
        assert "dim_1d_prompts" in CORPUS_DEFINITIONS

        for corpus_name, corpus_def in CORPUS_DEFINITIONS.items():
            assert "display_name" in corpus_def
            assert "description" in corpus_def
            assert "local_files" in corpus_def
            assert "gcs_prefix" in corpus_def
