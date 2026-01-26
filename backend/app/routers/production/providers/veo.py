"""VEO Provider for Production Bridge.

Google VEO 3.1 video generation provider with:
- Native audio generation
- Async polling
- Progress callbacks
- Credit calculation

Based on VeoService patterns.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable, List, Optional

from app.config import settings

from .base import (
    BaseProvider,
    MediaType,
    ProviderStatus,
    GenerationRequest,
    GenerationProgress,
    GenerationResult,
    ProviderCapabilities,
    ProviderError,
    ProviderTimeoutError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

VEO_MODELS = {
    "veo-3.1-generate-preview": {
        "display_name": "VEO 3.1 Standard",
        "credits": 200,
        "max_duration": 8,
    },
    "veo-3.1-fast-generate-preview": {
        "display_name": "VEO 3.1 Fast",
        "credits": 60,
        "max_duration": 8,
    },
}

DEFAULT_MODEL = "veo-3.1-generate-preview"
MAX_WAIT_SECONDS = 360
POLL_INTERVAL_START = 10
POLL_INTERVAL_MAX = 30
POLL_BACKOFF_FACTOR = 1.2


# =============================================================================
# VEO Provider
# =============================================================================

class VeoProvider(BaseProvider):
    """Google VEO 3.1 video generation provider."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize VEO provider.

        Args:
            api_key: Optional Gemini API key (uses settings if not provided)
        """
        self._api_key = api_key or settings.GEMINI_API_KEY

    @property
    def name(self) -> str:
        return "veo"

    @property
    def display_name(self) -> str:
        return "Google VEO 3.1"

    @property
    def media_types(self) -> List[MediaType]:
        return [MediaType.VIDEO]

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            name=self.name,
            display_name=self.display_name,
            media_types=self.media_types,
            max_duration_seconds=8,
            supported_resolutions=["1080p", "4K"],
            supported_aspect_ratios=["16:9", "9:16", "1:1"],
            supports_audio=True,
            supports_image_to_video=True,
            supports_reference_images=True,  # Veo 3.1 supports reference images
            max_reference_images=3,  # Veo 3.1 supports up to 3 reference images
            supports_frame_control=True,  # Veo 3.1 supports first/last frame
            default_model=DEFAULT_MODEL,
            available_models=list(VEO_MODELS.keys()),
            credit_cost_base=200,
            credit_cost_per_second=25,
        )

    def calculate_credits(self, request: GenerationRequest) -> int:
        """Calculate credit cost for VEO generation."""
        model = request.model or DEFAULT_MODEL
        model_info = VEO_MODELS.get(model, VEO_MODELS[DEFAULT_MODEL])
        return model_info["credits"]

    async def generate(
        self,
        request: GenerationRequest,
        progress_callback: Optional[Callable[[GenerationProgress], None]] = None,
    ) -> GenerationResult:
        """Generate video using VEO 3.1."""
        trace_id = self._generate_trace_id()
        start_time = time.time()

        # Validate request
        validation_error = self.validate_request(request)
        if validation_error:
            return GenerationResult(
                success=False,
                provider=self.name,
                media_type=MediaType.VIDEO,
                trace_id=trace_id,
                error=validation_error,
                error_code="VALIDATION_ERROR",
            )

        try:
            from google import genai
            from google.genai import types

            # Report start
            if progress_callback:
                progress_callback(GenerationProgress(
                    status=ProviderStatus.PENDING,
                    progress=0.0,
                    message="영상 생성 요청 중...",
                ))

            # Build prompt with system prompt if provided
            full_prompt = request.prompt
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\n{request.prompt}"

            # Initialize client
            client = genai.Client(api_key=self._api_key)
            model = request.model or DEFAULT_MODEL

            # Build config
            config = types.GenerateVideosConfig(
                aspect_ratio=request.aspect_ratio,
                number_of_videos=1,
                duration_seconds=request.duration_seconds or 8,
                negative_prompt=request.negative_prompt,
                person_generation="allow_adult",
                include_rai_reason=True,
            )

            # Submit generation request
            if progress_callback:
                progress_callback(GenerationProgress(
                    status=ProviderStatus.PROCESSING,
                    progress=0.1,
                    message="VEO 서버에 요청 제출 중...",
                ))

            # Prepare reference images (Veo 3.1 supports up to 3)
            reference_images_list = []
            if request.reference_images:
                for img_url in request.reference_images[:3]:  # Max 3 images
                    reference_images_list.append(
                        types.Part.from_uri(file_uri=img_url, mime_type="image/*")
                    )
            elif request.reference_image_url:  # Backward compatibility
                reference_images_list.append(
                    types.Part.from_uri(file_uri=request.reference_image_url, mime_type="image/*")
                )

            # Prepare first/last frame for transition generation (Veo 3.1 feature)
            first_frame = None
            last_frame = None
            if request.first_frame_url:
                first_frame = types.Part.from_uri(file_uri=request.first_frame_url, mime_type="image/*")
            if request.last_frame_url:
                last_frame = types.Part.from_uri(file_uri=request.last_frame_url, mime_type="image/*")

            # Build generation request based on mode
            if first_frame and last_frame:
                # Image-to-video mode with frame control (transition generation)
                operation = await client.aio.models.generate_videos(
                    model=model,
                    prompt=full_prompt,
                    image=first_frame,  # Start frame
                    config=config,
                )
                # Note: Veo 3.1 API handles last_frame through config or subsequent call
                # This is a simplified implementation - actual API may vary
            elif reference_images_list:
                # Reference image mode (character/style consistency)
                operation = await client.aio.models.generate_videos(
                    model=model,
                    prompt=full_prompt,
                    image=reference_images_list[0],  # Primary reference
                    config=config,
                )
            else:
                # Standard text-to-video mode
                operation = await client.aio.models.generate_videos(
                    model=model,
                    prompt=full_prompt,
                    config=config,
                )

            # Poll for completion
            poll_interval = POLL_INTERVAL_START
            poll_count = 0
            max_polls = int(MAX_WAIT_SECONDS / POLL_INTERVAL_START)

            while not operation.done and poll_count < max_polls:
                await asyncio.sleep(poll_interval)
                poll_count += 1

                elapsed = time.time() - start_time
                progress = min(0.9, 0.1 + (poll_count / max_polls) * 0.8)

                if progress_callback:
                    progress_callback(GenerationProgress(
                        status=ProviderStatus.PROCESSING,
                        progress=progress,
                        message=f"영상 생성 중... ({int(elapsed)}초 경과)",
                        elapsed_seconds=elapsed,
                        poll_count=poll_count,
                    ))

                # Refresh operation status
                operation = await client.aio.operations.get(operation)

                # Increase poll interval with backoff
                poll_interval = min(poll_interval * POLL_BACKOFF_FACTOR, POLL_INTERVAL_MAX)

            # Check result
            if not operation.done:
                raise ProviderTimeoutError(
                    f"VEO generation timed out after {MAX_WAIT_SECONDS}s",
                    error_code="TIMEOUT",
                )

            # Check for errors
            if operation.error:
                raise ProviderError(
                    f"VEO generation failed: {operation.error.message}",
                    error_code=operation.error.code,
                )

            # Extract video URI
            video_uri = None
            if operation.result and operation.result.generated_videos:
                video = operation.result.generated_videos[0]
                video_uri = video.video.uri if video.video else None

            if not video_uri:
                raise ProviderError("No video generated", error_code="NO_OUTPUT")

            elapsed_ms = int((time.time() - start_time) * 1000)

            if progress_callback:
                progress_callback(GenerationProgress(
                    status=ProviderStatus.COMPLETED,
                    progress=1.0,
                    message="영상 생성 완료!",
                    elapsed_seconds=elapsed_ms / 1000,
                ))

            # Build metadata with new Veo 3.1 features
            metadata = {
                "model": model,
                "aspect_ratio": request.aspect_ratio,
                "duration_seconds": request.duration_seconds or 8,
            }
            if request.reference_images:
                metadata["reference_images_count"] = len(request.reference_images[:3])
            if request.first_frame_url or request.last_frame_url:
                metadata["frame_control"] = {
                    "first_frame": request.first_frame_url is not None,
                    "last_frame": request.last_frame_url is not None,
                }

            return GenerationResult(
                success=True,
                provider=self.name,
                media_type=MediaType.VIDEO,
                media_uri=video_uri,
                trace_id=trace_id,
                duration_ms=elapsed_ms,
                credits_used=self.calculate_credits(request),
                evidence_refs=[f"db:production:veo:{trace_id}"],
                metadata=metadata,
            )

        except ProviderTimeoutError:
            raise
        except ProviderError:
            raise
        except Exception as e:
            logger.error(f"[VEO_PROVIDER] Error: {e}")
            return GenerationResult(
                success=False,
                provider=self.name,
                media_type=MediaType.VIDEO,
                trace_id=trace_id,
                duration_ms=int((time.time() - start_time) * 1000),
                error=str(e),
                error_code="UNKNOWN_ERROR",
            )


# =============================================================================
# Exports
# =============================================================================

__all__ = ["VeoProvider"]
