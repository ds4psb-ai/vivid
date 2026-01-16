"""Feature Flags & A/B Testing: Add experimentation infrastructure tables.

Revision ID: 013_add_feature_flags_ab_testing
Revises: 012_add_uqsl
Create Date: 2026-01-16

Tables:
    Feature Flags:
    - feature_flags: Feature flag definitions with targeting strategies
    - feature_flag_audits: Audit log for compliance

    A/B Testing:
    - experiments: Experiment definitions
    - experiment_variants: Variant configurations
    - experiment_exposures: User exposure tracking
    - experiment_conversions: Conversion events
    - experiment_results: Cached results for dashboard
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '013_add_feature_flags_ab_testing'
down_revision = '012_add_uqsl'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # FEATURE FLAGS
    # ==========================================================================

    # feature_flags - Feature flag definitions
    op.create_table(
        'feature_flags',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('flag_key', sa.String(255), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        # Status
        sa.Column('status', sa.String(20), nullable=False, default='active'),  # active, archived
        sa.Column('enabled', sa.Boolean(), nullable=False, default=False),
        # Targeting strategies (JSONB)
        sa.Column('strategies', postgresql.JSONB(), default={}, nullable=False),
        # Variants for multivariate flags
        sa.Column('variants', postgresql.JSONB(), default=[], nullable=False),
        sa.Column('default_variant', sa.String(100), default='off', nullable=False),
        # Metadata
        sa.Column('tags', postgresql.JSONB(), default=[], nullable=False),
        sa.Column('owner', sa.String(255), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for feature_flags
    op.create_index('ix_feature_flags_key', 'feature_flags', ['flag_key'])
    op.create_index('ix_feature_flags_status', 'feature_flags', ['status'])
    op.create_index('ix_feature_flags_enabled', 'feature_flags', ['enabled'])

    # feature_flag_audits - Audit log
    op.create_table(
        'feature_flag_audits',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('flag_id', sa.Integer(), sa.ForeignKey('feature_flags.id'), nullable=False),
        sa.Column('flag_key', sa.String(255), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),  # created, updated, enabled, disabled, archived
        sa.Column('changed_by', sa.String(255), nullable=True),
        sa.Column('changed_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('previous_state', postgresql.JSONB(), nullable=True),
        sa.Column('new_state', postgresql.JSONB(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
    )

    # Indexes for feature_flag_audits
    op.create_index('ix_feature_flag_audits_flag_key', 'feature_flag_audits', ['flag_key'])
    op.create_index('ix_feature_flag_audits_changed_at', 'feature_flag_audits', ['changed_at'])

    # ==========================================================================
    # A/B TESTING - EXPERIMENTS
    # ==========================================================================

    # experiments - Experiment definitions
    op.create_table(
        'experiments',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('experiment_key', sa.String(255), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('hypothesis', sa.Text(), nullable=True),
        # Status and timing
        sa.Column('status', sa.String(20), nullable=False, default='draft'),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        # Traffic allocation
        sa.Column('traffic_percentage', sa.Float(), default=100.0, nullable=False),
        # Metrics
        sa.Column('primary_metric', sa.String(255), nullable=False),
        sa.Column('secondary_metrics', postgresql.JSONB(), default=[], nullable=False),
        # Statistical settings
        sa.Column('min_sample_size', sa.Integer(), default=1000, nullable=False),
        sa.Column('confidence_level', sa.Float(), default=0.95, nullable=False),
        sa.Column('min_detectable_effect', sa.Float(), default=0.05, nullable=False),
        # Feature flag integration
        sa.Column('feature_flag_key', sa.String(255), nullable=True),
        # Metadata
        sa.Column('owner', sa.String(255), nullable=True),
        sa.Column('tags', postgresql.JSONB(), default=[], nullable=False),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for experiments
    op.create_index('ix_experiments_key', 'experiments', ['experiment_key'])
    op.create_index('ix_experiments_status', 'experiments', ['status'])

    # experiment_variants - Variant configurations
    op.create_table(
        'experiment_variants',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('experiment_id', sa.Integer(), sa.ForeignKey('experiments.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=False),  # Traffic weight 0-100
        sa.Column('payload', postgresql.JSONB(), default={}, nullable=False),
        sa.Column('is_control', sa.Boolean(), default=False, nullable=False),
        sa.UniqueConstraint('experiment_id', 'name', name='uq_experiment_variant'),
    )

    # Indexes for experiment_variants
    op.create_index('ix_experiment_variants_experiment', 'experiment_variants', ['experiment_id'])

    # experiment_exposures - User exposure tracking
    op.create_table(
        'experiment_exposures',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('experiment_id', sa.Integer(), sa.ForeignKey('experiments.id'), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('variant_name', sa.String(100), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('context', postgresql.JSONB(), default={}, nullable=False),
        sa.Column('pre_experiment_value', sa.Float(), nullable=True),  # For CUPED
        sa.UniqueConstraint('experiment_id', 'user_id', name='uq_experiment_user'),
    )

    # Indexes for experiment_exposures
    op.create_index('ix_experiment_exposures_user', 'experiment_exposures', ['user_id'])
    op.create_index('ix_experiment_exposures_variant', 'experiment_exposures', ['experiment_id', 'variant_name'])

    # experiment_conversions - Conversion events
    op.create_table(
        'experiment_conversions',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('experiment_id', sa.Integer(), sa.ForeignKey('experiments.id'), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('variant_name', sa.String(100), nullable=False),
        sa.Column('metric_name', sa.String(255), nullable=False),
        sa.Column('metric_value', sa.Float(), default=1.0, nullable=False),
        sa.Column('converted_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('attribution_window_hours', sa.Integer(), default=24, nullable=False),
    )

    # Indexes for experiment_conversions
    op.create_index('ix_experiment_conversions_user', 'experiment_conversions', ['user_id'])
    op.create_index('ix_experiment_conversions_metric', 'experiment_conversions', ['experiment_id', 'metric_name'])
    op.create_index('ix_experiment_conversions_variant', 'experiment_conversions', ['experiment_id', 'variant_name'])

    # experiment_results - Cached results for dashboard
    op.create_table(
        'experiment_results',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('experiment_id', sa.Integer(), sa.ForeignKey('experiments.id'), nullable=False),
        sa.Column('variant_name', sa.String(100), nullable=False),
        sa.Column('metric_name', sa.String(255), nullable=False),
        # Sample statistics
        sa.Column('sample_size', sa.Integer(), default=0, nullable=False),
        sa.Column('conversions', sa.Integer(), default=0, nullable=False),
        sa.Column('conversion_rate', sa.Float(), nullable=True),
        sa.Column('mean_value', sa.Float(), nullable=True),
        sa.Column('std_dev', sa.Float(), nullable=True),
        # Comparison to control
        sa.Column('relative_lift', sa.Float(), nullable=True),
        sa.Column('absolute_lift', sa.Float(), nullable=True),
        # Statistical significance
        sa.Column('p_value', sa.Float(), nullable=True),
        sa.Column('confidence_interval_lower', sa.Float(), nullable=True),
        sa.Column('confidence_interval_upper', sa.Float(), nullable=True),
        sa.Column('is_significant', sa.Boolean(), default=False, nullable=False),
        # Bayesian results
        sa.Column('probability_of_being_best', sa.Float(), nullable=True),
        sa.Column('expected_loss', sa.Float(), nullable=True),
        # Metadata
        sa.Column('computed_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('experiment_id', 'variant_name', 'metric_name', name='uq_experiment_result'),
    )

    # Indexes for experiment_results
    op.create_index('ix_experiment_results_experiment', 'experiment_results', ['experiment_id'])


def downgrade() -> None:
    # Drop A/B Testing tables
    op.drop_table('experiment_results')
    op.drop_table('experiment_conversions')
    op.drop_table('experiment_exposures')
    op.drop_table('experiment_variants')
    op.drop_table('experiments')

    # Drop Feature Flags tables
    op.drop_table('feature_flag_audits')
    op.drop_table('feature_flags')
