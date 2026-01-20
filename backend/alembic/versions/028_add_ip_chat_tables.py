"""Phase 10: IP Character Chat + Multi-Tenant + Marketplace tables.

Enterprise scale with IP character real-time chat capabilities.

Revision ID: 028_add_ip_chat_tables
Revises: 027_add_analytics_tables
Create Date: 2026-01-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "028_add_ip_chat_tables"
down_revision: Union[str, None] = "027_add_analytics_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Phase 10 tables for IP Chat, Multi-Tenant, and Marketplace."""

    # ==========================================================================
    # Tenants (Multi-Tenant Architecture)
    # ==========================================================================
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(64), unique=True, nullable=False),
        sa.Column("owner_user_id", sa.String(160), nullable=False),  # Tenant owner
        sa.Column("plan", sa.String(32), server_default="'free'"),  # free, starter, pro, enterprise
        sa.Column("status", sa.String(32), server_default="'active'"),  # active, suspended, pending
        sa.Column("settings", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("custom_domain", sa.String(200), nullable=True),  # White-label domain
        sa.Column("logo_url", sa.String(500), nullable=True),  # Custom branding
        # Usage limits
        sa.Column("max_api_calls", sa.Integer, server_default="1000"),
        sa.Column("max_users", sa.Integer, server_default="10"),
        sa.Column("max_ips", sa.Integer, server_default="5"),
        sa.Column("current_api_calls", sa.Integer, server_default="0"),  # Current period usage
        # Legacy fields (for compatibility)
        sa.Column("api_key_hash", sa.String(256), nullable=True),
        sa.Column("usage_limits", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("billing_email", sa.String(200), nullable=True),
        sa.Column("webhook_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()")),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"])
    op.create_index("ix_tenants_plan", "tenants", ["plan"])
    op.create_index("ix_tenants_status", "tenants", ["status"])
    op.create_index("ix_tenants_owner", "tenants", ["owner_user_id"])

    # ==========================================================================
    # Tenant API Keys
    # ==========================================================================
    op.create_table(
        "tenant_api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("key_hash", sa.String(256), nullable=False),
        sa.Column("key_prefix", sa.String(12), nullable=False),  # For display: "vvd_xxx..."
        sa.Column("scopes", postgresql.JSONB, server_default=sa.text("'[\"read\", \"write\"]'::jsonb")),
        sa.Column("rate_limit_per_minute", sa.Integer, server_default="60"),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("last_used_at", sa.DateTime, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
    )
    op.create_index("ix_tenant_api_keys_tenant", "tenant_api_keys", ["tenant_id"])
    op.create_index("ix_tenant_api_keys_prefix", "tenant_api_keys", ["key_prefix"])

    # ==========================================================================
    # IP Chat Sessions
    # ==========================================================================
    op.create_table(
        "ip_chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.String(160), nullable=False, index=True),
        sa.Column("ip_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ip_catalog.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("character_state", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),  # Character memory/state
        sa.Column("scenario_branch", sa.String(64), nullable=True),  # Current scenario path
        sa.Column("model_preference", sa.String(32), server_default="'flash'"),  # flash, pro, opus
        sa.Column("persona_mode", sa.String(32), server_default="'default'"),  # default, custom, roleplay
        sa.Column("total_messages", sa.Integer, server_default="0"),
        sa.Column("total_tokens_used", sa.Integer, server_default="0"),
        sa.Column("total_credits_spent", sa.Integer, server_default="0"),
        sa.Column("is_pinned", sa.Boolean, server_default="false"),
        sa.Column("is_archived", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("last_message_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_chat_session_user", "ip_chat_sessions", ["user_id", "last_message_at"])
    op.create_index("ix_chat_session_ip", "ip_chat_sessions", ["ip_id"])
    op.create_index("ix_chat_session_tenant", "ip_chat_sessions", ["tenant_id"])

    # ==========================================================================
    # IP Chat Messages
    # ==========================================================================
    op.create_table(
        "ip_chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ip_chat_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),  # user, assistant, system
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("media_urls", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),  # Images, audio, video
        sa.Column("tokens_used", sa.Integer, server_default="0"),
        sa.Column("credits_charged", sa.Integer, server_default="0"),
        sa.Column("model_used", sa.String(32), nullable=True),
        sa.Column("latency_ms", sa.Integer, server_default="0"),
        sa.Column("message_metadata", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),  # Scenario choices, emotions, etc.
        sa.Column("is_regenerated", sa.Boolean, server_default="false"),
        sa.Column("parent_message_id", postgresql.UUID(as_uuid=True), nullable=True),  # For branching conversations
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
    )
    op.create_index("ix_chat_message_session", "ip_chat_messages", ["session_id", "created_at"])
    op.create_index("ix_chat_message_parent", "ip_chat_messages", ["parent_message_id"])

    # ==========================================================================
    # IP Chat Scenarios (Branching paths)
    # ==========================================================================
    op.create_table(
        "ip_chat_scenarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("ip_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ip_catalog.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scenario_key", sa.String(64), nullable=False),
        sa.Column("name_ko", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200), nullable=False),
        sa.Column("description_ko", sa.Text, nullable=True),
        sa.Column("description_en", sa.Text, nullable=True),
        sa.Column("opening_message_ko", sa.Text, nullable=False),
        sa.Column("opening_message_en", sa.Text, nullable=False),
        sa.Column("character_mood", sa.String(32), server_default="'neutral'"),  # neutral, happy, sad, angry, etc.
        sa.Column("context_injection", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),  # Additional RAG context
        sa.Column("branch_options", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),  # [{key, label_ko, label_en}]
        sa.Column("sort_order", sa.Integer, server_default="0"),
        sa.Column("is_default", sa.Boolean, server_default="false"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
    )
    op.create_index("ix_chat_scenario_ip", "ip_chat_scenarios", ["ip_id"])
    op.create_unique_constraint("uq_chat_scenario_ip_key", "ip_chat_scenarios", ["ip_id", "scenario_key"])

    # ==========================================================================
    # Marketplace Listings (IP Licensing)
    # ==========================================================================
    op.create_table(
        "marketplace_listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("ip_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ip_catalog.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seller_id", sa.String(160), nullable=False),
        sa.Column("title_ko", sa.String(200), nullable=False),
        sa.Column("title_en", sa.String(200), nullable=False),
        sa.Column("description_ko", sa.Text, nullable=True),
        sa.Column("description_en", sa.Text, nullable=True),
        sa.Column("license_tier", sa.String(32), server_default="'free'"),  # free, commercial, exclusive
        sa.Column("price_credits", sa.Integer, server_default="0"),  # One-time price
        sa.Column("royalty_percent", sa.Integer, server_default="0"),  # Per-use royalty
        sa.Column("usage_rights", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),  # [chat, generation, commercial]
        sa.Column("territory_restrictions", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("view_count", sa.Integer, server_default="0"),
        sa.Column("purchase_count", sa.Integer, server_default="0"),
        sa.Column("average_rating", sa.Float, server_default="0"),
        sa.Column("rating_count", sa.Integer, server_default="0"),
        sa.Column("is_featured", sa.Boolean, server_default="false"),
        sa.Column("is_verified", sa.Boolean, server_default="false"),
        sa.Column("status", sa.String(32), server_default="'draft'"),  # draft, pending, active, suspended
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()")),
    )
    op.create_index("ix_marketplace_ip", "marketplace_listings", ["ip_id"])
    op.create_index("ix_marketplace_seller", "marketplace_listings", ["seller_id"])
    op.create_index("ix_marketplace_tier", "marketplace_listings", ["license_tier"])
    op.create_index("ix_marketplace_status", "marketplace_listings", ["status"])
    op.create_index("ix_marketplace_featured", "marketplace_listings", ["is_featured", "is_verified"])

    # ==========================================================================
    # Marketplace Purchases
    # ==========================================================================
    op.create_table(
        "marketplace_purchases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("marketplace_listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("buyer_id", sa.String(160), nullable=False),
        sa.Column("seller_id", sa.String(160), nullable=False),
        sa.Column("price_paid", sa.Integer, nullable=False),
        sa.Column("seller_revenue", sa.Integer, nullable=False),  # After platform fee (60%)
        sa.Column("platform_fee", sa.Integer, nullable=False),  # Platform share (30%)
        sa.Column("fork_royalty", sa.Integer, server_default="0"),  # Original creator share (10%)
        sa.Column("license_granted", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
    )
    op.create_index("ix_purchase_listing", "marketplace_purchases", ["listing_id"])
    op.create_index("ix_purchase_buyer", "marketplace_purchases", ["buyer_id"])
    op.create_index("ix_purchase_seller", "marketplace_purchases", ["seller_id"])

    # ==========================================================================
    # Marketplace Reviews
    # ==========================================================================
    op.create_table(
        "marketplace_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("marketplace_listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purchase_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("marketplace_purchases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", sa.String(160), nullable=False),
        sa.Column("rating", sa.Integer, nullable=False),  # 1-5
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("is_verified_purchase", sa.Boolean, server_default="true"),
        sa.Column("helpful_count", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()")),
    )
    op.create_index("ix_review_listing", "marketplace_reviews", ["listing_id"])
    op.create_unique_constraint("uq_review_purchase", "marketplace_reviews", ["purchase_id"])

    # ==========================================================================
    # Extend ip_catalog for Chat Features
    # ==========================================================================
    op.add_column(
        "ip_catalog",
        sa.Column("chat_enabled", sa.Boolean, server_default="false"),
    )
    op.add_column(
        "ip_catalog",
        sa.Column("persona_prompt", sa.Text, nullable=True),
    )
    op.add_column(
        "ip_catalog",
        sa.Column("voice_id", sa.String(64), nullable=True),  # ElevenLabs/Chatterbox voice ID
    )
    op.add_column(
        "ip_catalog",
        sa.Column("chat_model_default", sa.String(32), server_default="'flash'"),
    )
    op.add_column(
        "ip_catalog",
        sa.Column("chat_session_count", sa.Integer, server_default="0"),
    )
    op.add_column(
        "ip_catalog",
        sa.Column("chat_message_count", sa.Integer, server_default="0"),
    )
    op.add_column(
        "ip_catalog",
        sa.Column("marketplace_listing_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Create index for chat-enabled IPs
    op.create_index("ix_ip_catalog_chat_enabled", "ip_catalog", ["chat_enabled"])


def downgrade() -> None:
    """Drop Phase 10 tables."""
    # Drop columns from ip_catalog
    op.drop_index("ix_ip_catalog_chat_enabled", "ip_catalog")
    op.drop_column("ip_catalog", "marketplace_listing_id")
    op.drop_column("ip_catalog", "chat_message_count")
    op.drop_column("ip_catalog", "chat_session_count")
    op.drop_column("ip_catalog", "chat_model_default")
    op.drop_column("ip_catalog", "voice_id")
    op.drop_column("ip_catalog", "persona_prompt")
    op.drop_column("ip_catalog", "chat_enabled")

    # Drop new tables (reverse order)
    op.drop_table("marketplace_reviews")
    op.drop_table("marketplace_purchases")
    op.drop_table("marketplace_listings")
    op.drop_table("ip_chat_scenarios")
    op.drop_table("ip_chat_messages")
    op.drop_table("ip_chat_sessions")
    op.drop_table("tenant_api_keys")
    op.drop_table("tenants")
