"""
Tests for Aesthetic Dimension Endpoints.

Tests include:
- XSS sanitization for concept, mood, reference_style, subject, name, etc.
- Enum validation for lighting_style, color_mood, style_reference, target_medium, current_stage
- Edge case inputs
"""
import pytest
from pydantic import ValidationError

from app.routers.dimension.aesthetic import (
    # Constants
    ALLOWED_LIGHTING_STYLES,
    ALLOWED_COLOR_MOODS,
    ALLOWED_STYLE_REFERENCES,
    ALLOWED_TARGET_MEDIUMS,
    ALLOWED_PERSONA_STAGES,
    # Request models
    AestheticDirectRequest,
    AestheticMoodboardRequest,
    PersonaAnalyzeRequest,
    CharacterDNARequest,
    # Helpers
    _sanitize_text_field,
    _validate_lighting_style,
    _validate_color_mood,
    _validate_style_reference,
    _validate_target_medium,
    _validate_persona_stage,
)


# ============================================================================
# Sanitization Helpers Tests
# ============================================================================

class TestSanitizeTextField:
    """Test _sanitize_text_field helper."""

    def test_removes_html_tags(self):
        """Test HTML tag removal."""
        result = _sanitize_text_field("<div>visual concept</div>")
        assert "<div>" not in result
        assert "</div>" not in result
        assert "visual concept" in result

    def test_removes_script_tags(self):
        """Test script tag removal."""
        result = _sanitize_text_field("<script>evil()</script>concept")
        assert "<script>" not in result

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
        result = _sanitize_text_field("cinematic, moody, atmospheric")
        assert "cinematic" in result
        assert "moody" in result

    def test_preserves_korean(self):
        """Test Korean characters preserved."""
        result = _sanitize_text_field("영화적인 분위기의 시각적 컨셉")
        assert "영화적인" in result
        assert "분위기" in result

    def test_empty_returns_default(self):
        """Test empty string returns default."""
        assert _sanitize_text_field("", default="cinematic") == "cinematic"
        assert _sanitize_text_field("   ", default="cinematic") == "cinematic"

    def test_none_returns_default(self):
        """Test None returns default."""
        result = _sanitize_text_field(None, default="default")
        assert result == "default"


# ============================================================================
# Validation Helpers Tests
# ============================================================================

class TestValidateLightingStyle:
    """Test _validate_lighting_style helper."""

    def test_valid_styles(self):
        """Test valid lighting styles pass."""
        for style in ALLOWED_LIGHTING_STYLES:
            assert _validate_lighting_style(style) == style

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert _validate_lighting_style("NATURAL") == "natural"
        assert _validate_lighting_style("High-Key") == "high-key"

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        assert _validate_lighting_style("  natural  ") == "natural"

    def test_invalid_style_raises(self):
        """Test invalid style raises ValueError."""
        with pytest.raises(ValueError, match="Invalid lighting_style"):
            _validate_lighting_style("fluorescent")
        with pytest.raises(ValueError, match="Invalid lighting_style"):
            _validate_lighting_style("invalid")


class TestValidateColorMood:
    """Test _validate_color_mood helper."""

    def test_valid_moods(self):
        """Test valid color moods pass."""
        for mood in ALLOWED_COLOR_MOODS:
            assert _validate_color_mood(mood) == mood

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert _validate_color_mood("WARM") == "warm"
        assert _validate_color_mood("Cool") == "cool"

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        assert _validate_color_mood("  neutral  ") == "neutral"

    def test_invalid_mood_raises(self):
        """Test invalid mood raises ValueError."""
        with pytest.raises(ValueError, match="Invalid color_mood"):
            _validate_color_mood("neon")
        with pytest.raises(ValueError, match="Invalid color_mood"):
            _validate_color_mood("invalid")


