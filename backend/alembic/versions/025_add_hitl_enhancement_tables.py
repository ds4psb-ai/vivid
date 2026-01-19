"""Phase 7: Add HITL Enhancement tables.

Revision ID: 025_add_hitl_enhancement
Revises: 024_remove_legacy_params_from_blackhole_templates
Create Date: 2026-01-20

Tables:
    - feedback_corrections: 부정 피드백 교정 추적
    - feedback_ingestions: 긍정 피드백 RAG 수집 추적
    - creator_anomaly_logs: 크리에이터 이상 탐지 기록

Columns Added:
    - workflow_checkpoints: confidence_score, auto_approved
    - rag_feedbacks: ingested_to_rag, correction_applied
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '025_add_hitl_enhancement'
down_revision = '024_remove_legacy_params_from_blackhole_templates'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # feedback_corrections - 부정 피드백 교정 추적
    # ==========================================================================
    op.create_table(
        'feedback_corrections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('response_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feedback_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Correction Details
        sa.Column('correction_type', sa.String(50), nullable=False),
        # source_flagged, cache_invalidated, crag_triggered
        sa.Column('original_query', sa.Text(), nullable=False),
        sa.Column('corrected_answer', sa.Text(), nullable=True),
        sa.Column('correction_reason', sa.Text(), nullable=True),
        # Metadata
        sa.Column('dimension', sa.String(10), nullable=True),
        sa.Column('auteur_key', sa.String(50), nullable=True),
        # Review Status
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['response_id'], ['rag_responses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['feedback_id'], ['rag_feedbacks.id'], ondelete='CASCADE'),
    )

    # Indexes for feedback_corrections
    op.create_index('ix_feedback_corrections_response_id', 'feedback_corrections', ['response_id'])
    op.create_index('ix_feedback_corrections_feedback_id', 'feedback_corrections', ['feedback_id'])
    op.create_index('ix_feedback_corrections_correction_type', 'feedback_corrections', ['correction_type'])
    op.create_index('ix_feedback_corrections_dimension', 'feedback_corrections', ['dimension'])
    op.create_index('ix_feedback_corrections_created_at', 'feedback_corrections', ['created_at'])

    # ==========================================================================
    # feedback_ingestions - 긍정 피드백 RAG 수집 추적
    # ==========================================================================
    op.create_table(
        'feedback_ingestions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feedback_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Qdrant Indexing
        sa.Column('dimension', sa.String(10), nullable=False),
        sa.Column('qdrant_point_id', sa.String(100), nullable=False),
        sa.Column('collection_name', sa.String(100), nullable=False),
        # Content Info
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('content_preview', sa.String(500), nullable=True),
        # Embedding Info
        sa.Column('embedding_model', sa.String(100), nullable=True),
        sa.Column('embedding_dim', sa.Integer(), nullable=True),
        # Metadata
        sa.Column('auteur_key', sa.String(50), nullable=True),
        sa.Column('user_validated', sa.Boolean(), default=True),
        # Timestamps
        sa.Column('ingested_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['feedback_id'], ['rag_feedbacks.id'], ondelete='CASCADE'),
    )

    # Indexes for feedback_ingestions
    op.create_index('ix_feedback_ingestions_feedback_id', 'feedback_ingestions', ['feedback_id'])
    op.create_index('ix_feedback_ingestions_dimension', 'feedback_ingestions', ['dimension'])
    op.create_index('ix_feedback_ingestions_qdrant_point_id', 'feedback_ingestions', ['qdrant_point_id'])
    op.create_index('ix_feedback_ingestions_collection_name', 'feedback_ingestions', ['collection_name'])
    op.create_index('ix_feedback_ingestions_ingested_at', 'feedback_ingestions', ['ingested_at'])

    # ==========================================================================
    # creator_anomaly_logs - 크리에이터 이상 탐지 기록
    # ==========================================================================
    op.create_table(
        'creator_anomaly_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        # Anomaly Details
        sa.Column('anomaly_type', sa.String(50), nullable=False),
        # rating_drop, revision_spike, delivery_delay, credit_anomaly
        sa.Column('severity', sa.String(20), nullable=False),
        # low, medium, high, critical
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('expected_range_low', sa.Float(), nullable=True),
        sa.Column('expected_range_high', sa.Float(), nullable=True),
        sa.Column('deviation_std', sa.Float(), nullable=True),
        # Context
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('context', postgresql.JSONB(), nullable=True),
        # Resolution
        sa.Column('resolved', sa.Boolean(), default=False),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        # Timestamps
        sa.Column('detected_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )

    # Indexes for creator_anomaly_logs
    op.create_index('ix_creator_anomaly_logs_creator_id', 'creator_anomaly_logs', ['creator_id'])
    op.create_index('ix_creator_anomaly_logs_anomaly_type', 'creator_anomaly_logs', ['anomaly_type'])
    op.create_index('ix_creator_anomaly_logs_severity', 'creator_anomaly_logs', ['severity'])
    op.create_index('ix_creator_anomaly_logs_resolved', 'creator_anomaly_logs', ['resolved'])
    op.create_index('ix_creator_anomaly_logs_detected_at', 'creator_anomaly_logs', ['detected_at'])

    # ==========================================================================
    # Add columns to workflow_checkpoints
    # ==========================================================================
    op.add_column(
        'workflow_checkpoints',
        sa.Column('confidence_score', sa.Float(), nullable=True),
    )
    op.add_column(
        'workflow_checkpoints',
        sa.Column('auto_approved', sa.Boolean(), default=False),
    )
    op.add_column(
        'workflow_checkpoints',
        sa.Column('approval_decision', sa.String(30), nullable=True),
    )
    op.add_column(
        'workflow_checkpoints',
        sa.Column('quality_rating', sa.Integer(), nullable=True),
    )

    # Index for new columns
    op.create_index('ix_workflow_checkpoints_auto_approved', 'workflow_checkpoints', ['auto_approved'])
    op.create_index('ix_workflow_checkpoints_confidence_score', 'workflow_checkpoints', ['confidence_score'])

    # ==========================================================================
    # Add columns to rag_feedbacks
    # ==========================================================================
    op.add_column(
        'rag_feedbacks',
        sa.Column('ingested_to_rag', sa.Boolean(), default=False),
    )
    op.add_column(
        'rag_feedbacks',
        sa.Column('correction_applied', sa.Boolean(), default=False),
    )
    op.add_column(
        'rag_feedbacks',
        sa.Column('processed_for_learning', sa.Boolean(), default=False),
    )
    op.add_column(
        'rag_feedbacks',
        sa.Column('learning_cycle_id', sa.String(100), nullable=True),
    )

    # Index for new columns
    op.create_index('ix_rag_feedbacks_ingested_to_rag', 'rag_feedbacks', ['ingested_to_rag'])
    op.create_index('ix_rag_feedbacks_correction_applied', 'rag_feedbacks', ['correction_applied'])
    op.create_index('ix_rag_feedbacks_processed_for_learning', 'rag_feedbacks', ['processed_for_learning'])


def downgrade() -> None:
    # Drop indexes from rag_feedbacks
    op.drop_index('ix_rag_feedbacks_processed_for_learning', table_name='rag_feedbacks')
    op.drop_index('ix_rag_feedbacks_correction_applied', table_name='rag_feedbacks')
    op.drop_index('ix_rag_feedbacks_ingested_to_rag', table_name='rag_feedbacks')

    # Drop columns from rag_feedbacks
    op.drop_column('rag_feedbacks', 'learning_cycle_id')
    op.drop_column('rag_feedbacks', 'processed_for_learning')
    op.drop_column('rag_feedbacks', 'correction_applied')
    op.drop_column('rag_feedbacks', 'ingested_to_rag')

    # Drop indexes from workflow_checkpoints
    op.drop_index('ix_workflow_checkpoints_confidence_score', table_name='workflow_checkpoints')
    op.drop_index('ix_workflow_checkpoints_auto_approved', table_name='workflow_checkpoints')

    # Drop columns from workflow_checkpoints
    op.drop_column('workflow_checkpoints', 'quality_rating')
    op.drop_column('workflow_checkpoints', 'approval_decision')
    op.drop_column('workflow_checkpoints', 'auto_approved')
    op.drop_column('workflow_checkpoints', 'confidence_score')

    # Drop tables in reverse order
    op.drop_table('creator_anomaly_logs')
    op.drop_table('feedback_ingestions')
    op.drop_table('feedback_corrections')
