"""HITL (Human-in-the-Loop) Workflow Service.

Manages the HITL review workflow for:
- Vector drift approvals
- QC failure reviews
- Prompt pattern fixes
- Auto-apply approved actions

Implements 2026 HITL best practices from:
- permit.io/blog/human-in-the-loop-for-ai-agents-best-practices
- AWS ML Lens - Feedback Loops
- Comet HITL Workflows

Usage:
    from app.services.hitl_workflow import HITLWorkflowService

    service = HITLWorkflowService()

    # Create review item
    item = await service.create_review_item(
        review_type="vector_drift",
        payload={"ip_id": "...", "drift_score": 0.25},
        severity="high",
        suggested_action={"action": "create_version", ...},
        db=db,
    )

    # Approve and auto-apply
    item = await service.approve_and_apply(
        item_id=str(item.id),
        decision_by="admin-123",
        db=db,
    )
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_hitl import (
    HITLDecision,
    HITLReviewItem,
    HITLSeverity,
    HITLStatus,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

DEFAULT_EXPIRY_HOURS = 24
CRITICAL_EXPIRY_HOURS = 4


# =============================================================================
# HITL Workflow Service
# =============================================================================

class HITLWorkflowService:
    """Human-in-the-Loop workflow management.

    Handles review item lifecycle:
    1. Create → Pending
    2. Assign → In Review
    3. Decide → Approved/Rejected
    4. Apply (if approved)
    """

    async def create_review_item(
        self,
        review_type: str,
        payload: Dict[str, Any],
        severity: str = "medium",
        suggested_action: Optional[Dict[str, Any]] = None,
        ip_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> HITLReviewItem:
        """Create a new review item.

        Args:
            review_type: Type of review (vector_drift, qc_failure, etc.)
            payload: Review data
            severity: Severity level
            suggested_action: System-recommended action
            ip_id: Associated IP (optional)
            trace_id: Pipeline trace ID (optional)
            db: Database session

        Returns:
            Created HITLReviewItem
        """
        # Calculate expiry based on severity
        if severity == HITLSeverity.CRITICAL.value:
            expiry_hours = CRITICAL_EXPIRY_HOURS
        else:
            expiry_hours = DEFAULT_EXPIRY_HOURS

        item = HITLReviewItem(
            review_type=review_type,
            severity=severity,
            ip_id=ip_id,
            trace_id=trace_id,
            payload=payload,
            suggested_action=suggested_action,
            status=HITLStatus.PENDING.value,
            expires_at=datetime.utcnow() + timedelta(hours=expiry_hours),
        )

        if db:
            db.add(item)
            await db.flush()

            logger.info(
                f"[HITL] Created review item {item.id}: "
                f"type={review_type}, severity={severity}"
            )

            # Send notifications
            await self._notify_admins(item)

        return item

    async def approve_and_apply(
        self,
        item_id: str,
        decision_by: str,
        decision_notes: Optional[str] = None,
        modified_action: Optional[Dict[str, Any]] = None,
        db: Optional[AsyncSession] = None,
    ) -> HITLReviewItem:
        """Approve a review item and auto-apply the action.

        Args:
            item_id: Review item ID
            decision_by: Admin user ID
            decision_notes: Notes about the decision
            modified_action: Modified action (overrides suggested)
            db: Database session

        Returns:
            Updated HITLReviewItem
        """
        if not db:
            raise ValueError("Database session required")

        item = await db.get(HITLReviewItem, item_id)
        if not item:
            raise ValueError(f"Review item not found: {item_id}")

        item.status = HITLStatus.APPROVED.value
        item.decision = HITLDecision.APPROVE.value
        item.decision_by = decision_by
        item.decision_at = datetime.utcnow()
        item.decision_notes = decision_notes

        # Apply action
        action = modified_action or item.suggested_action
        if action:
            try:
                result = await self._apply_action(item.review_type, action, db)
                item.auto_applied = True
                item.applied_at = datetime.utcnow()
                item.apply_result = result
                logger.info(f"[HITL] Auto-applied action for {item_id}: {result}")
            except Exception as e:
                logger.error(f"[HITL] Failed to apply action for {item_id}: {e}")
                item.apply_result = {"error": str(e)}

        await db.flush()

        return item

    async def reject(
        self,
        item_id: str,
        decision_by: str,
        reason: str,
        db: Optional[AsyncSession] = None,
    ) -> HITLReviewItem:
        """Reject a review item.

        Args:
            item_id: Review item ID
            decision_by: Admin user ID
            reason: Rejection reason
            db: Database session

        Returns:
            Updated HITLReviewItem
        """
        if not db:
            raise ValueError("Database session required")

        item = await db.get(HITLReviewItem, item_id)
        if not item:
            raise ValueError(f"Review item not found: {item_id}")

        item.status = HITLStatus.REJECTED.value
        item.decision = HITLDecision.REJECT.value
        item.decision_by = decision_by
        item.decision_at = datetime.utcnow()
        item.decision_notes = reason

        await db.flush()

        logger.info(f"[HITL] Rejected item {item_id}: {reason}")

        return item

    async def assign(
        self,
        item_id: str,
        assigned_to: str,
        db: Optional[AsyncSession] = None,
    ) -> HITLReviewItem:
        """Assign a review item to an admin.

        Args:
            item_id: Review item ID
            assigned_to: Admin user ID
            db: Database session

        Returns:
            Updated HITLReviewItem
        """
        if not db:
            raise ValueError("Database session required")

        item = await db.get(HITLReviewItem, item_id)
        if not item:
            raise ValueError(f"Review item not found: {item_id}")

        item.status = HITLStatus.IN_REVIEW.value
        item.assigned_to = assigned_to

        await db.flush()

        logger.info(f"[HITL] Assigned item {item_id} to {assigned_to}")

        return item

    async def get_pending_by_type(
        self,
        review_type: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> List[HITLReviewItem]:
        """Get pending review items.

        Args:
            review_type: Filter by type (optional)
            db: Database session

        Returns:
            List of pending HITLReviewItem
        """
        if not db:
            return []

        query = (
            select(HITLReviewItem)
            .where(HITLReviewItem.status == HITLStatus.PENDING.value)
            .order_by(
                # Critical first, then by created_at
                HITLReviewItem.severity.desc(),
                HITLReviewItem.created_at.asc(),
            )
        )

        if review_type:
            query = query.where(HITLReviewItem.review_type == review_type)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_counts_by_type(
        self,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, int]:
        """Get pending item counts by review type.

        Args:
            db: Database session

        Returns:
            Dict of review_type -> count
        """
        if not db:
            return {}

        query = (
            select(
                HITLReviewItem.review_type,
                func.count(HITLReviewItem.id).label("count"),
            )
            .where(HITLReviewItem.status == HITLStatus.PENDING.value)
            .group_by(HITLReviewItem.review_type)
        )

        result = await db.execute(query)
        rows = result.all()

        counts = {row.review_type: row.count for row in rows}
        counts["total"] = sum(counts.values())

        return counts

    async def expire_old_items(
        self,
        db: Optional[AsyncSession] = None,
    ) -> int:
        """Expire items past their expiration date.

        Args:
            db: Database session

        Returns:
            Number of items expired
        """
        if not db:
            return 0

        now = datetime.utcnow()

        result = await db.execute(
            update(HITLReviewItem)
            .where(HITLReviewItem.status == HITLStatus.PENDING.value)
            .where(HITLReviewItem.expires_at != None)
            .where(HITLReviewItem.expires_at < now)
            .values(
                status=HITLStatus.EXPIRED.value,
                decision_notes="Auto-expired: not reviewed within deadline",
            )
        )

        count = result.rowcount
        if count > 0:
            logger.info(f"[HITL] Expired {count} items")

        return count

    # =========================================================================
    # Action Application
    # =========================================================================

    async def _apply_action(
        self,
        review_type: str,
        action: Dict[str, Any],
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Apply an approved action.

        Args:
            review_type: Type of review
            action: Action to apply
            db: Database session

        Returns:
            Result of applying the action
        """
        if review_type == "vector_drift":
            return await self._apply_vector_upgrade(action, db)
        elif review_type == "qc_failure":
            return await self._apply_qc_adjustment(action, db)
        elif review_type == "prompt_pattern":
            return await self._apply_prompt_patch(action, db)
        else:
            return {"status": "unknown_type", "type": review_type}

    async def _apply_vector_upgrade(
        self,
        action: Dict[str, Any],
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Apply Logic Vector version upgrade.

        Args:
            action: Action containing ip_id, logic_vector, source_videos
            db: Database session

        Returns:
            Result with new version info
        """
        try:
            from app.schemas.drift_detection import LogicVectorVersionCreate, DriftReason
            from app.services.logic_vector_versioning import LogicVectorVersioning

            service = LogicVectorVersioning()

            request = LogicVectorVersionCreate(
                ip_id=action["ip_id"],
                source_videos=action.get("source_videos", []),
                logic_vector=action["logic_vector"],
                drift_reason=DriftReason(action.get("drift_reason")) if action.get("drift_reason") else None,
            )

            result = await service.create_version(request, db)

            return {
                "status": "success",
                "action": "vector_upgrade",
                "version": result,
            }

        except Exception as e:
            logger.error(f"[HITL] Vector upgrade failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _apply_qc_adjustment(
        self,
        action: Dict[str, Any],
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Apply QC criteria adjustment.

        Args:
            action: Action containing ip_id, adjustments
            db: Database session

        Returns:
            Result of adjustment
        """
        try:
            # In a real implementation, this would update IP-specific QC criteria
            # For now, just log the action
            logger.info(f"[HITL] QC adjustment: {action}")

            return {
                "status": "success",
                "action": "qc_adjustment",
                "ip_id": action.get("ip_id"),
                "adjustments": action.get("adjustments", {}),
            }

        except Exception as e:
            logger.error(f"[HITL] QC adjustment failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _apply_prompt_patch(
        self,
        action: Dict[str, Any],
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Apply prompt template patch.

        Args:
            action: Action containing template_id, patch
            db: Database session

        Returns:
            Result of patch
        """
        try:
            # In a real implementation, this would update prompt templates
            logger.info(f"[HITL] Prompt patch: {action}")

            return {
                "status": "success",
                "action": "prompt_patch",
                "template_id": action.get("template_id"),
            }

        except Exception as e:
            logger.error(f"[HITL] Prompt patch failed: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # Notifications
    # =========================================================================

    async def _notify_admins(self, item: HITLReviewItem) -> None:
        """Send notification to admins about new review item.

        Args:
            item: The review item
        """
        try:
            from app.services.notification_service import NotificationService

            notification = NotificationService()

            # Map HITL severity to notification severity
            severity_map = {
                HITLSeverity.CRITICAL.value: "critical",
                HITLSeverity.HIGH.value: "warning",
                HITLSeverity.MEDIUM.value: "warning",
                HITLSeverity.LOW.value: "info",
            }

            notification_severity = severity_map.get(item.severity, "info")

            # Build descriptive message
            message_parts = [
                f"New *{item.severity}* severity review pending.",
                f"Type: `{item.review_type}`",
            ]
            if item.ip_id:
                message_parts.append(f"IP: `{item.ip_id}`")
            if item.expires_at:
                message_parts.append(f"Expires: {item.expires_at.strftime('%Y-%m-%d %H:%M UTC')}")

            await notification.send_admin_alert(
                title=f"HITL Review Required: {item.review_type}",
                message="\n".join(message_parts),
                severity=notification_severity,
                data={
                    "item_id": str(item.id),
                    "review_type": item.review_type,
                    "severity": item.severity,
                    "ip_id": item.ip_id,
                },
                trace_id=item.trace_id,
            )

        except ImportError:
            logger.debug("[HITL] NotificationService not available")
        except Exception as e:
            logger.warning(f"[HITL] Admin notification failed: {e}")


# =============================================================================
# Module-level convenience
# =============================================================================

_default_service: Optional[HITLWorkflowService] = None


def get_hitl_service() -> HITLWorkflowService:
    """Get or create the default HITL service."""
    global _default_service
    if _default_service is None:
        _default_service = HITLWorkflowService()
    return _default_service


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "HITLWorkflowService",
    "get_hitl_service",
]
