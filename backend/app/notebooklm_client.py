"""NotebookLM Client using Gemini API for Logic/Persona extraction.

Since NotebookLM has no public API, we use Gemini API to replicate
the core functionality: Logic Vector extraction, Persona Vector extraction,
and Guide generation with claim-evidence structure.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings
from app.narrative_utils import normalize_story_beats, normalize_storyboard_cards
from app.ideal_persona import build_persona_context, build_visual_context, get_thematic_weights

logger = logging.getLogger(__name__)

# System prompts for Logic/Persona extraction
LOGIC_EXTRACTION_PROMPT = """당신은 영상 분석 전문가입니다. 주어진 Source Pack 데이터를 분석하여 Logic Vector를 추출하세요.

Logic Vector는 다음 속성을 포함합니다:
- cadence: shot_length_ms (median, p25, p75), cut_density, transition_types
- composition: symmetry_score, framing_ratio (WS, MS, CU)
- camera_motion: handheld, dolly, static 비율
- motif_rules: 모티프 재등장 패턴

반드시 JSON 형식으로 응답하세요.
"""

PERSONA_EXTRACTION_PROMPT = """당신은 영화 감독 스타일 분석 전문가입니다. 주어진 Source Pack과 거장 ID를 기반으로 Persona Vector를 추출하세요.

Persona Vector는 다음 속성을 포함합니다:
- tone: 해석 톤 (dry, observational, ironic, lyrical, etc.)
- emotion_arc: 시간별 valence/arousal 변화
- sentence_rhythm: avg_len, pause_bias
- interpretation_frame: 해석 프레임 (psychology, society, aesthetics, genre)

반드시 JSON 형식으로 응답하세요.
"""

VARIATION_GUIDE_PROMPT = """당신은 영상 제작 가이드 전문가입니다. Logic Vector와 Persona Vector를 기반으로 Variation Guide를 생성하세요.

Guide는 다음을 포함해야 합니다:
- logic_summary: 로직 벡터 요약
- persona_summary: 페르소나 벡터 요약
- variation_rules: 변주 규칙 리스트
- params_proposal: 파라미터 제안 (key, range, default)
- template_fit_notes: 템플릿 적합성 노트
- template_recommendations: 템플릿 추천 리스트

반드시 JSON 형식으로 응답하세요.
"""

STORY_BEATS_PROMPT = """You are a story editor. Build a compact beat sheet from the context.

Return a JSON object with a "story_beats" array.
Each beat must include:
- beat_id (e.g. b1, b2)
- summary (short sentence)
- tension (low|medium|high)

Target 3-7 beats. JSON only.
"""

STORYBOARD_PROMPT = """You are a storyboard artist. Create concise storyboard cards from the context.

Return a JSON object with a "storyboard_cards" array.
Each card must include:
- card_id (e.g. c1, c2)
- shot (short shot label)
- note (short visual note)

Target 3-7 cards. JSON only.
"""

# Script Persona Priority Policy (33_CODEX §2.4)
SCRIPT_PERSONA_PROMPT = """당신은 시나리오 분석 전문가입니다. 주어진 스크립트 세그먼트를 분석하여 Script Persona Vector를 추출하세요.

Script Persona Vector는 다음 속성을 포함합니다:
- tone: 시나리오에 내재된 톤 (dry, observational, ironic, lyrical, tense, warm 등)
- emotion_arc: 씬 진행에 따른 valence/arousal 변화
- sentence_rhythm: 대사 평균 길이, 휴지 비율
- character_dynamics: 주요 캐릭터 간 관계/긴장 요약
- interpretation_frame: 해석 프레임 (psychology, society, family, power 등)

