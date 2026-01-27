"""Storyboard Orchestrator - Multi-shot video generation coordinator.

Orchestrates the generation of multi-shot storyboard videos by:
1. Planning shot sequence with coherence chain
2. Generating shots sequentially or in parallel (provider-dependent)
3. Extracting first/last frames for shot-to-shot continuity
4. Combining clips into final composite (if supported)

Provider Support:
- Sora 2 Pro: Native storyboard mode (single API call)
- VEO/Kling: Chained generation (shot-by-shot with frame references)

Usage:
    from app.services.storyboard_orchestrator import StoryboardOrchestrator

    orchestrator = StoryboardOrchestrator()
    result = await orchestrator.execute(
        request=storyboard_request,
        progress_callback=lambda p: print(p.message),
    )
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

from app.schemas.storyboard import (
    StoryboardRequest,
    StoryboardShot,
    StoryboardResult,
    ShotGenerationResult,
    StoryboardProgress,
    StoryboardProvider,
    CoherenceLevel,
    TransitionType,
)
from app.routers.production.providers.base import (
    GenerationRequest,
    GenerationResult,
    MediaType,
    get_provider,
)
from app.routers.production.providers.adapters import get_adapter

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class OrchestratorConfig:
    """Storyboard orchestrator configuration."""

    # Execution
    parallel_shots: bool = False  # Parallel generation (loses coherence)
    max_parallel: int = 3  # Max parallel generations

    # Frame extraction
    extract_frames: bool = True  # Extract first/last frames
    frame_quality: int = 90  # JPEG quality (0-100)

    # Retry
    max_retries: int = 2
    retry_delay_seconds: float = 5.0

    # Timeout
    shot_timeout_seconds: float = 300.0  # Per-shot timeout
    total_timeout_seconds: float = 1800.0  # Total timeout (30 min)

    # Provider-specific
    sora_native_storyboard: bool = True  # Use Sora's native mode
    frame_chain_enabled: bool = True  # Use frame chain for coherence


# =============================================================================
# Frame Extractor
# =============================================================================


class FrameExtractor:
    """Extract first/last frames from video clips for coherence chain."""

    async def extract_first_frame(
        self,
        video_uri: str,
        output_format: str = "jpeg",
    ) -> Optional[str]:
        """Extract first frame from video.

        Args:
            video_uri: Video URL
            output_format: Output format (jpeg, png)

        Returns:
            URL of extracted frame or None
        """
        # TODO: Implement using ffmpeg or cloud video processing
        # For now, return None (feature stub)
        logger.debug(f"[FRAME_EXTRACTOR] Would extract first frame from {video_uri}")
        return None

    async def extract_last_frame(
        self,
        video_uri: str,
        output_format: str = "jpeg",
    ) -> Optional[str]:
        """Extract last frame from video.

        Args:
            video_uri: Video URL
            output_format: Output format (jpeg, png)

        Returns:
            URL of extracted frame or None
        """
        # TODO: Implement using ffmpeg or cloud video processing
        logger.debug(f"[FRAME_EXTRACTOR] Would extract last frame from {video_uri}")
        return None


# =============================================================================
# Storyboard Orchestrator
# =============================================================================


class StoryboardOrchestrator:
    """Orchestrates multi-shot storyboard video generation.

    Handles:
    1. Shot planning with timing and transitions
    2. Sequential/parallel shot generation
    3. Frame chain management for coherence
    4. Progress tracking and callbacks
    5. Error recovery and retries
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """Initialize orchestrator.

        Args:
            config: Optional configuration
        """
        self.config = config or OrchestratorConfig()
        self.frame_extractor = FrameExtractor()

    async def execute(
        self,
        request: StoryboardRequest,
        progress_callback: Optional[Callable[[StoryboardProgress], None]] = None,
    ) -> StoryboardResult:
        """Execute storyboard generation.

        Args:
            request: Storyboard request with shots
            progress_callback: Optional progress callback

        Returns:
            StoryboardResult with all shot results
        """
        trace_id = f"storyboard-{uuid.uuid4().hex[:12]}"
        start_time = time.time()

        logger.info(
            f"[STORYBOARD] Starting generation: {len(request.shots)} shots, "
            f"provider={request.provider.value}, coherence={request.coherence_level.value}"
        )

        # Report start
        if progress_callback:
            progress_callback(StoryboardProgress(
                status="pending",
                current_shot=0,
                total_shots=len(request.shots),
                progress=0.0,
                message="Storyboard 생성 시작...",
            ))

        try:
            # Route to appropriate execution strategy
            if (
                request.provider == StoryboardProvider.SORA
                and self.config.sora_native_storyboard
            ):
                result = await self._execute_sora_native(
                    request,
                    trace_id,
                    progress_callback,
                )
            else:
                result = await self._execute_chained(
                    request,
                    trace_id,
                    progress_callback,
                )

            result.generation_latency_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"[STORYBOARD] Complete: {result.shots_completed}/{len(request.shots)} shots, "
                f"latency={result.generation_latency_ms}ms"
            )

            return result

        except asyncio.TimeoutError:
            logger.error(f"[STORYBOARD] Timeout after {self.config.total_timeout_seconds}s")
            return StoryboardResult(
                success=False,
                provider=request.provider.value,
                trace_id=trace_id,
                generation_latency_ms=int((time.time() - start_time) * 1000),
                error="Generation timed out",
                error_code="TIMEOUT",
            )
        except Exception as e:
            logger.error(f"[STORYBOARD] Error: {e}", exc_info=True)
            return StoryboardResult(
                success=False,
                provider=request.provider.value,
                trace_id=trace_id,
                generation_latency_ms=int((time.time() - start_time) * 1000),
                error=str(e),
                error_code="UNKNOWN_ERROR",
            )

    async def _execute_sora_native(
        self,
        request: StoryboardRequest,
        trace_id: str,
        progress_callback: Optional[Callable[[StoryboardProgress], None]],
    ) -> StoryboardResult:
        """Execute using Sora's native storyboard mode.

        Sora 2 Pro supports native multi-shot generation in a single API call.
        """
        logger.info("[STORYBOARD] Using Sora native storyboard mode")

        if progress_callback:
            progress_callback(StoryboardProgress(
                status="processing",
                current_shot=0,
                total_shots=len(request.shots),
                progress=0.1,
                message="Sora storyboard 모드로 생성 중...",
            ))

        try:
            # Get Sora adapter
            adapter = get_adapter("sora")

            # Build storyboard segments for Sora
            shot_defs = []
            for shot in request.shots:
                shot_def = {
                    "prompt": shot.prompt,
                    "duration": shot.duration_seconds,
                }
                if shot.transition_to_next != TransitionType.CUT:
                    shot_def["transition"] = shot.transition_to_next.value
                shot_defs.append(shot_def)

            # Compile storyboard prompt
            adapter_result = adapter.compile_storyboard(
                shots=shot_defs,
                total_duration_seconds=request.total_duration_seconds,
            )

            # Get Sora provider
            provider = get_provider("sora")
            if not provider:
                raise RuntimeError("Sora provider not available")

            # Build generation request
            gen_request = GenerationRequest(
                prompt=adapter_result.prompt,
                negative_prompt=adapter_result.negative_prompt or request.negative_prompt,
                media_type=MediaType.VIDEO,
                duration_seconds=request.total_duration_seconds,
                aspect_ratio=request.aspect_ratio,
                resolution=request.resolution,
                reference_images=request.global_reference_images[:3],
                include_audio=request.include_audio,
                extra_options={"mode": "storyboard"},
            )

            # Generate
            def progress_adapter(gp):
                if progress_callback:
                    progress_callback(StoryboardProgress(
                        status=gp.status.value,
                        current_shot=int(gp.progress * len(request.shots)),
                        total_shots=len(request.shots),
                        progress=gp.progress,
                        message=gp.message,
                        elapsed_seconds=gp.elapsed_seconds,
                    ))

            gen_result = await provider.generate(gen_request, progress_adapter)

            if not gen_result.success:
                return StoryboardResult(
                    success=False,
                    provider="sora",
                    trace_id=trace_id,
                    error=gen_result.error,
                    error_code=gen_result.error_code,
                )

            # Build result
            shot_results = []
            for i, shot in enumerate(request.shots):
                shot_results.append(ShotGenerationResult(
                    shot_index=i,
                    success=True,
                    media_uri=gen_result.media_uri,  # All shots in composite
                    duration_ms=int(shot.duration_seconds * 1000),
                    provider="sora",
                    trace_id=trace_id,
                ))

            return StoryboardResult(
                success=True,
                provider="sora",
                trace_id=trace_id,
                total_duration_ms=request.total_duration_seconds * 1000,
                shot_results=shot_results,
                shots_completed=len(request.shots),
                shots_failed=0,
                composite_media_uri=gen_result.media_uri,
                credits_used=gen_result.credits_used,
                evidence_refs=gen_result.evidence_refs,
            )

        except Exception as e:
            logger.error(f"[STORYBOARD] Sora native failed: {e}")
            # Fall back to chained mode
            logger.info("[STORYBOARD] Falling back to chained mode")
            return await self._execute_chained(request, trace_id, progress_callback)

    async def _execute_chained(
        self,
        request: StoryboardRequest,
        trace_id: str,
        progress_callback: Optional[Callable[[StoryboardProgress], None]],
    ) -> StoryboardResult:
        """Execute using chained shot-by-shot generation.

        For providers without native storyboard support (VEO, Kling).
        Uses frame extraction for shot-to-shot coherence.
        """
        logger.info("[STORYBOARD] Using chained generation mode")

        provider_name = request.provider.value
        provider = get_provider(provider_name)
        if not provider:
            return StoryboardResult(
                success=False,
                provider=provider_name,
                trace_id=trace_id,
                error=f"Provider {provider_name} not available",
                error_code="PROVIDER_NOT_FOUND",
            )

        adapter = get_adapter(provider_name)

        shot_results: List[ShotGenerationResult] = []
        individual_clips: List[str] = []
        coherence_chain: List[Dict[str, str]] = []
        total_credits = 0

        # Previous shot's last frame for continuity
        previous_last_frame: Optional[str] = None

        for i, shot in enumerate(request.shots):
            if progress_callback:
                progress_callback(StoryboardProgress(
                    status="processing",
                    current_shot=i + 1,
                    total_shots=len(request.shots),
                    progress=(i / len(request.shots)) * 0.9,
                    message=f"Shot {i + 1}/{len(request.shots)} 생성 중...",
                ))

            # Build shot request with coherence chain
            shot_result = await self._generate_shot(
                shot=shot,
                provider=provider,
                adapter=adapter,
                request=request,
                previous_last_frame=previous_last_frame,
                trace_id=f"{trace_id}-shot{i}",
            )

            shot_results.append(shot_result)

            if shot_result.success and shot_result.media_uri:
                individual_clips.append(shot_result.media_uri)
                total_credits += 1  # Estimate; actual from provider

                # Extract last frame for next shot's coherence
                if (
                    self.config.frame_chain_enabled
                    and request.coherence_level != CoherenceLevel.NONE
                    and i < len(request.shots) - 1
                ):
                    shot_result.last_frame_uri = await self.frame_extractor.extract_last_frame(
                        shot_result.media_uri
                    )
                    previous_last_frame = shot_result.last_frame_uri

                    if shot_result.last_frame_uri:
                        coherence_chain.append({
                            "shot_index": str(i),
                            "last_frame": shot_result.last_frame_uri,
                        })

        # Calculate totals
        shots_completed = sum(1 for r in shot_results if r.success)
        shots_failed = len(shot_results) - shots_completed
        total_duration = sum(r.duration_ms for r in shot_results if r.success)

        success = shots_completed > 0 and shots_failed == 0

        if progress_callback:
            progress_callback(StoryboardProgress(
                status="completed" if success else "failed",
                current_shot=len(request.shots),
                total_shots=len(request.shots),
                progress=1.0,
                message=f"완료: {shots_completed}/{len(request.shots)} shots",
            ))

        return StoryboardResult(
            success=success,
            provider=provider_name,
            trace_id=trace_id,
            total_duration_ms=total_duration,
            shot_results=shot_results,
            shots_completed=shots_completed,
            shots_failed=shots_failed,
            composite_media_uri=None,  # Chained mode doesn't auto-composite
            individual_clips=individual_clips,
            coherence_chain=coherence_chain,
            credits_used=total_credits,
            evidence_refs=[f"db:storyboard:{trace_id}"],
            error=None if success else f"{shots_failed} shots failed",
        )

    async def _generate_shot(
        self,
        shot: StoryboardShot,
        provider,
        adapter,
        request: StoryboardRequest,
        previous_last_frame: Optional[str],
        trace_id: str,
    ) -> ShotGenerationResult:
        """Generate a single shot with retry support."""
        for attempt in range(self.config.max_retries + 1):
            try:
                # Determine first frame from coherence chain
                first_frame = shot.first_frame_url
                if (
                    not first_frame
                    and shot.reference_from_previous
                    and previous_last_frame
                ):
                    first_frame = previous_last_frame

                # Build generation request
                reference_images = list(shot.reference_images)
                if request.global_reference_images:
                    # Combine shot-specific and global references
                    reference_images = (
                        reference_images + request.global_reference_images
                    )[:3]  # Max 3

                gen_request = GenerationRequest(
                    prompt=shot.prompt,
                    negative_prompt=request.negative_prompt,
                    media_type=MediaType.VIDEO,
                    duration_seconds=int(shot.duration_seconds),
                    aspect_ratio=request.aspect_ratio,
                    resolution=request.resolution,
                    reference_images=reference_images,
                    first_frame_url=first_frame,
                    include_audio=request.include_audio,
                )

                # Add system prompt from adapter if available
                if request.visual_style:
                    gen_request.system_prompt = f"Visual style: {request.visual_style}"

                # Generate
                result = await asyncio.wait_for(
                    provider.generate(gen_request),
                    timeout=self.config.shot_timeout_seconds,
                )

                if result.success:
                    return ShotGenerationResult(
                        shot_index=shot.index,
                        success=True,
                        media_uri=result.media_uri,
                        duration_ms=result.duration_ms,
                        provider=provider.name,
                        trace_id=trace_id,
                    )
                else:
                    logger.warning(
                        f"[STORYBOARD] Shot {shot.index} failed (attempt {attempt + 1}): "
                        f"{result.error}"
                    )

            except asyncio.TimeoutError:
                logger.warning(
                    f"[STORYBOARD] Shot {shot.index} timed out (attempt {attempt + 1})"
                )
            except Exception as e:
                logger.error(
                    f"[STORYBOARD] Shot {shot.index} error (attempt {attempt + 1}): {e}"
                )

            # Retry delay
            if attempt < self.config.max_retries:
                await asyncio.sleep(self.config.retry_delay_seconds)

        # All retries failed
        return ShotGenerationResult(
            shot_index=shot.index,
            success=False,
            error="Max retries exceeded",
            provider=provider.name,
            trace_id=trace_id,
        )


