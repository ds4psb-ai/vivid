"""Update tool endpoints to dimension API

Revision ID: 008_update_dimension_endpoints
Revises: 007_add_tool_registry
Create Date: 2026-01-04

Updates tool endpoints from /api/teaching/* to /api/dimension/*
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008_update_dimension_endpoints'
down_revision = '007_add_tool_registry'
branch_labels = None
depends_on = None


# Endpoint mapping: old -> new
ENDPOINT_MIGRATION = {
    '/api/teaching/prompt/generate': '/api/dimension/1d/generate',
    '/api/teaching/storyboard/create': '/api/dimension/2d/create',
    '/api/teaching/image/generate': '/api/dimension/3d/generate',
    '/api/teaching/reference/analyze': '/api/dimension/4d/analyze',
}


def upgrade():
    """Update tool endpoints to new dimension API paths."""
    for old_endpoint, new_endpoint in ENDPOINT_MIGRATION.items():
        op.execute(
            f"""
            UPDATE tools 
            SET endpoint = '{new_endpoint}',
                updated_at = NOW()
            WHERE endpoint = '{old_endpoint}'
            """
        )


def downgrade():
    """Revert to old teaching API paths."""
    for old_endpoint, new_endpoint in ENDPOINT_MIGRATION.items():
        op.execute(
            f"""
            UPDATE tools 
            SET endpoint = '{old_endpoint}',
                updated_at = NOW()
            WHERE endpoint = '{new_endpoint}'
            """
        )
