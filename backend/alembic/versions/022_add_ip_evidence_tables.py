"""Add IP evidence tables.

Revision ID: 022_add_ip_evidence_tables
Revises: 021_link_workflow_to_ip
Create Date: 2026-01-19

SSoT Decision (SSoT-DEC-002):
- New table names: ip_evidence_logs, ip_evidence_chains
- Avoid conflict with existing evidence_logs table
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "022_add_ip_evidence_tables"
down_revision = "021_link_workflow_to_ip"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ip_evidence_logs table
    op.create_table(
        "ip_evidence_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "generation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ip_generations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "execution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_executions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "node_result_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_node_results.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source", sa.String(32), default="capsule_run"),
        sa.Column("ref_string", sa.String(500), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("confidence", sa.Float, default=0.0),
        sa.Column("relevance_score", sa.Float, default=0.0),
        sa.Column("quality_score", sa.Float, default=0.0),
        sa.Column("status", sa.String(32), default="pending"),
        sa.Column(
            "extra_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("raw_content", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index(
        "ix_ip_evidence_logs_generation_id",
        "ip_evidence_logs",
        ["generation_id"],
    )
    op.create_index(
        "ix_ip_evidence_logs_execution_id",
        "ip_evidence_logs",
        ["execution_id"],
    )
    op.create_index(
        "ix_ip_evidence_logs_source",
        "ip_evidence_logs",
        ["source"],
    )
    op.create_index(
        "ix_ip_evidence_logs_created_at",
        "ip_evidence_logs",
        ["created_at"],
    )

    # ip_evidence_chains table
    op.create_table(
        "ip_evidence_chains",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "generation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ip_generations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "execution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_executions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("chain_type", sa.String(32), default="sequential"),
        sa.Column(
            "evidence_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("total_confidence", sa.Float, default=0.0),
        sa.Column("verified", sa.Boolean, default=False),
        sa.Column("verified_by", sa.String(160), nullable=True),
        sa.Column("verified_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index(
        "ix_ip_evidence_chains_generation_id",
        "ip_evidence_chains",
        ["generation_id"],
    )
    op.create_index(
        "ix_ip_evidence_chains_execution_id",
        "ip_evidence_chains",
        ["execution_id"],
    )
    op.create_index(
        "ix_ip_evidence_chains_created_at",
        "ip_evidence_chains",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_ip_evidence_chains_created_at", table_name="ip_evidence_chains")
    op.drop_index("ix_ip_evidence_chains_execution_id", table_name="ip_evidence_chains")
    op.drop_index("ix_ip_evidence_chains_generation_id", table_name="ip_evidence_chains")
    op.drop_table("ip_evidence_chains")

    op.drop_index("ix_ip_evidence_logs_created_at", table_name="ip_evidence_logs")
    op.drop_index("ix_ip_evidence_logs_source", table_name="ip_evidence_logs")
    op.drop_index("ix_ip_evidence_logs_execution_id", table_name="ip_evidence_logs")
    op.drop_index("ix_ip_evidence_logs_generation_id", table_name="ip_evidence_logs")
    op.drop_table("ip_evidence_logs")
