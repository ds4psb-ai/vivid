"""Tests for Style Presets CRUD API (4D Reference Decoder Style Library).

Comprehensive test suite (30+ tests) covering:
- Schema validation (create, update, search params)
- Service layer functions
- Router endpoint integration
- Evidence refs format (List[str])
- Access control (ownership, public visibility)
- Error handling

References:
- docs/research/02_REFERENCE_DECODER_RESEARCH.md
- Expert Workflow: "스타일 프롬프트라고 따로 둬요"
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4, UUID

from pydantic import ValidationError


# Skip tests if dependencies unavailable
try:
    from app.schemas.style_preset_schemas import (
        StylePresetCreateRequest,
        StylePresetUpdateRequest,
        StylePresetSearchParams,
        StylePresetResponse,
        StylePresetListResponse,
        StylePresetApplyResponse,
        StylePresetDiscoverResponse,
    )
    from app.services.style_preset_service import (
        StylePresetNotFoundError,
        StylePresetAccessDeniedError,
        StylePresetError,
    )
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    IMPORT_ERROR = str(e)


pytestmark = pytest.mark.skipif(
    not DEPS_AVAILABLE,
    reason=f"Dependencies not available: {IMPORT_ERROR if not DEPS_AVAILABLE else ''}"
)


# ============================================================================
# Test Data Fixtures
# ============================================================================


SAMPLE_STYLE_DATA = {
    "style_tags": ["cinematic", "moody", "noir"],
    "style_prompt": "Cinematic noir style with dramatic lighting and high contrast...",
    "color_palette": ["#1A1A2E", "#16213E", "#0F3460"],
    "lighting": "dramatic",
    "composition": "rule-of-thirds",
    "mood": "mysterious",
    "camera_angle": "low-angle",
    "reference_artists": ["Roger Deakins", "Gordon Willis"],
    "confidence": 0.85,
}


def create_mock_preset(
    preset_id: UUID = None,
    user_id: str = "user-123",
    name: str = "Cinematic Noir",
    is_public: bool = False,
    usage_count: int = 0,
):
    """Create a mock StylePreset model."""
    mock = MagicMock()
    mock.id = preset_id or uuid4()
    mock.user_id = user_id
    mock.name = name
    mock.description = "A dramatic noir style"
    mock.tags = ["noir", "cinematic"]
    mock.style_data = SAMPLE_STYLE_DATA.copy()
    mock.color_palette = SAMPLE_STYLE_DATA["color_palette"]
    mock.lighting = "dramatic"
    mock.mood = "mysterious"
    mock.thumbnail_url = None
    mock.source_reference_id = None
    mock.is_public = is_public
    mock.usage_count = usage_count
    mock.qdrant_point_id = None
    mock.created_at = datetime.utcnow()
    mock.updated_at = None
    return mock


# ============================================================================
# StylePresetCreateRequest Schema Tests
# ============================================================================


class TestStylePresetCreateRequest:
    """Test StylePresetCreateRequest schema validation."""

    def test_valid_minimal_request(self):
        """Test valid request with minimal fields."""
        request = StylePresetCreateRequest(
            name="My Style",
            style_data=SAMPLE_STYLE_DATA,
        )
        assert request.name == "My Style"
        assert request.style_data == SAMPLE_STYLE_DATA
        assert request.tags == []
        assert request.is_public is False

    def test_valid_full_request(self):
        """Test valid request with all fields."""
        request = StylePresetCreateRequest(
            name="Cinematic Noir",
            description="Dark, moody style inspired by film noir",
            tags=["noir", "cinematic", "dramatic"],
            style_data=SAMPLE_STYLE_DATA,
            color_palette=["#1A1A2E", "#16213E"],
            lighting="dramatic",
            mood="mysterious",
            is_public=True,
        )
        assert request.name == "Cinematic Noir"
        assert len(request.tags) == 3
        assert request.is_public is True

    def test_tags_normalized_lowercase(self):
        """Test tags are normalized to lowercase."""
        request = StylePresetCreateRequest(
            name="Test",
            style_data={},
            tags=["CINEMATIC", "Noir", "DRAMATIC"],
        )
        assert request.tags == ["cinematic", "noir", "dramatic"]

    def test_tags_deduplicated(self):
        """Test duplicate tags are removed."""
        request = StylePresetCreateRequest(
            name="Test",
            style_data={},
            tags=["noir", "NOIR", "Noir", "cinematic"],
        )
        assert request.tags == ["noir", "cinematic"]

    def test_tags_limited_to_20(self):
        """Test tags are limited to 20."""
        many_tags = [f"tag{i}" for i in range(30)]
        request = StylePresetCreateRequest(
            name="Test",
            style_data={},
            tags=many_tags,
        )
        assert len(request.tags) == 20

    def test_color_palette_validated_hex(self):
        """Test color palette validation for hex format."""
        request = StylePresetCreateRequest(
            name="Test",
            style_data={},
            color_palette=["#FF5733", "33FF57", "#invalid", "#3357FF"],
        )
        # Invalid colors are filtered out
        assert "#FF5733" in request.color_palette
        assert "#33FF57" in request.color_palette
        assert "#3357FF" in request.color_palette

    def test_color_palette_limited_to_10(self):
        """Test color palette is limited to 10."""
        many_colors = [f"#{i:02d}{i:02d}{i:02d}" for i in range(15)]
        request = StylePresetCreateRequest(
            name="Test",
            style_data={},
            color_palette=many_colors,
        )
        assert len(request.color_palette) <= 10

    def test_name_required(self):
        """Test name is required."""
        with pytest.raises(ValidationError):
            StylePresetCreateRequest(style_data={})

    def test_style_data_required(self):
        """Test style_data is required."""
        with pytest.raises(ValidationError):
            StylePresetCreateRequest(name="Test")

    def test_name_min_length(self):
        """Test name minimum length."""
        with pytest.raises(ValidationError):
            StylePresetCreateRequest(name="", style_data={})

    def test_name_max_length(self):
        """Test name maximum length."""
        with pytest.raises(ValidationError):
            StylePresetCreateRequest(name="x" * 201, style_data={})


# ============================================================================
# StylePresetUpdateRequest Schema Tests
# ============================================================================


class TestStylePresetUpdateRequest:
    """Test StylePresetUpdateRequest schema validation."""

    def test_all_fields_optional(self):
        """Test all fields are optional."""
        request = StylePresetUpdateRequest()
        assert request.name is None
        assert request.description is None
        assert request.tags is None
        assert request.is_public is None

    def test_partial_update(self):
        """Test partial update with some fields."""
        request = StylePresetUpdateRequest(
            name="New Name",
            is_public=True,
        )
        assert request.name == "New Name"
        assert request.is_public is True
        assert request.tags is None

    def test_tags_normalized(self):
        """Test tags are normalized in update."""
        request = StylePresetUpdateRequest(
            tags=["ANIME", "Cinematic"],
        )
        assert request.tags == ["anime", "cinematic"]


# ============================================================================
# StylePresetSearchParams Schema Tests
# ============================================================================


class TestStylePresetSearchParams:
    """Test StylePresetSearchParams schema validation."""

    def test_default_values(self):
        """Test default search param values."""
        params = StylePresetSearchParams()
        assert params.q is None
        assert params.tags is None
        assert params.include_public is True
        assert params.sort_by == "created_at"
        assert params.sort_order == "desc"
        assert params.offset == 0
        assert params.limit == 20

    def test_all_params(self):
        """Test with all params specified."""
        params = StylePresetSearchParams(
            q="noir",
            tags=["cinematic", "moody"],
            lighting="dramatic",
            mood="mysterious",
            is_public=True,
            include_public=False,
            sort_by="usage_count",
            sort_order="asc",
            offset=10,
            limit=50,
        )
        assert params.q == "noir"
        assert params.tags == ["cinematic", "moody"]
        assert params.include_public is False

    def test_limit_max_100(self):
        """Test limit maximum is 100."""
        with pytest.raises(ValidationError):
            StylePresetSearchParams(limit=101)

    def test_offset_non_negative(self):
        """Test offset must be non-negative."""
        with pytest.raises(ValidationError):
            StylePresetSearchParams(offset=-1)


# ============================================================================
# StylePresetResponse Schema Tests
# ============================================================================


class TestStylePresetResponse:
    """Test StylePresetResponse schema validation."""

    def test_from_model_method(self):
        """Test from_model class method."""
        mock_preset = create_mock_preset(user_id="user-123")

        response = StylePresetResponse.from_model(
            mock_preset, current_user_id="user-123"
        )

        assert response.id == mock_preset.id
        assert response.name == "Cinematic Noir"
        assert response.is_owner is True
        assert response.style_prompt == SAMPLE_STYLE_DATA["style_prompt"]
        assert response.confidence == 0.85

    def test_from_model_not_owner(self):
        """Test from_model when current user is not owner."""
        mock_preset = create_mock_preset(user_id="user-123")

        response = StylePresetResponse.from_model(
            mock_preset, current_user_id="other-user"
        )

        assert response.is_owner is False

    def test_style_data_extraction(self):
        """Test style_prompt, style_tags, confidence extracted from style_data."""
        mock_preset = create_mock_preset()

        response = StylePresetResponse.from_model(mock_preset)

        assert response.style_prompt == SAMPLE_STYLE_DATA["style_prompt"]
        assert response.style_tags == SAMPLE_STYLE_DATA["style_tags"]
        assert response.confidence == 0.85


# ============================================================================
# StylePresetListResponse Schema Tests
# ============================================================================


class TestStylePresetListResponse:
    """Test StylePresetListResponse schema validation."""

    def test_default_values(self):
        """Test default response values."""
        response = StylePresetListResponse()
        assert response.items == []
        assert response.total == 0
        assert response.has_more is False

    def test_has_more_calculation(self):
        """Test has_more is properly set."""
        response = StylePresetListResponse(
            items=[],
            total=100,
            offset=0,
            limit=20,
            has_more=True,
        )
        assert response.has_more is True


# ============================================================================
# StylePresetApplyResponse Schema Tests
# ============================================================================


class TestStylePresetApplyResponse:
    """Test StylePresetApplyResponse schema validation."""

    def test_evidence_refs_format(self):
        """Test evidence_refs is List[str] format (Vivid convention)."""
        preset_id = uuid4()
        response = StylePresetApplyResponse(
            id=preset_id,
            name="Test Style",
            style_prompt="Cinematic noir...",
            evidence_refs=[f"db:style_presets:{preset_id}"],
        )

        assert isinstance(response.evidence_refs, list)
        for ref in response.evidence_refs:
            assert isinstance(ref, str)
            assert ref.startswith("db:style_presets:")

    def test_includes_usage_count(self):
        """Test includes updated usage count."""
        response = StylePresetApplyResponse(
            id=uuid4(),
            name="Test",
            style_prompt="...",
            usage_count=42,
        )
        assert response.usage_count == 42


# ============================================================================
# StylePresetDiscoverResponse Schema Tests
# ============================================================================


class TestStylePresetDiscoverResponse:
    """Test StylePresetDiscoverResponse schema validation."""

    def test_includes_categories(self):
        """Test includes tag category counts."""
        response = StylePresetDiscoverResponse(
            items=[],
            total=10,
            categories={"noir": 5, "anime": 3, "cinematic": 2},
        )
        assert response.categories["noir"] == 5
        assert len(response.categories) == 3


# ============================================================================
# Service Error Classes Tests
# ============================================================================


class TestServiceErrors:
    """Test service error classes."""

    def test_not_found_error(self):
        """Test StylePresetNotFoundError."""
        error = StylePresetNotFoundError("Preset not found")
        assert str(error) == "Preset not found"
        assert isinstance(error, StylePresetError)

    def test_access_denied_error(self):
        """Test StylePresetAccessDeniedError."""
        error = StylePresetAccessDeniedError("Access denied")
        assert str(error) == "Access denied"
        assert isinstance(error, StylePresetError)


# ============================================================================
# Service Function Tests (with mocking)
# ============================================================================


class TestCreatePresetService:
    """Test create_preset service function."""

    @pytest.mark.asyncio
    async def test_create_preset_success(self):
        """Test successful preset creation."""
        from app.services import style_preset_service

        mock_db = AsyncMock()
        request = StylePresetCreateRequest(
            name="Test Style",
            style_data=SAMPLE_STYLE_DATA,
            tags=["noir", "cinematic"],
        )

        # Mock the StylePreset model
        with patch.object(style_preset_service, "StylePreset") as MockPreset:
            mock_preset = create_mock_preset(name="Test Style")
            MockPreset.return_value = mock_preset

            result = await style_preset_service.create_preset(
                mock_db, "user-123", request
            )

            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()


class TestApplyPresetService:
    """Test apply_preset service function."""

    @pytest.mark.asyncio
    async def test_apply_returns_evidence_refs(self):
        """Test apply returns proper evidence_refs."""
        from app.services import style_preset_service

        mock_db = AsyncMock()
        preset_id = uuid4()
        mock_preset = create_mock_preset(preset_id=preset_id, user_id="user-123")

        with patch.object(
            style_preset_service, "get_preset", return_value=mock_preset
        ) as mock_get:
            with patch.object(
                style_preset_service, "increment_usage", return_value=1
            ):
                result = await style_preset_service.apply_preset(
                    mock_db, preset_id, "user-123"
                )

                assert isinstance(result, StylePresetApplyResponse)
                assert f"db:style_presets:{preset_id}" in result.evidence_refs


# ============================================================================
# Router Endpoint Tests (with mocking)
# ============================================================================


class TestCreatePresetEndpoint:
    """Test POST /style-presets endpoint."""

    @pytest.mark.asyncio
    async def test_create_returns_201(self):
        """Test create endpoint returns 201 on success."""
        from app.routers.style_presets import create_style_preset
        from app.services import style_preset_service

        mock_db = AsyncMock()
        mock_user = {"id": "user-123", "is_admin": False}
        request = StylePresetCreateRequest(
            name="Test Style",
            style_data=SAMPLE_STYLE_DATA,
        )
        mock_preset = create_mock_preset(user_id="user-123")

        with patch.object(
            style_preset_service, "create_preset", return_value=mock_preset
        ):
            result = await create_style_preset(request, mock_db, mock_user)
            assert result.name == "Cinematic Noir"


class TestListPresetsEndpoint:
    """Test GET /style-presets endpoint."""

    @pytest.mark.asyncio
    async def test_list_returns_paginated(self):
        """Test list endpoint returns paginated response."""
        from app.routers.style_presets import list_style_presets
        from app.services import style_preset_service

        mock_db = AsyncMock()
        mock_user = {"id": "user-123", "is_admin": False}
        mock_presets = [create_mock_preset() for _ in range(3)]

        with patch.object(
            style_preset_service, "list_presets", return_value=(mock_presets, 3)
        ):
            # Pass all Query parameters explicitly (FastAPI Query defaults)
            result = await list_style_presets(
                q=None,
                tags=None,  # None instead of Query object
                lighting=None,
                mood=None,
                is_public=None,
                include_public=True,
                sort_by="created_at",
                sort_order="desc",
                offset=0,
                limit=20,
                db=mock_db,
                current_user=mock_user,
            )

            assert result.total == 3
            assert len(result.items) == 3


class TestDeletePresetEndpoint:
    """Test DELETE /style-presets/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_owner_success(self):
        """Test owner can delete their preset."""
        from app.routers.style_presets import delete_style_preset
        from app.services import style_preset_service

        mock_db = AsyncMock()
        mock_user = {"id": "user-123", "is_admin": False}
        preset_id = uuid4()

        with patch.object(
            style_preset_service, "delete_preset", return_value=True
        ):
            result = await delete_style_preset(preset_id, mock_db, mock_user)
            assert result is None  # 204 No Content

    @pytest.mark.asyncio
    async def test_delete_non_owner_forbidden(self):
        """Test non-owner cannot delete preset."""
        from app.routers.style_presets import delete_style_preset
        from app.services import style_preset_service
        from fastapi import HTTPException

        mock_db = AsyncMock()
        mock_user = {"id": "other-user", "is_admin": False}
        preset_id = uuid4()

        with patch.object(
            style_preset_service,
            "delete_preset",
            side_effect=StylePresetAccessDeniedError("Access denied"),
        ):
            with pytest.raises(HTTPException) as exc:
                await delete_style_preset(preset_id, mock_db, mock_user)
            assert exc.value.status_code == 403


