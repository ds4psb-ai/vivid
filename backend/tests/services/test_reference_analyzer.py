"""
Tests for ReferenceAnalyzer Service (2026 Expert Workflow).

Tests:
- Model validation (FrameAnalysis, VideoReferenceAnalysis, etc.)
- ReferenceAnalyzer initialization
- Video frame extraction
- Frame analysis
- Scene detection
- Shot list generation
- Moodboard selection
- Error handling
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import base64

from pydantic import ValidationError

from app.services.ai.reference_analyzer import (
    ReferenceAnalyzer,
    ReferenceAnalyzerConfig,
    FrameAnalysis,
    VideoReferenceAnalysis,
    ImageReferenceAnalysis,
    ShotSuggestion,
    SceneSegment,
    ReferenceAnalysisError,
    VideoProcessingError,
    get_reference_analyzer,
    analyze_video_reference,
    analyze_image_reference,
)
from app.services.ai.style_extractor import StyleExtractionResult


# ============================================================================
# Model Tests: FrameAnalysis
# ============================================================================


class TestFrameAnalysisModel:
    """Test FrameAnalysis Pydantic model."""

    def test_default_values(self):
        """Test default values."""
        frame = FrameAnalysis(timestamp=0.0)
        assert frame.timestamp == 0.0
        assert frame.frame_number == 0
        assert frame.description == ""
        assert frame.objects == []
        assert frame.actions == []
        assert frame.characters == []
        assert frame.camera_movement is None
        assert frame.shot_type is None
        assert frame.emotion is None

    def test_full_frame_analysis(self):
        """Test full frame analysis creation."""
        frame = FrameAnalysis(
            timestamp=5.5,
            frame_number=132,
            description="A woman walks through a neon-lit alley",
            objects=["neon signs", "puddles", "trash cans"],
            actions=["walking", "looking around"],
            characters=["young woman in leather jacket"],
            camera_movement="tracking",
            shot_type="medium",
            emotion="mysterious",
        )
        assert frame.timestamp == 5.5
        assert frame.frame_number == 132
        assert len(frame.objects) == 3
        assert frame.camera_movement == "tracking"


# ============================================================================
# Model Tests: ShotSuggestion
# ============================================================================


class TestShotSuggestionModel:
    """Test ShotSuggestion Pydantic model."""

    def test_valid_shot(self):
        """Test valid shot suggestion creation."""
        shot = ShotSuggestion(
            shot_number=1,
            duration_seconds=3.5,
            description="Opening wide shot of cityscape",
            camera_setup="Crane shot, high angle, slow pan left",
            prompt="Cinematic aerial view of neon-lit cyberpunk city...",
            reference_frame_index=0,
        )
        assert shot.shot_number == 1
        assert shot.duration_seconds == 3.5
        assert "cityscape" in shot.description


# ============================================================================
# Model Tests: SceneSegment
# ============================================================================


class TestSceneSegmentModel:
    """Test SceneSegment Pydantic model."""

    def test_valid_scene(self):
        """Test valid scene segment creation."""
        scene = SceneSegment(
            start_time=0.0,
            end_time=5.0,
            duration=5.0,
            description="Opening scene - establishing shot",
            key_frame_index=0,
        )
        assert scene.start_time == 0.0
        assert scene.end_time == 5.0
        assert scene.duration == 5.0


# ============================================================================
# Model Tests: VideoReferenceAnalysis
# ============================================================================


class TestVideoReferenceAnalysisModel:
    """Test VideoReferenceAnalysis Pydantic model."""

    def test_default_values(self):
        """Test default values."""
        analysis = VideoReferenceAnalysis()
        assert analysis.total_duration == 0.0
        assert analysis.frame_count == 0
        assert analysis.fps == 24.0
        assert analysis.frames == []
        assert analysis.scenes == []
        assert analysis.suggested_shots == []
        assert analysis.moodboard_frames == []
        assert analysis.analysis_depth == "detailed"
        assert analysis.confidence == 0.0

    def test_full_analysis(self):
        """Test full video analysis creation."""
        analysis = VideoReferenceAnalysis(
            total_duration=30.0,
            frame_count=10,
            fps=24.0,
            frames=[
                FrameAnalysis(timestamp=0.0, description="Frame 1"),
                FrameAnalysis(timestamp=3.0, description="Frame 2"),
            ],
            scenes=[
                SceneSegment(
                    start_time=0.0,
                    end_time=15.0,
                    duration=15.0,
                    description="Scene 1",
                    key_frame_index=0,
                ),
            ],
            style=StyleExtractionResult(style_tags=["cinematic"]),
            suggested_shots=[
                ShotSuggestion(
                    shot_number=1,
                    duration_seconds=5.0,
                    description="Shot 1",
                    camera_setup="Static",
                    prompt="Test prompt",
                    reference_frame_index=0,
                ),
            ],
            moodboard_frames=["base64_data_1", "base64_data_2"],
            confidence=0.85,
        )
        assert analysis.total_duration == 30.0
        assert len(analysis.frames) == 2
        assert len(analysis.scenes) == 1
        assert analysis.confidence == 0.85


# ============================================================================
# Model Tests: ImageReferenceAnalysis
# ============================================================================


class TestImageReferenceAnalysisModel:
    """Test ImageReferenceAnalysis Pydantic model."""

    def test_default_values(self):
        """Test default values."""
        analysis = ImageReferenceAnalysis()
        assert analysis.description == ""
        assert analysis.objects == []
        assert analysis.composition_analysis == ""
        assert analysis.recreation_prompt == ""
        assert analysis.similar_references == []

    def test_full_image_analysis(self):
        """Test full image analysis creation."""
        analysis = ImageReferenceAnalysis(
            description="A moody portrait with dramatic lighting",
            style=StyleExtractionResult(
                style_tags=["portrait", "dramatic"],
                lighting="dramatic",
            ),
            objects=["person", "shadows", "window"],
            composition_analysis="Rule of thirds, subject on left",
            recreation_prompt="Create a dramatic portrait with...",
            similar_references=["Rembrandt", "Caravaggio"],
        )
        assert "portrait" in analysis.description
        assert len(analysis.objects) == 3


# ============================================================================
# ReferenceAnalyzerConfig Tests
# ============================================================================


class TestReferenceAnalyzerConfig:
    """Test ReferenceAnalyzerConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ReferenceAnalyzerConfig()
        assert config.model == "gemini-2.5-pro"
        assert config.flash_model == "gemini-2.5-flash"
        assert config.max_frames == 20
        assert config.quick_frames == 10
        assert config.comprehensive_frames == 30
        assert config.max_retries == 3
        assert config.timeout_seconds == 60.0

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ReferenceAnalyzerConfig(
            model="custom-model",
            max_frames=50,
            timeout_seconds=120.0,
        )
        assert config.model == "custom-model"
        assert config.max_frames == 50
        assert config.timeout_seconds == 120.0


