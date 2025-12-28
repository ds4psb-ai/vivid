"""Signed token helpers for lightweight session state."""
from __future__ import annotations

import base64
import hmac
import hashlib
import json
import time
from typing import Any, Dict, Optional

TOKEN_VERSION = "v1"


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64decode(encoded: str) -> bytes:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(encoded + padding)


def _sign(payload_b64: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest


def create_token(payload: Dict[str, Any], secret: str, ttl_seconds: int) -> str:
    if not secret:
        raise ValueError("Session secret is required")
    now = int(time.time())
    data = {
        **payload,
        "iat": now,
        "exp": now + max(ttl_seconds, 1),
        "ver": TOKEN_VERSION,
    }
    payload_b64 = _b64encode(json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signature = _sign(payload_b64, secret)
    return f"{TOKEN_VERSION}.{payload_b64}.{signature}"


def decode_token(token: str, secret: str) -> Optional[Dict[str, Any]]:
    if not token or not secret:
        return None
    try:
        version, payload_b64, signature = token.split(".", 2)
    except ValueError:
        return None
    if version != TOKEN_VERSION:
        return None
    expected = _sign(payload_b64, secret)
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        payload = json.loads(_b64decode(payload_b64))
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    exp = payload.get("exp")
    if isinstance(exp, int) and exp < int(time.time()):
        return None
    return payload
