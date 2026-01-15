"""
Database Query Optimizer - 2026 Best Practices Implementation

Comprehensive database optimization with:
1. Slow query profiling and detection
2. Index recommendation engine
3. Connection pool monitoring
4. Query execution statistics

References:
- https://www.postgresql.org/docs/current/performance-tips.html
- SQLAlchemy 2.0 async best practices
- PostgreSQL EXPLAIN ANALYZE patterns
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from sqlalchemy import text, event
from sqlalchemy.engine import Engine

from app.config import settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

# Slow query threshold in milliseconds
SLOW_QUERY_THRESHOLD_MS = 100  # Queries over 100ms are considered slow
VERY_SLOW_QUERY_THRESHOLD_MS = 1000  # Queries over 1s are critical

# Max slow queries to store in memory
MAX_SLOW_QUERIES = 100

# Connection pool warning thresholds
POOL_UTILIZATION_WARNING = 0.7  # Warn at 70% utilization
POOL_UTILIZATION_CRITICAL = 0.9  # Critical at 90%

# Index advisor settings
MIN_ROWS_FOR_INDEX_RECOMMENDATION = 1000
MIN_SELECTIVITY_FOR_INDEX = 0.1  # Column should filter at least 10%


# =============================================================================
# Data Classes
# =============================================================================

class QueryType(str, Enum):
    """Query type classification."""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    OTHER = "other"


@dataclass
class SlowQueryEvent:
    """Slow query event for profiling."""
    query: str
    duration_ms: float
    query_type: QueryType
    timestamp: datetime
    parameters: Optional[Dict[str, Any]] = None
    explain_plan: Optional[str] = None
    table_name: Optional[str] = None
    caller_info: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query[:500] + "..." if len(self.query) > 500 else self.query,
            "duration_ms": round(self.duration_ms, 2),
            "query_type": self.query_type.value,
            "timestamp": self.timestamp.isoformat(),
            "table_name": self.table_name,
        }


@dataclass
class IndexRecommendation:
    """Index recommendation from advisor."""
    table_name: str
    column_names: List[str]
    index_type: str  # btree, hash, gin, gist
    reason: str
    estimated_improvement: float  # 0-1 scale
    priority: str  # high, medium, low
    create_statement: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table": self.table_name,
            "columns": self.column_names,
            "type": self.index_type,
            "reason": self.reason,
            "estimated_improvement": f"{self.estimated_improvement:.0%}",
            "priority": self.priority,
            "sql": self.create_statement,
        }


@dataclass
class PoolStats:
    """Connection pool statistics."""
    pool_size: int
    checked_out: int
    overflow: int
    max_overflow: int
    utilization: float
    status: str  # healthy, warning, critical
    avg_checkout_time_ms: float = 0.0
    total_connections_created: int = 0
    total_connections_recycled: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pool_size": self.pool_size,
            "checked_out": self.checked_out,
            "overflow": self.overflow,
            "max_overflow": self.max_overflow,
            "utilization": f"{self.utilization:.1%}",
            "status": self.status,
            "avg_checkout_time_ms": round(self.avg_checkout_time_ms, 2),
        }


@dataclass
class QueryStats:
    """Aggregated query statistics."""
    total_queries: int = 0
    total_time_ms: float = 0.0
    slow_queries: int = 0
    very_slow_queries: int = 0
    queries_by_type: Dict[str, int] = field(default_factory=dict)
    slowest_queries: List[SlowQueryEvent] = field(default_factory=list)

    @property
    def avg_time_ms(self) -> float:
        if self.total_queries == 0:
            return 0.0
        return self.total_time_ms / self.total_queries

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_queries": self.total_queries,
            "total_time_ms": round(self.total_time_ms, 2),
            "avg_time_ms": round(self.avg_time_ms, 2),
            "slow_queries": self.slow_queries,
            "very_slow_queries": self.very_slow_queries,
            "queries_by_type": self.queries_by_type,
            "slowest_queries": [q.to_dict() for q in self.slowest_queries[:10]],
        }


# =============================================================================
# Query Profiler
# =============================================================================

class QueryProfiler:
    """
    Profile and detect slow queries.

    Usage:
        profiler = QueryProfiler()

        # Profile a block
        async with profiler.profile():
            result = await session.execute(query)

        # Get slow queries
        slow = profiler.get_slow_queries()
    """

    def __init__(
        self,
        slow_threshold_ms: float = SLOW_QUERY_THRESHOLD_MS,
        very_slow_threshold_ms: float = VERY_SLOW_QUERY_THRESHOLD_MS,
    ):
        self.slow_threshold_ms = slow_threshold_ms
        self.very_slow_threshold_ms = very_slow_threshold_ms
        self._stats = QueryStats()
        self._slow_queries: List[SlowQueryEvent] = []
        self._current_query: Optional[str] = None
        self._query_start: Optional[float] = None

    @asynccontextmanager
    async def profile(self, query: Optional[str] = None):
        """Profile a query execution."""
        start = time.perf_counter()
        self._current_query = query
        self._query_start = start

        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self._record_query(query or "unknown", duration_ms)

    def _record_query(self, query: str, duration_ms: float) -> None:
        """Record query execution metrics."""
        self._stats.total_queries += 1
        self._stats.total_time_ms += duration_ms

        # Classify query type
        query_type = self._classify_query(query)
        type_key = query_type.value
        self._stats.queries_by_type[type_key] = self._stats.queries_by_type.get(type_key, 0) + 1

        # Check for slow query
        if duration_ms >= self.slow_threshold_ms:
            self._stats.slow_queries += 1
            event = SlowQueryEvent(
                query=query,
                duration_ms=duration_ms,
                query_type=query_type,
                timestamp=datetime.now(),
                table_name=self._extract_table_name(query),
            )
            self._slow_queries.append(event)

            # Keep only MAX_SLOW_QUERIES
            if len(self._slow_queries) > MAX_SLOW_QUERIES:
                self._slow_queries = sorted(
                    self._slow_queries,
                    key=lambda x: x.duration_ms,
                    reverse=True
                )[:MAX_SLOW_QUERIES]

            # Update slowest list
            self._stats.slowest_queries = sorted(
                self._slow_queries,
                key=lambda x: x.duration_ms,
                reverse=True
            )[:10]

            if duration_ms >= self.very_slow_threshold_ms:
                self._stats.very_slow_queries += 1
                logger.warning(
                    f"[QueryProfiler] VERY SLOW QUERY ({duration_ms:.0f}ms): "
                    f"{query[:200]}..."
                )
            else:
                logger.debug(
                    f"[QueryProfiler] Slow query ({duration_ms:.0f}ms): "
                    f"{query[:100]}..."
                )

    def _classify_query(self, query: str) -> QueryType:
        """Classify query type from SQL."""
        query_upper = query.strip().upper()
        if query_upper.startswith("SELECT"):
            return QueryType.SELECT
        elif query_upper.startswith("INSERT"):
            return QueryType.INSERT
        elif query_upper.startswith("UPDATE"):
            return QueryType.UPDATE
        elif query_upper.startswith("DELETE"):
            return QueryType.DELETE
        else:
            return QueryType.OTHER

    def _extract_table_name(self, query: str) -> Optional[str]:
        """Extract main table name from query."""
        import re
        # Match FROM table_name or INTO table_name
        patterns = [
            r"\bFROM\s+([^\s,()]+)",
            r"\bINTO\s+([^\s(]+)",
            r"\bUPDATE\s+([^\s]+)",
            r"\bDELETE\s+FROM\s+([^\s]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip('"')
        return None

    def get_slow_queries(self, limit: int = 20) -> List[SlowQueryEvent]:
        """Get slowest queries."""
        return sorted(
            self._slow_queries,
            key=lambda x: x.duration_ms,
            reverse=True
        )[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get query statistics."""
        return self._stats.to_dict()

    def reset_stats(self) -> None:
        """Reset all statistics."""
        self._stats = QueryStats()
        self._slow_queries = []


