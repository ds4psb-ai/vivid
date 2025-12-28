"""LLMOps Evaluation Harness.

Provides evaluation metrics for LLM outputs:
- Groundedness: How well outputs are supported by evidence
- Relevancy: How relevant outputs are to the input query
- Completeness: How complete/comprehensive the outputs are

Reference: 07_EXECUTION_PLAN_2025-12.md Phase 2.4
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import CapsuleRun, GenerationRun, TemplateLearningRun


class EvalMetricType(str, Enum):
    """Evaluation metric types."""
    GROUNDEDNESS = "groundedness"
    RELEVANCY = "relevancy"
    COMPLETENESS = "completeness"
    COHERENCE = "coherence"
    HUMAN_FEEDBACK = "human_feedback"


@dataclass
class EvalMetric:
    """Single evaluation metric result."""
    metric_type: str
    score: float
    confidence: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMEvalResult:
    """Full evaluation result for an LLM run."""
    run_id: str
    run_type: str  # capsule_run | generation_run | template_learning_run
    metrics: List[EvalMetric]
    overall_score: float
    evidence_count: int
    token_usage: int
    latency_ms: int
    evaluated_at: datetime


@dataclass
class EvalHarnessSummary:
    """Summary of evaluation harness metrics."""
    total_runs: int
    avg_groundedness: float
    avg_relevancy: float
    avg_completeness: float
    avg_overall: float
    runs_with_human_feedback: int
    human_feedback_avg: float
    period_start: str
    period_end: str


def calculate_groundedness(evidence_refs: List[Any], output_text: str) -> EvalMetric:
    """
    Calculate groundedness score based on evidence refs.
    
    Higher score = more evidence backing the output.
    Formula: min(1.0, evidence_count / 3) * evidence_quality_factor
    """
    evidence_count = len(evidence_refs) if evidence_refs else 0
    
    if evidence_count == 0:
        return EvalMetric(
            metric_type=EvalMetricType.GROUNDEDNESS,
            score=0.0,
            confidence=1.0,
            details={"evidence_count": 0, "reason": "No evidence refs"},
        )
    
    # Base score from evidence count (max at 3+ refs)
    base_score = min(1.0, evidence_count / 3)
    
    # Quality factor based on evidence structure
    quality_factor = 1.0
    for ref in evidence_refs:
        if isinstance(ref, dict):
            if ref.get("source_hash") or ref.get("time_start_ms"):
                quality_factor = min(quality_factor + 0.1, 1.2)
    
    score = min(base_score * quality_factor, 1.0)
    
    return EvalMetric(
        metric_type=EvalMetricType.GROUNDEDNESS,
        score=round(score, 4),
        confidence=0.9,
        details={
            "evidence_count": evidence_count,
            "quality_factor": round(quality_factor, 2),
        },
    )


def calculate_relevancy(inputs: Dict[str, Any], outputs: Dict[str, Any]) -> EvalMetric:
    """
    Calculate relevancy score.
    
    Heuristic: Check if output contains key terms from input.
    """
    input_text = str(inputs).lower()
    output_text = str(outputs).lower()
    
    # Simple keyword overlap heuristic
    input_words = set(input_text.split())
    output_words = set(output_text.split())
    
    # Remove common stopwords
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being", 
                 "have", "has", "had", "do", "does", "did", "will", "would", "could",
                 "should", "may", "might", "can", "to", "of", "in", "for", "on", "with",
                 "at", "by", "from", "as", "or", "and", "but", "if", "then", "else"}
    
    input_keywords = input_words - stopwords
    output_keywords = output_words - stopwords
    
    if not input_keywords:
        return EvalMetric(
            metric_type=EvalMetricType.RELEVANCY,
            score=0.5,
            confidence=0.5,
            details={"reason": "No input keywords to compare"},
        )
    
    overlap = len(input_keywords & output_keywords)
    overlap_ratio = overlap / len(input_keywords)
    
    # Map overlap ratio to score (0.3 overlap = 0.6 score, 0.5+ = 0.9+)
    score = min(0.3 + overlap_ratio * 1.4, 1.0)
    
    return EvalMetric(
        metric_type=EvalMetricType.RELEVANCY,
        score=round(score, 4),
        confidence=0.7,
        details={
            "input_keyword_count": len(input_keywords),
            "overlap_count": overlap,
            "overlap_ratio": round(overlap_ratio, 4),
        },
    )


def calculate_completeness(outputs: Dict[str, Any], expected_fields: Optional[List[str]] = None) -> EvalMetric:
    """
    Calculate completeness score.
    
    Checks if outputs contain expected fields/structure.
    """
    if expected_fields is None:
        # Default expected fields for capsule outputs
        expected_fields = ["summary", "result", "content", "message", "data"]
    
    if not outputs:
        return EvalMetric(
            metric_type=EvalMetricType.COMPLETENESS,
            score=0.0,
            confidence=1.0,
            details={"reason": "Empty output"},
        )
    
    output_keys = set(outputs.keys()) if isinstance(outputs, dict) else set()
    
    # Check for expected fields
    fields_present = sum(1 for f in expected_fields if f in output_keys)
    field_score = fields_present / len(expected_fields) if expected_fields else 0.5
    
    # Check for non-empty content
    content_score = 0.0
    total_content_length = 0
    for v in outputs.values() if isinstance(outputs, dict) else [outputs]:
        if isinstance(v, str):
            total_content_length += len(v)
        elif isinstance(v, (list, dict)):
            total_content_length += len(str(v))
    
    # Content length heuristic (100+ chars = good)
    content_score = min(total_content_length / 100, 1.0)
    
    # Combined score
    score = (field_score * 0.3 + content_score * 0.7)
    
    return EvalMetric(
        metric_type=EvalMetricType.COMPLETENESS,
        score=round(score, 4),
        confidence=0.8,
        details={
            "fields_present": fields_present,
            "expected_fields": len(expected_fields),
            "content_length": total_content_length,
        },
    )


async def evaluate_capsule_run(run_id: str) -> Optional[LLMEvalResult]:
    """Evaluate a single CapsuleRun."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CapsuleRun).where(CapsuleRun.id == run_id)
        )
        run = result.scalar_one_or_none()
        
        if not run:
            return None
        
        metrics = []
        
        # Groundedness
        groundedness = calculate_groundedness(
            run.evidence_refs or [],
            str(run.summary or {}),
        )
        metrics.append(groundedness)
        
        # Relevancy
        relevancy = calculate_relevancy(
            run.inputs or {},
            run.summary or {},
        )
        metrics.append(relevancy)
        
        # Completeness
        completeness = calculate_completeness(run.summary or {})
        metrics.append(completeness)
        
        # Calculate overall score (weighted average)
        weights = {
            EvalMetricType.GROUNDEDNESS: 0.4,
            EvalMetricType.RELEVANCY: 0.35,
            EvalMetricType.COMPLETENESS: 0.25,
        }
        
        overall = sum(
            m.score * weights.get(m.metric_type, 0.33) 
            for m in metrics
        )
        
        token_count = 0
        if run.token_usage:
            token_count = run.token_usage.get("total_tokens", 0) or sum(run.token_usage.values())
        
        return LLMEvalResult(
            run_id=str(run.id),
            run_type="capsule_run",
            metrics=metrics,
            overall_score=round(overall, 4),
            evidence_count=len(run.evidence_refs or []),
            token_usage=token_count,
            latency_ms=run.latency_ms or 0,
            evaluated_at=datetime.utcnow(),
        )