class TestApplyPresetEndpoint:
    """Test POST /style-presets/{id}/apply endpoint."""

    @pytest.mark.asyncio
    async def test_apply_increments_usage(self):
        """Test apply endpoint increments usage count."""
        from app.routers.style_presets import apply_style_preset
        from app.services import style_preset_service

        mock_db = AsyncMock()
        mock_user = {"id": "user-123", "is_admin": False}
        preset_id = uuid4()

        mock_response = StylePresetApplyResponse(
            id=preset_id,
            name="Test",
            style_prompt="Cinematic...",
            usage_count=5,
            evidence_refs=[f"db:style_presets:{preset_id}"],
        )

        with patch.object(
            style_preset_service, "apply_preset", return_value=mock_response
        ):
            result = await apply_style_preset(preset_id, mock_db, mock_user)
            assert result.usage_count == 5
            assert len(result.evidence_refs) == 1


class TestDiscoverEndpoint:
    """Test GET /style-presets/discover endpoint."""

    @pytest.mark.asyncio
    async def test_discover_no_auth_required(self):
        """Test discover endpoint does not require authentication."""
        from app.routers.style_presets import discover_public_presets
        from app.services import style_preset_service

        mock_db = AsyncMock()

        mock_response = StylePresetDiscoverResponse(
            items=[],
            total=0,
            categories={},
        )

        with patch.object(
            style_preset_service, "discover_public", return_value=mock_response
        ):
            result = await discover_public_presets(db=mock_db)
            assert result.total == 0


