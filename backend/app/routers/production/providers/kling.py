"""Kling Provider for Production Bridge.

Kuaishou Kling AI video generation provider with:
- Best-in-class lip sync
- Beat timestamp format
- Image-to-video support
- Reference image consistency

Based on KlingService patterns.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable, List, Optional

import httpx

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

KLING_MODELS = {
    "kling-v2.6": {
        "display_name": "Kling 2.6",
        "credits_5s": 50,
        "credits_10s": 100,
        "supports_audio": True,
    },
    "kling-v2.5": {
        "display_name": "Kling 2.5",
        "credits_5s": 35,
        "credits_10s": 70,
        "supports_audio": False,
    },
}

DEFAULT_MODEL = "kling-v2.6"
BASE_URL = "https://api.klingai.com/v1"
REQUEST_TIMEOUT = 30.0
POLL_TIMEOUT = 300.0
POLL_INTERVAL = 5.0


# =============================================================================
# Kling Provider
# =============================================================================

class KlingProvider(BaseProvider):
    """Kuaishou Kling AI video generation provider."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize Kling provider.

        Args:
            api_key: Optional Kling API key
            base_url: Optional API base URL
        """
        self._api_key = api_key or getattr(settings, "KLING_API_KEY", None)
        self._base_url = base_url or BASE_URL

    @property
    def name(self) -> str:
        return "kling"

    @property
    def display_name(self) -> str:
        return "Kling 2.6"

    @property
    def media_types(self) -> List[MediaType]:
        return [MediaType.VIDEO]

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            name=self.name,
            display_name=self.display_name,
            media_types=self.media_types,
            max_duration_seconds=10,
            supported_resolutions=["720p", "1080p"],
            supported_aspect_ratios=["16:9", "9:16", "1:1"],
            supports_audio=True,
            supports_image_to_video=True,
            supports_reference_images=True,
            default_model=DEFAULT_MODEL,
            available_models=list(KLING_MODELS.keys()),
            credit_cost_base=50,
            credit_cost_per_second=10,
        )

    def calculate_credits(self, request: GenerationRequest) -> int:
        """Calculate credit cost for Kling generation."""
        model = request.model or DEFAULT_MODEL
        model_info = KLING_MODELS.get(model, KLING_MODELS[DEFAULT_MODEL])

        duration = request.duration_seconds or 5
        if duration <= 5:
            return model_info["credits_5s"]
        else:
            return model_info["credits_10s"]

    async def generate(
        self,
        request: GenerationRequest,
        progress_callback: Optional[Callable[[GenerationProgress], None]] = None,
    ) -> GenerationResult:
        """Generate video using Kling AI."""
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

        # Check API key
        if not self._api_key:
            return GenerationResult(
                success=False,
                provider=self.name,
                media_type=MediaType.VIDEO,
                trace_id=trace_id,
                error="Kling API key not configured",
                error_code="NO_API_KEY",
            )

        try:
            if progress_callback:
                progress_callback(GenerationProgress(
                    status=ProviderStatus.PENDING,
                    progress=0.0,
                    message="Kling 영상 생성 요청 중...",
                ))

            # Build prompt with system prompt if provided
            full_prompt = request.prompt
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\n{request.prompt}"

            model = request.model or DEFAULT_MODEL
            model_info = KLING_MODELS.get(model, KLING_MODELS[DEFAULT_MODEL])

            # Build request payload
            payload = {
                "model": model,
                "prompt": full_prompt,
                "duration": str(request.duration_seconds or 5),
                "aspect_ratio": request.aspect_ratio,
                "mode": "std",
                "cfg_scale": request.cfg_scale,
            }

            if request.negative_prompt:
                payload["negative_prompt"] = request.negative_prompt

            if request.reference_image_url:
                payload["image"] = request.reference_image_url

            if model_info.get("supports_audio") and request.include_audio:
                payload["enable_audio"] = True

            # Submit generation request
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                if progress_callback:
                    progress_callback(GenerationProgress(
                        status=ProviderStatus.PROCESSING,
                        progress=0.1,
                        message="Kling 서버에 요청 제출 중...",
                    ))

                response = await client.post(
                    f"{self._base_url}/videos/text2video",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                task_id = data.get("data", {}).get("task_id")
                if not task_id:
                    raise ProviderError("No task ID returned", error_code="NO_TASK_ID")

                # Poll for completion
                poll_count = 0
                max_polls = int(POLL_TIMEOUT / POLL_INTERVAL)

                while poll_count < max_polls:
                    await asyncio.sleep(POLL_INTERVAL)
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

                    # Check task status
                    status_response = await client.get(
                        f"{self._base_url}/videos/text2video/{task_id}",
                        headers={"Authorization": f"Bearer {self._api_key}"},
                    )
                    status_response.raise_for_status()
                    status_data = status_response.json()

                    task_status = status_data.get("data", {}).get("task_status")

                    if task_status == "succeed":
                        videos = status_data.get("data", {}).get("task_result", {}).get("videos", [])
                        if videos:
                            video_uri = videos[0].get("url")

                            elapsed_ms = int((time.time() - start_time) * 1000)

                            if progress_callback:
                                progress_callback(GenerationProgress(
                                    status=ProviderStatus.COMPLETED,
                                    progress=1.0,
                                    message="영상 생성 완료!",
                                    elapsed_seconds=elapsed_ms / 1000,
                                ))

                            return GenerationResult(
                                success=True,
                                provider=self.name,
                                media_type=MediaType.VIDEO,
                                media_uri=video_uri,
                                trace_id=trace_id,
                                duration_ms=elapsed_ms,
                                credits_used=self.calculate_credits(request),
                                evidence_refs=[f"db:production:kling:{trace_id}"],
                                metadata={
                                    "model": model,
                                    "task_id": task_id,
                                    "aspect_ratio": request.aspect_ratio,
                                    "duration_seconds": request.duration_seconds or 5,
                                },
                            )

                    elif task_status == "failed":
                        error_msg = status_data.get("data", {}).get("task_status_msg", "Unknown error")
                        raise ProviderError(f"Kling generation failed: {error_msg}", error_code="GENERATION_FAILED")

                # Timeout
                raise ProviderTimeoutError(
                    f"Kling generation timed out after {POLL_TIMEOUT}s",
                    error_code="TIMEOUT",
                )

        except ProviderTimeoutError:
            raise
        except ProviderError:
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"[KLING_PROVIDER] HTTP error: {e}")
            return GenerationResult(
                success=False,
                provider=self.name,
                media_type=MediaType.VIDEO,
                trace_id=trace_id,
                duration_ms=int((time.time() - start_time) * 1000),
                error=f"HTTP error: {e.response.status_code}",
                error_code="HTTP_ERROR",
            )
        except Exception as e:
            logger.error(f"[KLING_PROVIDER] Error: {e}")
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

__all__ = ["KlingProvider"]
