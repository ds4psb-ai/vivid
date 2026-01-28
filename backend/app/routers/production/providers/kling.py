"""Kling Provider for Production Bridge.

Kuaishou Kling AI video generation provider with:
- Best-in-class lip sync
- Beat timestamp format
- Image-to-video support
- Reference image consistency
- Shot Grammar Transpiler integration (P1)

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
from .adapters.transpiler import ShotGrammarTranspiler, PromptCards

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

KLING_MODELS = {
    "kling-v3.0": {
        "display_name": "Kling 3.0",
        "max_duration": 120,  # Up to 2 minutes
        "credits_per_second": 15,  # Higher quality = higher cost
        "base_credits": 100,
        "supports_audio": True,
        "supports_long_form": True,
    },
    "kling-v2.6": {
        "display_name": "Kling 2.6",
        "max_duration": 10,
        "credits_5s": 50,
        "credits_10s": 100,
        "credits_per_second": 10,
        "base_credits": 0,
        "supports_audio": True,
        "supports_long_form": False,
    },
    "kling-v2.5": {
        "display_name": "Kling 2.5",
        "max_duration": 10,
        "credits_5s": 35,
        "credits_10s": 70,
        "credits_per_second": 7,
        "base_credits": 0,
        "supports_audio": False,
        "supports_long_form": False,
    },
}

DEFAULT_MODEL = "kling-v2.6"
BASE_URL = "https://api.klingai.com/v1"
REQUEST_TIMEOUT = 30.0
POLL_TIMEOUT = 300.0
POLL_TIMEOUT_EXTENDED = 900.0  # 15 minutes for long-form video (v3.0)
POLL_INTERVAL = 5.0
POLL_INTERVAL_LONG = 10.0  # Longer interval for long-form video


# =============================================================================
# Kling Provider
# =============================================================================

class KlingProvider(BaseProvider):
    """Kuaishou Kling AI video generation provider.

    Supports:
    - Kling 2.5: Basic video generation (up to 10s)
    - Kling 2.6: With audio support (up to 10s)
    - Kling 3.0: Long-form video generation (up to 120s)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """Initialize Kling provider.

        Args:
            api_key: Optional Kling API key
            base_url: Optional API base URL
            model: Optional default model (e.g., "kling-v3.0" for long-form)
        """
        self._api_key = api_key or getattr(settings, "KLING_API_KEY", None)
        self._base_url = base_url or BASE_URL
        self._model = model  # Allow setting default model

    @property
    def name(self) -> str:
        return "kling"

    @property
    def display_name(self) -> str:
        model = self._model or DEFAULT_MODEL
        model_info = KLING_MODELS.get(model, KLING_MODELS[DEFAULT_MODEL])
        return model_info["display_name"]

    @property
    def media_types(self) -> List[MediaType]:
        return [MediaType.VIDEO]

    def get_capabilities(self) -> ProviderCapabilities:
        # Dynamic capabilities based on selected model
        model = self._model or DEFAULT_MODEL
        model_info = KLING_MODELS.get(model, KLING_MODELS[DEFAULT_MODEL])

        return ProviderCapabilities(
            name=self.name,
            display_name=model_info["display_name"],
            media_types=self.media_types,
            max_duration_seconds=model_info["max_duration"],
            supported_resolutions=["720p", "1080p"],
            supported_aspect_ratios=["16:9", "9:16", "1:1"],
            supports_audio=model_info["supports_audio"],
            supports_image_to_video=True,
            supports_reference_images=True,
            default_model=model,
            available_models=list(KLING_MODELS.keys()),
            credit_cost_base=model_info.get("base_credits", 50),
            credit_cost_per_second=model_info.get("credits_per_second", 10),
        )

    def calculate_credits(self, request: GenerationRequest) -> int:
        """Calculate credit cost for Kling generation.

        Kling 3.0: base_credits + (duration * credits_per_second)
        Kling 2.x: Fixed pricing based on 5s/10s tiers
        """
        model = request.model or self._model or DEFAULT_MODEL
        model_info = KLING_MODELS.get(model, KLING_MODELS[DEFAULT_MODEL])
        duration = request.duration_seconds or 5

        # Kling 3.0 uses per-second pricing for long-form
        if model_info.get("supports_long_form", False):
            base = model_info.get("base_credits", 0)
            per_second = model_info.get("credits_per_second", 15)
            return base + (duration * per_second)

        # Kling 2.x uses tiered pricing
        if duration <= 5:
            return model_info.get("credits_5s", 50)
        else:
            return model_info.get("credits_10s", 100)

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

            # P1: Transpile prompt cards if provided
            full_prompt = request.prompt
            transpiler_used = False
            transpiled_data = {}
            if request.prompt_cards and isinstance(request.prompt_cards, PromptCards):
                try:
                    transpiler = ShotGrammarTranspiler()
                    transpiled_data = await transpiler.transpile(
                        prompt_cards=request.prompt_cards,
                        target_engine="kling",
                        logic_vector=request.logic_vector,
                    )
                    full_prompt = transpiled_data.get("prompt", request.prompt)
                    transpiler_used = True
                    logger.info(f"[KLING_PROVIDER] Transpiled prompt: {full_prompt[:100]}...")
                except Exception as e:
                    logger.warning(f"[KLING_PROVIDER] Transpiler failed, using raw prompt: {e}")

            # Build prompt with system prompt if provided (only if not using transpiler)
            if request.system_prompt and not transpiler_used:
                full_prompt = f"{request.system_prompt}\n\n{full_prompt}"

            model = request.model or self._model or DEFAULT_MODEL
            model_info = KLING_MODELS.get(model, KLING_MODELS[DEFAULT_MODEL])

            # Determine duration (with model max limit)
            max_duration = model_info.get("max_duration", 10)
            duration = min(request.duration_seconds or 5, max_duration)

            # Determine polling settings based on model/duration
            is_long_form = model_info.get("supports_long_form", False) and duration > 30
            poll_timeout = POLL_TIMEOUT_EXTENDED if is_long_form else POLL_TIMEOUT
            poll_interval = POLL_INTERVAL_LONG if is_long_form else POLL_INTERVAL

            # Build request payload
            payload = {
                "model": model,
                "prompt": full_prompt,
                "duration": str(duration),
                "aspect_ratio": request.aspect_ratio,
                "mode": "pro" if is_long_form else "std",  # Use pro mode for long-form
                "cfg_scale": request.cfg_scale,
            }

            # P1: Use transpiled data for Kling-specific features
            if transpiler_used and transpiled_data:
                if transpiled_data.get("motion_intensity"):
                    payload["motion_intensity"] = transpiled_data["motion_intensity"]
                if transpiled_data.get("camera_preset"):
                    payload["camera_preset"] = transpiled_data["camera_preset"]
                if transpiled_data.get("negative_prompt"):
                    payload["negative_prompt"] = transpiled_data["negative_prompt"]
                if transpiled_data.get("beat_markers"):
                    payload["beat_markers"] = transpiled_data["beat_markers"]
            elif request.negative_prompt:
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

                # Poll for completion with dynamic timeout
                poll_count = 0
                max_polls = int(poll_timeout / poll_interval)

                logger.info(
                    f"[KLING_PROVIDER] Starting poll: model={model}, duration={duration}s, "
                    f"timeout={poll_timeout}s, interval={poll_interval}s"
                )

                while poll_count < max_polls:
                    await asyncio.sleep(poll_interval)
                    poll_count += 1

                    elapsed = time.time() - start_time
                    progress = min(0.9, 0.1 + (poll_count / max_polls) * 0.8)

                    # Show extended message for long-form
                    msg = f"영상 생성 중... ({int(elapsed)}초 경과)"
                    if is_long_form:
                        msg = f"장편 영상 생성 중... ({int(elapsed)}초/{int(poll_timeout)}초)"

                    if progress_callback:
                        progress_callback(GenerationProgress(
                            status=ProviderStatus.PROCESSING,
                            progress=progress,
                            message=msg,
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
                                    "duration_seconds": duration,
                                    "is_long_form": is_long_form,
                                    "transpiler_used": transpiler_used,
                                },
                            )

                    elif task_status == "failed":
                        error_msg = status_data.get("data", {}).get("task_status_msg", "Unknown error")
                        raise ProviderError(f"Kling generation failed: {error_msg}", error_code="GENERATION_FAILED")

                # Timeout
                raise ProviderTimeoutError(
                    f"Kling generation timed out after {poll_timeout}s",
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
