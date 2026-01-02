"""
Unit Tests for Node Manipulator

Coverage Target: 80%+
"""
import pytest
from app.services.node_manipulator import (
    NodeManipulator, node_manipulator,
    NodeUpdateResult, VDGNode,
)
from app.schemas.intent_schemas import (
    NodeEditIntent, IntentType, PropertyChange, PropertyCategory,
)


class TestVDGNode:
    """VDGNode 테스트"""
    
    def test_node_creation(self):
        """노드 생성"""
        node = VDGNode(
            node_id="test_001",
            node_type="scene",
            properties={"mood": "calm", "lighting": 5},
        )
        
        assert node.node_id == "test_001"
        assert node.properties["mood"] == "calm"
        assert node.created_at is not None


class TestNodeUpdateResult:
    """NodeUpdateResult 테스트"""
    
    def test_success_result(self):
        """성공 결과"""
        result = NodeUpdateResult(
            success=True,
            node_id="node_001",
            changes_applied={"mood": "dramatic"},
            previous_values={"mood": "calm"},
            stpf_score=700,
        )
        
        assert result.success is True
        assert result.stpf_score == 700
    
    def test_failure_result(self):
        """실패 결과"""
        result = NodeUpdateResult(
            success=False,
            node_id="node_001",
            changes_applied={},
            previous_values={},
            error="STPF too low",
        )
        
        assert result.success is False
        assert result.error == "STPF too low"


class TestNodeManipulator:
    """Node Manipulator 테스트"""
    
    @pytest.fixture
    def manipulator(self):
        return NodeManipulator()
    
    @pytest.fixture
    def sample_node(self):
        return VDGNode(
            node_id="scene_001",
            node_type="scene",
            properties={
                "mood": "calm",
                "lighting": 5,
                "camera_motion": "static",
            },
        )
    
    @pytest.fixture
    def sample_intent(self):
        return NodeEditIntent(
            intent_type=IntentType.MODIFY,
            target_node_id="scene_001",
            original_text="더 극적으로",
            simple_changes={"mood": "dramatic", "lighting": 8},
        )
    
    # 기본 적용 테스트
    @pytest.mark.asyncio
    async def test_apply_intent_success(self, manipulator, sample_node, sample_intent):
        """Intent 적용 성공"""
        result = await manipulator.apply_intent(
            sample_intent,
            sample_node,
            validate_rules=False,
            send_feedback=False,
        )
        
        assert result.success is True
        assert result.node_id == "scene_001"
        assert sample_node.properties["mood"] == "dramatic"
        assert sample_node.properties["lighting"] == 8
    
    @pytest.mark.asyncio
    async def test_apply_intent_stores_previous(self, manipulator, sample_node, sample_intent):
        """이전 값 저장"""
        result = await manipulator.apply_intent(
            sample_intent,
            sample_node,
            validate_rules=False,
            send_feedback=False,
        )
        
        assert result.previous_values["mood"] == "calm"
        assert result.previous_values["lighting"] == 5
    
    @pytest.mark.asyncio
    async def test_apply_empty_changes(self, manipulator, sample_node):
        """빈 변경"""
        empty_intent = NodeEditIntent(
            intent_type=IntentType.MODIFY,
            original_text="테스트",
            simple_changes={},
        )
        
        result = await manipulator.apply_intent(
            empty_intent,
            sample_node,
            validate_rules=False,
            send_feedback=False,
        )
        
        assert result.success is False
        # 빈 변경이거나 유효한 변경 없음
        assert result.error is not None
    
    # 미리보기 테스트
    def test_preview_changes(self, manipulator, sample_node, sample_intent):
        """변경 미리보기"""
        preview = manipulator.preview_changes(sample_intent, sample_node)
        
        assert preview["node_id"] == "scene_001"
        assert len(preview["changes"]) == 2
        assert preview["stpf_score"] is not None
        assert "recommended" in preview
    
    # Undo 테스트
    def test_undo_change(self, manipulator, sample_node):
        """변경 취소"""
        # 변경
        sample_node.properties["mood"] = "dramatic"
        
        # Undo
        result = manipulator.undo_change(
            sample_node,
            {"mood": "calm"},
        )
        
        assert result.success is True
        assert sample_node.properties["mood"] == "calm"
    
    # 통계 테스트
    def test_stats(self, manipulator):
        """통계"""
        stats = manipulator.get_stats()
        
        assert "total_changes" in stats
        assert "error_count" in stats
        assert "error_rate" in stats


