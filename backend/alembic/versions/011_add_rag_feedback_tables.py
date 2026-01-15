"""P6: Add RAG Feedback tables.

Revision ID: 011_add_rag_feedback
Revises: 010_add_miniapp_submissions
Create Date: 2026-01-15

Tables:
    - rag_responses: RAG 응답 저장 (피드백 연결용)
    - rag_feedbacks: 명시적/암시적 피드백 수집
    - rag_response_daily_stats: 일별 통계 집계
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '011_add_rag_feedback'
down_revision = '010_add_miniapp_submissions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # rag_responses - RAG 응답 저장
    # ==========================================================================
    op.create_table(
        'rag_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        # Query & Answer
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('query_hash', sa.String(64), nullable=True),
        sa.Column('answer', sa.Text(), nullable=True),
        # P5 Classification
        sa.Column('query_type', sa.String(50), nullable=True),
        sa.Column('classification_confidence', sa.Float(), nullable=True),
        sa.Column('classifier_used', sa.String(50), nullable=True),
        # Strategy & Execution
        sa.Column('strategy_used', sa.String(50), nullable=True),
        sa.Column('retrieval_skipped', sa.Boolean(), default=False),
        # Performance Metrics
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('retrieval_count', sa.Integer(), default=0),
        sa.Column('reranked', sa.Boolean(), default=False),
        sa.Column('rerank_latency_ms', sa.Integer(), nullable=True),
        sa.Column('crag_triggered', sa.Boolean(), default=False),
        sa.Column('grounded', sa.Boolean(), default=False),
        # Source Information
        sa.Column('sources', postgresql.JSONB(), nullable=True),
        sa.Column('source_scores', postgresql.JSONB(), nullable=True),
        # RRF Fusion Details
        sa.Column('rrf_enabled', sa.Boolean(), default=False),
        sa.Column('keyword_results_count', sa.Integer(), default=0),
        sa.Column('vector_results_count', sa.Integer(), default=0),
        # Context
        sa.Column('app_key', sa.String(100), nullable=True),
        sa.Column('dimension', sa.String(10), nullable=True),
        sa.Column('auteur_key', sa.String(50), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        # Error tracking
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('error_type', sa.String(100), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for rag_responses
    op.create_index('ix_rag_responses_query_hash', 'rag_responses', ['query_hash'])
    op.create_index('ix_rag_responses_app_key', 'rag_responses', ['app_key'])
    op.create_index('ix_rag_responses_user_id', 'rag_responses', ['user_id'])
    op.create_index('ix_rag_responses_query_type', 'rag_responses', ['query_type'])
    op.create_index('ix_rag_responses_created_at', 'rag_responses', ['created_at'])
    op.create_index('ix_rag_responses_strategy_used', 'rag_responses', ['strategy_used'])

    # ==========================================================================
    # rag_feedbacks - 피드백 수집
    # ==========================================================================
    op.create_table(
        'rag_feedbacks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('response_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Explicit Feedback
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('feedback_type', sa.String(20), nullable=True),
        sa.Column('user_comment', sa.Text(), nullable=True),
        # Implicit Feedback - Source interaction
        sa.Column('source_clicked', sa.Boolean(), default=False),
        sa.Column('clicked_source_id', sa.String(100), nullable=True),
        sa.Column('clicked_source_index', sa.Integer(), nullable=True),
        # Session behavior
        sa.Column('session_duration_ms', sa.Integer(), nullable=True),
        # Query reformulation
        sa.Column('query_reformulated', sa.Boolean(), default=False),
        sa.Column('reformulated_query', sa.Text(), nullable=True),
        sa.Column('time_to_reformulate_ms', sa.Integer(), nullable=True),
        # Text copy
        sa.Column('text_copied', sa.Boolean(), default=False),
        sa.Column('copied_length', sa.Integer(), nullable=True),
        # Event type
        sa.Column('implicit_event_type', sa.String(30), nullable=True),
        # Metadata
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('client_ip', sa.String(45), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['response_id'], ['rag_responses.id'], ondelete='CASCADE')
    )

    # Indexes for rag_feedbacks
    op.create_index('ix_rag_feedbacks_response_id', 'rag_feedbacks', ['response_id'])
    op.create_index('ix_rag_feedbacks_user_id', 'rag_feedbacks', ['user_id'])
    op.create_index('ix_rag_feedbacks_feedback_type', 'rag_feedbacks', ['feedback_type'])
    op.create_index('ix_rag_feedbacks_created_at', 'rag_feedbacks', ['created_at'])
    op.create_index('ix_rag_feedbacks_rating', 'rag_feedbacks', ['rating'])

    # ==========================================================================
    # rag_response_daily_stats - 일별 통계 집계
    # ==========================================================================
    op.create_table(
        'rag_response_daily_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stat_date', sa.DateTime(), nullable=False),
        sa.Column('app_key', sa.String(100), nullable=True),
        sa.Column('query_type', sa.String(50), nullable=True),
        sa.Column('strategy_used', sa.String(50), nullable=True),
        # Counts
        sa.Column('total_queries', sa.Integer(), default=0),
        sa.Column('skip_retrieval_count', sa.Integer(), default=0),
        sa.Column('crag_trigger_count', sa.Integer(), default=0),
        sa.Column('error_count', sa.Integer(), default=0),
        # Averages
        sa.Column('avg_latency_ms', sa.Float(), nullable=True),
        sa.Column('avg_retrieval_count', sa.Float(), nullable=True),
        sa.Column('avg_confidence', sa.Float(), nullable=True),
        # Feedback aggregates
        sa.Column('feedback_count', sa.Integer(), default=0),
        sa.Column('avg_rating', sa.Float(), nullable=True),
        sa.Column('thumbs_up_count', sa.Integer(), default=0),
        sa.Column('thumbs_down_count', sa.Integer(), default=0),
        # Implicit metrics
        sa.Column('source_click_rate', sa.Float(), nullable=True),
        sa.Column('reformulation_rate', sa.Float(), nullable=True),
        sa.Column('copy_rate', sa.Float(), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for rag_response_daily_stats
    op.create_index('ix_rag_daily_stats_date', 'rag_response_daily_stats', ['stat_date'])
    op.create_index('ix_rag_daily_stats_app_key', 'rag_response_daily_stats', ['app_key'])
    op.create_index('ix_rag_daily_stats_query_type', 'rag_response_daily_stats', ['query_type'])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('rag_response_daily_stats')
    op.drop_table('rag_feedbacks')
    op.drop_table('rag_responses')
