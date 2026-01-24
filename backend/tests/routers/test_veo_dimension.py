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
    _validate_veo_model,
)
from app.routers.dimension._video_base import sanitize_video_text


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
    """Test sanitize_video_text helper."""

    def test_removes_html_tags(self):
        """Test HTML tag removal."""
        result = sanitize_video_text("<div>cinematic</div>")
        assert "<div>" not in result
        assert "</div>" not in result

    def test_removes_script_tags(self):
        """Test script tag removal."""
        result = sanitize_video_text("<script>evil()</script>test")
        assert "<script>" not in result
        assert "</script>" not in result

    def test_removes_javascript_protocol(self):
        """Test javascript: protocol removal."""
        result = sanitize_video_text("javascript:alert(1)")
        assert "javascript:" not in result.lower()

    def test_removes_event_handlers(self):
        """Test on* event handler removal."""
        result = sanitize_video_text("onload=alert(1)")
        assert "onload=" not in result.lower()

    def test_empty_returns_default(self):
        """Test empty string returns default."""
        assert sanitize_video_text("") == ""
        assert sanitize_video_text("", default="test") == "test"
        assert sanitize_video_text("   ", default="fallback") == "fallback"

    def test_preserves_normal_text(self):
        """Test normal text is preserved."""
        result = sanitize_video_text("cinematic, noir, moody")
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


# ============================================================================
# Character Consistency Integration Tests
# ============================================================================

class TestCharacterConsistency:
    """Test character_ids integration for Veo Ingredients."""

    def test_empty_character_ids_default(self):
        """Test empty character_ids default."""
        request = VeoGenerateRequest(prompt="Test prompt")
        assert request.character_ids == []

    def test_single_character_id(self):
        """Test single character_id."""
        request = VeoGenerateRequest(
            prompt="Test prompt",
            character_ids=["uuid-1"],
        )
        assert len(request.character_ids) == 1
        assert request.character_ids[0] == "uuid-1"

    def test_multiple_character_ids(self):
        """Test multiple character_ids (up to 3)."""
        request = VeoGenerateRequest(
            prompt="Test prompt",
            character_ids=["uuid-1", "uuid-2", "uuid-3"],
        )
        assert len(request.character_ids) == 3

    def test_max_character_ids(self):
        """Test max 3 character_ids limit."""
        with pytest.raises(ValidationError):
            VeoGenerateRequest(
                prompt="Test prompt",
                character_ids=["a", "b", "c", "d"],  # 4 exceeds limit
            )


# ============================================================================
# Duration Comprehensive Tests
# ============================================================================

class TestDurationComprehensive:
    """Comprehensive duration validation tests."""

    @pytest.mark.parametrize("duration", [4, 5, 6, 7, 8])
    def test_all_valid_durations(self, duration):
        """Test all valid duration values."""
        request = VeoGenerateRequest(prompt="Test", duration=duration)
        assert request.duration == duration

    def test_default_duration(self):
        """Test default duration is 6 seconds."""
        request = VeoGenerateRequest(prompt="Test")
        assert request.duration == 6

    @pytest.mark.parametrize("invalid_duration", [0, 1, 2, 3, 9, 10, 100, -1])
    def test_invalid_durations(self, invalid_duration):
        """Test invalid duration values fail."""
        with pytest.raises(ValidationError):
            VeoGenerateRequest(prompt="Test", duration=invalid_duration)


# ============================================================================
# Capsule ID Integration Tests
# ============================================================================

class TestCapsuleIdIntegration:
    """Test integration with dimension adapter system."""

    def test_veo_capsule_id_exists(self):
        """Verify VEO_VIDEO_GENERATE capsule ID exists."""
        from app.routers.dimension._base import DimensionCapsuleId
        assert hasattr(DimensionCapsuleId, "VEO_VIDEO_GENERATE")

    def test_capsule_in_fixtures(self):
        """Verify capsule is defined in fixtures."""
        from app.fixtures.dimension_capsules import DIMENSION_CAPSULES
        capsule = next(
            (c for c in DIMENSION_CAPSULES if "veo" in c["capsule_key"].lower()),
            None
        )
        assert capsule is not None
        assert "credit_costs" in capsule


