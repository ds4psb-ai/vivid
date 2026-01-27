"""VDG Reanalysis Queue Service

Manages automatic reanalysis of items that failed or have empty visual data.
Implements exponential backoff with jitter: 5min, 15min, 45min (±20%)

Usage:
    from app.services.vdg_reanalysis_queue import get_reanalysis_candidates, process_reanalysis_queue
    candidates = await get_reanalysis_candidates(db)
    result = await process_reanalysis_queue(db, limit=10)
"""

import logging
import random
from datetime import timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models._all import OutlierItem, RemixNode
from app.utils.time import utcnow

logger = logging.getLogger(__name__)

# Exponential backoff intervals (in minutes)
BACKOFF_INTERVALS = [5, 15, 45]  # 5min, 15min, 45min
MAX_RETRIES = 3


def calculate_backoff_minutes(retry_count: int, with_jitter: bool = True) -> int:
    """
    Calculate backoff interval based on retry count with optional jitter.

    Jitter adds ±20% randomization to prevent thundering herd problem
    when multiple items retry simultaneously.

    Args:
        retry_count: Current retry count (1, 2, or 3)
        with_jitter: Add ±20% random jitter (default: True)

    Returns:
        Backoff interval in minutes

    Examples:
        retry_count=1 -> ~5 minutes (4-6 with jitter)
        retry_count=2 -> ~15 minutes (12-18 with jitter)
        retry_count=3 -> ~45 minutes (36-54 with jitter)
    """
    if retry_count <= 0:
        base = BACKOFF_INTERVALS[0]
    elif retry_count > len(BACKOFF_INTERVALS):
        base = BACKOFF_INTERVALS[-1]
    else:
        base = BACKOFF_INTERVALS[retry_count - 1]

    if with_jitter:
        # Add ±20% jitter to prevent thundering herd
        jitter_factor = 1.0 + random.uniform(-0.2, 0.2)
        return max(1, int(base * jitter_factor))

    return base


def is_ready_for_retry(item: OutlierItem) -> bool:
    """
    Check if an item has waited long enough for retry based on backoff.

    Args:
        item: OutlierItem to check

    Returns:
        True if enough time has passed since last retry
    """
    if not item.last_retry_at:
        return True  # Never retried, ready now

    retry_count = item.retry_count or 0
    backoff_minutes = calculate_backoff_minutes(retry_count)
    ready_at = item.last_retry_at + timedelta(minutes=backoff_minutes)

    return utcnow() >= ready_at


async def get_reanalysis_candidates(
    db: AsyncSession,
    limit: int = 50,
    include_visual_empty: bool = True,
    include_failed_retryable: bool = True,
    include_comments_failed: bool = True,
) -> List[OutlierItem]:
    """
    Get items eligible for reanalysis.

    Candidates include:
    - Items with visual_empty=True (VDG completed but no visual data)
    - Items with analysis_status='failed_retryable' (temporary failure)
    - Items with analysis_status='comments_failed' (comment extraction failed)
    - Items with analysis_status='comments_pending_review' (awaiting manual comment)

    All must have retry_count < MAX_RETRIES and respect backoff timing.

    Args:
        db: Database session
        limit: Maximum number of candidates to return
        include_visual_empty: Include visual_empty items
        include_failed_retryable: Include failed_retryable items
        include_comments_failed: Include comments_failed/comments_pending_review items

    Returns:
        List of OutlierItem candidates ready for reanalysis
    """
    conditions = []

    if include_visual_empty:
        # Visual empty: completed but no visual data
        conditions.append(
            and_(
                OutlierItem.analysis_status == "completed",
                OutlierItem.visual_empty == True,
                OutlierItem.retry_count < MAX_RETRIES,
            )
        )

    if include_failed_retryable:
        # Failed retryable: temporary failure
        conditions.append(
            and_(
                OutlierItem.analysis_status == "failed_retryable",
                OutlierItem.retry_count < MAX_RETRIES,
            )
        )

    if include_comments_failed:
        # Comments failed: comment extraction failed (Self-healing may fix)
        conditions.append(
            and_(
                OutlierItem.analysis_status == "comments_failed",
                OutlierItem.retry_count < MAX_RETRIES,
            )
        )
        # Comments pending review: awaiting manual comment (auto-retry with Self-healing)
        conditions.append(
            and_(
                OutlierItem.analysis_status == "comments_pending_review",
                OutlierItem.retry_count < MAX_RETRIES,
            )
        )

    if not conditions:
        return []

    result = await db.execute(
        select(OutlierItem)
        .where(or_(*conditions))
        .order_by(OutlierItem.last_retry_at.asc().nullsfirst())  # Never retried first
        .limit(limit * 2)  # Get more than needed to filter by backoff
    )

    candidates = list(result.scalars().all())

    # Filter by backoff timing
    ready_candidates = [item for item in candidates if is_ready_for_retry(item)][:limit]

    return ready_candidates


