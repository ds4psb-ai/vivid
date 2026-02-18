"""Port contract tests for Foundry channel adapters."""
import pytest

from app.features.original_ip_foundry.channel_port import (
    ChannelEvent,
    ChannelMediaUpload,
    ChannelReply,
)
from app.features.original_ip_foundry.channels.kakao_adapter import KakaoChannelAdapter
from app.features.original_ip_foundry.channels.telegram_adapter import TelegramChannelAdapter
from app.features.original_ip_foundry.channels.web_adapter import WebChannelAdapter
from app.features.original_ip_foundry.webhook_signature import WebhookSignatureError


# --- ingest_event returns ChannelEvent with correct channel name ---


@pytest.mark.asyncio
async def test_telegram_ingest_returns_channel_event():
    adapter = TelegramChannelAdapter(bot_token="")
    event = await adapter.ingest_event({
        "update_id": 1,
        "message": {"chat": {"id": 100}, "text": "hi"},
    })
    assert isinstance(event, ChannelEvent)
    assert event.channel == "telegram"


@pytest.mark.asyncio
async def test_kakao_ingest_returns_channel_event():
    adapter = KakaoChannelAdapter()
    event = await adapter.ingest_event({
        "userRequest": {"utterance": "hello", "user": {"id": "k1"}},
    })
    assert isinstance(event, ChannelEvent)
    assert event.channel == "kakao"


@pytest.mark.asyncio
async def test_web_ingest_returns_channel_event():
    adapter = WebChannelAdapter()
    event = await adapter.ingest_event({"user_id": "w1", "text": "hey"})
    assert isinstance(event, ChannelEvent)
    assert event.channel == "web"


# --- send_reply returns dict with expected keys ---


@pytest.mark.asyncio
async def test_telegram_send_reply_skipped_without_token():
    adapter = TelegramChannelAdapter(bot_token="")
    result = await adapter.send_reply(
        ChannelReply(channel="telegram", user_id="100", text="reply")
    )
    assert isinstance(result, dict)
    assert result["status"] == "skipped"


@pytest.mark.asyncio
async def test_kakao_send_reply_skill_format():
    adapter = KakaoChannelAdapter()
    result = await adapter.send_reply(
        ChannelReply(channel="kakao", user_id="k1", text="response")
    )
    assert isinstance(result, dict)
    assert result["version"] == "2.0"
    assert result["template"]["outputs"][0]["simpleText"]["text"] == "response"


@pytest.mark.asyncio
async def test_web_send_reply_buffered():
    adapter = WebChannelAdapter()
    result = await adapter.send_reply(
        ChannelReply(channel="web", user_id="w1", text="hi")
    )
    assert isinstance(result, dict)
    assert result["status"] == "buffered"
    assert result["text"] == "hi"


# --- upload_media returns dict with expected keys ---


@pytest.mark.asyncio
async def test_telegram_upload_media_skipped_without_token():
    adapter = TelegramChannelAdapter(bot_token="")
    result = await adapter.upload_media(
        ChannelMediaUpload(channel="telegram", user_id="100", media_url="http://img.png")
    )
    assert isinstance(result, dict)
    assert result["status"] == "skipped"


@pytest.mark.asyncio
async def test_kakao_upload_media_simple_image():
    adapter = KakaoChannelAdapter()
    result = await adapter.upload_media(
        ChannelMediaUpload(channel="kakao", user_id="k1", media_url="http://img.png", caption="test")
    )
    assert isinstance(result, dict)
    assert result["version"] == "2.0"
    assert result["template"]["outputs"][0]["simpleImage"]["imageUrl"] == "http://img.png"


@pytest.mark.asyncio
async def test_web_upload_media_returns_url():
    adapter = WebChannelAdapter()
    result = await adapter.upload_media(
        ChannelMediaUpload(channel="web", user_id="w1", media_url="http://vid.mp4", media_type="video")
    )
    assert isinstance(result, dict)
    assert result["media_url"] == "http://vid.mp4"
    assert result["media_type"] == "video"
    assert result["status"] == "ready"


# --- Telegram: parses message.text, message.chat.id, photo attachments ---


@pytest.mark.asyncio
async def test_telegram_parses_text_and_chat_id():
    adapter = TelegramChannelAdapter(bot_token="")
    event = await adapter.ingest_event({
        "update_id": 42,
        "message": {
            "chat": {"id": 555, "type": "group"},
            "text": "hello from group",
        },
    })
    assert event.user_id == "555"
    assert event.text == "hello from group"
    assert event.event_id == "tg-42"
    assert event.metadata["chat_type"] == "group"


