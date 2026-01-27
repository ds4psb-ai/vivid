# backend/app/services/vdg_2pass/vdg_unified_pipeline.py
"""
VDG Unified Pipeline Orchestrator

아키텍처:
┌─────────────────────────────────────────────────────────────┐
│  Pass 1: UnifiedPass (Gemini 3.0 Pro)                      │
│  - Hook clip: 10fps (정밀 microbeat)                        │
│  - Full video: 1fps (전체 인과)                             │
│  - 출력: 의미/인과/Plan Seed                                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Pass 2: CVMeasurementPass (ffmpeg + OpenCV)               │
│  - 결정론적 측정                                            │
│  - 3개 MVP 메트릭: center_offset, brightness, blur          │
│  - 출력: 수치/좌표                                          │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Merger: VDG Result                                         │
│  - Semantic + CV 측정값 통합                                │
│  - Deterministic IDs 생성                                   │
│  - Evidence 링크                                            │
└─────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import os
import gc
import logging
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from app.config import settings
from app.utils.http_client import (
    build_async_client,
    fetch_bytes_limited,
    DownloadTooLargeError,
    InvalidContentTypeError,
)
from app.utils.security_audit import log_security_event
from app.services.download_abuse_guard import download_abuse_guard
from app.services.monitoring import send_alert
from app.schemas.vdg_unified_pass import (
    UnifiedPassLLMOutput,
    AnalysisPointSeedLLM,
    MeasurementSpecLLM,
)
from app.services.vdg_2pass.unified_pass import (
    UnifiedPass,
    UnifiedPassProvenance,
    get_video_duration_ms,
)
from app.services.vdg_2pass.cv_measurement_pass import (
    CVMeasurementPass,
    CVMeasurementResult,
    CVPassProvenance,
    PointMeasurement,
    MetricResult,
)
from app.services.vdg_2pass.visual_pass import (
    VisualPass,
    VisualPassConfig,
    VisualPassProvenance,
    VisualPassError,
)
from app.services.vdg_2pass.audio_analyzer import (
    analyze_audio,
    get_audio_summary,
    AudioAnalysis,
)
from app.services.vdg_2pass.motion_analyzer import (
    analyze_motion,
    get_motion_summary,
    MotionAnalysis,
)
from app.services.telemetry import trace_span, vdg_metrics, get_tracer
from app.metrics import record_analysis_complete

logger = logging.getLogger(__name__)

VIDEO_CONTENT_TYPES = (
    "video/*",
    "application/octet-stream",
    "binary/octet-stream",
)


# ============================================
# Pipeline Configuration
# ============================================

PIPELINE_VERSION = "vdg_unified_v1.0"


@dataclass
class PipelineConfig:
    """파이프라인 설정"""

    # Pass 1 설정
    model_id: Optional[str] = None
    media_resolution: str = "low"
    hook_clip_seconds: float = 4.0
    hook_clip_fps: float = 10.0
    full_video_fps: float = 1.0

    # Pass 2 설정
    cv_extraction_fps: float = 10.0
    save_evidence_frames: bool = False
    evidence_output_dir: Optional[str] = None

    # Visual Pass 설정
    skip_visual_pass: bool = False  # Visual Pass 스킵 (디버깅/속도용)
    visual_detection_conf: float = 0.5
    visual_ocr_enabled: bool = True

    # 일반 설정
    skip_cv_pass: bool = False  # CV Pass 스킵 (디버깅용)

    # P1 Fix: Memory management for long videos
    gc_threshold_ms: int = 300000  # 5분 이상 영상에서 gc 활성화
    gc_enabled: bool = True  # gc.collect() 활성화


# ============================================
# Result Types
# ============================================


@dataclass
class AnalysisPointResult:
    """단일 Analysis Point의 통합 결과"""

    ap_id: str  # 결정론적 ID
    t_center_ms: int
    t_window_ms: int
    priority: str
    reason: str

    # Pass 1에서
    target_entity_keys: List[str] = field(default_factory=list)
    evidence_note: Optional[str] = None

    # Pass 2에서
    metrics: Dict[str, MetricResult] = field(default_factory=dict)
    evidence_frame_path: Optional[str] = None


@dataclass
class VDGUnifiedResult:
    """VDG 통합 파이프라인 결과"""

    # 메타데이터
    pipeline_version: str = PIPELINE_VERSION
    run_at: str = ""
    video_path: str = ""
    duration_ms: int = 0

    # Pass 1 결과
    llm_output: Optional[UnifiedPassLLMOutput] = None
    llm_provenance: Optional[UnifiedPassProvenance] = None

    # Pass 2 결과
    cv_result: Optional[CVMeasurementResult] = None
    cv_provenance: Optional[CVPassProvenance] = None

    # Visual Pass 결과 (신규)
    visual_result: Optional[Dict[str, Any]] = None
    visual_provenance: Optional[VisualPassProvenance] = None

    # Audio Pass 결과 (P1)
    audio_analysis: Optional[AudioAnalysis] = None

    # Motion Pass 결과 (P2)
    motion_analysis: Optional[MotionAnalysis] = None

    # 통합 결과
    analysis_points: List[AnalysisPointResult] = field(default_factory=list)

    # 타이밍
    total_latency_ms: int = 0
    audio_latency_ms: int = 0
    motion_latency_ms: int = 0
    pass1_latency_ms: int = 0
    pass2_latency_ms: int = 0
    visual_latency_ms: int = 0


# ============================================
# ID Generation
# ============================================


def generate_ap_id(
    t_center_ms: int,
    t_window_ms: int,
    video_hash: str,
) -> str:
    """
    결정론적 Analysis Point ID 생성

    형식: ap_{video_hash[:8]}_{t_center_ms}_{t_window_ms}
    """
    return f"ap_{video_hash[:8]}_{t_center_ms}_{t_window_ms}"


def compute_video_hash(video_path: str) -> str:
    """비디오 파일 해시 (첫 1MB만)"""
    hasher = hashlib.sha256()
    with open(video_path, "rb") as f:
        chunk = f.read(1024 * 1024)  # 1MB
        hasher.update(chunk)
    return hasher.hexdigest()


# ============================================
# Main Pipeline Class
# ============================================


class VDGUnifiedPipeline:
    """
    VDG 통합 파이프라인 오케스트레이터

    Pass 1 (UnifiedPass) → Pass 2 (CVMeasurementPass) → Merge
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()

        # Pass 1 초기화
        self.pass1 = UnifiedPass(
            model_id=self.config.model_id,
            media_resolution=self.config.media_resolution,
            hook_clip_seconds=self.config.hook_clip_seconds,
            hook_clip_fps=self.config.hook_clip_fps,
            full_video_fps=self.config.full_video_fps,
        )

        # Pass 2 초기화
        self.pass2 = CVMeasurementPass(
            extraction_fps=self.config.cv_extraction_fps,
            save_evidence_frames=self.config.save_evidence_frames,
            evidence_output_dir=self.config.evidence_output_dir,
        )

    def _maybe_gc(self, duration_ms: int, pass_name: str) -> None:
        """
        P1 Fix: Conditional garbage collection for long videos.

        긴 영상(5분+) 처리 시 각 Pass 완료 후 메모리 해제하여 OOM 방지.
        """
        if not self.config.gc_enabled:
            return
        if duration_ms < self.config.gc_threshold_ms:
            return

        collected = gc.collect()
        if collected > 0:
            logger.debug(f"🧹 GC after {pass_name}: collected {collected} objects")

    def run(
        self,
        *,
        video_path: str,
        platform: str,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        top_comments: Optional[List[str]] = None,
        duration_ms: Optional[int] = None,
    ) -> VDGUnifiedResult:
        """
        통합 파이프라인 실행

        Args:
            video_path: 비디오 파일 경로
            platform: 플랫폼 (tiktok/youtube/instagram)
            caption: 영상 캡션
            hashtags: 해시태그 목록
            top_comments: 상위 댓글 목록
            duration_ms: 비디오 길이 (None이면 자동 추출)

        Returns:
            VDGUnifiedResult
        """
        import time

        start_time = time.time()
        tracer = get_tracer("vdg_pipeline")

        logger.info(f"🚀 VDG Pipeline starting: {video_path}")

        # duration 자동 추출
        if duration_ms is None:
            duration_ms = get_video_duration_ms(video_path)
            if duration_ms == 0:
                duration_ms = 60000  # 기본 60초

        # 비디오 해시 (ID 생성용)
        video_hash = compute_video_hash(video_path)

        result = VDGUnifiedResult(
            run_at=datetime.now(timezone.utc).isoformat(),
            video_path=video_path,
            duration_ms=duration_ms,
        )

        # ============================================
        # Audio Pass: librosa BPM/Onset Analysis (P1)
        # ============================================
        audio_start = time.time()
        audio_summary = ""

        with tracer.start_as_current_span("vdg.audio_pass") as audio_span:
            audio_span.set_attribute("video.duration_ms", duration_ms)
            audio_span.set_attribute("video.path", video_path)
            try:
                audio_result = analyze_audio(video_path)
                result.audio_analysis = audio_result
                result.audio_latency_ms = int((time.time() - audio_start) * 1000)

                if audio_result.has_audio:
                    audio_summary = get_audio_summary(audio_result)
                    bpm_str = f"{audio_result.bpm:.1f}" if audio_result.bpm else "N/A"
                    audio_span.set_attribute("audio.bpm", audio_result.bpm or 0)
                    audio_span.set_attribute("audio.onset_count", len(audio_result.onset_timestamps))
                    logger.info(
                        f"🎵 Audio Pass complete: BPM={bpm_str}, "
                        f"onsets={len(audio_result.onset_timestamps)}, "
                        f"latency={result.audio_latency_ms}ms"
                    )
                else:
                    audio_span.set_attribute("audio.has_audio", False)
                    logger.info("🎵 Audio Pass: No audio track detected")

                vdg_metrics.record_analysis_duration("audio", result.audio_latency_ms / 1000)

            except Exception as e:
                # Graceful degradation: 오디오 분석 실패해도 계속 진행
                audio_span.set_attribute("error", True)
                audio_span.set_attribute("error.message", str(e))
                logger.warning(f"🎵 Audio Pass failed (continuing): {e}")
                result.audio_latency_ms = int((time.time() - audio_start) * 1000)
                vdg_metrics.increment_failure("audio_pass")

        # P1 Fix: Memory cleanup after Audio Pass
        self._maybe_gc(duration_ms, "Audio Pass")

        # ============================================
        # Motion Pass: OpenCV Optical Flow Analysis (P2)
        # ============================================
        motion_start = time.time()
        motion_summary = ""

        with tracer.start_as_current_span("vdg.motion_pass") as motion_span:
            motion_span.set_attribute("video.duration_ms", duration_ms)
            try:
                motion_result = analyze_motion(video_path)
                result.motion_analysis = motion_result
                result.motion_latency_ms = int((time.time() - motion_start) * 1000)

                if motion_result.has_motion:
                    motion_summary = get_motion_summary(motion_result)
                    dominant = motion_result.dominant_movement.value if motion_result.dominant_movement else "N/A"
                    motion_span.set_attribute("motion.dominant", dominant)
                    motion_span.set_attribute("motion.segment_count", len(motion_result.segments))
                    logger.info(
                        f"🎬 Motion Pass complete: dominant={dominant}, "
                        f"segments={len(motion_result.segments)}, "
                        f"latency={result.motion_latency_ms}ms"
                    )
                else:
                    motion_span.set_attribute("motion.has_motion", False)
                    logger.info("🎬 Motion Pass: No motion data extracted")

                vdg_metrics.record_analysis_duration("motion", result.motion_latency_ms / 1000)

            except Exception as e:
                # Graceful degradation: 모션 분석 실패해도 계속 진행
                motion_span.set_attribute("error", True)
                motion_span.set_attribute("error.message", str(e))
                logger.warning(f"🎬 Motion Pass failed (continuing): {e}")
                result.motion_latency_ms = int((time.time() - motion_start) * 1000)
                vdg_metrics.increment_failure("motion_pass")

        # P1 Fix: Memory cleanup after Motion Pass
        self._maybe_gc(duration_ms, "Motion Pass")

        # ============================================
        # Pass 1: UnifiedPass (LLM)
        # ============================================
        pass1_start = time.time()

        with tracer.start_as_current_span("vdg.pass1_llm") as pass1_span:
            pass1_span.set_attribute("video.duration_ms", duration_ms)
            pass1_span.set_attribute("platform", platform)
            try:
                llm_output, llm_prov = self.pass1.run(
                    video_path=video_path,
                    duration_ms=duration_ms,
                    platform=platform,
                    caption=caption,
                    hashtags=hashtags,
                    top_comments=top_comments,
                    audio_summary=audio_summary,  # P1: Audio analysis context
                    motion_summary=motion_summary,  # P2: Motion analysis context
                )
                result.llm_output = llm_output
                result.llm_provenance = llm_prov
                result.pass1_latency_ms = int((time.time() - pass1_start) * 1000)

                pass1_span.set_attribute("llm.analysis_points", len(llm_output.analysis_plan.points))
                pass1_span.set_attribute("llm.model", llm_prov.model_id if llm_prov else "unknown")
                vdg_metrics.record_analysis_duration("pass1_llm", result.pass1_latency_ms / 1000)

                logger.info(
                    f"✅ Pass 1 complete: "
                    f"analysis_points={len(llm_output.analysis_plan.points)}, "
                    f"latency={result.pass1_latency_ms}ms"
                )
            except Exception as e:
                pass1_span.set_attribute("error", True)
                pass1_span.set_attribute("error.message", str(e))
                vdg_metrics.increment_failure("pass1_llm")
                logger.error(f"❌ Pass 1 failed: {e}")
                raise

        # P1 Fix: Memory cleanup after Pass 1 (LLM)
        self._maybe_gc(duration_ms, "Pass 1 LLM")

        # ============================================
        # Pass 2: CVMeasurementPass (CV) - Dynamic timeout
        # ============================================
        if not self.config.skip_cv_pass:
            pass2_start = time.time()

            # P0 Fix: Dynamic timeout based on video duration
            # Base: 120s, +3s per minute of video, max 600s (10min)
            cv_timeout_sec = min(600, max(120, 120 + int(duration_ms / 1000 / 60) * 3))

            logger.info(f"🔬 Pass 2 starting (CV measurement, timeout={cv_timeout_sec}s)...")

            with tracer.start_as_current_span("vdg.pass2_cv") as pass2_span:
                pass2_span.set_attribute("video.duration_ms", duration_ms)
                pass2_span.set_attribute("cv.timeout_sec", cv_timeout_sec)
                try:
                    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

                    def _run_cv():
                        return self.pass2.run(
                            video_path=video_path,
                            analysis_plan=llm_output.analysis_plan,
                        )

                    # P0 Fix: Dynamic timeout instead of fixed 120s
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(_run_cv)
                        cv_result, cv_prov = future.result(timeout=cv_timeout_sec)

                    result.cv_result = cv_result
                    result.cv_provenance = cv_prov
                    result.pass2_latency_ms = int((time.time() - pass2_start) * 1000)

                    pass2_span.set_attribute("cv.frames_processed", cv_result.total_frames_processed)
                    vdg_metrics.record_analysis_duration("pass2_cv", result.pass2_latency_ms / 1000)

                    logger.info(
                        f"✅ Pass 2 complete: "
                        f"frames={cv_result.total_frames_processed}, "
                        f"latency={result.pass2_latency_ms}ms"
                    )
                except FuturesTimeout:
                    result.pass2_latency_ms = int((time.time() - pass2_start) * 1000)
                    pass2_span.set_attribute("error", True)
                    pass2_span.set_attribute("error.type", "timeout")
                    vdg_metrics.increment_failure("pass2_cv_timeout")
                    logger.error(f"❌ Pass 2 timed out after {cv_timeout_sec}s (continuing without CV)")
                except Exception as e:
                    result.pass2_latency_ms = int((time.time() - pass2_start) * 1000)
                    pass2_span.set_attribute("error", True)
                    pass2_span.set_attribute("error.message", str(e))
                    vdg_metrics.increment_failure("pass2_cv")
                    logger.error(f"❌ Pass 2 failed: {e}")
                    # CV 실패해도 LLM 결과는 반환

            # P1 Fix: Memory cleanup after Pass 2 (CV)
            self._maybe_gc(duration_ms, "Pass 2 CV")

        # ============================================
        # Visual Pass: Entity Tracking (Optional)
        # ============================================
        if not self.config.skip_visual_pass:
            visual_start = time.time()

            logger.info("👁️ Visual Pass starting (Entity Tracking)...")

            with tracer.start_as_current_span("vdg.visual_pass") as visual_span:
                visual_span.set_attribute("video.duration_ms", duration_ms)
                try:
                    # Build config from pipeline config
                    visual_config = VisualPassConfig(
                        detection_conf_threshold=self.config.visual_detection_conf,
                        ocr_enabled=self.config.visual_ocr_enabled,
                        extraction_fps=self.config.cv_extraction_fps,
                    )

                    visual_pass = VisualPass(config=visual_config)

                    # Convert analysis_plan.points to dict format
                    analysis_points_dict = [
                        {
                            "t_center_ms": p.t_center_ms,
                            "t_window_ms": p.t_window_ms,
                        }
                        for p in llm_output.analysis_plan.points
                    ]

                    # Convert entity_hints to dict format
                    entity_hints_dict = (
                        [
                            {
                                "key": h.key,
                                "entity_type": h.entity_type,
                                "description": h.description,
                            }
                            for h in llm_output.entity_hints
                        ]
                        if llm_output.entity_hints
                        else []
                    )

                    visual_result, visual_prov = visual_pass.run(
                        video_path=video_path,
                        analysis_points=analysis_points_dict,
                        entity_hints=entity_hints_dict,
                        duration_ms=duration_ms,
                    )
                    result.visual_result = visual_result
                    result.visual_provenance = visual_prov
                    result.visual_latency_ms = int((time.time() - visual_start) * 1000)

                    visual_span.set_attribute("visual.entity_count", len(visual_result.get("entity_catalog", [])))
                    visual_span.set_attribute("visual.text_count", len(visual_result.get("text_geometries", [])))
                    vdg_metrics.record_analysis_duration("visual_pass", result.visual_latency_ms / 1000)

                    logger.info(
                        f"✅ Visual Pass complete: "
                        f"entities={len(visual_result.get('entity_catalog', []))}, "
                        f"texts={len(visual_result.get('text_geometries', []))}, "
                        f"latency={result.visual_latency_ms}ms"
                    )
                except ImportError as e:
                    visual_span.set_attribute("skipped", True)
                    visual_span.set_attribute("skip.reason", "dependencies_not_installed")
                    logger.warning(f"⚠️ Visual Pass skipped (dependencies not installed): {e}")
                except VisualPassError as e:
                    # P2: 0% 프레임 처리 등 심각한 Visual 실패는 파이프라인 중단
                    visual_span.set_attribute("error", True)
                    visual_span.set_attribute("error.message", str(e))
                    visual_span.set_attribute("error.fatal", True)
                    vdg_metrics.increment_failure("visual_pass")
                    logger.error(f"❌ Visual Pass FATAL: {e}")
                    raise  # re-raise to stop pipeline (video integrity issue)
                except Exception as e:
                    visual_span.set_attribute("error", True)
                    visual_span.set_attribute("error.message", str(e))
                    vdg_metrics.increment_failure("visual_pass")
                    logger.error(f"❌ Visual Pass failed: {e}")
                    # 일반 예외는 계속 진행 (partial result 가능)

            # P1 Fix: Memory cleanup after Visual Pass
            self._maybe_gc(duration_ms, "Visual Pass")

        # ============================================
        # Merge: 통합 결과 생성
        # ============================================
        result.analysis_points = self._merge_results(
            llm_output=result.llm_output,
            cv_result=result.cv_result,
            video_hash=video_hash,
        )

        result.total_latency_ms = int((time.time() - start_time) * 1000)

        # Record final metrics (OTel + Prometheus)
        vdg_metrics.record_analysis_duration("total", result.total_latency_ms / 1000)
        vdg_metrics.increment_success()
        record_analysis_complete(
            duration_seconds=result.total_latency_ms / 1000,
            status="completed",
            pass_name="total",
        )

        logger.info(
            f"🏁 VDG Pipeline complete: "
            f"points={len(result.analysis_points)}, "
            f"total_latency={result.total_latency_ms}ms"
        )

        return result

    def _merge_results(
        self,
        llm_output: UnifiedPassLLMOutput,
        cv_result: Optional[CVMeasurementResult],
        video_hash: str,
    ) -> List[AnalysisPointResult]:
        """Pass 1 + Pass 2 결과 병합"""

        merged = []

        # CV 결과를 t_center_ms로 인덱싱
        cv_by_time: Dict[int, PointMeasurement] = {}
        if cv_result:
            for pm in cv_result.measurements:
                cv_by_time[pm.t_center_ms] = pm

        # 각 analysis point 처리
        for point in llm_output.analysis_plan.points:
            # 결정론적 ID 생성
            ap_id = generate_ap_id(
                t_center_ms=point.t_center_ms,
                t_window_ms=point.t_window_ms,
                video_hash=video_hash,
            )

            # CV 측정값 매칭
            cv_point = cv_by_time.get(point.t_center_ms)

            merged_point = AnalysisPointResult(
                ap_id=ap_id,
                t_center_ms=point.t_center_ms,
                t_window_ms=point.t_window_ms,
                priority=point.priority,
                reason=point.reason,
                target_entity_keys=point.target_entity_keys,
                evidence_note=point.evidence_note,
                metrics=cv_point.metrics if cv_point else {},
                evidence_frame_path=cv_point.evidence_frame_path if cv_point else None,
            )

            merged.append(merged_point)

        return merged


