"""VPE (Video Parsing Engine) Service.

Analyzes video content using Gemini 3 Pro to extract cinematographic DNA (Logic Vector).

Features:
- Gemini 3 Pro video understanding API integration
- Shot-by-shot analysis with timestamp extraction
- Logic Vector generation for auteur DNA
- Confidence scoring and evidence_refs generation

Usage:
    from app.services.vpe_service import VPEService, get_vpe_service

    service = get_vpe_service()
    result = await service.parse_video(
        video_uri="gs://bucket/video.mp4",
        auteur_hint="bong",
    )
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from app.config import settings
from app.schemas.vpe import (
    Cadence,
    CameraGrammar,
    ColorScience,
    Composition,
    LightingPhysics,
    LogicVector,
    ShotAnalysis,
    VPEParseResponse,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Credit costs
VPE_CREDIT_COST = 50  # 50 credits per video analysis

# Timeout configuration
DEFAULT_MAX_WAIT_SECONDS = 300  # 5 minutes max wait
DEFAULT_TIMEOUT_SECONDS = 300

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 30]
RETRYABLE_ERRORS = ["RATE_LIMIT", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "DEADLINE_EXCEEDED"]

# User-friendly error messages (Korean)
ERROR_MESSAGES = {
    "RATE_LIMIT": "요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
    "QUOTA_EXCEEDED": "일일 사용량을 초과했습니다. 내일 다시 시도해주세요.",
    "RESOURCE_EXHAUSTED": "서버가 바쁩니다. 잠시 후 다시 시도해주세요.",
    "UNAVAILABLE": "서비스가 일시적으로 불안정합니다. 잠시 후 다시 시도해주세요.",
    "DEADLINE_EXCEEDED": "요청 시간이 초과되었습니다. 다시 시도해주세요.",
    "INVALID_ARGUMENT": "입력값이 올바르지 않습니다. 영상 URL을 확인해주세요.",
    "PERMISSION_DENIED": "API 키가 유효하지 않거나 권한이 없습니다.",
    "NOT_FOUND": "영상을 찾을 수 없습니다. URL을 확인해주세요.",
    "CONTENT_POLICY": "콘텐츠 정책에 위배되는 내용이 감지되었습니다.",
    "SAFETY": "안전 정책에 위배되는 내용이 감지되었습니다.",
    "TIMEOUT": "영상 분석 시간이 초과되었습니다. 더 짧은 영상을 시도해보세요.",
    "VIDEO_TOO_LONG": "영상이 너무 깁니다. 10분 이하의 영상을 사용해주세요.",
}


def _get_user_friendly_error(error: str) -> str:
    """Convert technical error to user-friendly Korean message."""
    error_upper = error.upper()

    for key, message in ERROR_MESSAGES.items():
        if key in error_upper:
            return message

    if "error" in error.lower() or "exception" in error.lower():
        return f"영상 분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요. (상세: {error[:100]})"

    return error


# =============================================================================
# System Prompts
# =============================================================================

VPE_SYSTEM_PROMPT = """당신은 영화 분석 전문가입니다. 제공된 영상을 분석하여 시네마틱 DNA (Logic Vector)를 추출하세요.

분석 항목:
1. CADENCE (리듬/페이싱): 샷 길이 평균, 리듬 패턴, 템포, hook/build/climax 타이밍
2. COMPOSITION (구도): 주요 구도 전략 (vertical_blocking, rule_of_thirds, central_framing 등), 대칭 점수
3. CAMERA_GRAMMAR (카메라 무브먼트): 각 카메라 움직임 비율 (static, dolly, handheld, push_in 등)
4. LIGHTING_PHYSICS (조명): 키 라이트 스타일 (high_key, low_key, natural 등), 색온도 범위
5. COLOR_SCIENCE (색채): LUT 참조, 팔레트 색상, 채도 레벨

각 샷별로 분석하고, 전체 영상의 Logic Vector를 JSON 형식으로 출력하세요.

