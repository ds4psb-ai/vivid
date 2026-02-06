"""
Scene Detection API
영상 업로드 → FFmpeg로 씬 감지 + 프레임 추출 → ZIP 반환
+ H.264 트랜스코딩 preview 서빙 (브라우저 코덱 호환성)
"""
import asyncio
import base64
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
import zipfile
from io import BytesIO
from math import ceil
from pathlib import Path
from fastapi import APIRouter, File, Form, Query, Request, UploadFile, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scene-detect", tags=["scene-detect"])

# ── Preview store (H.264 트랜스코딩된 영상 임시 저장) ──
_preview_store: dict[str, tuple[str, float]] = {}  # id → (path, created_at)
_PREVIEW_TTL = 1800  # 30분


def _cleanup_old_previews() -> None:
    """TTL 초과 preview 파일 정리"""
    now = time.time()
    expired = [pid for pid, (_, created) in _preview_store.items()
               if now - created > _PREVIEW_TTL]
    for pid in expired:
        path, _ = _preview_store.pop(pid)
        try:
            os.unlink(path)
        except OSError:
            pass


class SceneDetectResult(BaseModel):
    """씬 감지 결과"""
    timestamps: list[str]
    frame_count: int
    video_duration: float
    threshold: float
    preview_id: str | None = None


def run_ffmpeg_command(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    """FFmpeg 명령 실행"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="FFmpeg processing timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {str(e)}")


def detect_scenes(video_path: str, threshold: float = 0.19) -> list[str]:
    """
    FFmpeg로 씬 전환 타임스탬프 감지
    Antigravity와 동일한 방식
    """
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-vsync", "vfr",
        "-f", "null", "-"
    ]
    
    result = run_ffmpeg_command(cmd)
    
    # stderr에서 타임스탬프 추출 (showinfo 출력)
    timestamps = ["00:00.00"]  # 항상 첫 프레임 포함
    
    # pts_time 패턴 매칭
    pattern = r"pts_time:(\d+\.?\d*)"
    for match in re.finditer(pattern, result.stderr):
        pts_time = float(match.group(1))
        # 0.01초 단위로 올림
        pts_time = ceil(pts_time * 100) / 100
        # MM:SS.ms 형식으로 변환
        minutes = int(pts_time // 60)
        seconds = pts_time % 60
        timestamp = f"{minutes:02d}:{seconds:05.2f}"
        if timestamp not in timestamps:
            timestamps.append(timestamp)
    
    # 정렬
    timestamps.sort(key=lambda t: float(t.split(":")[0]) * 60 + float(t.split(":")[1]))
    
    return timestamps


def get_video_codec(video_path: str) -> str:
    """ffprobe로 비디오 코덱 확인"""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=codec_name",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout.strip().lower()
    except Exception:
        return ""


def _get_pixel_format(video_path: str) -> str:
    """ffprobe로 픽셀 포맷 확인"""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=pix_fmt",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout.strip().lower()
    except Exception:
        return ""


def create_web_preview(input_path: str, output_path: str) -> bool:
    """
    브라우저 호환 H.264/AAC MP4 생성.
    H.264 + yuv420p면 remux만 (초고속), 아니면 풀 트랜스코딩.
    - pix_fmt yuv420p 강제 (10-bit → 8-bit)
    - profile main / level 4.0 (HW 디코더 호환)
    - portrait/landscape 자동 대응 스케일 필터
    """
    codec = get_video_codec(input_path)
    pix_fmt = _get_pixel_format(input_path)

    if codec == "h264" and pix_fmt == "yuv420p":
        # remux only — 재인코딩 없이 컨테이너만 MP4로 변환
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            output_path,
        ]
    else:
        # 풀 트랜스코딩 → H.264 (max longest-side 1280, 짝수 보정)
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-c:v", "libx264", "-profile:v", "main", "-level:v", "4.0",
            "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            "-vf",
            "scale='if(gte(iw,ih),min(1280,iw),-2)'"
            ":'if(gte(iw,ih),-2,min(1280,ih))'"
            ",pad=ceil(iw/2)*2:ceil(ih/2)*2",
            output_path,
        ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.error(
                "FFmpeg transcode FAIL (code=%d) codec=%s pix_fmt=%s\nstderr: %s",
                result.returncode, codec, pix_fmt,
                result.stderr[-2000:] if result.stderr else "(empty)",
            )
            return False
        if not os.path.exists(output_path):
            logger.error("FFmpeg returned 0 but no output: %s", output_path)
            return False
        logger.info("Preview OK: %s/%s → h264/yuv420p", codec, pix_fmt)
        return True
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg transcode timeout 300s")
        return False
    except Exception as e:
        logger.warning("preview transcode exception: %s", e)
        return False


def get_video_duration(video_path: str) -> float:
    """영상 길이 추출"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = run_ffmpeg_command(cmd, timeout=30)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def extract_frame(video_path: str, timestamp: str, output_path: str) -> bool:
    """특정 타임스탬프에서 프레임 추출"""
    # MM:SS.ms → 초로 변환
    parts = timestamp.split(":")
    seconds = float(parts[0]) * 60 + float(parts[1])
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(seconds),
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",  # 고품질 JPEG
        output_path
    ]
    
    result = run_ffmpeg_command(cmd, timeout=30)
    return os.path.exists(output_path)


