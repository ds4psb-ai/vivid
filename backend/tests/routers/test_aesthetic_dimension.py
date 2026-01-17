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
    # Response models (2026 Best Practices)
    CharacterDNAResponse,
    AestheticQualityScore,
    AestheticPreferenceAspect,
    # Helpers
    _sanitize_text_field,
    _validate_lighting_style,
    _validate_color_mood,
    _validate_style_reference,
    _validate_target_medium,
    _validate_persona_stage,
    # 2026 Enhancements
    AUTEUR_COMPATIBILITY_MATRIX,
    AUTEUR_VISUAL_KEYWORDS,
    GOLDEN_RATIO,
    COLOR_HARMONY_ANGLES,
    AuteurBlendResult,
    AestheticPromptQuality,
    get_auteur_compatibility,
    blend_auteur_styles,
    calculate_golden_ratio_points,
    get_color_harmony_palette,
    assess_aesthetic_prompt_quality,
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


# ============================================================================
# Response Model Tests - CharacterDNAResponse (2026 Best Practices)
# ============================================================================

class TestCharacterDNAResponse:
    """Test CharacterDNAResponse model with evidence_refs."""

    def test_valid_response(self):
        """Test valid response creation."""
        response = CharacterDNAResponse(
            success=True,
            character_name="Sora",
            character_dna="48-year-old master chef, quiet and introverted",
            style_prompt="anime style",
            full_prompt="anime style, 48-year-old master chef",
            usage_hint="Use as prefix",
            trace_id="test-uuid-1234",
            evidence_refs=[
                "rag:character_dna:anime:visual_layer",
                "db:character_dna:uuid-5678",
            ],
            confidence=0.85,
        )
        assert response.success is True
        assert response.character_name == "Sora"
        assert "master chef" in response.character_dna
        assert response.trace_id == "test-uuid-1234"
        assert len(response.evidence_refs) == 2
        assert response.confidence == 0.85

    def test_evidence_refs_is_list_of_strings(self):
        """Test evidence_refs is List[str] (Vivid convention)."""
        response = CharacterDNAResponse(
            success=True,
            character_name="Test",
            character_dna="dna",
            style_prompt="style",
            full_prompt="full",
            usage_hint="hint",
            evidence_refs=["ref1", "ref2", "ref3"],
        )
        assert isinstance(response.evidence_refs, list)
        for ref in response.evidence_refs:
            assert isinstance(ref, str)

    def test_evidence_refs_format_rag(self):
        """Test evidence_refs follows RAG format."""
        response = CharacterDNAResponse(
            success=True,
            character_name="Test",
            character_dna="dna",
            style_prompt="style",
            full_prompt="full",
            usage_hint="hint",
            evidence_refs=[
                "rag:auteur_dna:bong:visual:composition",
                "rag:character_dna:anime:psychological_layer",
            ],
        )
        for ref in response.evidence_refs:
            assert ref.startswith("rag:") or ref.startswith("db:")

    def test_evidence_refs_default_empty(self):
        """Test evidence_refs defaults to empty list."""
        response = CharacterDNAResponse(
            success=False,
            character_name="Test",
            character_dna="",
            style_prompt="",
            full_prompt="",
            usage_hint="Error",
        )
        assert response.evidence_refs == []

    def test_confidence_bounds(self):
        """Test confidence is bounded [0, 1]."""
        response = CharacterDNAResponse(
            success=True,
            character_name="Test",
            character_dna="dna",
            style_prompt="style",
            full_prompt="full",
            usage_hint="hint",
            confidence=0.95,
        )
        assert 0.0 <= response.confidence <= 1.0

    def test_confidence_out_of_bounds_raises(self):
        """Test confidence out of bounds raises."""
        with pytest.raises(ValidationError):
            CharacterDNAResponse(
                success=True,
                character_name="Test",
                character_dna="dna",
                style_prompt="style",
                full_prompt="full",
                usage_hint="hint",
                confidence=1.5,
            )

    def test_trace_id_default_empty(self):
        """Test trace_id defaults to empty string."""
        response = CharacterDNAResponse(
            success=True,
            character_name="Test",
            character_dna="dna",
            style_prompt="style",
            full_prompt="full",
            usage_hint="hint",
        )
        assert response.trace_id == ""


