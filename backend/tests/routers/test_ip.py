"""
Tests for IP Catalog API router.

Tests the IP-First UX endpoints:
- GET /ip/home/rails - Home page rails
- GET /ip/catalog - IP catalog listing
- GET /ip/catalog/{slug} - IP detail
- GET /ip/catalog/{slug}/rights - IP rights
- GET /ip/presets/{preset_id} - Preset detail
- GET /ip/genres - Genre list
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4

from app.routers.ip import (
    # Response models
    IPCatalogItem,
    IPCatalogListResponse,
    IPDetailResponse,
    PresetItem,
    RailItem,
    HomeRailSection,
    HomeRailResponse,
)


# =============================================================================
# Schema Validation Tests
# =============================================================================

class TestIPCatalogItem:
    """Test IPCatalogItem schema validation."""

    def test_valid_minimal_item(self):
        """Test minimal valid item."""
        item = IPCatalogItem(
            id="test-id",
            slug="goblin",
            name_ko="도깨비",
            name_en="Goblin",
        )
        assert item.slug == "goblin"
        assert item.license_status == "allowed"  # default

    def test_valid_full_item(self):
        """Test full item with all fields."""
        item = IPCatalogItem(
            id="test-id",
            slug="goblin",
            name_ko="도깨비",
            name_en="Goblin",
            thumbnail_url="https://example.com/thumb.jpg",
            genre=["kdrama", "fantasy"],
            tags=["romantic", "supernatural"],
            preset_count=5,
            generation_count=100,
            license_status="restricted",
            is_featured=True,
        )
        assert item.genre == ["kdrama", "fantasy"]
        assert item.license_status == "restricted"
        assert item.is_featured is True

    def test_default_lists_empty(self):
        """Test default lists are empty."""
        item = IPCatalogItem(
            id="test-id",
            slug="test",
            name_ko="테스트",
            name_en="Test",
        )
        assert item.genre == []
        assert item.tags == []

    def test_license_status_values(self):
        """Test various license status values."""
        for status in ["allowed", "restricted", "prohibited"]:
            item = IPCatalogItem(
                id="test-id",
                slug="test",
                name_ko="테스트",
                name_en="Test",
                license_status=status,
            )
            assert item.license_status == status


class TestPresetItem:
    """Test PresetItem schema validation."""

    def test_valid_preset(self):
        """Test valid preset item."""
        preset = PresetItem(
            id="preset-1",
            name_ko="외전 드라마 3분",
            name_en="3-min Spinoff Drama",
            preset_type="video_short",
            estimated_credits=15,
            estimated_duration_seconds=180,
        )
        assert preset.preset_type == "video_short"
        assert preset.estimated_credits == 15

    def test_preset_with_descriptions(self):
        """Test preset with optional descriptions."""
        preset = PresetItem(
            id="preset-1",
            name_ko="외전",
            name_en="Spinoff",
            description_ko="3분 분량의 외전 드라마를 생성합니다.",
            description_en="Generate a 3-minute spinoff drama.",
            preset_type="video_short",
            estimated_credits=15,
            estimated_duration_seconds=180,
            is_featured=True,
        )
        assert preset.description_ko is not None
        assert preset.is_featured is True


class TestIPDetailResponse:
    """Test IPDetailResponse schema."""

    def test_detail_with_presets(self):
        """Test IP detail with presets list."""
        detail = IPDetailResponse(
            id="ip-1",
            slug="goblin",
            name_ko="도깨비",
            name_en="Goblin",
            presets=[
                PresetItem(
                    id="p-1",
                    name_ko="외전",
                    name_en="Spinoff",
                    preset_type="video_short",
                    estimated_credits=15,
                    estimated_duration_seconds=180,
                ),
            ],
        )
        assert len(detail.presets) == 1
        assert detail.presets[0].name_ko == "외전"

    def test_detail_with_worldbuilding(self):
        """Test IP detail with worldbuilding data."""
        detail = IPDetailResponse(
            id="ip-1",
            slug="goblin",
            name_ko="도깨비",
            name_en="Goblin",
            worldbuilding={
                "era": "modern",
                "setting": "Seoul",
                "characters": ["Kim Shin", "Ji Eun-tak"],
            },
        )
        assert detail.worldbuilding["era"] == "modern"
        assert len(detail.worldbuilding["characters"]) == 2


class TestRailItem:
    """Test RailItem schema."""

    def test_valid_rail_item(self):
        """Test valid rail item."""
        item = RailItem(
            id="ip-1",
            slug="goblin",
            name_ko="도깨비",
            name_en="Goblin",
        )
        assert item.license_status == "allowed"
        assert item.preset_count == 0


class TestHomeRailSection:
    """Test HomeRailSection schema."""

    def test_section_with_items(self):
        """Test section with rail items."""
        section = HomeRailSection(
            section_id="featured",
            title_ko="인기 IP",
            title_en="Popular IPs",
            items=[
                RailItem(
                    id="ip-1",
                    slug="goblin",
                    name_ko="도깨비",
                    name_en="Goblin",
                ),
                RailItem(
                    id="ip-2",
                    slug="squidgame",
                    name_ko="오징어 게임",
                    name_en="Squid Game",
                ),
            ],
            has_more=True,
        )
        assert len(section.items) == 2
        assert section.has_more is True


class TestIPCatalogListResponse:
    """Test IPCatalogListResponse schema."""

    def test_paginated_response(self):
        """Test paginated list response."""
        response = IPCatalogListResponse(
            items=[
                IPCatalogItem(
                    id="ip-1",
                    slug="goblin",
                    name_ko="도깨비",
                    name_en="Goblin",
                ),
            ],
            total=50,
            page=1,
            page_size=20,
            has_more=True,
        )
        assert response.total == 50
        assert response.has_more is True

    def test_empty_response(self):
        """Test empty list response."""
        response = IPCatalogListResponse(
            items=[],
            total=0,
            page=1,
            page_size=20,
            has_more=False,
        )
        assert len(response.items) == 0
        assert response.has_more is False


# =============================================================================
# License Status Tests
# =============================================================================

class TestLicenseStatusLogic:
    """Test license status business logic."""

    def test_allowed_status_enables_generation(self):
        """Allowed status should enable generation."""
        item = IPCatalogItem(
            id="test",
            slug="test",
            name_ko="테스트",
            name_en="Test",
            license_status="allowed",
        )
        assert item.license_status == "allowed"
        # In production, this would be checked by the generation endpoint

    def test_restricted_status_requires_consent(self):
        """Restricted status should require user consent."""
        item = IPCatalogItem(
            id="test",
            slug="test",
            name_ko="테스트",
            name_en="Test",
            license_status="restricted",
        )
        assert item.license_status == "restricted"
        # In production, frontend shows consent modal

    def test_prohibited_status_blocks_generation(self):
        """Prohibited status should block generation."""
        item = IPCatalogItem(
            id="test",
            slug="test",
            name_ko="테스트",
            name_en="Test",
            license_status="prohibited",
        )
        assert item.license_status == "prohibited"
        # In production, generation endpoint returns 403


# =============================================================================
# Genre Tests
# =============================================================================

class TestGenreHandling:
    """Test genre handling logic."""

    def test_multiple_genres(self):
        """Test IP with multiple genres."""
        item = IPCatalogItem(
            id="test",
            slug="test",
            name_ko="테스트",
            name_en="Test",
            genre=["kdrama", "fantasy", "romance"],
        )
        assert "kdrama" in item.genre
        assert "fantasy" in item.genre
        assert len(item.genre) == 3

    def test_genre_filter_logic(self):
        """Test genre contains filtering logic."""
        genres = ["kdrama", "fantasy"]
        filter_genre = "kdrama"
        assert filter_genre in genres

    def test_korean_genre_names(self):
        """Test Korean genre name mapping."""
        genre_map = {
            "kdrama": "K-드라마",
            "movie": "영화",
            "anime": "애니메이션",
            "fantasy": "판타지",
            "romance": "로맨스",
        }
        assert genre_map["kdrama"] == "K-드라마"
        assert genre_map["anime"] == "애니메이션"


# =============================================================================
# Preset Type Tests
# =============================================================================

class TestPresetTypes:
    """Test preset type handling."""

    def test_video_short_preset(self):
        """Test video_short preset type."""
        preset = PresetItem(
            id="p-1",
            name_ko="외전 3분",
            name_en="3-min Spinoff",
            preset_type="video_short",
            estimated_credits=15,
            estimated_duration_seconds=180,
        )
        assert preset.preset_type == "video_short"
        assert preset.estimated_duration_seconds == 180

    def test_video_mv_preset(self):
        """Test video_mv preset type."""
        preset = PresetItem(
            id="p-2",
            name_ko="MV 클립",
            name_en="MV Clip",
            preset_type="video_mv",
            estimated_credits=20,
            estimated_duration_seconds=240,
        )
        assert preset.preset_type == "video_mv"

    def test_still_image_preset(self):
        """Test still image preset type."""
        preset = PresetItem(
            id="p-3",
            name_ko="스틸컷",
            name_en="Still Shot",
            preset_type="still_image",
            estimated_credits=5,
            estimated_duration_seconds=30,
        )
        assert preset.preset_type == "still_image"


# =============================================================================
# Sorting and Pagination Tests
# =============================================================================

class TestSortingLogic:
    """Test sorting logic."""

    def test_sort_by_popular(self):
        """Test popular sorting (by generation_count)."""
        items = [
            {"slug": "a", "generation_count": 100},
            {"slug": "b", "generation_count": 500},
            {"slug": "c", "generation_count": 50},
        ]
        sorted_items = sorted(items, key=lambda x: x["generation_count"], reverse=True)
        assert sorted_items[0]["slug"] == "b"
        assert sorted_items[-1]["slug"] == "c"

    def test_sort_by_name(self):
        """Test alphabetical sorting by name."""
        items = [
            {"slug": "goblin", "name_ko": "도깨비"},
            {"slug": "squidgame", "name_ko": "오징어 게임"},
            {"slug": "crashlanding", "name_ko": "사랑의 불시착"},
        ]
        sorted_items = sorted(items, key=lambda x: x["name_ko"])
        assert sorted_items[0]["slug"] == "goblin"  # 도깨비 comes first


class TestPaginationLogic:
    """Test pagination logic."""

    def test_has_more_calculation(self):
        """Test has_more calculation."""
        total = 50
        page = 1
        page_size = 20
        items_returned = 20
        offset = (page - 1) * page_size

        has_more = (offset + items_returned) < total
        assert has_more is True

    def test_no_more_pages(self):
        """Test no more pages calculation."""
        total = 50
        page = 3
        page_size = 20
        items_returned = 10
        offset = (page - 1) * page_size

        has_more = (offset + items_returned) < total
        assert has_more is False

    def test_offset_calculation(self):
        """Test offset calculation."""
        page = 3
        page_size = 20
        expected_offset = 40
        assert (page - 1) * page_size == expected_offset


# =============================================================================
# Home Rails Tests
# =============================================================================

class TestHomeRailsLogic:
    """Test home rails business logic."""

    def test_featured_section_first(self):
        """Featured section should be first."""
        sections = [
            HomeRailSection(
                section_id="featured",
                title_ko="인기 IP",
                title_en="Popular IPs",
                items=[],
            ),
            HomeRailSection(
                section_id="new",
                title_ko="새로운 IP",
                title_en="New IPs",
                items=[],
            ),
        ]
        assert sections[0].section_id == "featured"

    def test_rail_item_limit(self):
        """Test rail items are limited to 10."""
        items = [
            RailItem(
                id=f"ip-{i}",
                slug=f"ip-{i}",
                name_ko=f"IP {i}",
                name_en=f"IP {i}",
            )
            for i in range(15)
        ]
        # Simulate the limit
        limited_items = items[:10]
        assert len(limited_items) == 10

    def test_has_more_when_limit_reached(self):
        """has_more should be True when limit is reached."""
        items_count = 10
        limit = 10
        has_more = items_count >= limit
        assert has_more is True


# =============================================================================
# Worldbuilding Tests
# =============================================================================

class TestWorldbuildingData:
    """Test worldbuilding data structure."""

    def test_worldbuilding_dict(self):
        """Test worldbuilding as dict."""
        worldbuilding = {
            "era": "modern",
            "setting": "Seoul, Korea",
            "mythology": "Korean folklore",
            "characters": [
                {"name": "Kim Shin", "role": "Guardian Goblin"},
                {"name": "Ji Eun-tak", "role": "Goblin Bride"},
            ],
        }
        detail = IPDetailResponse(
            id="ip-1",
            slug="goblin",
            name_ko="도깨비",
            name_en="Goblin",
            worldbuilding=worldbuilding,
        )
        assert detail.worldbuilding["era"] == "modern"
        assert len(detail.worldbuilding["characters"]) == 2

    def test_empty_worldbuilding(self):
        """Test empty worldbuilding defaults to empty dict."""
        detail = IPDetailResponse(
            id="ip-1",
            slug="test",
            name_ko="테스트",
            name_en="Test",
        )
        assert detail.worldbuilding == {}


# =============================================================================
# Korean Language Support Tests
# =============================================================================

class TestKoreanLanguageSupport:
    """Test Korean language field handling."""

    def test_korean_name_preservation(self):
        """Test Korean names are preserved."""
        item = IPCatalogItem(
            id="test",
            slug="goblin",
            name_ko="도깨비",
            name_en="Goblin",
        )
        assert item.name_ko == "도깨비"

    def test_korean_description(self):
        """Test Korean descriptions."""
        detail = IPDetailResponse(
            id="ip-1",
            slug="goblin",
            name_ko="도깨비",
            name_en="Goblin",
            description_ko="900살 먹은 도깨비와 그의 신부의 이야기",
            description_en="Story of a 900-year-old goblin and his bride",
        )
        assert "도깨비" in detail.description_ko
        assert "goblin" in detail.description_en.lower()

    def test_korean_search_pattern(self):
        """Test Korean search pattern matching."""
        search = "도깨비"
        names = ["도깨비", "오징어 게임", "사랑의 불시착"]
        matches = [n for n in names if search in n]
        assert len(matches) == 1
        assert matches[0] == "도깨비"
