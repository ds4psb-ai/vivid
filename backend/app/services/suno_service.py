"""
Suno AI Music Generation Service

Third-party Suno API integration for music generation.
Uses providers like sunoapi.org, musicapi.ai, etc.

API Reference (2025-2026):
- Models: V5, V4_5PLUS, V4_5, V4
- Custom mode with style/title/lyrics
- Instrumental mode
- Duration: 30s - 4min

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

class SunoConfig:
    """Suno API Configuration."""
    
    # Base URL (third-party providers)
    BASE_URL = "https://api.sunoapi.org/api/v1"
    
    # Timeout settings
    REQUEST_TIMEOUT = 30.0
    POLL_TIMEOUT = 180.0   # Music generation can take 2-3 minutes
    POLL_INTERVAL = 5.0
    
    # Model versions
    DEFAULT_MODEL = "V5"
    SUPPORTED_MODELS = ["V5", "V4_5PLUS", "V4_5ALL", "V4_5", "V4"]
    
    # Credit costs (per generation, returns 2 songs)
    CREDIT_COSTS = {
        "V5": 20,        # ~$0.14
        "V4_5PLUS": 15,  # ~$0.10
        "V4_5ALL": 15,
        "V4_5": 12,
        "V4": 10,
    }


# =============================================================================
# Enums & Models
# =============================================================================

class SunoModel(str, Enum):
    """Suno AI model versions."""
    V5 = "V5"
    V4_5_PLUS = "V4_5PLUS"
    V4_5_ALL = "V4_5ALL"
    V4_5 = "V4_5"
    V4 = "V4"


class SunoMusicRequest(BaseModel):
    """Request model for Suno music generation."""
    
    # Basic parameters
    prompt: str = Field(..., min_length=1, max_length=2000, description="Music description or lyrics")
    title: str = Field(..., min_length=1, max_length=100, description="Song title")
    style: str = Field(..., min_length=1, max_length=500, description="Music style/genre")
    
    # Mode settings
    custom_mode: bool = Field(default=True, description="Enable custom mode")
    instrumental: bool = Field(default=False, description="Instrumental only (no vocals)")
    
    # Model selection
    model: SunoModel = Field(default=SunoModel.V5, description="Model version")
    
    # Optional
    exclude_styles: Optional[str] = Field(None, max_length=200, description="Styles to exclude")


class SunoMusicResponse(BaseModel):
    """Response model for Suno music generation."""
    
    task_id: str = Field(..., description="Generation task ID")
    status: str = Field(..., description="Task status")
    songs: List[Dict[str, Any]] = Field(default=[], description="Generated songs")
    error: Optional[str] = Field(None, description="Error message")
    credits_used: int = Field(default=0, description="Credits consumed")


class SunoSong(BaseModel):
    """Individual song in response."""
    
    id: str
    title: str
    audio_url: Optional[str] = None
    stream_url: Optional[str] = None
    image_url: Optional[str] = None
    duration: Optional[float] = None
    status: str = "pending"


@dataclass
class SunoResult:
    """Internal result container."""
    success: bool
    task_id: str
    songs: List[SunoSong] = None
    error: Optional[str] = None
    credits_used: int = 0
    
    def __post_init__(self):
        if self.songs is None:
            self.songs = []


# =============================================================================
# Service Class
# =============================================================================

class SunoService:
    """
    Suno AI Music Generation Service
    
    Uses third-party API providers as Suno doesn't have an official public API.
    
    Usage:
        service = SunoService(api_key="your-api-key")
        result = await service.generate_music(request)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize Suno service.
        
        Args:
            api_key: API key for the third-party provider
            base_url: Optional custom API base URL
        """
        self.api_key = api_key
        self.base_url = base_url or SunoConfig.BASE_URL
        self._client: Optional[httpx.AsyncClient] = None
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=SunoConfig.REQUEST_TIMEOUT,
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
    
    def _calculate_credits(self, request: SunoMusicRequest) -> int:
        """Calculate credit cost based on model."""
        return SunoConfig.CREDIT_COSTS.get(request.model.value, 20)
    
    async def generate_music(
        self,
        request: SunoMusicRequest,
        wait_for_completion: bool = True,
    ) -> SunoResult:
        """
        Generate music using Suno AI.
        
        Args:
            request: Music generation request
            wait_for_completion: Whether to wait for completion
            
        Returns:
            SunoResult with song URLs or error
        """
        if not self.api_key:
            return SunoResult(
                success=False,
                task_id="",
                error="Suno API key not configured",
            )
        
        try:
            client = self._get_client()
            
            # Build request payload
            payload: Dict[str, Any] = {
                "customMode": request.custom_mode,
                "instrumental": request.instrumental,
                "model": request.model.value,
            }
            
            if request.custom_mode:
                payload["title"] = request.title
                payload["style"] = request.style
                payload["prompt"] = request.prompt  # As lyrics in custom mode
                if request.exclude_styles:
                    payload["exclude_styles"] = request.exclude_styles
            else:
                # Non-custom mode: prompt is the description
                payload["prompt"] = request.prompt
            
            # Submit generation request
            response = await client.post("/generate", json=payload)
            response.raise_for_status()
            
            data = response.json()
            task_id = data.get("taskId") or data.get("task_id") or data.get("id")
            
            if not task_id:
                return SunoResult(
                    success=False,
                    task_id="",
                    error="No task_id in response",
                )
            
            logger.info(f"Suno task submitted: {task_id}")
            
            # Return immediately if not waiting
            if not wait_for_completion:
                return SunoResult(
                    success=True,
                    task_id=task_id,
                    credits_used=self._calculate_credits(request),
                )
            
            # Poll for completion
            result = await self._poll_for_completion(task_id)
            result.credits_used = self._calculate_credits(request)
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Suno API error: {e.response.status_code} - {e.response.text}")
            return SunoResult(
                success=False,
                task_id="",
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            )
        except Exception as e:
            logger.error(f"Suno generation failed: {e}")
            return SunoResult(
                success=False,
                task_id="",
                error=str(e),
            )
    
    async def _poll_for_completion(self, task_id: str) -> SunoResult:
        """Poll for task completion."""
        client = self._get_client()
        start_time = asyncio.get_event_loop().time()
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > SunoConfig.POLL_TIMEOUT:
                return SunoResult(
                    success=False,
                    task_id=task_id,
                    error="Generation timeout",
                )
            
            try:
                response = await client.get(f"/tasks/{task_id}")
                response.raise_for_status()
                data = response.json()
                
                status = data.get("status", "").lower()
                
                if status in ("complete", "completed", "done"):
                    songs_data = data.get("songs") or data.get("data", [])
                    songs = [
                        SunoSong(
                            id=s.get("id", ""),
                            title=s.get("title", ""),
                            audio_url=s.get("audioUrl") or s.get("audio_url"),
                            stream_url=s.get("streamAudioUrl") or s.get("stream_url"),
                            image_url=s.get("imageUrl") or s.get("image_url"),
                            duration=s.get("duration"),
                            status="complete",
                        )
                        for s in songs_data
                    ]
                    return SunoResult(
                        success=True,
                        task_id=task_id,
                        songs=songs,
                    )
                
                if status in ("failed", "error"):
                    error = data.get("error") or data.get("message") or "Generation failed"
                    return SunoResult(
                        success=False,
                        task_id=task_id,
                        error=error,
                    )
                
                # Still processing
                await asyncio.sleep(SunoConfig.POLL_INTERVAL)
                
            except Exception as e:
                logger.warning(f"Poll error for {task_id}: {e}")
                await asyncio.sleep(SunoConfig.POLL_INTERVAL)
    
    async def get_task_status(self, task_id: str) -> SunoMusicResponse:
        """Get status of a generation task."""
        try:
            client = self._get_client()
            response = await client.get(f"/tasks/{task_id}")
            response.raise_for_status()
            data = response.json()
            
            return SunoMusicResponse(
                task_id=task_id,
                status=data.get("status", "unknown"),
                songs=data.get("songs", []),
            )
        except Exception as e:
            return SunoMusicResponse(
                task_id=task_id,
                status="error",
                error=str(e),
            )


# =============================================================================
# Factory Function
# =============================================================================

def get_suno_service(api_key: Optional[str] = None) -> SunoService:
    """
    Get Suno service instance.
    
    Args:
        api_key: Optional API key override
        
    Returns:
        SunoService instance
    """
    from app.config import settings
    
    key = api_key or getattr(settings, "SUNO_API_KEY", None)
    return SunoService(api_key=key)
