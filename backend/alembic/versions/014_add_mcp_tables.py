"""MCP Integration: Add MCP Gateway tables for Phase 4.

Revision ID: 014_add_mcp_tables
Revises: 013_add_feature_flags_ab_testing
Create Date: 2026-01-16

Tables:
    - mcp_audit_logs: MCP 호출 감사 로그 (compliance-ready)
    - mcp_policies: MCP 접근 정책
    - mcp_user_policies: 사용자-정책 매핑
    - mcp_server_configs: DB 기반 서버 설정 (선택)
    - mcp_rate_limit_states: Rate limit 상태 백업
    - mcp_tool_usage_stats: 도구 사용 통계 집계

2026 Best Practices:
    - MCP Gateway Pattern (centralized auth/audit/policy)
    - Streamable HTTP transport support
    - Comprehensive audit logging for compliance
    - Policy-based access control
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '014_add_mcp_tables'
down_revision = '013_add_feature_flags_ab_testing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # MCP AUDIT LOGS - Compliance-ready call logging
    # ==========================================================================

    op.create_table(
        'mcp_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        # Request identification
        sa.Column('request_id', sa.String(32), nullable=False),
        sa.Column('user_id', sa.String(160), nullable=False),
        # MCP call details
        sa.Column('server_id', sa.String(64), nullable=False),
        sa.Column('action', sa.String(32), nullable=False),
        sa.Column('tool_name', sa.String(128), nullable=True),
        # Security (hashed arguments)
        sa.Column('arguments_hash', sa.String(64), nullable=True),
        sa.Column('arguments_preview', postgresql.JSONB(), nullable=True),
        # Result
        sa.Column('success', sa.Boolean(), nullable=False, default=False),
        sa.Column('result_summary', sa.Text(), nullable=True),
        sa.Column('error_code', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        # Performance
        sa.Column('latency_ms', sa.Float(), nullable=False, default=0.0),
        # Economics
        sa.Column('credit_cost', sa.Integer(), nullable=False, default=0),
        sa.Column('run_token', sa.String(64), nullable=True),
        # Context
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(256), nullable=True),
        sa.Column('policy_applied', sa.String(64), nullable=True),
        # Extra metadata (named 'extra' to avoid SQLAlchemy reserved word)
        sa.Column('extra', postgresql.JSONB(), nullable=True),
    )

    # Indexes for mcp_audit_logs (optimized for common queries)
    op.create_index('ix_mcp_audit_user_time', 'mcp_audit_logs', ['user_id', 'timestamp'])
    op.create_index('ix_mcp_audit_server_time', 'mcp_audit_logs', ['server_id', 'timestamp'])
    op.create_index('ix_mcp_audit_success_time', 'mcp_audit_logs', ['success', 'timestamp'])
    op.create_index('ix_mcp_audit_request_id', 'mcp_audit_logs', ['request_id'])
    op.create_index('ix_mcp_audit_action', 'mcp_audit_logs', ['action'])
    op.create_index('ix_mcp_audit_timestamp', 'mcp_audit_logs', ['timestamp'])

    # ==========================================================================
    # MCP POLICIES - Access control policies
    # ==========================================================================

    op.create_table(
        'mcp_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('policy_id', sa.String(64), unique=True, nullable=False),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        # Access Control (arrays)
        sa.Column('allowed_servers', postgresql.ARRAY(sa.String()), default=[], nullable=False),
        sa.Column('denied_servers', postgresql.ARRAY(sa.String()), default=[], nullable=False),
        sa.Column('allowed_tools', postgresql.ARRAY(sa.String()), default=[], nullable=False),
        sa.Column('denied_tools', postgresql.ARRAY(sa.String()), default=[], nullable=False),
        # Rate Limits
        sa.Column('max_calls_per_minute', sa.Integer(), nullable=False, default=30),
        sa.Column('max_calls_per_hour', sa.Integer(), nullable=False, default=500),
        sa.Column('max_calls_per_day', sa.Integer(), nullable=False, default=5000),
        # Credit Limits
        sa.Column('max_credit_per_call', sa.Integer(), nullable=False, default=100),
        sa.Column('max_credit_per_day', sa.Integer(), nullable=False, default=10000),
        # Time Restrictions
        sa.Column('allowed_hours_start', sa.Integer(), nullable=False, default=0),
        sa.Column('allowed_hours_end', sa.Integer(), nullable=False, default=24),
        # Security
        sa.Column('require_run_token', sa.Boolean(), nullable=False, default=False),
        sa.Column('audit_level', sa.String(16), nullable=False, default='basic'),
        # Status and Priority
        sa.Column('status', sa.String(16), nullable=False, default='active'),
        sa.Column('priority', sa.Integer(), nullable=False, default=0),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(160), nullable=True),
    )

    # Indexes for mcp_policies
    op.create_index('ix_mcp_policies_status', 'mcp_policies', ['status'])
    op.create_index('ix_mcp_policies_priority', 'mcp_policies', ['priority'])

    # ==========================================================================
    # MCP USER POLICIES - User to policy mapping
    # ==========================================================================

    op.create_table(
        'mcp_user_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(160), unique=True, nullable=False),
        sa.Column('policy_id', sa.String(64), sa.ForeignKey('mcp_policies.policy_id', ondelete='CASCADE'), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('assigned_by', sa.String(160), nullable=True),
    )

    # Indexes for mcp_user_policies
    op.create_index('ix_mcp_user_policies_user', 'mcp_user_policies', ['user_id'], unique=True)

    # ==========================================================================
    # MCP SERVER CONFIGS - DB-based server configuration (optional)
    # ==========================================================================

    op.create_table(
        'mcp_server_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('server_id', sa.String(64), unique=True, nullable=False),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        # Transport
        sa.Column('transport', sa.String(32), nullable=False, default='streamable_http'),
        sa.Column('url', sa.String(512), nullable=True),
        sa.Column('command', sa.String(512), nullable=True),
        sa.Column('args', postgresql.ARRAY(sa.String()), default=[], nullable=False),
        sa.Column('env', postgresql.JSONB(), nullable=True),
        # Authentication (encrypted in production)
        sa.Column('auth_type', sa.String(32), nullable=True),
        sa.Column('auth_config_encrypted', sa.Text(), nullable=True),
        # Timeouts and Limits
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, default=30),
        sa.Column('max_retries', sa.Integer(), nullable=False, default=3),
        sa.Column('retry_delay_ms', sa.Integer(), nullable=False, default=1000),
        sa.Column('circuit_breaker_threshold', sa.Integer(), nullable=False, default=5),
        sa.Column('rate_limit_rpm', sa.Integer(), nullable=False, default=60),
        # Tier and Economics
        sa.Column('tier', sa.String(16), nullable=False, default='core'),
        sa.Column('credit_cost', sa.Integer(), nullable=False, default=1),
        # Status
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        # Extra metadata (named 'extra' to avoid SQLAlchemy reserved word)
        sa.Column('extra', postgresql.JSONB(), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for mcp_server_configs
    op.create_index('ix_mcp_server_configs_enabled', 'mcp_server_configs', ['enabled'])
    op.create_index('ix_mcp_server_configs_tier', 'mcp_server_configs', ['tier'])

    # ==========================================================================
    # MCP RATE LIMIT STATES - Redis backup for recovery
    # ==========================================================================

    op.create_table(
        'mcp_rate_limit_states',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(160), unique=True, nullable=False),
        # Counters
        sa.Column('minute_count', sa.Integer(), nullable=False, default=0),
        sa.Column('hour_count', sa.Integer(), nullable=False, default=0),
        sa.Column('day_count', sa.Integer(), nullable=False, default=0),
        sa.Column('day_credit', sa.Integer(), nullable=False, default=0),
        # Reset timestamps
        sa.Column('minute_reset', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('hour_reset', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('day_reset', sa.DateTime(), server_default=sa.func.now()),
        # Sync timestamp
        sa.Column('synced_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Indexes for mcp_rate_limit_states
    op.create_index('ix_mcp_rate_limit_user', 'mcp_rate_limit_states', ['user_id'], unique=True)

    # ==========================================================================
    # MCP TOOL USAGE STATS - Aggregated statistics
    # ==========================================================================

    op.create_table(
        'mcp_tool_usage_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('server_id', sa.String(64), nullable=False),
        sa.Column('tool_name', sa.String(128), nullable=False),
        # Counts
        sa.Column('total_calls', sa.Integer(), nullable=False, default=0),
        sa.Column('success_count', sa.Integer(), nullable=False, default=0),
        sa.Column('error_count', sa.Integer(), nullable=False, default=0),
        # Performance
        sa.Column('avg_latency_ms', sa.Float(), nullable=False, default=0.0),
        sa.Column('p50_latency_ms', sa.Float(), nullable=False, default=0.0),
        sa.Column('p95_latency_ms', sa.Float(), nullable=False, default=0.0),
        sa.Column('p99_latency_ms', sa.Float(), nullable=False, default=0.0),
        # Economics
        sa.Column('total_credits', sa.Integer(), nullable=False, default=0),
        # Unique users
        sa.Column('unique_users', sa.Integer(), nullable=False, default=0),
        # Timestamps
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for mcp_tool_usage_stats
    op.create_index('ix_mcp_tool_usage_server_tool_date', 'mcp_tool_usage_stats', ['server_id', 'tool_name', 'date'])
    op.create_index('ix_mcp_tool_usage_date', 'mcp_tool_usage_stats', ['date'])

    # Unique constraint for daily stats
    op.create_unique_constraint(
        'uq_mcp_tool_usage_daily',
        'mcp_tool_usage_stats',
        ['date', 'server_id', 'tool_name']
    )

    # ==========================================================================
    # INSERT DEFAULT POLICY
    # ==========================================================================

    # Insert default policy
    op.execute("""
        INSERT INTO mcp_policies (
            policy_id, name, description,
            max_calls_per_minute, max_calls_per_hour, max_calls_per_day,
            max_credit_per_call, max_credit_per_day,
            audit_level, status, priority
        ) VALUES (
            'default', 'Default Policy', 'Default MCP access policy for all users',
            30, 500, 5000,
            100, 10000,
            'basic', 'active', 0
        )
        ON CONFLICT (policy_id) DO NOTHING
    """)

    # Insert premium policy
    op.execute("""
        INSERT INTO mcp_policies (
            policy_id, name, description,
            max_calls_per_minute, max_calls_per_hour, max_calls_per_day,
            max_credit_per_call, max_credit_per_day,
            audit_level, status, priority
        ) VALUES (
            'premium', 'Premium Policy', 'Premium tier MCP access with higher limits',
            100, 2000, 20000,
            500, 50000,
            'full', 'active', 10
        )
        ON CONFLICT (policy_id) DO NOTHING
    """)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('mcp_tool_usage_stats')
    op.drop_table('mcp_rate_limit_states')
    op.drop_table('mcp_server_configs')
    op.drop_table('mcp_user_policies')
    op.drop_table('mcp_policies')
    op.drop_table('mcp_audit_logs')
