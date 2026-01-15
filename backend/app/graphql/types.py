"""
GraphQL Types - 2026 Best Practices

Defines all GraphQL types using Strawberry decorators.
Follows the Relay Connection specification for pagination.
"""

from datetime import datetime
from typing import List, Optional, Generic, TypeVar
from uuid import UUID
from enum import Enum

import strawberry


# =============================================================================
# Enums
# =============================================================================

@strawberry.enum
class ToolTier(Enum):
    """Tool trust tier."""
    EXPERIMENTAL = "experimental"
    VERIFIED = "verified"
    CERTIFIED = "certified"


@strawberry.enum
class RunStatus(Enum):
    """Tool run status."""
    STARTED = "started"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@strawberry.enum
class SafetyRating(Enum):
    """Tool safety rating."""
    SAFE = "safe"
    REVIEW = "review"
    RESTRICTED = "restricted"


@strawberry.enum
class CreditTransactionType(Enum):
    """Credit transaction type."""
    PURCHASE = "purchase"
    SPEND = "spend"
    REFUND = "refund"
    BONUS = "bonus"
    REVENUE_SHARE = "revenue_share"


# =============================================================================
# Connection Types (Relay Specification)
# =============================================================================

@strawberry.type
class PageInfo:
    """Pagination information following Relay spec."""
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str] = None
    end_cursor: Optional[str] = None


T = TypeVar("T")


@strawberry.type
class Edge(Generic[T]):
    """Generic edge type for connections."""
    node: T
    cursor: str


@strawberry.type
class Connection(Generic[T]):
    """Generic connection type following Relay spec."""
    edges: List[Edge[T]]
    page_info: PageInfo
    total_count: int


# =============================================================================
# User Types
# =============================================================================

@strawberry.type
class User:
    """User account information."""
    id: strawberry.ID
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

    credit_balance: int = 0
    total_spent: int = 0

    tier: str = "free"  # free, pro, enterprise

    created_at: datetime
    last_login_at: Optional[datetime] = None

    @strawberry.field
    def tools_created_count(self) -> int:
        """Number of tools created by this user."""
        return 0  # Resolved by dataloader

    @strawberry.field
    def total_runs(self) -> int:
        """Total tool runs by this user."""
        return 0  # Resolved by dataloader


@strawberry.type
class CreditBalance:
    """User credit balance details."""
    user_id: strawberry.ID
    balance: int
    reserved: int  # Credits reserved for pending operations
    available: int  # balance - reserved

    lifetime_purchased: int
    lifetime_spent: int
    lifetime_earned: int  # From tool revenue share


@strawberry.type
class CreditTransaction:
    """Credit transaction record."""
    id: strawberry.ID
    user_id: strawberry.ID

    transaction_type: CreditTransactionType
    amount: int

    description: str
    reference_id: Optional[str] = None  # tool_run_id, purchase_id, etc.

    created_at: datetime


# =============================================================================
# Tool Types
# =============================================================================

@strawberry.type
class Tool:
    """Tool (Capsule) definition."""
    id: strawberry.ID
    tool_key: str
    display_name: str
    description: str

    version: str
    category: str
    tier: ToolTier

    credit_cost: int

    # Statistics
    usage_count: int = 0
    fork_count: int = 0
    total_revenue: int = 0

    # Quality metrics
    success_rate: Optional[float] = None
    avg_rating: Optional[float] = None
    rating_count: int = 0

    # Metadata
    created_by: str
    safety_rating: SafetyRating = SafetyRating.SAFE
    sandbox_required: bool = False
    is_active: bool = True

    # Fork info
    parent_tool_id: Optional[strawberry.ID] = None
    fork_depth: int = 0

    created_at: datetime
    updated_at: datetime


