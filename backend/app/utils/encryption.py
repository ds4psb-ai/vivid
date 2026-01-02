"""
Encryption utilities for sensitive data storage.
Uses AES-256-GCM for authenticated encryption.
"""
import base64
import hashlib
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings


def _derive_key() -> bytes:
    """Derive a 32-byte key from SESSION_SECRET."""
    secret = settings.SESSION_SECRET or "dev-secret-key-not-for-production"
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
