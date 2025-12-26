"""Simple header-based auth for MVP."""
from typing import Optional

from fastapi import Header


async def get_user_id(x_user_id: Optional[str] = Header(default=None)) -> Optional[str]:
    return x_user_id


async def get_is_admin(x_admin_mode: Optional[str] = Header(default=None)) -> bool:
    if x_admin_mode is None:
        return False
    return str(x_admin_mode).strip().lower() in {"1", "true", "yes", "admin"}


async def get_is_verified(
    x_user_verified: Optional[str] = Header(default=None),
) -> bool:
    if x_user_verified is None:
        return False
    return str(x_user_verified).strip().lower() in {"1", "true", "yes"}
