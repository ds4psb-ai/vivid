"""Engine Constraint Schema Validation tests.

Tests that each engine adapter's compiled output stays within
engine-specific word and duration limits.
"""
from __future__ import annotations

import pytest

from app.features.original_ip_foundry.adapters.base_engine_adapter import (
    EnginePromptResult,
    FoundryShotPlan,
)
from app.features.original_ip_foundry.adapters.engine_constraint_schemas import (
    ENGINE_CONSTRAINTS,
    validate_engine_output,
)
from app.features.original_ip_foundry.adapters.kling_engine_adapter import KlingEngineAdapter
from app.features.original_ip_foundry.adapters.seedance_engine_adapter import SeedanceEngineAdapter
from app.features.original_ip_foundry.adapters.sora_engine_adapter import SoraEngineAdapter
from app.features.original_ip_foundry.adapters.veo_engine_adapter import VeoEngineAdapter

ADAPTERS = [
    VeoEngineAdapter(),
    SeedanceEngineAdapter(),
    KlingEngineAdapter(),
    SoraEngineAdapter(),
]

TYPICAL_PLANS = [
    FoundryShotPlan(
        shot_id="test_001",
        shot_size="wide",
        camera_angle="low_angle",
        camera_movement="dolly",
        emotion_tone="tension",
        transition_to_next="match_cut",
        location="hotel_corridor",
        characters=["jack"],
        duration_sec=8.0,
    ),
    FoundryShotPlan(
        shot_id="test_002",
        shot_size="close_up",
        camera_angle="eye_level",
        camera_movement="static",
        emotion_tone="melancholy",
        transition_to_next="dissolve",
        location="cafe",
        characters=["su_li_zhen", "chow_mo_wan"],
        duration_sec=5.0,
    ),
    FoundryShotPlan(
        shot_id="test_003",
        shot_size="extreme_wide",
        camera_angle="birds_eye",
        camera_movement="crane",
        emotion_tone="awe",
        transition_to_next="cut",
        location="space",
        characters=[],
        duration_sec=12.0,
    ),
    FoundryShotPlan(
        shot_id="test_004",
        shot_size="medium",
        camera_angle="dutch_angle",
        camera_movement="whip_pan",
        emotion_tone="rage",
        transition_to_next="jump_cut",
        location="warehouse",
        characters=["mr_white", "mr_pink", "mr_orange"],
        duration_sec=4.0,
    ),
    FoundryShotPlan(
        shot_id="test_005",
        shot_size="medium_close_up",
        camera_angle="eye_level",
        camera_movement="handheld",
        emotion_tone="intimacy",
        transition_to_next="fade",
        location="apartment_corridor",
        characters=["yiu_fai", "po_wing"],
        duration_sec=6.0,
    ),
]


# ── Constraint values ─────────────────────────────────────────────────


class TestEngineConstraintValues:
    """Verify constraint values for each engine."""

    def test_veo_constraints(self):
        c = ENGINE_CONSTRAINTS["veo"]
        assert c["max_prompt_words"] == 100
        assert c["min_prompt_words"] == 15
        assert c["max_duration_sec"] == 60

    def test_seedance_constraints(self):
        c = ENGINE_CONSTRAINTS["seedance"]
        assert c["max_prompt_words"] == 60
        assert c["min_prompt_words"] == 5
        assert c["max_duration_sec"] == 30

    def test_kling_constraints(self):
        c = ENGINE_CONSTRAINTS["kling"]
        assert c["max_prompt_words"] == 80
        assert c["min_prompt_words"] == 5
        assert c["max_duration_sec"] == 120

    def test_sora_constraints(self):
        c = ENGINE_CONSTRAINTS["sora"]
        assert c["max_prompt_words"] == 120
        assert c["min_prompt_words"] == 10
        assert c["max_duration_sec"] == 60


# ── Validation function ───────────────────────────────────────────────


