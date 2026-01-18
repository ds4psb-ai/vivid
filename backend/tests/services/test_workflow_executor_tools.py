"""Tool Mapping Tests for Workflow Executor (Phase 2-3 Registry-Based).

Tests that all frontend-expected tools exist in backend tool registry
and have proper configurations.

Frontend tools (from frontend/src/app/flow/page.tsx):
- prompt_generator, storyboard, image_tool, reference_analyzer
- quality_check, aesthetic_direct, persona_analyze
- story_architect, sound_craft, veo_generate
"""
import pytest
from unittest.mock import MagicMock

from app.services.workflow_tool_registry import (
    get_tool_spec,
    get_all_tools,
    list_tool_ids,
)
from app.services.workflow_adapters import (
    build_quality_check_inputs,
    build_aesthetic_inputs,
    build_persona_inputs,
    build_story_architect_inputs,
    build_sound_craft_inputs,
    build_veo_inputs,
)
from app.dimension_adapter import DimensionCapsuleId


REQUIRED_TOOLS = [
    "prompt_generator",
    "storyboard",
    "image_tool",
    "reference_analyzer",
    "quality_check",
    "aesthetic_direct",
    "persona_analyze",
    "story_architect",
    "sound_craft",
    "veo_generate",
]


class TestToolMappingCompleteness:
    """Test that all frontend tools exist in backend."""

    def test_all_frontend_tools_exist_in_backend(self):
        """All tools defined in frontend must exist in backend registry."""
        all_tools = get_all_tools()
        missing = [t for t in REQUIRED_TOOLS if t not in all_tools]
        assert not missing, f"Missing tools: {missing}"

    def test_all_tools_have_input_adapters(self):
        """All tools should have corresponding input adapters."""
        missing = []
        for tool_id in REQUIRED_TOOLS:
            spec = get_tool_spec(tool_id)
            if spec is None or spec.input_adapter is None:
                missing.append(tool_id)
        assert not missing, f"Missing adapters: {missing}"


class TestToolConfigValidation:
    """Test that tool configs have all required fields."""

    def test_all_tools_have_required_fields(self):
        """Each tool config must have capsule_id, tool_key, default_model, credit_cost."""
        for tool_id in REQUIRED_TOOLS:
            spec = get_tool_spec(tool_id)
            assert spec is not None, f"Tool {tool_id} not found"
            assert spec.capsule_id is not None, f"Tool {tool_id} missing capsule_id"
            assert spec.tool_key is not None, f"Tool {tool_id} missing tool_key"
            assert spec.default_model is not None, f"Tool {tool_id} missing default_model"
            assert spec.credit_cost >= 0, f"Tool {tool_id} has invalid credit_cost"

    def test_capsule_ids_are_valid_enums(self):
        """capsule_id must be a valid DimensionCapsuleId enum."""
        for tool_id in REQUIRED_TOOLS:
            spec = get_tool_spec(tool_id)
            assert isinstance(spec.capsule_id, DimensionCapsuleId)

    def test_credit_costs_are_positive(self):
        """credit_cost must be positive integer."""
        for tool_id in REQUIRED_TOOLS:
            spec = get_tool_spec(tool_id)
            assert spec.credit_cost > 0


class TestExtendedToolMappings:
    """Test extended tool specific mappings."""

    def test_quality_check_mapping(self):
        spec = get_tool_spec("quality_check")
        assert spec.capsule_id == DimensionCapsuleId.QUALITY_CHECK

    def test_aesthetic_direct_mapping(self):
        spec = get_tool_spec("aesthetic_direct")
        assert spec.capsule_id == DimensionCapsuleId.AESTHETIC_DIRECT

    def test_persona_analyze_mapping(self):
        spec = get_tool_spec("persona_analyze")
        assert spec.capsule_id == DimensionCapsuleId.PERSONA_ANALYZE

    def test_story_architect_mapping(self):
        spec = get_tool_spec("story_architect")
        assert spec.capsule_id == DimensionCapsuleId.STORY_ARCHITECT

    def test_sound_craft_mapping(self):
        spec = get_tool_spec("sound_craft")
        assert spec.capsule_id == DimensionCapsuleId.SOUND_CRAFT

    def test_veo_generate_alias(self):
        spec_alias = get_tool_spec("veo_generate")
        spec_original = get_tool_spec("veo_generator")
        # Aliases should resolve to the same spec object
        assert spec_alias is spec_original


class TestNewInputAdapters:
    """Test the new input adapter functions."""

    @pytest.fixture
    def mock_session(self):
        return MagicMock(
            extracted_params={
                "prompt": "default prompt",
                "style": "cinematic",
                "mood": "dramatic",
                "language": "ko",
            }
        )

    def test_build_quality_check_inputs(self, mock_session):
        node_inputs = {"content": "Test", "criteria": ["clarity"]}
        result = build_quality_check_inputs(node_inputs, mock_session)
        assert result["content"] == "Test"
        assert result["criteria"] == ["clarity"]

    def test_build_aesthetic_direct_inputs(self, mock_session):
        node_inputs = {"prompt": "neon cityscape", "auteur_key": "kubrick"}
        result = build_aesthetic_inputs(node_inputs, mock_session)
        assert result["prompt"] == "neon cityscape"
        assert result["auteur_key"] == "kubrick"

    def test_build_persona_analyze_inputs(self, mock_session):
        node_inputs = {"character_description": "A detective"}
        result = build_persona_inputs(node_inputs, mock_session)
        assert result["character_description"] == "A detective"

    def test_build_story_architect_inputs(self, mock_session):
        node_inputs = {"prompt": "A journey", "genre": "fantasy"}
        result = build_story_architect_inputs(node_inputs, mock_session)
        assert result["prompt"] == "A journey"
        assert result["genre"] == "fantasy"

    def test_build_sound_craft_inputs(self, mock_session):
        node_inputs = {"scene_description": "Forest at dawn", "mood": "peaceful"}
        result = build_sound_craft_inputs(node_inputs, mock_session)
        assert result["scene_description"] == "Forest at dawn"
        assert result["mood"] == "peaceful"

    def test_veo_generate_uses_same_adapter(self):
        spec_alias = get_tool_spec("veo_generate")
        spec_original = get_tool_spec("veo_generator")
        assert spec_alias.input_adapter is spec_original.input_adapter
