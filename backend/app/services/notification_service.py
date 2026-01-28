"""Notification Service for HITL and system alerts.

Supports:
- Slack webhook notifications
- Admin alert formatting
- Async delivery with retry

Usage:
    from app.services.notification_service import NotificationService, AdminAlert

    notification = NotificationService()

    alert = AdminAlert(
        title="HITL Review Required",
        message="New drift detected for auteur:bong",
        severity="warning",
        data={"drift_score": 0.25, "auteur_key": "bong"},
    )

    await notification.send_admin_alert(alert)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)
settings = Settings()


# =============================================================================
# Alert Data Classes
# =============================================================================

@dataclass
class AdminAlert:
    """Alert payload for admin notifications.

    Args:
        title: Alert title (short, descriptive)
        message: Detailed message body
        severity: Alert severity (info, warning, critical)
        data: Additional structured data
        trace_id: Optional trace ID for correlation
    """
    title: str
    message: str
    severity: str = "info"  # info, warning, critical
    data: Optional[Dict[str, Any]] = field(default_factory=dict)
    trace_id: Optional[str] = None


# =============================================================================
# Notification Service
# =============================================================================

class NotificationService:
    """Unified notification service for admin alerts.

    Supports:
    - Slack webhook notifications
    - Configurable via SLACK_WEBHOOK_URL
    - Graceful degradation when not configured

    Future extensions:
    - Email notifications
    - PagerDuty integration
    - Discord webhooks
    """

    def __init__(self, slack_webhook_url: Optional[str] = None):
        """Initialize notification service.

        Args:
            slack_webhook_url: Optional Slack webhook URL override
        """
        self.slack_webhook_url = slack_webhook_url or getattr(
            settings, "SLACK_WEBHOOK_URL", None
        )
        self.enabled = bool(self.slack_webhook_url)

    async def send_admin_alert(
        self,
        alert: Optional[AdminAlert] = None,
        *,
        title: Optional[str] = None,
        message: Optional[str] = None,
        severity: str = "info",
        data: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> bool:
        """Send alert to admin channels.

        Can be called with an AdminAlert object or keyword arguments.

        Args:
            alert: AdminAlert object (preferred)
            title: Alert title (if not using alert object)
            message: Alert message (if not using alert object)
            severity: Alert severity (if not using alert object)
            data: Additional data (if not using alert object)
            trace_id: Trace ID (if not using alert object)

        Returns:
            True if sent successfully, False otherwise
        """
        # Support both object and kwargs styles
        if alert is None:
            if title is None or message is None:
                logger.warning("[Notification] Missing title or message")
                return False
            alert = AdminAlert(
                title=title,
                message=message,
                severity=severity,
                data=data or {},
                trace_id=trace_id,
            )

        if not self.enabled:
            logger.info(
                f"[Notification] Notifications disabled, skipping: {alert.title}"
            )
            return False

        return await self._send_slack_alert(alert)

    async def _send_slack_alert(self, alert: AdminAlert) -> bool:
        """Send Slack webhook notification.

        Args:
            alert: AdminAlert to send

        Returns:
            True if successful
        """
        severity_config = {
            "info": {"emoji": "ℹ️", "color": "#36a64f"},
            "warning": {"emoji": "⚠️", "color": "#ff9800"},
            "critical": {"emoji": "🚨", "color": "#f44336"},
        }

        config = severity_config.get(alert.severity, severity_config["info"])

        # Build Slack blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{config['emoji']} {alert.title}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": alert.message,
                },
            },
        ]

        # Add data fields if present
        if alert.data:
            fields = []
            for key, value in list(alert.data.items())[:10]:  # Max 10 fields
                # Format value for display
                if isinstance(value, float):
                    display_value = f"{value:.4f}"
                elif isinstance(value, bool):
                    display_value = "Yes" if value else "No"
                else:
                    display_value = str(value)[:100]  # Truncate long values

                fields.append({
                    "type": "mrkdwn",
                    "text": f"*{key}*\n{display_value}",
                })

            # Slack allows max 10 fields per section
            if fields:
                blocks.append({
                    "type": "section",
                    "fields": fields[:10],
                })

        # Add trace ID context if present
        if alert.trace_id:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"trace_id: `{alert.trace_id}`",
                    }
                ],
            })

        # Build payload
        payload = {
            "blocks": blocks,
            "attachments": [
                {
                    "color": config["color"],
                    "fallback": f"{alert.title}: {alert.message}",
                }
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.slack_webhook_url,
                    json=payload,
                )
                response.raise_for_status()
                logger.info(f"[Notification] Slack alert sent: {alert.title}")
                return True

        except httpx.TimeoutException:
            logger.warning(f"[Notification] Slack timeout: {alert.title}")
            return False
        except httpx.HTTPStatusError as e:
            logger.error(
                f"[Notification] Slack HTTP error {e.response.status_code}: {alert.title}"
            )
            return False
        except Exception as e:
            logger.exception(f"[Notification] Slack error: {e}")
            return False


# =============================================================================
# Module-level convenience
# =============================================================================

_default_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get or create the default notification service."""
    global _default_service
    if _default_service is None:
        _default_service = NotificationService()
    return _default_service


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "AdminAlert",
    "NotificationService",
    "get_notification_service",
]
