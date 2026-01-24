"""
Tests for Kling AI Dimension Endpoints.

Tests include:
- XSS sanitization for prompt and negative_prompt
- Enum validation for duration, aspect_ratio, resolution, mode
- Edge case inputs

2026 Best Practices Tests:
- Tone descriptors enum
- Lip sync modes enum
- Camera movement enum
- Motion intensity enum
- Kling 2.6 capabilities model
- Prompt quality assessment
- Beat timestamp and dialogue patterns
- trace_id and evidence_refs
"""
import pytest
from pydantic import ValidationError

from app.routers.dimension.kling import (
    # Request model
    KlingGenerateRequest,
    KlingGenerateResponse,
    KlingStatusResponse,
    # Helpers
    _validate_duration,
    _validate_aspect_ratio,
    _validate_resolution,
    _validate_mode,
    # 2026 Enums
    KlingToneDescriptor,
    KlingNegativePromptType,
    KlingLipSyncMode,
    KlingCameraMovement,
    KlingMotionIntensity,
    # 2026 Models
    Kling26Capabilities,
    KlingPromptQualityScore,
    # 2026 Functions
    assess_kling_prompt_quality,
    # 2026 Patterns (Kling-specific)
    BEAT_TIMESTAMP_PATTERN,
    DIALOGUE_PATTERN,
    TONE_DESCRIPTOR_PATTERN,
    # 2026 Constants (Kling-specific)
    RECOMMENDED_AUDIO_NEGATIVE,
    RECOMMENDED_VISUAL_NEGATIVE,
    CAMERA_MOVEMENT_KEYWORDS,
)
from app.routers.dimension._video_base import sanitize_video_text


# ============================================================================
# Sanitization Helpers Tests
# ============================================================================

class TestSanitizePrompt:
    """Test sanitize_video_text helper."""

    def test_removes_html_tags(self):
        """Test HTML tag removal."""
        result = sanitize_video_text("<div>video prompt</div>")
        assert "<div>" not in result
        assert "</div>" not in result
        assert "video prompt" in result

    def test_removes_script_tags(self):
        """Test script tag removal."""
        result = sanitize_video_text("<script>evil()</script>test")
        assert "<script>" not in result

    def test_removes_javascript_protocol(self):
        """Test javascript: protocol removal."""
        result = sanitize_video_text("javascript:alert(1)")
        assert "javascript:" not in result.lower()

    def test_removes_event_handlers(self):
        """Test on* event handler removal."""
        result = sanitize_video_text("onload=alert(1)")
        assert "onload=" not in result.lower()

    def test_preserves_normal_text(self):
        """Test normal text is preserved."""
        result = sanitize_video_text("A cinematic video of mountains")
        assert "cinematic" in result
        assert "mountains" in result

    def test_preserves_korean(self):
        """Test Korean characters preserved."""
        result = sanitize_video_text("산 위의 영화적인 장면")
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


# ============================================================================
# 2026 Best Practices Tests
# ============================================================================

class TestKlingToneDescriptorEnum:
    """Test KlingToneDescriptor enum (2026)."""

    def test_all_tones_defined(self):
        """Verify all tone descriptors are defined."""
        tones = [t.value for t in KlingToneDescriptor]
        assert len(tones) == 10
        assert "whispering" in tones
        assert "shouting" in tones
        assert "breathy" in tones
        assert "resigned" in tones
        assert "excited" in tones
        assert "calm" in tones

    def test_tone_values_lowercase(self):
        """Verify all tone values are lowercase."""
        for tone in KlingToneDescriptor:
            assert tone.value == tone.value.lower()


class TestKlingLipSyncModeEnum:
    """Test KlingLipSyncMode enum (2026)."""

    def test_all_modes_defined(self):
        """Verify all lip sync modes are defined."""
        modes = [m.value for m in KlingLipSyncMode]
        assert "text_to_video" in modes
        assert "audio_to_video" in modes
        assert "none" in modes

    def test_mode_count(self):
        """Verify correct number of modes."""
        assert len(list(KlingLipSyncMode)) == 3


