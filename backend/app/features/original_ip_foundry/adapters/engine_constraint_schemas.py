"""Engine-specific prompt constraints for Foundry adapters."""

ENGINE_CONSTRAINTS = {
    "veo": {"max_prompt_words": 100, "min_prompt_words": 15, "max_duration_sec": 60},
    "seedance": {"max_prompt_words": 60, "min_prompt_words": 5, "max_duration_sec": 30},
    "kling": {"max_prompt_words": 80, "min_prompt_words": 5, "max_duration_sec": 120},
    "sora": {"max_prompt_words": 120, "min_prompt_words": 10, "max_duration_sec": 60},
}


def validate_engine_output(engine: str, prompt_text: str, duration_sec: float = 0) -> list[str]:
    """Validate prompt output against engine constraints. Returns list of violations."""
    constraints = ENGINE_CONSTRAINTS.get(engine)
    if not constraints:
        return [f"Unknown engine: {engine}"]
    violations = []
    word_count = len(prompt_text.split())
    if word_count > constraints["max_prompt_words"]:
        violations.append(
            f"Prompt exceeds {constraints['max_prompt_words']} word limit ({word_count} words)"
        )
    if word_count < constraints.get("min_prompt_words", 0):
        violations.append(
            f"Prompt below {constraints['min_prompt_words']} word minimum ({word_count} words)"
        )
    if duration_sec and duration_sec > constraints.get("max_duration_sec", float("inf")):
        violations.append(
            f"Duration {duration_sec}s exceeds {constraints['max_duration_sec']}s limit"
        )
    return violations
