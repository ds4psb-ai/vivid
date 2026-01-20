"""Tenant Middleware for Phase 10 Multi-Tenant Architecture.

Handles API key authentication and tenant context injection.

Usage:
    # In route handlers
    @router.get("/api/v1/tenant/data")
    async def get_data(
        tenant: Tenant | None = Depends(get_current_tenant),
    ):
        if tenant:
            # Tenant-specific logic
            pass

Based on: SSOT_DECISIONS_LOG.md Phase 10 design
"""
from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.database import get_db
from app.models_tenant import Tenant
from app.services.tenant_service import TenantService

logger = logging.getLogger(__name__)

# Context variable for current tenant
_current_tenant: ContextVar[Optional[Tenant]] = ContextVar("current_tenant", default=None)


def get_current_tenant_from_context() -> Optional[Tenant]:
    """Get current tenant from context (set by middleware)."""
    return _current_tenant.get()


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to authenticate tenant API keys and set tenant context.

    Checks for X-API-Key header and validates against tenant API keys.
    Sets tenant context for downstream handlers.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Skip tenant auth for certain paths
        skip_paths = ["/", "/health", "/docs", "/openapi.json", "/redoc"]
        if request.url.path in skip_paths or request.url.path.startswith("/api/v1/auth"):
            return await call_next(request)

        # Check for API key header
        api_key = request.headers.get("X-API-Key")

        if api_key:
            # Validate API key and get tenant
            try:
                async for db in get_db():
                    tenant_service = TenantService(db)
                    tenant = await tenant_service.get_tenant_by_api_key(api_key)

                    if tenant:
                        # Check tenant status
                        if tenant.status != "active":
                            return self._json_response(
                                {"error": "Tenant is not active"},
                                status_code=403,
                            )

                        # Check API call limits
                        can_proceed = await tenant_service.increment_api_calls(tenant.id)
                        if not can_proceed:
                            return self._json_response(
                                {"error": "API call limit exceeded for your plan"},
                                status_code=429,
                            )

                        # Set tenant context
                        _current_tenant.set(tenant)

                        # Add tenant info to request state
                        request.state.tenant = tenant
                        request.state.tenant_id = str(tenant.id)

                        logger.debug(f"Authenticated tenant: {tenant.slug}")
                    break

            except Exception as e:
                logger.error(f"Tenant auth error: {e}")
                # Don't fail request, just proceed without tenant context

        response = await call_next(request)

        # Clear tenant context after request
        _current_tenant.set(None)

        return response

    def _json_response(self, data: dict, status_code: int):
        """Create a JSON response."""
        import json
        from starlette.responses import Response

        return Response(
            content=json.dumps(data),
            status_code=status_code,
            media_type="application/json",
        )


# Dependency for getting current tenant
async def get_current_tenant(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> Optional[Tenant]:
    """FastAPI dependency to get current tenant.

    Can be used in route handlers:
        @router.get("/data")
        async def get_data(tenant: Tenant | None = Depends(get_current_tenant)):
            ...
    """
    # First check if middleware already set tenant
    if hasattr(request.state, "tenant"):
        return request.state.tenant

    # If no API key, return None (public access)
    if not x_api_key:
        return None

    # Validate API key
    tenant_service = TenantService(db)
    tenant = await tenant_service.get_tenant_by_api_key(x_api_key)

    if tenant and tenant.status != "active":
        raise HTTPException(status_code=403, detail="Tenant is not active")

    return tenant


async def require_tenant(
    tenant: Optional[Tenant] = Depends(get_current_tenant),
) -> Tenant:
    """FastAPI dependency that requires a valid tenant.

    Use when endpoint requires tenant authentication:
        @router.get("/tenant-only")
        async def tenant_only(tenant: Tenant = Depends(require_tenant)):
            ...
    """
    if not tenant:
        raise HTTPException(
            status_code=401,
            detail="Valid API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return tenant


async def check_tenant_feature(
    feature: str,
    tenant: Optional[Tenant] = Depends(get_current_tenant),
) -> bool:
    """Check if tenant has access to a specific feature.

    Usage:
        @router.get("/premium-feature")
        async def premium_feature(
            has_feature: bool = Depends(lambda: check_tenant_feature("white_label")),
        ):
            if not has_feature:
                raise HTTPException(403, "Feature not available in your plan")
    """
    if not tenant:
        return False

    from app.services.tenant_service import PLAN_LIMITS

    plan_features = PLAN_LIMITS.get(tenant.plan, {}).get("features", [])
    return feature in plan_features


def require_feature(feature: str):
    """Dependency factory for requiring specific features.

    Usage:
        @router.get("/analytics")
        async def get_analytics(
            _: None = Depends(require_feature("analytics")),
            tenant: Tenant = Depends(require_tenant),
        ):
            ...
    """
    async def _require_feature(
        tenant: Tenant = Depends(require_tenant),
    ):
        from app.services.tenant_service import PLAN_LIMITS

        plan_features = PLAN_LIMITS.get(tenant.plan, {}).get("features", [])
        if feature not in plan_features:
            raise HTTPException(
                status_code=403,
                detail=f"Feature '{feature}' is not available in your plan. Please upgrade.",
            )
        return None

    return _require_feature
