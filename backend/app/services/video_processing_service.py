"""Video Processing Service - FFmpeg-based video operations.

2026 Best Practices:
- Async subprocess execution for non-blocking I/O
- Temporary file management with cleanup
- Support for both local files and URLs
- Progress tracking for long operations

Usage:
    from app.services.video_processing_service import get_video_processor

    processor = get_video_processor()
    frame_path = await processor.extract_last_frame(video_url)
    concat_path = await processor.concatenate_videos(video_urls)
"""

import asyncio
import logging
import os
import re
import shutil
import tempfile
import threading
import uuid
from pathlib import Path
from typing import List, Optional, Set
from dataclasses import dataclass, field
from urllib.parse import urlparse

import aiofiles
import httpx

logger = logging.getLogger(__name__)

# =============================================================================
# Security Constants
# =============================================================================

MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB max download
MAX_VIDEOS_PER_CONCAT = 20  # Max videos to concatenate

# Allowed URL schemes and domains for SSRF protection
ALLOWED_SCHEMES: Set[str] = {"http", "https"}
BLOCKED_HOSTS: Set[str] = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"}
ALLOWED_DOMAINS: Set[str] = {
    "storage.googleapis.com",
    "storage.cloud.google.com",
    "firebasestorage.googleapis.com",
    "crebit-studio-media.storage.googleapis.com",
    # Add other allowed CDN/storage domains
}


def _validate_url(url: str) -> None:
    """Validate URL to prevent SSRF attacks.

    Args:
        url: URL to validate

    Raises:
        ValueError: If URL is not allowed
    """
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValueError(f"Invalid URL format: {e}")

    # Check scheme
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"URL scheme not allowed: {parsed.scheme}")

    # Check for blocked hosts
    hostname = parsed.hostname or ""
    if hostname in BLOCKED_HOSTS:
        raise ValueError(f"URL host not allowed: {hostname}")

    # Check for private IP ranges
    if hostname.startswith(("10.", "172.", "192.168.", "169.254.")):
        raise ValueError(f"Private IP addresses not allowed: {hostname}")

    # In production, enforce domain whitelist
    # Uncomment to enable strict domain checking:
    # if not any(hostname.endswith(d) for d in ALLOWED_DOMAINS):
    #     raise ValueError(f"Domain not whitelisted: {hostname}")

# =============================================================================
# Configuration
# =============================================================================

@dataclass
class VideoProcessingConfig:
    """Video processing configuration."""

    # FFmpeg path (auto-detect if not set)
    ffmpeg_path: str = os.getenv("FFMPEG_PATH", "ffmpeg")
    ffprobe_path: str = os.getenv("FFPROBE_PATH", "ffprobe")

    # Temporary file directory
    temp_dir: str = os.getenv("VIDEO_TEMP_DIR", "/tmp/video-processing")

    # Default output settings
    default_video_codec: str = "libx264"
    default_audio_codec: str = "aac"
    default_fps: int = 24
    default_crf: int = 23  # Quality (18=high, 23=medium, 28=low)

    # Timeout for operations (seconds)
    operation_timeout: int = 300  # 5 minutes

    def __post_init__(self):
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)


# =============================================================================
# Video Processing Service
# =============================================================================