async def queue_for_reanalysis(
    db: AsyncSession,
    item: OutlierItem,
) -> bool:
    """
    Queue a single item for reanalysis with idempotency protection.

    Sets the item to 'approved' status and clears stuck_at.
    The item will be picked up by the normal analysis flow.

    Idempotency: Skips items already being processed (analyzing state)
    to prevent duplicate execution.

    Args:
        db: Database session
        item: OutlierItem to queue

    Returns:
        True if successfully queued
    """
    # Idempotency: Skip if already being processed
    if item.analysis_status == "analyzing":
        logger.info(f"Skipping {item.id} - already being analyzed (idempotency)")
        return False

    # Verify item has a promoted node (required for VDG)
    if not item.promoted_to_node_id:
        logger.warning(f"Cannot queue {item.id} - no promoted node")
        return False

    # Check retry limit
    if (item.retry_count or 0) >= MAX_RETRIES:
        logger.warning(f"Cannot queue {item.id} - max retries exceeded")
        return False

    # Idempotency: Check if item was recently modified (within last 60 seconds)
    # This prevents race conditions when multiple workers try to queue the same item
    if item.last_retry_at:
        seconds_since_last_retry = (utcnow() - item.last_retry_at).total_seconds()
        if seconds_since_last_retry < 60:
            logger.info(f"Skipping {item.id} - recently processed {seconds_since_last_retry:.0f}s ago (idempotency)")
            return False

    # Reset for reanalysis - directly to "analyzing" to avoid dead end state
    item.analysis_status = "analyzing"
    item.stuck_at = utcnow()  # For stuck_recovery to track
    # Note: Don't increment retry_count here - it's incremented when analysis starts

    logger.info(f"Queued {item.id} for reanalysis (retry {item.retry_count or 0}/{MAX_RETRIES})")
    return True


async def process_reanalysis_queue(
    db: AsyncSession,
    limit: int = 10,
    trigger_analysis: bool = True,
) -> dict:
    """
    Process the reanalysis queue.

    Gets candidates, queues them for reanalysis, and optionally triggers analysis.

    Args:
        db: Database session
        limit: Maximum number of items to process
        trigger_analysis: If True, trigger VDG analysis for each item

    Returns:
        Statistics about processed items
    """
    from app.routers.outliers import _run_vdg_analysis_with_comments

    candidates = await get_reanalysis_candidates(db, limit=limit)

    if not candidates:
        logger.info("No reanalysis candidates found")
        return {
            "queued_count": 0,
            "triggered_count": 0,
            "skipped_count": 0,
            "item_ids": [],
        }

    queued_count = 0
    triggered_count = 0
    skipped_count = 0
    queued_ids: List[str] = []

    for item in candidates:
        # Get associated node for analysis
        node_result = await db.execute(select(RemixNode).where(RemixNode.id == item.promoted_to_node_id))
        node = node_result.scalar_one_or_none()

        if not node:
            logger.warning(f"Skipping {item.id} - node not found")
            skipped_count += 1
            continue

        # Queue the item
        if await queue_for_reanalysis(db, item):
            queued_count += 1
            queued_ids.append(str(item.id))

            # Trigger analysis if requested
            if trigger_analysis and item.video_url:
                try:
                    # Set to analyzing state
                    item.analysis_status = "analyzing"
                    item.stuck_at = utcnow()
                    item.retry_count = (item.retry_count or 0) + 1
                    item.last_retry_at = utcnow()
                    await db.commit()

                    # Note: In production, this should be a background task
                    # For now, we just queue it and let the caller handle async execution
                    triggered_count += 1
                    logger.info(f"Triggered reanalysis for {item.id}")

                except Exception as e:
                    logger.error(f"Failed to trigger analysis for {item.id}: {e}")
        else:
            skipped_count += 1

    await db.commit()

    logger.info(
        f"Reanalysis queue processed: {queued_count} queued, " f"{triggered_count} triggered, {skipped_count} skipped"
    )

    return {
        "queued_count": queued_count,
        "triggered_count": triggered_count,
        "skipped_count": skipped_count,
        "item_ids": queued_ids,
    }


