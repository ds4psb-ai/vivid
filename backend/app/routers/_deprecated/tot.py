"""
ToT (Tree of Thoughts) API Router

다중 경로 전략 탐색 API 엔드포인트.
"""
import logging
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.tot_simulator import tot_simulator
from app.schemas.tot_schemas import (
    SearchStrategy, SimulationRequest, SimulationResult,
    ThoughtNode, ToTTree,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tot", tags=["ToT Simulator"])


# =========================================================================
# Request/Response Models
# =========================================================================

class QuickSimulationRequest(BaseModel):
    """빠른 시뮬레이션 요청"""
    problem: str = Field(..., min_length=1, max_length=1000)
    context: Optional[str] = None
    strategy: str = Field(default="bfs", pattern="^(bfs|dfs|mcts|beam)$")
    max_depth: int = Field(default=3, ge=1, le=5)
    max_iterations: int = Field(default=20, ge=1, le=50)


class SimulationSummary(BaseModel):
    """시뮬레이션 요약"""
    tree_id: str
    problem: str
    strategy: str
    best_score: float
    best_path: list[str]
    total_nodes: int
    iterations: int
    recommendation: str


# =========================================================================
# Endpoints
# =========================================================================

@router.post("/simulate", response_model=SimulationSummary)
async def simulate(request: QuickSimulationRequest):
    """
    ToT 시뮬레이션 실행
    
    다중 경로를 탐색하여 최적 전략을 찾음
    """
    logger.info(f"ToT simulate: problem={request.problem[:50]}..., strategy={request.strategy}")
    
    # 전략 변환
    strategy_map = {
        "bfs": SearchStrategy.BFS,
        "dfs": SearchStrategy.DFS,
        "mcts": SearchStrategy.MCTS,
        "beam": SearchStrategy.BEAM,
    }
    
    sim_request = SimulationRequest(
        problem=request.problem,
        context=request.context,
        strategy=strategy_map[request.strategy],
        max_depth=request.max_depth,
        max_iterations=request.max_iterations,
    )
    
    result = tot_simulator.simulate(sim_request)
    
    return SimulationSummary(
        tree_id=result.tree.tree_id,
        problem=request.problem,
        strategy=request.strategy,
        best_score=result.best_score,
        best_path=[n.thought for n in result.best_path],
        total_nodes=result.total_nodes,
        iterations=result.iterations,
        recommendation=result.recommendation,
    )


@router.post("/simulate/full", response_model=SimulationResult)
async def simulate_full(request: QuickSimulationRequest):
    """
    ToT 시뮬레이션 (전체 결과)
    
    트리 전체 구조 포함
    """
    strategy_map = {
        "bfs": SearchStrategy.BFS,
        "dfs": SearchStrategy.DFS,
        "mcts": SearchStrategy.MCTS,
        "beam": SearchStrategy.BEAM,
    }
    
    sim_request = SimulationRequest(
        problem=request.problem,
        context=request.context,
        strategy=strategy_map[request.strategy],
        max_depth=request.max_depth,
        max_iterations=request.max_iterations,
    )
    
    return tot_simulator.simulate(sim_request)


@router.get("/strategies")
async def list_strategies():
    """사용 가능한 탐색 전략 목록"""
    return {
        "strategies": [
            {
                "name": "bfs",
                "description": "너비 우선 탐색 - 같은 깊이 노드 먼저",
                "best_for": "넓은 탐색, 최단 경로",
            },
            {
                "name": "dfs",
                "description": "깊이 우선 탐색 - 깊은 노드 먼저",
                "best_for": "깊은 전략, 메모리 효율",
            },
            {
                "name": "mcts",
                "description": "Monte Carlo Tree Search - 확률적 탐색",
                "best_for": "불확실성 높은 문제, 게임",
            },
            {
                "name": "beam",
                "description": "Beam Search - 상위 K개만 유지",
                "best_for": "대규모 탐색 공간",
            },
        ]
    }


@router.post("/compare")
async def compare_strategies(
    problem: str,
    context: Optional[str] = None,
    max_depth: int = 2,
    max_iterations: int = 10,
):
    """
    모든 전략 비교
    
    동일 문제에 대해 4가지 전략 결과 비교
    """
    results = {}
    
    for strategy in ["bfs", "dfs", "mcts", "beam"]:
        strategy_enum = SearchStrategy(strategy)
        request = SimulationRequest(
            problem=problem,
            context=context,
            strategy=strategy_enum,
            max_depth=max_depth,
            max_iterations=max_iterations,
        )
        
        result = tot_simulator.simulate(request)
        
        results[strategy] = {
            "best_score": result.best_score,
            "total_nodes": result.total_nodes,
            "iterations": result.iterations,
            "recommendation": result.recommendation,
        }
    
    # 최고 전략 찾기
    best_strategy = max(results.items(), key=lambda x: x[1]["best_score"])
    
    return {
        "problem": problem,
        "results": results,
        "best_strategy": best_strategy[0],
        "best_score": best_strategy[1]["best_score"],
    }


@router.get("/health")
async def health():
    """ToT 시뮬레이터 상태"""
    return {
        "status": "ok",
        "engine": "ToTSimulator",
        "version": "1.0.0",
        "strategies": ["bfs", "dfs", "mcts", "beam"],
    }
