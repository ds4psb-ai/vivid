"""
Tree of Thoughts (ToT) Simulator

다중 경로 전략 탐색 시뮬레이터.
BFS, DFS, MCTS, Beam Search 지원.

Based on:
- "Tree of Thoughts: Deliberate Problem Solving with Large Language Models"
- Yao et al., 2023

License: arkain.info@gmail.com (Gemini Enterprise)
"""
from __future__ import annotations

import logging
import random
import math
from collections import deque
from typing import Callable, Dict, List, Optional, Tuple
from copy import deepcopy

from app.schemas.tot_schemas import (
    ThoughtNode, ToTTree, ThoughtStatus, SearchStrategy,
    SimulationRequest, SimulationResult,
)
from app.services.stpf_engine import STPFv31Engine
from app.schemas.stpf_schemas import STPFInputs

logger = logging.getLogger(__name__)


class ToTSimulator:
    """
    Tree of Thoughts 시뮬레이터
    
    Features:
    - BFS/DFS/MCTS/Beam Search 탐색
    - STPF 기반 노드 평가
    - 가지치기 (pruning)
    - 최적 경로 추적
    """
    
    # 기본 생각 생성 템플릿 (LLM 없이 사용)
    DEFAULT_THOUGHTS = [
        "더 창의적인 접근: {}",
        "비용 효율적 접근: {}",
        "리스크 최소화 접근: {}",
        "속도 우선 접근: {}",
        "품질 우선 접근: {}",
    ]
    
    def __init__(self):
        self.stpf = STPFv31Engine()
    
    def simulate(
        self,
        request: SimulationRequest,
        thought_generator: Optional[Callable] = None,
    ) -> SimulationResult:
        """
        ToT 시뮬레이션 실행
        
        Args:
            request: 시뮬레이션 요청
            thought_generator: 커스텀 생각 생성 함수 (없으면 내장 사용)
        
        Returns:
            SimulationResult with best path and tree
        """
        # 1. 트리 초기화
        tree = ToTTree(
            problem=request.problem,
            context=request.context,
            max_depth=request.max_depth,
            branching_factor=request.branching_factor,
            strategy=request.strategy,
        )
        
        # 루트 노드 생성
        root = ThoughtNode(
            thought=f"문제: {request.problem}",
            reasoning="시작점",
            depth=0,
            status=ThoughtStatus.COMPLETED,
        )
        tree.root = root
        tree.add_node(root)
        
        # 2. 전략별 탐색 실행
        if request.strategy == SearchStrategy.BFS:
            self._bfs_search(tree, request, thought_generator)
        elif request.strategy == SearchStrategy.DFS:
            self._dfs_search(tree, request, thought_generator)
        elif request.strategy == SearchStrategy.MCTS:
            self._mcts_search(tree, request, thought_generator)
        elif request.strategy == SearchStrategy.BEAM:
            self._beam_search(tree, request, thought_generator)
        
        # 3. 최적 경로 추출
        best_node = self._find_best_node(tree)
        best_path = tree.get_path(best_node.node_id) if best_node else []
        
        tree.best_path = [n.node_id for n in best_path]
        tree.best_score = best_node.stpf_score if best_node and best_node.stpf_score else 0.0
        
        # 4. 결과 생성
        result = SimulationResult(
            tree=tree,
            best_path=best_path,
            best_score=tree.best_score,
            total_nodes=len(tree.nodes),
            iterations=tree.iterations,
            strategy_used=request.strategy,
            recommendation=self._generate_recommendation(best_path),
            alternative_paths=self._get_alternative_paths(tree, best_node),
        )
        
        logger.info(
            f"ToT Simulation complete: {len(tree.nodes)} nodes, "
            f"best_score={tree.best_score:.1f}, strategy={request.strategy.value}"
        )
        
        return result
    
    def _bfs_search(
        self,
        tree: ToTTree,
        request: SimulationRequest,
        thought_generator: Optional[Callable],
    ) -> None:
        """너비 우선 탐색"""
        queue = deque([tree.root.node_id])
        
        while queue and tree.iterations < request.max_iterations:
            node_id = queue.popleft()
            node = tree.nodes[node_id]
            
            if node.depth >= tree.max_depth:
                continue
            
            # 자식 노드 생성
            children = self._generate_children(
                tree, node, request, thought_generator
            )
            
            # 평가 및 추가
            for child in children:
                self._evaluate_node(child, request.base_inputs)
                tree.add_node(child)
                
                if child.stpf_score and child.stpf_score > 300:  # 프루닝 임계값
                    queue.append(child.node_id)
            
            tree.iterations += 1
    
    def _dfs_search(
        self,
        tree: ToTTree,
        request: SimulationRequest,
        thought_generator: Optional[Callable],
    ) -> None:
        """깊이 우선 탐색"""
        stack = [tree.root.node_id]
        
        while stack and tree.iterations < request.max_iterations:
            node_id = stack.pop()
            node = tree.nodes[node_id]
            
            if node.depth >= tree.max_depth:
                continue
            
            # 자식 노드 생성
            children = self._generate_children(
                tree, node, request, thought_generator
            )
            
            # 평가 및 추가 (역순으로 스택에 넣어야 정방향 탐색)
            for child in reversed(children):
                self._evaluate_node(child, request.base_inputs)
                tree.add_node(child)
                
                if child.stpf_score and child.stpf_score > 300:
                    stack.append(child.node_id)
            
            tree.iterations += 1
    
    def _mcts_search(
        self,
        tree: ToTTree,
        request: SimulationRequest,
        thought_generator: Optional[Callable],
    ) -> None:
        """Monte Carlo Tree Search"""
        for _ in range(request.max_iterations):
            # 1. Selection - UCB1로 노드 선택
            node = self._select_node(tree)
            
            if node.depth >= tree.max_depth:
                # 최대 깊이면 백프로파게이션만
                self._backpropagate(tree, node)
                continue
            
            # 2. Expansion - 자식 생성
            children = self._generate_children(
                tree, node, request, thought_generator
            )
            
            if children:
                child = random.choice(children)
                self._evaluate_node(child, request.base_inputs)
                tree.add_node(child)
                
                # 3. Simulation (간단화: 평가점수 사용)
                value = (child.stpf_score or 0) / 1000.0
                
                # 4. Backpropagation
                self._backpropagate(tree, child, value)
            
            tree.iterations += 1
    
    def _beam_search(
        self,
        tree: ToTTree,
        request: SimulationRequest,
        thought_generator: Optional[Callable],
        beam_width: int = 3,
    ) -> None:
        """Beam Search"""
        current_level = [tree.root.node_id]
        
        for depth in range(tree.max_depth):
            if not current_level or tree.iterations >= request.max_iterations:
                break
            
            all_children = []
            
            for node_id in current_level:
                node = tree.nodes[node_id]
                children = self._generate_children(
                    tree, node, request, thought_generator
                )
                
                for child in children:
                    self._evaluate_node(child, request.base_inputs)
                    tree.add_node(child)
                    all_children.append(child)
                
                tree.iterations += 1
            
            # 상위 beam_width개만 유지
            all_children.sort(
                key=lambda x: x.stpf_score or 0,
                reverse=True
            )
            current_level = [c.node_id for c in all_children[:beam_width]]
    
    def _generate_children(
        self,
        tree: ToTTree,
        parent: ThoughtNode,
        request: SimulationRequest,
        thought_generator: Optional[Callable],
    ) -> List[ThoughtNode]:
        """자식 노드 생성"""
        children = []
        
        if thought_generator:
            # 커스텀 생성기 사용
            thoughts = thought_generator(parent.thought, request.problem)
        else:
            # 기본 생성기 사용
            thoughts = self._default_thought_generator(
                parent.thought, 
                request.problem,
                tree.branching_factor
            )
        
        for thought in thoughts:
            child = ThoughtNode(
                parent_id=parent.node_id,
                depth=parent.depth + 1,
                thought=thought,
                reasoning=f"Parent: {parent.thought[:50]}...",
                status=ThoughtStatus.PENDING,
            )
            children.append(child)
        
        return children
    
    def _default_thought_generator(
        self,
        parent_thought: str,
        problem: str,
        num_thoughts: int,
    ) -> List[str]:
        """기본 생각 생성기"""
        approaches = [
            f"창의적 접근: {problem}을 새로운 관점에서",
            f"효율적 접근: {problem}을 최소 비용으로",
            f"안전한 접근: {problem}을 리스크 최소화로",
            f"빠른 접근: {problem}을 가장 빠르게",
            f"품질 접근: {problem}을 최고 품질로",
        ]
        return random.sample(approaches, min(num_thoughts, len(approaches)))
    
    def _evaluate_node(
        self,
        node: ThoughtNode,
        base_inputs: Optional[Dict[str, float]] = None,
    ) -> None:
        """노드 평가 (STPF 사용)"""
        # 기본 입력값 또는 노드 특성 기반 평가
        inputs_dict = base_inputs or {}
        
        # 노드 특성에 따른 점수 조정
        if "창의" in node.thought:
            inputs_dict["novelty"] = inputs_dict.get("novelty", 5.0) + 1
        if "효율" in node.thought or "비용" in node.thought:
            inputs_dict["cost"] = max(1.0, inputs_dict.get("cost", 5.0) - 1)
        if "안전" in node.thought or "리스크" in node.thought:
            inputs_dict["risk"] = max(1.0, inputs_dict.get("risk", 5.0) - 1)
        if "빠른" in node.thought or "속도" in node.thought:
            inputs_dict["lag"] = max(1.0, inputs_dict.get("lag", 5.0) - 1)
        if "품질" in node.thought:
            inputs_dict["proof"] = inputs_dict.get("proof", 5.0) + 1
        
        # 깊이 보너스 (깊은 노드는 더 정제된 전략)
        inputs_dict["capability"] = min(10.0, inputs_dict.get("capability", 5.0) + node.depth * 0.5)
        
        # STPF 계산
        try:
            inputs = STPFInputs(**{k: min(10.0, max(1.0, v)) for k, v in inputs_dict.items()})
            result = self.stpf.compute(inputs)
            node.stpf_score = result.score_1000
            node.confidence = result.p_success
            node.status = ThoughtStatus.COMPLETED
        except Exception as e:
            logger.warning(f"STPF evaluation failed: {e}")
            node.stpf_score = 0.0
            node.status = ThoughtStatus.COMPLETED
    
    def _select_node(self, tree: ToTTree) -> ThoughtNode:
        """UCB1 기반 노드 선택 (MCTS용)"""
        candidates = [
            n for n in tree.nodes.values()
            if n.status == ThoughtStatus.COMPLETED and n.depth < tree.max_depth
        ]
        
        if not candidates:
            return tree.root
        
        return max(candidates, key=lambda n: n.ucb1_score)
    
    def _backpropagate(
        self,
        tree: ToTTree,
        node: ThoughtNode,
        value: float = None,
    ) -> None:
        """MCTS 백프로파게이션"""
        if value is None:
            value = (node.stpf_score or 0) / 1000.0
        
        current = node
        while current:
            current.visits += 1
            current.total_value += value
            
            if current.parent_id and current.parent_id in tree.nodes:
                current = tree.nodes[current.parent_id]
            else:
                break
    
    def _find_best_node(self, tree: ToTTree) -> Optional[ThoughtNode]:
        """최고 점수 노드 찾기"""
        completed = [
            n for n in tree.nodes.values()
            if n.status == ThoughtStatus.COMPLETED and n.stpf_score is not None
        ]
        
        if not completed:
            return tree.root
        
        return max(completed, key=lambda n: n.stpf_score)
    
    def _generate_recommendation(self, path: List[ThoughtNode]) -> str:
        """경로 기반 권장 사항 생성"""
        if not path:
            return "탐색 결과 없음"
        
        best = path[-1]
        score = best.stpf_score or 0
        
        if score >= 600:
            return f"🚀 강력 추천: {best.thought}"
        elif score >= 400:
            return f"✅ 추천: {best.thought}"
        elif score >= 200:
            return f"⚠️ 검토 필요: {best.thought}"
        else:
            return f"❌ 재검토 권장: {best.thought}"
    
    def _get_alternative_paths(
        self,
        tree: ToTTree,
        best_node: Optional[ThoughtNode],
        top_k: int = 3,
    ) -> List[List[str]]:
        """대안 경로 추출"""
        if not best_node:
            return []
        
        # 상위 점수 노드들
        completed = [
            n for n in tree.nodes.values()
            if n.status == ThoughtStatus.COMPLETED 
            and n.stpf_score is not None
            and n.node_id != best_node.node_id
        ]
        
        completed.sort(key=lambda n: n.stpf_score, reverse=True)
        
        alternatives = []
        for node in completed[:top_k]:
            path = tree.get_path(node.node_id)
            alternatives.append([n.thought for n in path])
        
        return alternatives


# 싱글톤 인스턴스
tot_simulator = ToTSimulator()
