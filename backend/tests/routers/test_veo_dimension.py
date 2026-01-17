"""
Tests for VEO Dimension Endpoints.

Tests include:
- XSS sanitization for style and negative_prompt fields
- Veo model whitelist validation
- Duration and aspect ratio validation
- Edge case inputs
"""
import pytest
from pydantic import ValidationError

from app.routers.dimension.veo import (
    # Enums
    VeoModel,
    # Constants
    ALLOWED_VEO_MODELS,
    # Request model
    VeoGenerateRequest,
    # Helpers
    _sanitize_text_field,
    _validate_veo_model,
)


# ============================================================================
# Enums Tests
# ============================================================================

class TestVeoModelEnum:
    """Test VeoModel enum values."""

    def test_all_models_defined(self):
        """Verify all expected models are defined."""
        models = [m.value for m in VeoModel]
        assert "veo-3.1-generate-preview" in models
        assert "veo-3.1-fast-generate-preview" in models

    def test_enum_count(self):
        """Verify exactly 2 models."""
        assert len(VeoModel) == 2

    def test_allowed_models_matches_enum(self):
        """Verify ALLOWED_VEO_MODELS matches enum values."""
        for model in VeoModel:
            assert model.value in ALLOWED_VEO_MODELS


# ============================================================================
# Sanitization Helpers Tests
# ============================================================================

class TestSanitizeTextField:
    """Test _sanitize_text_field helper."""

    def test_removes_html_tags(self):
        """Test HTML tag removal."""
        result = _sanitize_text_field("<div>cinematic</div>")
        assert "<div>" not in result
        assert "</div>" not in result

    def test_removes_script_tags(self):
        """Test script tag removal."""
        result = _sanitize_text_field("<script>evil()</script>test")
        assert "<script>" not in result
        assert "</script>" not in result

    def test_removes_javascript_protocol(self):
        """Test javascript: protocol removal."""
        result = _sanitize_text_field("javascript:alert(1)")
        assert "javascript:" not in result.lower()

    def test_removes_event_handlers(self):
        """Test on* event handler removal."""
        result = _sanitize_text_field("onload=alert(1)")
        assert "onload=" not in result.lower()

    def test_empty_returns_default(self):
        """Test empty string returns default."""
        assert _sanitize_text_field("") == ""
        assert _sanitize_text_field("", default="test") == "test"
        assert _sanitize_text_field("   ", default="fallback") == "fallback"

    def test_preserves_normal_text(self):
        """Test normal text is preserved."""
        result = _sanitize_text_field("cinematic, noir, moody")
        assert "cinematic" in result
        assert "noir" in result


class TestValidateVeoModel:
    """Test _validate_veo_model helper."""

    def test_valid_models(self):
        """Test all valid models pass."""
        assert _validate_veo_model("veo-3.1-generate-preview") == "veo-3.1-generate-preview"
        assert _validate_veo_model("veo-3.1-fast-generate-preview") == "veo-3.1-fast-generate-preview"

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        assert _validate_veo_model("  veo-3.1-generate-preview  ") == "veo-3.1-generate-preview"

    def test_invalid_raises(self):
        """Test invalid model raises ValueError."""
        with pytest.raises(ValueError, match="Invalid Veo model"):
            _validate_veo_model("veo-2.0")
        with pytest.raises(ValueError, match="Invalid Veo model"):
            _validate_veo_model("invalid-model")


# ============================================================================
# Request Model Tests
# ============================================================================

