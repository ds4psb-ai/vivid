"""Tests for FoundryPromptCompiler and engine adapters."""
from app.features.original_ip_foundry.prompt_compiler import FoundryPromptCompiler
from app.features.original_ip_foundry.adapters import (
    BaseEngineAdapter,
    EnginePromptResult,
    FoundryShotPlan,
    KlingEngineAdapter,
    VeoEngineAdapter,
)


def _sample_shot():
    return {
        "shot_id": "sh1",
        "shot_size": "close_up",
        "camera_angle": "low_angle",
        "camera_movement": "dolly",
        "emotion_tone": "anxiety",
        "transition_to_next": "match_cut",
        "location": "dark alley",
        "characters": ["protagonist"],
        "duration_sec": 6.0,
    }


def test_compile_shot_returns_default_engines():
    compiler = FoundryPromptCompiler()
    result = compiler.compile_shot(_sample_shot())

    assert "kling" in result
    assert "veo" in result
    assert isinstance(result["kling"], EnginePromptResult)
    assert isinstance(result["veo"], EnginePromptResult)


def test_kling_prompt_structure():
    adapter = KlingEngineAdapter()
    plan = FoundryShotPlan(
        shot_id="sh1", shot_size="close_up", camera_angle="low_angle",
        camera_movement="dolly", emotion_tone="anxiety",
        location="dark alley", characters=["protagonist"], duration_sec=6.0,
    )
    result = adapter.compile(plan)

    assert result.engine == "kling"
    assert "protagonist" in result.prompt_text
    assert "low_angle" in result.prompt_text
    assert "close_up" in result.prompt_text
    assert "anxiety" in result.prompt_text
    assert "medium clip" in result.prompt_text
    assert "dark alley" in result.prompt_text
    assert result.negative_prompt  # non-empty


def test_veo_prompt_seven_layers():
    adapter = VeoEngineAdapter()
    plan = FoundryShotPlan(
        shot_id="sh1", shot_size="close_up", camera_angle="low_angle",
        camera_movement="dolly", emotion_tone="anxiety",
        transition_to_next="match_cut",
        location="dark alley", characters=["protagonist"], duration_sec=6.0,
    )
    result = adapter.compile(plan)

    assert result.engine == "veo"
    assert result.metadata["layer_count"] == 7
    assert result.metadata["word_count"] > 0
    assert "close_up" in result.prompt_text
    assert "low_angle" in result.prompt_text
    assert "anxiety" in result.prompt_text
    assert "protagonist" in result.prompt_text
    assert "dark alley" in result.prompt_text


def test_compile_scene_returns_list():
    compiler = FoundryPromptCompiler()
    shots = [_sample_shot(), {**_sample_shot(), "shot_id": "sh2", "shot_size": "wide"}]

    results = compiler.compile_scene(shots)

    assert len(results) == 2
    assert "kling" in results[0]
    assert "veo" in results[1]


def test_unsupported_engine_skipped():
    compiler = FoundryPromptCompiler()
    result = compiler.compile_shot(_sample_shot(), engines=["kling", "nonexistent"])

    assert "kling" in result
    assert "nonexistent" not in result


def test_register_custom_adapter():
    class MockAdapter(BaseEngineAdapter):
        ENGINE_NAME = "mock"
        def compile(self, plan):
            return EnginePromptResult(engine="mock", prompt_text="mock prompt")

    compiler = FoundryPromptCompiler()
    compiler.register_adapter("mock", MockAdapter())
    result = compiler.compile_shot(_sample_shot(), engines=["mock"])

    assert "mock" in result
    assert result["mock"].prompt_text == "mock prompt"


def test_kling_duration_hints():
    adapter = KlingEngineAdapter()
    assert adapter._duration_hint(2.0) == "short clip"
    assert adapter._duration_hint(5.0) == "medium clip"
    assert adapter._duration_hint(12.0) == "long clip"


def test_veo_pacing_descriptions():
    adapter = VeoEngineAdapter()
    assert "brief" in adapter._pacing_description(2.0)
    assert "measured" in adapter._pacing_description(5.0)
    assert "extended" in adapter._pacing_description(12.0)
