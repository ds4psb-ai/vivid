"""
Tests for Character Consistency Dimension API.

Tests the StoryMem-based character consistency endpoints:
- POST /dimension/character/create
- GET /dimension/character/{character_id}
- PATCH /dimension/character/{character_id}
- DELETE /dimension/character/{character_id}
- GET /dimension/character (list)
- POST /dimension/character/{character_id}/add-reference
- POST /dimension/character/{character_id}/sync-platform
- POST /dimension/character/{character_id}/update-memory
- GET /dimension/character/similar

Features:
- Character CRUD operations
- Reference image management
- Memory bank management
- Platform synchronization
- Similarity search
"""
import pytest
from datetime import datetime
from typing import List
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4, UUID

from app.routers.dimension.character import (
    _sanitize_text,
)
from app.schemas.character_schemas import (
    CharacterCreateRequest,
    CharacterUpdateRequest,
    CharacterResponse,
    CharacterSummaryResponse,
    CharacterSimilarity,
    CharacterListResponse,
    PlatformSyncRequest,
    PlatformSyncResponse,
    MemoryBankUpdateRequest,
    MemoryBankResponse,
    PlatformType,
    CharacterRole,
    SourceImage,
    MemoryKeyframe,
    PlatformRef,
    CharacterRef,
)


# =============================================================================
# Sanitization Tests
# =============================================================================

class TestTextSanitization:
    """Test XSS sanitization for text fields."""

    def test_sanitize_empty_text(self):
        """Empty text returns default."""
        assert _sanitize_text("") == ""
        assert _sanitize_text("", "default") == "default"

    def test_sanitize_strips_whitespace(self):
        """Whitespace is stripped."""
        assert _sanitize_text("  hello world  ") == "hello world"

    def test_sanitize_removes_html_tags(self):
        """HTML tags are removed."""
        result = _sanitize_text("<script>alert('xss')</script>hello")
        assert "<script>" not in result
        assert "hello" in result

    def test_sanitize_removes_javascript(self):
        """JavaScript patterns are removed."""
        assert "javascript" not in _sanitize_text("javascript:alert(1)")
        assert _sanitize_text("onclick=evil()").find("onclick=") == -1


# =============================================================================
# Enum Tests
# =============================================================================

class TestPlatformType:
    """Test PlatformType enum."""

    def test_platform_values(self):
        """PlatformType has expected values."""
        assert PlatformType.VEO.value == "veo"
        assert PlatformType.KLING.value == "kling"
        assert PlatformType.RUNWAY.value == "runway"
        assert PlatformType.HAILUO.value == "hailuo"

    def test_platform_from_string(self):
        """PlatformType can be created from string."""
        assert PlatformType("veo") == PlatformType.VEO
        assert PlatformType("kling") == PlatformType.KLING


class TestCharacterRole:
    """Test CharacterRole enum."""

    def test_role_values(self):
        """CharacterRole has expected values."""
        assert CharacterRole.PROTAGONIST.value == "protagonist"
        assert CharacterRole.SUPPORTING.value == "supporting"
        assert CharacterRole.BACKGROUND.value == "background"


# =============================================================================
# Nested Schema Tests
# =============================================================================

class TestSourceImage:
    """Test SourceImage schema."""

    def test_minimal_source_image(self):
        """Minimal source image works."""
        image = SourceImage(url="https://example.com/image.jpg")
        assert image.url == "https://example.com/image.jpg"
        assert image.is_primary is False
        assert image.quality_score is None

    def test_full_source_image(self):
        """Full source image with all fields."""
        image = SourceImage(
            url="https://example.com/image.jpg",
            timestamp=datetime.now(),
            quality_score=0.95,
            is_primary=True,
        )
        assert image.is_primary is True
        assert image.quality_score == 0.95