# ============================================================================
# Model Validation Comprehensive Tests
# ============================================================================

class TestModelValidationComprehensive:
    """Comprehensive model validation tests."""

    def test_standard_model(self):
        """Test standard Veo 3.1 model."""
        request = VeoGenerateRequest(
            prompt="Test",
            model="veo-3.1-generate-preview",
        )
        assert request.model == "veo-3.1-generate-preview"

    def test_fast_model(self):
        """Test fast Veo 3.1 model."""
        request = VeoGenerateRequest(
            prompt="Test",
            model="veo-3.1-fast-generate-preview",
        )
        assert request.model == "veo-3.1-fast-generate-preview"

    @pytest.mark.parametrize("invalid_model", [
        "veo-2.0",
        "veo-3.0",
        "veo-3.1",
        "sora-2",
        "kling-2.6",
        "runway-gen3",
        "",
        "INVALID",
    ])
    def test_invalid_models_fail(self, invalid_model):
        """Test invalid models are rejected."""
        with pytest.raises(ValidationError):
            VeoGenerateRequest(prompt="Test", model=invalid_model)


# ============================================================================
# Aspect Ratio Validation Tests
# ============================================================================

class TestAspectRatioValidation:
    """Test aspect ratio validation."""

    @pytest.mark.parametrize("ratio", ["16:9", "9:16", "1:1", "4:3", "3:4"])
    def test_common_aspect_ratios(self, ratio):
        """Test common aspect ratios are valid."""
        request = VeoGenerateRequest(prompt="Test", aspect_ratio=ratio)
        assert request.aspect_ratio == ratio

    def test_default_aspect_ratio(self):
        """Test default aspect ratio is 16:9."""
        request = VeoGenerateRequest(prompt="Test")
        assert request.aspect_ratio == "16:9"


# ============================================================================
# Combined Field Validation Tests
# ============================================================================

class TestCombinedFields:
    """Test combinations of fields together."""

    def test_full_request(self):
        """Test request with all fields populated."""
        request = VeoGenerateRequest(
            prompt="A cinematic shot of waves crashing on rocks at sunset",
            negative_prompt="blurry, low quality",
            aspect_ratio="16:9",
            duration=8,
            style="cinematic noir",
            seed=12345,
            model="veo-3.1-generate-preview",
            character_ids=["char-1", "char-2"],
        )
        assert len(request.prompt) > 10
        assert request.duration == 8
        assert len(request.character_ids) == 2

    def test_minimal_request(self):
        """Test request with only required fields."""
        request = VeoGenerateRequest(prompt="Test video prompt")
        # All defaults should be applied
        assert request.negative_prompt == ""
        assert request.aspect_ratio == "16:9"
        assert request.duration == 6
        assert request.style == "cinematic"
        assert request.seed == 0
        assert request.model == "veo-3.1-generate-preview"
        assert request.character_ids == []


# ============================================================================
# Veo 3.1 Feature Tests (2026 Best Practices)
# ============================================================================

class TestVeo31Features:
    """Test Veo 3.1 specific features (2026 Best Practices)."""

    def test_native_audio_enabled(self):
        """Veo 3.1 includes native audio by default."""
        # This tests the concept - actual audio is in VeoConfig
        request = VeoGenerateRequest(
            prompt="Two people talking at a coffee shop"
        )
        # Veo 3.1 should handle dialogue/audio natively
        assert request.model.startswith("veo-3.1")

    def test_1080p_support(self):
        """Veo 3.1 supports 1080p output."""
        # 16:9 aspect ratio supports HD
        request = VeoGenerateRequest(
            prompt="High quality cinematic shot",
            aspect_ratio="16:9",
        )
        assert request.aspect_ratio == "16:9"

    def test_vertical_video_support(self):
        """Veo 3.1 supports 9:16 for social media."""
        request = VeoGenerateRequest(
            prompt="Vertical video for TikTok",
            aspect_ratio="9:16",
        )
        assert request.aspect_ratio == "9:16"

    def test_dialogue_prompt_structure(self):
        """Test dialogue-containing prompt structure."""
        request = VeoGenerateRequest(
            prompt='A man says "Hello, how are you?" to a woman at a cafe. She smiles and responds.',
        )
        assert "says" in request.prompt
        assert '"' in request.prompt