class TestValidateEngineOutput:
    """Test the validate_engine_output function directly."""

    def test_valid_prompt_no_violations(self):
        result = validate_engine_output("veo", "A wide shot from a low angle perspective with dolly camera movement evoking a tension atmosphere featuring jack set in hotel corridor paced at a measured rhythm rendered in cinematic quality with natural lighting.", 8.0)
        assert result == []

    def test_exceeds_word_limit(self):
        long_prompt = " ".join(["word"] * 150)
        result = validate_engine_output("veo", long_prompt)
        assert len(result) == 1
        assert "exceeds" in result[0].lower()
        assert "100" in result[0]

    def test_below_word_minimum(self):
        short_prompt = "very short"
        result = validate_engine_output("veo", short_prompt)
        assert len(result) == 1
        assert "below" in result[0].lower()

    def test_exceeds_duration(self):
        result = validate_engine_output("seedance", "A cinematic shot with dolly camera motion and tension atmosphere set in corridor", 45.0)
        assert len(result) == 1
        assert "duration" in result[0].lower()

    def test_unknown_engine(self):
        result = validate_engine_output("nonexistent_engine", "some prompt")
        assert len(result) == 1
        assert "unknown engine" in result[0].lower()

    def test_multiple_violations(self):
        long_prompt = " ".join(["word"] * 70)
        result = validate_engine_output("seedance", long_prompt, 45.0)
        assert len(result) == 2

    def test_zero_duration_skips_check(self):
        result = validate_engine_output("veo", "A wide shot from a low angle perspective with camera movement evoking a tension atmosphere featuring characters set in a location with measured rhythm and natural lighting", 0)
        assert all("duration" not in v.lower() for v in result)


# ── Adapter compilation within limits ──────────────────────────────────


class TestAdaptersCompileWithinLimits:
    """Each adapter's compiled output should stay within its engine's limits."""

    @pytest.mark.parametrize("adapter", ADAPTERS, ids=lambda a: a.ENGINE_NAME)
    @pytest.mark.parametrize("plan", TYPICAL_PLANS, ids=lambda p: p.shot_id)
    def test_typical_shot_within_limits(self, adapter, plan):
        result = adapter.compile(plan)
        violations = adapter.validate_output(result, plan.duration_sec)
        assert not violations, (
            f"{adapter.ENGINE_NAME} / {plan.shot_id} violations: {violations}"
        )

    @pytest.mark.parametrize("adapter", ADAPTERS, ids=lambda a: a.ENGINE_NAME)
    def test_minimal_shot_within_limits(self, adapter):
        """Minimal shot should still produce valid output."""
        plan = FoundryShotPlan(shot_id="minimal_001")
        result = adapter.compile(plan)
        violations = adapter.validate_output(result, plan.duration_sec)
        assert not violations, (
            f"{adapter.ENGINE_NAME} minimal shot violations: {violations}"
        )

    @pytest.mark.parametrize("adapter", ADAPTERS, ids=lambda a: a.ENGINE_NAME)
    def test_engine_name_matches(self, adapter):
        plan = FoundryShotPlan(shot_id="name_check")
        result = adapter.compile(plan)
        assert result.engine == adapter.ENGINE_NAME


# ── Validation catches over-limit prompts ─────────────────────────────


class TestValidationCatchesOverLimit:
    """Manually crafted over-limit prompts should be caught."""

    @pytest.mark.parametrize(
        "engine,max_words",
        [("veo", 100), ("seedance", 60), ("kling", 80), ("sora", 120)],
    )
    def test_over_word_limit_detected(self, engine, max_words):
        over_prompt = " ".join(["cinematic"] * (max_words + 10))
        violations = validate_engine_output(engine, over_prompt)
        assert any("exceeds" in v.lower() for v in violations)

    @pytest.mark.parametrize(
        "engine,max_dur",
        [("veo", 60), ("seedance", 30), ("kling", 120), ("sora", 60)],
    )
    def test_over_duration_detected(self, engine, max_dur):
        violations = validate_engine_output(engine, "A cinematic shot with motion and atmosphere", max_dur + 10)
        assert any("duration" in v.lower() for v in violations)
