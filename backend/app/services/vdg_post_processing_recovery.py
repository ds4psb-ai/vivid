"""VDG Post-Processing Recovery Service

Detects and recovers items stuck in 'vdg_saved' state where post-processing
(viral_kicks + cluster_id assignment) failed or was incomplete.

Runs every 5 minutes via the lifespan scheduler.

Usage:
    from app.services.vdg_post_processing_recovery import recover_incomplete_post_processing
    result = await recover_incomplete_post_processing(db)
"""

import logging
from datetime import timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models._all import OutlierItem, PatternCluster, OutlierItemStatus, RemixNode
from app.services.cache import cache
from app.utils.time import utcnow

logger = logging.getLogger(__name__)

# Configuration
LOCK_KEY = "vdg_post_processing_recovery"
LOCK_TIMEOUT = 300  # 5 minutes
MAX_RETRIES = 3
BATCH_LIMIT = 20
STUCK_THRESHOLD_MINUTES = 10  # Items in vdg_saved for 10+ minutes are candidates


async def get_incomplete_items(
    db: AsyncSession,
    threshold_minutes: int = STUCK_THRESHOLD_MINUTES,
    limit: int = BATCH_LIMIT,
) -> List[OutlierItem]:
    """
    Find items where VDG analysis saved but post-processing incomplete.

    Conditions:
    - analysis_status = 'vdg_saved' (VDG completed but post-processing pending)
    - cluster_id is None (clustering not done)
    - stuck_at < now - threshold (to avoid racing with active processing)

    Args:
        db: Database session
        threshold_minutes: Minutes after which an item is considered stuck
        limit: Maximum number of items to return

    Returns:
        List of OutlierItem objects needing post-processing
    """
    cutoff = utcnow() - timedelta(minutes=threshold_minutes)

    result = await db.execute(
        select(OutlierItem)
        .options(selectinload(OutlierItem.promoted_node))
        .where(
            OutlierItem.analysis_status == "vdg_saved",
            OutlierItem.cluster_id.is_(None),
            OutlierItem.stuck_at.isnot(None),
            OutlierItem.stuck_at < cutoff,
            OutlierItem.status == OutlierItemStatus.PROMOTED,
            OutlierItem.promoted_to_node_id.isnot(None),
        )
        .order_by(OutlierItem.stuck_at.asc())  # Oldest first
        .limit(limit)
    )

    return list(result.scalars().all())


async def _process_viral_kicks(
    db: AsyncSession,
    item: OutlierItem,
) -> bool:
    """
    Backfill viral_kicks for an item from its VDG data.

    Returns:
        True if successful, False otherwise
    """
    from app.routers.outliers import _save_viral_kicks_to_table

    promoted_node = item.promoted_node
    if not promoted_node or not promoted_node.gemini_analysis:
        return False

    vdg_data = promoted_node.gemini_analysis
    provenance = vdg_data.get("provenance", {})
    kicks = provenance.get("viral_kicks", [])

    if not kicks:
        # No viral_kicks to save - this is OK
        return True

    try:
        await _save_viral_kicks_to_table(
            db=db,
            node_id=promoted_node.node_id,
            node_uuid=promoted_node.id,
            item_id=item.id,
            vdg_snapshot=vdg_data,
            logger=logger,
        )
        return True
    except Exception as e:
        logger.warning(f"Viral kicks save failed for {item.id}: {e}")
        return False


