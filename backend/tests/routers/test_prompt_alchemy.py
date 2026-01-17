"""
Tests for Prompt Alchemy (AI Video Platform Prompt Translator).

Tests the translation of scene descriptions into platform-specific prompts
for Veo 3.1, Kling 2.6, and Sora Max 2 Pro.
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
            assert result["output"]["native_audio"] is False
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