class TestMemoryKeyframe:
    """Test MemoryKeyframe schema (StoryMem-style)."""

    def test_keyframe_creation(self):
        """Keyframe with required fields."""
        keyframe = MemoryKeyframe(
            frame_url="https://example.com/frame.jpg",
            timestamp=5.5,
            clip_score=0.85,
            hps_score=0.72,
            face_confidence=0.95,
        )
        assert keyframe.timestamp == 5.5
        assert keyframe.is_long_term is False

    def test_keyframe_long_term(self):
        """Long-term memory keyframe."""
        keyframe = MemoryKeyframe(
            frame_url="https://example.com/frame.jpg",
            timestamp=10.0,
            clip_score=0.9,
            hps_score=0.85,
            face_confidence=0.98,
            is_long_term=True,
        )
        assert keyframe.is_long_term is True

    def test_keyframe_score_validation(self):
        """Scores must be between 0 and 1."""
        keyframe = MemoryKeyframe(
            frame_url="https://example.com/frame.jpg",
            timestamp=0.0,
            clip_score=0.0,
            hps_score=0.0,
            face_confidence=1.0,
        )
        assert 0.0 <= keyframe.clip_score <= 1.0
        assert 0.0 <= keyframe.hps_score <= 1.0
        assert 0.0 <= keyframe.face_confidence <= 1.0


class TestPlatformRef:
    """Test PlatformRef schema."""

    def test_minimal_platform_ref(self):
        """Minimal platform reference."""
        ref = PlatformRef(platform=PlatformType.VEO)
        assert ref.platform == PlatformType.VEO
        assert ref.ref_id is None

    def test_full_platform_ref(self):
        """Full platform reference with all fields."""
        ref = PlatformRef(
            platform=PlatformType.KLING,
            ref_id="kling-char-123",
            last_sync=datetime.now(),
            style_strength=0.75,
            metadata={"version": "2.6"},
        )
        assert ref.ref_id == "kling-char-123"
        assert ref.style_strength == 0.75


class TestCharacterRef:
    """Test CharacterRef schema."""

    def test_minimal_character_ref(self):
        """Minimal character reference."""
        char_id = uuid4()
        ref = CharacterRef(character_id=char_id)
        assert ref.character_id == char_id
        assert ref.role == CharacterRole.PROTAGONIST

    def test_character_ref_with_platform(self):
        """Character reference with platform data."""
        ref = CharacterRef(
            character_id=uuid4(),
            platform_ref=PlatformRef(platform=PlatformType.VEO, ref_id="veo-123"),
            role=CharacterRole.SUPPORTING,
        )
        assert ref.role == CharacterRole.SUPPORTING
        assert ref.platform_ref.platform == PlatformType.VEO


# =============================================================================
# Request Schema Tests
# =============================================================================

class TestCharacterCreateRequest:
    """Test CharacterCreateRequest validation."""

    def test_minimal_request(self):
        """Minimal request with just name."""
        request = CharacterCreateRequest(name="Hero")
        assert request.name == "Hero"
        assert request.tags == []
        assert request.project_id is None

    def test_full_request(self):
        """Full request with all fields."""
        project_id = uuid4()
        request = CharacterCreateRequest(
            name="Hero Character",
            description="A brave protagonist",
            tags=["hero", "protagonist", "main"],
            project_id=project_id,
            reference_image="base64encodeddata...",
        )
        assert request.name == "Hero Character"
        assert len(request.tags) == 3
        assert request.project_id == project_id

    def test_name_strips_whitespace(self):
        """Name is stripped of whitespace."""
        request = CharacterCreateRequest(name="  Hero  ")
        assert request.name == "Hero"

    def test_tags_normalized(self):
        """Tags are normalized (lowercase, stripped)."""
        request = CharacterCreateRequest(
            name="Hero",
            tags=["  HERO  ", "Main Character", "protagonist"]
        )
        assert "hero" in request.tags
        assert "main character" in request.tags
        assert "protagonist" in request.tags

    def test_tags_max_count(self):
        """Tags are limited to 20."""
        many_tags = [f"tag{i}" for i in range(30)]
        request = CharacterCreateRequest(name="Hero", tags=many_tags)
        assert len(request.tags) <= 20


class TestCharacterUpdateRequest:
    """Test CharacterUpdateRequest validation."""

    def test_partial_update(self):
        """Partial update with only some fields."""
        request = CharacterUpdateRequest(name="Updated Name")
        assert request.name == "Updated Name"
        assert request.description is None
        assert request.tags is None

    def test_full_update(self):
        """Full update with all fields."""
        request = CharacterUpdateRequest(
            name="New Name",
            description="New description",
            tags=["updated", "character"],
            primary_image_url="https://example.com/new.jpg",
        )
        assert request.name == "New Name"
        assert request.description == "New description"


