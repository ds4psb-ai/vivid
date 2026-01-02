"""
Bayesian Truth API Router

베이지안 신뢰도 갱신 API 엔드포인트.
"""
from typing import List
from fastapi import APIRouter, HTTPException
from app.schemas.director_pack import DNAInvariant
from app.schemas.bayesian_schemas import (
    Evidence,
    ConfidenceUpdate,
    BayesianUpdateRequest,
    BayesianUpdateResponse,
    BulkUpdateRequest,
    BulkUpdateResponse,
)
from app.services.bayesian_engine import bayesian_engine

router = APIRouter(prefix="/bayesian", tags=["Bayesian Truth"])


@router.post("/update", response_model=BayesianUpdateResponse)
async def update_confidence(request: BayesianUpdateRequest):
    """
    단일 DNAInvariant 신뢰도 갱신
    
    베이지안 갱신 공식:
    P(H|E) = P(E|H) × P(H)^α / Normalization
    """
    # 테스트용 기본 invariant 생성 (실제로는 DB에서 조회)
    from app.schemas.director_pack import InvariantType, RuleSpec, RulePriority
    
    invariant = DNAInvariant(
        rule_id=request.rule_id,
        rule_type=InvariantType.TIMING,
        name="Test Rule",
        condition="test_condition",
        spec=RuleSpec(operator="gt", value=0),
        priority=RulePriority.MEDIUM,
        confidence=0.5,
        prior_strength=1.0,
        evidence_count=0,
    )
    
    try:
        updated_inv, update = bayesian_engine.update_confidence(invariant, request.evidence)
        return BayesianUpdateResponse(
            update=update,
            message=f"신뢰도 갱신 완료: {update.prior:.3f} → {update.posterior:.3f}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/demo", response_model=ConfidenceUpdate)
async def demo_update(
    supports_rule: bool = True,
    strength: float = 1.0,
    prior: float = 0.5,
    prior_strength: float = 1.0,
):
    """
    베이지안 갱신 데모
    
    파라미터를 조정하여 갱신 결과를 확인할 수 있음
    """
    from app.schemas.director_pack import InvariantType, RuleSpec, RulePriority
    from datetime import datetime
    import uuid
    
    # 테스트 invariant
    invariant = DNAInvariant(
        rule_id="demo_rule",
        rule_type=InvariantType.TIMING,
        name="Demo Rule",
        condition="demo_condition",
        spec=RuleSpec(operator="gt", value=0),
        priority=RulePriority.MEDIUM,
        confidence=prior,
        prior_strength=prior_strength,
        evidence_count=0,
    )
    
    # 테스트 evidence
    evidence = Evidence(
        evidence_id=str(uuid.uuid4()),
        rule_id="demo_rule",
        evidence_type="user_feedback",
        supports_rule=supports_rule,
        strength=strength,
    )
    
    _, update = bayesian_engine.update_confidence(invariant, evidence)
    return update


@router.get("/health")
async def health():
    """Bayesian Engine 상태 확인"""
    return {
        "status": "ok",
        "engine": "BayesianTruthEngine",
        "version": "1.0.0",
        "min_confidence": bayesian_engine.MIN_CONFIDENCE,
        "max_confidence": bayesian_engine.MAX_CONFIDENCE,
    }
