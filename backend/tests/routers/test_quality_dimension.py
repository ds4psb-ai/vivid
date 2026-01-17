"""
Tests for Quality Dimension Endpoints.

Tests include:
- XSS sanitization for content, context
- Enum validation for content_type, inspection_mode, criteria, persona
- Threshold normalization
- Edge case inputs
"""
import pytest
from pydantic import ValidationError

from app.routers.dimension.quality import (
    # Constants
    ALLOWED_CONTENT_TYPES,
    ALLOWED_INSPECTION_MODES,
    ALLOWED_CRITERIA,
    ALLOWED_PERSONAS,
    # Request models
    QualityCheckRequest,
    CreativeEditorRequest,
    # Helpers
    _sanitize_text_field,
    _validate_content_type,
    _validate_inspection_mode,
    _validate_criteria_list,
    _validate_persona,
)


# ============================================================================
# Sanitization Helpers Tests
# ============================================================================

class TestSanitizeTextField:
    """Test _sanitize_text_field helper."""

    def test_removes_html_tags(self):
        """Test HTML tag removal."""
        result = _sanitize_text_field("<div>content here</div>")
        assert "<div>" not in result
        assert "</div>" not in result
        assert "content here" in result

    def test_removes_script_tags(self):
        """Test script tag removal."""
        result = _sanitize_text_field("<script>evil()</script>content")
        assert "<script>" not in result
        assert "content" in result

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
        result = _sanitize_text_field("A quality prompt for video generation")
        assert "quality" in result
        assert "prompt" in result
        assert "video" in result

    def test_preserves_korean(self):
        """Test Korean characters preserved."""
        result = _sanitize_text_field("영상 품질을 검사합니다")
        assert "영상" in result
        assert "품질" in result
        assert "검사" in result

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

class TestValidateContentType:
    """Test _validate_content_type helper."""

    def test_valid_content_types(self):
        """Test all valid content types pass."""
        for ct in ALLOWED_CONTENT_TYPES:
            assert _validate_content_type(ct) == ct

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        assert _validate_content_type("  prompt  ") == "prompt"

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert _validate_content_type("PROMPT") == "prompt"
        assert _validate_content_type("Scenario") == "scenario"

    def test_invalid_content_type_raises(self):
        """Test invalid content_type raises ValueError."""
        with pytest.raises(ValueError, match="지원하지 않는 콘텐츠 타입"):
            _validate_content_type("invalid_type")
        with pytest.raises(ValueError, match="지원하지 않는 콘텐츠 타입"):
            _validate_content_type("blog")


