"""Gemini Adapter - Direct LLM generation for storyboards and shot contracts.

Implements Gemini-based generation with optional DNA/Narrative/Hook injection.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.adapters.base_adapter import AdapterResult, BaseAdapter, aggregate_token_usage

logger = logging.getLogger(__name__)


class GeminiAdapter(BaseAdapter):
    """Gemini adapter for storyboard and shot contract generation.
    
    Supports:
    - Direct storyboard generation
    - DNA-based multi-scene consistency (Story-First)
    - Narrative arc injection
    - Hook variant A/B testing
    """
    
    def __init__(self):
        super().__init__("gemini")
    
    def run(
        self,
        capsule_id: str,
        capsule_version: str,
        inputs: Dict[str, Any],
        params: Dict[str, Any],
        capsule_spec: Optional[Dict[str, Any]] = None,
        director_pack: Optional[Dict[str, Any]] = None,
        scene_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
        narrative_arc: Optional[Dict[str, Any]] = None,
        hook_variant: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AdapterResult:
        """Run Gemini generation pipeline."""
        from app.config import settings
        
        if not settings.GEMINI_ENABLED or not settings.GEMINI_API_KEY:
            self.logger.info("Gemini adapter disabled or missing API key; returning fallback")
            return AdapterResult(
                summary={"summary": "Gemini disabled, using rule-based generation"},
                evidence_refs=[],
            )
        
        try:
            from app.gemini_client import (
                generate_storyboard_with_gemini,
                generate_shot_contracts_with_gemini,
                generate_shot_contracts_with_dna,
            )
            from app._deprecated.narrative_utils import normalize_storyboard_cards
            
            # Generate storyboard
            storyboard, storyboard_usage = generate_storyboard_with_gemini(
                inputs, params, capsule_id
            )
            
            # Determine generation mode
            dna_mode = "disabled"
            if director_pack or narrative_arc or hook_variant:
                dna_mode = "story_first"
                
                # Log generation mode
                mode_parts = []
                if director_pack:
                    mode_parts.append(f"DNA({len(director_pack.get('dna_invariants', []))} rules)")
                if narrative_arc:
                    mode_parts.append(f"Narrative({narrative_arc.get('arc_type', 'unknown')})")
                if hook_variant:
                    mode_parts.append(f"Hook({hook_variant.get('style', 'unknown')})")
                self.logger.info(f"Story-First generation: {' + '.join(mode_parts)}")
                
                shot_contracts, shot_usage = generate_shot_contracts_with_dna(
                    inputs, storyboard, params,
                    director_pack=director_pack,
                    scene_overrides=scene_overrides,
                    narrative_arc=narrative_arc,
                    hook_variant=hook_variant,
                    capsule_id=capsule_id,
                )
            else:
                shot_contracts, shot_usage = generate_shot_contracts_with_gemini(
                    inputs, storyboard, params, capsule_id
                )
            
            # Aggregate token usage
            total_usage = aggregate_token_usage(storyboard_usage, shot_usage)
            
            # Build summary
            summary_storyboard = normalize_storyboard_cards(storyboard)
            summary = {
                "summary": f"Gemini generated {len(storyboard)} storyboard cards, {len(shot_contracts)} shot contracts",
                "storyboard_cards": summary_storyboard,
                "shot_contracts": shot_contracts,
                "token_usage": total_usage,
                "model": settings.GEMINI_MODEL,
                "dna_mode": dna_mode,
            }
            
            # Add DNA compliance info if available
            if director_pack:
                summary["director_pack_id"] = director_pack.get("meta", {}).get("pack_id", "unknown")
                summary["dna_invariants_applied"] = len(director_pack.get("dna_invariants", []))
            
            return AdapterResult(
                summary=summary,
                evidence_refs=[],
                token_usage=total_usage,
            )
            
        except Exception as exc:
            self.logger.error(f"Gemini adapter error: {exc}")
            return AdapterResult(
                summary={"summary": f"Gemini fallback: {exc}", "error": str(exc)},
                evidence_refs=[],
            )
