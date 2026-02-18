"""Foundry access-control dependencies.

Guardrail ② — Internal Account Allowlist
Guardrail ④ — Read-only Write Guard

These FastAPI dependencies are applied to every Foundry router endpoint.
They are the *only* gate between external users and Foundry functionality.
"""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Request

from app.auth_tokens import decode_token
from app.config import settings


def _get_session_email(request: Request) -> Optional[str]:
    """Extract email from session cookie / Bearer token.

    Mirrors the pattern in ``app.auth._get_session_payload`` but returns
    only the email string.
    """
    token: Optional[str] = None
    auth_header = request.headers.get("Authorization") if request else None
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    if not token:
        token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        return None
    payload = decode_token(token, settings.SESSION_SECRET.get_secret_value())
    if not payload:
        return None
    email = payload.get("email")
    return email.lower().strip() if isinstance(email, str) else None


async def require_foundry_access(request: Request) -> str:
    """Dependency: allow only allowlisted accounts into Foundry endpoints.

    Returns the verified email.  Raises 401 (not authenticated) or 403
    (not on the allowlist).
    """
    email = _get_session_email(request)
    scope = getattr(settings, "AD_FOUNDRY_ACCESS_SCOPE", "internal")
    if not isinstance(scope, str):
        scope = "internal"
    scope = scope.lower().strip()

    if scope == "public":
        request.state.foundry_email = email or "public@anonymous"
        request.state.foundry_user_id = request.headers.get("X-User-Id", "")
        return request.state.foundry_email

    if not email:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to access Foundry.",
        )

    if scope == "authenticated":
        request.state.foundry_email = email
        request.state.foundry_user_id = request.headers.get("X-User-Id", "")
        return email

    if email not in settings.AD_FOUNDRY_ALLOWLIST_SET:
        raise HTTPException(
            status_code=403,
            detail="Foundry access denied — internal testing only.",
        )

    request.state.foundry_email = email
    request.state.foundry_user_id = request.headers.get("X-User-Id", "")
    return email


async def foundry_write_guard(request: Request) -> None:
    """Dependency: block mutating methods during read-only period.

    Applied as a *router-level* dependency so every POST/PUT/PATCH/DELETE
    is checked automatically.
    """
    safe_paths = getattr(settings, "AD_FOUNDRY_READONLY_SAFE_PATHS_SET", set())
    if not isinstance(safe_paths, set):
        safe_paths = set()

    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        if any(
            request.url.path == path or request.url.path.startswith(f"{path.rstrip('/')}/")
            for path in safe_paths
        ):
            return
        if not settings.AD_FOUNDRY_WRITE_ENABLED:
            raise HTTPException(
                status_code=403,
                detail="Foundry is in read-only mode. Contact admin to enable writes.",
            )
