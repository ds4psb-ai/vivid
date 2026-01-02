"""Fork Revenue Settlement Service.

Handles revenue distribution for tool forks based on Attribution Score.

Revenue Flow:
1. User pays X credits for tool run
2. Platform takes 30% fee
3. Remaining 70% split between:
   - Original creator(s): based on attribution lineage
   - Current tool owner: remainder

Attribution Score determines split:
- 0-25: Fork owner gets 10%, rest to parent chain
- 25-50: Fork owner gets 25%, rest to parent chain
- 50-75: Fork owner gets 50%, rest to parent chain
- 75-100: Fork owner gets 75%, rest to parent chain
"""
import logging
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_telemetry import ToolManifest, ForkEvent
from app.credit_service import get_or_create_user_credits, record_transaction

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

PLATFORM_FEE_RATE = Decimal("0.30")  # 30% platform fee
MAX_LINEAGE_DEPTH = 5  # Max ancestors to consider for revenue share


# =============================================================================
# Settlement Result Models (in-memory, not DB)
# =============================================================================

class SettlementShare:
    """Single recipient's share in a settlement."""
    def __init__(
        self,
        user_id: str,
        tool_id: UUID,
        credits: int,
        share_type: str,  # "owner", "ancestor", "platform"
        attribution_score: Optional[float] = None,
        lineage_depth: int = 0,
    ):
        self.user_id = user_id
        self.tool_id = tool_id
        self.credits = credits
        self.share_type = share_type
        self.attribution_score = attribution_score
        self.lineage_depth = lineage_depth


class SettlementResult:
    """Complete settlement breakdown."""
    def __init__(
        self,
        tool_run_id: UUID,
        tool_id: UUID,
        total_revenue: int,
        platform_fee: int,
        creator_pool: int,
        shares: List[SettlementShare],
    ):
        self.tool_run_id = tool_run_id
        self.tool_id = tool_id
        self.total_revenue = total_revenue
        self.platform_fee = platform_fee
        self.creator_pool = creator_pool
        self.shares = shares
        self.settled_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            "tool_run_id": str(self.tool_run_id),
            "tool_id": str(self.tool_id),
            "total_revenue": self.total_revenue,
            "platform_fee": self.platform_fee,
            "creator_pool": self.creator_pool,
            "shares": [
                {
                    "user_id": s.user_id,
                    "tool_id": str(s.tool_id),
                    "credits": s.credits,
                    "share_type": s.share_type,
                    "attribution_score": s.attribution_score,
                }
                for s in self.shares
            ],
            "settled_at": self.settled_at.isoformat(),
        }


# =============================================================================
# Core Settlement Logic
# =============================================================================

def calculate_owner_share_rate(attribution_score: float) -> Decimal:
    """
    Calculate fork owner's share rate based on attribution score.
    
    Higher attribution = fork added more value = higher owner share.
    """
    if attribution_score >= 75:
        return Decimal("0.75")
    elif attribution_score >= 50:
        return Decimal("0.50")
    elif attribution_score >= 25:
        return Decimal("0.25")
    else:
        return Decimal("0.10")


async def get_tool_lineage(
    db: AsyncSession,
    tool_id: UUID,
    max_depth: int = MAX_LINEAGE_DEPTH,
) -> List[tuple[ToolManifest, Optional[ForkEvent]]]:
    """
    Get the tool's ancestry chain (up to max_depth).
    
    Returns: List of (ToolManifest, ForkEvent) tuples, oldest ancestor first.
    """
    lineage = []
    current_id = tool_id
    depth = 0
    
    while current_id and depth < max_depth:
        tool = await db.get(ToolManifest, current_id)
        if not tool:
            break
        
        # Get fork event for this tool (as child)
        fork_result = await db.execute(
            select(ForkEvent).where(ForkEvent.child_tool_id == current_id)
        )
        fork = fork_result.scalars().first()
        
        lineage.append((tool, fork))
        
        if tool.parent_tool_id:
            current_id = tool.parent_tool_id
            depth += 1
        else:
            break
    
    # Return oldest ancestor first
    return list(reversed(lineage))


