"""Tests for 4D Reference Decoder DB Models.

Tests:
- StylePreset model validation and properties
- ReferenceItem model validation and properties
- ReferenceScene model for RAG
- CinematographyTechnique model for RAG
- JSONB field handling
- Relationship integrity

References:
- docs/research/02_REFERENCE_DECODER_RESEARCH.md
- 2026 SQLAlchemy 2.0 async best practices
"""
import uuid
from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_reference import (
    StylePreset,
    ReferenceItem,
    ReferenceScene,
    CinematographyTechnique,
    ReferenceType,
    AnalysisDepth,
)


# =============================================================================
# StylePreset Model Tests
# =============================================================================


class TestStylePresetModel:
    """Test StylePreset model."""

    def test_create_minimal(self):
        """Test creating StylePreset with minimal fields."""
        preset = StylePreset(
            user_id="user-123",
            name="Test Style",
            tags=[],
            style_data={},
            color_palette=[],
        )
        assert preset.user_id == "user-123"
        assert preset.name == "Test Style"
        assert preset.tags == []
        assert preset.style_data == {}

    def test_create_full(self):
        """Test creating StylePreset with all fields."""
        style_data = {
            "style_tags": ["anime", "cel-shading", "vibrant"],
            "style_prompt": "Cinematic anime style with bold outlines...",
            "color_palette": ["#FF5733", "#33FF57", "#3357FF"],
            "lighting": "neon",
            "composition": "rule-of-thirds",
            "mood": "energetic",
            "camera_angle": "low-angle",
            "reference_artists": ["Makoto Shinkai"],
            "confidence": 0.95,
        }

        preset = StylePreset(
            user_id="user-456",
            name="Anime Neon Style",
            description="Vibrant anime style with neon lighting",
            tags=["anime", "neon", "vibrant"],
            style_data=style_data,
            color_palette=["#FF5733", "#33FF57"],
            lighting="neon",
            mood="energetic",
            thumbnail_url="https://example.com/thumb.jpg",
            is_public=True,
            usage_count=42,
        )

        assert preset.name == "Anime Neon Style"
        assert len(preset.tags) == 3
        assert preset.style_data["confidence"] == 0.95
        assert preset.lighting == "neon"
        assert preset.is_public is True
        assert preset.usage_count == 42

    def test_style_prompt_property(self):
        """Test style_prompt property extracts from style_data."""
        preset = StylePreset(
            user_id="user-123",
            name="Test",
            style_data={
                "style_prompt": "Dramatic cinematic lighting...",
            },
        )
        assert preset.style_prompt == "Dramatic cinematic lighting..."

    def test_style_tags_property(self):
        """Test style_tags property extracts from style_data."""
        preset = StylePreset(
            user_id="user-123",
            name="Test",
            style_data={
                "style_tags": ["noir", "moody"],
            },
        )
        assert preset.style_tags == ["noir", "moody"]

    def test_confidence_property(self):
        """Test confidence property extracts from style_data."""
        preset = StylePreset(
            user_id="user-123",
            name="Test",
            style_data={"confidence": 0.85},
        )
        assert preset.confidence == 0.85

    def test_confidence_default(self):
        """Test confidence defaults to 0.0 when not in style_data."""
        preset = StylePreset(
            user_id="user-123",
            name="Test",
            style_data={},
        )
        assert preset.confidence == 0.0

    def test_repr(self):
        """Test string representation."""
        preset = StylePreset(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            user_id="user-123",
            name="Test Style",
        )
        assert "StylePreset" in repr(preset)
        assert "Test Style" in repr(preset)


# =============================================================================
# ReferenceItem Model Tests
# =============================================================================


