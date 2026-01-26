"""Tests for Production Bridge Router and Service.

Comprehensive test suite covering:
- Provider interface and base classes
- VEO, Kling, Suno providers
- Production Bridge service orchestration
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

from app.routers.production.providers.base import (
    BaseProvider,
    MediaType,
    ProviderStatus,
    GenerationRequest,
    GenerationProgress,
    GenerationResult,
    ProviderCapabilities,
    ProviderRegistry,
    get_provider_registry,
)
from app.routers.production.providers.veo import VeoProvider
from app.routers.production.providers.kling import KlingProvider
from app.routers.production.providers.suno import SunoProvider
from app.services.production_bridge_service import (
    ProductionBridgeService,
    ProductionBridgeResult,
    ProductionJob,
    get_production_bridge_service,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_generation_request() -> GenerationRequest:
    """Create a mock generation request."""
    return GenerationRequest(
        prompt="A cinematic shot of a sunset over mountains",
        negative_prompt="blurry, distorted",
        media_type=MediaType.VIDEO,
        duration_seconds=8,
        aspect_ratio="16:9",
        resolution="1080p",
        system_prompt="Following the visual style of Bong Joon-ho.",
        style="cinematic",
        include_audio=True,
    )


@pytest.fixture
def mock_audio_request() -> GenerationRequest:
    """Create a mock audio generation request."""
    return GenerationRequest(
        prompt="Epic orchestral music with dramatic tension",
        media_type=MediaType.AUDIO,
        duration_seconds=30,
        audio_style="orchestral",
    )


@pytest.fixture
def mock_generation_result() -> GenerationResult:
    """Create a mock generation result."""
    return GenerationResult(
        success=True,
        provider="veo",
        media_type=MediaType.VIDEO,
        media_uri="gs://bucket/video.mp4",
        trace_id="test-trace-123",
        duration_ms=45000,
        credits_used=200,
        evidence_refs=["db:production:veo:test-trace-123"],
        metadata={"model": "veo-3.1-generate-preview"},
    )


# =============================================================================
# Provider Base Tests
# =============================================================================

class TestProviderBase:
    """Tests for provider base classes."""

    def test_media_type_enum(self):
        """Test MediaType enum values."""
        assert MediaType.VIDEO.value == "video"
        assert MediaType.AUDIO.value == "audio"
        assert MediaType.IMAGE.value == "image"

    def test_provider_status_enum(self):
        """Test ProviderStatus enum values."""
        assert ProviderStatus.PENDING.value == "pending"
        assert ProviderStatus.PROCESSING.value == "processing"
        assert ProviderStatus.COMPLETED.value == "completed"
        assert ProviderStatus.FAILED.value == "failed"

    def test_generation_request_defaults(self):
        """Test GenerationRequest default values."""
        request = GenerationRequest(prompt="test")
        assert request.media_type == MediaType.VIDEO
        assert request.aspect_ratio == "16:9"
        assert request.resolution == "1080p"
        assert request.include_audio is True

    def test_generation_result_defaults(self):
        """Test GenerationResult default values."""
        result = GenerationResult(success=True, provider="test")
        assert result.media_type == MediaType.VIDEO
        assert result.credits_used == 0
        assert result.evidence_refs == []

    def test_provider_capabilities(self):
        """Test ProviderCapabilities dataclass."""
        caps = ProviderCapabilities(
            name="test",
            display_name="Test Provider",
            media_types=[MediaType.VIDEO],
            max_duration_seconds=60,
            supports_audio=True,
        )
        assert caps.name == "test"
        assert MediaType.VIDEO in caps.media_types
        assert caps.supports_audio is True

    def test_provider_registry(self):
        """Test ProviderRegistry."""
        registry = ProviderRegistry()

        # Create mock provider
        mock_provider = MagicMock(spec=BaseProvider)
        mock_provider.name = "test_provider"
        mock_provider.media_types = [MediaType.VIDEO]

        # Register
        registry.register(mock_provider)

        # Get
        assert registry.get("test_provider") == mock_provider
        assert registry.get("nonexistent") is None

        # List
        assert "test_provider" in registry.list_providers()


# =============================================================================
# VEO Provider Tests
# =============================================================================

class TestVeoProvider:
    """Tests for VEO provider."""

    def test_provider_properties(self):
        """Test VEO provider properties."""
        provider = VeoProvider()
        assert provider.name == "veo"
        assert provider.display_name == "Google VEO 3.1"
        assert MediaType.VIDEO in provider.media_types

    def test_capabilities(self):
        """Test VEO capabilities."""
        provider = VeoProvider()
        caps = provider.get_capabilities()

        assert caps.name == "veo"
        assert caps.max_duration_seconds == 8
        assert caps.supports_audio is True
        assert "16:9" in caps.supported_aspect_ratios
        assert "veo-3.1-generate-preview" in caps.available_models

    def test_calculate_credits(self, mock_generation_request: GenerationRequest):
        """Test VEO credit calculation."""
        provider = VeoProvider()

        # Default model
        credits = provider.calculate_credits(mock_generation_request)
        assert credits == 200

        # Fast model
        mock_generation_request.model = "veo-3.1-fast-generate-preview"
        credits = provider.calculate_credits(mock_generation_request)
        assert credits == 60

    def test_validate_request(self, mock_generation_request: GenerationRequest):
        """Test VEO request validation."""
        provider = VeoProvider()

        # Valid request
        error = provider.validate_request(mock_generation_request)
        assert error is None

        # Invalid media type
        mock_generation_request.media_type = MediaType.AUDIO
        error = provider.validate_request(mock_generation_request)
        assert error is not None

    @pytest.mark.asyncio
    async def test_generate_validation_error(self):
        """Test VEO generation with validation error."""
        provider = VeoProvider()
        request = GenerationRequest(prompt="ab", media_type=MediaType.VIDEO)  # Too short

        result = await provider.generate(request)
        assert result.success is False
        assert result.error_code == "VALIDATION_ERROR"


# =============================================================================
# Kling Provider Tests
# =============================================================================

class TestKlingProvider:
    """Tests for Kling provider."""

    def test_provider_properties(self):
        """Test Kling provider properties."""
        provider = KlingProvider()
        assert provider.name == "kling"
        assert provider.display_name == "Kling 2.6"
        assert MediaType.VIDEO in provider.media_types

    def test_capabilities(self):
        """Test Kling capabilities."""
        provider = KlingProvider()
        caps = provider.get_capabilities()

        assert caps.name == "kling"
        assert caps.max_duration_seconds == 10
        assert caps.supports_audio is True
        assert caps.supports_reference_images is True
        assert "kling-v2.6" in caps.available_models

    def test_calculate_credits(self, mock_generation_request: GenerationRequest):
        """Test Kling credit calculation."""
        provider = KlingProvider()

        # 5 second video
        mock_generation_request.duration_seconds = 5
        credits = provider.calculate_credits(mock_generation_request)
        assert credits == 50

        # 10 second video
        mock_generation_request.duration_seconds = 10
        credits = provider.calculate_credits(mock_generation_request)
        assert credits == 100

    @pytest.mark.asyncio
    async def test_generate_no_api_key(self, mock_generation_request: GenerationRequest):
        """Test Kling generation without API key."""
        provider = KlingProvider(api_key=None)

        result = await provider.generate(mock_generation_request)
        assert result.success is False
        assert result.error_code == "NO_API_KEY"


# =============================================================================
# Suno Provider Tests
# =============================================================================

class TestSunoProvider:
    """Tests for Suno provider."""

    def test_provider_properties(self):
        """Test Suno provider properties."""
        provider = SunoProvider()
        assert provider.name == "suno"
        assert provider.display_name == "Suno AI"
        assert MediaType.AUDIO in provider.media_types

    def test_capabilities(self):
        """Test Suno capabilities."""
        provider = SunoProvider()
        caps = provider.get_capabilities()

        assert caps.name == "suno"
        assert caps.max_duration_seconds == 180
        assert caps.supports_audio is True
        assert "chirp-v3.5" in caps.available_models

    def test_calculate_credits(self, mock_audio_request: GenerationRequest):
        """Test Suno credit calculation."""
        provider = SunoProvider()

        # Default model
        credits = provider.calculate_credits(mock_audio_request)
        assert credits == 30

        # v4 model
        mock_audio_request.model = "chirp-v4"
        credits = provider.calculate_credits(mock_audio_request)
        assert credits == 50

    def test_validate_request(self, mock_audio_request: GenerationRequest):
        """Test Suno request validation."""
        provider = SunoProvider()

        # Valid request
        error = provider.validate_request(mock_audio_request)
        assert error is None

        # Invalid media type
        mock_audio_request.media_type = MediaType.VIDEO
        error = provider.validate_request(mock_audio_request)
        assert error is not None


# =============================================================================
# Production Bridge Service Tests
# =============================================================================

class TestProductionBridgeService:
    """Tests for Production Bridge service."""

    def test_list_providers(self):
        """Test listing providers."""
        service = ProductionBridgeService()
        providers = service.list_providers()

        assert "veo" in providers
        assert "kling" in providers
        assert "suno" in providers

    def test_get_provider(self):
        """Test getting provider."""
        service = ProductionBridgeService()

        veo = service.get_provider("veo")
        assert veo is not None
        assert veo.name == "veo"

        nonexistent = service.get_provider("nonexistent")
        assert nonexistent is None

    def test_get_provider_capabilities(self):
        """Test getting provider capabilities."""
        service = ProductionBridgeService()

        caps = service.get_provider_capabilities("veo")
        assert caps is not None
        assert caps.name == "veo"

        caps = service.get_provider_capabilities("nonexistent")
        assert caps is None

    def test_calculate_credits(self, mock_generation_request: GenerationRequest):
        """Test credit calculation."""
        service = ProductionBridgeService()

        # VEO
        credits = service.calculate_credits("veo", mock_generation_request)
        assert credits == 200

        # Nonexistent provider
        credits = service.calculate_credits("nonexistent", mock_generation_request)
        assert credits == 0

    def test_select_best_provider_video(self, mock_generation_request: GenerationRequest):
        """Test best provider selection for video."""
        service = ProductionBridgeService()

        # Default video
        provider = service.select_best_provider(mock_generation_request)
        assert provider in ["veo", "kling"]

        # Dialogue heavy
        mock_generation_request.prompt = "A person speaking dialogue in a dramatic scene"
        provider = service.select_best_provider(mock_generation_request)
        assert provider == "veo"

        # Close-up
        mock_generation_request.prompt = "Close-up of a face with detailed expression"
        provider = service.select_best_provider(mock_generation_request)
        assert provider == "kling"

    def test_select_best_provider_audio(self, mock_audio_request: GenerationRequest):
        """Test best provider selection for audio."""
        service = ProductionBridgeService()

        provider = service.select_best_provider(mock_audio_request)
        assert provider == "suno"

    @pytest.mark.asyncio
    async def test_generate_provider_not_found(self, mock_generation_request: GenerationRequest):
        """Test generation with nonexistent provider."""
        service = ProductionBridgeService()

        result = await service.generate("nonexistent", mock_generation_request)
        assert result.success is False
        assert result.error_code == "PROVIDER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_generate_with_mock(
        self,
        mock_generation_request: GenerationRequest,
        mock_generation_result: GenerationResult,
    ):
        """Test generation with mocked provider."""
        service = ProductionBridgeService()

        # Mock the VEO provider's generate method
        with patch.object(VeoProvider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_generation_result

            result = await service.generate("veo", mock_generation_request)

            assert result.success is True
            assert result.provider == "veo"
            assert result.media_uri == "gs://bucket/video.mp4"

    @pytest.mark.asyncio
    async def test_generate_auto(
        self,
        mock_generation_request: GenerationRequest,
        mock_generation_result: GenerationResult,
    ):
        """Test auto generation."""
        service = ProductionBridgeService()

        with patch.object(VeoProvider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_generation_result

            result = await service.generate_auto(mock_generation_request)
            assert result.success is True

    @pytest.mark.asyncio
    async def test_generate_multi(
        self,
        mock_generation_request: GenerationRequest,
        mock_generation_result: GenerationResult,
    ):
        """Test multi-provider generation."""
        service = ProductionBridgeService()

        kling_result = GenerationResult(
            success=True,
            provider="kling",
            media_type=MediaType.VIDEO,
            media_uri="https://kling.ai/video.mp4",
            credits_used=50,
        )

        with patch.object(VeoProvider, "generate", new_callable=AsyncMock) as mock_veo:
            mock_veo.return_value = mock_generation_result

            with patch.object(KlingProvider, "generate", new_callable=AsyncMock) as mock_kling:
                mock_kling.return_value = kling_result

                jobs = [
                    {"provider": "veo", "request": mock_generation_request},
                    {"provider": "kling", "request": mock_generation_request},
                ]

                result = await service.generate_multi(jobs, parallel=True)

                assert result.success is True
                assert len(result.jobs) == 2
                assert result.total_credits_used == 250  # 200 + 50


# =============================================================================
# Router Tests
# =============================================================================

class TestProductionBridgeRouter:
    """Tests for Production Bridge API endpoints."""

    @pytest.mark.asyncio
    async def test_generate_endpoint_success(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/production/generate endpoint success."""
        with patch.object(VeoProvider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = GenerationResult(
                success=True,
                provider="veo",
                media_type=MediaType.VIDEO,
                media_uri="gs://bucket/video.mp4",
                trace_id="test-trace",
                credits_used=200,
            )

            with patch("app.routers.production.router.get_or_create_user_credits") as mock_credits:
                mock_credits.return_value = MagicMock(balance=1000)

                with patch("app.routers.production.router.deduct_credits", new_callable=AsyncMock):
                    response = await async_client.post(
                        "/api/production/generate",
                        json={
                            "provider": "veo",
                            "prompt": "A beautiful sunset over mountains",
                            "duration_seconds": 8,
                        },
                        headers=auth_headers,
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["provider"] == "veo"

    @pytest.mark.asyncio
    async def test_generate_endpoint_insufficient_credits(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/production/generate returns 402 when credits insufficient."""
        with patch("app.routers.production.router.get_or_create_user_credits") as mock_credits:
            mock_credits.return_value = MagicMock(balance=10)

            response = await async_client.post(
                "/api/production/generate",
                json={
                    "provider": "veo",
                    "prompt": "A beautiful sunset",
                },
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED

    @pytest.mark.asyncio
    async def test_list_providers(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/production/providers endpoint."""
        response = await async_client.get(
            "/api/production/providers",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "providers" in data
        provider_names = [p["name"] for p in data["providers"]]
        assert "veo" in provider_names

    @pytest.mark.asyncio
    async def test_get_provider_info(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/production/providers/{name} endpoint."""
        response = await async_client.get(
            "/api/production/providers/veo",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "veo"
        assert "video" in data["media_types"]

    @pytest.mark.asyncio
    async def test_get_provider_info_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/production/providers/{name} returns 404 for unknown provider."""
        response = await async_client.get(
            "/api/production/providers/nonexistent",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_calculate_credits(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/production/calculate-credits endpoint."""
        response = await async_client.post(
            "/api/production/calculate-credits",
            json={
                "provider": "veo",
                "prompt": "A test video",
                "duration_seconds": 8,
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["provider"] == "veo"
        assert data["credits"] == 200

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test /api/production/health endpoint."""
        response = await async_client.get("/api/production/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["service"] == "production_bridge"
        assert "providers" in data


# =============================================================================
# Integration Tests
# =============================================================================

class TestProductionBridgeIntegration:
    """Integration tests for Production Bridge."""

    @pytest.mark.asyncio
    async def test_full_video_generation_flow(self, mock_generation_request: GenerationRequest):
        """Test complete video generation flow."""
        with patch.object(VeoProvider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = GenerationResult(
                success=True,
                provider="veo",
                media_type=MediaType.VIDEO,
                media_uri="gs://bucket/video.mp4",
                trace_id="test",
                credits_used=200,
                evidence_refs=["db:production:veo:test"],
            )

            service = ProductionBridgeService()

            # Calculate credits first
            credits = service.calculate_credits("veo", mock_generation_request)
            assert credits == 200

            # Generate
            result = await service.generate("veo", mock_generation_request)

            assert result.success is True
            assert result.media_uri is not None
            assert len(result.evidence_refs) > 0

    @pytest.mark.asyncio
    async def test_story_engine_to_production_flow(self):
        """Test Story Engine → Production Bridge flow."""
        # Simulate system prompt from Story Engine
        system_prompt = """
        Following the visual style of Bong Joon-ho.
        Camera: 35% dolly, 15% handheld
        Lighting: low-key, 3200-4500K
        Composition: vertical_blocking with 0.74 symmetry
        """

        request = GenerationRequest(
            prompt="A man descends into a dark basement, tension building",
            system_prompt=system_prompt,
            media_type=MediaType.VIDEO,
            duration_seconds=8,
        )

        with patch.object(VeoProvider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = GenerationResult(
                success=True,
                provider="veo",
                media_type=MediaType.VIDEO,
                media_uri="gs://bucket/video.mp4",
                credits_used=200,
            )

            service = ProductionBridgeService()
            result = await service.generate("veo", request)

            assert result.success is True
            # Verify system prompt was passed
            call_args = mock_gen.call_args
            assert call_args[0][0].system_prompt == system_prompt

    def test_provider_registry_global(self):
        """Test global provider registry."""
        registry = get_provider_registry()

        # Should have default providers registered
        assert registry.get("veo") is not None
        assert registry.get("kling") is not None
        assert registry.get("suno") is not None


# =============================================================================
# Phase 4.5: Schema Enhancement Tests (Veo 3.1 Features)
# =============================================================================

class TestVeo31SchemaEnhancements:
    """Tests for Veo 3.1 schema enhancements: reference_images, first/last frame control."""

    def test_generation_request_reference_images_field(self):
        """Test GenerationRequest has reference_images field (max 3)."""
        request = GenerationRequest(
            prompt="Test prompt for video generation",
            reference_images=["img1.jpg", "img2.jpg", "img3.jpg"],
        )
        assert len(request.reference_images) == 3
        assert request.reference_images[0] == "img1.jpg"

    def test_generation_request_reference_images_default_empty(self):
        """Test reference_images defaults to empty list."""
        request = GenerationRequest(prompt="Test prompt")
        assert request.reference_images == []

    def test_generation_request_frame_control_fields(self):
        """Test GenerationRequest has first_frame_url and last_frame_url fields."""
        request = GenerationRequest(
            prompt="Smooth transition video",
            first_frame_url="https://example.com/start.jpg",
            last_frame_url="https://example.com/end.jpg",
        )
        assert request.first_frame_url == "https://example.com/start.jpg"
        assert request.last_frame_url == "https://example.com/end.jpg"

    def test_generation_request_backward_compatibility(self):
        """Test backward compatibility with reference_image_url (deprecated)."""
        request = GenerationRequest(
            prompt="Test prompt",
            reference_image_url="https://example.com/old_style.jpg",  # Deprecated field
        )
        assert request.reference_image_url == "https://example.com/old_style.jpg"
        # New field should be empty
        assert request.reference_images == []

    def test_veo_provider_capabilities_reference_images(self):
        """Test VEO provider capabilities include reference_images support."""
        provider = VeoProvider()
        caps = provider.get_capabilities()

        assert caps.supports_reference_images is True
        assert caps.max_reference_images == 3
        assert caps.supports_frame_control is True

    def test_veo_provider_validate_request_reference_images_count(self):
        """Test VEO provider validates max reference images."""
        provider = VeoProvider()

        # Valid: 3 reference images (max allowed)
        valid_request = GenerationRequest(
            prompt="Test video generation",
            reference_images=["img1.jpg", "img2.jpg", "img3.jpg"],
        )
        error = provider.validate_request(valid_request)
        assert error is None

    def test_provider_capabilities_dataclass_new_fields(self):
        """Test ProviderCapabilities has new fields."""
        caps = ProviderCapabilities(
            name="test",
            display_name="Test Provider",
            media_types=[MediaType.VIDEO],
            supports_reference_images=True,
            max_reference_images=3,
            supports_frame_control=True,
        )
        assert caps.max_reference_images == 3
        assert caps.supports_frame_control is True

    @pytest.mark.asyncio
    async def test_veo_generate_with_reference_images(self, mock_generation_request: GenerationRequest):
        """Test VEO generation passes reference images to API."""
        mock_generation_request.reference_images = ["img1.jpg", "img2.jpg"]

        with patch.object(VeoProvider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = GenerationResult(
                success=True,
                provider="veo",
                media_type=MediaType.VIDEO,
                media_uri="gs://bucket/video.mp4",
                metadata={
                    "model": "veo-3.1-generate-preview",
                    "reference_images_count": 2,
                },
            )

            provider = VeoProvider()
            result = await mock_gen(mock_generation_request)

            assert result.success is True
            assert result.metadata.get("reference_images_count") == 2

    @pytest.mark.asyncio
    async def test_veo_generate_with_frame_control(self, mock_generation_request: GenerationRequest):
        """Test VEO generation passes frame control to API."""
        mock_generation_request.first_frame_url = "https://example.com/start.jpg"
        mock_generation_request.last_frame_url = "https://example.com/end.jpg"

        with patch.object(VeoProvider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = GenerationResult(
                success=True,
                provider="veo",
                media_type=MediaType.VIDEO,
                media_uri="gs://bucket/transition.mp4",
                metadata={
                    "model": "veo-3.1-generate-preview",
                    "frame_control": {"first_frame": True, "last_frame": True},
                },
            )

            provider = VeoProvider()
            result = await mock_gen(mock_generation_request)

            assert result.success is True
            assert result.metadata.get("frame_control") == {"first_frame": True, "last_frame": True}


class TestVeo31RouterEnhancements:
    """Tests for Production Bridge router Veo 3.1 enhancements."""

    @pytest.mark.asyncio
    async def test_generate_endpoint_with_reference_images(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/production/generate accepts reference_images."""
        with patch.object(VeoProvider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = GenerationResult(
                success=True,
                provider="veo",
                media_type=MediaType.VIDEO,
                media_uri="gs://bucket/video.mp4",
                trace_id="test-trace",
                credits_used=200,
                metadata={"reference_images_count": 2},
            )

            with patch("app.routers.production.router.get_or_create_user_credits") as mock_credits:
                mock_credits.return_value = MagicMock(balance=1000)

                with patch("app.routers.production.router.deduct_credits", new_callable=AsyncMock):
                    response = await async_client.post(
                        "/api/production/generate",
                        json={
                            "provider": "veo",
                            "prompt": "A beautiful sunset over mountains",
                            "reference_images": ["img1.jpg", "img2.jpg"],
                        },
                        headers=auth_headers,
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["reference_images_count"] == 2

    @pytest.mark.asyncio
    async def test_generate_endpoint_with_frame_control(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/production/generate accepts first/last frame URLs."""
        with patch.object(VeoProvider, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = GenerationResult(
                success=True,
                provider="veo",
                media_type=MediaType.VIDEO,
                media_uri="gs://bucket/transition.mp4",
                trace_id="test-trace",
                credits_used=200,
                metadata={"frame_control": {"first_frame": True, "last_frame": True}},
            )

            with patch("app.routers.production.router.get_or_create_user_credits") as mock_credits:
                mock_credits.return_value = MagicMock(balance=1000)

                with patch("app.routers.production.router.deduct_credits", new_callable=AsyncMock):
                    response = await async_client.post(
                        "/api/production/generate",
                        json={
                            "provider": "veo",
                            "prompt": "Smooth transition between scenes",
                            "first_frame_url": "https://example.com/start.jpg",
                            "last_frame_url": "https://example.com/end.jpg",
                        },
                        headers=auth_headers,
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["frame_control"]["first_frame"] is True
        assert data["metadata"]["frame_control"]["last_frame"] is True

    @pytest.mark.asyncio
    async def test_provider_info_includes_new_capabilities(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test /api/production/providers/veo returns new capability fields."""
        response = await async_client.get(
            "/api/production/providers/veo",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["supports_reference_images"] is True
        assert data["max_reference_images"] == 3
        assert data["supports_frame_control"] is True

    @pytest.mark.asyncio
    async def test_reference_images_validation_max_3(
        self,
        async_client: AsyncClient,
        auth_headers: Dict[str, str],
    ):
        """Test reference_images validation rejects more than 3 images."""
        # Note: The validation happens in the Pydantic model
        response = await async_client.post(
            "/api/production/generate",
            json={
                "provider": "veo",
                "prompt": "Test video",
                "reference_images": ["img1.jpg", "img2.jpg", "img3.jpg", "img4.jpg"],  # 4 > 3 max
            },
            headers=auth_headers,
        )

        # Should return validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
