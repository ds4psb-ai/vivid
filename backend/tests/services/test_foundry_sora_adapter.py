"""Tests for SoraEngineAdapter."""
from app.features.original_ip_foundry.adapters import SoraEngineAdapter, FoundryShotPlan


def _plan(**overrides):
    defaults = {
        "shot_id": "sh1", "shot_size": "close_up", "camera_angle": "low_angle",
        "camera_movement": "dolly", "emotion_tone": "anxiety",
        "location": "dark alley", "characters": ["protagonist"], "duration_sec": 6.0,
    }
    defaults.update(overrides)
    return FoundryShotPlan(**defaults)


def test_engine_name():
    assert SoraEngineAdapter.ENGINE_NAME == "sora"


def test_compile_returns_sora_result():
    adapter = SoraEngineAdapter()
    result = adapter.compile(_plan())
    assert result.engine == "sora"
    assert result.metadata["engine_version"] == "sora_2.0"


def test_prompt_ends_with_period():
    adapter = SoraEngineAdapter()
    result = adapter.compile(_plan())
    assert result.prompt_text.endswith(".")


def test_includes_shot_size():
    adapter = SoraEngineAdapter()
    result = adapter.compile(_plan(shot_size="wide"))
    assert "wide" in result.prompt_text


def test_includes_camera_movement():
    adapter = SoraEngineAdapter()
    result = adapter.compile(_plan(camera_movement="tracking"))
    assert "tracking" in result.prompt_text


def test_duration_short():
    assert "3 seconds" in SoraEngineAdapter._duration_directive(2.0)


def test_duration_long():
    result = SoraEngineAdapter._duration_directive(15.0)
    assert "extended" in result and "15" in result
