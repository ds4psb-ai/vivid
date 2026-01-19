"""DMCA Notification Service.

Handles notifications and repeat infringer policy enforcement.
2026 Best Practices: Async-first, structured logging, proper error handling.

Reference:
- https://copyrightalliance.org/education/copyright-law-explained/the-digital-millennium-copyright-act-dmca/dmca-safe-harbor/
- https://patentpc.com/blog/the-complete-dmca-compliance-checklist-for-online-platforms-in-2025
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_ip import DMCACase

logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    """Result of a notification attempt."""
    success: bool
    notification_type: str
    recipient: str
    message: Optional[str] = None
    error: Optional[str] = None


@dataclass
class RepeatInfringerCheck:
    """Result of repeat infringer check."""
    user_id: str
    strike_count: int
    is_repeat_infringer: bool
    threshold: int
    action_taken: Optional[str] = None


class DMCANotificationService:
    """DMCA Notification and Repeat Infringer Policy Service.

    Key responsibilities:
    1. Notify content owners of DMCA takedown notices
    2. Notify claimants of counter-notices
    3. Track and enforce repeat infringer policy
    4. Log all notifications for audit trail
    """

    REPEAT_INFRINGER_THRESHOLD = 3  # Default threshold

    async def notify_content_owner(
        self,
        dmca_case: DMCACase,
        db: AsyncSession,
    ) -> NotificationResult:
        """Notify content owner of DMCA takedown notice.

        Args:
            dmca_case: The DMCA case to notify about
            db: Database session for lookups

        Returns:
            NotificationResult with success status
        """
        # In production, integrate with email service
        # For now, log the notification for audit trail
        logger.info(
            "DMCA_NOTIFICATION: Sending takedown notice to content owner",
            extra={
                "type": "content_owner_takedown",
                "case_id": str(dmca_case.id),
                "user_id": dmca_case.user_id,
                "content_id": str(dmca_case.content_id),
                "claimant": dmca_case.claimant_name,
                "counter_deadline": (
                    dmca_case.counter_deadline.isoformat()
                    if dmca_case.counter_deadline else None
                ),
            }
        )

        # TODO: Integrate with email service when available
        # await email_service.send(
        #     to=user_email,  # Would need to look up from user service
        #     template="dmca_takedown_notice",
        #     context={
        #         "case_id": str(dmca_case.id),
        #         "content_id": str(dmca_case.content_id),
        #         "claimant": dmca_case.claimant_name,
        #         "claim_description": dmca_case.claim_description[:500],
        #         "counter_deadline": dmca_case.counter_deadline,
        #         "counter_url": f"/dmca/counter/{dmca_case.id}",
        #     }
        # )

        return NotificationResult(
            success=True,
            notification_type="content_owner_takedown",
            recipient=dmca_case.user_id,
            message="Takedown notice notification logged",
        )

    async def notify_claimant_counter(
        self,
        dmca_case: DMCACase,
    ) -> NotificationResult:
        """Notify original claimant that a counter-notice was filed.

        Per 17 U.S.C. § 512(g)(2)(B), we must promptly notify the claimant
        that a counter-notice has been received.

        Args:
            dmca_case: The DMCA case with counter-notice

        Returns:
            NotificationResult with success status
        """
        logger.info(
            "DMCA_NOTIFICATION: Notifying claimant of counter-notice",
            extra={
                "type": "claimant_counter_notice",
                "case_id": str(dmca_case.id),
                "claimant_email": dmca_case.claimant_email,
                "restoration_deadline": (
                    dmca_case.counter_deadline.isoformat()
                    if dmca_case.counter_deadline else None
                ),
            }
        )

        # TODO: Integrate with email service
        # await email_service.send(
        #     to=dmca_case.claimant_email,
        #     template="dmca_counter_notice_received",
        #     context={
        #         "case_id": str(dmca_case.id),
        #         "restoration_deadline": dmca_case.counter_deadline,
        #         "message": "A counter-notice has been filed. Content may be restored in 10-14 business days unless you file a court action.",
        #     }
        # )

        return NotificationResult(
            success=True,
            notification_type="claimant_counter_notice",
            recipient=dmca_case.claimant_email,
            message="Counter-notice notification logged",
        )

    async def notify_account_suspension(
        self,
        user_id: str,
        strike_count: int,
        reason: str,
    ) -> NotificationResult:
        """Notify user that their account has been suspended.

        Args:
            user_id: The suspended user's ID
            strike_count: Number of DMCA strikes
            reason: Reason for suspension

        Returns:
            NotificationResult with success status
        """
        logger.warning(
            "DMCA_NOTIFICATION: Account suspended for repeat infringement",
            extra={
                "type": "account_suspension",
                "user_id": user_id,
                "strike_count": strike_count,
                "reason": reason,
            }
        )

        # TODO: Integrate with email service
        # await email_service.send(
        #     to=user_email,
        #     template="account_suspended_repeat_infringer",
        #     context={
        #         "strike_count": strike_count,
        #         "reason": reason,
        #         "appeal_url": "/account/appeal",
        #     }
        # )

        return NotificationResult(
            success=True,
            notification_type="account_suspension",
            recipient=user_id,
            message="Account suspension notification logged",
        )

    async def check_repeat_infringer(
        self,
        user_id: str,
        db: AsyncSession,
        threshold: Optional[int] = None,
    ) -> RepeatInfringerCheck:
        """Check if user is a repeat infringer under DMCA policy.

        Per 17 U.S.C. § 512(i)(1)(A), service providers must reasonably
        implement a policy of terminating repeat infringers.

        Args:
            user_id: User to check
            db: Database session
            threshold: Custom threshold (default: 3)

        Returns:
            RepeatInfringerCheck with status and action
        """
        effective_threshold = threshold or self.REPEAT_INFRINGER_THRESHOLD

        # Count valid DMCA strikes (removed or restored_after_lawsuit, not rejected)
        # Only count cases where counter-notice was not successful
        count_result = await db.execute(
            select(func.count())
            .select_from(DMCACase)
            .where(DMCACase.user_id == user_id)
            .where(DMCACase.status.in_(["removed", "restored_after_lawsuit"]))
        )
        strike_count = count_result.scalar() or 0

        is_repeat = strike_count >= effective_threshold
        action_taken = None

        if is_repeat:
            # Log repeat infringer status
            logger.warning(
                "REPEAT_INFRINGER_DETECTED: User exceeds DMCA strike threshold",
                extra={
                    "user_id": user_id,
                    "strike_count": strike_count,
                    "threshold": effective_threshold,
                }
            )

            # Flag for account action
            # In production, this would trigger account suspension
            action_taken = "flagged_for_suspension"

            # TODO: Integrate with user service for actual suspension
            # await user_service.suspend_account(
            #     user_id=user_id,
            #     reason="DMCA Repeat Infringer Policy",
            # )

        return RepeatInfringerCheck(
            user_id=user_id,
            strike_count=strike_count,
            is_repeat_infringer=is_repeat,
            threshold=effective_threshold,
            action_taken=action_taken,
        )

    async def process_takedown(
        self,
        dmca_case: DMCACase,
        db: AsyncSession,
    ) -> tuple[NotificationResult, RepeatInfringerCheck]:
        """Process a DMCA takedown: notify owner and check repeat infringer status.

        This is the main entry point after admin approves a takedown.

        Args:
            dmca_case: The approved DMCA case
            db: Database session

        Returns:
            Tuple of (notification_result, repeat_check)
        """
        # 1. Notify content owner
        notification = await self.notify_content_owner(dmca_case, db)

        # 2. Check repeat infringer status
        repeat_check = await self.check_repeat_infringer(
            user_id=dmca_case.user_id,
            db=db,
        )

        # 3. If repeat infringer, send suspension notification
        if repeat_check.is_repeat_infringer:
            await self.notify_account_suspension(
                user_id=dmca_case.user_id,
                strike_count=repeat_check.strike_count,
                reason="DMCA Repeat Infringer Policy",
            )

        return notification, repeat_check


# Singleton instance
dmca_notification_service = DMCANotificationService()
