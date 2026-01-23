"""Reference Analyzer Service for 4D Reference Decoder (2026 Expert Workflow).

Comprehensive reference analysis for videos and images:
- Frame-by-frame video analysis
- Scene detection and shot breakdown
- Style extraction integration
- Shot list generation for recreation
- Moodboard generation

Based on expert workflow: "레퍼런스 영상을 프레임별로 분석해서 샷 리스트를 만들어요"
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import tempfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from app.config import settings
from app.services.ai.style_extractor import (
    StyleExtractor,
    StyleExtractionResult,
    get_style_extractor,
)
from app.services.ai.auteur_matcher import (
    AuteurMatcher,
    AuteurMatch,
    get_auteur_matcher,
)
from app.services.ai.technique_detector import (
    TechniqueDetector,
    DetectedTechnique,
    TechniqueCategory,
    get_technique_detector,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Models
# =============================================================================


class FrameAnalysis(BaseModel):
    """Analysis result for a single video frame."""

    timestamp: float = Field(description="Timestamp in seconds")
    frame_number: int = Field(default=0, description="Frame number in sequence")
    description: str = Field(default="", description="Scene description")
    objects: List[str] = Field(default_factory=list, description="Detected objects")
    actions: List[str] = Field(default_factory=list, description="Actions/movements")
    characters: List[str] = Field(
        default_factory=list, description="Character descriptions"
    )
    camera_movement: Optional[str] = Field(
        default=None, description="Camera movement (pan, tilt, zoom, etc.)"
    )
    shot_type: Optional[str] = Field(
        default=None, description="Shot type (wide, medium, close-up, etc.)"
    )
    emotion: Optional[str] = Field(
        default=None, description="Emotional tone of the scene"
    )
    frame_base64: Optional[str] = Field(
        default=None, description="Base64 encoded frame for moodboard"
    )


class ShotSuggestion(BaseModel):
    """Suggested shot for recreation."""

    shot_number: int = Field(description="Shot sequence number")
    duration_seconds: float = Field(description="Suggested duration")
    description: str = Field(description="Shot description for recreation")
    camera_setup: str = Field(description="Camera setup instructions")
    prompt: str = Field(description="AI generation prompt for this shot")
    reference_frame_index: int = Field(
        description="Index of the reference frame this is based on"
    )


class SceneSegment(BaseModel):
    """A scene segment detected in the video."""

    start_time: float = Field(description="Start timestamp")
    end_time: float = Field(description="End timestamp")
    duration: float = Field(description="Duration in seconds")
    description: str = Field(description="Scene description")
    key_frame_index: int = Field(description="Index of representative frame")


class AuteurMatchSummary(BaseModel):
    """Summary of auteur match for serialization."""

    auteur_key: str = Field(description="Auteur key")
    auteur_name: str = Field(description="Auteur name in Korean")
    similarity_score: float = Field(description="Similarity score (0-1)")
    matched_techniques: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)


class DetectedTechniqueSummary(BaseModel):
    """Summary of detected technique for serialization."""

    technique_id: str = Field(description="Technique identifier")
    name: str = Field(description="Technique name")
    category: str = Field(description="Category (shot_type, camera_movement, etc.)")
    confidence: float = Field(description="Detection confidence")
    timestamp: Optional[float] = Field(default=None)
    description: Optional[str] = Field(default=None)


class VideoReferenceAnalysis(BaseModel):
    """Complete analysis result for a video reference."""

    # Basic info
    total_duration: float = Field(default=0.0, description="Total video duration in seconds")
    frame_count: int = Field(default=0, description="Number of analyzed frames")
    fps: float = Field(default=24.0, description="Video FPS")

    # Frame analysis
    frames: List[FrameAnalysis] = Field(
        default_factory=list, description="Per-frame analysis"
    )

    # Scene detection
    scenes: List[SceneSegment] = Field(
        default_factory=list, description="Detected scene segments"
    )

    # Style
    style: StyleExtractionResult = Field(
        default_factory=StyleExtractionResult, description="Extracted visual style"
    )

    # Auteur matching (Phase 2)
    auteur_matches: List[AuteurMatchSummary] = Field(
        default_factory=list, description="Matched auteurs based on style"
    )

    # Technique detection (Phase 2)
    detected_techniques: List[DetectedTechniqueSummary] = Field(
        default_factory=list, description="Detected cinematography techniques"
    )

    # Shot list for recreation
    suggested_shots: List[ShotSuggestion] = Field(
        default_factory=list, description="Suggested shots to recreate"
    )

    # Moodboard
    moodboard_frames: List[str] = Field(
        default_factory=list, description="Base64 encoded key frames for moodboard"
    )

    # Metadata
    analysis_depth: str = Field(
        default="detailed", description="Analysis depth used"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall confidence"
    )

    # Evidence refs (RAG traceability)
    evidence_refs: List[str] = Field(
        default_factory=list, description="Evidence references for RAG traceability"
    )


class ImageReferenceAnalysis(BaseModel):
    """Analysis result for an image reference."""

    description: str = Field(default="", description="Image description")
    style: StyleExtractionResult = Field(
        default_factory=StyleExtractionResult, description="Extracted style"
    )
    objects: List[str] = Field(default_factory=list, description="Detected objects")
    composition_analysis: str = Field(default="", description="Composition breakdown")
    recreation_prompt: str = Field(
        default="", description="Prompt to recreate this image"
    )
    similar_references: List[str] = Field(
        default_factory=list, description="Similar reference suggestions"
    )

    # Phase 2: Auteur matching
    auteur_matches: List[AuteurMatchSummary] = Field(
        default_factory=list, description="Matched auteurs based on style"
    )

    # Phase 2: Technique detection
    detected_techniques: List[DetectedTechniqueSummary] = Field(
        default_factory=list, description="Detected composition techniques"
    )

    # Evidence refs for RAG traceability
    evidence_refs: List[str] = Field(
        default_factory=list, description="Evidence references"
    )


@dataclass
class ReferenceAnalyzerConfig:
    """Configuration for reference analysis."""

    model: str = "gemini-3-pro-preview"  # Gemini 3 Pro for detailed analysis (Jan 2026)
    flash_model: str = "gemini-3-flash-preview"  # Gemini 3 Flash for quick frame analysis
    max_frames: int = 20  # Max frames to analyze for detailed
    quick_frames: int = 10  # Frames for quick analysis
    comprehensive_frames: int = 30  # Frames for comprehensive
    max_retries: int = 3
    timeout_seconds: float = 60.0


# =============================================================================
# Errors
# =============================================================================


class ReferenceAnalysisError(Exception):
    """Base error for reference analysis."""

    pass


class VideoProcessingError(ReferenceAnalysisError):
    """Raised when video processing fails."""

    pass


# =============================================================================
# Reference Analyzer Service
# =============================================================================


class ReferenceAnalyzer:
    """Comprehensive reference analysis (Expert Workflow Core).

    Analyzes video and image references to extract:
    - Frame-by-frame scene information
    - Visual style for consistency
    - Shot list for recreation
    - Moodboard materials
    """

    FRAME_ANALYSIS_PROMPT = """이 비디오 프레임을 분석하고 다음 정보를 추출하세요:

