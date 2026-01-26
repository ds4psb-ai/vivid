"""Tests for VPE (Video Parsing Engine) Router and Service.

Comprehensive test suite covering:
- VPE schema validation
- VPE service (mocked Gemini API)
- VPE storage (Qdrant operations)
- VPE router endpoints
- Error handling and refunds
"""
from __future__ import annotations

import json
import pytest
import uuid
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status
from httpx import AsyncClient

from app.schemas.vpe import (
    Cadence,
    CameraGrammar,
    ColorScience,
    Composition,
    LightingPhysics,
    LogicVector,
    ShotAnalysis,
    VPEParseRequest,
    VPEParseResponse,
    VPEQueryRequest,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_logic_vector() -> LogicVector:
    """Create a sample Logic Vector for testing."""
    return LogicVector(
        auteur_id="bong",
        cadence=Cadence(
            hook=0.5,
            build=2.0,
            climax=5.0,
            avg_shot_length=3.2,
            rhythm_pattern="slow_build",
            tempo="deliberate",
        ),
        composition=Composition(
            primary_strategy="vertical_blocking",
            symmetry_score=0.74,
            depth_staging="deep_focus",
        ),
        camera_grammar=CameraGrammar(
            static=0.3,
            dolly=0.35,
            handheld=0.15,
            push_in=0.02,
            tracking=0.18,
        ),
        lighting_physics=LightingPhysics(
            key_light="low_key",
            color_temp_range=[3200, 5600],
            contrast_ratio="high",
            shadow_quality="hard",
        ),
        color_science=ColorScience(
            lut_reference="Kodak_2383",
            palette=["desaturated", "green_tint"],
            saturation_level="muted",
            dominant_hue="green",
        ),
        source_video="gs://test-bucket/test-video.mp4",
        analysis_timestamp=datetime.utcnow(),
        confidence=0.85,
    )


@pytest.fixture
def sample_shot_analysis() -> ShotAnalysis:
    """Create a sample shot analysis for testing."""
    return ShotAnalysis(
        shot_number=1,
        start_time=0.0,
        end_time=2.5,
        duration=2.5,
        camera_movement="dolly",
        camera_angle="eye_level",
        shot_size="medium",
        composition_notes="Rule of thirds with subject in left third",
        lighting_style="low_key",
        subjects=["person", "window"],
        action_description="Character walks toward window",
        emotional_tone="tension",
    )


@pytest.fixture
def mock_gemini_response() -> Dict[str, Any]:
    """Mock Gemini API response for video analysis."""
    return {
        "logic_vector": {
            "auteur_id": "bong",
            "cadence": {
                "hook": 0.5,
                "build": 2.0,
                "climax": 5.0,
                "avg_shot_length": 3.2,
                "rhythm_pattern": "slow_build",
                "tempo": "deliberate",
            },
            "composition": {
                "primary_strategy": "vertical_blocking",
                "symmetry_score": 0.74,
            },
            "camera_grammar": {
                "static": 0.3,
                "dolly": 0.35,
                "handheld": 0.15,
                "push_in": 0.02,
            },
            "lighting_physics": {
                "key_light": "low_key",
                "color_temp_range": [3200, 5600],
            },
            "color_science": {
                "lut_reference": "Kodak_2383",
                "palette": ["desaturated", "green_tint"],
            },
        },
        "shots": [
            {
                "shot_number": 1,
                "start_time": 0.0,
                "end_time": 2.5,
                "duration": 2.5,
                "camera_movement": "dolly",
            },
        ],
        "confidence": 0.85,
    }


# =============================================================================
# Schema Tests
# =============================================================================

class TestVPESchemas:
    """Tests for VPE Pydantic schemas."""

    def test_logic_vector_creation(self, sample_logic_vector: LogicVector):
        """Test LogicVector can be created with valid data."""
        assert sample_logic_vector.auteur_id == "bong"
        assert sample_logic_vector.confidence == 0.85
        assert sample_logic_vector.composition.symmetry_score == 0.74

    def test_logic_vector_to_system_prompt(self, sample_logic_vector: LogicVector):
        """Test LogicVector can be converted to system prompt context."""
        context = sample_logic_vector.to_system_prompt_context()
        assert "BONG" in context
        assert "vertical_blocking" in context
        assert "low_key" in context

    def test_camera_grammar_normalization(self):
        """Test CameraGrammar clamps values to 0-1 range."""
        grammar = CameraGrammar(
            static=1.5,  # Should be clamped to 1.0
            dolly=-0.1,  # Should be clamped to 0.0
            handheld=0.5,
        )
        assert grammar.static == 1.0
        assert grammar.dolly == 0.0
        assert grammar.handheld == 0.5

    def test_vpe_parse_request_validation(self):
        """Test VPEParseRequest validates video_uri."""
        # Valid GCS URI
        request = VPEParseRequest(video_uri="gs://bucket/video.mp4")
        assert request.video_uri.startswith("gs://")

        # Valid HTTPS URI
        request = VPEParseRequest(video_uri="https://example.com/video.mp4")
        assert request.video_uri.startswith("https://")

        # Valid YouTube URI
        request = VPEParseRequest(video_uri="https://youtube.com/watch?v=abc123")
        assert "youtube.com" in request.video_uri

        # Invalid URI
        with pytest.raises(ValueError):
            VPEParseRequest(video_uri="invalid-uri")

    def test_vpe_parse_request_defaults(self):
        """Test VPEParseRequest has correct defaults."""
        request = VPEParseRequest(video_uri="gs://bucket/video.mp4")
        assert request.extract_shots is True
        assert request.store_to_qdrant is True
        assert request.max_shots == 50

    def test_shot_analysis_creation(self, sample_shot_analysis: ShotAnalysis):
        """Test ShotAnalysis can be created with valid data."""
        assert sample_shot_analysis.shot_number == 1
        assert sample_shot_analysis.duration == 2.5
        assert "person" in sample_shot_analysis.subjects

    def test_cadence_defaults(self):
        """Test Cadence has correct default values."""
        cadence = Cadence()
        assert cadence.hook == 0.0
        assert cadence.build == 0.0
        assert cadence.tempo is None

    def test_composition_strategy_validation(self):
        """Test Composition accepts valid strategies."""
        comp = Composition(primary_strategy="rule_of_thirds")
        assert comp.primary_strategy == "rule_of_thirds"

    def test_lighting_physics_color_temp(self):
        """Test LightingPhysics color temperature range."""
        lighting = LightingPhysics(color_temp_range=[2700, 6500])
        assert lighting.color_temp_range == [2700, 6500]

    def test_color_science_palette(self):
        """Test ColorScience palette handling."""
        color = ColorScience(palette=["warm", "desaturated", "amber"])
        assert len(color.palette) == 3

    def test_vpe_parse_response_evidence_refs(self):
        """Test VPEParseResponse evidence_refs format."""
        response = VPEParseResponse(
            success=True,
            trace_id="test-trace",
            evidence_refs=["db:vpe_results:123", "db:vpe_vectors:456"],
        )
        assert all(ref.startswith("db:") for ref in response.evidence_refs)


# =============================================================================
# Service Tests (with mocked Gemini)
# =============================================================================

class TestVPEService:
    """Tests for VPE service with mocked Gemini API."""

    @pytest.mark.asyncio
    async def test_parse_video_success(self, mock_gemini_response: Dict):
        """Test successful video parsing."""
        with patch("app.services.vpe_service.VPEService._get_client") as mock_client:
            # Setup mock
            mock_response = MagicMock()
            mock_response.text = json.dumps(mock_gemini_response)

            mock_genai_client = MagicMock()
            mock_genai_client.models.generate_content = MagicMock(return_value=mock_response)
            mock_client.return_value = mock_genai_client

            from app.services.vpe_service import VPEService

            service = VPEService(api_key="test-key")
            service._client = mock_genai_client

            # Mock the async call
            with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
                mock_thread.return_value = mock_response

                result = await service.parse_video(
                    video_uri="gs://test-bucket/video.mp4",
                    auteur_hint="bong",
                )

            assert result.success is True
            assert result.logic_vector is not None
            assert result.logic_vector.auteur_id == "bong"

    @pytest.mark.asyncio
    async def test_parse_video_with_shots(self, mock_gemini_response: Dict):
        """Test video parsing extracts shot analysis."""
        with patch("app.services.vpe_service.VPEService._get_client") as mock_client:
            mock_response = MagicMock()
            mock_response.text = json.dumps(mock_gemini_response)

            mock_genai_client = MagicMock()
            mock_client.return_value = mock_genai_client

            from app.services.vpe_service import VPEService

            service = VPEService(api_key="test-key")
            service._client = mock_genai_client

            with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
                mock_thread.return_value = mock_response

                result = await service.parse_video(
                    video_uri="gs://test-bucket/video.mp4",
                    extract_shots=True,
                )

            assert result.shots is not None
            assert len(result.shots) > 0

    @pytest.mark.asyncio
    async def test_parse_video_error_handling(self):
        """Test error handling when Gemini API fails."""
        from app.services.vpe_service import VPEService

        service = VPEService(api_key="test-key")

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.side_effect = Exception("API Error: RATE_LIMIT")

            result = await service.parse_video(
                video_uri="gs://test-bucket/video.mp4",
            )

            assert result.success is False
            assert result.error is not None
            assert "요청이 너무 많습니다" in result.error or "오류" in result.error

    @pytest.mark.asyncio
    async def test_merge_logic_vectors(self, sample_logic_vector: LogicVector):
        """Test merging multiple Logic Vectors."""
        from app.services.vpe_service import VPEService

        service = VPEService(api_key="test-key")

        # Create a second vector with different values
        vector2 = sample_logic_vector.model_copy()
        vector2.camera_grammar.dolly = 0.5
        vector2.camera_grammar.static = 0.2

        merged = await service.merge_logic_vectors([sample_logic_vector, vector2])

        assert merged.auteur_id == "bong"
        # Check that camera_grammar is averaged
        assert 0.25 <= merged.camera_grammar.static <= 0.3
        assert 0.35 <= merged.camera_grammar.dolly <= 0.5


# =============================================================================
# Storage Tests
# =============================================================================

class TestVPEStorage:
    """Tests for VPE Qdrant storage."""

    @pytest.mark.asyncio
    async def test_store_logic_vector(self, sample_logic_vector: LogicVector):
        """Test storing a Logic Vector to Qdrant."""
        with patch("app.services.vpe_storage.VPEStorage._get_client") as mock_client:
            mock_qdrant = MagicMock()
            mock_qdrant.get_collections.return_value = MagicMock(collections=[])
            mock_qdrant.create_collection = MagicMock()
            mock_qdrant.create_payload_index = MagicMock()
            mock_qdrant.upsert = MagicMock()
            mock_client.return_value = mock_qdrant

            from app.services.vpe_storage import VPEStorage

            storage = VPEStorage(use_hybrid=False)
            storage._available = True

            with patch.object(storage, "_get_embedder") as mock_embedder:
                mock_embedder.return_value.embed_async = AsyncMock(return_value=[0.1] * 384)

                doc_id = await storage.store_logic_vector(sample_logic_vector)

                assert doc_id is not None
                assert "vpe_bong_" in doc_id

    @pytest.mark.asyncio
    async def test_search_by_style(self):
        """Test searching Logic Vectors by style description."""
        with patch("app.services.vpe_storage.VPEStorage._get_client") as mock_client:
            mock_qdrant = MagicMock()
            mock_qdrant.get_collections.return_value = MagicMock(
                collections=[MagicMock(name="vpe_logic_vectors")]
            )

            # Mock search results
            mock_point = MagicMock()
            mock_point.id = "test-doc-id"
            mock_point.score = 0.9
            mock_point.payload = {
                "auteur_id": "bong",
                "logic_vector": {
                    "auteur_id": "bong",
                    "cadence": {},
                    "composition": {},
                    "camera_grammar": {},
                    "lighting_physics": {},
                    "color_science": {},
                },
            }
            mock_qdrant.search.return_value = [mock_point]
            mock_client.return_value = mock_qdrant

            from app.services.vpe_storage import VPEStorage

            storage = VPEStorage(use_hybrid=False)
            storage._available = True

            with patch.object(storage, "_get_embedder") as mock_embedder:
                mock_embedder.return_value.embed_async = AsyncMock(return_value=[0.1] * 384)

                results = await storage.search_by_style(
                    query="dark noir lighting with slow dolly shots",
                    auteur_filter="bong",
                )

                assert len(results) > 0
                assert results[0].logic_vector.auteur_id == "bong"

    @pytest.mark.asyncio
    async def test_storage_graceful_degradation(self):
        """Test storage gracefully handles Qdrant unavailable."""
        from app.services.vpe_storage import VPEStorage

        storage = VPEStorage()
        storage._available = False
        storage._client = None

        # Should return None instead of raising
        doc_id = await storage.store_logic_vector(
            LogicVector(auteur_id="test")
        )
        assert doc_id is None

        # Search should return empty list
        results = await storage.search_by_style("test query")
        assert results == []


# =============================================================================
# Router Tests
# =============================================================================

class TestVPERouter:
    """Tests for VPE API endpoints."""

    @pytest.mark.asyncio
    async def test_parse_endpoint_success(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
        mock_gemini_response: Dict,
    ):
        """Test /api/vpe/parse endpoint success."""
        with patch("app.routers.vpe.get_vpe_service") as mock_service:
            mock_svc = AsyncMock()
            mock_svc.parse_video = AsyncMock(return_value=VPEParseResponse(
                success=True,
                trace_id="test-trace",
                logic_vector=LogicVector(auteur_id="bong"),
                confidence=0.85,
            ))
            mock_service.return_value = mock_svc

            with patch("app.routers.vpe.get_or_create_user_credits") as mock_credits:
                mock_credits.return_value = MagicMock(balance=1000)

                with patch("app.routers.vpe.deduct_credits", new_callable=AsyncMock):
                    response = await async_client.post(
                        "/api/vpe/parse",
                        json={
                            "video_uri": "gs://test-bucket/video.mp4",
                            "auteur_hint": "bong",
                        },
                        headers=auth_headers,
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["logic_vector"]["auteur_id"] == "bong"

    @pytest.mark.asyncio
    async def test_parse_endpoint_insufficient_credits(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/vpe/parse returns 402 when credits insufficient."""
        with patch("app.routers.vpe.get_or_create_user_credits") as mock_credits:
            mock_credits.return_value = MagicMock(balance=10)  # Less than 50

            response = await async_client.post(
                "/api/vpe/parse",
                json={"video_uri": "gs://test-bucket/video.mp4"},
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED
        data = response.json()
        assert data["detail"]["code"] == "INSUFFICIENT_CREDITS"

    @pytest.mark.asyncio
    async def test_parse_endpoint_invalid_uri(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/vpe/parse validates video_uri."""
        response = await async_client.post(
            "/api/vpe/parse",
            json={"video_uri": "invalid-uri"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_query_endpoint(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/vpe/query endpoint."""
        with patch("app.routers.vpe.get_vpe_storage") as mock_storage:
            mock_store = MagicMock()
            mock_store.search_by_style = AsyncMock(return_value=[])
            mock_storage.return_value = mock_store

            response = await async_client.post(
                "/api/vpe/query",
                json={
                    "query": "dark noir cinematography",
                    "auteur_filter": "nolan",
                    "top_k": 5,
                },
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_get_vectors_by_auteur(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/vpe/vectors/{auteur_id} endpoint."""
        with patch("app.routers.vpe.get_vpe_storage") as mock_storage:
            mock_store = MagicMock()
            mock_store.get_by_auteur = AsyncMock(return_value=[])
            mock_storage.return_value = mock_store

            response = await async_client.get(
                "/api/vpe/vectors/bong",
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["auteur_id"] == "bong"

    @pytest.mark.asyncio
    async def test_delete_vector(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test DELETE /api/vpe/vectors/{doc_id} endpoint."""
        with patch("app.routers.vpe.get_vpe_storage") as mock_storage:
            mock_store = MagicMock()
            mock_store.delete_logic_vector = AsyncMock(return_value=True)
            mock_storage.return_value = mock_store

            response = await async_client.delete(
                "/api/vpe/vectors/test-doc-id",
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test /api/vpe/health endpoint."""
        with patch("app.routers.vpe.get_vpe_storage") as mock_storage:
            mock_store = MagicMock()
            mock_store.ensure_collection = AsyncMock(return_value=True)
            mock_storage.return_value = mock_store

            response = await async_client.get("/api/vpe/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["service"] == "vpe"


# =============================================================================
# Integration Tests
# =============================================================================

class TestVPEIntegration:
    """Integration tests for VPE full flow."""

    @pytest.mark.asyncio
    async def test_full_parse_and_store_flow(self, sample_logic_vector: LogicVector):
        """Test complete flow: parse video -> store Logic Vector -> query."""
        # This would be a longer integration test with real services
        # For now, we test the schema serialization round-trip
        json_data = sample_logic_vector.model_dump_json()
        restored = LogicVector.model_validate_json(json_data)

        assert restored.auteur_id == sample_logic_vector.auteur_id
        assert restored.confidence == sample_logic_vector.confidence
        assert restored.camera_grammar.dolly == sample_logic_vector.camera_grammar.dolly

    def test_logic_vector_system_prompt_generation(self, sample_logic_vector: LogicVector):
        """Test Logic Vector generates valid system prompt context."""
        context = sample_logic_vector.to_system_prompt_context()

        # Should contain key information
        assert "BONG" in context
        assert "Camera Movement" in context
        assert "Lighting" in context
        assert "Composition" in context


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestVPEErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_json_parse_error_handling(self):
        """Test handling of malformed JSON response."""
        from app.services.vpe_service import VPEService

        service = VPEService(api_key="test-key")

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_response = MagicMock()
            mock_response.text = "invalid json {{"
            mock_thread.return_value = mock_response

            result = await service.parse_video(
                video_uri="gs://test-bucket/video.mp4",
            )

            assert result.success is False
            assert "오류" in result.error

    def test_video_uri_validation_edge_cases(self):
        """Test video URI validation edge cases."""
        # Empty URI
        with pytest.raises(ValueError):
            VPEParseRequest(video_uri="")

        # Whitespace only
        with pytest.raises(ValueError):
            VPEParseRequest(video_uri="   ")

        # Short GCS URI
        with pytest.raises(ValueError):
            VPEParseRequest(video_uri="gs://")

    def test_max_shots_boundary(self):
        """Test max_shots parameter boundaries."""
        # Valid boundary
        request = VPEParseRequest(
            video_uri="gs://bucket/video.mp4",
            max_shots=200,
        )
        assert request.max_shots == 200

        # Invalid: too high
        with pytest.raises(ValueError):
            VPEParseRequest(
                video_uri="gs://bucket/video.mp4",
                max_shots=201,
            )

        # Invalid: too low
        with pytest.raises(ValueError):
            VPEParseRequest(
                video_uri="gs://bucket/video.mp4",
                max_shots=0,
            )
