"""Style Extraction Service for Reference Analysis (2026 Expert Workflow).

Extracts reusable visual style information from reference images using
Gemini 3 multimodal capabilities and color analysis.

Features:
- Style tag extraction (anime, photorealistic, etc.)
- Reusable style prompt generation
- Color palette extraction (K-Means clustering)
- Lighting, composition, mood analysis
- Reference artist matching

Based on expert workflow: "스타일 프롬프트라고 따로 둬요... 일관성을 위해서"
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Models
# =============================================================================


class StyleExtractionResult(BaseModel):
    """Result of style extraction from a reference image."""

    style_tags: List[str] = Field(
        default_factory=list,
        description="Style descriptors (anime, photorealistic, cel-shading, etc.)",
    )
    style_prompt: str = Field(
        default="",
        description="Reusable prompt that captures this visual style (50-100 words)",
    )
    color_palette: List[str] = Field(
        default_factory=list,
        description="Dominant colors as hex codes (#FF5733, etc.)",
    )
    lighting: str = Field(
        default="natural",
        description="Lighting type (dramatic, soft, neon, natural, etc.)",
    )
    composition: str = Field(
        default="balanced",
        description="Composition style (centered, rule-of-thirds, symmetrical)",
    )
    mood: str = Field(
        default="neutral",
        description="Overall mood/atmosphere (energetic, melancholic, mysterious)",
    )
    camera_angle: Optional[str] = Field(
        default=None,
        description="Camera angle if applicable (low-angle, eye-level, bird's-eye)",
    )
    reference_artists: List[str] = Field(
        default_factory=list,
        description="Similar known artists or visual styles",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of the extraction",
    )


@dataclass
class StyleExtractionConfig:
    """Configuration for style extraction."""

    model: str = "gemini-3-flash-preview"  # 2026 Gemini 3 Flash (Jan 2026)
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout_seconds: float = 30.0
    extract_color_palette: bool = True
    num_palette_colors: int = 7


# =============================================================================
# Errors
# =============================================================================


class StyleExtractionError(Exception):
    """Base error for style extraction."""

    pass


class StyleExtractionTimeoutError(StyleExtractionError):
    """Raised when extraction times out."""

    pass


class StyleExtractionAPIError(StyleExtractionError):
    """Raised when API call fails."""

    pass


# =============================================================================
# Style Extractor Service
# =============================================================================


class StyleExtractor:
    """Extract reusable style from reference images (2026 Expert Workflow).

    Uses Gemini 3 multimodal for style analysis and K-Means clustering
    for accurate color palette extraction.
    """

    # Expert-crafted extraction prompt (2026 best practices)
    EXTRACTION_PROMPT = """Analyze this reference image and extract detailed style information.

Return a JSON object with:
1. style_tags: List of style descriptors (anime, photorealistic, cel-shading, watercolor, etc.)
2. style_prompt: A reusable prompt (50-100 words) that captures this exact visual style.
   Focus on: rendering technique, color grading, line work, shading, texture, atmosphere.
   This should recreate the visual style consistently across different scenes.
