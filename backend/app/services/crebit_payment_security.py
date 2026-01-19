"""Crebit payment security helpers."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional

CONFIRM_TOKEN_TTL_HOURS = 24


def generate_confirm_token() -> str:
    """Generate a random confirm token for anonymous payment confirmation."""
    return secrets.token_urlsafe(32)


def hash_confirm_token(token: str) -> str:
    """Hash confirm token with SHA-256 for storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_confirm_token(token: str, token_hash: Optional[str]) -> bool:
    """Verify a confirm token against stored hash."""
    if not token_hash:
        return False
    candidate = hash_confirm_token(token)
    return hmac.compare_digest(candidate, token_hash)


def get_confirm_token_expiry(now: Optional[datetime] = None) -> datetime:
    """Return expiry timestamp for confirm token."""
    if now is None:
        now = datetime.utcnow()
    return now + timedelta(hours=CONFIRM_TOKEN_TTL_HOURS)


def normalize_amount_str(amount_raw: Optional[str], amount: int) -> str:
    """Normalize amount string used for signature verification."""
    if amount_raw:
        return amount_raw.strip()
    return str(amount)


def compute_nicepay_auth_signature(
    auth_token: str,
    client_id: str,
    amount_str: str,
    secret_key: str,
) -> str:
    """Compute NICEPAY auth signature (sha256 hex)."""
    payload = f"{auth_token}{client_id}{amount_str}{secret_key}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
