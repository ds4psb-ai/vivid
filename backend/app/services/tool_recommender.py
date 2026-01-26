"""Tool Recommender Service for IP-First Coordination Phase 2.5.

Provides intelligent tool recommendations based on IP context, user history,
and RAG knowledge. Generates confidence scores and reason codes for
transparent recommendations.

SSoT: IP-First Coordination Roadmap v2.1.1 (Phase 2.5).
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.dimension_tools import (
    TOOL_TO_CAPSULE,
    TOOL_TO_DIMENSION,
    CAPSULE_TO_TOOL,
)
from app.fixtures.dimension_capsules import DIMENSION_CAPSULES
from app.logging_config import get_logger
from app.models_ip import IPCatalog, IPWorkflowPreset
from app.rag.rag_suggestion import (
    ConfidenceLevel,
    build_evidence_ref_id,
    calculate_confidence_level,
)
from app.schemas.tool_recommendation import (
    ReasonCodeCategory,
    ToolRecommendation,
    ToolRecommendationRequest,
    ToolRecommendationResponse,
    ToolEvidenceResponse,
    build_reason_code,
)

logger = get_logger("tool_recommender")


# =============================================================================
# Tool Metadata Cache
# =============================================================================

_TOOL_METADATA_CACHE: Dict[str, Dict[str, Any]] = {}


def _build_tool_metadata_cache() -> Dict[str, Dict[str, Any]]:
    """Build tool metadata cache from DIMENSION_CAPSULES."""
    if _TOOL_METADATA_CACHE:
        return _TOOL_METADATA_CACHE

    for capsule in DIMENSION_CAPSULES:
        capsule_key = capsule.get("capsule_key", "")
        tool_id = CAPSULE_TO_TOOL.get(capsule_key)

        if tool_id:
            credit_costs = capsule.get("credit_costs", {})
            # Use the lower cost option as default
            base_credits = min(credit_costs.values()) if credit_costs else 10

            _TOOL_METADATA_CACHE[tool_id] = {
                "tool_id": tool_id,
                "capsule_key": capsule_key,
                "display_name_ko": capsule.get("display_name", tool_id),
                "display_name_en": capsule.get("display_name_en", tool_id),
                "dimension": TOOL_TO_DIMENSION.get(tool_id, ""),
                "stage": capsule.get("stage", ""),
                "stage_order": capsule.get("stage_order", 99),
                "base_credits": base_credits,
                "input_dimensions": capsule.get("input_dimensions", []),
                "output_dimensions": capsule.get("output_dimensions", []),
                "route_key": capsule.get("route_key", ""),
            }

    return _TOOL_METADATA_CACHE


def get_tool_metadata(tool_id: str) -> Optional[Dict[str, Any]]:
    """Get metadata for a tool.

    Args:
        tool_id: Tool identifier

    Returns:
        Tool metadata dict or None if not found
    """
    cache = _build_tool_metadata_cache()
    return cache.get(tool_id)


def get_all_tools() -> List[Dict[str, Any]]:
    """Get all available tools with metadata.

    Returns:
        List of tool metadata dicts
    """
    cache = _build_tool_metadata_cache()
    return list(cache.values())


# =============================================================================
# Recommendation Engine
# =============================================================================

class ToolRecommenderService:
    """Tool recommendation service.

    Analyzes IP context, user history, and RAG knowledge to recommend
    appropriate tools with confidence scores and reason codes.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service.

        Args:
            db: Async database session
        """
        self._db = db

    async def recommend_tools(
        self,
        request: ToolRecommendationRequest,
    ) -> ToolRecommendationResponse:
        """Get tool recommendations based on request context.

        Args:
            request: Recommendation request with IP/preset context

        Returns:
            ToolRecommendationResponse with ranked recommendations
        """
        trace_id = str(uuid.uuid4())[:8]
        logger.info(f"[ToolRec:{trace_id}] Starting recommendation | request={request}")

        # Load IP and preset context
        ip: Optional[IPCatalog] = None
        preset: Optional[IPWorkflowPreset] = None

        if request.ip_id:
            ip = await self._load_ip(request.ip_id)
        if request.preset_id:
            preset = await self._load_preset(request.preset_id)

        # Build recommendations
        recommendations = await self._build_recommendations(
            ip=ip,
            preset=preset,
            scene_type=request.scene_type,
            user_history=request.user_history or [],
            dimension_context=request.dimension_context,
            max_results=request.max_results,
            trace_id=trace_id,
        )

        # Calculate totals
        total_credits = sum(r.estimated_credits for r in recommendations)
        workflow_suggested = len(recommendations) >= 3 and preset is not None

        # Build reason summary
        reason_summary = self._build_reason_summary(
            ip=ip,
            preset=preset,
            recommendations=recommendations,
        )

        response = ToolRecommendationResponse(
            recommendations=recommendations,
            total_estimated_credits=total_credits,
            workflow_suggested=workflow_suggested,
            reason_summary=reason_summary,
            ip_context_used=ip is not None,
            trace_id=trace_id,
        )

        logger.info(
            f"[ToolRec:{trace_id}] Completed | "
            f"tools={len(recommendations)} total_credits={total_credits}"
        )

        return response

    async def get_tool_evidence(
        self,
        tool_id: str,
        ip_id: Optional[uuid.UUID] = None,
    ) -> ToolEvidenceResponse:
        """Get evidence for a specific tool selection.

        Args:
            tool_id: Tool identifier
            ip_id: Optional IP context

        Returns:
            ToolEvidenceResponse with evidence details
        """
        metadata = get_tool_metadata(tool_id)
        if not metadata:
            return ToolEvidenceResponse(tool_id=tool_id)

        evidence_refs: List[str] = []
        datasets_used: List[str] = []
        reason_codes: List[str] = []
        confidence = 0.5  # Base confidence

        # Add dimension reason
        dimension = metadata.get("dimension", "")
        if dimension:
            reason_codes.append(build_reason_code(ReasonCodeCategory.DIMENSION, dimension))

        # If IP context provided, add IP-based evidence
        if ip_id:
            ip = await self._load_ip(ip_id)
            if ip:
                evidence_refs.append(f"db:ip_catalog:{ip.slug}")
                datasets_used.append(f"ip:{ip.slug}")

                if ip.auteur_key:
                    reason_codes.append(
                        build_reason_code(ReasonCodeCategory.AUTEUR, ip.auteur_key)
                    )
                    confidence += 0.15

                if ip.genre:
                    for genre in ip.genre[:2]:  # Top 2 genres
                        reason_codes.append(
                            build_reason_code(ReasonCodeCategory.GENRE, genre.lower())
                        )
                    confidence += 0.1

        return ToolEvidenceResponse(
            tool_id=tool_id,
            evidence_refs=evidence_refs,
            datasets_used=datasets_used,
            reason_codes=reason_codes,
            confidence=min(confidence, 1.0),
            confidence_level=calculate_confidence_level(min(confidence, 1.0)),
        )

    async def get_ip_recommendations(
        self,
        ip_slug: str,
        max_results: int = 5,
    ) -> ToolRecommendationResponse:
        """Get recommendations for an IP by slug.

        Args:
            ip_slug: IP slug identifier
            max_results: Maximum number of recommendations (default 5)

        Returns:
            ToolRecommendationResponse
        """
        # Load IP by slug
        result = await self._db.execute(
            select(IPCatalog).where(IPCatalog.slug == ip_slug)
        )
        ip = result.scalar_one_or_none()

        if not ip:
            return ToolRecommendationResponse(
                reason_summary=f"IP '{ip_slug}' not found",
            )

        request = ToolRecommendationRequest(ip_id=ip.id, max_results=max_results)
        return await self.recommend_tools(request)

    async def recommend_workflow_from_prompt(
        self,
        user_prompt: str,
        ip_slug: str,
        content_type: str = "shortform",
    ) -> Dict[str, Any]:
        """Recommend workflow based on user's variation prompt using Gemini Flash.

        Uses Intent Classification to determine the best workflow template
        for the user's creative intent.

        Args:
            user_prompt: User's variation/remix prompt (e.g., "캐릭터를 INTJ로 변주")
            ip_slug: IP slug for context
            content_type: Content type ("shortform", "anime-mv")

        Returns:
            Dict with workflow_template, steps, and confidence
        """
        # Workflow templates
        WORKFLOW_TEMPLATES = {
            "character-variation": {
                "name_ko": "캐릭터 변주",
                "name_en": "Character Variation",
                "steps": [
                    {"tool_id": "analyze_reference", "name": "Reference Decoder", "dimension": "4D"},
                    {"tool_id": "persona_analyze", "name": "Abyss Mirror", "dimension": "AI"},
                    {"tool_id": "story_architect", "name": "Story Architect", "dimension": "2D"},
                    {"tool_id": "veo_generate", "name": "VEO Video", "dimension": "VEO"},
                ],
            },
            "style-remix": {
                "name_ko": "스타일 리믹스",
                "name_en": "Style Remix",
                "steps": [
                    {"tool_id": "analyze_reference", "name": "Reference Decoder", "dimension": "4D"},
                    {"tool_id": "aesthetic_direct", "name": "Aesthetic Director", "dimension": "AD"},
                    {"tool_id": "generate_image_prompt", "name": "Visual Realizer", "dimension": "3D"},
                ],
            },
            "scene-extension": {
                "name_ko": "씬 확장",
                "name_en": "Scene Extension",
                "steps": [
                    {"tool_id": "analyze_reference", "name": "Reference Decoder", "dimension": "4D"},
                    {"tool_id": "story_architect", "name": "Story Architect", "dimension": "2D"},
                    {"tool_id": "veo_sequence", "name": "VEO Sequence", "dimension": "VEO"},
                ],
            },
            "full-production": {
                "name_ko": "풀 프로덕션",
                "name_en": "Full Production",
                "steps": [
                    {"tool_id": "analyze_reference", "name": "Reference Decoder", "dimension": "4D"},
                    {"tool_id": "persona_analyze", "name": "Abyss Mirror", "dimension": "AI"},
                    {"tool_id": "aesthetic_direct", "name": "Aesthetic Director", "dimension": "AD"},
                    {"tool_id": "story_architect", "name": "Story Architect", "dimension": "2D"},
                    {"tool_id": "sound_crafter", "name": "Suno Music", "dimension": "AUDIO"},
                    {"tool_id": "veo_generate", "name": "VEO Video", "dimension": "VEO"},
                ],
            },
        }

        # Intent classification keywords
        INTENT_KEYWORDS = {
            "character-variation": [
                "캐릭터", "character", "MBTI", "INTJ", "ENFP", "성격", "personality",
                "persona", "페르소나", "변주", "variation", "인물",
            ],
            "style-remix": [
                "스타일", "style", "강주노", "노란", "ghibli", "지브리",
                "거장", "auteur", "미학", "aesthetic", "색감", "톤", "tone",
            ],
            "scene-extension": [
                "씬", "scene", "확장", "extend", "연장", "continuation",
                "이어서", "다음", "next", "후속",
            ],
        }

        # Simple keyword-based intent classification (fallback)
        prompt_lower = user_prompt.lower()
        detected_intent = "full-production"  # default
        max_matches = 0

        for intent, keywords in INTENT_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw.lower() in prompt_lower)
            if matches > max_matches:
                max_matches = matches
                detected_intent = intent

        # Try Gemini Flash for more accurate classification
        try:
            from app.services.genai_utils import get_gemini_client
            
            client = get_gemini_client()
            classification_prompt = f"""Classify the following user prompt into one of these workflow types:
