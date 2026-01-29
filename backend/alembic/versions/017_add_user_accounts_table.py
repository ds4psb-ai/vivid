"""Add user_accounts table

Revision ID: 017_add_user_accounts
Revises: 016_add_reference_decoder_tables
Create Date: 2026-01-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '017_add_user_accounts'
down_revision: Union[str, None] = '016_add_reference_decoder_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    # user_accounts table
    if 'user_accounts' not in existing_tables:
        op.create_table(
            'user_accounts',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('user_id', sa.String(160), nullable=False),
            sa.Column('provider', sa.String(32), nullable=False),
            sa.Column('provider_user_id', sa.String(200), nullable=False),
            sa.Column('email', sa.String(255), nullable=False),
            sa.Column('name', sa.String(200), nullable=True),
            sa.Column('avatar_url', sa.String(400), nullable=True),
            sa.Column('role', sa.String(32), nullable=False, server_default='user'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('last_login_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint('user_id', name='uq_user_accounts_user_id'),
            sa.UniqueConstraint('provider', 'provider_user_id', name='uq_user_accounts_provider'),
            sa.UniqueConstraint('email', name='uq_user_accounts_email'),
        )
        op.create_index('ix_user_accounts_email', 'user_accounts', ['email'])
        op.create_index('ix_user_accounts_provider_user_id', 'user_accounts', ['provider', 'provider_user_id'])


def downgrade() -> None:
    op.drop_index('ix_user_accounts_provider_user_id', table_name='user_accounts')
    op.drop_index('ix_user_accounts_email', table_name='user_accounts')
    op.drop_table('user_accounts')
