"""DNA Lab Service - Orchestrates DNA extraction from multiple sources.

Combines VPE (Video Parsing Engine), AD (Aesthetic Director), Mirror (Persona),
and QC (Quality Controller) to extract comprehensive Logic Vectors.

Features:
- Component-based execution (select which modules to run)
- Logic Vector merging from multiple sources
- Confidence aggregation
- Evidence refs collection

Usage:
    from app.services.dna_lab_service import DNALabService, get_dna_lab_service

    service = get_dna_lab_service()
    result = await service.extract_dna(
        video_uri="gs://bucket/video.mp4",
        concept="sci-fi noir",
        auteur_key="bong",
        components=["vpe", "ad"],
    )
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from app.config import settings
from app.schemas.vpe import LogicVector, VPEParseResponse

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

class DNAComponent(str, Enum):
    """Available DNA Lab components."""
    VPE = "vpe"         # Video Parsing Engine
    AD = "ad"           # Aesthetic Director
    MIRROR = "mirror"   # Abyss Mirror (Persona)
    QC = "qc"           # Quality Controller


# Credit costs per component
COMPONENT_CREDITS = {
    DNAComponent.VPE: 50,
    DNAComponent.AD: 10,
    DNAComponent.MIRROR: 5,
    DNAComponent.QC: 8,
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class AestheticGuidelines:
    """Aesthetic Director output."""
    visual_style: str = ""
    color_palette: List[str] = field(default_factory=list)
    mood_keywords: List[str] = field(default_factory=list)
    reference_directors: List[str] = field(default_factory=list)
    composition_notes: str = ""
    lighting_approach: str = ""


@dataclass
class PersonaDNA:
    """Mirror (Persona) analysis output."""
    persona_type: str = ""
    creative_tendencies: List[str] = field(default_factory=list)
    visual_preferences: List[str] = field(default_factory=list)
    narrative_style: str = ""
    emotional_range: List[str] = field(default_factory=list)


@dataclass
class QualityMetrics:
    """Quality Controller output."""
    overall_score: float = 0.0
    technical_score: float = 0.0
    aesthetic_score: float = 0.0
    narrative_coherence: float = 0.0
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class DNALabResult:
    """Combined DNA Lab extraction result."""
    success: bool
    trace_id: str
    logic_vector: Optional[LogicVector] = None
    aesthetic_guidelines: Optional[AestheticGuidelines] = None
    persona_dna: Optional[PersonaDNA] = None
    quality_metrics: Optional[QualityMetrics] = None
    evidence_refs: List[str] = field(default_factory=list)
    confidence: float = 0.0
    components_run: List[str] = field(default_factory=list)
    processing_time_ms: int = 0
    credits_used: int = 0
    errors: Dict[str, str] = field(default_factory=dict)


@dataclass
class DNALabProgress:
    """Progress update during DNA extraction."""
    status: str  # "starting", "processing", "merging", "completed", "failed"
    current_component: Optional[str] = None
    completed_components: List[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    message: str = ""


# =============================================================================
# DNA Lab Service
# =============================================================================

class DNALabServiceError(Exception):
    """Base exception for DNA Lab service errors."""
    pass


class DNALabService:
    """Orchestration service for DNA extraction from multiple sources."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize DNA Lab service.

        Args:
            api_key: Optional API key for external services
        """
        self._api_key = api_key or settings.GEMINI_API_KEY.get_secret_value()

    async def extract_dna(
        self,
        video_uri: Optional[str] = None,
        concept: Optional[str] = None,
        auteur_key: Optional[str] = None,
        components: Optional[List[str]] = None,
        persona_context: Optional[Dict[str, Any]] = None,
        quality_content: Optional[str] = None,
        progress_callback: Optional[Callable[[DNALabProgress], None]] = None,
    ) -> DNALabResult:
        """Extract DNA using selected components.

        Args:
            video_uri: Video URI for VPE analysis
            concept: Creative concept for AD analysis
            auteur_key: Auteur hint/filter
            components: List of components to run (default: ["ad"])
            persona_context: Context for Mirror analysis
            quality_content: Content for QC analysis
            progress_callback: Optional progress callback

        Returns:
            DNALabResult with combined outputs
        """
        start_time = time.monotonic()
        trace_id = str(uuid.uuid4())

        # Default to AD only
        if components is None:
            components = [DNAComponent.AD.value]

        # Normalize component names
        components = [c.lower() for c in components]
        valid_components = [c for c in components if c in [e.value for e in DNAComponent]]

        if not valid_components:
            return DNALabResult(
                success=False,
                trace_id=trace_id,
                errors={"components": "No valid components specified"},
            )

        def emit_progress(status: str, component: Optional[str] = None,
                          completed: Optional[List[str]] = None, message: str = ""):
            if progress_callback:
                try:
                    progress_callback(DNALabProgress(
                        status=status,
                        current_component=component,
                        completed_components=completed or [],
                        elapsed_seconds=time.monotonic() - start_time,
                        message=message,
                    ))
                except Exception as e:
                    logger.warning(f"[DNALab] Progress callback failed: {e}")

        emit_progress("starting", message="DNA 추출 시작...")

        # Prepare tasks for parallel execution
        tasks = {}
        results = {}
        errors = {}
        evidence_refs = []
        total_credits = 0

        # VPE Component
        if DNAComponent.VPE.value in valid_components:
            if video_uri:
                tasks["vpe"] = self._run_vpe(video_uri, auteur_key)
                total_credits += COMPONENT_CREDITS[DNAComponent.VPE]
            else:
                errors["vpe"] = "video_uri required for VPE"

        # AD Component
        if DNAComponent.AD.value in valid_components:
            if concept or auteur_key:
                tasks["ad"] = self._run_aesthetic_director(concept, auteur_key)
                total_credits += COMPONENT_CREDITS[DNAComponent.AD]
            else:
                errors["ad"] = "concept or auteur_key required for AD"

        # Mirror Component
        if DNAComponent.MIRROR.value in valid_components:
            if persona_context:
                tasks["mirror"] = self._run_mirror(persona_context)
                total_credits += COMPONENT_CREDITS[DNAComponent.MIRROR]
            else:
                errors["mirror"] = "persona_context required for Mirror"

        # QC Component
        if DNAComponent.QC.value in valid_components:
            if quality_content:
                tasks["qc"] = self._run_quality_check(quality_content)
                total_credits += COMPONENT_CREDITS[DNAComponent.QC]
            else:
                errors["qc"] = "quality_content required for QC"

        if not tasks:
            return DNALabResult(
                success=False,
                trace_id=trace_id,
                errors=errors,
            )

        # Execute tasks in parallel
        emit_progress("processing", message=f"Running {len(tasks)} components...")

        completed_components = []
        task_results = await asyncio.gather(
            *tasks.values(),
            return_exceptions=True,
        )

        for component, result in zip(tasks.keys(), task_results):
            if isinstance(result, Exception):
                errors[component] = str(result)
                logger.error(f"[DNALab] Component {component} failed: {result}")
            else:
                results[component] = result
                completed_components.append(component)
                emit_progress(
                    "processing",
                    component=component,
                    completed=completed_components,
                    message=f"{component.upper()} 완료",
                )

        emit_progress("merging", completed=completed_components, message="결과 병합 중...")

        # Extract and merge results
        logic_vector = None
        aesthetic_guidelines = None
        persona_dna = None
        quality_metrics = None
        confidence_scores = []

        # Process VPE result
        if "vpe" in results:
            vpe_result: VPEParseResponse = results["vpe"]
            if vpe_result.success and vpe_result.logic_vector:
                logic_vector = vpe_result.logic_vector
                evidence_refs.extend(vpe_result.evidence_refs)
                confidence_scores.append(vpe_result.confidence)

        # Process AD result
        if "ad" in results:
            ad_result = results["ad"]
            if ad_result.get("success"):
                output = ad_result.get("output", {})
                aesthetic_guidelines = AestheticGuidelines(
                    visual_style=output.get("visual_style", ""),
                    color_palette=output.get("color_palette", []),
                    mood_keywords=output.get("mood_keywords", []),
                    reference_directors=output.get("reference_directors", []),
                    composition_notes=output.get("composition_notes", ""),
                    lighting_approach=output.get("lighting_approach", ""),
                )
                evidence_refs.extend(output.get("evidence_refs", []))

                # If no VPE logic vector, create one from AD
                if logic_vector is None and auteur_key:
                    logic_vector = self._create_logic_vector_from_ad(
                        aesthetic_guidelines,
                        auteur_key,
                    )
                    confidence_scores.append(0.7)

        # Process Mirror result
        if "mirror" in results:
            mirror_result = results["mirror"]
            if mirror_result.get("success"):
                output = mirror_result.get("output", {})
                persona_dna = PersonaDNA(
                    persona_type=output.get("persona_type", ""),
                    creative_tendencies=output.get("creative_tendencies", []),
                    visual_preferences=output.get("visual_preferences", []),
                    narrative_style=output.get("narrative_style", ""),
                    emotional_range=output.get("emotional_range", []),
                )
                evidence_refs.extend(output.get("evidence_refs", []))

        # Process QC result
        if "qc" in results:
            qc_result = results["qc"]
            if qc_result.get("success"):
                output = qc_result.get("output", {})
                quality_metrics = QualityMetrics(
                    overall_score=output.get("score", 0.0),
                    technical_score=output.get("technical_score", 0.0),
                    aesthetic_score=output.get("aesthetic_score", 0.0),
                    narrative_coherence=output.get("narrative_coherence", 0.0),
                    issues=output.get("issues", []),
                    suggestions=output.get("suggestions", []),
                )
                evidence_refs.extend(output.get("evidence_refs", []))

        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        processing_time_ms = int((time.monotonic() - start_time) * 1000)

        emit_progress("completed", completed=completed_components, message="DNA 추출 완료!")

        return DNALabResult(
            success=len(completed_components) > 0,
            trace_id=trace_id,
            logic_vector=logic_vector,
            aesthetic_guidelines=aesthetic_guidelines,
            persona_dna=persona_dna,
            quality_metrics=quality_metrics,
            evidence_refs=evidence_refs,
            confidence=overall_confidence,
            components_run=completed_components,
            processing_time_ms=processing_time_ms,
            credits_used=total_credits,
            errors=errors,
        )

    async def _run_vpe(
        self,
        video_uri: str,
        auteur_hint: Optional[str] = None,
    ) -> VPEParseResponse:
        """Run VPE component."""
        from app.services.vpe_service import get_vpe_service

        service = get_vpe_service(api_key=self._api_key)
        return await service.parse_video(
            video_uri=video_uri,
            auteur_hint=auteur_hint,
            extract_shots=True,
        )

    async def _run_aesthetic_director(
        self,
        concept: Optional[str],
        auteur_key: Optional[str],
    ) -> Dict[str, Any]:
        """Run Aesthetic Director component."""
        from app.dimension_adapter import execute_dimension_capsule

        inputs = {
            "concept": concept or "",
            "auteur_key": auteur_key or "bong",
        }
        params = {"model": "gemini-3-flash-preview"}

        try:
            result = await execute_dimension_capsule(
                capsule_id="dimension.aesthetic.direct",
                inputs=inputs,
                params=params,
            )
            return result
        except Exception as e:
            logger.error(f"[DNALab] AD failed: {e}")
            return {"success": False, "error": str(e)}

    async def _run_mirror(
        self,
        persona_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run Mirror (Persona) component."""
        from app.dimension_adapter import execute_dimension_capsule

        inputs = {
            "analysis_stage": "intro",
            "conversation_history": [],
            **persona_context,
        }
        params = {"model": "gemini-3-flash-preview"}

        try:
            result = await execute_dimension_capsule(
                capsule_id="dimension.persona.analyze",
                inputs=inputs,
                params=params,
            )
            return result
        except Exception as e:
            logger.error(f"[DNALab] Mirror failed: {e}")
            return {"success": False, "error": str(e)}

    async def _run_quality_check(
        self,
        content: str,
    ) -> Dict[str, Any]:
        """Run Quality Controller component."""
        from app.dimension_adapter import execute_dimension_capsule

        inputs = {
            "content": content,
            "content_type": "general",
        }
        params = {"model": "gemini-3-flash-preview"}

        try:
            result = await execute_dimension_capsule(
                capsule_id="dimension.quality.check",
                inputs=inputs,
                params=params,
            )
            return result
        except Exception as e:
            logger.error(f"[DNALab] QC failed: {e}")
            return {"success": False, "error": str(e)}

    def _create_logic_vector_from_ad(
        self,
        guidelines: AestheticGuidelines,
        auteur_key: str,
    ) -> LogicVector:
        """Create a LogicVector from Aesthetic Director guidelines."""
        from app.schemas.vpe import (
            Cadence,
            CameraGrammar,
            ColorScience,
            Composition,
            LightingPhysics,
        )

        # Map visual style to composition
        composition_map = {
            "symmetrical": ("symmetry", 0.9),
            "dynamic": ("diagonal_tension", 0.4),
            "minimalist": ("negative_space", 0.6),
            "classical": ("rule_of_thirds", 0.7),
        }
        primary_strategy, symmetry = composition_map.get(
            guidelines.visual_style.lower().split()[0] if guidelines.visual_style else "",
            ("rule_of_thirds", 0.5)
        )

        # Map lighting approach
        lighting_map = {
            "natural": "natural",
            "dramatic": "low_key",
            "bright": "high_key",
            "moody": "chiaroscuro",
        }
        key_light = lighting_map.get(
            guidelines.lighting_approach.lower().split()[0] if guidelines.lighting_approach else "",
            "natural"
        )

        return LogicVector(
            auteur_id=auteur_key,
            cadence=Cadence(tempo="balanced"),
            composition=Composition(
                primary_strategy=primary_strategy,
                symmetry_score=symmetry,
            ),
            camera_grammar=CameraGrammar(
                static=0.4,
                dolly=0.3,
                handheld=0.2,
                tracking=0.1,
            ),
            lighting_physics=LightingPhysics(
                key_light=key_light,
                color_temp_range=[3200, 5600],
            ),
            color_science=ColorScience(
                palette=guidelines.color_palette[:5] if guidelines.color_palette else [],
            ),
            analysis_timestamp=datetime.utcnow(),
            confidence=0.7,
        )

    def calculate_total_credits(self, components: List[str]) -> int:
        """Calculate total credits for selected components."""
        total = 0
        for comp in components:
            try:
                total += COMPONENT_CREDITS[DNAComponent(comp.lower())]
            except (ValueError, KeyError):
                pass
        return total


