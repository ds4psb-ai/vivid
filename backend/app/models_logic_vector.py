"""Logic Vector Version Model.

SQLAlchemy model for Logic Vector versioning and drift tracking.

Usage:
    from app.models_logic_vector import LogicVectorVersion
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, Float, Integer, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LogicVectorVersion(Base):
    """Logic Vector version for IP-based versioning and drift tracking.

    Stores versioned Logic Vectors with drift scoring between versions.
    Supports active version tracking with valid_from/valid_until periods.

    Attributes:
        id: Unique version identifier
        ip_id: IP identifier
        version_number: Sequential version number (1, 2, 3, ...)
        embedding: 384-dim embedding vector for similarity search
        logic_vector: Full Logic Vector as JSONB
        source_videos: Video URIs used to create this version
        is_active: Whether this is the currently active version
        valid_from: When this version became active
        valid_until: When this version was superseded
        drift_score_from_prev: Drift score from previous version
        drift_reason: Reason for version change
        created_at: Creation timestamp
        created_by: User ID who created this version
    """
    __tablename__ = "logic_vector_versions"
    __table_args__ = (
        UniqueConstraint("ip_id", "version_number", name="uq_ip_version"),
        Index("ix_logic_vector_versions_ip_active", "ip_id", "is_active"),
        Index("ix_logic_vector_versions_ip_version", "ip_id", "version_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    ip_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Logic Vector data
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        ARRAY(Float),
        nullable=True,
    )
    logic_vector: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    source_videos: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
    )

    # Validity tracking
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    valid_from: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Drift metadata
    drift_score_from_prev: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    drift_reason: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    created_by: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "LogicVectorVersion",
]
