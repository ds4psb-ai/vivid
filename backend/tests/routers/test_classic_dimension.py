"""
Tests for Classic Dimension Endpoints (1D, 2D, 3D, 4D).

Tests include:
- XSS sanitization for style/mood fields
- Enum validation for analysis_depth/output_format/strategy
- Focus areas whitelist validation
- Edge case inputs
"""
import pytest
from pydantic import ValidationError

from app.routers.dimension.classic import (
    # Enums
    AnalysisDepth,
    OutputFormat,
    UQSLStrategy,
    # Constants
    ALLOWED_FOCUS_AREAS,
    DEFAULT_FOCUS_AREAS,
    # Request models
    PromptGenerateRequest,
    StoryboardCreateRequest,
    ImageGenerateRequest,
    ReferenceAnalyzeRequest,
    PromptMultiGenerateRequest,
    # Helpers
    _sanitize_style_mood,
    _validate_analysis_depth,
    _validate_output_format,
    _validate_focus_areas,
    _validate_strategy,
)


# ============================================================================
# Enums Tests
# ============================================================================

class TestAnalysisDepthEnum:
    """Test AnalysisDepth enum values."""

    def test_all_depths_defined(self):
        """Verify all expected depths are defined."""
        depths = [d.value for d in AnalysisDepth]
        assert "quick" in depths
        assert "standard" in depths
        assert "deep" in depths

    def test_enum_count(self):
        """Verify exactly 3 depths."""
        assert len(AnalysisDepth) == 3


class TestOutputFormatEnum:
    """Test OutputFormat enum values."""

    def test_all_formats_defined(self):
        """Verify all expected formats are defined."""
        formats = [f.value for f in OutputFormat]
        assert "structured" in formats
        assert "narrative" in formats
        assert "bullet" in formats

    def test_enum_count(self):
        """Verify exactly 3 formats."""
        assert len(OutputFormat) == 3


class TestUQSLStrategyEnum:
    """Test UQSLStrategy enum values."""

    def test_all_strategies_defined(self):
        """Verify all expected strategies are defined."""
        strategies = [s.value for s in UQSLStrategy]
        assert "auto" in strategies
        assert "quality" in strategies
        assert "hitl" in strategies

    def test_enum_count(self):
        """Verify exactly 3 strategies."""
        assert len(UQSLStrategy) == 3


class TestFocusAreasConstants:
    """Test focus areas constants."""

    def test_allowed_areas_count(self):
        """Verify reasonable number of allowed areas."""
        assert len(ALLOWED_FOCUS_AREAS) >= 10

    def test_default_areas_subset(self):
        """Verify default areas are subset of allowed."""
        for area in DEFAULT_FOCUS_AREAS:
            assert area in ALLOWED_FOCUS_AREAS

    def test_expected_areas_present(self):
        """Verify expected areas are in allowed list."""
        expected = ["cinematography", "editing", "color", "sound", "lighting"]
        for area in expected:
            assert area in ALLOWED_FOCUS_AREAS


# ============================================================================
# Sanitization Helpers Tests
# ============================================================================

class TestSanitizeStyleMood:
    """Test _sanitize_style_mood helper."""

    def test_removes_html_tags(self):
        """Test HTML tag removal."""
        result = _sanitize_style_mood("<div>cinematic</div>")
        assert "<div>" not in result
        assert "</div>" not in result

    def test_removes_script_tags(self):
        """Test script tag removal."""
        result = _sanitize_style_mood("<script>evil()</script>test")
        assert "<script>" not in result
        assert "</script>" not in result

    def test_removes_javascript_protocol(self):
        """Test javascript: protocol removal."""
        result = _sanitize_style_mood("javascript:alert(1)")
        assert "javascript:" not in result.lower()

    def test_removes_event_handlers(self):
        """Test on* event handler removal."""
        result = _sanitize_style_mood("onload=alert(1)cinematic")
        assert "onload=" not in result.lower()
        result2 = _sanitize_style_mood("onerror=evil()noir")
        assert "onerror=" not in result2.lower()

    def test_empty_returns_default(self):
        """Test empty string returns default."""
        assert _sanitize_style_mood("") == "cinematic"
        assert _sanitize_style_mood("   ") == "cinematic"
        assert _sanitize_style_mood("", default="noir") == "noir"

    def test_preserves_korean(self):
        """Test Korean characters preserved."""
        result = _sanitize_style_mood("시네마틱 느와르")
        assert "시네마틱" in result
        assert "느와르" in result

    def test_limits_length(self):
        """Test length limit of 100 chars."""
        long_input = "a" * 200
        result = _sanitize_style_mood(long_input)
        assert len(result) <= 100