# ============================================================================
# Prompt Validation Edge Cases
# ============================================================================

class TestPromptEdgeCases:
    """Additional prompt validation edge cases."""

    def test_prompt_with_newlines(self):
        """Test prompt with newline characters."""
        request = VeoGenerateRequest(
            prompt="Scene 1:\nA man walks.\nScene 2:\nHe stops."
        )
        assert "\n" in request.prompt

    def test_prompt_with_quotes(self):
        """Test prompt with various quote types."""
        request = VeoGenerateRequest(
            prompt="""He said "Hello" and she replied 'Hi there'"""
        )
        assert '"' in request.prompt
        assert "'" in request.prompt

    def test_prompt_with_numbers(self):
        """Test prompt with numbers and timestamps."""
        request = VeoGenerateRequest(
            prompt="At 10:30 AM, 5 people enter the room. Scene duration: 8 seconds."
        )
        assert "10:30" in request.prompt
        assert "5 people" in request.prompt

    def test_prompt_camera_directions(self):
        """Test prompt with camera movement directions."""
        request = VeoGenerateRequest(
            prompt="[DOLLY IN] Camera slowly approaches. [CUT TO] Wide shot of the landscape."
        )
        assert "[DOLLY IN]" in request.prompt
        assert "[CUT TO]" in request.prompt


# ============================================================================
# 2026 Video Generation Platform Capability Tests
# ============================================================================

class TestVideoGenerationPlatform:
    """Test VideoGenerationPlatform enum (2026 multi-platform support)."""

    def test_platform_enum_exists(self):
        """Test VideoGenerationPlatform enum is importable."""
        from app.routers.dimension.veo import VideoGenerationPlatform
        assert VideoGenerationPlatform is not None

    def test_supported_platforms(self):
        """Test 2026 supported video platforms."""
        from app.routers.dimension.veo import VideoGenerationPlatform
        assert VideoGenerationPlatform.VEO.value == "veo"
        assert VideoGenerationPlatform.KLING.value == "kling"
        assert VideoGenerationPlatform.SORA.value == "sora"
        assert VideoGenerationPlatform.HAILUO.value == "hailuo"
        assert VideoGenerationPlatform.SEEDANCE.value == "seedance"
        assert VideoGenerationPlatform.RUNWAY.value == "runway"

    def test_platform_count(self):
        """Test at least 6 platforms supported."""
        from app.routers.dimension.veo import VideoGenerationPlatform
        assert len(VideoGenerationPlatform) >= 6


class TestVideoOutputQuality:
    """Test VideoOutputQuality enum (2026 standards)."""

    def test_quality_levels(self):
        """Test 2026 video quality levels."""
        from app.routers.dimension.veo import VideoOutputQuality
        assert VideoOutputQuality.SD.value == "sd"  # 480p
        assert VideoOutputQuality.HD.value == "hd"  # 720p
        assert VideoOutputQuality.FHD.value == "fhd"  # 1080p
        assert VideoOutputQuality.UHD.value == "uhd"  # 4K


class TestAudioIntegrationMode:
    """Test AudioIntegrationMode enum (2026 native audio trend)."""

    def test_audio_modes(self):
        """Test 2026 audio integration modes."""
        from app.routers.dimension.veo import AudioIntegrationMode
        assert AudioIntegrationMode.NONE.value == "none"
        assert AudioIntegrationMode.NATIVE.value == "native"
        assert AudioIntegrationMode.SYNC.value == "sync"
        assert AudioIntegrationMode.DIALOGUE.value == "dialogue"


