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
