"""Crebit payments: add owner + confirm token tracking.

Revision ID: 017_add_crebit_payment_security
Revises: 016_add_reference_decoder
Create Date: 2026-01-19
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "017_add_crebit_payment_security"
down_revision = "016_add_reference_decoder"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("crebit_applications", sa.Column("owner_id", sa.String(length=160), nullable=True))
    op.add_column("crebit_applications", sa.Column("confirm_token_hash", sa.String(length=64), nullable=True))
    op.add_column("crebit_applications", sa.Column("confirm_token_expires_at", sa.DateTime(), nullable=True))
    op.create_index(
        "ix_crebit_applications_owner_id",
        "crebit_applications",
        ["owner_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_crebit_application_payment_id",
        "crebit_applications",
        ["payment_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_crebit_application_payment_id", "crebit_applications", type_="unique")
    op.drop_index("ix_crebit_applications_owner_id", table_name="crebit_applications")
    op.drop_column("crebit_applications", "confirm_token_expires_at")
    op.drop_column("crebit_applications", "confirm_token_hash")
    op.drop_column("crebit_applications", "owner_id")
