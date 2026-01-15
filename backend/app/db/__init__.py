"""
Database Optimization Module - 2026 Best Practices

This module provides production-ready database optimization:
1. QueryProfiler - Slow query detection and profiling
2. IndexAdvisor - Index recommendation engine
3. ConnectionPoolMonitor - Pool health monitoring
4. QueryCache - Query result caching

Usage:
    from app.db import get_db_optimizer, QueryProfiler

    # Profile slow queries
    profiler = QueryProfiler()
    async with profiler.profile():
        result = await session.execute(query)

    # Get index recommendations
    advisor = get_db_optimizer().index_advisor
    recommendations = await advisor.analyze_table("users")
"""

from app.db.query_optimizer import (
    QueryProfiler,
    IndexAdvisor,
    ConnectionPoolMonitor,
    DatabaseOptimizer,
    get_db_optimizer,
    SlowQueryEvent,
    IndexRecommendation,
    PoolStats,
)

__all__ = [
    "QueryProfiler",
    "IndexAdvisor",
    "ConnectionPoolMonitor",
    "DatabaseOptimizer",
    "get_db_optimizer",
    "SlowQueryEvent",
    "IndexRecommendation",
    "PoolStats",
]
