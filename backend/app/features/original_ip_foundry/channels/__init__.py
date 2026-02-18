"""Channel adapters for Foundry multi-channel routing."""
from app.features.original_ip_foundry.channels.telegram_adapter import TelegramChannelAdapter
from app.features.original_ip_foundry.channels.web_adapter import WebChannelAdapter
from app.features.original_ip_foundry.channels.kakao_adapter import KakaoChannelAdapter

__all__ = ["TelegramChannelAdapter", "WebChannelAdapter", "KakaoChannelAdapter"]
