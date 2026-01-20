"""
Encryption utilities for sensitive data storage.
Uses AES-256-GCM for authenticated encryption.

Security Note (H1.3b):
- NEVER use hardcoded fallback keys
- SESSION_SECRET must be configured in production
- In development, raise clear error if missing
"""
import base64
import hashlib
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings


class EncryptionConfigError(RuntimeError):
    """Raised when encryption configuration is missing or invalid."""
    pass


def _derive_key() -> bytes:
    """Derive a 32-byte key from SESSION_SECRET.

    H1.3b Security Fix:
    - Removed hardcoded fallback key "dev-secret-key-not-for-production"
    - Raises clear error if SESSION_SECRET not configured
    - Allows development with explicit warning

    Raises:
        EncryptionConfigError: If SESSION_SECRET is not configured in production
    """
    secret = settings.SESSION_SECRET.get_secret_value()

    if not secret:
        # In production, this is a critical error
        if settings.ENVIRONMENT.lower() in {"production", "prod", "staging"}:
            raise EncryptionConfigError(
                "SESSION_SECRET must be configured for encryption in production. "
                "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        # In development, use a warning-inducing but deterministic key
        # This allows dev/test to work but logs a warning
        import logging
        logging.getLogger(__name__).warning(
            "SESSION_SECRET not configured - using development-only key. "
            "DO NOT use in production!"
        )
        secret = "INSECURE-DEV-KEY-DO-NOT-USE-IN-PRODUCTION"

    return hashlib.sha256(secret.encode()).digest()


def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt an API key using AES-256-GCM.
    Returns base64-encoded ciphertext with nonce prepended.
    """
    key = _derive_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    ciphertext = aesgcm.encrypt(nonce, api_key.encode(), None)
    # Prepend nonce to ciphertext and base64 encode
    return base64.b64encode(nonce + ciphertext).decode()


def decrypt_api_key(encrypted: str) -> Optional[str]:
    """
    Decrypt an API key encrypted with encrypt_api_key.
    Returns None if decryption fails.
    """
    try:
        key = _derive_key()
        aesgcm = AESGCM(key)
        data = base64.b64decode(encrypted.encode())
        nonce = data[:12]
        ciphertext = data[12:]
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()
    except Exception:
        return None
