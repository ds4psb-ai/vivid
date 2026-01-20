"""
GraphQL DataLoaders - H2.1 Core Feature Hardening

Production-grade DataLoader implementation for N+1 query prevention.

Features:
1. Type-safe batch loading with proper error handling
2. Per-request caching (context-scoped)
3. Mutation cache invalidation support
4. Real database queries (not mock data)

Usage:
    ctx = GraphQLContext(...)
    loader = ctx.get_ip_catalog_loader()
    ip = await loader.load("my-ip-slug")
"""

from __future__ import annotations

import logging
from typing import TypeVar, Generic, Sequence, Optional, Any, Callable, Dict, List
from uuid import UUID
from collections.abc import Awaitable

from strawberry.dataloader import DataLoader
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

T = TypeVar("T")
KeyT = TypeVar("KeyT")


# =============================================================================
# Base DataLoader Infrastructure
# =============================================================================

class TypedDataLoader(Generic[KeyT, T]):
    """
    Type-safe DataLoader wrapper with caching and invalidation support.

    Features:
    - Per-request caching (each GraphQL request gets fresh loaders)
    - Cache invalidation after mutations
    - Error handling with partial results
    - Batch size optimization
    """

    def __init__(
        self,
        load_fn: Callable[[List[KeyT]], Awaitable[Sequence[T | None]]],
        max_batch_size: int = 100,
    ):
        """
        Initialize DataLoader with batch load function.

        Args:
            load_fn: Async function that takes list of keys and returns values in order
            max_batch_size: Maximum batch size for queries (default: 100)
        """
        self._load_fn = load_fn
        self._max_batch_size = max_batch_size
        self._loader: DataLoader[KeyT, T | None] | None = None

    @property
    def loader(self) -> DataLoader[KeyT, T | None]:
        """Get or create the underlying Strawberry DataLoader."""
        if self._loader is None:
            self._loader = DataLoader(
                load_fn=self._batch_load,
                max_batch_size=self._max_batch_size,
            )
        return self._loader

    async def _batch_load(self, keys: List[KeyT]) -> Sequence[T | None]:
        """Internal batch load with error handling."""
        try:
            return await self._load_fn(keys)
        except Exception as e:
            logger.exception(f"DataLoader batch load failed: {e}")
            # Return None for all keys on error
            return [None] * len(keys)

    async def load(self, key: KeyT) -> T | None:
        """Load a single value by key."""
        return await self.loader.load(key)

    async def load_many(self, keys: List[KeyT]) -> List[T | None]:
        """Load multiple values by keys."""
        return list(await self.loader.load_many(keys))

    def prime(self, key: KeyT, value: T) -> None:
        """Prime the cache with a known value."""
        self.loader.prime(key, value)

    def clear(self, key: KeyT) -> None:
        """Clear a specific key from cache (for mutation invalidation)."""
        self.loader.clear(key)

    def clear_all(self) -> None:
        """Clear entire cache (for bulk mutations)."""
        self.loader.clear_all()


# =============================================================================
# Domain-Specific DataLoaders
# =============================================================================

class IPCatalogDataLoader(TypedDataLoader[str, Any]):
    """
    DataLoader for IPCatalog entities.

    Batches IP lookups by slug to prevent N+1 queries when resolving
    IP relationships in GraphQL queries.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        super().__init__(load_fn=self._batch_load_ips)

    async def _batch_load_ips(self, slugs: List[str]) -> Sequence[Any | None]:
        """Batch load IPCatalogs by slug."""
        from app.models_ip import IPCatalog

        result = await self.db.execute(
            select(IPCatalog)
            .where(IPCatalog.slug.in_(slugs))
            .where(IPCatalog.is_active == True)
        )
        items = {item.slug: item for item in result.scalars().all()}

        # Return in same order as input slugs
        return [items.get(slug) for slug in slugs]


class UserDataLoader(TypedDataLoader[str, Any]):
    """
    DataLoader for User entities.

    Batches user lookups by ID to prevent N+1 queries when resolving
    user relationships (creator, owner, etc.) in GraphQL queries.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        super().__init__(load_fn=self._batch_load_users)

    async def _batch_load_users(self, user_ids: List[str]) -> Sequence[Any | None]:
        """Batch load Users by ID."""
        from app.models import UserAccount

        result = await self.db.execute(
            select(UserAccount).where(UserAccount.id.in_(user_ids))
        )
        items = {item.id: item for item in result.scalars().all()}

        return [items.get(uid) for uid in user_ids]


