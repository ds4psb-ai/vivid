"""Human Cloud Models.

Models for the Human Cloud marketplace:
- CreativeRequest: Client's request for creative work
- CreatorProfile: Creator's profile and portfolio
- Assignment: Request-creator matching
- EvidenceLog: Work progress documentation
- Delivery: Final deliverable submission
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Text, Integer, Boolean, DateTime, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# =============================================================================
# Enums
# =============================================================================

class RequestStatus(str, Enum):
    """Creative request status."""
    DRAFT = "draft"                 # Being composed
    OPEN = "open"                   # Accepting applications
    ASSIGNED = "assigned"           # Creator matched
    IN_PROGRESS = "in_progress"     # Work ongoing
    REVIEW = "review"               # Delivered, pending approval
    COMPLETED = "completed"         # Approved, payment processed
    CANCELLED = "cancelled"         # Request cancelled
    DISPUTED = "disputed"           # Payment dispute


class RequestCategory(str, Enum):
    """Creative work categories."""
    VIDEO_CREATIVE = "video_creative"     # 영상 크리에이티브
    THUMBNAIL = "thumbnail"               # 유튜브 썸네일
    SHORT_VIDEO = "short_video"           # 숏폼 영상
    MOTION_GRAPHIC = "motion_graphic"     # 모션 그래픽
    BRAND_VIDEO = "brand_video"           # 브랜드 영상


class AssignmentStatus(str, Enum):
    """Assignment status."""
    PENDING = "pending"         # Waiting acceptance
    ACCEPTED = "accepted"       # Creator accepted
    DECLINED = "declined"       # Creator declined
    ACTIVE = "active"           # Work in progress
    COMPLETED = "completed"     # Successfully delivered
    CANCELLED = "cancelled"     # Cancelled by either party


class EvidenceType(str, Enum):
    """Evidence log types."""
    STATUS_UPDATE = "status_update"   # Progress update
    FILE_UPLOAD = "file_upload"       # Work file uploaded
    MILESTONE = "milestone"           # Milestone completed
    REVISION = "revision"             # Revision requested/done
    COMMUNICATION = "communication"   # Client-creator message
    APPROVAL = "approval"             # Work approved


# =============================================================================
# Creator Profile
# =============================================================================

class CreatorProfile(Base):
    """Creator profile for Human Cloud marketplace.
    
    Stores creator capabilities, portfolio, and metrics.
    """
    __tablename__ = "creator_profiles"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    
    # Profile info
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    portfolio_urls: Mapped[list] = mapped_column(JSONB, default=list)
    
    # Capabilities
    categories: Mapped[list] = mapped_column(JSONB, default=list)  # List of RequestCategory
    skills: Mapped[list] = mapped_column(JSONB, default=list)      # Tags like "AfterEffects", "Premiere"
    
    # Rates
    hourly_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Credits per hour
    min_budget: Mapped[int] = mapped_column(Integer, default=100)               # Minimum project credits
    
    # Metrics (updated by system)
    completed_count: Mapped[int] = mapped_column(Integer, default=0)
    total_earned: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    avg_response_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


# =============================================================================
# Creative Request
# =============================================================================

class CreativeRequest(Base):
    """A creative work request from a client.
    
    Represents demand side of Human Cloud marketplace.
    """
    __tablename__ = "creative_requests"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    # Client
    client_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    # Request details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default=RequestCategory.VIDEO_CREATIVE.value)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    
    # Requirements
    requirements: Mapped[dict] = mapped_column(JSONB, default=dict)  # duration, format, etc.
    reference_urls: Mapped[list] = mapped_column(JSONB, default=list)
    attached_files: Mapped[list] = mapped_column(JSONB, default=list)
    
    # Budget & Timeline
    budget_credits: Mapped[int] = mapped_column(Integer, nullable=False)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    estimated_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20), 
        default=RequestStatus.DRAFT.value,
        index=True,
    )
    
    # Assignment (when matched)
    assigned_creator_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("creator_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Completion
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    client_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    client_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Payment tracking
    credits_escrowed: Mapped[int] = mapped_column(Integer, default=0)
    credits_released: Mapped[int] = mapped_column(Integer, default=0)
    platform_fee: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_creative_requests_status_category", "status", "category"),
    )


# =============================================================================
# Assignment
# =============================================================================

class Assignment(Base):
    """Assignment linking request to creator.
    
    Tracks the full lifecycle of a request-creator relationship.
    """
    __tablename__ = "assignments"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    request_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("creative_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    creator_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("creator_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20), 
        default=AssignmentStatus.PENDING.value,
    )
    
    # Terms agreed
    agreed_credits: Mapped[int] = mapped_column(Integer, nullable=False)
    agreed_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    agreed_revisions: Mapped[int] = mapped_column(Integer, default=1)
    
    # Progress
    milestones: Mapped[list] = mapped_column(JSONB, default=list)
    current_milestone: Mapped[int] = mapped_column(Integer, default=0)
    
    # Completion
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Ratings (mutual)
    creator_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    client_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


# =============================================================================
# Evidence Log
# =============================================================================

class EvidenceLog(Base):
    """Evidence log for work progress documentation.
    
    Auto-generated logs for transparency and dispute resolution.
    """
    __tablename__ = "evidence_logs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    assignment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Event details
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Who triggered
    actor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(20), nullable=False)  # client, creator, system
    
    # Attachments
    attachments: Mapped[list] = mapped_column(JSONB, default=list)  # file URLs
    
    # Extra data
    extra: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # For file uploads, track versions
    file_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Auto-captured context
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# =============================================================================
# Delivery
# =============================================================================

class Delivery(Base):
    """Final deliverable submission.
    
    Represents a complete submission for client review.
    """
    __tablename__ = "deliveries"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    assignment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Submission
    version: Mapped[int] = mapped_column(Integer, default=1)
    files: Mapped[list] = mapped_column(JSONB, default=list)  # file URLs
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Review
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, approved, rejected
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # If rejected, what needs to change
    revision_request: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamp
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# =============================================================================
# Revenue Share Constants (75/25)
# =============================================================================

HUMAN_CLOUD_REVENUE_SHARE = {
    "creator_share": 0.75,   # 75% to creator
    "platform_share": 0.25,  # 25% to platform
}
