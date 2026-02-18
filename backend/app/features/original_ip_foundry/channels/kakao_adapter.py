"""Kakao i (Skill) channel adapter for Foundry webhook routing."""
from __future__ import annotations

import json
import logging
import uuid

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


class KakaoChannelAdapter(ChannelPort):
    """Adapter for Kakao i Open Builder Skill callback format."""

    CHANNEL_NAME = "kakao"

    def __init__(self, app_key: str = ""):
        self._app_key = app_key

    async def ingest_event(self, raw_payload: dict, *, headers: dict | None = None) -> ChannelEvent:
        """Parse Kakao i Skill callback into ChannelEvent."""
        # Verify signature if an app key is configured
        if self._app_key:
            hdr = headers or {}
            signature = hdr.get("x-kakaoi-signature") or ""
            body = json.dumps(raw_payload, ensure_ascii=False).encode()
            if not WebhookSignatureVerifier.verify_kakao(self._app_key, body, signature):
                raise WebhookSignatureError("kakao", "invalid or missing signature")
        user_request = raw_payload.get("userRequest") or {}
        user = user_request.get("user") or {}
        utterance = user_request.get("utterance") or ""
        user_id = user.get("id") or f"kakao-{uuid.uuid4().hex[:8]}"
        block = user_request.get("block") or {}

        return ChannelEvent(
            event_id=f"kakao-{uuid.uuid4().hex[:12]}",
            channel=self.CHANNEL_NAME,
            user_id=user_id,
            text=utterance,
            metadata={
                "block_id": block.get("id", ""),
                "block_name": block.get("name", ""),
                "timezone": user_request.get("timezone", "Asia/Seoul"),
            },
            raw_payload=raw_payload,
        )

    async def send_reply(self, reply: ChannelReply) -> dict:
        """Return Kakao i Skill response format (simpleText)."""
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {"simpleText": {"text": reply.text}},
                ],
            },
        }

    async def upload_media(self, upload: ChannelMediaUpload) -> dict:
        """Return Kakao i Skill response with simpleImage card."""
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleImage": {
                            "imageUrl": upload.media_url,
                            "altText": upload.caption or "Foundry media",
                        },
                    },
                ],
            },
        }
