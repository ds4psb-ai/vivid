"""Create OutlierItem and VDG-related tables with 3-axis hook attributes.

Tables:
- outlier_items: Viral content metadata with hook_attributes JSONB
- remix_nodes: VDG graph nodes
- vdg_edges: Graph edges for content relationships
- viral_kicks: Viral kick points
- keyframe_evidences: CV-verified keyframe evidence
- comment_evidences: Comment evidence

Revision ID: 033_create_outlier_items
Revises: 032_add_missing_init_db_tables
Create Date: 2026-01-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "033_create_outlier_items"
down_revision: Union[str, None] = "032_add_missing_init_db_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if table already exists."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}')")
    )
    return result.scalar()


def upgrade() -> None:
    """Create VDG Outlier tables."""

    # ==========================================================================
    # outlier_items
    # ==========================================================================
    if not table_exists("outlier_items"):
        op.create_table(
            "outlier_items",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            # Content Metadata
            sa.Column("source_url", sa.String(800), nullable=False),
            sa.Column("source_id", sa.String(64), nullable=True),
            sa.Column("platform", sa.String(32), nullable=False, server_default="tiktok"),
            sa.Column("title", sa.String(500), nullable=True),
            sa.Column("category", sa.String(50), nullable=True),
            sa.Column("duration_ms", sa.Integer, nullable=True),
            # Analysis Status
            sa.Column("analysis_status", sa.String(50), nullable=False, server_default="pending"),
            sa.Column("analyzed_at", sa.DateTime, nullable=True),
            sa.Column("last_retry_at", sa.DateTime, nullable=True),
            sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
            sa.Column("failure_reason", sa.Text, nullable=True),
            # VDG Data
            sa.Column("vdg_data", postgresql.JSONB, nullable=True),
            sa.Column("vdg_feature_vector", postgresql.JSONB, nullable=True),
            sa.Column("vdg_quality_score", sa.Float, nullable=True),
            sa.Column("visual_empty", sa.Boolean, nullable=False, server_default="false"),
            # 3-Axis Hook Classification (VDG v5.0)
            sa.Column("hook_attributes", postgresql.JSONB, nullable=True),
            sa.Column("hook_format", sa.String(32), nullable=True),
            sa.Column("hook_trigger", sa.String(32), nullable=True),
            sa.Column("hook_device", sa.String(32), nullable=True),
            # Engagement Metrics
            sa.Column("view_count", sa.Integer, nullable=True),
            sa.Column("like_count", sa.Integer, nullable=True),
            sa.Column("comment_count", sa.Integer, nullable=True),
            sa.Column("share_count", sa.Integer, nullable=True),
            # Owner & Tags
            sa.Column("owner_id", sa.String(160), nullable=True),
            sa.Column("tags", postgresql.JSONB, nullable=True),
            # Timestamps
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        )
        # Indexes
        op.create_index("ix_outlier_items_analysis_status", "outlier_items", ["analysis_status"])
        op.create_index("ix_outlier_items_category", "outlier_items", ["category"])
        op.create_index("ix_outlier_items_platform", "outlier_items", ["platform"])
        op.create_index("ix_outlier_items_created_at", "outlier_items", ["created_at"])
        op.create_index("ix_outlier_items_analyzed_at", "outlier_items", ["analyzed_at"])
        op.create_index("ix_outlier_items_source_id", "outlier_items", ["source_id"])
        op.create_index("ix_outlier_items_hook_format", "outlier_items", ["hook_format"])
        op.create_index("ix_outlier_items_hook_trigger", "outlier_items", ["hook_trigger"])
        op.create_index("ix_outlier_items_hook_device", "outlier_items", ["hook_device"])
        # GIN index for JSONB hook_attributes
        op.execute(
            "CREATE INDEX ix_outlier_items_hook_attributes_gin ON outlier_items USING gin (hook_attributes)"
        )

    # ==========================================================================
    # remix_nodes
    # ==========================================================================
    if not table_exists("remix_nodes"):
        op.create_table(
            "remix_nodes",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("node_id", sa.String(120), nullable=False, unique=True),
            sa.Column("outlier_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("outlier_items.id"), nullable=True),
            sa.Column("title", sa.String(500), nullable=True),
            sa.Column("source_url", sa.String(800), nullable=True),
            sa.Column("platform", sa.String(32), nullable=False, server_default="tiktok"),
            sa.Column("vdg_json", postgresql.JSONB, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_remix_nodes_node_id", "remix_nodes", ["node_id"])
        op.create_index("ix_remix_nodes_outlier_item_id", "remix_nodes", ["outlier_item_id"])
        op.create_index("ix_remix_nodes_created_at", "remix_nodes", ["created_at"])

    # ==========================================================================
    # vdg_edges
    # ==========================================================================
    if not table_exists("vdg_edges"):
        op.create_table(
            "vdg_edges",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("parent_node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("remix_nodes.id"), nullable=False),
            sa.Column("child_node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("remix_nodes.id"), nullable=False),
            sa.Column("edge_type", sa.String(32), nullable=False, server_default="fork"),
            sa.Column("edge_status", sa.String(32), nullable=False, server_default="candidate"),
            sa.Column("confidence", sa.Float, nullable=False, server_default="0.5"),
            sa.Column("evidence_json", postgresql.JSONB, nullable=True),
            sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("confirmed_by", sa.String(160), nullable=True),
            sa.Column("confirmed_at", sa.DateTime, nullable=True),
            sa.Column("confirmation_source", sa.String(50), nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
            sa.UniqueConstraint("parent_node_id", "child_node_id", name="uq_vdg_edge_pair"),
        )
        op.create_index("ix_vdg_edges_parent_id", "vdg_edges", ["parent_node_id"])
        op.create_index("ix_vdg_edges_child_id", "vdg_edges", ["child_node_id"])
        op.create_index("ix_vdg_edges_status", "vdg_edges", ["edge_status"])

    # ==========================================================================
    # viral_kicks
    # ==========================================================================
    if not table_exists("viral_kicks"):
        op.create_table(
            "viral_kicks",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("kick_id", sa.String(120), nullable=False, unique=True),
            sa.Column("node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("remix_nodes.id"), nullable=False),
            sa.Column("outlier_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("outlier_items.id"), nullable=True),
            sa.Column("kick_index", sa.Integer, nullable=False, server_default="1"),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("mechanism", sa.String(500), nullable=False),
            sa.Column("creator_instruction", sa.String(500), nullable=True),
            sa.Column("start_ms", sa.Integer, nullable=False, server_default="0"),
            sa.Column("end_ms", sa.Integer, nullable=False, server_default="5000"),
            sa.Column("peak_ms", sa.Integer, nullable=True),
            sa.Column("confidence", sa.Float, nullable=False, server_default="0.7"),
            sa.Column("missing_reason", sa.String(200), nullable=True),
            sa.Column("proof_ready", sa.Boolean, nullable=False, server_default="false"),
            sa.Column("comment_evidence_ids", postgresql.JSONB, nullable=True),
            sa.Column("frame_evidence_ids", postgresql.JSONB, nullable=True),
            sa.Column("evidence_comment_ranks", postgresql.JSONB, nullable=True),
            sa.Column("mise_en_scene_snapshot", postgresql.JSONB, nullable=True),
            sa.Column("shotlist_items", postgresql.JSONB, nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_viral_kicks_node_id", "viral_kicks", ["node_id"])
        op.create_index("ix_viral_kicks_outlier_item_id", "viral_kicks", ["outlier_item_id"])
        op.create_index("ix_viral_kicks_kick_id", "viral_kicks", ["kick_id"])
        op.create_index("ix_viral_kicks_status", "viral_kicks", ["status"])

    # ==========================================================================
    # keyframe_evidences
    # ==========================================================================
    if not table_exists("keyframe_evidences"):
        op.create_table(
            "keyframe_evidences",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("evidence_id", sa.String(120), nullable=False, unique=True),
            sa.Column("kick_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("viral_kicks.id"), nullable=False),
            sa.Column("node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("remix_nodes.id"), nullable=False),
            sa.Column("role", sa.String(32), nullable=False, server_default="unknown"),
            sa.Column("t_ms", sa.Integer, nullable=False, server_default="0"),
            sa.Column("what_to_see", sa.String(200), nullable=True),
            sa.Column("blur_score", sa.Float, nullable=True),
            sa.Column("brightness", sa.Float, nullable=True),
            sa.Column("motion_proxy", sa.Float, nullable=True),
            sa.Column("frame_hash", sa.String(64), nullable=True),
            sa.Column("verified", sa.Boolean, nullable=False, server_default="false"),
            sa.Column("verification_reason", sa.String(100), nullable=True),
            # Cinematography Phase 1
            sa.Column("shot_type", sa.String(32), nullable=True),
            sa.Column("composition_grid", sa.String(32), nullable=True),
            sa.Column("lighting_type", sa.String(32), nullable=True),
            sa.Column("lens_type", sa.String(32), nullable=True),
            sa.Column("camera_movement", sa.String(32), nullable=True),
            sa.Column("extraction_source", sa.String(16), nullable=True),
            sa.Column("extraction_confidence", sa.Float, nullable=True),
            sa.Column("raw_values", postgresql.JSONB, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_keyframe_evidences_kick_id", "keyframe_evidences", ["kick_id"])
        op.create_index("ix_keyframe_evidences_node_id", "keyframe_evidences", ["node_id"])
        op.create_index("ix_keyframe_evidences_evidence_id", "keyframe_evidences", ["evidence_id"])

    # ==========================================================================
    # comment_evidences
    # ==========================================================================
    if not table_exists("comment_evidences"):
        op.create_table(
            "comment_evidences",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("evidence_id", sa.String(120), nullable=False, unique=True),
            sa.Column("node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("remix_nodes.id"), nullable=False),
            sa.Column("text_snippet", sa.String(500), nullable=False),
            sa.Column("like_count", sa.Integer, nullable=False, server_default="0"),
            sa.Column("rank", sa.Integer, nullable=False, server_default="1"),
            sa.Column("matched_kick_ids", postgresql.JSONB, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_comment_evidences_node_id", "comment_evidences", ["node_id"])
        op.create_index("ix_comment_evidences_evidence_id", "comment_evidences", ["evidence_id"])


def downgrade() -> None:
    """Drop VDG Outlier tables in reverse dependency order."""
    op.drop_table("comment_evidences")
    op.drop_table("keyframe_evidences")
    op.drop_table("viral_kicks")
    op.drop_table("vdg_edges")
    op.drop_table("remix_nodes")
    op.drop_table("outlier_items")
