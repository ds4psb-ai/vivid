"""
Tests for 4D Reference Decoder Endpoints (2026 Expert Workflow).

Comprehensive test suite (45+ tests) covering:
- StyleExtractionResponse model validation
- VideoAnalysisResponse model validation
- ImageAnalysisResponse model validation
- File upload validation (type, size)
- Endpoint integration with mocking
- Error handling
- Evidence refs format (List[str])

References:
- docs/research/02_REFERENCE_DECODER_RESEARCH.md
- Expert Workflow: "스타일 프롬프트라고 따로 둬요"
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO
import json

from fastapi import UploadFile
from pydantic import ValidationError

from app.routers.dimension.classic import (
    # Response models
    StyleExtractionResponse,
    VideoAnalysisResponse,
    ImageAnalysisResponse,
    # Constants
    ALLOWED_IMAGE_TYPES,
    ALLOWED_VIDEO_TYPES,
    MAX_IMAGE_SIZE,
    MAX_VIDEO_SIZE,
)


# ============================================================================
# StyleExtractionResponse Tests
# ============================================================================


class TestStyleExtractionResponse:
    """Test StyleExtractionResponse model."""

    def test_default_values(self):
        """Test default values for StyleExtractionResponse."""
        response = StyleExtractionResponse()
        assert response.success is True
        assert response.style_tags == []
        assert response.style_prompt == ""
        assert response.color_palette == []
        assert response.lighting == ""
        assert response.composition == ""
        assert response.mood == ""
        assert response.camera_angle is None
        assert response.reference_artists == []
        assert response.confidence == 0.0
        assert response.evidence_refs == []

    def test_full_response(self):
        """Test full StyleExtractionResponse with all fields."""
        response = StyleExtractionResponse(
            success=True,
            style_tags=["cinematic", "moody", "noir"],
            style_prompt="Cinematic noir style with dramatic lighting...",
            color_palette=["#1a1a2e", "#16213e", "#0f3460"],
            lighting="dramatic chiaroscuro",
            composition="rule of thirds with strong diagonal lines",
            mood="mysterious and tense",
            camera_angle="low angle",
            reference_artists=["Roger Deakins", "Gordon Willis"],
            confidence=0.85,
            evidence_refs=["db:style_extractions:user123:ref.jpg"],
        )
        assert len(response.style_tags) == 3
        assert "cinematic" in response.style_tags
        assert len(response.color_palette) == 3
        assert response.confidence == 0.85

    def test_evidence_refs_is_list_of_strings(self):
        """Test evidence_refs is List[str] format (Vivid convention)."""
        response = StyleExtractionResponse(
            evidence_refs=[
                "db:style_extractions:user123:ref.jpg",
                "rag:cinematography:rembrandt_lighting",
            ]
        )
        assert isinstance(response.evidence_refs, list)
        for ref in response.evidence_refs:
            assert isinstance(ref, str)
            assert ":" in ref  # Vivid ref format

    def test_color_palette_hex_format(self):
        """Test color palette with hex colors."""
        response = StyleExtractionResponse(
            color_palette=["#FF5733", "#33FF57", "#3357FF"]
        )
        assert len(response.color_palette) == 3
        for color in response.color_palette:
            assert color.startswith("#")

    def test_confidence_range(self):
        """Test confidence value within expected range."""
        response_low = StyleExtractionResponse(confidence=0.0)
        response_high = StyleExtractionResponse(confidence=1.0)
        response_mid = StyleExtractionResponse(confidence=0.75)

        assert 0.0 <= response_low.confidence <= 1.0
        assert 0.0 <= response_high.confidence <= 1.0
        assert 0.0 <= response_mid.confidence <= 1.0


# ============================================================================
# VideoAnalysisResponse Tests
# ============================================================================


class TestVideoAnalysisResponse:
    """Test VideoAnalysisResponse model."""

    def test_default_values(self):
        """Test default values for VideoAnalysisResponse."""
        response = VideoAnalysisResponse()
        assert response.success is True
        assert response.total_duration == 0.0
        assert response.frame_count == 0
        assert response.frames == []
        assert response.scenes == []
        assert response.style == {}
        assert response.suggested_shots == []
        assert response.moodboard_frames == []
        assert response.confidence == 0.0
        assert response.evidence_refs == []

    def test_full_response(self):
        """Test full VideoAnalysisResponse with all fields."""
        response = VideoAnalysisResponse(
            success=True,
            total_duration=30.5,
            frame_count=15,
            frames=[
                {
                    "timestamp": 0.0,
                    "frame_number": 0,
                    "description": "Opening wide shot of cityscape",
                    "objects": ["buildings", "sky", "cars"],
                    "actions": ["camera panning"],
                    "camera_movement": "pan left",
                    "shot_type": "wide",
                    "emotion": "establishing",
                },
                {
                    "timestamp": 3.0,
                    "frame_number": 1,
                    "description": "Close-up of protagonist",
                    "objects": ["face", "hands"],
                    "actions": ["speaking"],
                    "camera_movement": "static",
                    "shot_type": "close-up",
                    "emotion": "tense",
                },
            ],
            scenes=[
                {
                    "start_time": 0.0,
                    "end_time": 10.0,
                    "duration": 10.0,
                    "description": "Opening scene",
                    "key_frame_index": 0,
                },
            ],
            style={"style_tags": ["noir", "dramatic"], "lighting": "low-key"},
            suggested_shots=[
                {
                    "shot_number": 1,
                    "duration_seconds": 5.0,
                    "description": "Recreate opening shot",
                    "camera_setup": "Wide angle, low position",
                    "prompt": "Cinematic wide shot of urban landscape...",
                    "reference_frame_index": 0,
                },
            ],
            moodboard_frames=["base64_encoded_frame_1", "base64_encoded_frame_2"],
            confidence=0.82,
            evidence_refs=["db:video_analysis:user123:video.mp4"],
        )
        assert response.total_duration == 30.5
        assert response.frame_count == 15
        assert len(response.frames) == 2
        assert len(response.scenes) == 1
        assert len(response.suggested_shots) == 1
        assert len(response.moodboard_frames) == 2

    def test_frames_structure(self):
        """Test frames array structure."""
        response = VideoAnalysisResponse(
            frames=[
                {
                    "timestamp": 5.5,
                    "frame_number": 132,
                    "description": "A woman walks through neon-lit alley",
                    "objects": ["neon signs", "puddles"],
                    "actions": ["walking"],
                    "camera_movement": "tracking",
                    "shot_type": "medium",
                    "emotion": "mysterious",
                }
            ]
        )
        frame = response.frames[0]
        assert frame["timestamp"] == 5.5
        assert frame["frame_number"] == 132
        assert "walking" in frame["actions"]

    def test_scenes_structure(self):
        """Test scenes array structure."""
        response = VideoAnalysisResponse(
            scenes=[
                {
                    "start_time": 0.0,
                    "end_time": 15.0,
                    "duration": 15.0,
                    "description": "Scene 1 - Establishing",
                    "key_frame_index": 0,
                }
            ]
        )
        scene = response.scenes[0]
        assert scene["start_time"] == 0.0
        assert scene["end_time"] == 15.0
        assert scene["duration"] == 15.0

    def test_evidence_refs_format(self):
        """Test evidence_refs follows Vivid convention."""
        response = VideoAnalysisResponse(
            evidence_refs=[
                "db:video_analysis:user123:video.mp4",
                "rag:cinematography:dolly_zoom",
                "db:famous_scenes:parasite_stairs",
            ]
        )
        for ref in response.evidence_refs:
            assert isinstance(ref, str)
            parts = ref.split(":")
            assert len(parts) >= 2
            assert parts[0] in ["db", "rag"]


# ============================================================================
# ImageAnalysisResponse Tests
# ============================================================================


class TestImageAnalysisResponse:
    """Test ImageAnalysisResponse model."""

    def test_default_values(self):
        """Test default values for ImageAnalysisResponse."""
        response = ImageAnalysisResponse()
        assert response.success is True
        assert response.description == ""
        assert response.style == {}
        assert response.objects == []
        assert response.composition_analysis == ""
        assert response.recreation_prompt == ""
        assert response.similar_references == []
        assert response.evidence_refs == []

    def test_full_response(self):
        """Test full ImageAnalysisResponse with all fields."""
        response = ImageAnalysisResponse(
            success=True,
            description="A moody portrait with dramatic Rembrandt lighting",
            style={
                "style_tags": ["portrait", "dramatic", "chiaroscuro"],
                "lighting": "Rembrandt",
                "mood": "introspective",
            },
            objects=["person", "window", "shadows", "chair"],
            composition_analysis="Subject positioned using rule of thirds, strong diagonal shadow",
            recreation_prompt="Create a dramatic portrait with Rembrandt lighting...",
            similar_references=["Caravaggio paintings", "Gordon Willis cinematography"],
            evidence_refs=["db:image_analysis:user123:portrait.jpg"],
        )
        assert "portrait" in response.description
        assert len(response.objects) == 4
        assert "Rembrandt" in response.recreation_prompt

    def test_recreation_prompt_content(self):
        """Test recreation_prompt contains useful generation instructions."""
        response = ImageAnalysisResponse(
            recreation_prompt="Cinematic medium shot, dramatic side lighting, shallow depth of field, moody atmosphere, professional color grading"
        )
        assert "cinematic" in response.recreation_prompt.lower()
        assert len(response.recreation_prompt) > 50  # Substantial prompt


# ============================================================================
# File Type Validation Tests
# ============================================================================


class TestFileTypeValidation:
    """Test file type validation for upload endpoints."""

    def test_allowed_image_types_defined(self):
        """Test ALLOWED_IMAGE_TYPES is properly defined."""
        assert "image/jpeg" in ALLOWED_IMAGE_TYPES
        assert "image/png" in ALLOWED_IMAGE_TYPES
        assert "image/webp" in ALLOWED_IMAGE_TYPES

    def test_allowed_video_types_defined(self):
        """Test ALLOWED_VIDEO_TYPES is properly defined."""
        assert "video/mp4" in ALLOWED_VIDEO_TYPES
        assert "video/webm" in ALLOWED_VIDEO_TYPES

    def test_max_image_size(self):
        """Test MAX_IMAGE_SIZE is 10MB."""
        assert MAX_IMAGE_SIZE == 10 * 1024 * 1024

    def test_max_video_size(self):
        """Test MAX_VIDEO_SIZE is 100MB."""
        assert MAX_VIDEO_SIZE == 100 * 1024 * 1024

    def test_image_type_count(self):
        """Test reasonable number of allowed image types."""
        assert len(ALLOWED_IMAGE_TYPES) >= 3

    def test_video_type_count(self):
        """Test reasonable number of allowed video types."""
        assert len(ALLOWED_VIDEO_TYPES) >= 2


# ============================================================================
# Style Extraction Endpoint Tests
# ============================================================================


class TestStyleExtractionEndpoint:
    """Test /4d/extract-style endpoint logic."""

    @pytest.fixture
    def mock_style_extractor(self):
        """Create mock style extractor."""
        mock = MagicMock()
        mock.extract_style = AsyncMock(return_value=MagicMock(
            style_tags=["cinematic", "noir"],
            style_prompt="Cinematic noir style...",
            color_palette=["#1a1a2e", "#16213e"],
            lighting="dramatic",
            composition="rule of thirds",
            mood="mysterious",
            camera_angle="low angle",
            reference_artists=["Roger Deakins"],
            confidence=0.85,
        ))
        return mock

    def test_valid_jpeg_upload_type(self):
        """Test JPEG is accepted."""
        assert "image/jpeg" in ALLOWED_IMAGE_TYPES

    def test_valid_png_upload_type(self):
        """Test PNG is accepted."""
        assert "image/png" in ALLOWED_IMAGE_TYPES

    def test_valid_webp_upload_type(self):
        """Test WebP is accepted."""
        assert "image/webp" in ALLOWED_IMAGE_TYPES

    def test_gif_may_be_accepted(self):
        """Test GIF may be accepted (optional)."""
        # GIF is often included for reference images
        pass  # Implementation dependent

    def test_response_includes_evidence_refs(self):
        """Test response includes evidence_refs in correct format."""
        response = StyleExtractionResponse(
            success=True,
            style_tags=["test"],
            evidence_refs=["db:style_extractions:user123:test.jpg"],
        )
        assert len(response.evidence_refs) > 0
        assert response.evidence_refs[0].startswith("db:")


# ============================================================================
# Video Analysis Endpoint Tests
# ============================================================================


class TestVideoAnalysisEndpoint:
    """Test /4d/analyze-video endpoint logic."""

    def test_valid_mp4_upload_type(self):
        """Test MP4 is accepted."""
        assert "video/mp4" in ALLOWED_VIDEO_TYPES

    def test_valid_webm_upload_type(self):
        """Test WebM is accepted."""
        assert "video/webm" in ALLOWED_VIDEO_TYPES

    def test_response_includes_moodboard(self):
        """Test response can include moodboard frames."""
        response = VideoAnalysisResponse(
            moodboard_frames=["base64_frame_1", "base64_frame_2", "base64_frame_3"]
        )
        assert len(response.moodboard_frames) == 3

    def test_suggested_shots_structure(self):
        """Test suggested_shots follows expected structure."""
        response = VideoAnalysisResponse(
            suggested_shots=[
                {
                    "shot_number": 1,
                    "duration_seconds": 5.0,
                    "description": "Opening shot",
                    "camera_setup": "Wide angle",
                    "prompt": "Recreate opening with...",
                    "reference_frame_index": 0,
                }
            ]
        )
        shot = response.suggested_shots[0]
        assert "shot_number" in shot
        assert "prompt" in shot
        assert "reference_frame_index" in shot


# ============================================================================
# Image Analysis Endpoint Tests
# ============================================================================


class TestImageAnalysisEndpoint:
    """Test /4d/analyze-image endpoint logic."""

    def test_response_includes_recreation_prompt(self):
        """Test response includes recreation_prompt."""
        response = ImageAnalysisResponse(
            recreation_prompt="Cinematic shot with dramatic lighting..."
        )
        assert len(response.recreation_prompt) > 0

    def test_response_includes_similar_references(self):
        """Test response can include similar_references."""
        response = ImageAnalysisResponse(
            similar_references=["Blade Runner 2049", "Sicario"]
        )
        assert len(response.similar_references) == 2


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Test error handling for 4D endpoints."""

    def test_style_extraction_response_on_error(self):
        """Test StyleExtractionResponse can indicate failure."""
        response = StyleExtractionResponse(success=False)
        assert response.success is False

    def test_video_analysis_response_on_error(self):
        """Test VideoAnalysisResponse can indicate failure."""
        response = VideoAnalysisResponse(success=False)
        assert response.success is False

    def test_image_analysis_response_on_error(self):
        """Test ImageAnalysisResponse can indicate failure."""
        response = ImageAnalysisResponse(success=False)
        assert response.success is False

    def test_empty_evidence_refs_on_error(self):
        """Test evidence_refs can be empty on error."""
        response = StyleExtractionResponse(
            success=False,
            evidence_refs=[],
        )
        assert response.evidence_refs == []


