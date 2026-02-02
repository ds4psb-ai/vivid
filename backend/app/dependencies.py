"""FastAPI dependencies module.

Provides common dependencies for routers.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Depends, Header, HTTPException, Request, status

from app.auth import get_user_id, require_user_id, get_is_admin
from app.config import settings


async def get_current_user(
    request: Request,
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
) -> Dict[str, Any]:
    """Get current user from session or header.
    
    Returns a dict with user information. For development, creates a mock user
    if no authentication is present.
    
    Args:
        request: FastAPI request
        x_user_id: Optional user ID header (for development/testing)
        
    Returns:
        User dict with at least 'id' key
        
    Raises:
        HTTPException 401 if user not found in production
    """
    user_id = await get_user_id(request, x_user_id)
    
    if not user_id:
        # In development, allow anonymous access with mock user
        if settings.ENVIRONMENT.lower() in {"development", "dev", "local"}:
            user_id = "dev-user-001"
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
    
    is_admin = await get_is_admin(request)
    
    return {
        "id": user_id,
        "user_id": user_id,  # Alias for compatibility
        "is_admin": is_admin,
    }


async def get_optional_user_id(
    request: Request,
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
) -> Optional[str]:
    """Get user ID if authenticated, else return None.
    
    Returns just the user ID string, not the full user dict.
    Useful for endpoints that optionally personalize based on user.
    """
    user_id = await get_user_id(request, x_user_id)
    return user_id


async def get_current_user_id(
    request: Request,
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
) -> str:
    """Get current user ID as a string.
    
    Returns just the user ID string, not the full user dict.
    For development, returns "dev-user-001" if no auth.
    
    Use this when you only need the user_id string (e.g., for DB inserts).
    """
    user_id = await get_user_id(request, x_user_id)
    
    if not user_id:
        if settings.ENVIRONMENT.lower() in {"development", "dev", "local"}:
            user_id = "dev-user-001"
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
    
    return user_id


async def get_current_user_optional(
    request: Request,
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, else return None.
    
    Unlike get_current_user, this does not create a mock user in development.
    Returns None if user is not authenticated.
    """
    user_id = await get_user_id(request, x_user_id)
    
    if not user_id:
        return None
    
    is_admin = await get_is_admin(request)
    
    return {
        "id": user_id,
        "user_id": user_id,
        "is_admin": is_admin,
    }


async def require_authenticated_user(
    request: Request,
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
) -> Dict[str, Any]:
    """Require authenticated user.
    
    Same as get_current_user but always raises 401 if not authenticated,
    regardless of environment.
    """
    user_id = await require_user_id(request, x_user_id)
    is_admin = await get_is_admin(request)
    
    return {
        "id": user_id,
        "user_id": user_id,
        "is_admin": is_admin,
    }


async def require_admin(
    user: Dict[str, Any] = Depends(require_authenticated_user),
) -> Dict[str, Any]:
    """Require admin user.

    Raises HTTPException 403 if user is not admin.
    """
    if not user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def require_flow_enabled() -> None:
    """Gate for Flow/Workflow feature.

    Raises HTTPException 403 if FLOW_ENABLED is False.
    Use as a dependency on all workflow endpoints.
    """
    if not settings.FLOW_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Flow feature is currently disabled",
        )
