"""Tool Mapping Tests for Workflow Executor.

Tests that all frontend-expected tools exist in backend WORKFLOW_TOOL_MAP
and have proper configurations.

Frontend tools (from frontend/src/app/flow/page.tsx):
- prompt_generator, storyboard, image_tool, reference_analyzer
- quality_check, aesthetic_direct, persona_analyze
- story_architect, sound_craft, veo_generate
"""
import pytest
from unittest.mock import MagicMock

from app.services.workflow_executor import (
    WORKFLOW_TOOL_MAP,
    INPUT_ADAPTERS,
    _build_quality_check_inputs,
    _build_aesthetic_direct_inputs,
    _build_persona_analyze_inputs,
    _build_story_architect_inputs,
    _build_sound_craft_inputs,
    _build_veo_inputs,
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
        """All tools defined in frontend must exist in backend WORKFLOW_TOOL_MAP."""
        missing = [t for t in REQUIRED_TOOLS if t not in WORKFLOW_TOOL_MAP]
        assert not missing, f"Missing tools: {missing}"

    def test_all_tools_have_input_adapters(self):
        """All tools should have corresponding input adapters."""
        missing = [t for t in REQUIRED_TOOLS if t not in INPUT_ADAPTERS]
        assert not missing, f"Missing adapters: {missing}"


class TestToolConfigValidation:
    """Test that tool configs have all required fields."""

    REQUIRED_FIELDS = ["capsule_id", "tool_key", "default_model", "credit_cost"]

    def test_all_tools_have_required_fields(self):
        """Each tool config must have capsule_id, tool_key, default_model, credit_cost."""
        for tool_id in REQUIRED_TOOLS:
            config = WORKFLOW_TOOL_MAP.get(tool_id)
            assert config is not None, f"Tool {tool_id} not found"
            for field in self.REQUIRED_FIELDS:
                assert field in config, f"Tool {tool_id} missing field: {field}"

    def test_capsule_ids_are_valid_enums(self):
        """capsule_id must be a valid DimensionCapsuleId enum."""
        for tool_id in REQUIRED_TOOLS:
            config = WORKFLOW_TOOL_MAP.get(tool_id)
            assert isinstance(config["capsule_id"], DimensionCapsuleId)

    def test_credit_costs_are_positive(self):
        """credit_cost must be positive integer."""
        for tool_id in REQUIRED_TOOLS:
            config = WORKFLOW_TOOL_MAP.get(tool_id)
            assert config["credit_cost"] > 0


class TestExtendedToolMappings:
    """Test extended tool specific mappings."""

    def test_quality_check_mapping(self):
        spec = WORKFLOW_TOOL_MAP["quality_check"]
        assert spec["capsule_id"] == DimensionCapsuleId.QUALITY_CHECK

    def test_aesthetic_direct_mapping(self):
        spec = WORKFLOW_TOOL_MAP["aesthetic_direct"]
        assert spec["capsule_id"] == DimensionCapsuleId.AESTHETIC_DIRECT

    def test_persona_analyze_mapping(self):
        spec = WORKFLOW_TOOL_MAP["persona_analyze"]
        assert spec["capsule_id"] == DimensionCapsuleId.PERSONA_ANALYZE

    def test_story_architect_mapping(self):
        spec = WORKFLOW_TOOL_MAP["story_architect"]
        assert spec["capsule_id"] == DimensionCapsuleId.STORY_ARCHITECT

    def test_sound_craft_mapping(self):
        spec = WORKFLOW_TOOL_MAP["sound_craft"]
        assert spec["capsule_id"] == DimensionCapsuleId.SOUND_CRAFT

    def test_veo_generate_alias(self):
        spec_alias = WORKFLOW_TOOL_MAP["veo_generate"]
        spec_original = WORKFLOW_TOOL_MAP["veo_generator"]
        assert spec_alias["capsule_id"] == spec_original["capsule_id"]


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
        result = _build_quality_check_inputs(node_inputs, mock_session)
        assert result["content"] == "Test"
        assert result["criteria"] == ["clarity"]

    def test_build_aesthetic_direct_inputs(self, mock_session):
        node_inputs = {"prompt": "neon cityscape", "auteur_key": "kubrick"}
        result = _build_aesthetic_direct_inputs(node_inputs, mock_session)
        assert result["prompt"] == "neon cityscape"
        assert result["auteur_key"] == "kubrick"

    def test_build_persona_analyze_inputs(self, mock_session):
        node_inputs = {"character_description": "A detective"}
        result = _build_persona_analyze_inputs(node_inputs, mock_session)
        assert result["character_description"] == "A detective"

    def test_build_story_architect_inputs(self, mock_session):
        node_inputs = {"prompt": "A journey", "genre": "fantasy"}
        result = _build_story_architect_inputs(node_inputs, mock_session)
        assert result["prompt"] == "A journey"
        assert result["genre"] == "fantasy"

    def test_build_sound_craft_inputs(self, mock_session):
        node_inputs = {"scene_description": "Forest at dawn", "mood": "peaceful"}
        result = _build_sound_craft_inputs(node_inputs, mock_session)
        assert result["scene_description"] == "Forest at dawn"
        assert result["mood"] == "peaceful"

    def test_veo_generate_uses_same_adapter(self):
        assert INPUT_ADAPTERS["veo_generate"] == INPUT_ADAPTERS["veo_generator"]
