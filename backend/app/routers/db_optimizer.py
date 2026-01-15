"""
Database Optimizer API Router

Provides endpoints for monitoring and optimizing database performance.
Part of P3.2: Database Query Optimization (2026 Best Practices)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.db import get_db_optimizer

router = APIRouter(prefix="/admin/db", tags=["Database Optimizer"])


@router.get("/stats")
async def get_database_stats():
    """
    Get comprehensive database statistics.

    Returns query stats, slow queries, and pool health.
    """
    optimizer = get_db_optimizer()
    return optimizer.get_comprehensive_stats()


@router.get("/slow-queries")
async def get_slow_queries(
    limit: int = Query(default=20, le=100, description="Number of slow queries to return"),
):
    """
    Get the slowest queries recorded.

    Returns queries sorted by execution time (slowest first).
    """
    optimizer = get_db_optimizer()
    return {
        "slow_queries": optimizer.get_slow_queries(limit),
        "threshold_ms": optimizer.profiler.slow_threshold_ms,
    }


@router.get("/pool-health")
async def get_pool_health():
    """
    Check connection pool health.

    Returns pool statistics and recommendations.
    """
    optimizer = get_db_optimizer()
    return optimizer.check_pool_health()


@router.get("/index-recommendations/{table_name}")
async def get_index_recommendations(
    table_name: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get index recommendations for a specific table.

    Analyzes the table and suggests indexes that could improve query performance.
    """
    optimizer = get_db_optimizer()
    recommendations = await optimizer.get_index_recommendations(table_name, db)
    return {
        "table": table_name,
        "recommendations": recommendations,
        "count": len(recommendations),
    }


@router.get("/unused-indexes")
async def get_unused_indexes(
    db: AsyncSession = Depends(get_db),
):
    """
    Get indexes that haven't been used.

    These indexes may be candidates for removal to save disk space
    and improve write performance.
    """
    optimizer = get_db_optimizer()
    unused = await optimizer.get_unused_indexes(db)
    return {
        "unused_indexes": unused,
        "count": len(unused),
        "note": "Review carefully before dropping - indexes may be used by occasional queries",
    }


@router.post("/reset-stats")
async def reset_query_stats():
    """
    Reset query profiling statistics.

    Use this to start fresh monitoring after making optimizations.
    """
    optimizer = get_db_optimizer()
    optimizer.profiler.reset_stats()
    return {"status": "ok", "message": "Query statistics reset"}


@router.get("/query-stats")
async def get_query_stats():
    """
    Get query execution statistics.

    Includes total queries, average time, and breakdown by query type.
    """
    optimizer = get_db_optimizer()
    return optimizer.get_query_stats()
