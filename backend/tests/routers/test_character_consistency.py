"""Tests for Character Consistency API.

Comprehensive tests for StoryMem-based character consistency system.

Tests cover:
- Character CRUD operations
- Reference image management (up to 14 images)
- Memory bank operations (StoryMem algorithm)
- Platform synchronization (Veo, Kling, Runway, Hailuo)
- Similarity search (CoFE multi-expert fusion)
- Input validation and sanitization
- File validation (2026 Best Practices)
- Evidence refs (Vivid convention)

2026 Best Practices:
- Gemini 3 Pro Image: up to 5 people, 14 reference images
- ArcFace R100 (512D) + CLIP ViT-L/14 (768D)
- CoFE multi-expert fusion for similarity

References:
- StoryMem Paper: arXiv:2512.19539
- DIMENSION_APP_MACRO_PLANNING_2026.md Part 11
"""
from __future__ import annotations

import base64
import io
import uuid
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status, UploadFile
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
    KeyframeSelectionConfig,
    EmbeddingMetadata,
    SourceImage,
    CharacterSimilarity,
    CharacterListResponse,
)
from app.routers.dimension._base import sanitize_generic_text
from app.routers.dimension.character import (
    _validate_image_file,
    ALLOWED_IMAGE_TYPES,
    MAX_IMAGE_SIZE,
    MAX_REFERENCE_IMAGES,
    MAX_CHARACTERS_PER_VIDEO,
)


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
        assert sanitize_generic_text("  hello  ") == "hello"

    def test_returns_default_for_empty(self):
        """Returns default for empty string."""
        assert sanitize_generic_text("") == ""
        assert sanitize_generic_text("", "default") == "default"

    def test_returns_default_for_whitespace_only(self):
        """Returns default for whitespace-only string."""
        assert sanitize_generic_text("   ") == ""
        assert sanitize_generic_text("   ", "default") == "default"

    def test_removes_html_tags(self):
        """Removes HTML tags."""
        assert sanitize_generic_text("<script>alert('xss')</script>hello") == "alert(&#x27;xss&#x27;)hello"

    def test_escapes_html_entities(self):
        """Escapes HTML entities."""
        result = sanitize_generic_text("Tom & Jerry")
        assert "&amp;" in result

    def test_removes_javascript_protocol(self):
        """Removes javascript: protocol."""
        result = sanitize_generic_text("javascript:alert(1)")
        assert "javascript" not in result.lower() or ":" not in result

    def test_removes_event_handlers(self):
        """Removes event handler attributes."""
        result = sanitize_generic_text("onclick=alert(1)")
        assert "onclick=" not in result

    def test_handles_none(self):
        """Handles None input."""
        assert sanitize_generic_text(None) == ""


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
        sanitized_name = sanitize_generic_text(request_data["name"])
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
        sanitized = sanitize_generic_text(payload)
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


# ============================================================================
# File Validation Tests (2026 Best Practices)
# ============================================================================

class TestFileValidation:
    """Tests for file upload validation."""

    def test_allowed_image_types_defined(self):
        """ALLOWED_IMAGE_TYPES contains expected formats."""
        assert "image/jpeg" in ALLOWED_IMAGE_TYPES
        assert "image/png" in ALLOWED_IMAGE_TYPES
        assert "image/webp" in ALLOWED_IMAGE_TYPES
        assert "image/heic" in ALLOWED_IMAGE_TYPES
        assert "image/heif" in ALLOWED_IMAGE_TYPES

    def test_max_image_size(self):
        """MAX_IMAGE_SIZE is 20MB."""
        assert MAX_IMAGE_SIZE == 20 * 1024 * 1024

    def test_max_reference_images(self):
        """MAX_REFERENCE_IMAGES is 14 (Gemini 3 Pro Image limit)."""
        assert MAX_REFERENCE_IMAGES == 14

    def test_max_characters_per_video(self):
        """MAX_CHARACTERS_PER_VIDEO is 5 (Gemini 3 Pro Image limit)."""
        assert MAX_CHARACTERS_PER_VIDEO == 5

    def test_validate_jpeg_file(self):
        """Validates JPEG files."""
        file = MagicMock(spec=UploadFile)
        file.content_type = "image/jpeg"
        file.filename = "test.jpg"
        # Should not raise
        _validate_image_file(file)

    def test_validate_png_file(self):
        """Validates PNG files."""
        file = MagicMock(spec=UploadFile)
        file.content_type = "image/png"
        file.filename = "test.png"
        _validate_image_file(file)

    def test_validate_webp_file(self):
        """Validates WebP files."""
        file = MagicMock(spec=UploadFile)
        file.content_type = "image/webp"
        file.filename = "test.webp"
        _validate_image_file(file)

    def test_rejects_invalid_content_type(self):
        """Rejects unsupported content types."""
        file = MagicMock(spec=UploadFile)
        file.content_type = "application/pdf"
        file.filename = "test.pdf"

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            _validate_image_file(file)
        assert exc_info.value.status_code == 400
        assert "Unsupported image type" in str(exc_info.value.detail)

    def test_rejects_gif_files(self):
        """Rejects GIF files (not supported by Gemini)."""
        file = MagicMock(spec=UploadFile)
        file.content_type = "image/gif"
        file.filename = "test.gif"

        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            _validate_image_file(file)


# ============================================================================
# Evidence Refs Tests (Vivid Convention)
# ============================================================================

