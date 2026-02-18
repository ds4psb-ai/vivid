"""Tests for Channel Port, adapters, and webhook router."""
import pytest

from app.features.original_ip_foundry.channel_port import (
    ChannelEvent, ChannelReply, ChannelMediaUpload, ChannelPort,
)
from app.features.original_ip_foundry.channels.telegram_adapter import TelegramChannelAdapter
from app.features.original_ip_foundry.channels.web_adapter import WebChannelAdapter
from app.features.original_ip_foundry.channels.kakao_adapter import KakaoChannelAdapter
from app.features.original_ip_foundry.channel_router import ChannelWebhookRouter


@pytest.mark.asyncio
async def test_web_ingest_passthrough():
    adapter = WebChannelAdapter()
    event = await adapter.ingest_event({"event_id": "e1", "user_id": "u1", "text": "hello"})
    assert event.channel == "web"
    assert event.user_id == "u1"
    assert event.text == "hello"


@pytest.mark.asyncio
async def test_web_reply_buffered():
    adapter = WebChannelAdapter()
    result = await adapter.send_reply(ChannelReply(channel="web", user_id="u1", text="hi"))
    assert result["status"] == "buffered"


@pytest.mark.asyncio
async def test_web_upload_returns_url():
    adapter = WebChannelAdapter()
    result = await adapter.upload_media(
        ChannelMediaUpload(channel="web", user_id="u1", media_url="http://img.png")
    )
    assert result["media_url"] == "http://img.png"


@pytest.mark.asyncio
async def test_telegram_ingest_parses_message():
    adapter = TelegramChannelAdapter(bot_token="")
    event = await adapter.ingest_event({
        "update_id": 12345,
        "message": {"chat": {"id": 999, "type": "private"}, "text": "test message"},
    })
    assert event.channel == "telegram"
    assert event.user_id == "999"
    assert event.text == "test message"


@pytest.mark.asyncio
async def test_telegram_reply_skips_without_token():
    adapter = TelegramChannelAdapter(bot_token="")
    result = await adapter.send_reply(ChannelReply(channel="telegram", user_id="999", text="hi"))
    assert result["status"] == "skipped"


@pytest.mark.asyncio
async def test_kakao_ingest_parses_utterance():
    adapter = KakaoChannelAdapter()
    event = await adapter.ingest_event({
        "userRequest": {
            "utterance": "tracking shot",
            "user": {"id": "kakao-user-1"},
            "block": {"id": "b1", "name": "main"},
        }
    })
    assert event.channel == "kakao"
    assert event.text == "tracking shot"


@pytest.mark.asyncio
async def test_kakao_reply_skill_format():
    adapter = KakaoChannelAdapter()
    result = await adapter.send_reply(ChannelReply(channel="kakao", user_id="u1", text="reply"))
    assert result["version"] == "2.0"
    assert result["template"]["outputs"][0]["simpleText"]["text"] == "reply"


@pytest.mark.asyncio
async def test_webhook_router_processes_event():
    router = ChannelWebhookRouter()
    result = await router.handle_webhook("web", {"event_id": "e1", "user_id": "u1", "text": "hi"})
    assert result["status"] == "processed"
    assert result["event_id"] == "e1"


@pytest.mark.asyncio
async def test_webhook_router_dedup():
    router = ChannelWebhookRouter()
    await router.handle_webhook("web", {"event_id": "dup-1", "user_id": "u1", "text": "hi"})
    result = await router.handle_webhook("web", {"event_id": "dup-1", "user_id": "u1", "text": "hi"})
    assert result["status"] == "duplicate"


@pytest.mark.asyncio
async def test_webhook_router_monitoring():
    router = ChannelWebhookRouter()
    await router.handle_webhook("web", {"event_id": "m1", "user_id": "u1", "text": "x"})
    stats = router.get_monitoring()
    assert stats["event_counts"]["web"] == 1
    assert "web" in stats["supported_channels"]
