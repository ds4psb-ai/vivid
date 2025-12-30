"""Gemini API Client for Canvas Generation.

This module provides a wrapper around the Google Generative AI SDK
for generating storyboards and shot contracts using Gemini 3.0 Pro.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings

logger = logging.getLogger(__name__)

# Lazy-load the SDK to avoid import errors if not installed
_genai = None
_model = None


class GeminiGenerationError(Exception):
    """Custom exception for Gemini generation failures."""
    pass


def _get_genai():
    """Lazy-load google.generativeai module."""
    global _genai
    if _genai is None:
        try:
            import google.generativeai as genai
            _genai = genai
        except ImportError:
            raise GeminiGenerationError(
                "google-generativeai not installed. Run: pip install google-generativeai"
            )
    return _genai


def configure_gemini() -> bool:
    """Configure Gemini API with the API key from settings.
    
    Returns:
        True if configuration successful, False otherwise.
    """
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set, Gemini features disabled")
        return False
    
    try:
        genai = _get_genai()
        genai.configure(api_key=settings.GEMINI_API_KEY)
        logger.info(f"Gemini configured with model: {settings.GEMINI_MODEL}")
        return True
    except Exception as e:
        logger.error(f"Failed to configure Gemini: {e}")
        return False


def _get_model(use_video: bool = False):
    """Get or create the Gemini model instance.
    
    Args:
        use_video: If True, use GEMINI_VIDEO_MODEL (gemini-3.0-pro) for video interpretation.
                   If False, use GEMINI_MODEL (gemini-3.0-flash) for general tasks.
    """
    global _model
    model_name = settings.GEMINI_VIDEO_MODEL if use_video else settings.GEMINI_MODEL
    
    # For video model, always create fresh instance
    if use_video:
        if not configure_gemini():
            raise GeminiGenerationError("Gemini not configured")
        genai = _get_genai()
        return genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.4,  # Lower temp for video interpretation
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 16384,  # Higher for video analysis
                "response_mime_type": "application/json",
            },
        )
    
    # Cache text model
    if _model is None:
        if not configure_gemini():
            raise GeminiGenerationError("Gemini not configured")
        genai = _get_genai()
        _model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",
            },
        )
    return _model


def _get_video_model():
    """Get Gemini model instance specifically for video file interpretation.
    
    Uses GEMINI_VIDEO_MODEL (gemini-3.0-pro) which has advanced multimodal capabilities.
    """
    return _get_model(use_video=True)


def _call_with_retry(
    prompt: str,
    system_instruction: str,
    max_retries: int = 3,
    initial_delay: float = 1.0,
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """Call Gemini API with exponential backoff retry.
    
    Args:
        prompt: User prompt
        system_instruction: System instruction for the model
        max_retries: Maximum retry attempts
        initial_delay: Initial delay in seconds
        
    Returns:
        Tuple of (parsed_response, token_usage)
    """
    model = _get_model()
    delay = initial_delay
    last_error = None
    
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            
            # Create a new model instance with system instruction
            genai = _get_genai()
            configured_model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                system_instruction=system_instruction,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                    "response_mime_type": "application/json",
                },
            )
            
            response = configured_model.generate_content(prompt)
            elapsed = time.time() - start_time
            
            # Parse JSON response
            text = response.text.strip()
            parsed = json.loads(text)
            
            # Extract token usage
            usage = {
                "input": getattr(response.usage_metadata, 'prompt_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
                "output": getattr(response.usage_metadata, 'candidates_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
            }
            usage["total"] = usage["input"] + usage["output"]
            
            logger.info(f"Gemini call completed in {elapsed:.2f}s, tokens: {usage['total']}")
            return parsed, usage
            
        except json.JSONDecodeError as e:
            logger.warning(f"Gemini returned invalid JSON (attempt {attempt + 1}): {e}")
            last_error = e
        except Exception as e:
            logger.warning(f"Gemini API error (attempt {attempt + 1}): {e}")
            last_error = e
        
        if attempt < max_retries - 1:
            time.sleep(delay)
            delay *= 2
    
    raise GeminiGenerationError(f"Gemini API failed after {max_retries} attempts: {last_error}")


# ─────────────────────────────────────────────────────────────────────────────
# Auteur Style Prompts
# ─────────────────────────────────────────────────────────────────────────────

AUTEUR_SYSTEM_PROMPTS = {
    "auteur.bong-joon-ho": """You are a cinematic director assistant specializing in Bong Joon-ho's visual style.
Key characteristics:
- Symmetrical framing with class divide motifs
- Staircase and vertical blocking
- Deep focus with layered foreground/background
- Cool neutral palette with occasional warm accents
- Slow zooms and controlled camera movements
- Social commentary through visual metaphor""",

    "auteur.na-hongjin": """You are a cinematic director assistant specializing in Na Hong-jin's visual style.
Key characteristics:
- Chaotic, documentary-style handheld camera
- Dark, desaturated color grading
- Long takes building unbearable tension
- Rain and nighttime scenes
- Visceral violence depicted unflinchingly
- Rural Korean landscapes as horror backdrop""",

    "auteur.hong-sangsoo": """You are a cinematic director assistant specializing in Hong Sang-soo's visual style.