async def get_eval_harness_summary(
    days: int = 7,
    *,
    session: Optional[AsyncSession] = None,
) -> EvalHarnessSummary:
    """Get summary metrics from evaluation harness."""
    from datetime import timedelta
    
    close_session = session is None
    if session is None:
        session = AsyncSessionLocal()
    
    try:
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=days)
        
        # Get recent capsule runs
        result = await session.execute(
            select(CapsuleRun).where(
                CapsuleRun.created_at >= period_start,
                CapsuleRun.status == "done",
            )
        )
        runs = result.scalars().all()
        
        if not runs:
            return EvalHarnessSummary(
                total_runs=0,
                avg_groundedness=0.0,
                avg_relevancy=0.0,
                avg_completeness=0.0,
                avg_overall=0.0,
                runs_with_human_feedback=0,
                human_feedback_avg=0.0,
                period_start=period_start.isoformat() + "Z",
                period_end=period_end.isoformat() + "Z",
            )
        
        # Calculate aggregate metrics
        groundedness_scores = []
        relevancy_scores = []
        completeness_scores = []
        
        for run in runs:
            g = calculate_groundedness(run.evidence_refs or [], str(run.summary or {}))
            r = calculate_relevancy(run.inputs or {}, run.summary or {})
            c = calculate_completeness(run.summary or {})
            
            groundedness_scores.append(g.score)
            relevancy_scores.append(r.score)
            completeness_scores.append(c.score)
        
        avg_g = sum(groundedness_scores) / len(groundedness_scores)
        avg_r = sum(relevancy_scores) / len(relevancy_scores)
        avg_c = sum(completeness_scores) / len(completeness_scores)
        avg_overall = (avg_g * 0.4 + avg_r * 0.35 + avg_c * 0.25)
        
        # Human feedback from template learning runs
        learning_result = await session.execute(
            select(TemplateLearningRun).where(
                TemplateLearningRun.created_at >= period_start,
                TemplateLearningRun.reward_score.isnot(None),
            )
        )
        learning_runs = learning_result.scalars().all()
        
        runs_with_feedback = len([r for r in learning_runs if r.feedback])
        feedback_scores = [r.reward_score for r in learning_runs if r.reward_score]
        avg_feedback = sum(feedback_scores) / len(feedback_scores) if feedback_scores else 0.0
        
        return EvalHarnessSummary(
            total_runs=len(runs),
            avg_groundedness=round(avg_g, 4),
            avg_relevancy=round(avg_r, 4),
            avg_completeness=round(avg_c, 4),
            avg_overall=round(avg_overall, 4),
            runs_with_human_feedback=runs_with_feedback,
            human_feedback_avg=round(avg_feedback, 4),
            period_start=period_start.isoformat() + "Z",
            period_end=period_end.isoformat() + "Z",
        )
    finally:
        if close_session:
            await session.close()