@pytest.mark.asyncio
async def test_telegram_parses_photo_attachment():
    adapter = TelegramChannelAdapter(bot_token="")
    event = await adapter.ingest_event({
        "update_id": 99,
        "message": {
            "chat": {"id": 1},
            "text": "",
            "photo": [
                {"file_id": "small_id", "width": 100},
                {"file_id": "large_id", "width": 800},
            ],
        },
    })
    # Should use the last (largest) photo
    assert "large_id" in event.attachments


@pytest.mark.asyncio
async def test_telegram_parses_document_attachment():
    adapter = TelegramChannelAdapter(bot_token="")
    event = await adapter.ingest_event({
        "update_id": 100,
        "message": {
            "chat": {"id": 1},
            "document": {"file_id": "doc_file_id"},
        },
    })
    assert "doc_file_id" in event.attachments


# --- Kakao: parses userRequest.utterance, userRequest.user.id ---


@pytest.mark.asyncio
async def test_kakao_parses_utterance_and_user_id():
    adapter = KakaoChannelAdapter()
    event = await adapter.ingest_event({
        "userRequest": {
            "utterance": "dolly zoom effect",
            "user": {"id": "kakao-user-99"},
            "block": {"id": "blk1", "name": "scene_block"},
            "timezone": "Asia/Seoul",
        },
    })
    assert event.text == "dolly zoom effect"
    assert event.user_id == "kakao-user-99"
    assert event.metadata["block_id"] == "blk1"
    assert event.metadata["block_name"] == "scene_block"


# --- Web: passthrough preserves raw_payload fields ---


@pytest.mark.asyncio
async def test_web_passthrough_preserves_fields():
    payload = {
        "event_id": "web-custom-1",
        "user_id": "user-abc",
        "tenant_id": "tenant-x",
        "project_id": "proj-y",
        "text": "full passthrough",
        "attachments": ["a.png"],
        "metadata": {"custom": "value"},
    }
    adapter = WebChannelAdapter()
    event = await adapter.ingest_event(payload)
    assert event.event_id == "web-custom-1"
    assert event.user_id == "user-abc"
    assert event.tenant_id == "tenant-x"
    assert event.project_id == "proj-y"
    assert event.text == "full passthrough"
    assert event.attachments == ["a.png"]
    assert event.metadata == {"custom": "value"}
    assert event.raw_payload == payload


@pytest.mark.asyncio
async def test_web_defaults_for_missing_fields():
    adapter = WebChannelAdapter()
    event = await adapter.ingest_event({})
    assert event.user_id == "anonymous"
    assert event.tenant_id == "default"
    assert event.text == ""
    assert event.attachments == []


# --- Telegram: signature verification failure raises WebhookSignatureError ---


@pytest.mark.asyncio
async def test_telegram_signature_failure():
    adapter = TelegramChannelAdapter(bot_token="", webhook_secret="my-secret")
    with pytest.raises(WebhookSignatureError) as exc_info:
        await adapter.ingest_event(
            {"update_id": 1, "message": {"chat": {"id": 1}, "text": "x"}},
            headers={"x-telegram-bot-api-secret-token": "wrong-secret"},
        )
    assert exc_info.value.channel == "telegram"


@pytest.mark.asyncio
async def test_telegram_signature_missing_header():
    adapter = TelegramChannelAdapter(bot_token="", webhook_secret="my-secret")
    with pytest.raises(WebhookSignatureError):
        await adapter.ingest_event(
            {"update_id": 1, "message": {"chat": {"id": 1}, "text": "x"}},
            headers={},
        )


@pytest.mark.asyncio
async def test_telegram_signature_passes_with_correct_token():
    adapter = TelegramChannelAdapter(bot_token="", webhook_secret="correct-secret")
    event = await adapter.ingest_event(
        {"update_id": 1, "message": {"chat": {"id": 1}, "text": "ok"}},
        headers={"x-telegram-bot-api-secret-token": "correct-secret"},
    )
    assert event.text == "ok"


# --- Kakao: signature verification failure raises WebhookSignatureError ---


@pytest.mark.asyncio
async def test_kakao_signature_failure():
    adapter = KakaoChannelAdapter(app_key="test-app-key")
    with pytest.raises(WebhookSignatureError) as exc_info:
        await adapter.ingest_event(
            {"userRequest": {"utterance": "hi", "user": {"id": "u1"}}},
            headers={"x-kakaoi-signature": "invalid-sig"},
        )
    assert exc_info.value.channel == "kakao"


@pytest.mark.asyncio
async def test_kakao_signature_missing_header():
    adapter = KakaoChannelAdapter(app_key="test-app-key")
    with pytest.raises(WebhookSignatureError):
        await adapter.ingest_event(
            {"userRequest": {"utterance": "hi", "user": {"id": "u1"}}},
            headers={},
        )
