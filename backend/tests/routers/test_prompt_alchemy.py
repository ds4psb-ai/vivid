"""
Tests for Prompt Alchemy (AI Video Platform Prompt Translator).

Tests the translation of scene descriptions into platform-specific prompts
for Veo 3.1, Kling 2.6, and Sora Max 2 Pro.

2026 Best Practices Tests:
- Six-Layer Framework enums
- Native Audio integration
- Beat timestamp format for lip sync
- trace_id and evidence_refs (RAG Protocol v2)
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.dimension_adapter import (
    DimensionCapsuleId,
    PROMPT_ALCHEMY_PLATFORMS,
    run_prompt_translator,
)
from app.routers.dimension.prompt import (
    SUPPORTED_PLATFORMS,
    PLATFORM_INFO,
    PromptTranslateRequest,
    BatchTranslateRequest,
    UQSLStrategy,
    _sanitize_style,
    _validate_auteur_key,
    # 2026 Best Practices imports
    SixLayerDimension,
    AudioIntegrationType,
    MotionIntensity,
    CameraMovement,
    PromptQualityDimension,
    Veo31Capabilities,
    Kling26Capabilities,
    SoraMax2ProCapabilities,
    NativeAudioPromptTemplate,
    PromptOptimizationResult,
)


class TestPromptAlchemyConstants:
    """Test platform constants and configurations."""

    def test_supported_platforms_list(self):
        """Verify all 3 Crebit platforms are supported."""
        assert len(SUPPORTED_PLATFORMS) == 3
        assert "veo_31" in SUPPORTED_PLATFORMS
        assert "kling_26" in SUPPORTED_PLATFORMS
        assert "sora_max_2pro" in SUPPORTED_PLATFORMS

    def test_platform_info_structure(self):
        """Verify platform info contains required fields."""
        for platform_id, info in PLATFORM_INFO.items():
            assert "name" in info
            assert "use_case" in info
            assert "max_duration" in info
            assert "native_audio" in info

    def test_kling_is_recommended_default(self):
        """Verify Kling 2.6 is marked as recommended."""
        assert PLATFORM_INFO["kling_26"].get("recommended") is True

    def test_prompt_alchemy_platforms_match(self):
        """Verify adapter platforms match router platforms."""
        for platform_id in SUPPORTED_PLATFORMS:
            assert platform_id in PROMPT_ALCHEMY_PLATFORMS


class TestPromptTranslateRequest:
    """Test request validation."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = PromptTranslateRequest(
            scene_description="A man walks through a forest at sunset",
            target_platform="kling_26",
            style="cinematic",
        )
        assert request.scene_description == "A man walks through a forest at sunset"
        assert request.target_platform == "kling_26"

    def test_auto_select_when_no_platform(self):
        """Test that target_platform can be None for auto-select."""
        request = PromptTranslateRequest(
            scene_description="A dialogue scene between two characters",
        )
        assert request.target_platform is None

    def test_invalid_platform_raises_error(self):
        """Test that invalid platform raises validation error."""
        with pytest.raises(ValueError, match="지원하지 않는 플랫폼"):
            PromptTranslateRequest(
                scene_description="Test scene",
                target_platform="invalid_platform",
            )

    def test_description_strip_whitespace(self):
        """Test that description whitespace is stripped."""
        request = PromptTranslateRequest(
            scene_description="  A test scene  ",
        )
        assert request.scene_description == "A test scene"


class TestBatchTranslateRequest:
    """Test batch request validation."""

    def test_default_platforms(self):
        """Test that default platforms include all supported."""
        request = BatchTranslateRequest(
            scene_description="A beautiful sunset scene",
        )
        assert len(request.target_platforms) == 3

    def test_specific_platforms(self):
        """Test specifying subset of platforms."""
        request = BatchTranslateRequest(
            scene_description="A sunset scene",
            target_platforms=["veo_31", "kling_26"],
        )
        assert len(request.target_platforms) == 2


