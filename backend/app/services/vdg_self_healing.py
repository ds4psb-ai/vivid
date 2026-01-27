"""VDG Self-Healing Service

Automated remediation for VDG pipeline issues based on drift detection.
Implements PSI-triggered reanalysis and circuit breaker patterns.

Key Features:
- PSI >= 0.25 triggers automatic reanalysis of drifted items
- Circuit breaker prevents runaway remediation
- Slack interactive buttons for manual approval/override
- Prometheus metrics for tracking healing activity

Usage:
    from app.services.vdg_self_healing import VDGSelfHealingService

    service = VDGSelfHealingService(db)
    result = await service.process_drift_results(drift_results)

References:
    - https://www.fairwinds.com/blog/2026-kubernetes-playbook-ai-self-healing-clusters-growth
    - https://medium.com/@anudeepballa7/kill-the-pager-a-practical-guide-to-auto-remediation-and-self-healing-systems
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, asdict
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.utils.time import utcnow
from app.config import settings

logger = logging.getLogger(__name__)


class HealingAction(str, Enum):
    """Types of self-healing actions"""

    REANALYSIS = "reanalysis"
    BASELINE_REFRESH = "baseline_refresh"
    ALERT_ONLY = "alert_only"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass
class HealingResult:
    """Result of a self-healing action"""

    action: HealingAction
    feature_name: str
    psi_score: float
    items_affected: int
    success: bool
    message: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {**asdict(self), "action": self.action.value}


class CircuitBreaker:
    """
    Circuit breaker to prevent runaway self-healing.

    States:
    - CLOSED: Normal operation, healing allowed
    - OPEN: Too many failures, healing blocked
    - HALF_OPEN: Testing if system recovered

    Thresholds:
    - 5 failures in 30 minutes -> OPEN
    - 5 minutes cooldown -> HALF_OPEN
    - 1 success in HALF_OPEN -> CLOSED
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_minutes: int = 5,
        window_minutes: int = 30,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(minutes=recovery_timeout_minutes)
        self.window = timedelta(minutes=window_minutes)

        self._failures: List[datetime] = []
        self._state: Literal["closed", "open", "half_open"] = "closed"
        self._last_failure_time: Optional[datetime] = None

    @property
    def state(self) -> str:
        self._update_state()
        return self._state

    def _update_state(self) -> None:
        """Update circuit breaker state based on time and failures"""
        now = utcnow()

        # Clean old failures outside window
        self._failures = [f for f in self._failures if now - f < self.window]

        if self._state == "open":
            # Check if recovery timeout has passed
            if self._last_failure_time:
                if now - self._last_failure_time >= self.recovery_timeout:
                    self._state = "half_open"
                    logger.info("[CircuitBreaker] Transitioning to HALF_OPEN")

        elif self._state == "half_open":
            # Will be updated by record_success/record_failure
            pass

        elif self._state == "closed":
            # Check if too many failures
            if len(self._failures) >= self.failure_threshold:
                self._state = "open"
                logger.warning(f"[CircuitBreaker] OPENED - " f"{len(self._failures)} failures in window")

    def is_allowed(self) -> bool:
        """Check if an action is allowed"""
        self._update_state()
        return self._state in ("closed", "half_open")

    def record_success(self) -> None:
        """Record a successful action"""
        if self._state == "half_open":
            self._state = "closed"
            self._failures.clear()
            logger.info("[CircuitBreaker] CLOSED - recovery successful")

    def record_failure(self) -> None:
        """Record a failed action"""
        now = utcnow()
        self._failures.append(now)
        self._last_failure_time = now

        if self._state == "half_open":
            self._state = "open"
            logger.warning("[CircuitBreaker] Re-OPENED from HALF_OPEN")

        self._update_state()