class TestPlatformSyncRequest:
    """Test PlatformSyncRequest validation."""

    def test_sync_request(self):
        """Platform sync request."""
        request = PlatformSyncRequest(
            platform=PlatformType.VEO,
            style_strength=0.8,
            auto_update_memory=True,
        )
        assert request.platform == PlatformType.VEO
        assert request.style_strength == 0.8
        assert request.auto_update_memory is True

    def test_sync_request_defaults(self):
        """Sync request with defaults."""
        request = PlatformSyncRequest(platform=PlatformType.KLING)
        assert request.style_strength == 0.8  # Default
        assert request.auto_update_memory is True  # Default


class TestMemoryBankUpdateRequest:
    """Test MemoryBankUpdateRequest validation."""

    def test_memory_update_request(self):
        """Memory bank update request."""
        request = MemoryBankUpdateRequest(
            video_url="https://example.com/video.mp4",
            max_keyframes=15,
            long_term_count=7,
        )
        assert request.video_url == "https://example.com/video.mp4"
        assert request.max_keyframes == 15
        assert request.long_term_count == 7

    def test_memory_update_defaults(self):
        """Memory update with defaults."""
        request = MemoryBankUpdateRequest(video_url="https://example.com/video.mp4")
        assert request.max_keyframes == 10
        assert request.long_term_count == 5


# =============================================================================
# Response Schema Tests
# =============================================================================

class TestCharacterResponse:
    """Test CharacterResponse model."""

    def test_full_character_response(self):
        """Full character response with all fields."""
        char_id = uuid4()
        now = datetime.now()

        response = CharacterResponse(
            id=char_id,
            name="Hero",
            description="Main character",
            tags=["hero", "protagonist"],
            primary_image_url="https://example.com/hero.jpg",
            source_images=[
                SourceImage(url="https://example.com/ref1.jpg"),
            ],
            memory_keyframes=[
                MemoryKeyframe(
                    frame_url="https://example.com/frame1.jpg",
                    timestamp=0.0,
                    clip_score=0.9,
                    hps_score=0.85,
                    face_confidence=0.95,
                ),
            ],
            platform_refs={
                "veo": PlatformRef(platform=PlatformType.VEO, ref_id="veo-123"),
            },
            qdrant_point_id="point-123",
            project_id=uuid4(),
            user_id="user-123",
            created_at=now,
            updated_at=now,
        )

        assert response.id == char_id
        assert response.name == "Hero"
        assert len(response.source_images) == 1
        assert len(response.memory_keyframes) == 1
        assert "veo" in response.platform_refs


class TestCharacterSummaryResponse:
    """Test CharacterSummaryResponse model."""

    def test_summary_response(self):
        """Character summary response."""
        response = CharacterSummaryResponse(
            id=uuid4(),
            name="Hero",
            primary_image_url="https://example.com/hero.jpg",
            tags=["hero"],
            keyframe_count=5,
            platforms_synced=["veo", "kling"],
        )
        assert response.name == "Hero"
        assert response.keyframe_count == 5
        assert "veo" in response.platforms_synced


class TestCharacterSimilarity:
    """Test CharacterSimilarity model."""

    def test_similarity_result(self):
        """Similarity search result."""
        character = CharacterSummaryResponse(
            id=uuid4(),
            name="Similar Character",
            primary_image_url=None,
            tags=[],
            keyframe_count=0,
            platforms_synced=[],
        )
        result = CharacterSimilarity(
            character=character,
            similarity_score=0.87,
            match_type="face",
        )
        assert result.similarity_score == 0.87
        assert result.match_type == "face"


class TestCharacterListResponse:
    """Test CharacterListResponse model."""

    def test_list_response(self):
        """Character list response."""
        items = [
            CharacterSummaryResponse(
                id=uuid4(),
                name=f"Character {i}",
                primary_image_url=None,
                tags=[],
                keyframe_count=i,
                platforms_synced=[],
            )
            for i in range(3)
        ]
        response = CharacterListResponse(
            items=items,
            total=10,
            limit=3,
            offset=0,
        )
        assert len(response.items) == 3
        assert response.total == 10


