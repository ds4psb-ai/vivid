"""Production Bridge Service - Unified Media Generation Orchestration.

Mega app combining video/audio/image generation providers:
- VEO: Google's cinematic video generation
- Kling: Kuaishou's high-fidelity video with lip sync
- Suno: AI music generation
- Imagen: Google's image generation (future)

Features:
- Unified provider interface
- Automatic best provider selection
- Parallel multi-provider generation
- Story Engine integration
- Credit management

Usage:
    from app.services.production_bridge_service import ProductionBridgeService

    service = ProductionBridgeService()
    result = await service.generate(
        provider="veo",
        request=GenerationRequest(prompt="Cinematic scene..."),
    )
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from app.routers.production.providers.base import (
    BaseProvider,
    MediaType,
    GenerationRequest,
    GenerationProgress,
    GenerationResult,
    ProviderCapabilities,
    ProviderError,
    get_provider_registry,
    register_provider,
)
from app.routers.production.providers.veo import VeoProvider
from app.routers.production.providers.kling import KlingProvider
from app.routers.production.providers.suno import SunoProvider

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Auto-selection rules for best provider
AUTO_SELECT_RULES = {
    "dialogue_heavy": "veo",      # VEO for dialogue/narration
    "lip_sync": "kling",          # Kling for lip sync
    "close_up": "kling",          # Kling for facial detail
    "high_motion": "veo",         # VEO for action
    "cinematic": "veo",           # VEO for cinematic feel
    "music": "suno",              # Suno for music
    "sfx": "suno",                # Suno for sound effects
    "default_video": "veo",       # Default video provider
    "default_audio": "suno",      # Default audio provider
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ProductionJob:
    """A production generation job."""
    job_id: str
    provider: str
    request: GenerationRequest
    status: str = "pending"
    result: Optional[GenerationResult] = None
    error: Optional[str] = None


@dataclass
class ProductionBridgeResult:
    """Result from Production Bridge orchestration."""
    success: bool
    trace_id: str = ""
    jobs: List[ProductionJob] = field(default_factory=list)
    total_credits_used: int = 0
    evidence_refs: List[str] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)


# =============================================================================
# Production Bridge Service
# =============================================================================

class ProductionBridgeService:
    """Orchestrates media generation across multiple providers."""

    def __init__(self):
        """Initialize the Production Bridge service."""
        self._registry = get_provider_registry()
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Register default providers."""
        # Register providers if not already registered
        if not self._registry.get("veo"):
            register_provider(VeoProvider())
        if not self._registry.get("kling"):
            register_provider(KlingProvider())
        if not self._registry.get("suno"):
            register_provider(SunoProvider())

    def list_providers(self) -> List[str]:
        """List all available providers."""
        return self._registry.list_providers()

    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """Get a provider by name."""
        return self._registry.get(name)

    def get_provider_capabilities(self, name: str) -> Optional[ProviderCapabilities]:
        """Get capabilities for a provider."""
        provider = self._registry.get(name)
        if provider:
            return provider.get_capabilities()
        return None

    def calculate_credits(self, provider: str, request: GenerationRequest) -> int:
        """Calculate credits for a generation request.

        Args:
            provider: Provider name
            request: Generation request

        Returns:
            Credit cost
        """
        p = self._registry.get(provider)
        if not p:
            return 0
        return p.calculate_credits(request)

    def select_best_provider(
        self,
        request: GenerationRequest,
        media_type: Optional[MediaType] = None,
    ) -> Optional[str]:
        """Select the best provider for a request.

        Args:
            request: Generation request
            media_type: Optional media type override

        Returns:
            Best provider name
        """
        mt = media_type or request.media_type
        prompt_lower = request.prompt.lower()

        # Apply auto-selection rules
        if mt == MediaType.VIDEO:
            if any(kw in prompt_lower for kw in ["dialogue", "conversation", "speaking", "talking"]):
                return AUTO_SELECT_RULES["dialogue_heavy"]
            if any(kw in prompt_lower for kw in ["lip sync", "lipSync", "lips"]):
                return AUTO_SELECT_RULES["lip_sync"]
            if any(kw in prompt_lower for kw in ["close-up", "closeup", "face", "portrait"]):
                return AUTO_SELECT_RULES["close_up"]
            if any(kw in prompt_lower for kw in ["action", "fast", "running", "fighting"]):
                return AUTO_SELECT_RULES["high_motion"]
            return AUTO_SELECT_RULES["default_video"]

        elif mt == MediaType.AUDIO:
            return AUTO_SELECT_RULES["default_audio"]

        # Get best from registry
        best = self._registry.get_best_provider(mt, request)
        return best.name if best else None

    async def generate(
        self,
        provider: str,
        request: GenerationRequest,
        progress_callback: Optional[Callable[[GenerationProgress], None]] = None,
    ) -> GenerationResult:
        """Generate content using a specific provider.

        Args:
            provider: Provider name
            request: Generation request
            progress_callback: Optional progress callback

        Returns:
            GenerationResult
        """
        p = self._registry.get(provider)
        if not p:
            return GenerationResult(
                success=False,
                provider=provider,
                error=f"Provider '{provider}' not found",
                error_code="PROVIDER_NOT_FOUND",
            )

        return await p.generate(request, progress_callback)

    async def generate_auto(
        self,
        request: GenerationRequest,
        progress_callback: Optional[Callable[[GenerationProgress], None]] = None,
    ) -> GenerationResult:
        """Generate content with automatic provider selection.

        Args:
            request: Generation request
            progress_callback: Optional progress callback

        Returns:
            GenerationResult
        """
        provider = self.select_best_provider(request)
        if not provider:
            return GenerationResult(
                success=False,
                provider="auto",
                error="No suitable provider found",
                error_code="NO_PROVIDER",
            )

        return await self.generate(provider, request, progress_callback)

    async def generate_multi(
        self,
        requests: List[Dict[str, Any]],
        parallel: bool = True,
    ) -> ProductionBridgeResult:
        """Generate content with multiple providers.

        Args:
            requests: List of {"provider": str, "request": GenerationRequest}
            parallel: Whether to run in parallel

        Returns:
            ProductionBridgeResult with all job results
        """
        trace_id = f"production-bridge-{uuid.uuid4().hex[:12]}"
        jobs = []
        evidence_refs = []
        errors = {}
        total_credits = 0

        # Create jobs
        for idx, req_data in enumerate(requests):
            provider = req_data.get("provider", "veo")
            request = req_data.get("request")

            if isinstance(request, dict):
                request = GenerationRequest(**request)

            job_id = f"{trace_id}-{idx}"
            jobs.append(ProductionJob(
                job_id=job_id,
                provider=provider,
                request=request,
            ))

        # Execute jobs
        if parallel:
            tasks = [
                self._run_job(job)
                for job in jobs
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            for job in jobs:
                await self._run_job(job)

        # Collect results
        for job in jobs:
            if job.result:
                if job.result.success:
                    total_credits += job.result.credits_used
                    evidence_refs.extend(job.result.evidence_refs)
                else:
                    errors[job.provider] = job.result.error or "Unknown error"

        success = any(j.result and j.result.success for j in jobs)

        return ProductionBridgeResult(
            success=success,
            trace_id=trace_id,
            jobs=jobs,
            total_credits_used=total_credits,
            evidence_refs=evidence_refs,
            errors=errors,
        )

    async def _run_job(self, job: ProductionJob) -> None:
        """Run a single production job."""
        try:
            job.status = "processing"
            result = await self.generate(job.provider, job.request)
            job.result = result
            job.status = "completed" if result.success else "failed"
            if not result.success:
                job.error = result.error
        except Exception as e:
            logger.error(f"[PRODUCTION_BRIDGE] Job {job.job_id} failed: {e}")
            job.status = "failed"
            job.error = str(e)
            job.result = GenerationResult(
                success=False,
                provider=job.provider,
                error=str(e),
                error_code="JOB_EXCEPTION",
            )


# =============================================================================
# Module-level convenience functions
# =============================================================================

_default_service: Optional[ProductionBridgeService] = None


def get_production_bridge_service() -> ProductionBridgeService:
    """Get or create the default Production Bridge service instance."""
    global _default_service
    if _default_service is None:
        _default_service = ProductionBridgeService()
    return _default_service


async def generate_video(
    prompt: str,
    provider: str = "veo",
    duration_seconds: int = 8,
    system_prompt: Optional[str] = None,
) -> GenerationResult:
    """Convenience function for video generation."""
    service = get_production_bridge_service()
    request = GenerationRequest(
        prompt=prompt,
        media_type=MediaType.VIDEO,
        duration_seconds=duration_seconds,
        system_prompt=system_prompt,
    )
    return await service.generate(provider, request)


async def generate_audio(
    prompt: str,
    provider: str = "suno",
    duration_seconds: int = 30,
) -> GenerationResult:
    """Convenience function for audio generation."""
    service = get_production_bridge_service()
    request = GenerationRequest(
        prompt=prompt,
        media_type=MediaType.AUDIO,
        duration_seconds=duration_seconds,
    )
    return await service.generate(provider, request)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "ProductionBridgeService",
    "ProductionBridgeResult",
    "ProductionJob",
    "get_production_bridge_service",
    "generate_video",
    "generate_audio",
]
