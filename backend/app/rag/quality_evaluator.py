"""
Quality Evaluator: Gemini-based Automatic Quality Assessment.

Gemini 3.0 모델을 사용한 자동 품질 평가 시스템.
7차원 품질 기준에 따라 콘텐츠를 평가하고 점수를 산출.

Usage:
    from app.rag.quality_evaluator import QualityEvaluator, get_quality_evaluator

    evaluator = get_quality_evaluator()

    # AI 품질 평가
    quality = await evaluator.evaluate(
        dimension="AD",
        input_request={"concept": "봉준호 스타일"},
        output_result={"visual_guidelines": "..."},
    )

    # 사용자 피드백 요청 (선택적)
    user_feedback = await evaluator.request_user_feedback(session_id, output_result)
    quality.user_accepted = user_feedback.get("accepted", False)

    # 승격 자격 판단
    if quality.is_promotion_eligible:
        await store_success_pattern(...)
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional

from app.config import settings
from app.rag.quality_criteria import (
    QualityCriteria,
    DIMENSION_TECHNICAL_CRITERIA,
    QUALITY_WEIGHTS,
    classify_quality_level,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Quality Evaluation Prompt
# ============================================================================

QUALITY_EVALUATION_PROMPT = """You are a quality evaluator for creative AI content generation.

Evaluate the following output based on 7 quality dimensions.
Rate each dimension from 0.0 to 1.0 (where 1.0 is excellent).

## Evaluation Dimensions

1. **coherence** (Weight: {coherence_weight:.0%}): Logical consistency and flow
   - Is the content logically structured?
   - Are there contradictions or inconsistencies?

2. **completeness** (Weight: {completeness_weight:.0%}): Request fulfillment
   - Does the output fully address the input request?
   - Are all required elements present?

3. **creativity** (Weight: {creativity_weight:.0%}): Originality and innovation
   - Does the output show creative interpretation?
   - Is it unique while staying relevant?

4. **style_adherence** (Weight: {style_weight:.0%}): Style guide compliance
   - Does it follow the requested style/aesthetic?
   - Is there visual/tonal consistency?

5. **tone_match** (Weight: {tone_weight:.0%}): Tone and mood alignment
   - Does the mood match the intent?
   - Is the emotional register appropriate?

6. **technical_score** (Weight: {technical_weight:.0%}): Technical quality
   - Is the format correct for the dimension?
   - Are technical requirements met?
   {technical_criteria}

7. **user_rating** (Weight: {user_weight:.0%}): Estimated user satisfaction
   - Would a user be satisfied with this output?
   - Rate as if you were the user (1-5 scale, will be normalized)

## Input Request
{input_request}

## Output to Evaluate
{output_result}

## Dimension Context
Type: {dimension_name}
Requirements: {dimension_requirements}

