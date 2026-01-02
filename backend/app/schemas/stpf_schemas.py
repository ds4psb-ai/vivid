"""STPF v3.1 Schemas - Single Truth Pattern Formalization Engine."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class STPFInputs(BaseModel):
    """STPF v3.1 입력 변수 (1~10 스케일)"""
    
    # Gates (Kill Switch)
    trust: float = Field(5.0, ge=1.0, le=10.0, alias="Trust")
    legality: float = Field(10.0, ge=1.0, le=10.0, alias="Legality")
    hygiene: float = Field(8.0, ge=1.0, le=10.0, alias="Hygiene")
    
    # Numerator: Value
    essence: float = Field(5.0, ge=1.0, le=10.0, alias="E")
    capability: float = Field(5.0, ge=1.0, le=10.0, alias="K")
    novelty: float = Field(5.0, ge=1.0, le=10.0, alias="Nv")
    connection: float = Field(5.0, ge=1.0, le=10.0, alias="Cn")
    proof: float = Field(5.0, ge=1.0, le=10.0, alias="Prf")
    
    # Denominator: Friction (높을수록 나쁨)
    cost: float = Field(5.0, ge=1.0, le=10.0, alias="Cost")
    risk: float = Field(5.0, ge=1.0, le=10.0, alias="Risk")
    threat: float = Field(5.0, ge=1.0, le=10.0, alias="Threat")
    pressure: float = Field(5.0, ge=1.0, le=10.0, alias="Pressure")
    lag: float = Field(5.0, ge=1.0, le=10.0, alias="Lag")
    uncertainty: float = Field(5.0, ge=1.0, le=10.0, alias="Uncertainty")
    
    # Multipliers
    network: float = Field(5.0, ge=1.0, le=10.0, alias="Network")
    scarcity: float = Field(5.0, ge=1.0, le=10.0, alias="Scarcity")
    leverage: float = Field(5.0, ge=1.0, le=10.0, alias="Leverage")
    
    # Context (Gap)
    expectation: float = Field(5.0, ge=1.0, le=10.0, alias="Expectation")
    reality: float = Field(5.0, ge=1.0, le=10.0, alias="Reality")
    
    # Optional
    upside: Optional[float] = Field(None, alias="Upside")
    downside: Optional[float] = Field(None, alias="Downside")
    capital: Optional[float] = Field(None, alias="Capital")
    confidence: Optional[float] = Field(None, ge=1.0, le=10.0, alias="Confidence")
    
    model_config = {"populate_by_name": True}


class KellyResult(BaseModel):
    """Kelly Criterion 결과"""
    b: Optional[float] = Field(None, description="Odds ratio (Upside/Downside)")
    f: Optional[float] = Field(None, description="Full Kelly fraction")
    f_safe: Optional[float] = Field(None, description="Half Kelly (conservative)")


class MultipliersResult(BaseModel):
    """승수 결과"""
    s_boost: float = Field(description="Scarcity boost")
    lv_boost: float = Field(description="Leverage boost")
    nw_boost: float = Field(description="Network boost")
    entropy_boost: float = Field(description="Entropy/Gap boost")
    gap: float = Field(description="Reality - Expectation gap")


class STPFResult(BaseModel):
    """STPF v3.1 계산 결과"""
    status: Literal["OK", "GATE_FAIL", "MISSING_KEYS"]
    raw_score: float = Field(0.0, description="Raw computed score")
    score_1000: float = Field(0.0, ge=0.0, le=1000.0, description="Normalized 0~1000 score")
    p_success: float = Field(0.0, ge=0.0, le=1.0, description="Probability of success")
    
    # Components
    gate_factor: float = Field(0.0, description="Gate soft factor")
    gate_min: Optional[float] = Field(None, description="Minimum gate value (if failed)")
    v: float = Field(0.0, description="Numerator value")
    f_total: float = Field(0.0, description="Denominator friction total")
    f_eff: float = Field(0.0, description="Effective friction (after exponent)")
    
    # Multipliers
    multipliers: Optional[MultipliersResult] = None
    
    # Kelly
    kelly: KellyResult = Field(default_factory=KellyResult)
    
    # Grade
    grade: Optional[str] = None
    
    def model_post_init(self, __context):
        """Auto-calculate grade based on score_1000"""
        if self.grade is None and self.status == "OK":
            if self.score_1000 >= 800:
                self.grade = "Unicorn"
            elif self.score_1000 >= 500:
                self.grade = "High Potential"
            elif self.score_1000 >= 250:
                self.grade = "Average"
            else:
                self.grade = "Death Valley"


class SensitivityResult(BaseModel):
    """민감도 분석 결과"""
    status: str
    base_score: float
    leverage_point: Dict[str, Any] = Field(
        description="+1점 시 가장 큰 점수 증가 변수"
    )
    fatal_friction: Dict[str, Any] = Field(
        description="-1점 시 가장 큰 점수 증가 변수 (마찰 감소)"
    )
    deltas_up: Dict[str, float] = Field(default_factory=dict)
    deltas_down: Dict[str, float] = Field(default_factory=dict)


class ScenarioResult(BaseModel):
    """시나리오 분석 결과"""
    worst: STPFResult
    base: STPFResult
    best: STPFResult
    final_recommendation_score: float = Field(
        description="0.3*worst + 0.4*base + 0.3*best"
    )


class STPFComputeRequest(BaseModel):
    """STPF 계산 요청"""
    inputs: STPFInputs
    domain: Optional[str] = Field(None, description="분석 도메인")
    evidence: Optional[List[str]] = Field(None, description="Evidence refs")
