"""Add IP Catalog tables for IP-First UX.

Revision ID: 018_add_ip_catalog
Revises: 017_add_crebit_payment_security
Create Date: 2026-01-19

Adds tables for:
- ip_catalog: Core IP registry (e.g., K-dramas, movies)
- ip_workflow_presets: Pre-configured generation templates
- ip_rights: License and territory management
- dmca_cases: DMCA notice/counter-notice handling
- ip_generations: Track generations from IP presets
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "018_add_ip_catalog"
down_revision = "017_add_crebit_payment_security"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create IP Catalog tables."""

    # 1. IP Catalog - Core IP registry
    op.create_table(
        "ip_catalog",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
        # Display info
        sa.Column("name_ko", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200), nullable=False),
        sa.Column("description_ko", sa.Text(), nullable=True),
        sa.Column("description_en", sa.Text(), nullable=True),
        sa.Column("thumbnail_url", sa.String(500), nullable=True),
        sa.Column("banner_url", sa.String(500), nullable=True),
        # Classification
        sa.Column("genre", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("tags", postgresql.JSONB(), nullable=False, server_default="[]"),
        # Hidden auteur DNA (sealed from UI)
        sa.Column("auteur_key", sa.String(64), nullable=True),
        # Rights status
        sa.Column("license_status", sa.String(32), nullable=False, server_default="allowed"),
        # Stats
        sa.Column("preset_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("generation_count", sa.Integer(), nullable=False, server_default="0"),
        # Worldbuilding context
        sa.Column("worldbuilding", postgresql.JSONB(), nullable=False, server_default="{}"),
        # Metadata
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("featured_order", sa.Integer(), nullable=False, server_default="0"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_ip_catalog_slug", "ip_catalog", ["slug"])
    op.create_index("ix_ip_catalog_genre", "ip_catalog", ["genre"], postgresql_using="gin")
    op.create_index("ix_ip_catalog_license_status", "ip_catalog", ["license_status"])
    op.create_index("ix_ip_catalog_created_at", "ip_catalog", ["created_at"])

    # 2. IP Workflow Presets - Pre-configured generation templates
    op.create_table(
        "ip_workflow_presets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ip_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ip_catalog.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Display info
        sa.Column("name_ko", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200), nullable=False),
        sa.Column("description_ko", sa.Text(), nullable=True),
        sa.Column("description_en", sa.Text(), nullable=True),
        sa.Column("thumbnail_url", sa.String(500), nullable=True),
        # Preset type
        sa.Column("preset_type", sa.String(64), nullable=False),
        # Workflow configuration (Sealed)
        sa.Column("workflow_steps", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("default_params", postgresql.JSONB(), nullable=False, server_default="{}"),
        # Cost estimation
        sa.Column("estimated_credits", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("estimated_duration_seconds", sa.Integer(), nullable=False, server_default="180"),
        # Stats
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        # Metadata
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_ip_workflow_presets_ip_id", "ip_workflow_presets", ["ip_id"])
    op.create_index("ix_ip_workflow_presets_preset_type", "ip_workflow_presets", ["preset_type"])
    op.create_index("ix_ip_workflow_presets_is_active", "ip_workflow_presets", ["is_active"])

    # 3. IP Rights - License and territory management
    op.create_table(
        "ip_rights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ip_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ip_catalog.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        # License status
        sa.Column("license_status", sa.String(32), nullable=False, server_default="allowed"),
        # Territory restrictions
        sa.Column("territory", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("blocked_territory", postgresql.JSONB(), nullable=False, server_default="[]"),
        # Usage scope
        sa.Column("scope", sa.String(64), nullable=False, server_default="fan_creation"),
        sa.Column("commercial_ok", sa.Boolean(), nullable=False, server_default="false"),
        # License details
        sa.Column("license_holder", sa.String(200), nullable=True),
        sa.Column("license_notes", sa.Text(), nullable=True),
        sa.Column("expiry", sa.DateTime(), nullable=True),
        # DMCA Compliance
        sa.Column("dmca_agent_email", sa.String(200), nullable=True),
        sa.Column("dmca_agent_name", sa.String(200), nullable=True),
        sa.Column("repeat_infringer_threshold", sa.Integer(), nullable=False, server_default="3"),
        # Revenue share
        sa.Column("revenue_share_percent", sa.Integer(), nullable=False, server_default="0"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_ip_rights_ip_id", "ip_rights", ["ip_id"])
    op.create_index("ix_ip_rights_license_status", "ip_rights", ["license_status"])
    op.create_index("ix_ip_rights_expiry", "ip_rights", ["expiry"])

    # 4. DMCA Cases - Notice/Counter-notice handling
    op.create_table(
        "dmca_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # Related entities
        sa.Column(
            "ip_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ip_catalog.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_type", sa.String(64), nullable=False, server_default="generation"),
        sa.Column("user_id", sa.String(160), nullable=False),
        # Notice details
        sa.Column("claimant_name", sa.String(200), nullable=False),
        sa.Column("claimant_email", sa.String(200), nullable=False),
        sa.Column("claimant_company", sa.String(200), nullable=True),
        # Claim description
        sa.Column("claim_description", sa.Text(), nullable=False),
        sa.Column("claimed_work", sa.Text(), nullable=True),
        sa.Column("claimed_urls", postgresql.JSONB(), nullable=False, server_default="[]"),
        # Status tracking
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        # Counter-notice
        sa.Column("counter_statement", sa.Text(), nullable=True),
        sa.Column("counter_filed_at", sa.DateTime(), nullable=True),
        sa.Column("counter_user_name", sa.String(200), nullable=True),
        sa.Column("counter_user_email", sa.String(200), nullable=True),
        # DMCA timeline
        sa.Column("notice_received_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("content_removed_at", sa.DateTime(), nullable=True),
        sa.Column("counter_deadline", sa.DateTime(), nullable=True),
        sa.Column("restored_at", sa.DateTime(), nullable=True),
        # Admin notes
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("handled_by", sa.String(160), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_dmca_cases_ip_id", "dmca_cases", ["ip_id"])
    op.create_index("ix_dmca_cases_content_id", "dmca_cases", ["content_id"])
    op.create_index("ix_dmca_cases_status", "dmca_cases", ["status"])
    op.create_index("ix_dmca_cases_created_at", "dmca_cases", ["created_at"])

    # 5. IP Generations - Track generations from IP presets
    op.create_table(
        "ip_generations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # Related entities
        sa.Column(
            "ip_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ip_catalog.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "preset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ip_workflow_presets.id", ondelete="SET NULL"),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(160), nullable=False),
        # User input
        sa.Column("user_prompt", sa.Text(), nullable=True),
        # Workflow tracking
        sa.Column("workflow_session_id", sa.String(160), nullable=True),
        sa.Column("run_token_id", sa.String(160), nullable=True),
        # Status
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_step", sa.String(64), nullable=True),
        # Results
        sa.Column("output_artifacts", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("preview_url", sa.String(500), nullable=True),
        # Evidence tracking
        sa.Column("evidence_refs", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("pattern_version", sa.String(32), nullable=True),
        # Cost tracking
        sa.Column("credits_reserved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("credits_consumed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        # Error handling
        sa.Column("error_message", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    op.create_index("ix_ip_generations_ip_id", "ip_generations", ["ip_id"])
    op.create_index("ix_ip_generations_preset_id", "ip_generations", ["preset_id"])
    op.create_index("ix_ip_generations_user_id", "ip_generations", ["user_id"])
    op.create_index("ix_ip_generations_status", "ip_generations", ["status"])
    op.create_index("ix_ip_generations_created_at", "ip_generations", ["created_at"])


def downgrade() -> None:
    """Drop IP Catalog tables in reverse order."""
    # Drop ip_generations
    op.drop_index("ix_ip_generations_created_at", "ip_generations")
    op.drop_index("ix_ip_generations_status", "ip_generations")
    op.drop_index("ix_ip_generations_user_id", "ip_generations")
    op.drop_index("ix_ip_generations_preset_id", "ip_generations")
    op.drop_index("ix_ip_generations_ip_id", "ip_generations")
    op.drop_table("ip_generations")

    # Drop dmca_cases
    op.drop_index("ix_dmca_cases_created_at", "dmca_cases")
    op.drop_index("ix_dmca_cases_status", "dmca_cases")
    op.drop_index("ix_dmca_cases_content_id", "dmca_cases")
    op.drop_index("ix_dmca_cases_ip_id", "dmca_cases")
    op.drop_table("dmca_cases")

    # Drop ip_rights
    op.drop_index("ix_ip_rights_expiry", "ip_rights")
    op.drop_index("ix_ip_rights_license_status", "ip_rights")
    op.drop_index("ix_ip_rights_ip_id", "ip_rights")
    op.drop_table("ip_rights")

    # Drop ip_workflow_presets
    op.drop_index("ix_ip_workflow_presets_is_active", "ip_workflow_presets")
    op.drop_index("ix_ip_workflow_presets_preset_type", "ip_workflow_presets")
    op.drop_index("ix_ip_workflow_presets_ip_id", "ip_workflow_presets")
    op.drop_table("ip_workflow_presets")

    # Drop ip_catalog
    op.drop_index("ix_ip_catalog_created_at", "ip_catalog")
    op.drop_index("ix_ip_catalog_license_status", "ip_catalog")
    op.drop_index("ix_ip_catalog_genre", "ip_catalog")
    op.drop_index("ix_ip_catalog_slug", "ip_catalog")
    op.drop_table("ip_catalog")
