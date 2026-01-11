"""
Feedback Loop API Router

피드백 루프 API 엔드포인트.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.services.feedback_processor import feedback_processor
from app.dependencies import get_current_user, require_admin
from app.schemas.feedback_schemas import (
    ProductionResult, UserFeedback, ResultOutcome,
    FeedbackSummary, LearningCycle,
)
from app.schemas.director_pack import DNAInvariant, InvariantType, RuleSpec

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["Feedback Loop"])


# =========================================================================
# Request Models
# =========================================================================

class ProductionResultRequest(BaseModel):
    """프로덕션 결과 요청"""
    capsule_id: Optional[str] = None
    run_id: Optional[str] = None
    outcome: str = Field(default="success", pattern="^(success|partial|failure)$")
    score: Optional[float] = Field(None, ge=0.0, le=100.0)
    rule_ids: list[str] = Field(default_factory=list)
    metrics: dict = Field(default_factory=dict)


class UserFeedbackRequest(BaseModel):
    """사용자 피드백 요청"""
    capsule_id: Optional[str] = None
    run_id: Optional[str] = None
    user_id: Optional[str] = None
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class MetricUpdateRequest(BaseModel):
    """메트릭 업데이트 요청"""
    rule_id: str
    metric_name: str
    metric_value: float
    threshold: float


class RuleRegistrationRequest(BaseModel):
    """규칙 등록 요청"""
    rule_id: str
    rule_type: str = "engagement"
    name: str
    condition: str
    spec_operator: str = "gt"
    spec_value: float = 0.5
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


# =========================================================================
# Endpoints
# =========================================================================

@router.post("/production-result")
async def process_production_result(
    request: ProductionResultRequest,
    user: dict = Depends(get_current_user),  # P1: Auth required
):
    """프로덕션 결과 처리"""
    logger.info(f"Processing production result: {request.outcome}")
    
    result = ProductionResult(
        capsule_id=request.capsule_id,
        run_id=request.run_id,
        outcome=ResultOutcome(request.outcome),
        score=request.score,
        rule_ids=request.rule_ids,
        metrics=request.metrics,
    )
    
    updates = feedback_processor.process_production_result(result)
    
    return {
        "result_id": result.result_id,
        "outcome": result.outcome.value,
        "updates": [u.model_dump() for u in updates],
        "rules_updated": len(updates),
    }


@router.post("/user-feedback")
async def process_user_feedback(
    request: UserFeedbackRequest,
    user: dict = Depends(get_current_user),  # P1: Auth required
):
    """사용자 피드백 처리"""
    logger.info(f"Processing user feedback: rating={request.rating}")
    
    feedback = UserFeedback(
        capsule_id=request.capsule_id,
        run_id=request.run_id,
        user_id=request.user_id,
        rating=request.rating,
        comment=request.comment,
    )
    
    updates = feedback_processor.process_user_feedback(feedback)
    
    return {
        "feedback_id": feedback.feedback_id,
        "rating": feedback.rating,
        "updates": [u.model_dump() for u in updates],
        "rules_updated": len(updates),
    }


@router.post("/metric-update")
async def process_metric_update(
    request: MetricUpdateRequest,
    user: dict = Depends(require_admin),  # P1: Admin only
):
    """메트릭 업데이트 처리"""
    logger.info(f"Processing metric: {request.metric_name}={request.metric_value}")
    
    update = feedback_processor.process_metric_update(
        rule_id=request.rule_id,
        metric_name=request.metric_name,
        metric_value=request.metric_value,
        threshold=request.threshold,
    )
    
    if update:
        return {
            "rule_id": request.rule_id,
            "metric": request.metric_name,
            "update": update.model_dump(),
        }
    else:
        return {
            "rule_id": request.rule_id,
            "error": "Rule not found",
        }


@router.post("/register-rule")
async def register_rule(
    request: RuleRegistrationRequest,
    user: dict = Depends(require_admin),  # P1: Admin only
):
    """학습용 규칙 등록"""
    rule = DNAInvariant(
        rule_id=request.rule_id,
        rule_type=InvariantType(request.rule_type),
        name=request.name,
        condition=request.condition,
        spec=RuleSpec(operator=request.spec_operator, value=request.spec_value),
        confidence=request.confidence,
    )
    
    feedback_processor.register_rule(rule)
    
    return {
        "rule_id": rule.rule_id,
        "confidence": rule.confidence,
        "registered": True,
    }


@router.get("/rules")
async def list_rules():
    """등록된 규칙 목록"""
    rules = feedback_processor.get_all_rules()
    return {
        "rules": [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "confidence": r.confidence,
                "evidence_count": r.evidence_count,
            }
            for r in rules
        ],
        "total": len(rules),
    }


@router.get("/rules/{rule_id}")
async def get_rule(rule_id: str):
    """규칙 상세 조회"""
    rule = feedback_processor.get_rule(rule_id)
    if rule:
        return rule.model_dump()
    return {"error": "Rule not found"}


# =========================================================================
# Learning Cycle
# =========================================================================

@router.post("/cycle/start")
async def start_cycle():
    """학습 싸이클 시작"""
    cycle = feedback_processor.start_cycle()
    return {
        "cycle_id": cycle.cycle_id,
        "start_time": cycle.start_time.isoformat(),
        "status": cycle.status,
    }


@router.post("/cycle/complete")
async def complete_cycle():
    """학습 싸이클 완료"""
    cycle = feedback_processor.complete_cycle()
    if cycle:
        return {
            "cycle_id": cycle.cycle_id,
            "status": cycle.status,
            "events": cycle.event_count,
            "rules_updated": cycle.rules_updated,
            "avg_confidence_change": cycle.avg_confidence_change,
        }
    return {"error": "No active cycle"}


@router.get("/summary", response_model=FeedbackSummary)
async def get_summary():
    """현재 피드백 요약"""
    return feedback_processor.get_summary()


@router.get("/health")
async def health():
    """피드백 프로세서 상태"""
    summary = feedback_processor.get_summary()
    return {
        "status": "ok",
        "engine": "FeedbackProcessor",
        "version": "1.0.0",
        "total_events": summary.total_events,
        "rules_registered": len(feedback_processor.get_all_rules()),
        "active_cycle": feedback_processor.current_cycle is not None,
    }