class TestVeoGenerateRequest:
    """Test VeoGenerateRequest model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = VeoGenerateRequest(
            prompt="A cinematic drone shot over mountains",
            style="cinematic",
            duration=6,
        )
        assert "drone shot" in request.prompt
        assert request.style == "cinematic"
        assert request.duration == 6

    def test_default_values(self):
        """Test default values are applied."""
        request = VeoGenerateRequest(prompt="Test prompt")
        assert request.negative_prompt == ""
        assert request.aspect_ratio == "16:9"
        assert request.duration == 6
        assert request.style == "cinematic"
        assert request.seed == 0
        assert request.model == "veo-3.1-generate-preview"

    def test_style_sanitization(self):
        """Test style XSS sanitization."""
        request = VeoGenerateRequest(
            prompt="Test prompt",
            style="<script>alert('xss')</script>cinematic",
        )
        assert "<script>" not in request.style
        assert "cinematic" in request.style

    def test_negative_prompt_sanitization(self):
        """Test negative_prompt XSS sanitization."""
        request = VeoGenerateRequest(
            prompt="Test prompt",
            negative_prompt="javascript:alert(1)",
        )
        assert "javascript:" not in request.negative_prompt.lower()

    def test_empty_style_defaults(self):
        """Test empty style defaults to cinematic."""
        request = VeoGenerateRequest(
            prompt="Test prompt",
            style="",
        )
        assert request.style == "cinematic"

    def test_model_validation(self):
        """Test model whitelist validation."""
        # Valid model
        request = VeoGenerateRequest(
            prompt="Test prompt",
            model="veo-3.1-generate-preview",
        )
        assert request.model == "veo-3.1-generate-preview"

        # Fast model also valid
        request_fast = VeoGenerateRequest(
            prompt="Test prompt",
            model="veo-3.1-fast-generate-preview",
        )
        assert request_fast.model == "veo-3.1-fast-generate-preview"

    def test_invalid_model_fails(self):
        """Test invalid model fails validation."""
        with pytest.raises(ValidationError):
            VeoGenerateRequest(
                prompt="Test prompt",
                model="invalid-model",
            )

    def test_duration_boundaries(self):
        """Test duration boundary values."""
        # Min (4 seconds)
        request_min = VeoGenerateRequest(prompt="Test", duration=4)
        assert request_min.duration == 4

        # Max (8 seconds)
        request_max = VeoGenerateRequest(prompt="Test", duration=8)
        assert request_max.duration == 8

    def test_duration_below_min_fails(self):
        """Test duration below minimum fails."""
        with pytest.raises(ValidationError):
            VeoGenerateRequest(prompt="Test", duration=3)

    def test_duration_above_max_fails(self):
        """Test duration above maximum fails."""
        with pytest.raises(ValidationError):
            VeoGenerateRequest(prompt="Test", duration=9)

    def test_seed_non_negative(self):
        """Test seed must be non-negative."""
        request = VeoGenerateRequest(prompt="Test", seed=12345)
        assert request.seed == 12345

        with pytest.raises(ValidationError):
            VeoGenerateRequest(prompt="Test", seed=-1)

    def test_prompt_whitespace_strip(self):
        """Test prompt whitespace stripping."""
        request = VeoGenerateRequest(prompt="  Test prompt  ")
        assert request.prompt == "Test prompt"

    def test_prompt_min_length(self):
        """Test prompt minimum length."""
        # Valid minimum
        request = VeoGenerateRequest(prompt="A")
        assert request.prompt == "A"

        # Empty fails
        with pytest.raises(ValidationError):
            VeoGenerateRequest(prompt="")

    def test_prompt_max_length(self):
        """Test prompt maximum length (5000 chars)."""
        long_prompt = "A" * 5000
        request = VeoGenerateRequest(prompt=long_prompt)
        assert len(request.prompt) == 5000

        # Over limit fails
        with pytest.raises(ValidationError):
            VeoGenerateRequest(prompt="A" * 5001)


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
        "<body onload=alert(1)>",
    ])
    def test_style_xss(self, attack_vector):
        """Test style field XSS prevention."""
        request = VeoGenerateRequest(
            prompt="Test prompt",
            style=attack_vector + "cinematic",
        )
        assert "<script>" not in request.style.lower()
        assert "onerror" not in request.style.lower()
        assert "onload" not in request.style.lower()
        assert "javascript:" not in request.style.lower()

    @pytest.mark.parametrize("attack_vector", [
        "<script>evil()</script>",
        "onclick=malicious()",
    ])
    def test_negative_prompt_xss(self, attack_vector):
        """Test negative_prompt field XSS prevention."""
        request = VeoGenerateRequest(
            prompt="Test prompt",
            negative_prompt=attack_vector,
        )
        assert "<script>" not in request.negative_prompt.lower()
        assert "onclick" not in request.negative_prompt.lower()


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_in_prompt(self):
        """Test Korean and emoji in prompt."""
        request = VeoGenerateRequest(
            prompt="밤하늘 아래 걷는 두 연인 🌙✨"
        )
        assert "밤하늘" in request.prompt
        assert "🌙" in request.prompt

    def test_special_characters_in_prompt(self):
        """Test special characters in prompt."""
        request = VeoGenerateRequest(
            prompt="Scene #1: [CUT] - Action! @timestamp:00:15"
        )
        assert "#1" in request.prompt
        assert "[CUT]" in request.prompt

    def test_all_valid_models(self):
        """Test all valid models work."""
        for model in ALLOWED_VEO_MODELS:
            request = VeoGenerateRequest(prompt="Test", model=model)
            assert request.model == model

    def test_valid_aspect_ratios(self):
        """Test common aspect ratios."""
        for ratio in ["16:9", "9:16", "1:1", "4:3", "3:4"]:
            request = VeoGenerateRequest(prompt="Test", aspect_ratio=ratio)
            assert request.aspect_ratio == ratio

    def test_zero_seed(self):
        """Test zero seed (random)."""
        request = VeoGenerateRequest(prompt="Test", seed=0)
        assert request.seed == 0

    def test_large_seed(self):
        """Test large seed value."""
        request = VeoGenerateRequest(prompt="Test", seed=999999999)
        assert request.seed == 999999999