Key characteristics:
- Static wide shots with minimal movement
- Sudden zoom-ins for emphasis
- Soft, naturalistic lighting
- Conversational scenes at tables (soju drinking)
- Repetitive narrative structures
- Minimalist, observational approach""",
}

DEFAULT_SYSTEM_PROMPT = """You are a professional cinematic storyboard artist.
Create detailed, production-ready storyboards with:
- Clear shot descriptions
- Camera movements
- Mood and lighting notes
- Dialogue placement
Output must be valid JSON."""


def _get_auteur_prompt(capsule_id: str) -> str:
    """Get auteur-specific system prompt."""
    for key, prompt in AUTEUR_SYSTEM_PROMPTS.items():
        if key in capsule_id:
            return prompt
    return DEFAULT_SYSTEM_PROMPT


# ─────────────────────────────────────────────────────────────────────────────
# Generation Functions
# ─────────────────────────────────────────────────────────────────────────────

def generate_storyboard_with_gemini(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    capsule_id: str = "",
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Generate storyboard cards using Gemini.
    
    Args:
        inputs: Capsule inputs (scene_summary, duration_sec, emotion_curve)
        params: Capsule params (auteur style settings)
        capsule_id: Capsule identifier for auteur detection
        
    Returns:
        Tuple of (storyboard_cards, token_usage)
    """
    scene_summary = inputs.get("scene_summary", "A dramatic scene unfolds")
    duration = inputs.get("duration_sec", 60)
    emotion_curve = inputs.get("emotion_curve", [0.5, 0.6, 0.7, 0.8, 0.6])
    
    system_prompt = _get_auteur_prompt(capsule_id)
    
    user_prompt = f"""Generate a storyboard for the following scene:

Scene Summary: {scene_summary}
Duration: {duration} seconds
Emotion Curve: {emotion_curve}
Style Parameters: {json.dumps(params, ensure_ascii=False)}

Create 4-6 storyboard cards. Output as JSON array:
{{
  "storyboard_cards": [
    {{
      "card_index": 1,
      "title": "Opening Shot",
      "description": "Wide establishing shot of...",
      "duration_sec": 5,
      "camera_movement": "slow push in",
      "mood": "contemplative",
      "dialogue": null,
      "sound_notes": "ambient city noise"
    }}
  ]
}}"""

    result, usage = _call_with_retry(user_prompt, system_prompt)
    cards = result.get("storyboard_cards", [])
    
    # Validate and normalize card structure
    normalized = []
    for i, card in enumerate(cards):
        normalized.append({
            "card_index": card.get("card_index", i + 1),
            "title": card.get("title", f"Shot {i + 1}"),
            "description": card.get("description", ""),
            "duration_sec": card.get("duration_sec", 5),
            "camera_movement": card.get("camera_movement", "static"),
            "mood": card.get("mood", "neutral"),
            "dialogue": card.get("dialogue"),
            "sound_notes": card.get("sound_notes"),
        })
    
    return normalized, usage