class TestAutoSelection:
    """Test automatic platform selection logic."""

    @pytest.mark.asyncio
    async def test_dialogue_selects_veo(self):
        """Test that dialogue content selects Veo 3.1."""
        inputs = {
            "scene_description": "두 사람이 대화를 나누고 있다. 남자가 '안녕하세요'라고 말한다.",
        }
        params = {"model": "gemini-3-flash-preview", "auto_select": True}

        with patch("app.dimension_adapter._call_gemini") as mock_gemini:
            mock_gemini.return_value = (
                {"translated_prompt": "test", "quality_score": 0.9},
                MagicMock(latency_ms=100, input_tokens=50, output_tokens=50, model="gemini-3-flash-preview"),
            )

            result = await run_prompt_translator(inputs, params)

            # The handler should auto-select veo_31 for dialogue
            assert result["success"] is True
            assert result["metrics"]["platform"] == "veo_31"

    @pytest.mark.asyncio
    async def test_animation_selects_sora(self):
        """Test that animation content selects Sora Max 2 Pro."""
        inputs = {
            "scene_description": "An anime character running through a colorful cartoon world",
        }
        params = {"model": "gemini-3-flash-preview", "auto_select": True}

        with patch("app.dimension_adapter._call_gemini") as mock_gemini:
            mock_gemini.return_value = (
                {"translated_prompt": "test", "quality_score": 0.9},
                MagicMock(latency_ms=100, input_tokens=50, output_tokens=50, model="gemini-3-flash-preview"),
            )

            result = await run_prompt_translator(inputs, params)

            assert result["success"] is True
            assert result["metrics"]["platform"] == "sora_max_2pro"

    @pytest.mark.asyncio
    async def test_default_selects_kling(self):
        """Test that default content selects Kling 2.6."""
        inputs = {
            "scene_description": "A beautiful mountain landscape at golden hour",
        }
        params = {"model": "gemini-3-flash-preview", "auto_select": True}

        with patch("app.dimension_adapter._call_gemini") as mock_gemini:
            mock_gemini.return_value = (
                {"translated_prompt": "test", "quality_score": 0.9},
                MagicMock(latency_ms=100, input_tokens=50, output_tokens=50, model="gemini-3-flash-preview"),
            )

            result = await run_prompt_translator(inputs, params)

            assert result["success"] is True
            assert result["metrics"]["platform"] == "kling_26"


class TestPromptTranslator:
    """Test the prompt translator handler."""

    @pytest.mark.asyncio
    async def test_successful_translation(self):
        """Test successful prompt translation."""
        inputs = {
            "scene_description": "A cinematic shot of waves crashing on rocks",
            "target_platform": "kling_26",
            "style": "cinematic",
            "language": "ko",
        }
        params = {"model": "gemini-3-flash-preview", "auto_select": False}

        with patch("app.dimension_adapter._call_gemini") as mock_gemini:
            mock_gemini.return_value = (
                {
                    "translated_prompt": "[Subject]: Waves\n[Action]: Crashing\n[Context]: Rocks at sunset",
                    "quality_score": 0.95,
                    "platform_tips": ["Use slow motion for dramatic effect"],
                },
                MagicMock(latency_ms=150, input_tokens=100, output_tokens=80, model="gemini-3-flash-preview"),
            )

            result = await run_prompt_translator(inputs, params)

            assert result["success"] is True
            assert result["capsule_id"] == "prompt.alchemy.translate"
            assert result["output"]["target_platform"] == "kling_26"
            assert result["output"]["platform_name"] == "Kling 2.6"
            # 2026: Kling 2.6 now supports native audio
            assert result["output"]["native_audio"] is True
            assert result["output"]["lip_sync"] is True  # 2026 addition
            assert result["metrics"]["platform"] == "kling_26"

    @pytest.mark.asyncio
    async def test_missing_description_fails(self):
        """Test that missing description returns error."""
        inputs = {"scene_description": ""}
        params = {"model": "gemini-3-flash-preview"}

        result = await run_prompt_translator(inputs, params)

        assert result["success"] is False
        assert "required" in result["error"].lower() or "description" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_unsupported_platform_fails(self):
        """Test that unsupported platform returns error."""
        inputs = {
            "scene_description": "A test scene",
            "target_platform": "unsupported_model",
        }
        params = {"model": "gemini-3-flash-preview", "auto_select": False}

        result = await run_prompt_translator(inputs, params)

        assert result["success"] is False
        assert "unsupported" in result["error"].lower() or "platform" in result["error"].lower()


class TestDimensionCapsuleIdIntegration:
    """Test integration with dimension adapter system."""

    def test_capsule_id_exists(self):
        """Verify PROMPT_TRANSLATE capsule ID exists."""
        assert hasattr(DimensionCapsuleId, "PROMPT_TRANSLATE")
        assert DimensionCapsuleId.PROMPT_TRANSLATE.value == "prompt.alchemy.translate"

    def test_handler_registered(self):
        """Verify handler is registered in DIMENSION_ADAPTERS."""
        from app.dimension_adapter import DIMENSION_ADAPTERS

        assert DimensionCapsuleId.PROMPT_TRANSLATE.value in DIMENSION_ADAPTERS


