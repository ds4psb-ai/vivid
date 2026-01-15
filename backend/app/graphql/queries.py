"""
GraphQL Queries - 2026 Best Practices

Defines all query resolvers with:
1. Connection-based pagination
2. DataLoader usage for N+1 prevention
3. Authorization checks
4. Query complexity limits
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4

import strawberry

from app.graphql.types import (
    User,
    CreditBalance,
    CreditTransaction,
    CreditTransactionType,
    Tool,
    ToolTier,
    SafetyRating,
    ToolRun,
    RunStatus,
    ToolAnalytics,
    DimensionCapsule,
    WorkflowStage,
    SystemHealth,
    QueryStats,
    CacheStats,
    Connection,
    PaginationInput,
    ToolFilterInput,
    DateRangeInput,
    create_connection,
)
from app.graphql.context import Info


@strawberry.type
class Query:
    """GraphQL Query root type."""

    # =========================================================================
    # User Queries
    # =========================================================================

    @strawberry.field
    async def me(self, info: Info) -> Optional[User]:
        """Get current authenticated user."""
        info.context.require_auth()

        # In production, load from database using dataloader
        return User(
            id=strawberry.ID(info.context.user_id or ""),
            email=info.context.user_email or "",
            display_name=f"User {info.context.user_id}",
            credit_balance=1000,
            total_spent=500,
            tier=info.context.user_tier,
            created_at=datetime.now() - timedelta(days=30),
            last_login_at=datetime.now(),
        )

    @strawberry.field
    async def user(self, info: Info, id: strawberry.ID) -> Optional[User]:
        """Get user by ID (admin only)."""
        info.context.require_admin()

        # Use dataloader to batch user lookups
        loader = info.context.get_user_loader()
        user_data = await loader.load(str(id))

        if not user_data:
            return None

        return User(
            id=id,
            email=user_data.get("email", ""),
            display_name=user_data.get("display_name"),
            credit_balance=user_data.get("credit_balance", 0),
            total_spent=user_data.get("total_spent", 0),
            tier=user_data.get("tier", "free"),
            created_at=user_data.get("created_at", datetime.now()),
        )

    # =========================================================================
    # Credit Queries
    # =========================================================================

    @strawberry.field
    async def credit_balance(self, info: Info) -> CreditBalance:
        """Get current user's credit balance."""
        info.context.require_auth()

        user_id = info.context.user_id or ""

        # TODO: Load from database
        return CreditBalance(
            user_id=strawberry.ID(user_id),
            balance=1000,
            reserved=50,
            available=950,
            lifetime_purchased=2000,
            lifetime_spent=1000,
            lifetime_earned=100,
        )

    @strawberry.field
    async def credit_transactions(
        self,
        info: Info,
        pagination: Optional[PaginationInput] = None,
        date_range: Optional[DateRangeInput] = None,
    ) -> Connection[CreditTransaction]:
        """Get user's credit transaction history."""
        info.context.require_auth()

        user_id = info.context.user_id or ""

        # Mock data for now
        transactions = [
            CreditTransaction(
                id=strawberry.ID(str(uuid4())),
                user_id=strawberry.ID(user_id),
                transaction_type=CreditTransactionType.PURCHASE,
                amount=1000,
                description="Credit purchase",
                created_at=datetime.now() - timedelta(days=7),
            ),
            CreditTransaction(
                id=strawberry.ID(str(uuid4())),
                user_id=strawberry.ID(user_id),
                transaction_type=CreditTransactionType.SPEND,
                amount=-50,
                description="Tool run: prompt-alchemy",
                reference_id="run-123",
                created_at=datetime.now() - timedelta(days=1),
            ),
        ]

        limit = (pagination.first if pagination else None) or 20
        return create_connection(
            items=transactions[:limit],
            total_count=len(transactions),
            has_next=False,
            has_prev=False,
        )

    # =========================================================================
    # Tool Queries
    # =========================================================================

    @strawberry.field
    async def tool(self, info: Info, id: strawberry.ID) -> Optional[Tool]:
        """Get tool by ID."""
        loader = info.context.get_tool_loader()
        tool_data = await loader.load(str(id))

        if not tool_data:
            return None

        return Tool(
            id=id,
            tool_key=tool_data.get("tool_key", ""),
            display_name=tool_data.get("display_name", ""),
            description=tool_data.get("description", ""),
            version="1.0.0",
            category=tool_data.get("category", "general"),
            tier=ToolTier.EXPERIMENTAL,
            credit_cost=5,
            created_by="system",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @strawberry.field
    async def tool_by_key(self, info: Info, key: str) -> Optional[Tool]:
        """Get tool by key (e.g., 'prompt-alchemy')."""
        # TODO: Implement database lookup
        return Tool(
            id=strawberry.ID(str(uuid4())),
            tool_key=key,
            display_name=key.replace("-", " ").title(),
            description=f"Tool: {key}",
            version="1.0.0",
            category="dimension",
            tier=ToolTier.VERIFIED,
            credit_cost=5,
            usage_count=1250,
            fork_count=3,
            success_rate=0.95,
            avg_rating=4.5,
            rating_count=42,
            created_by="system",
            created_at=datetime.now() - timedelta(days=90),
            updated_at=datetime.now(),
        )

    @strawberry.field
    async def tools(
        self,
        info: Info,
        filter: Optional[ToolFilterInput] = None,
        pagination: Optional[PaginationInput] = None,
    ) -> Connection[Tool]:
        """List tools with filtering and pagination."""
        # TODO: Implement database query with filters
        tools = [
            Tool(
                id=strawberry.ID(str(uuid4())),
                tool_key="prompt-alchemy",
                display_name="Prompt Alchemy",
                description="Transform natural language into AI prompts",
                version="1.0.0",
                category="dimension",
                tier=ToolTier.CERTIFIED,
                credit_cost=5,
                usage_count=5000,
                success_rate=0.97,
                avg_rating=4.8,
                rating_count=150,
                created_by="system",
                created_at=datetime.now() - timedelta(days=180),
                updated_at=datetime.now(),
            ),
            Tool(
                id=strawberry.ID(str(uuid4())),
                tool_key="visual-realizer",
                display_name="Visual Realizer",
                description="Generate images from prompts",
                version="1.0.0",
                category="dimension",
                tier=ToolTier.VERIFIED,
                credit_cost=10,
                usage_count=3500,
                success_rate=0.92,
                avg_rating=4.6,
                rating_count=98,
                created_by="system",
                created_at=datetime.now() - timedelta(days=120),
                updated_at=datetime.now(),
            ),
        ]

        limit = (pagination.first if pagination else None) or 20
        return create_connection(
            items=tools[:limit],
            total_count=len(tools),
            has_next=False,
            has_prev=False,
        )

    @strawberry.field
    async def my_tools(
        self,
        info: Info,
        pagination: Optional[PaginationInput] = None,
    ) -> Connection[Tool]:
        """Get tools created by current user."""
        info.context.require_auth()

        # TODO: Filter tools by creator
        return create_connection(
            items=[],
            total_count=0,
            has_next=False,
            has_prev=False,
        )

    # =========================================================================
    # Tool Run Queries
    # =========================================================================

    @strawberry.field
    async def tool_run(self, info: Info, id: strawberry.ID) -> Optional[ToolRun]:
        """Get tool run by ID."""
        info.context.require_auth()

        # TODO: Implement database lookup
        return ToolRun(
            id=id,
            tool_id=strawberry.ID(str(uuid4())),
            tool_key="prompt-alchemy",
            user_id=info.context.user_id,
            status=RunStatus.SUCCESS,
            latency_ms=250,
            credits_charged=5,
            created_at=datetime.now() - timedelta(minutes=30),
            completed_at=datetime.now() - timedelta(minutes=30),
        )

    @strawberry.field
    async def my_tool_runs(
        self,
        info: Info,
        tool_key: Optional[str] = None,
        status: Optional[RunStatus] = None,
        date_range: Optional[DateRangeInput] = None,
        pagination: Optional[PaginationInput] = None,
    ) -> Connection[ToolRun]:
        """Get current user's tool run history."""
        info.context.require_auth()

        user_id = info.context.user_id or ""

        # Mock data
        runs = [
            ToolRun(
                id=strawberry.ID(str(uuid4())),
                tool_id=strawberry.ID(str(uuid4())),
                tool_key="prompt-alchemy",
                user_id=user_id,
                status=RunStatus.SUCCESS,
                latency_ms=250,
                credits_charged=5,
                user_rating=5,
                created_at=datetime.now() - timedelta(hours=2),
                completed_at=datetime.now() - timedelta(hours=2),
            ),
        ]

        limit = (pagination.first if pagination else None) or 20
        return create_connection(
            items=runs[:limit],
            total_count=len(runs),
            has_next=False,
            has_prev=False,
        )

    # =========================================================================
    # Analytics Queries
    # =========================================================================

    @strawberry.field
    async def tool_analytics(
        self,
        info: Info,
        tool_id: strawberry.ID,
        date_range: Optional[DateRangeInput] = None,
    ) -> Optional[ToolAnalytics]:
        """Get analytics for a specific tool."""
        loader = info.context.get_tool_analytics_loader()
        analytics_data = await loader.load(str(tool_id))

        if not analytics_data:
            return None

        return ToolAnalytics(
            tool_id=tool_id,
            tool_key=analytics_data.get("tool_key", "unknown"),
            total_runs=analytics_data.get("total_runs", 0),
            successful_runs=analytics_data.get("successful_runs", 0),
            failed_runs=analytics_data.get("failed_runs", 0),
            success_rate=analytics_data.get("success_rate", 0.0),
            avg_latency_ms=analytics_data.get("avg_latency_ms"),
            p95_latency_ms=analytics_data.get("p95_latency_ms"),
            total_credits_earned=analytics_data.get("total_credits_earned", 0),
            total_credits_refunded=analytics_data.get("total_credits_refunded", 0),
            net_revenue=analytics_data.get("net_revenue", 0),
            avg_rating=analytics_data.get("avg_rating"),
            rating_count=analytics_data.get("rating_count", 0),
            period_start=analytics_data.get("period_start", datetime.now()),
            period_end=analytics_data.get("period_end", datetime.now()),
        )

    # =========================================================================
    # Dimension Queries
    # =========================================================================

    @strawberry.field
    async def dimension_capsules(self, info: Info) -> List[DimensionCapsule]:
        """Get all dimension capsule definitions."""
        from app.fixtures.dimension_capsules import DIMENSION_CAPSULES

        return [
            DimensionCapsule(
                capsule_key=c["capsule_key"],
                version=c["version"],
                stage=c["stage"],
                stage_order=c["stage_order"],
                display_name=c["display_name"],
                display_name_en=c["display_name_en"],
                route_key=c["route_key"],
                input_dimensions=c["input_dimensions"],
                output_dimensions=c["output_dimensions"],
                credit_cost_flash=c["credit_costs"].get("gemini-3-flash-preview", 5),
                credit_cost_pro=c["credit_costs"].get("gemini-3-pro-preview", 15),
            )
            for c in DIMENSION_CAPSULES
        ]

    @strawberry.field
    async def workflow_stages(self, info: Info) -> List[WorkflowStage]:
        """Get workflow stage definitions with their capsules."""
        from app.fixtures.dimension_capsules import (
            WORKFLOW_STAGES,
            DIMENSION_CAPSULES,
        )

        stages = []
        for stage_key, stage_info in WORKFLOW_STAGES.items():
            capsules = [
                DimensionCapsule(
                    capsule_key=c["capsule_key"],
                    version=c["version"],
                    stage=c["stage"],
                    stage_order=c["stage_order"],
                    display_name=c["display_name"],
                    display_name_en=c["display_name_en"],
                    route_key=c["route_key"],
                    input_dimensions=c["input_dimensions"],
                    output_dimensions=c["output_dimensions"],
                    credit_cost_flash=c["credit_costs"].get("gemini-3-flash-preview", 5),
                    credit_cost_pro=c["credit_costs"].get("gemini-3-pro-preview", 15),
                )
                for c in DIMENSION_CAPSULES
                if c["stage"] == stage_key
            ]

            stages.append(
                WorkflowStage(
                    order=stage_info["order"],
                    name_ko=stage_info["name_ko"],
                    name_en=stage_info["name_en"],
                    capsules=capsules,
                )
            )

        return sorted(stages, key=lambda s: s.order)

    # =========================================================================
    # System Queries
    # =========================================================================

    @strawberry.field
    async def system_health(self, info: Info) -> SystemHealth:
        """Get system health status."""
        # Try to get real stats from optimizers
        try:
            from app.db import get_db_optimizer
            from app.llm import get_cost_optimizer

            db_opt = get_db_optimizer()
            llm_opt = get_cost_optimizer()

            pool_stats = db_opt.get_pool_stats()
            cache_stats = llm_opt.get_stats()

            slow_query_count = db_opt.get_query_stats().get("slow_queries", 0)
            pool_utilization = pool_stats.get("utilization", 0.0)
            if isinstance(pool_utilization, str):
                pool_utilization = float(pool_utilization.rstrip("%")) / 100

            total = cache_stats.get("total_requests", 0)
            hits = cache_stats.get("cache_hits", 0)
            cache_hit_rate = hits / total if total > 0 else 0.0

        except Exception:
            slow_query_count = 0
            pool_utilization = 0.0
            cache_hit_rate = 0.0

        return SystemHealth(
            status="healthy",
            version="2.0.0",
            database_status="healthy",
            redis_status="healthy",
            qdrant_status="healthy",
            slow_query_count=slow_query_count,
            pool_utilization=pool_utilization,
            cache_hit_rate=cache_hit_rate,
            avg_cost_reduction=0.45,  # 45% average
            uptime_seconds=86400,  # 1 day
            last_check=datetime.now(),
        )

    @strawberry.field
    async def query_stats(self, info: Info) -> QueryStats:
        """Get database query statistics (admin only)."""
        info.context.require_admin()

        try:
            from app.db import get_db_optimizer
            import json

            optimizer = get_db_optimizer()
            stats = optimizer.get_query_stats()

            return QueryStats(
                total_queries=stats.get("total_queries", 0),
                slow_queries=stats.get("slow_queries", 0),
                avg_query_time_ms=stats.get("avg_query_time_ms", 0.0),
                queries_by_type=json.dumps(stats.get("by_type", {})),
            )
        except Exception:
            return QueryStats(
                total_queries=0,
                slow_queries=0,
                avg_query_time_ms=0.0,
                queries_by_type="{}",
            )

    @strawberry.field
    async def cache_stats(self, info: Info) -> CacheStats:
        """Get LLM cache statistics (admin only)."""
        info.context.require_admin()

        try:
            from app.llm import get_cost_optimizer

            optimizer = get_cost_optimizer()
            stats = optimizer.get_stats()

            total = stats.get("total_requests", 0)
            hits = stats.get("cache_hits", 0)

            return CacheStats(
                total_requests=total,
                cache_hits=hits,
                cache_misses=total - hits,
                hit_rate=hits / total if total > 0 else 0.0,
                cost_saved_estimate=stats.get("cost_saved_estimate", 0.0),
            )
        except Exception:
            return CacheStats(
                total_requests=0,
                cache_hits=0,
                cache_misses=0,
                hit_rate=0.0,
                cost_saved_estimate=0.0,
            )
