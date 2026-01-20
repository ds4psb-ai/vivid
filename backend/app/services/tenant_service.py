"""Tenant Service for Phase 10 Multi-Tenant Architecture.

Handles tenant management, API key validation, and usage tracking.

Hub-Spoke Architecture:
- Hub: Crebit Studio main platform
- Spokes: Enterprise B2B deployments with isolated data

Based on: SSOT_DECISIONS_LOG.md Phase 10 design
"""
from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_tenant import Tenant, TenantAPIKey

logger = logging.getLogger(__name__)


# Plan limits configuration
PLAN_LIMITS = {
    "free": {
        "max_api_calls": 1000,
        "max_users": 10,
        "max_ips": 5,
        "features": ["chat"],
    },
    "starter": {
        "max_api_calls": 10000,
        "max_users": 100,
        "max_ips": 50,
        "features": ["chat", "custom_personas", "analytics"],
    },
    "pro": {
        "max_api_calls": 100000,
        "max_users": 1000,
        "max_ips": 500,
        "features": ["chat", "custom_personas", "analytics", "white_label", "priority_support"],
    },
    "enterprise": {
        "max_api_calls": -1,  # Unlimited
        "max_users": -1,
        "max_ips": -1,
        "features": ["chat", "custom_personas", "analytics", "white_label", "priority_support", "dedicated_support", "sla"],
    },
}


