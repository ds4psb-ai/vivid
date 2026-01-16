"""
A/B Testing API Router (2026 Best Practice)

Endpoints for experiment management, assignment, and analysis.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.experiments.ab_testing import get_ab_testing, ABTestingService
from app.experiments.models import (
    Experiment,
    ExperimentVariant,
    ExperimentStatus,
    ExperimentExposure,
    ExperimentResult,
)
from app.experiments.schemas import (
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentResponse,
    VariantConfig,
    AssignmentContext,
    AssignmentResponse,
    BulkAssignmentRequest,
    BulkAssignmentResponse,
    ConversionEvent,
    ExperimentResults,
    VariantResult,
    SampleSizeCalculation,
    SampleSizeResponse,
)
from app.experiments.statistics import get_statistical_analyzer

router = APIRouter(prefix="/api/v1/experiments", tags=["ab-testing"])


# =============================================================================
# Assignment Endpoints (High traffic)
# =============================================================================

@router.post("/assign/{experiment_key}", response_model=Optional[AssignmentResponse])
async def assign_variant(
    experiment_key: str,
    context: AssignmentContext,
    db: AsyncSession = Depends(get_db),
    ab_service: ABTestingService = Depends(get_ab_testing),
):
    """
    Assign user to experiment variant.

    Returns variant assignment or null if user not in experiment traffic.
    """
    assignment = await ab_service.assign_variant(
        experiment_key=experiment_key,
        user_id=context.user_id,
        db=db,
        context=context.properties,
        pre_experiment_value=context.pre_experiment_value,
    )

    if not assignment:
        return None

    return AssignmentResponse(
        experiment_key=assignment.experiment_key,
        variant_name=assignment.variant_name,
        is_control=assignment.is_control,
        payload=assignment.payload,
        already_assigned=assignment.already_assigned,
    )


@router.post("/assign", response_model=BulkAssignmentResponse)
async def assign_variants_bulk(
    request: BulkAssignmentRequest,
    db: AsyncSession = Depends(get_db),
    ab_service: ABTestingService = Depends(get_ab_testing),
):
    """
    Assign user to multiple experiments at once.

    More efficient than making multiple single assign calls.
    """
    start = time.perf_counter()

    assignments = {}
    for exp_key in request.experiment_keys:
        assignment = await ab_service.assign_variant(
            experiment_key=exp_key,
            user_id=request.context.user_id,
            db=db,
            context=request.context.properties,
            pre_experiment_value=request.context.pre_experiment_value,
        )
        if assignment:
            assignments[exp_key] = AssignmentResponse(
                experiment_key=assignment.experiment_key,
                variant_name=assignment.variant_name,
                is_control=assignment.is_control,
                payload=assignment.payload,
                already_assigned=assignment.already_assigned,
            )
        else:
            assignments[exp_key] = None

    await db.commit()

    return BulkAssignmentResponse(
        assignments=assignments,
        assignment_time_ms=(time.perf_counter() - start) * 1000,
    )


@router.get("/assignment/{experiment_key}/{user_id}")
async def get_assignment(
    experiment_key: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get existing assignment for user (does not create new assignment).
    """
    result = await db.execute(
        select(Experiment)
        .where(Experiment.experiment_key == experiment_key)
    )
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    exposure = await db.execute(
        select(ExperimentExposure)
        .where(ExperimentExposure.experiment_id == experiment.id)
        .where(ExperimentExposure.user_id == user_id)
    )
    exposure_record = exposure.scalar_one_or_none()

    if not exposure_record:
        return {"assigned": False, "experiment_key": experiment_key}

    variant = next(
        (v for v in experiment.variants if v.name == exposure_record.variant_name),
        None
    )

    return {
        "assigned": True,
        "experiment_key": experiment_key,
        "variant_name": exposure_record.variant_name,
        "is_control": variant.is_control if variant else False,
        "assigned_at": exposure_record.assigned_at.isoformat(),
    }


# =============================================================================
# Conversion Tracking
# =============================================================================

