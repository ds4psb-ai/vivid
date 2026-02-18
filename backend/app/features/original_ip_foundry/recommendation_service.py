"""Continuity-first recommendation engine for Original-IP Foundry."""
from __future__ import annotations

from typing import Dict, List

from app.features.original_ip_foundry.rights_service import FoundryRightsService


class FoundryRecommendationService:
    """Rank candidate scene variants with continuity as the first gate."""

    def __init__(self, rights_service: FoundryRightsService | None = None):
        self._rights_service = rights_service or FoundryRightsService()

    def recommend(
        self,
        *,
        scene_context: dict,
        candidates: List[dict],
        rights_action: str,
        continuity_floor: float = 0.6,
    ) -> dict:
        context_characters = {str(c).lower() for c in (scene_context.get("characters") or [])}
        context_location = str(scene_context.get("location") or "unknown").lower()
        desired_rhythm = str(scene_context.get("desired_camera_rhythm") or "balanced").lower()
        intent_tags = {str(tag).lower() for tag in (scene_context.get("intent_tags") or [])}

        ranked = []
        for candidate in candidates:
            shots = candidate.get("shots") or []
            first_shot = shots[0] if shots else {}

            continuity = self._calculate_continuity_score(
                context_characters=context_characters,
                context_location=context_location,
                desired_rhythm=desired_rhythm,
                first_shot=first_shot,
                shots=shots,
            )

            rights = self._rights_service.evaluate_assets(
                action=rights_action,
                assets=candidate.get("rights_assets") or [],
                requested_elements=candidate.get("pattern_tags") or [],
            )
            rights_decision = rights["decision"]

            pattern_affinity = self._pattern_affinity(
                intent_tags=intent_tags,
                candidate_tags={str(tag).lower() for tag in (candidate.get("pattern_tags") or [])},
            )
            clone_risk = float(candidate.get("clone_risk", 0.0))

            final_score = (
                0.40 * continuity
                + 0.18 * float(candidate.get("mise_en_scene_score", 0.5))
                + 0.14 * float(candidate.get("story_intent_fit", 0.5))
                + 0.10 * float(candidate.get("director_style_fit", 0.5))
                + 0.08 * float(candidate.get("execution_feasibility", 0.5))
                + 0.10 * pattern_affinity
                - 0.08 * clone_risk
            )
            final_score = max(0.0, min(round(final_score, 4), 1.0))

            reason_codes: List[str] = []
            decision = "allow"
            if rights_decision == "block":
                decision = "block"
                reason_codes.append("RIGHTS_BLOCKED")
            elif rights_decision == "review":
                decision = "review"
                reason_codes.append("RIGHTS_REVIEW_REQUIRED")

            if continuity < continuity_floor:
                decision = "hold" if decision == "allow" else decision
                reason_codes.append("CONTINUITY_BELOW_GATE")

            if decision == "allow" and final_score < 0.7:
                decision = "hold"
                reason_codes.append("QUALITY_GATE_REVIEW")

            reason_codes.extend(rights.get("reason_codes", []))
            reason_codes = list(dict.fromkeys(reason_codes))

            ranked.append(
                {
                    "candidate_id": candidate.get("candidate_id"),
                    "title": candidate.get("title") or "",
                    "decision": decision,
                    "final_score": final_score,
                    "continuity_score": continuity,
                    "reason_codes": reason_codes,
                    "recommendation_rationale": self._build_rationale(
                        continuity=continuity,
                        pattern_affinity=pattern_affinity,
                        rights_decision=rights_decision,
                        clone_risk=clone_risk,
                    ),
                    "rights_decision": rights_decision,
                    "recommended_shots": shots,
                }
            )

        ranked.sort(
            key=lambda item: (
                item["decision"] != "allow",
                item["decision"] == "block",
                -item["final_score"],
            )
        )
        return {
            "scene_id": scene_context.get("scene_id"),
            "ranked": ranked,
            "continuity_gate": continuity_floor,
        }

    def _calculate_continuity_score(
        self,
        *,
        context_characters: set[str],
        context_location: str,
        desired_rhythm: str,
        first_shot: Dict,
        shots: List[dict],
    ) -> float:
        shot_characters = {
            str(char).lower()
            for char in (first_shot.get("characters") or [])
        }
        if context_characters and shot_characters:
            char_overlap = len(context_characters.intersection(shot_characters)) / max(
                len(context_characters.union(shot_characters)),
                1,
            )
        elif not context_characters:
            char_overlap = 1.0
        else:
            char_overlap = 0.0

        shot_location = str(first_shot.get("location") or "unknown").lower()
        if context_location == "unknown" or shot_location == "unknown":
            location_score = 0.7
        else:
            location_score = 1.0 if context_location == shot_location else 0.35

        # Rhythm alignment from movement profile
        movements = [str(shot.get("camera_movement") or "static").lower() for shot in shots]
        dynamic_count = sum(1 for move in movements if move in {"handheld", "tracking", "dolly", "whip_pan"})
        rhythm_ratio = dynamic_count / max(len(movements), 1)
        if desired_rhythm in {"dynamic", "aggressive"}:
            rhythm_score = rhythm_ratio
        elif desired_rhythm in {"steady", "calm"}:
            rhythm_score = 1.0 - rhythm_ratio
        else:
            rhythm_score = 1.0 - abs(rhythm_ratio - 0.5)

        emotion = str(first_shot.get("emotion_tone") or "neutral").lower()
        emotion_score = 1.0 if emotion in {"neutral", "balanced"} else 0.78
        if emotion in {"panic", "fear", "rage"} and desired_rhythm in {"steady", "calm"}:
            emotion_score = 0.4

        score = (
            0.40 * char_overlap
            + 0.25 * location_score
            + 0.20 * rhythm_score
            + 0.15 * emotion_score
        )
        return max(0.0, min(round(score, 4), 1.0))

    def _pattern_affinity(self, *, intent_tags: set[str], candidate_tags: set[str]) -> float:
        if not intent_tags or not candidate_tags:
            return 0.5
        overlap = len(intent_tags.intersection(candidate_tags))
        union = len(intent_tags.union(candidate_tags))
        return round(overlap / max(union, 1), 4)

    def _build_rationale(
        self,
        *,
        continuity: float,
        pattern_affinity: float,
        rights_decision: str,
        clone_risk: float,
    ) -> List[str]:
        rationale = [
            f"Continuity score {continuity:.2f}를 기준으로 후보를 평가했습니다.",
            f"Pattern affinity {pattern_affinity:.2f}를 반영했습니다.",
            f"Rights decision은 {rights_decision}입니다.",
        ]
        if clone_risk >= 0.6:
            rationale.append("Clone risk가 높아 수동 검토가 필요합니다.")
        return rationale