# =============================================================================
# Convenience Functions
# =============================================================================


async def generate_storyboard(
    shots: List[Dict[str, Any]],
    provider: str = "sora",
    total_duration_seconds: int = 15,
    coherence_level: str = "both",
    progress_callback: Optional[Callable[[StoryboardProgress], None]] = None,
) -> StoryboardResult:
    """Convenience function to generate a storyboard.

    Args:
        shots: List of shot definitions with prompt and duration
        provider: Target provider (sora, veo, kling)
        total_duration_seconds: Total video duration
        coherence_level: Coherence level (character, style, both, none)
        progress_callback: Optional progress callback

    Returns:
        StoryboardResult

    Example:
        result = await generate_storyboard(
            shots=[
                {"prompt": "Wide shot of forest", "duration_seconds": 3},
                {"prompt": "Close-up of deer", "duration_seconds": 2},
            ],
            total_duration_seconds=5,
        )
    """
    # Convert dict shots to StoryboardShot
    storyboard_shots = []
    for i, shot_dict in enumerate(shots):
        storyboard_shots.append(StoryboardShot(
            index=i,
            prompt=shot_dict.get("prompt", ""),
            duration_seconds=shot_dict.get("duration_seconds", 3.0),
            transition_to_next=TransitionType(
                shot_dict.get("transition", "cut")
            ),
        ))

    request = StoryboardRequest(
        shots=storyboard_shots,
        total_duration_seconds=total_duration_seconds,
        coherence_level=CoherenceLevel(coherence_level),
        provider=StoryboardProvider(provider),
    )

    orchestrator = StoryboardOrchestrator()
    return await orchestrator.execute(request, progress_callback)


__all__ = [
    "StoryboardOrchestrator",
    "OrchestratorConfig",
    "FrameExtractor",
    "generate_storyboard",
]
