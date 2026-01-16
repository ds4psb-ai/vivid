"""
Feature Flag API Router (2026 Best Practice)

Admin endpoints for managing feature flags.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.features.flags import get_feature_flags, FeatureFlagService
from app.features.models import FeatureFlag, FeatureFlagAudit, FlagStatus
from app.features.schemas import (
    FeatureFlagCreate,
    FeatureFlagUpdate,
    FeatureFlagResponse,
    FeatureFlagEvaluation,
    FeatureContext,
    BulkEvaluationRequest,
    BulkEvaluationResponse,
)

router = APIRouter(prefix="/api/v1/features", tags=["feature-flags"])


# =============================================================================
# Evaluation Endpoints (High traffic)
# =============================================================================

@router.post("/evaluate/{flag_key}", response_model=FeatureFlagEvaluation)
async def evaluate_flag(
    flag_key: str,
    context: Optional[FeatureContext] = None,
    db: AsyncSession = Depends(get_db),
    flags: FeatureFlagService = Depends(get_feature_flags),
):
    """
    Evaluate a single feature flag.

    Returns whether the flag is enabled and which variant applies.
    """
    return await flags.evaluate(flag_key, context, db)


@router.post("/evaluate", response_model=BulkEvaluationResponse)
async def evaluate_flags_bulk(
    request: BulkEvaluationRequest,
    db: AsyncSession = Depends(get_db),
    flags: FeatureFlagService = Depends(get_feature_flags),
):
    """
    Evaluate multiple feature flags at once.

    More efficient than making multiple single evaluate calls.
    """
    import time
    start = time.perf_counter()

    evaluations = await flags.bulk_evaluate(
        request.flag_keys,
        request.context,
        db,
    )

    return BulkEvaluationResponse(
        evaluations=evaluations,
        evaluation_time_ms=(time.perf_counter() - start) * 1000,
    )


@router.get("/check/{flag_key}")
async def check_flag_enabled(
    flag_key: str,
    user_id: Optional[str] = Query(default=None),
    environment: str = Query(default="production"),
    db: AsyncSession = Depends(get_db),
    flags: FeatureFlagService = Depends(get_feature_flags),
) -> dict:
    """
    Quick check if a flag is enabled.

    Simple GET endpoint for easy integration.
    """
    context = FeatureContext(
        user_id=user_id,
        environment=environment,
    )
    enabled = await flags.is_enabled(flag_key, context, db)
    return {"flag_key": flag_key, "enabled": enabled}


# =============================================================================
# Admin CRUD Endpoints
# =============================================================================

@router.get("/flags", response_model=list[FeatureFlagResponse])
async def list_flags(
    status: Optional[FlagStatus] = Query(default=None),
    tag: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0),
    db: AsyncSession = Depends(get_db),
):
    """List all feature flags with optional filtering."""
    query = select(FeatureFlag).order_by(FeatureFlag.updated_at.desc())

    if status:
        query = query.where(FeatureFlag.status == status)

    if tag:
        # JSON array contains check
        query = query.where(FeatureFlag.tags.contains([tag]))

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    flags = result.scalars().all()

    return [FeatureFlagResponse.model_validate(f) for f in flags]


@router.get("/flags/{flag_key}", response_model=FeatureFlagResponse)
async def get_flag(
    flag_key: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific feature flag by key."""
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.flag_key == flag_key)
    )
    flag = result.scalar_one_or_none()

    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    return FeatureFlagResponse.model_validate(flag)


