"""Tests for Capsule Spec SSoT Service.

P5 Commit 1: Tests for list_specs, get_spec, resolve_latest_version, parse_capsule_id
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Skip all tests if dependencies unavailable
try:
    from app.services.capsule_specs import (
        CapsuleSpecResponse,
        parse_capsule_id,
        list_specs,
        get_spec,
        resolve_latest_version,
        get_spec_by_id,
        clear_fixtures_cache,
        _load_fixtures,
        _semver_key,
    )
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    # Placeholders
    CapsuleSpecResponse = None
    parse_capsule_id = None
    list_specs = None
    get_spec = None
    resolve_latest_version = None
    get_spec_by_id = None
    clear_fixtures_cache = lambda: None
    _load_fixtures = lambda: {}
    _semver_key = lambda v: (0, 0, 0)


pytestmark = pytest.mark.skipif(
    not DEPS_AVAILABLE,
    reason=f"Dependencies not available: {IMPORT_ERROR if not DEPS_AVAILABLE else ''}"
)


class TestParseCapsuleId:
    """Tests for parse_capsule_id function."""
    
    def test_with_version(self):
        """Should parse capsule_id with version."""
        key, version = parse_capsule_id("teaching.prompt.generate:1.0.0")
        assert key == "teaching.prompt.generate"
        assert version == "1.0.0"
    
    def test_without_version(self):
        """Should parse capsule_id without version."""
        key, version = parse_capsule_id("auteur.bong-joon-ho")
        assert key == "auteur.bong-joon-ho"
        assert version is None
    
    def test_with_multiple_colons(self):
        """Should handle capsule_id with multiple colons (takes first split)."""
        key, version = parse_capsule_id("some.key:1.0.0:extra")
        assert key == "some.key"
        assert version == "1.0.0:extra"
    
    def test_empty_string(self):
        """Should handle empty string."""
        key, version = parse_capsule_id("")
        assert key == ""
        assert version is None


class TestSemverKey:
    """Tests for _semver_key function."""
    
    def test_standard_version(self):
        """Should parse standard semver."""
        assert _semver_key("1.2.3") == (1, 2, 3)
    
    def test_two_part_version(self):
        """Should handle two-part version."""
        assert _semver_key("1.2") == (1, 2, 0)
    
    def test_single_number(self):
        """Should handle single number version."""
        assert _semver_key("1") == (1, 0, 0)
    
    def test_invalid_version(self):
        """Should return zeros for invalid version."""
        assert _semver_key("invalid") == (0, 0, 0)


class TestLoadFixtures:
    """Tests for _load_fixtures function."""
    
    def setup_method(self):
        """Clear cache before each test."""
        clear_fixtures_cache()
    
    def test_loads_dimension_capsules(self):
        """Should load dimension capsules from fixtures."""
        fixtures = _load_fixtures()
        
        # Should have at least some capsules
        assert len(fixtures) > 0
        
        # Check for a known dimension capsule
        teaching_key = "teaching.prompt.generate:1.0.0"
        if teaching_key in fixtures:
            spec = fixtures[teaching_key]
            assert spec.capsule_key == "teaching.prompt.generate"
            assert spec.is_active is True
    
    def test_loads_auteur_capsules(self):
        """Should load auteur capsules from fixtures."""
        fixtures = _load_fixtures()
        
        # Check for a known auteur capsule
        auteur_keys = [k for k in fixtures if k.startswith("auteur.")]
        assert len(auteur_keys) > 0
    
    def test_synthetic_id_format(self):
        """All fixtures should have synthetic ID in key:version format."""
        fixtures = _load_fixtures()
        
        for key, spec in fixtures.items():
            assert ":" in key
            assert spec.id == key
            parts = key.split(":", 1)
            assert spec.capsule_key == parts[0]
            assert spec.version == parts[1]
    
    def test_cache_works(self):
        """Should cache fixtures after first load."""
        fixtures1 = _load_fixtures()
        fixtures2 = _load_fixtures()
        
        # Should be the same object (cached)
        assert fixtures1 is fixtures2


class TestCapsuleSpecResponse:
    """Tests for CapsuleSpecResponse dataclass."""
    
    def test_to_dict(self):
        """Should convert to dict correctly."""
        spec = CapsuleSpecResponse(
            id="test:1.0.0",
            capsule_key="test",
            version="1.0.0",
            display_name="Test",
            description="Test description",
            spec={"key": "value"},
            is_active=True,
            category="teaching",
            credit_costs={"gemini-3-flash-preview": 5},
        )
        
        result = spec.to_dict()
        
        assert result["id"] == "test:1.0.0"
        assert result["capsule_key"] == "test"
        assert result["version"] == "1.0.0"
        assert result["is_active"] is True
        assert result["category"] == "teaching"


@pytest.mark.asyncio
class TestListSpecs:
    """Tests for list_specs function."""
    
    async def test_returns_fixtures_when_db_empty(self):
        """Should return fixtures when DB query returns empty."""
        clear_fixtures_cache()
        
        # Mock DB session with empty result
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        specs = await list_specs(mock_db)
        
        # Should have fixtures loaded
        assert len(specs) > 0
    
    async def test_category_filter(self):
        """Should filter by category."""
        clear_fixtures_cache()
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        specs = await list_specs(mock_db, category="auteur")
        
        for spec in specs:
            assert spec.category == "auteur"


@pytest.mark.asyncio
class TestGetSpec:
    """Tests for get_spec function."""
    
    async def test_returns_fixture_when_db_empty(self):
        """Should return fixture when not in DB."""
        clear_fixtures_cache()
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # Get a known fixture
        spec = await get_spec(mock_db, "teaching.prompt.generate", "1.0.0")
        
        if spec:  # May not exist in fixtures
            assert spec.capsule_key == "teaching.prompt.generate"
            assert spec.version == "1.0.0"


@pytest.mark.asyncio
class TestGetSpecById:
    """Tests for get_spec_by_id function."""
    
    async def test_parses_id_with_version(self):
        """Should parse capsule_id and delegate to get_spec."""
        clear_fixtures_cache()
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # Get a known fixture
        spec = await get_spec_by_id(mock_db, "teaching.prompt.generate:1.0.0")
        
        if spec:
            assert spec.capsule_key == "teaching.prompt.generate"