def generate_shot_contracts_with_gemini(
    inputs: Dict[str, Any],
    storyboard: List[Dict[str, Any]],
    params: Dict[str, Any],
    capsule_id: str = "",
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Generate shot contracts from storyboard using Gemini.
    
    Args:
        inputs: Capsule inputs
        storyboard: Storyboard cards
        params: Style parameters
        capsule_id: Capsule identifier
        
    Returns:
        Tuple of (shot_contracts, token_usage)
    """
    system_prompt = _get_auteur_prompt(capsule_id)
    
    user_prompt = f"""Convert these storyboard cards into production-ready shot contracts:

Storyboard Cards:
{json.dumps(storyboard, indent=2, ensure_ascii=False)}

Style Parameters: {json.dumps(params, ensure_ascii=False)}

Generate shot contracts with detailed video generation prompts. Output as JSON:
{{
  "shot_contracts": [
    {{
      "shot_id": "shot_001",
      "storyboard_ref": 1,
      "shot_type": "wide",
      "duration_sec": 5,
      "camera": {{
        "movement": "slow push in",
        "angle": "eye level",
        "lens": "35mm"
      }},
      "lighting": {{
        "key": "natural window light",
        "mood": "soft, contemplative"
      }},
      "composition": "rule of thirds, subject left",
      "prompt": "Cinematic wide shot of a person standing by a rain-streaked window, soft natural light, contemplative mood, 35mm lens, slow push in, film grain",
      "negative_prompt": "cartoon, anime, low quality, blurry"
    }}
  ]
}}"""

    result, usage = _call_with_retry(user_prompt, system_prompt)
    contracts = result.get("shot_contracts", [])
    
    # Validate and normalize
    normalized = []
    for i, shot in enumerate(contracts):
        shot_id = shot.get("shot_id", f"shot_{i+1:03d}")
        normalized.append({
            "shot_id": shot_id,
            "storyboard_ref": shot.get("storyboard_ref", i + 1),
            "shot_type": shot.get("shot_type", "medium"),
            "duration_sec": shot.get("duration_sec", 5),
            "camera": shot.get("camera", {}),
            "lighting": shot.get("lighting", {}),
            "composition": shot.get("composition", ""),
            "prompt": shot.get("prompt", ""),
            "negative_prompt": shot.get("negative_prompt", ""),
        })
    
    return normalized, usage


# ─────────────────────────────────────────────────────────────────────────────
# DirectorPack-Aware Shot Contract Generation (Multi-Scene Consistency)
# ─────────────────────────────────────────────────────────────────────────────

def _director_pack_to_prompt_rules(director_pack: Dict[str, Any]) -> str:
    """Convert DirectorPack to prompt rules for consistent shot generation.
    
    Args:
        director_pack: DirectorPack dict with dna_invariants, forbidden_mutations, etc.
        
    Returns:
        Formatted string of rules to inject into system prompt
    """
    meta = director_pack.get("meta", {})
    pack_name = meta.get("pattern_id", "unknown").split(".")[-1].replace("-", " ").title()
    
    lines = [
        f"# 🧬 DirectorPack: {pack_name}",
        f"버전: {meta.get('version', '1.0')} | 규칙 수: {meta.get('invariant_count', 0)}",
        "",
        "## ⚡ 핵심 규칙 (DNA Invariants) - 모든 샷에 반드시 적용",
        "각 샷의 프롬프트에 아래 규칙들을 명시적으로 반영하세요.",
        ""
    ]
    
    # DNA Invariants - detailed format
    dna_invariants = director_pack.get("dna_invariants", [])
    critical_rules = [inv for inv in dna_invariants if inv.get("priority") == "critical"]
    high_rules = [inv for inv in dna_invariants if inv.get("priority") == "high"]
    other_rules = [inv for inv in dna_invariants if inv.get("priority") not in ("critical", "high")]
    
    def format_invariant(inv, index):
        """Format a single invariant with full details."""
        rule_type = inv.get("rule_type", "general")
        name = inv.get("name", "")
        description = inv.get("description", "")
        condition = inv.get("condition", "")
        spec = inv.get("spec", {})
        priority = inv.get("priority", "medium")
        confidence = inv.get("confidence", 0.8)
        
        priority_labels = {
            "critical": "🔴 CRITICAL",
            "high": "🟠 HIGH",
            "medium": "🟡 MEDIUM",
            "low": "⚪ LOW"
        }
        
        type_labels = {
            "composition": "🎯 구도",
            "timing": "⏱️ 타이밍",
            "audio": "🔊 오디오",
            "lighting": "💡 조명",
            "color": "🎨 색감",
            "camera": "📹 카메라",
            "engagement": "📊 참여도",
            "narrative": "📖 서사",
            "technical": "⚙️ 기술"
        }
        
        result_lines = [
            f"### 규칙 {index}: {name}",
            f"- **유형**: {type_labels.get(rule_type, f'📌 {rule_type}')}",
            f"- **우선순위**: {priority_labels.get(priority, priority)}",
            f"- **설명**: {description}",
        ]
        
        # Add condition and spec
        if condition and spec:
            operator = spec.get("operator", "=")
            value = spec.get("value", "")
            unit = spec.get("unit", "")
            result_lines.append(f"- **조건**: `{condition}` {operator} {value}{unit}")
        
        # Add explicit guidance for prompt generation
        coach_line = inv.get("coach_line_ko") or inv.get("coach_line")
        if coach_line:
            result_lines.append(f"- **프롬프트 지침**: \"{coach_line}\"")
        
        # Add example keywords to include
        if rule_type == "composition":
            if "center" in condition.lower() or "중앙" in name:
                result_lines.append("- **포함할 키워드**: 중앙, 대칭, center, symmetric")
            elif "vertical" in condition.lower() or "수직" in name:
                result_lines.append("- **포함할 키워드**: 수직, 위아래, 계단, 층간, vertical, layered")
        elif rule_type == "timing":
            result_lines.append(f"- **목표 값**: {spec.get('operator', '')} {spec.get('value', '')} (신뢰도: {confidence:.0%})")
        
        return "\n".join(result_lines)
    
    # Critical rules first
    if critical_rules:
        lines.append("### 🔴 CRITICAL 규칙 (필수 준수)")
        for i, inv in enumerate(critical_rules, 1):
            lines.append(format_invariant(inv, i))
            lines.append("")
    
    # High priority rules
    if high_rules:
        lines.append("### 🟠 HIGH 규칙 (강력 권장)")
        for i, inv in enumerate(high_rules, 1 + len(critical_rules)):
            lines.append(format_invariant(inv, i))
            lines.append("")
    
    # Other rules
    if other_rules:
        lines.append("### 기타 규칙")
        for i, inv in enumerate(other_rules, 1 + len(critical_rules) + len(high_rules)):
            lines.append(format_invariant(inv, i))
            lines.append("")
    
    # Forbidden Mutations - explicit negative constraints
    forbidden = director_pack.get("forbidden_mutations", [])
    if forbidden:
        lines.extend([
            "",
            "## 🚫 금지 규칙 (Forbidden Mutations) - 절대 사용 금지",
            "아래 요소들은 프롬프트에 포함하지 마세요:",
            ""
        ])
        for fm in forbidden:
            severity = fm.get("severity", "major")
            severity_icon = {"critical": "🚫🚫", "major": "🚫", "minor": "⚠️"}.get(severity, "⚠️")
            name = fm.get("name", "")
            desc = fm.get("description", "")
            condition = fm.get("forbidden_condition", "")
            coach = fm.get("coach_line_ko") or fm.get("coach_line", "")
            
            lines.append(f"- {severity_icon} **{name}**: {desc}")
            if condition:
                lines.append(f"  - 금지 조건: `{condition}`")
            if coach:
                lines.append(f"  - 코칭: \"{coach}\"")
    
    # Mutation Slots - allowed variations
    slots = director_pack.get("mutation_slots", [])
    if slots:
        lines.extend([
            "",
            "## 🎛️ 변경 가능 요소 (Mutation Slots)",
            "아래 요소들은 씬에 따라 조정 가능합니다:",
            ""
        ])
        for slot in slots:
            name = slot.get("name", "")
            slot_type = slot.get("slot_type", "")
            allowed = slot.get("allowed_values", [])
            allowed_range = slot.get("allowed_range", [])
            default = slot.get("default_value")
            desc = slot.get("description", "")
            
            if allowed:
                values_str = " | ".join(f"`{v}`" for v in allowed)
                lines.append(f"- **{name}** ({slot_type}): {values_str}")
                lines.append(f"  - 기본값: `{default}` | {desc}")
            elif allowed_range:
                lines.append(f"- **{name}** ({slot_type}): {allowed_range[0]} ~ {allowed_range[1]}")
                lines.append(f"  - 기본값: `{default}` | {desc}")
    
    # Add compliance reminder
    lines.extend([
        "",
        "---",
        "## 📋 준수 체크리스트",
        "각 샷 생성 시 아래를 확인하세요:",
        "1. CRITICAL 규칙의 키워드가 프롬프트에 포함되어 있는가?",
        "2. 금지된 요소가 프롬프트에 없는가?",
        "3. 타이밍 규칙이 숫자로 명시되어 있는가?",
        ""
    ])
    
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# NarrativeArc & HookVariant Prompt Injection (Phase 2 + Phase 4 Integration)
# ─────────────────────────────────────────────────────────────────────────────

def _narrative_arc_to_prompt(narrative_arc: Dict[str, Any]) -> str:
    """Convert NarrativeArc to prompt instructions for story-aware shot generation.
    
    Args:
        narrative_arc: NarrativeArc dict with arc_type, sequences, emotion curve, etc.
        
    Returns:
        Formatted string of narrative rules to inject into system prompt
    """
    if not narrative_arc:
        return ""
    
    lines = [
        "",
        "# 📖 서사 구조 (Narrative Arc)",
        "",
        f"**Arc Type**: {narrative_arc.get('arc_type', '3-act')}",
        f"**Duration**: {narrative_arc.get('duration_sec', 60)}초",
        f"**Longform**: {'예' if narrative_arc.get('is_longform') else '아니오'}",
        "",
    ]
    
    # Emotion curve
    lines.extend([
        "## 감정 곡선 (Emotion Curve)",
        f"- 시작: {narrative_arc.get('emotion_start', 'neutral')}",
        f"- 피크: {narrative_arc.get('emotion_peak', 'excited')}",
        f"- 마무리: {narrative_arc.get('emotion_end', 'satisfied')}",
        "",
    ])
    
    # Dissonance design (viral key)
    if narrative_arc.get('dissonance_type'):
        lines.extend([
            "## 🎭 부조화 설계 (Dissonance Design) - 바이럴 핵심!",
            f"- 유형: {narrative_arc.get('dissonance_type')}",
            f"- 익숙한 요소: {narrative_arc.get('familiar_element', 'N/A')}",
            f"- 낯선 요소: {narrative_arc.get('unexpected_element', 'N/A')}",
            "",
            "→ 첫 샷에서 이 부조화를 시각적으로 즉시 드러내세요!",
            "",
        ])
    
    # Sequences (longform)
    sequences = narrative_arc.get('sequences', [])
    if sequences:
        lines.extend([
            "## 시퀀스 구조 (Sequences)",
        ])
        for seq in sequences:
            hook_icon = "🔥" if seq.get('hook_recommended', True) else "⏸️"
            lines.append(
                f"- {hook_icon} **{seq.get('name', 'Unnamed')}** ({seq.get('t_start', 0)}s - {seq.get('t_end', 30)}s): "
                f"{seq.get('phase', 'build')} | Hook: {seq.get('hook_intensity', 'medium')}"
            )
        lines.append("")
    
    # Shot roles
    shot_roles = narrative_arc.get('shot_roles', [])
    if shot_roles:
        lines.extend([
            "## 샷별 서사 역할 (Shot Narrative Roles)",
        ])
        for role in shot_roles[:10]:  # Limit to prevent prompt overflow
            phase = role.get('phase', 'build')
            hook_marker = "🎯 HOOK!" if role.get('hook_required') else ""
            expectation = role.get('expectation_created', '')
            exp_text = f" → 기대감: '{expectation}'" if expectation else ""
            lines.append(f"- {role.get('shot_id', 'shot')}: {phase} {hook_marker}{exp_text}")
        lines.append("")
    
    # Generation instructions
    lines.extend([
        "## 📌 서사 기반 생성 지침",
        "1. **Hook 샷 (phase=hook)**: 1.5초 내 시선 잡기! 부조화 요소 즉시 보여주기",
        "2. **Build 샷**: 긴장감 점진적 고조, 기대감 생성",
        "3. **Turn 샷**: 반전 또는 전환점, 예상을 뒤집기",
        "4. **Payoff 샷**: 앞서 만든 기대감 충족",
        "5. **Climax 샷**: 최고조의 감정/액션",
        "",
    ])
    
    return "\n".join(lines)


def _hook_variant_to_prompt(hook_variant: Dict[str, Any]) -> str:
    """Convert HookVariant to prompt modifiers for the first shot(s).
    
    Args:
        hook_variant: HookVariant dict with style, intensity, prompt_prefix, etc.
        
    Returns:
        Formatted string to modify hook shot generation
    """
    if not hook_variant:
        return ""
    
    style = hook_variant.get('style', 'curiosity')
    intensity = hook_variant.get('intensity', 'medium')
    prompt_prefix = hook_variant.get('prompt_prefix', '')
    keywords = hook_variant.get('prompt_keywords', [])
    visual_direction = hook_variant.get('visual_direction', '')
    coach_tip = hook_variant.get('coach_tip_ko') or hook_variant.get('coach_tip', '')
    
    # Intensity modifiers
    intensity_modifiers = {
        'soft': '자연스럽게, 부드럽게',
        'medium': '명확하게',
        'strong': '강렬하게, 집중적으로',
        'explosive': '폭발적으로, 충격적으로, 즉각적으로',
    }
    
    # Style-specific directions
    style_directions = {
        'shock': 'Start with the most visually shocking moment. No buildup, immediate impact.',
        'curiosity': 'Show just enough to intrigue, hide the full picture. Create mystery.',
        'emotion': 'Lead with genuine emotion. Close-up on face, eyes, expression.',
        'question': 'Open with a visual question. What? Why? How did this happen?',
        'paradox': 'Juxtapose familiar with unexpected. Create cognitive dissonance.',
        'tease': 'Flash-forward to the climax first, then rewind. "How did we get here?"',
        'action': 'Drop into action immediately. Movement, energy, no warmup.',
        'calm': 'Establish atmosphere slowly. Wide shot, ambient mood.',
    }
    
    lines = [
        "",
        "# 🎬 훅 스타일 지시 (Hook Variant Instructions)",
        "",
        f"**스타일**: {style.upper()} ({intensity})",
        f"**강도**: {intensity_modifiers.get(intensity, '명확하게')}",
        "",
        f"## 훅 연출 방향",
        f"{style_directions.get(style, '')}",
        "",
    ]
    
    if prompt_prefix:
        lines.extend([
            f"## 프롬프트 프리픽스 (첫 샷에 적용)",
            f'"{prompt_prefix}"',
            "",
        ])
    
    if keywords:
        lines.extend([
            f"## 포함할 키워드",
            f"첫 샷 프롬프트에 반드시 포함: {', '.join(keywords)}",
            "",
        ])
    
    if visual_direction:
        lines.extend([
            f"## 시각적 연출",
            visual_direction,
            "",
        ])
    
    if coach_tip:
        lines.extend([
            f"## 💡 코칭 팁",
            coach_tip,
            "",
        ])
    
    lines.extend([
        "## ⚠️ 중요",
        "위 훅 스타일을 **첫 번째 샷**과 **각 시퀀스 시작 샷**에 적용하세요!",
        "Hook이 아닌 중간 샷에는 적용하지 마세요.",
        "",
    ])
    
    return "\n".join(lines)


def _apply_hook_to_shot_prompt(
    shot_prompt: str,
    hook_variant: Dict[str, Any],
    is_hook_shot: bool,
) -> str:
    """Apply hook variant modifiers to a shot prompt.
    
    Args:
        shot_prompt: Original shot prompt
        hook_variant: HookVariant dict
        is_hook_shot: Whether this shot is a hook shot
        
    Returns:
        Modified prompt with hook style applied
    """
    if not hook_variant or not is_hook_shot:
        return shot_prompt
    
    prompt_prefix = hook_variant.get('prompt_prefix', '')
    keywords = hook_variant.get('prompt_keywords', [])
    
    # Add prefix
    if prompt_prefix and prompt_prefix not in shot_prompt:
        shot_prompt = f"{prompt_prefix} {shot_prompt}"
    
    # Add keywords if not present
    for kw in keywords:
        if kw.lower() not in shot_prompt.lower():
            shot_prompt = f"{shot_prompt}, {kw}"
    
    return shot_prompt


def generate_shot_contracts_with_dna(
    inputs: Dict[str, Any],
    storyboard: List[Dict[str, Any]],
    params: Dict[str, Any],
    director_pack: Optional[Dict[str, Any]] = None,
    scene_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
    narrative_arc: Optional[Dict[str, Any]] = None,
    hook_variant: Optional[Dict[str, Any]] = None,
    capsule_id: str = "",
    fallback_on_error: bool = True,
    max_retries: int = 3,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Generate shot contracts with DirectorPack DNA, NarrativeArc, and HookVariant.
    
    This function injects DirectorPack rules, narrative structure, and hook style
    into the generation prompt for Story-First + DNA consistency.
    
    Args:
        inputs: Capsule inputs
        storyboard: Storyboard cards
        params: Style parameters
        director_pack: DirectorPack dict with dna_invariants, forbidden_mutations, etc.
        scene_overrides: Optional per-scene overrides {scene_id: {custom_prompt, overridden_invariants}}
        narrative_arc: NarrativeArc dict with arc_type, sequences, emotion curve, dissonance
        hook_variant: HookVariant dict with style, intensity, prompt modifiers
        capsule_id: Capsule identifier for auteur detection
        fallback_on_error: If True, generate without DNA on failure
        max_retries: Maximum retry attempts for rate limiting
        
    Returns:
        Tuple of (shot_contracts, token_usage)
        
    Raises:
        GeminiGenerationError: If generation fails and fallback is disabled
    """
    start_time = time.time()
    token_usage = {"input": 0, "output": 0}
    
    # Build base system prompt
    base_prompt = _get_auteur_prompt(capsule_id)
    
    # Add DNA rules if provided
    dna_rules = ""
    dna_applied = False
    invariant_count = 0
    forbidden_count = 0
    
    # Add narrative arc rules
    narrative_rules = ""
    narrative_applied = False
    
    # Add hook variant rules
    hook_rules = ""
    hook_applied = False
    
    if director_pack:
        try:
            dna_rules = _director_pack_to_prompt_rules(director_pack)
            invariant_count = len(director_pack.get('dna_invariants', []))
            forbidden_count = len(director_pack.get('forbidden_mutations', []))
            dna_applied = True
            logger.info(
                f"[DNA] Injecting DirectorPack: pack_id={director_pack.get('meta', {}).get('pack_id', 'unknown')}, "
                f"invariants={invariant_count}, forbidden={forbidden_count}, "
                f"prompt_length={len(dna_rules)} chars"
            )
        except Exception as e:
            logger.warning(f"[DNA] Failed to generate DNA rules: {e}. Continuing without DNA.")
            dna_rules = ""
    
    # Add scene-specific overrides
    override_prompt = ""
    override_count = 0
    if scene_overrides:
        try:
            override_lines = ["\n## 씬별 특별 지시 (Scene Overrides)"]
            for scene_id, override in scene_overrides.items():
                if not override.get("enabled", True):
                    continue
                custom_prompt = override.get("custom_prompt")
                if custom_prompt:
                    override_lines.append(f"\n### {scene_id}")
                    override_lines.append(custom_prompt)
                    override_count += 1
                
                # Apply overridden invariants
                overridden = override.get("overridden_invariants", {})
                if overridden:
                    for rule_id, new_spec in overridden.items():
                        if new_spec and new_spec.get("spec"):
                            override_lines.append(f"- {rule_id}: 수정된 값 = {new_spec['spec'].get('value')}")
            
            override_prompt = "\n".join(override_lines)
            if override_count > 0:
                logger.info(f"[DNA] Applied {override_count} scene overrides")
        except Exception as e:
            logger.warning(f"[DNA] Failed to apply scene overrides: {e}")
    
    # Add narrative arc rules (Story-First)
    if narrative_arc:
        try:
            narrative_rules = _narrative_arc_to_prompt(narrative_arc)
            narrative_applied = True
            logger.info(
                f"[NARRATIVE] Injecting NarrativeArc: arc_type={narrative_arc.get('arc_type', 'unknown')}, "
                f"sequences={len(narrative_arc.get('sequences', []))}, "
                f"dissonance={narrative_arc.get('dissonance_type', 'none')}"
            )
        except Exception as e:
            logger.warning(f"[NARRATIVE] Failed to generate narrative rules: {e}")
            narrative_rules = ""
    
    # Add hook variant rules (Hook A/B Testing)
    if hook_variant:
        try:
            hook_rules = _hook_variant_to_prompt(hook_variant)
            hook_applied = True
            logger.info(
                f"[HOOK] Injecting HookVariant: style={hook_variant.get('style', 'unknown')}, "
                f"intensity={hook_variant.get('intensity', 'medium')}"
            )
        except Exception as e:
            logger.warning(f"[HOOK] Failed to generate hook rules: {e}")
            hook_rules = ""

    
    # Compose final system prompt
    system_prompt = f"""{base_prompt}

{dna_rules}

{narrative_rules}

{hook_rules}

{override_prompt}

위 규칙을 모든 샷에 일관되게 적용하세요. 
DNA 규칙 위반 시 해당 샷은 품질 검증에서 탈락합니다.
서사 구조(Narrative Arc)에 따라 각 샷의 역할을 명확히 하세요.
첫 샷과 시퀀스 시작 샷에는 반드시 지정된 Hook 스타일을 적용하세요.
"""
    
    user_prompt = f"""Convert these storyboard cards into production-ready shot contracts:

Storyboard Cards:
{json.dumps(storyboard, indent=2, ensure_ascii=False)}

Style Parameters: {json.dumps(params, ensure_ascii=False)}

Generate shot contracts that STRICTLY follow:
1. DNA Invariants (visual style rules)
2. Forbidden Mutations (never do these)
3. Narrative Arc (story structure) 
4. Hook Style (for first shot and sequence starts)

Each shot's prompt must incorporate the consistency rules and narrative role.

Output as JSON:
{{
  "shot_contracts": [
    {{
      "shot_id": "shot_001",
      "storyboard_ref": 1,
      "shot_type": "wide",
      "duration_sec": 5,
      "narrative_role": {{
        "phase": "hook",
        "hook_required": true,
        "target_emotion": "curiosity",
        "expectation_created": "Why is this person here?"
      }},
      "camera": {{
        "movement": "slow push in",
        "angle": "eye level",
        "lens": "35mm"
      }},
      "lighting": {{
        "key": "natural window light",
        "mood": "soft, contemplative"
      }},
      "composition": "rule of thirds, subject left",
      "prompt": "Cinematic wide shot with [hook style] opening...",
      "negative_prompt": "cartoon, anime, low quality, blurry, [forbidden elements]",
      "dna_compliance": {{
        "applied_rules": ["hook_timing_1_5s", "center_composition"],
        "confidence": 0.95
      }},
      "hook_applied": true
    }}
  ]
}}"""

    # Attempt generation with retry logic
    last_error = None
    for attempt in range(max_retries):
        try:
            result, usage = _call_with_retry(user_prompt, system_prompt)
            token_usage = usage
            contracts = result.get("shot_contracts", [])
            
            if not contracts:
                raise GeminiGenerationError("No shot contracts in response")
            
            # Validate and normalize with DNA + Narrative compliance tracking
            normalized = []
            for i, shot in enumerate(contracts):
                shot_id = shot.get("shot_id", f"shot_{i+1:03d}")
                
                # Determine if this is a hook shot
                narrative_role = shot.get("narrative_role", {})
                is_hook_shot = (
                    narrative_role.get("hook_required", False) or 
                    narrative_role.get("phase") == "hook" or
                    i == 0  # First shot is always treated as hook
                )
                
                # Apply hook variant to prompt if needed
                original_prompt = shot.get("prompt", "")
                final_prompt = _apply_hook_to_shot_prompt(
                    original_prompt, hook_variant, is_hook_shot
                ) if hook_variant else original_prompt
                
                normalized.append({
                    "shot_id": shot_id,
                    "storyboard_ref": shot.get("storyboard_ref", i + 1),
                    "shot_type": shot.get("shot_type", "medium"),
                    "duration_sec": shot.get("duration_sec", 5),
                    "narrative_role": {
                        "phase": narrative_role.get("phase", "build"),
                        "hook_required": narrative_role.get("hook_required", i == 0),
                        "target_emotion": narrative_role.get("target_emotion", ""),
                        "expectation_created": narrative_role.get("expectation_created", ""),
                        "expectation_fulfilled": narrative_role.get("expectation_fulfilled", ""),
                    },
                    "camera": shot.get("camera", {}),
                    "lighting": shot.get("lighting", {}),
                    "composition": shot.get("composition", ""),
                    "prompt": final_prompt,
                    "negative_prompt": shot.get("negative_prompt", ""),
                    "dna_compliance": shot.get("dna_compliance", {
                        "applied_rules": [],
                        "confidence": 0.0,
                    }),
                    "hook_applied": is_hook_shot and hook_applied,
                    "_meta": {
                        "dna_applied": dna_applied,
                        "narrative_applied": narrative_applied,
                        "hook_applied": hook_applied,
                        "hook_style": hook_variant.get("style") if hook_variant else None,
                        "pack_id": director_pack.get("meta", {}).get("pack_id") if director_pack else None,
                        "override_count": override_count,
                    }
                })
            
            elapsed = time.time() - start_time
            hook_count = sum(1 for s in normalized if s.get("hook_applied"))
            logger.info(
                f"[GENERATION] Generated {len(normalized)} shots in {elapsed:.2f}s | "
                f"DNA: {dna_applied} | Narrative: {narrative_applied} | "
                f"Hook: {hook_applied} (style={hook_variant.get('style') if hook_variant else 'none'}, applied_to={hook_count} shots) | "
                f"Tokens: {token_usage.get('input', 0)}+{token_usage.get('output', 0)}"
            )
            return normalized, token_usage
            
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            
            # Check for rate limiting
            if "429" in error_str or "rate" in error_str or "quota" in error_str:
                wait_time = (attempt + 1) * 5  # 5s, 10s, 15s
                logger.warning(f"[DNA] Rate limited (attempt {attempt+1}/{max_retries}), waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            # Check for context length issues
            if "context" in error_str or "length" in error_str or "token" in error_str:
                logger.warning(f"[DNA] Context too long, trying without DNA rules...")
                dna_rules = ""
                dna_applied = False
                continue
            
            # Other errors - log and possibly retry
            logger.error(f"[DNA] Generation failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            break
    
    # All retries failed
    if fallback_on_error:
        logger.warning(f"[DNA] All retries failed, falling back to generation without DNA")
        try:
            # Fallback: generate without DNA
            basic_prompt = f"""Convert storyboard to shot contracts:
{json.dumps(storyboard[:5], indent=2, ensure_ascii=False)}

Output JSON with shot_contracts array."""
            
            result, usage = _call_with_retry(basic_prompt, base_prompt)
            contracts = result.get("shot_contracts", [])
            
            normalized = [{
                "shot_id": shot.get("shot_id", f"shot_{i+1:03d}"),
                "prompt": shot.get("prompt", ""),
                "dna_compliance": {"applied_rules": [], "confidence": 0.0, "fallback": True},
            } for i, shot in enumerate(contracts)]
            
            logger.info(f"[DNA] Fallback generated {len(normalized)} shots (no DNA)")
            return normalized, usage
            
        except Exception as fallback_error:
            logger.error(f"[DNA] Fallback also failed: {fallback_error}")
            raise GeminiGenerationError(f"Generation failed: {last_error}") from last_error
    else:
        raise GeminiGenerationError(f"Generation failed after {max_retries} attempts: {last_error}")


def test_connection() -> Dict[str, Any]:
    """Test Gemini API connection.
    
    Returns:
        Dict with status and model info
    """
    if not settings.GEMINI_ENABLED:
        return {"status": "disabled", "message": "GEMINI_ENABLED is False"}
    
    if not settings.GEMINI_API_KEY:
        return {"status": "error", "message": "GEMINI_API_KEY not set"}
    
    try:
        configure_gemini()
        genai = _get_genai()
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = model.generate_content("Say 'OK' if you can receive this message.")
        return {
            "status": "ok",
            "model": settings.GEMINI_MODEL,
            "video_model": settings.GEMINI_VIDEO_MODEL,
            "response": response.text[:100],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# Video Interpretation (uses gemini-3.0-pro)
# ─────────────────────────────────────────────────────────────────────────────

def interpret_video_file(
    video_file_path: str,
    prompt: str = "Analyze this video and extract visual structure, scene changes, and key moments.",
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """Interpret a video file using Gemini 3.0 Pro.
    
    This function uses GEMINI_VIDEO_MODEL (gemini-3.0-pro) for advanced video understanding.
    
    Args:
        video_file_path: Path to the video file to analyze.
        prompt: Analysis prompt to guide the interpretation.
        
    Returns:
        Tuple of (analysis_result, token_usage)
        
    Note:
        This function uses gemini-3.0-pro which has enhanced multimodal capabilities
        specifically for video understanding tasks.
    """
    if not settings.GEMINI_ENABLED or not settings.GEMINI_API_KEY:
        raise GeminiGenerationError("Gemini not enabled or API key not set")
    
    configure_gemini()
    genai = _get_genai()
    
    # Use video model (gemini-3.0-pro)
    video_model = _get_video_model()
    logger.info(f"Using video model: {settings.GEMINI_VIDEO_MODEL} for video interpretation")
    
    try:
        # Upload video file
        video_file = genai.upload_file(path=video_file_path)
        
        # Wait for file processing
        import time
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
        
        if video_file.state.name == "FAILED":
            raise GeminiGenerationError(f"Video processing failed: {video_file.state.name}")
        
        # Generate analysis with video model
        response = video_model.generate_content([video_file, prompt])
        
        # Parse response
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError:
            result = {"analysis": response.text, "raw": True}
        
        # Token usage
        usage = {
            "input": getattr(response.usage_metadata, 'prompt_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
            "output": getattr(response.usage_metadata, 'candidates_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
        }
        usage["total"] = usage["input"] + usage["output"]
        
        return result, usage
        
    except Exception as e:
        logger.error(f"Video interpretation failed: {e}")
        raise GeminiGenerationError(f"Video interpretation failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Model Protocol Summary
# ─────────────────────────────────────────────────────────────────────────────
#
# GEMINI_MODEL (gemini-3.0-flash):
#   - Default for all text/general tasks
#   - Storyboard generation
#   - Shot contract generation
#   - NotebookLM analysis (Logic/Persona extraction)
#   - Fast response, cost-effective
#
# GEMINI_VIDEO_MODEL (gemini-3.0-pro):
#   - Video file interpretation only
#   - Advanced multimodal understanding
#   - Scene detection, visual structure analysis
#   - Higher token limits for video content
#

