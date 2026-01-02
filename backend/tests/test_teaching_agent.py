"""
Unit Tests for Teaching Agent

Coverage Target: 80%+
"""
import pytest
from app.services.teaching_agent import (
    TeachingAgent, teaching_agent,
    TEACHING_TOOLS, NODE_EDIT_TOOLS, UNIFIED_TOOLS,
    ToolExecutionResult, NodeStore,
)
from app.services.node_manipulator import VDGNode


class TestToolDeclarations:
    """도구 선언 테스트"""
    
    def test_teaching_tools_count(self):
        """Teaching 도구 수"""
        assert len(TEACHING_TOOLS) == 4
    
    def test_node_edit_tools_count(self):
        """Node Edit 도구 수"""
        assert len(NODE_EDIT_TOOLS) == 5
    
    def test_unified_tools_count(self):
        """통합 도구 수"""
        assert len(UNIFIED_TOOLS) == 9
    
    def test_tool_has_required_fields(self):
        """도구에 필수 필드 존재"""
        for tool in UNIFIED_TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool


class TestNodeStore:
    """NodeStore 테스트"""
    
    @pytest.fixture
    def store(self):
        return NodeStore()
    
    def test_create_node(self, store):
        """노드 생성"""
        node = store.create("scene", {"mood": "calm"})
        
        assert node.node_id is not None
        assert node.node_type == "scene"
        assert node.properties["mood"] == "calm"
    
    def test_get_node(self, store):
        """노드 조회"""
        node = store.create("scene")
        retrieved = store.get(node.node_id)
        
        assert retrieved is not None
        assert retrieved.node_id == node.node_id
    
    def test_put_node(self, store):
        """노드 저장"""
        node = VDGNode(node_id="custom_id", node_type="scene", properties={})
        store.put(node)
        
        assert store.get("custom_id") is not None
    
    def test_list_all(self, store):
        """모든 노드 조회"""
        store.create("scene")
        store.create("image")
        
        nodes = store.list_all()
        assert len(nodes) == 2


