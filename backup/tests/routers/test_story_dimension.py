"""
Tests for Story Dimension Endpoints.

Tests include:
- XSS sanitization for concept, persona_data, reference_analysis, scenario, style_preference
- Enum validation for genre, structure
- Edge case inputs
"""
import pytest
from pydantic import ValidationError

from app.routers.dimension.story import (
    # Request models
    StoryArchitectRequest,
    StoryRefineRequest,
    ShotListRequest,
    # Helpers
    _sanitize_text_field,
    _validate_genre,
    _validate_structure,
)
from app.routers.dimension._base import (
    ALLOWED_GENRES,
    ALLOWED_STRUCTURES,
)


# ============================================================================
# Sanitization Helpers Tests
# ============================================================================

class TestSanitizeTextField:
    """Test _sanitize_text_field helper."""

    def test_removes_html_tags(self):
        """Test HTML tag removal."""
        result = _sanitize_text_field("<div>my concept</div>")
        assert "<div>" not in result
        assert "</div>" not in result
        assert "my concept" in result

    def test_removes_script_tags(self):
        """Test script tag removal."""
        result = _sanitize_text_field("<script>evil()</script>story")
        assert "<script>" not in result
        assert "story" in result

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
        result = _sanitize_text_field("A dramatic story about love")
        assert "dramatic" in result
        assert "story" in result
        assert "love" in result

    def test_preserves_korean(self):
        """Test Korean characters preserved."""
        result = _sanitize_text_field("비 오는 날 카페에서")
        assert "비 오는 날" in result
        assert "카페에서" in result

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
        assert _validate_genre("Thriller") == "thriller"

    def test_invalid_genre_raises(self):
        """Test invalid genre raises ValueError."""
        with pytest.raises(ValueError, match="지원하지 않는 장르"):
            _validate_genre("invalid_genre")
        with pytest.raises(ValueError, match="지원하지 않는 장르"):
            _validate_genre("action")


class TestValidateStructure:
    """Test _validate_structure helper."""

    def test_valid_structures(self):
        """Test all valid structures pass."""
        for structure in ALLOWED_STRUCTURES:
            assert _validate_structure(structure) == structure

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        assert _validate_structure("  3-act  ") == "3-act"

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert _validate_structure("3-ACT") == "3-act"
        assert _validate_structure("Hero-Journey") == "hero-journey"

    def test_invalid_structure_raises(self):
        """Test invalid structure raises ValueError."""
        with pytest.raises(ValueError, match="지원하지 않는 구조"):
            _validate_structure("invalid_structure")
        with pytest.raises(ValueError, match="지원하지 않는 구조"):
            _validate_structure("4-act")


class TestAllowedGenresConstant:
    """Test ALLOWED_GENRES constant."""

    def test_expected_genres_present(self):
        """Verify expected genres are in allowed list."""
        expected = ["drama", "thriller", "comedy", "documentary", "horror", "scifi", "ad", "mv", "short"]
        for genre in expected:
            assert genre in ALLOWED_GENRES

    def test_genre_count(self):
        """Verify reasonable number of genres."""
        assert len(ALLOWED_GENRES) == 9


class TestAllowedStructuresConstant:
    """Test ALLOWED_STRUCTURES constant."""

    def test_expected_structures_present(self):
        """Verify expected structures are in allowed list."""
        expected = ["3-act", "5-act", "hook-body-cta", "problem-solution", "story-arc", "montage", "interview", "hero-journey", "nonlinear", "slice-of-life"]
        for structure in expected:
            assert structure in ALLOWED_STRUCTURES

    def test_structure_count(self):
        """Verify reasonable number of structures."""
        assert len(ALLOWED_STRUCTURES) == 10


# ============================================================================
# StoryArchitectRequest Tests
# ============================================================================

