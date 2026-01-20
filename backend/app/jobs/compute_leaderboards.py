"""Leaderboard Computation Job (Phase 9).

Computes and caches leaderboard snapshots for fast dashboard queries.

Schedule: Hourly
Target: < 2 minutes execution time

Usage:
    # Manual trigger
    from app.jobs.compute_leaderboards import compute_leaderboards_job
    await compute_leaderboards_job()

    # Or via scheduler
    scheduler.add_job(compute_leaderboards_job, "interval", hours=1)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Any

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models_analytics import LeaderboardSnapshot
from app.models_telemetry import ToolRunEvent, ToolManifest

logger = logging.getLogger(__name__)


# Leaderboard configurations
LEADERBOARD_CONFIGS = [
    {
        "type": "creator_revenue",
        "period_types": ["daily", "weekly", "monthly"],
        "scope": "global",
    },
    {
        "type": "tool_usage",
        "period_types": ["daily", "weekly", "monthly"],
        "scope": "global",
    },
    {
        "type": "engagement_score",
        "period_types": ["weekly", "monthly"],
        "scope": "global",
    },
]


async def compute_leaderboards_job() -> dict:
    """Hourly job: Compute leaderboard snapshots.

    Computes rankings for all configured leaderboard types.

    Returns:
        Job result summary
    """
    start_time = datetime.utcnow()
    logger.info("Starting leaderboard computation job")

    async with AsyncSessionLocal() as db:
        try:
            snapshots_created = 0

            for config in LEADERBOARD_CONFIGS:
                for period_type in config["period_types"]:
                    try:
                        snapshot = await _compute_leaderboard(
                            db,
                            config["type"],
                            period_type,
                            config["scope"],
                        )
                        if snapshot:
                            db.add(snapshot)
                            snapshots_created += 1
                    except Exception as e:
                        logger.warning(
                            f"Error computing {config['type']} {period_type}: {e}"
                        )

            await db.commit()

            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"Leaderboard computation completed: {snapshots_created} snapshots, "
                f"{elapsed:.2f}s"
            )

            return {
                "status": "completed",
                "snapshots_created": snapshots_created,
                "elapsed_seconds": elapsed,
            }

        except Exception as e:
            logger.exception(f"Leaderboard computation job failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
            }


async def _compute_leaderboard(
    db: AsyncSession,
    leaderboard_type: str,
    period_type: str,
    scope: str,
    limit: int = 100,
) -> LeaderboardSnapshot | None:
    """Compute a single leaderboard snapshot.

    Args:
        db: Database session
        leaderboard_type: Type of leaderboard
        period_type: Period granularity
        scope: Scope (global, dimension, category)
        limit: Max entries

    Returns:
        LeaderboardSnapshot or None if no data
    """
    now = datetime.utcnow()
    period_date = now.date()

    # Calculate lookback period
    if period_type == "daily":
        since = now - timedelta(days=1)
    elif period_type == "weekly":
        since = now - timedelta(weeks=1)
    else:  # monthly
        since = now - timedelta(days=30)

    # Get previous rankings for delta calculation
    prev_rankings = await _get_previous_rankings(
        db, leaderboard_type, period_type, scope
    )

    # Compute rankings based on type
    if leaderboard_type == "creator_revenue":
        rankings = await _compute_creator_revenue_rankings(db, since, limit)
    elif leaderboard_type == "tool_usage":
        rankings = await _compute_tool_usage_rankings(db, since, limit)
    elif leaderboard_type == "engagement_score":
        rankings = await _compute_engagement_rankings(db, since, limit)
    else:
        logger.warning(f"Unknown leaderboard type: {leaderboard_type}")
        return None

    if not rankings:
        return None

    # Add rank deltas
    for entry in rankings:
        user_id = entry["user_id"]
        if user_id in prev_rankings:
            entry["delta"] = prev_rankings[user_id] - entry["rank"]
        else:
            entry["delta"] = None  # New entry

    return LeaderboardSnapshot(
        leaderboard_type=leaderboard_type,
        scope=scope,
        scope_value=None,
        period_type=period_type,
        period_date=period_date,
        rankings=rankings,
    )


async def _compute_creator_revenue_rankings(
    db: AsyncSession,
    since: datetime,
    limit: int,
) -> List[Dict[str, Any]]:
    """Compute creator revenue rankings."""
    result = await db.execute(
        select(
            ToolManifest.created_by,
            func.sum(ToolRunEvent.credits_charged - ToolRunEvent.credits_refunded).label("score"),
        )
        .join(ToolManifest, ToolRunEvent.tool_id == ToolManifest.id)
        .where(
            ToolRunEvent.created_at >= since,
            ToolManifest.created_by.isnot(None),
        )
        .group_by(ToolManifest.created_by)
        .order_by(desc("score"))
        .limit(limit)
    )

    return [
        {
            "rank": i + 1,
            "user_id": row[0],
            "score": float(row[1] or 0),
        }
        for i, row in enumerate(result)
    ]


async def _compute_tool_usage_rankings(
    db: AsyncSession,
    since: datetime,
    limit: int,
) -> List[Dict[str, Any]]:
    """Compute tool usage rankings."""
    result = await db.execute(
        select(
            ToolRunEvent.user_id,
            func.count().label("score"),
        )
        .where(
            ToolRunEvent.created_at >= since,
            ToolRunEvent.user_id.isnot(None),
        )
        .group_by(ToolRunEvent.user_id)
        .order_by(desc("score"))
        .limit(limit)
    )

    return [
        {
            "rank": i + 1,
            "user_id": row[0],
            "score": float(row[1] or 0),
        }
        for i, row in enumerate(result)
    ]


async def _compute_engagement_rankings(
    db: AsyncSession,
    since: datetime,
    limit: int,
) -> List[Dict[str, Any]]:
    """Compute engagement score rankings.

    Uses a composite score based on activity frequency and success rate.
    """
    result = await db.execute(
        select(
            ToolRunEvent.user_id,
            func.count().label("total_runs"),
            func.sum(
                func.case(
                    (ToolRunEvent.status == "success", 1),
                    else_=0,
                )
            ).label("successful_runs"),
        )
        .where(
            ToolRunEvent.created_at >= since,
            ToolRunEvent.user_id.isnot(None),
        )
        .group_by(ToolRunEvent.user_id)
        .having(func.count() >= 5)  # Minimum activity threshold
        .order_by(desc("total_runs"))
        .limit(limit)
    )

    rankings = []
    for i, row in enumerate(result):
        total = row[1] or 0
        successful = row[2] or 0
        success_rate = successful / total if total > 0 else 0

        # Engagement score = frequency * success_rate
        score = total * (0.5 + 0.5 * success_rate)

        rankings.append({
            "rank": i + 1,
            "user_id": row[0],
            "score": round(score, 2),
            "total_runs": total,
            "success_rate": round(success_rate, 2),
        })

    # Re-sort by computed score
    rankings.sort(key=lambda x: x["score"], reverse=True)
    for i, r in enumerate(rankings):
        r["rank"] = i + 1

    return rankings


async def _get_previous_rankings(
    db: AsyncSession,
    leaderboard_type: str,
    period_type: str,
    scope: str,
) -> Dict[str, int]:
    """Get previous rankings for delta calculation.

    Args:
        db: Database session
        leaderboard_type: Type of leaderboard
        period_type: Period granularity
        scope: Scope

    Returns:
        Dict mapping user_id to rank
    """
    result = await db.execute(
        select(LeaderboardSnapshot)
        .where(
            LeaderboardSnapshot.leaderboard_type == leaderboard_type,
            LeaderboardSnapshot.period_type == period_type,
            LeaderboardSnapshot.scope == scope,
        )
        .order_by(desc(LeaderboardSnapshot.computed_at))
        .limit(1)
    )
    prev_snapshot = result.scalar_one_or_none()

    if not prev_snapshot:
        return {}

    return {
        entry["user_id"]: entry["rank"]
        for entry in prev_snapshot.rankings
    }