async def _assign_cluster(
    db: AsyncSession,
    item: OutlierItem,
) -> Optional[UUID]:
    """
    Assign a cluster to the item using hybrid clustering.

    Returns:
        cluster UUID if successful, None otherwise
    """
    from app.services.clustering import PatternClusteringService

    promoted_node = item.promoted_node
    if not promoted_node or not promoted_node.gemini_analysis:
        return None

    vdg_data = promoted_node.gemini_analysis
    clustering_service = PatternClusteringService(db)

    try:
        cluster_id_str, is_new = await clustering_service.get_or_create_cluster_hybrid(
            vdg_data,
            entry_embedding=None,
            vdg_weight=0.6,
            embedding_weight=0.4,
            threshold=0.75,
        )

        # Get the PatternCluster UUID
        cluster_result = await db.execute(select(PatternCluster.id).where(PatternCluster.cluster_id == cluster_id_str))
        cluster_uuid = cluster_result.scalar_one_or_none()

        if cluster_uuid:
            # E5: Incremental DNA Aggregation
            try:
                cluster_obj = await db.get(PatternCluster, cluster_uuid)
                if cluster_obj:
                    from app.services.incremental_dna_aggregator import IncrementalDNAAggregator

                    aggregator = IncrementalDNAAggregator(db)
                    await aggregator.aggregate(cluster=cluster_obj, new_outlier=item, vdg_analysis=vdg_data)
            except Exception as agg_e:
                logger.warning(f"DNA aggregation failed (non-fatal): {agg_e}")

            return cluster_uuid

        return None

    except Exception as e:
        logger.warning(f"Cluster assignment failed for {item.id}: {e}")
        return None


async def recover_incomplete_post_processing(
    db: AsyncSession,
    threshold_minutes: int = STUCK_THRESHOLD_MINUTES,
    limit: int = BATCH_LIMIT,
) -> dict:
    """
    Recover items with incomplete post-processing.

    This is the main entry point for post-processing recovery.
    Uses Redis distributed lock to prevent concurrent execution.

    Args:
        db: Database session
        threshold_minutes: Minutes after which an item is considered stuck
        limit: Maximum number of items to process in one batch

    Returns:
        Dictionary with recovery statistics
    """
    # Acquire distributed lock to prevent concurrent execution
    lock_token = await cache.acquire_lock(LOCK_KEY, timeout=LOCK_TIMEOUT)
    if not lock_token:
        logger.debug("Post-processing recovery lock not acquired (another instance running)")
        return {
            "status": "skipped",
            "reason": "lock_not_acquired",
            "recovered_count": 0,
            "failed_count": 0,
            "permanent_failed_count": 0,
        }

    try:
        items = await get_incomplete_items(db, threshold_minutes, limit)

        if not items:
            logger.debug("No incomplete post-processing items found")
            return {
                "status": "success",
                "recovered_count": 0,
                "failed_count": 0,
                "permanent_failed_count": 0,
                "item_ids": [],
            }

        recovered_count = 0
        failed_count = 0
        permanent_failed_count = 0
        recovered_ids: List[str] = []
        failed_ids: List[str] = []
        permanent_failed_ids: List[str] = []

        for item in items:
            try:
                # Check retry count
                current_retries = item.retry_count or 0

                if current_retries >= MAX_RETRIES:
                    # Mark as post_processing_failed (permanent)
                    item.analysis_status = "post_processing_failed"
                    item.failure_reason = "post_processing_max_retries"
                    item.stuck_at = None
                    permanent_failed_count += 1
                    permanent_failed_ids.append(str(item.id))
                    logger.warning(
                        f"Item {item.id} marked as post_processing_failed " f"after {current_retries} retries"
                    )
                    continue

                # Attempt post-processing
                kicks_ok = await _process_viral_kicks(db, item)
                cluster_uuid = await _assign_cluster(db, item)

                if cluster_uuid:
                    # Success - mark as completed
                    item.cluster_id = cluster_uuid
                    item.analysis_status = "completed"
                    item.stuck_at = None
                    item.last_error = None
                    recovered_count += 1
                    recovered_ids.append(str(item.id))
                    logger.info(f"Item {item.id} post-processing recovered successfully")
                else:
                    # Failed - increment retry count
                    item.retry_count = current_retries + 1
                    item.last_retry_at = utcnow()
                    item.last_error = "cluster_assignment_failed"
                    failed_count += 1
                    failed_ids.append(str(item.id))
                    logger.warning(f"Item {item.id} post-processing failed, " f"retry {item.retry_count}/{MAX_RETRIES}")

            except Exception as e:
                logger.error(f"Error processing item {item.id}: {e}")
                item.retry_count = (item.retry_count or 0) + 1
                item.last_retry_at = utcnow()
                item.last_error = str(e)[:500]
                failed_count += 1
                failed_ids.append(str(item.id))

        await db.commit()

        total_processed = recovered_count + failed_count + permanent_failed_count
        logger.info(
            f"Post-processing recovery complete: {recovered_count} recovered, "
            f"{failed_count} retrying, {permanent_failed_count} permanent failed"
        )

        return {
            "status": "success",
            "recovered_count": recovered_count,
            "failed_count": failed_count,
            "permanent_failed_count": permanent_failed_count,
            "total_processed": total_processed,
            "recovered_ids": recovered_ids,
            "failed_ids": failed_ids,
            "permanent_failed_ids": permanent_failed_ids,
        }

    finally:
        await cache.release_lock(LOCK_KEY, lock_token)


