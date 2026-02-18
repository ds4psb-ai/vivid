"""Contract tests for the Worker Port (BaseEngineAdapter compile interface)."""
from __future__ import annotations

import pytest

from app.features.original_ip_foundry.adapters.base_engine_adapter import (
    BaseEngineAdapter,
    EnginePromptResult,
    FoundryShotPlan,
)
from app.features.original_ip_foundry.adapters import (
    KlingEngineAdapter,
    VeoEngineAdapter,
    SeedanceEngineAdapter,
    SoraEngineAdapter,
)


class WorkerPortContractMixin:
    """Mixin that defines the worker (engine adapter) port contract.

    Each concrete test class must implement ``get_implementation``.
    """

    def get_implementation(self) -> BaseEngineAdapter:
        raise NotImplementedError

    def _default_plan(self, **overrides) -> FoundryShotPlan:
        defaults = dict(
            shot_id="shot_01",
            shot_size="medium",
            camera_angle="eye_level",
            camera_movement="static",
            emotion_tone="neutral",
            transition_to_next="cut",
            location="rooftop",
            characters=["@hero"],
            duration_sec=6.0,
        )
        defaults.update(overrides)
        return FoundryShotPlan(**defaults)

    # -- contract tests -------------------------------------------------------

    def test_compile_returns_engine_prompt_result(self):
        adapter = self.get_implementation()
        result = adapter.compile(self._default_plan())
        assert isinstance(result, EnginePromptResult)

    def test_compile_has_correct_engine_name(self):
        adapter = self.get_implementation()
        result = adapter.compile(self._default_plan())
        assert result.engine == adapter.ENGINE_NAME
        assert result.engine != ""

    def test_compile_produces_nonempty_prompt(self):
        adapter = self.get_implementation()
        result = adapter.compile(self._default_plan())
        assert len(result.prompt_text.strip()) > 0

    def test_compile_with_minimal_plan(self):
        adapter = self.get_implementation()
        minimal = FoundryShotPlan(shot_id="min_01")
        result = adapter.compile(minimal)
        assert isinstance(result, EnginePromptResult)
        assert len(result.prompt_text) > 0

    def test_compile_metadata_is_dict(self):
        adapter = self.get_implementation()
        result = adapter.compile(self._default_plan())
        assert isinstance(result.metadata, dict)


class TestKlingWorkerPort(WorkerPortContractMixin):
    def get_implementation(self) -> BaseEngineAdapter:
        return KlingEngineAdapter()


class TestVeoWorkerPort(WorkerPortContractMixin):
    def get_implementation(self) -> BaseEngineAdapter:
        return VeoEngineAdapter()


class TestSeedanceWorkerPort(WorkerPortContractMixin):
    def get_implementation(self) -> BaseEngineAdapter:
        return SeedanceEngineAdapter()


class TestSoraWorkerPort(WorkerPortContractMixin):
    def get_implementation(self) -> BaseEngineAdapter:
        return SoraEngineAdapter()
