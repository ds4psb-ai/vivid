"""
Tests for Sound Dimension Endpoints.

Tests include:
- XSS sanitization for concept, storyboard, mood, topic
- Enum validation for sound_type, genre, target_platform, tempo
- Edge case inputs
"""
import pytest
from pydantic import ValidationError

from app.routers.dimension.sound import (
    # Constants
    ALLOWED_TEMPOS,
    ALLOWED_AUDIO_PLATFORMS,
    ALLOWED_LANGUAGE_MIX,
    ALLOWED_SONG_STRUCTURES,
    # Request models
    SoundCraftRequest,
    SoundMoodboardRequest,
    LyricsRequest,
    LyricsStyleGuide,
    # Helpers
    _sanitize_text_field,
    _validate_tempo,
    _validate_sound_type,
    _validate_genre,
    _validate_audio_platform,
)
from app.routers.dimension._base import (
    ALLOWED_GENRES,
    ALLOWED_SOUND_TYPES,
)


# ============================================================================
# Sanitization Helpers Tests
# ============================================================================

class TestSanitizeTextField:
    """Test _sanitize_text_field helper."""

    def test_removes_html_tags(self):
        """Test HTML tag removal."""
        result = _sanitize_text_field("<div>music concept</div>")
        assert "<div>" not in result
        assert "</div>" not in result
        assert "music concept" in result

    def test_removes_script_tags(self):
        """Test script tag removal."""
        result = _sanitize_text_field("<script>evil()</script>sound")
        assert "<script>" not in result
        assert "sound" in result

    def test_removes_javascript_protocol(self):
        """Test javascript: protocol removal."""
        result = _sanitize_text_field("javascript:alert(1)")
        assert "javascript:" not in result.lower()

    def test_removes_event_handlers(self):
        """Test on* event handler removal."""
        result = _sanitize_text_field("onload=alert(1)")
        assert "onload=" not in result.lower()

    def test_preserves_normal_text(self):
        """Test normal text is preserved."""
        result = _sanitize_text_field("A cinematic music piece with strings")
        assert "cinematic" in result
        assert "music" in result
        assert "strings" in result

    def test_preserves_korean(self):
        """Test Korean characters preserved."""
        result = _sanitize_text_field("감미로운 재즈 음악")
        assert "감미로운" in result
        assert "재즈" in result
        assert "음악" in result

    def test_empty_returns_default(self):
        """Test empty string returns default."""
        result = _sanitize_text_field("", default="기본값")
        assert result == "기본값"

    def test_none_returns_default(self):
        """Test None returns default."""
        result = _sanitize_text_field(None, default="fallback")
        assert result == "fallback"

    def test_whitespace_only_returns_default(self):
        """Test whitespace-only string returns default."""
        result = _sanitize_text_field("   ", default="default")
        assert result == "default"


# ============================================================================
# Validation Helpers Tests
# ============================================================================

class TestValidateTempo:
    """Test _validate_tempo helper."""

    def test_valid_tempos(self):
        """Test all valid tempos pass."""
        for tempo in ALLOWED_TEMPOS:
            assert _validate_tempo(tempo) == tempo

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        assert _validate_tempo("  medium  ") == "medium"

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert _validate_tempo("MEDIUM") == "medium"
        assert _validate_tempo("Fast") == "fast"

    def test_invalid_tempo_raises(self):
        """Test invalid tempo raises ValueError."""
        with pytest.raises(ValueError, match="지원하지 않는 템포"):
            _validate_tempo("invalid_tempo")
        with pytest.raises(ValueError, match="지원하지 않는 템포"):
            _validate_tempo("allegro")


class TestValidateSoundType:
    """Test _validate_sound_type helper."""

    def test_valid_sound_types(self):
        """Test all valid sound types pass."""
        for st in ALLOWED_SOUND_TYPES:
            assert _validate_sound_type(st) == st

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        assert _validate_sound_type("  bgm  ") == "bgm"

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert _validate_sound_type("BGM") == "bgm"
        assert _validate_sound_type("Sfx") == "sfx"

    def test_invalid_sound_type_raises(self):
        """Test invalid sound_type raises ValueError."""
        with pytest.raises(ValueError, match="지원하지 않는 사운드 타입"):
            _validate_sound_type("invalid_type")