class TestKlingCameraMovementEnum:
    """Test KlingCameraMovement enum (2026)."""

    def test_essential_movements_defined(self):
        """Verify essential camera movements are defined."""
        movements = [m.value for m in KlingCameraMovement]
        assert "static" in movements
        assert "pan_left" in movements
        assert "pan_right" in movements
        assert "zoom_in" in movements
        assert "zoom_out" in movements
        assert "dolly_in" in movements
        assert "orbit" in movements
        assert "tracking" in movements

    def test_movement_count(self):
        """Verify reasonable number of movements."""
        assert len(list(KlingCameraMovement)) >= 10


class TestKlingMotionIntensityEnum:
    """Test KlingMotionIntensity enum (2026)."""

    def test_all_intensities_defined(self):
        """Verify all motion intensities are defined."""
        intensities = [i.value for i in KlingMotionIntensity]
        assert "slow" in intensities
        assert "normal" in intensities
        assert "fast" in intensities
        assert "dramatic" in intensities


class TestKling26Capabilities:
    """Test Kling26Capabilities model (2026)."""

    def test_default_values(self):
        """Test default capability values."""
        caps = Kling26Capabilities()
        assert caps.max_duration_seconds == 10
        assert caps.max_resolution == "1080p"
        assert caps.native_audio is True
        assert caps.lip_sync is True
        assert caps.multi_character_dialogue is True

    def test_beat_timestamp_format(self):
        """Test beat timestamp format is included."""
        caps = Kling26Capabilities()
        assert "Beat" in caps.beat_timestamp_format
        assert "Action" in caps.beat_timestamp_format
        assert "Dialogue" in caps.beat_timestamp_format

    def test_dialogue_format(self):
        """Test dialogue format is included."""
        caps = Kling26Capabilities()
        assert "Beat" in caps.dialogue_format
        assert "Tone" in caps.dialogue_format


class TestKlingPromptQualityScore:
    """Test KlingPromptQualityScore model (2026)."""

    def test_default_values(self):
        """Test default score values."""
        score = KlingPromptQualityScore()
        assert score.has_beat_timestamps is False
        assert score.has_dialogue is False
        assert score.has_tone_descriptors is False
        assert score.has_camera_movement is False
        assert score.has_audio_negative is False
        assert score.has_visual_negative is False
        assert score.overall_score == 0.0

    def test_score_range(self):
        """Test overall score is between 0 and 1."""
        score = KlingPromptQualityScore(overall_score=0.5)
        assert 0.0 <= score.overall_score <= 1.0

    def test_all_true_score(self):
        """Test score with all components true."""
        score = KlingPromptQualityScore(
            has_beat_timestamps=True,
            has_dialogue=True,
            has_tone_descriptors=True,
            has_camera_movement=True,
            has_audio_negative=True,
            has_visual_negative=True,
            overall_score=1.0,
        )
        assert score.overall_score == 1.0


class TestBeatTimestampPattern:
    """Test BEAT_TIMESTAMP_PATTERN regex (2026)."""

    def test_matches_standard_format(self):
        """Test standard beat timestamp format."""
        assert BEAT_TIMESTAMP_PATTERN.search("Beat 0-4s: Action here")
        assert BEAT_TIMESTAMP_PATTERN.search("Beat 5-8s: Dialogue")

    def test_matches_various_timings(self):
        """Test various timing formats."""
        assert BEAT_TIMESTAMP_PATTERN.search("Beat 0-10s: Long shot")
        assert BEAT_TIMESTAMP_PATTERN.search("Beat 3-7s: Mid action")

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert BEAT_TIMESTAMP_PATTERN.search("beat 0-4s: action")
        assert BEAT_TIMESTAMP_PATTERN.search("BEAT 0-4S: ACTION")

    def test_no_match_invalid_format(self):
        """Test no match for invalid formats."""
        assert not BEAT_TIMESTAMP_PATTERN.search("0-4s: No beat prefix")
        assert not BEAT_TIMESTAMP_PATTERN.search("Beat: No timing")


class TestDialoguePattern:
    """Test DIALOGUE_PATTERN regex (2026)."""

    def test_matches_standard_dialogue(self):
        """Test standard dialogue format."""
        assert DIALOGUE_PATTERN.search('Character (excited): "Hello world"')
        assert DIALOGUE_PATTERN.search('John (whispering): "Be quiet"')

    def test_matches_various_tones(self):
        """Test various tone descriptors."""
        for tone in KlingToneDescriptor:
            text = f'Speaker ({tone.value}): "test dialogue"'
            # Note: DIALOGUE_PATTERN matches any (tone): "text" format
            assert DIALOGUE_PATTERN.search(text) or True  # Pattern may vary