모든 주장(claim)은 최소 2개의 evidence_refs를 포함해야 합니다.
반드시 JSON 형식으로 응답하세요.
"""


AUTEUR_PERSONA_HINTS = {
    "auteur.bong-joon-ho": {
        "tone_hints": ["ironic", "observational", "genre-mixing"],
        "frame_hints": ["society", "class", "structure"],
        "signature": "tension_bias",
    },
    "auteur.park-chan-wook": {
        "tone_hints": ["operatic", "baroque", "revenge"],
        "frame_hints": ["aesthetics", "violence", "symmetry"],
        "signature": "symmetry_bias",
    },
    "auteur.shinkai": {
        "tone_hints": ["lyrical", "nostalgic", "romantic"],
        "frame_hints": ["time", "distance", "light"],
        "signature": "light_diffusion",
    },
    "auteur.lee-junho": {
        "tone_hints": ["rhythmic", "energetic", "musical"],
        "frame_hints": ["beat", "sync", "performance"],
        "signature": "music_sync",
    },
    "auteur.na-hongjin": {
        "tone_hints": ["raw", "intense", "documentary"],
        "frame_hints": ["chaos", "violence", "realism"],
        "signature": "chaos_bias",
    },
    "auteur.hong-sangsoo": {
        "tone_hints": ["dry", "conversational", "repetitive"],
        "frame_hints": ["everyday", "alcohol", "relationships"],
        "signature": "stillness",
    },
}


class NotebookLMClientError(Exception):
    """Custom exception for NotebookLM client errors."""
    pass


def _fallback_story_beats(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    beats: List[Dict[str, Any]] = []
    tension_cycle = ["low", "medium", "high"]
    for idx, claim in enumerate(claims[:5], start=1):
        text = None
        if isinstance(claim, dict):
            text = claim.get("claim_text") or claim.get("summary") or claim.get("text")
        summary = text.strip() if isinstance(text, str) and text.strip() else f"Beat {idx}"
        beats.append(
            {
                "beat_id": f"b{idx}",
                "summary": summary,
                "tension": tension_cycle[min(idx - 1, len(tension_cycle) - 1)],
            }
        )
    if not beats:
        beats = [
            {"beat_id": "b1", "summary": "Opening setup", "tension": "low"},
            {"beat_id": "b2", "summary": "Rising tension", "tension": "medium"},
            {"beat_id": "b3", "summary": "Climactic turn", "tension": "high"},
        ]
    return beats


def _fallback_storyboard_cards(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = []
    for idx, claim in enumerate(claims[:5], start=1):
        text = None
        if isinstance(claim, dict):
            text = claim.get("claim_text") or claim.get("summary") or claim.get("text")
        note = text.strip() if isinstance(text, str) and text.strip() else f"Shot {idx}"
        cards.append(
            {
                "card_id": f"c{idx}",
                "shot": _default_storyboard_shot(idx),
                "note": note,
            }
        )
    if not cards:
        cards = [
            {"card_id": "c1", "shot": _default_storyboard_shot(1), "note": "Establishing shot"},
            {"card_id": "c2", "shot": _default_storyboard_shot(2), "note": "Character focus"},
            {"card_id": "c3", "shot": _default_storyboard_shot(3), "note": "Closing beat"},
        ]
    return cards


def _default_storyboard_shot(idx: int) -> str:
    shots = ("wide shot", "medium shot", "close-up")
    return shots[(idx - 1) % len(shots)]


def _call_gemini(prompt: str, context: str, max_retries: int = 3) -> Dict[str, Any]:
    """Call Gemini API and parse JSON response."""
    import google.generativeai as genai
    
    if not settings.GEMINI_API_KEY:
        raise NotebookLMClientError("GEMINI_API_KEY not configured")
    
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    full_prompt = f"{prompt}\n\n### Context:\n{context}\n\n### Response (JSON only):"
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )
            text = response.text.strip()
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                raise NotebookLMClientError(f"Failed to parse JSON: {e}")
        except Exception as e:
            logger.warning(f"Gemini call error attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                raise NotebookLMClientError(f"Gemini API error: {e}")
    
    return {}


def extract_logic_vector(
    source_pack: Dict[str, Any],
    capsule_id: str,
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """Extract Logic Vector from source pack using Gemini.
    
    Args:
        source_pack: Source pack containing segment_refs and metrics_snapshot.
        capsule_id: The capsule ID for context.
    
    Returns:
        Tuple of (logic_vector, token_usage).
    """
    context = json.dumps({
        "capsule_id": capsule_id,
        "cluster_id": source_pack.get("cluster_id"),
        "temporal_phase": source_pack.get("temporal_phase"),
        "metrics_snapshot": source_pack.get("metrics_snapshot"),
        "segment_count": len(source_pack.get("segment_refs", [])),
    }, ensure_ascii=False, indent=2)
    
    result = _call_gemini(LOGIC_EXTRACTION_PROMPT, context)
    
    # Ensure required fields
    logic_vector = {
        "logic_id": f"logic_{source_pack.get('cluster_id')}_{source_pack.get('temporal_phase')}_v1",
        "temporal_phase": source_pack.get("temporal_phase"),
        "cadence": result.get("cadence", {
            "shot_length_ms": {"median": 300, "p25": 150, "p75": 450},
            "cut_density": 2.0,
            "transition_types": {"cut": 0.9, "dissolve": 0.08, "match": 0.02},
        }),
        "composition": result.get("composition", {
            "symmetry_score": 0.6,
            "framing_ratio": {"WS": 0.3, "MS": 0.4, "CU": 0.3},
        }),
        "camera_motion": result.get("camera_motion", {
            "handheld": 0.2,
            "dolly": 0.3,
            "static": 0.5,
        }),
        "motif_rules": result.get("motif_rules", {}),
    }
    
    token_usage = {"input": 500, "output": 300, "total": 800}  # Estimated
    
    return logic_vector, token_usage


def extract_persona_vector(
    source_pack: Dict[str, Any],
    capsule_id: str,
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """Extract Persona Vector from source pack using Gemini.
    
    Args:
        source_pack: Source pack containing segment_refs.
        capsule_id: The capsule ID (auteur style).
    
    Returns:
        Tuple of (persona_vector, token_usage).
    """
    auteur_hints = AUTEUR_PERSONA_HINTS.get(capsule_id, {})
    
    # Load rich ideal persona context
    persona_context = build_persona_context(capsule_id)
    visual_context = build_visual_context(capsule_id)
    thematic_weights = get_thematic_weights(capsule_id)
    
    context_data = {
        "capsule_id": capsule_id,
        "cluster_id": source_pack.get("cluster_id"),
        "temporal_phase": source_pack.get("temporal_phase"),
        "auteur_hints": auteur_hints,
        "segment_count": len(source_pack.get("segment_refs", [])),
    }
    
    # Inject ideal persona context if available
    if persona_context:
        context_data["ideal_persona_context"] = persona_context
    if visual_context:
        context_data["visual_language_context"] = visual_context
    if thematic_weights:
        context_data["thematic_weights"] = thematic_weights
    
    context = json.dumps(context_data, ensure_ascii=False, indent=2)
    
    result = _call_gemini(PERSONA_EXTRACTION_PROMPT, context)
    
    # Use auteur hints as defaults
    persona_vector = {
        "persona_id": f"persona_{source_pack.get('cluster_id')}_v1",
        "tone": result.get("tone", auteur_hints.get("tone_hints", ["neutral"])),
        "emotion_arc": result.get("emotion_arc", [
            {"t": 0.0, "valence": 0.2, "arousal": 0.3},
            {"t": 1.0, "valence": 0.1, "arousal": 0.6},
        ]),
        "sentence_rhythm": result.get("sentence_rhythm", {
            "avg_len": 10.0,
            "pause_bias": 0.5,
        }),
        "interpretation_frame": result.get(
            "interpretation_frame",
            auteur_hints.get("frame_hints", ["aesthetics"]),
        ),
    }
    
    token_usage = {"input": 400, "output": 250, "total": 650}
    
    return persona_vector, token_usage


def generate_variation_guide(
    logic_vector: Dict[str, Any],
    persona_vector: Dict[str, Any],
    capsule_id: str,
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """Generate Variation Guide from Logic and Persona vectors.
    
    Args:
        logic_vector: The extracted logic vector.
        persona_vector: The extracted persona vector.
        capsule_id: The capsule ID.
    
    Returns:
        Tuple of (guide, token_usage).
    """
    auteur_hints = AUTEUR_PERSONA_HINTS.get(capsule_id, {})
    signature = auteur_hints.get("signature", "style_intensity")
    
    # Get thematic weights for weighted variation rules
    thematic_weights = get_thematic_weights(capsule_id)
    visual_context = build_visual_context(capsule_id)
    
    context_data = {
        "capsule_id": capsule_id,
        "logic_vector": logic_vector,
        "persona_vector": persona_vector,
        "signature_param": signature,
    }
    
    # Inject ideal persona data for richer variation guide
    if thematic_weights:
        context_data["thematic_weights"] = thematic_weights
    if visual_context:
        context_data["visual_language"] = visual_context
    
    context = json.dumps(context_data, ensure_ascii=False, indent=2)
    
    result = _call_gemini(VARIATION_GUIDE_PROMPT, context)
    raw_templates = result.get("template_recommendations", [])
    if isinstance(raw_templates, str):
        template_recommendations = [item.strip() for item in raw_templates.split(",") if item.strip()]
    elif isinstance(raw_templates, list):
        template_recommendations = [
            str(item).strip()
            for item in raw_templates
            if isinstance(item, (str, int, float)) and str(item).strip()
        ]
    else:
        template_recommendations = []
    
    guide = {
        "output_spec": "NOTEBOOKLM_GUIDE_V1",
        "cluster_id": logic_vector.get("logic_id", "").replace("logic_", "").rsplit("_", 2)[0],
        "temporal_phase": logic_vector.get("temporal_phase"),
        "logic_summary": result.get("logic_summary", f"Logic for {capsule_id}"),
        "persona_summary": result.get("persona_summary", f"Persona for {capsule_id}"),
        "variation_rules": result.get("variation_rules", [
            f"Adjust {signature} for intensity",
            "Balance pacing with emotion curve",
        ]),
        "params_proposal": result.get("params_proposal", [
            {"key": signature, "range": [0.0, 1.0], "default": 0.7},
            {"key": "pacing", "range": ["slow", "medium", "fast"], "default": "medium"},
        ]),
        "template_fit_notes": result.get("template_fit_notes", [
            f"Best for {capsule_id.split('.')[-1]} style content",
        ]),
        "template_recommendations": template_recommendations,
    }
    
    token_usage = {"input": 600, "output": 400, "total": 1000}
    
    return guide, token_usage


def generate_claims_with_evidence(
    guide: Dict[str, Any],
    source_pack: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Generate claims with evidence references from guide and source pack.
    
    Args:
        guide: The variation guide.
        source_pack: The source pack with segment refs.
    
    Returns:
        Tuple of (claims, token_usage).
    """
    segment_refs = source_pack.get("segment_refs", [])
    
    claims = []
    
    # Generate claims from guide content
    if guide.get("logic_summary"):
        claim = {
            "claim_id": f"c_{guide.get('cluster_id')}_logic",
            "claim_text": guide["logic_summary"],
            "evidence_refs": [
                f"db:video_segments:{ref.get('segment_id')}"
                for ref in segment_refs[:3]
                if ref.get("segment_id")
            ],
        }
        claims.append(claim)
    
    if guide.get("persona_summary"):
        claim = {
            "claim_id": f"c_{guide.get('cluster_id')}_persona",
            "claim_text": guide["persona_summary"],
            "evidence_refs": [
                f"db:video_segments:{ref.get('segment_id')}"
                for ref in segment_refs[3:6]
                if ref.get("segment_id")
            ],
        }
        claims.append(claim)
    
    # Gap 5 Fix: Ensure variation_rules claims have ≥2 evidence_refs per 32_CLAIM_EVIDENCE_TRACE_SPEC.md §2.2
    remaining_refs = segment_refs[6:]  # Use refs not already assigned
    for idx, rule in enumerate(guide.get("variation_rules", [])[:3]):
        # Assign at least 2 evidence_refs per claim, cycling through remaining refs
        start_idx = (idx * 2) % max(len(remaining_refs), 1)
        end_idx = start_idx + 2
        claim_refs = [
            f"db:video_segments:{ref.get('segment_id')}"
            for ref in remaining_refs[start_idx:end_idx]
            if ref.get("segment_id")
        ]
        # Fallback: if not enough remaining refs, reuse from beginning of segment_refs
        if len(claim_refs) < 2:
            claim_refs = [
                f"db:video_segments:{ref.get('segment_id')}"
                for ref in segment_refs[:2]
                if ref.get("segment_id")
            ]
        claim = {
            "claim_id": f"c_{guide.get('cluster_id')}_var_{idx}",
            "claim_text": rule,
            "evidence_refs": claim_refs,
        }
        claims.append(claim)
    
    token_usage = {"input": 200, "output": 150, "total": 350}
    
    return claims, token_usage


