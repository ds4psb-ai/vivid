"""Gemini Analysis Adapter - Gemini-based Logic/Persona extraction.

Implements the Gemini analysis pipeline (NotebookLM-style outputs, Gemini backend):
1. Logic Vector extraction
2. Persona Vector extraction
3. Variation Guide generation
4. Claim-Evidence generation
5. Story beats and storyboard cards generation
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.adapters.base_adapter import AdapterResult, BaseAdapter
from app.adapters.source_pack_builder import SourcePackBuilder

logger = logging.getLogger(__name__)


class GeminiAnalysisAdapter(BaseAdapter):
    """Gemini analysis adapter (NotebookLM-style outputs).

    Gemini API를 사용해 분석 파이프라인을 수행합니다.
    NotebookLM Tier0(RAG) 어댑터와 혼동되지 않도록 별도 명칭을 사용합니다.
    """
    
    def __init__(self):
        super().__init__("gemini_analysis")
    
    def run(
        self,
        capsule_id: str,
        capsule_version: str,
        inputs: Dict[str, Any],
        params: Dict[str, Any],
        capsule_spec: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AdapterResult:
        """Run Gemini analysis pipeline (NotebookLM-style)."""
        from app.config import settings
        
        # Check if Gemini analysis is enabled
        if not settings.GEMINI_ENABLED or not settings.GEMINI_API_KEY:
            self.logger.info("Gemini analysis adapter disabled; returning simulated summary")
            return AdapterResult(
                summary={"summary": "Gemini analysis simulated summary", "source_count": 3},
                evidence_refs=[],
            )
        
        adapter_config = self._extract_adapter_config(capsule_spec)
        pattern_version = self._extract_pattern_version(capsule_spec)
        
        # Build source pack using the builder pattern
        source_pack = (
            SourcePackBuilder()
            .with_inputs(inputs)
            .with_adapter_config(adapter_config)
            .with_capsule_id(capsule_id)
            .build()
        )
        
        try:
            from app.utils.narrative import normalize_story_beats, normalize_storyboard_cards
            from app.gemini_analysis_client import (
                generate_story_beats,
                generate_storyboard_cards,
                run_gemini_analysis,
            )
            
            summary, evidence_refs = run_gemini_analysis(
                source_pack.to_dict(), capsule_id
            )
            
            # Normalize outputs if present
            if isinstance(summary, dict):
                guide = summary.get("guide", {})
                claims = summary.get("claims", [])
                
                # Normalize story beats
                story_beats = summary.get("story_beats")
                if isinstance(story_beats, list):
                    summary["story_beats"] = normalize_story_beats(story_beats)
                else:
                    summary["story_beats"] = generate_story_beats(
                        source_pack.to_dict(), capsule_id, guide, claims
                    )
                
                # Normalize storyboard cards
                storyboard_cards = summary.get("storyboard_cards")
                if isinstance(storyboard_cards, list):
                    summary["storyboard_cards"] = normalize_storyboard_cards(storyboard_cards)
                else:
                    summary["storyboard_cards"] = generate_storyboard_cards(
                        source_pack.to_dict(),
                        capsule_id,
                        guide,
                        claims,
                        summary.get("story_beats") or [],
                    )
            
            # Add pattern version
            if pattern_version:
                summary["pattern_version"] = pattern_version
            
            # Extract token usage
            token_usage = summary.get("token_usage", {})
            
            return AdapterResult(
                summary=summary,
                evidence_refs=evidence_refs,
                token_usage=token_usage,
            )
            
        except Exception as exc:
            self.logger.error(f"Gemini analysis adapter error: {exc}")
            return AdapterResult(
                summary={"summary": f"Gemini analysis fallback: {exc}", "error": str(exc)},
                evidence_refs=[],
            )
