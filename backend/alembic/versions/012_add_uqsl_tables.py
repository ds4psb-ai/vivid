"""UQSL: Add Universal Quality Selection Layer tables.

Revision ID: 012_add_uqsl
Revises: 011_add_rag_feedback
Create Date: 2026-01-16

Tables:
    - bandit_arms: Thompson Sampling Beta distribution parameters
    - uqsl_configs: App-level UQSL configuration
    - selection_history: Selection audit log for analytics
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
# Merge migration - combines both branches from 010_add_miniapp_submissions
revision = '012_add_uqsl'
down_revision = ('011_add_rag_feedback', '99fbecb5f034')  # Merge two heads
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # bandit_arms - Thompson Sampling Beta Distribution Parameters
    # ==========================================================================
    op.create_table(
        'bandit_arms',
        sa.Column('arm_id', sa.String(100), primary_key=True),
        sa.Column('arm_type', sa.String(50), nullable=False),  # backend, reranker, generation
        # Beta distribution parameters
        sa.Column('alpha', sa.Integer(), default=1, nullable=False),  # Success count + 1
        sa.Column('beta', sa.Integer(), default=1, nullable=False),   # Failure count + 1
        sa.Column('total_trials', sa.Integer(), default=0, nullable=False),
        sa.Column('last_reward', sa.Float(), nullable=True),
        # Metadata
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('enabled', sa.Boolean(), default=True, nullable=False),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for bandit_arms
    op.create_index('ix_bandit_arms_type', 'bandit_arms', ['arm_type'])
    op.create_index('ix_bandit_arms_enabled', 'bandit_arms', ['enabled'])

    # ==========================================================================
    # uqsl_configs - App-level UQSL Configuration
    # ==========================================================================
    op.create_table(
        'uqsl_configs',
        sa.Column('app_key', sa.String(100), primary_key=True),
        # Generation settings
        sa.Column('n_candidates', sa.Integer(), default=3, nullable=False),
        sa.Column('selection_strategy', sa.String(20), default='auto', nullable=False),
        # Quality weights (JSONB for flexibility)
        sa.Column('quality_weights', postgresql.JSONB(), default={
            'groundedness': 0.30,
            'relevance': 0.25,
            'coherence': 0.20,
            'creativity': 0.15,
            'safety': 0.10,
        }),
        # Bandit configuration
        sa.Column('bandit_arms', postgresql.ARRAY(sa.String()), default=[
            'backend:qdrant_hybrid',
            'backend:notebooklm',
        ]),
        # Tier and feature flags
        sa.Column('tier', sa.String(20), default='free', nullable=False),  # free, premium, dev
        sa.Column('enabled', sa.Boolean(), default=True, nullable=False),
        # Thresholds
        sa.Column('auto_threshold', sa.Float(), default=0.85),
        sa.Column('top_k_for_hitl', sa.Integer(), default=2),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for uqsl_configs
    op.create_index('ix_uqsl_configs_tier', 'uqsl_configs', ['tier'])
    op.create_index('ix_uqsl_configs_enabled', 'uqsl_configs', ['enabled'])

    # ==========================================================================
    # selection_history - Selection Audit Log
    # ==========================================================================
    op.create_table(
        'selection_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('app_key', sa.String(100), nullable=False),
        # Query information
        sa.Column('prompt_hash', sa.String(64), nullable=False),
        sa.Column('prompt_preview', sa.String(200), nullable=True),  # First 200 chars for debugging
        # Generation details
        sa.Column('n_candidates', sa.Integer(), nullable=False),
        sa.Column('candidates_data', postgresql.JSONB(), nullable=False),  # All candidate outputs
        sa.Column('quality_scores', postgresql.JSONB(), nullable=False),   # Per-candidate scores
        # Selection details
        sa.Column('selected_idx', sa.Integer(), nullable=False),
        sa.Column('selection_method', sa.String(20), nullable=False),  # auto, hitl, hybrid, llm_judge
        sa.Column('selection_confidence', sa.Float(), nullable=True),
        # Thompson Sampling tracking
        sa.Column('arms_used', postgresql.ARRAY(sa.String()), nullable=False),
        # User feedback (optional, updated later)
        sa.Column('user_feedback', sa.String(20), nullable=True),  # positive, negative
        sa.Column('feedback_timestamp', sa.DateTime(), nullable=True),
        # Performance metrics
        sa.Column('total_latency_ms', sa.Integer(), nullable=True),
        sa.Column('generation_latency_ms', sa.Integer(), nullable=True),
        sa.Column('evaluation_latency_ms', sa.Integer(), nullable=True),
        # Context
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('dimension', sa.String(10), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Indexes for selection_history
    op.create_index('ix_selection_history_app_key', 'selection_history', ['app_key'])
    op.create_index('ix_selection_history_prompt_hash', 'selection_history', ['prompt_hash'])
    op.create_index('ix_selection_history_user_id', 'selection_history', ['user_id'])
    op.create_index('ix_selection_history_created_at', 'selection_history', ['created_at'])
    op.create_index('ix_selection_history_selection_method', 'selection_history', ['selection_method'])
    op.create_index('ix_selection_history_user_feedback', 'selection_history', ['user_feedback'])
    # Composite index for analytics queries
    op.create_index(
        'ix_selection_history_app_method_feedback',
        'selection_history',
        ['app_key', 'selection_method', 'user_feedback']
    )

    # ==========================================================================
    # ensemble_comparisons - Ensemble++ 3-Way Comparison Results
    # ==========================================================================
    op.create_table(
        'ensemble_comparisons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('query_hash', sa.String(64), nullable=True),
        sa.Column('dimension', sa.String(10), nullable=True),
        sa.Column('auteur_key', sa.String(50), nullable=True),
        # 3-way results
        sa.Column('result_a', postgresql.JSONB(), nullable=False),      # Qdrant only
        sa.Column('result_b', postgresql.JSONB(), nullable=False),      # NotebookLM only
        sa.Column('result_ab', postgresql.JSONB(), nullable=False),     # Ensemble merged
        # Selection
        sa.Column('recommended', sa.String(2), nullable=False),         # a, b, ab
        sa.Column('user_selected', sa.String(2), nullable=True),        # a, b, ab, skip
        sa.Column('selection_match', sa.Boolean(), nullable=True),      # recommended == user_selected
        # Thompson Sampling snapshots
        sa.Column('arms_stats_before', postgresql.JSONB(), nullable=True),
        sa.Column('arms_stats_after', postgresql.JSONB(), nullable=True),
        # Context
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Indexes for ensemble_comparisons
    op.create_index('ix_ensemble_comparisons_query_hash', 'ensemble_comparisons', ['query_hash'])
    op.create_index('ix_ensemble_comparisons_dimension', 'ensemble_comparisons', ['dimension'])
    op.create_index('ix_ensemble_comparisons_auteur_key', 'ensemble_comparisons', ['auteur_key'])
    op.create_index('ix_ensemble_comparisons_recommended', 'ensemble_comparisons', ['recommended'])
    op.create_index('ix_ensemble_comparisons_created_at', 'ensemble_comparisons', ['created_at'])

    # ==========================================================================
    # Insert default bandit arms
    # ==========================================================================
    op.execute("""
        INSERT INTO bandit_arms (arm_id, arm_type, alpha, beta, total_trials, description, enabled)
        VALUES
            ('backend:qdrant_hybrid', 'backend', 1, 1, 0, 'Qdrant Hybrid Search (Vector + BM25)', true),
            ('backend:notebooklm', 'backend', 1, 1, 0, 'NotebookLM CDP (거장 DNA)', true),
            ('reranker:cross_encoder', 'reranker', 1, 1, 0, 'Cross-Encoder Reranker (BGE)', true),
            ('reranker:vertex', 'reranker', 1, 1, 0, 'Vertex AI Reranker', true),
            ('ensemble:ab', 'ensemble', 2, 1, 0, 'Ensemble A+B (NeurIPS 2025)', true)
        ON CONFLICT (arm_id) DO NOTHING
    """)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('ensemble_comparisons')
    op.drop_table('selection_history')
    op.drop_table('uqsl_configs')
    op.drop_table('bandit_arms')