# =============================================================================
# Index Advisor
# =============================================================================

class IndexAdvisor:
    """
    Analyze tables and recommend indexes.

    Usage:
        advisor = IndexAdvisor(engine)
        recommendations = await advisor.analyze_table("users")
    """

    def __init__(self, engine):
        self.engine = engine

    async def analyze_table(
        self,
        table_name: str,
        session: Optional["AsyncSession"] = None,
    ) -> List[IndexRecommendation]:
        """
        Analyze a table and recommend indexes.

        Looks at:
        - Missing indexes on foreign keys
        - Columns used in WHERE clauses
        - High-cardinality columns
        """
        from app.database import get_db_context

        recommendations = []

        try:
            if session:
                ctx = session
            else:
                ctx = get_db_context()

            async with ctx if not session else asynccontextmanager(lambda: (yield session))():
                db = session if session else ctx

                # Get existing indexes
                existing_indexes = await self._get_existing_indexes(db, table_name)

                # Get table statistics
                stats = await self._get_table_stats(db, table_name)

                if not stats:
                    return []

                # Check foreign keys without indexes
                fk_recommendations = await self._check_foreign_keys(db, table_name, existing_indexes)
                recommendations.extend(fk_recommendations)

                # Check columns used in slow queries
                # (Would need query log analysis - simplified here)

                # Check high-cardinality columns without indexes
                column_recommendations = await self._analyze_columns(
                    db, table_name, existing_indexes, stats
                )
                recommendations.extend(column_recommendations)

        except Exception as e:
            logger.warning(f"[IndexAdvisor] Analysis failed for {table_name}: {e}")

        return recommendations

    async def _get_existing_indexes(
        self,
        session: "AsyncSession",
        table_name: str,
    ) -> List[Dict[str, Any]]:
        """Get existing indexes on table."""
        query = text("""
            SELECT
                i.relname as index_name,
                a.attname as column_name,
                am.amname as index_type
            FROM pg_class t
            JOIN pg_index ix ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
            JOIN pg_am am ON i.relam = am.oid
            WHERE t.relname = :table_name
            ORDER BY i.relname, a.attnum
        """)
        result = await session.execute(query, {"table_name": table_name})
        return [dict(row._mapping) for row in result]

    async def _get_table_stats(
        self,
        session: "AsyncSession",
        table_name: str,
    ) -> Optional[Dict[str, Any]]:
        """Get table statistics."""
        query = text("""
            SELECT
                reltuples::bigint as row_count,
                pg_relation_size(:table_name) as table_size,
                pg_indexes_size(:table_name) as index_size
            FROM pg_class
            WHERE relname = :table_name
        """)
        result = await session.execute(query, {"table_name": table_name})
        row = result.first()
        if row:
            return dict(row._mapping)
        return None

    async def _check_foreign_keys(
        self,
        session: "AsyncSession",
        table_name: str,
        existing_indexes: List[Dict[str, Any]],
    ) -> List[IndexRecommendation]:
        """Check for foreign keys without indexes."""
        recommendations = []

        query = text("""
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = :table_name
        """)
        result = await session.execute(query, {"table_name": table_name})

        indexed_columns = {idx["column_name"] for idx in existing_indexes}

        for row in result:
            mapping = row._mapping
            column_name = mapping["column_name"]
            if column_name not in indexed_columns:
                recommendations.append(IndexRecommendation(
                    table_name=table_name,
                    column_names=[column_name],
                    index_type="btree",
                    reason=f"Foreign key to {mapping['foreign_table']} without index",
                    estimated_improvement=0.5,
                    priority="high",
                    create_statement=f"CREATE INDEX ix_{table_name}_{column_name} ON {table_name}({column_name})",
                ))

        return recommendations

    async def _analyze_columns(
        self,
        session: "AsyncSession",
        table_name: str,
        existing_indexes: List[Dict[str, Any]],
        stats: Dict[str, Any],
    ) -> List[IndexRecommendation]:
        """Analyze columns for potential indexes."""
        recommendations = []

        # Skip small tables
        if stats.get("row_count", 0) < MIN_ROWS_FOR_INDEX_RECOMMENDATION:
            return []

        # Get column statistics
        query = text("""
            SELECT
                attname as column_name,
                n_distinct,
                correlation
            FROM pg_stats
            WHERE tablename = :table_name
            AND n_distinct > 0
            ORDER BY n_distinct DESC
        """)
        result = await session.execute(query, {"table_name": table_name})

        indexed_columns = {idx["column_name"] for idx in existing_indexes}

        for row in result:
            mapping = row._mapping
            column_name = mapping["column_name"]
            n_distinct = mapping["n_distinct"]
            correlation = mapping.get("correlation", 0)

            if column_name in indexed_columns:
                continue

            # High cardinality columns are good index candidates
            if n_distinct < -0.5 or n_distinct > 100:  # Many distinct values
                # Check if it's a common filtering column
                if column_name.endswith("_id") or column_name.endswith("_at") or column_name == "status":
                    recommendations.append(IndexRecommendation(
                        table_name=table_name,
                        column_names=[column_name],
                        index_type="btree",
                        reason=f"High cardinality column ({n_distinct:.0f} distinct), commonly filtered",
                        estimated_improvement=0.3,
                        priority="medium",
                        create_statement=f"CREATE INDEX ix_{table_name}_{column_name} ON {table_name}({column_name})",
                    ))

        return recommendations

    async def get_unused_indexes(
        self,
        session: "AsyncSession",
    ) -> List[Dict[str, Any]]:
        """Get indexes that haven't been used."""
        query = text("""
            SELECT
                schemaname,
                relname as table_name,
                indexrelname as index_name,
                idx_scan as index_scans,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size
            FROM pg_stat_user_indexes
            WHERE idx_scan = 0
            AND indexrelname NOT LIKE 'pg_%'
            ORDER BY pg_relation_size(indexrelid) DESC
            LIMIT 20
        """)
        result = await session.execute(query)
        return [dict(row._mapping) for row in result]


