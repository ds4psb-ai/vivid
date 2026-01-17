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


@dataclass
class ReferenceAnalyzerConfig:
    """Configuration for reference analysis."""

    model: str = "gemini-2.5-pro"  # Pro for detailed analysis
    flash_model: str = "gemini-2.5-flash"  # Flash for quick frame analysis
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

    FRAME_ANALYSIS_PROMPT = """Analyze this video frame and extract:

1. description: Brief scene description (1-2 sentences)
2. objects: List of visible objects/elements
3. actions: Any actions or movements visible
4. characters: Description of any characters/people
5. camera_movement: Camera movement if detectable (static, pan, tilt, zoom, dolly, tracking)
6. shot_type: Shot type (extreme wide, wide, medium wide, medium, medium close-up, close-up, extreme close-up)
7. emotion: Emotional tone (exciting, tense, calm, sad, mysterious, etc.)

Return ONLY valid JSON with these fields."""

    SHOT_LIST_PROMPT = """Based on these frame analyses, create a shot list for recreating this video sequence.

Frame Analyses:
{frame_analyses}

For each distinct shot, provide:
1. shot_number: Sequential number
2. duration_seconds: Suggested duration (based on pacing)
3. description: What happens in this shot
4. camera_setup: Camera angle, movement, and framing instructions
5. prompt: An AI video generation prompt (100-150 words) that would recreate this shot
6. reference_frame_index: Which frame this shot is based on

Return a JSON array of shots. Focus on creating prompts that capture:
- The exact visual style
- Camera movement and framing
- Subject actions and emotions
- Lighting and atmosphere"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[ReferenceAnalyzerConfig] = None,
        style_extractor: Optional[StyleExtractor] = None,
    ):
        """Initialize ReferenceAnalyzer.

        Args:
            api_key: Optional API key
            config: Optional configuration
            style_extractor: Optional StyleExtractor instance
        """
        self._api_key = api_key or settings.GEMINI_API_KEY
        self.config = config or ReferenceAnalyzerConfig()
        self._style_extractor = style_extractor
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

        return VideoReferenceAnalysis(
            total_duration=total_duration,
            frame_count=len(frames),
            fps=fps,
            frames=frame_analyses,
            scenes=scenes,
            style=style,
            suggested_shots=suggested_shots,
            moodboard_frames=moodboard_frames,
            analysis_depth=analysis_depth,
            confidence=confidence,
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

        analysis_prompt = """Analyze this reference image in detail:

1. description: Detailed description of the scene (3-5 sentences)
2. objects: All visible objects and elements
3. composition_analysis: How the image is composed (rule of thirds, leading lines, etc.)
4. recreation_prompt: A detailed prompt (150-200 words) to recreate this image with AI,
   including style, lighting, composition, mood, and all visual elements.
5. similar_references: Suggest 3-5 similar reference styles or artists

Return ONLY valid JSON."""

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

        return ImageReferenceAnalysis(
            description=data.get("description", ""),
            style=style,
            objects=data.get("objects", []),
            composition_analysis=data.get("composition_analysis", ""),
            recreation_prompt=data.get("recreation_prompt", ""),
            similar_references=data.get("similar_references", []),
        )

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