1. description: 장면 설명 (1-2문장, 한국어로)
2. objects: 보이는 오브젝트/요소 목록
3. actions: 보이는 동작 또는 움직임
4. characters: 인물/캐릭터 설명
5. camera_movement: 카메라 움직임 (고정, 팬, 틸트, 줌, 달리, 트래킹 등)
6. shot_type: 샷 유형 (익스트림 와이드, 와이드, 미디엄 와이드, 미디엄, 미디엄 클로즈업, 클로즈업, 익스트림 클로즈업)
7. emotion: 감정적 톤 (신남, 긴장, 평화, 슬픔, 신비 등)

모든 설명은 한국어로 작성하고, 반드시 유효한 JSON만 반환하세요."""

    SHOT_LIST_PROMPT = """다음 프레임 분석을 바탕으로 이 비디오 시퀀스를 재현하기 위한 샷 리스트를 만드세요.

프레임 분석:
{frame_analyses}

각 샷에 대해 다음 정보를 제공하세요:
1. shot_number: 순번
2. duration_seconds: 권장 지속 시간 (페이스 기반)
3. description: 이 샷에서 일어나는 일 (한국어로 작성)
4. camera_setup: 카메라 앵글, 움직임, 프레이밍 지시사항 (한국어로)
5. prompt: 이 샷을 재현하기 위한 AI 영상 생성 프롬프트 (100-150단어, 한국어로)
6. reference_frame_index: 참조 프레임 인덱스

JSON 배열로 반환하세요. 프롬프트는 다음을 포착해야 합니다:
- 정확한 비주얼 스타일
- 카메라 움직임과 프레이밍
- 피사체의 동작과 감정
- 조명과 분위기