# ============================================================================
# 2026 Best Practices Tests - AestheticQualityScore (VisionPrefer/AesthetiQ)
# ============================================================================

class TestAestheticQualityScore:
    """Test AestheticQualityScore model (2026 VisionPrefer/AesthetiQ pattern)."""

    def test_valid_score(self):
        """Test valid quality score creation."""
        score = AestheticQualityScore(
            prompt_following=0.9,
            fidelity=0.8,
            aesthetic=0.85,
            harmlessness=1.0,
            overall=0.86,
        )
        assert score.prompt_following == 0.9
        assert score.fidelity == 0.8
        assert score.aesthetic == 0.85
        assert score.harmlessness == 1.0
        assert score.overall == 0.86

    def test_default_values(self):
        """Test default values for quality score."""
        score = AestheticQualityScore()
        assert score.prompt_following == 0.0
        assert score.fidelity == 0.0
        assert score.aesthetic == 0.0
        assert score.harmlessness == 1.0  # Safe by default
        assert score.overall == 0.0

    def test_bounds_enforcement(self):
        """Test all scores are bounded [0, 1]."""
        with pytest.raises(ValidationError):
            AestheticQualityScore(prompt_following=1.5)
        with pytest.raises(ValidationError):
            AestheticQualityScore(fidelity=-0.1)
        with pytest.raises(ValidationError):
            AestheticQualityScore(aesthetic=2.0)
        with pytest.raises(ValidationError):
            AestheticQualityScore(harmlessness=1.1)
        with pytest.raises(ValidationError):
            AestheticQualityScore(overall=-0.5)

    def test_all_aspects_covered(self):
        """Test all VisionPrefer aspects are present."""
        score = AestheticQualityScore(
            prompt_following=0.8,
            fidelity=0.7,
            aesthetic=0.9,
            harmlessness=1.0,
            overall=0.85,
        )
        # VisionPrefer 4 aspects: Prompt-Following, Fidelity, Aesthetic, Harmlessness
        assert hasattr(score, "prompt_following")
        assert hasattr(score, "fidelity")
        assert hasattr(score, "aesthetic")
        assert hasattr(score, "harmlessness")
        assert hasattr(score, "overall")


class TestAestheticPreferenceAspect:
    """Test AestheticPreferenceAspect enum (2026 fine-grained preference)."""

    def test_all_visionprefer_aspects(self):
        """Test all VisionPrefer aspects are defined."""
        assert AestheticPreferenceAspect.PROMPT_FOLLOWING == "prompt_following"
        assert AestheticPreferenceAspect.FIDELITY == "fidelity"
        assert AestheticPreferenceAspect.AESTHETIC == "aesthetic"
        assert AestheticPreferenceAspect.HARMLESSNESS == "harmlessness"

    def test_aspect_count(self):
        """Test correct number of aspects."""
        aspects = list(AestheticPreferenceAspect)
        assert len(aspects) == 4

    def test_aspect_values_are_strings(self):
        """Test all aspect values are strings."""
        for aspect in AestheticPreferenceAspect:
            assert isinstance(aspect.value, str)


# ============================================================================
# Evidence Refs Format Validation Tests
# ============================================================================