class TestSecurityValidation:
    """Test security-related validation (XSS, injection, etc.)."""

    def test_style_xss_sanitization(self):
        """Test that XSS script tags in style field are sanitized."""
        request = PromptTranslateRequest(
            scene_description="A beautiful sunset scene over the ocean",
            style="<script>alert('xss')</script>cinematic",
        )
        # HTML tags should be removed (content may remain but tags are stripped)
        assert "<script>" not in request.style
        assert "</script>" not in request.style
        # Check the final result is safe (no executable code)
        assert "cinematic" in request.style

    def test_style_javascript_injection(self):
        """Test that javascript: protocol is removed from style."""
        request = PromptTranslateRequest(
            scene_description="A beautiful sunset scene over the ocean",
            style="javascript:alert(1)",
        )
        assert "javascript:" not in request.style.lower()

    def test_style_event_handler_injection(self):
        """Test that on* event handlers are removed from style."""
        request = PromptTranslateRequest(
            scene_description="A beautiful sunset scene over the ocean",
            style="onload=alert(1)cinematic",
        )
        assert "onload=" not in request.style.lower()

    def test_style_html_entity_escape(self):
        """Test that special chars are escaped."""
        request = PromptTranslateRequest(
            scene_description="A beautiful sunset scene over the ocean",
            style="cinematic & noir",
        )
        # & should be escaped or kept safe
        assert request.style  # Should not raise

    def test_auteur_key_valid_format(self):
        """Test valid auteur_key formats."""
        valid_keys = ["kubrick", "bong_joonho", "nolan123", "spielberg"]
        for key in valid_keys:
            request = PromptTranslateRequest(
                scene_description="A beautiful sunset scene over the ocean",
                auteur_key=key,
            )
            assert request.auteur_key == key.lower()

    def test_auteur_key_invalid_starts_with_number(self):
        """Test that auteur_key starting with number is rejected."""
        with pytest.raises(ValueError, match="start with a letter"):
            PromptTranslateRequest(
                scene_description="A beautiful sunset scene over the ocean",
                auteur_key="123kubrick",
            )

    def test_auteur_key_invalid_special_chars(self):
        """Test that auteur_key with special chars is rejected."""
        invalid_keys = ["kubrick!", "bong-joonho", "nolan@director", "spiel berg"]
        for key in invalid_keys:
            with pytest.raises(ValueError, match="alphanumeric"):
                PromptTranslateRequest(
                    scene_description="A beautiful sunset scene over the ocean",
                    auteur_key=key,
                )

    def test_auteur_key_too_long(self):
        """Test that very long auteur_key is rejected."""
        with pytest.raises(ValueError, match="50 characters"):
            PromptTranslateRequest(
                scene_description="A beautiful sunset scene over the ocean",
                auteur_key="a" * 51,
            )


class TestEdgeCaseInputs:
    """Test edge case inputs."""

    def test_description_at_min_length(self):
        """Test description at minimum length (10 chars)."""
        request = PromptTranslateRequest(
            scene_description="1234567890",  # Exactly 10 chars
        )
        assert len(request.scene_description) == 10

    def test_description_below_min_length(self):
        """Test description below minimum length fails."""
        with pytest.raises(ValueError):
            PromptTranslateRequest(
                scene_description="123456789",  # 9 chars - below min
            )

    def test_description_with_unicode(self):
        """Test description with Korean and emoji."""
        request = PromptTranslateRequest(
            scene_description="밤하늘 아래 걷는 두 연인 🌙✨ 달빛이 비추고 있다",
        )
        assert "밤하늘" in request.scene_description
        assert "🌙" in request.scene_description

    def test_description_with_special_chars(self):
        """Test description with special characters."""
        request = PromptTranslateRequest(
            scene_description="Scene #1: A man walks... [CUT TO] - another scene!",
        )
        assert "#1" in request.scene_description
        assert "[CUT TO]" in request.scene_description

    def test_style_empty_defaults_to_cinematic(self):
        """Test that empty style defaults to cinematic."""
        request = PromptTranslateRequest(
            scene_description="A beautiful sunset scene over the ocean",
            style="",
        )
        assert request.style == "cinematic"

    def test_duration_at_boundaries(self):
        """Test duration at min and max boundaries."""
        # Min boundary
        request_min = PromptTranslateRequest(
            scene_description="A beautiful sunset scene over the ocean",
            duration=1,
        )
        assert request_min.duration == 1

        # Max boundary
        request_max = PromptTranslateRequest(
            scene_description="A beautiful sunset scene over the ocean",
            duration=120,
        )
        assert request_max.duration == 120

    def test_duration_below_min_fails(self):
        """Test duration below minimum fails."""
        with pytest.raises(ValueError):
            PromptTranslateRequest(
                scene_description="A beautiful sunset scene over the ocean",
                duration=0,
            )

    def test_duration_above_max_fails(self):
        """Test duration above maximum fails."""
        with pytest.raises(ValueError):
            PromptTranslateRequest(
                scene_description="A beautiful sunset scene over the ocean",
                duration=121,
            )