class TestNodeManipulatorIntegration:
    """통합 테스트"""
    
    def test_singleton_instance(self):
        """싱글톤 인스턴스"""
        assert node_manipulator is not None
        assert isinstance(node_manipulator, NodeManipulator)
    
    @pytest.mark.asyncio
    async def test_full_edit_cycle(self):
        """전체 편집 사이클"""
        # 1. 노드 생성
        node = VDGNode(
            node_id="test_full_cycle",
            node_type="scene",
            properties={"mood": "calm"},
        )
        
        # 2. Intent 생성
        intent = NodeEditIntent(
            intent_type=IntentType.MODIFY,
            target_node_id=node.node_id,
            original_text="극적으로",
            simple_changes={"mood": "dramatic"},
        )
        
        # 3. 미리보기
        preview = node_manipulator.preview_changes(intent, node)
        assert preview["recommended"] is True
        
        # 4. 적용
        result = await node_manipulator.apply_intent(
            intent, node,
            send_feedback=False,
        )
        
        assert result.success is True
        assert node.properties["mood"] == "dramatic"
        
        # 5. Undo
        undo_result = node_manipulator.undo_change(
            node,
            result.previous_values,
        )
        
        assert undo_result.success is True
        assert node.properties["mood"] == "calm"
    
    @pytest.mark.asyncio
    async def test_batch_apply(self):
        """배치 적용"""
        nodes = [
            VDGNode(node_id=f"batch_{i}", node_type="scene", properties={"mood": "calm"})
            for i in range(3)
        ]
        
        intent = NodeEditIntent(
            intent_type=IntentType.BATCH_EDIT,
            original_text="모두 극적으로",
            simple_changes={"mood": "dramatic"},
        )
        
        results = await node_manipulator.batch_apply(intent, nodes)
        
        assert len(results) == 3
        assert all(r.success for r in results)
        assert all(n.properties["mood"] == "dramatic" for n in nodes)