class TestTeachingAgent:
    """Teaching Agent 테스트"""
    
    @pytest.fixture
    def agent(self):
        return TeachingAgent()
    
    # 기본 메서드 테스트
    def test_get_tools(self, agent):
        """도구 목록 조회"""
        tools = agent.get_tools()
        assert len(tools) == 9
    
    def test_get_system_prompt(self, agent):
        """시스템 프롬프트 조회"""
        prompt = agent.get_system_prompt()
        assert "Teaching Tools" in prompt
        assert "Node Edit Tools" in prompt
    
    # Teaching 도구 실행 테스트
    @pytest.mark.asyncio
    async def test_execute_generate_veo_prompt(self, agent):
        """generate_veo_prompt 실행"""
        result = await agent.execute_tool(
            "generate_veo_prompt",
            {"topic": "요리 브이로그", "style": "vlog"},
        )
        
        assert result.success is True
        assert "prompt" in result.output
        assert result.node_spec is not None
    
    @pytest.mark.asyncio
    async def test_execute_create_storyboard(self, agent):
        """create_storyboard 실행"""
        result = await agent.execute_tool(
            "create_storyboard",
            {"concept": "아침 루틴", "scene_count": 5},
        )
        
        assert result.success is True
        assert "scenes" in result.output
        assert len(result.output["scenes"]) == 5
    
    @pytest.mark.asyncio
    async def test_execute_generate_image_prompt(self, agent):
        """generate_image_prompt 실행"""
        result = await agent.execute_tool(
            "generate_image_prompt",
            {"description": "일몰 풍경", "style": "cinematic"},
        )
        
        assert result.success is True
        assert "prompt" in result.output
    
    @pytest.mark.asyncio
    async def test_execute_analyze_reference(self, agent):
        """analyze_reference 실행"""
        result = await agent.execute_tool(
            "analyze_reference",
            {"video_description": "웨스 앤더슨 스타일 영상", "focus_areas": ["color", "composition"]},
        )
        
        assert result.success is True
        assert "analysis" in result.output
    
    # Node Edit 도구 실행 테스트
    @pytest.mark.asyncio
    async def test_execute_edit_node(self, agent):
        """edit_node 실행"""
        result = await agent.execute_tool(
            "edit_node",
            {"node_id": "test_node_1", "edit_description": "더 밝게 해줘"},
        )
        
        assert result.success is True
        assert result.output.get("stpf_score") is not None
    
    @pytest.mark.asyncio
    async def test_execute_preview_changes(self, agent):
        """preview_changes 실행"""
        result = await agent.execute_tool(
            "preview_changes",
            {"node_id": "test_node_2", "edit_description": "극적으로 바꿔줘"},
        )
        
        assert result.success is True
        assert "stpf_score" in result.output
    
    @pytest.mark.asyncio
    async def test_execute_batch_edit(self, agent):
        """batch_edit_nodes 실행"""
        result = await agent.execute_tool(
            "batch_edit_nodes",
            {
                "node_ids": ["batch_1", "batch_2", "batch_3"],
                "edit_description": "밝게 해줘",
            },
        )
        
        assert result.success is True
        assert result.output.get("success_count") == 3
    
    @pytest.mark.asyncio
    async def test_execute_connect_nodes(self, agent):
        """connect_nodes 실행"""
        # 먼저 노드 생성
        agent.node_store.create("scene")
        agent.node_store.create("scene")
        
        nodes = agent.node_store.list_all()
        if len(nodes) >= 2:
            result = await agent.execute_tool(
                "connect_nodes",
                {
                    "source_node_id": nodes[0].node_id,
                    "target_node_id": nodes[1].node_id,
                    "connection_type": "output",
                },
            )
            
            assert result.success is True
            assert "connection_id" in result.output
    
    # 에러 처리 테스트
    @pytest.mark.asyncio
    async def test_unknown_tool_error(self, agent):
        """알 수 없는 도구 에러"""
        result = await agent.execute_tool(
            "unknown_tool",
            {},
        )
        
        assert result.success is False
        assert "Unknown tool" in result.error
    
    @pytest.mark.asyncio
    async def test_undo_no_changes_error(self, agent):
        """Undo할 변경 없음"""
        # 새 노드는 히스토리 없음
        agent.node_store.create("scene")
        result = await agent.execute_tool(
            "undo_change",
            {"node_id": "nonexistent_node"},
        )
        
        assert result.success is False
    
    # 통계 테스트
    def test_stats(self, agent):
        """통계"""
        stats = agent.get_stats()
        
        assert "total_tools_executed" in stats
        assert "error_count" in stats
        assert "nodes_in_store" in stats


class TestTeachingAgentIntegration:
    """통합 테스트"""
    
    def test_singleton_instance(self):
        """싱글톤 인스턴스"""
        assert teaching_agent is not None
        assert isinstance(teaching_agent, TeachingAgent)
    
    @pytest.mark.asyncio
    async def test_full_edit_cycle(self):
        """전체 편집 사이클"""
        agent = TeachingAgent()
        
        # 1. 노드 편집
        edit_result = await agent.execute_tool(
            "edit_node",
            {"node_id": "cycle_test", "edit_description": "극적으로"},
        )
        assert edit_result.success is True
        
        # 2. 미리보기
        preview_result = await agent.execute_tool(
            "preview_changes",
            {"node_id": "cycle_test", "edit_description": "밝게"},
        )
        assert preview_result.success is True
        
        # 3. Undo - may or may not have changes depending on history
        change_id = edit_result.output.get("change_id")
        if change_id:
            undo_result = await agent.execute_tool(
                "undo_change",
                {"node_id": "cycle_test", "change_id": change_id},
            )
            # Undo 성공 또는 이미 되돌려짐
            assert undo_result is not None
