"""Google OAuth and session endpoints."""
from __future__ import annotations

import secrets
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode, quote

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from app.middleware.rate_limit import limiter, RATE_LIMIT_AUTH_LOGIN
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_tokens import create_token, decode_token
from app.config import settings
from app.credit_service import get_or_create_user_credits
from app.database import get_db
from app.dependencies import require_authenticated_user
from app.middleware.csrf import generate_csrf_token
from app.models import UserAccount, CrebitApplication

CSRF_COOKIE_NAME = "csrf_token"

router = APIRouter()


def _require_oauth_config() -> None:
    # H1.3: Use get_secret_value() for SecretStr fields
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET.get_secret_value():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured",
        )
    if not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth redirect URI not configured",
        )
    if not settings.SESSION_SECRET.get_secret_value():
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
    # H1.3: Use get_secret_value() for SecretStr
    secret = settings.SESSION_SECRET.get_secret_value()
    payload = decode_token(state, secret)
    cookie_payload = decode_token(cookie_state, secret)
    if not payload or not cookie_payload:
        return False
    if payload.get("purpose") != "oauth_state":
        return False
    return payload.get("nonce") == cookie_payload.get("nonce")


def _error_redirect(reason: str) -> RedirectResponse:
    target = settings.AUTH_ERROR_REDIRECT
    separator = "&" if "?" in target else "?"
    return RedirectResponse(f"{target}{separator}reason={quote(reason)}")


@router.get("/status")
async def auth_status() -> JSONResponse:
    """Check if OAuth is configured and available."""
    try:
        google_configured = bool(
            settings.GOOGLE_CLIENT_ID
            and settings.GOOGLE_CLIENT_SECRET.get_secret_value()
            and settings.GOOGLE_REDIRECT_URI
        )
        session_configured = bool(settings.SESSION_SECRET.get_secret_value())
    except Exception:
        google_configured = False
        session_configured = False

    return JSONResponse({
        "google_oauth_available": google_configured and session_configured,
        "providers": ["google"] if google_configured and session_configured else [],
    })


@router.get("/google/start")
async def google_start() -> RedirectResponse:
    _require_oauth_config()
    # H1.3: Use get_secret_value() for SecretStr
    state = create_token(
        {"purpose": "oauth_state", "nonce": secrets.token_urlsafe(16)},
        settings.SESSION_SECRET.get_secret_value(),
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
        domain=settings.COOKIE_DOMAIN or None,
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
        # H1.3: Use get_secret_value() for SecretStr
        token_resp = await client.post(
            settings.GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET.get_secret_value(),
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
    # H1.3: Use get_secret_value() for SecretStr
    session_token = create_token(session_payload, settings.SESSION_SECRET.get_secret_value(), settings.SESSION_TTL_SECONDS)
    response = RedirectResponse(settings.AUTH_SUCCESS_REDIRECT)
    response.delete_cookie(settings.OAUTH_STATE_COOKIE_NAME)
    response.set_cookie(
        settings.SESSION_COOKIE_NAME,
        session_token,
        max_age=settings.SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        domain=settings.COOKIE_DOMAIN or None,
    )
    # Set CSRF token cookie (must be readable by JS, so httponly=False)
    response.set_cookie(
        CSRF_COOKIE_NAME,
        generate_csrf_token(),
        max_age=settings.SESSION_TTL_SECONDS,
        httponly=False,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        domain=settings.COOKIE_DOMAIN or None,
    )
    return response


@router.get("/session")
async def get_session(request: Request) -> JSONResponse:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token and request.headers.get("Authorization", "").lower().startswith("bearer "):
        token = request.headers.get("Authorization").split(" ", 1)[1].strip()
    # H1.3: Use get_secret_value() for SecretStr
    payload = decode_token(token, settings.SESSION_SECRET.get_secret_value()) if token else None
    if not payload:
        return JSONResponse({"authenticated": False})

    response = JSONResponse(
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

    # Auto-set CSRF token if missing (for existing sessions before CSRF was added)
    if not request.cookies.get(CSRF_COOKIE_NAME):
        response.set_cookie(
            CSRF_COOKIE_NAME,
            generate_csrf_token(),
            max_age=settings.SESSION_TTL_SECONDS,
            httponly=False,
            samesite="lax",
            secure=settings.COOKIE_SECURE,
            domain=settings.COOKIE_DOMAIN or None,
        )

    return response


@router.get("/csrf")
async def get_csrf_token(request: Request) -> JSONResponse:
    """Get or refresh CSRF token.

    This endpoint sets a new CSRF token cookie for authenticated users.
    Useful for:
    - Existing sessions that don't have a CSRF token yet
    - Refreshing CSRF tokens periodically

    Returns 401 if not authenticated.
    """
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token and request.headers.get("Authorization", "").lower().startswith("bearer "):
        token = request.headers.get("Authorization").split(" ", 1)[1].strip()

    payload = decode_token(token, settings.SESSION_SECRET.get_secret_value()) if token else None
    if not payload:
        raise HTTPException(status_code=401, detail="Not authenticated")

    csrf_token = generate_csrf_token()
    response = JSONResponse({"csrf_token": csrf_token})
    response.set_cookie(
        CSRF_COOKIE_NAME,
        csrf_token,
        max_age=settings.SESSION_TTL_SECONDS,
        httponly=False,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        domain=settings.COOKIE_DOMAIN or None,
    )
    return response


@router.post("/logout")
@limiter.limit(RATE_LIMIT_AUTH_LOGIN)
async def logout(request: Request) -> JSONResponse:
    response = JSONResponse({"success": True})
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    response.delete_cookie(CSRF_COOKIE_NAME)
    return response


@router.get("/users/me")
async def get_current_user_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Get current user profile.

    Returns the authenticated user's profile from the database.
    """
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token and request.headers.get("Authorization", "").lower().startswith("bearer "):
        token = request.headers.get("Authorization").split(" ", 1)[1].strip()

    # H1.3: Use get_secret_value() for SecretStr
    payload = decode_token(token, settings.SESSION_SECRET.get_secret_value()) if token else None
    if not payload:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session")

    # Get full user profile from DB
    result = await db.execute(
        select(UserAccount).where(UserAccount.user_id == user_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="User not found")

    return JSONResponse({
        "user_id": account.user_id,
        "email": account.email,
        "name": account.name,
        "avatar_url": account.avatar_url,
        "role": account.role,
        "is_active": account.is_active,
        "created_at": account.created_at.isoformat() if account.created_at else None,
        "last_login_at": account.last_login_at.isoformat() if account.last_login_at else None,
    })


@router.get("/academy/access")
async def check_academy_access(
    user: dict = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Check if user has academy access (paid enrollment).

    Returns access info if the user has a paid CrebitApplication.
    Raises 403 if user is not enrolled or payment is not completed.
    Admin users (MASTER_ADMIN_EMAILS) can also access without enrollment.
    """
    user_id = user.get("user_id")
    user_email = user.get("email", "").lower()

    # Check if user is admin
    is_admin = user_email in settings.MASTER_ADMIN_EMAIL_SET

    # Check for paid application
    result = await db.execute(
        select(CrebitApplication)
        .where(CrebitApplication.owner_id == user_id)
        .where(CrebitApplication.status == "paid")
    )
    application = result.scalar_one_or_none()

    # Admin can access without enrollment
    if not application and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Academy access requires course enrollment",
        )

    return JSONResponse({
        "can_access": True,
        "cohort": application.cohort if application else None,
        "track": application.track if application else None,
        "enrolled_at": application.paid_at.isoformat() if application and application.paid_at else None,
        "is_admin": is_admin,
    })

