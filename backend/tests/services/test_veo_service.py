"""Unit tests for Veo 3.1 video generation service.

Tests cover:
- Successful video generation
- Timeout handling
- Retry logic on retryable errors
- Error handling for non-retryable errors
"""
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Mock google.genai before importing veo_service
mock_genai = MagicMock()
mock_types = MagicMock()
mock_genai.types = mock_types
sys.modules['google'] = MagicMock()
sys.modules['google.genai'] = mock_genai
sys.modules['google.genai.types'] = mock_types

from app.services.veo_service import (
    VeoService,
    VeoConfig,
    VeoResult,
    VeoModel,
    VeoTimeoutError,
    VeoGenerationError,
    MAX_RETRIES,
    RETRY_DELAYS,
    RETRYABLE_ERRORS,
)


@pytest.fixture
def veo_config():
    """Default VeoConfig for testing."""
    return VeoConfig(
        prompt="A serene mountain landscape at sunset",
        model=VeoModel.VEO_3_1_GENERATE.value,
        duration_seconds=8,
        aspect_ratio="16:9",
    )


@pytest.fixture
def mock_operation_success():
    """Mock successful operation result."""
    mock_video = MagicMock()
    mock_video.uri = "gs://bucket/video.mp4"

    mock_result = MagicMock()
    mock_result.generated_videos = [mock_video]

    mock_op = MagicMock()
    mock_op.done = True
    mock_op.result = mock_result
    mock_op.error = None

    return mock_op


@pytest.fixture
def mock_operation_pending():
    """Mock pending operation (not done)."""
    mock_op = MagicMock()
    mock_op.done = False
    mock_op.name = "operations/test-operation"
    mock_op.result = None
    mock_op.error = None
    return mock_op


