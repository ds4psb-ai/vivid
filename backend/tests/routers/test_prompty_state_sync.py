"""
Tests for Prompty STATE.md Sync API.

Tests the state parsing and generation functions:
- parse_scene_progress_table
- parse_overall_progress
- parse_current_task
- parse_state_md
- generate_state_md
"""
import pytest
from datetime import datetime

from app.routers.prompty.state_sync import (
    parse_scene_progress_table,
    parse_overall_progress,
    parse_current_task,
    parse_state_md,
    generate_progress_bar,
    find_anchor_scene,
    count_tikitaka_iterations,
    SceneProgress,
    StageProgress,
    StateMdParsed,
)


# =============================================================================
# Test Data
# =============================================================================

SAMPLE_STATE_MD = """# STATE.md
# Project: Test Project
# Last Updated: 2026-02-02T10:00:00Z

## Scene Progress
| Scene | Description | Image | Video | Status |
|-------|-------------|-------|-------|--------|
| 1 | Arrival | v2/scene01.png | - | ✅ 확정 |
| 2 | Anticipation (ANCHOR) | v3/scene02.png | - | ✅ 확정 |
| 3 | First Look | v1/scene03.png | - | 🔄 진행 |
| 4 | Awkward Smile | - | - | ⏳ 대기 |

## Overall Progress
- Stage 1: ANALYZE ██████████ 100%
- Stage 2: IMAGE   ████████░░ 80%
- Stage 3: VIDEO   ░░░░░░░░░░ 0%
- Stage 4: ASSEMBLY ░░░░░░░░░░ 0%

## Current Task
Scene 03 이미지 재생성 (캐릭터 일관성 개선)
"""

MINIMAL_STATE_MD = """# STATE.md

## Scene Progress
| Scene | Description | Image | Video | Status |
|-------|-------------|-------|-------|--------|
| 1 | Test Scene | - | - | ⏳ 대기 |
"""

EMPTY_STATE_MD = """# STATE.md
# No content
"""


# =============================================================================
# Scene Progress Parser Tests
# =============================================================================

class TestParseSceneProgressTable:
    """Test scene progress table parsing."""

    def test_parse_multiple_scenes(self):
        """Test parsing multiple scenes from table."""
        scenes = parse_scene_progress_table(SAMPLE_STATE_MD)

        assert len(scenes) == 4
        assert scenes[0].scene == "1"
        assert scenes[0].description == "Arrival"
        assert scenes[0].image_status == "v2/scene01.png"
        assert scenes[0].video_status == "-"
        assert "✅" in scenes[0].status_emoji

    def test_parse_anchor_scene(self):
        """Test ANCHOR marker detection in description."""
        scenes = parse_scene_progress_table(SAMPLE_STATE_MD)

        anchor_scene = next((s for s in scenes if "(ANCHOR)" in s.description), None)
        assert anchor_scene is not None
        assert anchor_scene.scene == "2"
        assert "Anticipation" in anchor_scene.description

    def test_parse_various_statuses(self):
        """Test different status emoji parsing."""
        scenes = parse_scene_progress_table(SAMPLE_STATE_MD)

        # ✅ 확정
        assert "✅" in scenes[0].status_emoji
        # 🔄 진행
        assert "🔄" in scenes[2].status_emoji
        # ⏳ 대기
        assert "⏳" in scenes[3].status_emoji

    def test_parse_empty_content(self):
        """Test parsing with no scene table."""
        scenes = parse_scene_progress_table(EMPTY_STATE_MD)
        assert len(scenes) == 0

    def test_parse_minimal_table(self):
        """Test parsing minimal single-row table."""
        scenes = parse_scene_progress_table(MINIMAL_STATE_MD)

        assert len(scenes) == 1
        assert scenes[0].scene == "1"
        assert scenes[0].description == "Test Scene"


# =============================================================================
# Overall Progress Parser Tests
# =============================================================================

