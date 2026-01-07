"""Add constellation table

Revision ID: 009_add_constellation
Revises: d3c6bb6b9050
Create Date: 2026-01-06

Adds constellations table for multi-scene projects (별자리).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_add_constellation'
down_revision = 'd3c6bb6b9050'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create constellations table."""
    op.create_table(
        'constellations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('preset', sa.String(64), nullable=False, server_default='short_drama'),
        sa.Column('target_scene_count', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('shared_context', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('star_points', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('creator_id', sa.String(160), nullable=False),
        sa.Column('creator_name', sa.String(100), nullable=False, server_default='Anonymous'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('use_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create indexes
    op.create_index('ix_constellations_creator', 'constellations', ['creator_id'])
    op.create_index('ix_constellations_preset', 'constellations', ['preset'])
    op.create_index('ix_constellations_is_public', 'constellations', ['is_public'])
    op.create_index('ix_constellations_created_at', 'constellations', ['created_at'])


def downgrade() -> None:
    """Drop constellations table."""
    op.drop_index('ix_constellations_created_at', 'constellations')
    op.drop_index('ix_constellations_is_public', 'constellations')
    op.drop_index('ix_constellations_preset', 'constellations')
    op.drop_index('ix_constellations_creator', 'constellations')
    op.drop_table('constellations')
