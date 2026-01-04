"""Dead Letter Queue Models.

Stores failed operations (refunds, settlements, payouts) for manual reconciliation.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, DateTime, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DLQEventType(str, Enum):
    """Types of events that can end up in DLQ."""
    REFUND_FAILED = "refund_failed"
    SETTLEMENT_FAILED = "settlement_failed"
    PAYOUT_FAILED = "payout_failed"
    CREDIT_GRANT_FAILED = "credit_grant_failed"


class DLQStatus(str, Enum):
    """Status of DLQ item."""
    PENDING = "pending"           # Awaiting manual review
    PROCESSING = "processing"     # Currently being processed
    RESOLVED = "resolved"         # Successfully resolved
    SKIPPED = "skipped"           # Manually marked as skip
    FAILED = "failed"             # Retry failed


class DeadLetterQueueItem(Base):
    """Dead Letter Queue for failed operations."""
    __tablename__ = "dead_letter_queue"
    __table_args__ = (
        Index("ix_dlq_status", "status"),
        Index("ix_dlq_event_type", "event_type"),
        Index("ix_dlq_user_id", "user_id"),
        Index("ix_dlq_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Event identification
    event_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default=DLQStatus.PENDING.value)
    
    # User context
    user_id: Mapped[str] = mapped_column(String(255))
    
    # Operation context
    operation_type: Mapped[str] = mapped_column(String(100))  # e.g., "prompt_generate", "storyboard_create"
    amount: Mapped[int] = mapped_column(Integer, default=0)   # Credits amount involved
    
    # Error details
    error_message: Mapped[str] = mapped_column(Text)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Original context (JSON)
    original_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Resolution tracking
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    last_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Resolution details
    resolved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Additional utility column for correlation
# Can link to settlement_id, run_id, etc.
# original_payload should contain {"correlation_id": "...", "correlation_type": "..."}