class VDGSelfHealingService:
    """
    Self-healing service for VDG pipeline.

    Processes drift detection results and takes automated actions:
    - PSI >= 0.25 (high): Auto-reanalyze recent items
    - PSI 0.2-0.25 (medium): Alert + suggest reanalysis
    - PSI 0.1-0.2 (low): Alert only
    - PSI < 0.1: No action

    Includes circuit breaker to prevent cascading failures.
    """

    # PSI thresholds for action levels
    PSI_AUTO_HEAL_THRESHOLD = 0.25  # High severity - auto action
    PSI_ALERT_THRESHOLD = 0.2  # Medium severity - alert + manual
    PSI_MONITOR_THRESHOLD = 0.1  # Low severity - monitor only

    # Reanalysis limits
    MAX_REANALYSIS_PER_FEATURE = 100  # Max items to reanalyze per feature
    MAX_REANALYSIS_TOTAL = 500  # Max total items per run
    REANALYSIS_LOOKBACK_DAYS = 7  # How far back to look for items

    def __init__(self, db: AsyncSession):
        self.db = db
        self._circuit_breaker = CircuitBreaker()

    async def process_drift_results(
        self,
        drift_results: Dict[str, Any],
        auto_heal: bool = True,
    ) -> Dict[str, Any]:
        """
        Process drift detection results and take appropriate actions.

        Args:
            drift_results: Results from VDGMLDriftDetector.detect_drift()
            auto_heal: Whether to automatically trigger reanalysis

        Returns:
            Summary of actions taken
        """
        actions_taken: List[HealingResult] = []
        total_items_affected = 0

        # Check circuit breaker
        if not self._circuit_breaker.is_allowed():
            logger.warning("[SelfHealing] Circuit breaker OPEN - skipping")
            return {
                "status": "circuit_breaker_open",
                "actions": [],
                "circuit_breaker_state": self._circuit_breaker.state,
            }

        results = drift_results.get("results", [])

        for result in results:
            feature_name = result.get("feature_name", "unknown")
            psi_score = result.get("drift_score", 0)
            severity = result.get("severity", "none")

            try:
                action_result = await self._process_feature_drift(
                    feature_name=feature_name,
                    psi_score=psi_score,
                    severity=severity,
                    auto_heal=auto_heal,
                )

                if action_result:
                    actions_taken.append(action_result)
                    total_items_affected += action_result.items_affected

                    if action_result.success:
                        self._circuit_breaker.record_success()
                    else:
                        self._circuit_breaker.record_failure()

            except Exception as e:
                logger.error(f"[SelfHealing] Error processing {feature_name}: {e}")
                self._circuit_breaker.record_failure()

        return {
            "status": "completed",
            "total_features_processed": len(results),
            "actions_taken": len(actions_taken),
            "total_items_affected": total_items_affected,
            "circuit_breaker_state": self._circuit_breaker.state,
            "actions": [a.to_dict() for a in actions_taken],
        }

    async def _process_feature_drift(
        self,
        feature_name: str,
        psi_score: float,
        severity: str,
        auto_heal: bool,
    ) -> Optional[HealingResult]:
        """Process drift for a single feature"""

        if psi_score < self.PSI_MONITOR_THRESHOLD:
            # No action needed
            return None

        if psi_score >= self.PSI_AUTO_HEAL_THRESHOLD and auto_heal:
            # High severity - auto reanalyze
            return await self._trigger_reanalysis(
                feature_name=feature_name,
                psi_score=psi_score,
                limit=self.MAX_REANALYSIS_PER_FEATURE,
            )

        elif psi_score >= self.PSI_ALERT_THRESHOLD:
            # Medium severity - alert with action buttons
            return await self._send_healing_alert(
                feature_name=feature_name,
                psi_score=psi_score,
                severity="medium",
            )

        else:
            # Low severity - alert only
            return await self._send_healing_alert(
                feature_name=feature_name,
                psi_score=psi_score,
                severity="low",
            )

    async def _trigger_reanalysis(
        self,
        feature_name: str,
        psi_score: float,
        limit: int = 100,
    ) -> HealingResult:
        """
        Trigger reanalysis for items affected by drift.

        Selects recent items and queues them for VDG reanalysis.
        """
        logger.info(f"[SelfHealing] Triggering reanalysis for {feature_name} " f"(PSI={psi_score:.3f})")

        try:
            from app.models import OutlierItem
            from app.services.vdg_reanalysis_queue import queue_items_for_reanalysis

            # Find recent items to reanalyze
            # Exclude items reanalyzed in the last 7 days to prevent loops
            cutoff = utcnow() - timedelta(days=self.REANALYSIS_LOOKBACK_DAYS)
            recent_reanalysis_cutoff = utcnow() - timedelta(days=7)

            query = (
                select(OutlierItem.id)
                .where(
                    and_(
                        OutlierItem.analysis_status == "completed",
                        OutlierItem.analyzed_at >= cutoff,
                        OutlierItem.vdg_feature_vector.isnot(None),
                        # Exclude items already reanalyzed recently
                        or_(
                            OutlierItem.last_retry_at.is_(None),
                            OutlierItem.last_retry_at < recent_reanalysis_cutoff,
                        ),
                    )
                )
                .order_by(OutlierItem.analyzed_at.desc())
                .limit(limit)
            )

            result = await self.db.execute(query)
            item_ids = [row[0] for row in result.fetchall()]

            if not item_ids:
                return HealingResult(
                    action=HealingAction.REANALYSIS,
                    feature_name=feature_name,
                    psi_score=psi_score,
                    items_affected=0,
                    success=True,
                    message="No items found for reanalysis",
                    timestamp=utcnow().isoformat(),
                )

            # Queue items for reanalysis
            queued = await queue_items_for_reanalysis(
                self.db,
                item_ids=item_ids,
                reason=f"ml_drift_{feature_name}",
            )

            # Send success alert
            await self._send_healing_action_alert(
                action="reanalysis_triggered",
                feature_name=feature_name,
                psi_score=psi_score,
                items_count=queued,
            )

            logger.info(f"[SelfHealing] Queued {queued} items for reanalysis " f"(feature={feature_name})")

            return HealingResult(
                action=HealingAction.REANALYSIS,
                feature_name=feature_name,
                psi_score=psi_score,
                items_affected=queued,
                success=True,
                message=f"Queued {queued} items for reanalysis",
                timestamp=utcnow().isoformat(),
            )

        except Exception as e:
            logger.error(f"[SelfHealing] Reanalysis failed: {e}")

            return HealingResult(
                action=HealingAction.REANALYSIS,
                feature_name=feature_name,
                psi_score=psi_score,
                items_affected=0,
                success=False,
                message=f"Failed: {str(e)}",
                timestamp=utcnow().isoformat(),
            )

    async def _send_healing_alert(
        self,
        feature_name: str,
        psi_score: float,
        severity: str,
    ) -> HealingResult:
        """Send alert with optional action buttons"""
        from app.services.vdg_alerting import VDGAlertService

        severity_map = {
            "low": "warning",
            "medium": "warning",
            "high": "critical",
        }
        alert_severity = severity_map.get(severity, "info")

        # Include action buttons for medium+ severity
        fields = {
            "Feature": feature_name,
            "PSI Score": f"{psi_score:.3f}",
            "Severity": severity.upper(),
            "Threshold": f"{self.PSI_AUTO_HEAL_THRESHOLD} (auto-heal)",
        }

        if severity in ("medium", "high"):
            fields["Action"] = "Use `/vdg reanalyze <feature>` to trigger manual reanalysis"

        try:
            await VDGAlertService.send_to_all_channels(
                severity=alert_severity,
                title=f"🔬 VDG ML Drift: {feature_name}",
                message=f"PSI score {psi_score:.3f} exceeds threshold",
                runbook_url="https://docs.shorti.ai/runbooks/vdg-ml-drift",
                fields=fields,
                rule_name=f"ml_drift_{feature_name}",
            )

            return HealingResult(
                action=HealingAction.ALERT_ONLY,
                feature_name=feature_name,
                psi_score=psi_score,
                items_affected=0,
                success=True,
                message=f"Alert sent (severity={severity})",
                timestamp=utcnow().isoformat(),
            )

        except Exception as e:
            logger.error(f"[SelfHealing] Alert failed: {e}")

            return HealingResult(
                action=HealingAction.ALERT_ONLY,
                feature_name=feature_name,
                psi_score=psi_score,
                items_affected=0,
                success=False,
                message=f"Alert failed: {str(e)}",
                timestamp=utcnow().isoformat(),
            )

    async def _send_healing_action_alert(
        self,
        action: str,
        feature_name: str,
        psi_score: float,
        items_count: int,
    ) -> None:
        """Send alert about healing action taken"""
        from app.services.vdg_alerting import VDGAlertService

        try:
            await VDGAlertService.send_to_all_channels(
                severity="info",
                title="🔧 VDG Self-Healing Action",
                message=f"Automatic remediation triggered for {feature_name}",
                fields={
                    "Action": action,
                    "Feature": feature_name,
                    "PSI Score": f"{psi_score:.3f}",
                    "Items Affected": str(items_count),
                },
            )
        except Exception as e:
            logger.error(f"[SelfHealing] Action alert failed: {e}")