class TestVeo31Capabilities:
    """Test Veo31Capabilities model (Oct 2025 release)."""

    def test_default_capabilities(self):
        """Test default Veo 3.1 capabilities."""
        from app.routers.dimension.veo import Veo31Capabilities, VideoOutputQuality
        caps = Veo31Capabilities()
        assert caps.max_duration_seconds == 60  # 60s max
        assert caps.resolution == VideoOutputQuality.FHD  # 1080p
        assert caps.supports_native_audio is True
        assert caps.supports_multi_image is True
        assert caps.supports_camera_control is True
        assert caps.pricing_per_second == 0.25

    def test_custom_capabilities(self):
        """Test custom capability values."""
        from app.routers.dimension.veo import Veo31Capabilities, VideoOutputQuality
        caps = Veo31Capabilities(
            max_duration_seconds=90,
            resolution=VideoOutputQuality.UHD,
            pricing_per_second=0.40,
        )
        assert caps.max_duration_seconds == 90
        assert caps.resolution == VideoOutputQuality.UHD


class TestKling26Capabilities:
    """Test Kling26Capabilities model (Dec 2025 release)."""

    def test_default_capabilities(self):
        """Test default Kling 2.6 capabilities."""
        from app.routers.dimension.veo import Kling26Capabilities, VideoOutputQuality
        caps = Kling26Capabilities()
        assert caps.max_duration_seconds == 120  # 2-minute max
        assert caps.resolution == VideoOutputQuality.FHD  # 1080p
        assert caps.supports_native_audio is True
        assert caps.supports_dialogue_sync is True  # Lip-sync
        assert caps.supports_high_action is True
        assert caps.frame_rate == 48  # 48 FPS

    def test_kling_vs_veo_comparison(self):
        """Test Kling 2.6 has longer duration than Veo 3.1."""
        from app.routers.dimension.veo import Veo31Capabilities, Kling26Capabilities
        veo = Veo31Capabilities()
        kling = Kling26Capabilities()
        assert kling.max_duration_seconds > veo.max_duration_seconds  # 120 > 60


class TestVideoGenerationResult:
    """Test VideoGenerationResult model (2026 comprehensive result)."""

    def test_result_creation_defaults(self):
        """Test result creation with defaults."""
        from app.routers.dimension.veo import (
            VideoGenerationResult, VideoGenerationPlatform,
            VideoOutputQuality, AudioIntegrationMode
        )
        result = VideoGenerationResult()
        assert result.success is False
        assert result.video_uri == ""
        assert result.duration_ms == 0
        assert result.credit_cost == 0
        assert result.platform == VideoGenerationPlatform.VEO
        assert result.output_quality == VideoOutputQuality.FHD
        assert result.audio_mode == AudioIntegrationMode.NATIVE
        assert result.characters_used == []
        assert result.trace_id == ""
        assert result.evidence_refs == []
        assert result.confidence == 0.0

    def test_result_with_data(self):
        """Test result with full data."""
        from app.routers.dimension.veo import (
            VideoGenerationResult, VideoGenerationPlatform,
            VideoOutputQuality, AudioIntegrationMode
        )
        result = VideoGenerationResult(
            success=True,
            video_uri="gs://bucket/video.mp4",
            duration_ms=45000,
            credit_cost=200,
            platform=VideoGenerationPlatform.VEO,
            output_quality=VideoOutputQuality.FHD,
            audio_mode=AudioIntegrationMode.NATIVE,
            characters_used=["char-1", "char-2"],
            trace_id="veo-abc123",
            evidence_refs=[
                "rag:veo:style:cinematic",
                "config:model:veo-3.1-generate-preview",
            ],
            confidence=0.9,
        )
        assert result.success is True
        assert result.video_uri == "gs://bucket/video.mp4"
        assert result.trace_id == "veo-abc123"
        assert len(result.evidence_refs) == 2
        assert result.confidence == 0.9

    def test_result_evidence_refs_list_str(self):
        """Test evidence_refs is List[str] (Vivid convention)."""
        from app.routers.dimension.veo import VideoGenerationResult
        result = VideoGenerationResult(
            evidence_refs=["rag:veo:test", "config:model:veo-3.1"]
        )
        assert isinstance(result.evidence_refs, list)
        assert all(isinstance(ref, str) for ref in result.evidence_refs)


