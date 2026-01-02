"""Tool Review and Approval Models.

Models for managing tool/fork review workflow:
- ToolReview: Individual review record
- ReviewChecklist: Automated check results
- TierPromotion: Track tier advancement
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, String, Text, Integer, Boolean, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# =============================================================================
# Enums
# =============================================================================

class ReviewStatus(str, Enum):
    """Review status."""
    PENDING = "pending"           # Waiting for review
    IN_PROGRESS = "in_progress"   # Reviewer assigned
    APPROVED = "approved"         # Passed review
    REJECTED = "rejected"         # Failed review
    CHANGES_REQUESTED = "changes_requested"  # Needs modifications


class ReviewType(str, Enum):
    """Type of review."""
    FORK_SUBMISSION = "fork_submission"    # New fork submitted
    TIER_PROMOTION = "tier_promotion"      # Tier upgrade request
    CODE_UPDATE = "code_update"            # Version update
    SAFETY_AUDIT = "safety_audit"          # Security review
    QUALITY_CHECK = "quality_check"        # Quality assessment


class CheckCategory(str, Enum):
    """Automated check categories."""
    SAFETY = "safety"           # Security/safety checks
    QUALITY = "quality"         # Code quality
    TESTING = "testing"         # Test pass rate
    PERFORMANCE = "performance" # Latency/resource usage
    SYBIL = "sybil"            # Sybil detection


# =============================================================================
# Tool Review
# =============================================================================

class ToolReview(Base):
    """Review record for tool/fork submissions.
    
    Tracks the review process from submission to decision.
    """
    __tablename__ = "tool_reviews"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    # What's being reviewed
    tool_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tool_manifests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tool_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Review type and status
    review_type: Mapped[str] = mapped_column(
        String(30),
        default=ReviewType.FORK_SUBMISSION.value,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=ReviewStatus.PENDING.value,
        index=True,
    )
    priority: Mapped[int] = mapped_column(Integer, default=0)  # Higher = more urgent
    
    # Submitter
    submitted_by: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    submission_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Reviewer
    assigned_to: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Decision
    decision_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    decision_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    decision_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Automated checks
    auto_checks_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_checks_score: Mapped[float] = mapped_column(Float, default=0.0)
    check_results: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    __table_args__ = (
        Index("ix_tool_review_status_priority", "status", "priority"),
        Index("ix_tool_review_type_status", "review_type", "status"),
    )


# =============================================================================
# Review Checklist
# =============================================================================

class ReviewCheckResult(Base):
    """Individual check result within a review.
    
    Tracks automated and manual check outcomes.
    """
    __tablename__ = "review_check_results"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    review_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tool_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Check info
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    check_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Result
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100
    weight: Mapped[float] = mapped_column(Float, default=1.0)  # Importance
    
    # Details
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Is this automated or manual?
    is_automated: Mapped[bool] = mapped_column(Boolean, default=True)
    checked_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# =============================================================================
# Tier Promotion
# =============================================================================

class TierPromotion(Base):
    """Track tier advancement history.
    
    Records when tools are promoted/demoted between tiers.
    """
    __tablename__ = "tier_promotions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    tool_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tool_manifests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Tier change
    from_tier: Mapped[str] = mapped_column(String(20), nullable=False)
    to_tier: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Reason
    promotion_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # e.g. "automatic", "manual", "demotion", "initial"
    
    # Decision
    decided_by: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metrics at time of promotion
    metrics_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict)
    # e.g. {"usage_count": 1000, "rating": 4.5, "test_pass_rate": 0.98}
    
    # Associated review (if any)
    review_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tool_reviews.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