class TenantService:
    """Service for multi-tenant operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Tenant Management
    # =========================================================================

    async def create_tenant(
        self,
        name: str,
        owner_user_id: str,
        slug: Optional[str] = None,
        plan: str = "free",
        settings: Optional[Dict] = None,
    ) -> Tenant:
        """Create a new tenant.

        Args:
            name: Tenant display name
            owner_user_id: Owner user ID
            slug: URL-safe identifier (auto-generated if not provided)
            plan: Subscription plan
            settings: Custom tenant settings

        Returns:
            Created tenant
        """
        if not slug:
            # Generate slug from name
            slug = name.lower().replace(" ", "-")
            slug = "".join(c for c in slug if c.isalnum() or c == "-")
            # Ensure uniqueness
            base_slug = slug
            counter = 1
            while await self._slug_exists(slug):
                slug = f"{base_slug}-{counter}"
                counter += 1

        # Verify plan is valid
        if plan not in PLAN_LIMITS:
            raise ValueError(f"Invalid plan: {plan}")

        tenant = Tenant(
            name=name,
            slug=slug,
            owner_user_id=owner_user_id,
            plan=plan,
            settings=settings or {},
            max_api_calls=PLAN_LIMITS[plan]["max_api_calls"],
            max_users=PLAN_LIMITS[plan]["max_users"],
            max_ips=PLAN_LIMITS[plan]["max_ips"],
        )

        self.db.add(tenant)
        await self.db.commit()

        logger.info(f"Created tenant {tenant.id} ({tenant.slug}) with plan {plan}")
        return tenant

    async def get_tenant(self, tenant_id: uuid.UUID) -> Optional[Tenant]:
        """Get a tenant by ID."""
        return await self.db.get(Tenant, tenant_id)

    async def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get a tenant by slug."""
        result = await self.db.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_tenant_by_api_key(self, api_key: str) -> Optional[Tenant]:
        """Get tenant by API key (for middleware authentication)."""
        # Hash the API key
        key_hash = self._hash_api_key(api_key)

        result = await self.db.execute(
            select(TenantAPIKey).where(
                TenantAPIKey.key_hash == key_hash,
                TenantAPIKey.is_active == True,
            )
        )
        api_key_record = result.scalar_one_or_none()

        if not api_key_record:
            return None

        # Check expiration
        if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
            return None

        # Update last used
        api_key_record.last_used_at = datetime.utcnow()
        await self.db.commit()

        return await self.get_tenant(api_key_record.tenant_id)

    async def list_tenants(
        self,
        owner_user_id: Optional[str] = None,
        plan: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Tenant], int]:
        """List tenants with filters."""
        query = select(Tenant).where(Tenant.status == "active")

        if owner_user_id:
            query = query.where(Tenant.owner_user_id == owner_user_id)

        if plan:
            query = query.where(Tenant.plan == plan)

        # Get total count
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        query = query.order_by(Tenant.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        tenants = list(result.scalars().all())

        return tenants, total

    async def update_tenant(
        self,
        tenant_id: uuid.UUID,
        owner_user_id: str,
        **updates,
    ) -> Optional[Tenant]:
        """Update a tenant (only owner can update)."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant or tenant.owner_user_id != owner_user_id:
            return None

        allowed_fields = {"name", "settings", "custom_domain", "logo_url"}

        for key, value in updates.items():
            if key in allowed_fields:
                setattr(tenant, key, value)

        tenant.updated_at = datetime.utcnow()
        await self.db.commit()

        return tenant

    async def upgrade_plan(
        self,
        tenant_id: uuid.UUID,
        new_plan: str,
    ) -> bool:
        """Upgrade tenant plan."""
        if new_plan not in PLAN_LIMITS:
            return False

        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False

        tenant.plan = new_plan
        tenant.max_api_calls = PLAN_LIMITS[new_plan]["max_api_calls"]
        tenant.max_users = PLAN_LIMITS[new_plan]["max_users"]
        tenant.max_ips = PLAN_LIMITS[new_plan]["max_ips"]
        tenant.updated_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"Upgraded tenant {tenant_id} to plan {new_plan}")
        return True

    # =========================================================================
    # API Key Management
    # =========================================================================

    async def create_api_key(
        self,
        tenant_id: uuid.UUID,
        name: str,
        scopes: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
    ) -> Tuple[TenantAPIKey, str]:
        """Create a new API key for a tenant.

        Args:
            tenant_id: Tenant ID
            name: Key name/description
            scopes: List of allowed scopes
            expires_in_days: Days until expiration (None = never)

        Returns:
            Tuple of (API key record, plain text key)
        """
        # Generate secure API key
        raw_key = f"vvd_{secrets.token_urlsafe(32)}"
        key_prefix = raw_key[:12]
        key_hash = self._hash_api_key(raw_key)

        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        api_key = TenantAPIKey(
            tenant_id=tenant_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            scopes=scopes or ["read", "write"],
            expires_at=expires_at,
        )

        self.db.add(api_key)
        await self.db.commit()

        logger.info(f"Created API key {api_key.id} for tenant {tenant_id}")

        # Return raw key only once (never stored)
        return api_key, raw_key

    async def list_api_keys(
        self,
        tenant_id: uuid.UUID,
    ) -> List[TenantAPIKey]:
        """List API keys for a tenant."""
        result = await self.db.execute(
            select(TenantAPIKey).where(
                TenantAPIKey.tenant_id == tenant_id,
                TenantAPIKey.is_active == True,
            ).order_by(TenantAPIKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def revoke_api_key(
        self,
        api_key_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> bool:
        """Revoke an API key."""
        api_key = await self.db.get(TenantAPIKey, api_key_id)
        if not api_key or api_key.tenant_id != tenant_id:
            return False

        api_key.is_active = False
        await self.db.commit()

        logger.info(f"Revoked API key {api_key_id}")
        return True

    # =========================================================================
    # Usage Tracking
    # =========================================================================

    async def increment_api_calls(self, tenant_id: uuid.UUID) -> bool:
        """Increment API call count for a tenant.

        Returns:
            True if within limits, False if limit exceeded
        """
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False

        # Check limits (-1 means unlimited)
        if tenant.max_api_calls != -1 and tenant.current_api_calls >= tenant.max_api_calls:
            return False

        tenant.current_api_calls += 1
        await self.db.commit()

        return True

    async def check_user_limit(self, tenant_id: uuid.UUID, current_users: int) -> bool:
        """Check if tenant can add more users."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False

        if tenant.max_users == -1:
            return True

        return current_users < tenant.max_users

    async def check_ip_limit(self, tenant_id: uuid.UUID, current_ips: int) -> bool:
        """Check if tenant can add more IPs."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False

        if tenant.max_ips == -1:
            return True

        return current_ips < tenant.max_ips

    async def get_usage_stats(self, tenant_id: uuid.UUID) -> Dict:
        """Get usage statistics for a tenant."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return {}

        return {
            "api_calls": {
                "used": tenant.current_api_calls,
                "limit": tenant.max_api_calls,
                "percentage": (
                    (tenant.current_api_calls / tenant.max_api_calls * 100)
                    if tenant.max_api_calls > 0 else 0
                ),
            },
            "users": {
                "limit": tenant.max_users,
            },
            "ips": {
                "limit": tenant.max_ips,
            },
            "plan": tenant.plan,
            "features": PLAN_LIMITS.get(tenant.plan, {}).get("features", []),
        }

    async def reset_monthly_usage(self, tenant_id: uuid.UUID) -> None:
        """Reset monthly API call counter (called by scheduled job)."""
        tenant = await self.get_tenant(tenant_id)
        if tenant:
            tenant.current_api_calls = 0
            await self.db.commit()

    # =========================================================================
    # Helpers
    # =========================================================================

    async def _slug_exists(self, slug: str) -> bool:
        """Check if a slug is already taken."""
        result = await self.db.execute(
            select(func.count()).where(Tenant.slug == slug)
        )
        return (result.scalar() or 0) > 0

    @staticmethod
    def _hash_api_key(raw_key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(raw_key.encode()).hexdigest()
