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
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    def get_columns(table_name):
        """Get column names for a table."""
        if table_name not in existing_tables:
            return []
        return [c['name'] for c in inspector.get_columns(table_name)]

    def get_indexes(table_name):
        """Get index names for a table."""
        if table_name not in existing_tables:
            return []
        return [idx['name'] for idx in inspector.get_indexes(table_name)]

    # ==========================================================================
    # feedback_corrections - 부정 피드백 교정 추적
    # ==========================================================================
    if 'rag_responses' not in existing_tables or 'rag_feedbacks' not in existing_tables:
        print("[SKIP] feedback_corrections - dependent tables (rag_responses, rag_feedbacks) not found")
    elif 'feedback_corrections' in existing_tables:
        print("[SKIP] feedback_corrections already exists")
    else:
        op.create_table(
            'feedback_corrections',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('response_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('feedback_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('correction_type', sa.String(50), nullable=False),
            sa.Column('original_query', sa.Text(), nullable=False),
            sa.Column('corrected_answer', sa.Text(), nullable=True),
            sa.Column('correction_reason', sa.Text(), nullable=True),
            sa.Column('dimension', sa.String(10), nullable=True),
            sa.Column('auteur_key', sa.String(50), nullable=True),
            sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['response_id'], ['rag_responses.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['feedback_id'], ['rag_feedbacks.id'], ondelete='CASCADE'),
        )
        op.create_index('ix_feedback_corrections_response_id', 'feedback_corrections', ['response_id'])
        op.create_index('ix_feedback_corrections_feedback_id', 'feedback_corrections', ['feedback_id'])
        op.create_index('ix_feedback_corrections_correction_type', 'feedback_corrections', ['correction_type'])
        op.create_index('ix_feedback_corrections_dimension', 'feedback_corrections', ['dimension'])
        op.create_index('ix_feedback_corrections_created_at', 'feedback_corrections', ['created_at'])

    # ==========================================================================
    # feedback_ingestions - 긍정 피드백 RAG 수집 추적
    # ==========================================================================
    if 'rag_feedbacks' not in existing_tables:
        print("[SKIP] feedback_ingestions - dependent table (rag_feedbacks) not found")
    elif 'feedback_ingestions' in existing_tables:
        print("[SKIP] feedback_ingestions already exists")
    else:
        op.create_table(
            'feedback_ingestions',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('feedback_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('dimension', sa.String(10), nullable=False),
            sa.Column('qdrant_point_id', sa.String(100), nullable=False),
            sa.Column('collection_name', sa.String(100), nullable=False),
            sa.Column('content_hash', sa.String(64), nullable=True),
            sa.Column('content_preview', sa.String(500), nullable=True),
            sa.Column('embedding_model', sa.String(100), nullable=True),
            sa.Column('embedding_dim', sa.Integer(), nullable=True),
            sa.Column('auteur_key', sa.String(50), nullable=True),
            sa.Column('user_validated', sa.Boolean(), default=True),
            sa.Column('ingested_at', sa.DateTime(), server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['feedback_id'], ['rag_feedbacks.id'], ondelete='CASCADE'),
        )
        op.create_index('ix_feedback_ingestions_feedback_id', 'feedback_ingestions', ['feedback_id'])
        op.create_index('ix_feedback_ingestions_dimension', 'feedback_ingestions', ['dimension'])
        op.create_index('ix_feedback_ingestions_qdrant_point_id', 'feedback_ingestions', ['qdrant_point_id'])
        op.create_index('ix_feedback_ingestions_collection_name', 'feedback_ingestions', ['collection_name'])
        op.create_index('ix_feedback_ingestions_ingested_at', 'feedback_ingestions', ['ingested_at'])

    # ==========================================================================
    # creator_anomaly_logs - 크리에이터 이상 탐지 기록
    # ==========================================================================
    if 'creator_anomaly_logs' in existing_tables:
        print("[SKIP] creator_anomaly_logs already exists")
    else:
        op.create_table(
            'creator_anomaly_logs',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('anomaly_type', sa.String(50), nullable=False),
            sa.Column('severity', sa.String(20), nullable=False),
            sa.Column('metric_name', sa.String(100), nullable=False),
            sa.Column('metric_value', sa.Float(), nullable=False),
            sa.Column('expected_range_low', sa.Float(), nullable=True),
            sa.Column('expected_range_high', sa.Float(), nullable=True),
            sa.Column('deviation_std', sa.Float(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('context', postgresql.JSONB(), nullable=True),
            sa.Column('resolved', sa.Boolean(), default=False),
            sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('resolution_notes', sa.Text(), nullable=True),
            sa.Column('detected_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_creator_anomaly_logs_creator_id', 'creator_anomaly_logs', ['creator_id'])
        op.create_index('ix_creator_anomaly_logs_anomaly_type', 'creator_anomaly_logs', ['anomaly_type'])
        op.create_index('ix_creator_anomaly_logs_severity', 'creator_anomaly_logs', ['severity'])
        op.create_index('ix_creator_anomaly_logs_resolved', 'creator_anomaly_logs', ['resolved'])
        op.create_index('ix_creator_anomaly_logs_detected_at', 'creator_anomaly_logs', ['detected_at'])

    # ==========================================================================
    # Add columns to workflow_checkpoints (idempotent)
    # ==========================================================================
    if 'workflow_checkpoints' not in existing_tables:
        print("[SKIP] workflow_checkpoints table not found")
    else:
        wc_columns = get_columns('workflow_checkpoints')
        wc_indexes = get_indexes('workflow_checkpoints')

        if 'confidence_score' not in wc_columns:
            op.add_column('workflow_checkpoints', sa.Column('confidence_score', sa.Float(), nullable=True))
        if 'auto_approved' not in wc_columns:
            op.add_column('workflow_checkpoints', sa.Column('auto_approved', sa.Boolean(), default=False))
        if 'approval_decision' not in wc_columns:
            op.add_column('workflow_checkpoints', sa.Column('approval_decision', sa.String(30), nullable=True))
        if 'quality_rating' not in wc_columns:
            op.add_column('workflow_checkpoints', sa.Column('quality_rating', sa.Integer(), nullable=True))

        if 'ix_workflow_checkpoints_auto_approved' not in wc_indexes:
            op.create_index('ix_workflow_checkpoints_auto_approved', 'workflow_checkpoints', ['auto_approved'])
        if 'ix_workflow_checkpoints_confidence_score' not in wc_indexes:
            op.create_index('ix_workflow_checkpoints_confidence_score', 'workflow_checkpoints', ['confidence_score'])

    # ==========================================================================
    # Add columns to rag_feedbacks (idempotent)
    # ==========================================================================
    if 'rag_feedbacks' not in existing_tables:
        print("[SKIP] rag_feedbacks table not found")
    else:
        rf_columns = get_columns('rag_feedbacks')
        rf_indexes = get_indexes('rag_feedbacks')

        if 'ingested_to_rag' not in rf_columns:
            op.add_column('rag_feedbacks', sa.Column('ingested_to_rag', sa.Boolean(), default=False))
        if 'correction_applied' not in rf_columns:
            op.add_column('rag_feedbacks', sa.Column('correction_applied', sa.Boolean(), default=False))
        if 'processed_for_learning' not in rf_columns:
            op.add_column('rag_feedbacks', sa.Column('processed_for_learning', sa.Boolean(), default=False))
        if 'learning_cycle_id' not in rf_columns:
            op.add_column('rag_feedbacks', sa.Column('learning_cycle_id', sa.String(100), nullable=True))

        if 'ix_rag_feedbacks_ingested_to_rag' not in rf_indexes:
            op.create_index('ix_rag_feedbacks_ingested_to_rag', 'rag_feedbacks', ['ingested_to_rag'])
        if 'ix_rag_feedbacks_correction_applied' not in rf_indexes:
            op.create_index('ix_rag_feedbacks_correction_applied', 'rag_feedbacks', ['correction_applied'])
        if 'ix_rag_feedbacks_processed_for_learning' not in rf_indexes:
            op.create_index('ix_rag_feedbacks_processed_for_learning', 'rag_feedbacks', ['processed_for_learning'])


def downgrade() -> None:
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    def get_indexes(table_name):
        if table_name not in existing_tables:
            return []
        return [idx['name'] for idx in inspector.get_indexes(table_name)]

    # Drop indexes from rag_feedbacks (if they exist)
    if 'rag_feedbacks' in existing_tables:
        rf_indexes = get_indexes('rag_feedbacks')
        if 'ix_rag_feedbacks_processed_for_learning' in rf_indexes:
            op.drop_index('ix_rag_feedbacks_processed_for_learning', table_name='rag_feedbacks')
        if 'ix_rag_feedbacks_correction_applied' in rf_indexes:
            op.drop_index('ix_rag_feedbacks_correction_applied', table_name='rag_feedbacks')
        if 'ix_rag_feedbacks_ingested_to_rag' in rf_indexes:
            op.drop_index('ix_rag_feedbacks_ingested_to_rag', table_name='rag_feedbacks')

        # Drop columns
        try:
            op.drop_column('rag_feedbacks', 'learning_cycle_id')
            op.drop_column('rag_feedbacks', 'processed_for_learning')
            op.drop_column('rag_feedbacks', 'correction_applied')
            op.drop_column('rag_feedbacks', 'ingested_to_rag')
        except Exception:
            pass

    # Drop indexes from workflow_checkpoints (if they exist)
    if 'workflow_checkpoints' in existing_tables:
        wc_indexes = get_indexes('workflow_checkpoints')
        if 'ix_workflow_checkpoints_confidence_score' in wc_indexes:
            op.drop_index('ix_workflow_checkpoints_confidence_score', table_name='workflow_checkpoints')
        if 'ix_workflow_checkpoints_auto_approved' in wc_indexes:
            op.drop_index('ix_workflow_checkpoints_auto_approved', table_name='workflow_checkpoints')

        # Drop columns
        try:
            op.drop_column('workflow_checkpoints', 'quality_rating')
            op.drop_column('workflow_checkpoints', 'approval_decision')
            op.drop_column('workflow_checkpoints', 'auto_approved')
            op.drop_column('workflow_checkpoints', 'confidence_score')
        except Exception:
            pass

    # Drop tables (if they exist)
    if 'creator_anomaly_logs' in existing_tables:
        op.drop_table('creator_anomaly_logs')
    if 'feedback_ingestions' in existing_tables:
        op.drop_table('feedback_ingestions')
    if 'feedback_corrections' in existing_tables:
        op.drop_table('feedback_corrections')
