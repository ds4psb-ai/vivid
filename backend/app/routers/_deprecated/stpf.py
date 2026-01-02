"""STPF v3.1 API Router - Single Truth Pattern Formalization."""
from fastapi import APIRouter

from app.schemas.stpf_schemas import (
    ScenarioResult,
    SensitivityResult,
    STPFComputeRequest,
    STPFResult,
)
from app.services.stpf_engine import stpf_engine

router = APIRouter(prefix="/stpf", tags=["stpf"])


@router.post("/compute", response_model=STPFResult)
async def compute_stpf(request: STPFComputeRequest) -> STPFResult:
    """
    STPF v3.1 점수 계산
    
    Safe Math 적용:
    - Division-by-zero 방지
    - Vanishing gradient 방지
    - Log-sigmoid 스케일링
    """
    return stpf_engine.compute(request.inputs)


@router.post("/sensitivity", response_model=SensitivityResult)
async def analyze_sensitivity(request: STPFComputeRequest) -> SensitivityResult:
    """
    민감도 분석
    
    Returns:
    - leverage_point: +1점 시 가장 큰 점수 증가 변수
    - fatal_friction: 마찰 -1점 시 가장 큰 점수 증가 변수
    """
    return stpf_engine.sensitivity(request.inputs)


@router.post("/scenarios", response_model=ScenarioResult)
async def simulate_scenarios(request: STPFComputeRequest) -> ScenarioResult:
    """
    3분기 시나리오 시뮬레이션
    
    Returns:
    - worst: 최악 시나리오 (n-2, d+2)
    - base: 현재 상태
    - best: 최선 시나리오 (n+2, d-2)
    - final_recommendation_score: 0.3*worst + 0.4*base + 0.3*best
    """
    return stpf_engine.scenarios(request.inputs)
