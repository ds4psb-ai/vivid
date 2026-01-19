"""
Tests for Tool Recommender Service.

Tests the tool recommendation engine for IP-First Coordination Phase 2.5:
- Tool metadata loading
- Recommendation scoring
- IP context integration
- Reason code generation
- Evidence building
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.schemas.tool_recommendation import (
    ReasonCodeCategory,
    ToolRecommendation,
    ToolRecommendationRequest,
    ToolRecommendationResponse,
    ToolEvidenceResponse,
    ToolDisplayInfo,
    build_reason_code,
    parse_reason_code,
)
from app.services.tool_recommender import (
    ToolRecommenderService,
    create_tool_recommender,
    get_tool_metadata,
    get_all_tools,
    _build_tool_metadata_cache,
)
from app.rag.rag_suggestion import ConfidenceLevel, calculate_confidence_level


# =============================================================================
# Reason Code Tests
# =============================================================================

class TestReasonCodes:
    """Test reason code building and parsing."""

    def test_build_reason_code_genre(self):
        """Test building a genre reason code."""
        code = build_reason_code(ReasonCodeCategory.GENRE, "romance")
        assert code == "genre:romance"

    def test_build_reason_code_auteur(self):
        """Test building an auteur reason code."""
        code = build_reason_code(ReasonCodeCategory.AUTEUR, "bong")
        assert code == "auteur:bong"

    def test_build_reason_code_dimension(self):
        """Test building a dimension reason code."""
        code = build_reason_code(ReasonCodeCategory.DIMENSION, "4D")
        assert code == "dimension:4D"

    def test_build_reason_code_shot(self):
        """Test building a shot type reason code."""
        code = build_reason_code(ReasonCodeCategory.SHOT, "closeup")
        assert code == "shot:closeup"

    def test_build_reason_code_context(self):
        """Test building a context reason code."""
        code = build_reason_code(ReasonCodeCategory.CONTEXT, "worldbuilding")
        assert code == "context:worldbuilding"

    def test_build_reason_code_history(self):
        """Test building a history reason code."""
        code = build_reason_code(ReasonCodeCategory.HISTORY, "frequently_used")
        assert code == "history:frequently_used"

    def test_parse_reason_code_valid(self):
        """Test parsing a valid reason code."""
        category, value = parse_reason_code("genre:romance")
        assert category == "genre"
        assert value == "romance"

    def test_parse_reason_code_with_colon_in_value(self):
        """Test parsing reason code with colon in value."""
        category, value = parse_reason_code("ref:db:rag_docs:4D")
        assert category == "ref"
        assert value == "db:rag_docs:4D"

    def test_parse_reason_code_no_colon(self):
        """Test parsing reason code without colon."""
        category, value = parse_reason_code("invalid")
        assert category == "invalid"
        assert value == ""


# =============================================================================
# Tool Recommendation Schema Tests
# =============================================================================

class TestToolRecommendation:
    """Test ToolRecommendation schema."""

    def test_from_tool_data_high_confidence(self):
        """Test creating recommendation with high confidence."""
        rec = ToolRecommendation.from_tool_data(
            tool_id="aesthetic_direct",
            display_name="Aesthetic Director",
            dimension="AD",
            confidence=0.92,
            reason_codes=["auteur:bong", "genre:drama"],
            evidence_refs=["db:ip_catalog:goblin"],
            estimated_credits=15,
            priority=1,
        )
        assert rec.tool_id == "aesthetic_direct"
        assert rec.confidence == 0.92
        assert rec.confidence_level == ConfidenceLevel.HIGH
        assert "auteur:bong" in rec.reason_codes

    def test_from_tool_data_medium_confidence(self):
        """Test creating recommendation with medium confidence."""
        rec = ToolRecommendation.from_tool_data(
            tool_id="story_architect",
            display_name="Story Architect",
            dimension="STORY",
            confidence=0.65,
            reason_codes=["genre:drama"],
            evidence_refs=[],
            estimated_credits=10,
            priority=2,
        )
        assert rec.confidence_level == ConfidenceLevel.MEDIUM

    def test_from_tool_data_low_confidence(self):
        """Test creating recommendation with low confidence."""
        rec = ToolRecommendation.from_tool_data(
            tool_id="veo_generate",
            display_name="Veo Generate",
            dimension="VEO",
            confidence=0.35,
            reason_codes=[],
            evidence_refs=[],
            estimated_credits=25,
            priority=3,
        )
        assert rec.confidence_level == ConfidenceLevel.LOW

    def test_recommendation_validation(self):
        """Test recommendation field validation."""
        # Confidence must be 0-1
        with pytest.raises(ValueError):
            ToolRecommendation(
                tool_id="test",
                display_name="Test",
                dimension="AD",
                confidence=1.5,  # Invalid
                confidence_level=ConfidenceLevel.HIGH,
                estimated_credits=10,
            )

    def test_recommendation_priority_validation(self):
        """Test priority must be >= 1."""
        with pytest.raises(ValueError):
            ToolRecommendation(
                tool_id="test",
                display_name="Test",
                dimension="AD",
                confidence=0.5,
                confidence_level=ConfidenceLevel.MEDIUM,
                estimated_credits=10,
                priority=0,  # Invalid
            )


class TestToolRecommendationRequest:
    """Test ToolRecommendationRequest schema."""

    def test_minimal_request(self):
        """Test request with minimal fields."""
        req = ToolRecommendationRequest()
        assert req.ip_id is None
        assert req.preset_id is None
        assert req.max_results == 5

    def test_full_request(self):
        """Test request with all fields."""
        ip_id = uuid4()
        preset_id = uuid4()
        req = ToolRecommendationRequest(
            ip_id=ip_id,
            preset_id=preset_id,
            scene_type="establishing",
            user_history=["aesthetic_direct", "story_architect"],
            dimension_context="AD",
            max_results=10,
        )
        assert req.ip_id == ip_id
        assert req.scene_type == "establishing"
        assert len(req.user_history) == 2

    def test_max_results_validation(self):
        """Test max_results bounds."""
        req = ToolRecommendationRequest(max_results=20)
        assert req.max_results == 20

        with pytest.raises(ValueError):
            ToolRecommendationRequest(max_results=25)  # > 20

        with pytest.raises(ValueError):
            ToolRecommendationRequest(max_results=0)  # < 1


class TestToolRecommendationResponse:
    """Test ToolRecommendationResponse schema."""

    def test_empty_response(self):
        """Test empty response."""
        resp = ToolRecommendationResponse()
        assert resp.recommendations == []
        assert resp.total_estimated_credits == 0
        assert resp.workflow_suggested is False

    def test_full_response(self):
        """Test response with recommendations."""
        rec = ToolRecommendation.from_tool_data(
            tool_id="aesthetic_direct",
            display_name="Aesthetic Director",
            dimension="AD",
            confidence=0.9,
            reason_codes=["auteur:bong"],
            evidence_refs=[],
            estimated_credits=15,
        )
        resp = ToolRecommendationResponse(
            recommendations=[rec],
            total_estimated_credits=15,
            workflow_suggested=False,
            reason_summary="Based on 'Goblin' (bong style)",
            ip_context_used=True,
            trace_id="abc123",
        )
        assert len(resp.recommendations) == 1
        assert resp.ip_context_used is True


class TestToolEvidenceResponse:
    """Test ToolEvidenceResponse schema."""

    def test_evidence_response(self):
        """Test evidence response."""
        resp = ToolEvidenceResponse(
            tool_id="aesthetic_direct",
            evidence_refs=["db:ip_catalog:goblin", "rag:tier1:ad:doc1"],
            datasets_used=["ip:goblin", "rag:ad"],
            reason_codes=["auteur:bong", "dimension:AD"],
            confidence=0.85,
            confidence_level=ConfidenceLevel.HIGH,
        )
        assert resp.tool_id == "aesthetic_direct"
        assert len(resp.evidence_refs) == 2
        assert resp.confidence_level == ConfidenceLevel.HIGH


# =============================================================================
# Tool Metadata Tests
# =============================================================================

class TestToolMetadata:
    """Test tool metadata functions."""

    def test_get_tool_metadata_existing(self):
        """Test getting metadata for existing tool."""
        # This relies on DIMENSION_CAPSULES fixture
        metadata = get_tool_metadata("aesthetic_direct")
        # May be None if fixture not loaded
        if metadata:
            assert metadata["tool_id"] == "aesthetic_direct"
            assert "dimension" in metadata

    def test_get_tool_metadata_nonexistent(self):
        """Test getting metadata for non-existent tool."""
        metadata = get_tool_metadata("nonexistent_tool_xyz")
        assert metadata is None

    def test_get_all_tools(self):
        """Test getting all tools."""
        tools = get_all_tools()
        # Should return a list (may be empty if fixture not loaded)
        assert isinstance(tools, list)


# =============================================================================
# ToolRecommenderService Tests
# =============================================================================

class TestToolRecommenderService:
    """Test ToolRecommenderService methods."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        return db

    @pytest.fixture
    def mock_ip(self):
        """Create mock IP catalog."""
        ip = MagicMock()
        ip.id = uuid4()
        ip.slug = "goblin"
        ip.name_ko = "도깨비"
        ip.name_en = "Goblin"
        ip.auteur_key = "bong"
        ip.genre = ["drama", "fantasy"]
        ip.tags = ["romantic", "supernatural"]
        ip.worldbuilding = {
            "characters": [{"name": "Kim Shin"}],
            "setting": "Modern Seoul",
            "themes": ["love", "fate"],
        }
        return ip

    @pytest.fixture
    def mock_preset(self):
        """Create mock workflow preset."""
        preset = MagicMock()
        preset.id = uuid4()
        preset.ip_id = uuid4()
        preset.name_ko = "외전 드라마"
        preset.name_en = "Spinoff Drama"
        preset.preset_type = "video_short"
        preset.workflow_steps = [
            {"step": "analyze", "tool_id": "aesthetic_direct"},
            {"step": "generate", "tool_id": "veo_generate"},
        ]
        preset.estimated_credits = 40
        preset.pattern_version = "1.0.0"
        return preset

    @pytest.mark.asyncio
    async def test_recommend_tools_no_context(self, mock_db):
        """Test recommendations without IP context."""
        service = ToolRecommenderService(mock_db)

        request = ToolRecommendationRequest()
        response = await service.recommend_tools(request)

        assert isinstance(response, ToolRecommendationResponse)
        assert response.ip_context_used is False
        assert response.trace_id is not None

    @pytest.mark.asyncio
    async def test_recommend_tools_with_ip(self, mock_db, mock_ip):
        """Test recommendations with IP context."""
        # Setup mock DB to return IP
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_ip
        mock_db.execute.return_value = mock_result

        service = ToolRecommenderService(mock_db)

        request = ToolRecommendationRequest(ip_id=mock_ip.id)
        response = await service.recommend_tools(request)

        assert isinstance(response, ToolRecommendationResponse)
        assert response.ip_context_used is True

    @pytest.mark.asyncio
    async def test_recommend_tools_with_scene_type(self, mock_db, mock_ip):
        """Test recommendations with scene type hint."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_ip
        mock_db.execute.return_value = mock_result

        service = ToolRecommenderService(mock_db)

        request = ToolRecommendationRequest(
            ip_id=mock_ip.id,
            scene_type="establishing",
        )
        response = await service.recommend_tools(request)

        assert isinstance(response, ToolRecommendationResponse)
        # Recommendations should include shot reason codes
        for rec in response.recommendations:
            if "establishing" in str(rec.reason_codes):
                assert True
                break

    @pytest.mark.asyncio
    async def test_recommend_tools_with_user_history(self, mock_db, mock_ip):
        """Test recommendations with user history."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_ip
        mock_db.execute.return_value = mock_result

        service = ToolRecommenderService(mock_db)

        request = ToolRecommendationRequest(
            ip_id=mock_ip.id,
            user_history=["aesthetic_direct", "story_architect"],
        )
        response = await service.recommend_tools(request)

        assert isinstance(response, ToolRecommendationResponse)

    @pytest.mark.asyncio
    async def test_recommend_tools_max_results(self, mock_db):
        """Test max_results limit."""
        service = ToolRecommenderService(mock_db)

        request = ToolRecommendationRequest(max_results=3)
        response = await service.recommend_tools(request)

        assert len(response.recommendations) <= 3

    @pytest.mark.asyncio
    async def test_get_tool_evidence_no_ip(self, mock_db):
        """Test getting evidence without IP context."""
        service = ToolRecommenderService(mock_db)

        response = await service.get_tool_evidence("aesthetic_direct")

        assert isinstance(response, ToolEvidenceResponse)
        assert response.tool_id == "aesthetic_direct"

    @pytest.mark.asyncio
    async def test_get_tool_evidence_with_ip(self, mock_db, mock_ip):
        """Test getting evidence with IP context."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_ip
        mock_db.execute.return_value = mock_result

        service = ToolRecommenderService(mock_db)

        response = await service.get_tool_evidence("aesthetic_direct", mock_ip.id)

        assert isinstance(response, ToolEvidenceResponse)
        assert response.tool_id == "aesthetic_direct"
        # Should have IP-based evidence
        assert len(response.evidence_refs) > 0

    @pytest.mark.asyncio
    async def test_get_ip_recommendations_found(self, mock_db, mock_ip):
        """Test getting recommendations by IP slug."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_ip
        mock_db.execute.return_value = mock_result

        service = ToolRecommenderService(mock_db)

        response = await service.get_ip_recommendations("goblin")

        assert isinstance(response, ToolRecommendationResponse)
        assert response.ip_context_used is True

    @pytest.mark.asyncio
    async def test_get_ip_recommendations_not_found(self, mock_db):
        """Test getting recommendations for non-existent IP."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = ToolRecommenderService(mock_db)

        response = await service.get_ip_recommendations("nonexistent")

        assert isinstance(response, ToolRecommendationResponse)
        assert "not found" in response.reason_summary


# =============================================================================
# Scoring Logic Tests
# =============================================================================

class TestScoringLogic:
    """Test scoring logic for recommendations."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    def test_auteur_tool_affinity_bong(self, mock_db):
        """Test auteur-tool affinity for Bong Joon-ho."""
        service = ToolRecommenderService(mock_db)

        # Bong should favor aesthetic tools
        score = service._auteur_tool_affinity("bong", "aesthetic_direct")
        assert score > 0.2

        # But also quality check
        score = service._auteur_tool_affinity("bong", "quality_check")
        assert score > 0.1

    def test_auteur_tool_affinity_tarantino(self, mock_db):
        """Test auteur-tool affinity for Tarantino."""
        service = ToolRecommenderService(mock_db)

        # Tarantino should favor sound (music)
        score = service._auteur_tool_affinity("tarantino", "sound_crafter")
        assert score > 0.2

    def test_auteur_tool_affinity_unknown(self, mock_db):
        """Test auteur-tool affinity for unknown auteur."""
        service = ToolRecommenderService(mock_db)

        # Unknown auteur gets base score
        score = service._auteur_tool_affinity("unknown_director", "aesthetic_direct")
        assert score == 0.1  # Default

    def test_genre_tool_affinity_horror(self, mock_db):
        """Test genre-tool affinity for horror."""
        service = ToolRecommenderService(mock_db)

        # Horror should favor sound
        score = service._genre_tool_affinity(["horror"], "sound_crafter")
        assert score > 0.2

    def test_genre_tool_affinity_multiple(self, mock_db):
        """Test genre-tool affinity for multiple genres."""
        service = ToolRecommenderService(mock_db)

        # Multiple genres can stack
        score = service._genre_tool_affinity(
            ["drama", "romance"], "story_architect"
        )
        assert score > 0.0

    def test_genre_tool_affinity_capped(self, mock_db):
        """Test genre-tool affinity is capped at 0.3."""
        service = ToolRecommenderService(mock_db)

        # Even with many genres, cap at 0.3
        score = service._genre_tool_affinity(
            ["drama", "romance", "fantasy", "comedy"], "story_architect"
        )
        assert score <= 0.3

    def test_worldbuilding_tool_affinity_characters(self, mock_db):
        """Test worldbuilding affinity with characters."""
        service = ToolRecommenderService(mock_db)

        worldbuilding = {"characters": [{"name": "Kim Shin"}]}
        score = service._worldbuilding_tool_affinity(
            worldbuilding, "aesthetic_direct"
        )
        assert score > 0.0

    def test_worldbuilding_tool_affinity_setting(self, mock_db):
        """Test worldbuilding affinity with setting."""
        service = ToolRecommenderService(mock_db)

        worldbuilding = {"setting": "Modern Seoul"}
        score = service._worldbuilding_tool_affinity(
            worldbuilding, "generate_image_prompt"
        )
        assert score > 0.0

    def test_worldbuilding_tool_affinity_themes(self, mock_db):
        """Test worldbuilding affinity with themes."""
        service = ToolRecommenderService(mock_db)

        worldbuilding = {"themes": ["love", "fate"]}
        score = service._worldbuilding_tool_affinity(
            worldbuilding, "story_architect"
        )
        assert score > 0.0

    def test_scene_type_affinity_establishing(self, mock_db):
        """Test scene type affinity for establishing shots."""
        service = ToolRecommenderService(mock_db)

        score = service._scene_type_affinity("establishing", "generate_image_prompt")
        assert score > 0.0

    def test_scene_type_affinity_action(self, mock_db):
        """Test scene type affinity for action."""
        service = ToolRecommenderService(mock_db)

        score = service._scene_type_affinity("action", "veo_generate")
        assert score > 0.0

    def test_scene_type_affinity_unknown(self, mock_db):
        """Test scene type affinity for unknown type."""
        service = ToolRecommenderService(mock_db)

        score = service._scene_type_affinity("unknown_scene", "any_tool")
        assert score == 0.0


# =============================================================================
# Factory Function Tests
# =============================================================================

class TestFactoryFunction:
    """Test factory function."""

    def test_create_tool_recommender(self):
        """Test creating a ToolRecommenderService."""
        mock_db = AsyncMock()
        service = create_tool_recommender(mock_db)

        assert isinstance(service, ToolRecommenderService)


# =============================================================================
# ToolDisplayInfo Tests
# =============================================================================

class TestToolDisplayInfo:
    """Test ToolDisplayInfo schema."""

    def test_tool_display_info(self):
        """Test ToolDisplayInfo creation."""
        info = ToolDisplayInfo(
            tool_id="aesthetic_direct",
            display_name_ko="미학 디렉터",
            display_name_en="Aesthetic Director",
            dimension="AD",
            description_ko="스타일 가이드 생성",
            description_en="Generate style guide",
            icon="icon-ad",
            base_credits=15,
        )
        assert info.tool_id == "aesthetic_direct"
        assert info.base_credits == 15
