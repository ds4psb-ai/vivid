"""Tests for Homepage API endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_ip import IPCatalog
from app.models_humancloud import CreatorProfile
from app.models_singularity import BlackholeTemplate


@pytest.mark.asyncio
async def test_get_featured_ip_default(async_client: AsyncClient):
    """Test featured IP endpoint returns default when DB is empty."""
    response = await async_client.get("/api/v1/homepage/featured")
    assert response.status_code == 200
    data = response.json()

    assert data["slug"] == "neon-horizon"
    assert data["title"] == "NEON"
    assert data["title_accent"] == "HORIZON"
    assert "rating" in data
    assert "remix_count" in data
    assert "character" in data


@pytest.mark.asyncio
async def test_get_homepage_characters_default(async_client: AsyncClient):
    """Test characters endpoint returns defaults when DB is empty."""
    response = await async_client.get("/api/v1/homepage/characters")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 4  # Default limit

    # Check structure
    for char in data:
        assert "id" in char
        assert "name" in char
        assert "image_url" in char
        assert "chat_count" in char
        assert "quote" in char
        assert "creator" in char


@pytest.mark.asyncio
async def test_get_homepage_characters_with_limit(async_client: AsyncClient):
    """Test characters endpoint respects limit parameter."""
    response = await async_client.get("/api/v1/homepage/characters?limit=2")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_homepage_cinema_default(async_client: AsyncClient):
    """Test cinema endpoint returns defaults when DB is empty."""
    response = await async_client.get("/api/v1/homepage/cinema")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 3  # Default limit

    # Check structure
    for card in data:
        assert "id" in card
        assert "title" in card
        assert "description" in card
        assert "thumbnail_url" in card
        assert "duration" in card
        assert "category" in card
        assert "category_color" in card
        assert "creator" in card
        assert "views" in card
        assert "like_percent" in card


@pytest.mark.asyncio
async def test_get_homepage_creators_default(async_client: AsyncClient):
    """Test creators endpoint returns defaults when DB is empty."""
    response = await async_client.get("/api/v1/homepage/creators")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 3  # Default limit

    # Check structure
    for creator in data:
        assert "id" in creator
        assert "initial" in creator
        assert "name" in creator
        assert "specialty" in creator
        assert "specialty_color" in creator
        assert "rating" in creator
        assert "description" in creator


@pytest.mark.asyncio
async def test_get_homepage_variations_popular(async_client: AsyncClient):
    """Test variations endpoint with popular sort."""
    response = await async_client.get("/api/v1/homepage/variations?sort=popular")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 5  # Default variations count

    # Check structure
    for card in data:
        assert "id" in card
        assert "name" in card
        assert "description" in card
        assert "thumbnail_url" in card
        assert "category" in card
        assert "href" in card


@pytest.mark.asyncio
async def test_get_homepage_variations_new(async_client: AsyncClient):
    """Test variations endpoint with new sort."""
    response = await async_client.get("/api/v1/homepage/variations?sort=new")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # New sort reverses order
    assert data[0]["id"] == "3d-audio"


@pytest.mark.asyncio
async def test_get_homepage_variations_invalid_sort(async_client: AsyncClient):
    """Test variations endpoint rejects invalid sort parameter."""
    response = await async_client.get("/api/v1/homepage/variations?sort=invalid")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_characters_default(async_client: AsyncClient):
    """Test character list endpoint returns defaults when DB is empty."""
    response = await async_client.get("/api/v1/homepage/characters/list")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "has_more" in data

    assert isinstance(data["items"], list)
    assert data["page"] == 1
    assert data["page_size"] == 20


@pytest.mark.asyncio
async def test_list_characters_with_search(async_client: AsyncClient):
    """Test character list with search filter."""
    response = await async_client.get("/api/v1/homepage/characters/list?search=akari")
    assert response.status_code == 200
    data = response.json()

    # Should find Akari in defaults
    assert len(data["items"]) >= 1
    assert any("akari" in item["name"].lower() for item in data["items"])


@pytest.mark.asyncio
async def test_list_characters_with_category(async_client: AsyncClient):
    """Test character list with category filter."""
    response = await async_client.get("/api/v1/homepage/characters/list?category=Cyberpunk")
    assert response.status_code == 200
    data = response.json()

    # Should filter by category
    for item in data["items"]:
        if item.get("category"):
            assert item["category"] == "Cyberpunk"


@pytest.mark.asyncio
async def test_list_characters_pagination(async_client: AsyncClient):
    """Test character list pagination."""
    response = await async_client.get("/api/v1/homepage/characters/list?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) <= 2
    assert data["page"] == 1
    assert data["page_size"] == 2


@pytest.mark.asyncio
async def test_list_characters_all_category(async_client: AsyncClient):
    """Test character list with 'All' category returns all."""
    response = await async_client.get("/api/v1/homepage/characters/list?category=All")
    assert response.status_code == 200
    data = response.json()

    # Should return all characters
    assert len(data["items"]) >= 1


# =============================================================================
# Tests with DB data (using fixtures)
# These tests require a real PostgreSQL database with proper JSONB support.
# Skip for now - can be enabled when running against a real test database.
# =============================================================================

@pytest.mark.skip(reason="Requires PostgreSQL with JSONB support")
@pytest.mark.asyncio
async def test_get_featured_ip_from_db(async_client: AsyncClient, db_session: AsyncSession):
    """Test featured IP endpoint with actual DB data."""
    # Create a featured IP
    ip = IPCatalog(
        slug="test-ip",
        name_ko="테스트 IP",
        name_en="Test IP Hero",
        description_ko="테스트 설명입니다.",
        banner_url="https://example.com/banner.jpg",
        thumbnail_url="https://example.com/thumb.jpg",
        is_active=True,
        is_featured=True,
        featured_order=1,
        chat_enabled=True,
        persona_prompt="테스트 페르소나",
        generation_count=1500,
        tags=["테스트", "2026"],
        genre=["Drama"],
    )
    db_session.add(ip)
    await db_session.commit()

    response = await async_client.get("/api/v1/homepage/featured")
    assert response.status_code == 200
    data = response.json()

    assert data["slug"] == "test-ip"
    assert data["title"] == "TEST"
    assert data["title_accent"] == "IP HERO"
    assert data["description"] == "테스트 설명입니다."
    assert data["remix_count"] == "1.5k"
    assert data["character"] is not None
    assert data["character"]["name"] == "테스트 IP"


@pytest.mark.skip(reason="Requires PostgreSQL with JSONB support")
@pytest.mark.asyncio
async def test_get_homepage_characters_from_db(async_client: AsyncClient, db_session: AsyncSession):
    """Test characters endpoint with actual DB data."""
    # Create chat-enabled IPs
    for i in range(3):
        ip = IPCatalog(
            slug=f"char-{i}",
            name_ko=f"캐릭터 {i}",
            name_en=f"Character {i}",
            description_ko=f"캐릭터 {i} 설명",
            thumbnail_url=f"https://example.com/char{i}.jpg",
            is_active=True,
            chat_enabled=True,
            chat_session_count=100 * (3 - i),  # Descending order
            genre=["Fantasy"],
        )
        db_session.add(ip)
    await db_session.commit()

    response = await async_client.get("/api/v1/homepage/characters?limit=3")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 3
    # Check sorted by chat_session_count descending
    assert data[0]["id"] == "char-0"
    assert data[0]["chat_count"] == "300"


@pytest.mark.skip(reason="Requires PostgreSQL with JSONB support")
@pytest.mark.asyncio
async def test_get_homepage_creators_from_db(async_client: AsyncClient, db_session: AsyncSession):
    """Test creators endpoint with actual DB data."""
    # Create verified creators
    for i in range(2):
        creator = CreatorProfile(
            user_id=f"user-{i}",
            display_name=f"크리에이터 {i}",
            bio=f"크리에이터 {i} 소개",
            is_available=True,
            is_verified=True,
            avg_rating=4.5 + (0.1 * i),
            categories=["video_creative"],
            completed_count=10 + i,
        )
        db_session.add(creator)
    await db_session.commit()

    response = await async_client.get("/api/v1/homepage/creators?limit=2")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    # Check sorted by rating descending
    assert data[0]["rating"] == 4.6


@pytest.mark.skip(reason="Requires PostgreSQL with JSONB support")
@pytest.mark.asyncio
async def test_list_characters_search_from_db(async_client: AsyncClient, db_session: AsyncSession):
    """Test character list search with DB data."""
    # Create IPs with different names
    ip1 = IPCatalog(
        slug="dragon-knight",
        name_ko="드래곤 나이트",
        name_en="Dragon Knight",
        description_ko="용을 타고 다니는 기사",
        is_active=True,
        chat_enabled=True,
        chat_session_count=100,
    )
    ip2 = IPCatalog(
        slug="water-mage",
        name_ko="워터 메이지",
        name_en="Water Mage",
        description_ko="물의 마법사",
        is_active=True,
        chat_enabled=True,
        chat_session_count=50,
    )
    db_session.add_all([ip1, ip2])
    await db_session.commit()

    # Search for dragon
    response = await async_client.get("/api/v1/homepage/characters/list?search=드래곤")
    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == "dragon-knight"


@pytest.mark.skip(reason="Requires PostgreSQL with JSONB support")
@pytest.mark.asyncio
async def test_list_characters_category_filter_from_db(async_client: AsyncClient, db_session: AsyncSession):
    """Test character list category filter with DB data."""
    # Create IPs with different genres
    ip1 = IPCatalog(
        slug="fantasy-hero",
        name_ko="판타지 히어로",
        name_en="Fantasy Hero",
        is_active=True,
        chat_enabled=True,
        genre=["Fantasy"],
        chat_session_count=100,
    )
    ip2 = IPCatalog(
        slug="scifi-robot",
        name_ko="SF 로봇",
        name_en="SciFi Robot",
        is_active=True,
        chat_enabled=True,
        genre=["Sci-Fi"],
        chat_session_count=50,
    )
    db_session.add_all([ip1, ip2])
    await db_session.commit()

    # Filter by Fantasy
    response = await async_client.get("/api/v1/homepage/characters/list?category=Fantasy")
    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == "fantasy-hero"
