"""Webhook signature verification for multi-channel security."""
from __future__ import annotations

import hashlib
import hmac


class WebhookSignatureError(Exception):
    """Raised when webhook signature verification fails."""

    def __init__(self, channel: str, reason: str = "invalid signature"):
        self.channel = channel
        self.reason = reason
        super().__init__(f"[{channel}] {reason}")


class WebhookSignatureVerifier:
    """Stateless helpers for per-channel webhook signature checks."""

    @staticmethod
    def verify_telegram(secret_token: str, header_token: str) -> bool:
        """Telegram uses a simple secret token comparison.

        The bot owner sets a secret_token when registering the webhook,
        and Telegram sends it back in the X-Telegram-Bot-Api-Secret-Token header.
        """
        if not secret_token or not header_token:
            return False
        return hmac.compare_digest(secret_token, header_token)

    @staticmethod
    def verify_kakao(app_key: str, body: bytes, signature: str) -> bool:
        """Kakao i verifies via HMAC-SHA256 of the request body."""
        if not app_key or not signature:
            return False
        expected = hmac.new(app_key.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def verify_generic_hmac(
        secret: str, body: bytes, signature: str, algo: str = "sha256",
    ) -> bool:
        """Generic HMAC verification for future channels."""
        if not secret or not signature:
            return False
        h = hmac.new(secret.encode(), body, getattr(hashlib, algo))
        return hmac.compare_digest(h.hexdigest(), signature)
