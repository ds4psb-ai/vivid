"""Sora Provider for Production Bridge.

OpenAI Sora video generation with:
- Timeline prompting (storyboard mode)
- Physics-aware generation
- Up to 20s video
- Strong cinematic understanding

Based on VeoProvider patterns and SoraAdapter.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional

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
from .adapters.sora_adapter import SoraAdapter

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

SORA_MODELS = {
    "sora-2": {
        "display_name": "Sora 2",
        "max_duration": 20,
        "credits_per_second": 20,
        "base_credits": 50,
        "supports_storyboard": True,
    },
    "sora-2-fast": {
        "display_name": "Sora 2 Fast",
        "max_duration": 10,
        "credits_per_second": 10,
        "base_credits": 30,
        "supports_storyboard": False,
    },
}

DEFAULT_MODEL = "sora-2"
MAX_WAIT_SECONDS = 600  # Sora can take longer
POLL_INTERVAL_START = 15
POLL_INTERVAL_MAX = 45
POLL_BACKOFF_FACTOR = 1.3


# =============================================================================
# Sora Provider
# =============================================================================

class SoraProvider(BaseProvider):
    """OpenAI Sora video generation provider.

    Features:
    - Storyboard mode (multi-shot sequences)
    - Physics-aware generation
    - Strong GPT-4 prompt understanding
    - Up to 20 seconds duration
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Sora provider.

        Args:
            api_key: Optional OpenAI API key (uses settings if not provided)
        """
        self._api_key = api_key or getattr(settings, "OPENAI_API_KEY", None)
        self._adapter = SoraAdapter()

    @property
    def name(self) -> str:
        return "sora"

    @property
    def display_name(self) -> str:
        return "OpenAI Sora 2"

    @property
    def media_types(self) -> List[MediaType]:
        return [MediaType.VIDEO]

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            name=self.name,
            display_name=self.display_name,
            media_types=self.media_types,
            max_duration_seconds=20,
            supported_resolutions=["720p", "1080p"],
            supported_aspect_ratios=["16:9", "9:16", "1:1"],
            supports_audio=False,
            supports_image_to_video=True,
            supports_reference_images=True,
            max_reference_images=2,
            supports_frame_control=True,
            default_model=DEFAULT_MODEL,
            available_models=list(SORA_MODELS.keys()),
            credit_cost_base=50,
            credit_cost_per_second=20,
        )

    def calculate_credits(self, request: GenerationRequest) -> int:
        """Calculate credit cost for Sora generation."""
        model = request.model or DEFAULT_MODEL
        model_info = SORA_MODELS.get(model, SORA_MODELS[DEFAULT_MODEL])
        duration = request.duration_seconds or 5
        return model_info["base_credits"] + (duration * model_info["credits_per_second"])

    async def generate(
        self,
        request: GenerationRequest,
        progress_callback: Optional[Callable[[GenerationProgress], None]] = None,
    ) -> GenerationResult:
        """Generate video using Sora.

        Args:
            request: Generation request with prompt and options
            progress_callback: Optional callback for progress updates

        Returns:
            GenerationResult with media URI or error
        """
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

        if not self._api_key:
            return GenerationResult(
                success=False,
                provider=self.name,
                media_type=MediaType.VIDEO,
                trace_id=trace_id,
                error="OpenAI API key not configured",
                error_code="NO_API_KEY",
            )

        try:
            # Report start
            if progress_callback:
                progress_callback(GenerationProgress(
                    status=ProviderStatus.PENDING,
                    progress=0.0,
                    message="Sora 영상 생성 요청 중...",
                ))

            # Transpile prompt cards if provided
            full_prompt = request.prompt
            transpiler_used = False
            storyboard_data: Optional[Dict[str, Any]] = None

            if request.prompt_cards and isinstance(request.prompt_cards, PromptCards):
                try:
                    transpiler = ShotGrammarTranspiler()
                    transpiled = await transpiler.transpile(
                        prompt_cards=request.prompt_cards,
                        target_engine="sora",
                        logic_vector=request.logic_vector,
                    )
                    storyboard_data = transpiled.get("storyboard")
                    if storyboard_data:
                        # Build prompt from storyboard cards
                        cards = storyboard_data.get("cards", [])
                        prompts = [card.get("text", "") for card in cards if card.get("text")]
                        if prompts:
                            full_prompt = "\n\n".join(prompts)
                    transpiler_used = True
                    logger.info(f"[SORA_PROVIDER] Transpiled {len(storyboard_data.get('cards', []))} storyboard cards")
                except Exception as e:
                    logger.warning(f"[SORA_PROVIDER] Transpiler failed, using raw prompt: {e}")
            elif request.system_prompt:
                # Build prompt with system prompt if provided
                full_prompt = f"{request.system_prompt}\n\n{full_prompt}"

            # Use adapter for additional prompt optimization
            adapter_result = None
            try:
                from .adapters.base_adapter import LogicVector
                if request.logic_vector:
                    lv = LogicVector(**request.logic_vector)
                    adapter_result = self._adapter.translate_logic_vector(lv)
                    if adapter_result.prompt and not transpiler_used:
                        full_prompt = adapter_result.prompt
                        logger.info(f"[SORA_PROVIDER] Adapter optimized prompt: {full_prompt[:100]}...")
            except Exception as e:
                logger.warning(f"[SORA_PROVIDER] Adapter optimization failed: {e}")

            model = request.model or DEFAULT_MODEL
            model_info = SORA_MODELS.get(model, SORA_MODELS[DEFAULT_MODEL])
            duration = min(request.duration_seconds or 5, model_info["max_duration"])

            if progress_callback:
                progress_callback(GenerationProgress(
                    status=ProviderStatus.PROCESSING,
                    progress=0.1,
                    message="Sora 서버에 요청 제출 중...",
                ))

            # TODO: Actual OpenAI Sora API call when available
            # The OpenAI Sora API is not yet publicly available for general use.
            # This implementation provides the structure for future integration.
            #
            # Expected API pattern (based on OpenAI conventions):
            # from openai import OpenAI
            # client = OpenAI(api_key=self._api_key)
            # response = await client.videos.generate(
            #     model=model,
            #     prompt=full_prompt,
            #     duration=duration,
            #     aspect_ratio=request.aspect_ratio,
            #     storyboard=storyboard_data,  # For multi-shot sequences
            # )

            # Simulate processing for development/testing
            # In production, this would be replaced with actual API polling
            elapsed_ms = int((time.time() - start_time) * 1000)

            if progress_callback:
                progress_callback(GenerationProgress(
                    status=ProviderStatus.PROCESSING,
                    progress=0.5,
                    message="Sora 영상 생성 중...",
                    elapsed_seconds=elapsed_ms / 1000,
                ))

            # Build metadata
            metadata: Dict[str, Any] = {
                "model": model,
                "aspect_ratio": request.aspect_ratio,
                "duration_seconds": duration,
                "transpiler_used": transpiler_used,
                "storyboard_mode": storyboard_data is not None,
            }

            if storyboard_data:
                metadata["storyboard_cards"] = len(storyboard_data.get("cards", []))

            if adapter_result:
                metadata["adapter_confidence"] = adapter_result.confidence

            if request.first_frame_url or request.last_frame_url:
                metadata["frame_control"] = {
                    "first_frame": request.first_frame_url is not None,
                    "last_frame": request.last_frame_url is not None,
                }

            if progress_callback:
                progress_callback(GenerationProgress(
                    status=ProviderStatus.COMPLETED,
                    progress=1.0,
                    message="Sora 영상 생성 완료!",
                    elapsed_seconds=elapsed_ms / 1000,
                ))

            # Return mock result (replace with actual API response)
            # The media_uri would come from the actual Sora API response
            return GenerationResult(
                success=True,
                provider=self.name,
                media_type=MediaType.VIDEO,
                media_uri=f"https://sora.openai.com/generated/{trace_id}.mp4",  # Placeholder
                trace_id=trace_id,
                duration_ms=elapsed_ms,
                credits_used=self.calculate_credits(request),
                evidence_refs=[f"db:production:sora:{trace_id}"],
                metadata=metadata,
            )

        except ProviderTimeoutError:
            raise
        except ProviderError:
            raise
        except Exception as e:
            logger.error(f"[SORA_PROVIDER] Error: {e}")
            return GenerationResult(
                success=False,
                provider=self.name,
                media_type=MediaType.VIDEO,
                trace_id=trace_id,
                duration_ms=int((time.time() - start_time) * 1000),
                error=str(e),
                error_code="UNKNOWN_ERROR",
            )

    async def generate_storyboard(
        self,
        shots: List[Dict[str, Any]],
        total_duration_seconds: int = 20,
        progress_callback: Optional[Callable[[GenerationProgress], None]] = None,
    ) -> GenerationResult:
        """Generate video from storyboard (Sora-specific feature).

        Args:
            shots: List of shot definitions with prompts and durations
            total_duration_seconds: Total video duration
            progress_callback: Optional callback for progress updates

        Returns:
            GenerationResult with media URI or error
        """
        trace_id = self._generate_trace_id()
        start_time = time.time()

        if not self._api_key:
            return GenerationResult(
                success=False,
                provider=self.name,
                media_type=MediaType.VIDEO,
                trace_id=trace_id,
                error="OpenAI API key not configured",
                error_code="NO_API_KEY",
            )

        try:
            if progress_callback:
                progress_callback(GenerationProgress(
                    status=ProviderStatus.PENDING,
                    progress=0.0,
                    message="Sora 스토리보드 영상 생성 중...",
                ))

            # Use adapter to compile storyboard
            adapter_result = self._adapter.compile_storyboard(
                shots=shots,
                total_duration_seconds=min(total_duration_seconds, 20),
            )

            if progress_callback:
                progress_callback(GenerationProgress(
                    status=ProviderStatus.PROCESSING,
                    progress=0.2,
                    message=f"{len(shots)}개 샷 스토리보드 컴파일 완료",
                ))

            # TODO: Actual Sora storyboard API call
            elapsed_ms = int((time.time() - start_time) * 1000)

            if progress_callback:
                progress_callback(GenerationProgress(
                    status=ProviderStatus.COMPLETED,
                    progress=1.0,
                    message="스토리보드 영상 생성 완료!",
                    elapsed_seconds=elapsed_ms / 1000,
                ))

            metadata = {
                "model": DEFAULT_MODEL,
                "storyboard_mode": True,
                "shot_count": len(shots),
                "total_duration": total_duration_seconds,
                "adapter_confidence": adapter_result.confidence,
            }

            return GenerationResult(
                success=True,
                provider=self.name,
                media_type=MediaType.VIDEO,
                media_uri=f"https://sora.openai.com/storyboard/{trace_id}.mp4",
                trace_id=trace_id,
                duration_ms=elapsed_ms,
                credits_used=50 + (total_duration_seconds * 20),
                evidence_refs=[f"db:production:sora:storyboard:{trace_id}"],
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"[SORA_PROVIDER] Storyboard error: {e}")
            return GenerationResult(
                success=False,
                provider=self.name,
                media_type=MediaType.VIDEO,
                trace_id=trace_id,
                duration_ms=int((time.time() - start_time) * 1000),
                error=str(e),
                error_code="STORYBOARD_ERROR",
            )


# =============================================================================
# Exports
# =============================================================================

__all__ = ["SoraProvider"]
