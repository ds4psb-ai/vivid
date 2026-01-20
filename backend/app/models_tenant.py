"""Tenant Models for Phase 10 Multi-Tenant Architecture.

This module defines models for enterprise multi-tenancy:
- Tenant: Organization/company entity
- TenantAPIKey: API key management for tenant access
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Tenant(Base):
    """Tenant - Organization/company for multi-tenant access.

    Hub-Spoke pattern: Shared AI Hub with tenant-isolated data.
    """
    __tablename__ = "tenants"
    __table_args__ = (
        Index("ix_tenants_slug", "slug"),
        Index("ix_tenants_plan", "plan"),
        Index("ix_tenants_status", "status"),
        Index("ix_tenants_owner", "owner_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    owner_user_id: Mapped[str] = mapped_column(String(160), nullable=False)

    # Plan and status
    plan: Mapped[str] = mapped_column(String(32), default="free")  # free, starter, pro, enterprise
    status: Mapped[str] = mapped_column(String(32), default="active")  # active, suspended, pending
    billing_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Configuration
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)  # Custom branding, features, etc.
    custom_domain: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # White-label domain
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Custom branding

    # Usage limits
    max_api_calls: Mapped[int] = mapped_column(Integer, default=1000)
    max_users: Mapped[int] = mapped_column(Integer, default=10)
    max_ips: Mapped[int] = mapped_column(Integer, default=5)
    current_api_calls: Mapped[int] = mapped_column(Integer, default=0)

    # Legacy fields (for compatibility)
    usage_limits: Mapped[dict] = mapped_column(JSONB, default=dict)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    api_key_hash: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    api_keys: Mapped[List["TenantAPIKey"]] = relationship("TenantAPIKey", back_populates="tenant", cascade="all, delete-orphan")


class TenantAPIKey(Base):
    """Tenant API Key - API key for tenant authentication.

    Supports multiple keys per tenant with different scopes.
    """
    __tablename__ = "tenant_api_keys"
    __table_args__ = (
        Index("ix_tenant_api_keys_tenant", "tenant_id"),
        Index("ix_tenant_api_keys_prefix", "key_prefix"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    # Key info
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(12), nullable=False)  # For display: "vvd_xxx..."

    # Permissions
    scopes: Mapped[list] = mapped_column(JSONB, default=lambda: ["read", "write"])  # read, write, admin
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=60)

    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="api_keys")

    @property
    def is_expired(self) -> bool:
        """Check if the API key has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if the API key is valid (active and not expired)."""
        return self.is_active and not self.is_expired
