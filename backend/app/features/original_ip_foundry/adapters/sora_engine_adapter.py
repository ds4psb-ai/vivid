from __future__ import annotations

from app.features.original_ip_foundry.adapters.base_engine_adapter import (
    BaseEngineAdapter,
    EnginePromptResult,
    FoundryShotPlan,
)


class SoraEngineAdapter(BaseEngineAdapter):
    """Sora 2.0 flowing paragraph prompt (50-100 words target)."""

    ENGINE_NAME = "sora"

    def compile(self, plan: FoundryShotPlan) -> EnginePromptResult:
        sections = []
        sections.append(
            f"A {plan.shot_size.replace('_', ' ')} shot from a "
            f"{plan.camera_angle.replace('_', ' ')} angle"
        )
        if plan.characters:
            sections.append(f"captures {' and '.join(plan.characters)}")
        if plan.location:
            sections.append(f"in {plan.location}")
        if plan.camera_movement != "static":
            sections.append(
                f"The camera moves with a {plan.camera_movement.replace('_', ' ')} motion"
            )
        sections.append(f"The mood is {plan.emotion_tone.replace('_', ' ')}")
        sections.append(self._duration_directive(plan.duration_sec))
        prompt_text = ". ".join(sections) + "."
        return EnginePromptResult(
            engine=self.ENGINE_NAME,
            prompt_text=prompt_text,
            negative_prompt="text, watermark, logo, low resolution, blurry",
            metadata={
                "engine_version": "sora_2.0",
                "word_count": len(prompt_text.split()),
                "duration_sec": plan.duration_sec,
            },
        )

    @staticmethod
    def _duration_directive(d: float) -> str:
        if d <= 3.0:
            return "The clip lasts approximately 3 seconds"
        if d <= 8.0:
            return f"The clip runs for about {int(d)} seconds"
        return f"This is an extended take of approximately {int(d)} seconds"