class TestEvidenceRefsFormat:
    """Test evidence_refs format validation."""

    @pytest.mark.parametrize("ref", [
        "rag:auteur_dna:bong:visual:composition",
        "rag:auteur_dna:kubrick:lighting:chiaroscuro",
        "rag:character_dna:anime:visual_layer",
        "rag:aesthetic:mathematical:golden_ratio",
        "db:character_dna:uuid-1234-5678",
        "db:aesthetic_guide:session-uuid",
    ])
    def test_valid_evidence_ref_formats(self, ref):
        """Test valid evidence_refs formats."""
        response = CharacterDNAResponse(
            success=True,
            character_name="Test",
            character_dna="dna",
            style_prompt="style",
            full_prompt="full",
            usage_hint="hint",
            evidence_refs=[ref],
        )
        assert ref in response.evidence_refs

    def test_multiple_evidence_refs(self):
        """Test multiple evidence_refs."""
        refs = [
            "rag:auteur_dna:bong:visual:composition",
            "rag:auteur_dna:bong:audio:silence_usage",
            "rag:mathematical_aesthetics:golden_ratio",
            "db:style_guide:session-uuid",
        ]
        response = CharacterDNAResponse(
            success=True,
            character_name="Test",
            character_dna="dna",
            style_prompt="style",
            full_prompt="full",
            usage_hint="hint",
            evidence_refs=refs,
        )
        assert len(response.evidence_refs) == 4
        for ref in refs:
            assert ref in response.evidence_refs

    def test_empty_evidence_refs_allowed(self):
        """Test empty evidence_refs is allowed (LLM-only mode)."""
        response = CharacterDNAResponse(
            success=True,
            character_name="Test",
            character_dna="dna",
            style_prompt="style",
            full_prompt="full",
            usage_hint="hint",
            evidence_refs=[],
        )
        assert response.evidence_refs == []


# ============================================================================
# 2026 Multimodal Best Practices Tests
# ============================================================================

class TestMultimodalAestheticPatterns:
    """Test 2026 multimodal aesthetic patterns."""

    def test_visual_dna_with_psychological_layer(self):
        """Test Character DNA includes both visual and psychological layers."""
        response = CharacterDNAResponse(
            success=True,
            character_name="Chef Sora",
            character_dna="48-year-old male chef, quiet introspective master craftsman, appears awkward when speaking",
            style_prompt="anime style",
            full_prompt="anime style, 48-year-old male chef",
            usage_hint="hint",
            evidence_refs=[
                "rag:character_dna:anime:visual_layer",
                "rag:character_dna:anime:psychological_layer",  # 2026: psychological acting layer
            ],
        )
        # Check both layers referenced
        visual_refs = [r for r in response.evidence_refs if "visual_layer" in r]
        psych_refs = [r for r in response.evidence_refs if "psychological_layer" in r]
        assert len(visual_refs) >= 1
        assert len(psych_refs) >= 1

    def test_style_reference_all_types(self):
        """Test all style references work correctly."""
        for style in ALLOWED_STYLE_REFERENCES:
            response = CharacterDNAResponse(
                success=True,
                character_name="Test",
                character_dna=f"Character in {style} style",
                style_prompt=f"{style} style prompt",
                full_prompt=f"{style} style prompt, Character",
                usage_hint="hint",
                evidence_refs=[f"rag:character_dna:{style}:visual_layer"],
            )
            assert style in response.evidence_refs[0]

    def test_cross_modal_consistency(self):
        """Test evidence_refs can reference cross-modal aspects."""
        response = CharacterDNAResponse(
            success=True,
            character_name="Test",
            character_dna="dna",
            style_prompt="style",
            full_prompt="full",
            usage_hint="hint",
            evidence_refs=[
                "rag:auteur_dna:bong:visual:composition",
                "rag:auteur_dna:bong:audio:silence_usage",
                "rag:auteur_dna:bong:narrative:pacing",
            ],
        )
        # Cross-modal: visual, audio, narrative
        assert any("visual" in ref for ref in response.evidence_refs)
        assert any("audio" in ref for ref in response.evidence_refs)
        assert any("narrative" in ref for ref in response.evidence_refs)


# ============================================================================
# 2026 Enhancements Tests: Auteur Style Blending
# ============================================================================

