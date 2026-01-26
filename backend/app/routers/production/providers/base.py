"""Base Provider Interface for Production Bridge.

Abstract base class defining the provider interface for:
- Video generation (VEO, Kling, Sora, Runway)
- Audio generation (Suno, ElevenLabs)
- Image generation (Imagen, Midjourney)

Features:
- Unified request/response model
- Async polling support
- Progress callbacks
- Credit calculation

Usage:
    class MyProvider(BaseProvider):
        async def generate(self, request: GenerationRequest) -> GenerationResult:
            # Implementation
            pass
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


# =============================================================================
# Enums
# =============================================================================

class MediaType(str, Enum):
    """Media types supported by providers."""
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"


class ProviderStatus(str, Enum):
    """Provider generation status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class GenerationRequest:
    """Unified request for content generation.

    Works across video, image, and audio providers.

    Veo 3.1 Enhancements (2026):
    - reference_images: Up to 3 reference images for character/style consistency
    - first_frame_url/last_frame_url: Frame control for transition generation
    """
    prompt: str
    negative_prompt: Optional[str] = None
    media_type: MediaType = MediaType.VIDEO

    # Video/Audio specific
    duration_seconds: Optional[int] = None

    # Video/Image specific
    aspect_ratio: str = "16:9"
    resolution: str = "1080p"

    # Style and references
    system_prompt: Optional[str] = None  # From DNA Lab/Story Engine
    style: Optional[str] = None
    reference_image_url: Optional[str] = None  # Deprecated: use reference_images
    end_image_url: Optional[str] = None  # Deprecated: use last_frame_url

    # Veo 3.1 Reference Images (max 3) - Character/Style Consistency
    reference_images: List[str] = field(default_factory=list)

    # Veo 3.1 First/Last Frame Control - Transition Generation
    first_frame_url: Optional[str] = None
    last_frame_url: Optional[str] = None

    # Audio specific
    include_audio: bool = True
    audio_style: Optional[str] = None

    # Provider-specific options
    model: Optional[str] = None
    seed: Optional[int] = None
    cfg_scale: float = 0.5
    extra_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationProgress:
    """Progress update during generation."""
    status: ProviderStatus
    progress: float  # 0.0 to 1.0
    message: str = ""
    elapsed_seconds: float = 0.0
    estimated_remaining_seconds: Optional[float] = None
    poll_count: int = 0


@dataclass
class GenerationResult:
    """Unified result from content generation."""
    success: bool
    provider: str
    media_type: MediaType = MediaType.VIDEO
    media_uri: Optional[str] = None
    trace_id: str = ""
    duration_ms: int = 0
    credits_used: int = 0
    evidence_refs: List[str] = field(default_factory=list)
    error: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderCapabilities:
    """Describes provider capabilities."""
    name: str
    display_name: str
    media_types: List[MediaType]
    max_duration_seconds: Optional[int] = None
    supported_resolutions: List[str] = field(default_factory=list)
    supported_aspect_ratios: List[str] = field(default_factory=list)
    supports_audio: bool = False
    supports_image_to_video: bool = False
    supports_reference_images: bool = False
    max_reference_images: int = 0  # Veo 3.1 supports up to 3
    supports_frame_control: bool = False  # Veo 3.1 first/last frame
    default_model: str = ""
    available_models: List[str] = field(default_factory=list)
    credit_cost_base: int = 0
    credit_cost_per_second: int = 0


# =============================================================================
# Exceptions
# =============================================================================

class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code


class ProviderTimeoutError(ProviderError):
    """Raised when generation times out."""
    pass


class ProviderQuotaError(ProviderError):
    """Raised when quota is exceeded."""
    pass


class ProviderContentPolicyError(ProviderError):
    """Raised when content violates policy."""
    pass


class ProviderRateLimitError(ProviderError):
    """Raised when rate limit is exceeded."""
    pass


# =============================================================================
# Base Provider
# =============================================================================

