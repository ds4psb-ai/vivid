"""Web/browser channel adapter for Foundry — passthrough for frontend SSE/polling."""
from __future__ import annotations

import uuid

from app.features.original_ip_foundry.channel_port import (
    ChannelEvent,
    ChannelMediaUpload,
    ChannelPort,
    ChannelReply,
)


class WebChannelAdapter(ChannelPort):
    """Passthrough adapter for web-based frontends."""

    CHANNEL_NAME = "web"

    async def ingest_event(self, raw_payload: dict, *, headers: dict | None = None) -> ChannelEvent:
        """Passthrough: raw payload already in ChannelEvent-compatible format."""
        return ChannelEvent(
            event_id=raw_payload.get("event_id") or f"web-{uuid.uuid4().hex[:12]}",
            channel=self.CHANNEL_NAME,
            user_id=raw_payload.get("user_id") or "anonymous",
            tenant_id=raw_payload.get("tenant_id") or "default",
            project_id=raw_payload.get("project_id"),
            text=raw_payload.get("text") or "",
            attachments=raw_payload.get("attachments") or [],
            metadata=raw_payload.get("metadata") or {},
            raw_payload=raw_payload,
        )

    async def send_reply(self, reply: ChannelReply) -> dict:
        """Buffer reply for frontend polling/SSE (no outbound push)."""
        return {
            "status": "buffered",
            "channel": self.CHANNEL_NAME,
            "user_id": reply.user_id,
            "text": reply.text,
            "attachments": reply.attachments,
        }

    async def upload_media(self, upload: ChannelMediaUpload) -> dict:
        """Return media URL reference for frontend rendering."""
        return {
            "status": "ready",
            "channel": self.CHANNEL_NAME,
            "user_id": upload.user_id,
            "media_url": upload.media_url,
            "media_type": upload.media_type,
            "caption": upload.caption,
        }
