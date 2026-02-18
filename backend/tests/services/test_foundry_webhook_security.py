"""Tests for webhook signature verification and rate limiting."""
from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest

from app.features.original_ip_foundry.webhook_signature import (
    WebhookSignatureError,
    WebhookSignatureVerifier,
)
from app.features.original_ip_foundry.channel_router import (
    ChannelWebhookRouter,
    WebhookRateLimiter,
    WebhookRateLimitError,
)
from app.features.original_ip_foundry.channels.telegram_adapter import TelegramChannelAdapter
from app.features.original_ip_foundry.channels.kakao_adapter import KakaoChannelAdapter
from app.features.original_ip_foundry.channels.web_adapter import WebChannelAdapter


# ---------------------------------------------------------------------------
# Telegram signature tests
# ---------------------------------------------------------------------------


def test_telegram_signature_valid():
    secret = "my-secret-token"
    assert WebhookSignatureVerifier.verify_telegram(secret, secret) is True


def test_telegram_signature_invalid():
    assert WebhookSignatureVerifier.verify_telegram("real-secret", "wrong-secret") is False


def test_telegram_signature_missing():
    assert WebhookSignatureVerifier.verify_telegram("real-secret", "") is False


@pytest.mark.asyncio
async def test_telegram_adapter_rejects_bad_signature():
    adapter = TelegramChannelAdapter(bot_token="", webhook_secret="my-secret")
    payload = {"update_id": 123, "message": {"chat": {"id": 1}, "text": "hi"}}
    with pytest.raises(WebhookSignatureError, match="telegram"):
        await adapter.ingest_event(payload, headers={"x-telegram-bot-api-secret-token": "bad"})


@pytest.mark.asyncio
async def test_telegram_adapter_accepts_valid_signature():
    secret = "correct-token"
    adapter = TelegramChannelAdapter(bot_token="", webhook_secret=secret)
    payload = {"update_id": 456, "message": {"chat": {"id": 2}, "text": "hello"}}
    event = await adapter.ingest_event(
        payload, headers={"x-telegram-bot-api-secret-token": secret},
    )
    assert event.channel == "telegram"
    assert event.text == "hello"


# ---------------------------------------------------------------------------
# Kakao signature tests
# ---------------------------------------------------------------------------


def test_kakao_signature_valid():
    app_key = "kakao-app-key-123"
    body = b'{"userRequest":{"utterance":"test"}}'
    sig = hmac.new(app_key.encode(), body, hashlib.sha256).hexdigest()
    assert WebhookSignatureVerifier.verify_kakao(app_key, body, sig) is True


def test_kakao_signature_invalid():
    app_key = "kakao-app-key-123"
    body = b'{"data":"test"}'
    assert WebhookSignatureVerifier.verify_kakao(app_key, body, "bad-signature") is False


def test_kakao_signature_missing():
    assert WebhookSignatureVerifier.verify_kakao("key", b"body", "") is False


@pytest.mark.asyncio
async def test_kakao_adapter_rejects_bad_signature():
    adapter = KakaoChannelAdapter(app_key="secret-key")
    payload = {"userRequest": {"user": {"id": "u1"}, "utterance": "hi", "block": {}}}
    with pytest.raises(WebhookSignatureError, match="kakao"):
        await adapter.ingest_event(payload, headers={"x-kakaoi-signature": "wrong"})


@pytest.mark.asyncio
async def test_kakao_adapter_accepts_valid_signature():
    app_key = "secret-key"
    payload = {"userRequest": {"user": {"id": "u1"}, "utterance": "hi", "block": {}}}
    body = json.dumps(payload, ensure_ascii=False).encode()
    sig = hmac.new(app_key.encode(), body, hashlib.sha256).hexdigest()
    adapter = KakaoChannelAdapter(app_key=app_key)
    event = await adapter.ingest_event(payload, headers={"x-kakaoi-signature": sig})
    assert event.channel == "kakao"
    assert event.text == "hi"


# ---------------------------------------------------------------------------
# Generic HMAC
# ---------------------------------------------------------------------------


def test_generic_hmac_verification():
    secret = "generic-secret"
    body = b"request-body-bytes"
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert WebhookSignatureVerifier.verify_generic_hmac(secret, body, sig) is True
    assert WebhookSignatureVerifier.verify_generic_hmac(secret, body, "bad") is False


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


def test_rate_limit_allows_within_limit():
    limiter = WebhookRateLimiter(max_requests=5, window_sec=60)
    for _ in range(5):
        assert limiter.check("telegram") is True


def test_rate_limit_blocks_excess():
    limiter = WebhookRateLimiter(max_requests=3, window_sec=60)
    for _ in range(3):
        assert limiter.check("telegram") is True
    assert limiter.check("telegram") is False


def test_rate_limit_window_slides(monkeypatch):
    limiter = WebhookRateLimiter(max_requests=2, window_sec=1)
    assert limiter.check("web") is True
    assert limiter.check("web") is True
    assert limiter.check("web") is False

    # Simulate time passing beyond the window
    original_time = time.time
    monkeypatch.setattr(time, "time", lambda: original_time() + 2)
    assert limiter.check("web") is True


# ---------------------------------------------------------------------------
# Bypass / web channel
# ---------------------------------------------------------------------------


def test_signature_bypass_when_no_secret_configured():
    """When no secret is configured, adapters skip verification."""
    # Telegram with empty secret — no error raised
    adapter = TelegramChannelAdapter(bot_token="", webhook_secret="")
    # The adapter has no secret, so ingest_event should NOT raise
    import asyncio
    payload = {"update_id": 1, "message": {"chat": {"id": 1}, "text": "bypass"}}
    event = asyncio.get_event_loop().run_until_complete(
        adapter.ingest_event(payload, headers={}),
    )
    assert event.text == "bypass"


@pytest.mark.asyncio
async def test_web_channel_no_signature_required():
    """Web channel never requires signature verification."""
    adapter = WebChannelAdapter()
    payload = {"user_id": "u1", "text": "web message"}
    event = await adapter.ingest_event(payload, headers={"x-any-header": "value"})
    assert event.channel == "web"
    assert event.text == "web message"
