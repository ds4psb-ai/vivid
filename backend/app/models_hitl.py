"""HITL (Human-in-the-Loop) Model.

SQLAlchemy model for HITL review workflow items.

Usage:
    from app.models_hitl import HITLReviewItem, HITLStatus, HITLDecision
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# =============================================================================
# Enums
# =============================================================================

class HITLStatus(str, Enum):
    """HITL review item status."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class HITLDecision(str, Enum):
    """HITL decision types."""
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"


class HITLSeverity(str, Enum):
    """HITL severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HITLReviewType(str, Enum):
    """HITL review types."""
    VECTOR_DRIFT = "vector_drift"
    QC_FAILURE = "qc_failure"
    PROMPT_PATTERN = "prompt_pattern"
    CREDIT_ANOMALY = "credit_anomaly"
    CONTENT_FLAG = "content_flag"


# =============================================================================
# HITL Review Item Model
# =============================================================================

class HITLReviewItem(Base):
    """Human-in-the-Loop review item.

    Implements 2026 HITL best practices:
    - Risk-based oversight (severity levels)
    - Async review channels
    - Human feedback as training data
    - Structured review queues with tracing

    Attributes:
        id: Unique item identifier
        review_type: Type of review (vector_drift, qc_failure, etc.)
        severity: Severity level (low, medium, high, critical)
        ip_id: Associated IP identifier (optional)
        trace_id: Pipeline trace ID for correlation
        payload: Review data as JSONB
        suggested_action: System-suggested action
        status: Workflow status
        assigned_to: Admin user assigned to review
        decision: Final decision
        decision_by: Admin who made the decision
        decision_at: When decision was made
        decision_notes: Notes about the decision
        auto_applied: Whether action was auto-applied
        applied_at: When action was applied
        apply_result: Result of applying the action
        created_at: Item creation time
        expires_at: Expiration time (auto-reject if not reviewed)
    """
    __tablename__ = "hitl_review_items"
    __table_args__ = (
        Index("ix_hitl_status_severity", "status", "severity"),
        Index("ix_hitl_review_type", "review_type"),
        Index("ix_hitl_assigned_to", "assigned_to", "status"),
        Index("ix_hitl_expires_at", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Review type and severity
    review_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=HITLSeverity.MEDIUM.value,
    )

    # Context
    ip_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    trace_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    # Review data
    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    suggested_action: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Workflow
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=HITLStatus.PENDING.value,
    )
    assigned_to: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )

    # Decision
    decision: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    decision_by: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    decision_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    decision_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Auto-apply tracking
    auto_applied: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    applied_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    apply_result: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "HITLReviewItem",
    "HITLStatus",
    "HITLDecision",
    "HITLSeverity",
    "HITLReviewType",
]