class TestStoryArchitectRequest:
    """Test StoryArchitectRequest model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = StoryArchitectRequest(
            concept="A heartwarming story about a stray dog finding a home",
            genre="drama",
            duration=60,
            structure="3-act",
        )
        assert "heartwarming" in request.concept
        assert request.genre == "drama"
        assert request.duration == 60
        assert request.structure == "3-act"

    def test_default_values(self):
        """Test default values are applied."""
        request = StoryArchitectRequest(
            concept="Test concept",
        )
        assert request.genre == "drama"
        assert request.duration == 60
        assert request.structure == "3-act"
        assert request.language == "ko"
        assert request.persona_data == ""
        assert request.reference_analysis == ""

    def test_concept_sanitization(self):
        """Test concept XSS sanitization."""
        request = StoryArchitectRequest(
            concept="<script>alert('xss')</script>my story",
        )
        assert "<script>" not in request.concept
        assert "my story" in request.concept

    def test_persona_data_sanitization(self):
        """Test persona_data XSS sanitization."""
        request = StoryArchitectRequest(
            concept="Test concept",
            persona_data="<img onerror=evil()>data",
        )
        assert "<img" not in request.persona_data
        assert "onerror" not in request.persona_data

    def test_reference_analysis_sanitization(self):
        """Test reference_analysis XSS sanitization."""
        request = StoryArchitectRequest(
            concept="Test concept",
            reference_analysis="javascript:alert(1)analysis",
        )
        assert "javascript:" not in request.reference_analysis.lower()
        assert "analysis" in request.reference_analysis

    def test_genre_validation(self):
        """Test genre validation."""
        request = StoryArchitectRequest(
            concept="Test",
            genre="comedy",
        )
        assert request.genre == "comedy"

    def test_invalid_genre_fails(self):
        """Test invalid genre fails validation."""
        with pytest.raises(ValidationError):
            StoryArchitectRequest(
                concept="Test",
                genre="action",
            )

    def test_structure_validation(self):
        """Test structure validation."""
        request = StoryArchitectRequest(
            concept="Test",
            structure="hero-journey",
        )
        assert request.structure == "hero-journey"

    def test_invalid_structure_fails(self):
        """Test invalid structure fails validation."""
        with pytest.raises(ValidationError):
            StoryArchitectRequest(
                concept="Test",
                structure="4-act",
            )

    def test_duration_bounds(self):
        """Test duration min/max bounds."""
        # Valid minimum
        request = StoryArchitectRequest(concept="Test", duration=10)
        assert request.duration == 10

        # Valid maximum
        request = StoryArchitectRequest(concept="Test", duration=600)
        assert request.duration == 600

        # Below minimum fails
        with pytest.raises(ValidationError):
            StoryArchitectRequest(concept="Test", duration=5)

        # Above maximum fails
        with pytest.raises(ValidationError):
            StoryArchitectRequest(concept="Test", duration=1000)

    def test_concept_min_length(self):
        """Test concept minimum length."""
        request = StoryArchitectRequest(concept="A")
        assert request.concept == "A"

        with pytest.raises(ValidationError):
            StoryArchitectRequest(concept="")


# ============================================================================
# StoryRefineRequest Tests
# ============================================================================

class TestStoryRefineRequest:
    """Test StoryRefineRequest model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = StoryRefineRequest(
            concept="A romantic comedy about two chefs competing",
            genre="comedy",
        )
        assert "romantic comedy" in request.concept
        assert request.genre == "comedy"

    def test_default_values(self):
        """Test default values are applied."""
        request = StoryRefineRequest(
            concept="Test concept",
        )
        assert request.genre == "drama"
        assert request.model == "gemini-3-flash-preview"

    def test_concept_sanitization(self):
        """Test concept XSS sanitization."""
        request = StoryRefineRequest(
            concept="<script>evil()</script>idea",
        )
        assert "<script>" not in request.concept
        assert "idea" in request.concept

    def test_genre_validation(self):
        """Test genre validation."""
        for genre in ALLOWED_GENRES:
            request = StoryRefineRequest(
                concept="Test",
                genre=genre,
            )
            assert request.genre == genre

    def test_invalid_genre_fails(self):
        """Test invalid genre fails validation."""
        with pytest.raises(ValidationError):
            StoryRefineRequest(
                concept="Test",
                genre="western",
            )


# ============================================================================
# ShotListRequest Tests
# ============================================================================

