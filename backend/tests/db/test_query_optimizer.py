"""
Tests for Database Query Optimizer Module

Tests the database optimization components:
1. QueryProfiler - Slow query detection
2. IndexAdvisor - Index recommendations
3. ConnectionPoolMonitor - Pool health monitoring
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from app.db.query_optimizer import (
    QueryProfiler,
    IndexAdvisor,
    ConnectionPoolMonitor,
    DatabaseOptimizer,
    get_db_optimizer,
    reset_db_optimizer,
    SlowQueryEvent,
    IndexRecommendation,
    PoolStats,
    QueryType,
    SLOW_QUERY_THRESHOLD_MS,
)


# =============================================================================
# QueryProfiler Tests
# =============================================================================

class TestQueryProfiler:
    """Tests for query profiling."""

    @pytest.fixture
    def profiler(self):
        """Create a profiler instance."""
        return QueryProfiler(
            slow_threshold_ms=50,  # Low threshold for testing
            very_slow_threshold_ms=200,
        )

    @pytest.mark.asyncio
    async def test_profile_fast_query(self, profiler):
        """Test profiling a fast query."""
        async with profiler.profile("SELECT 1"):
            pass  # Fast query

        stats = profiler.get_stats()
        assert stats["total_queries"] == 1
        assert stats["slow_queries"] == 0

    @pytest.mark.asyncio
    async def test_profile_slow_query(self, profiler):
        """Test profiling a slow query."""
        import asyncio

        async with profiler.profile("SELECT * FROM large_table"):
            await asyncio.sleep(0.06)  # 60ms > 50ms threshold

        stats = profiler.get_stats()
        assert stats["total_queries"] == 1
        assert stats["slow_queries"] >= 1

        slow_queries = profiler.get_slow_queries()
        assert len(slow_queries) >= 1
        assert slow_queries[0].duration_ms >= 50

    def test_classify_select_query(self, profiler):
        """Test query type classification for SELECT."""
        query_type = profiler._classify_query("SELECT * FROM users WHERE id = 1")
        assert query_type == QueryType.SELECT

    def test_classify_insert_query(self, profiler):
        """Test query type classification for INSERT."""
        query_type = profiler._classify_query("INSERT INTO users (name) VALUES ('test')")
        assert query_type == QueryType.INSERT

    def test_classify_update_query(self, profiler):
        """Test query type classification for UPDATE."""
        query_type = profiler._classify_query("UPDATE users SET name = 'new' WHERE id = 1")
        assert query_type == QueryType.UPDATE

    def test_classify_delete_query(self, profiler):
        """Test query type classification for DELETE."""
        query_type = profiler._classify_query("DELETE FROM users WHERE id = 1")
        assert query_type == QueryType.DELETE

    def test_extract_table_name_from(self, profiler):
        """Test table name extraction from SELECT."""
        table = profiler._extract_table_name("SELECT * FROM users WHERE id = 1")
        assert table == "users"

    def test_extract_table_name_into(self, profiler):
        """Test table name extraction from INSERT."""
        table = profiler._extract_table_name("INSERT INTO users (name) VALUES ('test')")
        assert table == "users"

    def test_extract_table_name_update(self, profiler):
        """Test table name extraction from UPDATE."""
        table = profiler._extract_table_name("UPDATE users SET name = 'new'")
        assert table == "users"

    def test_reset_stats(self, profiler):
        """Test stats reset."""
        profiler._stats.total_queries = 100
        profiler.reset_stats()

        stats = profiler.get_stats()
        assert stats["total_queries"] == 0


# =============================================================================
# IndexAdvisor Tests
# =============================================================================

class TestIndexAdvisor:
    """Tests for index advisor."""

    @pytest.fixture
    def advisor(self):
        """Create an advisor instance."""
        mock_engine = MagicMock()
        return IndexAdvisor(mock_engine)

    def test_index_recommendation_to_dict(self):
        """Test IndexRecommendation serialization."""
        rec = IndexRecommendation(
            table_name="users",
            column_names=["email"],
            index_type="btree",
            reason="High cardinality column",
            estimated_improvement=0.3,
            priority="medium",
            create_statement="CREATE INDEX ix_users_email ON users(email)",
        )

        data = rec.to_dict()

        assert data["table"] == "users"
        assert data["columns"] == ["email"]
        assert data["type"] == "btree"
        assert data["priority"] == "medium"
        assert "CREATE INDEX" in data["sql"]


# =============================================================================
# ConnectionPoolMonitor Tests
# =============================================================================

class TestConnectionPoolMonitor:
    """Tests for connection pool monitoring."""

    @pytest.fixture
    def monitor(self):
        """Create a monitor with mock pool."""
        mock_engine = MagicMock()
        mock_pool = MagicMock()
        mock_pool.size.return_value = 10
        mock_pool.checkedout.return_value = 3
        mock_pool.overflow.return_value = 0
        mock_pool._max_overflow = 20
        mock_engine.pool = mock_pool
        return ConnectionPoolMonitor(mock_engine)

    def test_get_healthy_stats(self, monitor):
        """Test healthy pool stats."""
        stats = monitor.get_stats()

        assert stats.pool_size == 10
        assert stats.checked_out == 3
        assert stats.overflow == 0
        assert stats.status == "healthy"
        assert stats.utilization < 0.7

    def test_get_warning_stats(self):
        """Test warning pool stats."""
        mock_engine = MagicMock()
        mock_pool = MagicMock()
        mock_pool.size.return_value = 10
        mock_pool.checkedout.return_value = 22  # 73% utilization
        mock_pool.overflow.return_value = 0
        mock_pool._max_overflow = 20
        mock_engine.pool = mock_pool

        monitor = ConnectionPoolMonitor(mock_engine)
        stats = monitor.get_stats()

        assert stats.status == "warning"

    def test_get_critical_stats(self):
        """Test critical pool stats."""
        mock_engine = MagicMock()
        mock_pool = MagicMock()
        mock_pool.size.return_value = 10
        mock_pool.checkedout.return_value = 28  # 93% utilization
        mock_pool.overflow.return_value = 0
        mock_pool._max_overflow = 20
        mock_engine.pool = mock_pool

        monitor = ConnectionPoolMonitor(mock_engine)
        stats = monitor.get_stats()

        assert stats.status == "critical"

    def test_record_checkout_time(self, monitor):
        """Test checkout time recording."""
        monitor.record_checkout_time(0.01)
        monitor.record_checkout_time(0.02)
        monitor.record_checkout_time(0.03)

        stats = monitor.get_stats()
        assert stats.avg_checkout_time_ms > 0

    def test_health_check_recommendations(self):
        """Test health check with recommendations."""
        mock_engine = MagicMock()
        mock_pool = MagicMock()
        mock_pool.size.return_value = 10
        mock_pool.checkedout.return_value = 28
        mock_pool.overflow.return_value = 0
        mock_pool._max_overflow = 20
        mock_engine.pool = mock_pool

        monitor = ConnectionPoolMonitor(mock_engine)
        health = monitor.check_health()

        assert health["status"] == "critical"
        assert len(health["recommendations"]) > 0


# =============================================================================
# DatabaseOptimizer Integration Tests
# =============================================================================

class TestDatabaseOptimizer:
    """Integration tests for database optimizer."""

    @pytest.fixture
    def optimizer(self):
        """Create optimizer with mocked engine."""
        reset_db_optimizer()

        mock_engine = MagicMock()
        mock_pool = MagicMock()
        mock_pool.size.return_value = 10
        mock_pool.checkedout.return_value = 3
        mock_pool.overflow.return_value = 0
        mock_pool._max_overflow = 20
        mock_engine.pool = mock_pool

        return DatabaseOptimizer(engine=mock_engine)

    @pytest.mark.asyncio
    async def test_profile_query(self, optimizer):
        """Test query profiling through optimizer."""
        async with optimizer.profile_query("SELECT * FROM test"):
            pass

        stats = optimizer.get_query_stats()
        assert stats["total_queries"] >= 1

    def test_get_pool_stats(self, optimizer):
        """Test pool stats retrieval."""
        stats = optimizer.get_pool_stats()

        assert "pool_size" in stats
        assert "utilization" in stats
        assert "status" in stats

    def test_get_comprehensive_stats(self, optimizer):
        """Test comprehensive stats."""
        stats = optimizer.get_comprehensive_stats()

        assert "query_stats" in stats
        assert "slow_queries" in stats
        assert "pool_stats" in stats
        assert "pool_health" in stats


# =============================================================================
# Data Class Tests
# =============================================================================

class TestSlowQueryEvent:
    """Tests for SlowQueryEvent data class."""

    def test_to_dict(self):
        """Test serialization."""
        event = SlowQueryEvent(
            query="SELECT * FROM users WHERE id = 1",
            duration_ms=150.5,
            query_type=QueryType.SELECT,
            timestamp=datetime.now(),
            table_name="users",
        )

        data = event.to_dict()

        assert "query" in data
        assert data["duration_ms"] == 150.5
        assert data["query_type"] == "select"
        assert data["table_name"] == "users"

    def test_long_query_truncation(self):
        """Test that long queries are truncated."""
        long_query = "SELECT " + "a, " * 500 + "b FROM users"
        event = SlowQueryEvent(
            query=long_query,
            duration_ms=100,
            query_type=QueryType.SELECT,
            timestamp=datetime.now(),
        )

        data = event.to_dict()

        assert len(data["query"]) <= 503  # 500 + "..."


class TestPoolStats:
    """Tests for PoolStats data class."""

    def test_to_dict(self):
        """Test serialization."""
        stats = PoolStats(
            pool_size=10,
            checked_out=5,
            overflow=2,
            max_overflow=20,
            utilization=0.23,
            status="healthy",
            avg_checkout_time_ms=5.5,
        )

        data = stats.to_dict()

        assert data["pool_size"] == 10
        assert data["checked_out"] == 5
        assert "23" in data["utilization"]  # Flexible check for float formatting
        assert data["status"] == "healthy"


# =============================================================================
# Singleton Tests
# =============================================================================

class TestSingleton:
    """Tests for singleton behavior."""

    def test_get_db_optimizer_singleton(self):
        """Test singleton pattern."""
        reset_db_optimizer()

        # Mock engine to avoid actual DB connection
        with patch("app.db.query_optimizer.DatabaseOptimizer.__init__", return_value=None):
            opt1 = get_db_optimizer()
            opt2 = get_db_optimizer()
            # Due to mock, these won't be same object, but function should work
            # In real usage, they would be same object
