"""
Scene Detection API
영상 업로드 → FFmpeg로 씬 감지 + 프레임 추출 → ZIP 반환
"""
import asyncio
import base64
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from io import BytesIO
from math import ceil
from pathlib import Path
from fastapi import APIRouter, File, Form, Query, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/scene-detect", tags=["scene-detect"])


class SceneDetectResult(BaseModel):
    """씬 감지 결과"""
    timestamps: list[str]
    frame_count: int
    video_duration: float
    threshold: float


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
    
    try:
        # 씬 감지
        timestamps = await asyncio.to_thread(detect_scenes, tmp_path, threshold)
        duration = await asyncio.to_thread(get_video_duration, tmp_path)
        
        return SceneDetectResult(
            timestamps=timestamps,
            frame_count=len(timestamps),
            video_duration=duration,
            threshold=threshold,
        )
    finally:
        os.unlink(tmp_path)


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