출력 형식:
```json
{
  "logic_vector": {
    "auteur_id": "분석 결과 추정된 스타일 (예: bong, epoch, prism, wong, voltage, park, seoyeon, yoon, abyss, wes_anderson, coen, nova, lynch, original)",
    "cadence": {
      "hook": 0.0,
      "build": 0.0,
      "climax": 0.0,
      "avg_shot_length": 0.0,
      "rhythm_pattern": "slow_build|staccato|meditative|dynamic",
      "tempo": "deliberate|frenetic|meditative|balanced"
    },
    "composition": {
      "primary_strategy": "vertical_blocking|rule_of_thirds|central_framing|diagonal_tension|frame_within_frame|negative_space|symmetry|asymmetry",
      "symmetry_score": 0.0,
      "depth_staging": "deep_focus|shallow|layered",
      "aspect_ratio_preference": "2.39:1|1.85:1|16:9|4:3"
    },
    "camera_grammar": {
      "static": 0.0,
      "dolly": 0.0,
      "handheld": 0.0,
      "push_in": 0.0,
      "pull_out": 0.0,
      "pan": 0.0,
      "tilt": 0.0,
      "crane": 0.0,
      "tracking": 0.0,
      "steadicam": 0.0
    },
    "lighting_physics": {
      "key_light": "high_key|low_key|natural|chiaroscuro|silhouette|practical|mixed",
      "color_temp_range": [3200, 5600],
      "contrast_ratio": "high|low|medium|4:1",
      "shadow_quality": "hard|soft|diffused"
    },
    "color_science": {
      "lut_reference": "Kodak_2383|Fuji_3510|ARRI_LogC|custom|none",
      "palette": ["desaturated", "warm_tones", "cool_tones", "monochromatic", "vibrant"],
      "saturation_level": "desaturated|muted|natural|vibrant",
      "dominant_hue": "blue|orange|green|yellow|red|neutral"
    }
  },
  "shots": [
    {
      "shot_number": 1,
      "start_time": 0.0,
      "end_time": 2.5,
      "duration": 2.5,
      "camera_movement": "static|dolly|handheld|...",
      "camera_angle": "eye_level|low_angle|high_angle|dutch|bird_eye|worm_eye",
      "shot_size": "extreme_wide|wide|full|medium_full|medium|medium_close|close|extreme_close",
      "composition_notes": "프레임 내 주요 요소 배치 설명",
      "lighting_style": "high_key|low_key|natural|...",
      "subjects": ["인물", "배경요소"],
      "action_description": "샷에서 일어나는 액션",
      "emotional_tone": "tension|calm|joy|sadness|mystery|..."
    }
  ],
  "confidence": 0.85,
  "analysis_notes": "분석 과정에서의 특이사항"
}
```