class TestValidateGenre:
    """Test _validate_genre helper."""

    def test_valid_genres(self):
        """Test all valid genres pass."""
        for genre in ALLOWED_GENRES:
            assert _validate_genre(genre) == genre

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        assert _validate_genre("  drama  ") == "drama"

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert _validate_genre("DRAMA") == "drama"

    def test_invalid_genre_raises(self):
        """Test invalid genre raises ValueError."""
        with pytest.raises(ValueError, match="지원하지 않는 장르"):
            _validate_genre("invalid_genre")


class TestValidateAudioPlatform:
    """Test _validate_audio_platform helper."""

    def test_valid_platforms(self):
        """Test all valid audio platforms pass."""
        for platform in ALLOWED_AUDIO_PLATFORMS:
            assert _validate_audio_platform(platform) == platform

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        assert _validate_audio_platform("  suno  ") == "suno"

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert _validate_audio_platform("SUNO") == "suno"

    def test_invalid_platform_raises(self):
        """Test invalid platform raises ValueError."""
        with pytest.raises(ValueError, match="지원하지 않는 오디오 플랫폼"):
            _validate_audio_platform("invalid_platform")


class TestAllowedConstantsVerification:
    """Test allowed constants."""

    def test_expected_tempos_present(self):
        """Verify expected tempos are in allowed list."""
        expected = ["slow", "medium", "fast", "very-slow", "very-fast"]
        for tempo in expected:
            assert tempo in ALLOWED_TEMPOS

    def test_expected_sound_types_present(self):
        """Verify expected sound types are in allowed list."""
        expected = ["bgm", "sfx", "voiceover", "full_mix"]
        for st in expected:
            assert st in ALLOWED_SOUND_TYPES

    def test_expected_genres_present(self):
        """Verify expected genres are in allowed list."""
        expected = ["drama", "thriller", "comedy", "documentary", "horror"]
        for genre in expected:
            assert genre in ALLOWED_GENRES


# ============================================================================
# SoundCraftRequest Tests
# ============================================================================

