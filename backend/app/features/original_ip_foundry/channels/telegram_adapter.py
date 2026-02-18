"""Telegram channel adapter for Foundry webhook routing."""
from __future__ import annotations

import logging
import uuid

import httpx

from app.features.original_ip_foundry.channel_port import (
    ChannelEvent,
    ChannelMediaUpload,
    ChannelPort,
    ChannelReply,
)
from app.features.original_ip_foundry.webhook_signature import (
    WebhookSignatureError,
    WebhookSignatureVerifier,
)

logger = logging.getLogger(__name__)


class TelegramChannelAdapter(ChannelPort):
    """Adapter for Telegram Bot API."""

    CHANNEL_NAME = "telegram"

    def __init__(self, bot_token: str = "", webhook_secret: str = ""):
        self._bot_token = bot_token
        self._webhook_secret = webhook_secret
        self._api_base = f"https://api.telegram.org/bot{bot_token}" if bot_token else ""

    async def ingest_event(self, raw_payload: dict, *, headers: dict | None = None) -> ChannelEvent:
        """Parse Telegram Update into ChannelEvent."""
        # Verify signature if a webhook secret is configured
        if self._webhook_secret:
            hdr = headers or {}
            token = hdr.get("x-telegram-bot-api-secret-token") or ""
            if not WebhookSignatureVerifier.verify_telegram(self._webhook_secret, token):
                raise WebhookSignatureError("telegram", "invalid or missing secret token")
        message = raw_payload.get("message") or {}
        chat = message.get("chat") or {}
        text = message.get("text") or ""
        chat_id = str(chat.get("id") or "")
        update_id = str(raw_payload.get("update_id") or uuid.uuid4().hex[:12])

        attachments: list[str] = []
        if message.get("photo"):
            photos = message["photo"]
            if photos:
                attachments.append(photos[-1].get("file_id", ""))
        if message.get("document"):
            attachments.append(message["document"].get("file_id", ""))

        return ChannelEvent(
            event_id=f"tg-{update_id}",
            channel=self.CHANNEL_NAME,
            user_id=chat_id,
            text=text,
            attachments=attachments,
            metadata={"chat_type": chat.get("type", "private")},
            raw_payload=raw_payload,
        )

    async def send_reply(self, reply: ChannelReply) -> dict:
        """Send text message via Telegram Bot API."""
        if not self._api_base:
            return {"status": "skipped", "reason": "no_bot_token"}

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self._api_base}/sendMessage",
                json={
                    "chat_id": reply.user_id,
                    "text": reply.text,
                    "parse_mode": "Markdown",
                },
            )
            return {"status": "sent", "telegram_response": resp.json()}

    async def upload_media(self, upload: ChannelMediaUpload) -> dict:
        """Upload media via Telegram Bot API."""
        if not self._api_base:
            return {"status": "skipped", "reason": "no_bot_token"}

        endpoint = "/sendPhoto" if upload.media_type == "image" else "/sendDocument"
        payload_key = "photo" if upload.media_type == "image" else "document"

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self._api_base}{endpoint}",
                json={
                    "chat_id": upload.user_id,
                    payload_key: upload.media_url,
                    "caption": upload.caption,
                },
            )
            return {"status": "sent", "telegram_response": resp.json()}
