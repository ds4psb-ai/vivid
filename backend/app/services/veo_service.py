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
from typing import Any, Callable, Dict, List, Optional

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

# Retry configuration for initial API call
MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 30]  # Progressive delays in seconds
RETRYABLE_ERRORS = ["RATE_LIMIT", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "DEADLINE_EXCEEDED"]

# Polling retry configuration
POLL_MAX_RETRIES = 3  # Max consecutive poll failures before giving up
POLL_RETRY_DELAY = 5  # Seconds to wait before retrying a failed poll

# User-friendly error messages (Korean)
ERROR_MESSAGES = {
    "RATE_LIMIT": "요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
    "QUOTA_EXCEEDED": "일일 사용량을 초과했습니다. 내일 다시 시도해주세요.",
    "RESOURCE_EXHAUSTED": "서버가 바쁩니다. 잠시 후 다시 시도해주세요.",
    "UNAVAILABLE": "서비스가 일시적으로 불안정합니다. 잠시 후 다시 시도해주세요.",
    "DEADLINE_EXCEEDED": "요청 시간이 초과되었습니다. 다시 시도해주세요.",
    "INVALID_ARGUMENT": "입력값이 올바르지 않습니다. 프롬프트를 확인해주세요.",
    "PERMISSION_DENIED": "API 키가 유효하지 않거나 권한이 없습니다.",
    "NOT_FOUND": "요청한 리소스를 찾을 수 없습니다.",
    "CONTENT_POLICY": "콘텐츠 정책에 위배되는 내용이 감지되었습니다. 프롬프트를 수정해주세요.",
    "SAFETY": "안전 정책에 위배되는 내용이 감지되었습니다. 프롬프트를 수정해주세요.",
    "BLOCKED": "요청이 차단되었습니다. 프롬프트를 수정해주세요.",
    "TIMEOUT": "영상 생성 시간이 초과되었습니다. 더 짧은 영상을 시도해보세요.",
    "NETWORK": "네트워크 연결이 불안정합니다. 인터넷 연결을 확인해주세요.",
}


