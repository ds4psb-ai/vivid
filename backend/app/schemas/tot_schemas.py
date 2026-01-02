"""
Tree of Thoughts (ToT) Schemas

다중 경로 전략 탐색을 위한 스키마.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class ThoughtStatus(str, Enum):
    """생각 노드 상태"""
    PENDING = "pending"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    PRUNED = "pruned"


class SearchStrategy(str, Enum):
    """탐색 전략"""
    BFS = "bfs"  # 너비 우선 탐색
    DFS = "dfs"  # 깊이 우선 탐색
    MCTS = "mcts"  # Monte Carlo Tree Search
    BEAM = "beam"  # Beam Search


class ThoughtNode(BaseModel):
    """
    생각 노드 (ToT Tree Node)
    
    각 노드는 하나의 전략/아이디어를 나타냄
    """
    node_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_id: Optional[str] = None
    depth: int = 0
    
    # 내용
    thought: str = Field(description="이 노드의 전략/아이디어")
    reasoning: Optional[str] = Field(None, description="도달 과정 설명")
    
    # 평가
    stpf_score: Optional[float] = Field(None, description="STPF 점수")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # 상태
    status: ThoughtStatus = ThoughtStatus.PENDING
    
    # 메타
    children_ids: List[str] = Field(default_factory=list)
    visits: int = 0  # MCTS용
    total_value: float = 0.0  # MCTS용
    
    @property
    def ucb1_score(self) -> float:
        """UCB1 점수 (MCTS용)"""
        import math
        if self.visits == 0:
            return float('inf')
        exploitation = self.total_value / self.visits
        exploration = math.sqrt(2 * math.log(self.visits + 1) / self.visits)
        return exploitation + exploration


class ToTTree(BaseModel):
    """
    생각의 나무 (Tree of Thoughts)
    
    전체 탐색 트리 구조
    """
    tree_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # 문제 정의
    problem: str = Field(description="해결할 문제")
    context: Optional[str] = Field(None, description="추가 컨텍스트")
    
    # 트리 구조
    root: Optional[ThoughtNode] = None
    nodes: Dict[str, ThoughtNode] = Field(default_factory=dict)
    
    # 설정
    max_depth: int = Field(default=3, ge=1, le=10)
    branching_factor: int = Field(default=3, ge=1, le=10)
    strategy: SearchStrategy = SearchStrategy.BFS
    
    # 결과
    best_path: List[str] = Field(default_factory=list)
    best_score: float = 0.0
    
    # 메타
    created_at: datetime = Field(default_factory=datetime.utcnow)
    iterations: int = 0
    
    def add_node(self, node: ThoughtNode) -> None:
        """노드 추가"""
        self.nodes[node.node_id] = node
        if node.parent_id and node.parent_id in self.nodes:
            parent = self.nodes[node.parent_id]
            if node.node_id not in parent.children_ids:
                parent.children_ids.append(node.node_id)
    
    def get_path(self, node_id: str) -> List[ThoughtNode]:
        """루트에서 해당 노드까지의 경로"""
        path = []
        current_id = node_id
        while current_id:
            if current_id in self.nodes:
                node = self.nodes[current_id]
                path.append(node)
                current_id = node.parent_id
            else:
                break
        return list(reversed(path))


class SimulationRequest(BaseModel):
    """ToT 시뮬레이션 요청"""
    problem: str = Field(..., min_length=1)
    context: Optional[str] = None
    strategy: SearchStrategy = SearchStrategy.BFS
    max_depth: int = Field(default=3, ge=1, le=5)
    branching_factor: int = Field(default=3, ge=1, le=5)
    max_iterations: int = Field(default=20, ge=1, le=100)
    
    # STPF 기준 점수
    base_inputs: Optional[Dict[str, float]] = None


class SimulationResult(BaseModel):
    """ToT 시뮬레이션 결과"""
    tree: ToTTree
    best_path: List[ThoughtNode]
    best_score: float
    total_nodes: int
    iterations: int
    strategy_used: SearchStrategy
    
    # 요약
    recommendation: str
    alternative_paths: List[List[str]] = Field(default_factory=list)


class ThoughtGenerationRequest(BaseModel):
    """생각 생성 요청 (LLM 호출용)"""
    parent_thought: str
    problem: str
    context: Optional[str] = None
    num_thoughts: int = Field(default=3, ge=1, le=5)


class ThoughtEvaluationRequest(BaseModel):
    """생각 평가 요청"""
    thought: str
    problem: str
    path_so_far: List[str] = Field(default_factory=list)
