"""Quality Director Service - Context-aware QC Evaluation.

Provides intelligent quality assessment that adapts to IP-specific criteria.
Supports style-aware evaluation based on IP metadata and AD context.

Features:
- IP-aware quality criteria (saturated palettes, specific styles)
- AD context integration for consistent style evaluation
- Structured quality reports with actionable suggestions
- Evidence refs for traceability

Usage:
    from app.services.quality_director_service import QualityDirectorService

    service = QualityDirectorService()
    report = await service.evaluate_with_context(
        content="prompt or generated content",
        ip_id="ip-123",
        ad_context={"visual_style": "cyberpunk", "mood_keywords": ["neon", "dark"]},
    )
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.config import settings
from app.schemas.dna_lab_unified import QualityReport

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Default quality thresholds
DEFAULT_PASS_THRESHOLD = 0.6
DEFAULT_CRITERIA_WEIGHTS = {
    "technical": 0.3,
    "aesthetic": 0.3,
    "narrative": 0.2,
    "consistency": 0.2,
}

# IP-specific criteria adjustments
IP_CRITERIA_PRESETS: Dict[str, Dict[str, Any]] = {
    "cyberpunk": {
        "saturation_tolerance": 0.9,  # Allow high saturation
        "contrast_tolerance": 0.8,
        "color_keywords": ["neon", "cyan", "magenta", "dark"],
    },
    "noir": {
        "saturation_tolerance": 0.3,  # Expect desaturated
        "contrast_tolerance": 0.9,
        "color_keywords": ["black", "white", "shadow", "chiaroscuro"],
    },
    "pastel": {
        "saturation_tolerance": 0.5,
        "contrast_tolerance": 0.4,
        "color_keywords": ["soft", "muted", "gentle", "light"],
    },
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class QualityCriteria:
    """Quality evaluation criteria."""
    name: str
    weight: float = 1.0
    threshold: float = 0.6
    description: str = ""


@dataclass
class IPContext:
    """IP-specific context for quality evaluation."""
    ip_id: str
    style_preset: Optional[str] = None
    saturation_tolerance: float = 0.7
    contrast_tolerance: float = 0.7
    color_keywords: List[str] = field(default_factory=list)
    custom_criteria: Dict[str, float] = field(default_factory=dict)


# =============================================================================
# Quality Director Service
# =============================================================================

class QualityDirectorService:
    """Context-aware quality evaluation service.

    Adapts quality criteria based on IP metadata and style context.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize service.

        Args:
            api_key: Optional API key for LLM-based evaluation
        """
        self._api_key = api_key or settings.GEMINI_API_KEY.get_secret_value()

    async def evaluate_with_context(
        self,
        content: str,
        ip_id: Optional[str] = None,
        ad_context: Optional[Dict[str, Any]] = None,
    ) -> QualityReport:
        """Evaluate content quality with IP and AD context.

        Args:
            content: Content to evaluate (prompt or generated output)
            ip_id: Optional IP identifier for context-aware evaluation
            ad_context: Optional AD (Aesthetic Director) context

        Returns:
            QualityReport with scores and suggestions
        """
        # Load IP context
        ip_context = await self._load_ip_context(ip_id) if ip_id else None

        # Build criteria based on context
        criteria = self._build_criteria(ip_context, ad_context)

        # Run evaluation
        results = await self._evaluate(content, criteria, ip_context, ad_context)

        return results

    async def _load_ip_context(self, ip_id: str) -> Optional[IPContext]:
        """Load IP-specific context from database or cache.

        Args:
            ip_id: IP identifier

        Returns:
            IPContext if found, None otherwise
        """
        try:
            from app.database import get_db_context
            from sqlalchemy import select, text

            # Try to load from ip_catalog table
            async with get_db_context() as db:
                result = await db.execute(
                    text("""
                        SELECT
                            id, name, style_preset, metadata
                        FROM ip_catalog
                        WHERE id = :ip_id OR name = :ip_id
                        LIMIT 1
                    """),
                    {"ip_id": ip_id},
                )
                row = result.fetchone()

                if row:
                    metadata = row.metadata or {}
                    style_preset = row.style_preset or metadata.get("style_preset")

                    # Get preset defaults if available
                    preset_config = IP_CRITERIA_PRESETS.get(style_preset, {})

                    return IPContext(
                        ip_id=ip_id,
                        style_preset=style_preset,
                        saturation_tolerance=metadata.get(
                            "saturation_tolerance",
                            preset_config.get("saturation_tolerance", 0.7),
                        ),
                        contrast_tolerance=metadata.get(
                            "contrast_tolerance",
                            preset_config.get("contrast_tolerance", 0.7),
                        ),
                        color_keywords=metadata.get(
                            "color_keywords",
                            preset_config.get("color_keywords", []),
                        ),
                        custom_criteria=metadata.get("quality_criteria", {}),
                    )

        except Exception as e:
            logger.warning(f"[QualityDirector] Failed to load IP context: {e}")

        return None

    def _build_criteria(
        self,
        ip_context: Optional[IPContext],
        ad_context: Optional[Dict[str, Any]],
    ) -> List[QualityCriteria]:
        """Build quality criteria based on context.

        Args:
            ip_context: IP-specific context
            ad_context: AD (Aesthetic Director) context

        Returns:
            List of QualityCriteria to evaluate
        """
        criteria = [
            QualityCriteria(
                name="technical",
                weight=0.3,
                threshold=0.6,
                description="Technical quality (clarity, coherence)",
            ),
            QualityCriteria(
                name="aesthetic",
                weight=0.3,
                threshold=0.6,
                description="Aesthetic quality (visual appeal, style)",
            ),
            QualityCriteria(
                name="narrative",
                weight=0.2,
                threshold=0.5,
                description="Narrative coherence (story, context)",
            ),
            QualityCriteria(
                name="consistency",
                weight=0.2,
                threshold=0.6,
                description="Style consistency with reference",
            ),
        ]

        # Adjust thresholds based on IP context
        if ip_context:
            # Adjust saturation criterion
            if ip_context.style_preset == "cyberpunk":
                # Cyberpunk expects high saturation, adjust threshold
                for c in criteria:
                    if c.name == "aesthetic":
                        c.threshold = 0.5  # More lenient for vibrant styles

            elif ip_context.style_preset == "noir":
                # Noir expects specific contrast patterns
                for c in criteria:
                    if c.name == "technical":
                        c.weight = 0.35  # Emphasize technical precision

        # Adjust based on AD context
        if ad_context:
            mood = ad_context.get("mood_keywords", [])
            if any(m in mood for m in ["experimental", "avant-garde", "surreal"]):
                # More lenient on narrative coherence for experimental work
                for c in criteria:
                    if c.name == "narrative":
                        c.threshold = 0.4

        return criteria

    async def _evaluate(
        self,
        content: str,
        criteria: List[QualityCriteria],
        ip_context: Optional[IPContext],
        ad_context: Optional[Dict[str, Any]],
    ) -> QualityReport:
        """Run quality evaluation.

        Args:
            content: Content to evaluate
            criteria: Quality criteria
            ip_context: IP context
            ad_context: AD context

        Returns:
            QualityReport with results
        """
        if not content or not content.strip():
            return QualityReport(
                passed=False,
                score=0.0,
                issues=["Content is empty or whitespace only"],
            )

        try:
            # Use LLM for evaluation
            scores = await self._llm_evaluate(content, criteria, ip_context, ad_context)
        except Exception as e:
            logger.error(f"[QualityDirector] LLM evaluation failed: {e}")
            # Fallback to rule-based evaluation
            scores = self._rule_based_evaluate(content, criteria)

        # Calculate overall score
        total_weight = sum(c.weight for c in criteria)
        overall_score = sum(
            scores.get(c.name, 0.5) * c.weight
            for c in criteria
        ) / total_weight if total_weight > 0 else 0.5

        # Check pass/fail
        passed = all(
            scores.get(c.name, 0.0) >= c.threshold
            for c in criteria
        )

        # Collect issues and suggestions
        issues = []
        suggestions = []

        for c in criteria:
            score = scores.get(c.name, 0.5)
            if score < c.threshold:
                issues.append(f"{c.name}: {score:.2f} < {c.threshold:.2f} threshold")
                suggestions.append(self._get_suggestion(c.name, score, ip_context))

        return QualityReport(
            passed=passed,
            score=round(overall_score, 3),
            criteria_results={c.name: round(scores.get(c.name, 0.5), 3) for c in criteria},
            issues=issues,
            suggestions=suggestions,
            technical_score=round(scores.get("technical", 0.5), 3),
            aesthetic_score=round(scores.get("aesthetic", 0.5), 3),
            narrative_coherence=round(scores.get("narrative", 0.5), 3),
            ip_context_used=ip_context is not None,
            ip_id=ip_context.ip_id if ip_context else None,
        )

    async def _llm_evaluate(
        self,
        content: str,
        criteria: List[QualityCriteria],
        ip_context: Optional[IPContext],
        ad_context: Optional[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Evaluate using LLM.

        Args:
            content: Content to evaluate
            criteria: Quality criteria
            ip_context: IP context
            ad_context: AD context

        Returns:
            Dict of criterion name to score
        """
        from app.generation_client import get_generation_client

        client = get_generation_client(api_key=self._api_key)

        # Build evaluation prompt
        context_parts = []
        if ip_context:
            context_parts.append(f"IP Style: {ip_context.style_preset or 'generic'}")
            if ip_context.color_keywords:
                context_parts.append(f"Expected colors: {', '.join(ip_context.color_keywords)}")
        if ad_context:
            if ad_context.get("visual_style"):
                context_parts.append(f"Visual style: {ad_context['visual_style']}")
            if ad_context.get("mood_keywords"):
                context_parts.append(f"Mood: {', '.join(ad_context['mood_keywords'])}")

        context_str = "\n".join(context_parts) if context_parts else "No specific context"

        criteria_str = "\n".join(
            f"- {c.name}: {c.description}"
            for c in criteria
        )

        prompt = f"""Evaluate the following content for quality.

Context:
{context_str}

Criteria to evaluate:
{criteria_str}

Content to evaluate:
{content[:2000]}

Respond with a JSON object containing scores from 0.0 to 1.0 for each criterion:
{{"technical": 0.X, "aesthetic": 0.X, "narrative": 0.X, "consistency": 0.X}}
"""

        try:
            response = await client.generate_json(
                prompt=prompt,
                model="gemini-3-flash-preview",
                response_schema={
                    "type": "object",
                    "properties": {
                        "technical": {"type": "number"},
                        "aesthetic": {"type": "number"},
                        "narrative": {"type": "number"},
                        "consistency": {"type": "number"},
                    },
                },
            )

            return {
                "technical": max(0.0, min(1.0, response.get("technical", 0.5))),
                "aesthetic": max(0.0, min(1.0, response.get("aesthetic", 0.5))),
                "narrative": max(0.0, min(1.0, response.get("narrative", 0.5))),
                "consistency": max(0.0, min(1.0, response.get("consistency", 0.5))),
            }

        except Exception as e:
            logger.warning(f"[QualityDirector] LLM eval failed: {e}")
            raise

    def _rule_based_evaluate(
        self,
        content: str,
        criteria: List[QualityCriteria],
    ) -> Dict[str, float]:
        """Fallback rule-based evaluation.

        Args:
            content: Content to evaluate
            criteria: Quality criteria

        Returns:
            Dict of criterion name to score
        """
        scores = {}

        # Simple heuristics
        content_len = len(content.strip())

        # Technical: length and structure
        if content_len < 10:
            scores["technical"] = 0.2
        elif content_len < 50:
            scores["technical"] = 0.5
        else:
            scores["technical"] = 0.7

        # Aesthetic: presence of descriptive words
        aesthetic_keywords = [
            "visual", "color", "light", "shadow", "tone",
            "composition", "frame", "shot", "scene",
        ]
        keyword_count = sum(1 for k in aesthetic_keywords if k in content.lower())
        scores["aesthetic"] = min(1.0, 0.3 + keyword_count * 0.1)

        # Narrative: sentence structure
        sentences = content.split(".")
        if len(sentences) > 1:
            scores["narrative"] = min(1.0, 0.4 + len(sentences) * 0.05)
        else:
            scores["narrative"] = 0.4

        # Consistency: default to moderate
        scores["consistency"] = 0.6

        return scores

    def _get_suggestion(
        self,
        criterion: str,
        score: float,
        ip_context: Optional[IPContext],
    ) -> str:
        """Get improvement suggestion for a criterion.

        Args:
            criterion: Criterion name
            score: Current score
            ip_context: IP context

        Returns:
            Suggestion string
        """
        suggestions = {
            "technical": "Improve technical clarity and coherence of the content.",
            "aesthetic": "Enhance visual descriptions and style elements.",
            "narrative": "Strengthen narrative flow and contextual connections.",
            "consistency": "Ensure style consistency with the reference.",
        }

        base = suggestions.get(criterion, "Review and improve this aspect.")

        if ip_context and ip_context.style_preset:
            base += f" Consider the {ip_context.style_preset} style requirements."

        return base


# =============================================================================
# Module-level convenience
# =============================================================================

_default_service: Optional[QualityDirectorService] = None


def get_quality_director_service(api_key: Optional[str] = None) -> QualityDirectorService:
    """Get or create the default service instance."""
    global _default_service
    if api_key:
        return QualityDirectorService(api_key=api_key)
    if _default_service is None:
        _default_service = QualityDirectorService()
    return _default_service


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "QualityDirectorService",
    "QualityCriteria",
    "IPContext",
    "IP_CRITERIA_PRESETS",
    "get_quality_director_service",
]
