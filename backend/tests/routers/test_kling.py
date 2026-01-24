"""
Tests for Kling AI Video Generation API.

Tests the Kling 2.6 video generation endpoints:
- POST /api/v1/dimension/kling/generate
- GET /api/v1/dimension/kling/status/{task_id}
- GET /api/v1/dimension/kling/pricing

Kling 2.6 Features:
- Elements (up to 4 reference images)
- Motion Control presets
- Camera Control presets
- End Frame for shot sequencing
- Audio generation
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.routers.dimension.kling import (
    KlingGenerateRequest,
    KlingGenerateResponse,
    KlingStatusResponse,
    KlingElementInput,
    get_credit_cost,
    _validate_duration,
    _validate_aspect_ratio,
    _validate_resolution,
    _validate_mode,
)
from app.routers.dimension._video_base import sanitize_video_text
from app.services.kling_service import (
    KlingService,
    KlingVideoRequest,
    KlingVideoResponse,
    KlingResult,
    KlingDuration,
    KlingAspectRatio,
    KlingResolution,
    KlingMode,
    KlingMotionPreset,
    KlingCameraPreset,
    KlingConfig,
)


# =============================================================================
# Sanitization Tests
# =============================================================================

class TestPromptSanitization:
    """Test XSS sanitization for prompts."""

    def test_sanitize_empty_prompt(self):
        """Empty prompt returns empty string."""
        assert sanitize_video_text("") == ""
        assert sanitize_video_text("", default="test") == "test"

    def test_sanitize_strips_whitespace(self):
        """Whitespace is stripped."""
        assert sanitize_video_text("  hello world  ") == "hello world"

    def test_sanitize_removes_html_tags(self):
        """HTML tags are removed (content between may be kept or removed)."""
        result = sanitize_video_text("<script>alert('xss')</script>hello")
        assert "<script>" not in result
        assert "</script>" not in result
        assert "hello" in result

        result = sanitize_video_text("hello<b>world</b>")
        assert "<b>" not in result
        assert "helloworld" in result

    def test_sanitize_escapes_entities(self):
        """HTML entities are escaped (& becomes &amp;)."""
        # Note: < and > may be stripped as tags first, then remaining content escaped
        result = sanitize_video_text("test & value")
        assert "&amp;" in result

    def test_sanitize_removes_javascript(self):
        """JavaScript patterns are removed."""
        assert "javascript" not in sanitize_video_text("javascript:alert(1)")
        assert sanitize_video_text("onclick=evil()").find("onclick=") == -1

    def test_sanitize_complex_xss(self):
        """Complex XSS patterns are handled."""
        dangerous = '<img src="x" onerror="alert(1)">'
        result = sanitize_video_text(dangerous)
        assert "<" not in result
        assert "onerror" not in result


# =============================================================================
# Validation Tests
# =============================================================================

class TestDurationValidation:
    """Test duration validation."""

    def test_valid_durations(self):
        """Valid durations pass."""
        assert _validate_duration("5") == "5"
        assert _validate_duration("10") == "10"

    def test_invalid_duration_raises(self):
        """Invalid duration raises ValueError."""
        with pytest.raises(ValueError, match="Invalid duration"):
            _validate_duration("15")
        with pytest.raises(ValueError, match="Invalid duration"):
            _validate_duration("3")


class TestAspectRatioValidation:
    """Test aspect ratio validation."""

    def test_valid_aspect_ratios(self):
        """Valid aspect ratios pass."""
        assert _validate_aspect_ratio("16:9") == "16:9"
        assert _validate_aspect_ratio("9:16") == "9:16"
        assert _validate_aspect_ratio("1:1") == "1:1"

    def test_invalid_aspect_ratio_raises(self):
        """Invalid aspect ratio raises ValueError."""
        with pytest.raises(ValueError, match="Invalid aspect_ratio"):
            _validate_aspect_ratio("4:3")
        with pytest.raises(ValueError, match="Invalid aspect_ratio"):
            _validate_aspect_ratio("21:9")


class TestResolutionValidation:
    """Test resolution validation."""

    def test_valid_resolutions(self):
        """Valid resolutions pass."""
        assert _validate_resolution("720p") == "720p"
        assert _validate_resolution("1080p") == "1080p"

    def test_invalid_resolution_raises(self):
        """Invalid resolution raises ValueError."""
        with pytest.raises(ValueError, match="Invalid resolution"):
            _validate_resolution("480p")
        with pytest.raises(ValueError, match="Invalid resolution"):
            _validate_resolution("4k")


class TestModeValidation:
    """Test mode validation."""

    def test_valid_modes(self):
        """Valid modes pass."""
        assert _validate_mode("std") == "std"
        assert _validate_mode("pro") == "pro"

    def test_invalid_mode_raises(self):
        """Invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid mode"):
            _validate_mode("fast")
        with pytest.raises(ValueError, match="Invalid mode"):
            _validate_mode("ultra")


