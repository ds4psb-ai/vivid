"""
VDG Outlier Models

OutlierItem 및 관련 VDG 테이블 모델:
- OutlierItem: 바이럴 콘텐츠 아웃라이어 메타데이터
- RemixNode: VDG 그래프 노드
- VDGEdge: 노드 간 관계 (Fork/Variation)
- ViralKick: 바이럴 킥 포인트
- KeyframeEvidence: 키프레임 증거
- CommentEvidence: 댓글 증거
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    UniqueConstraint,
    ForeignKey,
    Integer,
    Text,
    Float,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# =============================================================================
# Enums
# =============================================================================

class ViralKickStatus(str, Enum):
    """Status of a viral kick."""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class VDGEdgeType(str, Enum):
    """Type of VDG edge relationship."""
    FORK = "fork"
    VARIATION = "variation"
    INSPIRED_BY = "inspired_by"
    REMIX = "remix"


class VDGEdgeStatus(str, Enum):
    """Status of a VDG edge."""
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class AnalysisStatus(str, Enum):
    """Analysis status for OutlierItem."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    VDG_SAVED = "vdg_saved"
    COMMENTS_FAILED = "comments_failed"
    COMMENTS_PENDING_REVIEW = "comments_pending_review"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_PERMANENT = "failed_permanent"
    POST_PROCESSING_FAILED = "post_processing_failed"


# =============================================================================
# OutlierItem - Viral Content Metadata
# =============================================================================

class OutlierItem(Base):
    """
    Outlier item representing a viral content piece.

    Stores metadata, VDG analysis results, and quality metrics.
    """
    __tablename__ = "outlier_items"
    __table_args__ = (
        Index("ix_outlier_items_analysis_status", "analysis_status"),
        Index("ix_outlier_items_category", "category"),
        Index("ix_outlier_items_platform", "platform"),
        Index("ix_outlier_items_created_at", "created_at"),
        Index("ix_outlier_items_analyzed_at", "analyzed_at"),
        Index("ix_outlier_items_hook_format", "hook_format"),
        Index("ix_outlier_items_hook_trigger", "hook_trigger"),
        Index("ix_outlier_items_hook_device", "hook_device"),
        # GIN index for JSONB hook_attributes
        Index(
            "ix_outlier_items_hook_attributes_gin",
            "hook_attributes",
            postgresql_using="gin",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Content Metadata
    source_url: Mapped[str] = mapped_column(String(800))
    source_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    platform: Mapped[str] = mapped_column(String(32), default="tiktok")
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Analysis Status
    analysis_status: Mapped[str] = mapped_column(String(50), default="pending")
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # VDG Data
    vdg_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    vdg_feature_vector: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    vdg_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    visual_empty: Mapped[bool] = mapped_column(Boolean, default=False)

    # 3-Axis Hook Classification (VDG v5.0)
    hook_attributes: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # Denormalized columns for filtering
    hook_format: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    hook_trigger: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    hook_device: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # Engagement Metrics
    view_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    like_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comment_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    share_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Owner & Tags
    owner_id: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


# =============================================================================
# RemixNode - VDG Graph Node
# =============================================================================

class RemixNode(Base):
    """
    VDG graph node representing a content piece in the remix graph.
    """
    __tablename__ = "remix_nodes"
    __table_args__ = (
        Index("ix_remix_nodes_node_id", "node_id"),
        Index("ix_remix_nodes_outlier_item_id", "outlier_item_id"),
        Index("ix_remix_nodes_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    node_id: Mapped[str] = mapped_column(String(120), unique=True)
    outlier_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outlier_items.id"), nullable=True
    )

    # Node metadata
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(800), nullable=True)
    platform: Mapped[str] = mapped_column(String(32), default="tiktok")

    # VDG data reference
    vdg_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


# =============================================================================
# VDGEdge - Graph Edge
# =============================================================================

class VDGEdge(Base):
    """
    Edge in VDG graph representing content relationships.
    """
    __tablename__ = "vdg_edges"
    __table_args__ = (
        Index("ix_vdg_edges_parent_id", "parent_node_id"),
        Index("ix_vdg_edges_child_id", "child_node_id"),
        Index("ix_vdg_edges_status", "edge_status"),
        UniqueConstraint("parent_node_id", "child_node_id", name="uq_vdg_edge_pair"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    parent_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("remix_nodes.id")
    )
    child_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("remix_nodes.id")
    )

    edge_type: Mapped[str] = mapped_column(String(32), default="fork")
    edge_status: Mapped[str] = mapped_column(String(32), default="candidate")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    evidence_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    confirmed_by: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    confirmation_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


# =============================================================================
# ViralKick - Viral Kick Points
# =============================================================================

class ViralKick(Base):
    """
    Viral kick point extracted from VDG analysis.
    """
    __tablename__ = "viral_kicks"
    __table_args__ = (
        Index("ix_viral_kicks_node_id", "node_id"),
        Index("ix_viral_kicks_outlier_item_id", "outlier_item_id"),
        Index("ix_viral_kicks_kick_id", "kick_id"),
        Index("ix_viral_kicks_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    kick_id: Mapped[str] = mapped_column(String(120), unique=True)
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("remix_nodes.id")
    )
    outlier_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outlier_items.id"), nullable=True
    )

    # Kick metadata
    kick_index: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(200))
    mechanism: Mapped[str] = mapped_column(String(500))
    creator_instruction: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Time range
    start_ms: Mapped[int] = mapped_column(Integer, default=0)
    end_ms: Mapped[int] = mapped_column(Integer, default=5000)
    peak_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Quality
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    missing_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    proof_ready: Mapped[bool] = mapped_column(Boolean, default=False)

    # Evidence references
    comment_evidence_ids: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    frame_evidence_ids: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    evidence_comment_ranks: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Cinematography (Phase 1)
    mise_en_scene_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    shotlist_items: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="pending")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


