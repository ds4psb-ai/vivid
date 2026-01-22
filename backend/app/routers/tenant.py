"""Tenant Router for Phase 10 Multi-Tenant Architecture.

Provides API endpoints for tenant management, API keys, and usage tracking.

Based on: SSOT_DECISIONS_LOG.md Phase 10 design
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.utils.error_sanitize import safe_error_detail
from app.middleware.tenant import get_current_tenant, require_tenant
from app.models_tenant import Tenant
from app.services.tenant_service import TenantService, PLAN_LIMITS

# Type alias for user dict
UserDict = dict

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


# =============================================================================
# Schemas
# =============================================================================

class TenantCreate(BaseModel):
    """Schema for creating a tenant."""
    name: str = Field(..., min_length=2, max_length=128)
    slug: Optional[str] = Field(None, pattern=r"^[a-z0-9-]+$", max_length=64)
    plan: str = Field("free")
    settings: Optional[dict] = None


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""
    name: Optional[str] = Field(None, min_length=2, max_length=128)
    settings: Optional[dict] = None
    custom_domain: Optional[str] = None
    logo_url: Optional[str] = None


class TenantResponse(BaseModel):
    """Schema for tenant response."""
    id: str
    name: str
    slug: str
    plan: str
    status: str
    owner_user_id: str
    settings: dict
    custom_domain: Optional[str]
    logo_url: Optional[str]
    max_api_calls: int
    max_users: int
    max_ips: int
    current_api_calls: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApiKeyCreate(BaseModel):
    """Schema for creating an API key."""
    name: str = Field(..., min_length=2, max_length=128)
    scopes: List[str] = Field(default=["read", "write"])
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class ApiKeyResponse(BaseModel):
    """Schema for API key response (without actual key)."""
    id: str
    tenant_id: str
    key_prefix: str
    name: str
    scopes: List[str]
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyCreatedResponse(BaseModel):
    """Schema for newly created API key (includes raw key once)."""
    api_key: ApiKeyResponse
    raw_key: str = Field(
        ...,
        description="The raw API key. Store this securely - it won't be shown again!"
    )


class UsageStatsResponse(BaseModel):
    """Schema for usage statistics."""
    api_calls: dict
    users: dict
    ips: dict
    plan: str
    features: List[str]


class PlanInfoResponse(BaseModel):
    """Schema for plan information."""
    name: str
    max_api_calls: int
    max_users: int
    max_ips: int
    features: List[str]


# =============================================================================
# Tenant Management Endpoints
# =============================================================================

@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    data: TenantCreate,
    user: UserDict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new tenant.

    Creates a tenant organization for the current user.
    The user becomes the owner of the tenant.
    """
    service = TenantService(db)

    try:
        tenant = await service.create_tenant(
            name=data.name,
            owner_user_id=user["id"],
            slug=data.slug,
            plan=data.plan,
            settings=data.settings,
        )
        return TenantResponse(
            id=str(tenant.id),
            name=tenant.name,
            slug=tenant.slug,
            plan=tenant.plan,
            status=tenant.status,
            owner_user_id=tenant.owner_user_id,
            settings=tenant.settings or {},
            custom_domain=tenant.custom_domain,
            logo_url=tenant.logo_url,
            max_api_calls=tenant.max_api_calls,
            max_users=tenant.max_users,
            max_ips=tenant.max_ips,
            current_api_calls=tenant.current_api_calls,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Tenant operation"))


@router.get("", response_model=List[TenantResponse])
async def list_my_tenants(
    user: UserDict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List tenants owned by the current user."""
    service = TenantService(db)
    tenants, _ = await service.list_tenants(owner_user_id=user["id"])

    return [
        TenantResponse(
            id=str(t.id),
            name=t.name,
            slug=t.slug,
            plan=t.plan,
            status=t.status,
            owner_user_id=t.owner_user_id,
            settings=t.settings or {},
            custom_domain=t.custom_domain,
            logo_url=t.logo_url,
            max_api_calls=t.max_api_calls,
            max_users=t.max_users,
            max_ips=t.max_ips,
            current_api_calls=t.current_api_calls,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in tenants
    ]


@router.get("/current", response_model=Optional[TenantResponse])
async def get_current_tenant_info(
    tenant: Optional[Tenant] = Depends(get_current_tenant),
):
    """Get the current tenant from API key (if authenticated)."""
    if not tenant:
        return None

    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        slug=tenant.slug,
        plan=tenant.plan,
        status=tenant.status,
        owner_user_id=tenant.owner_user_id,
        settings=tenant.settings or {},
        custom_domain=tenant.custom_domain,
        logo_url=tenant.logo_url,
        max_api_calls=tenant.max_api_calls,
        max_users=tenant.max_users,
        max_ips=tenant.max_ips,
        current_api_calls=tenant.current_api_calls,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: uuid.UUID,
    user: UserDict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific tenant by ID."""
    service = TenantService(db)
    tenant = await service.get_tenant(tenant_id)

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Only owner can view tenant details
    if tenant.owner_user_id != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        slug=tenant.slug,
        plan=tenant.plan,
        status=tenant.status,
        owner_user_id=tenant.owner_user_id,
        settings=tenant.settings or {},
        custom_domain=tenant.custom_domain,
        logo_url=tenant.logo_url,
        max_api_calls=tenant.max_api_calls,
        max_users=tenant.max_users,
        max_ips=tenant.max_ips,
        current_api_calls=tenant.current_api_calls,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: uuid.UUID,
    data: TenantUpdate,
    user: UserDict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a tenant."""
    service = TenantService(db)

    updated = await service.update_tenant(
        tenant_id=tenant_id,
        owner_user_id=user["id"],
        **data.model_dump(exclude_unset=True),
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Tenant not found or not authorized")

    return TenantResponse(
        id=str(updated.id),
        name=updated.name,
        slug=updated.slug,
        plan=updated.plan,
        status=updated.status,
        owner_user_id=updated.owner_user_id,
        settings=updated.settings or {},
        custom_domain=updated.custom_domain,
        logo_url=updated.logo_url,
        max_api_calls=updated.max_api_calls,
        max_users=updated.max_users,
        max_ips=updated.max_ips,
        current_api_calls=updated.current_api_calls,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


# =============================================================================
# API Key Management Endpoints
# =============================================================================

@router.post("/{tenant_id}/api-keys", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    tenant_id: uuid.UUID,
    data: ApiKeyCreate,
    user: UserDict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key for a tenant.

    ⚠️ The raw API key is only returned once. Store it securely!
    """
    service = TenantService(db)

    # Verify ownership
    tenant = await service.get_tenant(tenant_id)
    if not tenant or tenant.owner_user_id != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    api_key, raw_key = await service.create_api_key(
        tenant_id=tenant_id,
        name=data.name,
        scopes=data.scopes,
        expires_in_days=data.expires_in_days,
    )

    return ApiKeyCreatedResponse(
        api_key=ApiKeyResponse(
            id=str(api_key.id),
            tenant_id=str(api_key.tenant_id),
            key_prefix=api_key.key_prefix,
            name=api_key.name,
            scopes=api_key.scopes or [],
            is_active=api_key.is_active,
            expires_at=api_key.expires_at,
            last_used_at=api_key.last_used_at,
            created_at=api_key.created_at,
        ),
        raw_key=raw_key,
    )


@router.get("/{tenant_id}/api-keys", response_model=List[ApiKeyResponse])
async def list_api_keys(
    tenant_id: uuid.UUID,
    user: UserDict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List API keys for a tenant."""
    service = TenantService(db)

    # Verify ownership
    tenant = await service.get_tenant(tenant_id)
    if not tenant or tenant.owner_user_id != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    keys = await service.list_api_keys(tenant_id)

    return [
        ApiKeyResponse(
            id=str(k.id),
            tenant_id=str(k.tenant_id),
            key_prefix=k.key_prefix,
            name=k.name,
            scopes=k.scopes or [],
            is_active=k.is_active,
            expires_at=k.expires_at,
            last_used_at=k.last_used_at,
            created_at=k.created_at,
        )
        for k in keys
    ]


@router.delete("/{tenant_id}/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    tenant_id: uuid.UUID,
    key_id: uuid.UUID,
    user: UserDict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key."""
    service = TenantService(db)

    # Verify ownership
    tenant = await service.get_tenant(tenant_id)
    if not tenant or tenant.owner_user_id != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    success = await service.revoke_api_key(key_id, tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")


# =============================================================================
# Usage & Plan Endpoints
# =============================================================================

@router.get("/{tenant_id}/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    tenant_id: uuid.UUID,
    user: UserDict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get usage statistics for a tenant."""
    service = TenantService(db)

    # Verify ownership
    tenant = await service.get_tenant(tenant_id)
    if not tenant or tenant.owner_user_id != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    stats = await service.get_usage_stats(tenant_id)
    return UsageStatsResponse(**stats)


@router.get("/plans/available", response_model=dict[str, PlanInfoResponse])
async def get_available_plans():
    """Get information about available plans."""
    return {
        plan_name: PlanInfoResponse(
            name=plan_name,
            max_api_calls=limits["max_api_calls"],
            max_users=limits["max_users"],
            max_ips=limits["max_ips"],
            features=limits["features"],
        )
        for plan_name, limits in PLAN_LIMITS.items()
    }


@router.post("/{tenant_id}/upgrade")
async def upgrade_tenant_plan(
    tenant_id: uuid.UUID,
    new_plan: str,
    user: UserDict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upgrade a tenant's plan.

    Note: In production, this would integrate with a payment system.
    """
    service = TenantService(db)

    # Verify ownership
    tenant = await service.get_tenant(tenant_id)
    if not tenant or tenant.owner_user_id != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    if new_plan not in PLAN_LIMITS:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {new_plan}")

    success = await service.upgrade_plan(tenant_id, new_plan)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to upgrade plan")

    return {"message": f"Successfully upgraded to {new_plan} plan"}