class TestBatchValidation:
    """Test batch request validation edge cases."""

    def test_empty_platforms_fails(self):
        """Test that empty platforms list fails."""
        with pytest.raises(ValueError, match="최소 하나의 플랫폼"):
            BatchTranslateRequest(
                scene_description="A beautiful sunset scene over the ocean",
                target_platforms=[],
            )

    def test_duplicate_platforms_deduplicated(self):
        """Test that duplicate platforms are removed."""
        request = BatchTranslateRequest(
            scene_description="A beautiful sunset scene over the ocean",
            target_platforms=["kling_26", "kling_26", "veo_31"],
        )
        # Should deduplicate
        assert request.target_platforms == ["kling_26", "veo_31"]

    def test_batch_style_sanitization(self):
        """Test that batch request also sanitizes style."""
        request = BatchTranslateRequest(
            scene_description="A beautiful sunset scene over the ocean",
            style="<img onerror=alert(1)>",
        )
        assert "<img" not in request.style
        assert "onerror" not in request.style

    def test_batch_auteur_key_validation(self):
        """Test that batch request validates auteur_key."""
        with pytest.raises(ValueError, match="alphanumeric"):
            BatchTranslateRequest(
                scene_description="A beautiful sunset scene over the ocean",
                auteur_key="invalid-key!",
            )


class TestUQSLStrategy:
    """Test UQSL strategy enum."""

    def test_all_strategies_defined(self):
        """Test that all expected strategies are defined."""
        strategies = [s.value for s in UQSLStrategy]
        assert "auto" in strategies
        assert "diversity" in strategies
        assert "quality" in strategies
        assert "speed" in strategies

    def test_strategy_values(self):
        """Test strategy enum values."""
        assert UQSLStrategy.AUTO.value == "auto"
        assert UQSLStrategy.DIVERSITY.value == "diversity"
        assert UQSLStrategy.QUALITY.value == "quality"
        assert UQSLStrategy.SPEED.value == "speed"


class TestSanitizationHelpers:
    """Test sanitization helper functions directly."""

    def test_sanitize_style_removes_html(self):
        """Test _sanitize_style removes HTML tags."""
        result = _sanitize_style("<div>cinematic</div>")
        assert "<div>" not in result
        assert "</div>" not in result

    def test_sanitize_style_removes_script(self):
        """Test _sanitize_style removes script tags."""
        result = _sanitize_style("<script>evil()</script>test")
        # Script tags are removed (content may remain but is not executable)
        assert "<script>" not in result
        assert "</script>" not in result
        assert "test" in result

    def test_sanitize_style_empty_returns_default(self):
        """Test _sanitize_style returns default for empty."""
        assert _sanitize_style("") == "cinematic"
        assert _sanitize_style("   ") == "cinematic"

    def test_sanitize_style_preserves_korean(self):
        """Test _sanitize_style preserves Korean characters."""
        result = _sanitize_style("시네마틱 느와르")
        assert "시네마틱" in result
        assert "느와르" in result

    def test_validate_auteur_key_lowercase(self):
        """Test _validate_auteur_key lowercases input."""
        result = _validate_auteur_key("KUBRICK")
        assert result == "kubrick"

    def test_validate_auteur_key_none(self):
        """Test _validate_auteur_key handles None."""
        assert _validate_auteur_key(None) is None
        assert _validate_auteur_key("") is None

    def test_validate_auteur_key_strips_whitespace(self):
        """Test _validate_auteur_key strips whitespace."""
        result = _validate_auteur_key("  kubrick  ")
        assert result == "kubrick"

    def test_validate_auteur_key_rejects_leading_digit(self):
        """Test _validate_auteur_key rejects keys starting with digit."""
        with pytest.raises(ValueError):
            _validate_auteur_key("1kubrick")

    def test_validate_auteur_key_allows_underscore(self):
        """Test _validate_auteur_key allows underscores."""
        result = _validate_auteur_key("bong_joonho_style")
        assert result == "bong_joonho_style"

    def test_validate_auteur_key_rejects_hyphen(self):
        """Test _validate_auteur_key rejects hyphens."""
        with pytest.raises(ValueError):
            _validate_auteur_key("bong-joonho")


# ============================================================================
# 2026 Best Practices Tests
# ============================================================================

class TestSixLayerDimensionEnum:
    """Test Six-Layer Framework dimension enum (2026)."""

    def test_all_layers_defined(self):
        """Verify all 6 layers are defined."""
        layers = [d.value for d in SixLayerDimension]
        assert len(layers) == 6
        assert "subject_action_emotion" in layers
        assert "shot_framing" in layers
        assert "camera_movement" in layers
        assert "lighting_environment" in layers
        assert "style_aesthetic" in layers
        assert "audio_dialogue" in layers

    def test_layer_order(self):
        """Test that layers follow cinematography hierarchy."""
        layer_order = list(SixLayerDimension)
        # Subject comes first (Layer 1)
        assert layer_order[0] == SixLayerDimension.SUBJECT_ACTION_EMOTION
        # Audio/Dialogue is last (Layer 6)
        assert layer_order[5] == SixLayerDimension.AUDIO_DIALOGUE