@strawberry.type
class ToolRun:
    """Tool execution record."""
    id: strawberry.ID
    tool_id: strawberry.ID
    tool_key: str

    user_id: Optional[str] = None
    session_id: Optional[str] = None

    status: RunStatus

    latency_ms: Optional[int] = None
    credits_charged: int = 0
    credits_refunded: int = 0

    error_message: Optional[str] = None

    # User feedback
    user_rating: Optional[int] = None
    user_feedback: Optional[str] = None

    created_at: datetime
    completed_at: Optional[datetime] = None


@strawberry.type
class ToolAnalytics:
    """Analytics summary for a tool."""
    tool_id: strawberry.ID
    tool_key: str

    # Usage stats
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float

    # Performance
    avg_latency_ms: Optional[float] = None
    p95_latency_ms: Optional[float] = None

    # Economics
    total_credits_earned: int
    total_credits_refunded: int
    net_revenue: int

    # Quality
    avg_rating: Optional[float] = None
    rating_count: int

    # Period
    period_start: datetime
    period_end: datetime


# =============================================================================
# Dimension Types
# =============================================================================

@strawberry.type
class DimensionCapsule:
    """Dimension app capsule specification."""
    capsule_key: str
    version: str
    stage: str
    stage_order: int

    display_name: str
    display_name_en: str
    route_key: str

    input_dimensions: List[str]
    output_dimensions: List[str]

    # Credit costs by model
    credit_cost_flash: int
    credit_cost_pro: int


@strawberry.type
class WorkflowStage:
    """Workflow stage definition."""
    order: int
    name_ko: str
    name_en: str
    capsules: List[DimensionCapsule]


# =============================================================================
# System Types
# =============================================================================

@strawberry.type
class SystemHealth:
    """System health status."""
    status: str  # healthy, degraded, unhealthy
    version: str

    database_status: str
    redis_status: str
    qdrant_status: str

    # Query optimizer stats
    slow_query_count: int
    pool_utilization: float

    # LLM optimizer stats
    cache_hit_rate: float
    avg_cost_reduction: float

    uptime_seconds: int
    last_check: datetime


@strawberry.type
class QueryStats:
    """Database query statistics."""
    total_queries: int
    slow_queries: int
    avg_query_time_ms: float

    queries_by_type: str  # JSON string of breakdown


@strawberry.type
class CacheStats:
    """LLM cache statistics."""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float

    cost_saved_estimate: float


# =============================================================================
# Input Types
# =============================================================================

@strawberry.input
class ToolRunInput:
    """Input for recording a tool run."""
    tool_key: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    inputs_summary: Optional[str] = None  # JSON string


@strawberry.input
class ToolRunCompleteInput:
    """Input for completing a tool run."""
    run_id: strawberry.ID
    status: RunStatus

    latency_ms: Optional[int] = None
    error_message: Optional[str] = None

    credits_charged: int = 0
    credits_refunded: int = 0


@strawberry.input
class ToolFeedbackInput:
    """Input for tool feedback."""
    run_id: strawberry.ID
    rating: int  # 1-5
    feedback: Optional[str] = None


@strawberry.input
class PaginationInput:
    """Pagination parameters."""
    first: Optional[int] = 20
    after: Optional[str] = None
    last: Optional[int] = None
    before: Optional[str] = None


@strawberry.input
class ToolFilterInput:
    """Filter parameters for tools."""
    category: Optional[str] = None
    tier: Optional[ToolTier] = None
    created_by: Optional[str] = None
    is_active: Optional[bool] = True
    min_rating: Optional[float] = None
    search: Optional[str] = None


@strawberry.input
class DateRangeInput:
    """Date range filter."""
    start: datetime
    end: datetime


# =============================================================================
# Helper Functions
# =============================================================================

def create_connection(
    items: List[T],
    total_count: int,
    has_next: bool,
    has_prev: bool,
    cursor_field: str = "id",
) -> Connection[T]:
    """Create a connection from a list of items."""
    edges = [
        Edge(
            node=item,
            cursor=str(getattr(item, cursor_field, i)),
        )
        for i, item in enumerate(items)
    ]

    return Connection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=has_next,
            has_previous_page=has_prev,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        total_count=total_count,
    )