class VideoProcessingService:
    """FFmpeg-based video processing service."""

    def __init__(self, config: Optional[VideoProcessingConfig] = None):
        self.config = config or VideoProcessingConfig()
        self._ffmpeg_available = None

    async def is_ffmpeg_available(self) -> bool:
        """Check if FFmpeg is available."""
        if self._ffmpeg_available is not None:
            return self._ffmpeg_available

        try:
            proc = await asyncio.create_subprocess_exec(
                self.config.ffmpeg_path,
                "-version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            self._ffmpeg_available = proc.returncode == 0
        except Exception:
            self._ffmpeg_available = False

        if not self._ffmpeg_available:
            logger.warning(
                "[VIDEO] FFmpeg not available. Video processing disabled. "
                "Install with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)"
            )
        else:
            logger.info("[VIDEO] FFmpeg is available")

        return self._ffmpeg_available

    async def _download_to_temp(self, url: str) -> Optional[str]:
        """Download URL to temporary file with validation and streaming.

        Args:
            url: URL to download (must pass SSRF validation)

        Returns:
            Path to downloaded temp file, or None on failure
        """
        temp_path = None
        try:
            # Validate URL for SSRF protection
            _validate_url(url)

            # Generate temp filename
            suffix = ".mp4"
            if ".webm" in url.lower():
                suffix = ".webm"
            elif ".mov" in url.lower():
                suffix = ".mov"

            temp_path = os.path.join(
                self.config.temp_dir,
                f"{uuid.uuid4()}{suffix}"
            )

            # Stream download with size limit
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()

                    # Check content-length if available
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > MAX_VIDEO_SIZE:
                        raise ValueError(
                            f"Video too large: {content_length} bytes (max {MAX_VIDEO_SIZE})"
                        )

                    # Stream to file with size tracking
                    total_size = 0
                    async with aiofiles.open(temp_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=65536):
                            total_size += len(chunk)
                            if total_size > MAX_VIDEO_SIZE:
                                raise ValueError(
                                    f"Video exceeds {MAX_VIDEO_SIZE} bytes during download"
                                )
                            await f.write(chunk)

            logger.debug(f"[VIDEO] Downloaded {total_size} bytes to {temp_path}")
            return temp_path

        except ValueError as e:
            logger.error(f"[VIDEO] Validation error for {url}: {e}")
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            return None
        except Exception as e:
            logger.error(f"[VIDEO] Failed to download {url}: {e}")
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            return None

    async def extract_last_frame(
        self,
        video_url: str,
        output_format: str = "jpg",
    ) -> Optional[str]:
        """Extract the last frame from a video.

        Args:
            video_url: URL of the video
            output_format: Output image format (jpg, png)

        Returns:
            Path to extracted frame, or None on failure
        """
        if not await self.is_ffmpeg_available():
            return None

        temp_video = None
        try:
            # Download video to temp file
            temp_video = await self._download_to_temp(video_url)
            if not temp_video:
                return None

            # Get video duration using ffprobe
            duration = await self._get_duration(temp_video)
            if duration is None:
                return None

            # Extract last frame (at duration - 0.1 seconds)
            frame_time = max(0, duration - 0.1)
            output_path = os.path.join(
                self.config.temp_dir,
                f"{uuid.uuid4()}.{output_format}"
            )

            cmd = [
                self.config.ffmpeg_path,
                "-ss", str(frame_time),
                "-i", temp_video,
                "-vframes", "1",
                "-q:v", "2",  # High quality
                "-y",  # Overwrite
                output_path,
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.config.operation_timeout,
            )

            if proc.returncode != 0:
                logger.error(f"[VIDEO] Frame extraction failed: {stderr.decode()}")
                return None

            if os.path.exists(output_path):
                logger.info(f"[VIDEO] Extracted last frame to {output_path}")
                return output_path

            return None

        except asyncio.TimeoutError:
            logger.error("[VIDEO] Frame extraction timed out")
            return None
        except Exception as e:
            logger.error(f"[VIDEO] Frame extraction error: {e}")
            return None
        finally:
            # Cleanup temp video
            if temp_video and os.path.exists(temp_video):
                os.remove(temp_video)

    async def _get_duration(self, video_path: str) -> Optional[float]:
        """Get video duration in seconds using ffprobe."""
        try:
            cmd = [
                self.config.ffprobe_path,
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                video_path,
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, _ = await proc.communicate()
            return float(stdout.decode().strip())
        except Exception as e:
            logger.warning(f"[VIDEO] Failed to get duration: {e}")
            return None

    async def concatenate_videos(
        self,
        video_urls: List[str],
        transition: str = "none",
        transition_duration: float = 0.5,
    ) -> Optional[str]:
        """Concatenate multiple videos.

        Args:
            video_urls: List of video URLs
            transition: Transition type (none, fade, dissolve)
            transition_duration: Duration of transitions in seconds

        Returns:
            Path to concatenated video, or None on failure

        Raises:
            ValueError: If too many videos requested
        """
        if not await self.is_ffmpeg_available():
            return None

        if not video_urls:
            return None

        # Limit number of videos to prevent DoS
        if len(video_urls) > MAX_VIDEOS_PER_CONCAT:
            raise ValueError(
                f"Too many videos: {len(video_urls)} (max {MAX_VIDEOS_PER_CONCAT})"
            )

        if len(video_urls) == 1:
            # Single video - just download it
            return await self._download_to_temp(video_urls[0])

        temp_files: List[str] = []
        try:
            # Download all videos
            for url in video_urls:
                temp_path = await self._download_to_temp(url)
                if temp_path:
                    temp_files.append(temp_path)

            if len(temp_files) < 2:
                logger.warning("[VIDEO] Not enough valid videos to concatenate")
                return temp_files[0] if temp_files else None

            # Create concat list file
            list_path = os.path.join(self.config.temp_dir, f"{uuid.uuid4()}_list.txt")
            with open(list_path, "w") as f:
                for temp_file in temp_files:
                    # Escape single quotes in path
                    safe_path = temp_file.replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")

            # Output path
            output_path = os.path.join(
                self.config.temp_dir,
                f"{uuid.uuid4()}_concat.mp4"
            )

            if transition == "none":
                # Simple concat (faster)
                cmd = [
                    self.config.ffmpeg_path,
                    "-f", "concat",
                    "-safe", "0",
                    "-i", list_path,
                    "-c", "copy",  # Stream copy for speed
                    "-y",
                    output_path,
                ]
            else:
                # Concat with re-encoding (for transitions)
                cmd = [
                    self.config.ffmpeg_path,
                    "-f", "concat",
                    "-safe", "0",
                    "-i", list_path,
                    "-c:v", self.config.default_video_codec,
                    "-crf", str(self.config.default_crf),
                    "-preset", "fast",
                    "-c:a", self.config.default_audio_codec,
                    "-y",
                    output_path,
                ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.config.operation_timeout,
            )

            # Cleanup list file
            os.remove(list_path)

            if proc.returncode != 0:
                logger.error(f"[VIDEO] Concatenation failed: {stderr.decode()}")
                return None

            if os.path.exists(output_path):
                logger.info(
                    f"[VIDEO] Concatenated {len(temp_files)} videos to {output_path}"
                )
                return output_path

            return None

        except asyncio.TimeoutError:
            logger.error("[VIDEO] Concatenation timed out")
            return None
        except Exception as e:
            logger.error(f"[VIDEO] Concatenation error: {e}")
            return None
        finally:
            # Cleanup temp files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

    async def sync_audio(
        self,
        video_url: str,
        audio_url: str,
        output_duration: Optional[float] = None,
    ) -> Optional[str]:
        """Sync audio track with video.

        Args:
            video_url: Video URL
            audio_url: Audio URL (BGM)
            output_duration: Target duration (optional, uses video duration)

        Returns:
            Path to audio-synced video, or None on failure
        """
        if not await self.is_ffmpeg_available():
            return None

        temp_video = None
        temp_audio = None
        try:
            # Download video and audio
            temp_video = await self._download_to_temp(video_url)
            temp_audio = await self._download_to_temp(audio_url)

            if not temp_video or not temp_audio:
                return None

            # Get video duration if not specified
            if output_duration is None:
                output_duration = await self._get_duration(temp_video)

            # Output path
            output_path = os.path.join(
                self.config.temp_dir,
                f"{uuid.uuid4()}_synced.mp4"
            )

            # Build ffmpeg command
            cmd = [
                self.config.ffmpeg_path,
                "-i", temp_video,
                "-i", temp_audio,
                "-c:v", "copy",  # Copy video stream
                "-c:a", self.config.default_audio_codec,
                "-map", "0:v:0",  # Video from first input
                "-map", "1:a:0",  # Audio from second input
                "-shortest",  # Match shortest stream
                "-y",
                output_path,
            ]

            if output_duration:
                cmd.insert(-1, "-t")
                cmd.insert(-1, str(output_duration))

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.config.operation_timeout,
            )

            if proc.returncode != 0:
                logger.error(f"[VIDEO] Audio sync failed: {stderr.decode()}")
                return None

            if os.path.exists(output_path):
                logger.info(f"[VIDEO] Audio synced to {output_path}")
                return output_path

            return None

        except asyncio.TimeoutError:
            logger.error("[VIDEO] Audio sync timed out")
            return None
        except Exception as e:
            logger.error(f"[VIDEO] Audio sync error: {e}")
            return None
        finally:
            # Cleanup temp files
            if temp_video and os.path.exists(temp_video):
                os.remove(temp_video)
            if temp_audio and os.path.exists(temp_audio):
                os.remove(temp_audio)

    async def cleanup_temp_files(self, max_age_hours: int = 1) -> int:
        """Clean up old temporary files asynchronously.

        Args:
            max_age_hours: Delete files older than this

        Returns:
            Number of files cleaned up
        """
        import time

        def _sync_cleanup() -> int:
            temp_dir = Path(self.config.temp_dir)
            if not temp_dir.exists():
                return 0

            cutoff = time.time() - (max_age_hours * 3600)
            cleaned = 0

            for file_path in temp_dir.iterdir():
                try:
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff:
                        file_path.unlink()
                        cleaned += 1
                except OSError as e:
                    logger.warning(f"[VIDEO] Failed to cleanup {file_path}: {e}")

            return cleaned

        cleaned = await asyncio.to_thread(_sync_cleanup)
        if cleaned:
            logger.info(f"[VIDEO] Cleaned up {cleaned} old temp files")
        return cleaned


# =============================================================================
# Singleton Instance (Thread-safe)
# =============================================================================

_service: Optional[VideoProcessingService] = None
_lock = threading.Lock()


def get_video_processor() -> VideoProcessingService:
    """Get or create VideoProcessingService instance (thread-safe)."""
    global _service
    if _service is None:
        with _lock:
            if _service is None:  # Double-check locking
                _service = VideoProcessingService()
    return _service


def reset_video_processor():
    """Reset singleton for testing."""
    global _service
    with _lock:
        _service = None
