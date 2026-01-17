"""
Tests for Kling AI Dimension Endpoints.

Tests include:
- XSS sanitization for prompt and negative_prompt
- Enum validation for duration, aspect_ratio, resolution, mode
- Edge case inputs
"""
import pytest
from pydantic import ValidationError

from app.routers.dimension.kling import (
    # Request model
    KlingGenerateRequest,
    # Helpers
    _sanitize_prompt,
    _validate_duration,
    _validate_aspect_ratio,
    _validate_resolution,
    _validate_mode,
)


# ============================================================================
# Sanitization Helpers Tests
# ============================================================================

class TestSanitizePrompt:
    """Test _sanitize_prompt helper."""

    def test_removes_html_tags(self):
        """Test HTML tag removal."""
        result = _sanitize_prompt("<div>video prompt</div>")
        assert "<div>" not in result
        assert "</div>" not in result
        assert "video prompt" in result

    def test_removes_script_tags(self):
        """Test script tag removal."""
        result = _sanitize_prompt("<script>evil()</script>test")
        assert "<script>" not in result

    def test_removes_javascript_protocol(self):
        """Test javascript: protocol removal."""
        result = _sanitize_prompt("javascript:alert(1)")
        assert "javascript:" not in result.lower()

    def test_removes_event_handlers(self):
        """Test on* event handler removal."""
        result = _sanitize_prompt("onload=alert(1)")
        assert "onload=" not in result.lower()

    def test_preserves_normal_text(self):
        """Test normal text is preserved."""
        result = _sanitize_prompt("A cinematic video of mountains")
        assert "cinematic" in result
        assert "mountains" in result

    def test_preserves_korean(self):
        """Test Korean characters preserved."""
        result = _sanitize_prompt("산 위의 영화적인 장면")
        assert "산" in result
        assert "영화적인" in result


# ============================================================================
# Validation Helpers Tests
# ============================================================================

class TestValidateDuration:
    """Test _validate_duration helper."""

    def test_valid_durations(self):
        """Test valid durations pass."""
        assert _validate_duration("5") == "5"
        assert _validate_duration("10") == "10"

    def test_invalid_duration_raises(self):
        """Test invalid duration raises ValueError."""
        with pytest.raises(ValueError, match="Invalid duration"):
            _validate_duration("3")
        with pytest.raises(ValueError, match="Invalid duration"):
            _validate_duration("15")


class TestValidateAspectRatio:
    """Test _validate_aspect_ratio helper."""

    def test_valid_ratios(self):
        """Test valid aspect ratios pass."""
        assert _validate_aspect_ratio("16:9") == "16:9"
        assert _validate_aspect_ratio("9:16") == "9:16"
        assert _validate_aspect_ratio("1:1") == "1:1"

    def test_invalid_ratio_raises(self):
        """Test invalid aspect ratio raises ValueError."""
        with pytest.raises(ValueError, match="Invalid aspect_ratio"):
            _validate_aspect_ratio("4:3")
        with pytest.raises(ValueError, match="Invalid aspect_ratio"):
            _validate_aspect_ratio("21:9")


class TestValidateResolution:
    """Test _validate_resolution helper."""

    def test_valid_resolutions(self):
        """Test valid resolutions pass."""
        assert _validate_resolution("720p") == "720p"
        assert _validate_resolution("1080p") == "1080p"

    def test_invalid_resolution_raises(self):
        """Test invalid resolution raises ValueError."""
        with pytest.raises(ValueError, match="Invalid resolution"):
            _validate_resolution("480p")
        with pytest.raises(ValueError, match="Invalid resolution"):
            _validate_resolution("4k")