def _get_user_friendly_error(error: str) -> str:
    """Convert technical error to user-friendly Korean message."""
    error_upper = error.upper()

    for key, message in ERROR_MESSAGES.items():
        if key in error_upper:
            return message

    # Default message for unknown errors
    if "error" in error.lower() or "exception" in error.lower():
        return f"영상 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요. (상세: {error[:100]})"

    return error


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
class VeoProgress:
    """Progress update during Veo video generation."""
    status: str  # "submitting", "polling", "processing", "completed", "failed"
    elapsed_seconds: float
    estimated_remaining_seconds: Optional[float] = None
    poll_count: int = 0
    message: str = ""


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
        # H1.3: SecretStr - use .get_secret_value() for actual API key
        self._api_key = api_key or settings.GEMINI_API_KEY.get_secret_value()
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
        progress_callback: Optional[Callable[[VeoProgress], None]] = None,
    ) -> VeoResult:
        """Generate video using Veo 3.1 with async polling.

        Submits a video generation job and polls until completion or timeout.
        Uses exponential backoff for polling to reduce API load.

        Args:
            config: VeoConfig with generation parameters
            max_wait_seconds: Maximum time to wait for completion (default 360s)
            poll_interval: Initial polling interval in seconds (default 10s)
            progress_callback: Optional callback for progress updates

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

        # Helper to emit progress updates
        def emit_progress(status: str, message: str = "", poll_count: int = 0):
            if progress_callback:
                elapsed = time.monotonic() - start_time
                # Estimate remaining time based on typical generation times
                estimated_remaining = None
                if status == "polling" and elapsed < max_wait_seconds:
                    # Veo typically takes 60-180 seconds for fast model, 120-360 for standard
                    avg_time = 90 if "fast" in model else 180
                    estimated_remaining = max(0, avg_time - elapsed)
                progress_callback(VeoProgress(
                    status=status,
                    elapsed_seconds=elapsed,
                    estimated_remaining_seconds=estimated_remaining,
                    poll_count=poll_count,
                    message=message,
                ))

        logger.info(f"Starting Veo generation: model={model}, duration={config.duration_seconds}s")
        emit_progress("submitting", "영상 생성 요청 중...")

        try:
            # Build generation config
            # Note: person_generation removed - 'dont_allow' is not supported in Veo 3.1
            generate_config = {
                "prompt": config.prompt,
                "duration_seconds": config.duration_seconds,
                "aspect_ratio": config.aspect_ratio,
            }

            if config.negative_prompt:
                generate_config["negative_prompt"] = config.negative_prompt
            if config.seed is not None:
                generate_config["seed"] = config.seed
            # Note: include_audio removed - Veo 3.1 includes audio by default

            # Submit async generation job with retry logic
            operation = None
            last_error = None

            for attempt in range(MAX_RETRIES):
                try:
                    operation = await asyncio.to_thread(
                        client.models.generate_videos,
                        model=model,
                        prompt=config.prompt,
                        config=types.GenerateVideosConfig(**{
                            k: v for k, v in generate_config.items() if k != "prompt"
                        }),
                    )
                    break  # Success, exit retry loop
                except Exception as e:
                    last_error = e
                    error_str = str(e).upper()

                    # Check if error is retryable
                    is_retryable = any(err in error_str for err in RETRYABLE_ERRORS)

                    if is_retryable and attempt < MAX_RETRIES - 1:
                        delay = RETRY_DELAYS[attempt]
                        logger.warning(
                            f"Veo API error (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                            f"Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                        continue

                    # Non-retryable or final attempt
                    raise

            if operation is None:
                raise VeoGenerationError(f"Failed to submit generation job: {last_error}")

            emit_progress("polling", "영상 생성 작업이 시작되었습니다. 잠시 기다려주세요...")

            # Poll for completion with exponential backoff and retry
            elapsed = 0
            current_interval = poll_interval
            consecutive_poll_failures = 0
            poll_count = 0

            while elapsed < max_wait_seconds:
                # Check if operation is done
                if hasattr(operation, 'done') and operation.done:
                    break

                # Wait before next poll
                await asyncio.sleep(current_interval)
                elapsed = time.monotonic() - start_time
                poll_count += 1

                # Emit progress update
                emit_progress(
                    "polling",
                    f"영상 생성 중... ({int(elapsed)}초 경과)",
                    poll_count
                )

                # Refresh operation status with retry logic
                if hasattr(operation, 'name'):
                    poll_success = False
                    for poll_attempt in range(POLL_MAX_RETRIES):
                        try:
                            operation = await asyncio.to_thread(
                                client.operations.get,
                                operation=operation,
                            )
                            poll_success = True
                            consecutive_poll_failures = 0  # Reset on success
                            break
                        except Exception as e:
                            consecutive_poll_failures += 1
                            if poll_attempt < POLL_MAX_RETRIES - 1:
                                logger.warning(
                                    f"Poll attempt {poll_attempt + 1}/{POLL_MAX_RETRIES} failed: {e}. "
                                    f"Retrying in {POLL_RETRY_DELAY}s..."
                                )
                                await asyncio.sleep(POLL_RETRY_DELAY)
                            else:
                                logger.error(f"All poll attempts failed: {e}")

                    # If too many consecutive failures, abort
                    if consecutive_poll_failures >= POLL_MAX_RETRIES * 2:
                        logger.error(f"Too many consecutive poll failures ({consecutive_poll_failures}), aborting")
                        emit_progress("failed", "네트워크 연결이 불안정합니다.")
                        return VeoResult(
                            success=False,
                            error="네트워크 연결이 불안정합니다. 잠시 후 다시 시도해주세요.",
                            duration_ms=int((time.monotonic() - start_time) * 1000),
                            model=model,
                            credit_cost=0,
                        )

                # Exponential backoff
                current_interval = min(current_interval * POLL_BACKOFF_FACTOR, MAX_POLL_INTERVAL)
                logger.debug(f"Polling Veo job, elapsed={elapsed:.1f}s, next_poll={current_interval:.1f}s")

            duration_ms = int((time.monotonic() - start_time) * 1000)

            # Check for timeout
            if elapsed >= max_wait_seconds:
                logger.error(f"Veo generation timed out after {max_wait_seconds}s")
                emit_progress("failed", "영상 생성 시간이 초과되었습니다.")
                return VeoResult(
                    success=False,
                    error=_get_user_friendly_error("TIMEOUT"),
                    duration_ms=duration_ms,
                    model=model,
                    credit_cost=0,  # No charge on timeout
                )

            # Extract result
            # Note: Google Veo API uses 'response' not 'result'
            response = getattr(operation, 'response', None) or getattr(operation, 'result', None)
            if response:
                videos = getattr(response, 'generated_videos', [])

                if videos and len(videos) > 0:
                    video = videos[0]

                    # Debug: Log the video object structure
                    logger.debug(f"Video object type: {type(video)}, attrs: {dir(video)}")

                    # Try multiple attribute paths for video URI
                    # Google Veo API may return URI in different structures
                    video_uri = None

                    # Path 1: video.uri (direct URI)
                    if hasattr(video, 'uri') and video.uri:
                        video_uri = video.uri
                        logger.debug(f"Found video URI at video.uri: {video_uri}")

                    # Path 2: video.video.uri (nested video object)
                    elif hasattr(video, 'video'):
                        video_file = video.video
                        logger.debug(f"Video file type: {type(video_file)}, attrs: {dir(video_file)}")
                        if hasattr(video_file, 'uri') and video_file.uri:
                            video_uri = video_file.uri
                            logger.debug(f"Found video URI at video.video.uri: {video_uri}")
                        elif hasattr(video_file, 'name') and video_file.name:
                            # Google Files API uses 'name' as the resource identifier
                            video_uri = video_file.name
                            logger.debug(f"Found video name at video.video.name: {video_uri}")

                    # Path 3: video.name (direct name)
                    elif hasattr(video, 'name') and video.name:
                        video_uri = video.name
                        logger.debug(f"Found video name at video.name: {video_uri}")

                    if video_uri:
                        logger.info(f"Veo generation completed in {duration_ms}ms")
                        emit_progress("completed", "영상 생성이 완료되었습니다!")
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
                user_friendly_error = _get_user_friendly_error(error_msg)
                emit_progress("failed", user_friendly_error)
                return VeoResult(
                    success=False,
                    error=user_friendly_error,
                    duration_ms=duration_ms,
                    model=model,
                    credit_cost=0,  # No charge on error
                )

            # Unknown state - log operation structure for debugging
            logger.error(
                f"Veo generation: Unknown state. "
                f"operation.done={getattr(operation, 'done', None)}, "
                f"has_response={hasattr(operation, 'response')}, "
                f"has_result={hasattr(operation, 'result')}, "
                f"operation_attrs={[a for a in dir(operation) if not a.startswith('_')]}"
            )
            if hasattr(operation, 'response') and operation.response:
                resp = operation.response
                logger.error(f"response_attrs={[a for a in dir(resp) if not a.startswith('_')]}")
            emit_progress("failed", "영상 생성 결과를 받지 못했습니다.")
            return VeoResult(
                success=False,
                error="영상 생성은 완료되었으나 결과를 받지 못했습니다. 다시 시도해주세요.",
                duration_ms=duration_ms,
                model=model,
                credit_cost=0,
            )

        except Exception as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.exception(f"Veo generation error: {e}")
            user_friendly_error = _get_user_friendly_error(str(e))
            emit_progress("failed", user_friendly_error)
            return VeoResult(
                success=False,
                error=user_friendly_error,
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
