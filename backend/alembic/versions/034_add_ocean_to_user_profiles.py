"""Add OCEAN (Big Five) columns to user_preference_profiles.

Revision ID: 034_add_ocean
Revises: 033_create_outlier_items_with_hook_attrs
Create Date: 2026-01-27

Big Five Personality Model (OCEAN):
- Openness: Creativity, curiosity, openness to experience
- Conscientiousness: Organization, dependability, self-discipline
- Extraversion: Sociability, assertiveness, positive emotions
- Agreeableness: Cooperation, trust, altruism
- Neuroticism: Emotional instability, anxiety, moodiness

Values range from 0.0 to 1.0, default 0.5 (neutral).
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "034_add_ocean"
down_revision = "033_create_outlier_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add OCEAN columns to user_preference_profiles
    op.add_column(
        "user_preference_profiles",
        sa.Column("openness", sa.Float(), nullable=True, server_default="0.5"),
    )
    op.add_column(
        "user_preference_profiles",
        sa.Column("conscientiousness", sa.Float(), nullable=True, server_default="0.5"),
    )
    op.add_column(
        "user_preference_profiles",
        sa.Column("extraversion", sa.Float(), nullable=True, server_default="0.5"),
    )
    op.add_column(
        "user_preference_profiles",
        sa.Column("agreeableness", sa.Float(), nullable=True, server_default="0.5"),
    )
    op.add_column(
        "user_preference_profiles",
        sa.Column("neuroticism", sa.Float(), nullable=True, server_default="0.5"),
    )
    op.add_column(
        "user_preference_profiles",
        sa.Column("last_ocean_update", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_preference_profiles", "last_ocean_update")
    op.drop_column("user_preference_profiles", "neuroticism")
    op.drop_column("user_preference_profiles", "agreeableness")
    op.drop_column("user_preference_profiles", "extraversion")
    op.drop_column("user_preference_profiles", "conscientiousness")
    op.drop_column("user_preference_profiles", "openness")
