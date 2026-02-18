"""Rights Graph models for Original-IP Foundry.

Stores source license constraints and generation provenance links used by
pre/post rights gate checks.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RightsAsset(Base):
    """Normalized rights asset source for generation-time policy checks."""

    __tablename__ = "rights_assets"
    __table_args__ = (
        Index("ix_rights_assets_asset_id", "asset_id"),
        Index("ix_rights_assets_license_type", "license_type"),
        Index("ix_rights_assets_source_type", "source_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    license_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_license: Mapped[str] = mapped_column(String(200), nullable=False)

    allowed_actions: Mapped[list] = mapped_column(JSONB, default=list)
    blocked_elements: Mapped[list] = mapped_column(JSONB, default=list)

    attribution_required: Mapped[bool] = mapped_column(Boolean, default=False)
    derivative_allowed: Mapped[bool] = mapped_column(Boolean, default=True)

    license_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("derivative_allowed", True)
        kwargs.setdefault("attribution_required", False)
        super().__init__(**kwargs)


class RightsRule(Base):
    """Policy rules attached to a rights asset."""

    __tablename__ = "rights_rules"
    __table_args__ = (
        Index("ix_rights_rules_asset_id", "rights_asset_id"),
        Index("ix_rights_rules_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rights_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rights_assets.id", ondelete="CASCADE"),
        nullable=False,
    )

    rule_code: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rule_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProvenanceEvent(Base):
    """Immutable provenance events linking source assets to outputs."""

    __tablename__ = "provenance_events"
    __table_args__ = (
        Index("ix_provenance_events_asset_id", "rights_asset_id"),
        Index("ix_provenance_events_project_scene", "project_id", "scene_id"),
        Index("ix_provenance_events_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rights_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rights_assets.id", ondelete="RESTRICT"),
        nullable=False,
    )

    project_id: Mapped[str] = mapped_column(String(120), nullable=False)
    scene_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    event_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    evidence_refs: Mapped[list] = mapped_column(JSONB, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
