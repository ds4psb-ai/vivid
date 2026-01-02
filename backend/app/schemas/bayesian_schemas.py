"""
Bayesian Truth Engine Schemas

Evidence and confidence update models for the Bayesian Truth System.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class Evidence(BaseModel):
    """
    증거 데이터 모델
    
    DNAInvariant의 신뢰도를 갱신하는 데 사용됨
    """
    evidence_id: str = Field(description="고유 증거 ID")
    rule_id: str = Field(description="관련 DNAInvariant rule_id")
    
    # Evidence Type
    evidence_type: Literal["production_result", "user_feedback", "metric", "expert"] = Field(
        description="증거 유형"
    )
    
    # Support or Refute
    supports_rule: bool = Field(
        description="True면 규칙 지지, False면 규칙 반박"
    )
    strength: float = Field(
        default=1.0, ge=0.0, le=1.0,
        description="증거 강도 (1.0 = 강력한 증거)"
    )
    
    # Source
    source_id: Optional[str] = Field(default=None, description="증거 출처 ID")
    source_description: Optional[str] = Field(default=None, description="증거 설명")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConfidenceUpdate(BaseModel):
    """베이지안 갱신 결과"""
    rule_id: str
    prior: float = Field(description="갱신 전 신뢰도")
    posterior: float = Field(description="갱신 후 신뢰도")
    delta: float = Field(description="변화량 (posterior - prior)")
    evidence_count: int = Field(description="총 증거 수")
    likelihood: float = Field(description="우도 (P(E|H))")


class BayesianUpdateRequest(BaseModel):
    """베이지안 갱신 요청"""
    rule_id: str
    evidence: Evidence


class BayesianUpdateResponse(BaseModel):
    """베이지안 갱신 응답"""
    update: ConfidenceUpdate
    message: str


class BulkUpdateRequest(BaseModel):
    """다중 증거 일괄 갱신 요청"""
    pack_id: str
    evidences: List[Evidence]


class BulkUpdateResponse(BaseModel):
    """다중 증거 일괄 갱신 응답"""
    updates: List[ConfidenceUpdate]
    total_rules_updated: int
    average_delta: float