# ============================================
# Convenience Functions
# ============================================


def analyze_video(
    video_path: str,
    platform: str = "tiktok",
    caption: Optional[str] = None,
    hashtags: Optional[List[str]] = None,
    top_comments: Optional[List[str]] = None,
    config: Optional[PipelineConfig] = None,
) -> VDGUnifiedResult:
    """
    편의 함수: 비디오 분석 실행

    Example:
        result = analyze_video(
            video_path="video.mp4",
            platform="tiktok",
            top_comments=["대박", "이거 어케함"]
        )

        # LLM 결과
        print(result.llm_output.hook_genome.strength)

        # CV 측정값
        for ap in result.analysis_points:
            print(f"{ap.ap_id}: {ap.metrics}")
    """
    pipeline = VDGUnifiedPipeline(config=config)
    return pipeline.run(
        video_path=video_path,
        platform=platform,
        caption=caption,
        hashtags=hashtags,
        top_comments=top_comments,
    )


async def run_vdg_async(
    video_url: str,
    content_id: str,
    platform: str = "tiktok",
    config: Optional[PipelineConfig] = None,
    *,
    node_id: Optional[str] = None,  # Phase 1: DB 저장용 node_id
    db_session: Optional[Any] = None,  # Phase 1: DB 세션
    timeout_seconds: int = 300,  # HTTP 타임아웃
    max_retries: int = 2,  # 다운로드 재시도
) -> Optional[VDGUnifiedResult]:
    """
    Phase 4-B: 비동기 VDG 파이프라인 실행 (BackgroundTask용)

    Hardening:
    - Input validation
    - HTTP timeout and retries
    - Proper temp file cleanup
    - Detailed error logging
    - DB save error isolation

    Args:
        video_url: 비디오 URL (S3 등)
        content_id: 콘텐츠 ID (session_id 등)
        platform: 플랫폼 (tiktok/youtube/instagram)
        config: 파이프라인 설정
        node_id: DB 저장용 RemixNode ID (optional)
        db_session: AsyncSession for DB persistence (optional)
        timeout_seconds: HTTP 다운로드 타임아웃 (기본 300초)
        max_retries: 다운로드 실패 시 재시도 횟수

    Returns:
        VDGUnifiedResult or None (실패 시)
    """
    import asyncio
    import tempfile

    video_path: Optional[str] = None

    # Input validation
    if not video_url:
        logger.error(f"❌ VDG async: video_url is empty for {content_id}")
        return None

    if not content_id:
        logger.error("❌ VDG async: content_id is empty")
        return None

    # Validate platform
    valid_platforms = {"tiktok", "youtube", "instagram", "shorts"}
    platform = platform.lower() if platform else "tiktok"
    if platform not in valid_platforms:
        logger.warning(f"Unknown platform '{platform}', defaulting to 'tiktok'")
        platform = "tiktok"

    logger.info(f"📹 VDG async pipeline starting: {content_id} (url: {video_url[:50]}...)")

    try:
        guard_state = await download_abuse_guard.check_blocked(video_url, user_id=None)
        if guard_state.blocked:
            log_security_event(
                "download_blocked",
                user_id=None,
                reason="download_cooldown",
                url_host=guard_state.host,
                guard_key=guard_state.key_hash,
                guard_scope=guard_state.key_type,
                guard_cooldown_seconds=guard_state.cooldown_seconds,
            )
            try:
                await send_alert(
                    title="VDG video blocked (cooldown)",
                    message=(
                        "Context: VDG async pipeline\n"
                        f"Host: {guard_state.host}\n"
                        f"Key: {guard_state.key_hash}\n"
                        f"Cooldown: {guard_state.cooldown_seconds}s"
                    ),
                    severity="warning",
                )
            except Exception as alert_exc:
                logger.warning("Download cooldown alert failed: %s", alert_exc)
            return None

        # 1. 비디오 다운로드 (with retries)
        import httpx

        video_content = None
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                async with build_async_client(
                    timeout=timeout_seconds,
                    follow_redirects=True,
                ) as client:
                    video_content = await fetch_bytes_limited(
                        client,
                        video_url,
                        max_bytes=settings.VIDEO_DOWNLOAD_MAX_BYTES,
                        allowed_content_types=VIDEO_CONTENT_TYPES,
                    )
                    break
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"⏱️ Timeout on attempt {attempt + 1}/{max_retries + 1}: {e}")
            except DownloadTooLargeError as e:
                last_error = e
                logger.error(f"❌ Download too large: {e}")
                guard_state = await download_abuse_guard.record_oversize(video_url, user_id=None)
                log_security_event(
                    "download_too_large",
                    user_id=None,
                    reason="vdg_video_download_cap",
                    url=video_url,
                    max_bytes=settings.VIDEO_DOWNLOAD_MAX_BYTES,
                    error=str(e),
                    guard_count=guard_state.count,
                    guard_threshold=guard_state.threshold,
                    guard_window_seconds=guard_state.window_seconds,
                    guard_cooldown_seconds=guard_state.cooldown_seconds,
                    guard_key=guard_state.key_hash,
                    guard_scope=guard_state.key_type,
                )
                try:
                    await send_alert(
                        title="VDG video blocked (size cap)",
                        message=(
                            f"URL: {video_url}\n"
                            f"Cap: {settings.VIDEO_DOWNLOAD_MAX_BYTES} bytes\n"
                            f"Count: {guard_state.count}/{guard_state.threshold}\n"
                            f"Blocked: {guard_state.blocked}"
                        ),
                        severity="warning",
                    )
                except Exception as alert_exc:
                    logger.warning("Download size alert failed: %s", alert_exc)
                if guard_state.blocked:
                    log_security_event(
                        "download_blocked",
                        user_id=None,
                        reason="oversize_threshold",
                        url_host=guard_state.host,
                        guard_key=guard_state.key_hash,
                        guard_scope=guard_state.key_type,
                        guard_count=guard_state.count,
                        guard_threshold=guard_state.threshold,
                        guard_cooldown_seconds=guard_state.cooldown_seconds,
                    )
                break
            except InvalidContentTypeError as e:
                last_error = e
                log_security_event(
                    "download_blocked",
                    user_id=None,
                    reason="content_type_not_allowed",
                    url=video_url,
                    allowed_types=VIDEO_CONTENT_TYPES,
                    error=str(e),
                )
                try:
                    await send_alert(
                        title="VDG video blocked (content-type)",
                        message=(f"URL: {video_url}\n" f"Allowed: {', '.join(VIDEO_CONTENT_TYPES)}"),
                        severity="warning",
                    )
                except Exception as alert_exc:
                    logger.warning("Download content-type alert failed: %s", alert_exc)
                break
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.error(f"❌ HTTP error {e.response.status_code} on attempt {attempt + 1}")
                if e.response.status_code >= 400 and e.response.status_code < 500:
                    # 4xx 에러는 재시도 불필요
                    break
            except Exception as e:
                last_error = e
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")

            if attempt < max_retries:
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff

        if video_content is None:
            logger.error(f"❌ Failed to download video after {max_retries + 1} attempts: {last_error}")
            return None

        # Validate content size
        if len(video_content) < 10000:  # 10KB minimum
            logger.error(f"❌ Downloaded video too small ({len(video_content)} bytes)")
            return None

        # 2. 임시 파일 생성
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                f.write(video_content)
                video_path = f.name
        except IOError as e:
            logger.error(f"❌ Failed to write temp file: {e}")
            return None

        del video_content  # 메모리 해제

        logger.info(f"📁 Video downloaded: {video_path} ({os.path.getsize(video_path)} bytes)")

        # 3. 동기 파이프라인을 thread에서 실행
        def run_pipeline() -> VDGUnifiedResult:
            return analyze_video(
                video_path=video_path,
                platform=platform,
                config=config,
            )

        result = await asyncio.to_thread(run_pipeline)

        if result is None:
            logger.error(f"❌ VDG pipeline returned None for {content_id}")
            return None

        logger.info(f"✅ VDG pipeline completed for {content_id}: latency={result.total_latency_ms}ms")

        # 4. Phase 1: DB 저장 (node_id와 db_session 제공 시)
        if node_id and db_session and result.llm_output:
            try:
                from app.services.vdg_2pass.vdg_db_saver import vdg_db_saver

                # VDGUnifiedResult → vdg_data dict 변환
                vdg_data = convert_result_to_vdg_data(result)

                if vdg_data:  # 빈 dict가 아닌 경우만
                    save_result = await vdg_db_saver.save_vdg_to_db(
                        db=db_session,
                        node_id=node_id,
                        vdg_data=vdg_data,
                        video_path=video_path,
                    )
                    logger.info(f"💾 VDG saved to DB: {save_result}")
                else:
                    logger.warning(f"⚠️ Empty vdg_data for {content_id}, skipping DB save")

            except Exception as e:
                # DB 저장 실패는 전체 실패로 이어지지 않음
                logger.error(f"❌ VDG DB save failed (continuing): {e}", exc_info=True)

        logger.info(f"✅ VDG async pipeline completed: {content_id}")
        return result

    except Exception as e:
        logger.error(f"❌ VDG async pipeline failed for {content_id}: {e}", exc_info=True)
        return None

    finally:
        # 5. 임시 파일 정리 (guaranteed cleanup)
        if video_path:
            try:
                os.unlink(video_path)
                logger.debug(f"🗑️ Cleaned up temp file: {video_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to cleanup temp file {video_path}: {e}")


