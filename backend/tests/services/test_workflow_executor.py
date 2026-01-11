"""P2: Workflow Executor Tests.

Tests for workflow_executor.py:
- Input adapters
- WORKFLOW_TOOL_MAP
- execute_step()
- execute_all_steps()
- seed_first_node_inputs()
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.workflow_executor import (
    WORKFLOW_TOOL_MAP,
    WorkflowStepResult,
    _build_prompt_inputs,
    _build_storyboard_inputs,
    _build_image_inputs,
    _build_reference_inputs,
    _build_veo_inputs,
    seed_first_node_inputs,
    execute_step,
)
from app.schemas.workflow_session import (
    WorkflowSession,
    WorkflowNodeState,
    WorkflowStatus,
    workflow_session_manager,
)
from app.dimension_adapter import DimensionCapsuleId


# =============================================================================
# Unit Tests: WORKFLOW_TOOL_MAP
# =============================================================================

class TestWorkflowToolMap:
    """WORKFLOW_TOOL_MAP SSoT tests."""
    
    def test_all_tools_have_required_fields(self):
        """모든 도구에 필수 필드가 있는지 확인."""
        required_fields = ["capsule_id", "tool_key", "default_model", "credit_cost"]
        
        for tool_id, spec in WORKFLOW_TOOL_MAP.items():
            for field in required_fields:
                assert field in spec, f"{tool_id} missing {field}"
    
    def test_capsule_ids_are_valid_enums(self):
        """capsule_id가 유효한 DimensionCapsuleId enum인지 확인."""
        for tool_id, spec in WORKFLOW_TOOL_MAP.items():
            assert isinstance(spec["capsule_id"], DimensionCapsuleId), \
                f"{tool_id} has invalid capsule_id"
    
    def test_prompt_generator_mapping(self):
        """prompt_generator 매핑 정확성."""
        spec = WORKFLOW_TOOL_MAP["prompt_generator"]
        assert spec["capsule_id"] == DimensionCapsuleId.PROMPT_GENERATE
        assert spec["tool_key"] == "generate_veo_prompt"
    
    def test_storyboard_mapping(self):
        """storyboard 매핑 정확성."""
        spec = WORKFLOW_TOOL_MAP["storyboard"]
        assert spec["capsule_id"] == DimensionCapsuleId.STORYBOARD_CREATE
        assert spec["tool_key"] == "create_storyboard"


# =============================================================================
# Unit Tests: Input Adapters
# =============================================================================

class TestInputAdapters:
    """Input adapter function tests."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock WorkflowSession."""
        return MagicMock(
            extracted_params={
                "topic": "사이버펑크 도시",
                "style": "cinematic",
                "language": "ko",
            }
        )
    
    def test_build_prompt_inputs_with_node_inputs(self, mock_session):
        """node_inputs가 session보다 우선."""
        node_inputs = {"topic": "우주 탐험", "mood": "hopeful"}
        
        result = _build_prompt_inputs(node_inputs, mock_session)
        
        assert result["topic"] == "우주 탐험"  # node > session
        assert result["mood"] == "hopeful"
        assert result["style"] == "cinematic"  # fallback to session
    
    def test_build_prompt_inputs_defaults(self, mock_session):
        """기본값 적용 확인."""
        node_inputs = {}
        mock_session.extracted_params = {}
        
        result = _build_prompt_inputs(node_inputs, mock_session)
        
        assert result["style"] == "cinematic"  # default
        assert result["duration"] == "8 seconds"  # default
        assert result["language"] == "ko"  # default
    
    def test_build_storyboard_inputs_concept_priority(self, mock_session):
        """storyboard: concept > prompt > script 우선순위."""
        # All three present
        node_inputs = {
            "concept": "직접 컨셉",
            "prompt": "프롬프트",
            "script": "스크립트",
        }
        result = _build_storyboard_inputs(node_inputs, mock_session)
        assert result["concept"] == "직접 컨셉"
        
        # Only script (backwards compat)
        node_inputs = {"script": "레거시 스크립트"}
        result = _build_storyboard_inputs(node_inputs, mock_session)
        assert result["concept"] == "레거시 스크립트"
        assert result["prompt"] == "레거시 스크립트"
    
    def test_build_storyboard_inputs_scene_count(self, mock_session):
        """scene_count 정수 변환."""
        node_inputs = {"scene_count": "8"}
        result = _build_storyboard_inputs(node_inputs, mock_session)
        assert result["scene_count"] == 8
        assert isinstance(result["scene_count"], int)
    
    def test_build_image_inputs(self, mock_session):
        """이미지 입력 변환."""
        node_inputs = {"description": "네온 도시 야경"}
        result = _build_image_inputs(node_inputs, mock_session)
        
        assert result["description"] == "네온 도시 야경"
        assert result["aspect_ratio"] == "16:9"  # default
    
    def test_build_reference_inputs_video_description(self, mock_session):
        """4D: video_description 필드 사용 (video_url 폴백)."""
        # New field
        node_inputs = {"video_description": "빠른 컷 편집의 액션 시퀀스"}
        result = _build_reference_inputs(node_inputs, mock_session)
        assert result["video_description"] == "빠른 컷 편집의 액션 시퀀스"
        
        # Old field (backwards compat)
        node_inputs = {"video_url": "https://youtube.com/xxx"}
        result = _build_reference_inputs(node_inputs, mock_session)
        assert result["video_description"] == "https://youtube.com/xxx"
    
    def test_build_veo_inputs(self, mock_session):
        """VEO 입력 변환."""
        node_inputs = {"prompt": "드론 샷, 해변 일몰", "duration": "8"}
        result = _build_veo_inputs(node_inputs, mock_session)
        
        assert result["prompt"] == "드론 샷, 해변 일몰"
        assert result["duration"] == 8
        assert result["aspect_ratio"] == "16:9"


