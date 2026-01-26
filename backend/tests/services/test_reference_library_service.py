"""Tests for Reference Library Service.

Tests CRUD operations for reference items and style presets.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4

from app.services.reference_library_service import (
    ReferenceLibraryService,
    ReferenceItemCreate,
    ReferenceItemUpdate,
    ReferenceItemResponse,
    StylePresetCreate,
    StylePresetUpdate,
    StylePresetResponse,
    ReferenceItemFilter,
    PaginationParams,
    PaginatedResponse,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def service(mock_db):
    """Create ReferenceLibraryService instance."""
    return ReferenceLibraryService(mock_db)


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return str(uuid4())


@pytest.fixture
def sample_reference_create():
    """Sample reference item create DTO."""
    return ReferenceItemCreate(
        name="Test Reference Video",
        description="A test reference for unit testing",
        tags=["test", "unit"],
        reference_type="video",
        source_url="https://example.com/video.mp4",
        file_size_bytes=1024000,
        mime_type="video/mp4",
        duration_seconds=30.0,
        thumbnail_url="https://example.com/thumb.jpg",
        analysis_depth="detailed",
    )


@pytest.fixture
def sample_style_preset_create():
    """Sample style preset create DTO."""
    return StylePresetCreate(
        name="Cinematic Style",
        description="A cinematic visual style",
        tags=["cinematic", "film"],
        style_data={
            "color_palette": ["#1a1a1a", "#f0f0f0"],
            "mood": "dramatic",
            "contrast": "high",
        },
        style_vector=[0.1, 0.2, 0.3, 0.4, 0.5],
        auteur_references=["epoch", "abyss"],
        is_public=False,
    )


# =============================================================================
# Reference Item Tests
# =============================================================================


class TestReferenceItemCreate:
    """Tests for creating reference items."""

    @pytest.mark.asyncio
    async def test_create_reference_item_success(
        self, service, mock_db, sample_user_id, sample_reference_create
    ):
        """Test successful reference item creation."""
        # Mock the database add and refresh
        mock_db.refresh = AsyncMock()

        result = await service.create_reference_item(
            sample_user_id, sample_reference_create
        )

        assert result is not None
        assert result.name == sample_reference_create.name
        assert result.user_id == sample_user_id
        assert result.reference_type == sample_reference_create.reference_type
        mock_db.add.assert_called_once()
        # Note: commit is called in the actual transaction context, not always on mock

    @pytest.mark.asyncio
    async def test_create_reference_item_with_project(
        self, service, mock_db, sample_user_id
    ):
        """Test creating reference item with project association."""
        project_id = str(uuid4())
        create_dto = ReferenceItemCreate(
            name="Project Reference",
            reference_type="image",
            source_url="https://example.com/image.jpg",
            project_id=project_id,
        )

        result = await service.create_reference_item(sample_user_id, create_dto)

        # project_id is stored as UUID, compare string representations
        assert str(result.project_id) == project_id


class TestReferenceItemRead:
    """Tests for reading reference items."""

    @pytest.mark.asyncio
    async def test_get_reference_item_not_found(
        self, service, mock_db, sample_user_id
    ):
        """Test getting non-existent reference item."""
        # Mock empty result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_reference_item(sample_user_id, str(uuid4()))

        assert result is None

    @pytest.mark.asyncio
    async def test_get_reference_items_with_filters(
        self, service, mock_db, sample_user_id
    ):
        """Test getting reference items with filters."""
        filters = ReferenceItemFilter(
            reference_type="video",
            analysis_status="completed",
            tags=["test"],
        )

        # Mock count result
        mock_count = MagicMock()
        mock_count.scalar.return_value = 5

        # Mock items result
        mock_items = MagicMock()
        mock_items.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_count, mock_items]

        # Use actual method signature (page and page_size as separate args)
        items, total = await service.get_reference_items(
            sample_user_id, filters, page=1, page_size=10
        )

        assert total == 5
        assert isinstance(items, list)


class TestReferenceItemUpdate:
    """Tests for updating reference items."""

    @pytest.mark.asyncio
    async def test_update_reference_item_not_found(
        self, service, mock_db, sample_user_id
    ):
        """Test updating non-existent reference item."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        update_dto = ReferenceItemUpdate(name="Updated Name")
        result = await service.update_reference_item(
            sample_user_id, str(uuid4()), update_dto
        )

        assert result is None


