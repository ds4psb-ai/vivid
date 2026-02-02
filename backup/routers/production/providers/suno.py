"""Suno Provider for Production Bridge.

Suno AI audio/music generation provider with:
- Music generation from prompts
- Sound effect generation
- Lyrics-based music creation

Based on existing audio generation patterns.
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

SUNO_MODELS = {
    "chirp-v3.5": {
        "display_name": "Suno Chirp v3.5",
        "credits": 30,
        "max_duration": 120,
    },
    "chirp-v4": {
        "display_name": "Suno Chirp v4",
        "credits": 50,
        "max_duration": 180,
    },
}

DEFAULT_MODEL = "chirp-v3.5"
REQUEST_TIMEOUT = 30.0
POLL_TIMEOUT = 180.0
POLL_INTERVAL = 5.0


# =============================================================================
# Suno Provider
# =============================================================================

class SunoProvider(BaseProvider):
    """Suno AI audio/music generation provider."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize Suno provider.

        Args:
            api_key: Optional Suno API key
            base_url: Optional API base URL
        """
        self._api_key = api_key or getattr(settings, "SUNO_API_KEY", None)
        self._base_url = base_url or "https://api.suno.ai/v1"

    @property
    def name(self) -> str:
        return "suno"

    @property
    def display_name(self) -> str:
        return "Suno AI"

    @property
    def media_types(self) -> List[MediaType]:
        return [MediaType.AUDIO]

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            name=self.name,
            display_name=self.display_name,
            media_types=self.media_types,
            max_duration_seconds=180,
            supported_resolutions=[],
            supported_aspect_ratios=[],
            supports_audio=True,
            supports_image_to_video=False,
            supports_reference_images=False,
            default_model=DEFAULT_MODEL,
            available_models=list(SUNO_MODELS.keys()),
            credit_cost_base=30,
            credit_cost_per_second=0,
        )

    def calculate_credits(self, request: GenerationRequest) -> int:
        """Calculate credit cost for Suno generation."""
        model = request.model or DEFAULT_MODEL
        model_info = SUNO_MODELS.get(model, SUNO_MODELS[DEFAULT_MODEL])
        return model_info["credits"]

    async def generate(
        self,
        request: GenerationRequest,
        progress_callback: Optional[Callable[[GenerationProgress], None]] = None,
    ) -> GenerationResult:
        """Generate audio using Suno AI."""
        trace_id = self._generate_trace_id()
        start_time = time.time()

        # Validate request
        validation_error = self.validate_request(request)
        if validation_error:
            return GenerationResult(
                success=False,
                provider=self.name,
                media_type=MediaType.AUDIO,
                trace_id=trace_id,
                error=validation_error,
                error_code="VALIDATION_ERROR",
            )

        # Check API key
        if not self._api_key:
            return GenerationResult(
                success=False,
                provider=self.name,
                media_type=MediaType.AUDIO,
                trace_id=trace_id,
                error="Suno API key not configured",
                error_code="NO_API_KEY",
            )

        try:
            if progress_callback:
                progress_callback(GenerationProgress(
                    status=ProviderStatus.PENDING,
                    progress=0.0,
                    message="Suno 음악 생성 요청 중...",
                ))

            # Build prompt with system prompt if provided
            full_prompt = request.prompt
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\n{request.prompt}"

            model = request.model or DEFAULT_MODEL

            # Build request payload
            payload = {
                "prompt": full_prompt,
                "model": model,
                "duration": request.duration_seconds or 30,
                "instrumental": "instrumental" in request.prompt.lower(),
            }

            if request.audio_style:
                payload["style"] = request.audio_style

            # Submit generation request
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                if progress_callback:
                    progress_callback(GenerationProgress(
                        status=ProviderStatus.PROCESSING,
                        progress=0.1,
                        message="Suno 서버에 요청 제출 중...",
                    ))

                response = await client.post(
                    f"{self._base_url}/generate",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                task_id = data.get("id") or data.get("task_id")
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
                            message=f"음악 생성 중... ({int(elapsed)}초 경과)",
                            elapsed_seconds=elapsed,
                            poll_count=poll_count,
                        ))

                    # Check task status
                    status_response = await client.get(
                        f"{self._base_url}/status/{task_id}",
                        headers={"Authorization": f"Bearer {self._api_key}"},
                    )
                    status_response.raise_for_status()
                    status_data = status_response.json()

                    task_status = status_data.get("status")

                    if task_status in ["complete", "succeeded"]:
                        audio_url = status_data.get("audio_url") or status_data.get("url")

                        elapsed_ms = int((time.time() - start_time) * 1000)

                        if progress_callback:
                            progress_callback(GenerationProgress(
                                status=ProviderStatus.COMPLETED,
                                progress=1.0,
                                message="음악 생성 완료!",
                                elapsed_seconds=elapsed_ms / 1000,
                            ))

                        return GenerationResult(
                            success=True,
                            provider=self.name,
                            media_type=MediaType.AUDIO,
                            media_uri=audio_url,
                            trace_id=trace_id,
                            duration_ms=elapsed_ms,
                            credits_used=self.calculate_credits(request),
                            evidence_refs=[f"db:production:suno:{trace_id}"],
                            metadata={
                                "model": model,
                                "task_id": task_id,
                                "duration_seconds": request.duration_seconds or 30,
                            },
                        )

                    elif task_status in ["failed", "error"]:
                        error_msg = status_data.get("error", "Unknown error")
                        raise ProviderError(f"Suno generation failed: {error_msg}", error_code="GENERATION_FAILED")

                # Timeout
                raise ProviderTimeoutError(
                    f"Suno generation timed out after {POLL_TIMEOUT}s",
                    error_code="TIMEOUT",
                )

        except ProviderTimeoutError:
            raise
        except ProviderError:
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"[SUNO_PROVIDER] HTTP error: {e}")
            return GenerationResult(
                success=False,
                provider=self.name,
                media_type=MediaType.AUDIO,
                trace_id=trace_id,
                duration_ms=int((time.time() - start_time) * 1000),
                error=f"HTTP error: {e.response.status_code}",
                error_code="HTTP_ERROR",
            )
        except Exception as e:
            logger.error(f"[SUNO_PROVIDER] Error: {e}")
            return GenerationResult(
                success=False,
                provider=self.name,
                media_type=MediaType.AUDIO,
                trace_id=trace_id,
                duration_ms=int((time.time() - start_time) * 1000),
                error=str(e),
                error_code="UNKNOWN_ERROR",
            )


# =============================================================================
# Exports
# =============================================================================

__all__ = ["SunoProvider"]