# =============================================================================
# Unit Tests: seed_first_node_inputs
# =============================================================================

class TestSeedFirstNodeInputs:
    """seed_first_node_inputs() tests."""
    
    def test_seed_first_node_success(self):
        """첫 노드에 파라미터 주입 성공."""
        # Setup: 세션 생성
        session = workflow_session_manager.create_session(
            user_id="test-user",
            template_id="test-template",
            template_name="Test",
            template_description="Test workflow",
            nodes=[{
                "id": "node-1",
                "tool_id": "prompt_generator",
                "data": {"inputs": {}},
            }],
            connections=[],
            original_request="테스트 요청",
            extracted_params={},
            estimated_credits=10,
        )
        
        # Act
        result = seed_first_node_inputs(session.id, {"topic": "테스트 주제", "style": "anime"})
        
        # Assert
        assert result is True
        updated_session = workflow_session_manager.get_session(session.id)
        assert updated_session.nodes[0].inputs["topic"] == "테스트 주제"
        assert updated_session.nodes[0].inputs["style"] == "anime"
        assert updated_session.extracted_params["topic"] == "테스트 주제"
        
        # Cleanup
        workflow_session_manager._sessions.pop(session.id, None)
    
    def test_seed_nonexistent_session(self):
        """존재하지 않는 세션."""
        result = seed_first_node_inputs("nonexistent-session", {"topic": "test"})
        assert result is False


# =============================================================================
# Integration Tests: execute_step (Mocked)
# =============================================================================

class TestExecuteStep:
    """execute_step() tests with mocked _execute_dimension_tool."""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_user(self):
        return {"id": "test-user-123", "email": "test@test.com"}
    
    @pytest.fixture
    def test_session(self):
        """테스트용 워크플로우 세션."""
        session = workflow_session_manager.create_session(
            user_id="test-user-123",
            template_id="quick_prompt",
            template_name="Quick Prompt",
            template_description="빠른 프롬프트 생성",
            nodes=[{
                "id": "node-1",
                "tool_id": "prompt_generator",
                "data": {"inputs": {"topic": "사이버펑크 도시"}},
            }],
            connections=[],
            original_request="사이버펑크 도시 영상 만들어줘",
            extracted_params={"topic": "사이버펑크 도시"},
            estimated_credits=10,
        )
        yield session
        # Cleanup
        workflow_session_manager._sessions.pop(session.id, None)
    
    @pytest.mark.asyncio
    async def test_execute_step_success(self, test_session, mock_db, mock_user):
        """성공적인 스텝 실행."""
        mock_result = MagicMock(
            success=True,
            output={"prompt": "A cyberpunk cityscape at night...", "negative_prompt": "blurry"},
            error=None,
            metrics={"credit_cost": 10, "latency_ms": 500},
        )
        
        with patch("app.services.workflow_executor._execute_dimension_tool", return_value=mock_result):
            result = await execute_step(
                session_id=test_session.id,
                user=mock_user,
                db=mock_db,
                byok_key=None,
            )
        
        assert result.success is True
        assert result.tool_id == "prompt_generator"
        assert "prompt" in result.output
        assert result.credits_used == 10
        
        # 세션 상태 확인
        session = workflow_session_manager.get_session(test_session.id)
        assert session.nodes[0].status == "completed"
        assert session.status == WorkflowStatus.COMPLETED  # 마지막 노드였으므로
    
    @pytest.mark.asyncio
    async def test_execute_step_already_completed(self, test_session, mock_db, mock_user):
        """이미 완료된 노드 재실행 방지 (idempotency)."""
        # 먼저 노드를 완료 상태로 설정
        test_session.nodes[0].status = "completed"
        test_session.nodes[0].output = {"prompt": "already done"}
        workflow_session_manager.update_session(test_session)
        
        result = await execute_step(
            session_id=test_session.id,
            user=mock_user,
            db=mock_db,
            byok_key=None,
        )
        
        # 실행되지 않고 기존 결과 반환
        assert result.success is True
        assert result.credits_used == 0  # 크레딧 재차감 없음
        assert result.output == {"prompt": "already done"}
    
    @pytest.mark.asyncio
    async def test_execute_step_unknown_tool(self, mock_db, mock_user):
        """알 수 없는 tool_id 에러."""
        session = workflow_session_manager.create_session(
            user_id="test-user-123",
            template_id="test",
            template_name="Test",
            template_description="Test",
            nodes=[{
                "id": "node-1",
                "tool_id": "unknown_tool",  # 없는 도구
                "data": {"inputs": {}},
            }],
            connections=[],
            original_request="test",
            extracted_params={},
            estimated_credits=10,
        )
        
        try:
            result = await execute_step(
                session_id=session.id,
                user=mock_user,
                db=mock_db,
                byok_key=None,
            )
            
            assert result.success is False
            assert "Unknown tool_id" in result.error
            
            # 세션 상태 확인
            updated_session = workflow_session_manager.get_session(session.id)
            assert updated_session.status == WorkflowStatus.FAILED
        finally:
            workflow_session_manager._sessions.pop(session.id, None)


# =============================================================================
# Run with: pytest -v tests/services/test_workflow_executor.py
# =============================================================================