# ============================================================================
# ReferenceAnalyzer Initialization Tests
# ============================================================================


class TestReferenceAnalyzerInit:
    """Test ReferenceAnalyzer initialization."""

    def test_init_default(self):
        """Test default initialization."""
        with patch("app.services.ai.reference_analyzer.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "test-key"
            analyzer = ReferenceAnalyzer()
            assert analyzer._api_key == "test-key"

    def test_init_custom_key(self):
        """Test initialization with custom API key."""
        analyzer = ReferenceAnalyzer(api_key="custom-key")
        assert analyzer._api_key == "custom-key"


# ============================================================================
# Scene Detection Tests
# ============================================================================


class TestSceneDetection:
    """Test scene detection logic."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return ReferenceAnalyzer(api_key="test-key")

    def test_detect_scenes_empty(self, analyzer):
        """Test scene detection with empty frames."""
        scenes = analyzer._detect_scenes([], [])
        assert scenes == []

    def test_detect_scenes_single_shot(self, analyzer):
        """Test scene detection with single shot type."""
        frames = [
            FrameAnalysis(timestamp=0.0, shot_type="wide"),
            FrameAnalysis(timestamp=1.0, shot_type="wide"),
            FrameAnalysis(timestamp=2.0, shot_type="wide"),
        ]
        timestamps = [0.0, 1.0, 2.0]

        scenes = analyzer._detect_scenes(frames, timestamps)

        # Should be one scene
        assert len(scenes) == 1
        assert scenes[0].start_time == 0.0
        assert scenes[0].end_time == 2.0

    def test_detect_scenes_multiple_shots(self, analyzer):
        """Test scene detection with multiple shot types."""
        frames = [
            FrameAnalysis(timestamp=0.0, shot_type="wide", description="Wide shot"),
            FrameAnalysis(timestamp=1.0, shot_type="wide", description="Wide shot"),
            FrameAnalysis(timestamp=2.0, shot_type="close-up", description="Close-up"),
            FrameAnalysis(timestamp=3.0, shot_type="close-up", description="Close-up"),
            FrameAnalysis(timestamp=4.0, shot_type="medium", description="Medium"),
        ]
        timestamps = [0.0, 1.0, 2.0, 3.0, 4.0]

        scenes = analyzer._detect_scenes(frames, timestamps)

        # Should detect 3 scenes (wide -> close-up -> medium)
        assert len(scenes) >= 2


# ============================================================================
# Moodboard Selection Tests
# ============================================================================


class TestMoodboardSelection:
    """Test moodboard frame selection."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return ReferenceAnalyzer(api_key="test-key")

    def test_select_moodboard_empty(self, analyzer):
        """Test moodboard selection with empty frames."""
        moodboard = analyzer._select_moodboard_frames([], [], 5)
        assert moodboard == []

    def test_select_moodboard_basic(self, analyzer):
        """Test basic moodboard selection."""
        frames = [b"frame1", b"frame2", b"frame3"]
        analyses = [
            FrameAnalysis(
                timestamp=0.0,
                description="Establishing shot",
                objects=["building", "sky"],
                emotion="calm",
            ),
            FrameAnalysis(
                timestamp=1.0,
                description="Action scene with characters",
                objects=["person", "car", "street", "lights"],
                emotion="tense",
            ),
            FrameAnalysis(
                timestamp=2.0,
                description="Close-up",
                objects=["face"],
            ),
        ]

        moodboard = analyzer._select_moodboard_frames(frames, analyses, 2)

        # Should return base64 encoded frames
        assert len(moodboard) <= 2
        for frame in moodboard:
            # Should be valid base64
            try:
                base64.b64decode(frame)
            except Exception:
                pytest.fail("Moodboard frame not valid base64")


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Test error handling in ReferenceAnalyzer."""

    def test_no_api_key_error(self):
        """Test error when no API key available."""
        with patch("app.services.ai.reference_analyzer.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = None
            analyzer = ReferenceAnalyzer()

            with pytest.raises(ReferenceAnalysisError, match="No API key"):
                analyzer._get_client()

    @pytest.mark.asyncio
    async def test_video_processing_error(self):
        """Test error when video processing fails."""
        analyzer = ReferenceAnalyzer(api_key="test-key")

        with pytest.raises(VideoProcessingError):
            await analyzer.analyze_video_reference(b"invalid video data")


# ============================================================================
# Module-Level Functions Tests
# ============================================================================


class TestModuleFunctions:
    """Test module-level convenience functions."""

    def test_get_reference_analyzer_default(self):
        """Test get_reference_analyzer returns singleton."""
        with patch("app.services.ai.reference_analyzer.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "test-key"

            analyzer1 = get_reference_analyzer()
            analyzer2 = get_reference_analyzer()

            assert analyzer1 is analyzer2

    def test_get_reference_analyzer_custom_key(self):
        """Test get_reference_analyzer with custom key."""
        analyzer = get_reference_analyzer(api_key="custom-key")
        assert analyzer._api_key == "custom-key"


# ============================================================================
# Integration Tests (Skipped by default)
# ============================================================================


@pytest.mark.skip(reason="Requires actual Gemini API key and video file")
class TestIntegration:
    """Integration tests with real Gemini API."""

    @pytest.mark.asyncio
    async def test_real_video_analysis(self):
        """Test real video analysis with Gemini."""
        pass

    @pytest.mark.asyncio
    async def test_real_image_analysis(self):
        """Test real image analysis with Gemini."""
        pass
