"""
Security Audit Utilities (P1 Stub)

Provides security event logging for audit trails.

TODO (P2): Implement full security audit with external logging.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


def log_security_event(
    event_type: str,
    user_id: Optional[str] = None,
    reason: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """
    Log a security-relevant event.

    P1 Stub: Logs to standard logger.
    P2 TODO: Send to security audit service.

    Args:
        event_type: Type of security event
        user_id: User ID if applicable
        reason: Reason for the event
        **kwargs: Additional event metadata
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    log_data = {
        "event_type": event_type,
        "timestamp": timestamp,
        "user_id": user_id,
        "reason": reason,
        **kwargs,
    }

    # Filter out None values
    log_data = {k: v for k, v in log_data.items() if v is not None}

    logger.info(f"[SECURITY_AUDIT] {event_type}: {log_data}")


__all__ = ["log_security_event"]