class TestValidateInspectionMode:
    """Test _validate_inspection_mode helper."""

    def test_valid_modes(self):
        """Test all valid modes pass."""
        for mode in ALLOWED_INSPECTION_MODES:
            assert _validate_inspection_mode(mode) == mode

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        assert _validate_inspection_mode("  comprehensive  ") == "comprehensive"

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert _validate_inspection_mode("COMPREHENSIVE") == "comprehensive"
        assert _validate_inspection_mode("Quick") == "quick"

    def test_invalid_mode_raises(self):
        """Test invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="지원하지 않는 검수 모드"):
            _validate_inspection_mode("invalid_mode")
        with pytest.raises(ValueError, match="지원하지 않는 검수 모드"):
            _validate_inspection_mode("detailed")


class TestValidateCriteriaList:
    """Test _validate_criteria_list helper."""

    def test_valid_criteria(self):
        """Test all valid criteria pass."""
        for criterion in ALLOWED_CRITERIA:
            result = _validate_criteria_list([criterion])
            assert result == [criterion]

    def test_multiple_valid_criteria(self):
        """Test multiple valid criteria pass."""
        result = _validate_criteria_list(["aesthetic", "safety", "technical"])
        assert result == ["aesthetic", "safety", "technical"]

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        result = _validate_criteria_list(["  aesthetic  ", "  safety  "])
        assert result == ["aesthetic", "safety"]

    def test_case_insensitive(self):
        """Test case insensitivity."""
        result = _validate_criteria_list(["AESTHETIC", "Safety"])
        assert result == ["aesthetic", "safety"]

    def test_invalid_criterion_raises(self):
        """Test invalid criterion raises ValueError."""
        with pytest.raises(ValueError, match="지원하지 않는 평가 기준"):
            _validate_criteria_list(["aesthetic", "invalid_criterion"])


class TestValidatePersona:
    """Test _validate_persona helper."""

    def test_valid_personas(self):
        """Test all valid personas pass."""
        for persona in ALLOWED_PERSONAS:
            assert _validate_persona(persona) == persona

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        result = _validate_persona("  Senior Editor  ")
        assert result == "Senior Editor"

    def test_case_insensitive(self):
        """Test case insensitivity (returns original case)."""
        result = _validate_persona("senior editor")
        assert result == "Senior Editor"

    def test_invalid_persona_raises(self):
        """Test invalid persona raises ValueError."""
        with pytest.raises(ValueError, match="지원하지 않는 페르소나"):
            _validate_persona("Random Persona")


class TestAllowedConstantsVerification:
    """Test allowed constants."""

    def test_expected_content_types_present(self):
        """Verify expected content types are in allowed list."""
        expected = ["prompt", "scenario", "script", "description", "dialogue", "narration", "ad_copy"]
        for ct in expected:
            assert ct in ALLOWED_CONTENT_TYPES

    def test_expected_modes_present(self):
        """Verify expected modes are in allowed list."""
        expected = ["comprehensive", "quick", "cinematic", "consistency"]
        for mode in expected:
            assert mode in ALLOWED_INSPECTION_MODES

    def test_expected_criteria_present(self):
        """Verify expected criteria are in allowed list."""
        expected = ["aesthetic", "consistency", "safety", "technical", "narrative", "ad_suitability"]
        for criterion in expected:
            assert criterion in ALLOWED_CRITERIA

    def test_expected_personas_present(self):
        """Verify expected personas are in allowed list."""
        expected = ["Senior Editor", "Script Doctor", "Creative Director", "Copy Editor", "Story Analyst"]
        for persona in expected:
            assert persona in ALLOWED_PERSONAS


# ============================================================================
# QualityCheckRequest Tests
# ============================================================================

class TestQualityCheckRequest:
    """Test QualityCheckRequest model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = QualityCheckRequest(
            content="A high quality video prompt about nature",
            content_type="prompt",
            inspection_mode="comprehensive",
            threshold=70,
        )
        assert "high quality" in request.content
        assert request.content_type == "prompt"
        assert request.inspection_mode == "comprehensive"
        assert request.threshold == 70

    def test_default_values(self):
        """Test default values are applied."""
        request = QualityCheckRequest(
            content="Test content",
        )
        assert request.content_type == "prompt"
        assert request.inspection_mode == "comprehensive"
        assert request.threshold == 70
        assert request.criteria == ["aesthetic", "consistency", "safety"]
        assert request.model == "gemini-3-flash-preview"

    def test_content_sanitization(self):
        """Test content XSS sanitization."""
        request = QualityCheckRequest(
            content="<script>alert('xss')</script>real content",
        )
        assert "<script>" not in request.content
        assert "real content" in request.content

    def test_content_type_validation(self):
        """Test content_type validation."""
        for ct in ALLOWED_CONTENT_TYPES:
            request = QualityCheckRequest(content="Test", content_type=ct)
            assert request.content_type == ct

    def test_invalid_content_type_fails(self):
        """Test invalid content_type fails validation."""
        with pytest.raises(ValidationError):
            QualityCheckRequest(content="Test", content_type="invalid")

    def test_inspection_mode_validation(self):
        """Test inspection_mode validation."""
        for mode in ALLOWED_INSPECTION_MODES:
            request = QualityCheckRequest(content="Test", inspection_mode=mode)
            assert request.inspection_mode == mode

    def test_invalid_inspection_mode_fails(self):
        """Test invalid inspection_mode fails validation."""
        with pytest.raises(ValidationError):
            QualityCheckRequest(content="Test", inspection_mode="invalid")

    def test_criteria_validation(self):
        """Test criteria validation."""
        request = QualityCheckRequest(
            content="Test",
            criteria=["aesthetic", "safety"],
        )
        assert request.criteria == ["aesthetic", "safety"]

    def test_invalid_criteria_fails(self):
        """Test invalid criteria fails validation."""
        with pytest.raises(ValidationError):
            QualityCheckRequest(content="Test", criteria=["invalid_criterion"])

    def test_threshold_bounds(self):
        """Test threshold min/max bounds."""
        # Valid minimum
        request = QualityCheckRequest(content="Test", threshold=0)
        assert request.threshold == 0

        # Valid maximum
        request = QualityCheckRequest(content="Test", threshold=100)
        assert request.threshold == 100

    def test_threshold_normalization_decimal(self):
        """Test threshold normalization from 0-1 to 0-100."""
        request = QualityCheckRequest(content="Test", threshold=0.7)
        assert request.threshold == 70

        request = QualityCheckRequest(content="Test", threshold=0.5)
        assert request.threshold == 50

    def test_threshold_clamp(self):
        """Test threshold clamping for out-of-bounds values."""
        request = QualityCheckRequest(content="Test", threshold=150)
        assert request.threshold == 100

        request = QualityCheckRequest(content="Test", threshold=-10)
        assert request.threshold == 0

    def test_content_min_length(self):
        """Test content minimum length."""
        request = QualityCheckRequest(content="A")
        assert request.content == "A"

        with pytest.raises(ValidationError):
            QualityCheckRequest(content="")

    def test_inspection_modes_list(self):
        """Test multi-mode inspection_modes list."""
        request = QualityCheckRequest(
            content="Test",
            inspection_modes=["comprehensive", "quick"],
        )
        assert request.inspection_modes == ["comprehensive", "quick"]


