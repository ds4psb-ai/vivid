"""DNA Lab Orchestrator Service - Saga Pattern Pipeline.

Orchestrates the DNA extraction pipeline using the Saga pattern:
VPE → AD → Mirror → QC

Features:
- Sequential execution with dependency chaining
- Compensation (rollback) on failure
- Transactional Outbox for Qdrant sync
- Credit management with partial refunds

Usage:
    from app.services.dna_lab_orchestrator import DNALabOrchestrator

    orchestrator = DNALabOrchestrator()
    result = await orchestrator.run_pipeline(
        video_uri="gs://bucket/video.mp4",
        user_id="user-123",
        db=db,
    )
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.schemas.dna_lab_unified import (
    AestheticGuidelines,
    DNALabPipelineRequest,
    DNALabResult,
    PersonaDNA,
    PipelineStatus,
    PipelineStep,
    QualityReport,
    StepResult,
)
from app.schemas.vpe import LogicVector

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Credit costs per step
STEP_CREDITS = {
    PipelineStep.VPE: 50,
    PipelineStep.AD: 10,
    PipelineStep.MIRROR: 5,
    PipelineStep.QC: 8,
}

# Compensation handlers (cleanup on failure)
COMPENSATION_HANDLERS: Dict[PipelineStep, str] = {
    PipelineStep.VPE: "_compensate_vpe",
    PipelineStep.AD: "_compensate_ad",
    PipelineStep.MIRROR: "_compensate_mirror",
    PipelineStep.QC: "_compensate_qc",
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class PipelineContext:
    """Context passed through pipeline steps."""
    trace_id: str
    user_id: str
    request: DNALabPipelineRequest

    # Step outputs (populated as pipeline progresses)
    vpe_result: Optional[LogicVector] = None
    ad_result: Optional[AestheticGuidelines] = None
    mirror_result: Optional[PersonaDNA] = None
    qc_result: Optional[QualityReport] = None

    # Evidence collection
    evidence_refs: List[str] = field(default_factory=list)

    # Execution tracking
    completed_steps: List[PipelineStep] = field(default_factory=list)
    step_results: List[StepResult] = field(default_factory=list)
    credits_used: int = 0

    # Error tracking
    errors: Dict[str, str] = field(default_factory=dict)


# =============================================================================
# Exceptions
# =============================================================================

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    def __init__(self, message: str, step: Optional[PipelineStep] = None):
        super().__init__(message)
        self.step = step


class StepError(PipelineError):
    """Error during step execution."""
    pass


class CompensationError(PipelineError):
    """Error during compensation (rollback)."""
    pass


# =============================================================================
# DNA Lab Orchestrator
# =============================================================================

class DNALabOrchestrator:
    """Saga pattern orchestrator for DNA Lab pipeline.

    Executes steps sequentially with dependency injection and
    compensates (rolls back) on failure.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize orchestrator.

        Args:
            api_key: Optional BYOK API key for Gemini
        """
        self._api_key = api_key or settings.GEMINI_API_KEY.get_secret_value()

    async def run_pipeline(
        self,
        request: DNALabPipelineRequest,
        user_id: str,
        db: AsyncSession,
        progress_callback: Optional[Callable[[str, float, str], None]] = None,
    ) -> DNALabResult:
        """Run the DNA Lab pipeline with Saga pattern.

        Args:
            request: Pipeline configuration
            user_id: User identifier
            db: Database session
            progress_callback: Optional (status, progress%, message) callback

        Returns:
            DNALabResult with all outputs and metadata
        """
        start_time = time.monotonic()
        trace_id = str(uuid.uuid4())

        ctx = PipelineContext(
            trace_id=trace_id,
            user_id=user_id,
            request=request,
        )

        def emit(status: str, progress: float, message: str):
            if progress_callback:
                try:
                    progress_callback(status, progress, message)
                except Exception as e:
                    logger.warning(f"[Pipeline] Progress callback error: {e}")

        emit("starting", 0, "파이프라인 시작...")

        try:
            # Execute steps in order
            steps = request.steps or [
                PipelineStep.VPE,
                PipelineStep.AD,
                PipelineStep.MIRROR,
                PipelineStep.QC,
            ]

            total_steps = len(steps)

            for i, step in enumerate(steps):
                progress = ((i / total_steps) * 80) + 5  # 5% - 85%
                emit("processing", progress, f"{step.value.upper()} 실행 중...")

                step_result = await self._execute_step(step, ctx, db)
                ctx.step_results.append(step_result)

                if step_result.status == "failed":
                    if request.fail_fast:
                        raise StepError(
                            f"Step {step.value} failed: {step_result.error}",
                            step=step,
                        )
                    ctx.errors[step.value] = step_result.error or "Unknown error"
                else:
                    ctx.completed_steps.append(step)
                    ctx.credits_used += step_result.credits_used

            emit("finalizing", 90, "결과 저장 중...")

            # Write to Outbox for Qdrant sync
            if request.store_to_qdrant:
                await self._write_to_outbox(ctx, db)

            emit("completed", 100, "파이프라인 완료!")

            processing_time_ms = int((time.monotonic() - start_time) * 1000)

            return DNALabResult(
                success=len(ctx.completed_steps) > 0,
                trace_id=trace_id,
                status=PipelineStatus.COMPLETED if not ctx.errors else PipelineStatus.PARTIAL,
                vpe=ctx.vpe_result,
                ad=ctx.ad_result,
                mirror=ctx.mirror_result,
                qc=ctx.qc_result,
                evidence_refs=ctx.evidence_refs,
                steps=ctx.step_results,
                credits_used=ctx.credits_used,
                processing_time_ms=processing_time_ms,
                errors=ctx.errors,
                completed_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.exception(f"[Pipeline] Error: {e}")
            emit("compensating", 95, "롤백 진행 중...")

            # Saga compensation: rollback completed steps
            await self._compensate(ctx.completed_steps, ctx, db)

            processing_time_ms = int((time.monotonic() - start_time) * 1000)

            return DNALabResult(
                success=False,
                trace_id=trace_id,
                status=PipelineStatus.FAILED,
                evidence_refs=ctx.evidence_refs,
                steps=ctx.step_results,
                credits_used=ctx.credits_used,
                processing_time_ms=processing_time_ms,
                errors={**ctx.errors, "pipeline": str(e)},
                completed_at=datetime.utcnow(),
            )

    # =========================================================================
    # Step Execution
    # =========================================================================

    async def _execute_step(
        self,
        step: PipelineStep,
        ctx: PipelineContext,
        db: AsyncSession,
    ) -> StepResult:
        """Execute a single pipeline step."""
        started_at = datetime.utcnow()
        start_time = time.monotonic()

        try:
            if step == PipelineStep.VPE:
                await self._run_vpe(ctx)
            elif step == PipelineStep.AD:
                await self._run_ad(ctx)
            elif step == PipelineStep.MIRROR:
                await self._run_mirror(ctx)
            elif step == PipelineStep.QC:
                await self._run_qc(ctx)

            duration_ms = int((time.monotonic() - start_time) * 1000)

            return StepResult(
                step=step,
                status="completed",
                started_at=started_at,
                completed_at=datetime.utcnow(),
                duration_ms=duration_ms,
                credits_used=STEP_CREDITS.get(step, 0),
            )

        except Exception as e:
            logger.error(f"[Pipeline] Step {step.value} failed: {e}")
            duration_ms = int((time.monotonic() - start_time) * 1000)

            return StepResult(
                step=step,
                status="failed",
                started_at=started_at,
                completed_at=datetime.utcnow(),
                duration_ms=duration_ms,
                error=str(e),
                credits_used=0,
            )

    async def _run_vpe(self, ctx: PipelineContext) -> None:
        """Run VPE (Video Parsing Engine) step."""
        if not ctx.request.video_uri:
            logger.info(f"[Pipeline] VPE skipped: no video_uri")
            return

        from app.services.vpe_service import get_vpe_service

        service = get_vpe_service(api_key=self._api_key)
        result = await service.parse_video(
            video_uri=ctx.request.video_uri,
            auteur_hint=ctx.request.auteur_key,
            extract_shots=True,
        )

        if result.success and result.logic_vector:
            ctx.vpe_result = result.logic_vector
            ctx.evidence_refs.extend(result.evidence_refs)
            ctx.evidence_refs.append(f"db:vpe_results:{ctx.trace_id}")
        else:
            raise StepError(result.error or "VPE parsing failed", step=PipelineStep.VPE)

    async def _run_ad(self, ctx: PipelineContext) -> None:
        """Run AD (Aesthetic Director) step.

        Uses VPE result if available for enhanced context.
        """
        from app.dimension_adapter import execute_dimension_capsule

        inputs = {
            "concept": ctx.request.concept or "",
            "auteur_key": ctx.request.auteur_key or "bong",
        }

        # Inject VPE context if available
        if ctx.vpe_result:
            inputs["vpe_context"] = ctx.vpe_result.to_system_prompt_context()

        params = {"model": "gemini-3-flash-preview"}

        result = await execute_dimension_capsule(
            capsule_id="dimension.aesthetic.direct",
            inputs=inputs,
            params=params,
        )

        if result.get("success"):
            output = result.get("output", {})
            ctx.ad_result = AestheticGuidelines(
                visual_style=output.get("visual_style", ""),
                color_palette=output.get("color_palette", []),
                mood_keywords=output.get("mood_keywords", []),
                auteur_reference=ctx.request.auteur_key,
                composition_notes=output.get("composition_notes", ""),
                lighting_approach=output.get("lighting_approach", ""),
                reference_directors=output.get("reference_directors", []),
            )
            ctx.evidence_refs.extend(output.get("evidence_refs", []))
            ctx.evidence_refs.append(f"db:ad_results:{ctx.trace_id}")
        else:
            raise StepError(result.get("error", "AD analysis failed"), step=PipelineStep.AD)

    async def _run_mirror(self, ctx: PipelineContext) -> None:
        """Run Mirror (Persona) step with Big Five inference."""
        from app.dimension_adapter import execute_dimension_capsule

        inputs = {
            "analysis_stage": "intro",
            "conversation_history": [],
            **(ctx.request.persona_context or {}),
        }
        params = {"model": "gemini-3-flash-preview"}

        result = await execute_dimension_capsule(
            capsule_id="dimension.persona.analyze",
            inputs=inputs,
            params=params,
        )

        if result.get("success"):
            output = result.get("output", {})

            # Extract Big Five traits
            ocean = output.get("big_five", output.get("ocean", {}))

            ctx.mirror_result = PersonaDNA(
                mbti=output.get("mbti"),
                archetype=output.get("archetype"),
                openness=ocean.get("openness", 0.5) if ocean else 0.5,
                conscientiousness=ocean.get("conscientiousness", 0.5) if ocean else 0.5,
                extraversion=ocean.get("extraversion", 0.5) if ocean else 0.5,
                agreeableness=ocean.get("agreeableness", 0.5) if ocean else 0.5,
                neuroticism=ocean.get("neuroticism", 0.5) if ocean else 0.5,
                persona_type=output.get("persona_type", ""),
                creative_tendencies=output.get("creative_tendencies", []),
                visual_preferences=output.get("visual_preferences", []),
                narrative_style=output.get("narrative_style", ""),
                emotional_range=output.get("emotional_range", []),
                creativity_index=output.get("creativity_index"),
                auteur_affinity=output.get("auteur_affinity", []),
            )
            ctx.evidence_refs.extend(output.get("evidence_refs", []))
            ctx.evidence_refs.append(f"db:mirror_results:{ctx.trace_id}")
        else:
            raise StepError(result.get("error", "Mirror analysis failed"), step=PipelineStep.MIRROR)

    async def _run_qc(self, ctx: PipelineContext) -> None:
        """Run QC (Quality Controller) step with IP context awareness."""
        from app.services.quality_director_service import QualityDirectorService

        service = QualityDirectorService()

        # Use AD result for context if available
        ad_context = None
        if ctx.ad_result:
            ad_context = {
                "visual_style": ctx.ad_result.visual_style,
                "mood_keywords": ctx.ad_result.mood_keywords,
            }

        result = await service.evaluate_with_context(
            content=ctx.request.quality_content or "",
            ip_id=ctx.request.ip_id,
            ad_context=ad_context,
        )

        ctx.qc_result = result
        ctx.evidence_refs.append(f"db:qc_results:{ctx.trace_id}")

    # =========================================================================
    # Saga Compensation (Rollback)
    # =========================================================================

    async def _compensate(
        self,
        completed_steps: List[PipelineStep],
        ctx: PipelineContext,
        db: AsyncSession,
    ) -> None:
        """Compensate (rollback) completed steps on failure.

        Executes compensating transactions in reverse order.
        """
        logger.info(f"[Pipeline] Compensating {len(completed_steps)} steps: {completed_steps}")

        for step in reversed(completed_steps):
            handler_name = COMPENSATION_HANDLERS.get(step)
            if handler_name and hasattr(self, handler_name):
                try:
                    handler = getattr(self, handler_name)
                    await handler(ctx, db)
                    logger.info(f"[Pipeline] Compensated step: {step.value}")
                except Exception as e:
                    logger.error(f"[Pipeline] Compensation failed for {step.value}: {e}")

    async def _compensate_vpe(self, ctx: PipelineContext, db: AsyncSession) -> None:
        """Compensate VPE step - mark Qdrant entry as invalid."""
        # In a real implementation, this would mark the Qdrant doc as invalid
        # or queue a deletion via Outbox
        logger.debug(f"[Pipeline] VPE compensation: trace_id={ctx.trace_id}")

    async def _compensate_ad(self, ctx: PipelineContext, db: AsyncSession) -> None:
        """Compensate AD step."""
        logger.debug(f"[Pipeline] AD compensation: trace_id={ctx.trace_id}")

    async def _compensate_mirror(self, ctx: PipelineContext, db: AsyncSession) -> None:
        """Compensate Mirror step."""
        logger.debug(f"[Pipeline] Mirror compensation: trace_id={ctx.trace_id}")

    async def _compensate_qc(self, ctx: PipelineContext, db: AsyncSession) -> None:
        """Compensate QC step."""
        logger.debug(f"[Pipeline] QC compensation: trace_id={ctx.trace_id}")

    # =========================================================================
    # Outbox Integration
    # =========================================================================

    async def _write_to_outbox(
        self,
        ctx: PipelineContext,
        db: AsyncSession,
    ) -> None:
        """Write pipeline result to Outbox for Qdrant sync."""
        try:
            from app.models_outbox import Outbox

            payload = {
                "trace_id": ctx.trace_id,
                "user_id": ctx.user_id,
                "vpe": ctx.vpe_result.model_dump() if ctx.vpe_result else None,
                "ad": ctx.ad_result.model_dump() if ctx.ad_result else None,
                "mirror": ctx.mirror_result.model_dump() if ctx.mirror_result else None,
                "qc": ctx.qc_result.model_dump() if ctx.qc_result else None,
                "evidence_refs": ctx.evidence_refs,
                "completed_steps": [s.value for s in ctx.completed_steps],
            }

            outbox_entry = Outbox(
                event_type="dna_lab_result",
                payload=payload,
                status="pending",
            )
            db.add(outbox_entry)
            await db.flush()

            logger.info(f"[Pipeline] Written to Outbox: {outbox_entry.id}")

        except ImportError:
            # Outbox model not yet created
            logger.warning("[Pipeline] Outbox model not found, skipping sync")
        except Exception as e:
            logger.error(f"[Pipeline] Failed to write to Outbox: {e}")


# =============================================================================
# Module-level convenience
# =============================================================================

_default_orchestrator: Optional[DNALabOrchestrator] = None


def get_orchestrator(api_key: Optional[str] = None) -> DNALabOrchestrator:
    """Get or create the default orchestrator instance."""
    global _default_orchestrator
    if api_key:
        return DNALabOrchestrator(api_key=api_key)
    if _default_orchestrator is None:
        _default_orchestrator = DNALabOrchestrator()
    return _default_orchestrator


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "DNALabOrchestrator",
    "PipelineContext",
    "PipelineError",
    "StepError",
    "CompensationError",
    "STEP_CREDITS",
    "get_orchestrator",
]
