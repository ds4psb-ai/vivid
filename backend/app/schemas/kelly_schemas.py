"""
Kelly Criterion Schemas

Kelly 기반 자원 배분을 위한 스키마.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class KellyResult(BaseModel):
    """Kelly Criterion 계산 결과"""
    success_probability: float = Field(
        ge=0.0, le=1.0,
        description="성공 확률 (베이지안 posterior)"
    )
    reward_ratio: float = Field(
        ge=0.0,
        description="성공 시 보상 비율 (b = upside/downside)"
    )
    f_star: float = Field(
        description="최적 Kelly 비율 (음수면 투자 X)"
    )
    f_safe: float = Field(
        ge=0.0, le=1.0,
        description="안전 Kelly 비율 (50% 적용)"
    )
    edge: float = Field(
        description="기대 에지 (bp - q)"
    )
    recommendation: str = Field(
        description="투자 권장 사항"
    )


class CreditAllocation(BaseModel):
    """크레딧 배분 결과"""
    user_balance: int = Field(description="현재 잔여 크레딧")
    base_cost: int = Field(description="단위 작업 비용")
    
    # Kelly 결과
    kelly: KellyResult
    
    # 권장 배분
    max_safe_investment: int = Field(
        description="Kelly 기준 최대 안전 투자 크레딧"
    )
    recommended_runs: int = Field(
        description="권장 실행 횟수"
    )
    bankruptcy_probability: float = Field(
        ge=0.0, le=1.0,
        description="파산 확률 (0.05 이하 목표)"
    )


class AllocationRequest(BaseModel):
    """배분 요청"""
    user_id: str
    capsule_id: Optional[str] = None
    model: str = Field(default="gemini-2.0-flash-exp")
    success_probability: Optional[float] = Field(
        default=None,
        description="외부 제공 성공확률 (없으면 히스토리에서 추정)"
    )
    reward_ratio: float = Field(
        default=2.0,
        description="성공 시 보상 비율"
    )


class AllocationResponse(BaseModel):
    """배분 응답"""
    allocation: CreditAllocation
    message: str


class BatchAllocationRequest(BaseModel):
    """다중 캡슐 배분 요청"""
    user_id: str
    capsule_ids: List[str]
    model: str = Field(default="gemini-2.0-flash-exp")