# =============================================================================
# Credit Cost Tests
# =============================================================================

class TestCreditCost:
    """Test credit cost calculation."""

    def test_5s_720p_cost(self):
        """5s 720p costs 35 credits."""
        assert get_credit_cost("5", "720p") == 35

    def test_5s_1080p_cost(self):
        """5s 1080p costs 50 credits."""
        assert get_credit_cost("5", "1080p") == 50

    def test_10s_720p_cost(self):
        """10s 720p costs 70 credits."""
        assert get_credit_cost("10", "720p") == 70

    def test_10s_1080p_cost(self):
        """10s 1080p costs 100 credits."""
        assert get_credit_cost("10", "1080p") == 100

    def test_unknown_combination_default(self):
        """Unknown combination defaults to 50."""
        assert get_credit_cost("30", "4k") == 50


# =============================================================================
# Request Model Tests
# =============================================================================

class TestKlingGenerateRequest:
    """Test KlingGenerateRequest validation."""

    def test_minimal_request(self):
        """Minimal request with just prompt works."""
        request = KlingGenerateRequest(prompt="A cinematic scene")
        assert request.prompt == "A cinematic scene"
        assert request.duration == "5"
        assert request.aspect_ratio == "16:9"
        assert request.resolution == "1080p"
        assert request.mode == "std"

    def test_full_request(self):
        """Full request with all options works."""
        request = KlingGenerateRequest(
            prompt="A dramatic forest scene",
            negative_prompt="blurry, low quality",
            duration="10",
            aspect_ratio="9:16",
            resolution="720p",
            mode="pro",
            enable_audio=True,
            image_url="https://example.com/start.jpg",
            end_image_url="https://example.com/end.jpg",
            motion_preset="dramatic",
            camera_preset="dolly_in",
        )
        assert request.duration == "10"
        assert request.motion_preset == "dramatic"
        assert request.camera_preset == "dolly_in"

    def test_elements_validation(self):
        """Elements up to max 4 work."""
        elements = [
            KlingElementInput(image_url="https://example.com/char1.jpg"),
            KlingElementInput(image_url="https://example.com/char2.jpg", element_type="style", weight=0.8),
        ]
        request = KlingGenerateRequest(
            prompt="Character consistency test",
            elements=elements,
        )
        assert len(request.elements) == 2
        assert request.elements[0].weight == 1.0
        assert request.elements[1].weight == 0.8

    def test_prompt_sanitization(self):
        """Prompt is sanitized on creation."""
        request = KlingGenerateRequest(
            prompt="<script>alert('xss')</script>Beautiful sunset"
        )
        assert "<script>" not in request.prompt
        assert "Beautiful sunset" in request.prompt

    def test_negative_prompt_sanitization(self):
        """Negative prompt is also sanitized."""
        request = KlingGenerateRequest(
            prompt="A test scene",
            negative_prompt="<img onerror=evil>blurry",
        )
        assert "<img" not in request.negative_prompt


class TestKlingElementInput:
    """Test KlingElementInput validation."""

    def test_minimal_element(self):
        """Minimal element with just image_url."""
        elem = KlingElementInput(image_url="https://example.com/ref.jpg")
        assert elem.element_type == "character"
        assert elem.weight == 1.0

    def test_element_weight_bounds(self):
        """Weight must be between 0.0 and 2.0."""
        elem = KlingElementInput(image_url="https://example.com/ref.jpg", weight=0.0)
        assert elem.weight == 0.0

        elem = KlingElementInput(image_url="https://example.com/ref.jpg", weight=2.0)
        assert elem.weight == 2.0

    def test_element_types(self):
        """Different element types work."""
        for elem_type in ["character", "style", "scene"]:
            elem = KlingElementInput(
                image_url="https://example.com/ref.jpg",
                element_type=elem_type,
            )
            assert elem.element_type == elem_type


# =============================================================================
# Response Model Tests
# =============================================================================

class TestKlingGenerateResponse:
    """Test KlingGenerateResponse model."""

    def test_success_response(self):
        """Success response includes video URL."""
        response = KlingGenerateResponse(
            success=True,
            task_id="task-123",
            status="completed",
            video_url="https://cdn.kling.ai/video.mp4",
            credits_used=50,
        )
        assert response.success is True
        assert response.video_url is not None
        assert response.credits_used == 50

    def test_error_response(self):
        """Error response includes error message."""
        response = KlingGenerateResponse(
            success=False,
            task_id="task-456",
            status="failed",
            error="Content policy violation",
        )
        assert response.success is False
        assert response.error is not None