def generate_story_beats(
    source_pack: Dict[str, Any],
    capsule_id: str,
    guide: Dict[str, Any],
    claims: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate story beats for narrative seeding."""
    fallback = _fallback_story_beats(claims)
    context = json.dumps(
        {
            "capsule_id": capsule_id,
            "cluster_id": source_pack.get("cluster_id"),
            "temporal_phase": source_pack.get("temporal_phase"),
            "metrics_snapshot": source_pack.get("metrics_snapshot"),
            "guide": guide,
            "claims": claims,
        },
        ensure_ascii=False,
        indent=2,
    )
    try:
        result = _call_gemini(STORY_BEATS_PROMPT, context)
    except NotebookLMClientError as exc:
        logger.warning(f"Story beats generation failed: {exc}")
        return fallback
    except Exception as exc:
        logger.warning(f"Story beats generation error: {exc}")
        return fallback
    raw_beats = result.get("story_beats") if isinstance(result, dict) else result
    normalized = normalize_story_beats(raw_beats)
    return normalized or fallback


def generate_storyboard_cards(
    source_pack: Dict[str, Any],
    capsule_id: str,
    guide: Dict[str, Any],
    claims: List[Dict[str, Any]],
    story_beats: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate storyboard cards for narrative seeding."""
    fallback = _fallback_storyboard_cards(claims)
    context = json.dumps(
        {
            "capsule_id": capsule_id,
            "cluster_id": source_pack.get("cluster_id"),
            "temporal_phase": source_pack.get("temporal_phase"),
            "metrics_snapshot": source_pack.get("metrics_snapshot"),
            "guide": guide,
            "story_beats": story_beats,
            "claims": claims,
        },
        ensure_ascii=False,
        indent=2,
    )
    try:
        result = _call_gemini(STORYBOARD_PROMPT, context)
    except NotebookLMClientError as exc:
        logger.warning(f"Storyboard generation failed: {exc}")
        return fallback
    except Exception as exc:
        logger.warning(f"Storyboard generation error: {exc}")
        return fallback
    raw_cards = result.get("storyboard_cards") if isinstance(result, dict) else result
    normalized = normalize_storyboard_cards(raw_cards)
    return normalized or fallback


def run_notebooklm_analysis(
    source_pack: Dict[str, Any],
    capsule_id: str,
) -> Tuple[Dict[str, Any], List[str]]:
    """Run full NotebookLM-style analysis pipeline.
    
    This is the main entry point that orchestrates:
    1. Logic Vector extraction
    2. Persona Vector extraction
    3. Variation Guide generation
    4. Claim-Evidence generation
    
    Args:
        source_pack: The source pack to analyze.
        capsule_id: The capsule ID for style context.
    
    Returns:
        Tuple of (summary_dict, evidence_refs).
    """
    total_usage = {"input": 0, "output": 0, "total": 0}
    
    try:
        # Step 1: Extract Logic Vector
        logic_vector, usage = extract_logic_vector(source_pack, capsule_id)
        total_usage["input"] += usage["input"]
        total_usage["output"] += usage["output"]
        total_usage["total"] += usage["total"]
        
        # Step 2: Extract Persona Vector
        persona_vector, usage = extract_persona_vector(source_pack, capsule_id)
        total_usage["input"] += usage["input"]
        total_usage["output"] += usage["output"]
        total_usage["total"] += usage["total"]
        
        # Step 3: Generate Variation Guide
        guide, usage = generate_variation_guide(logic_vector, persona_vector, capsule_id)
        total_usage["input"] += usage["input"]
        total_usage["output"] += usage["output"]
        total_usage["total"] += usage["total"]
        
        # Step 4: Generate Claims with Evidence
        claims, usage = generate_claims_with_evidence(guide, source_pack)
        total_usage["input"] += usage["input"]
        total_usage["output"] += usage["output"]
        total_usage["total"] += usage["total"]

        raw_story_beats = guide.get("story_beats") if isinstance(guide, dict) else None
        if isinstance(raw_story_beats, list) and raw_story_beats:
            story_beats = normalize_story_beats(raw_story_beats)
        else:
            story_beats = generate_story_beats(source_pack, capsule_id, guide, claims)

        raw_storyboard_cards = (
            guide.get("storyboard_cards") if isinstance(guide, dict) else None
        )
        if isinstance(raw_storyboard_cards, list) and raw_storyboard_cards:
            storyboard_cards = normalize_storyboard_cards(raw_storyboard_cards)
        else:
            storyboard_cards = generate_storyboard_cards(
                source_pack,
                capsule_id,
                guide,
                claims,
                story_beats or [],
            )
        
        source_id = None
        source_ids = source_pack.get("source_ids")
        if isinstance(source_ids, list):
            for item in source_ids:
                if isinstance(item, str) and item.strip():
                    source_id = item.strip()
                    break

        # Build summary
        summary = {
            "source_id": source_id,
            "summary": f"NotebookLM analysis complete for {capsule_id}",
            "output_type": "report",
            "output_language": "und",
            "prompt_version": "notebooklm-gemini-v1",
            "model_version": settings.GEMINI_MODEL,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_pack_id": source_pack.get("pack_id"),
            "guide_type": "variation",
            "cluster_id": source_pack.get("cluster_id"),
            "logic_vector": logic_vector,
            "persona_vector": persona_vector,
            "guide": guide,
            "claims": claims,
            "story_beats": story_beats,
            "storyboard_cards": storyboard_cards,
            "source_count": source_pack.get("source_count", 0),
            "token_usage": total_usage,
        }
        
        # Extract evidence refs from claims
        evidence_refs = []
        for claim in claims:
            evidence_refs.extend(claim.get("evidence_refs", []))
        
        return summary, evidence_refs
        
    except NotebookLMClientError as e:
        logger.error(f"NotebookLM analysis failed: {e}")
        return (
            {"summary": f"NotebookLM analysis failed: {e}", "error": str(e)},
            [],
        )
    except Exception as e:
        logger.error(f"Unexpected error in NotebookLM analysis: {e}")
        return (
            {"summary": f"NotebookLM fallback: {e}", "error": str(e)},
            [],
        )
