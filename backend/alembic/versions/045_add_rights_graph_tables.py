"""Add rights graph core tables.

Revision ID: 045_add_rights_graph_tables
Revises: 044_prompty_visibility
Create Date: 2026-02-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "045_add_rights_graph_tables"
down_revision = "044_prompty_visibility"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rights_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", sa.String(length=160), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("license_type", sa.String(length=64), nullable=False),
        sa.Column("source_license", sa.String(length=200), nullable=False),
        sa.Column("allowed_actions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("blocked_elements", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("attribution_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("derivative_allowed", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("license_url", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id"),
    )
    op.create_index("ix_rights_assets_asset_id", "rights_assets", ["asset_id"])
    op.create_index("ix_rights_assets_license_type", "rights_assets", ["license_type"])
    op.create_index("ix_rights_assets_source_type", "rights_assets", ["source_type"])

    op.create_table(
        "rights_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rights_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_code", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("rule_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["rights_asset_id"], ["rights_assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rights_rules_asset_id", "rights_rules", ["rights_asset_id"])
    op.create_index("ix_rights_rules_active", "rights_rules", ["is_active"])

    op.create_table(
        "provenance_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rights_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", sa.String(length=120), nullable=False),
        sa.Column("scene_id", sa.String(length=120), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("event_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["rights_asset_id"], ["rights_assets.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_provenance_events_asset_id", "provenance_events", ["rights_asset_id"])
    op.create_index("ix_provenance_events_project_scene", "provenance_events", ["project_id", "scene_id"])
    op.create_index("ix_provenance_events_created_at", "provenance_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_provenance_events_created_at", table_name="provenance_events")
    op.drop_index("ix_provenance_events_project_scene", table_name="provenance_events")
    op.drop_index("ix_provenance_events_asset_id", table_name="provenance_events")
    op.drop_table("provenance_events")

    op.drop_index("ix_rights_rules_active", table_name="rights_rules")
    op.drop_index("ix_rights_rules_asset_id", table_name="rights_rules")
    op.drop_table("rights_rules")

    op.drop_index("ix_rights_assets_source_type", table_name="rights_assets")
    op.drop_index("ix_rights_assets_license_type", table_name="rights_assets")
    op.drop_index("ix_rights_assets_asset_id", table_name="rights_assets")
    op.drop_table("rights_assets")