class UserCreditsDataLoader(TypedDataLoader[str, Any]):
    """
    DataLoader for UserCredits entities.

    Batches credit balance lookups by user_id to prevent N+1 queries
    when resolving credit information in user profiles.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        super().__init__(load_fn=self._batch_load_credits)

    async def _batch_load_credits(self, user_ids: List[str]) -> Sequence[Any | None]:
        """Batch load UserCredits by user_id."""
        from app.models import UserCredits

        result = await self.db.execute(
            select(UserCredits).where(UserCredits.user_id.in_(user_ids))
        )
        items = {item.user_id: item for item in result.scalars().all()}

        return [items.get(uid) for uid in user_ids]


class ToolManifestDataLoader(TypedDataLoader[str, Any]):
    """
    DataLoader for ToolManifest entities.

    Batches tool lookups by ID (UUID as string) to prevent N+1 queries
    when resolving tool information in runs and analytics.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        super().__init__(load_fn=self._batch_load_tools)

    async def _batch_load_tools(self, tool_ids: List[str]) -> Sequence[Any | None]:
        """Batch load ToolManifests by ID."""
        from app.models_telemetry import ToolManifest

        # Convert string IDs to UUIDs
        uuid_ids = []
        for tid in tool_ids:
            try:
                uuid_ids.append(UUID(tid))
            except ValueError:
                uuid_ids.append(None)  # type: ignore

        valid_uuids = [u for u in uuid_ids if u is not None]

        if not valid_uuids:
            return [None] * len(tool_ids)

        result = await self.db.execute(
            select(ToolManifest).where(ToolManifest.id.in_(valid_uuids))
        )
        items = {str(item.id): item for item in result.scalars().all()}

        return [items.get(tid) for tid in tool_ids]


class ToolByKeyDataLoader(TypedDataLoader[str, Any]):
    """
    DataLoader for ToolManifest entities by tool_key.

    Batches tool lookups by key (e.g., 'prompt-alchemy') to prevent
    N+1 queries when resolving tools by their key identifier.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        super().__init__(load_fn=self._batch_load_tools_by_key)

    async def _batch_load_tools_by_key(self, tool_keys: List[str]) -> Sequence[Any | None]:
        """Batch load ToolManifests by tool_key."""
        from app.models_telemetry import ToolManifest

        result = await self.db.execute(
            select(ToolManifest)
            .where(ToolManifest.tool_key.in_(tool_keys))
            .where(ToolManifest.is_active == True)
        )
        items = {item.tool_key: item for item in result.scalars().all()}

        return [items.get(key) for key in tool_keys]


class ToolRunsCountDataLoader(TypedDataLoader[str, int]):
    """
    DataLoader for tool run counts by user_id.

    Batches count queries to prevent N+1 when showing run counts
    in user profiles or analytics dashboards.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        super().__init__(load_fn=self._batch_load_run_counts)

    async def _batch_load_run_counts(self, user_ids: List[str]) -> Sequence[int | None]:
        """Batch load run counts by user_id."""
        from app.models_sandbox import SandboxExecution

        result = await self.db.execute(
            select(
                SandboxExecution.user_id,
                func.count(SandboxExecution.id).label("run_count")
            )
            .where(SandboxExecution.user_id.in_(user_ids))
            .group_by(SandboxExecution.user_id)
        )

        counts = {row.user_id: row.run_count for row in result.all()}

        return [counts.get(uid, 0) for uid in user_ids]