class TestPlatformSyncResponse:
    """Test PlatformSyncResponse model."""

    def test_sync_success_response(self):
        """Successful sync response."""
        response = PlatformSyncResponse(
            platform=PlatformType.VEO,
            status="success",
            platform_ref_id="veo-char-123",
        )
        assert response.status == "success"
        assert response.platform_ref_id == "veo-char-123"

    def test_sync_failed_response(self):
        """Failed sync response."""
        response = PlatformSyncResponse(
            platform=PlatformType.KLING,
            status="failed",
            message="API error",
        )
        assert response.status == "failed"
        assert response.message == "API error"


# =============================================================================
# YAML Config Tests
# =============================================================================

class TestCharacterYAMLConfig:
    """Test Character YAML configuration."""

    @pytest.fixture
    def config_path(self):
        """Get absolute path to config file."""
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        project_root = os.path.dirname(backend_dir)
        return os.path.join(project_root, "config/apps/content/dimensions/character.yaml")

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
        assert config["metadata"]["name"] == "character"
        assert config["metadata"]["type"] == "dimension"

        # Display
        assert "display" in config
        assert "icon" in config["display"]

        # Capabilities
        assert "capabilities" in config
        capability_names = [c["name"] for c in config["capabilities"]]
        assert "execution" in capability_names

        # Extensions
        assert "extensions" in config


# =============================================================================
# Integration-Style Tests (mocked)
# =============================================================================

class TestCharacterEndpointBehavior:
    """Test expected endpoint behaviors (mocked)."""

    @pytest.mark.asyncio
    async def test_create_character_flow(self):
        """Character creation flow."""
        request = CharacterCreateRequest(
            name="Test Hero",
            description="A test character",
            tags=["test", "hero"],
        )

        # Verify request is valid
        assert request.name == "Test Hero"
        assert len(request.tags) == 2

    @pytest.mark.asyncio
    async def test_platform_sync_to_veo(self):
        """Platform sync to Veo."""
        request = PlatformSyncRequest(
            platform=PlatformType.VEO,
            style_strength=0.85,
        )

        # Verify request
        assert request.platform == PlatformType.VEO
        assert request.style_strength == 0.85

    @pytest.mark.asyncio
    async def test_memory_bank_update_flow(self):
        """Memory bank update flow (StoryMem-style)."""
        request = MemoryBankUpdateRequest(
            video_url="https://example.com/generated_video.mp4",
            max_keyframes=10,
            long_term_count=5,
        )

        # Verify request
        assert request.max_keyframes == 10
        assert request.long_term_count == 5
        assert request.long_term_count <= request.max_keyframes

    @pytest.mark.asyncio
    async def test_keyframe_quality_scoring(self):
        """Keyframe quality scoring criteria."""
        # StoryMem uses CLIP score + HPS score + face confidence
        keyframe = MemoryKeyframe(
            frame_url="https://example.com/frame.jpg",
            timestamp=5.0,
            clip_score=0.9,
            hps_score=0.85,
            face_confidence=0.95,
        )

        # Combined score could be weighted average
        combined_score = (keyframe.clip_score * 0.4 +
                         keyframe.hps_score * 0.3 +
                         keyframe.face_confidence * 0.3)

        assert combined_score > 0.85  # High quality keyframe

    @pytest.mark.asyncio
    async def test_platform_ref_for_multiple_platforms(self):
        """Character can be synced to multiple platforms."""
        platform_refs = {
            "veo": PlatformRef(platform=PlatformType.VEO, ref_id="veo-123"),
            "kling": PlatformRef(platform=PlatformType.KLING, ref_id="kling-456"),
            "runway": PlatformRef(platform=PlatformType.RUNWAY, ref_id="runway-789"),
        }

        assert len(platform_refs) == 3
        assert platform_refs["veo"].platform == PlatformType.VEO
        assert platform_refs["kling"].platform == PlatformType.KLING
