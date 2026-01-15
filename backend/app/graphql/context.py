"""
GraphQL Context - 2026 Best Practices

Provides request context with:
1. Authentication info
2. DataLoaders for N+1 prevention
3. Database session access
4. Request metadata
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from functools import cached_property

import strawberry
from strawberry.fastapi import BaseContext
from strawberry.dataloader import DataLoader
from fastapi import Request, Response

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class GraphQLContext(BaseContext):
    """
    GraphQL execution context.

    Provides access to:
    - Current authenticated user
    - Database session
    - DataLoaders for batched queries
    - Request/Response objects
    """

    request: Request
    response: Response

    # User info (populated from auth)
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_tier: str = "free"
    is_authenticated: bool = False
    is_admin: bool = False

    # Request metadata
    request_id: Optional[str] = None
    client_ip: Optional[str] = None

    # Internal state
    _db_session: Optional["AsyncSession"] = None
    _dataloaders: Dict[str, DataLoader] = field(default_factory=dict)

    @cached_property
    def db(self) -> "AsyncSession":
        """Get database session (lazy loaded)."""
        if self._db_session is None:
            raise RuntimeError("Database session not available in this context")
        return self._db_session

    def require_auth(self) -> None:
        """Raise error if not authenticated."""
        if not self.is_authenticated:
            raise PermissionError("Authentication required")

    def require_admin(self) -> None:
        """Raise error if not admin."""
        if not self.is_admin:
            raise PermissionError("Admin access required")

    # =========================================================================
    # DataLoaders
    # =========================================================================

    def get_user_loader(self) -> DataLoader:
        """Get or create user DataLoader."""
        if "user" not in self._dataloaders:
            self._dataloaders["user"] = DataLoader(load_fn=self._load_users)
        return self._dataloaders["user"]

    def get_tool_loader(self) -> DataLoader:
        """Get or create tool DataLoader."""
        if "tool" not in self._dataloaders:
            self._dataloaders["tool"] = DataLoader(load_fn=self._load_tools)
        return self._dataloaders["tool"]

    def get_tool_runs_loader(self) -> DataLoader:
        """Get or create tool runs DataLoader (by user_id)."""
        if "tool_runs" not in self._dataloaders:
            self._dataloaders["tool_runs"] = DataLoader(load_fn=self._load_tool_runs)
        return self._dataloaders["tool_runs"]

    def get_tool_analytics_loader(self) -> DataLoader:
        """Get or create tool analytics DataLoader."""
        if "tool_analytics" not in self._dataloaders:
            self._dataloaders["tool_analytics"] = DataLoader(
                load_fn=self._load_tool_analytics
            )
        return self._dataloaders["tool_analytics"]

    # =========================================================================
    # DataLoader implementations
    # =========================================================================

    async def _load_users(self, user_ids: List[str]) -> List[Optional[Dict[str, Any]]]:
        """
        Batch load users by ID.

        This prevents N+1 queries when resolving user fields.
        """
        # TODO: Implement actual database query
        # For now, return mock data
        return [
            {
                "id": uid,
                "email": f"user-{uid}@example.com",
                "display_name": f"User {uid}",
                "credit_balance": 100,
            }
            for uid in user_ids
        ]

    async def _load_tools(self, tool_ids: List[str]) -> List[Optional[Dict[str, Any]]]:
        """
        Batch load tools by ID.
        """
        # TODO: Implement actual database query
        return [
            {
                "id": tid,
                "tool_key": f"tool-{tid}",
                "display_name": f"Tool {tid}",
                "category": "general",
            }
            for tid in tool_ids
        ]

    async def _load_tool_runs(
        self, user_ids: List[str]
    ) -> List[List[Dict[str, Any]]]:
        """
        Batch load tool runs by user ID.

        Returns a list of runs for each user ID.
        """
        # TODO: Implement actual database query
        return [[] for _ in user_ids]

    async def _load_tool_analytics(
        self, tool_ids: List[str]
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Batch load tool analytics by tool ID.
        """
        # TODO: Implement actual database query
        from datetime import datetime

        return [
            {
                "tool_id": tid,
                "total_runs": 100,
                "successful_runs": 95,
                "failed_runs": 5,
                "success_rate": 0.95,
                "avg_latency_ms": 250.0,
                "period_start": datetime.now(),
                "period_end": datetime.now(),
            }
            for tid in tool_ids
        ]


async def get_graphql_context(
    request: Request,
    response: Response,
) -> GraphQLContext:
    """
    Context factory for GraphQL requests.

    Extracts authentication info from request headers
    and creates the context object.
    """
    # Extract auth info from headers
    auth_header = request.headers.get("Authorization", "")
    user_id = None
    user_email = None
    user_tier = "free"
    is_authenticated = False
    is_admin = False

    if auth_header.startswith("Bearer "):
        # TODO: Implement actual JWT validation
        # For now, extract user info from a simple token format
        token = auth_header[7:]
        if token:
            # Mock: treat token as user_id for testing
            user_id = token
            user_email = f"{token}@example.com"
            is_authenticated = True

    # Extract request metadata
    request_id = request.headers.get("X-Request-ID")
    client_ip = request.client.host if request.client else None

    # Check admin status (from custom header or user role)
    is_admin = request.headers.get("X-Admin-Access") == "true"

    return GraphQLContext(
        request=request,
        response=response,
        user_id=user_id,
        user_email=user_email,
        user_tier=user_tier,
        is_authenticated=is_authenticated,
        is_admin=is_admin,
        request_id=request_id,
        client_ip=client_ip,
    )


# Type alias for strawberry.Info with our context
Info = strawberry.Info[GraphQLContext, None]