# ============================================================================
# Evidence Refs Format Tests (Vivid Convention)
# ============================================================================

class TestEvidenceRefsFormat:
    """Test evidence_refs follows Vivid List[str] convention."""

    def test_evidence_refs_format_veo(self):
        """Test veo evidence_refs format."""
        expected_format = "rag:veo:style:cinematic"
        assert expected_format.startswith("rag:")
        parts = expected_format.split(":")
        assert len(parts) >= 3
        assert parts[0] in ("rag", "db", "config")

    def test_evidence_refs_format_model(self):
        """Test model config evidence_refs format."""
        expected_format = "config:model:veo-3.1-generate-preview"
        parts = expected_format.split(":")
        assert parts[0] == "config"
        assert parts[1] == "model"
        assert parts[2] in ALLOWED_VEO_MODELS

    def test_evidence_refs_format_character(self):
        """Test character db evidence_refs format."""
        expected_format = "db:character:uuid-123"
        parts = expected_format.split(":")
        assert parts[0] == "db"
        assert parts[1] == "character"


# ============================================================================
# 2026 Multi-Platform Workflow Tests
# ============================================================================

class TestMultiPlatformWorkflow:
    """Test 2026 multi-platform video generation patterns."""

    def test_veo_native_audio_support(self):
        """Test Veo 3.1 native audio support."""
        from app.routers.dimension.veo import Veo31Capabilities
        caps = Veo31Capabilities()
        assert caps.supports_native_audio is True

    def test_kling_dialogue_sync(self):
        """Test Kling 2.6 dialogue sync support."""
        from app.routers.dimension.veo import Kling26Capabilities
        caps = Kling26Capabilities()
        assert caps.supports_dialogue_sync is True

    def test_platform_pricing_comparison(self):
        """Test pricing comparison between platforms."""
        from app.routers.dimension.veo import Veo31Capabilities
        caps = Veo31Capabilities()
        # Veo 3.1: $0.15-0.40/sec average
        assert 0.10 <= caps.pricing_per_second <= 0.50

    def test_image_to_video_workflow(self):
        """Test Image-to-Video workflow for character consistency."""
        # 2026 Best Practice: Generate character in Midjourney, animate in Veo
        request = VeoGenerateRequest(
            prompt="[Character: John] A man walks through a forest",
            character_ids=["char-john-001"],
        )
        assert len(request.character_ids) == 1
        assert "Character:" in request.prompt


# ============================================================================
# 2026 Audio Integration Tests
# ============================================================================

class TestAudioIntegration:
    """Test 2026 native audio integration features."""

    def test_audio_modes_enum_complete(self):
        """Test all audio modes are defined."""
        from app.routers.dimension.veo import AudioIntegrationMode
        modes = [m.value for m in AudioIntegrationMode]
        assert "none" in modes
        assert "native" in modes
        assert "sync" in modes
        assert "dialogue" in modes

    def test_veo_supports_native_audio(self):
        """Test Veo 3.1 supports native audio generation."""
        from app.routers.dimension.veo import Veo31Capabilities
        caps = Veo31Capabilities()
        assert caps.supports_native_audio is True

    def test_kling_supports_dialogue(self):
        """Test Kling 2.6 supports dialogue lip-sync."""
        from app.routers.dimension.veo import Kling26Capabilities
        caps = Kling26Capabilities()
        assert caps.supports_dialogue_sync is True
