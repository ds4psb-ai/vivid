"""Pipeline Result Model.

SQLAlchemy model for pipeline execution feedback and analysis.

Usage:
    from app.models_pipeline import PipelineResult
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PipelineResult(Base):
    """Pipeline execution result with feedback tracking.

    Stores results, errors, and user feedback for continuous improvement.

    Attributes:
        id: Unique result identifier
        trace_id: Pipeline trace ID for correlation
        user_id: User who ran the pipeline
        pipeline_type: Type of pipeline (e.g., "dna_lab")
        steps_requested: Steps that were requested
        steps_completed: Steps that completed successfully
        dna_result: Full result data as JSONB
        success: Overall success status
        partial_success: Whether some steps succeeded
        failure_step: Step that failed (if any)
        failure_reason: Reason for failure
        error_category: Error category (timeout, validation, api_error, etc.)
        user_rating: User rating 1-5
        user_feedback: Free-text feedback
        feedback_tags: Feedback category tags
        processing_time_ms: Total processing time
        credits_used: Credits consumed
        credits_refunded: Credits refunded
        analyzed: Whether this result has been analyzed
        pattern_detected: Pattern detected during analysis
        improvement_applied: Whether improvement was applied
    """
    __tablename__ = "pipeline_results"
    __table_args__ = (
        Index("ix_pipeline_results_failure", "success", "failure_step", "error_category"),
        Index("ix_pipeline_results_rating", "user_rating", "created_at"),
        Index("ix_pipeline_results_analyzed", "analyzed", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    trace_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
        index=True,
    )

    # Pipeline config
    pipeline_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="dna_lab",
    )
    steps_requested: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
    )
    steps_completed: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
    )

    # Result data
    dna_result: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    partial_success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Error tracking
    failure_step: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    error_category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # User feedback
    user_rating: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    user_feedback: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    feedback_tags: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    # Performance metrics
    processing_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    credits_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    credits_refunded: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Analysis flags
    analyzed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    pattern_detected: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    improvement_applied: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    feedback_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "PipelineResult",
]
