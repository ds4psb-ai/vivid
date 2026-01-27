"""
VDG Alerting Service (P1 Stub)

Handles alerts for VDG pipeline events.

TODO (P2): Implement full alerting with Slack/PagerDuty integration.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of VDG alerts."""
    PIPELINE_FAILURE = "pipeline_failure"
    QUALITY_DEGRADATION = "quality_degradation"
    CV_UNAVAILABLE = "cv_unavailable"
    AUDIO_ANALYSIS_FAILED = "audio_analysis_failed"
    MOTION_ANALYSIS_FAILED = "motion_analysis_failed"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class VDGAlert:
    """VDG alert record."""
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    context: Dict[str, Any]
    timestamp: datetime
    video_path: Optional[str] = None
    content_id: Optional[str] = None


# =============================================================================
# VDG Alert Service
# =============================================================================


class VDGAlertService:
    """
    VDG pipeline alerting service.

    P1 Stub: Logs alerts but doesn't send to external services.
    P2 TODO: Integrate with monitoring service (app.services.monitoring).

    Features (TODO):
    - Slack notifications for critical alerts
    - PagerDuty for production issues
    - Alert aggregation and deduplication
    - Dashboard metrics
    """

    def __init__(
        self,
        db=None,
        enable_slack: bool = False,
        enable_pagerduty: bool = False,
    ):
        """
        Initialize alerting service.

        Args:
            db: Database session (for alert persistence)
            enable_slack: Enable Slack notifications
            enable_pagerduty: Enable PagerDuty alerts
        """
        self._db = db
        self._enable_slack = enable_slack
        self._enable_pagerduty = enable_pagerduty
        self._alert_history: List[VDGAlert] = []

    def send_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        video_path: Optional[str] = None,
        content_id: Optional[str] = None,
    ) -> None:
        """
        Send an alert.

        P1 Stub: Logs the alert but doesn't send externally.

        Args:
            alert_type: Type of alert
            severity: Alert severity
            message: Alert message
            context: Additional context
            video_path: Path to video (if applicable)
            content_id: Content ID (if applicable)
        """
        alert = VDGAlert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            context=context or {},
            timestamp=datetime.now(timezone.utc),
            video_path=video_path,
            content_id=content_id,
        )

        # Store in memory (P1)
        self._alert_history.append(alert)

        # Log based on severity
        log_msg = f"[VDG_ALERT] {alert_type.value}: {message}"
        if context:
            log_msg += f" | context: {context}"

        if severity == AlertSeverity.CRITICAL:
            logger.critical(log_msg)
        elif severity == AlertSeverity.ERROR:
            logger.error(log_msg)
        elif severity == AlertSeverity.WARNING:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        # TODO (P2): Send to external services
        # if self._enable_slack and severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]:
        #     await self._send_slack(alert)
        # if self._enable_pagerduty and severity == AlertSeverity.CRITICAL:
        #     await self._send_pagerduty(alert)

    def alert_pipeline_failure(
        self,
        error: str,
        video_path: Optional[str] = None,
        content_id: Optional[str] = None,
        stage: str = "unknown",
    ) -> None:
        """
        Alert for pipeline failure.

        Args:
            error: Error message
            video_path: Path to video
            content_id: Content ID
            stage: Pipeline stage that failed
        """
        self.send_alert(
            alert_type=AlertType.PIPELINE_FAILURE,
            severity=AlertSeverity.ERROR,
            message=f"VDG pipeline failed at stage '{stage}': {error}",
            context={"stage": stage, "error": error},
            video_path=video_path,
            content_id=content_id,
        )

    def alert_quality_degradation(
        self,
        tier: str,
        issues: List[str],
        content_id: Optional[str] = None,
    ) -> None:
        """
        Alert for quality degradation.

        Args:
            tier: Quality tier (bronze, fail, etc.)
            issues: List of quality issues
            content_id: Content ID
        """
        severity = AlertSeverity.WARNING if tier == "bronze" else AlertSeverity.ERROR
        self.send_alert(
            alert_type=AlertType.QUALITY_DEGRADATION,
            severity=severity,
            message=f"VDG quality degraded to '{tier}': {len(issues)} issues",
            context={"tier": tier, "issues": issues},
            content_id=content_id,
        )

    def alert_cv_unavailable(self) -> None:
        """Alert when CV (OpenCV) is unavailable."""
        self.send_alert(
            alert_type=AlertType.CV_UNAVAILABLE,
            severity=AlertSeverity.WARNING,
            message="OpenCV not available, CV measurements using stub values",
            context={},
        )

    def alert_timeout(
        self,
        stage: str,
        timeout_seconds: float,
        content_id: Optional[str] = None,
    ) -> None:
        """
        Alert for timeout.

        Args:
            stage: Pipeline stage that timed out
            timeout_seconds: Timeout value
            content_id: Content ID
        """
        self.send_alert(
            alert_type=AlertType.TIMEOUT,
            severity=AlertSeverity.ERROR,
            message=f"VDG pipeline timed out at stage '{stage}' after {timeout_seconds}s",
            context={"stage": stage, "timeout_seconds": timeout_seconds},
            content_id=content_id,
        )

    def get_recent_alerts(
        self,
        limit: int = 100,
        severity_filter: Optional[AlertSeverity] = None,
    ) -> List[VDGAlert]:
        """
        Get recent alerts from memory.

        P1 Stub: Returns from in-memory history.

        Args:
            limit: Maximum alerts to return
            severity_filter: Filter by severity

        Returns:
            List of recent alerts
        """
        alerts = self._alert_history[-limit:]
        if severity_filter:
            alerts = [a for a in alerts if a.severity == severity_filter]
        return alerts

    def clear_history(self) -> None:
        """Clear alert history (for testing)."""
        self._alert_history.clear()


# =============================================================================
# Singleton Instance
# =============================================================================

vdg_alert_service = VDGAlertService()


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "VDGAlertService",
    "VDGAlert",
    "AlertSeverity",
    "AlertType",
    "vdg_alert_service",
]