# ============================================================================
# Access Control Tests
# ============================================================================


class TestAccessControl:
    """Test access control for style presets."""

    @pytest.mark.asyncio
    async def test_owner_can_access_private(self):
        """Test owner can access their private preset."""
        from app.services import style_preset_service

        mock_db = AsyncMock()
        preset_id = uuid4()
        mock_preset = create_mock_preset(
            preset_id=preset_id,
            user_id="user-123",
            is_public=False,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_preset
        mock_db.execute.return_value = mock_result

        result = await style_preset_service.get_preset(
            mock_db, preset_id, user_id="user-123", check_access=True
        )

        assert result.id == preset_id

    @pytest.mark.asyncio
    async def test_non_owner_cannot_access_private(self):
        """Test non-owner cannot access private preset."""
        from app.services import style_preset_service

        mock_db = AsyncMock()
        preset_id = uuid4()
        mock_preset = create_mock_preset(
            preset_id=preset_id,
            user_id="owner-123",
            is_public=False,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_preset
        mock_db.execute.return_value = mock_result

        with pytest.raises(StylePresetAccessDeniedError):
            await style_preset_service.get_preset(
                mock_db, preset_id, user_id="other-user", check_access=True
            )

    @pytest.mark.asyncio
    async def test_non_owner_can_access_public(self):
        """Test non-owner can access public preset."""
        from app.services import style_preset_service

        mock_db = AsyncMock()
        preset_id = uuid4()
        mock_preset = create_mock_preset(
            preset_id=preset_id,
            user_id="owner-123",
            is_public=True,  # Public preset
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_preset
        mock_db.execute.return_value = mock_result

        result = await style_preset_service.get_preset(
            mock_db, preset_id, user_id="other-user", check_access=True
        )

        assert result.id == preset_id


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_style_data(self):
        """Test preset with empty style_data."""
        request = StylePresetCreateRequest(
            name="Empty Style",
            style_data={},
        )
        assert request.style_data == {}

    def test_empty_tags_list(self):
        """Test preset with empty tags."""
        request = StylePresetCreateRequest(
            name="No Tags",
            style_data={},
            tags=[],
        )
        assert request.tags == []

    def test_whitespace_tags_filtered(self):
        """Test whitespace-only tags are filtered."""
        request = StylePresetCreateRequest(
            name="Test",
            style_data={},
            tags=["valid", "   ", "", "another"],
        )
        assert "valid" in request.tags
        assert "another" in request.tags
        assert "" not in request.tags

    def test_response_handles_none_style_data(self):
        """Test response handles None style_data gracefully."""
        mock_preset = create_mock_preset()
        mock_preset.style_data = None

        response = StylePresetResponse.from_model(mock_preset)
        assert response.style_prompt == ""
        assert response.style_tags == []
        assert response.confidence == 0.0