class BaseProvider(ABC):
    """Abstract base class for content generation providers.

    All providers must implement:
    - generate(): Main generation method
    - calculate_credits(): Credit cost calculation
    - get_capabilities(): Provider capabilities

    Optional overrides:
    - validate_request(): Custom request validation
    - cancel(): Cancel generation job
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'veo', 'kling', 'suno')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name (e.g., 'Google VEO 3.1')."""
        pass

    @property
    @abstractmethod
    def media_types(self) -> List[MediaType]:
        """Supported media types."""
        pass

    @abstractmethod
    async def generate(
        self,
        request: GenerationRequest,
        progress_callback: Optional[Callable[[GenerationProgress], None]] = None,
    ) -> GenerationResult:
        """Generate content from request.

        Args:
            request: Generation request with prompt and options
            progress_callback: Optional callback for progress updates

        Returns:
            GenerationResult with media URI or error
        """
        pass

    @abstractmethod
    def calculate_credits(self, request: GenerationRequest) -> int:
        """Calculate credit cost for request.

        Args:
            request: Generation request

        Returns:
            Credit cost as integer
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities.

        Returns:
            ProviderCapabilities describing features
        """
        pass

    def validate_request(self, request: GenerationRequest) -> Optional[str]:
        """Validate request before generation.

        Args:
            request: Generation request

        Returns:
            Error message if invalid, None if valid
        """
        if not request.prompt or len(request.prompt.strip()) < 5:
            return "Prompt must be at least 5 characters"

        caps = self.get_capabilities()

        # Check media type
        if request.media_type not in caps.media_types:
            return f"Media type {request.media_type.value} not supported by {self.name}"

        # Check duration
        if request.duration_seconds:
            if caps.max_duration_seconds and request.duration_seconds > caps.max_duration_seconds:
                return f"Duration {request.duration_seconds}s exceeds max {caps.max_duration_seconds}s"

        # Check resolution
        if request.resolution and caps.supported_resolutions:
            if request.resolution not in caps.supported_resolutions:
                return f"Resolution {request.resolution} not supported"

        # Check aspect ratio
        if request.aspect_ratio and caps.supported_aspect_ratios:
            if request.aspect_ratio not in caps.supported_aspect_ratios:
                return f"Aspect ratio {request.aspect_ratio} not supported"

        # Check reference images (Veo 3.1 feature)
        if request.reference_images:
            if not caps.supports_reference_images:
                return f"Reference images not supported by {self.name}"
            if caps.max_reference_images > 0 and len(request.reference_images) > caps.max_reference_images:
                return f"Too many reference images: {len(request.reference_images)} > max {caps.max_reference_images}"

        # Check frame control (Veo 3.1 feature)
        if request.first_frame_url or request.last_frame_url:
            if not caps.supports_frame_control:
                return f"First/last frame control not supported by {self.name}"

        return None

    async def cancel(self, job_id: str) -> bool:
        """Cancel a generation job.

        Args:
            job_id: Job identifier

        Returns:
            True if cancelled successfully
        """
        # Default implementation - not all providers support cancellation
        return False

    def _generate_trace_id(self) -> str:
        """Generate a trace ID for this request."""
        return f"{self.name}-{uuid.uuid4().hex[:12]}"


# =============================================================================
# Provider Registry
# =============================================================================

class ProviderRegistry:
    """Registry for available providers."""

    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {}

    def register(self, provider: BaseProvider) -> None:
        """Register a provider."""
        self._providers[provider.name] = provider

    def get(self, name: str) -> Optional[BaseProvider]:
        """Get a provider by name."""
        return self._providers.get(name)

    def list_providers(self) -> List[str]:
        """List registered provider names."""
        return list(self._providers.keys())

    def get_by_media_type(self, media_type: MediaType) -> List[BaseProvider]:
        """Get all providers supporting a media type."""
        return [p for p in self._providers.values() if media_type in p.media_types]

    def get_best_provider(
        self,
        media_type: MediaType,
        request: Optional[GenerationRequest] = None,
    ) -> Optional[BaseProvider]:
        """Get the best provider for a media type.

        Selection criteria:
        1. Lowest credit cost (if request provided)
        2. First registered (default)
        """
        providers = self.get_by_media_type(media_type)
        if not providers:
            return None

        if request:
            # Sort by credit cost
            providers.sort(key=lambda p: p.calculate_credits(request))

        return providers[0]


# Global registry instance
_registry = ProviderRegistry()


def get_provider_registry() -> ProviderRegistry:
    """Get the global provider registry."""
    return _registry


def register_provider(provider: BaseProvider) -> None:
    """Register a provider in the global registry."""
    _registry.register(provider)


def get_provider(name: str) -> Optional[BaseProvider]:
    """Get a provider by name from the global registry."""
    return _registry.get(name)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "BaseProvider",
    "MediaType",
    "ProviderStatus",
    "GenerationRequest",
    "GenerationProgress",
    "GenerationResult",
    "ProviderCapabilities",
    "ProviderError",
    "ProviderTimeoutError",
    "ProviderQuotaError",
    "ProviderContentPolicyError",
    "ProviderRateLimitError",
    "ProviderRegistry",
    "get_provider_registry",
    "register_provider",
    "get_provider",
]
