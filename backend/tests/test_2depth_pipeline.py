"""Podcast Service Tests.

Tests the Podcast API functionality.

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

class TestPodcastService:
    """Podcast 서비스 단위 테스트."""

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
            custom_focus="강주노 감독 스타일에 집중"
        )
        assert "강주노" in prompt


# ============================================================================
# Live API Tests (Requires GCP auth)
# ============================================================================

@pytest.mark.live
class TestLivePodcast:
    """Live Podcast API 테스트 (GCP 인증 필요)."""

    @pytest.mark.asyncio
    async def test_live_podcast_generation(self):
        """Live 팟캐스트 생성 테스트 (async start only)."""
        from app.rag import get_podcast_service, PodcastFormat, PodcastLength

        service = get_podcast_service()
        result = await service.generate_podcast(
            sources=["테스트 콘텐츠입니다. 강주노 감독의 영화적 특징을 분석합니다."],
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
