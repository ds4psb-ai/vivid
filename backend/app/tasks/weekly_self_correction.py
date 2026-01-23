"""P7: Weekly Self-Correction Task.

주간 자동 실행 Cron Job으로 RAG 쿼리 분류를 자동 개선합니다.

Pipeline:
1. P6 피드백 수집 (7일)
2. 오분류 분석 (MisclassificationAnalyzer)
3. 프롬프트 개선안 생성 (PromptTuner)
4. 임계값 최적화 (ThresholdTuner)
5. A/B 테스트 배포 (10%)
6. 이전 실험 결과 평가
7. 성공 시 채택, 실패 시 롤백

Cron Schedule:
    매주 일요일 03:00 UTC
    0 3 * * 0

Usage:
    # Cron Job으로 실행
    python -m app.tasks.weekly_self_correction

    # 수동 실행
    from app.tasks.weekly_self_correction import run_weekly_self_correction
    result = await run_weekly_self_correction(db)
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session_context
from app.experiments.models import Experiment, ExperimentStatus
from app.schemas.self_correction_schemas import (
    ExperimentEvaluation,
    ExperimentType,
    SelfCorrectionCycleResult,
    SelfCorrectionStatus,
)
from app.services.misclassification_analyzer import (
    MisclassificationAnalyzer,
    get_misclassification_analyzer,
)
from app.services.prompt_tuner import PromptTuner, get_prompt_tuner
from app.services.threshold_tuner import ThresholdTuner, get_threshold_tuner

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


class SelfCorrectionConfig:
    """Self-Correction 설정."""

    # Analysis settings
    ANALYSIS_DAYS = 7
    MIN_FEEDBACK_COUNT = 50  # 최소 피드백 수

    # Tuning settings
    MAX_FAILURES_FOR_PROMPT = 100
    AUTO_EXPERIMENT = True
    EXPERIMENT_TRAFFIC = 0.10  # 10%

    # Evaluation settings
    MIN_EXPERIMENT_DURATION_DAYS = 7
    MIN_SAMPLE_SIZE = 100
    SIGNIFICANCE_LEVEL = 0.95
    MIN_LIFT_FOR_ADOPTION = 0.02  # 2% improvement

    # Limits
    MAX_CONCURRENT_EXPERIMENTS = 3


# =============================================================================
# Weekly Self-Correction Pipeline
# =============================================================================


async def run_weekly_self_correction(
    db: AsyncSession,
    config: Optional[SelfCorrectionConfig] = None,
    skip_analysis: bool = False,
    skip_tuning: bool = False,
    skip_experiment: bool = False,
    evaluate_previous: bool = True,
) -> SelfCorrectionCycleResult:
    """주간 Self-Correction 파이프라인 실행.

    Args:
        db: Database session
        config: 설정 (None이면 기본값)
        skip_analysis: 분석 건너뛰기
        skip_tuning: 튜닝 건너뛰기
        skip_experiment: 실험 건너뛰기
        evaluate_previous: 이전 실험 평가 여부

    Returns:
        SelfCorrectionCycleResult with execution details
    """
    if config is None:
        config = SelfCorrectionConfig()

    result = SelfCorrectionCycleResult(
        status=SelfCorrectionStatus.ANALYZING,
    )

    logger.info(f"[P7] Starting weekly self-correction cycle: {result.cycle_id}")

    try:
        # =====================================================================
        # Phase 1: Analyze Misclassifications
        # =====================================================================

        if not skip_analysis:
            result.status = SelfCorrectionStatus.ANALYZING
            analyzer = get_misclassification_analyzer()

            report = await analyzer.analyze_period(
                db,
                days=config.ANALYSIS_DAYS,
                min_feedback_count=1,
            )
            result.misclassification_report = report

            logger.info(
                f"[P7] Analysis complete: {report.total_misclassified} misclassifications "
                f"out of {report.total_with_feedback} with feedback "
                f"(rate: {report.misclassification_rate:.1%})"
            )

            # Check if we have enough data
            if report.total_with_feedback < config.MIN_FEEDBACK_COUNT:
                logger.warning(
                    f"[P7] Insufficient feedback data ({report.total_with_feedback} < {config.MIN_FEEDBACK_COUNT}). "
                    "Skipping tuning."
                )
                result.summary = f"Insufficient feedback data ({report.total_with_feedback})"
                result.status = SelfCorrectionStatus.COMPLETED
                result.end_time = datetime.utcnow()
                return result

        # =====================================================================
        # Phase 2: Evaluate Previous Experiments
        # =====================================================================

        if evaluate_previous:
            evaluations = await _evaluate_previous_experiments(db, config)

            for eval_result in evaluations:
                result.previous_experiments_evaluated.append(eval_result.experiment_key)

                if eval_result.should_adopt:
                    adopted = await _adopt_experiment(db, eval_result)
                    if adopted:
                        result.adoptions.append(eval_result.experiment_key)
                        logger.info(f"[P7] Adopted experiment: {eval_result.experiment_key}")
                else:
                    rolled_back = await _rollback_experiment(db, eval_result)
                    if rolled_back:
                        result.rollbacks.append(eval_result.experiment_key)
                        logger.info(f"[P7] Rolled back experiment: {eval_result.experiment_key}")

        # =====================================================================
        # Phase 3: Tune Prompts and Thresholds
        # =====================================================================

        if not skip_tuning and result.misclassification_report:
            result.status = SelfCorrectionStatus.TUNING

            # Check concurrent experiment limit
            running_count = await _count_running_experiments(db)
            if running_count >= config.MAX_CONCURRENT_EXPERIMENTS:
                logger.warning(
                    f"[P7] Max concurrent experiments reached ({running_count}). "
                    "Skipping new experiments."
                )
                skip_experiment = True

            # Prompt Tuning
            if result.misclassification_report.total_misclassified > 0:
                prompt_tuner = get_prompt_tuner()
                misclassified_queries = result.misclassification_report.top_misclassified_queries

                if misclassified_queries:
                    prompt_result = await prompt_tuner.run_full_tuning(
                        failures=misclassified_queries[:config.MAX_FAILURES_FOR_PROMPT],
                        db=db if not skip_experiment else None,
                        auto_experiment=config.AUTO_EXPERIMENT and not skip_experiment,
                        experiment_traffic=config.EXPERIMENT_TRAFFIC,
                    )
                    result.prompt_tuning = prompt_result

                    if prompt_result.experiment_key:
                        result.experiments_started.append(prompt_result.experiment_key)
                        logger.info(f"[P7] Started prompt tuning experiment: {prompt_result.experiment_key}")

            # Threshold Tuning
            threshold_tuner = get_threshold_tuner()
            threshold_result = await threshold_tuner.run_full_tuning(
                db=db,
                days=config.ANALYSIS_DAYS,
                report=result.misclassification_report,
                auto_experiment=config.AUTO_EXPERIMENT and not skip_experiment,
                experiment_traffic=config.EXPERIMENT_TRAFFIC,
            )
            result.threshold_tuning = threshold_result

            if threshold_result.experiment_key:
                result.experiments_started.append(threshold_result.experiment_key)
                logger.info(f"[P7] Started threshold tuning experiment: {threshold_result.experiment_key}")

        # =====================================================================
        # Phase 4: Finalize
        # =====================================================================

        result.status = SelfCorrectionStatus.COMPLETED
        result.end_time = datetime.utcnow()

        # Build summary
        result.summary = _build_summary(result)

        # Extract metrics
        if result.misclassification_report:
            result.metrics_before = {
                "misclassification_rate": result.misclassification_report.misclassification_rate,
                "skip_negative_rate": result.misclassification_report.skip_retrieval_negative_rate,
                "crag_trigger_rate": result.misclassification_report.crag_trigger_rate,
                "crag_success_rate": result.misclassification_report.crag_success_rate,
            }

        logger.info(f"[P7] Self-correction cycle completed: {result.cycle_id}")
        logger.info(f"[P7] Summary: {result.summary}")

        return result

    except Exception as e:
        logger.error(f"[P7] Self-correction failed: {e}", exc_info=True)
        result.status = SelfCorrectionStatus.FAILED
        result.error = str(e)
        result.end_time = datetime.utcnow()
        return result


# =============================================================================
# Experiment Evaluation
# =============================================================================


async def _evaluate_previous_experiments(
    db: AsyncSession,
    config: SelfCorrectionConfig,
) -> List[ExperimentEvaluation]:
    """이전 실험 평가."""
    evaluations = []

    # Get completed P7 experiments
    min_end_date = datetime.utcnow() - timedelta(days=config.MIN_EXPERIMENT_DURATION_DAYS)

    result = await db.execute(
        select(Experiment)
        .where(
            and_(
                Experiment.status == ExperimentStatus.RUNNING,
                Experiment.start_date <= min_end_date,
                Experiment.experiment_key.like("p7_%"),
            )
        )
    )
    experiments = list(result.scalars().all())

    for experiment in experiments:
        try:
            from app.experiments.ab_testing import get_ab_testing

            ab_service = get_ab_testing()
            significance_result = await ab_service.calculate_results(
                experiment.experiment_key, db
            )

            if significance_result is None:
                continue

            # Determine experiment type
            exp_type = ExperimentType.PROMPT_TUNING
            if "threshold" in experiment.experiment_key:
                exp_type = ExperimentType.THRESHOLD_TUNING

            # Evaluate results
            should_adopt = (
                significance_result.is_significant
                and significance_result.relative_lift >= config.MIN_LIFT_FOR_ADOPTION
            )

            risk_level = "low"
            if significance_result.relative_lift < 0:
                risk_level = "high"
            elif significance_result.p_value > 0.1:
                risk_level = "medium"

            adoption_reason = ""
            if should_adopt:
                adoption_reason = (
                    f"Significant improvement: {significance_result.relative_lift:.1%} lift "
                    f"(p={significance_result.p_value:.3f})"
                )
            else:
                if not significance_result.is_significant:
                    adoption_reason = f"Not significant (p={significance_result.p_value:.3f})"
                elif significance_result.relative_lift < config.MIN_LIFT_FOR_ADOPTION:
                    adoption_reason = f"Lift too small ({significance_result.relative_lift:.1%})"

            evaluation = ExperimentEvaluation(
                experiment_key=experiment.experiment_key,
                experiment_type=exp_type,
                started_at=experiment.start_date,
                control_sample_size=0,  # Would need to query
                treatment_sample_size=0,
                control_accuracy=0.0,
                treatment_accuracy=0.0,
                relative_lift=significance_result.relative_lift,
                p_value=significance_result.p_value,
                is_significant=significance_result.is_significant,
                confidence_interval=significance_result.confidence_interval,
                should_adopt=should_adopt,
                adoption_reason=adoption_reason,
                risk_level=risk_level,
            )
            evaluations.append(evaluation)

        except Exception as e:
            logger.error(f"[P7] Failed to evaluate experiment {experiment.experiment_key}: {e}")

    return evaluations


async def _adopt_experiment(
    db: AsyncSession,
    evaluation: ExperimentEvaluation,
) -> bool:
    """성공한 실험 채택."""
    try:
        # Get experiment
        result = await db.execute(
            select(Experiment)
            .where(Experiment.experiment_key == evaluation.experiment_key)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            return False

        # Mark as completed
        experiment.status = ExperimentStatus.COMPLETED
        experiment.end_date = datetime.utcnow()

        # Apply changes based on experiment type
        if evaluation.experiment_type == ExperimentType.PROMPT_TUNING:
            # Get treatment variant payload
            treatment = next(
                (v for v in experiment.variants if not v.is_control),
                None
            )
            if treatment and treatment.payload:
                prompt = treatment.payload.get("prompt")
                if prompt:
                    prompt_tuner = get_prompt_tuner()
                    prompt_tuner.set_current_prompt(prompt)
                    logger.info(f"[P7] Applied improved prompt from {evaluation.experiment_key}")

        elif evaluation.experiment_type == ExperimentType.THRESHOLD_TUNING:
            treatment = next(
                (v for v in experiment.variants if not v.is_control),
                None
            )
            if treatment and treatment.payload:
                from app.schemas.self_correction_schemas import ThresholdConfig
                new_config = ThresholdConfig(**treatment.payload)
                threshold_tuner = get_threshold_tuner()
                threshold_tuner.apply_config(new_config)
                logger.info(f"[P7] Applied threshold config from {evaluation.experiment_key}")

        await db.commit()
        return True

    except Exception as e:
        logger.error(f"[P7] Failed to adopt experiment: {e}")
        await db.rollback()
        return False


async def _rollback_experiment(
    db: AsyncSession,
    evaluation: ExperimentEvaluation,
) -> bool:
    """실패한 실험 롤백."""
    try:
        result = await db.execute(
            select(Experiment)
            .where(Experiment.experiment_key == evaluation.experiment_key)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            return False

        # Mark as archived (rolled back)
        experiment.status = ExperimentStatus.ARCHIVED
        experiment.end_date = datetime.utcnow()

        await db.commit()
        return True

    except Exception as e:
        logger.error(f"[P7] Failed to rollback experiment: {e}")
        await db.rollback()
        return False


async def _count_running_experiments(db: AsyncSession) -> int:
    """Count running P7 experiments."""
    result = await db.execute(
        select(Experiment)
        .where(
            and_(
                Experiment.status == ExperimentStatus.RUNNING,
                Experiment.experiment_key.like("p7_%"),
            )
        )
    )
    return len(list(result.scalars().all()))


def _build_summary(result: SelfCorrectionCycleResult) -> str:
    """Build human-readable summary."""
    parts = []

    if result.misclassification_report:
        report = result.misclassification_report
        parts.append(
            f"Analyzed {report.total_with_feedback} feedbacks, "
            f"found {report.total_misclassified} misclassifications "
            f"({report.misclassification_rate:.1%})"
        )

    if result.experiments_started:
        parts.append(f"Started {len(result.experiments_started)} new experiments")

    if result.adoptions:
        parts.append(f"Adopted {len(result.adoptions)} successful experiments")

    if result.rollbacks:
        parts.append(f"Rolled back {len(result.rollbacks)} failed experiments")

    return "; ".join(parts) if parts else "No actions taken"


# =============================================================================
# CLI Entry Point
# =============================================================================


async def main():
    """CLI entry point for cron job."""
    logger.info("[P7] Running weekly self-correction...")

    async with get_async_session_context() as db:
        result = await run_weekly_self_correction(db)

    if result.status == SelfCorrectionStatus.COMPLETED:
        logger.info(f"[P7] Completed successfully: {result.summary}")
    else:
        logger.error(f"[P7] Failed: {result.error}")

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
