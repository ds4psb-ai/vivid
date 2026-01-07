"""Veo 3.1 Video Generation Service with Async Polling.

Provides async video generation using Google's Veo 3.1 API with:
- Async job submission
- Exponential backoff polling
- Credit integration
- Timeout handling

Based on Google GenAI Veo 3.1 API (2025).
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

class VeoModel(str, Enum):
    """Available Veo models."""
    VEO_3_1_GENERATE = "veo-3.1-generate-preview"
    VEO_3_1_FAST = "veo-3.1-fast-generate-preview"


# Credit costs per model
VEO_CREDIT_COSTS = {
    VeoModel.VEO_3_1_GENERATE.value: 200,  # 8 seconds, with audio
    VeoModel.VEO_3_1_FAST.value: 60,       # 8 seconds, fast generation
}

# Polling configuration
DEFAULT_MAX_WAIT_SECONDS = 360  # 6 minutes max wait
DEFAULT_POLL_INTERVAL = 10     # Start with 10 seconds
MAX_POLL_INTERVAL = 30         # Cap at 30 seconds
POLL_BACKOFF_FACTOR = 1.2      # Exponential backoff factor


@dataclass
class VeoConfig:
    """Configuration for Veo video generation."""
    prompt: str
    model: str = VeoModel.VEO_3_1_GENERATE.value
    duration_seconds: int = 8
    aspect_ratio: str = "16:9"
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None

    # Audio options (Veo 3.1 feature)
    include_audio: bool = True

    # Safety settings
    person_generation: str = "dont_allow"  # "allow_adult" or "dont_allow"


@dataclass
class VeoResult:
    """Result from Veo video generation."""
    success: bool
    video_uri: Optional[str] = None
    error: Optional[str] = None
    duration_ms: int = 0
    model: str = ""
    credit_cost: int = 0
    metadata: Optional[Dict[str, Any]] = None


class VeoServiceError(Exception):
    """Base exception for Veo service errors."""
    pass


class VeoTimeoutError(VeoServiceError):
    """Raised when video generation times out."""
    pass


class VeoGenerationError(VeoServiceError):
    """Raised when video generation fails."""
    pass


# =============================================================================
# Veo Service
# =============================================================================

class VeoService:
    """Async Veo 3.1 video generation service with polling."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Veo service.

        Args:
            api_key: Optional API key. Uses settings.GEMINI_API_KEY if not provided.
        """
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._client = None

    def _get_client(self):
        """Get or create the GenAI client."""
        if self._client is None:
            from google import genai
            if not self._api_key:
                raise VeoServiceError("No API key available. Configure GEMINI_API_KEY.")
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def generate_video(
        self,
        config: VeoConfig,
        max_wait_seconds: int = DEFAULT_MAX_WAIT_SECONDS,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ) -> VeoResult:
        """Generate video using Veo 3.1 with async polling.

        Submits a video generation job and polls until completion or timeout.
        Uses exponential backoff for polling to reduce API load.

        Args:
            config: VeoConfig with generation parameters
            max_wait_seconds: Maximum time to wait for completion (default 360s)
            poll_interval: Initial polling interval in seconds (default 10s)

        Returns:
            VeoResult with video URI or error

        Raises:
            VeoTimeoutError: If generation times out
            VeoGenerationError: If generation fails
            VeoServiceError: For other errors
        """
        from google.genai import types

        start_time = time.monotonic()
        client = self._get_client()

        # Validate model
        model = config.model
        if model not in VEO_CREDIT_COSTS:
            model = VeoModel.VEO_3_1_GENERATE.value

        credit_cost = VEO_CREDIT_COSTS.get(model, 200)

        logger.info(f"Starting Veo generation: model={model}, duration={config.duration_seconds}s")

        try:
            # Build generation config
            generate_config = {
                "prompt": config.prompt,
                "duration_seconds": config.duration_seconds,
                "aspect_ratio": config.aspect_ratio,
                "person_generation": config.person_generation,
            }

            if config.negative_prompt:
                generate_config["negative_prompt"] = config.negative_prompt
            if config.seed is not None:
                generate_config["seed"] = config.seed
            if config.include_audio and "3.1" in model:
                generate_config["include_audio"] = True

            # Submit async generation job
            # Note: Using aio for async operation
            operation = await asyncio.to_thread(
                client.models.generate_videos,
                model=model,
                prompt=config.prompt,
                config=types.GenerateVideosConfig(**{
                    k: v for k, v in generate_config.items() if k != "prompt"
                }),
            )

            # Poll for completion with exponential backoff
            elapsed = 0
            current_interval = poll_interval

            while elapsed < max_wait_seconds:
                # Check if operation is done
                if hasattr(operation, 'done') and operation.done:
                    break

                # Wait before next poll
                await asyncio.sleep(current_interval)
                elapsed = time.monotonic() - start_time

                # Refresh operation status
                try:
                    if hasattr(operation, 'name'):
                        operation = await asyncio.to_thread(
                            client.operations.get,
                            operation=operation,
                        )
                except Exception as e:
                    logger.warning(f"Failed to get operation status: {e}")

                # Exponential backoff
                current_interval = min(current_interval * POLL_BACKOFF_FACTOR, MAX_POLL_INTERVAL)
                logger.debug(f"Polling Veo job, elapsed={elapsed:.1f}s, next_poll={current_interval:.1f}s")

            duration_ms = int((time.monotonic() - start_time) * 1000)

            # Check for timeout
            if elapsed >= max_wait_seconds:
                logger.error(f"Veo generation timed out after {max_wait_seconds}s")
                return VeoResult(
                    success=False,
                    error=f"Video generation timed out after {max_wait_seconds} seconds",
                    duration_ms=duration_ms,
                    model=model,
                    credit_cost=0,  # No charge on timeout
                )

            # Extract result
            if hasattr(operation, 'result') and operation.result:
                result = operation.result
                videos = getattr(result, 'generated_videos', [])

                if videos and len(videos) > 0:
                    video = videos[0]
                    video_uri = getattr(video, 'uri', None)

                    if video_uri:
                        logger.info(f"Veo generation completed in {duration_ms}ms")
                        return VeoResult(
                            success=True,
                            video_uri=video_uri,
                            duration_ms=duration_ms,
                            model=model,
                            credit_cost=credit_cost,
                            metadata={
                                "duration_seconds": config.duration_seconds,
                                "aspect_ratio": config.aspect_ratio,
                                "include_audio": config.include_audio,
                            },
                        )

            # Check for error
            if hasattr(operation, 'error') and operation.error:
                error_msg = str(operation.error)
                logger.error(f"Veo generation failed: {error_msg}")
                return VeoResult(
                    success=False,
                    error=f"Video generation failed: {error_msg}",
                    duration_ms=duration_ms,
                    model=model,
                    credit_cost=0,  # No charge on error
                )

            # Unknown state
            return VeoResult(
                success=False,
                error="Video generation completed but no video was returned",
                duration_ms=duration_ms,
                model=model,
                credit_cost=0,
            )

        except Exception as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.exception(f"Veo generation error: {e}")
            return VeoResult(
                success=False,
                error=f"Video generation error: {type(e).__name__}: {str(e)}",
                duration_ms=duration_ms,
                model=model,
                credit_cost=0,
            )

    async def generate_video_simple(
        self,
        prompt: str,
        model: str = VeoModel.VEO_3_1_GENERATE.value,
        duration_seconds: int = 8,
        aspect_ratio: str = "16:9",
        include_audio: bool = True,
    ) -> VeoResult:
        """Simplified video generation with common defaults.

        Args:
            prompt: Video generation prompt
            model: Veo model to use
            duration_seconds: Video duration (4, 6, or 8)
            aspect_ratio: Video aspect ratio
            include_audio: Whether to include audio (Veo 3.1)

        Returns:
            VeoResult with video URI or error
        """
        config = VeoConfig(
            prompt=prompt,
            model=model,
            duration_seconds=duration_seconds,
            aspect_ratio=aspect_ratio,
            include_audio=include_audio,
        )
        return await self.generate_video(config)


# =============================================================================
# Module-level convenience functions
# =============================================================================

_default_service: Optional[VeoService] = None


def get_veo_service(api_key: Optional[str] = None) -> VeoService:
    """Get or create the default Veo service instance.

    Args:
        api_key: Optional API key override

    Returns:
        VeoService instance
    """
    global _default_service
    if api_key:
        return VeoService(api_key=api_key)
    if _default_service is None:
        _default_service = VeoService()
    return _default_service


async def generate_video(
    prompt: str,
    model: str = VeoModel.VEO_3_1_GENERATE.value,
    duration_seconds: int = 8,
    aspect_ratio: str = "16:9",
    include_audio: bool = True,
    api_key: Optional[str] = None,
) -> VeoResult:
    """Convenience function for video generation.

    Args:
        prompt: Video generation prompt
        model: Veo model to use
        duration_seconds: Video duration
        aspect_ratio: Video aspect ratio
        include_audio: Whether to include audio
        api_key: Optional API key override

    Returns:
        VeoResult with video URI or error
    """
    service = get_veo_service(api_key)
    return await service.generate_video_simple(
        prompt=prompt,
        model=model,
        duration_seconds=duration_seconds,
        aspect_ratio=aspect_ratio,
        include_audio=include_audio,
    )