# =============================================================================
# Slack Interactive Handler (for manual approval)
# =============================================================================


async def handle_slack_interaction(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle Slack interactive button callbacks.

    Expected actions:
    - vdg_reanalyze_{feature_name}: Trigger reanalysis for feature
    - vdg_dismiss_{feature_name}: Dismiss alert
    - vdg_baseline_refresh: Refresh baseline

    Args:
        payload: Slack interaction payload

    Returns:
        Response to send back to Slack
    """
    actions = payload.get("actions", [])
    if not actions:
        return {"text": "No action specified"}

    action = actions[0]
    action_id = action.get("action_id", "")

    if action_id.startswith("vdg_reanalyze_"):
        feature_name = action_id.replace("vdg_reanalyze_", "")
        return await _handle_reanalyze_action(feature_name)

    elif action_id.startswith("vdg_dismiss_"):
        return {"text": "Alert dismissed", "response_type": "ephemeral"}

    elif action_id == "vdg_baseline_refresh":
        return await _handle_baseline_refresh()

    return {"text": f"Unknown action: {action_id}"}


async def _handle_reanalyze_action(feature_name: str) -> Dict[str, Any]:
    """Handle manual reanalyze button click"""
    from app.database import async_session_maker

    try:
        async with async_session_maker() as db:
            service = VDGSelfHealingService(db)
            result = await service._trigger_reanalysis(
                feature_name=feature_name,
                psi_score=0.0,  # Manual trigger
                limit=100,
            )

        return {
            "text": (f"✅ Reanalysis triggered for `{feature_name}`\n" f"Items queued: {result.items_affected}"),
            "response_type": "in_channel",
        }

    except Exception as e:
        logger.error(f"[Slack] Reanalyze action failed: {e}")
        return {
            "text": f"❌ Reanalysis failed: {str(e)}",
            "response_type": "ephemeral",
        }


async def _handle_baseline_refresh() -> Dict[str, Any]:
    """Handle baseline refresh button click"""
    from app.workers.vdg_tasks import refresh_baseline_task

    try:
        # Trigger async task
        refresh_baseline_task.delay(period_days=14)

        return {
            "text": "🔄 Baseline refresh task queued",
            "response_type": "in_channel",
        }

    except Exception as e:
        logger.error(f"[Slack] Baseline refresh failed: {e}")
        return {
            "text": f"❌ Baseline refresh failed: {str(e)}",
            "response_type": "ephemeral",
        }


# =============================================================================
# Convenience Functions
# =============================================================================


async def auto_heal_from_drift_results(
    db: AsyncSession,
    drift_results: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convenience function to process drift results with self-healing.

    Args:
        db: Database session
        drift_results: Results from VDGMLDriftDetector.detect_drift()

    Returns:
        Healing action summary
    """
    service = VDGSelfHealingService(db)
    return await service.process_drift_results(drift_results)