class TestAuteurCompatibilityMatrix:
    """Test AUTEUR_COMPATIBILITY_MATRIX constant."""

    def test_matrix_has_expected_auteurs(self):
        """Test matrix contains key auteurs."""
        expected = {"bong", "nolan", "wong", "villeneuve", "tarantino", "miyazaki", "kubrick", "fincher"}
        actual = set(AUTEUR_COMPATIBILITY_MATRIX.keys())
        assert expected.issubset(actual)

    def test_matrix_values_are_valid(self):
        """Test all compatibility values are in valid range."""
        for primary, mappings in AUTEUR_COMPATIBILITY_MATRIX.items():
            for secondary, score in mappings.items():
                assert 0.0 <= score <= 1.0, f"{primary}-{secondary}: {score} out of range"

    def test_bong_nolan_compatibility(self):
        """Test Bong-Nolan compatibility is high."""
        assert AUTEUR_COMPATIBILITY_MATRIX["bong"]["nolan"] >= 0.7

    def test_nolan_villeneuve_compatibility(self):
        """Test Nolan-Villeneuve compatibility is very high."""
        assert AUTEUR_COMPATIBILITY_MATRIX["nolan"]["villeneuve"] >= 0.85


class TestAuteurVisualKeywords:
    """Test AUTEUR_VISUAL_KEYWORDS constant."""

    def test_keywords_has_expected_auteurs(self):
        """Test keywords contains key auteurs."""
        expected = {"bong", "nolan", "wong", "villeneuve", "tarantino", "miyazaki", "kubrick", "fincher"}
        actual = set(AUTEUR_VISUAL_KEYWORDS.keys())
        assert expected.issubset(actual)

    def test_keywords_are_lists(self):
        """Test all keyword values are lists."""
        for auteur, keywords in AUTEUR_VISUAL_KEYWORDS.items():
            assert isinstance(keywords, list), f"{auteur} keywords not a list"
            assert len(keywords) >= 3, f"{auteur} should have at least 3 keywords"

    def test_bong_keywords_contain_expected(self):
        """Test Bong keywords contain expected terms."""
        bong_keywords = AUTEUR_VISUAL_KEYWORDS["bong"]
        assert "class symbolism" in bong_keywords or any("class" in kw for kw in bong_keywords)

    def test_nolan_keywords_contain_expected(self):
        """Test Nolan keywords contain expected terms."""
        nolan_keywords = AUTEUR_VISUAL_KEYWORDS["nolan"]
        assert "IMAX scale" in nolan_keywords or any("imax" in kw.lower() for kw in nolan_keywords)

    def test_keywords_align_with_compatibility_matrix(self):
        """Regression test for P3 issue: all compatibility matrix auteurs must have keywords.

        AUTEUR_VISUAL_KEYWORDS must have entries for all auteurs in AUTEUR_COMPATIBILITY_MATRIX.
        """
        # Collect all auteurs from compatibility matrix
        matrix_auteurs = set()
        for primary, secondaries in AUTEUR_COMPATIBILITY_MATRIX.items():
            matrix_auteurs.add(primary)
            matrix_auteurs.update(secondaries.keys())

        # All matrix auteurs should have keyword entries
        keywords_auteurs = set(AUTEUR_VISUAL_KEYWORDS.keys())
        missing = matrix_auteurs - keywords_auteurs
        assert len(missing) == 0, f"Missing keywords for: {missing}"

    def test_spielberg_keywords_exist(self):
        """Test Spielberg keywords exist (previously missing)."""
        assert "spielberg" in AUTEUR_VISUAL_KEYWORDS
        assert len(AUTEUR_VISUAL_KEYWORDS["spielberg"]) >= 3

    def test_cameron_keywords_exist(self):
        """Test Cameron keywords exist (previously missing)."""
        assert "cameron" in AUTEUR_VISUAL_KEYWORDS
        assert any("blue" in kw.lower() for kw in AUTEUR_VISUAL_KEYWORDS["cameron"])

    def test_shinkai_keywords_exist(self):
        """Test Shinkai keywords exist (previously missing)."""
        assert "shinkai" in AUTEUR_VISUAL_KEYWORDS
        assert any("background" in kw.lower() or "light" in kw.lower() for kw in AUTEUR_VISUAL_KEYWORDS["shinkai"])

    def test_blend_with_spielberg_has_keywords(self):
        """Test blending with Spielberg now returns visual keywords."""
        result = blend_auteur_styles("spielberg", "cameron")
        assert len(result.visual_keywords) >= 2
        assert result.compatibility_score > 0