# ============================================================================
# CreativeEditorRequest Tests
# ============================================================================

class TestCreativeEditorRequest:
    """Test CreativeEditorRequest model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = CreativeEditorRequest(
            content="A draft script that needs improvement",
            context="Drama, adult audience",
            persona="Senior Editor",
        )
        assert "draft script" in request.content
        assert "Drama" in request.context
        assert request.persona == "Senior Editor"

    def test_default_values(self):
        """Test default values are applied."""
        request = CreativeEditorRequest(
            content="Test content",
            context="Test context",
        )
        assert request.persona == "Senior Editor"
        assert request.use_rag is True
        assert request.model == "gemini-3-flash-preview"

    def test_content_sanitization(self):
        """Test content XSS sanitization."""
        request = CreativeEditorRequest(
            content="<script>evil()</script>draft content",
            context="Test context",
        )
        assert "<script>" not in request.content
        assert "draft content" in request.content

    def test_context_sanitization(self):
        """Test context XSS sanitization."""
        request = CreativeEditorRequest(
            content="Test content",
            context="javascript:alert(1)Drama",
        )
        assert "javascript:" not in request.context.lower()
        assert "Drama" in request.context

    def test_persona_validation(self):
        """Test persona validation."""
        for persona in ALLOWED_PERSONAS:
            request = CreativeEditorRequest(
                content="Test",
                context="Test",
                persona=persona,
            )
            assert request.persona == persona

    def test_invalid_persona_fails(self):
        """Test invalid persona fails validation."""
        with pytest.raises(ValidationError):
            CreativeEditorRequest(
                content="Test",
                context="Test",
                persona="Random Person",
            )

    def test_persona_case_normalization(self):
        """Test persona case normalization."""
        request = CreativeEditorRequest(
            content="Test",
            context="Test",
            persona="senior editor",
        )
        assert request.persona == "Senior Editor"

    def test_content_min_length(self):
        """Test content minimum length."""
        request = CreativeEditorRequest(content="A", context="B")
        assert request.content == "A"

        with pytest.raises(ValidationError):
            CreativeEditorRequest(content="", context="Test")

    def test_context_min_length(self):
        """Test context minimum length."""
        request = CreativeEditorRequest(content="A", context="B")
        assert request.context == "B"

        with pytest.raises(ValidationError):
            CreativeEditorRequest(content="Test", context="")

    def test_use_rag_toggle(self):
        """Test use_rag can be toggled."""
        request = CreativeEditorRequest(
            content="Test",
            context="Test",
            use_rag=False,
        )
        assert request.use_rag is False


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
    def test_content_xss_qualitycheck(self, attack_vector):
        """Test QualityCheckRequest content field XSS prevention."""
        request = QualityCheckRequest(
            content=attack_vector + "content",
        )
        assert "<script>" not in request.content.lower()
        assert "onerror" not in request.content.lower()
        assert "javascript:" not in request.content.lower()
        assert "onclick" not in request.content.lower()

    @pytest.mark.parametrize("attack_vector", [
        "<script>evil()</script>",
        "onclick=malicious()",
    ])
    def test_content_xss_creativeeditor(self, attack_vector):
        """Test CreativeEditorRequest content field XSS prevention."""
        request = CreativeEditorRequest(
            content=attack_vector + "content",
            context="Test context",
        )
        assert "<script>" not in request.content.lower()
        assert "onclick" not in request.content.lower()

    @pytest.mark.parametrize("attack_vector", [
        "<script>alert('xss')</script>",
        "javascript:void(0)",
    ])
    def test_context_xss(self, attack_vector):
        """Test CreativeEditorRequest context field XSS prevention."""
        request = CreativeEditorRequest(
            content="Test content",
            context=attack_vector + "Drama",
        )
        assert "<script>" not in request.context.lower()
        assert "javascript:" not in request.context.lower()


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_in_content(self):
        """Test Korean and emoji in content."""
        request = QualityCheckRequest(
            content="영화 시나리오 품질 검사 🎬",
        )
        assert "영화" in request.content
        assert "시나리오" in request.content
        assert "🎬" in request.content

    def test_unicode_in_context(self):
        """Test Korean and emoji in context."""
        request = CreativeEditorRequest(
            content="Test content",
            context="드라마, 성인 관객 🎭",
        )
        assert "드라마" in request.context
        assert "🎭" in request.context

    def test_all_valid_content_types(self):
        """Test all valid content types work."""
        for ct in ALLOWED_CONTENT_TYPES:
            request = QualityCheckRequest(content="Test", content_type=ct)
            assert request.content_type == ct

    def test_all_valid_inspection_modes(self):
        """Test all valid inspection modes work."""
        for mode in ALLOWED_INSPECTION_MODES:
            request = QualityCheckRequest(content="Test", inspection_mode=mode)
            assert request.inspection_mode == mode

    def test_all_valid_criteria(self):
        """Test all valid criteria work."""
        for criterion in ALLOWED_CRITERIA:
            request = QualityCheckRequest(content="Test", criteria=[criterion])
            assert criterion in request.criteria

    def test_all_valid_personas(self):
        """Test all valid personas work."""
        for persona in ALLOWED_PERSONAS:
            request = CreativeEditorRequest(
                content="Test",
                context="Test",
                persona=persona,
            )
            assert request.persona == persona

    def test_long_content(self):
        """Test long content within max length."""
        long_content = "Quality " * 500  # 4000 chars
        request = QualityCheckRequest(content=long_content)
        assert len(request.content) == len(long_content.strip())

    def test_content_whitespace_strip(self):
        """Test content whitespace stripping."""
        request = QualityCheckRequest(content="  Test content  ")
        assert request.content == "Test content"

    def test_context_whitespace_strip(self):
        """Test context whitespace stripping."""
        request = CreativeEditorRequest(
            content="Test",
            context="  Drama, audience  ",
        )
        assert request.context == "Drama, audience"

    def test_content_type_case_normalization(self):
        """Test content_type is normalized to lowercase."""
        request = QualityCheckRequest(content="Test", content_type="PROMPT")
        assert request.content_type == "prompt"

    def test_inspection_mode_case_normalization(self):
        """Test inspection_mode is normalized to lowercase."""
        request = QualityCheckRequest(content="Test", inspection_mode="COMPREHENSIVE")
        assert request.inspection_mode == "comprehensive"

    def test_multiple_criteria(self):
        """Test multiple criteria work."""
        request = QualityCheckRequest(
            content="Test",
            criteria=["aesthetic", "safety", "technical", "narrative"],
        )
        assert len(request.criteria) == 4
        assert "aesthetic" in request.criteria
        assert "narrative" in request.criteria

    def test_special_characters_in_content(self):
        """Test special characters preserved in content."""
        request = QualityCheckRequest(
            content="A quality check: prompt & evaluation - testing...",
        )
        assert ":" in request.content or "&#x27;" in request.content
        assert "-" in request.content

    def test_threshold_zero(self):
        """Test threshold can be zero."""
        request = QualityCheckRequest(content="Test", threshold=0)
        assert request.threshold == 0

    def test_threshold_hundred(self):
        """Test threshold can be 100."""
        request = QualityCheckRequest(content="Test", threshold=100)
        assert request.threshold == 100
