"""Settlement Transaction Models.

Complete database models for production-level revenue settlement:
- SettlementTransaction: Main settlement record
- SettlementPayout: Individual recipient payouts
- SettlementDispute: Dispute handling
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    ForeignKey,
    Index,
    String,
    Text,
    Float,
    Integer,
    Boolean,
    DateTime,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# =============================================================================
# Enums
# =============================================================================

class SettlementStatus(str, Enum):
    """Settlement transaction status."""
    PENDING = "pending"           # Created, not yet processed
    PROCESSING = "processing"     # Currently being processed
    COMPLETED = "completed"       # Successfully completed
    FAILED = "failed"            # Processing failed
    CANCELLED = "cancelled"       # Cancelled before processing
    DISPUTED = "disputed"         # Under dispute review
    REVERSED = "reversed"         # Rolled back after completion


class PayoutStatus(str, Enum):
    """Individual payout status."""
    PENDING = "pending"           # Waiting for settlement
    CREDITED = "credited"         # Credits added to user
    FAILED = "failed"            # Failed to credit
    REVERSED = "reversed"         # Rolled back


class ShareType(str, Enum):
    """Type of revenue share."""
    OWNER = "owner"               # Current tool owner
    ANCESTOR = "ancestor"         # Parent tool creator(s)
    BONUS = "bonus"              # Platform bonus
    REFERRAL = "referral"         # Referral commission


class DisputeStatus(str, Enum):
    """Dispute status."""
    OPEN = "open"                 # Newly created
    INVESTIGATING = "investigating"  # Under review
    RESOLVED = "resolved"         # Resolved (accepted)
    REJECTED = "rejected"         # Resolved (rejected)


# =============================================================================
# Settlement Transaction
# =============================================================================

class SettlementTransaction(Base):
    """Main settlement transaction record.
    
    One settlement per tool run. Tracks the overall distribution
    of credits from a tool execution.
    """
    __tablename__ = "settlement_transactions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    # References
    tool_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), 
        ForeignKey("tool_run_events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One settlement per run
        index=True,
    )
    tool_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tool_manifests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tool_key: Mapped[str] = mapped_column(String(64), nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20), 
        default=SettlementStatus.PENDING.value,
        index=True,
    )
    
    # Amounts (all in credits)
    total_credits: Mapped[int] = mapped_column(Integer, nullable=False)
    platform_fee: Mapped[int] = mapped_column(Integer, nullable=False)
    creator_pool: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Tool context at time of settlement
    lineage_depth: Mapped[int] = mapped_column(Integer, default=0)
    attribution_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # User context
    payer_user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Audit
    processed_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Relationships
    payouts: Mapped[list["SettlementPayout"]] = relationship(
        "SettlementPayout", back_populates="settlement", cascade="all, delete-orphan"
    )
    disputes: Mapped[list["SettlementDispute"]] = relationship(
        "SettlementDispute", back_populates="settlement"
    )

    __table_args__ = (
        Index("ix_settlement_status_created", "status", "created_at"),
    )


# =============================================================================
# Settlement Payout
# =============================================================================

class SettlementPayout(Base):
    """Individual recipient payout record.
    
    One payout per recipient per settlement. Tracks the actual
    credit distribution to each participant.
    """
    __tablename__ = "settlement_payouts"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    # Settlement reference
    settlement_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("settlement_transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Recipient
    recipient_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    recipient_tool_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    recipient_tool_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Amount
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    share_type: Mapped[str] = mapped_column(String(20), nullable=False)
    share_rate: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 - 1.0
    
    # Lineage position (0 = current tool owner, 1+ = ancestors)
    lineage_position: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=PayoutStatus.PENDING.value,
        index=True,
    )
    
    # Credit ledger reference
    ledger_entry_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    credited_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationship
    settlement: Mapped["SettlementTransaction"] = relationship(
        "SettlementTransaction", back_populates="payouts"
    )


# =============================================================================
# Settlement Dispute
# =============================================================================

class SettlementDispute(Base):
    """Dispute record for settlement challenges.
    
    Allows users to dispute revenue distribution if they
    believe it's incorrect.
    """
    __tablename__ = "settlement_disputes"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    # Settlement reference
    settlement_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("settlement_transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Complainant
    complainant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    # Dispute details
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    expected_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=DisputeStatus.OPEN.value,
        index=True,
    )
    
    # Resolution
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    adjustment_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationship
    settlement: Mapped["SettlementTransaction"] = relationship(
        "SettlementTransaction", back_populates="disputes"
    )
