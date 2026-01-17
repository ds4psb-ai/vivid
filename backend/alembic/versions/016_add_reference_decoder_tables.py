"""4D Reference Decoder: Add reference analysis tables.

Revision ID: 016_add_reference_decoder
Revises: 015_add_character_consistency
Create Date: 2026-01-18

Tables:
    - style_presets: Reusable visual styles extracted from references
    - reference_items: Uploaded references (video/image) with analysis
    - reference_scenes: Indexed scenes for RAG and cross-modal search
    - cinematography_techniques: Technique reference for RAG

References:
    - docs/research/02_REFERENCE_DECODER_RESEARCH.md
    - Expert Workflow: "스타일 프롬프트라고 따로 둬요"
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '016_add_reference_decoder'
down_revision = '015_add_character_consistency'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # Enable required extensions
    # ==========================================================================
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ==========================================================================
    # reference_items - Uploaded references with analysis results
    # (Created first as style_presets references this table)
    # ==========================================================================
    op.create_table(
        'reference_items',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),

        # Ownership
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),

        # Metadata
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.JSONB(), server_default='[]', nullable=False),

        # Media info
        sa.Column('reference_type', sa.String(20), nullable=False,
                  comment='video or image'),
        sa.Column('source_url', sa.String(2000), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True,
                  comment='Video duration in seconds'),
        sa.Column('thumbnail_url', sa.String(2000), nullable=True),

        # Analysis
        sa.Column('analysis_depth', sa.String(20), server_default='detailed', nullable=False,
                  comment='quick, detailed, comprehensive'),
        sa.Column('analysis_status', sa.String(20), server_default='pending', nullable=False,
                  comment='pending, processing, completed, failed'),
        sa.Column('analysis_result', postgresql.JSONB(), server_default='{}', nullable=False,
                  comment='VideoReferenceAnalysis or ImageReferenceAnalysis'),
        sa.Column('analysis_confidence', sa.Float(), nullable=True,
                  comment='Overall analysis confidence (0.0-1.0)'),

        # Moodboard
        sa.Column('moodboard_frames', postgresql.JSONB(), server_default='[]', nullable=False,
                  comment='Base64 encoded key frames for moodboard'),

        # Style extraction link (will be set after style is extracted)
        sa.Column('extracted_style_id', postgresql.UUID(as_uuid=True), nullable=True,
                  comment='Link to StylePreset extracted from this reference'),

        # Multimodal embedding references (Qdrant)
        sa.Column('qdrant_point_id', sa.String(100), nullable=True, unique=True,
                  comment='ImageBind/Vertex embedding in Qdrant'),

        # Evidence refs (RAG sources used in analysis)
        sa.Column('evidence_refs', postgresql.JSONB(), server_default='[]', nullable=False,
                  comment='["rag:cinematography:technique_id", "db:famous_scenes:scene_id"]'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now(), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(), nullable=True,
                  comment='When analysis was completed'),

        # Constraints
        sa.CheckConstraint(
            "reference_type IN ('video', 'image')",
            name='ck_reference_items_type'
        ),
        sa.CheckConstraint(
            "analysis_status IN ('pending', 'processing', 'completed', 'failed')",
            name='ck_reference_items_status'
        ),
    )

    # Indexes for reference_items
    op.create_index('ix_reference_items_user_project', 'reference_items',
                    ['user_id', 'project_id'])
    op.create_index('ix_reference_items_tags', 'reference_items',
                    ['tags'], postgresql_using='gin')
    op.create_index('ix_reference_items_type', 'reference_items', ['reference_type'])
    op.create_index('ix_reference_items_status', 'reference_items', ['analysis_status'])
    op.create_index('ix_reference_items_created', 'reference_items', ['created_at'])
    op.create_index('ix_reference_items_name_search', 'reference_items',
                    ['name'], postgresql_using='gin',
                    postgresql_ops={'name': 'gin_trgm_ops'})

    # ==========================================================================
    # style_presets - Reusable visual styles extracted from references
    # ==========================================================================
    op.create_table(
        'style_presets',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),

        # Ownership
        sa.Column('user_id', sa.String(255), nullable=False, index=True),

        # Metadata
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.JSONB(), server_default='[]', nullable=False,
                  comment='["anime", "cinematic", "neon-noir", ...]'),

        # Style data (Full StyleExtractionResult)
        sa.Column('style_data', postgresql.JSONB(), server_default='{}', nullable=False,
                  comment='Full StyleExtractionResult from style_extractor.py'),

        # Denormalized for fast filtering
        sa.Column('color_palette', postgresql.JSONB(), server_default='[]', nullable=False,
                  comment='["#FF5733", "#33FF57", ...] - dominant colors'),
        sa.Column('lighting', sa.String(50), nullable=True,
                  comment='dramatic, soft, neon, natural, etc.'),
        sa.Column('mood', sa.String(50), nullable=True,
                  comment='energetic, melancholic, mysterious, etc.'),

        # Preview
        sa.Column('thumbnail_url', sa.String(2000), nullable=True),

        # Source reference
        sa.Column('source_reference_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('reference_items.id', ondelete='SET NULL'),
                  nullable=True, index=True),

        # Sharing & usage
        sa.Column('is_public', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('usage_count', sa.Integer(), server_default='0', nullable=False),

        # Qdrant reference for style embedding
        sa.Column('qdrant_point_id', sa.String(100), nullable=True, unique=True,
                  comment='Qdrant point ID for style embedding vector'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now(), nullable=True),
    )

    # Indexes for style_presets (user_id already indexed via index=True)
    op.create_index('ix_style_presets_tags', 'style_presets',
                    ['tags'], postgresql_using='gin')
    op.create_index('ix_style_presets_lighting', 'style_presets', ['lighting'])
    op.create_index('ix_style_presets_mood', 'style_presets', ['mood'])
    op.create_index('ix_style_presets_public', 'style_presets', ['is_public'])
    op.create_index('ix_style_presets_name_search', 'style_presets',
                    ['name'], postgresql_using='gin',
                    postgresql_ops={'name': 'gin_trgm_ops'})

    # Add FK from reference_items.extracted_style_id to style_presets
    op.create_foreign_key(
        'fk_reference_items_extracted_style',
        'reference_items', 'style_presets',
        ['extracted_style_id'], ['id'],
        ondelete='SET NULL'
    )

    # ==========================================================================
    # reference_scenes - Indexed scenes for RAG and cross-modal search
    # ==========================================================================
    op.create_table(
        'reference_scenes',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),

        # Unique identifier
        sa.Column('scene_key', sa.String(200), unique=True, nullable=False,
                  comment='Unique key like "parasite_stairs_sequence"'),

        # Film metadata
        sa.Column('film_title', sa.String(300), nullable=False),
        sa.Column('film_year', sa.Integer(), nullable=True),
        sa.Column('director', sa.String(200), nullable=True, index=True),
        sa.Column('cinematographer', sa.String(200), nullable=True, index=True),

        # Scene info
        sa.Column('timestamp', sa.String(50), nullable=True,
                  comment='Timestamp range like "1:23:45 - 1:25:30"'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('thematic_significance', sa.Text(), nullable=True),

        # Analysis data
        sa.Column('cinematography', postgresql.JSONB(), server_default='{}', nullable=False,
                  comment='shot_types, movements, lens, composition, lighting'),
        sa.Column('color_analysis', postgresql.JSONB(), server_default='{}', nullable=False,
                  comment='dominant_colors, color_meaning, grading_style'),
        sa.Column('mise_en_scene', postgresql.JSONB(), server_default='{}', nullable=False,
                  comment='set_design, props, blocking, costume'),
        sa.Column('sound_design', postgresql.JSONB(), server_default='{}', nullable=False,
                  comment='diegetic, score, silence'),

        # Tags and categorization
        sa.Column('auteur_tags', postgresql.JSONB(), server_default='[]', nullable=False,
                  comment='["bong_joon_ho", "roger_deakins", ...]'),
        sa.Column('technique_tags', postgresql.JSONB(), server_default='[]', nullable=False,
                  comment='["dolly_zoom", "rembrandt_lighting", ...]'),
        sa.Column('mood_tags', postgresql.JSONB(), server_default='[]', nullable=False,
                  comment='["tense", "mysterious", "intimate", ...]'),
        sa.Column('genre_tags', postgresql.JSONB(), server_default='[]', nullable=False,
                  comment='["thriller", "drama", "noir", ...]'),

        # Recreation guide
        sa.Column('recreation_guide', postgresql.JSONB(), server_default='{}', nullable=False,
                  comment='key_elements, ai_prompt_suggestion, recommended_tool, difficulty'),

        # Preview
        sa.Column('thumbnail_url', sa.String(2000), nullable=True),
        sa.Column('video_clip_url', sa.String(2000), nullable=True),

        # Multimodal embedding (Qdrant)
        sa.Column('qdrant_point_id', sa.String(100), nullable=True, unique=True,
                  comment='ImageBind/Vertex embedding for cross-modal search'),

        # Source tracking
        sa.Column('source', sa.String(200), nullable=True,
                  comment='every_frame_a_painting, studiobinder, academic, etc.'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now(), nullable=True),
    )

    # Indexes for reference_scenes (director, cinematographer already indexed via index=True)
    op.create_index('ix_reference_scenes_film', 'reference_scenes', ['film_title'])
    op.create_index('ix_reference_scenes_year', 'reference_scenes', ['film_year'])
    op.create_index('ix_reference_scenes_auteur_tags', 'reference_scenes',
                    ['auteur_tags'], postgresql_using='gin')
    op.create_index('ix_reference_scenes_technique_tags', 'reference_scenes',
                    ['technique_tags'], postgresql_using='gin')
    op.create_index('ix_reference_scenes_mood_tags', 'reference_scenes',
                    ['mood_tags'], postgresql_using='gin')
    op.create_index('ix_reference_scenes_genre_tags', 'reference_scenes',
                    ['genre_tags'], postgresql_using='gin')
    op.create_index('ix_reference_scenes_description_search', 'reference_scenes',
                    ['description'], postgresql_using='gin',
                    postgresql_ops={'description': 'gin_trgm_ops'})

    # ==========================================================================
    # cinematography_techniques - Technique reference for RAG
    # ==========================================================================
    op.create_table(
        'cinematography_techniques',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),

        # Unique identifier
        sa.Column('technique_id', sa.String(100), unique=True, nullable=False,
                  comment='Unique key like "dolly_zoom"'),

        # Categorization
        sa.Column('category', sa.String(50), nullable=False, index=True,
                  comment='shot_type, camera_movement, lighting, composition, lens, color'),

        # Names
        sa.Column('name_en', sa.String(200), nullable=False),
        sa.Column('name_ko', sa.String(200), nullable=True),
        sa.Column('aliases', postgresql.JSONB(), server_default='[]', nullable=False,
                  comment='["Vertigo effect", "Zolly", "Contra-zoom"]'),

        # Description
        sa.Column('description', sa.Text(), nullable=False),

        # Effects and usage
        sa.Column('emotional_effect', postgresql.JSONB(), server_default='[]', nullable=False,
                  comment='["disorientation", "realization", "dread"]'),
        sa.Column('narrative_use', postgresql.JSONB(), server_default='[]', nullable=False,
                  comment='["character epiphany", "horror reveal"]'),

        # Examples
        sa.Column('famous_examples', postgresql.JSONB(), server_default='[]', nullable=False,
                  comment='[{film, scene, director, year, description}]'),

        # Execution details
        sa.Column('execution_details', postgresql.JSONB(), server_default='{}', nullable=False,
                  comment='equipment, difficulty, duration_typical'),

        # AI reproducibility
        sa.Column('ai_reproducibility', postgresql.JSONB(), server_default='{}', nullable=False,
                  comment='reproducible, platforms, prompt_keywords, limitations'),

        # Related techniques
        sa.Column('related_techniques', postgresql.JSONB(), server_default='[]', nullable=False,
                  comment='["push_in", "zoom_in", ...]'),

        # Source tracking
        sa.Column('source', sa.String(200), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now(), nullable=True),

        # Constraints
        sa.CheckConstraint(
            "category IN ('shot_type', 'camera_movement', 'lighting', 'composition', 'lens', 'color')",
            name='ck_cine_techniques_category'
        ),
    )

    # Indexes for cinematography_techniques (category already indexed via index=True)
    op.create_index('ix_cine_techniques_aliases', 'cinematography_techniques',
                    ['aliases'], postgresql_using='gin')
    op.create_index('ix_cine_techniques_emotional', 'cinematography_techniques',
                    ['emotional_effect'], postgresql_using='gin')
    op.create_index('ix_cine_techniques_narrative', 'cinematography_techniques',
                    ['narrative_use'], postgresql_using='gin')
    op.create_index('ix_cine_techniques_name_search', 'cinematography_techniques',
                    ['name_en'], postgresql_using='gin',
                    postgresql_ops={'name_en': 'gin_trgm_ops'})


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table('cinematography_techniques')
    op.drop_table('reference_scenes')

    # Drop FK constraint before dropping style_presets
    op.drop_constraint('fk_reference_items_extracted_style', 'reference_items', type_='foreignkey')

    op.drop_table('style_presets')
    op.drop_table('reference_items')