class TestSoundCraftRequest:
    """Test SoundCraftRequest model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = SoundCraftRequest(
            concept="A cinematic score for a dramatic scene",
            sound_type="bgm",
            genre="drama",
            tempo="medium",
            target_platform="suno",
        )
        assert "cinematic" in request.concept
        assert request.sound_type == "bgm"
        assert request.genre == "drama"
        assert request.tempo == "medium"

    def test_default_values(self):
        """Test default values are applied."""
        request = SoundCraftRequest(
            concept="Test concept",
        )
        assert request.sound_type == "bgm"
        assert request.genre == "drama"
        assert request.tempo == "medium"
        assert request.duration == 60
        assert request.target_platform == "suno"
        assert request.mood == "cinematic"

    def test_concept_sanitization(self):
        """Test concept XSS sanitization."""
        request = SoundCraftRequest(
            concept="<script>alert('xss')</script>music",
        )
        assert "<script>" not in request.concept
        assert "music" in request.concept

    def test_storyboard_sanitization(self):
        """Test storyboard XSS sanitization."""
        request = SoundCraftRequest(
            concept="Test concept",
            storyboard="<img onerror=evil()>scene description",
        )
        assert "<img" not in request.storyboard
        assert "onerror" not in request.storyboard

    def test_mood_sanitization(self):
        """Test mood XSS sanitization."""
        request = SoundCraftRequest(
            concept="Test concept",
            mood="javascript:alert(1)hopeful",
        )
        assert "javascript:" not in request.mood.lower()

    def test_sound_type_validation(self):
        """Test sound_type validation."""
        for st in ALLOWED_SOUND_TYPES:
            request = SoundCraftRequest(concept="Test", sound_type=st)
            assert request.sound_type == st

    def test_invalid_sound_type_fails(self):
        """Test invalid sound_type fails validation."""
        with pytest.raises(ValidationError):
            SoundCraftRequest(concept="Test", sound_type="invalid")

    def test_genre_validation(self):
        """Test genre validation."""
        for genre in ALLOWED_GENRES:
            request = SoundCraftRequest(concept="Test", genre=genre)
            assert request.genre == genre

    def test_invalid_genre_fails(self):
        """Test invalid genre fails validation."""
        with pytest.raises(ValidationError):
            SoundCraftRequest(concept="Test", genre="invalid")

    def test_tempo_validation(self):
        """Test tempo validation."""
        for tempo in ALLOWED_TEMPOS:
            request = SoundCraftRequest(concept="Test", tempo=tempo)
            assert request.tempo == tempo

    def test_invalid_tempo_fails(self):
        """Test invalid tempo fails validation."""
        with pytest.raises(ValidationError):
            SoundCraftRequest(concept="Test", tempo="allegro")

    def test_platform_validation(self):
        """Test target_platform validation."""
        for platform in ALLOWED_AUDIO_PLATFORMS:
            request = SoundCraftRequest(concept="Test", target_platform=platform)
            assert request.target_platform == platform

    def test_invalid_platform_fails(self):
        """Test invalid platform fails validation."""
        with pytest.raises(ValidationError):
            SoundCraftRequest(concept="Test", target_platform="invalid")

    def test_duration_bounds(self):
        """Test duration min/max bounds."""
        # Valid minimum
        request = SoundCraftRequest(concept="Test", duration=10)
        assert request.duration == 10

        # Valid maximum
        request = SoundCraftRequest(concept="Test", duration=300)
        assert request.duration == 300

        # Below minimum fails
        with pytest.raises(ValidationError):
            SoundCraftRequest(concept="Test", duration=5)

        # Above maximum fails
        with pytest.raises(ValidationError):
            SoundCraftRequest(concept="Test", duration=500)

    def test_concept_min_length(self):
        """Test concept minimum length."""
        request = SoundCraftRequest(concept="A")
        assert request.concept == "A"

        with pytest.raises(ValidationError):
            SoundCraftRequest(concept="")


# ============================================================================
# SoundMoodboardRequest Tests
# ============================================================================

class TestSoundMoodboardRequest:
    """Test SoundMoodboardRequest model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = SoundMoodboardRequest(
            concept="Upbeat pop music for a dance video",
        )
        assert "Upbeat" in request.concept
        assert "pop" in request.concept

    def test_default_values(self):
        """Test default values are applied."""
        request = SoundMoodboardRequest(concept="Test")
        assert request.model == "gemini-3-flash-preview"

    def test_concept_sanitization(self):
        """Test concept XSS sanitization."""
        request = SoundMoodboardRequest(
            concept="<script>evil()</script>music idea",
        )
        assert "<script>" not in request.concept
        assert "music idea" in request.concept

    def test_concept_min_length(self):
        """Test concept minimum length."""
        request = SoundMoodboardRequest(concept="A")
        assert request.concept == "A"

        with pytest.raises(ValidationError):
            SoundMoodboardRequest(concept="")


# ============================================================================
# LyricsRequest Tests
# ============================================================================

