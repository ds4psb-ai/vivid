"""
Tests for Prompty Workflow Guide - find_next_step function.

Tests the core navigation logic that was fixed:
- Bug: current_step="" caused immediate "completed" response
- Fix: Empty current_step now returns first pending step
"""
import pytest
from typing import List

from app.routers.prompty.guide import (
    find_next_step,
    StepInfo,
    StageInfo,
)


# =============================================================================
# Test Fixtures
# =============================================================================

def create_stages_info(step_statuses: List[List[str]]) -> List[StageInfo]:
    """Create stages_info for testing.

    Args:
        step_statuses: List of lists, each inner list contains step statuses
                      for that stage. e.g. [["pending", "pending"], ["pending"]]
    """
    stages = []
    stage_names = ["analysis", "image", "video", "assembly"]

    for i, statuses in enumerate(step_statuses):
        steps = []
        for j, status in enumerate(statuses):
            steps.append(StepInfo(
                id=f"step_{i}_{j}",
                name=f"Step {i}.{j}",
                status=status,
            ))

        stage_id = stage_names[i] if i < len(stage_names) else f"stage_{i}"
        stages.append(StageInfo(
            id=stage_id,
            name=stage_id.title(),
            steps=steps,
        ))

    return stages


# =============================================================================
# Bug Fix Tests - Empty current_step
# =============================================================================

class TestFindNextStepEmptyCurrentStep:
    """Test find_next_step when current_step is empty (the bug fix)."""

    def test_empty_current_step_returns_first_pending(self):
        """Bug fix: Empty current_step should return first pending step, not completed."""
        stages = create_stages_info([["pending", "pending"], ["pending"]])

        next_stage, next_step, completed = find_next_step(stages, "", "")

        assert completed is False
        assert next_stage == "analysis"
        assert next_step == "step_0_0"

    def test_empty_current_step_skips_completed(self):
        """Empty current_step skips completed steps."""
        stages = create_stages_info([["completed", "pending"], ["pending"]])

        next_stage, next_step, completed = find_next_step(stages, "", "")

        assert completed is False
        assert next_stage == "analysis"
        assert next_step == "step_0_1"

    def test_empty_current_step_finds_step_in_later_stage(self):
        """Empty current_step finds pending step in later stages."""
        stages = create_stages_info([["completed", "completed"], ["pending"]])

        next_stage, next_step, completed = find_next_step(stages, "", "")

        assert completed is False
        assert next_stage == "image"
        assert next_step == "step_1_0"

    def test_empty_current_step_all_completed(self):
        """Empty current_step returns completed if all steps done."""
        stages = create_stages_info([["completed", "completed"], ["completed"]])

        next_stage, next_step, completed = find_next_step(stages, "", "")

        assert completed is True


# =============================================================================
# Normal Navigation Tests
# =============================================================================

class TestFindNextStepNormalNavigation:
    """Test find_next_step with normal current_step values."""

    def test_advance_within_same_stage(self):
        """Advance from one step to next in same stage."""
        stages = create_stages_info([["pending", "pending"], ["pending"]])

        next_stage, next_step, completed = find_next_step(
            stages, "analysis", "step_0_0"
        )

        assert completed is False
        assert next_stage == "analysis"
        assert next_step == "step_0_1"

    def test_advance_to_next_stage(self):
        """Advance from last step of stage to next stage."""
        stages = create_stages_info([["pending", "pending"], ["pending"]])

        next_stage, next_step, completed = find_next_step(
            stages, "analysis", "step_0_1"
        )

        assert completed is False
        assert next_stage == "image"
        assert next_step == "step_1_0"

    def test_skip_completed_steps(self):
        """Skip already completed steps when advancing."""
        stages = create_stages_info([["pending", "completed"], ["pending"]])

        next_stage, next_step, completed = find_next_step(
            stages, "analysis", "step_0_0"
        )

        assert completed is False
        # Should skip step_0_1 (completed) and go to step_1_0
        assert next_stage == "image"
        assert next_step == "step_1_0"

    def test_last_step_returns_completed(self):
        """Last step in workflow returns completed=True."""
        stages = create_stages_info([["pending"], ["pending"]])

        next_stage, next_step, completed = find_next_step(
            stages, "image", "step_1_0"
        )

        assert completed is True

    def test_all_remaining_completed(self):
        """Returns completed when all remaining steps are done."""
        stages = create_stages_info([["pending", "completed"], ["completed"]])

        next_stage, next_step, completed = find_next_step(
            stages, "analysis", "step_0_0"
        )

        assert completed is True


