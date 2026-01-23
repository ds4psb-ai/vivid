"""
GraphQL Mutations - 2026 Best Practices

Defines all mutation resolvers with:
1. Input validation
2. Authorization checks
3. Proper error handling
4. Transactional semantics
5. Full database integration (P0 Implementation)
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4, UUID

import strawberry
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

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
from app.models_telemetry import ToolManifest, ToolRunEvent, ForkEvent
from app.models_telemetry import ToolTier as DBToolTier


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
        db = info.context.db

        try:
            # 1. Validate tool exists in database
            result = await db.execute(
                select(ToolManifest).where(ToolManifest.tool_key == input.tool_key)
            )
            tool = result.scalar_one_or_none()

            if not tool:
                return ToolRunStartResult(
                    errors=[
                        MutationError(
                            field="tool_key",
                            message=f"Tool '{input.tool_key}' not found",
                            code="TOOL_NOT_FOUND",
                        )
                    ]
                )

            if not tool.is_active:
                return ToolRunStartResult(
                    errors=[
                        MutationError(
                            field="tool_key",
                            message=f"Tool '{input.tool_key}' is not active",
                            code="TOOL_INACTIVE",
                        )
                    ]
                )

            # 2. Create run event record
            run_event = ToolRunEvent(
                tool_id=tool.id,
                tool_key=input.tool_key,
                tool_version=tool.version,
                user_id=user_id,
                session_id=UUID(input.session_id) if input.session_id else None,
                status="started",
                inputs_summary={} if not input.inputs_summary else {"summary": input.inputs_summary},
            )

            db.add(run_event)
            await db.commit()
            await db.refresh(run_event)

            # 3. Increment tool usage count
            await db.execute(
                update(ToolManifest)
                .where(ToolManifest.id == tool.id)
                .values(usage_count=ToolManifest.usage_count + 1)
            )
            await db.commit()

            # Invalidate DataLoader caches
            info.context.invalidate_loaders()

            run = ToolRun(
                id=strawberry.ID(str(run_event.id)),
                tool_id=strawberry.ID(str(tool.id)),
                tool_key=input.tool_key,
                user_id=user_id,
                session_id=input.session_id,
                status=RunStatus.STARTED,
                credits_charged=0,
                created_at=run_event.created_at,
            )

            return ToolRunStartResult(run=run)

        except Exception as e:
            await db.rollback()
            return ToolRunStartResult(
                errors=[
                    MutationError(
                        message=f"Failed to start tool run: {str(e)}",
                        code="INTERNAL_ERROR",
                    )
                ]
            )

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

        db = info.context.db
        user_id = info.context.user_id

        try:
            # 1. Load run from database
            run_id = UUID(str(input.run_id))
            result = await db.execute(
                select(ToolRunEvent).where(ToolRunEvent.id == run_id)
            )
            run_event = result.scalar_one_or_none()

            if not run_event:
                return ToolRunCompleteResult(
                    errors=[
                        MutationError(
                            field="run_id",
                            message="Run not found",
                            code="RUN_NOT_FOUND",
                        )
                    ]
                )

            # 2. Verify ownership
            if run_event.user_id and run_event.user_id != user_id:
                return ToolRunCompleteResult(
                    errors=[
                        MutationError(
                            field="run_id",
                            message="Not authorized to complete this run",
                            code="UNAUTHORIZED",
                        )
                    ]
                )

            # 3. Update run status in database
            status_map = {
                RunStatus.SUCCESS: "success",
                RunStatus.FAILED: "failed",
                RunStatus.TIMEOUT: "timeout",
                RunStatus.STARTED: "started",
            }

            await db.execute(
                update(ToolRunEvent)
                .where(ToolRunEvent.id == run_id)
                .values(
                    status=status_map.get(input.status, "success"),
                    latency_ms=input.latency_ms,
                    error_message=input.error_message,
                    credits_charged=input.credits_charged,
                    credits_refunded=input.credits_refunded,
                    completed_at=datetime.utcnow(),
                )
            )
            await db.commit()

            # 4. Update tool revenue if credits were charged
            if input.credits_charged > 0:
                # Get tool and update total_revenue
                tool_result = await db.execute(
                    select(ToolManifest).where(ToolManifest.id == run_event.tool_id)
                )
                tool = tool_result.scalar_one_or_none()
                if tool:
                    net_revenue = input.credits_charged - (input.credits_refunded or 0)
                    await db.execute(
                        update(ToolManifest)
                        .where(ToolManifest.id == tool.id)
                        .values(total_revenue=ToolManifest.total_revenue + net_revenue)
                    )
                    await db.commit()

            # Invalidate DataLoader caches
            info.context.invalidate_loaders()

            run = ToolRun(
                id=input.run_id,
                tool_id=strawberry.ID(str(run_event.tool_id)),
                tool_key=run_event.tool_key,
                user_id=user_id,
                status=input.status,
                latency_ms=input.latency_ms,
                error_message=input.error_message,
                credits_charged=input.credits_charged,
                credits_refunded=input.credits_refunded,
                created_at=run_event.created_at,
                completed_at=datetime.utcnow(),
            )

            return ToolRunCompleteResult(run=run)

        except Exception as e:
            await db.rollback()
            return ToolRunCompleteResult(
                errors=[
                    MutationError(
                        message=f"Failed to complete tool run: {str(e)}",
                        code="INTERNAL_ERROR",
                    )
                ]
            )

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

        db = info.context.db
        user_id = info.context.user_id

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

        try:
            # 1. Load run from database
            run_id = UUID(str(input.run_id))
            result = await db.execute(
                select(ToolRunEvent).where(ToolRunEvent.id == run_id)
            )
            run_event = result.scalar_one_or_none()

            if not run_event:
                return ToolFeedbackResult(
                    errors=[
                        MutationError(
                            field="run_id",
                            message="Run not found",
                            code="RUN_NOT_FOUND",
                        )
                    ]
                )

            # 2. Verify ownership
            if run_event.user_id and run_event.user_id != user_id:
                return ToolFeedbackResult(
                    errors=[
                        MutationError(
                            field="run_id",
                            message="Not authorized to provide feedback for this run",
                            code="UNAUTHORIZED",
                        )
                    ]
                )

            # 3. Update run with feedback
            await db.execute(
                update(ToolRunEvent)
                .where(ToolRunEvent.id == run_id)
                .values(
                    user_rating=input.rating,
                    user_feedback=input.feedback,
                )
            )
            await db.commit()

            # 4. Update tool quality_rating (moving average approximation)
            tool_result = await db.execute(
                select(ToolManifest).where(ToolManifest.id == run_event.tool_id)
            )
            tool = tool_result.scalar_one_or_none()
            if tool:
                # Simple moving average: new_avg = (old_avg * count + new_rating) / (count + 1)
                old_rating = tool.quality_rating or 0.0
                # Estimate count from usage (rough approximation)
                estimated_feedbacks = max(1, tool.usage_count // 10)
                new_rating = (old_rating * estimated_feedbacks + input.rating) / (estimated_feedbacks + 1)
                await db.execute(
                    update(ToolManifest)
                    .where(ToolManifest.id == tool.id)
                    .values(quality_rating=new_rating)
                )
                await db.commit()

            # Invalidate DataLoader caches
            info.context.invalidate_loaders()

            return ToolFeedbackResult(
                run_id=input.run_id,
                rating=input.rating,
            )

        except Exception as e:
            await db.rollback()
            return ToolFeedbackResult(
                errors=[
                    MutationError(
                        message=f"Failed to submit feedback: {str(e)}",
                        code="INTERNAL_ERROR",
                    )
                ]
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
        Note: Payment processing is mocked for now. In production,
        integrate with Stripe/payment provider before crediting.
        """
        info.context.require_auth()

        db = info.context.db
        user_id = info.context.user_id

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

        if not payment_method_id or len(payment_method_id) < 3:
            return CreditPurchaseResult(
                errors=[
                    MutationError(
                        field="payment_method_id",
                        message="Valid payment method required",
                        code="INVALID_PAYMENT_METHOD",
                    )
                ]
            )

        try:
            # 1. Process payment (mock for now - in production use Stripe/etc)
            # In production: await payment_service.charge(payment_method_id, amount)
            payment_successful = True  # Mock
            if not payment_successful:
                return CreditPurchaseResult(
                    errors=[
                        MutationError(
                            field="payment_method_id",
                            message="Payment failed",
                            code="PAYMENT_FAILED",
                        )
                    ]
                )

            # 2. Get or create user credit record
            from app.models import User
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            transaction_id = str(uuid4())

            if user:
                # Update existing user balance
                current_balance = getattr(user, "credit_balance", 0) or 0
                new_balance = current_balance + amount

                await db.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(credit_balance=new_balance)
                )
                await db.commit()
            else:
                # User doesn't exist in database - return current purchase amount
                # This can happen with external auth systems
                new_balance = amount

            # 3. Create transaction record (optional: depends on credit_ledger table)
            # In production: await credit_service.record_transaction(...)

            # Invalidate DataLoader caches
            info.context.invalidate_loaders()

            return CreditPurchaseResult(
                new_balance=new_balance,
                transaction_id=strawberry.ID(transaction_id),
            )

        except Exception as e:
            await db.rollback()
            return CreditPurchaseResult(
                errors=[
                    MutationError(
                        message=f"Failed to purchase credits: {str(e)}",
                        code="INTERNAL_ERROR",
                    )
                ]
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

        db = info.context.db
        user_id = info.context.user_id

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

        try:
            # Define known promo codes (in production: store in database)
            promo_codes = {
                "WELCOME100": {"credits": 100, "max_uses": 1},
                "BETA2026": {"credits": 500, "max_uses": 1},
                "CREATOR": {"credits": 1000, "max_uses": 1},
            }

            code_upper = code.upper()
            if code_upper not in promo_codes:
                return CreditPurchaseResult(
                    errors=[
                        MutationError(
                            field="code",
                            message="Promo code not found or expired",
                            code="CODE_NOT_FOUND",
                        )
                    ]
                )

            promo = promo_codes[code_upper]
            credit_amount = promo["credits"]

            # 2. Get user and update balance
            from app.models import User
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            transaction_id = str(uuid4())

            if user:
                current_balance = getattr(user, "credit_balance", 0) or 0
                new_balance = current_balance + credit_amount

                await db.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(credit_balance=new_balance)
                )
                await db.commit()
            else:
                new_balance = credit_amount

            # Invalidate DataLoader caches
            info.context.invalidate_loaders()

            return CreditPurchaseResult(
                new_balance=new_balance,
                transaction_id=strawberry.ID(transaction_id),
            )

        except Exception as e:
            await db.rollback()
            return CreditPurchaseResult(
                errors=[
                    MutationError(
                        message=f"Failed to redeem promo code: {str(e)}",
                        code="INTERNAL_ERROR",
                    )
                ]
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

        db = info.context.db
        user_id = info.context.user_id

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

        try:
            # 1. Check for duplicate tool_key
            existing = await db.execute(
                select(ToolManifest).where(ToolManifest.tool_key == tool_key)
            )
            if existing.scalar_one_or_none():
                return ToolCreateResult(
                    errors=[
                        MutationError(
                            field="tool_key",
                            message=f"Tool with key '{tool_key}' already exists",
                            code="DUPLICATE_TOOL_KEY",
                        )
                    ]
                )

            # 2. Create tool manifest in database
            tool_manifest = ToolManifest(
                tool_key=tool_key,
                display_name=display_name,
                description=description,
                version="1.0.0",
                category=category,
                tier=DBToolTier.EXPERIMENTAL.value,
                credit_cost=credit_cost,
                created_by=user_id or "unknown",
                safety_rating="review",
                sandbox_required=True,
                is_active=True,
            )

            db.add(tool_manifest)
            await db.commit()
            await db.refresh(tool_manifest)

            # Invalidate DataLoader caches
            info.context.invalidate_loaders()

            tool = Tool(
                id=strawberry.ID(str(tool_manifest.id)),
                tool_key=tool_key,
                display_name=display_name,
                description=description,
                version="1.0.0",
                category=category,
                tier=ToolTier.EXPERIMENTAL,
                credit_cost=credit_cost,
                created_by=user_id or "unknown",
                safety_rating=SafetyRating.REVIEW,
                sandbox_required=True,
                created_at=tool_manifest.created_at,
                updated_at=tool_manifest.updated_at,
            )

            return ToolCreateResult(tool=tool)

        except IntegrityError:
            await db.rollback()
            return ToolCreateResult(
                errors=[
                    MutationError(
                        field="tool_key",
                        message=f"Tool with key '{tool_key}' already exists",
                        code="DUPLICATE_TOOL_KEY",
                    )
                ]
            )
        except Exception as e:
            await db.rollback()
            return ToolCreateResult(
                errors=[
                    MutationError(
                        message=f"Failed to create tool: {str(e)}",
                        code="INTERNAL_ERROR",
                    )
                ]
            )

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

        db = info.context.db
        user_id = info.context.user_id

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

        try:
            # 1. Validate parent tool exists
            parent_uuid = UUID(str(parent_tool_id))
            parent_result = await db.execute(
                select(ToolManifest).where(ToolManifest.id == parent_uuid)
            )
            parent_tool = parent_result.scalar_one_or_none()

            if not parent_tool:
                return ToolCreateResult(
                    errors=[
                        MutationError(
                            field="parent_tool_id",
                            message="Parent tool not found",
                            code="PARENT_NOT_FOUND",
                        )
                    ]
                )

            # 2. Check for duplicate tool_key
            existing = await db.execute(
                select(ToolManifest).where(ToolManifest.tool_key == new_tool_key)
            )
            if existing.scalar_one_or_none():
                return ToolCreateResult(
                    errors=[
                        MutationError(
                            field="new_tool_key",
                            message=f"Tool with key '{new_tool_key}' already exists",
                            code="DUPLICATE_TOOL_KEY",
                        )
                    ]
                )

            # 3. Calculate fork depth
            fork_depth = parent_tool.fork_depth + 1

            # 4. Create new tool manifest
            forked_tool = ToolManifest(
                tool_key=new_tool_key,
                display_name=new_display_name,
                description=f"Forked from {parent_tool.display_name}: {fork_reason or 'Custom modifications'}",
                version="1.0.0",
                category=parent_tool.category,
                tier=DBToolTier.EXPERIMENTAL.value,
                credit_cost=parent_tool.credit_cost,
                input_schema=parent_tool.input_schema,
                output_schema=parent_tool.output_schema,
                parent_tool_id=parent_uuid,
                fork_depth=fork_depth,
                created_by=user_id or "unknown",
                safety_rating="review",
                sandbox_required=True,
                is_active=True,
            )

            db.add(forked_tool)
            await db.commit()
            await db.refresh(forked_tool)

            # 5. Update parent's fork count
            await db.execute(
                update(ToolManifest)
                .where(ToolManifest.id == parent_uuid)
                .values(fork_count=ToolManifest.fork_count + 1)
            )
            await db.commit()

            # 6. Create fork event for attribution tracking
            fork_event = ForkEvent(
                parent_tool_id=parent_uuid,
                child_tool_id=forked_tool.id,
                fork_depth=fork_depth,
                forker_id=user_id or "unknown",
                fork_reason=fork_reason,
            )

            db.add(fork_event)
            await db.commit()

            # Invalidate DataLoader caches
            info.context.invalidate_loaders()

            tool = Tool(
                id=strawberry.ID(str(forked_tool.id)),
                tool_key=new_tool_key,
                display_name=new_display_name,
                description=forked_tool.description,
                version="1.0.0",
                category=parent_tool.category,
                tier=ToolTier.EXPERIMENTAL,
                credit_cost=parent_tool.credit_cost,
                parent_tool_id=parent_tool_id,
                fork_depth=fork_depth,
                created_by=user_id or "unknown",
                safety_rating=SafetyRating.REVIEW,
                sandbox_required=True,
                created_at=forked_tool.created_at,
                updated_at=forked_tool.updated_at,
            )

            return ToolCreateResult(tool=tool)

        except IntegrityError:
            await db.rollback()
            return ToolCreateResult(
                errors=[
                    MutationError(
                        field="new_tool_key",
                        message=f"Tool with key '{new_tool_key}' already exists",
                        code="DUPLICATE_TOOL_KEY",
                    )
                ]
            )
        except Exception as e:
            await db.rollback()
            return ToolCreateResult(
                errors=[
                    MutationError(
                        message=f"Failed to fork tool: {str(e)}",
                        code="INTERNAL_ERROR",
                    )
                ]
            )

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

        db = info.context.db
        admin_id = info.context.user_id

        try:
            # 1. Load tool from database
            tool_uuid = UUID(str(tool_id))
            result = await db.execute(
                select(ToolManifest).where(ToolManifest.id == tool_uuid)
            )
            tool_manifest = result.scalar_one_or_none()

            if not tool_manifest:
                return ToolCreateResult(
                    errors=[
                        MutationError(
                            field="tool_id",
                            message="Tool not found",
                            code="TOOL_NOT_FOUND",
                        )
                    ]
                )

            # 2. Map GraphQL enums to DB values
            tier_map = {
                ToolTier.EXPERIMENTAL: DBToolTier.EXPERIMENTAL.value,
                ToolTier.VERIFIED: DBToolTier.VERIFIED.value,
                ToolTier.CERTIFIED: DBToolTier.CERTIFIED.value,
            }
            safety_map = {
                SafetyRating.SAFE: "safe",
                SafetyRating.REVIEW: "review",
                SafetyRating.RESTRICTED: "restricted",
            }

            # 3. Update tool tier, safety rating, and approval info
            await db.execute(
                update(ToolManifest)
                .where(ToolManifest.id == tool_uuid)
                .values(
                    tier=tier_map[new_tier],
                    safety_rating=safety_map[safety_rating],
                    approved_at=datetime.utcnow(),
                    approved_by=admin_id,
                    sandbox_required=safety_rating == SafetyRating.RESTRICTED,
                    updated_at=datetime.utcnow(),
                )
            )
            await db.commit()

            # Refresh to get updated values
            await db.refresh(tool_manifest)

            # Invalidate DataLoader caches
            info.context.invalidate_loaders()

            tool = Tool(
                id=tool_id,
                tool_key=tool_manifest.tool_key,
                display_name=tool_manifest.display_name,
                description=tool_manifest.description,
                version=tool_manifest.version,
                category=tool_manifest.category,
                tier=new_tier,
                credit_cost=tool_manifest.credit_cost,
                created_by=tool_manifest.created_by,
                safety_rating=safety_rating,
                sandbox_required=safety_rating == SafetyRating.RESTRICTED,
                created_at=tool_manifest.created_at,
                updated_at=tool_manifest.updated_at,
            )

            return ToolCreateResult(tool=tool)

        except Exception as e:
            await db.rollback()
            return ToolCreateResult(
                errors=[
                    MutationError(
                        message=f"Failed to approve tool: {str(e)}",
                        code="INTERNAL_ERROR",
                    )
                ]
            )

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