# =============================================================================
# Connection Pool Monitor
# =============================================================================

class ConnectionPoolMonitor:
    """
    Monitor connection pool health.

    Usage:
        monitor = ConnectionPoolMonitor(engine)
        stats = monitor.get_stats()
    """

    def __init__(self, engine):
        self.engine = engine
        self._checkout_times: List[float] = []
        self._max_checkout_samples = 1000

    def get_stats(self) -> PoolStats:
        """Get current pool statistics."""
        pool = self.engine.pool

        # Get pool metrics
        pool_size = pool.size()
        checked_out = pool.checkedout()
        overflow = pool.overflow()
        max_overflow = pool._max_overflow

        # Calculate utilization
        total_capacity = pool_size + max_overflow
        utilization = checked_out / total_capacity if total_capacity > 0 else 0

        # Determine status
        if utilization >= POOL_UTILIZATION_CRITICAL:
            status = "critical"
        elif utilization >= POOL_UTILIZATION_WARNING:
            status = "warning"
        else:
            status = "healthy"

        # Calculate average checkout time
        avg_checkout_time = (
            sum(self._checkout_times) / len(self._checkout_times)
            if self._checkout_times else 0.0
        )

        return PoolStats(
            pool_size=pool_size,
            checked_out=checked_out,
            overflow=overflow,
            max_overflow=max_overflow,
            utilization=utilization,
            status=status,
            avg_checkout_time_ms=avg_checkout_time * 1000,
        )

    def record_checkout_time(self, duration: float) -> None:
        """Record a connection checkout time."""
        self._checkout_times.append(duration)
        if len(self._checkout_times) > self._max_checkout_samples:
            self._checkout_times = self._checkout_times[-self._max_checkout_samples:]

    def check_health(self) -> Dict[str, Any]:
        """Check pool health and return diagnostics."""
        stats = self.get_stats()

        diagnostics = {
            "status": stats.status,
            "stats": stats.to_dict(),
            "recommendations": [],
        }

        if stats.status == "critical":
            diagnostics["recommendations"].append(
                "Connection pool near capacity. Consider increasing pool_size or max_overflow."
            )
        elif stats.status == "warning":
            diagnostics["recommendations"].append(
                "Connection pool utilization high. Monitor for potential bottlenecks."
            )

        if stats.avg_checkout_time_ms > 100:
            diagnostics["recommendations"].append(
                f"High connection checkout time ({stats.avg_checkout_time_ms:.0f}ms). "
                "Check for connection leaks or slow queries."
            )

        return diagnostics


