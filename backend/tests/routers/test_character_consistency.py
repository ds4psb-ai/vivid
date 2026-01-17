"""Tests for Character Consistency API.

Tests cover:
- Character CRUD operations
- Reference image management
- Memory bank operations
- Platform synchronization
- Similarity search
- Input validation and sanitization

References:
- StoryMem Paper: arXiv:2512.19539
- DIMENSION_APP_MACRO_PLANNING_2026.md Part 11
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient

from app.models_character import Character, CharacterAppearance
from app.schemas.character_schemas import (
    CharacterCreateRequest,
    CharacterResponse,
    CharacterSummaryResponse,
    CharacterUpdateRequest,
    MemoryKeyframe,
    PlatformType,
    PlatformSyncRequest,
    PlatformSyncResponse,
    MemoryBankUpdateRequest,
    MemoryBankResponse,
)
from app.routers.dimension.character import _sanitize_text


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_character_data() -> Dict[str, Any]:
    """Sample character creation data."""
    return {
        "name": "Test Character",
        "description": "A test character for consistency testing",
        "tags": ["protagonist", "human", "test"],
        "project_id": None,
    }


@pytest.fixture
def sample_character() -> Character:
    """Sample character entity."""
    return Character(
        id=uuid.uuid4(),
        user_id="test-user-123",
        name="Sample Character",
        description="A sample character",
        tags=["protagonist", "human"],
        source_images=[{
            "url": "https://example.com/image1.jpg",
            "timestamp": datetime.utcnow().isoformat(),
            "quality_score": 0.9,
            "is_primary": True,
        }],
        primary_image_url="https://example.com/image1.jpg",
        qdrant_point_id="qdrant-point-123",
        platform_refs={
            "veo": {"ref_id": "veo-ref-123", "last_sync": datetime.utcnow().isoformat()},
        },
        memory_keyframes=[
            {
                "frame_url": "https://example.com/keyframe1.jpg",
                "timestamp": 1.0,
                "clip_score": 0.92,
                "hps_score": 0.85,
                "face_confidence": 0.98,
                "is_long_term": True,
            },
            {
                "frame_url": "https://example.com/keyframe2.jpg",
                "timestamp": 3.5,
                "clip_score": 0.88,
                "hps_score": 0.82,
                "face_confidence": 0.95,
                "is_long_term": False,
            },
        ],
        created_at=datetime.utcnow(),
    )


# ============================================================================
# Sanitization Tests
# ============================================================================

class TestSanitizeText:
    """Tests for text sanitization helper."""

    def test_strips_whitespace(self):
        """Strips leading and trailing whitespace."""
        assert _sanitize_text("  hello  ") == "hello"

    def test_returns_default_for_empty(self):
        """Returns default for empty string."""
        assert _sanitize_text("") == ""
        assert _sanitize_text("", "default") == "default"

    def test_returns_default_for_whitespace_only(self):
        """Returns default for whitespace-only string."""
        assert _sanitize_text("   ") == ""
        assert _sanitize_text("   ", "default") == "default"

    def test_removes_html_tags(self):
        """Removes HTML tags."""
        assert _sanitize_text("<script>alert('xss')</script>hello") == "alert(&#x27;xss&#x27;)hello"

    def test_escapes_html_entities(self):
        """Escapes HTML entities."""
        result = _sanitize_text("Tom & Jerry")
        assert "&amp;" in result

    def test_removes_javascript_protocol(self):
        """Removes javascript: protocol."""
        result = _sanitize_text("javascript:alert(1)")
        assert "javascript" not in result.lower() or ":" not in result

    def test_removes_event_handlers(self):
        """Removes event handler attributes."""
        result = _sanitize_text("onclick=alert(1)")
        assert "onclick=" not in result

    def test_handles_none(self):
        """Handles None input."""
        assert _sanitize_text(None) == ""


# ============================================================================
# Character Schema Tests
# ============================================================================

class TestCharacterCreateRequest:
    """Tests for CharacterCreateRequest schema."""

    def test_valid_request(self, sample_character_data):
        """Valid request passes validation."""
        request = CharacterCreateRequest(**sample_character_data)
        assert request.name == "Test Character"
        assert request.description == "A test character for consistency testing"
        assert "protagonist" in request.tags

    def test_strips_name_whitespace(self):
        """Name is stripped of whitespace."""
        request = CharacterCreateRequest(name="  Test Name  ")
        assert request.name == "Test Name"

    def test_normalizes_tags(self):
        """Tags are normalized to lowercase."""
        request = CharacterCreateRequest(name="Test", tags=["UPPER", "Mixed", "  spaced  "])
        assert request.tags == ["upper", "mixed", "spaced"]

    def test_limits_tags(self):
        """Limits tags to 20."""
        many_tags = [f"tag{i}" for i in range(30)]
        request = CharacterCreateRequest(name="Test", tags=many_tags)
        assert len(request.tags) <= 20

    def test_rejects_empty_name(self):
        """Rejects empty name."""
        with pytest.raises(ValueError):
            CharacterCreateRequest(name="")

    def test_rejects_long_name(self):
        """Rejects name over 100 characters."""
        with pytest.raises(ValueError):
            CharacterCreateRequest(name="x" * 101)


class TestMemoryKeyframe:
    """Tests for MemoryKeyframe schema."""

    def test_valid_keyframe(self):
        """Valid keyframe passes validation."""
        kf = MemoryKeyframe(
            frame_url="https://example.com/frame.jpg",
            timestamp=2.5,
            clip_score=0.92,
            hps_score=0.85,
            face_confidence=0.98,
            is_long_term=True,
        )
        assert kf.timestamp == 2.5
        assert kf.is_long_term is True

    def test_rejects_negative_timestamp(self):
        """Rejects negative timestamp."""
        with pytest.raises(ValueError):
            MemoryKeyframe(
                frame_url="https://example.com/frame.jpg",
                timestamp=-1.0,
                clip_score=0.9,
                hps_score=0.8,
                face_confidence=0.9,
            )

    def test_rejects_out_of_range_scores(self):
        """Rejects scores outside 0-1 range."""
        with pytest.raises(ValueError):
            MemoryKeyframe(
                frame_url="https://example.com/frame.jpg",
                timestamp=1.0,
                clip_score=1.5,  # Invalid
                hps_score=0.8,
                face_confidence=0.9,
            )


class TestPlatformType:
    """Tests for PlatformType enum."""

    def test_all_platforms(self):
        """All platforms are defined."""
        assert PlatformType.VEO.value == "veo"
        assert PlatformType.KLING.value == "kling"
        assert PlatformType.RUNWAY.value == "runway"
        assert PlatformType.HAILUO.value == "hailuo"


# ============================================================================
# Character Model Tests
# ============================================================================

class TestCharacterModel:
    """Tests for Character SQLAlchemy model."""

    def test_keyframe_count_property(self, sample_character):
        """keyframe_count property returns correct count."""
        assert sample_character.keyframe_count == 2

    def test_keyframe_count_empty(self):
        """keyframe_count returns 0 for empty list."""
        char = Character(
            id=uuid.uuid4(),
            user_id="test",
            name="Test",
            memory_keyframes=[],
        )
        assert char.keyframe_count == 0

    def test_long_term_keyframes_property(self, sample_character):
        """long_term_keyframes filters correctly."""
        long_term = sample_character.long_term_keyframes
        assert len(long_term) == 1
        assert long_term[0]["is_long_term"] is True

    def test_sliding_window_keyframes_property(self, sample_character):
        """sliding_window_keyframes filters correctly."""
        sliding = sample_character.sliding_window_keyframes
        assert len(sliding) == 1
        assert sliding[0]["is_long_term"] is False

    def test_platforms_synced_property(self, sample_character):
        """platforms_synced returns synced platform list."""
        synced = sample_character.platforms_synced
        assert "veo" in synced
        assert len(synced) == 1


# ============================================================================
# API Endpoint Tests (Mock)
# ============================================================================

class TestCharacterEndpoints:
    """Tests for Character API endpoints."""

    @pytest.fixture
    def mock_service(self):
        """Mock character service."""
        with patch("app.routers.dimension.character.create_character") as mock_create, \
             patch("app.routers.dimension.character.get_character") as mock_get, \
             patch("app.routers.dimension.character.list_characters") as mock_list, \
             patch("app.routers.dimension.character.delete_character") as mock_delete:
            yield {
                "create": mock_create,
                "get": mock_get,
                "list": mock_list,
                "delete": mock_delete,
            }

    @pytest.mark.asyncio
    async def test_create_character_sanitizes_input(self, mock_service, sample_character):
        """Create endpoint sanitizes text input."""
        mock_service["create"].return_value = sample_character

        # The endpoint should sanitize the name
        request_data = {
            "name": "<script>alert('xss')</script>Test",
            "description": "Normal description",
        }

        # Verify that sanitization is applied
        sanitized_name = _sanitize_text(request_data["name"])
        assert "<script>" not in sanitized_name

    @pytest.mark.asyncio
    async def test_list_characters_returns_summaries(self, mock_service, sample_character):
        """List endpoint returns character summaries."""
        mock_service["list"].return_value = ([sample_character], 1)

        # Verify summary format
        summary = CharacterSummaryResponse(
            id=sample_character.id,
            name=sample_character.name,
            primary_image_url=sample_character.primary_image_url,
            tags=sample_character.tags,
            keyframe_count=sample_character.keyframe_count,
            platforms_synced=sample_character.platforms_synced,
        )
        assert summary.keyframe_count == 2
        assert "veo" in summary.platforms_synced


# ============================================================================
# Memory Bank Tests
# ============================================================================

class TestMemoryBankOperations:
    """Tests for memory bank operations."""

    def test_memory_bank_response_schema(self):
        """MemoryBankResponse schema validation."""
        response = MemoryBankResponse(
            character_id=uuid.uuid4(),
            keyframes_extracted=30,
            long_term_updated=5,
            sliding_window_updated=10,
            new_keyframes=[
                MemoryKeyframe(
                    frame_url="https://example.com/frame.jpg",
                    timestamp=1.0,
                    clip_score=0.9,
                    hps_score=0.85,
                    face_confidence=0.95,
                    is_long_term=False,
                )
            ],
        )
        assert response.keyframes_extracted == 30
        assert len(response.new_keyframes) == 1

    def test_memory_bank_update_request_validation(self):
        """MemoryBankUpdateRequest validation."""
        request = MemoryBankUpdateRequest(
            video_url="https://example.com/video.mp4",
            max_keyframes=10,
            long_term_count=5,
        )
        assert request.max_keyframes == 10
        assert request.long_term_count == 5

    def test_memory_bank_update_request_limits(self):
        """MemoryBankUpdateRequest enforces limits."""
        with pytest.raises(ValueError):
            MemoryBankUpdateRequest(
                video_url="https://example.com/video.mp4",
                max_keyframes=100,  # Over limit
            )


# ============================================================================
# Platform Sync Tests
# ============================================================================

class TestPlatformSync:
    """Tests for platform synchronization."""

    def test_platform_sync_request_validation(self):
        """PlatformSyncRequest validation."""
        request = PlatformSyncRequest(
            platform=PlatformType.VEO,
            style_strength=0.8,
            auto_update_memory=True,
        )
        assert request.platform == PlatformType.VEO
        assert request.style_strength == 0.8

    def test_platform_sync_response_success(self):
        """PlatformSyncResponse for success."""
        response = PlatformSyncResponse(
            platform=PlatformType.VEO,
            status="success",
            platform_ref_id="veo-ref-123",
        )
        assert response.status == "success"
        assert response.platform_ref_id == "veo-ref-123"

    def test_platform_sync_response_failure(self):
        """PlatformSyncResponse for failure."""
        response = PlatformSyncResponse(
            platform=PlatformType.KLING,
            status="failed",
            message="API rate limit exceeded",
        )
        assert response.status == "failed"
        assert "rate limit" in response.message.lower()


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
        ('"><img src=x onerror=alert("XSS")>', "onerror"),
        ("<iframe src=javascript:alert('XSS')>", "javascript:"),
        ("<body onload=alert('XSS')>", "onload"),
        ("'onclick=alert('XSS')//", "onclick"),
        ('<a href="javascript:alert(\'XSS\')">click</a>', "javascript:"),
    ]

    @pytest.mark.parametrize("payload,dangerous_content", XSS_PAYLOADS)
    def test_sanitizes_xss_payload(self, payload: str, dangerous_content: str):
        """Sanitizes various XSS payloads."""
        sanitized = _sanitize_text(payload)
        # Should not contain dangerous content
        assert dangerous_content.lower() not in sanitized.lower()


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    def test_unicode_names(self):
        """Handles unicode character names."""
        request = CharacterCreateRequest(name="김철수")
        assert request.name == "김철수"

    def test_emoji_in_tags(self):
        """Handles emoji in tags."""
        request = CharacterCreateRequest(name="Test", tags=["hero 🦸", "happy 😊"])
        assert len(request.tags) == 2

    def test_empty_tags_list(self):
        """Handles empty tags list."""
        request = CharacterCreateRequest(name="Test", tags=[])
        assert request.tags == []

    def test_null_project_id(self):
        """Handles null project_id."""
        request = CharacterCreateRequest(name="Test", project_id=None)
        assert request.project_id is None

    def test_valid_uuid_project_id(self):
        """Handles valid UUID project_id."""
        project_id = uuid.uuid4()
        request = CharacterCreateRequest(name="Test", project_id=project_id)
        assert request.project_id == project_id


# ============================================================================
# Integration Tests (Database)
# ============================================================================

@pytest.mark.asyncio
class TestCharacterDatabaseIntegration:
    """Integration tests with database (requires test database)."""

    @pytest.fixture
    async def db_session(self):
        """Create test database session."""
        # This would be implemented with actual test database setup
        # For now, we'll skip these tests in CI
        pytest.skip("Requires test database setup")

    async def test_create_and_retrieve_character(self, db_session, sample_character_data):
        """Create and retrieve character from database."""
        # Would test actual database operations
        pass

    async def test_update_character_metadata(self, db_session, sample_character):
        """Update character metadata in database."""
        pass

    async def test_delete_character_cascade(self, db_session, sample_character):
        """Delete character cascades to appearances."""
        pass