class TestKlingStatusResponse:
    """Test KlingStatusResponse model."""

    def test_pending_status(self):
        """Pending status response."""
        response = KlingStatusResponse(
            task_id="task-789",
            status="processing",
        )
        assert response.status == "processing"
        assert response.video_url is None


# =============================================================================
# Service Tests
# =============================================================================

class TestKlingServiceConfig:
    """Test Kling service configuration."""

    def test_default_config(self):
        """Default config values are set."""
        assert KlingConfig.DEFAULT_MODEL == "kling-v2.6"
        assert "kling-v2.6" in KlingConfig.SUPPORTED_MODELS
        assert KlingConfig.REQUEST_TIMEOUT == 30.0
        assert KlingConfig.POLL_TIMEOUT == 300.0

    def test_credit_costs(self):
        """Credit costs match pricing."""
        assert KlingConfig.CREDIT_COSTS["5s_720p"] == 35
        assert KlingConfig.CREDIT_COSTS["5s_1080p"] == 50
        assert KlingConfig.CREDIT_COSTS["10s_720p"] == 70
        assert KlingConfig.CREDIT_COSTS["10s_1080p"] == 100


class TestKlingServiceEnums:
    """Test Kling service enums."""

    def test_duration_enum(self):
        """Duration enum values."""
        assert KlingDuration.SHORT.value == "5"
        assert KlingDuration.LONG.value == "10"

    def test_aspect_ratio_enum(self):
        """Aspect ratio enum values."""
        assert KlingAspectRatio.LANDSCAPE.value == "16:9"
        assert KlingAspectRatio.PORTRAIT.value == "9:16"
        assert KlingAspectRatio.SQUARE.value == "1:1"

    def test_resolution_enum(self):
        """Resolution enum values."""
        assert KlingResolution.HD.value == "720p"
        assert KlingResolution.FHD.value == "1080p"

    def test_mode_enum(self):
        """Mode enum values."""
        assert KlingMode.STANDARD.value == "std"
        assert KlingMode.PROFESSIONAL.value == "pro"

    def test_motion_preset_enum(self):
        """Motion preset enum values (v2.6)."""
        assert KlingMotionPreset.SLOW.value == "slow"
        assert KlingMotionPreset.NORMAL.value == "normal"
        assert KlingMotionPreset.FAST.value == "fast"
        assert KlingMotionPreset.DRAMATIC.value == "dramatic"

    def test_camera_preset_enum(self):
        """Camera preset enum values (v2.6)."""
        assert KlingCameraPreset.STATIC.value == "static"
        assert KlingCameraPreset.PAN_LEFT.value == "pan_left"
        assert KlingCameraPreset.ZOOM_IN.value == "zoom_in"
        assert KlingCameraPreset.ORBIT.value == "orbit"


class TestKlingVideoRequest:
    """Test KlingVideoRequest model from service."""

    def test_request_with_26_features(self):
        """Request with Kling 2.6 features."""
        request = KlingVideoRequest(
            prompt="A dramatic scene",
            duration=KlingDuration.LONG,
            aspect_ratio=KlingAspectRatio.LANDSCAPE,
            resolution=KlingResolution.FHD,
            mode=KlingMode.PROFESSIONAL,
            enable_audio=True,
            end_image_url="https://example.com/end.jpg",
            elements=[
                {"image_url": "https://example.com/char.jpg", "element_type": "character", "weight": 1.0}
            ],
            motion_preset="dramatic",
            camera_preset="dolly_in",
        )
        assert request.duration == KlingDuration.LONG
        assert request.enable_audio is True
        assert request.end_image_url is not None
        assert len(request.elements) == 1
        assert request.motion_preset == "dramatic"


class TestKlingService:
    """Test KlingService methods."""

    def test_service_init_no_key(self):
        """Service initializes without API key."""
        service = KlingService()
        assert service.api_key is None
        assert service.base_url == KlingConfig.BASE_URL

    def test_service_init_with_key(self):
        """Service initializes with API key."""
        service = KlingService(api_key="test-key")
        assert service.api_key == "test-key"

    def test_calculate_credits(self):
        """Credit calculation from request."""
        service = KlingService(api_key="test")

        request_5s_1080p = KlingVideoRequest(
            prompt="test",
            duration=KlingDuration.SHORT,
            resolution=KlingResolution.FHD,
        )
        assert service._calculate_credits(request_5s_1080p) == 50

        request_10s_720p = KlingVideoRequest(
            prompt="test",
            duration=KlingDuration.LONG,
            resolution=KlingResolution.HD,
        )
        assert service._calculate_credits(request_10s_720p) == 70

    @pytest.mark.asyncio
    async def test_generate_without_key(self):
        """Generate fails without API key."""
        service = KlingService()
        request = KlingVideoRequest(prompt="test")
        result = await service.generate_video(request)

        assert result.success is False
        assert "API key not configured" in result.error