# =============================================================================
# Unified Database Optimizer
# =============================================================================

class DatabaseOptimizer:
    """
    Unified database optimization combining all techniques.

    Usage:
        optimizer = get_db_optimizer()

        # Get query stats
        stats = optimizer.get_query_stats()

        # Get index recommendations
        recommendations = await optimizer.get_index_recommendations("users")

        # Check pool health
        health = optimizer.check_pool_health()
    """

    def __init__(self, engine=None):
        # Lazy engine import
        if engine is None:
            from app.database import engine as db_engine
            engine = db_engine

        self.engine = engine
        self._profiler = QueryProfiler()
        self._index_advisor = IndexAdvisor(engine)
        self._pool_monitor = ConnectionPoolMonitor(engine)

    @property
    def profiler(self) -> QueryProfiler:
        return self._profiler

    @property
    def index_advisor(self) -> IndexAdvisor:
        return self._index_advisor

    @property
    def pool_monitor(self) -> ConnectionPoolMonitor:
        return self._pool_monitor

    @asynccontextmanager
    async def profile_query(self, query: Optional[str] = None):
        """Profile a query execution."""
        async with self._profiler.profile(query):
            yield

    def get_query_stats(self) -> Dict[str, Any]:
        """Get query execution statistics."""
        return self._profiler.get_stats()

    def get_slow_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get slowest queries."""
        return [q.to_dict() for q in self._profiler.get_slow_queries(limit)]

    async def get_index_recommendations(
        self,
        table_name: str,
        session: Optional["AsyncSession"] = None,
    ) -> List[Dict[str, Any]]:
        """Get index recommendations for a table."""
        recommendations = await self._index_advisor.analyze_table(table_name, session)
        return [r.to_dict() for r in recommendations]

    async def get_unused_indexes(
        self,
        session: "AsyncSession",
    ) -> List[Dict[str, Any]]:
        """Get unused indexes that could be dropped."""
        return await self._index_advisor.get_unused_indexes(session)

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return self._pool_monitor.get_stats().to_dict()

    def check_pool_health(self) -> Dict[str, Any]:
        """Check connection pool health."""
        return self._pool_monitor.check_health()

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get all database statistics."""
        return {
            "query_stats": self.get_query_stats(),
            "slow_queries": self.get_slow_queries(10),
            "pool_stats": self.get_pool_stats(),
            "pool_health": self.check_pool_health(),
        }


# =============================================================================
# Singleton
# =============================================================================

_db_optimizer: Optional[DatabaseOptimizer] = None


def get_db_optimizer() -> DatabaseOptimizer:
    """Get the singleton database optimizer."""
    global _db_optimizer
    if _db_optimizer is None:
        _db_optimizer = DatabaseOptimizer()
    return _db_optimizer


def reset_db_optimizer() -> None:
    """Reset the database optimizer (for testing)."""
    global _db_optimizer
    _db_optimizer = None
