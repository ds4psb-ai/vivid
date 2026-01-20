"""Daily Revenue Metrics Aggregation Job (Phase 9).

Aggregates user revenue metrics daily for fast dashboard queries.

Schedule: Daily at 00:05 UTC
Target: < 5 minutes execution time

Usage:
    # Manual trigger
    from app.jobs.aggregate_revenue_metrics import aggregate_daily_revenue_job
    await aggregate_daily_revenue_job()

    # Or via scheduler
    scheduler.add_job(aggregate_daily_revenue_job, "cron", hour=0, minute=5)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, date
from typing import List

from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models_telemetry import ToolRunEvent
from app.services.revenue_attribution_service import RevenueAttributionService

logger = logging.getLogger(__name__)


async def aggregate_daily_revenue_job(
    target_date: date | None = None,
) -> dict:
    """Daily job: Aggregate user revenue metrics.

    Runs at 00:05 UTC to aggregate the previous day's data.

    Args:
        target_date: Date to aggregate (defaults to yesterday)

    Returns:
        Job result summary
    """
    start_time = datetime.utcnow()
    logger.info("Starting daily revenue aggregation job")

    if target_date is None:
        target_date = (datetime.utcnow() - timedelta(days=1)).date()

    logger.info(f"Aggregating revenue for date: {target_date}")

    async with AsyncSessionLocal() as db:
        try:
            # Get all users with activity on the target date
            user_ids = await _get_active_users(db, target_date)
            logger.info(f"Found {len(user_ids)} active users")

            service = RevenueAttributionService(db)
            processed = 0
            errors = 0

            for user_id in user_ids:
                try:
                    # Generate and save snapshot
                    snapshot = await service.aggregate_daily_snapshot(user_id, target_date)
                    await service.save_daily_snapshot(snapshot)
                    processed += 1

                    # Log progress every 100 users
                    if processed % 100 == 0:
                        logger.info(f"Processed {processed}/{len(user_ids)} users")

                except Exception as e:
                    logger.warning(f"Error aggregating user {user_id}: {e}")
                    errors += 1

            await db.commit()

            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"Revenue aggregation completed: {processed} users, "
                f"{errors} errors, {elapsed:.2f}s"
            )

            return {
                "status": "completed",
                "target_date": target_date.isoformat(),
                "users_processed": processed,
                "errors": errors,
                "elapsed_seconds": elapsed,
            }

        except Exception as e:
            logger.exception(f"Revenue aggregation job failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
            }


async def _get_active_users(
    db: AsyncSession,
    target_date: date,
) -> List[str]:
    """Get users with activity on the target date.

    Args:
        db: Database session
        target_date: Date to check

    Returns:
        List of user IDs
    """
    start_dt = datetime.combine(target_date, datetime.min.time())
    end_dt = datetime.combine(target_date, datetime.max.time())

    result = await db.execute(
        select(distinct(ToolRunEvent.user_id))
        .where(
            ToolRunEvent.created_at >= start_dt,
            ToolRunEvent.created_at <= end_dt,
            ToolRunEvent.user_id.isnot(None),
        )
    )

    return [row[0] for row in result if row[0]]


async def backfill_revenue_metrics(
    start_date: date,
    end_date: date,
) -> dict:
    """Backfill revenue metrics for a date range.

    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)

    Returns:
        Job result summary
    """
    logger.info(f"Backfilling revenue metrics from {start_date} to {end_date}")

    current_date = start_date
    total_processed = 0
    total_errors = 0

    while current_date <= end_date:
        result = await aggregate_daily_revenue_job(current_date)

        if result["status"] == "completed":
            total_processed += result.get("users_processed", 0)
            total_errors += result.get("errors", 0)
        else:
            total_errors += 1

        current_date += timedelta(days=1)

    return {
        "status": "completed",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_users_processed": total_processed,
        "total_errors": total_errors,
    }
