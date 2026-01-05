"""NotebookLM Adapter - Gemini-based Logic/Persona extraction.

Implements the NotebookLM-style analysis pipeline:
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


class NotebookLMAdapter(BaseAdapter):
    """NotebookLM adapter using Gemini API for Logic/Persona extraction.
    
    This adapter replicates NotebookLM's core functionality since NotebookLM
    has no public API. Uses Gemini API under the hood.
    """
    
    def __init__(self):
        super().__init__("notebooklm")
    
    def run(
        self,
        capsule_id: str,
        capsule_version: str,
        inputs: Dict[str, Any],
        params: Dict[str, Any],
        capsule_spec: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AdapterResult:
        """Run NotebookLM-style analysis pipeline."""
        from app.config import settings
        
        # Check if Gemini (NotebookLM substitute) is enabled
        if not settings.GEMINI_ENABLED or not settings.GEMINI_API_KEY:
            self.logger.info("NotebookLM (Gemini) adapter disabled; returning simulated summary")
            return AdapterResult(
                summary={"summary": "NotebookLM simulated summary", "source_count": 3},
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
            from app._deprecated.narrative_utils import normalize_story_beats, normalize_storyboard_cards
            from app.notebooklm_client import (
                generate_story_beats,
                generate_storyboard_cards,
                run_notebooklm_analysis,
            )
            
            summary, evidence_refs = run_notebooklm_analysis(
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
            self.logger.error(f"NotebookLM adapter error: {exc}")
            return AdapterResult(
                summary={"summary": f"NotebookLM fallback: {exc}", "error": str(exc)},
                evidence_refs=[],
            )