@router.post("/", response_model=SceneDetectResult)
async def scene_detect_metadata(
    video: UploadFile = File(...),
    threshold: float = Query(0.19, ge=0.05, le=0.5, description="Scene detection threshold"),
):
    """
    씬 감지 메타데이터만 반환 (프레임 이미지 없이)
    빠른 응답용
    """
    if not video.filename:
        raise HTTPException(status_code=400, detail="No video file provided")
    
    # 임시 파일로 저장
    suffix = Path(video.filename).suffix or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await video.read())
        tmp_path = tmp.name
    
    preview_id = str(uuid.uuid4())
    preview_path = os.path.join(tempfile.gettempdir(), f"preview_{preview_id}.mp4")

    try:
        # 씬 감지 + H.264 트랜스코딩 병렬 실행
        timestamps, duration, transcode_ok = await asyncio.gather(
            asyncio.to_thread(detect_scenes, tmp_path, threshold),
            asyncio.to_thread(get_video_duration, tmp_path),
            asyncio.to_thread(create_web_preview, tmp_path, preview_path),
        )

        if transcode_ok:
            _preview_store[preview_id] = (preview_path, time.time())
        else:
            preview_id = None
            try:
                os.unlink(preview_path)
            except OSError:
                pass

        _cleanup_old_previews()

        return SceneDetectResult(
            timestamps=timestamps,
            frame_count=len(timestamps),
            video_duration=duration,
            threshold=threshold,
            preview_id=preview_id,
        )
    finally:
        os.unlink(tmp_path)


@router.get("/preview/{preview_id}")
async def get_preview(preview_id: str, request: Request):
    """트랜스코딩된 H.264 영상 서빙 (브라우저 호환 + Range 지원)"""
    if preview_id not in _preview_store:
        raise HTTPException(status_code=404, detail="Preview not found or expired")
    path, _ = _preview_store[preview_id]
    if not os.path.exists(path):
        _preview_store.pop(preview_id, None)
        raise HTTPException(status_code=404, detail="Preview file not found")

    file_size = os.path.getsize(path)
    range_header = request.headers.get("range")

    if range_header:
        range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            end = min(end, file_size - 1)
            length = end - start + 1

            def iter_file():
                with open(path, "rb") as f:
                    f.seek(start)
                    remaining = length
                    while remaining > 0:
                        chunk = f.read(min(8192, remaining))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk

            return StreamingResponse(
                iter_file(), status_code=206, media_type="video/mp4",
                headers={
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Content-Length": str(length),
                    "Accept-Ranges": "bytes",
                },
            )

    return FileResponse(path, media_type="video/mp4",
                        headers={"Accept-Ranges": "bytes"})