async def calculate_settlement(
    db: AsyncSession,
    tool_id: UUID,
    total_credits: int,
    tool_run_id: Optional[UUID] = None,
) -> SettlementResult:
    """
    Calculate revenue settlement for a tool run.
    
    Args:
        db: Database session
        tool_id: The tool that was run
        total_credits: Total credits charged for the run
        tool_run_id: Optional run ID for tracking
    
    Returns:
        SettlementResult with complete breakdown
    """
    shares: List[SettlementShare] = []
    
    # 1. Calculate platform fee
    total = Decimal(total_credits)
    platform_fee_amount = (total * PLATFORM_FEE_RATE).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    creator_pool = total - platform_fee_amount
    
    # 2. Get tool lineage
    lineage = await get_tool_lineage(db, tool_id)
    
    if not lineage:
        logger.error(f"Tool {tool_id} not found in lineage")
        return SettlementResult(
            tool_run_id=tool_run_id or uuid4(),
            tool_id=tool_id,
            total_revenue=total_credits,
            platform_fee=int(platform_fee_amount),
            creator_pool=int(creator_pool),
            shares=[],
        )
    
    # 3. If no forks (original tool), owner gets all creator pool
    current_tool, current_fork = lineage[-1]  # Most recent (the running tool)
    
    if len(lineage) == 1 or current_fork is None:
        # Original tool - owner gets 100% of creator pool
        shares.append(SettlementShare(
            user_id=current_tool.created_by,
            tool_id=current_tool.id,
            credits=int(creator_pool),
            share_type="owner",
            attribution_score=None,
            lineage_depth=0,
        ))
    else:
        # 4. Forked tool - calculate attribution-based split
        attr_score = current_fork.attribution_score if current_fork else 50.0
        owner_rate = calculate_owner_share_rate(attr_score)
        owner_amount = (creator_pool * owner_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        ancestor_pool = creator_pool - owner_amount
        
        # Owner share
        shares.append(SettlementShare(
            user_id=current_tool.created_by,
            tool_id=current_tool.id,
            credits=int(owner_amount),
            share_type="owner",
            attribution_score=attr_score,
            lineage_depth=0,
        ))
        
        # 5. Distribute ancestor_pool among ancestors (equal split for simplicity)
        # In future: weight by each ancestor's own attribution to their parent
        ancestors = lineage[:-1]  # All except current tool
        if ancestors and ancestor_pool > 0:
            per_ancestor = (ancestor_pool / len(ancestors)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            remainder = int(ancestor_pool) - (int(per_ancestor) * len(ancestors))
            
            for i, (ancestor_tool, ancestor_fork) in enumerate(ancestors):
                ancestor_credits = int(per_ancestor)
                if i == 0:
                    ancestor_credits += remainder  # Give remainder to oldest ancestor
                
                if ancestor_credits > 0:
                    shares.append(SettlementShare(
                        user_id=ancestor_tool.created_by,
                        tool_id=ancestor_tool.id,
                        credits=ancestor_credits,
                        share_type="ancestor",
                        attribution_score=ancestor_fork.attribution_score if ancestor_fork else None,
                        lineage_depth=len(ancestors) - i,
                    ))
    
    return SettlementResult(
        tool_run_id=tool_run_id or uuid4(),
        tool_id=tool_id,
        total_revenue=total_credits,
        platform_fee=int(platform_fee_amount),
        creator_pool=int(creator_pool),
        shares=shares,
    )


async def execute_settlement(
    db: AsyncSession,
    settlement: SettlementResult,
) -> None:
    """
    Execute a settlement by crediting all recipients.
    
    This creates ledger entries for each share.
    """
    for share in settlement.shares:
        # Get or create user credits
        user_credits = await get_or_create_user_credits(db, share.user_id, seed_balance=0)
        
        # Add credits
        user_credits.topup_credits += share.credits
        user_credits.balance += share.credits
        
        # Record transaction
        await record_transaction(
            db=db,
            user_id=share.user_id,
            event_type="revenue_share",
            amount=share.credits,
            new_balance=user_credits.balance,
            description=f"Tool revenue: {share.share_type}",
            capsule_run_id=settlement.tool_run_id,
            meta={
                "tool_id": str(share.tool_id),
                "share_type": share.share_type,
                "attribution_score": share.attribution_score,
                "total_revenue": settlement.total_revenue,
                "lineage_depth": share.lineage_depth,
            },
        )
    
    # Update fork's revenue tracking
    if settlement.shares:
        owner_share = next((s for s in settlement.shares if s.share_type == "owner"), None)
        if owner_share:
            # Update ForkEvent revenue
            fork_result = await db.execute(
                select(ForkEvent).where(ForkEvent.child_tool_id == settlement.tool_id)
            )
            fork = fork_result.scalars().first()
            if fork:
                fork.revenue_generated += owner_share.credits
                # Calculate shared amount (total - owner's share)
                shared = settlement.creator_pool - owner_share.credits
                fork.revenue_shared += shared
    
    # Update tool's total revenue
    await db.execute(
        update(ToolManifest)
        .where(ToolManifest.id == settlement.tool_id)
        .values(total_revenue=ToolManifest.total_revenue + settlement.creator_pool)
    )
    
    await db.commit()
    
    logger.info(
        f"Settlement executed: run={settlement.tool_run_id}, "
        f"tool={settlement.tool_id}, total={settlement.total_revenue}, "
        f"shares={len(settlement.shares)}"
    )


async def settle_tool_run(
    db: AsyncSession,
    tool_id: UUID,
    total_credits: int,
    tool_run_id: Optional[UUID] = None,
) -> SettlementResult:
    """
    Convenience function: calculate and execute settlement in one call.
    """
    settlement = await calculate_settlement(db, tool_id, total_credits, tool_run_id)
    await execute_settlement(db, settlement)
    return settlement
