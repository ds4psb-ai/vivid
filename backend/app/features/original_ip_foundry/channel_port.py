"""Channel Port ABC — base contracts for multi-channel message routing."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ChannelEvent:
    """Inbound event from any channel."""
    event_id: str
    channel: str  # "telegram" | "web" | "kakao"
    user_id: str
    tenant_id: str = "default"
    project_id: str | None = None
    text: str = ""
    attachments: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    raw_payload: dict = field(default_factory=dict)


@dataclass
class ChannelReply:
    """Outbound reply to a channel user."""
    channel: str
    user_id: str
    text: str
    attachments: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class ChannelMediaUpload:
    """Outbound media upload to a channel."""
    channel: str
    user_id: str
    media_url: str
    media_type: str = "image"  # "image" | "video" | "document"
    caption: str = ""
    metadata: dict = field(default_factory=dict)


class ChannelPort(ABC):
    """Abstract base for channel adapters."""

    CHANNEL_NAME: str = ""

    @abstractmethod
    async def ingest_event(self, raw_payload: dict, *, headers: dict | None = None) -> ChannelEvent:
        """Parse raw webhook payload into a ChannelEvent."""
        ...

    @abstractmethod
    async def send_reply(self, reply: ChannelReply) -> dict:
        """Send a text reply to the channel user."""
        ...

    @abstractmethod
    async def upload_media(self, upload: ChannelMediaUpload) -> dict:
        """Upload media (image/video/document) to the channel."""
        ...