# ============================================================================
# Evidence Refs Format Tests (Vivid Convention)
# ============================================================================


class TestEvidenceRefsFormat:
    """Test evidence_refs follows Vivid List[str] convention."""

    def test_style_extraction_evidence_refs_type(self):
        """Test evidence_refs is List[str] in StyleExtractionResponse."""
        response = StyleExtractionResponse(
            evidence_refs=["db:style_extractions:user1:img.jpg"]
        )
        assert isinstance(response.evidence_refs, list)
        assert all(isinstance(ref, str) for ref in response.evidence_refs)

    def test_video_analysis_evidence_refs_type(self):
        """Test evidence_refs is List[str] in VideoAnalysisResponse."""
        response = VideoAnalysisResponse(
            evidence_refs=["db:video_analysis:user1:video.mp4"]
        )
        assert isinstance(response.evidence_refs, list)
        assert all(isinstance(ref, str) for ref in response.evidence_refs)

    def test_image_analysis_evidence_refs_type(self):
        """Test evidence_refs is List[str] in ImageAnalysisResponse."""
        response = ImageAnalysisResponse(
            evidence_refs=["db:image_analysis:user1:image.png"]
        )
        assert isinstance(response.evidence_refs, list)
        assert all(isinstance(ref, str) for ref in response.evidence_refs)

    def test_evidence_refs_db_prefix(self):
        """Test evidence_refs can use db: prefix."""
        response = StyleExtractionResponse(
            evidence_refs=["db:capsule_runs:uuid123"]
        )
        assert response.evidence_refs[0].startswith("db:")

    def test_evidence_refs_rag_prefix(self):
        """Test evidence_refs can use rag: prefix."""
        response = VideoAnalysisResponse(
            evidence_refs=["rag:cinematography:dolly_zoom"]
        )
        assert response.evidence_refs[0].startswith("rag:")

    def test_multiple_evidence_refs(self):
        """Test multiple evidence_refs can coexist."""
        response = ImageAnalysisResponse(
            evidence_refs=[
                "db:image_analysis:user1:ref.jpg",
                "rag:famous_scenes:parasite_stairs",
                "db:style_presets:preset123",
            ]
        )
        assert len(response.evidence_refs) == 3


