"""Transactional Outbox Model.

Implements the Transactional Outbox pattern for reliable event publishing
to external systems (Qdrant) with at-least-once delivery guarantee.

Pattern Benefits:
- Atomic writes: Event + DB change in single transaction
- Eventual consistency: Async sync to Qdrant
- Retry with backoff: Handles transient failures
- Audit trail: All events are persisted

Usage:
    from app.models_outbox import Outbox, OutboxStatus

    # Write event in transaction
    outbox_entry = Outbox(
        event_type="dna_lab_result",
        payload={"trace_id": "...", "vpe": {...}},
    )
    db.add(outbox_entry)
    await db.commit()

    # Publisher polls and syncs
    await outbox_publisher.poll_and_publish(db)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, DateTime, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# =============================================================================
# Enums
# =============================================================================

class OutboxStatus(str, Enum):
    """Outbox entry status."""
    PENDING = "pending"         # Awaiting publish
    PUBLISHED = "published"     # Successfully published
    FAILED = "failed"           # Failed after max retries
    SKIPPED = "skipped"         # Intentionally skipped


# =============================================================================
# Outbox Model
# =============================================================================

class Outbox(Base):
    """Transactional Outbox for reliable event publishing.

    Stores events for async publishing to external systems (Qdrant).
    Publisher polls this table and publishes pending events.

    Attributes:
        id: Unique event identifier
        event_type: Type of event (e.g., "dna_lab_result", "vector_update")
        aggregate_type: Aggregate type (optional, for filtering)
        aggregate_id: Aggregate identifier (optional)
        payload: Event data as JSONB
        status: Current status (pending, published, failed, skipped)
        retry_count: Number of publish attempts
        max_retries: Maximum retry attempts before marking failed
        last_error: Most recent error message
        created_at: When the event was created
        published_at: When the event was successfully published
        scheduled_at: When to attempt next publish (for delayed events)
    """
    __tablename__ = "outbox"
    __table_args__ = (
        Index("ix_outbox_status_created", "status", "created_at"),
        Index("ix_outbox_scheduled", "scheduled_at"),
        Index("ix_outbox_aggregate", "aggregate_type", "aggregate_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Event metadata
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    aggregate_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    aggregate_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )

    # Event data
    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        default=OutboxStatus.PENDING.value,
        index=True,
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )
    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
    )
    last_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        default=datetime.utcnow,
    )

    def mark_published(self) -> None:
        """Mark as successfully published."""
        self.status = OutboxStatus.PUBLISHED.value
        self.published_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """Mark as failed with error message."""
        self.retry_count += 1
        self.last_error = error[:1000] if error else None

        if self.retry_count >= self.max_retries:
            self.status = OutboxStatus.FAILED.value
        # else status remains pending for retry

    def should_retry(self) -> bool:
        """Check if this entry should be retried."""
        return (
            self.status == OutboxStatus.PENDING.value and
            self.retry_count < self.max_retries
        )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "Outbox",
    "OutboxStatus",
]
