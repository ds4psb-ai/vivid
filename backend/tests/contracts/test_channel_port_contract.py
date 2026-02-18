"""Contract tests for the ChannelPort ABC across all 3 adapters."""
from __future__ import annotations

import pytest

from app.features.original_ip_foundry.channel_port import (
    ChannelEvent,
    ChannelMediaUpload,
    ChannelPort,
    ChannelReply,
)
from app.features.original_ip_foundry.channels import (
    KakaoChannelAdapter,
    TelegramChannelAdapter,
    WebChannelAdapter,
)


class ChannelPortContractMixin:
    """Mixin that defines the channel port contract.

    Each concrete test class must implement ``get_implementation`` and
    ``sample_payload``.
    """

    def get_implementation(self) -> ChannelPort:
        raise NotImplementedError

    def sample_payload(self) -> dict:
        raise NotImplementedError

    # -- contract tests -------------------------------------------------------

    @pytest.mark.asyncio
    async def test_ingest_returns_channel_event(self):
        adapter = self.get_implementation()
        event = await adapter.ingest_event(self.sample_payload())
        assert isinstance(event, ChannelEvent)

    @pytest.mark.asyncio
    async def test_event_has_required_fields(self):
        adapter = self.get_implementation()
        event = await adapter.ingest_event(self.sample_payload())
        assert event.event_id != ""
        assert event.channel == adapter.CHANNEL_NAME
        assert event.user_id != ""

    @pytest.mark.asyncio
    async def test_send_reply_returns_dict(self):
        adapter = self.get_implementation()
        reply = ChannelReply(
            channel=adapter.CHANNEL_NAME,
            user_id="test_user_123",
            text="Hello from contract test",
        )
        result = await adapter.send_reply(reply)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_upload_media_returns_dict(self):
        adapter = self.get_implementation()
        upload = ChannelMediaUpload(
            channel=adapter.CHANNEL_NAME,
            user_id="test_user_123",
            media_url="https://example.com/test.png",
            media_type="image",
            caption="test image",
        )
        result = await adapter.upload_media(upload)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_channel_name_is_set(self):
        adapter = self.get_implementation()
        assert adapter.CHANNEL_NAME != ""

    @pytest.mark.asyncio
    async def test_ingest_preserves_text(self):
        adapter = self.get_implementation()
        event = await adapter.ingest_event(self.sample_payload())
        # Every adapter should extract some text from the payload
        assert isinstance(event.text, str)

    @pytest.mark.asyncio
    async def test_event_raw_payload_stored(self):
        adapter = self.get_implementation()
        payload = self.sample_payload()
        event = await adapter.ingest_event(payload)
        assert event.raw_payload == payload

    @pytest.mark.asyncio
    async def test_event_metadata_is_dict(self):
        adapter = self.get_implementation()
        event = await adapter.ingest_event(self.sample_payload())
        assert isinstance(event.metadata, dict)


# -- Concrete implementations -------------------------------------------------


class TestTelegramChannelPort(ChannelPortContractMixin):
    def get_implementation(self) -> ChannelPort:
        return TelegramChannelAdapter(bot_token="")

    def sample_payload(self) -> dict:
        return {
            "update_id": 12345,
            "message": {
                "message_id": 1,
                "chat": {"id": 999, "type": "private"},
                "text": "Hello Foundry",
            },
        }


class TestKakaoChannelPort(ChannelPortContractMixin):
    def get_implementation(self) -> ChannelPort:
        return KakaoChannelAdapter()

    def sample_payload(self) -> dict:
        return {
            "userRequest": {
                "user": {"id": "kakao_user_42"},
                "utterance": "Hello Foundry",
                "block": {"id": "block_1", "name": "test_block"},
                "timezone": "Asia/Seoul",
            },
        }


class TestWebChannelPort(ChannelPortContractMixin):
    def get_implementation(self) -> ChannelPort:
        return WebChannelAdapter()

    def sample_payload(self) -> dict:
        return {
            "event_id": "web-evt-001",
            "user_id": "web_user_7",
            "tenant_id": "default",
            "text": "Hello Foundry",
            "metadata": {"browser": "chrome"},
        }
