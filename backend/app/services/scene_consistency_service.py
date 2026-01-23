"""Scene Consistency Service - Episode Sequence Generation.

Core service for generating consistent multi-scene video sequences.

Features:
- End Frame extraction for scene continuity
- Character Ingredients injection (max 3 per scene)
- Scene transition generation (fade/dissolve/cut)
- Audio sync with Suno BGM

2026 Best Practices:
- Veo 3.1 Scene Extension for continuity
- Character memory bank integration
- Multi-scene storyline coherence

References:
- Veo 3.1: 7-second extensions, up to 148 seconds total
- StoryMem: arXiv:2512.19539 for character consistency
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Prompt Sanitization Utilities
# =============================================================================

MAX_FIELD_LENGTH = 100
UNSAFE_CHARS = re.compile(r'[\[\]{}()<>"|;`$\\]')


def _sanitize_prompt_input(value: str, max_length: int = MAX_FIELD_LENGTH) -> str:
    """Sanitize user input for prompt injection prevention.

    Strips unsafe characters and limits length.

    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    return UNSAFE_CHARS.sub('', value.strip()[:max_length])


# =============================================================================
# Constants
# =============================================================================

MAX_SCENES_PER_SEQUENCE = 10  # Reasonable limit for one episode
MAX_EXTENSION_COUNT = 20  # Veo 3.1 max extensions
EXTENSION_SECONDS = 7  # Each extension adds 7 seconds
MAX_VIDEO_DURATION = 148  # 7 * 21 = 147, rounded up

# Transition durations in milliseconds
TRANSITION_DURATIONS = {
    "cut": 0,
    "fade": 500,
    "dissolve": 1000,
    "wipe": 750,
}


# =============================================================================
# Enums
# =============================================================================

class TransitionType(str, Enum):
    """Scene transition types."""
    CUT = "cut"
    FADE = "fade"
    DISSOLVE = "dissolve"
    WIPE = "wipe"


class SequenceStatus(str, Enum):
    """Sequence generation status."""
    PENDING = "pending"
    GENERATING = "generating"
    CONCATENATING = "concatenating"
    AUDIO_SYNC = "audio_sync"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class SceneConfig:
    """Configuration for a single scene."""
    scene_id: str
    prompt: str
    duration_seconds: int = 8
    transition_to_next: TransitionType = TransitionType.CUT
    character_ids: Optional[List[str]] = None
    style_hints: Optional[Dict[str, Any]] = None


@dataclass
class SceneClip:
    """Generated scene clip with metadata."""
    scene_id: str
    video_url: str
    start_frame_url: Optional[str] = None  # First frame for continuity reference
    end_frame_url: Optional[str] = None    # Last frame for next scene reference
    prompt: str = ""
    duration_seconds: int = 0
    transition: TransitionType = TransitionType.CUT
    generation_time_ms: int = 0
    character_ids: List[str] = field(default_factory=list)


@dataclass
class StyleGuide:
    """Visual style guide for sequence consistency."""
    color_palette: Optional[List[str]] = None
    lighting: Optional[str] = None
    camera_style: Optional[str] = None
    mood: Optional[str] = None
    reference_images: Optional[List[str]] = None
    auteur_blend: Optional[Dict[str, float]] = None  # Director style mix


@dataclass
class SequenceProgress:
    """Progress update during sequence generation."""
    status: SequenceStatus
    current_scene: int
    total_scenes: int
    elapsed_seconds: float
    estimated_remaining_seconds: Optional[float] = None
    current_scene_name: str = ""
    message: str = ""


@dataclass
class SequenceResult:
    """Result from sequence generation."""
    success: bool
    sequence_id: str
    clips: List[SceneClip] = field(default_factory=list)
    concatenated_url: Optional[str] = None
    total_duration_seconds: int = 0
    audio_sync_url: Optional[str] = None
    generation_time_ms: int = 0
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# =============================================================================
# Scene Consistency Service
# =============================================================================