class TestReferenceItemModel:
    """Test ReferenceItem model."""

    def test_create_video_reference(self):
        """Test creating video reference item."""
        item = ReferenceItem(
            user_id="user-123",
            name="Inception Hallway Scene",
            reference_type=ReferenceType.VIDEO.value,
            source_url="https://storage.example.com/video.mp4",
            duration_seconds=120.5,
            analysis_status="pending",
            analysis_depth="detailed",
            tags=[],
            analysis_result={},
            moodboard_frames=[],
            evidence_refs=[],
        )
        assert item.reference_type == "video"
        assert item.is_video is True
        assert item.is_image is False
        assert item.analysis_status == "pending"
        assert item.analysis_depth == "detailed"

    def test_create_image_reference(self):
        """Test creating image reference item."""
        item = ReferenceItem(
            user_id="user-456",
            name="Blade Runner Still",
            reference_type=ReferenceType.IMAGE.value,
            source_url="https://storage.example.com/image.jpg",
            tags=[],
            analysis_result={},
            moodboard_frames=[],
            evidence_refs=[],
        )
        assert item.reference_type == "image"
        assert item.is_image is True
        assert item.is_video is False

    def test_analysis_result_video(self):
        """Test analysis result for video reference."""
        analysis = {
            "total_duration": 30.0,
            "frame_count": 10,
            "fps": 24.0,
            "frames": [
                {"timestamp": 0.0, "description": "Frame 1"},
                {"timestamp": 3.0, "description": "Frame 2"},
            ],
            "scenes": [
                {"start_time": 0.0, "end_time": 15.0, "description": "Scene 1"},
                {"start_time": 15.0, "end_time": 30.0, "description": "Scene 2"},
            ],
            "suggested_shots": [
                {"shot_number": 1, "description": "Shot 1"},
            ],
        }

        item = ReferenceItem(
            user_id="user-123",
            name="Test Video",
            reference_type="video",
            source_url="https://example.com/video.mp4",
            analysis_result=analysis,
            analysis_status="completed",
        )

        assert item.frame_count == 10
        assert item.scene_count == 2
        assert len(item.suggested_shots) == 1
        assert item.is_analyzed is True

    def test_moodboard_frames(self):
        """Test moodboard frames storage."""
        item = ReferenceItem(
            user_id="user-123",
            name="Test",
            reference_type="video",
            source_url="https://example.com/video.mp4",
            moodboard_frames=[
                "base64_frame_1",
                "base64_frame_2",
                "base64_frame_3",
            ],
        )
        assert len(item.moodboard_frames) == 3

    def test_evidence_refs(self):
        """Test evidence_refs storage as List[str]."""
        item = ReferenceItem(
            user_id="user-123",
            name="Test",
            reference_type="image",
            source_url="https://example.com/image.jpg",
            evidence_refs=[
                "rag:cinematography_techniques:rembrandt_lighting",
                "db:reference_scenes:parasite_stairs",
            ],
        )
        assert len(item.evidence_refs) == 2
        assert item.evidence_refs[0].startswith("rag:")

    def test_analysis_pending_status(self):
        """Test is_analyzed returns False when pending."""
        item = ReferenceItem(
            user_id="user-123",
            name="Test",
            reference_type="image",
            source_url="https://example.com/image.jpg",
            analysis_status="pending",
        )
        assert item.is_analyzed is False

    def test_repr(self):
        """Test string representation."""
        item = ReferenceItem(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            user_id="user-123",
            name="Test Reference",
            reference_type="video",
            source_url="https://example.com/video.mp4",
        )
        assert "ReferenceItem" in repr(item)
        assert "Test Reference" in repr(item)
        assert "video" in repr(item)


# =============================================================================
# ReferenceScene Model Tests
# =============================================================================