class TestGetAuteurCompatibility:
    """Test get_auteur_compatibility function."""

    def test_same_auteur_returns_1(self):
        """Test same auteur has perfect compatibility."""
        assert get_auteur_compatibility("bong", "bong") == 1.0
        assert get_auteur_compatibility("nolan", "nolan") == 1.0

    def test_known_pair_returns_score(self):
        """Test known pair returns correct score."""
        score = get_auteur_compatibility("bong", "nolan")
        assert score == AUTEUR_COMPATIBILITY_MATRIX["bong"]["nolan"]

    def test_reverse_order_same_score(self):
        """Test reverse order returns same score."""
        score1 = get_auteur_compatibility("bong", "fincher")
        score2 = get_auteur_compatibility("fincher", "bong")
        assert score1 == score2

    def test_unknown_pair_returns_default(self):
        """Test unknown pair returns default 0.5."""
        score = get_auteur_compatibility("unknown_director", "another_unknown")
        assert score == 0.5

    def test_case_insensitive(self):
        """Test function is case insensitive."""
        score1 = get_auteur_compatibility("Bong", "NOLAN")
        score2 = get_auteur_compatibility("bong", "nolan")
        assert score1 == score2


class TestBlendAuteurStyles:
    """Test blend_auteur_styles function."""

    def test_blend_returns_auteur_blend_result(self):
        """Test blend returns AuteurBlendResult."""
        result = blend_auteur_styles("bong", "nolan")
        assert isinstance(result, AuteurBlendResult)

    def test_blend_has_correct_auteurs(self):
        """Test result has correct auteur names."""
        result = blend_auteur_styles("bong", "nolan")
        assert result.primary_auteur == "bong"
        assert result.secondary_auteur == "nolan"

    def test_blend_has_compatibility_score(self):
        """Test result has valid compatibility score."""
        result = blend_auteur_styles("bong", "nolan")
        assert 0.0 <= result.compatibility_score <= 1.0
        assert result.compatibility_score == get_auteur_compatibility("bong", "nolan")

    def test_blend_has_visual_keywords(self):
        """Test result has visual keywords from both auteurs."""
        result = blend_auteur_styles("bong", "nolan")
        assert len(result.visual_keywords) >= 2

    def test_blend_ratio_default_60_40(self):
        """Test default blend ratio is 60:40."""
        result = blend_auteur_styles("bong", "nolan")
        assert result.blend_ratio == "60:40"

    def test_blend_ratio_custom_weight(self):
        """Test custom weight produces correct ratio."""
        result = blend_auteur_styles("bong", "nolan", primary_weight=0.7)
        assert result.blend_ratio == "70:30"

    def test_high_compatibility_has_seamless_blend(self):
        """Test high compatibility produces seamless blend approach."""
        result = blend_auteur_styles("nolan", "villeneuve")  # 0.90 compatibility
        assert "seamless" in result.color_approach.lower() or result.compatibility_score >= 0.8

    def test_low_compatibility_has_separate_zones(self):
        """Test low compatibility suggests separate zones."""
        result = blend_auteur_styles("bong", "tarantino")  # 0.45 compatibility
        assert "separate" in result.color_approach.lower() or "zone" in result.color_approach.lower()

    def test_recommended_for_includes_entries(self):
        """Test recommended_for has suggestions."""
        result = blend_auteur_styles("bong", "nolan")
        assert len(result.recommended_for) >= 1

    def test_case_insensitive_auteurs(self):
        """Test function handles case variations."""
        result1 = blend_auteur_styles("Bong", "NOLAN")
        result2 = blend_auteur_styles("bong", "nolan")
        assert result1.compatibility_score == result2.compatibility_score