@router.post("/convert")
async def record_conversion(
    event: ConversionEvent,
    db: AsyncSession = Depends(get_db),
    ab_service: ABTestingService = Depends(get_ab_testing),
):
    """
    Record conversion event for experiment.

    User must be already assigned to the experiment.
    """
    success = await ab_service.record_conversion(
        experiment_key=event.experiment_key,
        user_id=event.user_id,
        metric_name=event.metric_name,
        db=db,
        metric_value=event.metric_value,
        attribution_window_hours=event.attribution_window_hours,
    )

    if not success:
        return {
            "recorded": False,
            "reason": "User not exposed to experiment",
        }

    await db.commit()
    return {"recorded": True, "experiment_key": event.experiment_key}


# =============================================================================
# Admin CRUD Endpoints
# =============================================================================

@router.get("/", response_model=list[ExperimentResponse])
async def list_experiments(
    status: Optional[ExperimentStatus] = Query(default=None),
    owner: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    db: AsyncSession = Depends(get_db),
):
    """List all experiments with optional filtering."""
    query = select(Experiment).order_by(Experiment.created_at.desc())

    if status:
        query = query.where(Experiment.status == status)
    if owner:
        query = query.where(Experiment.owner == owner)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    experiments = result.scalars().all()

    return [
        ExperimentResponse(
            id=exp.id,
            experiment_key=exp.experiment_key,
            name=exp.name,
            description=exp.description,
            hypothesis=exp.hypothesis,
            status=exp.status.value,
            start_date=exp.start_date,
            end_date=exp.end_date,
            traffic_percentage=exp.traffic_percentage,
            primary_metric=exp.primary_metric,
            secondary_metrics=exp.secondary_metrics or [],
            min_sample_size=exp.min_sample_size,
            confidence_level=exp.confidence_level,
            min_detectable_effect=exp.min_detectable_effect,
            feature_flag_key=exp.feature_flag_key,
            owner=exp.owner,
            tags=exp.tags or [],
            created_at=exp.created_at,
            updated_at=exp.updated_at,
            variants=[
                VariantConfig(
                    name=v.name,
                    description=v.description,
                    weight=v.weight,
                    payload=v.payload or {},
                    is_control=v.is_control,
                )
                for v in exp.variants
            ],
        )
        for exp in experiments
    ]


@router.get("/{experiment_key}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_key: str,
    db: AsyncSession = Depends(get_db),
):
    """Get experiment by key."""
    result = await db.execute(
        select(Experiment).where(Experiment.experiment_key == experiment_key)
    )
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    return ExperimentResponse(
        id=experiment.id,
        experiment_key=experiment.experiment_key,
        name=experiment.name,
        description=experiment.description,
        hypothesis=experiment.hypothesis,
        status=experiment.status.value,
        start_date=experiment.start_date,
        end_date=experiment.end_date,
        traffic_percentage=experiment.traffic_percentage,
        primary_metric=experiment.primary_metric,
        secondary_metrics=experiment.secondary_metrics or [],
        min_sample_size=experiment.min_sample_size,
        confidence_level=experiment.confidence_level,
        min_detectable_effect=experiment.min_detectable_effect,
        feature_flag_key=experiment.feature_flag_key,
        owner=experiment.owner,
        tags=experiment.tags or [],
        created_at=experiment.created_at,
        updated_at=experiment.updated_at,
        variants=[
            VariantConfig(
                name=v.name,
                description=v.description,
                weight=v.weight,
                payload=v.payload or {},
                is_control=v.is_control,
            )
            for v in experiment.variants
        ],
    )


