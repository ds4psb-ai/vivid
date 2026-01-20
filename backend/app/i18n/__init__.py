"""
Internationalization (i18n) Module (H3.3)

Provides localized error messages for RFC 9457 Problem Details.

Usage:
    from app.i18n import get_localized_message

    message = get_localized_message("INSUFFICIENT_CREDITS", lang="ko")
"""
from app.i18n.errors import ERROR_MESSAGES, get_localized_message, get_supported_languages

__all__ = [
    "ERROR_MESSAGES",
    "get_localized_message",
    "get_supported_languages",
]