class TestValidateAnalysisDepth:
    """Test _validate_analysis_depth helper."""

    def test_valid_depths(self):
        """Test all valid depths pass."""
        assert _validate_analysis_depth("quick") == "quick"
        assert _validate_analysis_depth("standard") == "standard"
        assert _validate_analysis_depth("deep") == "deep"

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert _validate_analysis_depth("QUICK") == "quick"
        assert _validate_analysis_depth("Standard") == "standard"

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        assert _validate_analysis_depth("  deep  ") == "deep"

    def test_invalid_raises(self):
        """Test invalid depth raises ValueError."""
        with pytest.raises(ValueError, match="Invalid analysis_depth"):
            _validate_analysis_depth("invalid")
        with pytest.raises(ValueError, match="Invalid analysis_depth"):
            _validate_analysis_depth("medium")


class TestValidateOutputFormat:
    """Test _validate_output_format helper."""

    def test_valid_formats(self):
        """Test all valid formats pass."""
        assert _validate_output_format("structured") == "structured"
        assert _validate_output_format("narrative") == "narrative"
        assert _validate_output_format("bullet") == "bullet"

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert _validate_output_format("STRUCTURED") == "structured"

    def test_invalid_raises(self):
        """Test invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid output_format"):
            _validate_output_format("json")


class TestValidateFocusAreas:
    """Test _validate_focus_areas helper."""

    def test_valid_areas(self):
        """Test valid areas pass."""
        result = _validate_focus_areas(["cinematography", "editing"])
        assert result == ["cinematography", "editing"]

    def test_empty_returns_default(self):
        """Test empty list returns default."""
        result = _validate_focus_areas([])
        assert result == DEFAULT_FOCUS_AREAS

    def test_deduplicates(self):
        """Test duplicate removal."""
        result = _validate_focus_areas(["color", "color", "sound"])
        assert result == ["color", "sound"]

    def test_normalizes(self):
        """Test normalization (lowercase, underscore)."""
        result = _validate_focus_areas(["Production Design", "VFX"])
        assert "production_design" in result
        assert "vfx" in result

    def test_invalid_raises(self):
        """Test invalid area raises ValueError."""
        with pytest.raises(ValueError, match="Invalid focus_areas"):
            _validate_focus_areas(["cinematography", "invalid_area"])


class TestValidateStrategy:
    """Test _validate_strategy helper."""

    def test_valid_strategies(self):
        """Test all valid strategies pass."""
        assert _validate_strategy("auto") == "auto"
        assert _validate_strategy("quality") == "quality"
        assert _validate_strategy("hitl") == "hitl"

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert _validate_strategy("AUTO") == "auto"

    def test_invalid_raises(self):
        """Test invalid strategy raises ValueError."""
        with pytest.raises(ValueError, match="Invalid strategy"):
            _validate_strategy("random")


# ============================================================================
# Request Model Tests - PromptGenerateRequest (1D)
# ============================================================================

class TestPromptGenerateRequest:
    """Test PromptGenerateRequest (1D Origin)."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = PromptGenerateRequest(
            topic="A sunset over mountains",
            style="cinematic",
            mood="peaceful",
        )
        assert request.topic == "A sunset over mountains"
        assert request.style == "cinematic"
        assert request.mood == "peaceful"

    def test_style_sanitization(self):
        """Test style XSS sanitization."""
        request = PromptGenerateRequest(
            topic="A sunset over mountains",
            style="<script>alert('xss')</script>cinematic",
        )
        assert "<script>" not in request.style
        assert "cinematic" in request.style

    def test_mood_sanitization(self):
        """Test mood XSS sanitization."""
        request = PromptGenerateRequest(
            topic="A sunset over mountains",
            mood="javascript:alert(1)",
        )
        assert "javascript:" not in request.mood.lower()

    def test_empty_style_defaults(self):
        """Test empty style defaults to cinematic."""
        request = PromptGenerateRequest(
            topic="A sunset over mountains",
            style="",
        )
        assert request.style == "cinematic"

    def test_empty_mood_defaults(self):
        """Test empty mood defaults to neutral."""
        request = PromptGenerateRequest(
            topic="A sunset over mountains",
            mood="",
        )
        assert request.mood == "neutral"

    def test_duration_boundaries(self):
        """Test duration boundary values."""
        # Min
        request_min = PromptGenerateRequest(topic="Test", duration=4)
        assert request_min.duration == 4
        # Max
        request_max = PromptGenerateRequest(topic="Test", duration=8)
        assert request_max.duration == 8

    def test_duration_below_min(self):
        """Test duration below minimum fails."""
        with pytest.raises(ValidationError):
            PromptGenerateRequest(topic="Test", duration=3)

    def test_duration_above_max(self):
        """Test duration above maximum fails."""
        with pytest.raises(ValidationError):
            PromptGenerateRequest(topic="Test", duration=9)

    def test_topic_with_unicode(self):
        """Test Korean and emoji in topic."""
        request = PromptGenerateRequest(
            topic="밤하늘 아래 걷는 두 연인 🌙✨"
        )
        assert "밤하늘" in request.topic
        assert "🌙" in request.topic