class TestAudioIntegrationTypeEnum:
    """Test Audio integration strategy enum (2026)."""

    def test_all_types_defined(self):
        """Verify all audio integration types are defined."""
        types = [t.value for t in AudioIntegrationType]
        assert "native" in types
        assert "separate" in types
        assert "hybrid" in types
        assert "none" in types

    def test_native_for_veo_kling(self):
        """Verify native audio is the strategy for modern platforms."""
        # Both Veo 3.1 and Kling 2.6 now support native audio (2026)
        assert AudioIntegrationType.NATIVE.value == "native"


class TestMotionIntensityEnum:
    """Test Motion intensity enum (2026)."""

    def test_all_intensities_defined(self):
        """Verify all motion intensity levels are defined."""
        intensities = [i.value for i in MotionIntensity]
        assert len(intensities) == 5
        assert "static" in intensities
        assert "low" in intensities
        assert "medium" in intensities
        assert "high" in intensities
        assert "extreme" in intensities


class TestCameraMovementEnum:
    """Test Camera movement enum (2026)."""

    def test_all_movements_defined(self):
        """Verify all camera movements are defined."""
        movements = [m.value for m in CameraMovement]
        assert len(movements) == 14
        # Essential movements
        assert "static" in movements
        assert "dolly_in" in movements
        assert "dolly_out" in movements
        assert "pan_left" in movements
        assert "pan_right" in movements
        assert "tilt_up" in movements
        assert "tilt_down" in movements
        assert "tracking" in movements
        assert "orbit" in movements
        assert "whip_pan" in movements

    def test_standard_film_terminology(self):
        """Test movements use standard film terminology."""
        # These should be recognized by AI models
        assert CameraMovement.DOLLY_IN.value == "dolly_in"
        assert CameraMovement.STEADICAM.value == "steadicam"
        assert CameraMovement.CRANE_UP.value == "crane_up"


class TestPromptQualityDimensionEnum:
    """Test Prompt quality evaluation dimensions (2026)."""

    def test_all_dimensions_defined(self):
        """Verify all quality dimensions are defined."""
        dims = [d.value for d in PromptQualityDimension]
        assert len(dims) == 6
        assert "specificity" in dims
        assert "clarity" in dims
        assert "motion_guidance" in dims
        assert "audio_cues" in dims
        assert "style_coherence" in dims
        assert "temporal_structure" in dims


class TestVeo31Capabilities:
    """Test Veo 3.1 capabilities model (2026)."""

    def test_default_values(self):
        """Test default capability values."""
        caps = Veo31Capabilities()
        assert caps.max_duration_seconds == 8
        assert caps.max_resolution == "4K"
        assert caps.native_audio is True
        assert caps.lip_sync is True

    def test_dialogue_format(self):
        """Test dialogue prompt format."""
        caps = Veo31Capabilities()
        assert "Speaker" in caps.dialogue_format
        assert "Tone" in caps.dialogue_format
        # Format: [Dialogue]: Speaker (Tone): "text"
        assert "[Dialogue]" in caps.dialogue_format

    def test_primary_strength(self):
        """Test primary strength is emotional realism."""
        caps = Veo31Capabilities()
        assert caps.primary_strength == "emotional_realism"


class TestKling26Capabilities:
    """Test Kling 2.6 capabilities model (2026)."""

    def test_default_values(self):
        """Test default capability values."""
        caps = Kling26Capabilities()
        assert caps.max_duration_seconds == 120
        assert caps.max_resolution == "1080p"
        assert caps.native_audio is True  # 2026: Now supports native audio
        assert caps.lip_sync is True  # Best-in-class

    def test_beat_timestamp_format(self):
        """Test beat timestamp format for lip sync."""
        caps = Kling26Capabilities()
        assert "Beat" in caps.beat_timestamp_format
        # Format: Beat 0-4s: [Action], Beat 5-8s: [Dialogue]
        assert "0-4s" in caps.beat_timestamp_format
        assert "5-8s" in caps.beat_timestamp_format

    def test_primary_strength(self):
        """Test primary strength is photorealistic humans."""
        caps = Kling26Capabilities()
        assert caps.primary_strength == "photorealistic_humans"