class SceneConsistencyService:
    """Multi-scene video sequence generation with character consistency.
    
    Workflow:
    1. Parse scene configs and style guide
    2. For each scene:
       a. Extract end frame from previous scene (if exists)
       b. Inject character ingredients (max 3)
       c. Generate video with Veo 3.1
       d. Extract end frame for next scene
    3. Concatenate all clips with transitions
    4. Sync audio track (if provided)
    5. Return final episode URL
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize service.
        
        Args:
            api_key: Optional API key override for Veo/Gemini
        """
        self._api_key = api_key

    async def generate_sequence(
        self,
        db: AsyncSession,
        user_id: str,
        scenes: List[SceneConfig],
        style_guide: Optional[StyleGuide] = None,
        audio_track_url: Optional[str] = None,
        progress_callback: Optional[Callable[[SequenceProgress], None]] = None,
    ) -> SequenceResult:
        """Generate multi-scene video sequence.
        
        Args:
            db: Database session
            user_id: User ID for character access
            scenes: List of scene configurations
            style_guide: Visual style guide for consistency
            audio_track_url: Optional Suno BGM URL
            progress_callback: Optional progress callback
            
        Returns:
            SequenceResult with concatenated video or error
        """
        # Safe imports with fallback
        try:
            from app.services.veo_service import VeoConfig, VeoResult, get_veo_service
        except ImportError as e:
            logger.error(f"[SEQ_GEN] VeoService import failed: {e}")
            return SequenceResult(
                success=False,
                sequence_id=str(uuid.uuid4()),
                error="VeoService를 불러올 수 없습니다. 서버 설정을 확인하세요.",
            )
        
        try:
            from app.services.character_veo_service import get_character_veo_service
            char_veo_service = get_character_veo_service()
        except ImportError:
            logger.warning("[SEQ_GEN] CharacterVeoService not available, character features disabled")
            char_veo_service = None

        sequence_id = str(uuid.uuid4())
        start_time = time.monotonic()
        clips: List[SceneClip] = []
        
        # Validate input
        if not scenes:
            return SequenceResult(
                success=False,
                sequence_id=sequence_id,
                error="최소 1개 이상의 씬이 필요합니다.",
            )
        
        if len(scenes) > MAX_SCENES_PER_SEQUENCE:
            return SequenceResult(
                success=False,
                sequence_id=sequence_id,
                error=f"씬은 최대 {MAX_SCENES_PER_SEQUENCE}개까지 가능합니다.",
            )

        def emit_progress(
            status: SequenceStatus,
            current_scene: int,
            message: str = "",
        ):
            if progress_callback:
                try:
                    elapsed = time.monotonic() - start_time
                    avg_time_per_scene = elapsed / max(current_scene, 1)
                    remaining_scenes = len(scenes) - current_scene
                    estimated_remaining = avg_time_per_scene * remaining_scenes if current_scene > 0 else None

                    scene_name = scenes[current_scene - 1].scene_id if current_scene > 0 else ""
                    progress_callback(SequenceProgress(
                        status=status,
                        current_scene=current_scene,
                        total_scenes=len(scenes),
                        elapsed_seconds=elapsed,
                        estimated_remaining_seconds=estimated_remaining,
                        current_scene_name=scene_name,
                        message=message,
                    ))
                except Exception as e:
                    logger.warning(f"[SEQ_GEN] Progress callback failed: {e}")

        logger.info(f"[SEQ_GEN] Starting sequence {sequence_id} with {len(scenes)} scenes")
        emit_progress(SequenceStatus.GENERATING, 0, "시퀀스 생성 시작...")

        veo_service = get_veo_service(self._api_key)

        prev_end_frame_url: Optional[str] = None
        
        try:
            for idx, scene in enumerate(scenes, 1):
                emit_progress(
                    SequenceStatus.GENERATING,
                    idx,
                    f"씬 {idx}/{len(scenes)} 생성 중: {scene.scene_id}",
                )
                
                # Build enhanced prompt with style guide
                enhanced_prompt = self._enhance_prompt(
                    scene.prompt,
                    style_guide,
                    prev_end_frame_url,
                )
                
                scene_start = time.monotonic()
                
                # Generate with or without characters
                veo_result = None
                if scene.character_ids and char_veo_service:
                    try:
                        config = VeoConfig(
                            prompt=enhanced_prompt,
                            duration_seconds=scene.duration_seconds,
                            include_audio=True,
                        )
                        gen_result = await char_veo_service.generate_with_characters(
                            db=db,
                            user_id=user_id,
                            config=config,
                            character_ids=scene.character_ids,
                            api_key=self._api_key,
                        )
                        veo_result = gen_result.veo_result
                    except Exception as char_err:
                        logger.warning(f"[SEQ_GEN] Character generation failed, fallback to simple: {char_err}")
                        veo_result = None
                
                # Fallback to simple generation
                if veo_result is None:
                    try:
                        veo_result = await veo_service.generate_video_simple(
                            prompt=enhanced_prompt,
                            duration_seconds=scene.duration_seconds,
                            include_audio=True,
                        )
                    except AttributeError:
                        # generate_video_simple may not exist, try generate_video
                        config = VeoConfig(
                            prompt=enhanced_prompt,
                            duration_seconds=scene.duration_seconds,
                            include_audio=True,
                        )
                        veo_result = await veo_service.generate_video(config=config)
                
                scene_time = int((time.monotonic() - scene_start) * 1000)
                
                if not veo_result.success:
                    logger.error(f"[SEQ_GEN] Scene {idx} failed: {veo_result.error}")
                    return SequenceResult(
                        success=False,
                        sequence_id=sequence_id,
                        clips=clips,
                        error=f"씬 {idx} 생성 실패: {veo_result.error}",
                        generation_time_ms=int((time.monotonic() - start_time) * 1000),
                    )
                
                # Extract end frame for next scene (async)
                end_frame_url = await self._extract_end_frame(
                    veo_result.video_uri,
                    scene.scene_id,
                )
                
                clip = SceneClip(
                    scene_id=scene.scene_id,
                    video_url=veo_result.video_uri,
                    start_frame_url=prev_end_frame_url,
                    end_frame_url=end_frame_url,
                    prompt=scene.prompt,
                    duration_seconds=scene.duration_seconds,
                    transition=scene.transition_to_next,
                    generation_time_ms=scene_time,
                    character_ids=scene.character_ids or [],
                )
                clips.append(clip)
                
                # Update for next iteration
                prev_end_frame_url = end_frame_url
                
                logger.info(f"[SEQ_GEN] Scene {idx} completed in {scene_time}ms")

            # Concatenate clips
            emit_progress(
                SequenceStatus.CONCATENATING,
                len(scenes),
                "클립 연결 중...",
            )
            
            concatenated_url = await self._concatenate_clips(clips)
            total_duration = sum(c.duration_seconds for c in clips)
            
            # Audio sync if provided
            audio_synced_url = None
            if audio_track_url and concatenated_url:
                emit_progress(
                    SequenceStatus.AUDIO_SYNC,
                    len(scenes),
                    "오디오 싱크 중...",
                )
                audio_synced_url = await self._sync_audio(
                    concatenated_url,
                    audio_track_url,
                    total_duration,
                )
            
            generation_time_ms = int((time.monotonic() - start_time) * 1000)
            
            emit_progress(SequenceStatus.COMPLETED, len(scenes), "시퀀스 생성 완료!")
            
            logger.info(
                f"[SEQ_GEN] Sequence {sequence_id} completed: "
                f"{len(clips)} clips, {total_duration}s, {generation_time_ms}ms"
            )
            
            return SequenceResult(
                success=True,
                sequence_id=sequence_id,
                clips=clips,
                concatenated_url=audio_synced_url or concatenated_url,
                total_duration_seconds=total_duration,
                audio_sync_url=audio_synced_url,
                generation_time_ms=generation_time_ms,
                metadata={
                    "scene_count": len(clips),
                    "style_guide": style_guide.__dict__ if style_guide else None,
                    "has_audio": audio_synced_url is not None,
                },
            )

        except Exception as e:
            logger.exception(f"[SEQ_GEN] Sequence generation error: {e}")
            emit_progress(SequenceStatus.FAILED, len(clips), str(e))
            return SequenceResult(
                success=False,
                sequence_id=sequence_id,
                clips=clips,
                error=f"시퀀스 생성 중 오류: {str(e)}",
                generation_time_ms=int((time.monotonic() - start_time) * 1000),
            )

    def _enhance_prompt(
        self,
        prompt: str,
        style_guide: Optional[StyleGuide],
        prev_end_frame_url: Optional[str],
    ) -> str:
        """Enhance prompt with style guide and continuity hints.

        Args:
            prompt: Original scene prompt
            style_guide: Visual style guide
            prev_end_frame_url: Previous scene's end frame

        Returns:
            Enhanced prompt
        """
        parts = [prompt]

        if style_guide:
            if style_guide.mood:
                sanitized_mood = _sanitize_prompt_input(style_guide.mood)
                parts.append(f"[Mood: {sanitized_mood}]")
            if style_guide.lighting:
                sanitized_lighting = _sanitize_prompt_input(style_guide.lighting)
                parts.append(f"[Lighting: {sanitized_lighting}]")
            if style_guide.camera_style:
                sanitized_camera = _sanitize_prompt_input(style_guide.camera_style)
                parts.append(f"[Camera: {sanitized_camera}]")
            if style_guide.color_palette:
                sanitized_colors = [_sanitize_prompt_input(c) for c in style_guide.color_palette[:5]]
                colors = ", ".join(sanitized_colors)
                parts.append(f"[Colors: {colors}]")

        if prev_end_frame_url:
            parts.append("[CONTINUITY: Match previous scene ending]")

        return " ".join(parts)

    async def _extract_end_frame(
        self,
        video_url: Optional[str],
        scene_id: str,
    ) -> Optional[str]:
        """Extract the last frame from a video for continuity.
        
        Uses Gemini to analyze video and extract key frame.
        
        Args:
            video_url: Video URL to extract from
            scene_id: Scene ID for naming
            
        Returns:
            URL of extracted end frame, or None
        """
        if not video_url:
            return None

        try:
            from app.services.video_processing_service import get_video_processor
            from app.services.storage_service import get_storage_service

            processor = get_video_processor()
            storage = get_storage_service()

            # Check if ffmpeg is available
            if not await processor.is_ffmpeg_available():
                logger.debug(f"[SEQ_GEN] FFmpeg not available, skipping frame extraction for {scene_id}")
                return None

            # Extract last frame using ffmpeg
            frame_path = await processor.extract_last_frame(video_url, output_format="jpg")
            if not frame_path:
                logger.warning(f"[SEQ_GEN] Failed to extract frame for {scene_id}")
                return None

            # Upload frame to storage
            import aiofiles
            async with aiofiles.open(frame_path, "rb") as f:
                frame_data = await f.read()

            frame_url = await storage.upload_image(
                frame_data,
                f"frames/{scene_id}/end_frame.jpg"
            )

            # Cleanup local temp file
            import os
            if os.path.exists(frame_path):
                os.remove(frame_path)

            logger.info(f"[SEQ_GEN] Extracted end frame for {scene_id}: {frame_url}")
            return frame_url

        except Exception as e:
            logger.warning(f"[SEQ_GEN] Failed to extract end frame: {e}")
            return None

    async def _concatenate_clips(
        self,
        clips: List[SceneClip],
    ) -> Optional[str]:
        """Concatenate video clips with transitions.
        
        Args:
            clips: List of scene clips to concatenate
            
        Returns:
            URL of concatenated video, or None
        """
        if not clips:
            return None

        if len(clips) == 1:
            return clips[0].video_url

        try:
            # Collect valid video URLs
            valid_urls = [c.video_url for c in clips if c.video_url]

            if not valid_urls:
                logger.warning("[SEQ_GEN] No valid video URLs to concatenate")
                return None

            if len(valid_urls) == 1:
                return valid_urls[0]

            from app.services.video_processing_service import get_video_processor
            from app.services.storage_service import get_storage_service

            processor = get_video_processor()
            storage = get_storage_service()

            # Check if ffmpeg is available
            if not await processor.is_ffmpeg_available():
                logger.info(
                    f"[SEQ_GEN] FFmpeg not available, returning first clip. "
                    f"Total {len(valid_urls)} clips available in result.clips"
                )
                return valid_urls[0]

            # Concatenate videos using ffmpeg
            concat_path = await processor.concatenate_videos(valid_urls)
            if not concat_path:
                logger.warning("[SEQ_GEN] Concatenation failed, returning first clip")
                return valid_urls[0]

            # Upload concatenated video to storage
            import aiofiles
            async with aiofiles.open(concat_path, "rb") as f:
                video_data = await f.read()

            import uuid
            concat_url = await storage.upload_video(
                video_data,
                f"sequences/{uuid.uuid4()}/concatenated.mp4"
            )

            # Cleanup local temp file
            import os
            if os.path.exists(concat_path):
                os.remove(concat_path)

            logger.info(f"[SEQ_GEN] Concatenated {len(valid_urls)} clips: {concat_url}")
            return concat_url

        except Exception as e:
            logger.error(f"[SEQ_GEN] Failed to concatenate clips: {e}")
            return None

    async def _sync_audio(
        self,
        video_url: str,
        audio_url: str,
        duration_seconds: int,
    ) -> Optional[str]:
        """Sync audio track with video.
        
        Args:
            video_url: Video URL
            audio_url: Audio track URL (Suno BGM)
            duration_seconds: Target duration
            
        Returns:
            URL of audio-synced video, or None
        """
        try:
            from app.services.video_processing_service import get_video_processor
            from app.services.storage_service import get_storage_service

            processor = get_video_processor()
            storage = get_storage_service()

            # Check if ffmpeg is available
            if not await processor.is_ffmpeg_available():
                logger.info("[SEQ_GEN] FFmpeg not available, returning video without audio sync")
                return video_url

            # Sync audio using ffmpeg
            synced_path = await processor.sync_audio(
                video_url,
                audio_url,
                output_duration=float(duration_seconds),
            )
            if not synced_path:
                logger.warning("[SEQ_GEN] Audio sync failed, returning original video")
                return video_url

            # Upload synced video to storage
            import aiofiles
            async with aiofiles.open(synced_path, "rb") as f:
                video_data = await f.read()

            import uuid
            synced_url = await storage.upload_video(
                video_data,
                f"sequences/{uuid.uuid4()}/audio_synced.mp4"
            )

            # Cleanup local temp file
            import os
            if os.path.exists(synced_path):
                os.remove(synced_path)

            logger.info(f"[SEQ_GEN] Audio synced: {synced_url}")
            return synced_url

        except Exception as e:
            logger.error(f"[SEQ_GEN] Failed to sync audio: {e}")
            return None


