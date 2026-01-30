"""
Alert Manager for Production Monitoring

Centralized alerting for critical system events.
Integrates with:
- Prometheus metrics (for alert rules)
- Sentry (for error tracking)
- Slack (for team notifications)

Usage:
    from app.services.alert_manager import AlertManager, get_alert_manager

    alert_mgr = get_alert_manager()
    await alert_mgr.circuit_breaker_open("gemini", "Connection timeout")
    await alert_mgr.high_error_rate(0.15, 0.05)
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Alert Types and Severity
# =============================================================================

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts."""
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    CIRCUIT_BREAKER_HALF_OPEN = "circuit_breaker_half_open"
    HIGH_ERROR_RATE = "high_error_rate"
    HIGH_LATENCY = "high_latency"
    CREDIT_DEDUCTION_FAILED = "credit_deduction_failed"
    RAG_QUALITY_LOW = "rag_quality_low"
    VIDEO_GENERATION_FAILED = "video_generation_failed"
    TIMEOUT_SPIKE = "timeout_spike"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SHUTDOWN_INITIATED = "shutdown_initiated"
    CUSTOM = "custom"


@dataclass
class Alert:
    """Alert data structure."""
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.alert_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "labels": self.labels,
            "annotations": self.annotations,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# Alert Deduplication
# =============================================================================

class AlertDeduplicator:
    """
    Prevents alert flooding by deduplicating similar alerts.

    Uses a sliding window to track recent alerts and suppress duplicates.
    """

    def __init__(self, window_seconds: int = 300):
        """Initialize deduplicator.

        Args:
            window_seconds: Time window for deduplication (default: 5 min)
        """
        self._recent_alerts: Dict[str, datetime] = {}
        self._window = timedelta(seconds=window_seconds)

    def _make_key(self, alert: Alert) -> str:
        """Generate deduplication key for alert."""
        return f"{alert.alert_type.value}:{alert.severity.value}:{sorted(alert.labels.items())}"

    def should_send(self, alert: Alert) -> bool:
        """Check if alert should be sent (not a duplicate).

        Args:
            alert: Alert to check

        Returns:
            True if alert should be sent
        """
        self._cleanup_old()

        key = self._make_key(alert)
        if key in self._recent_alerts:
            return False

        self._recent_alerts[key] = datetime.utcnow()
        return True

    def _cleanup_old(self) -> None:
        """Remove expired entries."""
        cutoff = datetime.utcnow() - self._window
        self._recent_alerts = {
            k: v for k, v in self._recent_alerts.items()
            if v > cutoff
        }


# =============================================================================
# Alert Senders
# =============================================================================

class SlackAlertSender:
    """Sends alerts to Slack via webhook."""

    SEVERITY_COLORS = {
        AlertSeverity.INFO: "#36a64f",      # Green
        AlertSeverity.WARNING: "#ff9800",   # Orange
        AlertSeverity.CRITICAL: "#ff0000",  # Red
    }

    SEVERITY_EMOJIS = {
        AlertSeverity.INFO: ":information_source:",
        AlertSeverity.WARNING: ":warning:",
        AlertSeverity.CRITICAL: ":rotating_light:",
    }

    def __init__(self, webhook_url: str):
        """Initialize Slack sender.

        Args:
            webhook_url: Slack incoming webhook URL
        """
        self._webhook_url = webhook_url
        self._client = httpx.AsyncClient(timeout=10.0)

    async def send(self, alert: Alert) -> bool:
        """Send alert to Slack.

        Args:
            alert: Alert to send

        Returns:
            True if sent successfully
        """
        if not self._webhook_url:
            return False

        try:
            payload = self._format_slack_message(alert)
            response = await self._client.post(
                self._webhook_url,
                json=payload,
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"[ALERT] Failed to send Slack alert: {e}")
            return False

    def _format_slack_message(self, alert: Alert) -> Dict[str, Any]:
        """Format alert as Slack message."""
        color = self.SEVERITY_COLORS.get(alert.severity, "#808080")
        emoji = self.SEVERITY_EMOJIS.get(alert.severity, ":bell:")

        # Build fields from labels
        fields = [
            {"title": k, "value": v, "short": True}
            for k, v in alert.labels.items()
        ]

        return {
            "attachments": [
                {
                    "color": color,
                    "title": f"{emoji} {alert.title}",
                    "text": alert.message,
                    "fields": fields,
                    "footer": f"Vivid Production | {alert.alert_type.value}",
                    "ts": int(alert.timestamp.timestamp()),
                }
            ]
        }

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()