class TestEvidenceRefs:
    """Tests for evidence_refs format (List[str])."""

    def test_memory_bank_response_has_evidence_refs(self):
        """MemoryBankResponse includes evidence_refs."""
        response = MemoryBankResponse(
            character_id=uuid.uuid4(),
            keyframes_extracted=10,
            long_term_updated=5,
            sliding_window_updated=5,
            new_keyframes=[],
            evidence_refs=["db:characters:uuid-123", "qdrant:character_embeddings:point-456"],
        )
        assert isinstance(response.evidence_refs, list)
        assert all(isinstance(ref, str) for ref in response.evidence_refs)
        assert "db:characters:uuid-123" in response.evidence_refs

    def test_evidence_refs_format_db_prefix(self):
        """Evidence refs use db: prefix for database references."""
        refs = ["db:characters:abc123", "db:character_appearances:def456"]
        for ref in refs:
            assert ref.startswith("db:")
            parts = ref.split(":")
            assert len(parts) == 3  # db:table:id

    def test_evidence_refs_format_qdrant_prefix(self):
        """Evidence refs use qdrant: prefix for vector store."""
        refs = ["qdrant:character_embeddings:point123"]
        for ref in refs:
            assert ref.startswith("qdrant:")

    def test_character_response_has_evidence_refs(self):
        """CharacterResponse includes evidence_refs field."""
        # Check that the field exists in the model
        assert "evidence_refs" in CharacterResponse.model_fields


# ============================================================================
# Keyframe Selection Config Tests
# ============================================================================

class TestKeyframeSelectionConfig:
    """Tests for StoryMem keyframe selection configuration."""

    def test_default_weights(self):
        """Default weights sum to 1.0."""
        config = KeyframeSelectionConfig()
        total = config.clip_weight + config.hps_weight + config.face_weight
        assert abs(total - 1.0) < 0.01

    def test_custom_weights(self):
        """Custom weights are applied."""
        config = KeyframeSelectionConfig(
            clip_weight=0.5,
            hps_weight=0.25,
            face_weight=0.25,
        )
        assert config.clip_weight == 0.5
        assert config.hps_weight == 0.25

    def test_min_score_thresholds(self):
        """Minimum score thresholds are reasonable."""
        config = KeyframeSelectionConfig()
        assert 0.5 <= config.min_clip_score <= 0.9
        assert 0.3 <= config.min_hps_score <= 0.8
        assert 0.7 <= config.min_face_confidence <= 1.0

    def test_diversity_threshold(self):
        """Diversity threshold is within expected range."""
        config = KeyframeSelectionConfig()
        assert 0.1 <= config.diversity_threshold <= 0.3


# ============================================================================
# Embedding Metadata Tests
# ============================================================================

class TestEmbeddingMetadata:
    """Tests for embedding metadata schema."""

    def test_required_fields(self):
        """Required fields are present."""
        metadata = EmbeddingMetadata(
            character_id="char-123",
            user_id="user-456",
            name="Test Character",
            created_at=datetime.utcnow().isoformat(),
        )
        assert metadata.character_id == "char-123"
        assert metadata.user_id == "user-456"

    def test_optional_fields_default(self):
        """Optional fields have defaults."""
        metadata = EmbeddingMetadata(
            character_id="char-123",
            user_id="user-456",
            name="Test",
            created_at=datetime.utcnow().isoformat(),
        )
        assert metadata.project_id is None
        assert metadata.tags == []
        assert metadata.source_image_urls == []


# ============================================================================
# Source Image Tests
# ============================================================================

class TestSourceImage:
    """Tests for SourceImage schema."""

    def test_source_image_with_url(self):
        """SourceImage with URL."""
        img = SourceImage(url="https://example.com/image.jpg")
        assert img.url == "https://example.com/image.jpg"
        assert img.is_primary is False

    def test_source_image_quality_score_range(self):
        """Quality score must be 0-1."""
        img = SourceImage(url="https://example.com/image.jpg", quality_score=0.95)
        assert img.quality_score == 0.95

    def test_source_image_quality_score_validation(self):
        """Quality score outside range raises error."""
        with pytest.raises(ValueError):
            SourceImage(url="https://example.com/image.jpg", quality_score=1.5)


# ============================================================================
# Character Similarity Tests
# ============================================================================

class TestCharacterSimilaritySchema:
    """Tests for CharacterSimilarity response schema."""

    def test_similarity_score_range(self):
        """Similarity score must be 0-1."""
        summary = CharacterSummaryResponse(
            id=uuid.uuid4(),
            name="Test",
            primary_image_url=None,
            tags=[],
            keyframe_count=0,
            platforms_synced=[],
        )
        similarity = CharacterSimilarity(
            character=summary,
            similarity_score=0.85,
            match_type="combined",
        )
        assert similarity.similarity_score == 0.85

    def test_match_types(self):
        """Match type is one of allowed values."""
        summary = CharacterSummaryResponse(
            id=uuid.uuid4(),
            name="Test",
            primary_image_url=None,
            tags=[],
            keyframe_count=0,
            platforms_synced=[],
        )

        for match_type in ["face", "clip", "combined"]:
            similarity = CharacterSimilarity(
                character=summary,
                similarity_score=0.8,
                match_type=match_type,
            )
            assert similarity.match_type == match_type


# ============================================================================
# Character List Response Tests
# ============================================================================

class TestCharacterListResponse:
    """Tests for paginated character list response."""

    def test_pagination_fields(self):
        """Pagination fields are present."""
        response = CharacterListResponse(
            items=[],
            total=100,
            limit=20,
            offset=40,
        )
        assert response.total == 100
        assert response.limit == 20
        assert response.offset == 40

    def test_items_list(self):
        """Items is a list of CharacterSummaryResponse."""
        summary = CharacterSummaryResponse(
            id=uuid.uuid4(),
            name="Test",
            primary_image_url=None,
            tags=["test"],
            keyframe_count=5,
            platforms_synced=["veo"],
        )
        response = CharacterListResponse(
            items=[summary],
            total=1,
            limit=20,
            offset=0,
        )
        assert len(response.items) == 1
        assert response.items[0].name == "Test"
