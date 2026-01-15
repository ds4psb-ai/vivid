"""
GraphQL Mutations - 2026 Best Practices

Defines all mutation resolvers with:
1. Input validation
2. Authorization checks
3. Proper error handling
4. Transactional semantics
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

import strawberry

from app.graphql.types import (
    Tool,
    ToolTier,
    SafetyRating,
    ToolRun,
    RunStatus,
    ToolRunInput,
    ToolRunCompleteInput,
    ToolFeedbackInput,
)
from app.graphql.context import Info


# =============================================================================
# Mutation Response Types
# =============================================================================

@strawberry.type
class MutationError:
    """Error details for failed mutations."""
    field: Optional[str] = None
    message: str
    code: str


@strawberry.type
class ToolRunStartResult:
    """Result of starting a tool run."""
    run: Optional[ToolRun] = None
    errors: list[MutationError] = strawberry.field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.run is not None and len(self.errors) == 0


@strawberry.type
class ToolRunCompleteResult:
    """Result of completing a tool run."""
    run: Optional[ToolRun] = None
    errors: list[MutationError] = strawberry.field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.run is not None and len(self.errors) == 0


@strawberry.type
class ToolFeedbackResult:
    """Result of submitting tool feedback."""
    run_id: Optional[strawberry.ID] = None
    rating: Optional[int] = None
    errors: list[MutationError] = strawberry.field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.run_id is not None and len(self.errors) == 0


@strawberry.type
class CreditPurchaseResult:
    """Result of purchasing credits."""
    new_balance: Optional[int] = None
    transaction_id: Optional[strawberry.ID] = None
    errors: list[MutationError] = strawberry.field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.new_balance is not None and len(self.errors) == 0


@strawberry.type
class ToolCreateResult:
    """Result of creating a tool."""
    tool: Optional[Tool] = None
    errors: list[MutationError] = strawberry.field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.tool is not None and len(self.errors) == 0


# =============================================================================
# Mutations
# =============================================================================

@strawberry.type
class Mutation:
    """GraphQL Mutation root type."""

    # =========================================================================
    # Tool Run Mutations
    # =========================================================================

    @strawberry.mutation
    async def start_tool_run(
        self,
        info: Info,
        input: ToolRunInput,
    ) -> ToolRunStartResult:
        """
        Start a new tool run.

        Records the start of a tool execution and reserves credits.
        """
        info.context.require_auth()

        user_id = info.context.user_id

        # Validate tool exists
        # TODO: Check tool_key in database

        # Create run record
        run_id = str(uuid4())

        # TODO: Reserve credits from user balance
        # TODO: Insert run record in database

        run = ToolRun(
            id=strawberry.ID(run_id),
            tool_id=strawberry.ID(str(uuid4())),  # TODO: Get actual tool ID
            tool_key=input.tool_key,
            user_id=user_id,
            session_id=input.session_id,
            status=RunStatus.STARTED,
            credits_charged=0,
            created_at=datetime.now(),
        )

        return ToolRunStartResult(run=run)

    @strawberry.mutation
    async def complete_tool_run(
        self,
        info: Info,
        input: ToolRunCompleteInput,
    ) -> ToolRunCompleteResult:
        """
        Complete a tool run.

        Records the completion status and finalizes credit charges.
        """
        info.context.require_auth()

        # Validate run exists and belongs to user
        # TODO: Load run from database

        # Update run status
        run = ToolRun(
            id=input.run_id,
            tool_id=strawberry.ID(str(uuid4())),
            tool_key="unknown",  # TODO: Get from database
            user_id=info.context.user_id,
            status=input.status,
            latency_ms=input.latency_ms,
            error_message=input.error_message,
            credits_charged=input.credits_charged,
            credits_refunded=input.credits_refunded,
            created_at=datetime.now(),
            completed_at=datetime.now(),
        )

        # TODO: Commit or refund credits based on status
        # TODO: Update run record in database

        return ToolRunCompleteResult(run=run)

    @strawberry.mutation
    async def submit_tool_feedback(
        self,
        info: Info,
        input: ToolFeedbackInput,
    ) -> ToolFeedbackResult:
        """
        Submit feedback for a tool run.

        Records user rating and optional text feedback.
        """
        info.context.require_auth()

        # Validate rating
        if input.rating < 1 or input.rating > 5:
            return ToolFeedbackResult(
                errors=[
                    MutationError(
                        field="rating",
                        message="Rating must be between 1 and 5",
                        code="INVALID_RATING",
                    )
                ]
            )

        # TODO: Validate run exists and belongs to user
        # TODO: Update run record with feedback

        return ToolFeedbackResult(
            run_id=input.run_id,
            rating=input.rating,
        )

    # =========================================================================
    # Credit Mutations
    # =========================================================================

    @strawberry.mutation
    async def purchase_credits(
        self,
        info: Info,
        amount: int,
        payment_method_id: str,
    ) -> CreditPurchaseResult:
        """
        Purchase credits for the user's account.

        Processes payment and adds credits to balance.
        """
        info.context.require_auth()

        # Validate amount
        if amount < 100:
            return CreditPurchaseResult(
                errors=[
                    MutationError(
                        field="amount",
                        message="Minimum purchase is 100 credits",
                        code="INVALID_AMOUNT",
                    )
                ]
            )

        if amount > 100000:
            return CreditPurchaseResult(
                errors=[
                    MutationError(
                        field="amount",
                        message="Maximum purchase is 100,000 credits",
                        code="INVALID_AMOUNT",
                    )
                ]
            )

        # TODO: Process payment via payment service
        # TODO: Add credits to user balance
        # TODO: Create transaction record

        transaction_id = str(uuid4())
        new_balance = 1000 + amount  # Mock: add to current balance

        return CreditPurchaseResult(
            new_balance=new_balance,
            transaction_id=strawberry.ID(transaction_id),
        )

    @strawberry.mutation
    async def redeem_promo_code(
        self,
        info: Info,
        code: str,
    ) -> CreditPurchaseResult:
        """
        Redeem a promotional code for credits.
        """
        info.context.require_auth()

        # Validate code format
        if len(code) < 4:
            return CreditPurchaseResult(
                errors=[
                    MutationError(
                        field="code",
                        message="Invalid promo code",
                        code="INVALID_CODE",
                    )
                ]
            )

        # TODO: Validate promo code in database
        # TODO: Check if already redeemed by this user
        # TODO: Add credits to balance

        # Mock: assume valid code for 100 credits
        return CreditPurchaseResult(
            new_balance=1100,
            transaction_id=strawberry.ID(str(uuid4())),
        )

    # =========================================================================
    # Tool Management Mutations
    # =========================================================================

    @strawberry.mutation
    async def create_tool(
        self,
        info: Info,
        tool_key: str,
        display_name: str,
        description: str,
        category: str,
        credit_cost: int = 5,
    ) -> ToolCreateResult:
        """
        Create a new tool (capsule).

        New tools start in 'experimental' tier.
        """
        info.context.require_auth()

        # Validate tool_key format
        import re

        if not re.match(r"^[a-z0-9-]+$", tool_key):
            return ToolCreateResult(
                errors=[
                    MutationError(
                        field="tool_key",
                        message="Tool key must be lowercase alphanumeric with hyphens only",
                        code="INVALID_TOOL_KEY",
                    )
                ]
            )

        if len(tool_key) < 3 or len(tool_key) > 50:
            return ToolCreateResult(
                errors=[
                    MutationError(
                        field="tool_key",
                        message="Tool key must be 3-50 characters",
                        code="INVALID_TOOL_KEY",
                    )
                ]
            )

        # TODO: Check for duplicate tool_key
        # TODO: Insert tool into database

        tool = Tool(
            id=strawberry.ID(str(uuid4())),
            tool_key=tool_key,
            display_name=display_name,
            description=description,
            version="1.0.0",
            category=category,
            tier=ToolTier.EXPERIMENTAL,
            credit_cost=credit_cost,
            created_by=info.context.user_id or "unknown",
            safety_rating=SafetyRating.REVIEW,  # New tools need review
            sandbox_required=True,  # New tools run in sandbox
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        return ToolCreateResult(tool=tool)

    @strawberry.mutation
    async def fork_tool(
        self,
        info: Info,
        parent_tool_id: strawberry.ID,
        new_tool_key: str,
        new_display_name: str,
        fork_reason: Optional[str] = None,
    ) -> ToolCreateResult:
        """
        Fork an existing tool to create a modified version.

        Creates a new tool based on an existing one, maintaining
        attribution for revenue sharing.
        """
        info.context.require_auth()

        # Validate new tool_key format
        import re

        if not re.match(r"^[a-z0-9-]+$", new_tool_key):
            return ToolCreateResult(
                errors=[
                    MutationError(
                        field="new_tool_key",
                        message="Tool key must be lowercase alphanumeric with hyphens only",
                        code="INVALID_TOOL_KEY",
                    )
                ]
            )

        # TODO: Validate parent tool exists
        # TODO: Check for duplicate tool_key
        # TODO: Create fork event
        # TODO: Insert new tool into database

        tool = Tool(
            id=strawberry.ID(str(uuid4())),
            tool_key=new_tool_key,
            display_name=new_display_name,
            description=f"Forked from tool {parent_tool_id}",
            version="1.0.0",
            category="forked",
            tier=ToolTier.EXPERIMENTAL,
            credit_cost=5,
            parent_tool_id=parent_tool_id,
            fork_depth=1,  # TODO: Calculate actual depth
            created_by=info.context.user_id or "unknown",
            safety_rating=SafetyRating.REVIEW,
            sandbox_required=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        return ToolCreateResult(tool=tool)

    # =========================================================================
    # Admin Mutations
    # =========================================================================

    @strawberry.mutation
    async def approve_tool(
        self,
        info: Info,
        tool_id: strawberry.ID,
        new_tier: ToolTier,
        safety_rating: SafetyRating,
    ) -> ToolCreateResult:
        """
        Approve a tool and update its tier (admin only).

        Promotes a tool from experimental to verified/certified.
        """
        info.context.require_admin()

        # TODO: Load tool from database
        # TODO: Update tool tier and safety rating
        # TODO: Update approved_at timestamp

        tool = Tool(
            id=tool_id,
            tool_key="approved-tool",
            display_name="Approved Tool",
            description="An approved tool",
            version="1.0.0",
            category="dimension",
            tier=new_tier,
            credit_cost=5,
            created_by="original-creator",
            safety_rating=safety_rating,
            sandbox_required=safety_rating == SafetyRating.RESTRICTED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        return ToolCreateResult(tool=tool)

    @strawberry.mutation
    async def reset_query_stats(self, info: Info) -> bool:
        """
        Reset database query statistics (admin only).
        """
        info.context.require_admin()

        try:
            from app.db import get_db_optimizer

            optimizer = get_db_optimizer()
            optimizer.profiler.reset_stats()
            return True
        except Exception:
            return False

    @strawberry.mutation
    async def reset_cache_stats(self, info: Info) -> bool:
        """
        Reset LLM cache statistics (admin only).
        """
        info.context.require_admin()

        try:
            from app.llm import get_cost_optimizer

            optimizer = get_cost_optimizer()
            optimizer.reset_stats()
            return True
        except Exception:
            return False