class TestValidateStyleReference:
    """Test _validate_style_reference helper."""

    def test_valid_styles(self):
        """Test valid style references pass."""
        for style in ALLOWED_STYLE_REFERENCES:
            assert _validate_style_reference(style) == style

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert _validate_style_reference("ANIME") == "anime"
        assert _validate_style_reference("Realistic") == "realistic"

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        assert _validate_style_reference("  cinematic  ") == "cinematic"

    def test_invalid_style_raises(self):
        """Test invalid style raises ValueError."""
        with pytest.raises(ValueError, match="Invalid style_reference"):
            _validate_style_reference("cartoon")
        with pytest.raises(ValueError, match="Invalid style_reference"):
            _validate_style_reference("invalid")


class TestValidateTargetMedium:
    """Test _validate_target_medium helper."""

    def test_valid_mediums(self):
        """Test valid target mediums pass."""
        for medium in ALLOWED_TARGET_MEDIUMS:
            assert _validate_target_medium(medium) == medium

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert _validate_target_medium("VIDEO") == "video"
        assert _validate_target_medium("Image") == "image"

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        assert _validate_target_medium("  video  ") == "video"

    def test_invalid_medium_raises(self):
        """Test invalid medium raises ValueError."""
        with pytest.raises(ValueError, match="Invalid target_medium"):
            _validate_target_medium("cinema")
        with pytest.raises(ValueError, match="Invalid target_medium"):
            _validate_target_medium("invalid")


class TestValidatePersonaStage:
    """Test _validate_persona_stage helper."""

    def test_valid_stages(self):
        """Test valid persona stages pass."""
        for stage in ALLOWED_PERSONA_STAGES:
            assert _validate_persona_stage(stage) == stage

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert _validate_persona_stage("INTRO") == "intro"
        assert _validate_persona_stage("Birth") == "birth"

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        assert _validate_persona_stage("  intro  ") == "intro"

    def test_invalid_stage_raises(self):
        """Test invalid stage raises ValueError."""
        with pytest.raises(ValueError, match="Invalid current_stage"):
            _validate_persona_stage("middle")
        with pytest.raises(ValueError, match="Invalid current_stage"):
            _validate_persona_stage("invalid")


class TestAllowedConstantsContent:
    """Test allowed constants have expected values."""

    def test_lighting_styles_content(self):
        """Verify expected lighting styles are present."""
        expected = ["natural", "high-key", "low-key", "dramatic", "soft"]
        for style in expected:
            assert style in ALLOWED_LIGHTING_STYLES

    def test_color_moods_content(self):
        """Verify expected color moods are present."""
        expected = ["neutral", "warm", "cool", "desaturated", "vibrant"]
        for mood in expected:
            assert mood in ALLOWED_COLOR_MOODS

    def test_style_references_content(self):
        """Verify expected style references are present."""
        expected = ["anime", "realistic", "stylized", "cinematic"]
        for style in expected:
            assert style in ALLOWED_STYLE_REFERENCES

    def test_target_mediums_content(self):
        """Verify expected target mediums are present."""
        expected = ["video", "image", "animation", "web", "print", "social"]
        for medium in expected:
            assert medium in ALLOWED_TARGET_MEDIUMS

    def test_persona_stages_content(self):
        """Verify expected persona stages are present."""
        expected = ["intro", "birth", "saju", "synthesis", "final"]
        for stage in expected:
            assert stage in ALLOWED_PERSONA_STAGES


# ============================================================================
# Request Model Tests - AestheticDirectRequest
# ============================================================================