# =============================================================================
# Module-level convenience functions
# =============================================================================

_default_service: Optional[DNALabService] = None


def get_dna_lab_service(api_key: Optional[str] = None) -> DNALabService:
    """Get or create the default DNA Lab service instance.

    Args:
        api_key: Optional API key override

    Returns:
        DNALabService instance
    """
    global _default_service
    if api_key:
        return DNALabService(api_key=api_key)
    if _default_service is None:
        _default_service = DNALabService()
    return _default_service


async def extract_dna(
    video_uri: Optional[str] = None,
    concept: Optional[str] = None,
    auteur_key: Optional[str] = None,
    components: Optional[List[str]] = None,
    api_key: Optional[str] = None,
) -> DNALabResult:
    """Convenience function for DNA extraction.

    Args:
        video_uri: Video URI for VPE
        concept: Creative concept for AD
        auteur_key: Auteur hint
        components: Components to run
        api_key: Optional API key override

    Returns:
        DNALabResult
    """
    service = get_dna_lab_service(api_key)
    return await service.extract_dna(
        video_uri=video_uri,
        concept=concept,
        auteur_key=auteur_key,
        components=components,
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "DNALabService",
    "DNALabServiceError",
    "DNALabResult",
    "DNALabProgress",
    "DNAComponent",
    "AestheticGuidelines",
    "PersonaDNA",
    "QualityMetrics",
    "COMPONENT_CREDITS",
    "get_dna_lab_service",
    "extract_dna",
]