@router.post("/", response_model=ExperimentResponse, status_code=201)
async def create_experiment(
    request: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new experiment."""
    # Check if experiment already exists
    existing = await db.execute(
        select(Experiment).where(Experiment.experiment_key == request.experiment_key)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Experiment already exists")

    # Validate variant weights sum to ~100
    total_weight = sum(v.weight for v in request.variants)
    if abs(total_weight - 100) > 0.1:
        raise HTTPException(
            status_code=400,
            detail=f"Variant weights must sum to 100, got {total_weight}",
        )

    # Validate exactly one control
    controls = [v for v in request.variants if v.is_control]
    if len(controls) != 1:
        raise HTTPException(
            status_code=400,
            detail="Exactly one variant must be marked as control",
        )

    # Create experiment
    experiment = Experiment(
        experiment_key=request.experiment_key,
        name=request.name,
        description=request.description,
        hypothesis=request.hypothesis,
        primary_metric=request.primary_metric,
        secondary_metrics=request.secondary_metrics,
        traffic_percentage=request.traffic_percentage,
        min_sample_size=request.min_sample_size,
        confidence_level=request.confidence_level,
        min_detectable_effect=request.min_detectable_effect,
        feature_flag_key=request.feature_flag_key,
        owner=request.owner,
        tags=request.tags,
    )
    db.add(experiment)
    await db.flush()

    # Create variants
    for variant_config in request.variants:
        variant = ExperimentVariant(
            experiment_id=experiment.id,
            name=variant_config.name,
            description=variant_config.description,
            weight=variant_config.weight,
            payload=variant_config.payload,
            is_control=variant_config.is_control,
        )
        db.add(variant)

    await db.commit()
    await db.refresh(experiment)

    return ExperimentResponse(
        id=experiment.id,
        experiment_key=experiment.experiment_key,
        name=experiment.name,
        description=experiment.description,
        hypothesis=experiment.hypothesis,
        status=experiment.status.value,
        start_date=experiment.start_date,
        end_date=experiment.end_date,
        traffic_percentage=experiment.traffic_percentage,
        primary_metric=experiment.primary_metric,
        secondary_metrics=experiment.secondary_metrics or [],
        min_sample_size=experiment.min_sample_size,
        confidence_level=experiment.confidence_level,
        min_detectable_effect=experiment.min_detectable_effect,
        feature_flag_key=experiment.feature_flag_key,
        owner=experiment.owner,
        tags=experiment.tags or [],
        created_at=experiment.created_at,
        updated_at=experiment.updated_at,
        variants=[
            VariantConfig(
                name=v.name,
                description=v.description,
                weight=v.weight,
                payload=v.payload or {},
                is_control=v.is_control,
            )
            for v in experiment.variants
        ],
    )


@router.patch("/{experiment_key}", response_model=ExperimentResponse)
async def update_experiment(
    experiment_key: str,
    request: ExperimentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update experiment settings (limited updates for running experiments)."""
    result = await db.execute(
        select(Experiment).where(Experiment.experiment_key == experiment_key)
    )
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Apply updates
    if request.name is not None:
        experiment.name = request.name
    if request.description is not None:
        experiment.description = request.description
    if request.hypothesis is not None:
        experiment.hypothesis = request.hypothesis
    if request.traffic_percentage is not None:
        experiment.traffic_percentage = request.traffic_percentage
    if request.secondary_metrics is not None:
        experiment.secondary_metrics = request.secondary_metrics
    if request.owner is not None:
        experiment.owner = request.owner
    if request.tags is not None:
        experiment.tags = request.tags

    experiment.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(experiment)

    return ExperimentResponse(
        id=experiment.id,
        experiment_key=experiment.experiment_key,
        name=experiment.name,
        description=experiment.description,
        hypothesis=experiment.hypothesis,
        status=experiment.status.value,
        start_date=experiment.start_date,
        end_date=experiment.end_date,
        traffic_percentage=experiment.traffic_percentage,
        primary_metric=experiment.primary_metric,
        secondary_metrics=experiment.secondary_metrics or [],
        min_sample_size=experiment.min_sample_size,
        confidence_level=experiment.confidence_level,
        min_detectable_effect=experiment.min_detectable_effect,
        feature_flag_key=experiment.feature_flag_key,
        owner=experiment.owner,
        tags=experiment.tags or [],
        created_at=experiment.created_at,
        updated_at=experiment.updated_at,
        variants=[
            VariantConfig(
                name=v.name,
                description=v.description,
                weight=v.weight,
                payload=v.payload or {},
                is_control=v.is_control,
            )
            for v in experiment.variants
        ],
    )


# =============================================================================
# Experiment Lifecycle
# =============================================================================

@router.post("/{experiment_key}/start")
async def start_experiment(
    experiment_key: str,
    db: AsyncSession = Depends(get_db),
):
    """Start an experiment (move from DRAFT to RUNNING)."""
    result = await db.execute(
        select(Experiment).where(Experiment.experiment_key == experiment_key)
    )
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment.status != ExperimentStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start experiment in {experiment.status.value} status",
        )

    experiment.status = ExperimentStatus.RUNNING
    experiment.start_date = datetime.utcnow()
    experiment.updated_at = datetime.utcnow()

    await db.commit()

    return {"status": "running", "experiment_key": experiment_key}


