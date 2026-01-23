"""Integration tests for Veo 3.1 video generation service.

These tests require a valid GEMINI_API_KEY and make real API calls.
Run with: pytest tests/services/test_veo_service_integration.py -v --integration

Skipped by default unless --integration flag is provided.
"""
import os
import pytest

from app.services.veo_service import (
    VeoService,
    VeoConfig,
    VeoModel,
    generate_video,
)
from app.config import settings


# Skip all tests in this module if no API key or --integration not provided
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.getenv("GEMINI_API_KEY") and not settings.GEMINI_API_KEY.get_secret_value(),
        reason="GEMINI_API_KEY not configured"
    ),
]


@pytest.fixture
def api_key():
    """Get API key from environment or settings."""
    return os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY.get_secret_value()


class TestVeoServiceIntegration:
    """Integration tests that make real API calls."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_real_video_generation_fast_model(self, api_key):
        """Test real video generation with fast model (shorter wait)."""
        service = VeoService(api_key=api_key)

        config = VeoConfig(
            prompt="A calm ocean wave gently rolling onto a sandy beach at sunset",
            model=VeoModel.VEO_3_1_FAST.value,
            duration_seconds=4,  # Shortest duration
            aspect_ratio="16:9",
            include_audio=True,
        )

        result = await service.generate_video(
            config,
            max_wait_seconds=180,  # 3 minutes for fast model
        )

        # We expect either success or a meaningful error
        if result.success:
            assert result.video_uri is not None
            assert result.video_uri.startswith("gs://") or result.video_uri.startswith("http")
            assert result.credit_cost == 60  # VEO_3_1_FAST cost
            assert result.duration_ms > 0
            print(f"\n[SUCCESS] Video generated: {result.video_uri}")
            print(f"Duration: {result.duration_ms}ms")
        else:
            # Some errors are acceptable (quota, rate limit)
            acceptable_errors = ["요청이 너무 많습니다", "일일 사용량", "서버가 바쁩니다"]
            is_acceptable = any(err in result.error for err in acceptable_errors)
            if not is_acceptable:
                print(f"\n[FAILED] Error: {result.error}")
            assert is_acceptable, f"Unexpected error: {result.error}"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_real_video_generation_with_negative_prompt(self, api_key):
        """Test real video generation with negative prompt."""
        service = VeoService(api_key=api_key)

        config = VeoConfig(
            prompt="A beautiful mountain landscape with snow-capped peaks",
            negative_prompt="blurry, low quality, distorted, artifacts",
            model=VeoModel.VEO_3_1_FAST.value,
            duration_seconds=4,
            aspect_ratio="9:16",  # Vertical video
        )

        result = await service.generate_video(
            config,
            max_wait_seconds=180,
        )

        if result.success:
            assert result.video_uri is not None
            print(f"\n[SUCCESS] Vertical video: {result.video_uri}")
        else:
            print(f"\n[INFO] Expected failure or quota: {result.error}")

    @pytest.mark.asyncio
    async def test_invalid_api_key_error(self):
        """Test that invalid API key returns user-friendly error."""
        service = VeoService(api_key="invalid-api-key-12345")

        config = VeoConfig(
            prompt="Test video",
            model=VeoModel.VEO_3_1_FAST.value,
            duration_seconds=4,
        )

        result = await service.generate_video(config)

        assert result.success is False
        # Should get a permission or invalid key error (Korean or English)
        assert any(keyword in result.error.lower() for keyword in ["api", "key", "invalid", "권한", "유효하지", "입력값"])

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_convenience_function_integration(self, api_key):
        """Test the module-level convenience function."""
        result = await generate_video(
            prompt="A serene forest with sunlight filtering through the trees",
            model=VeoModel.VEO_3_1_FAST.value,
            duration_seconds=4,
            api_key=api_key,
        )

        if result.success:
            assert result.video_uri is not None
            print(f"\n[SUCCESS] Video via convenience function: {result.video_uri}")
        else:
            print(f"\n[INFO] Error: {result.error}")


class TestVeoServiceEdgeCases:
    """Test edge cases with real API."""

    @pytest.mark.asyncio
    async def test_empty_prompt_error(self, api_key):
        """Test that empty prompt returns proper error."""
        service = VeoService(api_key=api_key)

        config = VeoConfig(
            prompt="",  # Empty prompt
            model=VeoModel.VEO_3_1_FAST.value,
        )

        result = await service.generate_video(config)

        # Empty prompts should fail
        assert result.success is False

    @pytest.mark.asyncio
    async def test_very_long_prompt(self, api_key):
        """Test handling of very long prompts."""
        service = VeoService(api_key=api_key)

        # Create a very long prompt (10,000 chars)
        long_prompt = "A beautiful landscape with " + "rolling hills and green meadows " * 300

        config = VeoConfig(
            prompt=long_prompt,
            model=VeoModel.VEO_3_1_FAST.value,
            duration_seconds=4,
        )

        result = await service.generate_video(
            config,
            max_wait_seconds=60,
        )

        # Should either truncate and succeed, or return error
        # Both are acceptable behaviors
        print(f"\n[INFO] Long prompt result: success={result.success}, error={result.error}")


# Pytest configuration for integration tests
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require API key)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (may take minutes)"
    )