3. color_palette: List of 5-7 dominant colors as hex codes
4. lighting: Type of lighting (dramatic, soft, neon, natural, high-key, low-key, etc.)
5. composition: Composition style (centered, rule-of-thirds, symmetrical, dynamic diagonal)
6. mood: Overall mood/atmosphere (energetic, melancholic, mysterious, serene, tense)
7. camera_angle: If applicable (low-angle, eye-level, bird's-eye, dutch-angle)
8. reference_artists: Similar known artists, directors, or visual styles this resembles
9. confidence: Your confidence in this analysis (0.0-1.0)

Example style_prompt format:
"Cinematic 35mm film aesthetic with heavy grain, desaturated teal and orange color grading,
soft diffused lighting with strong rim lights, shallow depth of field, atmospheric haze,
high contrast shadows with crushed blacks, vintage lens flare artifacts."

Return ONLY valid JSON, no markdown code blocks or explanations."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[StyleExtractionConfig] = None,
    ):
        """Initialize StyleExtractor.

        Args:
            api_key: Optional API key. Uses settings.GEMINI_API_KEY if not provided.
            config: Optional configuration. Uses defaults if not provided.
        """
        self._api_key = api_key or settings.GEMINI_API_KEY
        self.config = config or StyleExtractionConfig()
        self._client = None

    def _get_client(self):
        """Get or create the GenAI client (google-genai SDK 2026)."""
        if self._client is None:
            from google import genai

            if not self._api_key:
                raise StyleExtractionError(
                    "No API key available. Configure GEMINI_API_KEY."
                )
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def extract_style(
        self,
        image_bytes: bytes,
        additional_context: Optional[str] = None,
        mime_type: str = "image/jpeg",
    ) -> StyleExtractionResult:
        """Extract style from a reference image.

        Args:
            image_bytes: Raw image bytes
            additional_context: Optional context (e.g., "This is from a sci-fi film")
            mime_type: Image MIME type

        Returns:
            StyleExtractionResult with extracted style information

        Raises:
            StyleExtractionError: If extraction fails
            StyleExtractionTimeoutError: If extraction times out
        """
        from google.genai import types

        client = self._get_client()

        # Build prompt with optional context
        prompt = self.EXTRACTION_PROMPT
        if additional_context:
            prompt += f"\n\nAdditional context: {additional_context}"

        # Prepare image part
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type,
        )

        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                # Call Gemini with image and prompt
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        client.models.generate_content,
                        model=self.config.model,
                        contents=[image_part, prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.3,  # Lower for more consistent extraction
                        ),
                    ),
                    timeout=self.config.timeout_seconds,
                )

                # Parse response
                text = response.text.strip()
                result = self._parse_response(text)

                # Enhance with K-Means color extraction if enabled
                if self.config.extract_color_palette:
                    try:
                        kmeans_colors = self._extract_colors_kmeans(
                            image_bytes, self.config.num_palette_colors
                        )
                        if kmeans_colors:
                            # Merge AI colors with K-Means (prefer K-Means for accuracy)
                            result.color_palette = kmeans_colors
                    except Exception as e:
                        logger.warning(f"K-Means color extraction failed: {e}")

                logger.info(
                    f"Style extracted: {len(result.style_tags)} tags, "
                    f"confidence={result.confidence:.2f}"
                )
                return result

            except asyncio.TimeoutError:
                last_error = StyleExtractionTimeoutError(
                    f"Style extraction timed out after {self.config.timeout_seconds}s"
                )
            except json.JSONDecodeError as e:
                last_error = StyleExtractionError(f"Failed to parse response: {e}")
            except Exception as e:
                last_error = StyleExtractionAPIError(f"API error: {e}")

            # Exponential backoff
            if attempt < self.config.max_retries - 1:
                delay = self.config.retry_delay * (2**attempt)
                logger.warning(
                    f"Style extraction attempt {attempt + 1} failed: {last_error}. "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)

        raise last_error or StyleExtractionError("Style extraction failed")

    async def extract_from_video_frames(
        self,
        video_bytes: bytes,
        num_frames: int = 5,
    ) -> StyleExtractionResult:
        """Extract consistent style from video key frames.

        Analyzes multiple frames and merges results for consistency.

        Args:
            video_bytes: Raw video bytes
            num_frames: Number of key frames to analyze

        Returns:
            StyleExtractionResult with merged style from all frames
        """
        # Extract key frames
        frames = self._extract_key_frames(video_bytes, num_frames)

        if not frames:
            raise StyleExtractionError("No frames extracted from video")

        # Analyze each frame in parallel
        tasks = [
            self.extract_style(frame, additional_context="From video sequence")
            for frame in frames
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        valid_results = [r for r in results if isinstance(r, StyleExtractionResult)]

        if not valid_results:
            raise StyleExtractionError("All frame extractions failed")

        # Merge results
        return self._merge_style_results(valid_results)

    def _parse_response(self, text: str) -> StyleExtractionResult:
        """Parse Gemini response into StyleExtractionResult."""
        # Clean response (remove markdown if present)
        clean_text = text
        if text.startswith("```"):
            lines = text.split("\n")
            clean_text = "\n".join(
                lines[1:-1] if lines[-1].startswith("```") else lines[1:]
            )

        try:
            data = json.loads(clean_text)
            return StyleExtractionResult.model_validate(data)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"JSON parse failed, attempting fallback: {e}")
            return self._fallback_parse(text)

    def _fallback_parse(self, text: str) -> StyleExtractionResult:
        """Fallback parsing when JSON fails."""
        result = StyleExtractionResult()

        # Extract style tags from text
        if "style_tags" in text.lower() or "style" in text.lower():
            # Look for quoted strings after style_tags
            import re

            tags = re.findall(r'"([^"]+)"', text)
            if tags:
                result.style_tags = tags[:10]  # Limit to 10

        # Extract mood
        mood_keywords = [
            "energetic",
            "melancholic",
            "mysterious",
            "serene",
            "tense",
            "dramatic",
        ]
        for mood in mood_keywords:
            if mood.lower() in text.lower():
                result.mood = mood
                break

        result.confidence = 0.3  # Low confidence for fallback
        return result

    def _extract_colors_kmeans(
        self,
        image_bytes: bytes,
        n_colors: int = 7,
    ) -> List[str]:
        """Extract dominant colors using K-Means clustering.

        Args:
            image_bytes: Raw image bytes
            n_colors: Number of colors to extract

        Returns:
            List of hex color codes
        """
        try:
            import numpy as np
            from PIL import Image
            from sklearn.cluster import KMeans
        except ImportError:
            logger.warning("K-Means dependencies not available (PIL, sklearn)")
            return []

        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            image = image.convert("RGB")

            # Resize for faster processing
            image.thumbnail((200, 200))

            # Convert to numpy array
            pixels = np.array(image).reshape(-1, 3)

            # K-Means clustering
            kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
            kmeans.fit(pixels)

            # Get cluster centers (colors)
            colors = kmeans.cluster_centers_.astype(int)

            # Sort by cluster size (most dominant first)
            labels, counts = np.unique(kmeans.labels_, return_counts=True)
            sorted_indices = np.argsort(-counts)
            sorted_colors = colors[sorted_indices]

            # Convert to hex
            hex_colors = [
                f"#{r:02x}{g:02x}{b:02x}".upper()
                for r, g, b in sorted_colors
            ]

            return hex_colors

        except Exception as e:
            logger.warning(f"Color extraction error: {e}")
            return []

    def _extract_key_frames(
        self,
        video_bytes: bytes,
        num_frames: int = 5,
    ) -> List[bytes]:
        """Extract key frames from video using OpenCV.

        Args:
            video_bytes: Raw video bytes
            num_frames: Number of frames to extract

        Returns:
            List of frame bytes (JPEG encoded)
        """
        try:
            import cv2
        except ImportError:
            logger.warning("OpenCV not available for frame extraction")
            return []

        frames = []
        temp_path = None

        try:
            # Write to temp file for OpenCV
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                f.write(video_bytes)
                temp_path = f.name

            cap = cv2.VideoCapture(temp_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            if total_frames == 0:
                return []

            # Calculate frame intervals
            interval = max(1, total_frames // num_frames)

            for i in range(0, total_frames, interval):
                if len(frames) >= num_frames:
                    break

                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()

                if ret:
                    # Encode to JPEG bytes
                    _, buffer = cv2.imencode(".jpg", frame)
                    frames.append(buffer.tobytes())

            cap.release()

        except Exception as e:
            logger.warning(f"Frame extraction error: {e}")
        finally:
            if temp_path:
                import os

                try:
                    os.unlink(temp_path)
                except Exception:
                    pass

        return frames

    def _merge_style_results(
        self,
        results: List[StyleExtractionResult],
    ) -> StyleExtractionResult:
        """Merge multiple style extractions into a consistent result.

        Uses voting/consensus for categorical fields and averaging for numeric.
        """
        if not results:
            return StyleExtractionResult()

        if len(results) == 1:
            return results[0]

        # Find common style tags (appear in >50% of results)
        all_tags: List[str] = []
        for r in results:
            all_tags.extend(r.style_tags)
        tag_counts = Counter(all_tags)
        threshold = len(results) / 2
        common_tags = [tag for tag, count in tag_counts.items() if count > threshold]

        # Use first result as base
        base = results[0].model_copy()

        # Merge tags (common + unique from high-confidence results)
        if common_tags:
            base.style_tags = common_tags
        else:
            # If no common tags, use tags from highest confidence result
            best = max(results, key=lambda r: r.confidence)
            base.style_tags = best.style_tags

        # Use style_prompt from highest confidence result
        best = max(results, key=lambda r: r.confidence)
        base.style_prompt = best.style_prompt

        # Merge color palettes (take union, dedupe, limit to 7)
        all_colors = []
        for r in results:
            all_colors.extend(r.color_palette)
        # Remove near-duplicates and limit
        unique_colors = list(dict.fromkeys(all_colors))[:7]
        base.color_palette = unique_colors

        # Vote on categorical fields
        base.lighting = self._majority_vote([r.lighting for r in results])
        base.composition = self._majority_vote([r.composition for r in results])
        base.mood = self._majority_vote([r.mood for r in results])

        # Average confidence
        base.confidence = sum(r.confidence for r in results) / len(results)

        return base

    def _majority_vote(self, values: List[str]) -> str:
        """Return most common value from list."""
        if not values:
            return ""
        counter = Counter(values)
        return counter.most_common(1)[0][0]


# =============================================================================
# Module-level convenience functions
# =============================================================================


_default_extractor: Optional[StyleExtractor] = None


def get_style_extractor(api_key: Optional[str] = None) -> StyleExtractor:
    """Get or create the default StyleExtractor instance."""
    global _default_extractor
    if api_key:
        return StyleExtractor(api_key=api_key)
    if _default_extractor is None:
        _default_extractor = StyleExtractor()
    return _default_extractor


async def extract_style(
    image_bytes: bytes,
    additional_context: Optional[str] = None,
    api_key: Optional[str] = None,
) -> StyleExtractionResult:
    """Convenience function for style extraction.

    Args:
        image_bytes: Raw image bytes
        additional_context: Optional context
        api_key: Optional API key override

    Returns:
        StyleExtractionResult with extracted style information
    """
    extractor = get_style_extractor(api_key)
    return await extractor.extract_style(image_bytes, additional_context)