@router.post("/{experiment_key}/pause")
async def pause_experiment(
    experiment_key: str,
    db: AsyncSession = Depends(get_db),
):
    """Pause a running experiment."""
    result = await db.execute(
        select(Experiment).where(Experiment.experiment_key == experiment_key)
    )
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment.status != ExperimentStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot pause experiment in {experiment.status.value} status",
        )

    experiment.status = ExperimentStatus.PAUSED
    experiment.updated_at = datetime.utcnow()

    await db.commit()

    return {"status": "paused", "experiment_key": experiment_key}


@router.post("/{experiment_key}/resume")
async def resume_experiment(
    experiment_key: str,
    db: AsyncSession = Depends(get_db),
):
    """Resume a paused experiment."""
    result = await db.execute(
        select(Experiment).where(Experiment.experiment_key == experiment_key)
    )
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment.status != ExperimentStatus.PAUSED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resume experiment in {experiment.status.value} status",
        )

    experiment.status = ExperimentStatus.RUNNING
    experiment.updated_at = datetime.utcnow()

    await db.commit()

    return {"status": "running", "experiment_key": experiment_key}


@router.post("/{experiment_key}/complete")
async def complete_experiment(
    experiment_key: str,
    winner: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Complete an experiment and declare winner (optional)."""
    result = await db.execute(
        select(Experiment).where(Experiment.experiment_key == experiment_key)
    )
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment.status not in [ExperimentStatus.RUNNING, ExperimentStatus.PAUSED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot complete experiment in {experiment.status.value} status",
        )

    experiment.status = ExperimentStatus.COMPLETED
    experiment.end_date = datetime.utcnow()
    experiment.updated_at = datetime.utcnow()

    await db.commit()

    return {
        "status": "completed",
        "experiment_key": experiment_key,
        "winner": winner,
    }


# =============================================================================
# Results & Analysis
# =============================================================================

@router.get("/{experiment_key}/results", response_model=ExperimentResults)
async def get_experiment_results(
    experiment_key: str,
    metric: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    ab_service: ABTestingService = Depends(get_ab_testing),
):
    """
    Get experiment results with statistical analysis.

    Returns variant statistics, lift, and significance.
    """
    result = await db.execute(
        select(Experiment).where(Experiment.experiment_key == experiment_key)
    )
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    metric_name = metric or experiment.primary_metric

    # Get cached results
    cached_results = await db.execute(
        select(ExperimentResult)
        .where(ExperimentResult.experiment_id == experiment.id)
        .where(ExperimentResult.metric_name == metric_name)
    )
    cached = {r.variant_name: r for r in cached_results.scalars().all()}

    # Get total sample size
    total_result = await db.execute(
        select(func.count(ExperimentExposure.id))
        .where(ExperimentExposure.experiment_id == experiment.id)
    )
    total_sample_size = total_result.scalar() or 0

    # Build variant results
    variant_results = []
    control_result = None

    for variant in experiment.variants:
        cached_variant = cached.get(variant.name)

        if cached_variant:
            vr = VariantResult(
                variant_name=variant.name,
                sample_size=cached_variant.sample_size,
                conversions=cached_variant.conversions,
                conversion_rate=cached_variant.conversion_rate or 0.0,
                mean_value=cached_variant.mean_value,
                std_dev=cached_variant.std_dev,
                relative_lift=cached_variant.relative_lift if not variant.is_control else None,
                absolute_lift=cached_variant.absolute_lift if not variant.is_control else None,
                p_value=cached_variant.p_value if not variant.is_control else None,
                confidence_interval=(
                    (cached_variant.confidence_interval_lower, cached_variant.confidence_interval_upper)
                    if cached_variant.confidence_interval_lower is not None
                    else None
                ) if not variant.is_control else None,
                is_significant=cached_variant.is_significant if not variant.is_control else False,
                probability_of_being_best=cached_variant.probability_of_being_best,
                expected_loss=cached_variant.expected_loss,
            )
        else:
            # No cached results yet
            stats = await ab_service.get_variant_stats(
                experiment.id, variant.name, metric_name, db
            )
            vr = VariantResult(
                variant_name=variant.name,
                sample_size=stats.sample_size,
                conversions=stats.conversions,
                conversion_rate=stats.conversion_rate,
                mean_value=stats.mean,
                std_dev=stats.std_dev,
                relative_lift=None,
                absolute_lift=None,
                p_value=None,
                confidence_interval=None,
                is_significant=False,
                probability_of_being_best=None,
                expected_loss=None,
            )

        variant_results.append(vr)
        if variant.is_control:
            control_result = vr

    # Determine winner and recommendation
    winner = None
    recommendation = "continue"

    significant_variants = [
        v for v in variant_results
        if v.is_significant and v.relative_lift and v.relative_lift > 0
    ]
    if significant_variants:
        best = max(significant_variants, key=lambda v: v.relative_lift or 0)
        winner = best.variant_name
        recommendation = "stop_winner"
    elif total_sample_size >= experiment.min_sample_size:
        # Check if all variants are not significant
        all_not_significant = all(
            not v.is_significant for v in variant_results if not v.variant_name == control_result.variant_name
        ) if control_result else True
        if all_not_significant:
            recommendation = "stop_no_effect"

    return ExperimentResults(
        experiment_key=experiment_key,
        status=experiment.status.value,
        primary_metric=metric_name,
        total_sample_size=total_sample_size,
        variants=variant_results,
        winner=winner,
        recommendation=recommendation,
        achieved_power=None,  # TODO: Calculate
        days_remaining=None,  # TODO: Calculate
        computed_at=datetime.utcnow(),
    )


@router.post("/{experiment_key}/refresh-results")
async def refresh_experiment_results(
    experiment_key: str,
    db: AsyncSession = Depends(get_db),
    ab_service: ABTestingService = Depends(get_ab_testing),
):
    """Refresh cached experiment results."""
    await ab_service.update_cached_results(experiment_key, db)
    await db.commit()
    return {"status": "refreshed", "experiment_key": experiment_key}


# =============================================================================
# Utility Endpoints
# =============================================================================

@router.post("/calculate-sample-size", response_model=SampleSizeResponse)
async def calculate_sample_size(
    request: SampleSizeCalculation,
):
    """
    Calculate required sample size for experiment.

    Based on baseline rate, MDE, power, and confidence level.
    """
    from app.experiments.statistics import StatisticalAnalyzer

    analyzer = StatisticalAnalyzer(confidence_level=request.confidence_level)
    sample_size = analyzer.calculate_required_sample_size(
        baseline_rate=request.baseline_rate,
        minimum_detectable_effect=request.minimum_detectable_effect,
        power=request.power,
    )

    return SampleSizeResponse(
        required_sample_size_per_variant=sample_size,
        total_sample_size=sample_size * 2,  # Control + treatment
        baseline_rate=request.baseline_rate,
        minimum_detectable_effect=request.minimum_detectable_effect,
        power=request.power,
        confidence_level=request.confidence_level,
    )
