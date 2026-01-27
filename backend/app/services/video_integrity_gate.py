"""
Video Integrity Gate - Download Validation Layer

다운로드된 비디오 파일의 정합성을 검증하는 게이트.
분석 파이프라인 진입 전 반드시 통과해야 함.

검증 순서:
1. 파일 존재 및 최소 크기 (10KB)
2. FFprobe 메타데이터 (fps, width, height 필수)
3. FFmpeg null decode (선택적, 전체 프레임 무결성)

Usage:
    from app.services.video_integrity_gate import (
        validate_video_integrity,
        VideoIntegrityResult,
        VideoIntegrityError,
    )

    result = validate_video_integrity(video_path)
    if not result.is_valid:
        raise VideoIntegrityError(result.error_message)

References:
- https://reelmind.ai/blog/how-to-use-ffmpeg-to-check-videos-integrity-technical-verification
- https://johannesfilter.com/verify-integrity-of-videos-files-with-ffmpeg/
"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from typing import Optional, List

logger = logging.getLogger(__name__)

# Validation thresholds
MIN_FILE_SIZE_BYTES = 10 * 1024  # 10KB minimum
MAX_FFPROBE_TIMEOUT = 30  # seconds
MAX_FFMPEG_DECODE_TIMEOUT = 120  # seconds for full decode check


class VideoIntegrityError(Exception):
    """비디오 무결성 검증 실패"""

    pass


@dataclass
class VideoMetadataResult:
    """FFprobe 메타데이터 결과"""

    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    duration_sec: Optional[float] = None
    codec_name: Optional[str] = None
    has_audio: bool = False

    @property
    def is_valid(self) -> bool:
        """필수 메타데이터 존재 여부"""
        return (
            self.width is not None
            and self.width > 0
            and self.height is not None
            and self.height > 0
            and self.fps is not None
            and self.fps > 0
        )


@dataclass
class VideoIntegrityResult:
    """비디오 무결성 검증 결과"""

    is_valid: bool = False
    file_exists: bool = False
    file_size_bytes: int = 0

    # Metadata (from ffprobe)
    metadata: Optional[VideoMetadataResult] = None

    # Full decode check (optional)
    decode_checked: bool = False
    decode_errors: List[str] = field(default_factory=list)

    # Error info
    error_stage: Optional[str] = None  # "file", "ffprobe", "decode"
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "file_exists": self.file_exists,
            "file_size_bytes": self.file_size_bytes,
            "metadata": {
                "width": self.metadata.width if self.metadata else None,
                "height": self.metadata.height if self.metadata else None,
                "fps": self.metadata.fps if self.metadata else None,
                "duration_sec": self.metadata.duration_sec if self.metadata else None,
                "codec_name": self.metadata.codec_name if self.metadata else None,
                "has_audio": self.metadata.has_audio if self.metadata else False,
            }
            if self.metadata
            else None,
            "decode_checked": self.decode_checked,
            "decode_errors": self.decode_errors,
            "error_stage": self.error_stage,
            "error_message": self.error_message,
        }


def _check_file_exists(video_path: str) -> tuple[bool, int, Optional[str]]:
    """파일 존재 및 최소 크기 확인"""
    if not os.path.exists(video_path):
        return False, 0, f"File does not exist: {video_path}"

    file_size = os.path.getsize(video_path)
    if file_size < MIN_FILE_SIZE_BYTES:
        return False, file_size, f"File too small: {file_size} bytes (min: {MIN_FILE_SIZE_BYTES})"

    return True, file_size, None


def _run_ffprobe(video_path: str) -> VideoMetadataResult:
    """
    FFprobe로 메타데이터 추출

    실패 시 빈 VideoMetadataResult 반환 (is_valid=False)
    """
    result = VideoMetadataResult()

    try:
        # Video stream info
        proc = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", "-show_format", video_path],
            capture_output=True,
            text=True,
            timeout=MAX_FFPROBE_TIMEOUT,
        )

        if proc.returncode != 0:
            logger.warning(f"[IntegrityGate] ffprobe failed: {proc.stderr[:200]}")
            return result

        data = json.loads(proc.stdout)
        streams = data.get("streams", [])
        format_info = data.get("format", {})

        # Find video stream
        video_stream = None
        for stream in streams:
            if stream.get("codec_type") == "video":
                video_stream = stream
            elif stream.get("codec_type") == "audio":
                result.has_audio = True

        if not video_stream:
            logger.warning("[IntegrityGate] No video stream found")
            return result

        # Extract metadata
        result.width = video_stream.get("width")
        result.height = video_stream.get("height")
        result.codec_name = video_stream.get("codec_name")

        # FPS calculation (avg_frame_rate: "30/1" or "30000/1001")
        fps_str = video_stream.get("avg_frame_rate", "0/1")
        if "/" in fps_str:
            num, denom = fps_str.split("/")
            if int(denom) > 0:
                result.fps = round(int(num) / int(denom), 2)

        # Duration (from format or stream)
        duration = format_info.get("duration") or video_stream.get("duration")
        if duration:
            try:
                result.duration_sec = float(duration)
            except (ValueError, TypeError):
                pass

        return result

    except subprocess.TimeoutExpired:
        logger.warning(f"[IntegrityGate] ffprobe timeout: {video_path}")
        return result
    except json.JSONDecodeError as e:
        logger.warning(f"[IntegrityGate] ffprobe JSON parse error: {e}")
        return result
    except Exception as e:
        logger.warning(f"[IntegrityGate] ffprobe error: {e}")
        return result


def _run_ffmpeg_decode_check(video_path: str) -> tuple[bool, List[str]]:
    """
    FFmpeg null decode로 전체 프레임 무결성 검사

    ffmpeg -v error -i file.mp4 -f null -
    빈 출력 = 유효, 출력 있음 = 손상된 프레임

    Returns:
        (is_valid, error_list)
    """
    try:
        proc = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", video_path, "-f", "null", "-"],
            capture_output=True,
            text=True,
            timeout=MAX_FFMPEG_DECODE_TIMEOUT,
        )

        # Collect errors from stderr
        errors = []
        if proc.stderr:
            # Filter meaningful errors (skip warnings)
            for line in proc.stderr.strip().split("\n"):
                line = line.strip()
                if line and "error" in line.lower():
                    errors.append(line[:200])  # Truncate long lines

        # returncode != 0 or errors present = invalid
        is_valid = proc.returncode == 0 and len(errors) == 0

        if not is_valid:
            logger.warning(f"[IntegrityGate] FFmpeg decode found {len(errors)} errors")

        return is_valid, errors[:10]  # Max 10 errors

    except subprocess.TimeoutExpired:
        logger.warning(f"[IntegrityGate] ffmpeg decode timeout: {video_path}")
        return False, ["Decode timeout exceeded"]
    except Exception as e:
        logger.warning(f"[IntegrityGate] ffmpeg decode error: {e}")
        return False, [str(e)]


def validate_video_integrity(
    video_path: str,
    check_decode: bool = False,
) -> VideoIntegrityResult:
    """
    비디오 파일 무결성 검증

    Args:
        video_path: 비디오 파일 경로
        check_decode: FFmpeg full decode 검사 여부 (느리지만 정확)

    Returns:
        VideoIntegrityResult
    """
    result = VideoIntegrityResult()

    # Stage 1: File existence and size
    file_ok, file_size, file_error = _check_file_exists(video_path)
    result.file_size_bytes = file_size
    result.file_exists = file_ok

    if not file_ok:
        result.error_stage = "file"
        result.error_message = file_error
        logger.warning(f"[IntegrityGate] File check failed: {file_error}")
        return result

    # Stage 2: FFprobe metadata
    metadata = _run_ffprobe(video_path)
    result.metadata = metadata

    if not metadata.is_valid:
        result.error_stage = "ffprobe"
        missing = []
        if not metadata.width:
            missing.append("width")
        if not metadata.height:
            missing.append("height")
        if not metadata.fps:
            missing.append("fps")
        result.error_message = f"Missing metadata: {', '.join(missing)}"
        logger.warning(f"[IntegrityGate] Metadata invalid: {result.error_message}")
        return result

    # Stage 3: Optional full decode check
    if check_decode:
        decode_ok, decode_errors = _run_ffmpeg_decode_check(video_path)
        result.decode_checked = True
        result.decode_errors = decode_errors

        if not decode_ok:
            result.error_stage = "decode"
            result.error_message = f"Decode errors: {len(decode_errors)}"
            logger.warning(f"[IntegrityGate] Decode check failed: {decode_errors[:3]}")
            return result

    # All checks passed
    result.is_valid = True
    logger.info(
        f"[IntegrityGate] Valid: {video_path} "
        f"({metadata.width}x{metadata.height} @ {metadata.fps}fps, "
        f"{file_size / 1024:.1f}KB)"
    )

    return result


def require_valid_video(video_path: str, check_decode: bool = False) -> VideoMetadataResult:
    """
    비디오 무결성 검증 후 메타데이터 반환 (실패 시 예외)

    Args:
        video_path: 비디오 파일 경로
        check_decode: FFmpeg full decode 검사 여부

    Returns:
        VideoMetadataResult (fps, width, height 등)

    Raises:
        VideoIntegrityError: 검증 실패 시
    """
    result = validate_video_integrity(video_path, check_decode=check_decode)

    if not result.is_valid:
        raise VideoIntegrityError(f"Video integrity check failed at '{result.error_stage}': " f"{result.error_message}")

    return result.metadata
