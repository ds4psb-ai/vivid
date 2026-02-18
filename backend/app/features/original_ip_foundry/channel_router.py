"""Channel webhook router with dedup and memory integration."""
from __future__ import annotations

import collections
import logging
import time

from app.features.original_ip_foundry.channel_port import (
    ChannelMediaUpload,
    ChannelPort,
    ChannelReply,
)
from app.features.original_ip_foundry.channels.telegram_adapter import TelegramChannelAdapter
from app.features.original_ip_foundry.channels.web_adapter import WebChannelAdapter
from app.features.original_ip_foundry.channels.kakao_adapter import KakaoChannelAdapter
from app.features.original_ip_foundry.memory_adapter import OpenClawMemoryAdapter
from app.features.original_ip_foundry.webhook_signature import WebhookSignatureError

logger = logging.getLogger(__name__)

DEDUP_TTL_SEC = 3600  # 1 hour
RATE_LIMIT_WINDOW_SEC = 60  # sliding window


class WebhookRateLimitError(Exception):
    """Raised when a channel exceeds its rate limit."""

    def __init__(self, channel: str):
        self.channel = channel
        super().__init__(f"Rate limit exceeded for channel: {channel}")


class WebhookRateLimiter:
    """Per-channel sliding-window rate limiter using a deque of timestamps."""

    def __init__(self, max_requests: int = 60, window_sec: int = RATE_LIMIT_WINDOW_SEC):
        self._max = max_requests
        self._window = window_sec
        self._buckets: dict[str, collections.deque[float]] = {}

    def check(self, channel: str) -> bool:
        """Return True if request is allowed, False if rate limit exceeded."""
        now = time.time()
        bucket = self._buckets.setdefault(channel, collections.deque())
        # Evict timestamps outside the window
        while bucket and now - bucket[0] > self._window:
            bucket.popleft()
        if len(bucket) >= self._max:
            return False
        bucket.append(now)
        return True


class ChannelWebhookRouter:
    """Manage multi-channel webhook ingestion with dedup and memory integration."""

    MAX_DEDUP_ENTRIES = 50_000

    def __init__(
        self,
        memory_adapter: OpenClawMemoryAdapter | None = None,
        memory_store=None,
        rate_limit: int = 60,
    ):
        self._adapters: dict[str, ChannelPort] = {
            "telegram": TelegramChannelAdapter(),
            "web": WebChannelAdapter(),
            "kakao": KakaoChannelAdapter(),
        }
        self._memory_adapter = memory_adapter
        self._memory_store = memory_store
        self._event_dedup: dict[str, float] = {}  # event_id -> timestamp
        self._event_counter: dict[str, int] = {}  # channel -> count
        self._rate_limiter = WebhookRateLimiter(max_requests=rate_limit)

    def _cleanup_expired(self) -> None:
        """Remove expired dedup entries."""
        now = time.time()
        expired = [k for k, v in self._event_dedup.items() if now - v > DEDUP_TTL_SEC]
        for k in expired:
            del self._event_dedup[k]

    async def handle_webhook(self, channel: str, payload: dict, *, headers: dict | None = None) -> dict:
        """Process inbound webhook: rate-limit -> verify sig -> ingest -> dedup -> normalize -> store."""
        adapter = self._adapters.get(channel)
        if not adapter:
            raise ValueError(f"Unsupported channel: {channel}")

        # Rate limit check (before any processing)
        if not self._rate_limiter.check(channel):
            raise WebhookRateLimitError(channel)

        # ingest_event handles per-adapter signature verification internally
        event = await adapter.ingest_event(payload, headers=headers)

        # Dedup check
        self._cleanup_expired()
        if event.event_id in self._event_dedup:
            return {
                "status": "duplicate",
                "event_id": event.event_id,
                "channel": channel,
            }

        # Register event (bounded)
        if len(self._event_dedup) >= self.MAX_DEDUP_ENTRIES:
            oldest_key = next(iter(self._event_dedup))
            del self._event_dedup[oldest_key]
        self._event_dedup[event.event_id] = time.time()
        self._event_counter[channel] = self._event_counter.get(channel, 0) + 1

        # Normalize and store to memory
        normalized: dict | None = None
        if self._memory_adapter and event.text:
            try:
                entry = self._memory_adapter.normalize(
                    tenant_id=event.tenant_id,
                    project_id=event.project_id or "default",
                    scene_id=None,
                    source_channel=channel if channel in ("telegram", "web") else "other",
                    note=event.text,
                    attachments=event.attachments,
                )
                if self._memory_store:
                    self._memory_store.put(entry)
                normalized = entry.to_dict()
            except Exception as e:
                logger.warning(f"[ChannelRouter] Memory normalization failed: {e}")

        return {
            "status": "processed",
            "event_id": event.event_id,
            "channel": channel,
            "user_id": event.user_id,
            "normalized": normalized,
        }

    async def handle_reply(self, channel: str, user_id: str, text: str, attachments: list[str] | None = None) -> dict:
        """Send reply through specified channel adapter."""
        adapter = self._adapters.get(channel)
        if not adapter:
            raise ValueError(f"Unsupported channel: {channel}")
        reply = ChannelReply(
            channel=channel, user_id=user_id, text=text,
            attachments=attachments or [],
        )
        return await adapter.send_reply(reply)

    async def handle_upload(
        self, channel: str, user_id: str, media_url: str,
        media_type: str = "image", caption: str = "",
    ) -> dict:
        """Upload media through specified channel adapter."""
        adapter = self._adapters.get(channel)
        if not adapter:
            raise ValueError(f"Unsupported channel: {channel}")
        upload = ChannelMediaUpload(
            channel=channel, user_id=user_id, media_url=media_url,
            media_type=media_type, caption=caption,
        )
        return await adapter.upload_media(upload)

    def get_monitoring(self) -> dict:
        """Return event dedup and counter stats for monitoring."""
        return {
            "active_dedup_entries": len(self._event_dedup),
            "event_counts": dict(self._event_counter),
            "supported_channels": list(self._adapters.keys()),
        }