@router.post("/flags", response_model=FeatureFlagResponse, status_code=201)
async def create_flag(
    request: FeatureFlagCreate,
    db: AsyncSession = Depends(get_db),
    flags: FeatureFlagService = Depends(get_feature_flags),
):
    """Create a new feature flag."""
    # Check if flag already exists
    existing = await db.execute(
        select(FeatureFlag).where(FeatureFlag.flag_key == request.flag_key)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Flag already exists")

    # Create flag
    flag = FeatureFlag(
        flag_key=request.flag_key,
        name=request.name,
        description=request.description,
        enabled=request.enabled,
        strategies=request.strategies.model_dump() if request.strategies else {},
        variants=[v.model_dump() for v in request.variants] if request.variants else [],
        default_variant=request.default_variant,
        tags=request.tags,
        owner=request.owner,
    )
    db.add(flag)

    # Create audit log
    audit = FeatureFlagAudit(
        flag_id=0,  # Will be set after flush
        flag_key=request.flag_key,
        action="created",
        new_state=flag.__dict__.copy(),
    )

    await db.flush()
    audit.flag_id = flag.id
    db.add(audit)

    await db.commit()
    await db.refresh(flag)

    return FeatureFlagResponse.model_validate(flag)


@router.patch("/flags/{flag_key}", response_model=FeatureFlagResponse)
async def update_flag(
    flag_key: str,
    request: FeatureFlagUpdate,
    db: AsyncSession = Depends(get_db),
    flags: FeatureFlagService = Depends(get_feature_flags),
):
    """Update a feature flag."""
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.flag_key == flag_key)
    )
    flag = result.scalar_one_or_none()

    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    # Store previous state for audit
    previous_state = {
        "enabled": flag.enabled,
        "strategies": flag.strategies,
        "variants": flag.variants,
    }

    # Apply updates
    if request.name is not None:
        flag.name = request.name
    if request.description is not None:
        flag.description = request.description
    if request.enabled is not None:
        flag.enabled = request.enabled
    if request.strategies is not None:
        flag.strategies = request.strategies.model_dump()
    if request.variants is not None:
        flag.variants = [v.model_dump() for v in request.variants]
    if request.default_variant is not None:
        flag.default_variant = request.default_variant
    if request.tags is not None:
        flag.tags = request.tags
    if request.owner is not None:
        flag.owner = request.owner

    flag.updated_at = datetime.utcnow()

    # Create audit log
    audit = FeatureFlagAudit(
        flag_id=flag.id,
        flag_key=flag_key,
        action="updated",
        previous_state=previous_state,
        new_state={
            "enabled": flag.enabled,
            "strategies": flag.strategies,
            "variants": flag.variants,
        },
        reason=request.reason,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(flag)

    # Invalidate cache
    await flags.invalidate_cache(flag_key)

    return FeatureFlagResponse.model_validate(flag)


@router.post("/flags/{flag_key}/enable")
async def enable_flag(
    flag_key: str,
    reason: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    flags: FeatureFlagService = Depends(get_feature_flags),
):
    """Quick enable a feature flag."""
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.flag_key == flag_key)
    )
    flag = result.scalar_one_or_none()

    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    flag.enabled = True
    flag.updated_at = datetime.utcnow()

    audit = FeatureFlagAudit(
        flag_id=flag.id,
        flag_key=flag_key,
        action="enabled",
        previous_state={"enabled": False},
        new_state={"enabled": True},
        reason=reason,
    )
    db.add(audit)

    await db.commit()
    await flags.invalidate_cache(flag_key)

    return {"status": "enabled", "flag_key": flag_key}


@router.post("/flags/{flag_key}/disable")
async def disable_flag(
    flag_key: str,
    reason: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    flags: FeatureFlagService = Depends(get_feature_flags),
):
    """
    Quick disable a feature flag (Kill Switch).

    2026 Best Practice: Emergency kill switch for production incidents.
    """
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.flag_key == flag_key)
    )
    flag = result.scalar_one_or_none()

    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    flag.enabled = False
    flag.updated_at = datetime.utcnow()

    audit = FeatureFlagAudit(
        flag_id=flag.id,
        flag_key=flag_key,
        action="disabled",
        previous_state={"enabled": True},
        new_state={"enabled": False},
        reason=reason or "Kill switch activated",
    )
    db.add(audit)

    await db.commit()
    await flags.invalidate_cache(flag_key)

    return {"status": "disabled", "flag_key": flag_key}


@router.delete("/flags/{flag_key}")
async def archive_flag(
    flag_key: str,
    db: AsyncSession = Depends(get_db),
    flags: FeatureFlagService = Depends(get_feature_flags),
):
    """Archive (soft delete) a feature flag."""
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.flag_key == flag_key)
    )
    flag = result.scalar_one_or_none()

    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    flag.status = FlagStatus.ARCHIVED
    flag.enabled = False
    flag.updated_at = datetime.utcnow()

    audit = FeatureFlagAudit(
        flag_id=flag.id,
        flag_key=flag_key,
        action="archived",
    )
    db.add(audit)

    await db.commit()
    await flags.invalidate_cache(flag_key)

    return {"status": "archived", "flag_key": flag_key}


# =============================================================================
# Audit Endpoints
# =============================================================================

@router.get("/flags/{flag_key}/audit")
async def get_flag_audit_log(
    flag_key: str,
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get audit log for a specific flag."""
    result = await db.execute(
        select(FeatureFlagAudit)
        .where(FeatureFlagAudit.flag_key == flag_key)
        .order_by(FeatureFlagAudit.changed_at.desc())
        .limit(limit)
    )
    audits = result.scalars().all()

    return [
        {
            "action": a.action,
            "changed_by": a.changed_by,
            "changed_at": a.changed_at.isoformat(),
            "previous_state": a.previous_state,
            "new_state": a.new_state,
            "reason": a.reason,
        }
        for a in audits
    ]


# =============================================================================
# Cache Management
# =============================================================================

@router.post("/cache/invalidate/{flag_key}")
async def invalidate_flag_cache(
    flag_key: str,
    flags: FeatureFlagService = Depends(get_feature_flags),
):
    """Invalidate cache for a specific flag."""
    await flags.invalidate_cache(flag_key)
    return {"status": "invalidated", "flag_key": flag_key}


@router.post("/cache/invalidate-all")
async def invalidate_all_caches(
    flags: FeatureFlagService = Depends(get_feature_flags),
):
    """Invalidate all flag caches."""
    await flags.invalidate_all_caches()
    return {"status": "all_caches_invalidated"}
