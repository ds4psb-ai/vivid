"""Drift Detection Schemas.

Pydantic models for Logic Vector versioning and drift detection.

Usage:
    from app.schemas.drift_detection import (
        DriftDetectionResult,
        LogicVectorVersionCreate,
        DriftReason,
    )
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class DriftReason(str, Enum):
    """Reasons for Logic Vector drift."""
    SEASON_CHANGE = "season_change"       # New season/content release
    DIRECTOR_CHANGE = "director_change"   # Change in creative direction
    PLATFORM_SHIFT = "platform_shift"     # Target platform change (YT→TikTok)
    STYLE_EVOLUTION = "style_evolution"   # Natural style evolution
    CONTENT_EXPANSION = "content_expansion"  # New content types
    MANUAL_UPDATE = "manual_update"       # Admin-initiated update
    AUTO_RETRAIN = "auto_retrain"         # Automatic retraining trigger


class DriftAction(str, Enum):
    """Recommended actions for drift detection."""
    NO_CHANGE = "no_change"               # No significant drift
    REQUIRE_HUMAN_REVIEW = "require_human_review"  # Needs admin approval
    AUTO_UPGRADE = "auto_upgrade"         # Safe to auto-upgrade


# =============================================================================
# Drift Detection Models
# =============================================================================

class DriftMetrics(BaseModel):
    """Drift measurement metrics."""
    cosine_distance: float = Field(
        ge=0.0,
        le=2.0,
        description="Cosine distance between vectors (0=identical, 2=opposite)"
    )
    ks_statistic: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Kolmogorov-Smirnov test statistic"
    )
    ks_pvalue: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="KS test p-value (< 0.05 indicates significant difference)"
    )
    cadence_drift: Optional[float] = Field(
        default=None,
        description="Drift in cadence/timing patterns"
    )
    camera_grammar_drift: Optional[float] = Field(
        default=None,
        description="Drift in camera movement distribution"
    )
    color_drift: Optional[float] = Field(
        default=None,
        description="Drift in color palette"
    )


class DriftDetectionResult(BaseModel):
    """Result of drift detection analysis."""
    action: DriftAction = Field(
        description="Recommended action based on drift analysis"
    )
    current_version: Optional[int] = Field(
        default=None,
        description="Current active version number"
    )
    proposed_version: Optional[int] = Field(
        default=None,
        description="Proposed new version number"
    )
    drift_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall drift score (0=no drift, 1=complete drift)"
    )
    metrics: Optional[DriftMetrics] = Field(
        default=None,
        description="Detailed drift metrics"
    )
    reason: Optional[DriftReason] = Field(
        default=None,
        description="Inferred reason for drift"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in the drift assessment"
    )
    details: str = Field(
        default="",
        description="Human-readable explanation"
    )


# =============================================================================
# Logic Vector Version Models
# =============================================================================

class LogicVectorVersionCreate(BaseModel):
    """Request to create a new Logic Vector version."""
    ip_id: str = Field(
        ...,
        description="IP identifier"
    )
    source_videos: List[str] = Field(
        default_factory=list,
        description="Source video URIs used for this version"
    )
    logic_vector: Dict[str, Any] = Field(
        ...,
        description="Logic Vector data"
    )
    embedding: Optional[List[float]] = Field(
        default=None,
        description="384-dim embedding vector"
    )
    drift_reason: Optional[DriftReason] = Field(
        default=None,
        description="Reason for creating new version"
    )
    drift_score_from_prev: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Drift score from previous version"
    )
    created_by: Optional[str] = Field(
        default=None,
        description="User ID who created this version"
    )


class LogicVectorVersionResponse(BaseModel):
    """Response with Logic Vector version details."""
    id: str
    ip_id: str
    version_number: int
    logic_vector: Dict[str, Any]
    source_videos: List[str]
    is_active: bool
    valid_from: datetime
    valid_until: Optional[datetime]
    drift_score_from_prev: Optional[float]
    drift_reason: Optional[str]
    created_at: datetime
    created_by: Optional[str]


class LogicVectorVersionHistory(BaseModel):
    """History of Logic Vector versions for an IP."""
    ip_id: str
    current_version: int
    versions: List[LogicVectorVersionResponse]
    total_versions: int


# =============================================================================
# HITL Review Models (for drift-triggered reviews)
# =============================================================================

class DriftReviewPayload(BaseModel):
    """Payload for drift-triggered HITL review."""
    ip_id: str
    current_version: int
    proposed_version: int
    drift_result: DriftDetectionResult
    new_logic_vector: Dict[str, Any]
    source_videos: List[str]
    comparison_summary: str = Field(
        default="",
        description="Human-readable comparison summary"
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "DriftReason",
    "DriftAction",
    # Drift detection
    "DriftMetrics",
    "DriftDetectionResult",
    # Version management
    "LogicVectorVersionCreate",
    "LogicVectorVersionResponse",
    "LogicVectorVersionHistory",
    # HITL
    "DriftReviewPayload",
]
