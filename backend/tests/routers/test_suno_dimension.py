"""
Tests for Suno AI Dimension Endpoints.

Tests include:
- XSS sanitization for prompt, title, style
- Model whitelist validation
- Edge case inputs
"""
import pytest
from pydantic import ValidationError

from app.routers.dimension.suno import (
    # Constants
    ALLOWED_SUNO_MODELS,
    # Request model
    SunoGenerateRequest,
    # Helpers
    _sanitize_text,
    _validate_suno_model,
)


# ============================================================================
# Sanitization Helpers Tests
# ============================================================================

class TestSanitizeText:
    """Test _sanitize_text helper."""

    def test_removes_html_tags(self):
        """Test HTML tag removal."""
        result = _sanitize_text("<div>lyrics here</div>")
        assert "<div>" not in result
        assert "</div>" not in result
        assert "lyrics here" in result

    def test_removes_script_tags(self):
        """Test script tag removal."""
        result = _sanitize_text("<script>evil()</script>music")
        assert "<script>" not in result

    def test_removes_javascript_protocol(self):
        """Test javascript: protocol removal."""
        result = _sanitize_text("javascript:alert(1)")
        assert "javascript:" not in result.lower()

    def test_removes_event_handlers(self):
        """Test on* event handler removal."""
        result = _sanitize_text("onload=alert(1)")
        assert "onload=" not in result.lower()

    def test_preserves_normal_text(self):
        """Test normal text is preserved."""
        result = _sanitize_text("Jazz, Smooth, Relaxing")
        assert "Jazz" in result
        assert "Smooth" in result

    def test_preserves_korean(self):
        """Test Korean characters preserved."""
        result = _sanitize_text("감미로운 재즈 음악")
        assert "감미로운" in result
        assert "재즈" in result


# ============================================================================
# Validation Helpers Tests
# ============================================================================

class TestValidateSunoModel:
    """Test _validate_suno_model helper."""

    def test_valid_models(self):
        """Test all valid models pass."""
        for model in ALLOWED_SUNO_MODELS:
            assert _validate_suno_model(model) == model

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        assert _validate_suno_model("  V5  ") == "V5"

    def test_invalid_model_raises(self):
        """Test invalid model raises ValueError."""
        with pytest.raises(ValueError, match="Invalid model"):
            _validate_suno_model("V3")
        with pytest.raises(ValueError, match="Invalid model"):
            _validate_suno_model("invalid")


class TestAllowedModelsConstant:
    """Test ALLOWED_SUNO_MODELS constant."""

    def test_expected_models_present(self):
        """Verify expected models are in allowed list."""
        expected = ["V5", "V4_5PLUS", "V4_5ALL", "V4_5", "V4"]
        for model in expected:
            assert model in ALLOWED_SUNO_MODELS

    def test_model_count(self):
        """Verify reasonable number of models."""
        assert len(ALLOWED_SUNO_MODELS) == 5


# ============================================================================
# Request Model Tests
# ============================================================================