class MetricsAlertSender:
    """Records alerts as Prometheus metrics."""

    def __init__(self):
        """Initialize metrics sender."""
        self._alerts_total: Dict[str, int] = {}

    async def send(self, alert: Alert) -> bool:
        """Record alert in metrics.

        Args:
            alert: Alert to record

        Returns:
            True (always succeeds)
        """
        key = f"{alert.alert_type.value}_{alert.severity.value}"
        self._alerts_total[key] = self._alerts_total.get(key, 0) + 1

        # Log for Prometheus scraping (structured logging)
        logger.info(
            f"[ALERT_METRIC] type={alert.alert_type.value} "
            f"severity={alert.severity.value} "
            f"labels={json.dumps(alert.labels)}"
        )
        return True

    def get_counts(self) -> Dict[str, int]:
        """Get alert counts."""
        return self._alerts_total.copy()


# =============================================================================
# Alert Manager
# =============================================================================

class AlertManager:
    """
    Centralized alert management for production monitoring.

    Features:
    - Multiple alert channels (Slack, metrics)
    - Alert deduplication
    - Severity-based routing
    - Structured alert data
    """

    _instance: Optional["AlertManager"] = None

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize alert manager."""
        if self._initialized:
            return

        self._deduplicator = AlertDeduplicator(window_seconds=300)
        self._senders: List[Any] = []

        # Initialize Slack sender if configured
        if settings.SLACK_WEBHOOK_URL:
            self._senders.append(SlackAlertSender(settings.SLACK_WEBHOOK_URL))

        # Always add metrics sender
        self._metrics_sender = MetricsAlertSender()
        self._senders.append(self._metrics_sender)

        self._initialized = True

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert through all channels.

        Args:
            alert: Alert to send

        Returns:
            True if sent to at least one channel
        """
        # Check deduplication
        if not self._deduplicator.should_send(alert):
            logger.debug(f"[ALERT] Deduplicated: {alert.title}")
            return False

        # Log the alert
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.CRITICAL: logging.ERROR,
        }.get(alert.severity, logging.WARNING)

        logger.log(
            log_level,
            f"[ALERT] {alert.severity.value.upper()}: {alert.title} - {alert.message}"
        )

        # Send through all channels
        results = await asyncio.gather(
            *[sender.send(alert) for sender in self._senders],
            return_exceptions=True,
        )

        return any(r is True for r in results)

    # =========================================================================
    # Convenience Methods for Common Alerts
    # =========================================================================

    async def circuit_breaker_open(
        self,
        name: str,
        reason: str,
        remaining_seconds: Optional[float] = None,
    ) -> bool:
        """Alert for circuit breaker opening.

        Args:
            name: Circuit breaker name
            reason: Reason for opening
            remaining_seconds: Seconds until half-open

        Returns:
            True if alert sent
        """
        alert = Alert(
            alert_type=AlertType.CIRCUIT_BREAKER_OPEN,
            severity=AlertSeverity.CRITICAL,
            title=f"Circuit Breaker OPEN: {name}",
            message=f"Circuit breaker '{name}' opened due to: {reason}",
            labels={
                "circuit": name,
                "remaining_seconds": str(remaining_seconds) if remaining_seconds else "N/A",
            },
        )
        return await self.send_alert(alert)

    async def circuit_breaker_half_open(self, name: str) -> bool:
        """Alert for circuit breaker entering half-open state.

        Args:
            name: Circuit breaker name

        Returns:
            True if alert sent
        """
        alert = Alert(
            alert_type=AlertType.CIRCUIT_BREAKER_HALF_OPEN,
            severity=AlertSeverity.WARNING,
            title=f"Circuit Breaker HALF-OPEN: {name}",
            message=f"Circuit breaker '{name}' is testing recovery",
            labels={"circuit": name},
        )
        return await self.send_alert(alert)

    async def high_error_rate(
        self,
        current_rate: float,
        threshold: float,
        endpoint: Optional[str] = None,
    ) -> bool:
        """Alert for high error rate.

        Args:
            current_rate: Current error rate (0-1)
            threshold: Threshold that was exceeded
            endpoint: Optional endpoint path

        Returns:
            True if alert sent
        """
        severity = AlertSeverity.CRITICAL if current_rate > 0.1 else AlertSeverity.WARNING

        alert = Alert(
            alert_type=AlertType.HIGH_ERROR_RATE,
            severity=severity,
            title=f"High Error Rate: {current_rate:.1%}",
            message=f"Error rate {current_rate:.1%} exceeds threshold {threshold:.1%}",
            labels={
                "current_rate": f"{current_rate:.2%}",
                "threshold": f"{threshold:.2%}",
                "endpoint": endpoint or "all",
            },
        )
        return await self.send_alert(alert)

    async def high_latency(
        self,
        current_latency: float,
        threshold: float,
        percentile: str = "p99",
        endpoint: Optional[str] = None,
    ) -> bool:
        """Alert for high latency.

        Args:
            current_latency: Current latency in seconds
            threshold: Threshold in seconds
            percentile: Percentile (p50, p95, p99)
            endpoint: Optional endpoint path

        Returns:
            True if alert sent
        """
        alert = Alert(
            alert_type=AlertType.HIGH_LATENCY,
            severity=AlertSeverity.WARNING,
            title=f"High Latency ({percentile}): {current_latency:.2f}s",
            message=f"Latency {current_latency:.2f}s exceeds threshold {threshold:.2f}s",
            labels={
                "current": f"{current_latency:.2f}s",
                "threshold": f"{threshold:.2f}s",
                "percentile": percentile,
                "endpoint": endpoint or "all",
            },
        )
        return await self.send_alert(alert)

    async def credit_deduction_failed(
        self,
        user_id: str,
        amount: int,
        reason: str,
    ) -> bool:
        """Alert for credit deduction failure.

        Args:
            user_id: User ID
            amount: Credit amount
            reason: Failure reason

        Returns:
            True if alert sent
        """
        alert = Alert(
            alert_type=AlertType.CREDIT_DEDUCTION_FAILED,
            severity=AlertSeverity.CRITICAL,
            title="Credit Deduction Failed",
            message=f"Failed to deduct {amount} credits for user {user_id}: {reason}",
            labels={
                "user_id": user_id,
                "amount": str(amount),
                "reason": reason,
            },
        )
        return await self.send_alert(alert)

    async def rag_quality_low(
        self,
        score: float,
        threshold: float,
        dimension: Optional[str] = None,
    ) -> bool:
        """Alert for low RAG quality score.

        Args:
            score: Current quality score
            threshold: Threshold score
            dimension: Optional dimension

        Returns:
            True if alert sent
        """
        alert = Alert(
            alert_type=AlertType.RAG_QUALITY_LOW,
            severity=AlertSeverity.WARNING,
            title=f"Low RAG Quality: {score:.2f}",
            message=f"RAG quality score {score:.2f} below threshold {threshold:.2f}",
            labels={
                "score": f"{score:.2f}",
                "threshold": f"{threshold:.2f}",
                "dimension": dimension or "all",
            },
        )
        return await self.send_alert(alert)

    async def video_generation_failed(
        self,
        provider: str,
        reason: str,
        job_id: Optional[str] = None,
    ) -> bool:
        """Alert for video generation failure.

        Args:
            provider: Video provider (veo, kling)
            reason: Failure reason
            job_id: Optional job ID

        Returns:
            True if alert sent
        """
        alert = Alert(
            alert_type=AlertType.VIDEO_GENERATION_FAILED,
            severity=AlertSeverity.WARNING,
            title=f"Video Generation Failed: {provider}",
            message=f"Video generation with {provider} failed: {reason}",
            labels={
                "provider": provider,
                "job_id": job_id or "N/A",
            },
        )
        return await self.send_alert(alert)

    async def shutdown_initiated(
        self,
        reason: str,
        in_flight_requests: int,
    ) -> bool:
        """Alert for graceful shutdown initiation.

        Args:
            reason: Shutdown reason
            in_flight_requests: Number of in-flight requests

        Returns:
            True if alert sent
        """
        alert = Alert(
            alert_type=AlertType.SHUTDOWN_INITIATED,
            severity=AlertSeverity.INFO,
            title="Graceful Shutdown Initiated",
            message=f"Server shutdown initiated: {reason}. {in_flight_requests} requests in flight.",
            labels={
                "reason": reason,
                "in_flight_requests": str(in_flight_requests),
            },
        )
        return await self.send_alert(alert)

    async def custom_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.WARNING,
        labels: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Send a custom alert.

        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity
            labels: Optional labels

        Returns:
            True if alert sent
        """
        alert = Alert(
            alert_type=AlertType.CUSTOM,
            severity=severity,
            title=title,
            message=message,
            labels=labels or {},
        )
        return await self.send_alert(alert)

    def get_stats(self) -> Dict[str, Any]:
        """Get alert statistics.

        Returns:
            Dict with alert counts
        """
        return {
            "counts": self._metrics_sender.get_counts(),
            "channels": len(self._senders),
        }


# =============================================================================
# Singleton Instance
# =============================================================================

_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get singleton AlertManager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
