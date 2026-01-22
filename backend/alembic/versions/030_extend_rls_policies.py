"""H1.4: Extend RLS policies to additional user data tables.

Security Hardening: Extends PostgreSQL RLS to protect sensitive user data
in credit, agent, and user preference tables.

Revision ID: 030_extend_rls_policies
Revises: 029_add_rls_policies
Create Date: 2026-01-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "030_extend_rls_policies"
down_revision: Union[str, None] = "029_add_rls_policies"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables to add RLS with tenant_id
RLS_TABLES_TENANT = [
    "user_credits",
    "credit_ledger",
    "agent_sessions",
    "agent_messages",
    "agent_artifacts",
    "constellations",
    "characters",
    "user_preference_profiles",
    "user_interaction_signals",
    "session_preferences",
]

# Tables that use user_id directly (no tenant_id column needed, use existing user_id)
RLS_TABLES_USER_ID = [
    # These tables already have user_id, we just enable RLS
]


def upgrade() -> None:
    """Add tenant_id columns and enable RLS policies for additional tables.

    Security Note (H1.4 Extended):
    - Protects sensitive user data: credits, agent conversations, preferences
    - Uses same pattern as 029: app.current_tenant session variable
    - NULL tenant_id allows legacy data and superuser access
    """

    # ==========================================================================
    # 1. Add tenant_id columns to tables
    # ==========================================================================

    for table_name in RLS_TABLES_TENANT:
        try:
            op.add_column(
                table_name,
                sa.Column("tenant_id", sa.String(36), nullable=True, index=True)
            )
        except Exception:
            # Column might already exist
            pass

    # ==========================================================================
    # 2. Enable Row Level Security
    # ==========================================================================

    for table_name in RLS_TABLES_TENANT:
        op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY")

    # ==========================================================================
    # 3. Create RLS Policies
    # ==========================================================================

    for table_name in RLS_TABLES_TENANT:
        policy_name = f"tenant_isolation_{table_name}"
        op.execute(f"""
            CREATE POLICY {policy_name} ON {table_name}
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
    # 4. Create composite indexes for efficient tenant queries
    # ==========================================================================

    # Critical tables get composite indexes
    critical_tables = ["user_credits", "credit_ledger", "agent_sessions"]

    for table_name in critical_tables:
        try:
            op.create_index(
                f"ix_{table_name}_tenant_created",
                table_name,
                ["tenant_id", "created_at"],
                postgresql_using="btree"
            )
        except Exception:
            # Index might not have created_at column, skip
            pass


def downgrade() -> None:
    """Remove RLS policies and tenant_id columns."""

    # Drop indexes
    critical_tables = ["user_credits", "credit_ledger", "agent_sessions"]
    for table_name in critical_tables:
        try:
            op.drop_index(f"ix_{table_name}_tenant_created", table_name=table_name)
        except Exception:
            pass

    # Drop RLS policies
    for table_name in RLS_TABLES_TENANT:
        policy_name = f"tenant_isolation_{table_name}"
        op.execute(f"DROP POLICY IF EXISTS {policy_name} ON {table_name}")

    # Disable RLS
    for table_name in RLS_TABLES_TENANT:
        op.execute(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY")

    # Drop tenant_id columns
    for table_name in RLS_TABLES_TENANT:
        try:
            op.drop_column(table_name, "tenant_id")
        except Exception:
            pass
