"""MiniApps Models.

Models for MiniApp/Dimension Portal submission requests.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MiniAppSubmission(Base):
    """User-submitted MiniApp proposals for review.

    When users create and submit dimension portals/miniapps,
    they go into pending_review status for the internal team.
    """
    __tablename__ = "miniapp_submissions"
    __table_args__ = (
        Index("ix_miniapp_submissions_user", "user_id"),
        Index("ix_miniapp_submissions_status", "status"),
        Index("ix_miniapp_submissions_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(160))

    # App info
    app_name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)

    # Source
    source_type: Mapped[str] = mapped_column(String(10))  # "github" or "zip"
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    zip_file_uri: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Optional metadata
    ai_tool: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Review status: pending_review, approved, rejected
    status: Mapped[str] = mapped_column(String(20), default="pending_review")
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
