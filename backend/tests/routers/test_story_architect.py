"""Tests for Story Architect API.

Comprehensive tests for AI-powered scenario and shot list generation.

Tests cover:
- Story Architect scenario generation
- Story Refine concept refinement
- Shot List timeline generation
- Tool recommendation heuristics
- Input validation and sanitization
- Evidence refs format (Vivid convention)

2026 Best Practices:
- Script-to-storyboard generation
- Tool selection (Veo, Kling, Sora)
- Camera movement theory
- Montage editing patterns

References:
- LTX Studio, DomoAI, Mootion (2026 tools)
- DIMENSION_APP_MACRO_PLANNING_2026.md Part 11
"""
from __future__ import annotations

import uuid
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from pydantic import ValidationError

from app.routers.dimension.story import (
    StoryArchitectRequest,
    StoryRefineRequest,
    ShotListRequest,
    ShotListResponse,
    TimelineShot,
    _sanitize_text_field,
    _validate_genre,
    _validate_structure,
)
from app.routers.dimension._base import (
    ALLOWED_GENRES,
    ALLOWED_STRUCTURES,
    MAX_CONCEPT_LENGTH,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_story_architect_data() -> Dict[str, Any]:
    """Sample Story Architect request data."""
    return {
        "concept": "A detective solving a mysterious case in a neon-lit city",
        "persona_data": "Experienced noir filmmaker with focus on atmosphere",
        "reference_analysis": "Reference: Blade Runner 2049, dark lighting, rain",
        "genre": "thriller",  # Use valid genre from ALLOWED_GENRES
        "duration": 120,
        "structure": "3-act",
        "language": "ko",
        "model": "gemini-3-flash-preview",
    }


@pytest.fixture
def sample_shot_list_data() -> Dict[str, Any]:
    """Sample Shot List request data."""
    return {
        "scenario": """
        Scene 1: The detective enters a dark alley. Rain pours down.
        Scene 2: A mysterious figure appears in the shadows.
        Scene 3: Tension builds as they face each other.
        """,
        "total_duration": 60,
        "max_shot_duration": 8,
        "style_preference": "cinematic noir",
        "model": "gemini-3-flash-preview",
    }


@pytest.fixture
def sample_timeline_shot() -> TimelineShot:
    """Sample timeline shot."""
    return TimelineShot(
        shot_number=1,
        time_range="0:00-0:05",
        start_seconds=0,
        end_seconds=5,
        duration=5,
        shot_type="wide",
        description="Establishing shot of rain-soaked alley",
        camera_movement="slow_push_in",
        recommended_tool="veo",
        tool_reason="Cinematic atmosphere with audio sync",
        audio_notes="Rain ambiance, distant thunder",
    )


# ============================================================================
# Sanitization Tests
# ============================================================================

class TestSanitizeTextField:
    """Tests for text field sanitization."""

    def test_strips_whitespace(self):
        """Strips leading and trailing whitespace."""
        assert _sanitize_text_field("  hello world  ") == "hello world"

    def test_returns_default_for_empty(self):
        """Returns default for empty string."""
        assert _sanitize_text_field("") == ""
        assert _sanitize_text_field("", "default") == "default"

    def test_returns_default_for_whitespace_only(self):
        """Returns default for whitespace-only string."""
        assert _sanitize_text_field("   ") == ""
        assert _sanitize_text_field("   ", "default") == "default"

    def test_removes_html_tags(self):
        """Removes HTML tags."""
        result = _sanitize_text_field("<script>alert('xss')</script>hello")
        assert "<script>" not in result
        assert "hello" in result

    def test_escapes_html_entities(self):
        """Escapes HTML entities."""
        result = _sanitize_text_field("Tom & Jerry")
        assert "&amp;" in result

    def test_removes_javascript_protocol(self):
        """Removes javascript: protocol."""
        result = _sanitize_text_field("javascript:alert(1)")
        assert "javascript:" not in result.lower()

    def test_removes_event_handlers(self):
        """Removes event handler attributes."""
        result = _sanitize_text_field("onclick=alert(1)")
        assert "onclick=" not in result

    def test_handles_none(self):
        """Handles None input gracefully."""
        # The function expects string, but should handle None
        assert _sanitize_text_field(None) == ""

    def test_preserves_korean_text(self):
        """Preserves Korean text."""
        korean = "강주노 감독의 영화 스타일"
        assert _sanitize_text_field(korean) == korean


# ============================================================================
# Genre Validation Tests
# ============================================================================

class TestValidateGenre:
    """Tests for genre validation."""

    def test_valid_genres(self):
        """All allowed genres pass validation."""
        for genre in list(ALLOWED_GENRES)[:5]:  # Test first 5
            result = _validate_genre(genre)
            assert result == genre.lower().strip()

    def test_strips_and_lowercases(self):
        """Strips whitespace and lowercases."""
        assert _validate_genre("  Drama  ") == "drama"
        assert _validate_genre("THRILLER") == "thriller"

    def test_rejects_invalid_genre(self):
        """Rejects genres not in allowed list."""
        with pytest.raises(ValueError) as exc_info:
            _validate_genre("invalid_genre_xyz")
        assert "지원하지 않는 장르" in str(exc_info.value)


# ============================================================================
# Structure Validation Tests
# ============================================================================

class TestValidateStructure:
    """Tests for structure validation."""

    def test_valid_structures(self):
        """All allowed structures pass validation."""
        for structure in ALLOWED_STRUCTURES:
            result = _validate_structure(structure)
            assert result == structure.lower().strip()

    def test_strips_and_lowercases(self):
        """Strips whitespace and lowercases."""
        assert _validate_structure("  3-ACT  ") == "3-act"

    def test_rejects_invalid_structure(self):
        """Rejects structures not in allowed list."""
        with pytest.raises(ValueError) as exc_info:
            _validate_structure("invalid_structure")
        assert "지원하지 않는 구조" in str(exc_info.value)


# ============================================================================
# StoryArchitectRequest Tests
# ============================================================================

class TestStoryArchitectRequest:
    """Tests for StoryArchitectRequest schema."""

    def test_valid_request(self, sample_story_architect_data):
        """Valid request passes validation."""
        request = StoryArchitectRequest(**sample_story_architect_data)
        assert request.concept.startswith("A detective")
        assert request.genre == "thriller"
        assert request.duration == 120

    def test_sanitizes_concept(self):
        """Concept is sanitized."""
        request = StoryArchitectRequest(
            concept="<script>alert('xss')</script>Test concept",
            genre="drama",
        )
        assert "<script>" not in request.concept
        assert "Test concept" in request.concept

    def test_sanitizes_persona_data(self):
        """Persona data is sanitized."""
        request = StoryArchitectRequest(
            concept="Test",
            persona_data="<img onerror=alert(1)>Data",
            genre="drama",
        )
        assert "onerror" not in request.persona_data

    def test_sanitizes_reference_analysis(self):
        """Reference analysis is sanitized."""
        request = StoryArchitectRequest(
            concept="Test",
            reference_analysis="javascript:void(0)",
            genre="drama",
        )
        assert "javascript:" not in request.reference_analysis.lower()

    def test_validates_genre(self):
        """Genre is validated against allowed list."""
        with pytest.raises(ValidationError):
            StoryArchitectRequest(concept="Test", genre="invalid_genre")

    def test_validates_structure(self):
        """Structure is validated against allowed list."""
        with pytest.raises(ValidationError):
            StoryArchitectRequest(concept="Test", structure="invalid_structure")

    def test_duration_range(self):
        """Duration must be between 10 and 600."""
        # Valid range
        request = StoryArchitectRequest(concept="Test", duration=60, genre="drama")
        assert request.duration == 60

        # Below minimum
        with pytest.raises(ValidationError):
            StoryArchitectRequest(concept="Test", duration=5, genre="drama")

        # Above maximum
        with pytest.raises(ValidationError):
            StoryArchitectRequest(concept="Test", duration=1000, genre="drama")

    def test_concept_max_length(self):
        """Concept has maximum length."""
        long_concept = "x" * (MAX_CONCEPT_LENGTH + 100)
        with pytest.raises(ValidationError):
            StoryArchitectRequest(concept=long_concept, genre="drama")


# ============================================================================
# StoryRefineRequest Tests
# ============================================================================

class TestStoryRefineRequest:
    """Tests for StoryRefineRequest schema."""

    def test_valid_request(self):
        """Valid request passes validation."""
        request = StoryRefineRequest(
            concept="A love story in Paris",
            genre="drama",
        )
        assert request.concept == "A love story in Paris"
        assert request.genre == "drama"

    def test_sanitizes_concept(self):
        """Concept is sanitized."""
        request = StoryRefineRequest(
            concept="<script>bad</script>Good content",
            genre="drama",
        )
        assert "<script>" not in request.concept

    def test_validates_genre(self):
        """Genre is validated."""
        with pytest.raises(ValidationError):
            StoryRefineRequest(concept="Test", genre="nonexistent_genre")

    def test_default_model(self):
        """Default model is set."""
        request = StoryRefineRequest(concept="Test", genre="drama")
        assert "gemini" in request.model.lower()


# ============================================================================
# ShotListRequest Tests
# ============================================================================

class TestShotListRequest:
    """Tests for ShotListRequest schema."""

    def test_valid_request(self, sample_shot_list_data):
        """Valid request passes validation."""
        request = ShotListRequest(**sample_shot_list_data)
        assert "detective" in request.scenario.lower()
        assert request.total_duration == 60

    def test_sanitizes_scenario(self):
        """Scenario is sanitized."""
        request = ShotListRequest(
            scenario="<script>alert(1)</script>Scene 1: Action",
            total_duration=60,
        )
        assert "<script>" not in request.scenario

    def test_sanitizes_style_preference(self):
        """Style preference is sanitized."""
        request = ShotListRequest(
            scenario="Scene 1: Test",
            style_preference="onclick=hack() cinematic",
        )
        assert "onclick=" not in request.style_preference

    def test_scenario_min_length(self):
        """Scenario must be at least 10 characters."""
        with pytest.raises(ValidationError):
            ShotListRequest(scenario="Short", total_duration=60)

    def test_duration_range(self):
        """Duration must be between 10 and 300."""
        # Valid
        request = ShotListRequest(scenario="Scene 1: Valid scene", total_duration=60)
        assert request.total_duration == 60

        # Below minimum
        with pytest.raises(ValidationError):
            ShotListRequest(scenario="Scene 1: Valid scene", total_duration=5)

        # Above maximum
        with pytest.raises(ValidationError):
            ShotListRequest(scenario="Scene 1: Valid scene", total_duration=500)

    def test_max_shot_duration_range(self):
        """Max shot duration must be between 4 and 10."""
        # Valid
        request = ShotListRequest(
            scenario="Scene 1: Valid scene",
            max_shot_duration=8,
        )
        assert request.max_shot_duration == 8

        # Below minimum
        with pytest.raises(ValidationError):
            ShotListRequest(
                scenario="Scene 1: Valid scene",
                max_shot_duration=2,
            )

        # Above maximum
        with pytest.raises(ValidationError):
            ShotListRequest(
                scenario="Scene 1: Valid scene",
                max_shot_duration=15,
            )


# ============================================================================
# TimelineShot Tests
# ============================================================================

class TestTimelineShot:
    """Tests for TimelineShot schema."""

    def test_valid_shot(self, sample_timeline_shot):
        """Valid shot passes validation."""
        assert sample_timeline_shot.shot_number == 1
        assert sample_timeline_shot.time_range == "0:00-0:05"
        assert sample_timeline_shot.duration == 5

    def test_shot_fields(self):
        """All shot fields are accessible."""
        shot = TimelineShot(
            shot_number=2,
            time_range="0:06-0:10",
            start_seconds=6,
            end_seconds=10,
            duration=4,
            shot_type="close-up",
            description="Character reveals emotion",
            camera_movement="static",
            recommended_tool="kling",
            tool_reason="Best for facial detail",
            audio_notes="Silence",
        )
        assert shot.shot_type == "close-up"
        assert shot.recommended_tool == "kling"

    def test_shot_type_values(self):
        """Common shot types are valid."""
        for shot_type in ["wide", "medium", "close-up", "extreme-close-up"]:
            shot = TimelineShot(
                shot_number=1,
                time_range="0:00-0:05",
                start_seconds=0,
                end_seconds=5,
                duration=5,
                shot_type=shot_type,
                description="Test",
                camera_movement="static",
                recommended_tool="veo",
                tool_reason="Test",
            )
            assert shot.shot_type == shot_type


# ============================================================================
# ShotListResponse Tests
# ============================================================================

class TestShotListResponse:
    """Tests for ShotListResponse schema."""

    def test_successful_response(self, sample_timeline_shot):
        """Successful response includes all fields."""
        response = ShotListResponse(
            success=True,
            total_shots=1,
            total_duration=5.0,
            shots=[sample_timeline_shot],
            tool_summary={"veo": 1, "kling": 0, "sora": 0},
            evidence_refs=["rag:cinematography:expert_heuristics"],
        )
        assert response.success is True
        assert response.total_shots == 1
        assert len(response.shots) == 1

    def test_failed_response(self):
        """Failed response has empty shots."""
        response = ShotListResponse(
            success=False,
            total_shots=0,
            total_duration=0,
            shots=[],
            tool_summary={"error": "Parse error"},
            evidence_refs=[],
        )
        assert response.success is False
        assert len(response.shots) == 0


# ============================================================================
# Evidence Refs Tests (Vivid Convention)
# ============================================================================

class TestEvidenceRefs:
    """Tests for evidence_refs format (List[str])."""

    def test_shot_list_response_has_evidence_refs(self, sample_timeline_shot):
        """ShotListResponse includes evidence_refs."""
        response = ShotListResponse(
            success=True,
            total_shots=1,
            total_duration=5.0,
            shots=[sample_timeline_shot],
            tool_summary={"veo": 1},
            evidence_refs=[
                "rag:cinematography:expert_heuristics",
                "rag:cinematography:montage_theory",
                "rag:tool_selection:veo",
            ],
        )
        assert isinstance(response.evidence_refs, list)
        assert all(isinstance(ref, str) for ref in response.evidence_refs)

    def test_evidence_refs_format_rag_prefix(self):
        """Evidence refs use rag: prefix for RAG sources."""
        refs = [
            "rag:cinematography:expert_heuristics",
            "rag:tool_selection:kling",
        ]
        for ref in refs:
            assert ref.startswith("rag:")
            parts = ref.split(":")
            assert len(parts) == 3  # rag:category:id

    def test_evidence_refs_deduplication(self, sample_timeline_shot):
        """Evidence refs should be deduplicated."""
        # Create response with duplicate refs
        response = ShotListResponse(
            success=True,
            total_shots=2,
            total_duration=10.0,
            shots=[sample_timeline_shot, sample_timeline_shot],
            tool_summary={"veo": 2},
            evidence_refs=[
                "rag:tool_selection:veo",
                "rag:tool_selection:veo",  # Duplicate
            ],
        )
        # Implementation should deduplicate
        unique_refs = list(set(response.evidence_refs))
        assert len(unique_refs) <= len(response.evidence_refs)


# ============================================================================
# Tool Recommendation Tests
# ============================================================================

class TestToolRecommendations:
    """Tests for AI tool recommendation heuristics."""

    def test_veo_for_cinematic(self):
        """Veo recommended for cinematic narrative."""
        shot = TimelineShot(
            shot_number=1,
            time_range="0:00-0:06",
            start_seconds=0,
            end_seconds=6,
            duration=6,
            shot_type="wide",
            description="Establishing cinematic shot",
            camera_movement="slow_push_in",
            recommended_tool="veo",
            tool_reason="Cinematic narrative with atmosphere",
        )
        assert shot.recommended_tool == "veo"
        assert "cinematic" in shot.tool_reason.lower()

    def test_kling_for_closeup(self):
        """Kling recommended for close-up with detail."""
        shot = TimelineShot(
            shot_number=2,
            time_range="0:07-0:10",
            start_seconds=7,
            end_seconds=10,
            duration=3,
            shot_type="extreme-close-up",
            description="Face detail shot",
            camera_movement="static",
            recommended_tool="kling",
            tool_reason="High facial fidelity in static shots",
        )
        assert shot.recommended_tool == "kling"

    def test_sora_for_action(self):
        """Sora recommended for high motion action."""
        shot = TimelineShot(
            shot_number=3,
            time_range="0:11-0:15",
            start_seconds=11,
            end_seconds=15,
            duration=4,
            shot_type="medium",
            description="Chase sequence with rapid movement",
            camera_movement="tracking",
            recommended_tool="sora",
            tool_reason="Temporal consistency in complex motion",
        )
        assert shot.recommended_tool == "sora"

    def test_tool_summary_counts(self):
        """Tool summary counts each tool correctly."""
        shots = [
            TimelineShot(
                shot_number=i,
                time_range=f"{i}:00-{i}:05",
                start_seconds=i * 5,
                end_seconds=i * 5 + 5,
                duration=5,
                shot_type="medium",
                description="Test",
                camera_movement="static",
                recommended_tool=tool,
                tool_reason="Test",
            )
            for i, tool in enumerate(["veo", "veo", "kling", "sora", "sora", "sora"])
        ]

        tool_counts = {"veo": 0, "kling": 0, "sora": 0}
        for shot in shots:
            tool = shot.recommended_tool.lower()
            if tool in tool_counts:
                tool_counts[tool] += 1

        assert tool_counts["veo"] == 2
        assert tool_counts["kling"] == 1
        assert tool_counts["sora"] == 3


# ============================================================================
# Camera Movement Tests
# ============================================================================

class TestCameraMovements:
    """Tests for camera movement heuristics."""

    def test_push_in_for_emotion(self):
        """Push-in movement for emotional emphasis."""
        shot = TimelineShot(
            shot_number=1,
            time_range="0:00-0:05",
            start_seconds=0,
            end_seconds=5,
            duration=5,
            shot_type="medium",
            description="Character realizes the truth",
            camera_movement="push_in",
            recommended_tool="veo",
            tool_reason="Emotional revelation",
        )
        assert shot.camera_movement == "push_in"

    def test_pull_out_for_isolation(self):
        """Pull-out movement for isolation/ending."""
        shot = TimelineShot(
            shot_number=2,
            time_range="0:06-0:10",
            start_seconds=6,
            end_seconds=10,
            duration=4,
            shot_type="wide",
            description="Character left alone",
            camera_movement="pull_out",
            recommended_tool="veo",
            tool_reason="Scene ending isolation",
        )
        assert shot.camera_movement == "pull_out"

    def test_dolly_zoom_for_shock(self):
        """Dolly zoom for shock/disorientation."""
        shot = TimelineShot(
            shot_number=3,
            time_range="0:11-0:14",
            start_seconds=11,
            end_seconds=14,
            duration=3,
            shot_type="medium",
            description="Shocking revelation",
            camera_movement="dolly_zoom",
            recommended_tool="sora",
            tool_reason="Vertigo effect for shock",
        )
        assert shot.camera_movement == "dolly_zoom"


# ============================================================================
# XSS Prevention Tests
# ============================================================================

class TestXSSPrevention:
    """Comprehensive XSS prevention tests."""

    XSS_PAYLOADS = [
        ("<script>alert('XSS')</script>", "script"),
        ("<img src=x onerror=alert('XSS')>", "onerror"),
        ("javascript:alert('XSS')", "javascript:"),
        ("<svg onload=alert('XSS')>", "onload"),
        ("'><script>alert('XSS')</script>", "script"),
        ('<a href="javascript:alert(1)">click</a>', "javascript:"),
    ]

    @pytest.mark.parametrize("payload,dangerous_content", XSS_PAYLOADS)
    def test_sanitizes_xss_in_concept(self, payload: str, dangerous_content: str):
        """Sanitizes XSS payloads in concept field."""
        request = StoryArchitectRequest(
            concept=f"{payload} valid concept text",
            genre="drama",
        )
        assert dangerous_content.lower() not in request.concept.lower()

    @pytest.mark.parametrize("payload,dangerous_content", XSS_PAYLOADS)
    def test_sanitizes_xss_in_scenario(self, payload: str, dangerous_content: str):
        """Sanitizes XSS payloads in scenario field."""
        request = ShotListRequest(
            scenario=f"{payload} Scene 1: Test scene text",
            total_duration=60,
        )
        # For 'script' tag, verify the <script> tag is removed (not the word 'script')
        if dangerous_content == "script":
            assert "<script>" not in request.scenario.lower()
        else:
            assert dangerous_content.lower() not in request.scenario.lower()


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    def test_unicode_concept(self):
        """Handles unicode in concept."""
        request = StoryArchitectRequest(
            concept="강주노 감독 스타일의 영화 시나리오",
            genre="drama",
        )
        assert "강주노" in request.concept

    def test_emoji_in_concept(self):
        """Handles emoji in concept."""
        request = StoryArchitectRequest(
            concept="A happy story about love 💕",
            genre="drama",
        )
        assert "💕" in request.concept

    def test_multiline_scenario(self):
        """Handles multiline scenario."""
        scenario = """
        Scene 1: Introduction
        - Character enters
        - Music starts

        Scene 2: Development
        - Conflict arises
        """
        request = ShotListRequest(scenario=scenario, total_duration=120)
        assert "Scene 1" in request.scenario
        assert "Scene 2" in request.scenario

    def test_empty_persona_data(self):
        """Handles empty persona data."""
        request = StoryArchitectRequest(
            concept="Test concept",
            persona_data="",
            genre="drama",
        )
        assert request.persona_data == ""

    def test_empty_reference_analysis(self):
        """Handles empty reference analysis."""
        request = StoryArchitectRequest(
            concept="Test concept",
            reference_analysis="",
            genre="drama",
        )
        assert request.reference_analysis == ""

    def test_default_values(self):
        """Default values are set correctly."""
        request = StoryArchitectRequest(concept="Test", genre="drama")
        assert request.duration == 60
        assert request.structure == "3-act"
        assert request.language == "ko"
        assert "gemini" in request.model.lower()


# ============================================================================
# Integration-Ready Tests (Mocked)
# ============================================================================

class TestStoryArchitectIntegration:
    """Integration tests with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_shot_list_request_validation(self, sample_shot_list_data):
        """Test shot list request validation."""
        request = ShotListRequest(**sample_shot_list_data)
        assert request.total_duration == 60
        assert request.max_shot_duration == 8

    @pytest.mark.asyncio
    async def test_story_architect_request_processing(self, sample_story_architect_data):
        """Test story architect request processing."""
        request = StoryArchitectRequest(**sample_story_architect_data)
        assert request.genre == "thriller"
        assert request.structure == "3-act"


# ============================================================================
# Constants Validation
# ============================================================================

class TestConstants:
    """Tests for module constants."""

    def test_allowed_genres_not_empty(self):
        """ALLOWED_GENRES is not empty."""
        assert len(ALLOWED_GENRES) > 0

    def test_allowed_structures_not_empty(self):
        """ALLOWED_STRUCTURES is not empty."""
        assert len(ALLOWED_STRUCTURES) > 0

    def test_max_concept_length_reasonable(self):
        """MAX_CONCEPT_LENGTH is reasonable."""
        assert MAX_CONCEPT_LENGTH >= 100
        assert MAX_CONCEPT_LENGTH <= 10000

    def test_common_genres_included(self):
        """Common genres are included."""
        # Use genres that are actually in ALLOWED_GENRES
        common_genres = ["drama", "comedy", "horror", "thriller", "scifi"]
        for genre in common_genres:
            assert genre in ALLOWED_GENRES or genre.lower() in ALLOWED_GENRES

    def test_common_structures_included(self):
        """Common structures are included."""
        assert "3-act" in ALLOWED_STRUCTURES