async def get_post_processing_statistics(db: AsyncSession) -> dict:
    """
    Get statistics about items needing post-processing recovery.

    Args:
        db: Database session

    Returns:
        Statistics dictionary
    """
    from sqlalchemy import func

    # Count vdg_saved items without cluster_id
    vdg_saved_count_result = await db.execute(
        select(func.count(OutlierItem.id)).where(
            OutlierItem.analysis_status == "vdg_saved",
            OutlierItem.cluster_id.is_(None),
        )
    )
    vdg_saved_count = vdg_saved_count_result.scalar() or 0

    # Count post_processing_failed items
    failed_count_result = await db.execute(
        select(func.count(OutlierItem.id)).where(OutlierItem.analysis_status == "post_processing_failed")
    )
    failed_count = failed_count_result.scalar() or 0

    # Oldest stuck item
    cutoff = utcnow() - timedelta(minutes=STUCK_THRESHOLD_MINUTES)
    oldest_result = await db.execute(
        select(OutlierItem.stuck_at)
        .where(
            OutlierItem.analysis_status == "vdg_saved",
            OutlierItem.cluster_id.is_(None),
            OutlierItem.stuck_at.isnot(None),
            OutlierItem.stuck_at < cutoff,
        )
        .order_by(OutlierItem.stuck_at.asc())
        .limit(1)
    )
    oldest_stuck_at = oldest_result.scalar_one_or_none()

    oldest_duration_minutes = None
    if oldest_stuck_at:
        oldest_duration_minutes = int((utcnow() - oldest_stuck_at).total_seconds() / 60)

    return {
        "vdg_saved_pending_count": vdg_saved_count,
        "post_processing_failed_count": failed_count,
        "threshold_minutes": STUCK_THRESHOLD_MINUTES,
        "max_retries": MAX_RETRIES,
        "oldest_stuck_duration_minutes": oldest_duration_minutes,
    }


# =============================================================================
# Orphan Promoted Items Recovery
# =============================================================================
# Problem: Items with status="promoted" and promoted_to_node_id set,
# but the corresponding RemixNode doesn't exist in the database.
# This causes reanalyze_vdg() to fail with 404 and creates stuck items.
# =============================================================================

ORPHAN_LOCK_KEY = "vdg_orphan_recovery"


async def get_orphan_promoted_items(
    db: AsyncSession,
    limit: int = BATCH_LIMIT,
) -> List[OutlierItem]:
    """
    Find orphan promoted items where:
    - status = "promoted"
    - promoted_to_node_id is set
    - BUT corresponding RemixNode doesn't exist

    These items are stuck because reanalyze_vdg() will 404 on the missing node.

    Args:
        db: Database session
        limit: Maximum number of items to return

    Returns:
        List of orphan OutlierItem objects
    """
    result = await db.execute(
        select(OutlierItem)
        .outerjoin(RemixNode, OutlierItem.promoted_to_node_id == RemixNode.id)
        .where(
            OutlierItem.status == OutlierItemStatus.PROMOTED,
            OutlierItem.promoted_to_node_id.isnot(None),
            RemixNode.id.is_(None),  # LEFT JOIN returns no match
        )
        .limit(limit)
    )
    return list(result.scalars().all())


