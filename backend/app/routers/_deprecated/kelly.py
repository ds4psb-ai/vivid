"""
Kelly Credit Allocation API Router

Kelly Criterion 기반 크레딧 배분 API 엔드포인트.
"""
from fastapi import APIRouter
from app.schemas.kelly_schemas import (
    KellyResult,
    CreditAllocation,
    AllocationRequest,
    AllocationResponse,
)
from app.services.kelly_allocator import kelly_allocator

router = APIRouter(prefix="/kelly", tags=["Kelly Credit"])


@router.post("/calculate", response_model=KellyResult)
async def calculate_kelly(
    success_probability: float = 0.6,
    reward_ratio: float = 2.0,
):
    """
    Kelly Criterion 계산
    
    f* = (bp - q) / b
    """
    return kelly_allocator.calculate_kelly(success_probability, reward_ratio)


@router.post("/allocate", response_model=AllocationResponse)
async def allocate_credits(request: AllocationRequest):
    """
    크레딧 배분 계산
    
    Kelly 기준으로 최적 투자 비율과 권장 실행 횟수 계산
    """
    # 테스트용 기본값 (실제로는 DB에서 조회)
    user_balance = 1000
    base_cost = kelly_allocator.get_model_cost(request.model)
    success_prob = request.success_probability or 0.6
    
    allocation = kelly_allocator.calculate_allocation(
        user_balance=user_balance,
        base_cost=base_cost,
        success_probability=success_prob,
        reward_ratio=request.reward_ratio,
    )
    
    return AllocationResponse(
        allocation=allocation,
        message=f"Kelly 배분 계산 완료: 권장 {allocation.recommended_runs}회 실행"
    )


@router.get("/demo")
async def demo_allocation(
    balance: int = 1000,
    cost: int = 10,
    success_prob: float = 0.6,
    reward_ratio: float = 2.0,
):
    """
    Kelly 배분 데모
    
    파라미터를 조정하여 결과를 확인할 수 있음
    """
    allocation = kelly_allocator.calculate_allocation(
        user_balance=balance,
        base_cost=cost,
        success_probability=success_prob,
        reward_ratio=reward_ratio,
    )
    
    return {
        "kelly_fraction": allocation.kelly.f_safe,
        "max_safe_investment": allocation.max_safe_investment,
        "recommended_runs": allocation.recommended_runs,
        "bankruptcy_probability": allocation.bankruptcy_probability,
        "recommendation": allocation.kelly.recommendation,
    }


@router.get("/optimal-batch")
async def get_optimal_batch(
    balance: int = 1000,
    cost: int = 10,
    success_prob: float = 0.7,
    target_ruin_prob: float = 0.05,
):
    """
    목표 파산 확률을 만족하는 최적 배치 크기
    """
    batch_size = kelly_allocator.calculate_optimal_batch_size(
        user_balance=balance,
        base_cost=cost,
        success_probability=success_prob,
        target_ruin_prob=target_ruin_prob,
    )
    
    return {
        "optimal_batch_size": batch_size,
        "target_ruin_probability": target_ruin_prob,
        "total_cost": batch_size * cost,
    }


@router.get("/health")
async def health():
    """Kelly Allocator 상태 확인"""
    return {
        "status": "ok",
        "engine": "KellyBasedCreditAllocator",
        "version": "1.0.0",
        "kelly_fraction": kelly_allocator.KELLY_FRACTION,
        "default_costs": kelly_allocator.DEFAULT_COSTS,
    }
