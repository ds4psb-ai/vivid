"""
Feature Flag SQLAlchemy Models (2026 Best Practice)

Tables:
- feature_flags: Flag definitions with targeting rules
- feature_flag_audit: Audit log for changes
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Text,
    Integer,
    JSON,
    ForeignKey,
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class FlagStatus(str, enum.Enum):
    """Feature flag status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class FeatureFlag(Base):
    """
    Feature flag definition with targeting rules.

    2026 Best Practice:
    - JSON strategies for flexible targeting
    - Variants for multivariate flags
    - Audit trail for compliance
    """
    __tablename__ = "feature_flags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flag_key = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Global enable/disable (kill switch)
    enabled = Column(Boolean, default=False, nullable=False)
    status = Column(SQLEnum(FlagStatus), default=FlagStatus.ACTIVE, nullable=False)

    # Targeting strategies (JSON)
    # Example: {"userIds": ["user1", "user2"], "percentage": 50, "properties": {"plan": "premium"}}
    strategies = Column(JSON, default=dict, nullable=False)

    # Variants for A/B or multivariate (JSON)
    # Example: [{"name": "control", "weight": 50}, {"name": "variant_a", "weight": 50}]
    variants = Column(JSON, default=list, nullable=False)

    # Default variant when no strategies match
    default_variant = Column(String(100), default="off", nullable=False)

    # Environment targeting
    environments = Column(JSON, default=lambda: ["production", "staging", "development"])

    # Metadata
    tags = Column(JSON, default=list, nullable=False)
    owner = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    audit_logs = relationship("FeatureFlagAudit", back_populates="flag", lazy="dynamic")

    # Indexes
    __table_args__ = (
        Index("ix_feature_flags_status", "status"),
        Index("ix_feature_flags_enabled", "enabled"),
    )

    def __repr__(self) -> str:
        return f"<FeatureFlag {self.flag_key} enabled={self.enabled}>"


class FeatureFlagAudit(Base):
    """
    Audit log for feature flag changes.

    2026 Best Practice:
    - Track all changes for compliance
    - Store before/after state
    - Record who made changes
    """
    __tablename__ = "feature_flag_audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flag_id = Column(Integer, ForeignKey("feature_flags.id"), nullable=False)
    flag_key = Column(String(255), nullable=False, index=True)

    # Change details
    action = Column(String(50), nullable=False)  # created, updated, deleted, enabled, disabled
    changed_by = Column(String(255), nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # State snapshots (JSON)
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)

    # Change reason/comment
    reason = Column(Text, nullable=True)

    # Relationships
    flag = relationship("FeatureFlag", back_populates="audit_logs")

    # Indexes
    __table_args__ = (
        Index("ix_feature_flag_audit_changed_at", "changed_at"),
    )

    def __repr__(self) -> str:
        return f"<FeatureFlagAudit {self.flag_key} action={self.action}>"
