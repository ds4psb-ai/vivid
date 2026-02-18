from __future__ import annotations

from app.features.original_ip_foundry.adapters.base_engine_adapter import (
    BaseEngineAdapter,
    EnginePromptResult,
    FoundryShotPlan,
)


class VeoEngineAdapter(BaseEngineAdapter):
    """Veo 3 seven-layer prompt structure."""

    ENGINE_NAME = "veo"

    def compile(self, plan: FoundryShotPlan) -> EnginePromptResult:
        layers: list[str] = []

        # Layer 1: Visual foundation (shot size + camera angle)
        layers.append(
            f"A {plan.shot_size} shot from a {plan.camera_angle} perspective"
        )

        # Layer 2: Motion dynamics (camera movement + transition)
        if plan.camera_movement == "static":
            layers.append("with a locked-off camera")
        else:
            layers.append(f"with {plan.camera_movement} camera movement")
        if plan.transition_to_next != "cut":
            layers.append(f"transitioning via {plan.transition_to_next}")

        # Layer 3: Emotional atmosphere
        layers.append(f"evoking a {plan.emotion_tone} atmosphere")

        # Layer 4: Character presence
        if plan.characters:
            char_str = " and ".join(plan.characters)
            layers.append(f"featuring {char_str}")

        # Layer 5: Environmental context
        if plan.location:
            layers.append(f"set in {plan.location}")

        # Layer 6: Temporal pacing
        pacing = self._pacing_description(plan.duration_sec)
        layers.append(pacing)

        # Layer 7: Technical specifications
        layers.append("rendered in cinematic quality with natural lighting")

        prompt_text = ", ".join(layers) + "."
        word_count = len(prompt_text.split())

        return EnginePromptResult(
            engine=self.ENGINE_NAME,
            prompt_text=prompt_text,
            negative_prompt="artificial, plastic, uncanny valley, text overlay",
            metadata={
                "engine_version": "veo_3",
                "layer_count": 7,
                "word_count": word_count,
                "duration_sec": plan.duration_sec,
            },
        )

    @staticmethod
    def _pacing_description(duration_sec: float) -> str:
        if duration_sec <= 3.0:
            return "unfolding in a brief moment"
        if duration_sec <= 8.0:
            return "paced at a measured rhythm"
        return "developing over an extended take"
