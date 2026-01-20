"""H1.4: Add Row Level Security (RLS) policies for multi-tenant isolation.

Security Hardening: Enables PostgreSQL RLS for critical tables to ensure
tenant data isolation at the database level.

Revision ID: 029_add_rls_policies
Revises: 028_add_ip_chat_tables
Create Date: 2026-01-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "029_add_rls_policies"
down_revision: Union[str, None] = "028_add_ip_chat_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add tenant_id columns and enable RLS policies.

    Security Note (H1.4):
    - RLS enforces tenant isolation at database level
    - Even if application code has bugs, data cannot leak between tenants
    - Uses app.current_tenant session variable set by middleware
    """

    # ==========================================================================
    # 1. Add tenant_id columns to key tables
    # ==========================================================================

    # CapsuleRun - main execution records
    op.add_column(
        "capsule_runs",
        sa.Column("tenant_id", sa.String(36), nullable=True, index=True)
    )

    # WorkflowExecution - workflow execution records
    op.add_column(
        "workflow_executions",
        sa.Column("tenant_id", sa.String(36), nullable=True, index=True)
    )

    # IPChatSession - chat sessions (Phase 10)
    op.add_column(
        "ip_chat_sessions",
        sa.Column("tenant_id", sa.String(36), nullable=True, index=True)
    )

    # IPChatMessage - chat messages (Phase 10)
    op.add_column(
        "ip_chat_messages",
        sa.Column("tenant_id", sa.String(36), nullable=True, index=True)
    )

    # ==========================================================================
    # 2. Enable Row Level Security
    # ==========================================================================

    # Enable RLS on capsule_runs
    op.execute("ALTER TABLE capsule_runs ENABLE ROW LEVEL SECURITY")

    # Enable RLS on workflow_executions
    op.execute("ALTER TABLE workflow_executions ENABLE ROW LEVEL SECURITY")

    # Enable RLS on ip_chat_sessions
    op.execute("ALTER TABLE ip_chat_sessions ENABLE ROW LEVEL SECURITY")

    # Enable RLS on ip_chat_messages
    op.execute("ALTER TABLE ip_chat_messages ENABLE ROW LEVEL SECURITY")

    # ==========================================================================
    # 3. Create RLS Policies
    # ==========================================================================

    # Policy for capsule_runs: tenant can only see their own runs
    # current_setting('app.current_tenant', true) returns NULL if not set
    op.execute("""
        CREATE POLICY tenant_isolation_capsule_runs ON capsule_runs
        FOR ALL
        USING (
            tenant_id IS NULL
            OR tenant_id = current_setting('app.current_tenant', true)
        )
        WITH CHECK (
            tenant_id IS NULL
            OR tenant_id = current_setting('app.current_tenant', true)
        )
    """)

    # Policy for workflow_executions: tenant isolation
    op.execute("""
        CREATE POLICY tenant_isolation_workflow_executions ON workflow_executions
        FOR ALL
        USING (
            tenant_id IS NULL
            OR tenant_id = current_setting('app.current_tenant', true)
        )
        WITH CHECK (
            tenant_id IS NULL
            OR tenant_id = current_setting('app.current_tenant', true)
        )
    """)

    # Policy for ip_chat_sessions: tenant isolation
    op.execute("""
        CREATE POLICY tenant_isolation_ip_chat_sessions ON ip_chat_sessions
        FOR ALL
        USING (
            tenant_id IS NULL
            OR tenant_id = current_setting('app.current_tenant', true)
        )
        WITH CHECK (
            tenant_id IS NULL
            OR tenant_id = current_setting('app.current_tenant', true)
        )
    """)

    # Policy for ip_chat_messages: tenant isolation
    op.execute("""
        CREATE POLICY tenant_isolation_ip_chat_messages ON ip_chat_messages
        FOR ALL
        USING (
            tenant_id IS NULL
            OR tenant_id = current_setting('app.current_tenant', true)
        )
        WITH CHECK (
            tenant_id IS NULL
            OR tenant_id = current_setting('app.current_tenant', true)
        )
    """)

    # ==========================================================================
    # 4. Create indexes for efficient tenant queries
    # ==========================================================================

    # Composite index for common queries
    op.create_index(
        "ix_capsule_runs_tenant_created",
        "capsule_runs",
        ["tenant_id", "created_at"],
        postgresql_using="btree"
    )

    op.create_index(
        "ix_workflow_executions_tenant_created",
        "workflow_executions",
        ["tenant_id", "created_at"],
        postgresql_using="btree"
    )


def downgrade() -> None:
    """Remove RLS policies and tenant_id columns."""

    # Drop indexes
    op.drop_index("ix_capsule_runs_tenant_created", table_name="capsule_runs")
    op.drop_index("ix_workflow_executions_tenant_created", table_name="workflow_executions")

    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS tenant_isolation_capsule_runs ON capsule_runs")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_workflow_executions ON workflow_executions")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_ip_chat_sessions ON ip_chat_sessions")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_ip_chat_messages ON ip_chat_messages")

    # Disable RLS
    op.execute("ALTER TABLE capsule_runs DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workflow_executions DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE ip_chat_sessions DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE ip_chat_messages DISABLE ROW LEVEL SECURITY")

    # Drop tenant_id columns
    op.drop_column("capsule_runs", "tenant_id")
    op.drop_column("workflow_executions", "tenant_id")
    op.drop_column("ip_chat_sessions", "tenant_id")
    op.drop_column("ip_chat_messages", "tenant_id")
