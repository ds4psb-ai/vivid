"""
Tests for Tool Recommendation API router.

Tests the IP-First Coordination Phase 2.5 endpoints:
- POST /tools/recommend - Get tool recommendations
- GET /tools/ip/{slug}/recommendations - IP-specific recommendations
- GET /tools/{tool_id}/evidence - Tool evidence
- GET /tools/list - List all tools
- GET /tools/{tool_id}/info - Tool info
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
from fastapi import HTTPException

from app.schemas.tool_recommendation import (
    ToolRecommendation,
    ToolRecommendationRequest,
    ToolRecommendationResponse,
    ToolEvidenceResponse,
    ToolDisplayInfo,
)
from app.rag.rag_suggestion import ConfidenceLevel


# =============================================================================
# Schema Tests for API
# =============================================================================

class TestToolRecommendationRequestAPI:
    """Test ToolRecommendationRequest for API validation."""

    def test_valid_request_minimal(self):
        """Test minimal valid request."""
        req = ToolRecommendationRequest()
        assert req.ip_id is None
        assert req.max_results == 5

    def test_valid_request_with_ip(self):
        """Test request with IP ID."""
        ip_id = uuid4()
        req = ToolRecommendationRequest(ip_id=ip_id)
        assert req.ip_id == ip_id

    def test_valid_request_with_preset(self):
        """Test request with preset ID."""
        preset_id = uuid4()
        req = ToolRecommendationRequest(preset_id=preset_id)
        assert req.preset_id == preset_id

    def test_valid_request_full(self):
        """Test full request with all fields."""
        ip_id = uuid4()
        preset_id = uuid4()
        req = ToolRecommendationRequest(
            ip_id=ip_id,
            preset_id=preset_id,
            scene_type="establishing",
            user_history=["tool1", "tool2"],
            dimension_context="AD",
            max_results=10,
        )
        assert req.ip_id == ip_id
        assert req.preset_id == preset_id
        assert req.scene_type == "establishing"
        assert len(req.user_history) == 2
        assert req.dimension_context == "AD"
        assert req.max_results == 10

    def test_invalid_max_results_too_high(self):
        """Test max_results > 20 fails."""
        with pytest.raises(ValueError):
            ToolRecommendationRequest(max_results=21)

    def test_invalid_max_results_zero(self):
        """Test max_results = 0 fails."""
        with pytest.raises(ValueError):
            ToolRecommendationRequest(max_results=0)

    def test_invalid_max_results_negative(self):
        """Test negative max_results fails."""
        with pytest.raises(ValueError):
            ToolRecommendationRequest(max_results=-1)


class TestToolRecommendationResponseAPI:
    """Test ToolRecommendationResponse for API serialization."""

    def test_response_serialization(self):
        """Test response can be serialized to JSON."""
        rec = ToolRecommendation.from_tool_data(
            tool_id="aesthetic_direct",
            display_name="Aesthetic Director",
            dimension="AD",
            confidence=0.9,
            reason_codes=["auteur:bong"],
            evidence_refs=["db:ip_catalog:goblin"],
            estimated_credits=15,
        )
        resp = ToolRecommendationResponse(
            recommendations=[rec],
            total_estimated_credits=15,
            workflow_suggested=False,
            reason_summary="Based on 'Goblin'",
            ip_context_used=True,
            trace_id="test123",
        )

        # Serialize to dict (like JSON)
        data = resp.model_dump()
        assert data["recommendations"][0]["tool_id"] == "aesthetic_direct"
        assert data["total_estimated_credits"] == 15
        assert data["ip_context_used"] is True

    def test_response_empty_recommendations(self):
        """Test empty recommendations response."""
        resp = ToolRecommendationResponse()
        data = resp.model_dump()
        assert data["recommendations"] == []
        assert data["total_estimated_credits"] == 0

    def test_response_multiple_recommendations(self):
        """Test response with multiple recommendations."""
        recs = [
            ToolRecommendation.from_tool_data(
                tool_id=f"tool_{i}",
                display_name=f"Tool {i}",
                dimension="AD",
                confidence=0.9 - (i * 0.1),
                reason_codes=[],
                evidence_refs=[],
                estimated_credits=10 + i,
                priority=i + 1,
            )
            for i in range(3)
        ]
        resp = ToolRecommendationResponse(
            recommendations=recs,
            total_estimated_credits=sum(r.estimated_credits for r in recs),
        )
        assert len(resp.recommendations) == 3
        assert resp.total_estimated_credits == 33


class TestToolEvidenceResponseAPI:
    """Test ToolEvidenceResponse for API serialization."""

    def test_evidence_response_serialization(self):
        """Test evidence response serialization."""
        resp = ToolEvidenceResponse(
            tool_id="aesthetic_direct",
            evidence_refs=["db:ip_catalog:goblin"],
            datasets_used=["ip:goblin"],
            reason_codes=["auteur:bong", "dimension:AD"],
            confidence=0.85,
            confidence_level=ConfidenceLevel.HIGH,
        )
        data = resp.model_dump()
        assert data["tool_id"] == "aesthetic_direct"
        assert len(data["evidence_refs"]) == 1
        assert data["confidence_level"] == "high"


class TestToolDisplayInfoAPI:
    """Test ToolDisplayInfo for API serialization."""

    def test_display_info_serialization(self):
        """Test display info serialization."""
        info = ToolDisplayInfo(
            tool_id="aesthetic_direct",
            display_name_ko="미학 디렉터",
            display_name_en="Aesthetic Director",
            dimension="AD",
            icon="icon-ad",
            base_credits=15,
        )
        data = info.model_dump()
        assert data["tool_id"] == "aesthetic_direct"
        assert data["display_name_ko"] == "미학 디렉터"
        assert data["base_credits"] == 15


# =============================================================================
# Router Endpoint Tests (Mocked)
# =============================================================================

class TestRecommendEndpoint:
    """Test POST /tools/recommend endpoint."""

    @pytest.mark.asyncio
    async def test_recommend_success(self):
        """Test successful recommendation."""
        from app.routers.tool_recommendation import recommend_tools

        mock_db = AsyncMock()
        mock_response = ToolRecommendationResponse(
            recommendations=[],
            total_estimated_credits=0,
            ip_context_used=False,
            trace_id="test",
        )

        with patch(
            "app.routers.tool_recommendation.create_tool_recommender"
        ) as mock_create:
            mock_service = AsyncMock()
            mock_service.recommend_tools.return_value = mock_response
            mock_create.return_value = mock_service

            request = ToolRecommendationRequest()
            response = await recommend_tools(request, mock_db, None)

            assert isinstance(response, ToolRecommendationResponse)
            mock_service.recommend_tools.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_recommend_with_ip(self):
        """Test recommendation with IP ID."""
        from app.routers.tool_recommendation import recommend_tools

        mock_db = AsyncMock()
        ip_id = uuid4()
        mock_response = ToolRecommendationResponse(
            recommendations=[],
            ip_context_used=True,
            trace_id="test",
        )

        with patch(
            "app.routers.tool_recommendation.create_tool_recommender"
        ) as mock_create:
            mock_service = AsyncMock()
            mock_service.recommend_tools.return_value = mock_response
            mock_create.return_value = mock_service

            request = ToolRecommendationRequest(ip_id=ip_id)
            response = await recommend_tools(request, mock_db, "user123")

            assert response.ip_context_used is True

    @pytest.mark.asyncio
    async def test_recommend_error_handling(self):
        """Test error handling in recommendation."""
        from app.routers.tool_recommendation import recommend_tools

        mock_db = AsyncMock()

        with patch(
            "app.routers.tool_recommendation.create_tool_recommender"
        ) as mock_create:
            mock_service = AsyncMock()
            mock_service.recommend_tools.side_effect = Exception("Test error")
            mock_create.return_value = mock_service

            request = ToolRecommendationRequest()

            with pytest.raises(HTTPException) as exc_info:
                await recommend_tools(request, mock_db, None)

            assert exc_info.value.status_code == 500


class TestIPRecommendationsEndpoint:
    """Test GET /tools/ip/{slug}/recommendations endpoint."""

    @pytest.mark.asyncio
    async def test_ip_recommendations_success(self):
        """Test successful IP recommendations."""
        from app.routers.tool_recommendation import get_ip_recommendations

        mock_db = AsyncMock()
        mock_response = ToolRecommendationResponse(
            recommendations=[],
            ip_context_used=True,
            reason_summary="Based on 'Goblin'",
        )

        with patch(
            "app.routers.tool_recommendation.create_tool_recommender"
        ) as mock_create:
            mock_service = AsyncMock()
            mock_service.get_ip_recommendations.return_value = mock_response
            mock_create.return_value = mock_service

            response = await get_ip_recommendations(
                slug="goblin",
                max_results=5,
                scene_type=None,
                dimension_context=None,
                db=mock_db,
                user_id=None,
            )

            assert isinstance(response, ToolRecommendationResponse)

    @pytest.mark.asyncio
    async def test_ip_recommendations_not_found(self):
        """Test IP not found returns appropriate response."""
        from app.routers.tool_recommendation import get_ip_recommendations

        mock_db = AsyncMock()
        mock_response = ToolRecommendationResponse(
            recommendations=[],
            reason_summary="IP 'nonexistent' not found",
        )

        with patch(
            "app.routers.tool_recommendation.create_tool_recommender"
        ) as mock_create:
            mock_service = AsyncMock()
            mock_service.get_ip_recommendations.return_value = mock_response
            mock_create.return_value = mock_service

            response = await get_ip_recommendations(
                slug="nonexistent",
                max_results=5,
                scene_type=None,
                dimension_context=None,
                db=mock_db,
                user_id=None,
            )

            assert "not found" in response.reason_summary


class TestToolEvidenceEndpoint:
    """Test GET /tools/{tool_id}/evidence endpoint."""

    @pytest.mark.asyncio
    async def test_evidence_success(self):
        """Test successful evidence retrieval."""
        from app.routers.tool_recommendation import get_tool_evidence

        mock_db = AsyncMock()
        mock_response = ToolEvidenceResponse(
            tool_id="aesthetic_direct",
            evidence_refs=["db:ip_catalog:goblin"],
            confidence=0.85,
            confidence_level=ConfidenceLevel.HIGH,
        )

        with patch(
            "app.routers.tool_recommendation.get_tool_metadata"
        ) as mock_get_meta:
            mock_get_meta.return_value = {"tool_id": "aesthetic_direct"}

            with patch(
                "app.routers.tool_recommendation.create_tool_recommender"
            ) as mock_create:
                mock_service = AsyncMock()
                mock_service.get_tool_evidence.return_value = mock_response
                mock_create.return_value = mock_service

                response = await get_tool_evidence(
                    tool_id="aesthetic_direct",
                    ip_id=None,
                    db=mock_db,
                    user_id=None,
                )

                assert response.tool_id == "aesthetic_direct"

    @pytest.mark.asyncio
    async def test_evidence_tool_not_found(self):
        """Test evidence for non-existent tool."""
        from app.routers.tool_recommendation import get_tool_evidence

        mock_db = AsyncMock()

        with patch(
            "app.routers.tool_recommendation.get_tool_metadata"
        ) as mock_get_meta:
            mock_get_meta.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await get_tool_evidence(
                    tool_id="nonexistent",
                    ip_id=None,
                    db=mock_db,
                    user_id=None,
                )

            assert exc_info.value.status_code == 404


class TestListToolsEndpoint:
    """Test GET /tools/list endpoint."""

    @pytest.mark.asyncio
    async def test_list_tools_all(self):
        """Test listing all tools."""
        from app.routers.tool_recommendation import list_tools

        with patch(
            "app.routers.tool_recommendation.get_all_tools"
        ) as mock_get_all:
            mock_get_all.return_value = [
                {
                    "tool_id": "aesthetic_direct",
                    "display_name_ko": "미학 디렉터",
                    "display_name_en": "Aesthetic Director",
                    "dimension": "AD",
                    "stage": "planning",
                    "base_credits": 15,
                },
            ]

            response = await list_tools(dimension=None, stage=None)

            assert len(response) == 1
            assert response[0].tool_id == "aesthetic_direct"

    @pytest.mark.asyncio
    async def test_list_tools_filter_dimension(self):
        """Test listing tools filtered by dimension."""
        from app.routers.tool_recommendation import list_tools

        with patch(
            "app.routers.tool_recommendation.get_all_tools"
        ) as mock_get_all:
            mock_get_all.return_value = [
                {
                    "tool_id": "aesthetic_direct",
                    "display_name_ko": "미학 디렉터",
                    "display_name_en": "Aesthetic Director",
                    "dimension": "AD",
                    "stage": "planning",
                    "base_credits": 15,
                },
                {
                    "tool_id": "story_architect",
                    "display_name_ko": "스토리 아키텍트",
                    "display_name_en": "Story Architect",
                    "dimension": "STORY",
                    "stage": "planning",
                    "base_credits": 10,
                },
            ]

            response = await list_tools(dimension="AD", stage=None)

            assert len(response) == 1
            assert response[0].dimension == "AD"

    @pytest.mark.asyncio
    async def test_list_tools_filter_stage(self):
        """Test listing tools filtered by stage."""
        from app.routers.tool_recommendation import list_tools

        with patch(
            "app.routers.tool_recommendation.get_all_tools"
        ) as mock_get_all:
            mock_get_all.return_value = [
                {
                    "tool_id": "aesthetic_direct",
                    "display_name_ko": "미학 디렉터",
                    "display_name_en": "Aesthetic Director",
                    "dimension": "AD",
                    "stage": "planning",
                    "base_credits": 15,
                },
                {
                    "tool_id": "veo_generate",
                    "display_name_ko": "비디오 메이커",
                    "display_name_en": "Video Maker",
                    "dimension": "VEO",
                    "stage": "production",
                    "base_credits": 25,
                },
            ]

            response = await list_tools(dimension=None, stage="production")

            assert len(response) == 1
            assert response[0].tool_id == "veo_generate"

    @pytest.mark.asyncio
    async def test_list_tools_empty(self):
        """Test listing tools returns empty when filtered out."""
        from app.routers.tool_recommendation import list_tools

        with patch(
            "app.routers.tool_recommendation.get_all_tools"
        ) as mock_get_all:
            mock_get_all.return_value = [
                {
                    "tool_id": "aesthetic_direct",
                    "dimension": "AD",
                    "stage": "planning",
                },
            ]

            response = await list_tools(dimension="VEO", stage=None)

            assert len(response) == 0


class TestToolInfoEndpoint:
    """Test GET /tools/{tool_id}/info endpoint."""

    @pytest.mark.asyncio
    async def test_tool_info_success(self):
        """Test getting tool info."""
        from app.routers.tool_recommendation import get_tool_info

        with patch(
            "app.routers.tool_recommendation.get_tool_metadata"
        ) as mock_get_meta:
            mock_get_meta.return_value = {
                "tool_id": "aesthetic_direct",
                "display_name_ko": "미학 디렉터",
                "display_name_en": "Aesthetic Director",
                "dimension": "AD",
                "base_credits": 15,
            }

            response = await get_tool_info(tool_id="aesthetic_direct")

            assert response.tool_id == "aesthetic_direct"
            assert response.display_name_en == "Aesthetic Director"

    @pytest.mark.asyncio
    async def test_tool_info_not_found(self):
        """Test tool info for non-existent tool."""
        from app.routers.tool_recommendation import get_tool_info

        with patch(
            "app.routers.tool_recommendation.get_tool_metadata"
        ) as mock_get_meta:
            mock_get_meta.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await get_tool_info(tool_id="nonexistent")

            assert exc_info.value.status_code == 404


# =============================================================================
# Integration Tests (with mock DB)
# =============================================================================

class TestRecommendationIntegration:
    """Integration tests for recommendation flow."""

    @pytest.mark.asyncio
    async def test_full_recommendation_flow(self):
        """Test full recommendation flow."""
        from app.routers.tool_recommendation import recommend_tools
        from app.services.tool_recommender import ToolRecommenderService

        mock_db = AsyncMock()

        # Mock IP data
        mock_ip = MagicMock()
        mock_ip.id = uuid4()
        mock_ip.slug = "goblin"
        mock_ip.name_en = "Goblin"
        mock_ip.auteur_key = "bong"
        mock_ip.genre = ["drama", "fantasy"]
        mock_ip.worldbuilding = {}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_ip
        mock_db.execute.return_value = mock_result

        request = ToolRecommendationRequest(
            ip_id=mock_ip.id,
            scene_type="establishing",
        )

        response = await recommend_tools(request, mock_db, "user123")

        assert isinstance(response, ToolRecommendationResponse)
        # With actual service, should have recommendations

    @pytest.mark.asyncio
    async def test_recommendation_credits_calculation(self):
        """Test that total credits are calculated correctly."""
        rec1 = ToolRecommendation.from_tool_data(
            tool_id="tool1",
            display_name="Tool 1",
            dimension="AD",
            confidence=0.9,
            reason_codes=[],
            evidence_refs=[],
            estimated_credits=15,
        )
        rec2 = ToolRecommendation.from_tool_data(
            tool_id="tool2",
            display_name="Tool 2",
            dimension="STORY",
            confidence=0.8,
            reason_codes=[],
            evidence_refs=[],
            estimated_credits=10,
        )

        resp = ToolRecommendationResponse(
            recommendations=[rec1, rec2],
            total_estimated_credits=rec1.estimated_credits + rec2.estimated_credits,
        )

        assert resp.total_estimated_credits == 25


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_reason_codes(self):
        """Test recommendation with empty reason codes."""
        rec = ToolRecommendation.from_tool_data(
            tool_id="test",
            display_name="Test",
            dimension="AD",
            confidence=0.5,
            reason_codes=[],
            evidence_refs=[],
            estimated_credits=10,
        )
        assert rec.reason_codes == []

    def test_empty_evidence_refs(self):
        """Test recommendation with empty evidence refs."""
        rec = ToolRecommendation.from_tool_data(
            tool_id="test",
            display_name="Test",
            dimension="AD",
            confidence=0.5,
            reason_codes=["test:value"],
            evidence_refs=[],
            estimated_credits=10,
        )
        assert rec.evidence_refs == []

    def test_boundary_confidence_values(self):
        """Test boundary confidence values."""
        # Exactly 0
        rec = ToolRecommendation.from_tool_data(
            tool_id="test",
            display_name="Test",
            dimension="AD",
            confidence=0.0,
            reason_codes=[],
            evidence_refs=[],
            estimated_credits=10,
        )
        assert rec.confidence == 0.0
        assert rec.confidence_level == ConfidenceLevel.LOW

        # Exactly 1
        rec = ToolRecommendation.from_tool_data(
            tool_id="test",
            display_name="Test",
            dimension="AD",
            confidence=1.0,
            reason_codes=[],
            evidence_refs=[],
            estimated_credits=10,
        )
        assert rec.confidence == 1.0
        assert rec.confidence_level == ConfidenceLevel.HIGH

        # Exactly 0.75 (HIGH threshold)
        rec = ToolRecommendation.from_tool_data(
            tool_id="test",
            display_name="Test",
            dimension="AD",
            confidence=0.75,
            reason_codes=[],
            evidence_refs=[],
            estimated_credits=10,
        )
        assert rec.confidence_level == ConfidenceLevel.HIGH

        # Exactly 0.5 (MEDIUM threshold)
        rec = ToolRecommendation.from_tool_data(
            tool_id="test",
            display_name="Test",
            dimension="AD",
            confidence=0.5,
            reason_codes=[],
            evidence_refs=[],
            estimated_credits=10,
        )
        assert rec.confidence_level == ConfidenceLevel.MEDIUM

    def test_unicode_in_reason_summary(self):
        """Test unicode characters in reason summary."""
        resp = ToolRecommendationResponse(
            recommendations=[],
            reason_summary="강주노 감독 스타일의 드라마에 최적화된 도구",
        )
        assert "강주노" in resp.reason_summary

    def test_special_characters_in_slug(self):
        """Test special characters in IP slug."""
        # Slugs should handle hyphens
        req = ToolRecommendationRequest()
        # Just ensure no crash
        assert req is not None