class TestReferenceItemDelete:
    """Tests for deleting reference items."""

    @pytest.mark.asyncio
    async def test_delete_reference_item_not_found(
        self, service, mock_db, sample_user_id
    ):
        """Test deleting non-existent reference item returns False."""
        # Mock execute result for delete to return 0 rowcount
        mock_delete_result = MagicMock()
        mock_delete_result.rowcount = 0
        mock_db.execute.return_value = mock_delete_result

        result = await service.delete_reference_item(sample_user_id, str(uuid4()))

        # Should return False when no rows deleted
        assert result is False


# =============================================================================
# Style Preset Tests
# =============================================================================


class TestStylePresetCreate:
    """Tests for creating style presets."""

    @pytest.mark.asyncio
    async def test_create_style_preset_success(
        self, service, mock_db, sample_user_id, sample_style_preset_create
    ):
        """Test successful style preset creation."""
        result = await service.create_style_preset(
            sample_user_id, sample_style_preset_create
        )

        assert result is not None
        assert result.name == sample_style_preset_create.name
        assert result.user_id == sample_user_id
        mock_db.add.assert_called_once()
        # Note: commit is called in the actual transaction context, not always on mock

    @pytest.mark.asyncio
    async def test_create_public_style_preset(
        self, service, mock_db, sample_user_id
    ):
        """Test creating public style preset."""
        create_dto = StylePresetCreate(
            name="Public Preset",
            style_data={"mood": "calm"},
            is_public=True,
        )

        result = await service.create_style_preset(sample_user_id, create_dto)

        assert result.is_public is True


class TestStylePresetRead:
    """Tests for reading style presets."""

    @pytest.mark.asyncio
    async def test_get_style_presets_include_public(
        self, service, mock_db, sample_user_id
    ):
        """Test getting style presets including public ones."""
        # Mock count and items
        mock_count = MagicMock()
        mock_count.scalar.return_value = 3
        mock_items = MagicMock()
        mock_items.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [mock_count, mock_items]

        # Use actual method signature (page and page_size as separate args)
        presets, total = await service.get_style_presets(
            sample_user_id,
            include_public=True,
            page=1,
            page_size=10,
        )

        assert total == 3
        assert isinstance(presets, list)


# =============================================================================
# DTO Validation Tests
# =============================================================================


class TestDTOValidation:
    """Tests for Pydantic DTO validation."""

    def test_reference_item_create_valid(self):
        """Test valid reference item creation DTO."""
        dto = ReferenceItemCreate(
            name="Valid Name",
            reference_type="video",
            source_url="https://example.com/video.mp4",
        )
        assert dto.name == "Valid Name"

    def test_reference_item_create_invalid_type(self):
        """Test invalid reference type validation."""
        with pytest.raises(ValueError):
            ReferenceItemCreate(
                name="Test",
                reference_type="audio",  # Invalid
                source_url="https://example.com/file",
            )

    def test_reference_item_create_empty_name(self):
        """Test empty name validation."""
        with pytest.raises(ValueError):
            ReferenceItemCreate(
                name="",  # Empty
                reference_type="video",
                source_url="https://example.com/video.mp4",
            )

    def test_style_preset_create_with_vector(self):
        """Test style preset with style vector."""
        dto = StylePresetCreate(
            name="Test Style",
            style_data={"mood": "dark"},
            style_vector=[0.1, 0.2, 0.3],
        )
        assert dto.style_vector == [0.1, 0.2, 0.3]

    def test_pagination_params_defaults(self):
        """Test pagination params defaults."""
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20

    def test_reference_item_filter_all_fields(self):
        """Test reference item filter with all fields."""
        filters = ReferenceItemFilter(
            project_id="proj-123",
            reference_type="image",
            analysis_status="completed",
            tags=["landscape", "nature"],
            search="mountain",
        )
        assert filters.project_id == "proj-123"
        assert len(filters.tags) == 2