# ============================================================================
# 2026 Enhancements Tests: Mathematical Aesthetics
# ============================================================================

class TestGoldenRatioConstant:
    """Test GOLDEN_RATIO constant."""

    def test_golden_ratio_value(self):
        """Test golden ratio has correct value."""
        assert abs(GOLDEN_RATIO - 1.618033988749895) < 0.0001

    def test_golden_ratio_property(self):
        """Test golden ratio satisfies φ = 1 + 1/φ."""
        assert abs(GOLDEN_RATIO - (1 + 1 / GOLDEN_RATIO)) < 0.0001


class TestColorHarmonyAngles:
    """Test COLOR_HARMONY_ANGLES constant."""

    def test_complementary_is_180(self):
        """Test complementary is 180 degrees."""
        assert COLOR_HARMONY_ANGLES["complementary"] == [180]

    def test_triadic_is_120_240(self):
        """Test triadic is 120 and 240 degrees."""
        assert COLOR_HARMONY_ANGLES["triadic"] == [120, 240]

    def test_analogous_is_30_minus30(self):
        """Test analogous is +30 and -30 degrees."""
        assert COLOR_HARMONY_ANGLES["analogous"] == [30, -30]

    def test_split_complementary_exists(self):
        """Test split_complementary harmony exists."""
        assert "split_complementary" in COLOR_HARMONY_ANGLES

    def test_tetradic_has_four_points(self):
        """Test tetradic has 3 angles (4 colors total with base)."""
        assert len(COLOR_HARMONY_ANGLES["tetradic"]) == 3


class TestCalculateGoldenRatioPoints:
    """Test calculate_golden_ratio_points function."""

    def test_returns_dict(self):
        """Test function returns dict."""
        result = calculate_golden_ratio_points(1920, 1080)
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        """Test result has all required keys."""
        result = calculate_golden_ratio_points(1920, 1080)
        required = {"golden_ratio", "vertical_lines", "horizontal_lines", "power_points", "center", "thirds_grid"}
        assert required.issubset(result.keys())

    def test_1920x1080_vertical_lines(self):
        """Test 1920x1080 vertical lines are approximately correct."""
        result = calculate_golden_ratio_points(1920, 1080)
        v_lines = result["vertical_lines"]
        # φ^-1 ≈ 0.618, so lines at ~38.2% and ~61.8%
        assert v_lines[0] < 1920 // 2  # Left of center
        assert v_lines[1] > 1920 // 2  # Right of center
        assert 700 < v_lines[0] < 800   # ~38.2% of 1920 ≈ 734
        assert 1100 < v_lines[1] < 1250  # ~61.8% of 1920 ≈ 1186

    def test_power_points_count(self):
        """Test there are 4 power points (intersections)."""
        result = calculate_golden_ratio_points(1920, 1080)
        assert len(result["power_points"]) == 4

    def test_power_points_are_tuples(self):
        """Test power points are coordinate tuples."""
        result = calculate_golden_ratio_points(1920, 1080)
        for point in result["power_points"]:
            assert isinstance(point, tuple)
            assert len(point) == 2

    def test_center_is_correct(self):
        """Test center is calculated correctly."""
        result = calculate_golden_ratio_points(1920, 1080)
        assert result["center"] == (960, 540)

    def test_thirds_grid_exists(self):
        """Test thirds grid is included."""
        result = calculate_golden_ratio_points(1920, 1080)
        thirds = result["thirds_grid"]
        assert "vertical" in thirds
        assert "horizontal" in thirds
        assert len(thirds["vertical"]) == 2
        assert len(thirds["horizontal"]) == 2


