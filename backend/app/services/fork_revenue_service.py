"""Fork Revenue Settlement Service.

Complete production-level settlement service with:
- Settlement creation and status management
- Batch processing
- Individual payout tracking
- Dispute handling
- Rollback/reversal
- Audit trail
"""
import logging
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models_telemetry import ToolManifest, ToolRunEvent, ForkEvent
from app.models_settlement import (
    SettlementTransaction,
    SettlementPayout,
    SettlementDispute,
    SettlementStatus,
    PayoutStatus,
    ShareType,
    DisputeStatus,
)
from app.credit_service import get_or_create_user_credits, record_transaction

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

PLATFORM_FEE_RATE = Decimal("0.30")  # 30% platform fee
MAX_LINEAGE_DEPTH = 5               # Max ancestors for revenue share
MIN_PAYOUT_AMOUNT = 1               # Minimum credits per payout
MAX_RETRY_COUNT = 3                 # Max retries for failed settlements


# =============================================================================
# Settlement Calculation
# =============================================================================

def calculate_owner_share_rate(attribution_score: Optional[float]) -> Decimal:
    """
    Calculate fork owner's share rate based on attribution score.
    Higher attribution = more value added = higher owner share.
    """
    if attribution_score is None:
        return Decimal("1.0")  # Original tool gets 100%
    
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
) -> List[Tuple[ToolManifest, Optional[ForkEvent]]]:
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
    
    return list(reversed(lineage))