async def queue_items_for_reanalysis(
    db: AsyncSession,
    item_ids: List[UUID],
    reason: str = "manual",
) -> int:
    """
    Queue multiple items for reanalysis by ID.

    Used by self-healing service to trigger batch reanalysis.

    Args:
        db: Database session
        item_ids: List of OutlierItem UUIDs to queue
        reason: Reason for reanalysis (for logging)

    Returns:
        Number of items successfully queued
    """
    if not item_ids:
        return 0

    result = await db.execute(select(OutlierItem).where(OutlierItem.id.in_(item_ids)))
    items = list(result.scalars().all())

    queued_count = 0
    for item in items:
        # Skip items already being processed or at max retries
        if item.analysis_status == "analyzing":
            continue
        if (item.retry_count or 0) >= MAX_RETRIES:
            continue

        # Reset for reanalysis - directly to "analyzing" to avoid dead end state
        item.analysis_status = "analyzing"
        item.stuck_at = utcnow()  # For stuck_recovery to track
        item.retry_count = (item.retry_count or 0) + 1
        item.last_retry_at = utcnow()
        queued_count += 1

    await db.commit()

    logger.info(f"[ReanalysisQueue] Queued {queued_count}/{len(item_ids)} items " f"for reanalysis (reason={reason})")

    return queued_count


async def get_reanalysis_statistics(db: AsyncSession) -> dict:
    """
    Get statistics about items eligible for reanalysis.

    Args:
        db: Database session

    Returns:
        Statistics about reanalysis candidates
    """
    from sqlalchemy import func

    # Count visual_empty items
    visual_empty_result = await db.execute(
        select(func.count(OutlierItem.id))
        .where(OutlierItem.analysis_status == "completed")
        .where(OutlierItem.visual_empty == True)
        .where(OutlierItem.retry_count < MAX_RETRIES)
    )
    visual_empty_count = visual_empty_result.scalar() or 0

    # Count failed_retryable items
    failed_retryable_result = await db.execute(
        select(func.count(OutlierItem.id))
        .where(OutlierItem.analysis_status == "failed_retryable")
        .where(OutlierItem.retry_count < MAX_RETRIES)
    )
    failed_retryable_count = failed_retryable_result.scalar() or 0

    # Count failed_permanent items
    failed_permanent_result = await db.execute(
        select(func.count(OutlierItem.id)).where(OutlierItem.analysis_status == "failed_permanent")
    )
    failed_permanent_count = failed_permanent_result.scalar() or 0

    # Count comments_failed items
    comments_failed_result = await db.execute(
        select(func.count(OutlierItem.id))
        .where(OutlierItem.analysis_status.in_(["comments_failed", "comments_pending_review"]))
        .where(OutlierItem.retry_count < MAX_RETRIES)
    )
    comments_failed_count = comments_failed_result.scalar() or 0

    # Ready for retry now
    candidates = await get_reanalysis_candidates(db, limit=1000)
    ready_count = len(candidates)

    return {
        "visual_empty_count": visual_empty_count,
        "failed_retryable_count": failed_retryable_count,
        "failed_permanent_count": failed_permanent_count,
        "comments_failed_count": comments_failed_count,
        "ready_for_retry_count": ready_count,
        "max_retries": MAX_RETRIES,
        "backoff_intervals_minutes": BACKOFF_INTERVALS,
    }
