"""P2: Workflow Executor Tests (Phase 2-3 Registry-Based).

Tests for workflow_executor.py:
- Input adapters (via workflow_adapters.py)
- Tool registry (via workflow_tool_registry.py)
- execute_step()
- execute_all_steps()
- seed_first_node_inputs()
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.workflow_executor import (
    WorkflowStepResult,
    seed_first_node_inputs,
    execute_step,
)
from app.services.workflow_tool_registry import (
    get_tool_spec,
    get_all_tools,
    list_tool_ids,
)
from app.services.workflow_adapters import (
    build_prompt_inputs,
    build_storyboard_inputs,
    build_image_inputs,
    build_reference_inputs,
    build_veo_inputs,
)
from app.schemas.workflow_session import (
    WorkflowSession,
    WorkflowNodeState,
    WorkflowStatus,
    workflow_session_manager,
)
from app.dimension_adapter import DimensionCapsuleId


# =============================================================================
# Unit Tests: Tool Registry (Phase 2-3)
# =============================================================================

class TestWorkflowToolRegistry:
    """Decorator-based tool registry tests."""

    def test_all_tools_have_required_fields(self):
        """모든 도구에 필수 필드가 있는지 확인."""
        all_tools = get_all_tools()

        for tool_id, spec in all_tools.items():
            assert spec.capsule_id is not None, f"{tool_id} missing capsule_id"
            assert spec.tool_key is not None, f"{tool_id} missing tool_key"
            assert spec.default_model is not None, f"{tool_id} missing default_model"
            assert spec.credit_cost >= 0, f"{tool_id} has invalid credit_cost"

    def test_capsule_ids_are_valid_enums(self):
        """capsule_id가 유효한 DimensionCapsuleId enum인지 확인."""
        all_tools = get_all_tools()
        for tool_id, spec in all_tools.items():
            assert isinstance(spec.capsule_id, DimensionCapsuleId), \
                f"{tool_id} has invalid capsule_id"

    def test_prompt_generator_mapping(self):
        """prompt_generator 매핑 정확성."""
        spec = get_tool_spec("prompt_generator")
        assert spec is not None
        assert spec.capsule_id == DimensionCapsuleId.PROMPT_GENERATE
        assert spec.tool_key == "generate_veo_prompt"

    def test_storyboard_mapping(self):
        """storyboard 매핑 정확성."""
        spec = get_tool_spec("storyboard")
        assert spec is not None
        assert spec.capsule_id == DimensionCapsuleId.STORYBOARD_CREATE
        assert spec.tool_key == "create_storyboard"

    def test_list_tool_ids(self):
        """list_tool_ids() returns unique tool IDs."""
        tool_ids = list_tool_ids()
        assert len(tool_ids) >= 10  # At least 10 core tools
        assert "prompt_generator" in tool_ids
        assert "veo_generator" in tool_ids

    def test_alias_resolution(self):
        """Aliases resolve to the same spec as primary ID."""
        primary = get_tool_spec("veo_generator")
        alias = get_tool_spec("veo_generate")
        assert primary is alias  # Same object

    def test_frozen_spec_immutability(self):
        """WorkflowToolSpec is immutable (frozen dataclass)."""
        spec = get_tool_spec("prompt_generator")
        with pytest.raises(AttributeError):
            spec.credit_cost = 9999  # Should raise


# =============================================================================
# Unit Tests: Input Adapters
# =============================================================================

class TestInputAdapters:
    """Input adapter function tests (Phase 2-3)."""

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

        result = build_prompt_inputs(node_inputs, mock_session)

        assert result["topic"] == "우주 탐험"  # node > session
        assert result["mood"] == "hopeful"
        assert result["style"] == "cinematic"  # fallback to session

    def test_build_prompt_inputs_defaults(self, mock_session):
        """기본값 적용 확인."""
        node_inputs = {}
        mock_session.extracted_params = {}

        result = build_prompt_inputs(node_inputs, mock_session)

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
        result = build_storyboard_inputs(node_inputs, mock_session)
        assert result["concept"] == "직접 컨셉"

        # Only script (backwards compat)
        node_inputs = {"script": "레거시 스크립트"}
        result = build_storyboard_inputs(node_inputs, mock_session)
        assert result["concept"] == "레거시 스크립트"
        assert result["prompt"] == "레거시 스크립트"

    def test_build_storyboard_inputs_scene_count(self, mock_session):
        """scene_count 정수 변환."""
        node_inputs = {"scene_count": "8"}
        result = build_storyboard_inputs(node_inputs, mock_session)
        assert result["scene_count"] == 8
        assert isinstance(result["scene_count"], int)

    def test_build_image_inputs(self, mock_session):
        """이미지 입력 변환."""
        node_inputs = {"description": "네온 도시 야경"}
        result = build_image_inputs(node_inputs, mock_session)

        assert result["description"] == "네온 도시 야경"
        assert result["aspect_ratio"] == "16:9"  # default

    def test_build_reference_inputs_video_description(self, mock_session):
        """4D: video_description 필드 사용 (description 폴백)."""
        # New field
        node_inputs = {"video_description": "빠른 컷 편집의 액션 시퀀스"}
        result = build_reference_inputs(node_inputs, mock_session)
        assert result["video_description"] == "빠른 컷 편집의 액션 시퀀스"

        # Fallback to description
        node_inputs = {"description": "액션 장면 분석"}
        result = build_reference_inputs(node_inputs, mock_session)
        assert result["video_description"] == "액션 장면 분석"

    def test_build_veo_inputs(self, mock_session):
        """VEO 입력 변환."""
        node_inputs = {"prompt": "드론 샷, 해변 일몰", "duration": "8"}
        result = build_veo_inputs(node_inputs, mock_session)

        assert result["prompt"] == "드론 샷, 해변 일몰"
        assert result["duration"] == 8
        assert result["aspect_ratio"] == "16:9"

    def test_input_adapter_from_registry(self, mock_session):
        """Registry에서 input_adapter 함수 직접 호출."""
        spec = get_tool_spec("prompt_generator")
        assert spec.input_adapter is not None

        node_inputs = {"topic": "레지스트리 테스트"}
        result = spec.input_adapter(node_inputs, mock_session)
        assert result["topic"] == "레지스트리 테스트"


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


    def test_seed_first_node_priority(self):
        """초기 파라미터가 기존 세션 파라미터를 덮어쓰는지 확인."""
        session = workflow_session_manager.create_session(
            user_id="test",
            template_id="test",
            template_name="Test",
            template_description="Test",
            nodes=[{"id": "n1", "tool_id": "test", "data": {"inputs": {}}}],
            connections=[],
            original_request="req",
            extracted_params={"topic": "Old Topic", "style": "Old Style"},
            estimated_credits=10,
        )

        # Act: New params should overwrite Old
        seed_first_node_inputs(session.id, {"topic": "New Topic"})

        updated = workflow_session_manager.get_session(session.id)
        assert updated.extracted_params["topic"] == "New Topic"  # Overwritten
        assert updated.extracted_params["style"] == "Old Style"  # Preserved
        assert updated.nodes[0].inputs["topic"] == "New Topic"


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
        # Fix: metrics needs to be an object to support dot notation (AttributeError fix test)
        mock_metrics = MagicMock()
        mock_metrics.credits_charged = 10
        mock_metrics.latency_ms = 500

        mock_result = MagicMock(
            success=True,
            output={"prompt": "A cyberpunk cityscape at night...", "negative_prompt": "blurry"},
            error=None,
            metrics=mock_metrics,
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
