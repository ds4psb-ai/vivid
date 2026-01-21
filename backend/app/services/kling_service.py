"""
Kling AI Video Generation Service

Kuaishou Kling AI API integration for video generation.
Supports text-to-video and image-to-video generation.

API Reference (2025-2026):
- Models: kling-v2.6, kling-v2.5, kling-v2.2
- Text-to-video & Image-to-video
- Audio generation support (v2.6+)
- Duration: 5s, 10s
- Resolution: 720p, 1080p

License: arkain.info@gmail.com (Gemini Enterprise)
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

class KlingConfig:
    """Kling API Configuration."""
    
    # Base URL for Kling API (via proxy like kie.ai, piapi.ai, etc.)
    # Can be overridden by environment variable
    BASE_URL = "https://api.klingai.com/v1"
    
    # Timeout settings
    REQUEST_TIMEOUT = 30.0  # For API calls
    POLL_TIMEOUT = 300.0    # Max wait for generation
    POLL_INTERVAL = 5.0     # Polling interval
    
    # Model versions
    DEFAULT_MODEL = "kling-v2.6"
    SUPPORTED_MODELS = ["kling-v2.6", "kling-v2.5", "kling-v2.2", "kling-v1.6"]
    
    # Credit costs (per second of video)
    CREDIT_COSTS = {
        "5s_720p": 35,   # ~$0.25
        "5s_1080p": 50,  # ~$0.35
        "10s_720p": 70,  # ~$0.50
        "10s_1080p": 100, # ~$0.70
    }


# =============================================================================
# Enums & Models
# =============================================================================

class KlingMode(str, Enum):
    """Generation quality mode."""
    STANDARD = "std"
    PROFESSIONAL = "pro"


class KlingAspectRatio(str, Enum):
    """Video aspect ratio."""
    LANDSCAPE = "16:9"
    PORTRAIT = "9:16"
    SQUARE = "1:1"


class KlingDuration(str, Enum):
    """Video duration."""
    SHORT = "5"   # 5 seconds
    LONG = "10"   # 10 seconds


class KlingResolution(str, Enum):
    """Video resolution."""
    HD = "720p"
    FHD = "1080p"


class KlingMotionPreset(str, Enum):
    """Motion control presets (v2.6+)."""
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"
    DRAMATIC = "dramatic"


class KlingCameraPreset(str, Enum):
    """Camera control presets (v2.6+)."""
    STATIC = "static"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    ORBIT = "orbit"


@dataclass
class KlingElement:
    """Element for character/style reference (v2.6+).

    Kling 2.6 supports up to 4 reference images for consistency.
    """
    image_url: str
    element_type: str = "character"  # character, style, scene
    weight: float = 1.0


class KlingVideoRequest(BaseModel):
    """Request model for Kling video generation.

    Kling 2.6 Features:
    - Elements: Up to 4 reference images for character consistency
    - Motion Control: Preset-based motion intensity
    - Camera Control: Preset camera movements
    - End Frame: For shot sequencing
    - Native Audio: Sound effects and ambient audio
    """

    prompt: str = Field(..., min_length=1, max_length=2500, description="Video description")
    negative_prompt: Optional[str] = Field(None, max_length=500, description="Elements to avoid")
    duration: KlingDuration = Field(default=KlingDuration.SHORT, description="Video duration")
    aspect_ratio: KlingAspectRatio = Field(default=KlingAspectRatio.LANDSCAPE, description="Aspect ratio")
    resolution: KlingResolution = Field(default=KlingResolution.FHD, description="Video resolution")
    mode: KlingMode = Field(default=KlingMode.STANDARD, description="Quality mode")
    model: str = Field(default=KlingConfig.DEFAULT_MODEL, description="Model version")
    enable_audio: bool = Field(default=False, description="Enable audio generation (v2.6+)")
    cfg_scale: float = Field(default=0.5, ge=0, le=1, description="Prompt adherence (0-1)")

    # Image-to-video (optional)
    image_url: Optional[str] = Field(None, description="Initial frame image URL")

    # Kling 2.6: End Frame for shot sequencing
    end_image_url: Optional[str] = Field(None, description="End frame image URL (v2.6+)")

    # Kling 2.6: Elements (character/style reference)
    elements: Optional[List[Dict[str, Any]]] = Field(
        None,
        max_length=4,
        description="Reference images for consistency (max 4, v2.6+)"
    )

    # Kling 2.6: Motion Control
    motion_preset: Optional[str] = Field(
        None,
        description="Motion intensity preset: slow, normal, fast, dramatic"
    )

    # Kling 2.6: Camera Control
    camera_preset: Optional[str] = Field(
        None,
        description="Camera movement preset"
    )


class KlingVideoResponse(BaseModel):
    """Response model for Kling video generation."""
    
    task_id: str = Field(..., description="Generation task ID")
    status: str = Field(..., description="Task status (pending/processing/completed/failed)")
    video_url: Optional[str] = Field(None, description="Generated video URL")
    thumbnail_url: Optional[str] = Field(None, description="Video thumbnail URL")
    duration_seconds: Optional[float] = Field(None, description="Actual video duration")
    credits_used: int = Field(default=0, description="Credits consumed")
    error: Optional[str] = Field(None, description="Error message if failed")


@dataclass
class KlingResult:
    """Internal result container."""
    success: bool
    task_id: str
    video_url: Optional[str] = None
    error: Optional[str] = None
    credits_used: int = 0


# =============================================================================
# Motion Transfer (Kling 2.6+) Data Classes
# =============================================================================

class CharacterOrientation(str, Enum):
    """Character orientation mode for motion transfer.
    
    - VIDEO: Full body follows reference video (max 30s)
    - IMAGE: Portrait animation with camera movement (max 10s)
    """
    VIDEO = "video"
    IMAGE = "image"


@dataclass
class MotionTransferConfig:
    """Configuration for Kling 2.6 Motion Transfer.
    
    Transfers motion from a reference video to a character image.
    Ideal for dance videos, action sequences, and character animations.
    
    References:
    - API Endpoint: POST /videos/motion-create
    - Max duration: 30s (video orientation), 10s (image orientation)
    - Features: Full-body motion, hand/finger precision, audio preservation
    """
    image_url: str  # Character/subject image
    motion_video_url: str  # Reference video with motion to transfer
    prompt: str = ""  # Scene/background description
    character_orientation: CharacterOrientation = CharacterOrientation.VIDEO
    keep_original_sound: bool = True
    mode: KlingMode = KlingMode.PROFESSIONAL
    negative_prompt: Optional[str] = None
    model: str = KlingConfig.DEFAULT_MODEL


@dataclass
class MotionTransferResult:
    """Result from Kling Motion Transfer."""
    success: bool
    task_id: str
    video_url: Optional[str] = None
    duration_seconds: float = 0
    credits_used: int = 0
    error: Optional[str] = None


# =============================================================================
# Service Class
# =============================================================================

class KlingService:
    """
    Kling AI Video Generation Service
    
    Usage:
        service = KlingService(api_key="your-api-key")
        result = await service.generate_video(request)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize Kling service.
        
        Args:
            api_key: Kling API key (required for production)
            base_url: Optional custom API base URL
        """
        self.api_key = api_key
        self.base_url = base_url or KlingConfig.BASE_URL
        self._client: Optional[httpx.AsyncClient] = None
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=KlingConfig.REQUEST_TIMEOUT,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client
    
    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    def _calculate_credits(self, request: KlingVideoRequest) -> int:
        """Calculate credit cost based on request parameters."""
        duration = request.duration.value
        resolution = request.resolution.value
        key = f"{duration}s_{resolution}"
        return KlingConfig.CREDIT_COSTS.get(key, 50)
    
    async def generate_video(
        self,
        request: KlingVideoRequest,
        wait_for_completion: bool = True,
    ) -> KlingResult:
        """
        Generate video using Kling AI.
        
        Args:
            request: Video generation request
            wait_for_completion: Whether to wait for video completion
            
        Returns:
            KlingResult with video URL or error
        """
        if not self.api_key:
            return KlingResult(
                success=False,
                task_id="",
                error="Kling API key not configured",
            )
        
        try:
            client = self._get_client()
            
            # Build request payload
            payload: Dict[str, Any] = {
                "prompt": request.prompt,
                "duration": request.duration.value,
                "aspect_ratio": request.aspect_ratio.value,
                "mode": request.mode.value,
                "model_name": request.model,
                "cfg_scale": request.cfg_scale,
            }

            # Optional parameters
            if request.negative_prompt:
                payload["negative_prompt"] = request.negative_prompt
            if request.image_url:
                payload["image_url"] = request.image_url
            if request.enable_audio:
                payload["sound"] = True

            # Kling 2.6: End Frame for shot sequencing
            if request.end_image_url:
                payload["end_image_url"] = request.end_image_url

            # Kling 2.6: Elements (character/style reference)
            if request.elements:
                payload["elements"] = [
                    {
                        "image_url": elem.get("image_url"),
                        "type": elem.get("element_type", "character"),
                        "weight": elem.get("weight", 1.0),
                    }
                    for elem in request.elements[:4]  # Max 4 elements
                ]

            # Kling 2.6: Motion Control
            if request.motion_preset:
                payload["motion_control"] = {
                    "preset": request.motion_preset
                }

            # Kling 2.6: Camera Control
            if request.camera_preset:
                payload["camera_control"] = {
                    "preset": request.camera_preset
                }

            # Submit generation request
            endpoint = "/videos/text2video" if not request.image_url else "/videos/image2video"
            response = await client.post(endpoint, json=payload)
            response.raise_for_status()
            
            data = response.json()
            task_id = data.get("data", {}).get("task_id") or data.get("task_id")
            
            if not task_id:
                return KlingResult(
                    success=False,
                    task_id="",
                    error="No task_id in response",
                )
            
            logger.info(f"Kling task submitted: {task_id}")
            
            # Return immediately if not waiting
            if not wait_for_completion:
                return KlingResult(
                    success=True,
                    task_id=task_id,
                    credits_used=self._calculate_credits(request),
                )
            
            # Poll for completion
            result = await self._poll_for_completion(task_id)
            result.credits_used = self._calculate_credits(request)
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Kling API error: {e.response.status_code} - {e.response.text}")
            return KlingResult(
                success=False,
                task_id="",
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            )
        except Exception as e:
            logger.error(f"Kling generation failed: {e}")
            return KlingResult(
                success=False,
                task_id="",
                error=str(e),
            )
    
    async def _poll_for_completion(self, task_id: str) -> KlingResult:
        """Poll for task completion."""
        client = self._get_client()
        start_time = asyncio.get_event_loop().time()
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > KlingConfig.POLL_TIMEOUT:
                return KlingResult(
                    success=False,
                    task_id=task_id,
                    error="Generation timeout",
                )
            
            try:
                response = await client.get(f"/videos/{task_id}")
                response.raise_for_status()
                data = response.json()
                
                task_data = data.get("data", data)
                status = task_data.get("status", "").lower()
                
                if status in ("completed", "succeed", "done"):
                    video_url = (
                        task_data.get("video_url") or
                        task_data.get("output", {}).get("video_url") or
                        task_data.get("works", [{}])[0].get("video_url")
                    )
                    return KlingResult(
                        success=True,
                        task_id=task_id,
                        video_url=video_url,
                    )
                
                if status in ("failed", "error"):
                    error = task_data.get("error") or task_data.get("message") or "Generation failed"
                    return KlingResult(
                        success=False,
                        task_id=task_id,
                        error=error,
                    )
                
                # Still processing
                await asyncio.sleep(KlingConfig.POLL_INTERVAL)
                
            except Exception as e:
                logger.warning(f"Poll error for {task_id}: {e}")
                await asyncio.sleep(KlingConfig.POLL_INTERVAL)
    
    async def get_task_status(self, task_id: str) -> KlingVideoResponse:
        """Get status of a generation task."""
        try:
            client = self._get_client()
            response = await client.get(f"/videos/{task_id}")
            response.raise_for_status()
            data = response.json()
            
            task_data = data.get("data", data)
            
            return KlingVideoResponse(
                task_id=task_id,
                status=task_data.get("status", "unknown"),
                video_url=task_data.get("video_url"),
                thumbnail_url=task_data.get("thumbnail_url"),
                duration_seconds=task_data.get("duration"),
            )
        except Exception as e:
            return KlingVideoResponse(
                task_id=task_id,
                status="error",
                error=str(e),
            )

    async def transfer_motion(
        self,
        config: MotionTransferConfig,
        wait_for_completion: bool = True,
    ) -> MotionTransferResult:
        """Transfer motion from reference video to character image.
        
        Kling 2.6 Motion Control API.
        
        Args:
            config: Motion transfer configuration
            wait_for_completion: Whether to wait for video completion
            
        Returns:
            MotionTransferResult with video URL or error
        """
        if not self.api_key:
            return MotionTransferResult(
                success=False,
                task_id="",
                error="Kling API key not configured",
            )
        
        try:
            client = self._get_client()
            
            # Build motion transfer request payload
            payload: Dict[str, Any] = {
                "image": config.image_url,
                "video": config.motion_video_url,
                "model_name": config.model,
                "mode": config.mode.value,
                "character_orientation": config.character_orientation.value,
                "keep_original_sound": config.keep_original_sound,
            }
            
            # Optional parameters
            if config.prompt:
                payload["prompt"] = config.prompt
            if config.negative_prompt:
                payload["negative_prompt"] = config.negative_prompt
            
            # Submit motion transfer request
            logger.info(
                f"[KLING_MOTION] Submitting motion transfer: "
                f"orientation={config.character_orientation.value}, "
                f"audio={config.keep_original_sound}"
            )
            
            response = await client.post("/videos/motion-create", json=payload)
            response.raise_for_status()
            
            data = response.json()
            task_id = data.get("data", {}).get("task_id") or data.get("task_id")
            
            if not task_id:
                return MotionTransferResult(
                    success=False,
                    task_id="",
                    error="No task_id in response",
                )
            
            logger.info(f"[KLING_MOTION] Task submitted: {task_id}")
            
            # Return immediately if not waiting
            if not wait_for_completion:
                # Estimate credits based on orientation (30s max for video, 10s for image)
                max_duration = 30 if config.character_orientation == CharacterOrientation.VIDEO else 10
                estimated_credits = max_duration * 10  # ~10 credits per second for pro
                return MotionTransferResult(
                    success=True,
                    task_id=task_id,
                    credits_used=estimated_credits,
                )
            
            # Poll for completion
            result = await self._poll_motion_completion(task_id)
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"[KLING_MOTION] API error: {e.response.status_code} - {e.response.text}")
            return MotionTransferResult(
                success=False,
                task_id="",
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            )
        except Exception as e:
            logger.exception(f"[KLING_MOTION] Motion transfer failed: {e}")
            return MotionTransferResult(
                success=False,
                task_id="",
                error=str(e),
            )

    async def _poll_motion_completion(self, task_id: str) -> MotionTransferResult:
        """Poll for motion transfer task completion."""
        client = self._get_client()
        start_time = asyncio.get_event_loop().time()
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > KlingConfig.POLL_TIMEOUT:
                return MotionTransferResult(
                    success=False,
                    task_id=task_id,
                    error="Motion transfer timeout",
                )
            
            try:
                response = await client.get(f"/videos/{task_id}")
                response.raise_for_status()
                data = response.json()
                
                task_data = data.get("data", data)
                status = task_data.get("status", "").lower()
                
                if status in ("completed", "succeed", "done"):
                    video_url = (
                        task_data.get("video_url") or
                        task_data.get("output", {}).get("video_url") or
                        task_data.get("works", [{}])[0].get("video_url")
                    )
                    duration = task_data.get("duration", 0)
                    
                    # Calculate credits based on actual duration
                    credits = int(duration * 10) if duration else 100
                    
                    logger.info(f"[KLING_MOTION] Completed: {task_id}, duration={duration}s")
                    
                    return MotionTransferResult(
                        success=True,
                        task_id=task_id,
                        video_url=video_url,
                        duration_seconds=duration,
                        credits_used=credits,
                    )
                
                if status in ("failed", "error"):
                    error = task_data.get("error") or task_data.get("message") or "Motion transfer failed"
                    return MotionTransferResult(
                        success=False,
                        task_id=task_id,
                        error=error,
                    )
                
                # Still processing
                await asyncio.sleep(KlingConfig.POLL_INTERVAL)
                
            except Exception as e:
                logger.warning(f"[KLING_MOTION] Poll error for {task_id}: {e}")
                await asyncio.sleep(KlingConfig.POLL_INTERVAL)


# =============================================================================
# Factory Function
# =============================================================================

def get_kling_service(api_key: Optional[str] = None) -> KlingService:
    """
    Get Kling service instance.
    
    Args:
        api_key: Optional API key override
        
    Returns:
        KlingService instance
    """
    from app.config import settings
    
    key = api_key or getattr(settings, "KLING_API_KEY", None)
    base_url = getattr(settings, "KLING_API_BASE_URL", None)
    return KlingService(api_key=key, base_url=base_url)

