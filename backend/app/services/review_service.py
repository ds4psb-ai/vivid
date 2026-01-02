"""Review and Approval Service.

Handles:
- Review creation and workflow
- Automated checks (safety, quality, sybil)
- Tier promotion logic
- Review queue management
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_telemetry import ToolManifest, ToolTier
from app.models_versioning import ToolVersion, VersionStatus
from app.models_review import (
    ToolReview,
    ReviewCheckResult,
    TierPromotion,
    ReviewStatus,
    ReviewType,
    CheckCategory,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Tier Promotion Rules
# =============================================================================

TIER_PROMOTION_RULES = {
    # experimental -> verified
    "experimental_to_verified": {
        "min_usage_count": 50,
        "min_quality_rating": 3.5,
        "min_test_pass_rate": 0.9,
        "max_error_rate": 0.1,
        "min_unique_users": 5,
        "requires_safety_review": True,
    },
    # verified -> certified
    "verified_to_certified": {
        "min_usage_count": 500,
        "min_quality_rating": 4.0,
        "min_test_pass_rate": 0.95,
        "max_error_rate": 0.05,
        "min_unique_users": 25,
        "min_revenue_generated": 100,
        "requires_safety_review": True,
        "requires_security_audit": True,
    },
}


# =============================================================================
# Automated Checks
# =============================================================================

async def run_automated_checks(
    db: AsyncSession,
    review_id: UUID,
    tool: ToolManifest,
    version: Optional[ToolVersion] = None,
) -> Tuple[bool, float, List[ReviewCheckResult]]:
    """
    Run automated checks on a tool/version.
    
    Returns: (all_passed, total_score, check_results)
    """
    results = []
    
    # 1. Sybil Detection Check
    sybil_check = ReviewCheckResult(
        id=uuid4(),
        review_id=review_id,
        category=CheckCategory.SYBIL.value,
        check_name="sybil_detection",
        description="Check for trivial fork / self-fork patterns",
        is_automated=True,
        created_at=datetime.utcnow(),
    )
    
    # Check fork event if exists
    from app.models_versioning import ToolDiff
    diff_result = await db.execute(
        select(ToolDiff)
        .join(ToolVersion, ToolDiff.forked_version_id == ToolVersion.id)
        .where(ToolVersion.tool_id == tool.id)
        .order_by(ToolDiff.created_at.desc())
        .limit(1)
    )
    tool_diff = diff_result.scalars().first()
    
    if tool_diff:
        sybil_check.passed = not tool_diff.is_trivial_change
        sybil_check.score = 100 - tool_diff.similarity_ratio * 100
        sybil_check.details = {
            "similarity_ratio": tool_diff.similarity_ratio,
            "diff_score": tool_diff.diff_score,
            "is_trivial": tool_diff.is_trivial_change,
        }
        if tool_diff.is_trivial_change:
            sybil_check.error_message = "Trivial changes detected - possible Sybil attack"
    else:
        sybil_check.passed = True
        sybil_check.score = 100
        sybil_check.details = {"note": "No fork diff found - original tool"}
    
    sybil_check.checked_at = datetime.utcnow()
    results.append(sybil_check)
    
    # 2. Code Quality Check
    quality_check = ReviewCheckResult(
        id=uuid4(),
        review_id=review_id,
        category=CheckCategory.QUALITY.value,
        check_name="code_quality",
        description="Basic code quality validation",
        is_automated=True,
        created_at=datetime.utcnow(),
    )
    
    if version and version.code_content:
        code = version.code_content
        code_length = len(code)
        has_comments = "#" in code or "// " in code or "/*" in code
        
        quality_check.passed = code_length >= 50 and has_comments
        quality_check.score = min(100, (code_length / 10) + (50 if has_comments else 0))
        quality_check.details = {
            "code_length": code_length,
            "has_comments": has_comments,
        }
        if not quality_check.passed:
            quality_check.error_message = "Code too short or missing comments"
    else:
        quality_check.passed = False
        quality_check.score = 0
        quality_check.error_message = "No code content found"
    
    quality_check.checked_at = datetime.utcnow()
    results.append(quality_check)
    
    # 3. Safety Check (basic)
    safety_check = ReviewCheckResult(
        id=uuid4(),
        review_id=review_id,
        category=CheckCategory.SAFETY.value,
        check_name="safety_keywords",
        description="Check for dangerous patterns",
        is_automated=True,
        created_at=datetime.utcnow(),
    )
    
    dangerous_patterns = ["os.system", "subprocess", "eval(", "exec(", "__import__"]
    
    if version and version.code_content:
        found_patterns = [p for p in dangerous_patterns if p in version.code_content]
        safety_check.passed = len(found_patterns) == 0
        safety_check.score = 100 if safety_check.passed else 0
        safety_check.details = {"found_patterns": found_patterns}
        if found_patterns:
            safety_check.error_message = f"Dangerous patterns found: {', '.join(found_patterns)}"
    else:
        safety_check.passed = True
        safety_check.score = 100
    
    safety_check.checked_at = datetime.utcnow()
    results.append(safety_check)
    
    # 4. Performance Check (placeholder)
    perf_check = ReviewCheckResult(
        id=uuid4(),
        review_id=review_id,
        category=CheckCategory.PERFORMANCE.value,
        check_name="performance_estimate",
        description="Estimated performance characteristics",
        is_automated=True,
        passed=True,
        score=80,
        details={"note": "Performance check requires runtime data"},
        created_at=datetime.utcnow(),
        checked_at=datetime.utcnow(),
    )
    results.append(perf_check)
    
    # Calculate totals
    total_weight = sum(r.weight for r in results)
    total_score = sum(r.score * r.weight for r in results) / total_weight if total_weight > 0 else 0
    all_passed = all(r.passed for r in results)
    
    # Save all results
    for result in results:
        db.add(result)
    
    await db.commit()
    
    return all_passed, total_score, results


# =============================================================================
# Review Management
# =============================================================================

async def create_review(
    db: AsyncSession,
    tool_id: UUID,
    version_id: Optional[UUID],
    review_type: str,
    submitted_by: str,
    notes: Optional[str] = None,
    priority: int = 0,
) -> ToolReview:
    """Create a review request."""
    review = ToolReview(
        id=uuid4(),
        tool_id=tool_id,
        version_id=version_id,
        review_type=review_type,
        status=ReviewStatus.PENDING.value,
        priority=priority,
        submitted_by=submitted_by,
        submission_notes=notes,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(review)
    await db.commit()
    await db.refresh(review)
    
    # Run automated checks
    tool = await db.get(ToolManifest, tool_id)
    version = await db.get(ToolVersion, version_id) if version_id else None
    
    all_passed, score, _ = await run_automated_checks(db, review.id, tool, version)
    
    # Update review with check results
    review.auto_checks_passed = all_passed
    review.auto_checks_score = score
    await db.commit()
    
    logger.info(f"Review created: {review.id}, auto_passed={all_passed}, score={score:.1f}")
    return review


async def assign_review(
    db: AsyncSession,
    review_id: UUID,
    reviewer_id: str,
) -> ToolReview:
    """Assign a reviewer to a review."""
    review = await db.get(ToolReview, review_id)
    if not review:
        raise ValueError("Review not found")
    
    review.assigned_to = reviewer_id
    review.assigned_at = datetime.utcnow()
    review.status = ReviewStatus.IN_PROGRESS.value
    review.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(review)
    return review


async def approve_review(
    db: AsyncSession,
    review_id: UUID,
    approver_id: str,
    notes: Optional[str] = None,
) -> ToolReview:
    """Approve a review and activate the tool/version."""
    review = await db.get(ToolReview, review_id)
    if not review:
        raise ValueError("Review not found")
    
    review.status = ReviewStatus.APPROVED.value
    review.decision_by = approver_id
    review.decision_at = datetime.utcnow()
    review.decision_notes = notes
    review.updated_at = datetime.utcnow()
    
    # Activate the tool
    tool = await db.get(ToolManifest, review.tool_id)
    if tool:
        tool.is_active = True
        tool.updated_at = datetime.utcnow()
    
    # Activate the version
    if review.version_id:
        version = await db.get(ToolVersion, review.version_id)
        if version:
            # Demote old live version
            await db.execute(
                update(ToolVersion)
                .where(ToolVersion.tool_id == review.tool_id)
                .where(ToolVersion.is_live == True)
                .values(is_live=False, status=VersionStatus.DEPRECATED.value)
            )
            
            version.status = VersionStatus.APPROVED.value
            version.is_live = True
            version.reviewed_by = approver_id
            version.reviewed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(review)
    
    logger.info(f"Review approved: {review_id} by {approver_id}")
    return review


async def reject_review(
    db: AsyncSession,
    review_id: UUID,
    rejector_id: str,
    reason: str,
    notes: Optional[str] = None,
) -> ToolReview:
    """Reject a review."""
    review = await db.get(ToolReview, review_id)
    if not review:
        raise ValueError("Review not found")
    
    review.status = ReviewStatus.REJECTED.value
    review.decision_by = rejector_id
    review.decision_at = datetime.utcnow()
    review.decision_notes = notes
    review.rejection_reason = reason
    review.updated_at = datetime.utcnow()
    
    # Mark version as rejected
    if review.version_id:
        version = await db.get(ToolVersion, review.version_id)
        if version:
            version.status = VersionStatus.REJECTED.value
            version.review_notes = reason
    
    await db.commit()
    await db.refresh(review)
    
    logger.info(f"Review rejected: {review_id} by {rejector_id}")
    return review


# =============================================================================
# Tier Promotion
# =============================================================================

async def check_tier_eligibility(
    db: AsyncSession,
    tool_id: UUID,
) -> dict:
    """Check if a tool is eligible for tier promotion."""
    tool = await db.get(ToolManifest, tool_id)
    if not tool:
        raise ValueError("Tool not found")
    
    current_tier = tool.tier
    
    # Determine target tier
    if current_tier == ToolTier.EXPERIMENTAL.value:
        target_tier = ToolTier.VERIFIED.value
        rules = TIER_PROMOTION_RULES["experimental_to_verified"]
    elif current_tier == ToolTier.VERIFIED.value:
        target_tier = ToolTier.CERTIFIED.value
        rules = TIER_PROMOTION_RULES["verified_to_certified"]
    else:
        return {"eligible": False, "reason": "Already at highest tier"}
    
    # Check metrics
    checks = {}
    all_passed = True
    
    # Usage count
    checks["usage_count"] = {
        "required": rules["min_usage_count"],
        "actual": tool.usage_count,
        "passed": tool.usage_count >= rules["min_usage_count"],
    }
    all_passed = all_passed and checks["usage_count"]["passed"]
    
    # Quality rating
    checks["quality_rating"] = {
        "required": rules["min_quality_rating"],
        "actual": tool.quality_rating or 0,
        "passed": (tool.quality_rating or 0) >= rules["min_quality_rating"],
    }
    all_passed = all_passed and checks["quality_rating"]["passed"]
    
    return {
        "eligible": all_passed,
        "current_tier": current_tier,
        "target_tier": target_tier,
        "checks": checks,
        "requires_review": rules.get("requires_safety_review", False),
    }


async def promote_tier(
    db: AsyncSession,
    tool_id: UUID,
    to_tier: str,
    decided_by: str,
    reason: Optional[str] = None,
    review_id: Optional[UUID] = None,
) -> TierPromotion:
    """Promote a tool to a new tier."""
    tool = await db.get(ToolManifest, tool_id)
    if not tool:
        raise ValueError("Tool not found")
    
    from_tier = tool.tier
    
    # Create promotion record
    promotion = TierPromotion(
        id=uuid4(),
        tool_id=tool_id,
        from_tier=from_tier,
        to_tier=to_tier,
        promotion_type="automatic" if not review_id else "manual",
        decided_by=decided_by,
        reason=reason,
        metrics_snapshot={
            "usage_count": tool.usage_count,
            "quality_rating": tool.quality_rating,
            "fork_count": tool.fork_count,
            "total_revenue": tool.total_revenue,
        },
        review_id=review_id,
        created_at=datetime.utcnow(),
    )
    db.add(promotion)
    
    # Update tool tier
    tool.tier = to_tier
    tool.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(promotion)
    
    logger.info(f"Tool {tool_id} promoted: {from_tier} -> {to_tier}")
    return promotion


# =============================================================================
# Review Queue
# =============================================================================

async def get_pending_reviews(
    db: AsyncSession,
    limit: int = 50,
    review_type: Optional[str] = None,
) -> List[ToolReview]:
    """Get pending reviews ordered by priority."""
    query = (
        select(ToolReview)
        .where(ToolReview.status == ReviewStatus.PENDING.value)
    )
    
    if review_type:
        query = query.where(ToolReview.review_type == review_type)
    
    query = query.order_by(
        ToolReview.priority.desc(),
        ToolReview.created_at.asc()
    ).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_review_stats(db: AsyncSession) -> dict:
    """Get review queue statistics."""
    # Pending count
    pending = await db.execute(
        select(func.count()).where(ToolReview.status == ReviewStatus.PENDING.value)
    )
    
    # In-progress count
    in_progress = await db.execute(
        select(func.count()).where(ToolReview.status == ReviewStatus.IN_PROGRESS.value)
    )
    
    # Today's decisions
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    decided_today = await db.execute(
        select(func.count()).where(
            and_(
                ToolReview.decision_at >= today,
                ToolReview.status.in_([ReviewStatus.APPROVED.value, ReviewStatus.REJECTED.value])
            )
        )
    )
    
    # Average auto-check score for pending
    avg_score = await db.execute(
        select(func.avg(ToolReview.auto_checks_score))
        .where(ToolReview.status == ReviewStatus.PENDING.value)
    )
    
    return {
        "pending_count": pending.scalar() or 0,
        "in_progress_count": in_progress.scalar() or 0,
        "decided_today": decided_today.scalar() or 0,
        "avg_auto_score": round(avg_score.scalar() or 0, 1),
    }