- character-variation: For character personality, MBTI, persona changes
- style-remix: For visual style, auteur style (강주노, Ghibli, etc.), aesthetic changes
- scene-extension: For extending scenes, continuations, next parts
- full-production: For complete video production from scratch

User prompt: "{user_prompt}"
Content type: {content_type}

Respond with ONLY the workflow type name (e.g., "character-variation")."""

            response = await client.generate_content_async(
                classification_prompt,
                generation_config={"max_output_tokens": 50, "temperature": 0.1},
            )
            
            gemini_intent = response.text.strip().lower().replace('"', '').replace("'", "")
            if gemini_intent in WORKFLOW_TEMPLATES:
                detected_intent = gemini_intent
                logger.info(f"[WorkflowRec] Gemini classified intent: {detected_intent}")
        except Exception as e:
            logger.warning(f"[WorkflowRec] Gemini classification failed, using keyword fallback: {e}")

        # Get the template
        template = WORKFLOW_TEMPLATES.get(detected_intent, WORKFLOW_TEMPLATES["full-production"])
        
        # Calculate confidence based on match quality
        confidence = min(0.5 + (max_matches * 0.1), 0.95)

        return {
            "workflow_template": detected_intent,
            "name_ko": template["name_ko"],
            "name_en": template["name_en"],
            "steps": template["steps"],
            "confidence": confidence,
            "user_prompt": user_prompt,
            "ip_slug": ip_slug,
            "content_type": content_type,
        }

    # =========================================================================
    # Private Methods
    # =========================================================================

    async def _load_ip(self, ip_id: uuid.UUID) -> Optional[IPCatalog]:
        """Load IP catalog by ID."""
        result = await self._db.execute(
            select(IPCatalog).where(IPCatalog.id == ip_id)
        )
        return result.scalar_one_or_none()

    async def _load_preset(self, preset_id: uuid.UUID) -> Optional[IPWorkflowPreset]:
        """Load workflow preset by ID."""
        result = await self._db.execute(
            select(IPWorkflowPreset).where(IPWorkflowPreset.id == preset_id)
        )
        return result.scalar_one_or_none()

    async def _build_recommendations(
        self,
        ip: Optional[IPCatalog],
        preset: Optional[IPWorkflowPreset],
        scene_type: Optional[str],
        user_history: List[str],
        dimension_context: Optional[str],
        max_results: int,
        trace_id: str,
    ) -> List[ToolRecommendation]:
        """Build ranked tool recommendations.

        Scoring factors:
        1. IP context match (auteur, genre, worldbuilding)
        2. Preset workflow alignment
        3. Scene type relevance
        4. User history patterns
        5. Dimension flow (input/output compatibility)
        """
        all_tools = get_all_tools()
        scored_tools: List[Tuple[float, Dict[str, Any], List[str], List[str]]] = []

        for tool_meta in all_tools:
            score, reason_codes, evidence_refs = self._score_tool(
                tool_meta=tool_meta,
                ip=ip,
                preset=preset,
                scene_type=scene_type,
                user_history=user_history,
                dimension_context=dimension_context,
            )

            if score > 0:
                scored_tools.append((score, tool_meta, reason_codes, evidence_refs))

        # Sort by score descending
        scored_tools.sort(key=lambda x: x[0], reverse=True)

        # Build recommendations
        recommendations: List[ToolRecommendation] = []
        for priority, (score, tool_meta, reason_codes, evidence_refs) in enumerate(
            scored_tools[:max_results], start=1
        ):
            recommendation = ToolRecommendation.from_tool_data(
                tool_id=tool_meta["tool_id"],
                display_name=tool_meta["display_name_en"],
                dimension=tool_meta["dimension"],
                confidence=min(score, 1.0),
                reason_codes=reason_codes,
                evidence_refs=evidence_refs,
                estimated_credits=tool_meta["base_credits"],
                priority=priority,
                description=self._get_tool_description(tool_meta, ip),
            )
            recommendations.append(recommendation)

        return recommendations

    def _score_tool(
        self,
        tool_meta: Dict[str, Any],
        ip: Optional[IPCatalog],
        preset: Optional[IPWorkflowPreset],
        scene_type: Optional[str],
        user_history: List[str],
        dimension_context: Optional[str],
    ) -> Tuple[float, List[str], List[str]]:
        """Score a tool based on context.

        Returns:
            Tuple of (score, reason_codes, evidence_refs)
        """
        score = 0.3  # Base score
        reason_codes: List[str] = []
        evidence_refs: List[str] = []

        tool_id = tool_meta["tool_id"]
        dimension = tool_meta["dimension"]

        # Add dimension reason code
        if dimension:
            reason_codes.append(build_reason_code(ReasonCodeCategory.DIMENSION, dimension))

        # IP Context scoring
        if ip:
            evidence_refs.append(f"db:ip_catalog:{ip.slug}")

            # Auteur match
            if ip.auteur_key:
                score += self._auteur_tool_affinity(ip.auteur_key, tool_id)
                reason_codes.append(
                    build_reason_code(ReasonCodeCategory.AUTEUR, ip.auteur_key)
                )

            # Genre match
            if ip.genre:
                genre_boost = self._genre_tool_affinity(ip.genre, tool_id)
                score += genre_boost
                if ip.genre:
                    reason_codes.append(
                        build_reason_code(ReasonCodeCategory.GENRE, ip.genre[0].lower())
                    )

            # Worldbuilding context
            if ip.worldbuilding:
                context_boost = self._worldbuilding_tool_affinity(
                    ip.worldbuilding, tool_id
                )
                score += context_boost
                if context_boost > 0:
                    reason_codes.append(
                        build_reason_code(ReasonCodeCategory.CONTEXT, "worldbuilding")
                    )

        # Preset workflow scoring
        if preset:
            workflow_steps = preset.workflow_steps or []
            if any(
                step.get("tool_id") == tool_id or step.get("capsule") == tool_meta.get("capsule_key")
                for step in workflow_steps
            ):
                score += 0.25
                reason_codes.append(
                    build_reason_code(ReasonCodeCategory.CONTEXT, "workflow_preset")
                )

        # Scene type scoring
        if scene_type:
            scene_boost = self._scene_type_affinity(scene_type, tool_id)
            score += scene_boost
            if scene_boost > 0:
                reason_codes.append(
                    build_reason_code(ReasonCodeCategory.SHOT, scene_type.lower())
                )

        # User history scoring
        if user_history:
            history_boost = self._user_history_affinity(user_history, tool_id, tool_meta)
            score += history_boost
            if history_boost > 0:
                reason_codes.append(
                    build_reason_code(ReasonCodeCategory.HISTORY, "workflow_pattern")
                )

        # Dimension context scoring
        if dimension_context:
            # Check if this tool is a natural next step
            if dimension_context in tool_meta.get("input_dimensions", []):
                score += 0.2
            elif dimension_context == dimension:
                score += 0.1

        return score, reason_codes, evidence_refs

    def _auteur_tool_affinity(self, auteur_key: str, tool_id: str) -> float:
        """Calculate auteur-tool affinity score.

        Different auteurs have different tool preferences based on their style.
        """
        # Auteur -> preferred tools mapping
        auteur_preferences = {
            "bong": {
                "aesthetic_direct": 0.3,  # Strong visual style
                "quality_check": 0.2,
                "analyze_reference": 0.25,
            },
            "epoch": {
                "story_architect": 0.3,  # Complex narratives
                "analyze_reference": 0.2,
                "aesthetic_direct": 0.2,
            },
            "prism": {
                "aesthetic_direct": 0.35,  # Meticulous visual style
                "quality_check": 0.25,
                "analyze_reference": 0.2,
            },
            "voltage": {
                "story_architect": 0.25,  # Dialogue-heavy
                "sound_crafter": 0.3,  # Music emphasis
                "aesthetic_direct": 0.15,
            },
            "ghibli": {
                "generate_image_prompt": 0.3,  # Visual emphasis
                "aesthetic_direct": 0.25,
                "story_architect": 0.2,
            },
            "abyss": {
                "veo_generate": 0.25,  # Grand visuals
                "aesthetic_direct": 0.25,
                "sound_crafter": 0.2,
            },
        }

        prefs = auteur_preferences.get(auteur_key, {})
        return prefs.get(tool_id, 0.1)  # Default small boost for any IP context

    def _genre_tool_affinity(self, genres: List[str], tool_id: str) -> float:
        """Calculate genre-tool affinity score."""
        genre_preferences = {
            "horror": {"aesthetic_direct": 0.2, "sound_crafter": 0.25},
            "romance": {"aesthetic_direct": 0.2, "story_architect": 0.2},
            "action": {"veo_generate": 0.2, "create_storyboard": 0.2},
            "drama": {"story_architect": 0.25, "aesthetic_direct": 0.15},
            "comedy": {"story_architect": 0.2, "sound_crafter": 0.15},
            "fantasy": {"generate_image_prompt": 0.25, "aesthetic_direct": 0.2},
            "sci-fi": {"veo_generate": 0.2, "generate_image_prompt": 0.2},
            "documentary": {"analyze_reference": 0.25, "quality_check": 0.2},
        }

        total_boost = 0.0
        for genre in genres:
            prefs = genre_preferences.get(genre.lower(), {})
            total_boost += prefs.get(tool_id, 0.0)

        return min(total_boost, 0.3)  # Cap at 0.3

    def _worldbuilding_tool_affinity(
        self, worldbuilding: Dict[str, Any], tool_id: str
    ) -> float:
        """Calculate worldbuilding-tool affinity score."""
        boost = 0.0

        # If has characters, character-related tools get boost
        if worldbuilding.get("characters"):
            if tool_id in ["aesthetic_direct", "persona_analyze", "generate_character_dna"]:
                boost += 0.15

        # If has settings, visual tools get boost
        if worldbuilding.get("setting") or worldbuilding.get("locations"):
            if tool_id in ["generate_image_prompt", "aesthetic_direct", "create_storyboard"]:
                boost += 0.1

        # If has themes, story tools get boost
        if worldbuilding.get("themes"):
            if tool_id in ["story_architect", "analyze_reference"]:
                boost += 0.1

        return boost

    def _scene_type_affinity(self, scene_type: str, tool_id: str) -> float:
        """Calculate scene type-tool affinity score."""
        scene_preferences = {
            "establishing": {
                "generate_image_prompt": 0.2,
                "aesthetic_direct": 0.15,
                "create_storyboard": 0.1,
            },
            "dialogue": {
                "story_architect": 0.2,
                "aesthetic_direct": 0.1,
            },
            "action": {
                "veo_generate": 0.2,
                "create_storyboard": 0.2,
                "sound_crafter": 0.15,
            },
            "montage": {
                "create_storyboard": 0.25,
                "sound_crafter": 0.2,
            },
            "closeup": {
                "aesthetic_direct": 0.2,
                "generate_image_prompt": 0.15,
            },
        }

        prefs = scene_preferences.get(scene_type.lower(), {})
        return prefs.get(tool_id, 0.0)

    def _user_history_affinity(
        self,
        user_history: List[str],
        tool_id: str,
        tool_meta: Dict[str, Any],
    ) -> float:
        """Calculate user history-tool affinity score.

        Boosts tools that are natural next steps based on recent usage.
        """
        if not user_history:
            return 0.0

        # Check if this tool is a natural next step
        last_tool = user_history[-1] if user_history else None
        if last_tool:
            last_meta = get_tool_metadata(last_tool)
            if last_meta:
                # Check if current tool is in output dimensions of last tool
                output_dims = last_meta.get("output_dimensions", [])
                route_key = tool_meta.get("route_key", "")
                if route_key in output_dims:
                    return 0.2

        # Check if recently used (mild preference)
        if tool_id in user_history[-3:]:
            return 0.1

        return 0.0

    def _get_tool_description(
        self,
        tool_meta: Dict[str, Any],
        ip: Optional[IPCatalog],
    ) -> str:
        """Generate a contextual description for the tool recommendation."""
        display_name = tool_meta.get("display_name_en", tool_meta["tool_id"])
        dimension = tool_meta.get("dimension", "")

        if ip:
            return f"{display_name} optimized for {ip.name_en} ({dimension})"
        return f"{display_name} - {dimension} dimension tool"

    def _build_reason_summary(
        self,
        ip: Optional[IPCatalog],
        preset: Optional[IPWorkflowPreset],
        recommendations: List[ToolRecommendation],
    ) -> str:
        """Build a human-readable reason summary."""
        parts = []

        if ip:
            parts.append(f"Based on '{ip.name_en}'")
            if ip.auteur_key:
                parts.append(f"({ip.auteur_key} style)")

        if preset:
            parts.append(f"optimized for {preset.name_en} workflow")

        if recommendations:
            top_dims = list(set(r.dimension for r in recommendations[:3]))
            if top_dims:
                parts.append(f"recommended tools: {', '.join(top_dims)}")

        return " ".join(parts) if parts else "General tool recommendations"


# =============================================================================
# Factory Function
# =============================================================================

def create_tool_recommender(db: AsyncSession) -> ToolRecommenderService:
    """Create a ToolRecommenderService instance.

    Args:
        db: Async database session

    Returns:
        ToolRecommenderService instance
    """
    return ToolRecommenderService(db)