def _safe_model_dump(obj: Any) -> Optional[Dict[str, Any]]:
    """안전한 Pydantic model dump"""
    if obj is None:
        return None
    try:
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        elif isinstance(obj, dict):
            return obj
        else:
            return None
    except Exception as e:
        logger.warning(f"model_dump failed: {e}")
        return None


def _safe_list_dump(items: Any) -> List[Dict[str, Any]]:
    """안전한 리스트 model dump"""
    if not items:
        return []

    result = []
    try:
        for item in items:
            dumped = _safe_model_dump(item)
            if dumped:
                result.append(dumped)
    except Exception as e:
        logger.warning(f"List dump failed: {e}")

    return result


def convert_result_to_vdg_data(result: VDGUnifiedResult) -> Dict[str, Any]:
    """
    VDGUnifiedResult → save_vdg_to_db용 vdg_data dict 변환

    Hardening:
    - Null checks for all attributes
    - Safe model_dump with fallback
    - Error isolation per field

    Phase 1 Cinematography Pipeline:
    - llm_output의 viral_kicks, mise_en_scene_signals 추출
    - hook_genome, scenes, implementation_layer 매핑

    Returns:
        Dict or empty dict if conversion fails
    """
    # Input validation
    if result is None:
        logger.warning("convert_result_to_vdg_data: result is None")
        return {}

    if not hasattr(result, "llm_output") or result.llm_output is None:
        logger.warning("convert_result_to_vdg_data: llm_output is None")
        return {}

    llm = result.llm_output

    try:
        # 1. viral_kicks 변환
        viral_kicks = []
        if hasattr(llm, "provenance") and llm.provenance:
            prov = llm.provenance
            if hasattr(prov, "viral_kicks") and prov.viral_kicks:
                viral_kicks = _safe_list_dump(prov.viral_kicks)

        # 2. comment_evidence_top5
        comment_evidence_top5 = []
        if hasattr(llm, "comment_evidence_top5") and llm.comment_evidence_top5:
            comment_evidence_top5 = _safe_list_dump(llm.comment_evidence_top5)

        # 3. mise_en_scene_signals
        mise_en_scene_signals = []
        if hasattr(llm, "mise_en_scene_signals") and llm.mise_en_scene_signals:
            mise_en_scene_signals = _safe_list_dump(llm.mise_en_scene_signals)

        # 4. hook_genome
        hook_genome = {}
        if hasattr(llm, "hook_genome") and llm.hook_genome:
            hook_genome = _safe_model_dump(llm.hook_genome) or {}

        # 5. scenes
        scenes = []
        if hasattr(llm, "scenes") and llm.scenes:
            scenes = _safe_list_dump(llm.scenes)

        # 6. implementation_layer
        implementation_layer = {}
        if hasattr(llm, "implementation_layer") and llm.implementation_layer:
            implementation_layer = _safe_model_dump(llm.implementation_layer) or {}

        # 7. capsule_brief (shotlist 포함)
        capsule_brief = {}
        if hasattr(llm, "capsule_brief") and llm.capsule_brief:
            capsule_brief = _safe_model_dump(llm.capsule_brief) or {}

        # Meta 정보 (safe access)
        pipeline_version = getattr(result, "pipeline_version", "unknown")
        run_at = getattr(result, "run_at", "")
        total_latency_ms = getattr(result, "total_latency_ms", 0)

        return {
            "provenance": {
                "viral_kicks": viral_kicks,
                "comment_evidence_top5": comment_evidence_top5,
            },
            "viral_kicks": viral_kicks,
            "comment_evidence_top5": comment_evidence_top5,
            "mise_en_scene_signals": mise_en_scene_signals,
            "hook_genome": hook_genome,
            "scenes": scenes,
            "implementation_layer": implementation_layer,
            "capsule_brief": capsule_brief,
            "meta": {
                "pipeline_version": pipeline_version,
                "run_at": run_at,
                "total_latency_ms": total_latency_ms,
            },
        }

    except Exception as e:
        logger.error(f"convert_result_to_vdg_data failed: {e}", exc_info=True)
        return {}
