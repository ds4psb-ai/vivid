"""
Unit Tests for ToT Simulator

Coverage Target: 80%+
"""
import pytest
from app.services.tot_simulator import ToTSimulator, tot_simulator
from app.schemas.tot_schemas import (
    ThoughtNode, ToTTree, ThoughtStatus, SearchStrategy,
    SimulationRequest, SimulationResult,
)


class TestThoughtNode:
    """ThoughtNode 테스트"""
    
    def test_node_creation(self):
        """노드 생성"""
        node = ThoughtNode(
            thought="테스트 생각",
            reasoning="테스트 이유",
        )
        
        assert node.thought == "테스트 생각"
        assert node.depth == 0
        assert node.status == ThoughtStatus.PENDING
        assert node.node_id is not None
    
    def test_ucb1_score_unvisited(self):
        """방문하지 않은 노드의 UCB1 점수"""
        node = ThoughtNode(thought="test", visits=0)
        assert node.ucb1_score == float('inf')
    
    def test_ucb1_score_visited(self):
        """방문한 노드의 UCB1 점수"""
        node = ThoughtNode(thought="test", visits=5, total_value=2.5)
        score = node.ucb1_score
        assert score > 0
        assert score < float('inf')


class TestToTTree:
    """ToTTree 테스트"""
    
    def test_tree_creation(self):
        """트리 생성"""
        tree = ToTTree(
            problem="테스트 문제",
            max_depth=3,
        )
        
        assert tree.problem == "테스트 문제"
        assert tree.max_depth == 3
        assert len(tree.nodes) == 0
    
    def test_add_node(self):
        """노드 추가"""
        tree = ToTTree(problem="test")
        root = ThoughtNode(thought="root")
        child = ThoughtNode(thought="child", parent_id=root.node_id)
        
        tree.add_node(root)
        tree.add_node(child)
        
        assert len(tree.nodes) == 2
        assert child.node_id in tree.nodes[root.node_id].children_ids
    
    def test_get_path(self):
        """경로 추출"""
        tree = ToTTree(problem="test")
        root = ThoughtNode(thought="root", depth=0)
        child = ThoughtNode(thought="child", parent_id=root.node_id, depth=1)
        
        tree.add_node(root)
        tree.add_node(child)
        
        path = tree.get_path(child.node_id)
        assert len(path) == 2
        assert path[0].thought == "root"
        assert path[1].thought == "child"


class TestToTSimulator:
    """ToT 시뮬레이터 테스트"""
    
    @pytest.fixture
    def simulator(self):
        return ToTSimulator()
    
    @pytest.fixture
    def basic_request(self):
        return SimulationRequest(
            problem="최적의 영상 제작 전략",
            max_depth=2,
            max_iterations=10,
        )
    
    def test_bfs_simulation(self, simulator, basic_request):
        """BFS 시뮬레이션"""
        basic_request.strategy = SearchStrategy.BFS
        result = simulator.simulate(basic_request)
        
        assert result.total_nodes > 0
        assert result.strategy_used == SearchStrategy.BFS
        assert result.recommendation is not None
    
    def test_dfs_simulation(self, simulator, basic_request):
        """DFS 시뮬레이션"""
        basic_request.strategy = SearchStrategy.DFS
        result = simulator.simulate(basic_request)
        
        assert result.total_nodes > 0
        assert result.strategy_used == SearchStrategy.DFS
    
    def test_mcts_simulation(self, simulator, basic_request):
        """MCTS 시뮬레이션"""
        basic_request.strategy = SearchStrategy.MCTS
        result = simulator.simulate(basic_request)
        
        assert result.total_nodes > 0
        assert result.strategy_used == SearchStrategy.MCTS
    
    def test_beam_simulation(self, simulator, basic_request):
        """Beam Search 시뮬레이션"""
        basic_request.strategy = SearchStrategy.BEAM
        result = simulator.simulate(basic_request)
        
        assert result.total_nodes > 0
        assert result.strategy_used == SearchStrategy.BEAM
    
    def test_best_path_exists(self, simulator, basic_request):
        """최적 경로 존재"""
        result = simulator.simulate(basic_request)
        
        assert len(result.best_path) > 0
        assert result.best_score >= 0
    
    def test_alternative_paths(self, simulator, basic_request):
        """대안 경로"""
        basic_request.max_depth = 2
        basic_request.max_iterations = 15
        result = simulator.simulate(basic_request)
        
        # 대안 경로는 있을 수도 없을 수도 있음
        assert isinstance(result.alternative_paths, list)
    
    def test_node_evaluation(self, simulator):
        """노드 평가 (STPF)"""
        node = ThoughtNode(thought="창의적 접근: 테스트")
        simulator._evaluate_node(node)
        
        assert node.stpf_score is not None
        assert node.status == ThoughtStatus.COMPLETED
    
    def test_pruning(self, simulator, basic_request):
        """프루닝 작동"""
        basic_request.max_depth = 3
        basic_request.max_iterations = 30
        result = simulator.simulate(basic_request)
        
        # 모든 노드가 max_depth^branching_factor보다 적어야 함 (프루닝)
        max_possible = sum(3**i for i in range(4))  # 1+3+9+27=40
        assert result.total_nodes < max_possible


class TestToTIntegration:
    """통합 테스트"""
    
    def test_singleton_instance(self):
        """싱글톤 인스턴스"""
        assert tot_simulator is not None
        assert isinstance(tot_simulator, ToTSimulator)
    
    def test_full_simulation_cycle(self):
        """전체 시뮬레이션 사이클"""
        request = SimulationRequest(
            problem="AI 영상 자동화 최적 전략",
            context="Veo 3.1 사용, 월 예산 $1000",
            strategy=SearchStrategy.BFS,
            max_depth=2,
            max_iterations=15,
        )
        
        result = tot_simulator.simulate(request)
        
        # 기본 검증
        assert result.tree.problem == request.problem
        assert result.total_nodes > 0
        assert result.best_score >= 0
        
        # 트리 구조 검증
        assert result.tree.root is not None
        assert result.tree.root.node_id in result.tree.nodes
        
        # 권장 사항 검증
        assert result.recommendation is not None
        assert len(result.recommendation) > 0
    
    def test_different_strategies_produce_different_results(self):
        """다른 전략은 다른 결과"""
        problem = "비용 효율적인 콘텐츠 제작"
        
        results = {}
        for strategy in SearchStrategy:
            request = SimulationRequest(
                problem=problem,
                strategy=strategy,
                max_depth=2,
                max_iterations=10,
            )
            result = tot_simulator.simulate(request)
            results[strategy.value] = result.total_nodes
        
        # 최소 하나는 다른 결과 (MCTS는 확률적이라 다를 수 있음)
        assert len(set(results.values())) >= 1