@router.post("/extract-frames")
async def extract_frames_from_timestamps(
    video: UploadFile = File(...),
    timestamps: str = Form(""),  # JSON string of timestamps array
):
    """
    전달받은 타임스탬프 기준으로 프레임 추출 → ZIP 반환
    씬 감지를 다시 실행하지 않고 정확한 프레임 추출
    """
    import json

    if not video.filename:
        raise HTTPException(status_code=400, detail="No video file provided")

    # 타임스탬프 파싱
    try:
        ts_list = json.loads(timestamps) if timestamps else []
        if not ts_list:
            raise HTTPException(status_code=400, detail="No timestamps provided")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid timestamps format")

    # 임시 디렉토리 생성
    work_dir = tempfile.mkdtemp(prefix="scene_detect_")
    video_name = Path(video.filename).stem or "video"
    suffix = Path(video.filename).suffix or ".mp4"
    video_path = os.path.join(work_dir, f"input{suffix}")

    try:
        # 영상 저장
        with open(video_path, "wb") as f:
            f.write(await video.read())

        duration = await asyncio.to_thread(get_video_duration, video_path)

        # 프레임 추출 (전달받은 타임스탬프 사용)
        frames_dir = os.path.join(work_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)

        for i, ts in enumerate(ts_list):
            frame_path = os.path.join(frames_dir, f"frame_{i+1:02d}_{ts.replace(':', '-')}.jpg")
            await asyncio.to_thread(extract_frame, video_path, ts, frame_path)

        # 타임스탬프 텍스트 파일 생성
        timestamps_path = os.path.join(work_dir, "timestamps.txt")
        with open(timestamps_path, "w") as f:
            f.write(f"# Scene Frames\n")
            f.write(f"# Duration: {duration:.2f}s\n")
            f.write(f"# Frames: {len(ts_list)}\n\n")
            for i, ts in enumerate(ts_list):
                f.write(f"Scene {i+1:02d}: {ts}\n")

        # ZIP 생성
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(timestamps_path, "timestamps.txt")
            for frame_file in sorted(os.listdir(frames_dir)):
                frame_path = os.path.join(frames_dir, frame_file)
                zf.write(frame_path, f"frames/{frame_file}")

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{video_name}_scenes.zip"'
            }
        )

    finally:
        # 임시 파일 정리
        shutil.rmtree(work_dir, ignore_errors=True)


class ThumbnailItem(BaseModel):
    timestamp: str
    data_url: str


class ThumbnailsResponse(BaseModel):
    thumbnails: list[ThumbnailItem]


@router.post("/thumbnails", response_model=ThumbnailsResponse)
async def extract_thumbnails(
    video: UploadFile = File(...),
    timestamps: str = Form(""),
):
    """
    타임스탬프 기준 썸네일 추출 (base64 data URL 반환)
    - 320x180 JPEG, quality=5 로 경량화
    - 프론트엔드 canvas 추출 대체용
    """
    import json

    if not video.filename:
        raise HTTPException(status_code=400, detail="No video file provided")

    try:
        ts_list = json.loads(timestamps) if timestamps else []
        if not ts_list:
            raise HTTPException(status_code=400, detail="No timestamps provided")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid timestamps format")

    suffix = Path(video.filename).suffix or ".mp4"
    work_dir = tempfile.mkdtemp(prefix="thumbnails_")
    video_path = os.path.join(work_dir, f"input{suffix}")

    try:
        with open(video_path, "wb") as f:
            f.write(await video.read())

        thumbnails: list[ThumbnailItem] = []

        for ts in ts_list:
            frame_path = os.path.join(work_dir, f"thumb_{ts.replace(':', '-')}.jpg")

            # MM:SS.ms → seconds
            parts = ts.split(":")
            seconds = float(parts[0]) * 60 + float(parts[1])

            cmd = [
                "ffmpeg", "-y",
                "-ss", str(seconds),
                "-i", video_path,
                "-vframes", "1",
                "-vf", "scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2:black",
                "-q:v", "5",
                frame_path,
            ]
            await asyncio.to_thread(run_ffmpeg_command, cmd, 15)

            if os.path.exists(frame_path):
                with open(frame_path, "rb") as img:
                    b64 = base64.b64encode(img.read()).decode("ascii")
                thumbnails.append(ThumbnailItem(
                    timestamp=ts,
                    data_url=f"data:image/jpeg;base64,{b64}",
                ))

        return ThumbnailsResponse(thumbnails=thumbnails)

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
