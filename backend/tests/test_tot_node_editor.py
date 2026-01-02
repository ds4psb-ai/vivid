"""
Unit Tests for ToT Node Editor
"""
import pytest
from app.services.tot_node_editor import (
    ToTNodeEditor, tot_node_editor,
    EditStep, EditPlan, TotEditResult,
)
from app.services.node_manipulator import VDGNode
from app.schemas.tot_schemas import SearchStrategy


class TestToTNodeEditor:
    """ToT Node Editor 테스트"""
    
    @pytest.fixture
    def editor(self):
        return ToTNodeEditor()
    
    @pytest.fixture
    def sample_nodes(self):
        return [
            VDGNode(node_id=f"node_{i}", node_type="scene", properties={"mood": "calm"})
            for i in range(3)
        ]
    
    # 복잡 편집 감지
    def test_detect_simple_edit(self, editor):
        """단순 편집 감지"""
        is_complex, reason = editor.is_complex_edit("밝게", 1, 1)
        assert is_complex is False
    
    def test_detect_complex_multi_node(self, editor):
        """다중 노드 편집 감지"""
        is_complex, reason = editor.is_complex_edit("밝게", 5, 1)
        assert is_complex is True
        assert "다중" in reason
    
    def test_detect_complex_by_keyword(self, editor):
        """키워드로 복잡 편집 감지"""
        is_complex, reason = editor.is_complex_edit("전체 씬을 밝게", 1, 1)
        assert is_complex is True
        assert "전체" in reason
    
    # 계획 수립
    def test_plan_edit(self, editor, sample_nodes):
        """편집 계획 수립"""
        plan = editor.plan_edit("밝게", sample_nodes, SearchStrategy.BFS)
        
        assert plan is not None
        assert plan.plan_id is not None
        assert len(plan.steps) > 0
    
    def test_quick_plan(self, editor):
        """빠른 계획"""
        steps = editor.quick_plan("밝게", ["node_1", "node_2"])
        
        assert len(steps) == 2
        assert all("node_id" in s for s in steps)
    
    # 실행
    @pytest.mark.asyncio
    async def test_execute_plan(self, editor, sample_nodes):
        """계획 실행"""
        plan = editor.plan_edit("밝게", sample_nodes, SearchStrategy.BFS)
        
        # 노드 딕셔너리 생성
        nodes_dict = {n.node_id: n for n in sample_nodes}
        
        result = await editor.execute_plan(plan, nodes_dict, skip_low_score=False)
        
        assert result.success is True
        assert result.total_applied > 0
    
    def test_stats(self, editor):
        """통계"""
        stats = editor.get_stats()
        assert "total_plans" in stats
        assert "total_executions" in stats


class TestToTIntegration:
    """통합 테스트"""
    
    def test_singleton(self):
        """싱글톤"""
        assert tot_node_editor is not None
