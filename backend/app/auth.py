"""Session-aware auth dependencies with header fallback."""
from typing import Optional, Dict, Any

from fastapi import Header, Request

from app.auth_tokens import decode_token
from app.config import settings


def _get_session_payload(request: Request) -> Optional[Dict[str, Any]]:
    token = None
    auth_header = request.headers.get("Authorization") if request else None
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    if not token:
        token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        return None
    return decode_token(token, settings.SESSION_SECRET)


async def get_user_id(
    request: Request,
    x_user_id: Optional[str] = Header(default=None),
) -> Optional[str]:
    payload = _get_session_payload(request)
    if payload and isinstance(payload.get("user_id"), str):
        return payload["user_id"]
    return x_user_id


async def get_is_admin(
    request: Request,
    x_admin_mode: Optional[str] = Header(default=None),
) -> bool:
    payload = _get_session_payload(request)
    if payload:
        role = payload.get("role")
        if isinstance(role, str) and role.lower() in {"admin", "master"}:
            return True
    if settings.ENVIRONMENT.lower() in {"production", "prod"}:
        return False
    if x_admin_mode is None:
        return False
    return str(x_admin_mode).strip().lower() in {"1", "true", "yes", "admin"}


async def get_is_verified(
    request: Request,
    x_user_verified: Optional[str] = Header(default=None),
) -> bool:
    payload = _get_session_payload(request)
    if payload:
        verified = payload.get("verified")
        if isinstance(verified, bool):
            return verified
        if isinstance(verified, str):
            return verified.strip().lower() in {"1", "true", "yes"}
    if x_user_verified is None:
        return False
    return str(x_user_verified).strip().lower() in {"1", "true", "yes"}