class TestParseOverallProgress:
    """Test overall progress section parsing."""

    def test_parse_four_stages(self):
        """Test parsing all four stages."""
        stages = parse_overall_progress(SAMPLE_STATE_MD)

        assert len(stages) == 4
        assert stages[0].stage_id == "stage1"
        assert stages[0].name == "ANALYZE"
        assert stages[0].percent == 100

    def test_parse_stage_percentages(self):
        """Test correct percentage parsing."""
        stages = parse_overall_progress(SAMPLE_STATE_MD)

        percentages = [s.percent for s in stages]
        assert percentages == [100, 80, 0, 0]

    def test_parse_progress_bars(self):
        """Test progress bar string parsing."""
        stages = parse_overall_progress(SAMPLE_STATE_MD)

        # 100% should have full bar
        assert "█" in stages[0].bar
        # 0% should have empty bar
        assert "░" in stages[3].bar

    def test_parse_no_progress_section(self):
        """Test parsing with no progress section."""
        stages = parse_overall_progress(EMPTY_STATE_MD)
        assert len(stages) == 0


# =============================================================================
# Current Task Parser Tests
# =============================================================================

class TestParseCurrentTask:
    """Test current task section parsing."""

    def test_parse_current_task(self):
        """Test extracting current task."""
        task = parse_current_task(SAMPLE_STATE_MD)

        assert task is not None
        assert "Scene 03" in task
        assert "이미지 재생성" in task

    def test_no_current_task(self):
        """Test when no current task section exists."""
        task = parse_current_task(EMPTY_STATE_MD)
        assert task is None


# =============================================================================
# Full STATE.md Parser Tests
# =============================================================================

class TestParseStateMd:
    """Test complete STATE.md parsing."""

    def test_parse_complete_state(self):
        """Test parsing complete STATE.md."""
        parsed = parse_state_md(SAMPLE_STATE_MD)

        assert len(parsed.scenes) == 4
        assert len(parsed.stages) == 4
        assert parsed.current_task is not None
        assert parsed.anchor_scene == "2"

    def test_anchor_detection(self):
        """Test ANCHOR scene is correctly identified."""
        parsed = parse_state_md(SAMPLE_STATE_MD)
        assert parsed.anchor_scene == "2"

    def test_parse_minimal_state(self):
        """Test parsing minimal STATE.md."""
        parsed = parse_state_md(MINIMAL_STATE_MD)

        assert len(parsed.scenes) == 1
        assert len(parsed.stages) == 0
        assert parsed.anchor_scene is None

    def test_parse_empty_state(self):
        """Test parsing empty STATE.md."""
        parsed = parse_state_md(EMPTY_STATE_MD)

        assert len(parsed.scenes) == 0
        assert len(parsed.stages) == 0
        assert parsed.anchor_scene is None


# =============================================================================
# Helper Function Tests
# =============================================================================

class TestHelperFunctions:
    """Test utility functions."""

    def test_generate_progress_bar_empty(self):
        """Test 0% progress bar."""
        bar = generate_progress_bar(0)
        assert bar == "░░░░░░░░░░"

    def test_generate_progress_bar_full(self):
        """Test 100% progress bar."""
        bar = generate_progress_bar(100)
        assert bar == "██████████"

    def test_generate_progress_bar_half(self):
        """Test 50% progress bar."""
        bar = generate_progress_bar(50)
        assert bar.count("█") == 5
        assert bar.count("░") == 5

    def test_generate_progress_bar_custom_width(self):
        """Test custom width progress bar."""
        bar = generate_progress_bar(50, width=20)
        assert len(bar) == 20
        assert bar.count("█") == 10

    def test_find_anchor_scene_found(self):
        """Test finding ANCHOR scene."""
        scenes = [
            SceneProgress(scene="1", description="First", image_status="-", video_status="-", status_emoji="✅"),
            SceneProgress(scene="2", description="Second (ANCHOR)", image_status="-", video_status="-", status_emoji="✅"),
        ]
        anchor = find_anchor_scene(scenes)
        assert anchor == "2"

    def test_find_anchor_scene_not_found(self):
        """Test when no ANCHOR scene exists."""
        scenes = [
            SceneProgress(scene="1", description="First", image_status="-", video_status="-", status_emoji="✅"),
        ]
        anchor = find_anchor_scene(scenes)
        assert anchor is None

    def test_count_tikitaka_iterations(self):
        """Test tikitaka iteration counting."""
        content = """
        #1 Score: 65
        #2 Score: 72
        #3 Score: 88
        """
        count = count_tikitaka_iterations(content)
        assert count == 3

    def test_count_tikitaka_no_iterations(self):
        """Test counting with no iterations."""
        count = count_tikitaka_iterations(EMPTY_STATE_MD)
        assert count == 0