# =============================================================================
# KeyframeEvidence - Keyframe Evidence Records
# =============================================================================

class KeyframeEvidence(Base):
    """
    CV-verified keyframe evidence for viral kicks.
    """
    __tablename__ = "keyframe_evidences"
    __table_args__ = (
        Index("ix_keyframe_evidences_kick_id", "kick_id"),
        Index("ix_keyframe_evidences_node_id", "node_id"),
        Index("ix_keyframe_evidences_evidence_id", "evidence_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    evidence_id: Mapped[str] = mapped_column(String(120), unique=True)
    kick_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("viral_kicks.id")
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("remix_nodes.id")
    )

    # Keyframe metadata
    role: Mapped[str] = mapped_column(String(32), default="unknown")
    t_ms: Mapped[int] = mapped_column(Integer, default=0)
    what_to_see: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # CV metrics
    blur_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    brightness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    motion_proxy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    frame_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Verification
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Cinematography (Phase 1)
    shot_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    composition_grid: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    lighting_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    lens_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    camera_movement: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    extraction_source: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    extraction_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw_values: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


# =============================================================================
# CommentEvidence - Comment Evidence Records
# =============================================================================

class CommentEvidence(Base):
    """
    Comment evidence for viral kicks.
    """
    __tablename__ = "comment_evidences"
    __table_args__ = (
        Index("ix_comment_evidences_node_id", "node_id"),
        Index("ix_comment_evidences_evidence_id", "evidence_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    evidence_id: Mapped[str] = mapped_column(String(120), unique=True)
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("remix_nodes.id")
    )

    # Comment data
    text_snippet: Mapped[str] = mapped_column(String(500))
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    rank: Mapped[int] = mapped_column(Integer, default=1)

    # Matched kicks
    matched_kick_ids: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "ViralKickStatus",
    "VDGEdgeType",
    "VDGEdgeStatus",
    "AnalysisStatus",
    # Models
    "OutlierItem",
    "RemixNode",
    "VDGEdge",
    "ViralKick",
    "KeyframeEvidence",
    "CommentEvidence",
]
