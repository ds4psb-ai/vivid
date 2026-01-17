"""Character Consistency: Add StoryMem character tables.

Revision ID: 015_add_character_consistency
Revises: 014_add_mcp_tables
Create Date: 2026-01-17

Tables:
    - characters: Character metadata and StoryMem memory bank
    - character_appearances: Shot-level character tracking

References:
    - StoryMem Paper: arXiv:2512.19539
    - DIMENSION_APP_MACRO_PLANNING_2026.md Part 11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '015_add_character_consistency'
down_revision = '014_add_mcp_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # Enable required extensions
    # ==========================================================================
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ==========================================================================
    # characters - Core character entity with StoryMem memory bank
    # ==========================================================================
    op.create_table(
        'characters',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),

        # Ownership
        sa.Column('user_id', sa.String(255), sa.ForeignKey('users.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('projects.id', ondelete='SET NULL'),
                  nullable=True, index=True),

        # Metadata
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.JSONB(), server_default='[]', nullable=False,
                  comment='["protagonist", "human", "female"]'),

        # Reference images
        sa.Column('source_images', postgresql.JSONB(), server_default='[]', nullable=False,
                  comment='[{url, timestamp, quality_score, is_primary}]'),
        sa.Column('primary_image_url', sa.String(2000), nullable=True),

        # Qdrant reference (embeddings stored externally)
        sa.Column('qdrant_point_id', sa.String(100), nullable=True, unique=True,
                  comment='Qdrant point ID for face/clip/style embeddings'),

        # Platform-specific references
        sa.Column('platform_refs', postgresql.JSONB(), server_default='{}', nullable=False,
                  comment='{"veo": {ref_id, last_sync, ...}, "kling": {...}}'),

        # StoryMem Memory Bank
        sa.Column('memory_keyframes', postgresql.JSONB(), server_default='[]', nullable=False,
                  comment='StoryMem keyframes: [{frame_url, timestamp, clip_score, hps_score, face_confidence, is_long_term}]'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now(), nullable=True),
    )

    # Indexes for characters
    op.create_index('ix_characters_user_project', 'characters', ['user_id', 'project_id'])
    op.create_index('ix_characters_tags', 'characters', ['tags'], postgresql_using='gin')
    op.create_index('ix_characters_name_search', 'characters', ['name'],
                    postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'})
    op.create_index('ix_characters_created_at', 'characters', ['created_at'])
    op.create_index('ix_characters_qdrant_point', 'characters', ['qdrant_point_id'])

    # ==========================================================================
    # character_appearances - Shot-level character tracking
    # ==========================================================================
    op.create_table(
        'character_appearances',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),

        # References
        sa.Column('character_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('characters.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('shot_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('shots.id', ondelete='SET NULL'),
                  nullable=True, index=True),
        sa.Column('video_generation_id', postgresql.UUID(as_uuid=True),
                  nullable=True, index=True),

        # Appearance context
        sa.Column('scene_description', sa.Text(), nullable=True),
        sa.Column('pose_description', sa.String(200), nullable=True),
        sa.Column('emotion', sa.String(50), nullable=True),

        # Quality metrics
        sa.Column('consistency_score', sa.Float(), nullable=True,
                  comment='Auto-computed CLIP/Face similarity (0.0-1.0)'),
        sa.Column('user_rating', sa.Integer(), nullable=True,
                  comment='User feedback (1-5 stars)'),

        # Generated frame reference
        sa.Column('generated_frame_url', sa.String(2000), nullable=True,
                  comment='Best frame from this appearance'),

        # Embedding snapshot (for consistency analysis)
        sa.Column('face_embedding_snapshot', postgresql.ARRAY(sa.Float()), nullable=True,
                  comment='512D ArcFace embedding at generation time'),
        sa.Column('clip_embedding_snapshot', postgresql.ARRAY(sa.Float()), nullable=True,
                  comment='768D CLIP embedding at generation time'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Indexes for character_appearances
    op.create_index('ix_appearances_character_video', 'character_appearances',
                    ['character_id', 'video_generation_id'])
    op.create_index('ix_appearances_consistency_score', 'character_appearances',
                    ['consistency_score'])
    op.create_index('ix_appearances_created_at', 'character_appearances',
                    ['created_at'])

    # ==========================================================================
    # character_platform_syncs - Platform sync history (audit log)
    # ==========================================================================
    op.create_table(
        'character_platform_syncs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('character_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('characters.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('platform', sa.String(20), nullable=False),  # veo, kling, runway, hailuo
        sa.Column('status', sa.String(20), nullable=False),    # success, failed, pending
        sa.Column('platform_ref_id', sa.String(255), nullable=True),
        sa.Column('style_strength', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Indexes for character_platform_syncs
    op.create_index('ix_platform_syncs_character_platform', 'character_platform_syncs',
                    ['character_id', 'platform'])
    op.create_index('ix_platform_syncs_status', 'character_platform_syncs', ['status'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('character_platform_syncs')
    op.drop_table('character_appearances')
    op.drop_table('characters')
