from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class FoundryShotPlan:
    shot_id: str
    shot_size: str = "medium"
    camera_angle: str = "eye_level"
    camera_movement: str = "static"
    emotion_tone: str = "neutral"
    transition_to_next: str = "cut"
    location: str | None = None
    characters: list[str] = field(default_factory=list)
    duration_sec: float = 6.0


@dataclass
class EnginePromptResult:
    engine: str
    prompt_text: str
    negative_prompt: str = ""
    metadata: dict = field(default_factory=dict)


class BaseEngineAdapter(ABC):
    ENGINE_NAME: str = ""

    @abstractmethod
    def compile(self, plan: FoundryShotPlan) -> EnginePromptResult:
        ...

    def validate_output(self, result: EnginePromptResult, duration_sec: float = 0) -> list[str]:
        from app.features.original_ip_foundry.adapters.engine_constraint_schemas import validate_engine_output

        return validate_engine_output(self.ENGINE_NAME, result.prompt_text, duration_sec)
