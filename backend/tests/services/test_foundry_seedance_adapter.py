"""Tests for SeedanceEngineAdapter."""
from app.features.original_ip_foundry.adapters import SeedanceEngineAdapter, FoundryShotPlan


def _plan(**overrides):
    defaults = {
        "shot_id": "sh1", "shot_size": "close_up", "camera_angle": "low_angle",
        "camera_movement": "dolly", "emotion_tone": "anxiety",
        "location": "dark alley", "characters": ["protagonist"], "duration_sec": 6.0,
    }
    defaults.update(overrides)
    return FoundryShotPlan(**defaults)


def test_engine_name():
    assert SeedanceEngineAdapter.ENGINE_NAME == "seedance"


def test_compile_returns_seedance_result():
    adapter = SeedanceEngineAdapter()
    result = adapter.compile(_plan())
    assert result.engine == "seedance"
    assert result.metadata["engine_version"] == "seedance_2.0"


def test_cinematic_prefix():
    adapter = SeedanceEngineAdapter()
    result = adapter.compile(_plan())
    assert result.prompt_text.startswith("Cinematic")


def test_includes_camera_angle():
    adapter = SeedanceEngineAdapter()
    result = adapter.compile(_plan(camera_angle="high_angle"))
    assert "high angle" in result.prompt_text


def test_includes_characters():
    adapter = SeedanceEngineAdapter()
    result = adapter.compile(_plan(characters=["hero", "villain"]))
    assert "hero and villain" in result.prompt_text


def test_pacing_short():
    assert "impactful" in SeedanceEngineAdapter._pacing(2.0).lower()


def test_pacing_long():
    assert "contemplative" in SeedanceEngineAdapter._pacing(12.0).lower()
