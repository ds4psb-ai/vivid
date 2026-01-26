"""Tests for DNA Lab Router and Service.

Comprehensive test suite covering:
- DNA Lab service orchestration
- Component integration (VPE, AD, Mirror, QC)
- Credit calculation
- Error handling
"""
from __future__ import annotations

import pytest
from dataclasses import asdict
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status
from httpx import AsyncClient

from app.schemas.vpe import LogicVector, VPEParseResponse
from app.services.dna_lab_service import (
    AestheticGuidelines,
    COMPONENT_CREDITS,
    DNAComponent,
    DNALabResult,
    DNALabService,
    PersonaDNA,
    QualityMetrics,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_vpe_response() -> VPEParseResponse:
    """Create a mock VPE response."""
    return VPEParseResponse(
        success=True,
        trace_id="vpe-trace-123",
        logic_vector=LogicVector(
            auteur_id="bong",
            confidence=0.85,
        ),
        evidence_refs=["db:vpe_results:123"],
        confidence=0.85,
        shot_count=10,
    )


@pytest.fixture
def mock_ad_response() -> Dict[str, Any]:
    """Create a mock AD response."""
    return {
        "success": True,
        "output": {
            "visual_style": "dark cinematic",
            "color_palette": ["desaturated", "green_tint"],
            "mood_keywords": ["tension", "suspense"],
            "reference_directors": ["Bong Joon-ho"],
            "composition_notes": "vertical blocking",
            "lighting_approach": "low-key dramatic",
            "evidence_refs": ["db:ad_results:456"],
        },
    }


@pytest.fixture
def mock_mirror_response() -> Dict[str, Any]:
    """Create a mock Mirror response."""
    return {
        "success": True,
        "output": {
            "persona_type": "creative_visionary",
            "creative_tendencies": ["visual_storytelling", "symbolic_imagery"],
            "visual_preferences": ["symmetry", "depth"],
            "narrative_style": "layered_meaning",
            "emotional_range": ["subtle", "impactful"],
            "evidence_refs": ["db:mirror_results:789"],
        },
    }


@pytest.fixture
def mock_qc_response() -> Dict[str, Any]:
    """Create a mock QC response."""
    return {
        "success": True,
        "output": {
            "score": 0.85,
            "technical_score": 0.9,
            "aesthetic_score": 0.8,
            "narrative_coherence": 0.85,
            "issues": [],
            "suggestions": ["Consider stronger lighting contrast"],
            "evidence_refs": ["db:qc_results:101"],
        },
    }


# =============================================================================
# Service Tests
# =============================================================================

class TestDNALabService:
    """Tests for DNA Lab service."""

    def test_calculate_total_credits(self):
        """Test credit calculation for components."""
        service = DNALabService()

        # Single component
        assert service.calculate_total_credits(["ad"]) == COMPONENT_CREDITS[DNAComponent.AD]

        # Multiple components
        expected = (
            COMPONENT_CREDITS[DNAComponent.VPE] +
            COMPONENT_CREDITS[DNAComponent.AD]
        )
        assert service.calculate_total_credits(["vpe", "ad"]) == expected

        # All components
        all_cost = sum(COMPONENT_CREDITS.values())
        assert service.calculate_total_credits(["vpe", "ad", "mirror", "qc"]) == all_cost

        # Invalid component
        assert service.calculate_total_credits(["invalid"]) == 0

    @pytest.mark.asyncio
    async def test_extract_dna_ad_only(self, mock_ad_response: Dict):
        """Test DNA extraction with AD component only."""
        with patch.object(DNALabService, "_run_aesthetic_director", new_callable=AsyncMock) as mock_ad:
            mock_ad.return_value = mock_ad_response

            service = DNALabService()
            result = await service.extract_dna(
                concept="dark sci-fi",
                auteur_key="bong",
                components=["ad"],
            )

            assert result.success is True
            assert "ad" in result.components_run
            assert result.aesthetic_guidelines is not None
            assert result.aesthetic_guidelines.visual_style == "dark cinematic"

    @pytest.mark.asyncio
    async def test_extract_dna_vpe_and_ad(
        self,
        mock_vpe_response: VPEParseResponse,
        mock_ad_response: Dict,
    ):
        """Test DNA extraction with VPE and AD components."""
        with patch.object(DNALabService, "_run_vpe", new_callable=AsyncMock) as mock_vpe:
            mock_vpe.return_value = mock_vpe_response

            with patch.object(DNALabService, "_run_aesthetic_director", new_callable=AsyncMock) as mock_ad:
                mock_ad.return_value = mock_ad_response

                service = DNALabService()
                result = await service.extract_dna(
                    video_uri="gs://test-bucket/video.mp4",
                    concept="dark sci-fi",
                    auteur_key="bong",
                    components=["vpe", "ad"],
                )

                assert result.success is True
                assert "vpe" in result.components_run
                assert "ad" in result.components_run
                assert result.logic_vector is not None
                assert result.logic_vector.auteur_id == "bong"

    @pytest.mark.asyncio
    async def test_extract_dna_all_components(
        self,
        mock_vpe_response: VPEParseResponse,
        mock_ad_response: Dict,
        mock_mirror_response: Dict,
        mock_qc_response: Dict,
    ):
        """Test DNA extraction with all components."""
        with patch.object(DNALabService, "_run_vpe", new_callable=AsyncMock) as mock_vpe:
            mock_vpe.return_value = mock_vpe_response

            with patch.object(DNALabService, "_run_aesthetic_director", new_callable=AsyncMock) as mock_ad:
                mock_ad.return_value = mock_ad_response

                with patch.object(DNALabService, "_run_mirror", new_callable=AsyncMock) as mock_mirror:
                    mock_mirror.return_value = mock_mirror_response

                    with patch.object(DNALabService, "_run_quality_check", new_callable=AsyncMock) as mock_qc:
                        mock_qc.return_value = mock_qc_response

                        service = DNALabService()
                        result = await service.extract_dna(
                            video_uri="gs://test-bucket/video.mp4",
                            concept="dark sci-fi",
                            auteur_key="bong",
                            components=["vpe", "ad", "mirror", "qc"],
                            persona_context={"birth_date": "1990-01-01"},
                            quality_content="Test content",
                        )

                        assert result.success is True
                        assert len(result.components_run) == 4
                        assert result.logic_vector is not None
                        assert result.aesthetic_guidelines is not None
                        assert result.persona_dna is not None
                        assert result.quality_metrics is not None

    @pytest.mark.asyncio
    async def test_extract_dna_partial_failure(self, mock_ad_response: Dict):
        """Test DNA extraction handles partial component failure."""
        with patch.object(DNALabService, "_run_vpe", new_callable=AsyncMock) as mock_vpe:
            mock_vpe.side_effect = Exception("VPE failed")

            with patch.object(DNALabService, "_run_aesthetic_director", new_callable=AsyncMock) as mock_ad:
                mock_ad.return_value = mock_ad_response

                service = DNALabService()
                result = await service.extract_dna(
                    video_uri="gs://test-bucket/video.mp4",
                    concept="dark sci-fi",
                    auteur_key="bong",
                    components=["vpe", "ad"],
                )

                # Should still succeed with partial results
                assert result.success is True
                assert "ad" in result.components_run
                assert "vpe" not in result.components_run
                assert "vpe" in result.errors

    @pytest.mark.asyncio
    async def test_extract_dna_missing_required_input(self):
        """Test DNA extraction with missing required inputs."""
        service = DNALabService()

        # VPE without video_uri
        result = await service.extract_dna(
            components=["vpe"],
        )
        assert "vpe" in result.errors
        assert "video_uri" in result.errors["vpe"].lower()

        # QC without quality_content
        result = await service.extract_dna(
            components=["qc"],
        )
        assert "qc" in result.errors

    @pytest.mark.asyncio
    async def test_extract_dna_invalid_components(self):
        """Test DNA extraction with invalid component names."""
        service = DNALabService()
        result = await service.extract_dna(
            components=["invalid_component"],
        )
        assert result.success is False
        assert "components" in result.errors

    @pytest.mark.asyncio
    async def test_extract_dna_evidence_refs_collection(
        self,
        mock_vpe_response: VPEParseResponse,
        mock_ad_response: Dict,
    ):
        """Test evidence_refs are properly collected from all components."""
        with patch.object(DNALabService, "_run_vpe", new_callable=AsyncMock) as mock_vpe:
            mock_vpe.return_value = mock_vpe_response

            with patch.object(DNALabService, "_run_aesthetic_director", new_callable=AsyncMock) as mock_ad:
                mock_ad.return_value = mock_ad_response

                service = DNALabService()
                result = await service.extract_dna(
                    video_uri="gs://test-bucket/video.mp4",
                    concept="dark sci-fi",
                    components=["vpe", "ad"],
                )

                # Should have refs from both components
                assert len(result.evidence_refs) >= 2
                assert any("vpe" in ref for ref in result.evidence_refs)
                assert any("ad" in ref for ref in result.evidence_refs)

    def test_create_logic_vector_from_ad(self):
        """Test Logic Vector creation from AD guidelines."""
        service = DNALabService()

        guidelines = AestheticGuidelines(
            visual_style="symmetrical minimalist",
            color_palette=["desaturated", "blue"],
            lighting_approach="dramatic low-key",
        )

        lv = service._create_logic_vector_from_ad(guidelines, "prism")

        assert lv.auteur_id == "prism"
        assert lv.composition.primary_strategy in ["symmetry", "rule_of_thirds", "negative_space"]
        assert "desaturated" in lv.color_science.palette or "blue" in lv.color_science.palette


# =============================================================================
# Router Tests
# =============================================================================

class TestDNALabRouter:
    """Tests for DNA Lab API endpoints."""

    @pytest.mark.asyncio
    async def test_extract_endpoint_success(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/dna-lab/extract endpoint success."""
        with patch("app.routers.dna_lab.router.get_dna_lab_service") as mock_service:
            mock_svc = MagicMock()
            mock_svc.calculate_total_credits.return_value = 10
            mock_svc.extract_dna = AsyncMock(return_value=DNALabResult(
                success=True,
                trace_id="test-trace",
                components_run=["ad"],
                confidence=0.8,
                credits_used=10,
            ))
            mock_service.return_value = mock_svc

            with patch("app.routers.dna_lab.router.get_or_create_user_credits") as mock_credits:
                mock_credits.return_value = MagicMock(balance=1000)

                with patch("app.routers.dna_lab.router.deduct_credits", new_callable=AsyncMock):
                    response = await async_client.post(
                        "/api/dna-lab/extract",
                        json={
                            "concept": "dark sci-fi",
                            "auteur_key": "bong",
                            "components": ["ad"],
                        },
                        headers=auth_headers,
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "ad" in data["components_run"]

    @pytest.mark.asyncio
    async def test_extract_endpoint_insufficient_credits(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/dna-lab/extract returns 402 when credits insufficient."""
        with patch("app.routers.dna_lab.router.get_dna_lab_service") as mock_service:
            mock_svc = MagicMock()
            mock_svc.calculate_total_credits.return_value = 100
            mock_service.return_value = mock_svc

            with patch("app.routers.dna_lab.router.get_or_create_user_credits") as mock_credits:
                mock_credits.return_value = MagicMock(balance=10)

                response = await async_client.post(
                    "/api/dna-lab/extract",
                    json={
                        "video_uri": "gs://bucket/video.mp4",
                        "components": ["vpe", "ad"],
                    },
                    headers=auth_headers,
                )

        assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED

    @pytest.mark.asyncio
    async def test_get_credit_costs(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/dna-lab/credits endpoint."""
        response = await async_client.get(
            "/api/dna-lab/credits",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "components" in data
        assert "vpe" in data["components"]
        assert "ad" in data["components"]
        assert data["total_for_all"] == sum(COMPONENT_CREDITS.values())

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test /api/dna-lab/health endpoint."""
        response = await async_client.get("/api/dna-lab/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["service"] == "dna_lab"
        assert "components" in data


# =============================================================================
# Data Classes Tests
# =============================================================================

class TestDNALabDataClasses:
    """Tests for DNA Lab data classes."""

    def test_aesthetic_guidelines_defaults(self):
        """Test AestheticGuidelines default values."""
        guidelines = AestheticGuidelines()
        assert guidelines.visual_style == ""
        assert guidelines.color_palette == []

    def test_persona_dna_defaults(self):
        """Test PersonaDNA default values."""
        persona = PersonaDNA()
        assert persona.persona_type == ""
        assert persona.creative_tendencies == []

    def test_quality_metrics_defaults(self):
        """Test QualityMetrics default values."""
        metrics = QualityMetrics()
        assert metrics.overall_score == 0.0
        assert metrics.issues == []

    def test_dna_lab_result_to_dict(self):
        """Test DNALabResult can be serialized."""
        result = DNALabResult(
            success=True,
            trace_id="test",
            aesthetic_guidelines=AestheticGuidelines(visual_style="test"),
        )

        # Should be serializable
        if result.aesthetic_guidelines:
            data = asdict(result.aesthetic_guidelines)
            assert data["visual_style"] == "test"


# =============================================================================
# Integration Tests
# =============================================================================

class TestDNALabIntegration:
    """Integration tests for DNA Lab."""

    @pytest.mark.asyncio
    async def test_full_extraction_flow(self, mock_ad_response: Dict):
        """Test complete extraction flow with mocked components."""
        with patch.object(DNALabService, "_run_aesthetic_director", new_callable=AsyncMock) as mock_ad:
            mock_ad.return_value = mock_ad_response

            service = DNALabService()
            result = await service.extract_dna(
                concept="film noir detective story",
                auteur_key="epoch",
                components=["ad"],
            )

            assert result.success is True
            assert result.logic_vector is not None  # Created from AD
            assert result.logic_vector.auteur_id == "epoch"
            assert result.aesthetic_guidelines is not None

    def test_component_enum_values(self):
        """Test DNAComponent enum has expected values."""
        assert DNAComponent.VPE.value == "vpe"
        assert DNAComponent.AD.value == "ad"
        assert DNAComponent.MIRROR.value == "mirror"
        assert DNAComponent.QC.value == "qc"

    def test_component_credits_coverage(self):
        """Test all components have credit costs defined."""
        for component in DNAComponent:
            assert component in COMPONENT_CREDITS
            assert COMPONENT_CREDITS[component] > 0