# ============================================================================
# Request Model Tests - StoryboardCreateRequest (2D)
# ============================================================================

class TestStoryboardCreateRequest:
    """Test StoryboardCreateRequest (2D Blueprint)."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = StoryboardCreateRequest(
            concept="A hero's journey through a mystical forest",
            scene_count=6,
        )
        assert "hero's journey" in request.concept
        assert request.scene_count == 6

    def test_scene_count_boundaries(self):
        """Test scene_count boundary values."""
        # Defaults from _base constants
        request = StoryboardCreateRequest(concept="Test")
        assert request.scene_count >= 1

    def test_concept_whitespace_strip(self):
        """Test concept whitespace stripping."""
        request = StoryboardCreateRequest(
            concept="  A story concept  "
        )
        assert request.concept == "A story concept"


# ============================================================================
# Request Model Tests - ImageGenerateRequest (3D)
# ============================================================================

class TestImageGenerateRequest:
    """Test ImageGenerateRequest (3D Ambience)."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = ImageGenerateRequest(
            description="A serene lake at dawn with mist rising",
            style="photorealistic",
            aspect_ratio="16:9",
        )
        assert "serene lake" in request.description
        assert request.style == "photorealistic"

    def test_style_sanitization(self):
        """Test style XSS sanitization."""
        request = ImageGenerateRequest(
            description="A serene lake at dawn",
            style="<img onerror=alert(1)>artistic",
        )
        assert "<img" not in request.style
        assert "onerror" not in request.style

    def test_empty_style_defaults(self):
        """Test empty style defaults to photorealistic."""
        request = ImageGenerateRequest(
            description="A serene lake at dawn",
            style="",
        )
        assert request.style == "photorealistic"


# ============================================================================
# Request Model Tests - ReferenceAnalyzeRequest (4D)
# ============================================================================

class TestReferenceAnalyzeRequest:
    """Test ReferenceAnalyzeRequest (4D Moment)."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = ReferenceAnalyzeRequest(
            video_description="A long tracking shot in Goodfellas",
            focus_areas=["cinematography", "editing"],
            analysis_depth="deep",
            output_format="structured",
        )
        assert "Goodfellas" in request.video_description
        assert request.focus_areas == ["cinematography", "editing"]
        assert request.analysis_depth == "deep"
        assert request.output_format == "structured"

    def test_focus_areas_validation(self):
        """Test focus_areas whitelist validation."""
        with pytest.raises(ValidationError):
            ReferenceAnalyzeRequest(
                video_description="A long tracking shot",
                focus_areas=["invalid_area"],
            )

    def test_focus_areas_default(self):
        """Test focus_areas defaults to DEFAULT_FOCUS_AREAS."""
        request = ReferenceAnalyzeRequest(
            video_description="A long tracking shot",
        )
        assert request.focus_areas == DEFAULT_FOCUS_AREAS

    def test_analysis_depth_validation(self):
        """Test analysis_depth enum validation."""
        with pytest.raises(ValidationError):
            ReferenceAnalyzeRequest(
                video_description="A long tracking shot",
                analysis_depth="invalid",
            )

    def test_output_format_validation(self):
        """Test output_format enum validation."""
        with pytest.raises(ValidationError):
            ReferenceAnalyzeRequest(
                video_description="A long tracking shot",
                output_format="json",
            )

    def test_focus_areas_deduplication(self):
        """Test focus_areas deduplication."""
        request = ReferenceAnalyzeRequest(
            video_description="A long tracking shot",
            focus_areas=["color", "color", "sound"],
        )
        assert request.focus_areas == ["color", "sound"]

    def test_focus_areas_normalization(self):
        """Test focus_areas normalization."""
        request = ReferenceAnalyzeRequest(
            video_description="A long tracking shot",
            focus_areas=["Production Design", "VFX"],
        )
        assert "production_design" in request.focus_areas
        assert "vfx" in request.focus_areas


# ============================================================================
# Request Model Tests - PromptMultiGenerateRequest (1D UQSL)
# ============================================================================

class TestPromptMultiGenerateRequest:
    """Test PromptMultiGenerateRequest (1D UQSL)."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = PromptMultiGenerateRequest(
            topic="A chase scene through city streets",
            n_candidates=3,
            strategy="auto",
        )
        assert "chase scene" in request.topic
        assert request.n_candidates == 3
        assert request.strategy == "auto"

    def test_style_sanitization(self):
        """Test style XSS sanitization."""
        request = PromptMultiGenerateRequest(
            topic="A chase scene",
            style="<script>alert('xss')</script>action",
        )
        assert "<script>" not in request.style

    def test_mood_sanitization(self):
        """Test mood XSS sanitization."""
        request = PromptMultiGenerateRequest(
            topic="A chase scene",
            mood="onmouseover=evil()",
        )
        assert "onmouseover" not in request.mood.lower()

    def test_strategy_validation(self):
        """Test strategy enum validation."""
        with pytest.raises(ValidationError):
            PromptMultiGenerateRequest(
                topic="A chase scene",
                strategy="invalid_strategy",
            )

    def test_n_candidates_boundaries(self):
        """Test n_candidates boundary values."""
        # Min
        request_min = PromptMultiGenerateRequest(topic="Test", n_candidates=2)
        assert request_min.n_candidates == 2
        # Max
        request_max = PromptMultiGenerateRequest(topic="Test", n_candidates=5)
        assert request_max.n_candidates == 5

    def test_n_candidates_below_min(self):
        """Test n_candidates below minimum fails."""
        with pytest.raises(ValidationError):
            PromptMultiGenerateRequest(topic="Test", n_candidates=1)

    def test_n_candidates_above_max(self):
        """Test n_candidates above maximum fails."""
        with pytest.raises(ValidationError):
            PromptMultiGenerateRequest(topic="Test", n_candidates=6)