class TestReferenceSceneModel:
    """Test ReferenceScene model for RAG."""

    def test_create_scene(self):
        """Test creating reference scene."""
        scene = ReferenceScene(
            scene_key="parasite_stairs_sequence",
            film_title="Parasite",
            film_year=2019,
            director="Bong Joon-ho",
            cinematographer="Hong Kyung-pyo",
            timestamp="1:23:45 - 1:25:30",
            description="The family descends the stairs during the flood...",
            auteur_tags=["bong_joon_ho"],
            technique_tags=["tracking_shot", "long_take"],
            mood_tags=["tense", "desperate"],
            genre_tags=["thriller", "drama"],
        )

        assert scene.scene_key == "parasite_stairs_sequence"
        assert scene.film_title == "Parasite"
        assert scene.director == "Bong Joon-ho"
        assert "bong_joon_ho" in scene.auteur_tags

    def test_cinematography_analysis(self):
        """Test cinematography JSONB field."""
        scene = ReferenceScene(
            scene_key="test_scene",
            film_title="Test Film",
            description="Test description",
            cinematography={
                "shot_types": ["wide", "medium", "close-up"],
                "movements": ["tracking", "dolly"],
                "lens": "35mm",
                "composition": "rule of thirds",
                "lighting": "low-key",
            },
        )

        assert scene.cinematography["lens"] == "35mm"
        assert "tracking" in scene.cinematography["movements"]

    def test_color_analysis(self):
        """Test color analysis JSONB field."""
        scene = ReferenceScene(
            scene_key="test_scene",
            film_title="Test Film",
            description="Test description",
            color_analysis={
                "dominant_colors": ["#2B3A42", "#1A1A2E", "#4A90D9"],
                "color_meaning": "Cold, oppressive atmosphere",
                "grading_style": "Desaturated teal and orange",
            },
        )

        assert len(scene.dominant_colors) == 3
        assert scene.dominant_colors[0] == "#2B3A42"

    def test_recreation_guide(self):
        """Test recreation guide JSONB field."""
        scene = ReferenceScene(
            scene_key="test_scene",
            film_title="Test Film",
            description="Test description",
            recreation_guide={
                "key_elements": ["long take", "tracking shot", "rain"],
                "ai_prompt_suggestion": "Cinematic tracking shot following characters...",
                "recommended_tool": "veo",
                "difficulty": "hard",
            },
        )

        assert scene.ai_recreation_prompt == "Cinematic tracking shot following characters..."
        assert scene.recommended_tool == "veo"

    def test_recommended_tool_default(self):
        """Test recommended_tool defaults to 'veo'."""
        scene = ReferenceScene(
            scene_key="test_scene",
            film_title="Test Film",
            description="Test description",
            recreation_guide={},  # Empty dict, should return "veo" as default
        )
        assert scene.recommended_tool == "veo"

    def test_repr(self):
        """Test string representation."""
        scene = ReferenceScene(
            scene_key="test_scene",
            film_title="Test Film",
            description="Test description",
        )
        assert "ReferenceScene" in repr(scene)
        assert "test_scene" in repr(scene)


# =============================================================================
# CinematographyTechnique Model Tests
# =============================================================================