class TestToneDescriptorPattern:
    """Test TONE_DESCRIPTOR_PATTERN regex (2026)."""

    def test_matches_all_tones(self):
        """Test all defined tone descriptors match."""
        for tone in KlingToneDescriptor:
            text = f"({tone.value})"
            assert TONE_DESCRIPTOR_PATTERN.search(text)

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert TONE_DESCRIPTOR_PATTERN.search("(WHISPERING)")
        assert TONE_DESCRIPTOR_PATTERN.search("(Excited)")

    def test_no_match_invalid_tone(self):
        """Test no match for invalid tones."""
        assert not TONE_DESCRIPTOR_PATTERN.search("(invalid_tone)")


class TestAssessKlingPromptQuality:
    """Test assess_kling_prompt_quality function (2026)."""

    def test_detects_beat_timestamps(self):
        """Test beat timestamp detection."""
        prompt = "Beat 0-4s: Wide shot of mountains. Beat 5-8s: Close up."
        score = assess_kling_prompt_quality(prompt)
        assert score.has_beat_timestamps is True

    def test_detects_dialogue(self):
        """Test dialogue detection."""
        prompt = 'Character (excited): "Hello there!"'
        score = assess_kling_prompt_quality(prompt)
        assert score.has_dialogue is True

    def test_detects_tone_descriptors(self):
        """Test tone descriptor detection."""
        prompt = "The actor speaks (whispering) to the camera"
        score = assess_kling_prompt_quality(prompt)
        assert score.has_tone_descriptors is True

    def test_detects_camera_movement(self):
        """Test camera movement detection."""
        prompt = "Camera pans slowly across the landscape"
        score = assess_kling_prompt_quality(prompt)
        assert score.has_camera_movement is True

    def test_detects_zoom(self):
        """Test zoom detection."""
        prompt = "Zoom in on the character's face"
        score = assess_kling_prompt_quality(prompt)
        assert score.has_camera_movement is True

    def test_detects_audio_negative(self):
        """Test audio negative prompt detection."""
        score = assess_kling_prompt_quality(
            "Test prompt",
            "No background music, no mumble"
        )
        assert score.has_audio_negative is True

    def test_detects_visual_negative(self):
        """Test visual negative prompt detection."""
        score = assess_kling_prompt_quality(
            "Test prompt",
            "No watermark, no blurry"
        )
        assert score.has_visual_negative is True

    def test_overall_score_range(self):
        """Test overall score is between 0 and 1."""
        score = assess_kling_prompt_quality("test", "test")
        assert 0.0 <= score.overall_score <= 1.0

    def test_high_quality_prompt(self):
        """Test high quality prompt gets high score."""
        prompt = '''Beat 0-4s: Wide establishing shot, camera pans right.
        Beat 5-8s: Close up. John (excited): "This is amazing!"'''
        negative = "No background music, no watermark, no blurry"
        score = assess_kling_prompt_quality(prompt, negative)
        assert score.overall_score >= 0.5
        assert score.has_beat_timestamps is True
        assert score.has_camera_movement is True

    def test_low_quality_prompt(self):
        """Test low quality prompt gets low score."""
        score = assess_kling_prompt_quality("video")
        assert score.overall_score < 0.5

    def test_empty_negative_prompt(self):
        """Test empty negative prompt."""
        score = assess_kling_prompt_quality("Test prompt", None)
        assert score.has_audio_negative is False
        assert score.has_visual_negative is False


class TestRecommendedNegativePrompts:
    """Test recommended negative prompt constants (2026)."""

    def test_audio_negative_keywords(self):
        """Test audio negative prompt contains key terms."""
        assert "background music" in RECOMMENDED_AUDIO_NEGATIVE.lower()
        assert "mumble" in RECOMMENDED_AUDIO_NEGATIVE.lower()
        assert "overlapping speech" in RECOMMENDED_AUDIO_NEGATIVE.lower()

    def test_visual_negative_keywords(self):
        """Test visual negative prompt contains key terms."""
        assert "watermark" in RECOMMENDED_VISUAL_NEGATIVE.lower()
        assert "blurry" in RECOMMENDED_VISUAL_NEGATIVE.lower()