모든 비율 값은 0.0~1.0 사이로 출력하세요. 전체 비율 합이 1.0이 되도록 정규화하세요."""

VPE_SHOT_ANALYSIS_PROMPT = """영상의 각 샷을 상세히 분석하세요.
타임코드, 카메라 움직임, 구도, 조명, 피사체를 포함하세요.
최대 {max_shots}개의 샷만 분석하세요."""


# =============================================================================
# Progress Tracking
# =============================================================================

@dataclass
class VPEProgress:
    """Progress update during VPE video analysis."""
    status: str  # "uploading", "analyzing", "extracting", "completed", "failed"
    elapsed_seconds: float
    estimated_remaining_seconds: Optional[float] = None
    current_shot: int = 0
    total_shots: int = 0
    message: str = ""


# =============================================================================
# VPE Service
# =============================================================================

class VPEServiceError(Exception):
    """Base exception for VPE service errors."""
    pass


class VPETimeoutError(VPEServiceError):
    """Raised when video analysis times out."""
    pass


class VPEAnalysisError(VPEServiceError):
    """Raised when video analysis fails."""
    pass


class VPEService:
    """Video Parsing Engine service for extracting Logic Vectors."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize VPE service.

        Args:
            api_key: Optional API key. Uses settings.GEMINI_API_KEY if not provided.
        """
        self._api_key = api_key or settings.GEMINI_API_KEY.get_secret_value()
        self._client = None

    def _get_client(self):
        """Get or create the GenAI client."""
        if self._client is None:
            from google import genai
            if not self._api_key:
                raise VPEServiceError("No API key available. Configure GEMINI_API_KEY.")
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def parse_video(
        self,
        video_uri: str,
        auteur_hint: Optional[str] = None,
        extract_shots: bool = True,
        max_shots: int = 50,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        progress_callback: Optional[Callable[[VPEProgress], None]] = None,
    ) -> VPEParseResponse:
        """Parse video and extract Logic Vector.

        Args:
            video_uri: Video URI (gs://, https://, or YouTube URL)
            auteur_hint: Optional hint for auteur style matching
            extract_shots: Whether to extract shot-by-shot analysis
            max_shots: Maximum number of shots to analyze
            timeout_seconds: Timeout for analysis
            progress_callback: Optional callback for progress updates

        Returns:
            VPEParseResponse with Logic Vector and optional shot analysis
        """
        from google.genai import types

        start_time = time.monotonic()
        trace_id = str(uuid.uuid4())

        # Helper to emit progress updates
        def emit_progress(status: str, message: str = "", current_shot: int = 0, total_shots: int = 0):
            if progress_callback:
                try:
                    elapsed = time.monotonic() - start_time
                    estimated_remaining = None
                    if status == "analyzing" and elapsed < timeout_seconds:
                        estimated_remaining = max(0, 60 - elapsed)  # Rough estimate
                    progress_callback(VPEProgress(
                        status=status,
                        elapsed_seconds=elapsed,
                        estimated_remaining_seconds=estimated_remaining,
                        current_shot=current_shot,
                        total_shots=total_shots,
                        message=message,
                    ))
                except Exception as e:
                    logger.warning(f"[VPE] Progress callback failed: {e}")

        logger.info(f"[VPE] Starting video analysis: uri={video_uri[:50]}..., auteur_hint={auteur_hint}")
        emit_progress("uploading", "영상 분석 준비 중...")

        try:
            client = self._get_client()

            # Build the prompt with auteur hint
            system_prompt = VPE_SYSTEM_PROMPT
            if auteur_hint:
                system_prompt += f"\n\n참고: 이 영상은 '{auteur_hint}' 스타일의 특징을 가질 수 있습니다. 이를 염두에 두고 분석하세요."

            shot_prompt = VPE_SHOT_ANALYSIS_PROMPT.format(max_shots=max_shots) if extract_shots else ""
            full_prompt = f"{system_prompt}\n\n{shot_prompt}"

            emit_progress("analyzing", "Gemini 3 Pro로 영상 분석 중...")

            # Call Gemini with video file
            # Handle different URI types
            video_content = None

            if video_uri.startswith("gs://"):
                # Google Cloud Storage URI
                video_content = types.Part.from_uri(
                    file_uri=video_uri,
                    mime_type="video/mp4"
                )
            elif "youtube.com" in video_uri or "youtu.be" in video_uri:
                # YouTube URL - pass directly
                video_content = types.Part.from_uri(
                    file_uri=video_uri,
                    mime_type="video/*"
                )
            else:
                # HTTPS URL - try to use as file reference
                video_content = types.Part.from_uri(
                    file_uri=video_uri,
                    mime_type="video/mp4"
                )

            # Generate content with video and prompt
            response = None
            last_error = None

            for attempt in range(MAX_RETRIES):
                try:
                    response = await asyncio.to_thread(
                        client.models.generate_content,
                        model="gemini-3-pro-preview",
                        contents=[
                            video_content,
                            full_prompt,
                        ],
                        config=types.GenerateContentConfig(
                            temperature=0.3,
                            max_output_tokens=8192,
                            response_mime_type="application/json",
                        ),
                    )
                    break
                except Exception as e:
                    last_error = e
                    error_str = str(e).upper()

                    is_retryable = any(err in error_str for err in RETRYABLE_ERRORS)

                    if is_retryable and attempt < MAX_RETRIES - 1:
                        delay = RETRY_DELAYS[attempt]
                        logger.warning(f"[VPE] API error (attempt {attempt + 1}/{MAX_RETRIES}): {e}. Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        continue

                    raise

            if response is None:
                raise VPEAnalysisError(f"Failed to get response: {last_error}")

            emit_progress("extracting", "Logic Vector 추출 중...")

            # Parse the response
            response_text = response.text if hasattr(response, 'text') else str(response)

            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)

            # Clean up common JSON issues
            response_text = response_text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]

            try:
                parsed_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"[VPE] Failed to parse JSON response: {e}\nResponse: {response_text[:500]}")
                raise VPEAnalysisError(f"Failed to parse analysis response: {e}")

            # Extract Logic Vector
            lv_data = parsed_data.get("logic_vector", {})

            # Build LogicVector object
            logic_vector = LogicVector(
                auteur_id=lv_data.get("auteur_id", auteur_hint or "original"),
                cadence=Cadence(**lv_data.get("cadence", {})) if lv_data.get("cadence") else Cadence(),
                composition=Composition(**lv_data.get("composition", {})) if lv_data.get("composition") else Composition(),
                camera_grammar=CameraGrammar(**lv_data.get("camera_grammar", {})) if lv_data.get("camera_grammar") else CameraGrammar(),
                lighting_physics=LightingPhysics(**lv_data.get("lighting_physics", {})) if lv_data.get("lighting_physics") else LightingPhysics(),
                color_science=ColorScience(**lv_data.get("color_science", {})) if lv_data.get("color_science") else ColorScience(),
                source_video=video_uri,
                analysis_timestamp=datetime.utcnow(),
                confidence=parsed_data.get("confidence", 0.7),
            )

            # Extract shot analysis
            shots = None
            if extract_shots and "shots" in parsed_data:
                shots = []
                for shot_data in parsed_data["shots"][:max_shots]:
                    try:
                        shot = ShotAnalysis(
                            shot_number=shot_data.get("shot_number", len(shots) + 1),
                            start_time=shot_data.get("start_time", 0.0),
                            end_time=shot_data.get("end_time", 0.0),
                            duration=shot_data.get("duration", 0.0),
                            camera_movement=shot_data.get("camera_movement"),
                            camera_angle=shot_data.get("camera_angle"),
                            shot_size=shot_data.get("shot_size"),
                            composition_notes=shot_data.get("composition_notes"),
                            lighting_style=shot_data.get("lighting_style"),
                            subjects=shot_data.get("subjects", []),
                            action_description=shot_data.get("action_description"),
                            emotional_tone=shot_data.get("emotional_tone"),
                        )
                        shots.append(shot)
                    except Exception as e:
                        logger.warning(f"[VPE] Failed to parse shot {shot_data}: {e}")

            processing_time_ms = int((time.monotonic() - start_time) * 1000)

            # Generate evidence_refs
            evidence_refs = [f"db:vpe_results:{trace_id}"]

            emit_progress("completed", "영상 분석 완료!")

            logger.info(f"[VPE] Analysis completed in {processing_time_ms}ms, auteur={logic_vector.auteur_id}")

            return VPEParseResponse(
                success=True,
                trace_id=trace_id,
                logic_vector=logic_vector,
                shots=shots,
                evidence_refs=evidence_refs,
                confidence=logic_vector.confidence,
                processing_time_ms=processing_time_ms,
                shot_count=len(shots) if shots else 0,
            )

        except VPEServiceError:
            raise
        except Exception as e:
            processing_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.exception(f"[VPE] Video analysis error: {e}")
            user_friendly_error = _get_user_friendly_error(str(e))
            emit_progress("failed", user_friendly_error)

            return VPEParseResponse(
                success=False,
                trace_id=trace_id,
                error=user_friendly_error,
                processing_time_ms=processing_time_ms,
            )

    async def parse_video_simple(
        self,
        video_uri: str,
        auteur_hint: Optional[str] = None,
    ) -> VPEParseResponse:
        """Simplified video parsing with defaults.

        Args:
            video_uri: Video URI
            auteur_hint: Optional auteur hint

        Returns:
            VPEParseResponse
        """
        return await self.parse_video(
            video_uri=video_uri,
            auteur_hint=auteur_hint,
            extract_shots=True,
            max_shots=30,
        )

    async def merge_logic_vectors(
        self,
        vectors: List[LogicVector],
        weights: Optional[List[float]] = None,
    ) -> LogicVector:
        """Merge multiple Logic Vectors into one.

        Useful for combining analysis from multiple videos of the same auteur.

        Args:
            vectors: List of Logic Vectors to merge
            weights: Optional weights for each vector (default: equal weights)

        Returns:
            Merged LogicVector
        """
        if not vectors:
            raise ValueError("At least one Logic Vector required")

        if len(vectors) == 1:
            return vectors[0]

        # Default to equal weights
        if weights is None:
            weights = [1.0 / len(vectors)] * len(vectors)
        else:
            # Normalize weights
            total = sum(weights)
            weights = [w / total for w in weights]

        # Merge camera_grammar by weighted average
        merged_camera = {}
        for key in ["static", "dolly", "handheld", "push_in", "pull_out", "pan", "tilt", "crane", "tracking", "steadicam"]:
            merged_camera[key] = sum(
                getattr(v.camera_grammar, key, 0.0) * w
                for v, w in zip(vectors, weights)
            )

        # Merge composition by most common primary_strategy
        strategies = [v.composition.primary_strategy for v in vectors]
        most_common_strategy = max(set(strategies), key=strategies.count)
        avg_symmetry = sum(v.composition.symmetry_score * w for v, w in zip(vectors, weights))

        # Merge color palettes
        all_palettes = []
        for v in vectors:
            all_palettes.extend(v.color_science.palette)
        unique_palettes = list(set(all_palettes))[:5]

        # Use most common auteur_id or "merged"
        auteur_ids = [v.auteur_id for v in vectors]
        most_common_auteur = max(set(auteur_ids), key=auteur_ids.count)

        # Average confidence
        avg_confidence = sum(v.confidence * w for v, w in zip(vectors, weights))

        return LogicVector(
            auteur_id=most_common_auteur,
            cadence=vectors[0].cadence,  # Take from first vector
            composition=Composition(
                primary_strategy=most_common_strategy,
                symmetry_score=avg_symmetry,
            ),
            camera_grammar=CameraGrammar(**merged_camera),
            lighting_physics=vectors[0].lighting_physics,  # Take from first
            color_science=ColorScience(
                lut_reference=vectors[0].color_science.lut_reference,
                palette=unique_palettes,
            ),
            analysis_timestamp=datetime.utcnow(),
            confidence=avg_confidence,
        )


# =============================================================================
# Module-level convenience functions
# =============================================================================

_default_service: Optional[VPEService] = None


def get_vpe_service(api_key: Optional[str] = None) -> VPEService:
    """Get or create the default VPE service instance.

    Args:
        api_key: Optional API key override

    Returns:
        VPEService instance
    """
    global _default_service
    if api_key:
        return VPEService(api_key=api_key)
    if _default_service is None:
        _default_service = VPEService()
    return _default_service


async def parse_video(
    video_uri: str,
    auteur_hint: Optional[str] = None,
    extract_shots: bool = True,
    api_key: Optional[str] = None,
) -> VPEParseResponse:
    """Convenience function for video parsing.

    Args:
        video_uri: Video URI
        auteur_hint: Optional auteur hint
        extract_shots: Whether to extract shots
        api_key: Optional API key override

    Returns:
        VPEParseResponse
    """
    service = get_vpe_service(api_key)
    return await service.parse_video(
        video_uri=video_uri,
        auteur_hint=auteur_hint,
        extract_shots=extract_shots,
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "VPEService",
    "VPEServiceError",
    "VPETimeoutError",
    "VPEAnalysisError",
    "VPEProgress",
    "VPE_CREDIT_COST",
    "get_vpe_service",
    "parse_video",
]
