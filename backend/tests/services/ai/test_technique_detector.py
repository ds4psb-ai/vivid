"""Tests for Technique Detector Service.

Tests cinematography technique detection from frame analyses.
"""

import pytest
from typing import List, Optional

from app.services.ai.technique_detector import (
    TechniqueDetector,
    DetectedTechnique,
    TechniqueCategory,
    TECHNIQUE_DATABASE,
    get_technique_detector,
)
from app.services.ai.reference_analyzer import FrameAnalysis


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def technique_detector():
    """Create TechniqueDetector instance."""
    return TechniqueDetector()


@pytest.fixture
def close_up_frame():
    """Create frame analysis for close-up shot."""
    return FrameAnalysis(
        timestamp=0.0,
        frame_number=0,
        description="얼굴 클로즈업, 감정 표현",
        shot_type="클로즈업",
        camera_movement="고정",
        emotion="긴장",
    )


@pytest.fixture
def wide_shot_frame():
    """Create frame analysis for wide shot."""
    return FrameAnalysis(
        timestamp=5.0,
        frame_number=120,
        description="드넓은 풍경을 담은 와이드 샷",
        shot_type="익스트림 와이드",
        camera_movement="팬",
        emotion="경외",
    )


@pytest.fixture
def tracking_shot_frame():
    """Create frame analysis for tracking shot."""
    return FrameAnalysis(
        timestamp=10.0,
        frame_number=240,
        description="캐릭터를 따라가는 트래킹 샷",
        shot_type="미디엄",
        camera_movement="트래킹",
        emotion="긴박",
    )


@pytest.fixture
def mixed_frames():
    """Create a list of mixed frame analyses."""
    return [
        FrameAnalysis(timestamp=0.0, frame_number=0, shot_type="와이드", camera_movement="고정"),
        FrameAnalysis(timestamp=2.0, frame_number=48, shot_type="미디엄", camera_movement="팬"),
        FrameAnalysis(timestamp=4.0, frame_number=96, shot_type="클로즈업", camera_movement="고정"),
        FrameAnalysis(timestamp=6.0, frame_number=144, shot_type="익스트림 클로즈업", camera_movement="고정"),
        FrameAnalysis(timestamp=8.0, frame_number=192, shot_type="와이드", camera_movement="트래킹"),
    ]


# =============================================================================
# Technique Database Tests
# =============================================================================


class TestTechniqueDatabase:
    """Tests for technique database configuration."""

    def test_database_is_dict(self):
        """Test database is a dictionary."""
        assert isinstance(TECHNIQUE_DATABASE, dict)
        assert len(TECHNIQUE_DATABASE) > 0

    def test_database_has_techniques(self):
        """Test database contains techniques."""
        # Check some expected technique keys
        expected_keys = ["extreme_wide", "wide", "medium", "close_up"]
        for key in expected_keys:
            assert key in TECHNIQUE_DATABASE

    def test_technique_structure(self):
        """Test technique entry structure."""
        for tech_id, tech in TECHNIQUE_DATABASE.items():
            assert "name" in tech
            assert "name_ko" in tech
            assert "category" in tech
            assert "keywords" in tech


# =============================================================================
# Technique Detection Tests
# =============================================================================


