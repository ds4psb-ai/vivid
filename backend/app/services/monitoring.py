"""
Monitoring Service (P1 Stub)

Provides alerting and monitoring utilities.

TODO (P2): Implement full monitoring with Slack/PagerDuty.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def send_alert(
    title: str,
    message: str,
    severity: str = "info",
    channel: Optional[str] = None,
) -> bool:
    """
    Send an alert to monitoring system.

    P1 Stub: Logs the alert.
    P2 TODO: Send to Slack/PagerDuty.

    Args:
        title: Alert title
        message: Alert message
        severity: Alert severity (info, warning, error, critical)
        channel: Optional channel override

    Returns:
        True if alert sent successfully
    """
    log_msg = f"[ALERT:{severity.upper()}] {title}: {message}"

    if severity == "critical":
        logger.critical(log_msg)
    elif severity == "error":
        logger.error(log_msg)
    elif severity == "warning":
        logger.warning(log_msg)
    else:
        logger.info(log_msg)

    return True


__all__ = ["send_alert"]