# ============================================================================
# Security Tests - XSS Prevention
# ============================================================================

class TestXSSPrevention:
    """Test XSS attack prevention across all models."""

    @pytest.mark.parametrize("attack_vector", [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(document.cookie)",
        "<svg onload=alert(1)>",
        "<<script>alert(1)</script>",
        "<body onload=alert(1)>",
    ])
    def test_1d_style_xss(self, attack_vector):
        """Test 1D style field XSS prevention."""
        request = PromptGenerateRequest(
            topic="Test",
            style=attack_vector + "cinematic",
        )
        # Verify dangerous patterns removed
        assert "<script>" not in request.style.lower()
        assert "onerror" not in request.style.lower()
        assert "onload" not in request.style.lower()
        assert "javascript:" not in request.style.lower()

    @pytest.mark.parametrize("attack_vector", [
        "<script>alert('xss')</script>",
        "onmouseover=evil()",
        "javascript:void(0)",
    ])
    def test_1d_mood_xss(self, attack_vector):
        """Test 1D mood field XSS prevention."""
        request = PromptGenerateRequest(
            topic="Test",
            mood=attack_vector + "neutral",
        )
        assert "<script>" not in request.mood.lower()
        assert "onmouseover" not in request.mood.lower()
        assert "javascript:" not in request.mood.lower()

    @pytest.mark.parametrize("attack_vector", [
        "<div onclick=alert(1)>",
        "<iframe src='evil.com'>",
    ])
    def test_3d_style_xss(self, attack_vector):
        """Test 3D style field XSS prevention."""
        request = ImageGenerateRequest(
            description="Test description here",
            style=attack_vector + "artistic",
        )
        assert "<div" not in request.style.lower()
        assert "<iframe" not in request.style.lower()
        assert "onclick" not in request.style.lower()


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_minimum_topic_length(self):
        """Test minimum topic length (1 char)."""
        request = PromptGenerateRequest(topic="A")
        assert request.topic == "A"

    def test_empty_topic_fails(self):
        """Test empty topic fails validation."""
        with pytest.raises(ValidationError):
            PromptGenerateRequest(topic="")

    def test_whitespace_only_topic_fails(self):
        """Test whitespace-only topic fails (after strip)."""
        with pytest.raises(ValidationError):
            PromptGenerateRequest(topic="   ")

    def test_special_characters_in_description(self):
        """Test special characters in descriptions."""
        request = ReferenceAnalyzeRequest(
            video_description="Scene #1: [CUT TO] - Another scene! @timestamp:00:15"
        )
        assert "#1" in request.video_description
        assert "[CUT TO]" in request.video_description

    def test_all_valid_strategies(self):
        """Test all valid strategies work."""
        for strategy in ["auto", "quality", "hitl"]:
            request = PromptMultiGenerateRequest(
                topic="Test",
                strategy=strategy,
            )
            assert request.strategy == strategy

    def test_all_valid_depths(self):
        """Test all valid analysis depths work."""
        for depth in ["quick", "standard", "deep"]:
            request = ReferenceAnalyzeRequest(
                video_description="Test video",
                analysis_depth=depth,
            )
            assert request.analysis_depth == depth

    def test_all_valid_formats(self):
        """Test all valid output formats work."""
        for fmt in ["structured", "narrative", "bullet"]:
            request = ReferenceAnalyzeRequest(
                video_description="Test video",
                output_format=fmt,
            )
            assert request.output_format == fmt
