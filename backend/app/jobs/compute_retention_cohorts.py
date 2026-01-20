"""Retention Cohort Computation Job (Phase 9).

Computes retention cohort matrices for analytics dashboards.

Schedule: Weekly (Monday 01:00 UTC)
Target: < 10 minutes execution time

Usage:
    # Manual trigger
    from app.jobs.compute_retention_cohorts import compute_retention_cohorts_job
    await compute_retention_cohorts_job()

    # Or via scheduler
    scheduler.add_job(compute_retention_cohorts_job, "cron", day_of_week="mon", hour=1)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, date
from typing import List

from app.database import AsyncSessionLocal
from app.services.engagement_analytics_service import EngagementAnalyticsService

logger = logging.getLogger(__name__)


# Cohort configurations
COHORT_CONFIGS = [
    {
        "cohort_type": "first_tool",
        "period_type": "weekly",
        "lookback_periods": 12,
    },
    {
        "cohort_type": "first_tool",
        "period_type": "monthly",
        "lookback_periods": 6,
    },
]


async def compute_retention_cohorts_job() -> dict:
    """Weekly job: Compute retention cohort snapshots.

    Computes retention matrices for configured cohort types.

    Returns:
        Job result summary
    """
    start_time = datetime.utcnow()
    logger.info("Starting retention cohort computation job")

    async with AsyncSessionLocal() as db:
        try:
            service = EngagementAnalyticsService(db)
            snapshots_created = 0
            total_cohorts = 0

            for config in COHORT_CONFIGS:
                try:
                    logger.info(
                        f"Computing {config['cohort_type']} "
                        f"{config['period_type']} cohorts"
                    )

                    cohorts = await service.compute_retention_cohorts(
                        config["cohort_type"],
                        config["period_type"],
                        config["lookback_periods"],
                    )

                    for cohort in cohorts:
                        await service.save_retention_cohort(cohort)
                        snapshots_created += 1

                    total_cohorts += len(cohorts)

                except Exception as e:
                    logger.warning(
                        f"Error computing {config['cohort_type']} cohorts: {e}"
                    )

            await db.commit()

            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"Retention cohort computation completed: {snapshots_created} snapshots "
                f"for {total_cohorts} cohorts, {elapsed:.2f}s"
            )

            return {
                "status": "completed",
                "snapshots_created": snapshots_created,
                "total_cohorts": total_cohorts,
                "elapsed_seconds": elapsed,
            }

        except Exception as e:
            logger.exception(f"Retention cohort computation job failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
            }


async def backfill_retention_cohorts(
    cohort_type: str,
    period_type: str,
    lookback_periods: int = 24,
) -> dict:
    """Backfill retention cohorts for historical analysis.

    Args:
        cohort_type: Type of cohort
        period_type: Period granularity
        lookback_periods: Number of periods to compute

    Returns:
        Job result summary
    """
    logger.info(
        f"Backfilling {cohort_type} {period_type} cohorts "
        f"for {lookback_periods} periods"
    )

    async with AsyncSessionLocal() as db:
        try:
            service = EngagementAnalyticsService(db)

            cohorts = await service.compute_retention_cohorts(
                cohort_type,
                period_type,
                lookback_periods,
            )

            for cohort in cohorts:
                await service.save_retention_cohort(cohort)

            await db.commit()

            return {
                "status": "completed",
                "cohort_type": cohort_type,
                "period_type": period_type,
                "cohorts_created": len(cohorts),
            }

        except Exception as e:
            logger.exception(f"Retention cohort backfill failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
            }