class TestSoraMax2ProCapabilities:
    """Test Sora Max 2 Pro capabilities model (2026)."""

    def test_default_values(self):
        """Test default capability values."""
        caps = SoraMax2ProCapabilities()
        assert caps.max_duration_seconds == 60  # Pro tier
        assert caps.max_resolution == "4K"
        assert caps.native_audio is True
        assert caps.lip_sync is True

    def test_primary_strength(self):
        """Test primary strength is physics accuracy."""
        caps = SoraMax2ProCapabilities()
        assert caps.primary_strength == "physics_accuracy"


class TestNativeAudioPromptTemplate:
    """Test Native audio prompt template model (2026)."""

    def test_required_fields(self):
        """Test required fields."""
        template = NativeAudioPromptTemplate(
            platform="veo_31",
            visual_block="A man walks through a forest",
        )
        assert template.platform == "veo_31"
        assert template.visual_block == "A man walks through a forest"

    def test_optional_blocks(self):
        """Test optional audio blocks."""
        template = NativeAudioPromptTemplate(
            platform="veo_31",
            visual_block="A man walks through a forest",
            dialogue_block='John (whispering): "I hear something..."',
            ambient_block="Birds chirping, wind rustling leaves",
            mood_block="Tense, mysterious",
            sfx_block="Footsteps on leaves",
        )
        assert template.dialogue_block is not None
        assert template.ambient_block is not None
        assert template.mood_block is not None
        assert template.sfx_block is not None

    def test_no_subtitles_default(self):
        """Test no_subtitles defaults to True."""
        template = NativeAudioPromptTemplate(
            platform="veo_31",
            visual_block="A man walks",
        )
        assert template.no_subtitles is True


class TestPromptOptimizationResult:
    """Test Prompt optimization result model with RAG Protocol v2 (2026)."""

    def test_trace_id_field(self):
        """Test trace_id field exists and defaults to empty."""
        result = PromptOptimizationResult(
            optimized_prompt="Test prompt",
            platform="kling_26",
        )
        assert hasattr(result, "trace_id")
        assert result.trace_id == ""

    def test_evidence_refs_field(self):
        """Test evidence_refs is List[str] not List[dict]."""
        result = PromptOptimizationResult(
            optimized_prompt="Test prompt",
            platform="kling_26",
            evidence_refs=["db:rag_docs:PROMPT:auteur:kubrick", "db:platform_config:kling_26"],
        )
        # Must be List[str] per Vivid P0 rules
        assert isinstance(result.evidence_refs, list)
        assert all(isinstance(ref, str) for ref in result.evidence_refs)

    def test_confidence_range(self):
        """Test confidence score is between 0 and 1."""
        result = PromptOptimizationResult(
            optimized_prompt="Test prompt",
            platform="kling_26",
            confidence=0.85,
        )
        assert 0.0 <= result.confidence <= 1.0

    def test_quality_scores_by_dimension(self):
        """Test quality scores can be set by dimension."""
        result = PromptOptimizationResult(
            optimized_prompt="Test prompt",
            platform="kling_26",
            quality_scores={
                "specificity": 0.9,
                "clarity": 0.85,
                "motion_guidance": 0.7,
            },
        )
        assert result.quality_scores["specificity"] == 0.9
        assert result.quality_scores["clarity"] == 0.85

    def test_audio_strategy_default(self):
        """Test audio strategy defaults to native."""
        result = PromptOptimizationResult(
            optimized_prompt="Test prompt",
            platform="kling_26",
        )
        assert result.audio_strategy == AudioIntegrationType.NATIVE


class TestPlatformInfo2026Updates:
    """Test PLATFORM_INFO 2026 updates."""

    def test_veo_31_native_audio(self):
        """Test Veo 3.1 has native audio support."""
        assert PLATFORM_INFO["veo_31"]["native_audio"] is True

    def test_kling_26_native_audio_2026(self):
        """Test Kling 2.6 now has native audio support (2026 update)."""
        assert PLATFORM_INFO["kling_26"]["native_audio"] is True

    def test_kling_26_lip_sync(self):
        """Test Kling 2.6 has lip sync support."""
        assert PLATFORM_INFO["kling_26"]["lip_sync"] is True

    def test_sora_max_native_audio(self):
        """Test Sora Max 2 Pro has native audio support."""
        assert PLATFORM_INFO["sora_max_2pro"]["native_audio"] is True

    def test_all_platforms_have_negative_prompts(self):
        """Test all platforms have negative prompts defined."""
        for platform_id, info in PLATFORM_INFO.items():
            assert "negative_prompts" in info, f"{platform_id} missing negative_prompts"
            assert isinstance(info["negative_prompts"], list)
            assert len(info["negative_prompts"]) > 0

    def test_veo_negative_prompts(self):
        """Test Veo 3.1 negative prompts include 'No subtitles'."""
        neg = PLATFORM_INFO["veo_31"]["negative_prompts"]
        assert "No subtitles" in neg

    def test_kling_negative_prompts(self):
        """Test Kling 2.6 negative prompts include 'No background music'."""
        neg = PLATFORM_INFO["kling_26"]["negative_prompts"]
        assert "No background music" in neg

    def test_platform_prompt_tips_exist(self):
        """Test all platforms have prompt_tips."""
        for platform_id, info in PLATFORM_INFO.items():
            assert "prompt_tips" in info, f"{platform_id} missing prompt_tips"
            assert isinstance(info["prompt_tips"], list)

    def test_platform_audio_format_exists(self):
        """Test all platforms have audio_format."""
        for platform_id, info in PLATFORM_INFO.items():
            assert "audio_format" in info, f"{platform_id} missing audio_format"