class TestVeoServiceSuccess:
    """Tests for successful video generation."""

    @pytest.mark.asyncio
    async def test_generate_video_success(self, veo_config, mock_operation_success):
        """Successful video generation returns correct result."""
        with patch.object(VeoService, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_videos.return_value = mock_operation_success
            mock_get_client.return_value = mock_client

            service = VeoService(api_key="test-key")
            result = await service.generate_video(veo_config)

            assert result.success is True
            assert "video.mp4" in result.video_uri
            assert result.credit_cost == 200  # VEO_3_1_GENERATE cost
            assert result.error is None

    @pytest.mark.asyncio
    async def test_generate_video_with_fast_model(self, mock_operation_success):
        """Fast model returns correct credit cost."""
        config = VeoConfig(
            prompt="Test video",
            model=VeoModel.VEO_3_1_FAST.value,
        )

        with patch.object(VeoService, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_videos.return_value = mock_operation_success
            mock_get_client.return_value = mock_client

            service = VeoService(api_key="test-key")
            result = await service.generate_video(config)

            assert result.success is True
            assert result.credit_cost == 60  # VEO_3_1_FAST cost


class TestVeoServiceTimeout:
    """Tests for timeout handling."""

    @pytest.mark.asyncio
    async def test_generate_video_timeout(self, veo_config, mock_operation_pending):
        """Timeout returns failure with no credit charge."""
        with patch.object(VeoService, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_videos.return_value = mock_operation_pending
            mock_client.operations.get.return_value = mock_operation_pending
            mock_get_client.return_value = mock_client

            service = VeoService(api_key="test-key")
            result = await service.generate_video(
                veo_config,
                max_wait_seconds=1,  # Very short timeout
                poll_interval=0.5,
            )

            assert result.success is False
            assert "timed out" in result.error.lower()
            assert result.credit_cost == 0  # No charge on timeout


class TestVeoServiceRetry:
    """Tests for retry logic on API errors."""

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, veo_config, mock_operation_success):
        """Retries on RATE_LIMIT error and succeeds."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("RATE_LIMIT_EXCEEDED: Too many requests")
            return mock_operation_success

        with patch.object(VeoService, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_videos.side_effect = side_effect
            mock_get_client.return_value = mock_client

            service = VeoService(api_key="test-key")

            # Patch sleep to avoid waiting
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await service.generate_video(veo_config)

            assert result.success is True
            assert call_count == 2  # First failed, second succeeded

    @pytest.mark.asyncio
    async def test_retry_on_unavailable(self, veo_config, mock_operation_success):
        """Retries on UNAVAILABLE error and succeeds."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Service UNAVAILABLE")
            return mock_operation_success

        with patch.object(VeoService, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_videos.side_effect = side_effect
            mock_get_client.return_value = mock_client

            service = VeoService(api_key="test-key")

            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await service.generate_video(veo_config)

            assert result.success is True
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_non_retryable_error(self, veo_config):
        """Non-retryable errors fail immediately."""
        with patch.object(VeoService, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_videos.side_effect = Exception("INVALID_ARGUMENT: Bad prompt")
            mock_get_client.return_value = mock_client

            service = VeoService(api_key="test-key")
            result = await service.generate_video(veo_config)

            assert result.success is False
            assert "INVALID_ARGUMENT" in result.error
            # Should have tried only once (no retries for non-retryable errors)
            assert mock_client.models.generate_videos.call_count == 1

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, veo_config):
        """Fails after exhausting all retries."""
        with patch.object(VeoService, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_videos.side_effect = Exception("RATE_LIMIT: Always failing")
            mock_get_client.return_value = mock_client

            service = VeoService(api_key="test-key")

            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await service.generate_video(veo_config)

            assert result.success is False
            assert "RATE_LIMIT" in result.error
            assert mock_client.models.generate_videos.call_count == MAX_RETRIES


class TestVeoServiceErrorHandling:
    """Tests for various error conditions."""

    @pytest.mark.asyncio
    async def test_operation_error_result(self, veo_config):
        """Handles operation error result correctly."""
        mock_op = MagicMock()
        mock_op.done = True
        mock_op.result = None
        mock_op.error = "Generation failed: Content policy violation"

        with patch.object(VeoService, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_videos.return_value = mock_op
            mock_get_client.return_value = mock_client

            service = VeoService(api_key="test-key")
            result = await service.generate_video(veo_config)

            assert result.success is False
            assert "Content policy violation" in result.error
            assert result.credit_cost == 0

    @pytest.mark.asyncio
    async def test_no_video_returned(self, veo_config):
        """Handles empty video list correctly."""
        mock_result = MagicMock()
        mock_result.generated_videos = []

        mock_op = MagicMock()
        mock_op.done = True
        mock_op.result = mock_result
        mock_op.error = None

        with patch.object(VeoService, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_videos.return_value = mock_op
            mock_get_client.return_value = mock_client

            service = VeoService(api_key="test-key")
            result = await service.generate_video(veo_config)

            assert result.success is False
            assert "no video was returned" in result.error.lower()

    @pytest.mark.asyncio
    async def test_invalid_model_falls_back(self):
        """Invalid model falls back to default."""
        config = VeoConfig(
            prompt="Test video",
            model="invalid-model-name",
        )

        mock_video = MagicMock()
        mock_video.uri = "gs://bucket/video.mp4"
        mock_result = MagicMock()
        mock_result.generated_videos = [mock_video]
        mock_op = MagicMock()
        mock_op.done = True
        mock_op.result = mock_result
        mock_op.error = None

        with patch.object(VeoService, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_videos.return_value = mock_op
            mock_get_client.return_value = mock_client

            service = VeoService(api_key="test-key")
            result = await service.generate_video(config)

            assert result.success is True
            # Should use default model
            assert result.model == VeoModel.VEO_3_1_GENERATE.value


class TestVeoServiceConvenienceFunctions:
    """Tests for module-level convenience functions."""

    @pytest.mark.asyncio
    async def test_generate_video_function(self, mock_operation_success):
        """Module-level generate_video function works correctly."""
        from app.services.veo_service import generate_video

        with patch.object(VeoService, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_videos.return_value = mock_operation_success
            mock_get_client.return_value = mock_client

            result = await generate_video(
                prompt="Test video",
                api_key="test-key",
            )

            assert result.success is True