class TestValidateMode:
    """Test _validate_mode helper."""

    def test_valid_modes(self):
        """Test valid modes pass."""
        assert _validate_mode("std") == "std"
        assert _validate_mode("pro") == "pro"

    def test_invalid_mode_raises(self):
        """Test invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid mode"):
            _validate_mode("basic")
        with pytest.raises(ValueError, match="Invalid mode"):
            _validate_mode("ultra")


# ============================================================================
# Request Model Tests
# ============================================================================

class TestKlingGenerateRequest:
    """Test KlingGenerateRequest model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = KlingGenerateRequest(
            prompt="A cinematic drone shot over mountains",
            duration="5",
            resolution="1080p",
        )
        assert "drone shot" in request.prompt
        assert request.duration == "5"
        assert request.resolution == "1080p"

    def test_default_values(self):
        """Test default values are applied."""
        request = KlingGenerateRequest(prompt="Test prompt")
        assert request.negative_prompt is None
        assert request.duration == "5"
        assert request.aspect_ratio == "16:9"
        assert request.resolution == "1080p"
        assert request.mode == "std"
        assert request.enable_audio is False
        assert request.image_url is None

    def test_prompt_sanitization(self):
        """Test prompt XSS sanitization."""
        request = KlingGenerateRequest(
            prompt="<script>alert('xss')</script>cinematic video",
        )
        assert "<script>" not in request.prompt
        assert "cinematic video" in request.prompt

    def test_negative_prompt_sanitization(self):
        """Test negative_prompt XSS sanitization."""
        request = KlingGenerateRequest(
            prompt="Test prompt",
            negative_prompt="javascript:alert(1)",
        )
        assert "javascript:" not in request.negative_prompt.lower()

    def test_invalid_duration_fails(self):
        """Test invalid duration fails validation."""
        with pytest.raises(ValidationError):
            KlingGenerateRequest(prompt="Test", duration="3")

    def test_invalid_aspect_ratio_fails(self):
        """Test invalid aspect ratio fails validation."""
        with pytest.raises(ValidationError):
            KlingGenerateRequest(prompt="Test", aspect_ratio="4:3")

    def test_invalid_resolution_fails(self):
        """Test invalid resolution fails validation."""
        with pytest.raises(ValidationError):
            KlingGenerateRequest(prompt="Test", resolution="480p")

    def test_invalid_mode_fails(self):
        """Test invalid mode fails validation."""
        with pytest.raises(ValidationError):
            KlingGenerateRequest(prompt="Test", mode="ultra")

    def test_prompt_whitespace_strip(self):
        """Test prompt whitespace stripping."""
        request = KlingGenerateRequest(prompt="  Test prompt  ")
        assert request.prompt == "Test prompt"

    def test_prompt_min_length(self):
        """Test prompt minimum length."""
        # Valid minimum
        request = KlingGenerateRequest(prompt="A")
        assert request.prompt == "A"

        # Empty fails
        with pytest.raises(ValidationError):
            KlingGenerateRequest(prompt="")


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
        request = KlingGenerateRequest(
            prompt=attack_vector + "video",
        )
        assert "<script>" not in request.prompt.lower()
        assert "onerror" not in request.prompt.lower()
        assert "javascript:" not in request.prompt.lower()

    @pytest.mark.parametrize("attack_vector", [
        "<script>evil()</script>",
        "onclick=malicious()",
    ])
    def test_negative_prompt_xss(self, attack_vector):
        """Test negative_prompt field XSS prevention."""
        request = KlingGenerateRequest(
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
        request = KlingGenerateRequest(
            prompt="밤하늘 아래 걷는 두 연인 🌙✨"
        )
        assert "밤하늘" in request.prompt
        assert "🌙" in request.prompt

    def test_all_valid_durations(self):
        """Test all valid durations work."""
        for duration in ["5", "10"]:
            request = KlingGenerateRequest(prompt="Test", duration=duration)
            assert request.duration == duration

    def test_all_valid_aspect_ratios(self):
        """Test all valid aspect ratios work."""
        for ratio in ["16:9", "9:16", "1:1"]:
            request = KlingGenerateRequest(prompt="Test", aspect_ratio=ratio)
            assert request.aspect_ratio == ratio

    def test_all_valid_resolutions(self):
        """Test all valid resolutions work."""
        for resolution in ["720p", "1080p"]:
            request = KlingGenerateRequest(prompt="Test", resolution=resolution)
            assert request.resolution == resolution

    def test_all_valid_modes(self):
        """Test all valid modes work."""
        for mode in ["std", "pro"]:
            request = KlingGenerateRequest(prompt="Test", mode=mode)
            assert request.mode == mode

    def test_null_negative_prompt(self):
        """Test null negative_prompt is allowed."""
        request = KlingGenerateRequest(
            prompt="Test prompt",
            negative_prompt=None,
        )
        assert request.negative_prompt is None

    def test_enable_audio_true(self):
        """Test enable_audio can be True."""
        request = KlingGenerateRequest(
            prompt="Test prompt",
            enable_audio=True,
        )
        assert request.enable_audio is True

    def test_image_url_provided(self):
        """Test image_url can be provided."""
        request = KlingGenerateRequest(
            prompt="Test prompt",
            image_url="https://example.com/image.jpg",
        )
        assert request.image_url == "https://example.com/image.jpg"