모든 텍스트는 한국어로 작성하세요."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[ReferenceAnalyzerConfig] = None,
        style_extractor: Optional[StyleExtractor] = None,
        auteur_matcher: Optional[AuteurMatcher] = None,
        technique_detector: Optional[TechniqueDetector] = None,
    ):
        """Initialize ReferenceAnalyzer.

        Args:
            api_key: Optional API key
            config: Optional configuration
            style_extractor: Optional StyleExtractor instance
            auteur_matcher: Optional AuteurMatcher instance
            technique_detector: Optional TechniqueDetector instance
        """
        # H1.3: SecretStr - use .get_secret_value() for actual API key
        self._api_key = api_key or settings.GEMINI_API_KEY.get_secret_value()
        self.config = config or ReferenceAnalyzerConfig()
        self._style_extractor = style_extractor
        self._auteur_matcher = auteur_matcher
        self._technique_detector = technique_detector
        self._client = None

    def _get_client(self):
        """Get or create the GenAI client."""
        if self._client is None:
            from google import genai

            if not self._api_key:
                raise ReferenceAnalysisError(
                    "No API key available. Configure GEMINI_API_KEY."
                )
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def _get_style_extractor(self) -> StyleExtractor:
        """Get or create StyleExtractor instance."""
        if self._style_extractor is None:
            self._style_extractor = get_style_extractor(self._api_key)
        return self._style_extractor

    def _get_auteur_matcher(self) -> AuteurMatcher:
        """Get or create AuteurMatcher instance."""
        if self._auteur_matcher is None:
            self._auteur_matcher = get_auteur_matcher()
        return self._auteur_matcher

    def _get_technique_detector(self) -> TechniqueDetector:
        """Get or create TechniqueDetector instance."""
        if self._technique_detector is None:
            self._technique_detector = get_technique_detector()
        return self._technique_detector

    async def analyze_video_reference(
        self,
        video_bytes: bytes,
        analysis_depth: str = "detailed",  # "quick", "detailed", "comprehensive"
    ) -> VideoReferenceAnalysis:
        """Analyze video reference frame by frame.

        Args:
            video_bytes: Raw video bytes
            analysis_depth: Level of detail ("quick", "detailed", "comprehensive")

        Returns:
            VideoReferenceAnalysis with complete analysis

        Raises:
            ReferenceAnalysisError: If analysis fails
        """
        # Determine frame count based on depth
        if analysis_depth == "quick":
            num_frames = self.config.quick_frames
        elif analysis_depth == "comprehensive":
            num_frames = self.config.comprehensive_frames
        else:
            num_frames = self.config.max_frames

        logger.info(f"Starting video analysis: depth={analysis_depth}, frames={num_frames}")

        # Extract key frames with metadata
        frames, timestamps, fps, total_duration = self._extract_video_frames(
            video_bytes, num_frames
        )

        if not frames:
            raise VideoProcessingError("No frames could be extracted from video")

        # Analyze frames in parallel (batched to avoid rate limits)
        frame_analyses = await self._analyze_frames_batch(frames, timestamps)

        # Extract style from representative frame
        style_extractor = self._get_style_extractor()
        middle_frame_idx = len(frames) // 2
        try:
            style = await style_extractor.extract_style(
                frames[middle_frame_idx],
                additional_context="Key frame from video reference",
            )
        except Exception as e:
            logger.warning(f"Style extraction failed: {e}")
            style = StyleExtractionResult()

        # Detect scenes (simple shot boundary detection)
        scenes = self._detect_scenes(frame_analyses, timestamps)

        # Phase 2: Auteur matching based on style
        auteur_matcher = self._get_auteur_matcher()
        auteur_matches_raw = await auteur_matcher.match_style_to_auteurs(style, max_matches=3)

        # Convert AuteurMatch to AuteurMatchSummary for serialization
        auteur_matches = [
            AuteurMatchSummary(
                auteur_key=match.auteur_key,
                auteur_name=match.auteur_name,
                similarity_score=match.similarity_score,
                matched_techniques=[t.name for t in match.matched_techniques],
                evidence_refs=match.evidence_refs,
            )
            for match in auteur_matches_raw
        ]

        # Phase 2: Technique detection from frame analyses
        technique_detector = self._get_technique_detector()
        detected_techniques_raw = await technique_detector.detect_techniques(
            frame_analyses, timestamps
        )

        # Convert DetectedTechnique to DetectedTechniqueSummary for serialization
        detected_techniques = [
            DetectedTechniqueSummary(
                technique_id=tech.technique_id,
                name=tech.name,
                category=tech.category,
                confidence=tech.confidence,
                timestamp=tech.timestamp,
                description=tech.description,
            )
            for tech in detected_techniques_raw
        ]

        # Generate shot list
        suggested_shots = await self._generate_shot_list(
            frame_analyses, style, timestamps
        )

        # Select moodboard frames (key moments)
        moodboard_frames = self._select_moodboard_frames(frames, frame_analyses, 5)

        # Calculate confidence
        confidence = sum(
            1.0 for f in frame_analyses if f.description
        ) / max(len(frame_analyses), 1)

        # Collect evidence refs for RAG traceability
        evidence_refs = []
        for match in auteur_matches:
            evidence_refs.extend(match.evidence_refs)

        return VideoReferenceAnalysis(
            total_duration=total_duration,
            frame_count=len(frames),
            fps=fps,
            frames=frame_analyses,
            scenes=scenes,
            style=style,
            auteur_matches=auteur_matches,
            detected_techniques=detected_techniques,
            suggested_shots=suggested_shots,
            moodboard_frames=moodboard_frames,
            analysis_depth=analysis_depth,
            confidence=confidence,
            evidence_refs=evidence_refs,
        )

    async def analyze_image_reference(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
    ) -> ImageReferenceAnalysis:
        """Analyze image reference.

        Args:
            image_bytes: Raw image bytes
            mime_type: Image MIME type

        Returns:
            ImageReferenceAnalysis with complete analysis
        """
        from google.genai import types

        client = self._get_client()
        style_extractor = self._get_style_extractor()

        # Extract style
        style = await style_extractor.extract_style(image_bytes, mime_type=mime_type)

        # Detailed image analysis
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        analysis_prompt = """이 레퍼런스 이미지를 상세히 분석하세요:

1. description: 장면에 대한 상세 설명 (3-5문장, 한국어로)
2. objects: 보이는 모든 오브젝트와 요소
3. composition_analysis: 이미지 구도 분석 (삼등분법, 유도선 등)
4. recreation_prompt: AI로 이 이미지를 재현하기 위한 상세 프롬프트 (150-200단어, 한국어로),
   스타일, 조명, 구도, 분위기, 모든 시각적 요소 포함.
5. similar_references: 유사한 레퍼런스 스타일 또는 아티스트 3-5개 제안

모든 텍스트는 한국어로 작성하고, 반드시 유효한 JSON만 반환하세요."""

        response = await asyncio.to_thread(
            client.models.generate_content,
            model=self.config.model,
            contents=[image_part, analysis_prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,
            ),
        )

        try:
            data = json.loads(response.text.strip())
        except json.JSONDecodeError:
            data = {}

        # Phase 2: Auteur matching based on extracted style
        auteur_matcher = self._get_auteur_matcher()
        auteur_matches_raw = await auteur_matcher.match_style_to_auteurs(style, max_matches=3)

        # Convert to summary format
        auteur_matches = [
            AuteurMatchSummary(
                auteur_key=match.auteur_key,
                auteur_name=match.auteur_name,
                similarity_score=match.similarity_score,
                matched_techniques=[t.name for t in match.matched_techniques],
                evidence_refs=match.evidence_refs,
            )
            for match in auteur_matches_raw
        ]

        # Phase 2: Simple technique detection for images (composition-focused)
        technique_detector = self._get_technique_detector()

        # Create a single frame analysis from image data for technique detection
        frame_analysis = FrameAnalysis(
            timestamp=0.0,
            frame_number=0,
            description=data.get("description", ""),
            objects=data.get("objects", []),
            shot_type=self._infer_shot_type_from_composition(data.get("composition_analysis", "")),
        )
        detected_techniques_raw = await technique_detector.detect_techniques([frame_analysis], [0.0])

        detected_techniques = [
            DetectedTechniqueSummary(
                technique_id=tech.technique_id,
                name=tech.name,
                category=tech.category,
                confidence=tech.confidence,
                timestamp=tech.timestamp,
                description=tech.description,
            )
            for tech in detected_techniques_raw
        ]

        # Collect evidence refs
        evidence_refs = []
        for match in auteur_matches:
            evidence_refs.extend(match.evidence_refs)

        return ImageReferenceAnalysis(
            description=data.get("description", ""),
            style=style,
            objects=data.get("objects", []),
            composition_analysis=data.get("composition_analysis", ""),
            recreation_prompt=data.get("recreation_prompt", ""),
            similar_references=data.get("similar_references", []),
            auteur_matches=auteur_matches,
            detected_techniques=detected_techniques,
            evidence_refs=evidence_refs,
        )

    def _infer_shot_type_from_composition(self, composition: str) -> Optional[str]:
        """Infer shot type from composition analysis text."""
        composition_lower = composition.lower()
        if "클로즈업" in composition_lower or "close-up" in composition_lower or "얼굴" in composition_lower:
            return "클로즈업"
        if "와이드" in composition_lower or "wide" in composition_lower or "전경" in composition_lower:
            return "와이드"
        if "미디엄" in composition_lower or "medium" in composition_lower:
            return "미디엄"
        return None

    def _extract_video_frames(
        self,
        video_bytes: bytes,
        num_frames: int,
    ) -> Tuple[List[bytes], List[float], float, float]:
        """Extract key frames from video with metadata.

        Returns:
            Tuple of (frames, timestamps, fps, total_duration)
        """
        try:
            import cv2
        except ImportError:
            raise VideoProcessingError("OpenCV not available for video processing")

        frames = []
        timestamps = []
        temp_path = None

        try:
            # Write to temp file
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                f.write(video_bytes)
                temp_path = f.name

            cap = cv2.VideoCapture(temp_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
            total_duration = total_frames / fps

            if total_frames == 0:
                raise VideoProcessingError("Video has no frames")

            # Calculate intervals for even distribution
            interval = max(1, total_frames // num_frames)

            for i in range(0, total_frames, interval):
                if len(frames) >= num_frames:
                    break

                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()

                if ret:
                    # Encode to JPEG
                    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    frames.append(buffer.tobytes())
                    timestamps.append(i / fps)

            cap.release()

            return frames, timestamps, fps, total_duration

        except Exception as e:
            raise VideoProcessingError(f"Frame extraction failed: {e}")
        finally:
            if temp_path:
                import os

                try:
                    os.unlink(temp_path)
                except Exception:
                    pass

    async def _analyze_frames_batch(
        self,
        frames: List[bytes],
        timestamps: List[float],
        batch_size: int = 5,
    ) -> List[FrameAnalysis]:
        """Analyze frames in batches to manage rate limits."""
        from google.genai import types

        client = self._get_client()
        results = []

        for i in range(0, len(frames), batch_size):
            batch = frames[i : i + batch_size]
            batch_timestamps = timestamps[i : i + batch_size]

            # Analyze batch in parallel
            tasks = []
            for j, (frame, ts) in enumerate(zip(batch, batch_timestamps)):
                task = self._analyze_single_frame(
                    client, frame, ts, i + j, types
                )
                tasks.append(task)

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, FrameAnalysis):
                    results.append(result)
                else:
                    # Failed analysis - add placeholder
                    logger.warning(f"Frame analysis failed: {result}")
                    results.append(
                        FrameAnalysis(
                            timestamp=0.0,
                            description="Analysis failed",
                        )
                    )

            # Small delay between batches to avoid rate limits
            if i + batch_size < len(frames):
                await asyncio.sleep(0.5)

        return results

    async def _analyze_single_frame(
        self,
        client,
        frame_bytes: bytes,
        timestamp: float,
        frame_number: int,
        types,
    ) -> FrameAnalysis:
        """Analyze a single frame."""
        try:
            image_part = types.Part.from_bytes(
                data=frame_bytes, mime_type="image/jpeg"
            )

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.models.generate_content,
                    model=self.config.flash_model,  # Use flash for speed
                    contents=[image_part, self.FRAME_ANALYSIS_PROMPT],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                ),
                timeout=30.0,
            )

            data = json.loads(response.text.strip())

            return FrameAnalysis(
                timestamp=timestamp,
                frame_number=frame_number,
                description=data.get("description", ""),
                objects=data.get("objects", []),
                actions=data.get("actions", []),
                characters=data.get("characters", []),
                camera_movement=data.get("camera_movement"),
                shot_type=data.get("shot_type"),
                emotion=data.get("emotion"),
            )

        except Exception as e:
            logger.warning(f"Frame {frame_number} analysis error: {e}")
            return FrameAnalysis(
                timestamp=timestamp,
                frame_number=frame_number,
                description=f"Analysis failed: {str(e)[:50]}",
            )

    def _detect_scenes(
        self,
        frame_analyses: List[FrameAnalysis],
        timestamps: List[float],
    ) -> List[SceneSegment]:
        """Simple scene detection based on shot type changes."""
        if not frame_analyses:
            return []

        scenes = []
        current_scene_start = 0
        current_shot_type = frame_analyses[0].shot_type

        for i, analysis in enumerate(frame_analyses[1:], 1):
            # Scene change when shot type changes significantly
            if analysis.shot_type != current_shot_type:
                scenes.append(
                    SceneSegment(
                        start_time=timestamps[current_scene_start],
                        end_time=timestamps[i - 1] if i > 0 else timestamps[0],
                        duration=timestamps[i - 1] - timestamps[current_scene_start],
                        description=frame_analyses[current_scene_start].description,
                        key_frame_index=current_scene_start,
                    )
                )
                current_scene_start = i
                current_shot_type = analysis.shot_type

        # Add final scene
        if timestamps:
            scenes.append(
                SceneSegment(
                    start_time=timestamps[current_scene_start],
                    end_time=timestamps[-1],
                    duration=timestamps[-1] - timestamps[current_scene_start],
                    description=frame_analyses[current_scene_start].description,
                    key_frame_index=current_scene_start,
                )
            )

        return scenes

    async def _generate_shot_list(
        self,
        frame_analyses: List[FrameAnalysis],
        style: StyleExtractionResult,
        timestamps: List[float],
    ) -> List[ShotSuggestion]:
        """Generate shot list for video recreation."""
        from google.genai import types

        client = self._get_client()

        # Prepare frame analysis summary
        frame_summary = []
        for i, analysis in enumerate(frame_analyses):
            frame_summary.append({
                "index": i,
                "timestamp": timestamps[i] if i < len(timestamps) else 0,
                "description": analysis.description,
                "shot_type": analysis.shot_type,
                "camera_movement": analysis.camera_movement,
                "emotion": analysis.emotion,
            })

        prompt = self.SHOT_LIST_PROMPT.format(
            frame_analyses=json.dumps(frame_summary, indent=2)
        )

        # Add style context
        prompt += f"\n\nStyle to maintain: {style.style_prompt}"

        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self.config.model,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.5,
                ),
            )

            data = json.loads(response.text.strip())

            # Parse shot list
            if isinstance(data, list):
                shots = [ShotSuggestion.model_validate(shot) for shot in data]
            else:
                shots = []

            return shots

        except Exception as e:
            logger.warning(f"Shot list generation failed: {e}")
            return []

    def _select_moodboard_frames(
        self,
        frames: List[bytes],
        analyses: List[FrameAnalysis],
        num_frames: int = 5,
    ) -> List[str]:
        """Select best frames for moodboard (base64 encoded)."""
        if not frames:
            return []

        # Select frames with most descriptive analyses
        scored_indices = []
        for i, analysis in enumerate(analyses):
            score = (
                len(analysis.description)
                + len(analysis.objects) * 5
                + (10 if analysis.emotion else 0)
            )
            scored_indices.append((i, score))

        # Sort by score, take top N
        scored_indices.sort(key=lambda x: x[1], reverse=True)
        selected_indices = [idx for idx, _ in scored_indices[:num_frames]]

        # Encode selected frames
        moodboard = []
        for idx in sorted(selected_indices):  # Keep chronological order
            if idx < len(frames):
                b64 = base64.b64encode(frames[idx]).decode("utf-8")
                moodboard.append(b64)

        return moodboard


# =============================================================================
# Module-level convenience functions
# =============================================================================


_default_analyzer: Optional[ReferenceAnalyzer] = None


def get_reference_analyzer(api_key: Optional[str] = None) -> ReferenceAnalyzer:
    """Get or create the default ReferenceAnalyzer instance."""
    global _default_analyzer
    if api_key:
        return ReferenceAnalyzer(api_key=api_key)
    if _default_analyzer is None:
        _default_analyzer = ReferenceAnalyzer()
    return _default_analyzer


async def analyze_video_reference(
    video_bytes: bytes,
    analysis_depth: str = "detailed",
    api_key: Optional[str] = None,
) -> VideoReferenceAnalysis:
    """Convenience function for video reference analysis."""
    analyzer = get_reference_analyzer(api_key)
    return await analyzer.analyze_video_reference(video_bytes, analysis_depth)


async def analyze_image_reference(
    image_bytes: bytes,
    api_key: Optional[str] = None,
) -> ImageReferenceAnalysis:
    """Convenience function for image reference analysis."""
    analyzer = get_reference_analyzer(api_key)
    return await analyzer.analyze_image_reference(image_bytes)
