from __future__ import annotations

from app.features.original_ip_foundry.adapters.base_engine_adapter import (
    BaseEngineAdapter,
    EnginePromptResult,
    FoundryShotPlan,
)


class SeedanceEngineAdapter(BaseEngineAdapter):
    """Seedance 2.0 cinematic prompt structure (40-60 words target)."""

    ENGINE_NAME = "seedance"

    def compile(self, plan: FoundryShotPlan) -> EnginePromptResult:
        parts = ["Cinematic"]
        parts.append(f"{plan.camera_angle.replace('_', ' ')} shot")
        if plan.camera_movement != "static":
            parts.append(f"with {plan.camera_movement.replace('_', ' ')}")
        if plan.characters:
            parts.append(f"of {' and '.join(plan.characters)}")
        parts.append(f"{plan.emotion_tone.replace('_', ' ')} atmosphere")
        if plan.location:
            parts.append(f"set in {plan.location}")
        parts.append(self._pacing(plan.duration_sec))
        prompt_text = ". ".join(parts)
        return EnginePromptResult(
            engine=self.ENGINE_NAME,
            prompt_text=prompt_text,
            negative_prompt="static, flat, artificial lighting",
            metadata={
                "engine_version": "seedance_2.0",
                "word_count": len(prompt_text.split()),
                "duration_sec": plan.duration_sec,
            },
        )

    @staticmethod
    def _pacing(duration_sec: float) -> str:
        if duration_sec <= 3.0:
            return "Quick, impactful moment"
        if duration_sec <= 8.0:
            return "Steady cinematic rhythm"
        return "Extended contemplative take"