class TestSunoGenerateRequest:
    """Test SunoGenerateRequest model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = SunoGenerateRequest(
            prompt="A smooth jazz song about the night sky",
            title="Midnight Dreams",
            style="Jazz, Smooth, Relaxing",
        )
        assert "smooth jazz" in request.prompt
        assert request.title == "Midnight Dreams"
        assert "Jazz" in request.style

    def test_default_values(self):
        """Test default values are applied."""
        request = SunoGenerateRequest(
            prompt="Test prompt",
            title="Test Title",
            style="Pop",
        )
        assert request.instrumental is False
        assert request.model == "V5"

    def test_prompt_sanitization(self):
        """Test prompt XSS sanitization."""
        request = SunoGenerateRequest(
            prompt="<script>alert('xss')</script>my lyrics",
            title="Test",
            style="Pop",
        )
        assert "<script>" not in request.prompt
        assert "my lyrics" in request.prompt

    def test_title_sanitization(self):
        """Test title XSS sanitization."""
        request = SunoGenerateRequest(
            prompt="Test prompt",
            title="javascript:alert(1)Song",
            style="Pop",
        )
        assert "javascript:" not in request.title.lower()
        assert "Song" in request.title

    def test_style_sanitization(self):
        """Test style XSS sanitization."""
        request = SunoGenerateRequest(
            prompt="Test prompt",
            title="Test",
            style="<img onerror=evil()>Jazz",
        )
        assert "<img" not in request.style
        assert "onerror" not in request.style

    def test_invalid_model_fails(self):
        """Test invalid model fails validation."""
        with pytest.raises(ValidationError):
            SunoGenerateRequest(
                prompt="Test",
                title="Test",
                style="Pop",
                model="V3",
            )

    def test_prompt_whitespace_strip(self):
        """Test prompt whitespace stripping."""
        request = SunoGenerateRequest(
            prompt="  Test prompt  ",
            title="Test",
            style="Pop",
        )
        assert request.prompt == "Test prompt"

    def test_prompt_min_length(self):
        """Test prompt minimum length."""
        # Valid minimum
        request = SunoGenerateRequest(
            prompt="A",
            title="Test",
            style="Pop",
        )
        assert request.prompt == "A"

        # Empty fails
        with pytest.raises(ValidationError):
            SunoGenerateRequest(
                prompt="",
                title="Test",
                style="Pop",
            )

    def test_title_min_length(self):
        """Test title minimum length."""
        # Valid minimum
        request = SunoGenerateRequest(
            prompt="Test",
            title="A",
            style="Pop",
        )
        assert request.title == "A"

        # Empty fails
        with pytest.raises(ValidationError):
            SunoGenerateRequest(
                prompt="Test",
                title="",
                style="Pop",
            )

    def test_style_min_length(self):
        """Test style minimum length."""
        # Valid minimum
        request = SunoGenerateRequest(
            prompt="Test",
            title="Test",
            style="A",
        )
        assert request.style == "A"

        # Empty fails
        with pytest.raises(ValidationError):
            SunoGenerateRequest(
                prompt="Test",
                title="Test",
                style="",
            )


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
    def test_prompt_xss(self, attack_vector):
        """Test prompt field XSS prevention."""
        request = SunoGenerateRequest(
            prompt=attack_vector + "lyrics",
            title="Test",
            style="Pop",
        )
        assert "<script>" not in request.prompt.lower()
        assert "onerror" not in request.prompt.lower()
        assert "javascript:" not in request.prompt.lower()

    @pytest.mark.parametrize("attack_vector", [
        "<script>evil()</script>",
        "onclick=malicious()",
    ])
    def test_title_xss(self, attack_vector):
        """Test title field XSS prevention."""
        request = SunoGenerateRequest(
            prompt="Test",
            title=attack_vector + "Song",
            style="Pop",
        )
        assert "<script>" not in request.title.lower()
        assert "onclick" not in request.title.lower()

    @pytest.mark.parametrize("attack_vector", [
        "<div onclick=evil()>",
        "onmouseover=alert(1)",
    ])
    def test_style_xss(self, attack_vector):
        """Test style field XSS prevention."""
        request = SunoGenerateRequest(
            prompt="Test",
            title="Test",
            style=attack_vector + "Jazz",
        )
        assert "onclick" not in request.style.lower()
        assert "onmouseover" not in request.style.lower()


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_in_prompt(self):
        """Test Korean and emoji in prompt."""
        request = SunoGenerateRequest(
            prompt="밤하늘 아래 🌙 노래하는 새들",
            title="밤의 노래",
            style="발라드, 감성적",
        )
        assert "밤하늘" in request.prompt
        assert "🌙" in request.prompt
        assert "밤의 노래" in request.title

    def test_all_valid_models(self):
        """Test all valid models work."""
        for model in ALLOWED_SUNO_MODELS:
            request = SunoGenerateRequest(
                prompt="Test",
                title="Test",
                style="Pop",
                model=model,
            )
            assert request.model == model

    def test_instrumental_true(self):
        """Test instrumental can be True."""
        request = SunoGenerateRequest(
            prompt="Test",
            title="Test",
            style="Jazz",
            instrumental=True,
        )
        assert request.instrumental is True

    def test_multiple_styles(self):
        """Test multiple styles in comma-separated format."""
        request = SunoGenerateRequest(
            prompt="Test",
            title="Test",
            style="Jazz, Smooth, Relaxing, Instrumental",
        )
        assert "Jazz" in request.style
        assert "Smooth" in request.style
        assert "Relaxing" in request.style

    def test_long_prompt(self):
        """Test long prompt within max length."""
        long_prompt = "A " * 500  # 1000 chars
        request = SunoGenerateRequest(
            prompt=long_prompt,
            title="Test",
            style="Pop",
        )
        assert len(request.prompt) == len(long_prompt.strip())

    def test_prompt_max_length_exceeded(self):
        """Test prompt exceeding max length fails."""
        with pytest.raises(ValidationError):
            SunoGenerateRequest(
                prompt="A" * 2001,  # Over 2000 limit
                title="Test",
                style="Pop",
            )
