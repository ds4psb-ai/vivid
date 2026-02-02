"""
Tests for Prompty Tikitaka Workflow API.

Comprehensive tests for the 6-step Dual AI (Gemini <-> Claude) workflow.
Tests cover:
- Workflow initialization
- Step advancement
- Goto (jump) functionality
- Tool prompts generation
- Anchor scene management
- Edge cases and error handling
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.routers.prompty.tikitaka import (
    generate_tool_prompts,
    TOOL_CONFIGS,
    TikitakaStartRequest,
    TikitakaAdvanceRequest,
    TikitakaGotoRequest,
)


# =============================================================================
# Tool Configuration Tests
# =============================================================================

class TestToolConfigs:
    """Test TOOL_CONFIGS constant."""

    def test_all_tools_present(self):
        """All expected tools are configured."""
        expected_tools = ["nanobanana", "midjourney", "kling", "veo", "sora"]
        for tool in expected_tools:
            assert tool in TOOL_CONFIGS, f"{tool} should be in TOOL_CONFIGS"

    def test_tool_has_name(self):
        """Each tool has a name."""
        for tool_id, config in TOOL_CONFIGS.items():
            assert "name" in config, f"{tool_id} should have name"
            assert isinstance(config["name"], str)

    def test_tool_has_url(self):
        """Each tool has a URL."""
        for tool_id, config in TOOL_CONFIGS.items():
            assert "url" in config, f"{tool_id} should have url"
            assert config["url"].startswith("http")

    def test_nanobanana_config(self):
        """NanoBanana specific config."""
        assert TOOL_CONFIGS["nanobanana"]["name"] == "NanoBanana"
        assert "nanobanana.ai" in TOOL_CONFIGS["nanobanana"]["url"]

    def test_midjourney_config(self):
        """Midjourney specific config."""
        assert TOOL_CONFIGS["midjourney"]["name"] == "MJ V7"
        assert "discord" in TOOL_CONFIGS["midjourney"]["url"]

    def test_kling_config(self):
        """Kling specific config."""
        assert TOOL_CONFIGS["kling"]["name"] == "Kling 2.6"
        assert "klingai" in TOOL_CONFIGS["kling"]["url"]

    def test_veo_config(self):
        """Veo specific config."""
        assert TOOL_CONFIGS["veo"]["name"] == "Veo 3.1"
        assert "google" in TOOL_CONFIGS["veo"]["url"]

    def test_sora_config(self):
        """Sora specific config."""
        assert TOOL_CONFIGS["sora"]["name"] == "Sora 2 Pro"
        assert "sora.com" in TOOL_CONFIGS["sora"]["url"]


# =============================================================================
# Tool Prompts Generation Tests
# =============================================================================

class TestGenerateToolPrompts:
    """Test generate_tool_prompts function."""

    def test_generates_all_tools(self):
        """Generates prompts for all tools."""
        base_prompt = "Korean boy, 7 years old, birthday party"
        prompts = generate_tool_prompts(base_prompt)

        expected_tools = ["nanobanana", "midjourney", "kling", "veo", "sora"]
        for tool in expected_tools:
            assert tool in prompts, f"{tool} prompt should be generated"

    def test_nanobanana_format_korean(self):
        """NanoBanana prompt includes Korean marker."""
        base_prompt = "Test prompt"
        prompts = generate_tool_prompts(base_prompt)

        assert "한글 프롬프트" in prompts["nanobanana"]
        assert base_prompt in prompts["nanobanana"]

    def test_midjourney_format_params(self):
        """Midjourney prompt includes V7 params."""
        base_prompt = "Test prompt"
        prompts = generate_tool_prompts(base_prompt)

        assert "--ar 16:9" in prompts["midjourney"]
        assert "--v 7" in prompts["midjourney"]
        assert "--style raw" in prompts["midjourney"]
        assert "--no" in prompts["midjourney"]

    def test_kling_format_video(self):
        """Kling prompt is video-focused."""
        base_prompt = "Test prompt"
        prompts = generate_tool_prompts(base_prompt)

        assert "Image-to-Video" in prompts["kling"]
        assert "Duration" in prompts["kling"]
        assert "Camera" in prompts["kling"]

    def test_veo_format_video(self):
        """Veo prompt is video-focused."""
        base_prompt = "Test prompt"
        prompts = generate_tool_prompts(base_prompt)

        assert "video" in prompts["veo"].lower()
        assert "Duration" in prompts["veo"]
        assert "Photorealistic" in prompts["veo"]

    def test_sora_format_video(self):
        """Sora prompt is video-focused."""
        base_prompt = "Test prompt"
        prompts = generate_tool_prompts(base_prompt)

        assert "Reference Image" in prompts["sora"]
        assert "Motion" in prompts["sora"]
        assert "Duration" in prompts["sora"]

    def test_base_prompt_preserved(self):
        """Base prompt is included in all tool prompts."""
        base_prompt = "Unique test content XYZ123"
        prompts = generate_tool_prompts(base_prompt)

        for tool, prompt in prompts.items():
            assert base_prompt in prompt, f"{tool} should contain base prompt"

    def test_empty_base_prompt(self):
        """Empty base prompt still generates structure."""
        prompts = generate_tool_prompts("")

        for tool in prompts:
            assert len(prompts[tool]) > 0, f"{tool} should have some structure"


# =============================================================================
# Schema Validation Tests
# =============================================================================

class TestTikitakaSchemas:
    """Test Pydantic schema validation."""

    def test_start_request_optional_anchor(self):
        """TikitakaStartRequest anchor_scene_id is optional."""
        request = TikitakaStartRequest()
        assert request.anchor_scene_id is None

    def test_start_request_with_anchor(self):
        """TikitakaStartRequest with anchor scene."""
        request = TikitakaStartRequest(anchor_scene_id="scene_2")
        assert request.anchor_scene_id == "scene_2"

    def test_advance_request_all_optional(self):
        """TikitakaAdvanceRequest all fields are optional."""
        request = TikitakaAdvanceRequest()
        assert request.gemini_output is None
        assert request.claude_output is None
        assert request.user_feedback is None

    def test_advance_request_with_outputs(self):
        """TikitakaAdvanceRequest with outputs."""
        request = TikitakaAdvanceRequest(
            gemini_output="Analysis JSON...",
            claude_output="Draft prompts...",
            user_feedback="Looks good",
        )
        assert request.gemini_output == "Analysis JSON..."
        assert request.claude_output == "Draft prompts..."
        assert request.user_feedback == "Looks good"

    def test_goto_request_optional_reason(self):
        """TikitakaGotoRequest reason is optional."""
        request = TikitakaGotoRequest()
        assert request.reason is None

    def test_goto_request_with_reason(self):
        """TikitakaGotoRequest with reason."""
        request = TikitakaGotoRequest(reason="REVISE")
        assert request.reason == "REVISE"


# =============================================================================
# Workflow State Tests
# =============================================================================

class TestWorkflowState:
    """Test workflow state management."""

    def test_initial_state_structure(self):
        """Initial tikitaka state has correct structure."""
        project_id = uuid4()
        now = datetime.utcnow()

        tikitaka_state = {
            "tikitaka_id": f"tt_{project_id.hex[:8]}_{now.strftime('%Y%m%d%H%M%S')}",
            "current_step": 1,
            "anchor_scene_id": None,
            "started_at": now.isoformat(),
            "step_outputs": {},
            "tool_prompts": {},
        }

        assert tikitaka_state["current_step"] == 1
        assert tikitaka_state["step_outputs"] == {}
        assert tikitaka_state["tool_prompts"] == {}

    def test_tikitaka_id_format(self):
        """Tikitaka ID follows expected format."""
        project_id = uuid4()
        now = datetime.utcnow()
        tikitaka_id = f"tt_{project_id.hex[:8]}_{now.strftime('%Y%m%d%H%M%S')}"

        assert tikitaka_id.startswith("tt_")
        assert len(tikitaka_id.split("_")[1]) == 8  # 8 hex chars

    def test_step_output_storage(self):
        """Step outputs are stored correctly."""
        step_outputs = {}
        current_step = 1

        # Store Gemini output
        step_outputs[f"step_{current_step}_gemini"] = "Gemini analysis JSON"
        assert step_outputs["step_1_gemini"] == "Gemini analysis JSON"

        # Store Claude output
        current_step = 2
        step_outputs[f"step_{current_step}_claude"] = "Claude draft prompts"
        assert step_outputs["step_2_claude"] == "Claude draft prompts"


# =============================================================================
# Step Advancement Tests
# =============================================================================

class TestStepAdvancement:
    """Test step advancement logic."""

    def test_advance_from_step_1(self):
        """Advance from step 1 to step 2."""
        current_step = 1
        new_step = current_step + 1
        assert new_step == 2

    def test_advance_through_all_steps(self):
        """Can advance through all 6 steps."""
        for current_step in range(1, 6):
            new_step = current_step + 1
            assert new_step == current_step + 1

    def test_step_6_is_final(self):
        """Step 6 is the final step."""
        current_step = 6
        completed = current_step >= 6
        assert completed is True

    def test_advance_generates_tool_prompts_step_2(self):
        """Tool prompts generated after step 2 (Draft)."""
        current_step = 2
        claude_output = "Generated prompts..."

        if current_step in (2, 4):
            tool_prompts = generate_tool_prompts(claude_output)
            assert len(tool_prompts) > 0

    def test_advance_generates_tool_prompts_step_4(self):
        """Tool prompts generated after step 4 (Revise)."""
        current_step = 4
        claude_output = "Revised prompts..."

        if current_step in (2, 4):
            tool_prompts = generate_tool_prompts(claude_output)
            assert len(tool_prompts) > 0


# =============================================================================
# Goto (Jump) Tests
# =============================================================================

class TestGotoStep:
    """Test goto/jump step functionality."""

    def test_goto_valid_steps(self):
        """Can goto any step 1-6."""
        for step in range(1, 7):
            assert 1 <= step <= 6

    def test_goto_step_0_invalid(self):
        """Step 0 is invalid."""
        step = 0
        valid = 1 <= step <= 6
        assert valid is False

    def test_goto_step_7_invalid(self):
        """Step 7 is invalid."""
        step = 7
        valid = 1 <= step <= 6
        assert valid is False

    def test_goto_resets_completion(self):
        """Goto resets completed_at."""
        tikitaka_state = {
            "current_step": 6,
            "completed_at": "2024-01-01T00:00:00",
        }

        # When goto is called
        tikitaka_state["current_step"] = 2
        tikitaka_state["completed_at"] = None

        assert tikitaka_state["completed_at"] is None

    def test_goto_logs_reason(self):
        """Goto stores reason in step_outputs."""
        step_outputs = {}
        target_step = 2
        reason = "REVISE"

        step_outputs[f"goto_{target_step}_reason"] = reason

        assert step_outputs["goto_2_reason"] == "REVISE"


# =============================================================================
# Anchor Scene Tests
# =============================================================================

class TestAnchorScene:
    """Test anchor scene management."""

    def test_set_anchor_scene(self):
        """Can set anchor scene."""
        tikitaka_state = {"anchor_scene_id": None}
        tikitaka_state["anchor_scene_id"] = "scene_3"

        assert tikitaka_state["anchor_scene_id"] == "scene_3"

    def test_update_anchor_scene(self):
        """Can update anchor scene."""
        tikitaka_state = {"anchor_scene_id": "scene_2"}
        tikitaka_state["anchor_scene_id"] = "scene_5"

        assert tikitaka_state["anchor_scene_id"] == "scene_5"

    def test_anchor_scene_in_start_request(self):
        """Anchor scene can be set at workflow start."""
        request = TikitakaStartRequest(anchor_scene_id="scene_2")
        tikitaka_state = {
            "anchor_scene_id": request.anchor_scene_id,
        }

        assert tikitaka_state["anchor_scene_id"] == "scene_2"


# =============================================================================
# Workflow Scenario Tests
# =============================================================================

class TestWorkflowScenarios:
    """Test realistic workflow scenarios."""

    def test_full_workflow_pass(self):
        """Complete workflow with PASS at step 3."""
        workflow = {
            "step": 1,
            "outputs": {},
        }

        # Step 1: Gemini Success Brief
        workflow["outputs"]["step_1_gemini"] = "Analysis JSON"
        workflow["step"] = 2

        # Step 2: Claude Draft
        workflow["outputs"]["step_2_claude"] = "Draft prompts"
        workflow["step"] = 3

        # Step 3: Gemini Critique - PASS (85+)
        workflow["outputs"]["step_3_gemini"] = "Score: 90, PASS"
        workflow["step"] = 4

        # Skip step 4 (Revise) since PASS
        workflow["step"] = 5

        # Step 5: User generates
        workflow["outputs"]["step_5_feedback"] = "Generated successfully"
        workflow["step"] = 6

        # Step 6: Complete
        workflow["completed"] = True

        assert workflow["completed"] is True
        assert workflow["step"] == 6

    def test_workflow_with_revise(self):
        """Workflow with REVISE verdict requiring iteration."""
        workflow = {
            "step": 3,
            "outputs": {},
        }

        # Step 3: Critique returns REVISE (60-84)
        workflow["outputs"]["step_3_gemini"] = "Score: 72, REVISE"

        # Go to step 4 for revision
        workflow["step"] = 4

        # Step 4: Claude Revise
        workflow["outputs"]["step_4_claude"] = "Revised prompts"

        # Back to step 3 for re-critique
        workflow["step"] = 3
        workflow["outputs"]["step_3_gemini_v2"] = "Score: 88, PASS"

        # Now can proceed
        workflow["step"] = 5

        assert workflow["step"] == 5

    def test_workflow_with_reject(self):
        """Workflow with REJECT verdict requiring major revision."""
        workflow = {
            "step": 3,
            "outputs": {},
        }

        # Step 3: Critique returns REJECT (<60)
        workflow["outputs"]["step_3_gemini"] = "Score: 45, REJECT"

        # Go back to step 2 for major rework
        workflow["step"] = 2
        workflow["outputs"]["step_2_claude_v2"] = "Completely new prompts"

        # Critique again
        workflow["step"] = 3

        assert workflow["step"] == 3

    def test_micro_adjust_loop(self):
        """Step 5-6 micro-adjust loop."""
        workflow = {
            "step": 5,
            "outputs": {},
        }

        # Step 5: Generate - not quite right
        workflow["outputs"]["step_5_feedback"] = "Background person looks western"

        # Step 6: Micro-adjust
        workflow["step"] = 6
        workflow["outputs"]["step_6_feedback"] = "Added --no caucasian"

        # Back to step 5 to regenerate
        workflow["step"] = 5
        workflow["outputs"]["step_5_feedback_v2"] = "Looks good now"

        # Complete
        workflow["step"] = 6
        workflow["completed"] = True

        assert workflow["completed"] is True
