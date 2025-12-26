"""Database models for the canvas MVP."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, UniqueConstraint, ForeignKey, Integer, Text, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Canvas(Base):
    __tablename__ = "canvases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200))
    graph_data: Mapped[dict] = mapped_column(JSONB, default=lambda: {"nodes": [], "edges": []})
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    owner_id: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(400))
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    graph_data: Mapped[dict] = mapped_column(JSONB, default=lambda: {"nodes": [], "edges": []})
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    preview_video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    creator_id: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TemplateVersion(Base):
    __tablename__ = "template_versions"
    __table_args__ = (UniqueConstraint("template_id", "version", name="uq_template_versions"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("templates.id"))
    version: Mapped[int] = mapped_column(Integer)
    graph_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    notes: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)
    creator_id: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CapsuleSpec(Base):
    __tablename__ = "capsule_specs"
    __table_args__ = (UniqueConstraint("capsule_key", "version", name="uq_capsule_version"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    capsule_key: Mapped[str] = mapped_column(String(160))
    version: Mapped[str] = mapped_column(String(32))
    display_name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(400))
    spec: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CapsuleRun(Base):
    __tablename__ = "capsule_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    capsule_key: Mapped[str] = mapped_column(String(160))
    capsule_version: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    inputs: Mapped[dict] = mapped_column(JSONB, default=dict)
    params: Mapped[dict] = mapped_column(JSONB, default=dict)
    upstream_context: Mapped[dict] = mapped_column(JSONB, default=dict)
    summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    evidence_refs: Mapped[list] = mapped_column(JSONB, default=list)
    token_usage: Mapped[dict] = mapped_column(JSONB, default=dict)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost_usd_est: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GenerationRun(Base):
    __tablename__ = "generation_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canvas_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canvases.id"))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    spec: Mapped[dict] = mapped_column(JSONB, default=dict)
    outputs: Mapped[dict] = mapped_column(JSONB, default=dict)
    owner_id: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NotebookLibrary(Base):
    __tablename__ = "notebook_library"
    __table_args__ = (UniqueConstraint("notebook_id", name="uq_notebook_library_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notebook_id: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(200))
    notebook_ref: Mapped[str] = mapped_column(String(400))
    owner_id: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    cluster_id: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    cluster_label: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    cluster_tags: Mapped[list] = mapped_column(JSONB, default=list)
    guide_scope: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    source_ids: Mapped[list] = mapped_column(JSONB, default=list)
    source_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    curator_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NotebookAsset(Base):
    __tablename__ = "notebook_assets"
    __table_args__ = (
        UniqueConstraint(
            "notebook_id",
            "asset_id",
            "asset_type",
            name="uq_notebook_assets_key",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notebook_id: Mapped[str] = mapped_column(String(64))
    asset_id: Mapped[str] = mapped_column(String(200))
    asset_type: Mapped[str] = mapped_column(String(32))
    asset_ref: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RawAsset(Base):
    __tablename__ = "raw_assets"
    __table_args__ = (UniqueConstraint("source_id", name="uq_raw_assets_source_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[str] = mapped_column(String(64))
    source_url: Mapped[str] = mapped_column(String(800))
    source_type: Mapped[str] = mapped_column(String(32))
    title: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)
    director: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    scene_ranges: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rights_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VideoSegment(Base):
    __tablename__ = "video_segments"
    __table_args__ = (UniqueConstraint("segment_id", name="uq_video_segments_segment_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id: Mapped[str] = mapped_column(String(120))
    source_id: Mapped[str] = mapped_column(String(64))
    work_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    sequence_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    scene_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    shot_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    time_start: Mapped[str] = mapped_column(String(32))
    time_end: Mapped[str] = mapped_column(String(32))
    shot_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    keyframes: Mapped[list] = mapped_column(JSONB, default=list)
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    visual_schema: Mapped[dict] = mapped_column(JSONB, default=dict)
    audio_schema: Mapped[dict] = mapped_column(JSONB, default=dict)
    motifs: Mapped[list] = mapped_column(JSONB, default=list)
    evidence_refs: Mapped[list] = mapped_column(JSONB, default=list)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    prompt_version: Mapped[str] = mapped_column(String(64))
    model_version: Mapped[str] = mapped_column(String(64))
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "prompt_version",
            "model_version",
            "output_type",
            "output_language",
            name="uq_evidence_record_key",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[str] = mapped_column(String(64))
    summary: Mapped[str] = mapped_column(Text)
    guide_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    homage_guide: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    variation_guide: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    template_recommendations: Mapped[list] = mapped_column(JSONB, default=list)
    user_fit_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    persona_profile: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    synapse_logic: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    origin_notebook_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    filter_notebook_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    cluster_id: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    cluster_label: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    cluster_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    style_logic: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mise_en_scene: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    director_intent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    labels: Mapped[list] = mapped_column(JSONB, default=list)
    signature_motifs: Mapped[list] = mapped_column(JSONB, default=list)
    camera_motion: Mapped[dict] = mapped_column(JSONB, default=dict)
    color_palette: Mapped[dict] = mapped_column(JSONB, default=dict)
    pacing: Mapped[dict] = mapped_column(JSONB, default=dict)
    sound_design: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    editing_rhythm: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    story_beats: Mapped[list] = mapped_column(JSONB, default=list)
    storyboard_cards: Mapped[list] = mapped_column(JSONB, default=list)
    key_patterns: Mapped[list] = mapped_column(JSONB, default=list)
    output_type: Mapped[str] = mapped_column(String(32))
    output_language: Mapped[str] = mapped_column(String(16))
    studio_output_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    adapter: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    opal_workflow_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    prompt_version: Mapped[str] = mapped_column(String(64))
    model_version: Mapped[str] = mapped_column(String(64))
    notebook_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    notebook_ref: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)
    evidence_refs: Mapped[list] = mapped_column(JSONB, default=list)
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PatternCandidate(Base):
    __tablename__ = "pattern_candidates"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "pattern_name",
            "pattern_type",
            "evidence_ref",
            name="uq_pattern_candidate_key",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[str] = mapped_column(String(64))
    pattern_name: Mapped[str] = mapped_column(String(200))
    pattern_type: Mapped[str] = mapped_column(String(32))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evidence_ref: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="proposed")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Pattern(Base):
    __tablename__ = "patterns"
    __table_args__ = (UniqueConstraint("name", "pattern_type", name="uq_patterns_name_type"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    pattern_type: Mapped[str] = mapped_column(String(32))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="validated")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PatternTrace(Base):
    __tablename__ = "pattern_trace"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "pattern_id",
            "evidence_ref",
            name="uq_pattern_trace_key",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[str] = mapped_column(String(64))
    pattern_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patterns.id"))
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evidence_ref: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PatternVersion(Base):
    __tablename__ = "pattern_versions"
    __table_args__ = (UniqueConstraint("version", name="uq_pattern_versions_version"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version: Mapped[str] = mapped_column(String(32))
    note: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OpsActionLog(Base):
    __tablename__ = "ops_action_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    note: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    stats: Mapped[dict] = mapped_column(JSONB, default=dict)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actor_id: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AffiliateProfile(Base):
    __tablename__ = "affiliate_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_affiliate_profile_user"),
        UniqueConstraint("affiliate_code", name="uq_affiliate_profile_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(160))
    affiliate_code: Mapped[str] = mapped_column(String(64))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AffiliateReferral(Base):
    __tablename__ = "affiliate_referrals"
    __table_args__ = (
        UniqueConstraint(
            "referrer_user_id",
            "referee_user_id",
            name="uq_affiliate_referrals_pair",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    affiliate_code: Mapped[str] = mapped_column(String(64))
    referrer_user_id: Mapped[str] = mapped_column(String(160))
    referee_user_id: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    referee_label: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="clicked")
    reward_status: Mapped[str] = mapped_column(String(32), default="pending")
    reward_amount: Mapped[int] = mapped_column(Integer, default=0)
    referee_reward_amount: Mapped[int] = mapped_column(Integer, default=0)
    reward_ledger_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    referee_reward_ledger_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserCredits(Base):
    """User credit balance tracking."""
    __tablename__ = "user_credits"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_credits_user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(160))
    balance: Mapped[int] = mapped_column(Integer, default=0)
    subscription_credits: Mapped[int] = mapped_column(Integer, default=0)
    topup_credits: Mapped[int] = mapped_column(Integer, default=0)
    promo_credits: Mapped[int] = mapped_column(Integer, default=0)
    promo_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CreditLedger(Base):
    """Append-only credit transaction ledger."""
    __tablename__ = "credit_ledger"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(160))
    event_type: Mapped[str] = mapped_column(String(32))  # topup | usage | reward | promo | refund
    amount: Mapped[int] = mapped_column(Integer)  # +/- credits
    balance_snapshot: Mapped[int] = mapped_column(Integer)  # Balance after this tx
    description: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)
    capsule_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("capsule_runs.id"), nullable=True
    )
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