class TestGetColorHarmonyPalette:
    """Test get_color_harmony_palette function."""

    def test_complementary_returns_two_hues(self):
        """Test complementary returns 2 hues."""
        palette = get_color_harmony_palette(0, "complementary")
        assert len(palette) == 2

    def test_complementary_180_apart(self):
        """Test complementary hues are 180 degrees apart."""
        palette = get_color_harmony_palette(0, "complementary")
        assert palette[0] == 0
        assert palette[1] == 180

    def test_triadic_returns_three_hues(self):
        """Test triadic returns 3 hues."""
        palette = get_color_harmony_palette(0, "triadic")
        assert len(palette) == 3

    def test_analogous_returns_three_hues(self):
        """Test analogous returns 3 hues."""
        palette = get_color_harmony_palette(0, "analogous")
        assert len(palette) == 3

    def test_tetradic_returns_four_hues(self):
        """Test tetradic returns 4 hues."""
        palette = get_color_harmony_palette(0, "tetradic")
        assert len(palette) == 4

    def test_hue_wrapping(self):
        """Test hues wrap around 360."""
        palette = get_color_harmony_palette(350, "complementary")
        assert palette[0] == 350
        assert palette[1] == (350 + 180) % 360  # 170

    def test_invalid_type_defaults_to_complementary(self):
        """Test invalid harmony type defaults to complementary."""
        palette = get_color_harmony_palette(0, "invalid_type")
        assert len(palette) == 2  # complementary

    def test_base_hue_always_first(self):
        """Test base hue is always first in palette."""
        for base in [0, 90, 180, 270]:
            for harmony in COLOR_HARMONY_ANGLES.keys():
                palette = get_color_harmony_palette(base, harmony)
                assert palette[0] == base


# ============================================================================
# 2026 Enhancements Tests: Prompt Quality Assessment
# ============================================================================

class TestAestheticPromptQualityModel:
    """Test AestheticPromptQuality model."""

    def test_model_creation(self):
        """Test model creation with defaults."""
        quality = AestheticPromptQuality()
        assert quality.concept_clarity == 0
        assert quality.style_specificity == 0
        assert quality.technical_detail == 0
        assert quality.overall_score == 0

    def test_model_with_scores(self):
        """Test model with scores."""
        quality = AestheticPromptQuality(
            concept_clarity=80,
            style_specificity=75,
            technical_detail=70,
            overall_score=75,
        )
        assert quality.concept_clarity == 80
        assert quality.overall_score == 75

    def test_boolean_flags(self):
        """Test boolean component flags."""
        quality = AestheticPromptQuality(
            has_auteur_reference=True,
            has_color_specification=True,
            has_lighting_specification=False,
            has_composition_hint=True,
        )
        assert quality.has_auteur_reference is True
        assert quality.has_lighting_specification is False

    def test_suggestions_list(self):
        """Test suggestions is list."""
        quality = AestheticPromptQuality(
            suggestions=["Add auteur", "Specify lighting"],
        )
        assert len(quality.suggestions) == 2

    def test_score_bounds(self):
        """Test scores are bounded 0-100."""
        with pytest.raises(ValidationError):
            AestheticPromptQuality(concept_clarity=101)
        with pytest.raises(ValidationError):
            AestheticPromptQuality(concept_clarity=-1)


