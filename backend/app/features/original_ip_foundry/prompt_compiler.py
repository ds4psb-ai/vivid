from __future__ import annotations

from app.features.original_ip_foundry.adapters import (
    BaseEngineAdapter,
    EnginePromptResult,
    FoundryShotPlan,
    KlingEngineAdapter,
    VeoEngineAdapter,
    SeedanceEngineAdapter,
    SoraEngineAdapter,
)


class FoundryPromptCompiler:
    DEFAULT_ENGINES = ["kling", "veo", "seedance", "sora"]

    def __init__(self) -> None:
        self._adapters: dict[str, BaseEngineAdapter] = {
            "kling": KlingEngineAdapter(),
            "veo": VeoEngineAdapter(),
            "seedance": SeedanceEngineAdapter(),
            "sora": SoraEngineAdapter(),
        }

    def register_adapter(self, name: str, adapter: BaseEngineAdapter) -> None:
        self._adapters[name] = adapter

    def compile_shot(
        self, shot_input, engines: list[str] | None = None
    ) -> dict[str, EnginePromptResult]:
        plan = self._to_shot_plan(shot_input)
        target = engines or self.DEFAULT_ENGINES
        results: dict[str, EnginePromptResult] = {}
        for e in target:
            if e not in self._adapters:
                continue
            results[e] = self._adapters[e].compile(plan)
        return results

    def compile_scene(
        self, shots: list, engines: list[str] | None = None
    ) -> list[dict[str, EnginePromptResult]]:
        return [self.compile_shot(s, engines) for s in shots]

    def _to_shot_plan(self, shot_input) -> FoundryShotPlan:
        if hasattr(shot_input, "model_dump"):
            data = shot_input.model_dump()
        elif isinstance(shot_input, dict):
            data = shot_input
        else:
            data = {}
        return FoundryShotPlan(
            shot_id=data.get("shot_id", "unknown"),
            shot_size=data.get("shot_size", "medium"),
            camera_angle=data.get("camera_angle", "eye_level"),
            camera_movement=data.get("camera_movement", "static"),
            emotion_tone=data.get("emotion_tone", "neutral"),
            transition_to_next=data.get("transition_to_next", "cut"),
            location=data.get("location"),
            characters=data.get("characters", []),
            duration_sec=data.get("duration_sec", 6.0),
        )