## Response Format
Respond ONLY with valid JSON (no markdown, no code blocks):
{{
  "coherence": 0.0-1.0,
  "completeness": 0.0-1.0,
  "creativity": 0.0-1.0,
  "style_adherence": 0.0-1.0,
  "tone_match": 0.0-1.0,
  "technical_score": 0.0-1.0,
  "user_rating": 1-5,
  "reasoning": "Brief explanation of scores"
}}
"""


# ============================================================================
# Quality Evaluator
# ============================================================================

class QualityEvaluator:
    """Gemini 기반 품질 평가기.

    Features:
    - 7차원 품질 평가
    - 차원별 기술적 기준 적용
    - 사용자 피드백 통합
    - 캐싱 (동일 입출력 재평가 방지)
    """

    def __init__(self, model: str = "gemini-3-flash-preview"):
        """Initialize evaluator.

        Args:
            model: Gemini model to use for evaluation
        """
        self.model = model
        self._cache: Dict[str, QualityCriteria] = {}
        self._genai_client = None

    @property
    def genai_client(self):
        """Lazy-initialize Gemini client."""
        if self._genai_client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._genai_client = genai.GenerativeModel(self.model)
            except Exception as e:
                logger.error(f"[QualityEvaluator] Failed to initialize Gemini: {e}")
                self._genai_client = None
        return self._genai_client

    def _get_cache_key(
        self,
        dimension: str,
        input_request: Dict[str, Any],
        output_result: Dict[str, Any],
    ) -> str:
        """Generate cache key for evaluation."""
        import hashlib
        content = f"{dimension}:{json.dumps(input_request, sort_keys=True)}:{json.dumps(output_result, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _build_prompt(
        self,
        dimension: str,
        input_request: Dict[str, Any],
        output_result: Dict[str, Any],
    ) -> str:
        """Build evaluation prompt.

        Args:
            dimension: Target dimension (1D, 2D, ..., AD, etc.)
            input_request: Original input request
            output_result: Generated output to evaluate

        Returns:
            Formatted prompt string
        """
        # Get dimension-specific criteria
        dim_criteria = DIMENSION_TECHNICAL_CRITERIA.get(dimension, {})
        dim_name = dim_criteria.get("name", dimension)
        dim_requirements = dim_criteria.get("criteria", [])

        # Format technical criteria
        tech_criteria = ""
        if dim_requirements:
            tech_criteria = "\n   Technical requirements:\n   - " + "\n   - ".join(dim_requirements)

        return QUALITY_EVALUATION_PROMPT.format(
            coherence_weight=QUALITY_WEIGHTS["coherence"],
            completeness_weight=QUALITY_WEIGHTS["completeness"],
            creativity_weight=QUALITY_WEIGHTS["creativity"],
            style_weight=QUALITY_WEIGHTS["style_adherence"],
            tone_weight=QUALITY_WEIGHTS["tone_match"],
            technical_weight=QUALITY_WEIGHTS["technical_score"],
            user_weight=QUALITY_WEIGHTS["user_rating"],
            technical_criteria=tech_criteria,
            input_request=json.dumps(input_request, ensure_ascii=False, indent=2),
            output_result=json.dumps(output_result, ensure_ascii=False, indent=2)[:3000],
            dimension_name=dim_name,
            dimension_requirements="\n".join(f"- {r}" for r in dim_requirements) if dim_requirements else "General quality standards",
        )

    async def evaluate(
        self,
        dimension: str,
        input_request: Dict[str, Any],
        output_result: Dict[str, Any],
        use_cache: bool = True,
    ) -> QualityCriteria:
        """Evaluate output quality using Gemini.

        Args:
            dimension: Target dimension
            input_request: Original input request
            output_result: Generated output to evaluate
            use_cache: Whether to use cached results

        Returns:
            QualityCriteria with evaluation scores
        """
        # Check cache
        cache_key = self._get_cache_key(dimension, input_request, output_result)
        if use_cache and cache_key in self._cache:
            logger.debug(f"[QualityEvaluator] Cache hit: {cache_key}")
            return self._cache[cache_key]

        # Build prompt
        prompt = self._build_prompt(dimension, input_request, output_result)

        # Call Gemini
        try:
            client = self.genai_client
            if client is None:
                logger.warning("[QualityEvaluator] Gemini unavailable, using fallback")
                return self._fallback_evaluation(dimension, input_request, output_result)

            response = await client.generate_content_async(
                prompt,
                generation_config={
                    "temperature": 0.1,  # Low temperature for consistent evaluation
                    "max_output_tokens": 500,
                },
            )

            # Parse response
            result = self._parse_evaluation_response(response.text, dimension)

            # Cache result
            self._cache[cache_key] = result
            logger.info(
                f"[QualityEvaluator] Evaluated {dimension}: "
                f"overall={result.overall:.2f}, level={classify_quality_level(result.overall)}"
            )
            return result

        except Exception as e:
            logger.error(f"[QualityEvaluator] Evaluation failed: {e}")
            return self._fallback_evaluation(dimension, input_request, output_result)

    def _parse_evaluation_response(
        self,
        response_text: str,
        dimension: str,
    ) -> QualityCriteria:
        """Parse Gemini response into QualityCriteria.

        Args:
            response_text: Raw response from Gemini
            dimension: Target dimension

        Returns:
            QualityCriteria instance
        """
        try:
            # Try to extract JSON from response
            # Handle potential markdown code blocks
            json_text = response_text.strip()
            if "```" in json_text:
                # Extract from code block
                match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', json_text)
                if match:
                    json_text = match.group(1)

            data = json.loads(json_text)

            return QualityCriteria(
                coherence=float(data.get("coherence", 0.7)),
                completeness=float(data.get("completeness", 0.7)),
                creativity=float(data.get("creativity", 0.7)),
                style_adherence=float(data.get("style_adherence", 0.7)),
                tone_match=float(data.get("tone_match", 0.7)),
                technical_score=float(data.get("technical_score", 0.7)),
                user_rating=float(data.get("user_rating", 3.5)),
                user_accepted=False,  # Must be set by user feedback
                dimension=dimension,
                metadata={"reasoning": data.get("reasoning", "")},
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"[QualityEvaluator] Parse error: {e}, response: {response_text[:200]}")
            return self._fallback_evaluation(dimension, {}, {})

    def _fallback_evaluation(
        self,
        dimension: str,
        input_request: Dict[str, Any],
        output_result: Dict[str, Any],
    ) -> QualityCriteria:
        """Fallback evaluation when Gemini is unavailable.

        Uses simple heuristics based on output structure.

        Args:
            dimension: Target dimension
            input_request: Original input request
            output_result: Generated output

        Returns:
            QualityCriteria with heuristic scores
        """
        # Basic heuristics
        has_content = bool(output_result)
        content_length = len(json.dumps(output_result))
        has_required_fields = self._check_required_fields(dimension, output_result)

        # Base scores
        base_score = 0.6 if has_content else 0.3
        length_bonus = min(0.2, content_length / 5000)
        field_bonus = 0.1 if has_required_fields else 0.0

        score = min(0.9, base_score + length_bonus + field_bonus)

        return QualityCriteria(
            coherence=score,
            completeness=score + 0.05 if has_required_fields else score - 0.1,
            creativity=score - 0.1,  # Conservative on creativity
            style_adherence=score,
            tone_match=score,
            technical_score=score + 0.1 if has_required_fields else score - 0.1,
            user_rating=3.5 if score >= 0.7 else 2.5,
            user_accepted=False,
            dimension=dimension,
            metadata={"fallback": True},
        )

    def _check_required_fields(
        self,
        dimension: str,
        output_result: Dict[str, Any],
    ) -> bool:
        """Check if output has required fields for dimension.

        Args:
            dimension: Target dimension
            output_result: Generated output

        Returns:
            True if required fields are present
        """
        required_fields_map = {
            "1D": ["prompt"],
            "2D": ["scenes"],
            "3D": ["prompt", "style_tags"],
            "4D": ["analysis"],
            "QC": ["scores", "suggestions"],
            "AD": ["visual_guidelines"],
            "AI": ["persona_update"],
            "VEO": ["prompt"],
        }

        required = required_fields_map.get(dimension, [])
        return all(field in output_result for field in required)

    async def request_user_feedback(
        self,
        session_id: str,
        output_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Request user feedback for output.

        NOTE: This is a placeholder. In production, this would:
        1. Store the output for user review
        2. Send notification to user
        3. Wait for async feedback (webhook or polling)

        Args:
            session_id: User session ID
            output_result: Output to get feedback on

        Returns:
            User feedback dict with "accepted" key
        """
        # Placeholder: In production, implement actual user feedback collection
        # For now, return a pending state
        logger.info(f"[QualityEvaluator] Feedback requested for session {session_id}")
        return {
            "session_id": session_id,
            "accepted": False,  # Must be explicitly set by user
            "rating": None,
            "feedback_pending": True,
        }

    def update_with_user_feedback(
        self,
        quality: QualityCriteria,
        user_feedback: Dict[str, Any],
    ) -> QualityCriteria:
        """Update QualityCriteria with user feedback.

        Args:
            quality: Existing quality criteria
            user_feedback: User feedback dict

        Returns:
            Updated QualityCriteria
        """
        quality.user_accepted = user_feedback.get("accepted", False)

        # Update user_rating if provided
        if user_feedback.get("rating"):
            quality.user_rating = float(user_feedback["rating"])

        # Add feedback to metadata
        quality.metadata["user_feedback"] = {
            "accepted": quality.user_accepted,
            "rating": user_feedback.get("rating"),
            "comment": user_feedback.get("comment"),
        }

        return quality

    def clear_cache(self) -> None:
        """Clear evaluation cache."""
        self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get evaluator statistics.

        Returns:
            Statistics dict
        """
        return {
            "model": self.model,
            "cache_size": len(self._cache),
            "genai_available": self.genai_client is not None,
        }


# ============================================================================
# Singleton
# ============================================================================

_quality_evaluator: Optional[QualityEvaluator] = None


def get_quality_evaluator(model: str = "gemini-3-flash-preview") -> QualityEvaluator:
    """Get QualityEvaluator singleton.

    Args:
        model: Gemini model (only used on first call)

    Returns:
        QualityEvaluator instance
    """
    global _quality_evaluator
    if _quality_evaluator is None:
        _quality_evaluator = QualityEvaluator(model)
    return _quality_evaluator


def reset_quality_evaluator() -> None:
    """Reset evaluator singleton (for testing)."""
    global _quality_evaluator
    _quality_evaluator = None