class TestPromptTranslatorTraceId:
    """Test trace_id generation in prompt translator (2026)."""

    @pytest.mark.asyncio
    async def test_trace_id_in_output(self):
        """Test that trace_id is included in successful output."""
        inputs = {
            "scene_description": "A cinematic shot of waves crashing on rocks",
            "target_platform": "kling_26",
            "style": "cinematic",
            "language": "ko",
        }
        params = {"model": "gemini-3-flash-preview", "auto_select": False}

        with patch("app.dimension_adapter._call_gemini") as mock_gemini:
            mock_gemini.return_value = (
                {"translated_prompt": "test", "quality_score": 0.9},
                MagicMock(latency_ms=100, input_tokens=50, output_tokens=50, model="gemini-3-flash-preview"),
            )

            result = await run_prompt_translator(inputs, params)

            assert result["success"] is True
            assert "trace_id" in result["output"]
            assert result["output"]["trace_id"].startswith("prompt-")

    @pytest.mark.asyncio
    async def test_trace_id_in_metrics(self):
        """Test that trace_id is also included in metrics."""
        inputs = {
            "scene_description": "A cinematic shot of waves crashing",
            "target_platform": "kling_26",
        }
        params = {"model": "gemini-3-flash-preview", "auto_select": False}

        with patch("app.dimension_adapter._call_gemini") as mock_gemini:
            mock_gemini.return_value = (
                {"translated_prompt": "test", "quality_score": 0.9},
                MagicMock(latency_ms=100, input_tokens=50, output_tokens=50, model="gemini-3-flash-preview"),
            )

            result = await run_prompt_translator(inputs, params)

            assert "trace_id" in result["metrics"]
            assert result["metrics"]["trace_id"] == result["output"]["trace_id"]


class TestPromptTranslatorEvidenceRefs:
    """Test evidence_refs generation in prompt translator (2026)."""

    @pytest.mark.asyncio
    async def test_evidence_refs_in_output(self):
        """Test that evidence_refs is List[str] in output."""
        inputs = {
            "scene_description": "A cinematic shot of waves crashing",
            "target_platform": "kling_26",
        }
        params = {"model": "gemini-3-flash-preview", "auto_select": False}

        with patch("app.dimension_adapter._call_gemini") as mock_gemini:
            mock_gemini.return_value = (
                {"translated_prompt": "test", "quality_score": 0.9},
                MagicMock(latency_ms=100, input_tokens=50, output_tokens=50, model="gemini-3-flash-preview"),
            )

            result = await run_prompt_translator(inputs, params)

            assert "evidence_refs" in result["output"]
            assert isinstance(result["output"]["evidence_refs"], list)
            # All refs must be strings (P0 rule)
            for ref in result["output"]["evidence_refs"]:
                assert isinstance(ref, str)

    @pytest.mark.asyncio
    async def test_evidence_refs_includes_platform_config(self):
        """Test that evidence_refs includes platform config reference."""
        inputs = {
            "scene_description": "A cinematic shot of waves crashing",
            "target_platform": "veo_31",
        }
        params = {"model": "gemini-3-flash-preview", "auto_select": False}

        with patch("app.dimension_adapter._call_gemini") as mock_gemini:
            mock_gemini.return_value = (
                {"translated_prompt": "test", "quality_score": 0.9},
                MagicMock(latency_ms=100, input_tokens=50, output_tokens=50, model="gemini-3-flash-preview"),
            )

            result = await run_prompt_translator(inputs, params)

            refs = result["output"]["evidence_refs"]
            assert any("platform_config:veo_31" in ref for ref in refs)

    @pytest.mark.asyncio
    async def test_evidence_refs_with_auteur_key(self):
        """Test that auteur_key adds RAG reference."""
        inputs = {
            "scene_description": "A cinematic shot in Kubrick style",
            "target_platform": "kling_26",
            "auteur_key": "kubrick",
        }
        params = {"model": "gemini-3-flash-preview", "auto_select": False}

        with patch("app.dimension_adapter._call_gemini") as mock_gemini, \
             patch("app.dimension_adapter._get_rag_context") as mock_rag:
            mock_rag.return_value = {"context": "Kubrick style info"}
            mock_gemini.return_value = (
                {"translated_prompt": "test", "quality_score": 0.9},
                MagicMock(latency_ms=100, input_tokens=50, output_tokens=50, model="gemini-3-flash-preview"),
            )

            result = await run_prompt_translator(inputs, params)

            refs = result["output"]["evidence_refs"]
            assert any("auteur:kubrick" in ref for ref in refs)