class TestAestheticDirectRequest:
    """Test AestheticDirectRequest model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = AestheticDirectRequest(
            concept="A cinematic urban nightscape with neon lights",
            reference_style="bong",
            mood="moody",
            lighting_style="dramatic",
            color_mood="cool",
            target_medium="video",
        )
        assert "nightscape" in request.concept
        assert request.reference_style == "bong"
        assert request.lighting_style == "dramatic"
        assert request.color_mood == "cool"

    def test_default_values(self):
        """Test default values are applied."""
        request = AestheticDirectRequest(concept="Test concept")
        assert request.reference_style == "bong"
        assert request.mood == "cinematic"
        assert request.lighting_style == "natural"
        assert request.color_mood == "neutral"
        assert request.target_medium == "video"
        assert request.use_rag is True
        assert request.model == "gemini-3-flash-preview"

    def test_concept_sanitization(self):
        """Test concept XSS sanitization."""
        request = AestheticDirectRequest(
            concept="<script>alert('xss')</script>urban scene",
        )
        assert "<script>" not in request.concept
        assert "urban scene" in request.concept

    def test_mood_sanitization(self):
        """Test mood XSS sanitization."""
        request = AestheticDirectRequest(
            concept="Test concept",
            mood="javascript:alert(1)moody",
        )
        assert "javascript:" not in request.mood.lower()

    def test_reference_style_sanitization(self):
        """Test reference_style XSS sanitization."""
        request = AestheticDirectRequest(
            concept="Test concept",
            reference_style="<img onerror=evil()>bong",
        )
        assert "<img" not in request.reference_style
        assert "onerror" not in request.reference_style

    def test_invalid_lighting_style_fails(self):
        """Test invalid lighting_style fails validation."""
        with pytest.raises(ValidationError):
            AestheticDirectRequest(
                concept="Test concept",
                lighting_style="fluorescent",
            )

    def test_invalid_color_mood_fails(self):
        """Test invalid color_mood fails validation."""
        with pytest.raises(ValidationError):
            AestheticDirectRequest(
                concept="Test concept",
                color_mood="neon",
            )

    def test_invalid_target_medium_fails(self):
        """Test invalid target_medium fails validation."""
        with pytest.raises(ValidationError):
            AestheticDirectRequest(
                concept="Test concept",
                target_medium="cinema",
            )

    def test_concept_min_length(self):
        """Test concept minimum length."""
        request = AestheticDirectRequest(concept="A")
        assert request.concept == "A"

        with pytest.raises(ValidationError):
            AestheticDirectRequest(concept="")


# ============================================================================
# Request Model Tests - AestheticMoodboardRequest
# ============================================================================

class TestAestheticMoodboardRequest:
    """Test AestheticMoodboardRequest model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = AestheticMoodboardRequest(
            concept="A dreamy forest scene",
            mood="ethereal",
        )
        assert "forest" in request.concept
        assert request.mood == "ethereal"

    def test_default_values(self):
        """Test default values are applied."""
        request = AestheticMoodboardRequest(concept="Test concept")
        assert request.mood == "cinematic"
        assert request.model == "gemini-3-flash-preview"

    def test_concept_sanitization(self):
        """Test concept XSS sanitization."""
        request = AestheticMoodboardRequest(
            concept="<script>evil()</script>visual concept",
        )
        assert "<script>" not in request.concept
        assert "visual concept" in request.concept

    def test_mood_sanitization(self):
        """Test mood XSS sanitization."""
        request = AestheticMoodboardRequest(
            concept="Test concept",
            mood="onmouseover=alert(1)",
        )
        assert "onmouseover=" not in request.mood.lower()


# ============================================================================
# Request Model Tests - PersonaAnalyzeRequest
# ============================================================================