async def record_human_feedback(
    run_id: str,
    feedback_type: str,  # thumbs_up | thumbs_down | rating | comment
    value: Any,
    user_id: Optional[str] = None,
) -> bool:
    """
    Record human feedback for a learning run.
    
    Updates TemplateLearningRun.feedback JSONB field.
    """
    async with AsyncSessionLocal() as session:
        # Try to find matching template learning run
        result = await session.execute(
            select(TemplateLearningRun).where(
                TemplateLearningRun.run_id == run_id
            )
        )
        learning_run = result.scalar_one_or_none()
        
        if not learning_run:
            return False
        
        # Update feedback
        current_feedback = learning_run.feedback or {}
        current_feedback[feedback_type] = value
        current_feedback["recorded_at"] = datetime.utcnow().isoformat()
        if user_id:
            current_feedback["user_id"] = user_id
        
        learning_run.feedback = current_feedback
        
        # Update reward score based on feedback
        if feedback_type == "thumbs_up":
            learning_run.reward_score = min((learning_run.reward_score or 0.5) + 0.1, 1.0)
        elif feedback_type == "thumbs_down":
            learning_run.reward_score = max((learning_run.reward_score or 0.5) - 0.1, 0.0)
        elif feedback_type == "rating" and isinstance(value, (int, float)):
            # Scale 1-5 rating to 0-1
            learning_run.reward_score = (value - 1) / 4
        
        await session.commit()
        return True