class TestNodeManipulatorHardening:
    """Node Manipulator 하드닝 테스트"""
    
    @pytest.fixture
    def manipulator(self):
        from app.services.node_manipulator import NodeManipulator
        return NodeManipulator()
    
    @pytest.fixture
    def sample_node(self):
        return VDGNode(
            node_id="hardening_test",
            node_type="scene",
            properties={"mood": "calm", "lighting": 5},
        )
    
    # 노드 검증 테스트
    @pytest.mark.asyncio
    async def test_none_node_rejected(self, manipulator):
        """None 노드 거부"""
        intent = NodeEditIntent(
            intent_type=IntentType.MODIFY,
            original_text="test",
            simple_changes={"mood": "dramatic"},
        )
        
        result = await manipulator.apply_intent(intent, None)
        assert result.success is False
        assert "None" in result.error
    
    @pytest.mark.asyncio
    async def test_node_without_id_rejected(self, manipulator):
        """ID 없는 노드 거부"""
        node = VDGNode(node_id="", node_type="scene", properties={})
        intent = NodeEditIntent(
            intent_type=IntentType.MODIFY,
            original_text="test",
            simple_changes={"mood": "dramatic"},
        )
        
        result = await manipulator.apply_intent(intent, node)
        assert result.success is False
    
    # 보호된 속성 테스트
    @pytest.mark.asyncio
    async def test_protected_property_blocked(self, manipulator, sample_node):
        """보호된 속성 변경 차단"""
        intent = NodeEditIntent(
            intent_type=IntentType.MODIFY,
            original_text="test",
            simple_changes={"node_id": "hacked", "mood": "dramatic"},
        )
        
        result = await manipulator.apply_intent(intent, sample_node, send_feedback=False)
        assert result.success is False
        assert "보호된" in result.error
    
    # 값 정규화 테스트
    @pytest.mark.asyncio
    async def test_xss_sanitized(self, manipulator, sample_node):
        """XSS 문자 제거"""
        intent = NodeEditIntent(
            intent_type=IntentType.MODIFY,
            original_text="test",
            simple_changes={"description": "<script>alert('xss')</script>"},
        )
        
        result = await manipulator.apply_intent(intent, sample_node, send_feedback=False)
        assert result.success is True
        # 위험한 문자가 제거됨
        assert "<" not in sample_node.properties.get("description", "")
    
    @pytest.mark.asyncio
    async def test_negative_number_clamped(self, manipulator, sample_node):
        """음수 값 0으로 클램프"""
        intent = NodeEditIntent(
            intent_type=IntentType.MODIFY,
            original_text="test",
            simple_changes={"lighting": -10},
        )
        
        result = await manipulator.apply_intent(intent, sample_node, send_feedback=False)
        assert result.success is True
        assert sample_node.properties["lighting"] == 0
    
    @pytest.mark.asyncio
    async def test_large_number_clamped(self, manipulator, sample_node):
        """큰 값 100으로 클램프"""
        intent = NodeEditIntent(
            intent_type=IntentType.MODIFY,
            original_text="test",
            simple_changes={"volume": 500},
        )
        
        result = await manipulator.apply_intent(intent, sample_node, send_feedback=False)
        assert result.success is True
        assert sample_node.properties["volume"] == 100
    
    # 히스토리 테스트
    @pytest.mark.asyncio
    async def test_change_history_recorded(self, manipulator, sample_node):
        """변경 히스토리 기록"""
        intent = NodeEditIntent(
            intent_type=IntentType.MODIFY,
            original_text="test",
            simple_changes={"mood": "dramatic"},
        )
        
        result = await manipulator.apply_intent(intent, sample_node, send_feedback=False)
        assert result.success is True
        assert result.change_id is not None
        
        # 히스토리 확인
        history = manipulator.get_history(sample_node.node_id)
        assert len(history) > 0
    
    @pytest.mark.asyncio
    async def test_undo_by_change_id(self, manipulator, sample_node):
        """change_id로 Undo"""
        # 변경
        intent = NodeEditIntent(
            intent_type=IntentType.MODIFY,
            original_text="test",
            simple_changes={"mood": "dramatic"},
        )
        
        result = await manipulator.apply_intent(intent, sample_node, send_feedback=False)
        change_id = result.change_id
        
        # Undo
        undo_result = manipulator.undo_by_change_id(sample_node, change_id)
        assert undo_result.success is True
        assert sample_node.properties["mood"] == "calm"
    
    # 버전 추적 테스트
    @pytest.mark.asyncio
    async def test_version_incremented(self, manipulator):
        """버전 증가"""
        node = VDGNode(
            node_id="version_test",
            node_type="scene",
            properties={"mood": "calm"},
        )
        initial_version = node.version
        
        intent = NodeEditIntent(
            intent_type=IntentType.MODIFY,
            original_text="test",
            simple_changes={"mood": "dramatic"},
        )
        
        await manipulator.apply_intent(intent, node, send_feedback=False)
        assert node.version == initial_version + 1
    
    # 통계 테스트
    def test_stats_include_reject_count(self, manipulator):
        """통계에 거부 카운트 포함"""
        stats = manipulator.get_stats()
        
        assert "total_changes" in stats
        assert "error_count" in stats
        assert "reject_count" in stats
        assert "history_size" in stats
    
    # 미리보기 에러 처리
    def test_preview_with_invalid_node(self, manipulator):
        """잘못된 노드로 미리보기"""
        node = VDGNode(node_id="", node_type="", properties={})
        intent = NodeEditIntent(
            intent_type=IntentType.MODIFY,
            original_text="test",
            simple_changes={"mood": "dramatic"},
        )
        
        preview = manipulator.preview_changes(intent, node)
        assert "error" in preview
        assert preview["recommended"] is False

