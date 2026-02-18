"""4-factor weighted reward function for Foundry experiments."""
from __future__ import annotations


class EnhancedRewardService:
    """SSOT formula: 0.40*adoption + 0.20*edit_distance + 0.20*decision_speed + 0.20*satisfaction."""

    WEIGHTS = {
        "adoption": 0.40,
        "edit_distance": 0.20,
        "decision_speed": 0.20,
        "satisfaction": 0.20,
    }
    ADOPTION_MAP = {"accepted": 1.0, "edited": 0.5, "rejected": 0.0}
    SPEED_EXCELLENT_SEC = 10
    SPEED_POOR_SEC = 300

    def compute_reward(
        self,
        *,
        outcome: str,
        completion_seconds: float | None = None,
        edit_distance: float = 0.0,
        satisfaction_score: float | None = None,
    ) -> dict:
        """Compute weighted reward from 4 factors."""
        adoption = self.ADOPTION_MAP.get(outcome, 0.0)
        edit_factor = max(0.0, 1.0 - edit_distance)
        speed = self._normalize_speed(completion_seconds) if completion_seconds is not None else 0.5
        satisfaction = satisfaction_score if satisfaction_score is not None else adoption

        reward = sum(
            self.WEIGHTS[k] * v
            for k, v in [
                ("adoption", adoption),
                ("edit_distance", edit_factor),
                ("decision_speed", speed),
                ("satisfaction", satisfaction),
            ]
        )
        return {
            "reward": round(reward, 4),
            "factors": {
                "adoption": round(adoption, 4),
                "edit_distance": round(edit_factor, 4),
                "decision_speed": round(speed, 4),
                "satisfaction": round(satisfaction, 4),
            },
            "weights": dict(self.WEIGHTS),
        }

    def _normalize_speed(self, seconds: float) -> float:
        """Linear interpolation: EXCELLENT_SEC -> 1.0, POOR_SEC -> 0.0."""
        if seconds <= self.SPEED_EXCELLENT_SEC:
            return 1.0
        if seconds >= self.SPEED_POOR_SEC:
            return 0.0
        return round(1.0 - (seconds - self.SPEED_EXCELLENT_SEC) / (self.SPEED_POOR_SEC - self.SPEED_EXCELLENT_SEC), 4)