class TestPersonaAnalyzeRequest:
    """Test PersonaAnalyzeRequest model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = PersonaAnalyzeRequest(
            subject="Creative filmmaker persona",
            user_message="Tell me about my creative style",
            current_stage="intro",
        )
        assert "filmmaker" in request.subject
        assert request.current_stage == "intro"

    def test_default_values(self):
        """Test default values are applied."""
        request = PersonaAnalyzeRequest(subject="Test subject")
        assert request.user_message == ""
        assert request.current_stage == "intro"
        assert request.persona_data == {}
        assert request.birth_info == {}

    def test_subject_sanitization(self):
        """Test subject XSS sanitization."""
        request = PersonaAnalyzeRequest(
            subject="<script>alert('xss')</script>creative persona",
        )
        assert "<script>" not in request.subject
        assert "creative persona" in request.subject

    def test_user_message_sanitization(self):
        """Test user_message XSS sanitization."""
        request = PersonaAnalyzeRequest(
            subject="Test subject",
            user_message="javascript:alert(1)",
        )
        assert "javascript:" not in request.user_message.lower()

    def test_invalid_stage_fails(self):
        """Test invalid current_stage fails validation."""
        with pytest.raises(ValidationError):
            PersonaAnalyzeRequest(
                subject="Test subject",
                current_stage="middle",
            )

    def test_all_valid_stages(self):
        """Test all valid stages work."""
        for stage in ALLOWED_PERSONA_STAGES:
            request = PersonaAnalyzeRequest(
                subject="Test subject",
                current_stage=stage,
            )
            assert request.current_stage == stage


# ============================================================================
# Request Model Tests - CharacterDNARequest
# ============================================================================

class TestCharacterDNARequest:
    """Test CharacterDNARequest model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = CharacterDNARequest(
            name="Sora",
            role="48-year-old master chef",
            personality="Quiet and introspective",
            physical_traits="Strong weathered hands",
            style_reference="anime",
        )
        assert request.name == "Sora"
        assert "master chef" in request.role
        assert request.style_reference == "anime"

    def test_default_values(self):
        """Test default values are applied."""
        request = CharacterDNARequest(
            name="Test",
            role="Test role",
        )
        assert request.personality == ""
        assert request.physical_traits == ""
        assert request.wiki_context == ""
        assert request.style_reference == "anime"
        assert request.model == "gemini-3-flash-preview"

    def test_name_sanitization(self):
        """Test name XSS sanitization."""
        request = CharacterDNARequest(
            name="<script>evil()</script>Sora",
            role="Chef",
        )
        assert "<script>" not in request.name

    def test_role_sanitization(self):
        """Test role XSS sanitization."""
        request = CharacterDNARequest(
            name="Test",
            role="javascript:alert(1)chef",
        )
        assert "javascript:" not in request.role.lower()

    def test_personality_sanitization(self):
        """Test personality XSS sanitization."""
        request = CharacterDNARequest(
            name="Test",
            role="Chef",
            personality="<img onerror=evil()>quiet",
        )
        assert "<img" not in request.personality
        assert "onerror" not in request.personality

    def test_physical_traits_sanitization(self):
        """Test physical_traits XSS sanitization."""
        request = CharacterDNARequest(
            name="Test",
            role="Chef",
            physical_traits="<div onclick=alert(1)>strong hands",
        )
        assert "<div" not in request.physical_traits
        assert "onclick" not in request.physical_traits

    def test_wiki_context_sanitization(self):
        """Test wiki_context XSS sanitization."""
        request = CharacterDNARequest(
            name="Test",
            role="Chef",
            wiki_context="<script>steal(cookies)</script>context",
        )
        assert "<script>" not in request.wiki_context

    def test_invalid_style_reference_fails(self):
        """Test invalid style_reference fails validation."""
        with pytest.raises(ValidationError):
            CharacterDNARequest(
                name="Test",
                role="Chef",
                style_reference="cartoon",
            )

    def test_all_valid_style_references(self):
        """Test all valid style references work."""
        for style in ALLOWED_STYLE_REFERENCES:
            request = CharacterDNARequest(
                name="Test",
                role="Chef",
                style_reference=style,
            )
            assert request.style_reference == style


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
    ])
    def test_concept_xss(self, attack_vector):
        """Test concept field XSS prevention."""
        request = AestheticDirectRequest(
            concept=attack_vector + "visual",
        )
        assert "<script>" not in request.concept.lower()
        assert "onerror" not in request.concept.lower()
        assert "javascript:" not in request.concept.lower()
        assert "onload" not in request.concept.lower()

    @pytest.mark.parametrize("attack_vector", [
        "<script>evil()</script>",
        "onclick=malicious()",
    ])
    def test_mood_xss(self, attack_vector):
        """Test mood field XSS prevention."""
        request = AestheticDirectRequest(
            concept="Test",
            mood=attack_vector + "moody",
        )
        assert "<script>" not in request.mood.lower()
        assert "onclick" not in request.mood.lower()

    @pytest.mark.parametrize("attack_vector", [
        "<div onclick=evil()>",
        "onmouseover=alert(1)",
    ])
    def test_subject_xss(self, attack_vector):
        """Test subject field XSS prevention."""
        request = PersonaAnalyzeRequest(
            subject=attack_vector + "persona",
        )
        assert "onclick" not in request.subject.lower()
        assert "onmouseover" not in request.subject.lower()

    @pytest.mark.parametrize("attack_vector", [
        "<script>steal()</script>",
        "javascript:void(0)",
    ])
    def test_character_name_xss(self, attack_vector):
        """Test character name field XSS prevention."""
        request = CharacterDNARequest(
            name=attack_vector + "Sora",
            role="Chef",
        )
        assert "<script>" not in request.name.lower()
        assert "javascript:" not in request.name.lower()


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_in_concept(self):
        """Test Korean and emoji in concept."""
        request = AestheticDirectRequest(
            concept="도시의 밤하늘 아래 🌃 네온 사인",
        )
        assert "도시의" in request.concept
        assert "🌃" in request.concept

    def test_all_valid_lighting_styles(self):
        """Test all valid lighting styles work."""
        for style in ALLOWED_LIGHTING_STYLES:
            request = AestheticDirectRequest(
                concept="Test",
                lighting_style=style,
            )
            assert request.lighting_style == style

    def test_all_valid_color_moods(self):
        """Test all valid color moods work."""
        for mood in ALLOWED_COLOR_MOODS:
            request = AestheticDirectRequest(
                concept="Test",
                color_mood=mood,
            )
            assert request.color_mood == mood

    def test_all_valid_target_mediums(self):
        """Test all valid target mediums work."""
        for medium in ALLOWED_TARGET_MEDIUMS:
            request = AestheticDirectRequest(
                concept="Test",
                target_medium=medium,
            )
            assert request.target_medium == medium

    def test_empty_optional_fields(self):
        """Test empty optional fields are allowed."""
        request = CharacterDNARequest(
            name="Test",
            role="Chef",
            personality="",
            physical_traits="",
            wiki_context="",
        )
        assert request.personality == ""
        assert request.physical_traits == ""
        assert request.wiki_context == ""

    def test_long_concept(self):
        """Test long concept within max length."""
        long_concept = "A " * 500  # 1000 chars
        request = AestheticDirectRequest(
            concept=long_concept,
        )
        assert len(request.concept) > 0

    def test_long_wiki_context(self):
        """Test long wiki_context within max length."""
        long_context = "Context " * 500  # ~4000 chars
        request = CharacterDNARequest(
            name="Test",
            role="Chef",
            wiki_context=long_context,
        )
        assert len(request.wiki_context) > 0

    def test_persona_with_dict_fields(self):
        """Test persona with dict fields."""
        request = PersonaAnalyzeRequest(
            subject="Test",
            persona_data={"trait": "creative", "score": 85},
            birth_info={"year": 1990, "month": 5},
        )
        assert request.persona_data["trait"] == "creative"
        assert request.birth_info["year"] == 1990

    def test_persona_with_params(self):
        """Test persona with params field."""
        request = PersonaAnalyzeRequest(
            subject="Test",
            params={"depth_level": "deep", "focus": "creativity"},
        )
        assert request.params["depth_level"] == "deep"

    def test_moodboard_with_custom_mood(self):
        """Test moodboard with custom mood (after sanitization)."""
        request = AestheticMoodboardRequest(
            concept="Test",
            mood="ethereal and dreamy",
        )
        assert "ethereal" in request.mood
        assert "dreamy" in request.mood