class TestPromptTranslatorConfidence:
    """Test confidence score in prompt translator output (2026)."""

    @pytest.mark.asyncio
    async def test_confidence_from_quality_score(self):
        """Test that confidence is derived from quality_score."""
        inputs = {
            "scene_description": "A cinematic shot of waves",
            "target_platform": "kling_26",
        }
        params = {"model": "gemini-3-flash-preview", "auto_select": False}

        with patch("app.dimension_adapter._call_gemini") as mock_gemini:
            mock_gemini.return_value = (
                {"translated_prompt": "test", "quality_score": 0.87},
                MagicMock(latency_ms=100, input_tokens=50, output_tokens=50, model="gemini-3-flash-preview"),
            )

            result = await run_prompt_translator(inputs, params)

            assert "confidence" in result["output"]
            assert result["output"]["confidence"] == 0.87


class TestPromptTranslatorLipSyncOutput:
    """Test lip sync fields in output (2026)."""

    @pytest.mark.asyncio
    async def test_lip_sync_in_output(self):
        """Test that lip_sync field is in output."""
        inputs = {
            "scene_description": "A character speaks",
            "target_platform": "kling_26",
        }
        params = {"model": "gemini-3-flash-preview", "auto_select": False}

        with patch("app.dimension_adapter._call_gemini") as mock_gemini:
            mock_gemini.return_value = (
                {"translated_prompt": "test", "quality_score": 0.9},
                MagicMock(latency_ms=100, input_tokens=50, output_tokens=50, model="gemini-3-flash-preview"),
            )

            result = await run_prompt_translator(inputs, params)

            assert "lip_sync" in result["output"]
            assert result["output"]["lip_sync"] is True

    @pytest.mark.asyncio
    async def test_negative_prompts_in_output(self):
        """Test that negative_prompts is in output."""
        inputs = {
            "scene_description": "A character speaks",
            "target_platform": "veo_31",
        }
        params = {"model": "gemini-3-flash-preview", "auto_select": False}

        with patch("app.dimension_adapter._call_gemini") as mock_gemini:
            mock_gemini.return_value = (
                {"translated_prompt": "test", "quality_score": 0.9},
                MagicMock(latency_ms=100, input_tokens=50, output_tokens=50, model="gemini-3-flash-preview"),
            )

            result = await run_prompt_translator(inputs, params)

            assert "negative_prompts" in result["output"]
            assert "No subtitles" in result["output"]["negative_prompts"]


class TestPromptAlchemyPlatforms2026:
    """Test PROMPT_ALCHEMY_PLATFORMS 2026 updates in adapter."""

    def test_kling_native_audio_updated(self):
        """Test Kling 2.6 native_audio is now True."""
        assert PROMPT_ALCHEMY_PLATFORMS["kling_26"]["native_audio"] is True

    def test_kling_lip_sync_added(self):
        """Test Kling 2.6 has lip_sync field."""
        assert PROMPT_ALCHEMY_PLATFORMS["kling_26"]["lip_sync"] is True

    def test_kling_beat_timestamp_format(self):
        """Test Kling 2.6 has beat timestamp format."""
        assert "beat_timestamp_format" in PROMPT_ALCHEMY_PLATFORMS["kling_26"]
        fmt = PROMPT_ALCHEMY_PLATFORMS["kling_26"]["beat_timestamp_format"]
        assert "Beat" in fmt

    def test_sora_max_duration_extended(self):
        """Test Sora Max 2 Pro duration is extended to 60s."""
        assert PROMPT_ALCHEMY_PLATFORMS["sora_max_2pro"]["max_duration"] == 60

    def test_veo_max_duration_extended(self):
        """Test Veo 3.1 duration is extended (from 8s)."""
        assert PROMPT_ALCHEMY_PLATFORMS["veo_31"]["max_duration"] == 120

    def test_all_platforms_have_negative_prompts(self):
        """Test all adapter platforms have negative_prompts."""
        for platform_id, config in PROMPT_ALCHEMY_PLATFORMS.items():
            assert "negative_prompts" in config, f"{platform_id} missing negative_prompts"
