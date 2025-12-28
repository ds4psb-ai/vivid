"""Google OAuth and session endpoints."""
from __future__ import annotations

import secrets
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode, quote

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_tokens import create_token, decode_token
from app.config import settings
from app.credit_service import get_or_create_user_credits
from app.database import get_db
from app.models import UserAccount

router = APIRouter()


def _require_oauth_config() -> None:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured",
        )
    if not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth redirect URI not configured",
        )
    if not settings.SESSION_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session secret not configured",
        )


def _build_google_auth_url(state: str) -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": settings.GOOGLE_OAUTH_SCOPES,
        "state": state,
        "access_type": "online",
        "prompt": "consent",
    }
    return f"{settings.GOOGLE_AUTH_URL}?{urlencode(params)}"


def _validate_state(state: Optional[str], cookie_state: Optional[str]) -> bool:
    if not state or not cookie_state:
        return False
    payload = decode_token(state, settings.SESSION_SECRET)
    cookie_payload = decode_token(cookie_state, settings.SESSION_SECRET)
    if not payload or not cookie_payload:
        return False
    if payload.get("purpose") != "oauth_state":
        return False
    return payload.get("nonce") == cookie_payload.get("nonce")


def _error_redirect(reason: str) -> RedirectResponse:
    target = settings.AUTH_ERROR_REDIRECT
    separator = "&" if "?" in target else "?"
    return RedirectResponse(f"{target}{separator}reason={quote(reason)}")


@router.get("/google/start")
async def google_start() -> RedirectResponse:
    _require_oauth_config()
    state = create_token(
        {"purpose": "oauth_state", "nonce": secrets.token_urlsafe(16)},
        settings.SESSION_SECRET,
        settings.OAUTH_STATE_TTL_SECONDS,
    )
    response = RedirectResponse(_build_google_auth_url(state))
    response.set_cookie(
        settings.OAUTH_STATE_COOKIE_NAME,
        state,
        max_age=settings.OAUTH_STATE_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
    )
    return response


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    _require_oauth_config()
    cookie_state = request.cookies.get(settings.OAUTH_STATE_COOKIE_NAME)
    if not _validate_state(state, cookie_state):
        return _error_redirect("invalid_state")
    if not code:
        return _error_redirect("missing_code")

    async with httpx.AsyncClient(timeout=15) as client:
        token_resp = await client.post(
            settings.GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code >= 400:
            return _error_redirect("token_exchange_failed")
        token_data = token_resp.json()
        id_token = token_data.get("id_token")
        if not id_token:
            return _error_redirect("missing_id_token")

        info_resp = await client.get(
            settings.GOOGLE_TOKEN_INFO_URL,
            params={"id_token": id_token},
        )
        if info_resp.status_code >= 400:
            return _error_redirect("token_info_failed")
        info = info_resp.json()

    email = info.get("email")
    sub = info.get("sub")
    if not email or not sub:
        return _error_redirect("missing_profile")

    name = info.get("name") or ""
    avatar_url = info.get("picture") or ""
    email_verified = info.get("email_verified") in (True, "true", "True", "1", 1)
    role = "master" if email.lower() in settings.MASTER_ADMIN_EMAIL_SET else "user"
    user_id = f"google:{sub}"

    result = await db.execute(
        select(UserAccount).where(
            UserAccount.provider == "google",
            UserAccount.provider_user_id == sub,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        email_result = await db.execute(
            select(UserAccount).where(
                UserAccount.provider == "google",
                UserAccount.email == email,
            )
        )
        account = email_result.scalar_one_or_none()
        if account:
            account.provider_user_id = sub
            account.user_id = user_id
        else:
            account = UserAccount(
                user_id=user_id,
                provider="google",
                provider_user_id=sub,
                email=email,
            )
            db.add(account)

    account.email = email
    account.name = name or account.name
    account.avatar_url = avatar_url or account.avatar_url
    account.role = role
    account.is_active = True
    account.last_login_at = datetime.utcnow()
    await db.commit()
    await db.refresh(account)

    await get_or_create_user_credits(db, account.user_id)

    session_payload = {
        "user_id": account.user_id,
        "email": account.email,
        "name": account.name,
        "role": account.role,
        "verified": email_verified,
    }
    session_token = create_token(session_payload, settings.SESSION_SECRET, settings.SESSION_TTL_SECONDS)
    response = RedirectResponse(settings.AUTH_SUCCESS_REDIRECT)
    response.delete_cookie(settings.OAUTH_STATE_COOKIE_NAME)
    response.set_cookie(
        settings.SESSION_COOKIE_NAME,
        session_token,
        max_age=settings.SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
    )
    return response


@router.get("/session")
async def get_session(request: Request) -> JSONResponse:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token and request.headers.get("Authorization", "").lower().startswith("bearer "):
        token = request.headers.get("Authorization").split(" ", 1)[1].strip()
    payload = decode_token(token, settings.SESSION_SECRET) if token else None
    if not payload:
        return JSONResponse({"authenticated": False})
    return JSONResponse(
        {
            "authenticated": True,
            "user": {
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "name": payload.get("name"),
                "role": payload.get("role"),
                "verified": payload.get("verified"),
            },
        }
    )


@router.post("/logout")
async def logout() -> JSONResponse:
    response = JSONResponse({"success": True})
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    return response