class ToolAnalyticsDataLoader(TypedDataLoader[str, Dict[str, Any]]):
    """
    DataLoader for aggregated tool analytics.

    Batches analytics queries to prevent N+1 when displaying
    tool statistics in lists or dashboards.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        super().__init__(load_fn=self._batch_load_analytics)

    async def _batch_load_analytics(
        self, tool_ids: List[str]
    ) -> Sequence[Dict[str, Any] | None]:
        """Batch load analytics by tool_id."""
        from app.models_sandbox import SandboxExecution, ExecutionStatus
        from datetime import datetime, timedelta

        # Convert string IDs to UUIDs
        uuid_ids = []
        for tid in tool_ids:
            try:
                uuid_ids.append(UUID(tid))
            except ValueError:
                pass

        if not uuid_ids:
            return [None] * len(tool_ids)

        # Get aggregated stats for the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        result = await self.db.execute(
            select(
                SandboxExecution.tool_id,
                func.count(SandboxExecution.id).label("total_runs"),
                func.count(
                    SandboxExecution.id
                ).filter(
                    SandboxExecution.status == ExecutionStatus.SUCCESS.value
                ).label("successful_runs"),
                func.avg(SandboxExecution.execution_time_ms).label("avg_latency_ms"),
                func.sum(SandboxExecution.credits_charged).label("total_credits"),
                func.sum(SandboxExecution.credits_refunded).label("total_refunds"),
            )
            .where(SandboxExecution.tool_id.in_(uuid_ids))
            .where(SandboxExecution.queued_at >= thirty_days_ago)
            .group_by(SandboxExecution.tool_id)
        )

        analytics = {}
        for row in result.all():
            total = row.total_runs or 0
            success = row.successful_runs or 0
            analytics[str(row.tool_id)] = {
                "tool_id": str(row.tool_id),
                "total_runs": total,
                "successful_runs": success,
                "failed_runs": total - success,
                "success_rate": success / total if total > 0 else 0.0,
                "avg_latency_ms": float(row.avg_latency_ms or 0),
                "total_credits_earned": int(row.total_credits or 0),
                "total_credits_refunded": int(row.total_refunds or 0),
                "net_revenue": int((row.total_credits or 0) - (row.total_refunds or 0)),
                "period_start": thirty_days_ago,
                "period_end": datetime.utcnow(),
            }

        return [analytics.get(tid) for tid in tool_ids]


class CreditTransactionsDataLoader(TypedDataLoader[str, List[Any]]):
    """
    DataLoader for credit transactions by user_id.

    Batches transaction queries to prevent N+1 when showing
    transaction history in user profiles.
    """

    def __init__(self, db: AsyncSession, limit: int = 20):
        self.db = db
        self.limit = limit
        super().__init__(load_fn=self._batch_load_transactions)

    async def _batch_load_transactions(
        self, user_ids: List[str]
    ) -> Sequence[List[Any] | None]:
        """Batch load recent transactions by user_id."""
        from app.models import CreditLedger

        result = await self.db.execute(
            select(CreditLedger)
            .where(CreditLedger.user_id.in_(user_ids))
            .order_by(CreditLedger.created_at.desc())
            .limit(self.limit * len(user_ids))  # Approximate limit
        )

        # Group by user_id
        transactions_by_user: Dict[str, List[Any]] = {uid: [] for uid in user_ids}
        for tx in result.scalars().all():
            if tx.user_id in transactions_by_user:
                if len(transactions_by_user[tx.user_id]) < self.limit:
                    transactions_by_user[tx.user_id].append(tx)

        return [transactions_by_user.get(uid, []) for uid in user_ids]


# =============================================================================
# DataLoader Registry (Context Integration)
# =============================================================================

class DataLoaderRegistry:
    """
    Registry of all DataLoaders for a request context.

    Creates DataLoaders lazily and caches them for the request duration.
    Each GraphQL request should get a fresh registry to ensure proper
    per-request caching and isolation.
    """

    def __init__(self, db: AsyncSession):
        """Initialize registry with database session."""
        self.db = db
        self._loaders: Dict[str, Any] = {}

    def _get_or_create(self, name: str, factory: Callable[[], Any]) -> Any:
        """Get existing loader or create new one."""
        if name not in self._loaders:
            self._loaders[name] = factory()
        return self._loaders[name]

    @property
    def ip_catalog(self) -> IPCatalogDataLoader:
        """Get IPCatalog DataLoader."""
        return self._get_or_create("ip_catalog", lambda: IPCatalogDataLoader(self.db))

    @property
    def user(self) -> UserDataLoader:
        """Get User DataLoader."""
        return self._get_or_create("user", lambda: UserDataLoader(self.db))

    @property
    def user_credits(self) -> UserCreditsDataLoader:
        """Get UserCredits DataLoader."""
        return self._get_or_create("user_credits", lambda: UserCreditsDataLoader(self.db))

    @property
    def tool_manifest(self) -> ToolManifestDataLoader:
        """Get ToolManifest DataLoader."""
        return self._get_or_create("tool_manifest", lambda: ToolManifestDataLoader(self.db))

    @property
    def tool_by_key(self) -> ToolByKeyDataLoader:
        """Get Tool by key DataLoader."""
        return self._get_or_create("tool_by_key", lambda: ToolByKeyDataLoader(self.db))

    @property
    def tool_runs_count(self) -> ToolRunsCountDataLoader:
        """Get tool runs count DataLoader."""
        return self._get_or_create("tool_runs_count", lambda: ToolRunsCountDataLoader(self.db))

    @property
    def tool_analytics(self) -> ToolAnalyticsDataLoader:
        """Get tool analytics DataLoader."""
        return self._get_or_create("tool_analytics", lambda: ToolAnalyticsDataLoader(self.db))

    @property
    def credit_transactions(self) -> CreditTransactionsDataLoader:
        """Get credit transactions DataLoader."""
        return self._get_or_create(
            "credit_transactions",
            lambda: CreditTransactionsDataLoader(self.db)
        )

    def invalidate_all(self) -> None:
        """Invalidate all loader caches (after mutation)."""
        for loader in self._loaders.values():
            if hasattr(loader, "clear_all"):
                loader.clear_all()
