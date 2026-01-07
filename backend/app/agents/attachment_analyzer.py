"""Attachment Analyzer for Workflow Inference.

Analyzes file attachments to determine the optimal workflow starting point
and dimension sequence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.logging_config import get_logger

logger = get_logger("attachment_analyzer")


@dataclass
class WorkflowSuggestion:
    """Suggested workflow based on attachment analysis."""
    start_dimension: str
    dimensions: List[str]
    reason: str
    attachment_type: Optional[str] = None


class AttachmentAnalyzer:
    """Analyze attachments and infer appropriate workflow."""

    # MIME type → (start_dimension, workflow_dimensions)
    MIME_TO_DIMENSION: Dict[str, Tuple[str, List[str]]] = {
        # Video → 4D 분석 먼저 (레퍼런스 분석 후 프롬프트 생성)
        "video/mp4": ("4D", ["4D", "1D", "2D", "3D"]),
        "video/quicktime": ("4D", ["4D", "1D", "2D", "3D"]),
        "video/webm": ("4D", ["4D", "1D", "2D", "3D"]),
        "video/x-msvideo": ("4D", ["4D", "1D", "2D", "3D"]),
        "video/mpeg": ("4D", ["4D", "1D", "2D", "3D"]),

        # Image → 4D 스타일 참조 분석
        "image/jpeg": ("4D", ["4D", "1D", "2D", "3D"]),
        "image/png": ("4D", ["4D", "1D", "2D", "3D"]),
        "image/webp": ("4D", ["4D", "1D", "2D", "3D"]),
        "image/gif": ("4D", ["4D", "1D", "2D", "3D"]),
        "image/heic": ("4D", ["4D", "1D", "2D", "3D"]),

        # Audio → 1D 프롬프트 (사운드 기반 컨셉)
        "audio/mpeg": ("1D", ["1D", "2D", "3D"]),
        "audio/wav": ("1D", ["1D", "2D", "3D"]),
        "audio/mp3": ("1D", ["1D", "2D", "3D"]),
        "audio/ogg": ("1D", ["1D", "2D", "3D"]),

        # PDF/Document → AI 분석 먼저 (페르소나/컨셉 추출)
        "application/pdf": ("AI", ["AI", "1D", "2D", "3D"]),
        "text/plain": ("1D", ["1D", "2D", "3D"]),
    }

    # Default workflow when no attachments
    DEFAULT_WORKFLOW = ["1D", "2D", "3D"]
    DEFAULT_START = "1D"

    @classmethod
    def analyze(cls, attachments: Optional[List[dict]]) -> WorkflowSuggestion:
        """Analyze attachments and return workflow suggestion.

        Args:
            attachments: List of attachment dicts with 'mime_type', 'file_uri', etc.

        Returns:
            WorkflowSuggestion with recommended dimensions
        """
        if not attachments:
            return WorkflowSuggestion(
                start_dimension=cls.DEFAULT_START,
                dimensions=cls.DEFAULT_WORKFLOW.copy(),
                reason="첨부파일 없음 - 기본 워크플로우",
            )

        # Primary attachment determines workflow
        primary = attachments[0]
        mime_type = primary.get("mime_type", "") or ""
        file_name = primary.get("name", "") or primary.get("file_name", "") or ""

        logger.info(
            "Analyzing attachment",
            extra={"mime_type": mime_type, "file_name": file_name}
        )

        # Exact MIME type match
        if mime_type in cls.MIME_TO_DIMENSION:
            start, dims = cls.MIME_TO_DIMENSION[mime_type]
            return WorkflowSuggestion(
                start_dimension=start,
                dimensions=dims.copy(),
                reason=f"{mime_type} 파일 → {start} 분석부터 시작",
                attachment_type=mime_type,
            )

        # Partial match by media type prefix
        media_type = mime_type.split("/")[0] if "/" in mime_type else ""

        if media_type == "video":
            return WorkflowSuggestion(
                start_dimension="4D",
                dimensions=["4D", "1D", "2D", "3D"],
                reason=f"비디오 파일({mime_type}) → 4D 레퍼런스 분석",
                attachment_type="video",
            )
        elif media_type == "image":
            return WorkflowSuggestion(
                start_dimension="4D",
                dimensions=["4D", "1D", "2D", "3D"],
                reason=f"이미지 파일({mime_type}) → 4D 스타일 분석",
                attachment_type="image",
            )
        elif media_type == "audio":
            return WorkflowSuggestion(
                start_dimension="1D",
                dimensions=["1D", "2D", "3D"],
                reason=f"오디오 파일({mime_type}) → 1D 컨셉 생성",
                attachment_type="audio",
            )

        # Fallback: check file extension
        if file_name:
            ext = file_name.lower().split(".")[-1] if "." in file_name else ""

            video_exts = {"mp4", "mov", "webm", "avi", "mkv", "m4v"}
            image_exts = {"jpg", "jpeg", "png", "webp", "gif", "heic", "bmp"}
            audio_exts = {"mp3", "wav", "ogg", "m4a", "aac", "flac"}

            if ext in video_exts:
                return WorkflowSuggestion(
                    start_dimension="4D",
                    dimensions=["4D", "1D", "2D", "3D"],
                    reason=f".{ext} 파일 → 4D 레퍼런스 분석",
                    attachment_type="video",
                )
            elif ext in image_exts:
                return WorkflowSuggestion(
                    start_dimension="4D",
                    dimensions=["4D", "1D", "2D", "3D"],
                    reason=f".{ext} 파일 → 4D 스타일 분석",
                    attachment_type="image",
                )
            elif ext in audio_exts:
                return WorkflowSuggestion(
                    start_dimension="1D",
                    dimensions=["1D", "2D", "3D"],
                    reason=f".{ext} 파일 → 1D 컨셉 생성",
                    attachment_type="audio",
                )

        # Unknown file type - default workflow
        logger.warning(
            "Unknown attachment type, using default workflow",
            extra={"mime_type": mime_type, "file_name": file_name}
        )
        return WorkflowSuggestion(
            start_dimension=cls.DEFAULT_START,
            dimensions=cls.DEFAULT_WORKFLOW.copy(),
            reason=f"알 수 없는 파일 타입({mime_type}) - 기본 워크플로우",
        )

    @classmethod
    def enhance_workflow_for_full_pipeline(
        cls,
        base_suggestion: WorkflowSuggestion,
        include_quality_check: bool = True,
        include_video_generation: bool = True,
    ) -> WorkflowSuggestion:
        """Enhance base workflow with QC and VEO for full pipeline.

        Args:
            base_suggestion: Base workflow suggestion
            include_quality_check: Add QC after main workflow
            include_video_generation: Add VEO at the end

        Returns:
            Enhanced WorkflowSuggestion
        """
        enhanced_dims = base_suggestion.dimensions.copy()

        # Add AD (Aesthetic Director) at the beginning if not present
        if "AD" not in enhanced_dims:
            # Insert after reference analysis (4D) if present, otherwise at start
            if "4D" in enhanced_dims:
                idx = enhanced_dims.index("4D") + 1
                enhanced_dims.insert(idx, "AD")
            else:
                enhanced_dims.insert(0, "AD")

        # Add QC after main creative dimensions
        if include_quality_check and "QC" not in enhanced_dims:
            # Insert before VEO if we're adding it, otherwise at end
            enhanced_dims.append("QC")

        # Add VEO at the end
        if include_video_generation and "VEO" not in enhanced_dims:
            enhanced_dims.append("VEO")

        return WorkflowSuggestion(
            start_dimension=enhanced_dims[0],
            dimensions=enhanced_dims,
            reason=f"전체 파이프라인: {' → '.join(enhanced_dims)}",
            attachment_type=base_suggestion.attachment_type,
        )
