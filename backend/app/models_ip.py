"""IP (Intellectual Property) Models for IP-First UX.

This module defines models for:
- IP Catalog: Core IP registry (e.g., Goblin, Squid Game)
- IP Workflow Presets: Pre-configured generation templates per IP
- IP Rights: License and rights management per IP
- DMCA Cases: Notice/Counter-notice handling for takedowns
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IPCatalog(Base):
    """IP Catalog - Core IP registry for IP-First UX.

    Each IP entry represents a cultural property (drama, movie, etc.)
    that users can create fan-fiction content for.
    """
    __tablename__ = "ip_catalog"
    __table_args__ = (
        Index("ix_ip_catalog_slug", "slug"),
        Index("ix_ip_catalog_genre", "genre"),
        Index("ix_ip_catalog_license_status", "license_status"),
        Index("ix_ip_catalog_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    # Display info
    name_ko: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str] = mapped_column(String(200), nullable=False)
    description_ko: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    banner_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Classification
    genre: Mapped[list] = mapped_column(JSONB, default=list)  # ["drama", "fantasy", "romance"]
    tags: Mapped[list] = mapped_column(JSONB, default=list)   # ["trending", "popular"]

    # Hidden auteur DNA (sealed from UI)
    auteur_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Rights status
    license_status: Mapped[str] = mapped_column(String(32), default="allowed")  # allowed/restricted/prohibited

    # Stats
    preset_count: Mapped[int] = mapped_column(Integer, default=0)
    generation_count: Mapped[int] = mapped_column(Integer, default=0)

    # Worldbuilding context (for AI generation)
    worldbuilding: Mapped[dict] = mapped_column(JSONB, default=dict)  # characters, setting, themes

    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    featured_order: Mapped[int] = mapped_column(Integer, default=0)

    # Phase 10: Chat features
    chat_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    persona_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    voice_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # ElevenLabs/Chatterbox voice ID
    chat_model_default: Mapped[str] = mapped_column(String(32), default="flash")  # flash, pro, opus
    chat_session_count: Mapped[int] = mapped_column(Integer, default=0)
    chat_message_count: Mapped[int] = mapped_column(Integer, default=0)
    marketplace_listing_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IPWorkflowPreset(Base):
    """IP Workflow Preset - Pre-configured generation templates.

    Each preset defines a specific output type (e.g., 3-min drama, MV clip)
    with pre-configured workflow steps and estimated costs.
    """
    __tablename__ = "ip_workflow_presets"
    __table_args__ = (
        Index("ix_ip_workflow_presets_ip_id", "ip_id"),
        Index("ix_ip_workflow_presets_preset_type", "preset_type"),
        Index("ix_ip_workflow_presets_is_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ip_catalog.id"), nullable=False)

    # Display info
    name_ko: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str] = mapped_column(String(200), nullable=False)
    description_ko: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Preset type
    preset_type: Mapped[str] = mapped_column(String(64), nullable=False)  # drama_3min, mv_clip, still_cut, etc.

    # Workflow configuration (Sealed - not exposed to UI)
    workflow_steps: Mapped[list] = mapped_column(JSONB, default=list)  # [{"step": "story", "capsule": "..."}]
    default_params: Mapped[dict] = mapped_column(JSONB, default=dict)  # default generation params
    workflow_capsule_id: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    pattern_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # Cost estimation
    estimated_credits: Mapped[int] = mapped_column(Integer, default=10)
    estimated_duration_seconds: Mapped[int] = mapped_column(Integer, default=180)  # 3 minutes

    # Stats
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IPRights(Base):
    """IP Rights - License and territory management.

    Tracks license status, territories, scope, and DMCA compliance
    information for each IP.
    """
    __tablename__ = "ip_rights"
    __table_args__ = (
        Index("ix_ip_rights_ip_id", "ip_id"),
        Index("ix_ip_rights_license_status", "license_status"),
        Index("ix_ip_rights_expiry", "expiry"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ip_catalog.id"), nullable=False, unique=True)

    # License status
    license_status: Mapped[str] = mapped_column(String(32), default="allowed")  # allowed/restricted/prohibited

    # Territory restrictions
    territory: Mapped[list] = mapped_column(JSONB, default=list)  # ["KR", "US", "JP"] - empty means worldwide
    blocked_territory: Mapped[list] = mapped_column(JSONB, default=list)  # territories where generation is blocked

    # Usage scope
    scope: Mapped[str] = mapped_column(String(64), default="fan_creation")  # fan_creation/commercial/educational
    commercial_ok: Mapped[bool] = mapped_column(Boolean, default=False)

    # License details
    license_holder: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    license_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expiry: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # DMCA Compliance
    dmca_agent_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    dmca_agent_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    repeat_infringer_threshold: Mapped[int] = mapped_column(Integer, default=3)

    # Revenue share (if applicable)
    revenue_share_percent: Mapped[int] = mapped_column(Integer, default=0)  # IP owner's share

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DMCACase(Base):
    """DMCA Case - Takedown notice and counter-notice handling.

    Implements DMCA Safe Harbor compliance with proper notice/counter flow.
    """
    __tablename__ = "dmca_cases"
    __table_args__ = (
        Index("ix_dmca_cases_ip_id", "ip_id"),
        Index("ix_dmca_cases_content_id", "content_id"),
        Index("ix_dmca_cases_status", "status"),
        Index("ix_dmca_cases_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Related entities
    ip_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("ip_catalog.id"), nullable=True)
    content_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)  # generation or artifact ID
    content_type: Mapped[str] = mapped_column(String(64), default="generation")  # generation/artifact/etc.
    user_id: Mapped[str] = mapped_column(String(160), nullable=False)  # content owner

    # Notice details
    claimant_name: Mapped[str] = mapped_column(String(200), nullable=False)
    claimant_email: Mapped[str] = mapped_column(String(200), nullable=False)
    claimant_company: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Claim description
    claim_description: Mapped[str] = mapped_column(Text, nullable=False)
    claimed_work: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # original work being infringed
    claimed_urls: Mapped[list] = mapped_column(JSONB, default=list)  # URLs of infringing content

    # Status tracking
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending/removed/counter_pending/restored/rejected

    # Counter-notice (if filed)
    counter_statement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    counter_filed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    counter_user_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    counter_user_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # DMCA timeline
    notice_received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    content_removed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    counter_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # 10-14 business days after counter
    restored_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Admin notes
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    handled_by: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IPGeneration(Base):
    """IP Generation - Track generations created from IP presets.

    Links IP catalog, presets, and capsule runs for evidence tracking.
    """
    __tablename__ = "ip_generations"
    __table_args__ = (
        Index("ix_ip_generations_ip_id", "ip_id"),
        Index("ix_ip_generations_preset_id", "preset_id"),
        Index("ix_ip_generations_user_id", "user_id"),
        Index("ix_ip_generations_status", "status"),
        Index("ix_ip_generations_workflow_execution_id", "workflow_execution_id"),
        Index("ix_ip_generations_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Related entities
    ip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ip_catalog.id"), nullable=False)
    preset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ip_workflow_presets.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(160), nullable=False)

    # User input
    user_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Workflow tracking
    run_token_id: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    workflow_execution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id"),
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending/running/completed/failed/cancelled
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Results
    output_artifacts: Mapped[list] = mapped_column(JSONB, default=list)  # artifact IDs
    preview_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Evidence tracking
    evidence_refs: Mapped[list] = mapped_column(JSONB, default=list)  # evidence references
    pattern_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # Cost tracking
    credits_reserved: Mapped[int] = mapped_column(Integer, default=0)
    credits_consumed: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class IPPayoutLedger(Base):
    """IP Payout Ledger - Revenue split and holdback tracking per IP generation."""
    __tablename__ = "ip_payout_ledger"
    __table_args__ = (
        Index("ix_ip_payout_ledger_ip_id", "ip_id"),
        Index("ix_ip_payout_ledger_creator_id", "creator_id"),
        Index("ix_ip_payout_ledger_status", "status"),
        Index("ix_ip_payout_ledger_holdback_until", "holdback_until"),
        Index("ix_ip_payout_ledger_generation_id", "generation_id"),
        UniqueConstraint("generation_id", name="uq_ip_payout_ledger_generation_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ip_catalog.id"), nullable=False)
    generation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ip_generations.id", ondelete="SET NULL"),
        nullable=True,
    )
    creator_id: Mapped[str] = mapped_column(String(160), nullable=False)

    gross_amount: Mapped[int] = mapped_column(Integer, default=0)
    ip_owner_share: Mapped[int] = mapped_column(Integer, default=0)
    creator_share: Mapped[int] = mapped_column(Integer, default=0)
    platform_share: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending/holdback/released/disputed
    holdback_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    dispute_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IPPayoutDispute(Base):
    """Dispute records for IP payout ledger."""
    __tablename__ = "ip_payout_disputes"
    __table_args__ = (
        Index("ix_ip_payout_disputes_ledger_id", "ledger_id"),
        Index("ix_ip_payout_disputes_status", "status"),
        Index("ix_ip_payout_disputes_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ledger_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ip_payout_ledger.id", ondelete="CASCADE"),
        nullable=False,
    )
    complainant_id: Mapped[str] = mapped_column(String(160), nullable=False)

    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list] = mapped_column(JSONB, default=list)

    status: Mapped[str] = mapped_column(String(32), default="open")  # open/in_review/resolved/rejected
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