class TestCinematographyTechniqueModel:
    """Test CinematographyTechnique model for RAG."""

    def test_create_technique(self):
        """Test creating cinematography technique."""
        technique = CinematographyTechnique(
            technique_id="dolly_zoom",
            category="camera_movement",
            name_en="Dolly Zoom",
            name_ko="달리 줌",
            description="A camera technique where the camera dollies...",
            aliases=["Vertigo effect", "Zolly", "Contra-zoom"],
            emotional_effect=["disorientation", "realization", "dread"],
            narrative_use=["character epiphany", "horror reveal"],
        )

        assert technique.technique_id == "dolly_zoom"
        assert technique.category == "camera_movement"
        assert "Vertigo effect" in technique.aliases
        assert "disorientation" in technique.emotional_effect

    def test_ai_reproducibility(self):
        """Test AI reproducibility JSONB field."""
        technique = CinematographyTechnique(
            technique_id="push_in",
            category="camera_movement",
            name_en="Push In",
            description="Camera moves toward subject...",
            ai_reproducibility={
                "reproducible": True,
                "platforms": ["veo", "kling", "sora"],
                "prompt_keywords": ["dolly in", "push in", "move closer"],
                "limitations": ["Speed control limited"],
            },
        )

        assert technique.is_ai_reproducible is True
        assert "veo" in technique.supported_platforms
        assert "dolly in" in technique.ai_prompt_keywords

    def test_is_ai_reproducible_false(self):
        """Test is_ai_reproducible when not reproducible."""
        technique = CinematographyTechnique(
            technique_id="steadicam_360",
            category="camera_movement",
            name_en="Steadicam 360",
            description="Complex steadicam movement...",
            ai_reproducibility={
                "reproducible": False,
                "limitations": ["Too complex for current AI"],
            },
        )

        assert technique.is_ai_reproducible is False
        assert technique.supported_platforms == []

    def test_famous_examples(self):
        """Test famous examples JSONB field."""
        technique = CinematographyTechnique(
            technique_id="dolly_zoom",
            category="camera_movement",
            name_en="Dolly Zoom",
            description="Camera technique...",
            famous_examples=[
                {
                    "film": "Vertigo",
                    "scene": "Bell tower scene",
                    "director": "Cipher Gray",
                    "year": 1958,
                    "description": "First famous use of the technique",
                },
                {
                    "film": "Jaws",
                    "scene": "Beach realization",
                    "director": "Min Seoyeon",
                    "year": 1975,
                    "description": "Chief Brody realizes shark attack",
                },
            ],
        )

        assert len(technique.famous_examples) == 2
        assert technique.famous_examples[0]["film"] == "Vertigo"

    def test_execution_details(self):
        """Test execution details JSONB field."""
        technique = CinematographyTechnique(
            technique_id="dolly_zoom",
            category="camera_movement",
            name_en="Dolly Zoom",
            description="Camera technique...",
            execution_details={
                "equipment": ["dolly", "zoom lens", "track"],
                "difficulty": "hard",
                "duration_typical": "3-10 seconds",
            },
        )

        assert technique.execution_details["difficulty"] == "hard"
        assert "dolly" in technique.execution_details["equipment"]

    def test_repr(self):
        """Test string representation."""
        technique = CinematographyTechnique(
            technique_id="dolly_zoom",
            category="camera_movement",
            name_en="Dolly Zoom",
            description="Camera technique...",
        )
        assert "CinematographyTechnique" in repr(technique)
        assert "dolly_zoom" in repr(technique)


# =============================================================================
# Enum Tests
# =============================================================================


class TestEnums:
    """Test enum values."""

    def test_reference_type_values(self):
        """Test ReferenceType enum values."""
        assert ReferenceType.VIDEO.value == "video"
        assert ReferenceType.IMAGE.value == "image"

    def test_analysis_depth_values(self):
        """Test AnalysisDepth enum values."""
        assert AnalysisDepth.QUICK.value == "quick"
        assert AnalysisDepth.DETAILED.value == "detailed"
        assert AnalysisDepth.COMPREHENSIVE.value == "comprehensive"


# =============================================================================
# JSONB Field Tests
# =============================================================================


class TestJSONBFields:
    """Test JSONB field handling."""

    def test_jsonb_default_list(self):
        """Test JSONB fields accept empty list values."""
        item = ReferenceItem(
            user_id="user-123",
            name="Test",
            reference_type="image",
            source_url="https://example.com/image.jpg",
            tags=[],
            moodboard_frames=[],
            evidence_refs=[],
            analysis_result={},
        )
        assert item.tags == []
        assert item.moodboard_frames == []
        assert item.evidence_refs == []

    def test_jsonb_default_dict(self):
        """Test JSONB fields accept empty dict values."""
        item = ReferenceItem(
            user_id="user-123",
            name="Test",
            reference_type="image",
            source_url="https://example.com/image.jpg",
            tags=[],
            moodboard_frames=[],
            evidence_refs=[],
            analysis_result={},
        )
        assert item.analysis_result == {}

    def test_jsonb_mutation(self):
        """Test JSONB fields can be mutated."""
        preset = StylePreset(
            user_id="user-123",
            name="Test",
            style_data={"key": "value"},
        )
        preset.style_data["new_key"] = "new_value"
        assert preset.style_data["new_key"] == "new_value"

    def test_jsonb_nested_access(self):
        """Test nested JSONB field access."""
        scene = ReferenceScene(
            scene_key="test",
            film_title="Test",
            description="Test",
            cinematography={
                "lighting": {
                    "key_light": "high",
                    "fill_ratio": "2:1",
                },
            },
        )
        assert scene.cinematography["lighting"]["key_light"] == "high"