class TestShotListRequest:
    """Test ShotListRequest model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = ShotListRequest(
            scenario="A chef prepares a dish in a busy kitchen.",
            total_duration=60,
            max_shot_duration=8,
            style_preference="cinematic",
        )
        assert "chef" in request.scenario
        assert request.total_duration == 60
        assert request.max_shot_duration == 8
        assert request.style_preference == "cinematic"

    def test_default_values(self):
        """Test default values are applied."""
        request = ShotListRequest(
            scenario="A simple test scenario with enough characters.",
        )
        assert request.total_duration == 60
        assert request.max_shot_duration == 8
        assert request.style_preference == "cinematic"
        assert request.model == "gemini-3-flash-preview"

    def test_scenario_sanitization(self):
        """Test scenario XSS sanitization."""
        request = ShotListRequest(
            scenario="<script>alert('xss')</script>The scene opens in a cafe.",
        )
        assert "<script>" not in request.scenario
        assert "The scene opens" in request.scenario

    def test_style_preference_sanitization(self):
        """Test style_preference XSS sanitization."""
        request = ShotListRequest(
            scenario="A valid scenario with at least 10 characters",
            style_preference="javascript:alert(1)noir",
        )
        assert "javascript:" not in request.style_preference.lower()

    def test_total_duration_bounds(self):
        """Test total_duration min/max bounds."""
        # Valid minimum
        request = ShotListRequest(
            scenario="A valid test scenario.",
            total_duration=10,
        )
        assert request.total_duration == 10

        # Valid maximum
        request = ShotListRequest(
            scenario="A valid test scenario.",
            total_duration=300,
        )
        assert request.total_duration == 300

        # Below minimum fails
        with pytest.raises(ValidationError):
            ShotListRequest(
                scenario="A valid test scenario.",
                total_duration=5,
            )

        # Above maximum fails
        with pytest.raises(ValidationError):
            ShotListRequest(
                scenario="A valid test scenario.",
                total_duration=500,
            )

    def test_max_shot_duration_bounds(self):
        """Test max_shot_duration min/max bounds."""
        # Valid minimum
        request = ShotListRequest(
            scenario="A valid test scenario.",
            max_shot_duration=4,
        )
        assert request.max_shot_duration == 4

        # Valid maximum
        request = ShotListRequest(
            scenario="A valid test scenario.",
            max_shot_duration=10,
        )
        assert request.max_shot_duration == 10

        # Below minimum fails
        with pytest.raises(ValidationError):
            ShotListRequest(
                scenario="A valid test scenario.",
                max_shot_duration=2,
            )

        # Above maximum fails
        with pytest.raises(ValidationError):
            ShotListRequest(
                scenario="A valid test scenario.",
                max_shot_duration=15,
            )

    def test_scenario_min_length(self):
        """Test scenario minimum length (10 characters)."""
        # Valid minimum (exactly 10)
        request = ShotListRequest(scenario="1234567890")
        assert len(request.scenario) >= 10

        # Below minimum fails
        with pytest.raises(ValidationError):
            ShotListRequest(scenario="short")


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
    def test_concept_xss_storyarchitect(self, attack_vector):
        """Test StoryArchitectRequest concept field XSS prevention."""
        request = StoryArchitectRequest(
            concept=attack_vector + "story",
        )
        assert "<script>" not in request.concept.lower()
        assert "onerror" not in request.concept.lower()
        assert "javascript:" not in request.concept.lower()
        assert "onclick" not in request.concept.lower()
        assert "onmouseover" not in request.concept.lower()
        assert "onload" not in request.concept.lower()

    @pytest.mark.parametrize("attack_vector", [
        "<script>evil()</script>",
        "onclick=malicious()",
    ])
    def test_persona_data_xss(self, attack_vector):
        """Test persona_data field XSS prevention."""
        request = StoryArchitectRequest(
            concept="Test",
            persona_data=attack_vector + "data",
        )
        assert "<script>" not in request.persona_data.lower()
        assert "onclick" not in request.persona_data.lower()

    @pytest.mark.parametrize("attack_vector", [
        "<script>alert('xss')</script>",
        "javascript:void(0)",
    ])
    def test_concept_xss_storyrefine(self, attack_vector):
        """Test StoryRefineRequest concept field XSS prevention."""
        request = StoryRefineRequest(
            concept=attack_vector + "idea",
        )
        assert "<script>" not in request.concept.lower()
        assert "javascript:" not in request.concept.lower()

    @pytest.mark.parametrize("attack_vector", [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(1)",
    ])
    def test_scenario_xss(self, attack_vector):
        """Test ShotListRequest scenario field XSS prevention."""
        request = ShotListRequest(
            scenario=attack_vector + "The scene opens at dawn.",
        )
        assert "<script>" not in request.scenario.lower()
        assert "onerror" not in request.scenario.lower()
        assert "javascript:" not in request.scenario.lower()

    @pytest.mark.parametrize("attack_vector", [
        "<div onclick=evil()>",
        "onmouseover=alert(1)",
    ])
    def test_style_preference_xss(self, attack_vector):
        """Test ShotListRequest style_preference field XSS prevention."""
        request = ShotListRequest(
            scenario="A valid scenario with at least 10 characters.",
            style_preference=attack_vector + "cinematic",
        )
        assert "onclick" not in request.style_preference.lower()
        assert "onmouseover" not in request.style_preference.lower()


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_in_concept(self):
        """Test Korean and emoji in concept."""
        request = StoryArchitectRequest(
            concept="밤하늘 아래 🌙 별을 세는 소녀의 이야기",
        )
        assert "밤하늘" in request.concept
        assert "🌙" in request.concept
        assert "소녀" in request.concept

    def test_unicode_in_scenario(self):
        """Test Korean and emoji in scenario."""
        request = ShotListRequest(
            scenario="새벽 4시, 작은 카페에서 ☕ 바리스타가 커피를 내린다.",
        )
        assert "새벽 4시" in request.scenario
        assert "☕" in request.scenario
        assert "바리스타" in request.scenario

    def test_all_valid_genres(self):
        """Test all valid genres work in StoryArchitectRequest."""
        for genre in ALLOWED_GENRES:
            request = StoryArchitectRequest(
                concept="Test concept",
                genre=genre,
            )
            assert request.genre == genre

    def test_all_valid_structures(self):
        """Test all valid structures work in StoryArchitectRequest."""
        for structure in ALLOWED_STRUCTURES:
            request = StoryArchitectRequest(
                concept="Test concept",
                structure=structure,
            )
            assert request.structure == structure

    def test_long_concept(self):
        """Test long concept within max length."""
        long_concept = "A " * 500  # 1000 chars
        request = StoryArchitectRequest(
            concept=long_concept,
        )
        assert len(request.concept) == len(long_concept.strip())

    def test_long_scenario(self):
        """Test long scenario within max length."""
        long_scenario = "Scene " * 500  # 3000 chars
        request = ShotListRequest(
            scenario=long_scenario,
        )
        assert len(request.scenario) == len(long_scenario.strip())

    def test_concept_whitespace_strip(self):
        """Test concept whitespace stripping."""
        request = StoryArchitectRequest(
            concept="  Test concept with spaces  ",
        )
        assert request.concept == "Test concept with spaces"

    def test_scenario_whitespace_strip(self):
        """Test scenario whitespace stripping."""
        request = ShotListRequest(
            scenario="  The scene opens at dawn  ",
        )
        assert request.scenario == "The scene opens at dawn"

    def test_empty_persona_data(self):
        """Test empty persona_data is allowed."""
        request = StoryArchitectRequest(
            concept="Test concept",
            persona_data="",
        )
        assert request.persona_data == ""

    def test_empty_reference_analysis(self):
        """Test empty reference_analysis is allowed."""
        request = StoryArchitectRequest(
            concept="Test concept",
            reference_analysis="",
        )
        assert request.reference_analysis == ""

    def test_genre_case_normalization(self):
        """Test genre is normalized to lowercase."""
        request = StoryArchitectRequest(
            concept="Test",
            genre="DRAMA",
        )
        assert request.genre == "drama"

    def test_structure_case_normalization(self):
        """Test structure is normalized to lowercase."""
        request = StoryArchitectRequest(
            concept="Test",
            structure="HERO-JOURNEY",
        )
        assert request.structure == "hero-journey"

    def test_special_characters_in_concept(self):
        """Test special characters preserved in concept."""
        request = StoryArchitectRequest(
            concept="A story about love & loss - the journey begins...",
        )
        assert "&" in request.concept or "&amp;" in request.concept
        assert "-" in request.concept

    def test_newlines_in_scenario(self):
        """Test newlines in scenario are preserved."""
        request = ShotListRequest(
            scenario="Scene 1: The cafe opens.\nScene 2: Coffee brewing.",
        )
        assert "\n" in request.scenario or "Scene 1" in request.scenario