# =============================================================================
# Edge Cases
# =============================================================================

class TestFindNextStepEdgeCases:
    """Test edge cases for find_next_step."""

    def test_single_step_workflow(self):
        """Single step workflow."""
        stages = create_stages_info([["pending"]])

        # Start from empty
        next_stage, next_step, completed = find_next_step(stages, "", "")
        assert completed is False
        assert next_step == "step_0_0"

        # After completing single step
        next_stage, next_step, completed = find_next_step(
            stages, "analysis", "step_0_0"
        )
        assert completed is True

    def test_empty_stages(self):
        """Empty stages list."""
        stages = []

        next_stage, next_step, completed = find_next_step(stages, "", "")

        assert completed is True

    def test_nonexistent_current_step(self):
        """Current step doesn't exist in stages."""
        stages = create_stages_info([["pending", "pending"]])

        # Non-existent step - should return completed since it never finds current
        next_stage, next_step, completed = find_next_step(
            stages, "analysis", "nonexistent_step"
        )

        # This returns completed=True because found_current never becomes True
        assert completed is True

    def test_in_progress_step_treated_as_not_completed(self):
        """in_progress status should be treated as a valid next step."""
        stages = create_stages_info([["pending", "in_progress"], ["pending"]])

        next_stage, next_step, completed = find_next_step(
            stages, "analysis", "step_0_0"
        )

        # in_progress is not "completed", so it should be returned
        assert completed is False
        assert next_step == "step_0_1"


# =============================================================================
# Real Workflow Scenarios
# =============================================================================

class TestRealWorkflowScenarios:
    """Test realistic workflow scenarios."""

    def test_kyle_nut_workflow_start(self):
        """Kyle Nut workflow - starting from beginning."""
        # Simulating: analysis(1 step), image(2 steps), video(1 step), assembly(1 step)
        stages = create_stages_info([
            ["pending"],  # analysis: analyze_reference
            ["pending", "pending"],  # image: anchor_girl, anchor_boy
            ["pending"],  # video: scene_assembly
            ["pending"],  # assembly: final_edit
        ])

        # First Next Step should go to analyze_reference
        next_stage, next_step, completed = find_next_step(stages, "", "")

        assert completed is False
        assert next_stage == "analysis"
        assert next_step == "step_0_0"

    def test_kyle_nut_workflow_midway(self):
        """Kyle Nut workflow - partway through."""
        stages = create_stages_info([
            ["completed"],  # analysis done
            ["completed", "pending"],  # anchor_girl done, anchor_boy pending
            ["pending"],
            ["pending"],
        ])

        # From anchor_girl, should go to anchor_boy
        next_stage, next_step, completed = find_next_step(
            stages, "image", "step_1_0"
        )

        assert completed is False
        assert next_stage == "image"
        assert next_step == "step_1_1"

    def test_kyle_nut_workflow_final_step(self):
        """Kyle Nut workflow - on final step."""
        stages = create_stages_info([
            ["completed"],
            ["completed", "completed"],
            ["completed"],
            ["pending"],  # final_edit
        ])

        # On final step
        next_stage, next_step, completed = find_next_step(
            stages, "assembly", "step_3_0"
        )

        assert completed is True
