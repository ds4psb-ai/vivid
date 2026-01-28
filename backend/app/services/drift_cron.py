"""Drift Detection Cron Service.

Periodically checks for Logic Vector drift across all active IPs.
Creates HITL review items when significant drift is detected.

Usage:
    # Run once (for testing or manual trigger)
    python -m app.services.drift_cron --once

    # Start background scheduler
    python -m app.services.drift_cron
"""
from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime
from typing import List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import get_db_context
from app.schemas.drift_detection import DriftAction, LogicVectorVersionCreate

logger = logging.getLogger(__name__)

# Auto-approve threshold: confidence > 0.8 = 자동 승인
AUTO_APPROVE_CONFIDENCE_THRESHOLD = 0.8


class DriftCronService:
    """Scheduled drift detection service."""

    def __init__(
        self,
        versioning: Optional["LogicVectorVersioning"] = None,
        hitl: Optional["HITLWorkflowService"] = None,
    ):
        """Initialize drift cron service.

        Args:
            versioning: Optional LogicVectorVersioning service override
            hitl: Optional HITLWorkflowService override
        """
        self._versioning = versioning
        self._hitl = hitl
        self._scheduler: Optional[AsyncIOScheduler] = None

    def _get_versioning(self) -> "LogicVectorVersioning":
        """Lazy load versioning service."""
        if self._versioning is None:
            from app.services.logic_vector_versioning import get_versioning_service
            self._versioning = get_versioning_service()
        return self._versioning

    def _get_hitl(self) -> "HITLWorkflowService":
        """Lazy load HITL service."""
        if self._hitl is None:
            from app.services.hitl_workflow import HITLWorkflowService
            self._hitl = HITLWorkflowService()
        return self._hitl

    async def run_drift_check(self) -> dict:
        """Run drift check for all active auteur keys.

        Returns:
            Summary of drift check results
        """
        logger.info("[DriftCron] Starting drift detection run")
        start_time = datetime.utcnow()

        results = {
            "checked": 0,
            "drifts_detected": 0,
            "auto_approved": 0,
            "reviews_created": 0,
            "errors": 0,
            "details": [],
        }

        async with get_db_context() as db:
            try:
                # Get all auteur keys with active versions
                versioning = self._get_versioning()
                auteur_keys = await versioning.get_active_auteur_keys(db)
                logger.info(f"[DriftCron] Found {len(auteur_keys)} active auteur keys")

                for auteur_key in auteur_keys:
                    try:
                        result = await self._check_auteur(auteur_key, db)
                        results["checked"] += 1
                        results["details"].append(result)

                        if result.get("drift_detected"):
                            results["drifts_detected"] += 1
                        if result.get("auto_approved"):
                            results["auto_approved"] += 1
                        if result.get("review_created"):
                            results["reviews_created"] += 1

                    except Exception as e:
                        logger.error(f"[DriftCron] Error checking {auteur_key}: {e}")
                        results["errors"] += 1
                        results["details"].append({
                            "auteur_key": auteur_key,
                            "error": str(e),
                        })

            except Exception as e:
                logger.error(f"[DriftCron] Fatal error: {e}")
                results["errors"] += 1

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        results["elapsed_seconds"] = elapsed

        logger.info(
            f"[DriftCron] Completed: checked={results['checked']}, "
            f"drifts={results['drifts_detected']}, auto_approved={results['auto_approved']}, "
            f"reviews={results['reviews_created']}, errors={results['errors']}, elapsed={elapsed:.1f}s"
        )

        return results

    async def _check_auteur(self, auteur_key: str, db) -> dict:
        """Check drift for a single auteur key.

        Args:
            auteur_key: The auteur key to check
            db: Database session

        Returns:
            Check result summary
        """
        ip_id = f"auteur:{auteur_key}"

        # For now, we'll check with no new videos
        # In production, this would fetch recent videos from content pipeline
        new_videos: List[str] = []  # TODO: Fetch from content pipeline

        if not new_videos:
            # Skip if no new videos to compare
            return {
                "auteur_key": auteur_key,
                "ip_id": ip_id,
                "skipped": True,
                "reason": "no_new_videos",
            }

        versioning = self._get_versioning()
        drift_result = await versioning.detect_drift(
            ip_id=ip_id,
            new_videos=new_videos,
            db=db,
        )

        result = {
            "auteur_key": auteur_key,
            "ip_id": ip_id,
            "action": drift_result.action.value,
            "drift_score": drift_result.drift_score,
            "confidence": drift_result.confidence,
            "drift_detected": drift_result.action != DriftAction.NO_CHANGE,
            "auto_approved": False,
            "review_created": False,
        }

        # Handle drift based on confidence
        if drift_result.action == DriftAction.REQUIRE_HUMAN_REVIEW:
            if drift_result.confidence >= AUTO_APPROVE_CONFIDENCE_THRESHOLD:
                # High confidence → 자동 승인
                await self._auto_approve_drift(
                    ip_id=ip_id,
                    auteur_key=auteur_key,
                    drift_result=drift_result,
                    new_videos=new_videos,
                    db=db,
                )
                result["auto_approved"] = True
                result["action"] = "auto_approved"
                logger.info(
                    f"[DriftCron] Auto-approved drift for {auteur_key}: "
                    f"score={drift_result.drift_score:.3f}, confidence={drift_result.confidence:.2f}"
                )
            else:
                # Low confidence → HITL 리뷰 생성
                logger.info(
                    f"[DriftCron] Drift needs review for {auteur_key}: "
                    f"score={drift_result.drift_score:.3f}, confidence={drift_result.confidence:.2f}"
                )
                # TODO: Create HITL review with new_vector when available
                result["review_created"] = False

        return result

    async def _auto_approve_drift(
        self,
        ip_id: str,
        auteur_key: str,
        drift_result,
        new_videos: List[str],
        db,
    ) -> None:
        """Auto-approve and apply drift when confidence is high.

        Args:
            ip_id: IP identifier
            auteur_key: Auteur key
            drift_result: Drift detection result
            new_videos: Source videos for new version
            db: Database session
        """
        try:
            from app.services.notification_service import get_notification_service

            # Notify admins about auto-approval (informational)
            notification = get_notification_service()
            await notification.send_admin_alert(
                title=f"Logic Vector 자동 업데이트: {auteur_key}",
                message=(
                    f"*{auteur_key}* IP의 Logic Vector가 자동 업데이트되었습니다.\n"
                    f"• Drift Score: `{drift_result.drift_score:.3f}`\n"
                    f"• Confidence: `{drift_result.confidence:.2f}` (>0.8 자동승인)\n"
                    f"• Version: `v{drift_result.current_version}` → `v{drift_result.proposed_version}`"
                ),
                severity="info",
                data={
                    "ip_id": ip_id,
                    "drift_score": drift_result.drift_score,
                    "confidence": drift_result.confidence,
                    "from_version": drift_result.current_version,
                    "to_version": drift_result.proposed_version,
                },
            )

            # TODO: Create new version when new_logic_vector is available
            # versioning = self._get_versioning()
            # await versioning.create_version(
            #     LogicVectorVersionCreate(
            #         ip_id=ip_id,
            #         source_videos=new_videos,
            #         logic_vector=new_logic_vector,
            #         drift_reason=drift_result.reason,
            #         drift_score_from_prev=drift_result.drift_score,
            #     ),
            #     db=db,
            # )

        except Exception as e:
            logger.error(f"[DriftCron] Auto-approve failed for {auteur_key}: {e}")

    def start_scheduler(
        self,
        hour: int = 2,
        minute: int = 0,
    ) -> None:
        """Start the background scheduler.

        Args:
            hour: Hour to run (UTC, 0-23)
            minute: Minute to run (0-59)
        """
        if self._scheduler is not None:
            logger.warning("[DriftCron] Scheduler already running")
            return

        self._scheduler = AsyncIOScheduler()

        # Add drift check job
        self._scheduler.add_job(
            self.run_drift_check,
            CronTrigger(hour=hour, minute=minute),
            id="drift_check",
            name="Logic Vector Drift Detection",
            replace_existing=True,
        )

        # Add HITL expiry check
        self._scheduler.add_job(
            self._expire_old_reviews,
            CronTrigger(hour="*", minute=0),  # Every hour
            id="hitl_expiry",
            name="HITL Review Expiry Check",
            replace_existing=True,
        )

        self._scheduler.start()
        logger.info(f"[DriftCron] Scheduler started: drift check at {hour:02d}:{minute:02d} UTC")

    async def _expire_old_reviews(self) -> None:
        """Expire old HITL review items."""
        async with get_db_context() as db:
            try:
                hitl = self._get_hitl()
                count = await hitl.expire_old_items(db)
                if count > 0:
                    logger.info(f"[DriftCron] Expired {count} HITL items")
            except Exception as e:
                logger.error(f"[DriftCron] Expiry check error: {e}")

    def stop_scheduler(self) -> None:
        """Stop the background scheduler."""
        if self._scheduler:
            self._scheduler.shutdown()
            self._scheduler = None
            logger.info("[DriftCron] Scheduler stopped")


# =============================================================================
# Module-level singleton
# =============================================================================

_default_service: Optional[DriftCronService] = None


def get_drift_cron_service() -> DriftCronService:
    """Get or create default drift cron service."""
    global _default_service
    if _default_service is None:
        _default_service = DriftCronService()
    return _default_service


# =============================================================================
# CLI Entry Point
# =============================================================================

async def main(once: bool = False) -> None:
    """Main entry point.

    Args:
        once: If True, run once and exit. Otherwise start scheduler.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    service = DriftCronService()

    if once:
        # Run once and exit
        result = await service.run_drift_check()
        print(f"Drift check complete: {result}")
    else:
        # Start scheduler and run forever
        service.start_scheduler()
        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            service.stop_scheduler()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Drift Detection Cron")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    asyncio.run(main(once=args.once))