class TestAssessAestheticPromptQuality:
    """Test assess_aesthetic_prompt_quality function."""

    def test_empty_concept_low_score(self):
        """Test empty concept gets low score."""
        result = assess_aesthetic_prompt_quality("")
        assert result.concept_clarity == 0
        assert result.overall_score < 30

    def test_short_concept_suggests_more_detail(self):
        """Test short concept suggests more detail."""
        result = assess_aesthetic_prompt_quality("A tree")
        assert any("detail" in s.lower() for s in result.suggestions)

    def test_detailed_concept_higher_score(self):
        """Test detailed concept gets higher score."""
        short_result = assess_aesthetic_prompt_quality("A scene")
        detailed_result = assess_aesthetic_prompt_quality(
            "A wide shot composition of a character standing in a dramatic landscape with layered framing"
        )
        assert detailed_result.concept_clarity > short_result.concept_clarity

    def test_auteur_reference_increases_score(self):
        """Test auteur reference increases style score."""
        without_auteur = assess_aesthetic_prompt_quality("A scene")
        with_auteur = assess_aesthetic_prompt_quality("A scene", reference_style="bong")
        assert with_auteur.style_specificity > without_auteur.style_specificity
        assert with_auteur.has_auteur_reference is True

    def test_known_auteur_higher_than_unknown(self):
        """Test known auteur scores higher than unknown."""
        known = assess_aesthetic_prompt_quality("A scene", reference_style="bong")
        unknown = assess_aesthetic_prompt_quality("A scene", reference_style="unknown_director")
        assert known.style_specificity >= unknown.style_specificity

    def test_lighting_specification_detected(self):
        """Test lighting specification is detected."""
        result = assess_aesthetic_prompt_quality(
            "A scene",
            lighting_style="dramatic"
        )
        assert result.has_lighting_specification is True

    def test_color_specification_detected(self):
        """Test color specification is detected."""
        result = assess_aesthetic_prompt_quality(
            "A scene",
            color_mood="warm"
        )
        assert result.has_color_specification is True

    def test_full_prompt_high_score(self):
        """Test fully specified prompt gets high score."""
        result = assess_aesthetic_prompt_quality(
            concept="A wide composition shot of a character silhouette against a dramatic landscape with layered framing and foreground elements",
            reference_style="bong",
            mood="cinematic and moody",
            lighting_style="dramatic",
            color_mood="desaturated",
        )
        assert result.overall_score >= 70
        assert result.has_auteur_reference is True
        assert result.has_lighting_specification is True
        assert result.has_color_specification is True

    def test_no_auteur_suggests_auteur(self):
        """Test missing auteur generates suggestion."""
        result = assess_aesthetic_prompt_quality("A scene")
        assert any("auteur" in s.lower() for s in result.suggestions)

    def test_visual_keywords_increase_clarity(self):
        """Test visual keywords increase concept clarity."""
        without_keywords = assess_aesthetic_prompt_quality("A person in a room")
        with_keywords = assess_aesthetic_prompt_quality("A wide shot composition of a character in perspective")
        assert with_keywords.concept_clarity > without_keywords.concept_clarity

    def test_subject_keywords_increase_clarity(self):
        """Test subject keywords increase concept clarity."""
        vague = assess_aesthetic_prompt_quality("Something happening somewhere")
        specific = assess_aesthetic_prompt_quality("A character standing in an interior")
        assert specific.concept_clarity > vague.concept_clarity


class TestAuteurBlendResultModel:
    """Test AuteurBlendResult model."""

    def test_model_creation(self):
        """Test model creation."""
        result = AuteurBlendResult(
            primary_auteur="bong",
            secondary_auteur="nolan",
            compatibility_score=0.75,
            blend_ratio="60:40",
            visual_keywords=["layered framing", "IMAX scale"],
            color_approach="Seamless blend",
            composition_approach="Primary rules",
            recommended_for=["feature film"],
        )
        assert result.primary_auteur == "bong"
        assert result.compatibility_score == 0.75

    def test_compatibility_score_bounds(self):
        """Test compatibility score is bounded 0-1."""
        with pytest.raises(ValidationError):
            AuteurBlendResult(
                primary_auteur="test",
                secondary_auteur="test2",
                compatibility_score=1.5,
            )

    def test_default_values(self):
        """Test default values."""
        result = AuteurBlendResult(
            primary_auteur="test",
            secondary_auteur="test2",
        )
        assert result.compatibility_score == 0.0
        assert result.blend_ratio == "60:40"
        assert result.visual_keywords == []
        assert result.recommended_for == []