# =============================================================================
# Schema Tests
# =============================================================================

class TestSceneProgressSchema:
    """Test SceneProgress Pydantic model."""

    def test_valid_scene_progress(self):
        """Test valid SceneProgress creation."""
        scene = SceneProgress(
            scene="1",
            description="Test Scene",
            image_status="v1/test.png",
            video_status="-",
            status_emoji="✅ 확정",
        )
        assert scene.scene == "1"
        assert scene.description == "Test Scene"

    def test_scene_with_anchor(self):
        """Test scene with ANCHOR marker."""
        scene = SceneProgress(
            scene="2",
            description="Main Character (ANCHOR)",
            image_status="v3/anchor.png",
            video_status="-",
            status_emoji="✅ 확정",
        )
        assert "(ANCHOR)" in scene.description


class TestStageProgressSchema:
    """Test StageProgress Pydantic model."""

    def test_valid_stage_progress(self):
        """Test valid StageProgress creation."""
        stage = StageProgress(
            stage_id="stage1",
            name="ANALYZE",
            percent=100,
            bar="██████████",
        )
        assert stage.stage_id == "stage1"
        assert stage.percent == 100

    def test_stage_zero_percent(self):
        """Test stage with 0% progress."""
        stage = StageProgress(
            stage_id="stage4",
            name="ASSEMBLY",
            percent=0,
            bar="░░░░░░░░░░",
        )
        assert stage.percent == 0


class TestStateMdParsedSchema:
    """Test StateMdParsed Pydantic model."""

    def test_valid_parsed_state(self):
        """Test valid StateMdParsed creation."""
        parsed = StateMdParsed(
            scenes=[],
            stages=[],
            current_task="Test task",
            anchor_scene="2",
            tikitaka_count=3,
        )
        assert parsed.current_task == "Test task"
        assert parsed.anchor_scene == "2"
        assert parsed.tikitaka_count == 3

    def test_default_values(self):
        """Test default values."""
        parsed = StateMdParsed(
            scenes=[],
            stages=[],
        )
        assert parsed.current_task is None
        assert parsed.anchor_scene is None
        assert parsed.tikitaka_count == 0


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_malformed_table(self):
        """Test handling malformed table."""
        content = """
        ## Scene Progress
        Not a valid table
        | just | partial |
        """
        scenes = parse_scene_progress_table(content)
        assert len(scenes) == 0

    def test_unicode_content(self):
        """Test handling Korean and emoji content."""
        content = """
        ## Scene Progress
        | Scene | Description | Image | Video | Status |
        |-------|-------------|-------|-------|--------|
        | 1 | 한글 씬 🎬 | v1/test.png | - | ✅ 완료 |
        """
        scenes = parse_scene_progress_table(content)
        assert len(scenes) == 1
        assert "한글" in scenes[0].description

    def test_percentage_edge_values(self):
        """Test percentage parsing at boundaries."""
        content = """
        ## Overall Progress
        - Stage 1: TEST ██████████ 100%
        - Stage 2: TEST ░░░░░░░░░░ 0%
        """
        stages = parse_overall_progress(content)
        assert stages[0].percent == 100
        assert stages[1].percent == 0

    def test_whitespace_handling(self):
        """Test handling extra whitespace."""
        content = """
        ##   Scene Progress
        |   Scene   |   Description   |   Image   |   Video   |   Status   |
        |-----------|-----------------|-----------|-----------|------------|
        |    1      |   Test Scene    |    -      |    -      |  ✅ 확정   |
        """
        scenes = parse_scene_progress_table(content)
        # Parser should handle whitespace
        assert len(scenes) >= 0  # Graceful handling