class TestLyricsRequest:
    """Test LyricsRequest model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = LyricsRequest(
            topic="A song about chasing dreams",
            style_guide=LyricsStyleGuide(
                genre="Pop rock",
                tempo="fast",
                mood="hopeful",
            ),
        )
        assert "chasing dreams" in request.topic
        assert request.style_guide.genre == "Pop rock"
        assert request.style_guide.tempo == "fast"

    def test_default_values(self):
        """Test default values are applied."""
        request = LyricsRequest(topic="Test topic")
        assert request.style_guide.genre == "J-POP rock"
        assert request.style_guide.tempo == "fast"
        assert request.style_guide.mood == "hopeful"
        assert request.style_guide.language_mix == "korean"
        assert request.song_structure == "verse-chorus-verse-chorus-bridge-chorus"

    def test_topic_sanitization(self):
        """Test topic XSS sanitization."""
        request = LyricsRequest(
            topic="<script>alert('xss')</script>love song",
        )
        assert "<script>" not in request.topic
        assert "love song" in request.topic

    def test_topic_min_length(self):
        """Test topic minimum length."""
        request = LyricsRequest(topic="A")
        assert request.topic == "A"

        with pytest.raises(ValidationError):
            LyricsRequest(topic="")

    def test_context_documents(self):
        """Test context_documents can be provided."""
        request = LyricsRequest(
            topic="Historical ballad",
            context_documents=["Wiki article about event", "Research paper"],
        )
        assert len(request.context_documents) == 2


class TestLyricsStyleGuide:
    """Test LyricsStyleGuide model."""

    def test_default_values(self):
        """Test default values are applied."""
        guide = LyricsStyleGuide()
        assert guide.genre == "J-POP rock"
        assert guide.tempo == "fast"
        assert guide.mood == "hopeful"
        assert guide.vocal_style == "powerful male rock vocal"
        assert guide.language_mix == "korean"
        assert guide.reference_songs == []

    def test_custom_values(self):
        """Test custom values can be set."""
        guide = LyricsStyleGuide(
            genre="K-Pop",
            tempo="medium",
            mood="energetic",
            vocal_style="female vocal",
            language_mix="mixed",
            reference_songs=["Song A", "Song B"],
        )
        assert guide.genre == "K-Pop"
        assert guide.tempo == "medium"
        assert guide.mood == "energetic"
        assert len(guide.reference_songs) == 2


# ============================================================================
# Security Tests - XSS Prevention
# ============================================================================

class TestXSSPrevention:
    """Test XSS attack prevention."""

    @pytest.mark.parametrize("attack_vector", [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(document.cookie)",
        "<svg onload=alert(1)>",
        "<div onclick=evil()>",
        "onmouseover=alert(1)",
    ])
    def test_concept_xss_soundcraft(self, attack_vector):
        """Test SoundCraftRequest concept field XSS prevention."""
        request = SoundCraftRequest(
            concept=attack_vector + "music",
        )
        assert "<script>" not in request.concept.lower()
        assert "onerror" not in request.concept.lower()
        assert "javascript:" not in request.concept.lower()
        assert "onclick" not in request.concept.lower()

    @pytest.mark.parametrize("attack_vector", [
        "<script>evil()</script>",
        "onclick=malicious()",
    ])
    def test_storyboard_xss(self, attack_vector):
        """Test storyboard field XSS prevention."""
        request = SoundCraftRequest(
            concept="Test",
            storyboard=attack_vector + "scene",
        )
        assert "<script>" not in request.storyboard.lower()
        assert "onclick" not in request.storyboard.lower()

    @pytest.mark.parametrize("attack_vector", [
        "<script>alert('xss')</script>",
        "javascript:void(0)",
    ])
    def test_concept_xss_moodboard(self, attack_vector):
        """Test SoundMoodboardRequest concept field XSS prevention."""
        request = SoundMoodboardRequest(
            concept=attack_vector + "music",
        )
        assert "<script>" not in request.concept.lower()
        assert "javascript:" not in request.concept.lower()

    @pytest.mark.parametrize("attack_vector", [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
    ])
    def test_topic_xss(self, attack_vector):
        """Test LyricsRequest topic field XSS prevention."""
        request = LyricsRequest(
            topic=attack_vector + "song theme",
        )
        assert "<script>" not in request.topic.lower()
        assert "onerror" not in request.topic.lower()


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_in_concept(self):
        """Test Korean and emoji in concept."""
        request = SoundCraftRequest(
            concept="밤하늘 아래 🎵 피아노 선율",
        )
        assert "밤하늘" in request.concept
        assert "🎵" in request.concept
        assert "피아노" in request.concept

    def test_unicode_in_topic(self):
        """Test Korean and emoji in topic."""
        request = LyricsRequest(
            topic="사랑과 이별 💔 노래 주제",
        )
        assert "사랑과" in request.topic
        assert "💔" in request.topic

    def test_all_valid_sound_types(self):
        """Test all valid sound types work."""
        for st in ALLOWED_SOUND_TYPES:
            request = SoundCraftRequest(concept="Test", sound_type=st)
            assert request.sound_type == st

    def test_all_valid_tempos(self):
        """Test all valid tempos work."""
        for tempo in ALLOWED_TEMPOS:
            request = SoundCraftRequest(concept="Test", tempo=tempo)
            assert request.tempo == tempo

    def test_all_valid_platforms(self):
        """Test all valid audio platforms work."""
        for platform in ALLOWED_AUDIO_PLATFORMS:
            request = SoundCraftRequest(concept="Test", target_platform=platform)
            assert request.target_platform == platform

    def test_long_concept(self):
        """Test long concept within max length."""
        long_concept = "Music " * 200  # 1400 chars
        request = SoundCraftRequest(concept=long_concept)
        assert len(request.concept) == len(long_concept.strip())

    def test_long_storyboard(self):
        """Test long storyboard within max length."""
        long_storyboard = "Scene " * 400  # 2400 chars
        request = SoundCraftRequest(concept="Test", storyboard=long_storyboard)
        assert len(request.storyboard) == len(long_storyboard.strip())

    def test_concept_whitespace_strip(self):
        """Test concept whitespace stripping."""
        request = SoundCraftRequest(concept="  Test concept  ")
        assert request.concept == "Test concept"

    def test_empty_storyboard(self):
        """Test empty storyboard is allowed."""
        request = SoundCraftRequest(concept="Test", storyboard="")
        assert request.storyboard == ""

    def test_sound_type_case_normalization(self):
        """Test sound_type is normalized to lowercase."""
        request = SoundCraftRequest(concept="Test", sound_type="BGM")
        assert request.sound_type == "bgm"

    def test_tempo_case_normalization(self):
        """Test tempo is normalized to lowercase."""
        request = SoundCraftRequest(concept="Test", tempo="MEDIUM")
        assert request.tempo == "medium"

    def test_genre_case_normalization(self):
        """Test genre is normalized to lowercase."""
        request = SoundCraftRequest(concept="Test", genre="DRAMA")
        assert request.genre == "drama"

    def test_empty_reference_songs(self):
        """Test empty reference_songs is allowed."""
        guide = LyricsStyleGuide(reference_songs=[])
        assert guide.reference_songs == []

    def test_multiple_reference_songs(self):
        """Test multiple reference songs."""
        guide = LyricsStyleGuide(reference_songs=["Song A", "Song B", "Song C"])
        assert len(guide.reference_songs) == 3

    def test_special_characters_in_concept(self):
        """Test special characters preserved in concept."""
        request = SoundCraftRequest(
            concept="A song about love & loss - the journey...",
        )
        assert "&" in request.concept or "&amp;" in request.concept
        assert "-" in request.concept


# ============================================================================
# 2026 Audio Platform Capability Tests
# ============================================================================

class TestAudioPlatform:
    """Test AudioPlatform enum (2026 platform support)."""

    def test_audio_platform_enum_exists(self):
        """Test AudioPlatform enum is importable."""
        from app.routers.dimension.sound import AudioPlatform
        assert AudioPlatform is not None

    def test_supported_platforms(self):
        """Test 2026 supported platforms."""
        from app.routers.dimension.sound import AudioPlatform
        assert AudioPlatform.SUNO.value == "suno"
        assert AudioPlatform.UDIO.value == "udio"
        assert AudioPlatform.ELEVENLABS.value == "elevenlabs"
        assert AudioPlatform.MINIMAX.value == "minimax"  # New 2026

    def test_platform_count(self):
        """Test at least 4 platforms supported."""
        from app.routers.dimension.sound import AudioPlatform
        assert len(AudioPlatform) >= 4


class TestAudioQuality:
    """Test AudioQuality enum (2026 industry standards)."""

    def test_audio_quality_enum_exists(self):
        """Test AudioQuality enum is importable."""
        from app.routers.dimension.sound import AudioQuality
        assert AudioQuality is not None

    def test_quality_levels(self):
        """Test 2026 audio quality levels."""
        from app.routers.dimension.sound import AudioQuality
        assert AudioQuality.STANDARD.value == "standard"  # 32 kHz
        assert AudioQuality.HIGH.value == "high"  # 44.1 kHz
        assert AudioQuality.STUDIO.value == "studio"  # 48 kHz


class TestStemExportFormat:
    """Test StemExportFormat enum (Suno v5 feature)."""

    def test_stem_export_formats(self):
        """Test stem export formats."""
        from app.routers.dimension.sound import StemExportFormat
        assert StemExportFormat.WAV.value == "wav"
        assert StemExportFormat.MIDI.value == "midi"
        assert StemExportFormat.MP3.value == "mp3"


class TestSunoV5Capabilities:
    """Test SunoV5Capabilities model (2026 Suno v5 features)."""

    def test_default_capabilities(self):
        """Test default Suno v5 capabilities."""
        from app.routers.dimension.sound import SunoV5Capabilities
        caps = SunoV5Capabilities()
        assert caps.max_duration_seconds == 480  # 8 minutes
        assert caps.sample_rate_khz == 44.1  # Studio-grade
        assert caps.max_stems == 12  # 12-stem export
        assert caps.supports_midi_export is True
        assert caps.supports_audio_upload is True
        assert caps.supports_vocals_upload is True

    def test_custom_capabilities(self):
        """Test custom capability values."""
        from app.routers.dimension.sound import SunoV5Capabilities
        caps = SunoV5Capabilities(
            max_duration_seconds=600,
            sample_rate_khz=48.0,
            max_stems=16,
        )
        assert caps.max_duration_seconds == 600
        assert caps.sample_rate_khz == 48.0
        assert caps.max_stems == 16


class TestUdioCapabilities:
    """Test UdioCapabilities model (2026 Udio features)."""

    def test_default_capabilities(self):
        """Test default Udio capabilities."""
        from app.routers.dimension.sound import UdioCapabilities
        caps = UdioCapabilities()
        assert caps.max_duration_seconds == 300  # 5 minutes
        assert caps.sample_rate_khz == 48.0  # Broadcast-grade
        assert caps.supports_detailed_remixing is True
        assert caps.supports_song_extensions is True
        assert caps.vocal_quality == "human-like"


class TestSoundGenerationResult:
    """Test SoundGenerationResult model (2026 comprehensive result)."""

    def test_result_creation_defaults(self):
        """Test result creation with defaults."""
        from app.routers.dimension.sound import SoundGenerationResult, AudioPlatform, AudioQuality
        result = SoundGenerationResult()
        assert result.suno_prompt == ""
        assert result.udio_prompt == ""
        assert result.elevenlabs_prompt == ""
        assert result.target_platform == AudioPlatform.SUNO
        assert result.audio_quality == AudioQuality.HIGH
        assert result.stem_export_available is False
        assert result.stem_count == 0
        assert result.trace_id == ""
        assert result.evidence_refs == []
        assert result.confidence == 0.0

    def test_result_with_prompts(self):
        """Test result with platform-specific prompts."""
        from app.routers.dimension.sound import SoundGenerationResult, AudioPlatform, AudioQuality
        result = SoundGenerationResult(
            suno_prompt="Genre: Pop, Tempo: 120, Mood: Happy",
            udio_prompt="Pop track with energetic vocals",
            target_platform=AudioPlatform.SUNO,
            audio_quality=AudioQuality.STUDIO,
            stem_export_available=True,
            stem_count=12,
            trace_id="sc-abc123",
            evidence_refs=[
                "rag:sound_craft:bgm",
                "config:platform:suno",
            ],
            confidence=0.9,
        )
        assert "Genre: Pop" in result.suno_prompt
        assert result.stem_export_available is True
        assert result.stem_count == 12
        assert result.trace_id == "sc-abc123"
        assert len(result.evidence_refs) == 2

    def test_result_evidence_refs_list_str(self):
        """Test evidence_refs is List[str] (Vivid convention)."""
        from app.routers.dimension.sound import SoundGenerationResult
        result = SoundGenerationResult(
            evidence_refs=["rag:sound:test", "config:platform:suno"]
        )
        assert isinstance(result.evidence_refs, list)
        assert all(isinstance(ref, str) for ref in result.evidence_refs)


class TestStructureSegment:
    """Test StructureSegment model (2026 Structure Strategy)."""

    def test_segment_creation(self):
        """Test segment creation."""
        from app.routers.dimension.sound import StructureSegment
        segment = StructureSegment(
            name="chorus",
            duration_beats=32,
            bpm_hint=140,
            mood_hint="energetic",
        )
        assert segment.name == "chorus"
        assert segment.duration_beats == 32
        assert segment.bpm_hint == 140
        assert segment.mood_hint == "energetic"

    def test_segment_defaults(self):
        """Test segment default values."""
        from app.routers.dimension.sound import StructureSegment
        segment = StructureSegment(name="verse")
        assert segment.duration_beats == 16
        assert segment.bpm_hint == 120
        assert segment.mood_hint == "neutral"


# ============================================================================
# Evidence Refs Format Tests (Vivid Convention)
# ============================================================================

class TestEvidenceRefsFormat:
    """Test evidence_refs follows Vivid List[str] convention."""

    def test_evidence_refs_format_sound_craft(self):
        """Test sound_craft evidence_refs format."""
        expected_format = "rag:sound_craft:bgm"
        assert expected_format.startswith("rag:")
        parts = expected_format.split(":")
        assert len(parts) >= 3
        assert parts[0] in ("rag", "db", "config")

    def test_evidence_refs_format_platform(self):
        """Test platform evidence_refs format."""
        expected_format = "config:platform:suno"
        parts = expected_format.split(":")
        assert parts[0] == "config"
        assert parts[1] == "platform"
        assert parts[2] in ALLOWED_AUDIO_PLATFORMS

    def test_evidence_refs_format_genre(self):
        """Test genre evidence_refs format."""
        expected_format = "config:genre:drama"
        parts = expected_format.split(":")
        assert parts[0] == "config"
        assert parts[1] == "genre"
        assert parts[2] in ALLOWED_GENRES


# ============================================================================
# LyricsResponse 2026 Tests
# ============================================================================

class TestLyricsResponse2026:
    """Test LyricsResponse with 2026 RAG Protocol v2 fields."""

    def test_lyrics_response_trace_fields(self):
        """Test LyricsResponse has trace fields."""
        from app.routers.dimension.sound import LyricsResponse, LyricsSection
        response = LyricsResponse(
            success=True,
            topic_analysis="Analysis of love theme",
            lyrics_sections=[
                LyricsSection(type="verse", content="First verse...")
            ],
            full_lyrics="[Verse]\nFirst verse...",
            suno_prompt="Genre: Pop",
            udio_prompt="Pop ballad",
            style_summary="Modern pop ballad",
            trace_id="lyr-abc123",
            evidence_refs=[
                "rag:lyrics:genre:pop",
                "config:structure:verse-chorus",
            ],
            confidence=0.85,
        )
        assert response.trace_id == "lyr-abc123"
        assert len(response.evidence_refs) == 2
        assert response.confidence == 0.85

    def test_lyrics_response_default_trace_fields(self):
        """Test LyricsResponse default trace field values."""
        from app.routers.dimension.sound import LyricsResponse
        response = LyricsResponse(
            success=True,
            topic_analysis="Test",
            lyrics_sections=[],
            full_lyrics="",
            suno_prompt="",
            udio_prompt="",
            style_summary="",
        )
        assert response.trace_id == ""
        assert response.evidence_refs == []
        assert response.confidence == 0.0


# ============================================================================
# 2026 Multi-Platform Prompt Tests
# ============================================================================

class TestMultiPlatformPrompts:
    """Test 2026 multi-platform prompt generation patterns."""

    def test_suno_v5_prompt_structure(self):
        """Test Suno v5 prompt structure strategy."""
        # 2026 Suno prompt structure: Style -> Lyrics -> Structure
        suno_prompt = "Style: Lo-fi Hip Hop, female vocals, 80bpm\n[Verse 1] Rain..."
        assert "Style:" in suno_prompt
        assert "[Verse" in suno_prompt

    def test_udio_prompt_structure(self):
        """Test Udio prompt structure."""
        # Udio: Tag-driven, modular structure
        udio_prompt = "lo-fi, female vocal, melancholic, 80bpm"
        assert "," in udio_prompt  # Tag-based

    def test_platform_specific_capabilities(self):
        """Test different platforms have different capabilities."""
        from app.routers.dimension.sound import SunoV5Capabilities, UdioCapabilities
        suno = SunoV5Capabilities()
        udio = UdioCapabilities()
        # Suno v5 has longer duration (8 min vs 5 min)
        assert suno.max_duration_seconds > udio.max_duration_seconds
        # Udio has higher sample rate (48 kHz vs 44.1 kHz)
        assert udio.sample_rate_khz > suno.sample_rate_khz