# =============================================================================
# Singleton Instance
# =============================================================================

_service: Optional[SceneConsistencyService] = None


def get_scene_consistency_service(api_key: Optional[str] = None) -> SceneConsistencyService:
    """Get or create SceneConsistencyService instance.
    
    Args:
        api_key: Optional API key override
        
    Returns:
        SceneConsistencyService instance
    """
    global _service
    if api_key:
        return SceneConsistencyService(api_key=api_key)
    if _service is None:
        _service = SceneConsistencyService()
    return _service


# =============================================================================
# Convenience Functions
# =============================================================================

async def generate_episode_sequence(
    db: AsyncSession,
    user_id: str,
    scenes: List[Dict[str, Any]],
    style_guide: Optional[Dict[str, Any]] = None,
    audio_track_url: Optional[str] = None,
    api_key: Optional[str] = None,
    progress_callback: Optional[Callable[[SequenceProgress], None]] = None,
) -> SequenceResult:
    """Convenience function to generate episode sequence.
    
    Args:
        db: Database session
        user_id: User ID
        scenes: List of scene dicts with keys: scene_id, prompt, duration_seconds, etc.
        style_guide: Optional style guide dict
        audio_track_url: Optional Suno BGM URL
        api_key: Optional API key override
        progress_callback: Optional progress callback
        
    Returns:
        SequenceResult
    """
    # Convert dicts to dataclasses
    scene_configs = [
        SceneConfig(
            scene_id=s.get("scene_id", f"scene_{i+1}"),
            prompt=s.get("prompt", ""),
            duration_seconds=s.get("duration_seconds", 8),
            transition_to_next=TransitionType(s.get("transition", "cut")),
            character_ids=s.get("character_ids"),
            style_hints=s.get("style_hints"),
        )
        for i, s in enumerate(scenes)
    ]
    
    style = None
    if style_guide:
        style = StyleGuide(
            color_palette=style_guide.get("color_palette"),
            lighting=style_guide.get("lighting"),
            camera_style=style_guide.get("camera_style"),
            mood=style_guide.get("mood"),
            reference_images=style_guide.get("reference_images"),
            auteur_blend=style_guide.get("auteur_blend"),
        )
    
    service = get_scene_consistency_service(api_key)
    return await service.generate_sequence(
        db=db,
        user_id=user_id,
        scenes=scene_configs,
        style_guide=style,
        audio_track_url=audio_track_url,
        progress_callback=progress_callback,
    )