async def recover_orphan_promoted_items(
    db: AsyncSession,
    limit: int = BATCH_LIMIT,
) -> dict:
    """
    Reset orphan promoted items to pending status.

    Orphan items are those with status="promoted" and promoted_to_node_id set,
    but the RemixNode doesn't exist. These are reset to pending so they can
    be re-approved and properly processed.

    Uses Redis distributed lock to prevent concurrent execution.

    Args:
        db: Database session
        limit: Maximum number of items to process

    Returns:
        Dictionary with recovery statistics
    """
    lock_token = await cache.acquire_lock(ORPHAN_LOCK_KEY, timeout=LOCK_TIMEOUT)
    if not lock_token:
        logger.debug("Orphan recovery lock not acquired (another instance running)")
        return {
            "status": "skipped",
            "reason": "lock_not_acquired",
            "recovered_count": 0,
        }

    try:
        orphans = await get_orphan_promoted_items(db, limit)

        if not orphans:
            logger.debug("No orphan promoted items found")
            return {
                "status": "success",
                "recovered_count": 0,
                "item_ids": [],
            }

        recovered_count = 0
        recovered_ids: List[str] = []

        for item in orphans:
            old_node_id = item.promoted_to_node_id
            item.status = OutlierItemStatus.PENDING
            item.promoted_to_node_id = None
            item.analysis_status = "pending"
            item.retry_count = 0
            item.failure_reason = None
            item.last_error = None
            item.stuck_at = None
            recovered_count += 1
            recovered_ids.append(str(item.id))
            logger.warning(f"[OrphanRecovery] Reset {item.id} to pending " f"(missing node: {old_node_id})")

        await db.commit()

        if recovered_count > 0:
            logger.info(f"[OrphanRecovery] Recovered {recovered_count} orphan items: " f"{recovered_ids}")

        return {
            "status": "success",
            "recovered_count": recovered_count,
            "item_ids": recovered_ids,
        }

    finally:
        await cache.release_lock(ORPHAN_LOCK_KEY, lock_token)


# =============================================================================
# Failed Items with VDG Recovery
# =============================================================================
# Problem: Items with analysis_status in (failed_permanent, failed_retryable, vdg_saved)
# but RemixNode.gemini_analysis exists. These are legacy items where VDG analysis
# completed but status wasn't updated properly.
# =============================================================================

FAILED_WITH_VDG_LOCK_KEY = "vdg_failed_with_vdg_recovery"


async def recover_failed_items_with_vdg(
    db: AsyncSession,
    limit: int = BATCH_LIMIT,
) -> dict:
    """
    Recover items where VDG analysis exists but status is still failed.

    These are legacy items where:
    - analysis_status in ('failed_permanent', 'failed_retryable', 'vdg_saved', 'analyzing')
    - RemixNode exists with gemini_analysis populated

    Uses Redis distributed lock to prevent concurrent execution.

    Args:
        db: Database session
        limit: Maximum number of items to process

    Returns:
        Dictionary with recovery statistics
    """
    lock_token = await cache.acquire_lock(FAILED_WITH_VDG_LOCK_KEY, timeout=LOCK_TIMEOUT)
    if not lock_token:
        logger.debug("Failed-with-VDG recovery lock not acquired (another instance running)")
        return {
            "status": "skipped",
            "reason": "lock_not_acquired",
            "recovered_count": 0,
        }

    try:
        # Find items with failed status but VDG exists
        result = await db.execute(
            select(OutlierItem, RemixNode)
            .join(RemixNode, OutlierItem.promoted_to_node_id == RemixNode.id)
            .where(
                OutlierItem.analysis_status.in_(["failed_permanent", "failed_retryable", "vdg_saved", "analyzing"]),
                RemixNode.gemini_analysis.isnot(None),
            )
            .limit(limit)
        )
        rows = result.all()

        if not rows:
            logger.debug("No failed items with VDG found")
            return {
                "status": "success",
                "recovered_count": 0,
                "item_ids": [],
            }

        recovered_count = 0
        recovered_ids: List[str] = []

        for item, node in rows:
            old_status = item.analysis_status
            item.analysis_status = "completed"
            item.stuck_at = None
            item.last_error = None
            recovered_count += 1
            recovered_ids.append(str(item.id))
            logger.info(f"[FailedWithVDG] Recovered {item.id}: {old_status} -> completed")

        await db.commit()

        if recovered_count > 0:
            logger.info(f"[FailedWithVDG] Recovered {recovered_count} items: {recovered_ids}")

        return {
            "status": "success",
            "recovered_count": recovered_count,
            "item_ids": recovered_ids,
        }

    finally:
        await cache.release_lock(FAILED_WITH_VDG_LOCK_KEY, lock_token)