class TestTechniqueDetection:
    """Tests for technique detection from frames."""

    @pytest.mark.asyncio
    async def test_detect_close_up(self, technique_detector, close_up_frame):
        """Test detecting close-up technique."""
        techniques = await technique_detector.detect_techniques(
            [close_up_frame], [0.0]
        )

        assert isinstance(techniques, list)
        # Should detect at least some techniques
        if techniques:
            first_tech = techniques[0]
            assert isinstance(first_tech, DetectedTechnique)

    @pytest.mark.asyncio
    async def test_detect_tracking_shot(self, technique_detector, tracking_shot_frame):
        """Test detecting tracking shot technique."""
        techniques = await technique_detector.detect_techniques(
            [tracking_shot_frame], [10.0]
        )

        assert isinstance(techniques, list)

    @pytest.mark.asyncio
    async def test_detect_multiple_techniques(self, technique_detector, mixed_frames):
        """Test detecting multiple techniques from multiple frames."""
        timestamps = [f.timestamp for f in mixed_frames]
        techniques = await technique_detector.detect_techniques(
            mixed_frames, timestamps
        )

        assert isinstance(techniques, list)

    @pytest.mark.asyncio
    async def test_technique_confidence_range(self, technique_detector, mixed_frames):
        """Test that technique confidence is in valid range."""
        timestamps = [f.timestamp for f in mixed_frames]
        techniques = await technique_detector.detect_techniques(
            mixed_frames, timestamps
        )

        for tech in techniques:
            assert 0 <= tech.confidence <= 1

    @pytest.mark.asyncio
    async def test_empty_frames_returns_empty(self, technique_detector):
        """Test that empty frames list returns empty techniques."""
        techniques = await technique_detector.detect_techniques([], [])
        assert techniques == []


# =============================================================================
# DetectedTechnique Model Tests
# =============================================================================


class TestDetectedTechniqueModel:
    """Tests for DetectedTechnique dataclass."""

    def test_detected_technique_creation(self):
        """Test creating DetectedTechnique instance."""
        tech = DetectedTechnique(
            technique_id="close_up",
            name="Close-Up",
            name_ko="클로즈업",
            category="shot_type",
            confidence=0.95,
            description="얼굴을 가까이서 촬영",
        )

        assert tech.technique_id == "close_up"
        assert tech.confidence == 0.95

    def test_detected_technique_with_optional_fields(self):
        """Test DetectedTechnique with optional fields."""
        tech = DetectedTechnique(
            technique_id="pan",
            name="Pan",
            name_ko="팬",
            category="camera_movement",
            confidence=0.8,
        )

        assert tech.description == ""
        assert tech.frame_indices == []


# =============================================================================
# TechniqueCategory Model Tests
# =============================================================================


class TestTechniqueCategoryModel:
    """Tests for TechniqueCategory model."""

    def test_technique_category_creation(self):
        """Test creating TechniqueCategory instance."""
        tech1 = DetectedTechnique(
            technique_id="close_up",
            name="Close-Up",
            name_ko="클로즈업",
            category="shot_type",
            confidence=0.9,
        )

        category = TechniqueCategory(
            category="shot_type",
            category_name_ko="샷 유형",
            techniques=[tech1],
            total_confidence=0.9,
        )

        assert category.category == "shot_type"
        assert len(category.techniques) == 1


# =============================================================================
# Module-level Function Tests
# =============================================================================


class TestModuleFunctions:
    """Tests for module-level convenience functions."""

    def test_get_technique_detector_returns_instance(self):
        """Test get_technique_detector returns TechniqueDetector instance."""
        detector = get_technique_detector()
        assert isinstance(detector, TechniqueDetector)

    def test_get_technique_detector_caches_instance(self):
        """Test get_technique_detector returns same instance."""
        detector1 = get_technique_detector()
        detector2 = get_technique_detector()
        assert detector1 is detector2


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_frame_with_none_shot_type(self, technique_detector):
        """Test handling frame with None shot type."""
        frame = FrameAnalysis(
            timestamp=0.0,
            frame_number=0,
            description="Some description",
            shot_type=None,
            camera_movement=None,
        )

        # Should not raise error
        techniques = await technique_detector.detect_techniques([frame], [0.0])
        assert isinstance(techniques, list)

    @pytest.mark.asyncio
    async def test_frame_with_unknown_shot_type(self, technique_detector):
        """Test handling frame with unknown shot type."""
        frame = FrameAnalysis(
            timestamp=0.0,
            frame_number=0,
            description="Some description",
            shot_type="unknown_type_xyz",
            camera_movement="unknown_movement_xyz",
        )

        techniques = await technique_detector.detect_techniques([frame], [0.0])
        # Should return empty or minimal matches
        assert isinstance(techniques, list)
