"""AI Services Package.

Contains AI-powered services for reference analysis, style extraction,
and video frame processing. Uses Google GenAI SDK (2026).
"""

from app.services.ai.style_extractor import (
    StyleExtractor,
    StyleExtractionResult,
    StyleExtractionError,
    get_style_extractor,
    extract_style,
)
from app.services.ai.reference_analyzer import (
    ReferenceAnalyzer,
    VideoReferenceAnalysis,
    ImageReferenceAnalysis,
    FrameAnalysis,
    ShotSuggestion,
    SceneSegment,
    ReferenceAnalysisError,
    get_reference_analyzer,
    analyze_video_reference,
    analyze_image_reference,
)

__all__ = [
    # Style Extractor
    "StyleExtractor",
    "StyleExtractionResult",
    "StyleExtractionError",
    "get_style_extractor",
    "extract_style",
    # Reference Analyzer
    "ReferenceAnalyzer",
    "VideoReferenceAnalysis",
    "ImageReferenceAnalysis",
    "FrameAnalysis",
    "ShotSuggestion",
    "SceneSegment",
    "ReferenceAnalysisError",
    "get_reference_analyzer",
    "analyze_video_reference",
    "analyze_image_reference",
]
