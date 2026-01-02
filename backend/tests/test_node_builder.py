"""
Unit Tests for Node Builder and Agent Tool Executor
"""
import pytest
from app.services.node_builder import (
    build_node_spec,
    build_pipeline_spec,
    build_node_created_event,
    build_node_updated_event,
    get_available_capsule_types,
    get_capsule_config,
    validate_capsule_inputs,
    CAPSULE_CONFIGS,
)
from app.services.agent_tool_executor import (
    agent_tool_executor,
    AgentToolExecutor,
    TOOL_HANDLERS,
)


class TestNodeBuilder:
    """Node Builder 테스트"""
    
    def test_build_node_spec(self):
        """노드 스펙 생성"""
        spec = build_node_spec(
            capsule_type="teaching.prompt",
            inputs={"topic": "요리 브이로그"},
            output={"prompt": "A cooking vlog..."},
        )
        
        assert spec["capsule_id"] == "teaching.prompt"
        assert spec["data"]["inputs"]["topic"] == "요리 브이로그"
        assert spec["executed"] is True
    
    def test_build_node_spec_with_position(self):
        """위치 지정 노드 스펙"""
        spec = build_node_spec(
            capsule_type="teaching.storyboard",
            inputs={"concept": "테스트"},
            output={},
            position={"x": 100, "y": 200},
        )
        
        assert spec["position"]["x"] == 100
        assert spec["position"]["y"] == 200
    
    def test_build_pipeline_spec(self):
        """파이프라인 스펙 생성"""
        node1 = build_node_spec("teaching.prompt", {"topic": "test"}, {})
        node2 = build_node_spec("teaching.storyboard", {"concept": "test"}, {})
        
        pipeline = build_pipeline_spec([node1, node2])
        
        assert len(pipeline["nodes"]) == 2
        assert len(pipeline["edges"]) == 1
    
    def test_build_node_created_event(self):
        """노드 생성 SSE 이벤트"""
        spec = build_node_spec("teaching.image", {"description": "test"}, {})
        event = build_node_created_event("session_1", spec, 1)
        
        assert event["type"] == "agent.node_created"
        assert event["payload"]["action"] == "add_to_canvas"
    
    def test_build_node_updated_event(self):
        """노드 업데이트 SSE 이벤트"""
        event = build_node_updated_event("session_1", "node_1", {"mood": "dramatic"}, 2)
        
        assert event["type"] == "agent.node_updated"
        assert event["payload"]["node_id"] == "node_1"
    
    def test_get_available_capsule_types(self):
        """캡슐 타입 목록"""
        types = get_available_capsule_types()
        
        assert "teaching.prompt" in types
        assert "teaching.storyboard" in types
        assert len(types) >= 4
    
    def test_validate_capsule_inputs_valid(self):
        """유효한 입력 검증"""
        valid, errors = validate_capsule_inputs(
            "teaching.prompt",
            {"topic": "test"},
        )
        
        assert valid is True
        assert len(errors) == 0
    
    def test_validate_capsule_inputs_missing_required(self):
        """필수 입력 누락"""
        valid, errors = validate_capsule_inputs(
            "teaching.prompt",
            {},
        )
        
        assert valid is False
        assert len(errors) > 0


class TestAgentToolExecutor:
    """Agent Tool Executor 테스트"""
    
    @pytest.fixture
    def executor(self):
        return AgentToolExecutor()
    
    def test_get_tool_info(self, executor):
        """도구 정보 조회"""
        info = executor.get_tool_info("generate_veo_prompt")
        
        assert info is not None
        assert info["capsule_type"] == "teaching.prompt"
    
    def test_get_tool_info_unknown(self, executor):
        """알 수 없는 도구"""
        info = executor.get_tool_info("unknown_tool")
        
        assert info is None
    
    def test_validate_tool_args_valid(self, executor):
        """유효한 인자 검증"""
        valid, error = executor.validate_tool_args(
            "generate_veo_prompt",
            {"topic": "test"},
        )
        
        assert valid is True
    
    def test_validate_tool_args_missing(self, executor):
        """필수 인자 누락"""
        valid, error = executor.validate_tool_args(
            "generate_veo_prompt",
            {},
        )
        
        assert valid is False
        assert "topic" in error
    
    def test_merge_with_defaults(self, executor):
        """기본값 병합"""
        merged = executor.merge_with_defaults(
            "generate_veo_prompt",
            {"topic": "test"},
        )
        
        assert merged["topic"] == "test"
        assert merged["style"] == "cinematic"  # default
    
    @pytest.mark.asyncio
    async def test_execute_teaching_tool(self, executor):
        """Teaching 도구 실행"""
        result = await executor.execute(
            "generate_veo_prompt",
            {"topic": "요리 브이로그"},
        )
        
        assert result["success"] is True
        assert result["node_spec"] is not None
    
    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, executor):
        """알 수 없는 도구 실행"""
        result = await executor.execute(
            "unknown_tool",
            {},
        )
        
        assert result["success"] is False
    
    def test_stats(self, executor):
        """통계"""
        stats = executor.get_stats()
        
        assert "available_tools" in stats
        assert len(stats["available_tools"]) == 9


class TestIntegration:
    """통합 테스트"""
    
    def test_tool_handlers_count(self):
        """TOOL_HANDLERS 수"""
        assert len(TOOL_HANDLERS) == 9
    
    def test_capsule_configs_count(self):
        """CAPSULE_CONFIGS 수"""
        assert len(CAPSULE_CONFIGS) >= 6
    
    def test_singleton_instance(self):
        """싱글톤"""
        assert agent_tool_executor is not None