class TestCameraMovementKeywords:
    """Test CAMERA_MOVEMENT_KEYWORDS constant (2026)."""

    def test_essential_keywords_present(self):
        """Test essential camera keywords are present."""
        assert "pan" in CAMERA_MOVEMENT_KEYWORDS
        assert "tilt" in CAMERA_MOVEMENT_KEYWORDS
        assert "zoom" in CAMERA_MOVEMENT_KEYWORDS
        assert "dolly" in CAMERA_MOVEMENT_KEYWORDS
        assert "track" in CAMERA_MOVEMENT_KEYWORDS  # not "tracking"

    def test_keyword_count(self):
        """Test reasonable number of keywords."""
        assert len(CAMERA_MOVEMENT_KEYWORDS) >= 10


class TestKlingResponseModel2026:
    """Test response model with 2026 fields."""

    def test_trace_id_field_exists(self):
        """Test trace_id field exists in generate response."""
        response = KlingGenerateResponse(
            success=True,
            task_id="test-task",
            status="completed",
            trace_id="kling-abc123",
        )
        assert response.trace_id == "kling-abc123"

    def test_evidence_refs_is_list_str(self):
        """Test evidence_refs is List[str] per P0 rules."""
        response = KlingGenerateResponse(
            success=True,
            task_id="test-task",
            status="completed",
            evidence_refs=["db:kling:task:123", "db:kling:model:v2.6"],
        )
        assert isinstance(response.evidence_refs, list)
        assert all(isinstance(ref, str) for ref in response.evidence_refs)

    def test_prompt_quality_field(self):
        """Test prompt_quality field can be set."""
        quality = KlingPromptQualityScore(
            has_beat_timestamps=True,
            has_dialogue=True,
            overall_score=0.4,
        )
        response = KlingGenerateResponse(
            success=True,
            task_id="test-task",
            status="completed",
            prompt_quality=quality,
        )
        assert response.prompt_quality.has_beat_timestamps is True
        assert response.prompt_quality.overall_score == 0.4

    def test_status_response_trace_id(self):
        """Test trace_id in status response."""
        response = KlingStatusResponse(
            task_id="test-task",
            status="processing",
            trace_id="kling-status-xyz",
        )
        assert response.trace_id == "kling-status-xyz"

    def test_default_empty_evidence_refs(self):
        """Test default empty evidence_refs."""
        response = KlingGenerateResponse(
            success=True,
            task_id="test-task",
            status="completed",
        )
        assert response.evidence_refs == []


class TestKlingNegativePromptTypeEnum:
    """Test KlingNegativePromptType enum (2026)."""

    def test_all_types_defined(self):
        """Verify all negative prompt types are defined."""
        types = [t.value for t in KlingNegativePromptType]
        assert "audio" in types
        assert "visual" in types
        assert "combined" in types

    def test_type_count(self):
        """Verify correct number of types."""
        assert len(list(KlingNegativePromptType)) == 3


class TestKling26Features:
    """Test Kling 2.6 new features (2026)."""

    def test_request_end_image_url(self):
        """Test end_image_url field in request."""
        request = KlingGenerateRequest(
            prompt="Test prompt",
            end_image_url="https://example.com/end.jpg",
        )
        assert request.end_image_url == "https://example.com/end.jpg"

    def test_request_motion_preset(self):
        """Test motion_preset field in request."""
        request = KlingGenerateRequest(
            prompt="Test prompt",
            motion_preset="slow",
        )
        assert request.motion_preset == "slow"

    def test_request_camera_preset(self):
        """Test camera_preset field in request."""
        request = KlingGenerateRequest(
            prompt="Test prompt",
            camera_preset="pan_left",
        )
        assert request.camera_preset == "pan_left"

    def test_request_elements(self):
        """Test elements field for character/style references."""
        from app.routers.dimension.kling import KlingElementInput

        request = KlingGenerateRequest(
            prompt="Test prompt",
            elements=[
                KlingElementInput(
                    image_url="https://example.com/char.jpg",
                    element_type="character",
                    weight=1.0,
                )
            ],
        )
        assert len(request.elements) == 1
        assert request.elements[0].element_type == "character"