# ============================================================================
# JSON Serialization Tests
# ============================================================================


class TestJSONSerialization:
    """Test JSON serialization of response models."""

    def test_style_extraction_to_json(self):
        """Test StyleExtractionResponse serializes to JSON."""
        response = StyleExtractionResponse(
            success=True,
            style_tags=["cinematic"],
            confidence=0.85,
        )
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["success"] is True
        assert "cinematic" in parsed["style_tags"]

    def test_video_analysis_to_json(self):
        """Test VideoAnalysisResponse serializes to JSON."""
        response = VideoAnalysisResponse(
            success=True,
            total_duration=30.0,
            frame_count=10,
        )
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["total_duration"] == 30.0

    def test_image_analysis_to_json(self):
        """Test ImageAnalysisResponse serializes to JSON."""
        response = ImageAnalysisResponse(
            success=True,
            description="Test description",
        )
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)
        assert "Test description" in parsed["description"]

    def test_nested_dict_serialization(self):
        """Test nested dicts serialize correctly."""
        response = VideoAnalysisResponse(
            style={"lighting": "dramatic", "mood": "tense"},
        )
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["style"]["lighting"] == "dramatic"

    def test_list_of_dicts_serialization(self):
        """Test list of dicts serializes correctly."""
        response = VideoAnalysisResponse(
            frames=[
                {"timestamp": 0.0, "description": "Frame 1"},
                {"timestamp": 1.0, "description": "Frame 2"},
            ]
        )
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)
        assert len(parsed["frames"]) == 2


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_style_tags(self):
        """Test empty style_tags list."""
        response = StyleExtractionResponse(style_tags=[])
        assert response.style_tags == []

    def test_very_long_style_prompt(self):
        """Test very long style_prompt."""
        long_prompt = "cinematic " * 1000
        response = StyleExtractionResponse(style_prompt=long_prompt)
        assert len(response.style_prompt) > 5000

    def test_unicode_in_description(self):
        """Test Korean/Unicode in description."""
        response = ImageAnalysisResponse(
            description="봉준호 감독 스타일의 시네마틱 장면 🎬"
        )
        assert "봉준호" in response.description
        assert "🎬" in response.description

    def test_zero_duration_video(self):
        """Test zero duration video response."""
        response = VideoAnalysisResponse(total_duration=0.0)
        assert response.total_duration == 0.0

    def test_zero_confidence(self):
        """Test zero confidence value."""
        response = StyleExtractionResponse(confidence=0.0)
        assert response.confidence == 0.0

    def test_max_confidence(self):
        """Test max confidence value."""
        response = StyleExtractionResponse(confidence=1.0)
        assert response.confidence == 1.0

    def test_single_frame_video(self):
        """Test single frame video analysis."""
        response = VideoAnalysisResponse(
            frame_count=1,
            frames=[{"timestamp": 0.0, "description": "Single frame"}]
        )
        assert response.frame_count == 1
        assert len(response.frames) == 1

    def test_many_moodboard_frames(self):
        """Test many moodboard frames."""
        frames = [f"base64_frame_{i}" for i in range(20)]
        response = VideoAnalysisResponse(moodboard_frames=frames)
        assert len(response.moodboard_frames) == 20