def calculate_payouts(
    creator_pool: int,
    lineage: List[Tuple[ToolManifest, Optional[ForkEvent]]],
) -> List[dict]:
    """
    Calculate payout distribution for all participants.
    
    Returns list of payout dicts with:
    - recipient_id, recipient_tool_id, amount, share_type, share_rate, lineage_position
    """
    if not lineage:
        return []
    
    payouts = []
    pool = Decimal(creator_pool)
    
    # Current tool (last in lineage)
    current_tool, current_fork = lineage[-1]
    
    if len(lineage) == 1 or current_fork is None:
        # Original tool - owner gets 100%
        payouts.append({
            "recipient_id": current_tool.created_by,
            "recipient_tool_id": current_tool.id,
            "recipient_tool_key": current_tool.tool_key,
            "amount": int(pool),
            "share_type": ShareType.OWNER.value,
            "share_rate": 1.0,
            "lineage_position": 0,
        })
    else:
        # Forked tool - attribution-based split
        attr_score = current_fork.attribution_score if current_fork else 50.0
        owner_rate = calculate_owner_share_rate(attr_score)
        owner_amount = (pool * owner_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        ancestor_pool = pool - owner_amount
        
        # Owner payout
        if int(owner_amount) >= MIN_PAYOUT_AMOUNT:
            payouts.append({
                "recipient_id": current_tool.created_by,
                "recipient_tool_id": current_tool.id,
                "recipient_tool_key": current_tool.tool_key,
                "amount": int(owner_amount),
                "share_type": ShareType.OWNER.value,
                "share_rate": float(owner_rate),
                "lineage_position": 0,
            })
        
        # Ancestor payouts (equal split)
        ancestors = lineage[:-1]
        if ancestors and ancestor_pool > 0:
            per_ancestor = (ancestor_pool / len(ancestors)).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
            remainder = int(ancestor_pool) - (int(per_ancestor) * len(ancestors))
            
            for i, (ancestor_tool, _) in enumerate(ancestors):
                ancestor_amount = int(per_ancestor)
                if i == 0:
                    ancestor_amount += remainder
                
                if ancestor_amount >= MIN_PAYOUT_AMOUNT:
                    payouts.append({
                        "recipient_id": ancestor_tool.created_by,
                        "recipient_tool_id": ancestor_tool.id,
                        "recipient_tool_key": ancestor_tool.tool_key,
                        "amount": ancestor_amount,
                        "share_type": ShareType.ANCESTOR.value,
                        "share_rate": float(Decimal(ancestor_amount) / pool),
                        "lineage_position": len(ancestors) - i,
                    })
    
    return payouts


# =============================================================================
# Settlement Creation
# =============================================================================

async def create_settlement(
    db: AsyncSession,
    tool_run_id: UUID,
    tool_id: UUID,
    tool_key: str,
    total_credits: int,
    payer_user_id: str,
) -> SettlementTransaction:
    """
    Create a new settlement transaction (PENDING status).
    
    This is the first step - actual processing happens separately.
    """
    # Calculate amounts
    total = Decimal(total_credits)
    platform_fee = int((total * PLATFORM_FEE_RATE).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    creator_pool = total_credits - platform_fee
    
    # Get lineage info
    lineage = await get_tool_lineage(db, tool_id)
    lineage_depth = len(lineage)
    
    # Get attribution score (for forked tools)
    attribution_score = None
    if lineage:
        _, current_fork = lineage[-1]
        if current_fork:
            attribution_score = current_fork.attribution_score
    
    # Create settlement transaction
    settlement = SettlementTransaction(
        id=uuid4(),
        tool_run_id=tool_run_id,
        tool_id=tool_id,
        tool_key=tool_key,
        status=SettlementStatus.PENDING.value,
        total_credits=total_credits,
        platform_fee=platform_fee,
        creator_pool=creator_pool,
        lineage_depth=lineage_depth,
        attribution_score=attribution_score,
        payer_user_id=payer_user_id,
        created_at=datetime.utcnow(),
    )
    
    # Calculate and create payout records
    payout_data = calculate_payouts(creator_pool, lineage)
    for pd in payout_data:
        payout = SettlementPayout(
            id=uuid4(),
            settlement_id=settlement.id,
            recipient_id=pd["recipient_id"],
            recipient_tool_id=pd["recipient_tool_id"],
            recipient_tool_key=pd["recipient_tool_key"],
            amount=pd["amount"],
            share_type=pd["share_type"],
            share_rate=pd["share_rate"],
            lineage_position=pd["lineage_position"],
            status=PayoutStatus.PENDING.value,
            created_at=datetime.utcnow(),
        )
        db.add(payout)
    
    db.add(settlement)
    await db.commit()
    await db.refresh(settlement)
    
    logger.info(
        f"Settlement created: id={settlement.id}, tool={tool_key}, "
        f"total={total_credits}, payouts={len(payout_data)}"
    )
    
    return settlement


# =============================================================================
# Settlement Processing
# =============================================================================

async def process_settlement(
    db: AsyncSession,
    settlement_id: UUID,
    processed_by: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Process a pending settlement - credit all recipients.
    
    Returns: (success, error_message)
    """
    # Load settlement with payouts
    result = await db.execute(
        select(SettlementTransaction)
        .options(selectinload(SettlementTransaction.payouts))
        .where(SettlementTransaction.id == settlement_id)
    )
    settlement = result.scalars().first()
    
    if not settlement:
        return False, "Settlement not found"
    
    if settlement.status != SettlementStatus.PENDING.value:
        return False, f"Invalid status: {settlement.status}"
    
    # Mark as processing
    settlement.status = SettlementStatus.PROCESSING.value
    settlement.processed_at = datetime.utcnow()
    settlement.processed_by = processed_by
    await db.commit()
    
    # Process each payout
    failed_payouts = []
    for payout in settlement.payouts:
        try:
            # Get or create user credits
            user_credits = await get_or_create_user_credits(db, payout.recipient_id, seed_balance=0)
            
            # Add credits
            user_credits.topup_credits += payout.amount
            user_credits.balance += payout.amount
            
            # Record transaction
            ledger = await record_transaction(
                db=db,
                user_id=payout.recipient_id,
                event_type="revenue_share",
                amount=payout.amount,
                new_balance=user_credits.balance,
                description=f"Tool revenue: {payout.share_type}",
                capsule_run_id=settlement.tool_run_id,
                meta={
                    "settlement_id": str(settlement.id),
                    "tool_id": str(payout.recipient_tool_id) if payout.recipient_tool_id else None,
                    "tool_key": payout.recipient_tool_key,
                    "share_type": payout.share_type,
                    "share_rate": payout.share_rate,
                    "lineage_position": payout.lineage_position,
                },
            )
            
            # Update payout status
            payout.status = PayoutStatus.CREDITED.value
            payout.credited_at = datetime.utcnow()
            payout.ledger_entry_id = ledger.id
            
        except Exception as e:
            logger.error(f"Payout failed: payout_id={payout.id}, error={e}")
            payout.status = PayoutStatus.FAILED.value
            payout.error_message = str(e)
            failed_payouts.append(payout.id)
    
    # Update fork revenue tracking
    if settlement.tool_id:
        fork_result = await db.execute(
            select(ForkEvent).where(ForkEvent.child_tool_id == settlement.tool_id)
        )
        fork = fork_result.scalars().first()
        if fork:
            owner_payout = next(
                (p for p in settlement.payouts if p.share_type == ShareType.OWNER.value),
                None
            )
            if owner_payout:
                fork.revenue_generated += owner_payout.amount
                fork.revenue_shared += settlement.creator_pool - owner_payout.amount
        
        # Update tool total revenue
        await db.execute(
            update(ToolManifest)
            .where(ToolManifest.id == settlement.tool_id)
            .values(total_revenue=ToolManifest.total_revenue + settlement.creator_pool)
        )
    
    # Finalize settlement status
    if failed_payouts:
        settlement.status = SettlementStatus.FAILED.value
        settlement.error_message = f"Failed payouts: {failed_payouts}"
        settlement.retry_count += 1
        await db.commit()
        return False, settlement.error_message
    else:
        settlement.status = SettlementStatus.COMPLETED.value
        settlement.completed_at = datetime.utcnow()
        await db.commit()
        
        logger.info(f"Settlement completed: id={settlement.id}")
        return True, None


async def process_batch_settlements(
    db: AsyncSession,
    limit: int = 100,
    processed_by: Optional[str] = None,
) -> dict:
    """
    Process multiple pending settlements in batch.
    """
    # Get pending settlements
    result = await db.execute(
        select(SettlementTransaction)
        .where(SettlementTransaction.status == SettlementStatus.PENDING.value)
        .where(SettlementTransaction.retry_count < MAX_RETRY_COUNT)
        .order_by(SettlementTransaction.created_at)
        .limit(limit)
    )
    settlements = result.scalars().all()
    
    results = {
        "processed": 0,
        "succeeded": 0,
        "failed": 0,
        "errors": [],
    }
    
    for settlement in settlements:
        success, error = await process_settlement(db, settlement.id, processed_by)
        results["processed"] += 1
        if success:
            results["succeeded"] += 1
        else:
            results["failed"] += 1
            results["errors"].append({
                "settlement_id": str(settlement.id),
                "error": error,
            })
    
    logger.info(f"Batch settlement: {results['processed']} processed, {results['succeeded']} succeeded")
    return results


# =============================================================================
# Settlement Rollback
# =============================================================================

async def rollback_settlement(
    db: AsyncSession,
    settlement_id: UUID,
    reason: str,
    rolled_back_by: str,
) -> Tuple[bool, Optional[str]]:
    """
    Rollback a completed settlement by reversing all payouts.
    """
    # Load settlement
    result = await db.execute(
        select(SettlementTransaction)
        .options(selectinload(SettlementTransaction.payouts))
        .where(SettlementTransaction.id == settlement_id)
    )
    settlement = result.scalars().first()
    
    if not settlement:
        return False, "Settlement not found"
    
    if settlement.status not in [SettlementStatus.COMPLETED.value, SettlementStatus.FAILED.value]:
        return False, f"Cannot rollback status: {settlement.status}"
    
    # Reverse each credited payout
    reversed_count = 0
    for payout in settlement.payouts:
        if payout.status == PayoutStatus.CREDITED.value:
            try:
                # Deduct credits
                user_credits = await get_or_create_user_credits(db, payout.recipient_id, seed_balance=0)
                user_credits.topup_credits = max(0, user_credits.topup_credits - payout.amount)
                user_credits.balance = max(0, user_credits.balance - payout.amount)
                
                # Record reversal
                await record_transaction(
                    db=db,
                    user_id=payout.recipient_id,
                    event_type="revenue_reversal",
                    amount=-payout.amount,
                    new_balance=user_credits.balance,
                    description=f"Settlement rollback: {reason}",
                    meta={
                        "settlement_id": str(settlement.id),
                        "original_payout_id": str(payout.id),
                        "rollback_reason": reason,
                    },
                )
                
                payout.status = PayoutStatus.REVERSED.value
                reversed_count += 1
                
            except Exception as e:
                logger.error(f"Rollback failed for payout {payout.id}: {e}")
    
    # Update settlement status
    settlement.status = SettlementStatus.REVERSED.value
    settlement.meta = {
        **settlement.meta,
        "rollback_reason": reason,
        "rolled_back_by": rolled_back_by,
        "rolled_back_at": datetime.utcnow().isoformat(),
        "reversed_payouts": reversed_count,
    }
    
    # Reverse fork revenue
    if settlement.tool_id:
        fork_result = await db.execute(
            select(ForkEvent).where(ForkEvent.child_tool_id == settlement.tool_id)
        )
        fork = fork_result.scalars().first()
        if fork:
            fork.revenue_generated = max(0, fork.revenue_generated - settlement.creator_pool)
        
        # Reverse tool revenue
        await db.execute(
            update(ToolManifest)
            .where(ToolManifest.id == settlement.tool_id)
            .values(total_revenue=func.greatest(0, ToolManifest.total_revenue - settlement.creator_pool))
        )
    
    await db.commit()
    logger.info(f"Settlement rolled back: id={settlement.id}, reversed={reversed_count}")
    
    return True, None


# =============================================================================
# Dispute Management
# =============================================================================

async def create_dispute(
    db: AsyncSession,
    settlement_id: UUID,
    complainant_id: str,
    reason: str,
    expected_amount: Optional[int] = None,
    evidence: Optional[dict] = None,
) -> SettlementDispute:
    """
    Create a dispute for a settlement.
    """
    # Verify settlement exists
    settlement = await db.get(SettlementTransaction, settlement_id)
    if not settlement:
        raise ValueError("Settlement not found")
    
    # Mark settlement as disputed
    settlement.status = SettlementStatus.DISPUTED.value
    
    dispute = SettlementDispute(
        id=uuid4(),
        settlement_id=settlement_id,
        complainant_id=complainant_id,
        reason=reason,
        expected_amount=expected_amount,
        evidence=evidence or {},
        status=DisputeStatus.OPEN.value,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(dispute)
    await db.commit()
    await db.refresh(dispute)
    
    logger.info(f"Dispute created: id={dispute.id}, settlement={settlement_id}")
    return dispute


async def resolve_dispute(
    db: AsyncSession,
    dispute_id: UUID,
    resolution: str,
    status: DisputeStatus,
    adjustment_amount: Optional[int],
    resolved_by: str,
) -> SettlementDispute:
    """
    Resolve a dispute.
    """
    dispute = await db.get(SettlementDispute, dispute_id)
    if not dispute:
        raise ValueError("Dispute not found")
    
    dispute.status = status.value
    dispute.resolution = resolution
    dispute.adjustment_amount = adjustment_amount
    dispute.resolved_by = resolved_by
    dispute.resolved_at = datetime.utcnow()
    dispute.updated_at = datetime.utcnow()
    
    # If resolved/rejected, update settlement status back
    settlement = await db.get(SettlementTransaction, dispute.settlement_id)
    if settlement and settlement.status == SettlementStatus.DISPUTED.value:
        # Check for other open disputes
        open_disputes = await db.execute(
            select(func.count(SettlementDispute.id))
            .where(SettlementDispute.settlement_id == settlement.id)
            .where(SettlementDispute.status.in_([DisputeStatus.OPEN.value, DisputeStatus.INVESTIGATING.value]))
        )
        if open_disputes.scalar() == 0:
            settlement.status = SettlementStatus.COMPLETED.value
    
    await db.commit()
    await db.refresh(dispute)
    
    logger.info(f"Dispute resolved: id={dispute_id}, status={status.value}")
    return dispute


# =============================================================================
# Query Functions
# =============================================================================

async def get_user_settlements(
    db: AsyncSession,
    user_id: str,
    status: Optional[SettlementStatus] = None,
    days: int = 30,
    limit: int = 50,
) -> List[SettlementPayout]:
    """
    Get all payouts for a user.
    """
    since = datetime.utcnow() - timedelta(days=days)
    
    query = (
        select(SettlementPayout)
        .join(SettlementTransaction)
        .where(SettlementPayout.recipient_id == user_id)
        .where(SettlementPayout.created_at >= since)
    )
    
    if status:
        query = query.where(SettlementTransaction.status == status.value)
    
    query = query.order_by(SettlementPayout.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_user_settlement_summary(
    db: AsyncSession,
    user_id: str,
    days: int = 30,
) -> dict:
    """
    Get settlement summary for a user.
    """
    since = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(
            func.count(SettlementPayout.id).label("total_payouts"),
            func.sum(SettlementPayout.amount).label("total_amount"),
            func.avg(SettlementPayout.amount).label("avg_amount"),
        )
        .join(SettlementTransaction)
        .where(SettlementPayout.recipient_id == user_id)
        .where(SettlementPayout.status == PayoutStatus.CREDITED.value)
        .where(SettlementPayout.created_at >= since)
    )
    row = result.one()
    
    # Pending payouts
    pending_result = await db.execute(
        select(func.sum(SettlementPayout.amount))
        .where(SettlementPayout.recipient_id == user_id)
        .where(SettlementPayout.status == PayoutStatus.PENDING.value)
    )
    pending_amount = pending_result.scalar() or 0
    
    return {
        "period_days": days,
        "total_payouts": row.total_payouts or 0,
        "total_earned": row.total_amount or 0,
        "avg_per_payout": round(float(row.avg_amount or 0), 2),
        "pending_amount": pending_amount,
    }


async def get_settlement_details(
    db: AsyncSession,
    settlement_id: UUID,
) -> Optional[SettlementTransaction]:
    """
    Get full settlement details with payouts and disputes.
    """
    result = await db.execute(
        select(SettlementTransaction)
        .options(
            selectinload(SettlementTransaction.payouts),
            selectinload(SettlementTransaction.disputes),
        )
        .where(SettlementTransaction.id == settlement_id)
    )
    return result.scalars().first()


async def get_pending_settlements_count(db: AsyncSession) -> int:
    """Get count of pending settlements."""
    result = await db.execute(
        select(func.count(SettlementTransaction.id))
        .where(SettlementTransaction.status == SettlementStatus.PENDING.value)
    )
    return result.scalar() or 0


async def get_open_disputes_count(db: AsyncSession) -> int:
    """Get count of open disputes."""
    result = await db.execute(
        select(func.count(SettlementDispute.id))
        .where(SettlementDispute.status.in_([
            DisputeStatus.OPEN.value,
            DisputeStatus.INVESTIGATING.value,
        ]))
    )
    return result.scalar() or 0