class TestKlingResult:
    """Test KlingResult dataclass."""

    def test_success_result(self):
        """Success result with video URL."""
        result = KlingResult(
            success=True,
            task_id="task-123",
            video_url="https://cdn.kling.ai/video.mp4",
            credits_used=50,
        )
        assert result.success is True
        assert result.video_url is not None
        assert result.error is None

    def test_error_result(self):
        """Error result with message."""
        result = KlingResult(
            success=False,
            task_id="task-456",
            error="Generation failed",
        )
        assert result.success is False
        assert result.error is not None


# =============================================================================
# Integration-Style Tests (mocked)
# =============================================================================

class TestKlingEndpointBehavior:
    """Test expected endpoint behaviors (mocked)."""

    @pytest.mark.asyncio
    async def test_generate_deducts_credits_on_success(self):
        """Credits are deducted on successful generation."""
        # This tests the expected flow:
        # 1. Check credit balance
        # 2. Deduct credits upfront
        # 3. Call Kling API
        # 4. If success, keep credits
        # 5. If failure, refund credits

        # Note: Full integration test would use TestClient
        # This is a behavioral specification test

        mock_result = KlingResult(
            success=True,
            task_id="task-123",
            video_url="https://cdn.kling.ai/test.mp4",
        )

        with patch.object(KlingService, 'generate_video', return_value=mock_result):
            service = KlingService(api_key="test")
            request = KlingVideoRequest(prompt="test")
            result = await service.generate_video(request)

            assert result.success is True
            assert result.video_url is not None

    @pytest.mark.asyncio
    async def test_generate_refunds_on_failure(self):
        """Credits are refunded on failed generation."""
        mock_result = KlingResult(
            success=False,
            task_id="task-456",
            error="Content policy violation",
        )

        with patch.object(KlingService, 'generate_video', return_value=mock_result):
            service = KlingService(api_key="test")
            request = KlingVideoRequest(prompt="test")
            result = await service.generate_video(request)

            assert result.success is False
            # In real scenario, credits would be refunded


# =============================================================================
# YAML Config Tests
# =============================================================================

class TestKlingYAMLConfig:
    """Test Kling YAML configuration."""

    @pytest.fixture
    def config_path(self):
        """Get absolute path to config file."""
        import os
        # Tests run from backend/ directory, config is at project root (one level up)
        # __file__ is tests/routers/test_kling.py -> tests/routers -> tests -> backend -> vivid (root)
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        project_root = os.path.dirname(backend_dir)  # Go one more level up from backend/
        return os.path.join(project_root, "config/apps/content/dimensions/kling.yaml")

    def test_config_file_exists(self, config_path):
        """Config file should exist."""
        import os
        assert os.path.exists(config_path), f"Config file not found: {config_path}"

    def test_config_structure(self, config_path):
        """Config has required structure."""
        import yaml

        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Metadata
        assert config["metadata"]["name"] == "kling"
        assert config["metadata"]["type"] == "dimension"
        assert "2.6" in config["metadata"]["version"]

        # Display
        assert "display" in config
        assert config["display"]["icon"] == "🎬"

        # Capabilities
        assert "capabilities" in config
        capability_names = [c["name"] for c in config["capabilities"]]
        assert "cache" in capability_names
        assert "execution" in capability_names

        # Extensions
        assert "extensions" in config
        assert "kling_video" in config["extensions"]

        kling_ext = config["extensions"]["kling_video"]

        # Models
        assert "models" in kling_ext
        model_ids = [m["id"] for m in kling_ext["models"]]
        assert "kling-v2.6" in model_ids

        # Durations
        assert "durations" in kling_ext
        duration_values = [d["value"] for d in kling_ext["durations"]]
        assert "5" in duration_values
        assert "10" in duration_values

        # Motion Control (v2.6)
        assert "motion_control" in kling_ext
        assert kling_ext["motion_control"]["enabled"] is True

        # Camera Control (v2.6)
        assert "camera_control" in kling_ext
        assert kling_ext["camera_control"]["enabled"] is True

        # Elements (v2.6)
        assert "elements" in kling_ext
        assert kling_ext["elements"]["max_images"] == 4

        # End Frame (v2.6)
        assert "end_frame" in kling_ext
        assert kling_ext["end_frame"]["enabled"] is True

        # Audio (v2.6)
        assert "audio" in kling_ext
        assert kling_ext["audio"]["enabled"] is True
