"""
CT Dashboard API Router

프론트엔드용 통합 대시보드 API.
모든 CT Architecture 데이터를 한 곳에서 제공.
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user

from app.services.stpf_engine import stpf_engine
from app.services.bayesian_engine import bayesian_engine
from app.services.kelly_allocator import kelly_allocator
from app.services.tot_simulator import tot_simulator
from app.services.feedback_processor import feedback_processor
from app.mcp_servers.pattern_truth_mcp import pattern_truth_mcp

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# =========================================================================
# Response Models
# =========================================================================

class CTSummary(BaseModel):
    """CT 아키텍처 요약"""
    # 시스템 상태
    status: str = "healthy"
    version: str = "1.0.0"
    
    # 엔진 현황
    engines: Dict[str, bool]
    
    # 통계
    total_rules_tracked: int
    total_feedback_events: int
    active_learning_cycle: bool
    
    # Kelly 현황
    kelly_fraction: float
    recommended_action: str


class ConfidenceChartData(BaseModel):
    """신뢰도 차트 데이터"""
    rule_id: str
    rule_name: str
    confidences: List[float]  # 시간순
    timestamps: List[str]
    current: float
    trend: str  # up, down, stable


class KellyDashboard(BaseModel):
    """Kelly 대시보드"""
    balance: int
    kelly_fraction: float
    max_safe_investment: int
    recommended_runs: int
    bankruptcy_probability: float
    success_probability: float
    recommendation: str


class FeedbackStats(BaseModel):
    """피드백 통계"""
    total_events: int
    events_by_type: Dict[str, int]
    success_rate: float
    avg_score: Optional[float]
    confidence_trend: str


# =========================================================================
# Endpoints
# =========================================================================

@router.get("/summary", response_model=CTSummary)
async def get_ct_summary(
    user: dict = Depends(get_current_user),
):
    """CT 아키텍처 전체 요약"""
    # 피드백 요약
    feedback_summary = feedback_processor.get_summary()
    
    # 기본 Kelly (데모용)
    kelly_result = kelly_allocator.calculate_allocation(
        user_balance=1000,
        base_cost=10,
        success_probability=0.7,
        reward_ratio=2.0,
    )
    
    return CTSummary(
        status="healthy",
        version="1.0.0",
        engines={
            "stpf": True,
            "bayesian": True,
            "kelly": True,
            "tot": True,
            "feedback": True,
            "mcp": True,
        },
        total_rules_tracked=len(feedback_processor.get_all_rules()),
        total_feedback_events=feedback_summary.total_events,
        active_learning_cycle=feedback_processor.current_cycle is not None,
        kelly_fraction=kelly_result.kelly.f_safe,
        recommended_action=kelly_result.kelly.recommendation,
    )


@router.get("/confidence-chart")
async def get_confidence_chart(
    limit: int = 10,
) -> Dict[str, Any]:
    """신뢰도 차트 데이터"""
    rules = feedback_processor.get_all_rules()
    
    chart_data = []
    for rule in rules[:limit]:
        chart_data.append({
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "current_confidence": rule.confidence,
            "evidence_count": rule.evidence_count,
            "trend": "stable",  # TODO: 실제 트렌드 계산
        })
    
    return {
        "rules": chart_data,
        "total_rules": len(rules),
    }


@router.get("/kelly")
async def get_kelly_dashboard(
    balance: int = 1000,
    cost_per_run: int = 10,
    user: dict = Depends(get_current_user),
) -> KellyDashboard:
    """Kelly 대시보드"""
    # 성공 확률 (피드백 기반)
    feedback_summary = feedback_processor.get_summary()
    success_prob = feedback_summary.success_rate if feedback_summary.total_events > 0 else 0.7
    
    result = kelly_allocator.calculate_allocation(
        user_balance=balance,
        base_cost=cost_per_run,
        success_probability=max(0.1, min(0.9, success_prob)),
        reward_ratio=2.0,
    )
    
    return KellyDashboard(
        balance=balance,
        kelly_fraction=result.kelly.f_safe,
        max_safe_investment=result.max_safe_investment,
        recommended_runs=result.recommended_runs,
        bankruptcy_probability=result.bankruptcy_probability,
        success_probability=success_prob,
        recommendation=result.kelly.recommendation,
    )


@router.get("/feedback-stats", response_model=FeedbackStats)
async def get_feedback_stats():
    """피드백 통계"""
    summary = feedback_processor.get_summary()
    
    return FeedbackStats(
        total_events=summary.total_events,
        events_by_type=summary.events_by_type,
        success_rate=summary.success_rate,
        avg_score=summary.avg_score,
        confidence_trend=summary.confidence_trend,
    )


@router.get("/stpf/quick-score")
async def quick_stpf_score(
    trust: float = 7.0,
    legality: float = 8.0,
    hygiene: float = 6.0,
    essence: float = 7.0,
    capability: float = 6.0,
) -> Dict[str, Any]:
    """빠른 STPF 점수 계산"""
    from app.schemas.stpf_schemas import STPFInputs
    
    inputs = STPFInputs(
        trust=trust,
        legality=legality,
        hygiene=hygiene,
        essence=essence,
        capability=capability,
    )
    
    result = stpf_engine.compute(inputs)
    
    return {
        "score": round(result.score_1000, 1),
        "grade": result.grade,
        "status": result.status,
        "p_success": round(result.p_success, 3),
        "kelly_recommendation": result.kelly.recommendation,
    }


@router.get("/tot/quick-simulate")
async def quick_tot_simulate(
    problem: str = "최적 영상 제작 전략",
    strategy: str = "bfs",
    max_depth: int = 2,
) -> Dict[str, Any]:
    """빠른 ToT 시뮬레이션"""
    from app.schemas.tot_schemas import SimulationRequest, SearchStrategy
    
    request = SimulationRequest(
        problem=problem,
        strategy=SearchStrategy(strategy),
        max_depth=max_depth,
        max_iterations=15,
    )
    
    result = tot_simulator.simulate(request)
    
    return {
        "best_score": result.best_score,
        "total_nodes": result.total_nodes,
        "recommendation": result.recommendation,
        "best_path": [n.thought for n in result.best_path],
    }


@router.get("/mcp/tools")
async def list_mcp_tools() -> Dict[str, Any]:
    """MCP 도구 목록"""
    tools = pattern_truth_mcp.list_tools()
    
    return {
        "server": pattern_truth_mcp.name,
        "version": pattern_truth_mcp.version,
        "tools": [
            {
                "name": t.name,
                "description": t.description,
            }
            for t in tools
        ],
    }


@router.get("/health")
async def dashboard_health():
    """대시보드 상태"""
    return {
        "status": "healthy",
        "components": {
            "stpf": "ok",
            "bayesian": "ok",
            "kelly": "ok",
            "tot": "ok",
            "feedback": "ok",
            "mcp": "ok",
        },
        "routes_available": [
            "/dashboard/summary",
            "/dashboard/confidence-chart",
            "/dashboard/kelly",
            "/dashboard/feedback-stats",
            "/dashboard/stpf/quick-score",
            "/dashboard/tot/quick-simulate",
            "/dashboard/mcp/tools",
        ],
    }
