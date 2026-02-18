from __future__ import annotations

from app.features.original_ip_foundry.adapters.base_engine_adapter import (
    BaseEngineAdapter,
    EnginePromptResult,
    FoundryShotPlan,
)


class KlingEngineAdapter(BaseEngineAdapter):
    """Kling 3.0 subject-first prompt structure."""

    ENGINE_NAME = "kling"

    def compile(self, plan: FoundryShotPlan) -> EnginePromptResult:
        parts: list[str] = []

        # Subject / Character
        if plan.characters:
            parts.append(", ".join(plan.characters))
        else:
            parts.append("A figure")

        # Action / Motion
        if plan.camera_movement != "static":
            parts.append(f"{plan.camera_movement} motion")

        # Camera: angle + movement
        parts.append(f"Camera: {plan.camera_angle}")
        if plan.camera_movement != "static":
            parts.append(plan.camera_movement)

        # Shot size
        parts.append(f"{plan.shot_size} shot")

        # Mood / Tone
        parts.append(f"{plan.emotion_tone} mood")

        # Setting / Location
        if plan.location:
            parts.append(f"in {plan.location}")

        # Duration hint
        duration_hint = self._duration_hint(plan.duration_sec)
        parts.append(duration_hint)

        prompt_text = ", ".join(parts)

        return EnginePromptResult(
            engine=self.ENGINE_NAME,
            prompt_text=prompt_text,
            negative_prompt="blurry, distorted, low quality, watermark",
            metadata={
                "engine_version": "kling_3.0",
                "duration_sec": plan.duration_sec,
                "shot_size": plan.shot_size,
            },
        )

    @staticmethod
    def _duration_hint(duration_sec: float) -> str:
        if duration_sec <= 3.0:
            return "short clip"
        if duration_sec <= 8.0:
            return "medium clip"
        return "long clip"
