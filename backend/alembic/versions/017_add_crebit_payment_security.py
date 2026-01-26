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
    # Check if table exists first
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'crebit_applications')")
    )
    if not result.scalar():
        # Table doesn't exist, skip this migration
        return

    # Add columns (check if they already exist)
    inspector = sa.inspect(conn)
    existing_columns = [c['name'] for c in inspector.get_columns('crebit_applications')]

    if 'owner_id' not in existing_columns:
        op.add_column("crebit_applications", sa.Column("owner_id", sa.String(length=160), nullable=True))
    if 'confirm_token_hash' not in existing_columns:
        op.add_column("crebit_applications", sa.Column("confirm_token_hash", sa.String(length=64), nullable=True))
    if 'confirm_token_expires_at' not in existing_columns:
        op.add_column("crebit_applications", sa.Column("confirm_token_expires_at", sa.DateTime(), nullable=True))

    # Create index if not exists
    try:
        op.create_index(
            "ix_crebit_applications_owner_id",
            "crebit_applications",
            ["owner_id"],
            unique=False,
        )
    except Exception:
        pass  # Index might already exist

    # Create unique constraint if not exists
    try:
        op.create_unique_constraint(
            "uq_crebit_application_payment_id",
            "crebit_applications",
            ["payment_id"],
        )
    except Exception:
        pass  # Constraint might already exist


def downgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'crebit_applications')")
    )
    if not result.scalar():
        return

    try:
        op.drop_constraint("uq_crebit_application_payment_id", "crebit_applications", type_="unique")
    except Exception:
        pass
    try:
        op.drop_index("ix_crebit_applications_owner_id", table_name="crebit_applications")
    except Exception:
        pass
    try:
        op.drop_column("crebit_applications", "confirm_token_expires_at")
    except Exception:
        pass
    try:
        op.drop_column("crebit_applications", "confirm_token_hash")
    except Exception:
        pass
    try:
        op.drop_column("crebit_applications", "owner_id")
    except Exception:
        pass
