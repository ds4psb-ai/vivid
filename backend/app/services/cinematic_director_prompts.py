"""Cinematic Director Prompts — LLM System Prompts for Scenario Decomposition.

Contains the "AI Director" system prompts that transform a user's
freeform scenario text into a structured multi-shot video production plan.

Architecture:
  User Scenario (text) → DIRECTOR_SYSTEM_V2 (Gemini) → 5-Domain JSON
  5-Domain JSON → ad_prompt_engine → Engine-Native Multi-Shot Formats

Based on 2026 research:
  - VGoT 5-Domain Decomposition (NeurIPS 2025 Oral)
  - LTX Studio Element Extraction Pipeline
  - Kling 3.0 AI Director / 5-Layer Formula
  - Seedance 2.0 @tag Reference System
"""

# ═══════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT — Cinematic Director v2
# ═══════════════════════════════════════════════════════════════════════

DIRECTOR_SYSTEM_V2 = """You are an expert **Cinematic Director AI** — a fusion of a Hollywood director, 
cinematographer, and editor. You analyze scenarios and decompose them into multi-shot video sequences 
optimized for AI video generation engines (Kling 3.0, Seedance 2.0, Veo 3.1).

## YOUR CORE RESPONSIBILITIES

### 1. Beat Structure Design
Every scenario MUST be decomposed into a **narrative beat structure**:
- **OPENER** (1-2 shots): Establishing shot → sets location, mood, scale. Use WIDE/EXTREME WIDE.
- **RISING** (1-3 shots): Builds tension/interest. Tighten framing: MEDIUM → MEDIUM CLOSE-UP.
- **CLIMAX** (1-2 shots): Peak moment. CLOSE-UP / EXTREME CLOSE-UP. Dynamic camera (crash zoom, handheld).
- **RESOLVE** (1 shot): Emotional landing. Pull back to WIDE or match the opener framing.

### 2. Character Extraction Protocol
EXTRACT every character/entity from the scenario and assign a persistent binding token:
- Format: `[Character A: one-sentence visual description]`
- Include: age, gender, clothing, hair, distinguishing features
- Once defined, REUSE the SAME token in every subsequent shot
- If no human characters exist, bind key OBJECTS or ENVIRONMENTS the same way

### 3. Shot Type Intelligence
For each shot, SELECT the cinematically optimal combination:
| Beat     | Shot Scale      | Camera Movement      | Why                           |
|----------|-----------------|----------------------|-------------------------------|
| OPENER   | EWS / WS        | Crane up / Drone sweep | Geography, scale, context    |
| RISING   | MS / MCU        | Dolly in / Tracking   | Character introduction, build |
| CLIMAX   | CU / ECU        | Crash zoom / Handheld | Emotional peak, intimacy     |
| RESOLVE  | WS / FS         | Crane up / Slow pull  | Catharsis, breathing room    |

Apply these cinematography rules:
- **180° Rule**: Maintain spatial consistency across shot-reverse-shot pairs
- **30° Rule**: Each new angle must differ by ≥30° from previous
- **Match-on-Action**: Action continuity across cuts
- **Shot-Reverse-Shot**: For dialogue, alternate OTS (over-the-shoulder) framing

### 4. Pacing & Duration Design
Specify a **pacing_profile** for the entire sequence:
- `"explosive"` — Fast cuts (1-2s each), action/horror. Total: 5-8s.
- `"dramatic"` — Medium tempo (2-4s each), drama/thriller. Total: 8-12s.
- `"contemplative"` — Slow, lingering (3-6s each), art/romance. Total: 10-15s.
- `"escalating"` — Starts slow, accelerates. Duration per shot decreases.
- `"breathing"` — Alternates fast and slow for rhythm.

### 5. Audio Design
For EACH shot, specify audio cues:
- **Ambient**: Environmental sounds (rain, traffic, wind)
- **SFX**: Specific sound effects tied to action
- **Music**: Mood descriptor (not specific songs)
- **Dialogue**: Exact lines if applicable, with emotional tone

### 6. Engine Constraints Awareness
Your output will feed into:
- **Kling 3.0**: Max 6 shots per sequence, 3-15s total. Character binding via `[Char: desc]`.
- **Seedance 2.0**: 30-100 words per shot. @tag references for consistency. Single prompt, multi-shot.
- **Veo 3.1**: 4/6/8s per generation. Timestamp format `[0-2s] prompt...`. Extend chaining for 30s+.

Keep shot count between 3-6 for optimal quality. Each shot prompt should be 30-80 words.

## OUTPUT RULES
- All `description` fields: Korean (한국어)
- All `description_en`, `prompt`, `audio` fields: English
- Do NOT name real directors, artists, or copyrighted works
- Use atomic cinematic technique IDs from the corpus (e.g., `dolly_in`, `chiaroscuro`)
- Be SPECIFIC about camera distances: EWS, WS, FS, MS, MCU, CU, ECU
- Include physical verbs for motion (walks, turns, shatters, drifts — not "experiences")
"""


# ═══════════════════════════════════════════════════════════════════════
# USER PROMPT TEMPLATE — 5-Domain Decomposition
# ═══════════════════════════════════════════════════════════════════════

DECOMPOSITION_USER_TEMPLATE = """Decompose this scenario into a cinematic multi-shot video sequence.

## SCENARIO
{scenario}

{style_hint_section}

## INSTRUCTIONS
1. Extract ALL characters/entities → bind with `[Character X: description]`
2. Design a beat structure (OPENER → RISING → CLIMAX → RESOLVE)
3. For each shot: specify type, camera, lighting, color, audio
4. Design emotional arc with intensity curve (0.0-1.0)
5. Ensure cross-shot continuity (style, character, lighting consistency)

## REQUIRED JSON OUTPUT
```json
{{
  "characters": [
    {{
      "binding_token": "[Character A: young woman in white dress, long dark hair, melancholic expression]",
      "name": "Character A",
      "description_en": "young woman in white dress, long dark hair, melancholic expression",
      "first_appears_in_shot": 1,
      "arc_summary_en": "Starts isolated, discovers hope, transforms"
    }}
  ],
  "beat_structure": {{
    "type": "4-act",
    "pacing_profile": "dramatic",
    "total_target_duration_sec": 10,
    "beats": [
      {{"beat": "OPENER", "shot_numbers": [1], "purpose_en": "Establish rainy city atmosphere"}},
      {{"beat": "RISING", "shot_numbers": [2, 3], "purpose_en": "Character walks, discovers object"}},
      {{"beat": "CLIMAX", "shot_numbers": [4], "purpose_en": "Emotional revelation close-up"}},
      {{"beat": "RESOLVE", "shot_numbers": [5], "purpose_en": "Character walks into light"}}
    ]
  }},
  "shots": [
    {{
      "shot_number": 1,
      "beat": "OPENER",
      "description": "비 내리는 도시의 전경. 네온이 물에 반사된다.",
      "description_en": "Wide establishing shot of rain-soaked city. Neon lights reflect in puddles on empty streets at midnight.",
      "shot_type": "establishing",
      "duration_weight": 1.2,
      "techniques": {{
        "shot_scale": ["extreme_wide"],
        "camera_movement": ["crane_down"],
        "camera_angle": ["bird_eye"],
        "lighting": ["neon_saturated", "low_key_lighting"],
        "color": ["teal_orange_grade"],
        "composition": ["leading_lines"],
        "aesthetic_style": ["film_noir_neo"],
        "physics_motion": ["water_surface"],
        "focus_technique": ["deep_focus"],
        "editing_rhythm": ["slow_motion_editing"]
      }},
      "characters_in_shot": [],
      "action_en": "Camera slowly descends from aerial view to street level, revealing the wet cityscape.",
      "audio": {{
        "ambient": "Heavy rain pattering on concrete, distant thunder",
        "sfx": "Neon sign buzzing, water dripping",
        "music": "Low ominous synth drone, minor key",
        "dialogue": null
      }},
      "continuity_anchors": {{
        "character": "",
        "style": "neo-noir, wet reflections, teal-orange palette",
        "end_frame_hint": "Street level view of empty wet road with neon reflections"
      }},
      "transition_to_next": "match_cut"
    }}
  ],
  "sequence": {{
    "emotional_arc": [
      {{"shot_number": 1, "emotion": "고독", "intensity": 0.3, "description": "도시의 고립된 분위기"}}
    ],
    "visual_rhythm": {{
      "camera_distance_curve": ["EWS", "MS", "MCU", "CU", "WS"],
      "edit_tempo": "점진적 가속, 클라이맥스에서 빠른 컷, 해소에서 느려짐"
    }},
    "color_progression": [
      {{"shot_number": 1, "temperature": "cool", "palette": "청녹색+주황, 네온 반사"}}
    ],
    "continuity_anchors": {{
      "character_anchors": ["[Character A: young woman in white dress, long dark hair]"],
      "style_anchors": ["neo-noir", "wet surfaces", "neon reflections"],
      "lighting_anchors": ["low-key with practical neon sources"]
    }},
    "five_domains": {{
      "character_dynamics": "Character A starts alone in the rain, discovers a glowing object, experiences emotional revelation",
      "background_continuity": "Rain-soaked urban environment throughout, transitioning from wide streets to intimate alley",
      "relationship_evolution": "Solo character arc — from isolation to discovery to transformation",
      "camera_evolution": "Wide aerial → medium tracking → close-up intimate → wide pull-back",
      "lighting_evolution": "Cool neon exterior → warm practical light on object → mixed warm/cool resolution"
    }}
  }}
}}
```

Target engines: {engines}
Respond ONLY with valid JSON. No markdown code blocks."""


# ═══════════════════════════════════════════════════════════════════════
# SHOT TYPE GUIDELINES — per-beat optimal cinematography
# ═══════════════════════════════════════════════════════════════════════

SHOT_TYPE_GUIDELINES = {
    "OPENER": {
        "preferred_scales": ["extreme_wide", "wide_shot", "establishing_shot"],
        "preferred_movements": ["crane_down", "crane_up", "drone_aerial", "cable_cam", "jib_sweep"],
        "preferred_angles": ["bird_eye", "aerial_survey", "eye_level"],
        "purpose": "Establish geography, scale, mood. Orient the viewer.",
        "duration_weight": 1.2,
    },
    "RISING": {
        "preferred_scales": ["medium_shot", "medium_closeup", "full_body_shot", "cowboy_shot"],
        "preferred_movements": ["dolly_in", "lateral_tracking", "slow_push_in", "parallax_scroll"],
        "preferred_angles": ["eye_level", "slightly_low_angle"],
        "purpose": "Introduce characters, build tension/interest. Tighten framing.",
        "duration_weight": 1.0,
    },
    "CLIMAX": {
        "preferred_scales": ["closeup_shot", "extreme_closeup", "insert_shot"],
        "preferred_movements": ["crash_zoom", "handheld_shaky", "vertigo_effect", "whip_pan"],
        "preferred_angles": ["low_angle", "dutch_tilt", "over_the_shoulder"],
        "purpose": "Emotional peak. Maximum intimacy or impact. Dynamic camera.",
        "duration_weight": 0.8,
    },
    "RESOLVE": {
        "preferred_scales": ["wide_shot", "full_body_shot", "extreme_wide"],
        "preferred_movements": ["crane_up", "dolly_out", "static_hold"],
        "preferred_angles": ["eye_level", "slightly_high_angle"],
        "purpose": "Emotional landing. Breathing room. Often mirrors opener.",
        "duration_weight": 1.3,
    },
}


# ═══════════════════════════════════════════════════════════════════════
# PACING PROFILES — genre-specific rhythm patterns
# ═══════════════════════════════════════════════════════════════════════

PACING_PROFILES = {
    "explosive": {
        "avg_shot_duration": 1.5,
        "total_range": (5, 8),
        "duration_pattern": "constant_fast",
        "cut_style": "rapid_cuts",
        "transition_types": ["smash_cut", "flash_cut", "whip_pan_transition"],
        "genres": ["action", "horror", "music_video"],
    },
    "dramatic": {
        "avg_shot_duration": 3.0,
        "total_range": (8, 12),
        "duration_pattern": "escalating",
        "cut_style": "deliberate",
        "transition_types": ["cross_dissolve", "match_cut", "slow_dissolve"],
        "genres": ["drama", "thriller", "romance"],
    },
    "contemplative": {
        "avg_shot_duration": 5.0,
        "total_range": (10, 15),
        "duration_pattern": "lingering",
        "cut_style": "slow",
        "transition_types": ["slow_dissolve", "fade_to_black", "cross_dissolve"],
        "genres": ["art_film", "meditation", "nature"],
    },
    "escalating": {
        "avg_shot_duration": 3.0,
        "total_range": (8, 12),
        "duration_pattern": "decelerating_shots",
        "cut_style": "builds_to_rapid",
        "transition_types": ["cross_dissolve", "match_cut", "smash_cut"],
        "genres": ["suspense", "heist", "sports"],
    },
    "breathing": {
        "avg_shot_duration": 3.0,
        "total_range": (8, 15),
        "duration_pattern": "alternating",
        "cut_style": "rhythmic",
        "transition_types": ["cross_dissolve", "match_cut", "slow_dissolve"],
        "genres": ["documentary", "interview", "lifestyle"],
    },
}


# ═══════════════════════════════════════════════════════════════════════
# CHARACTER BINDING RULES — consistency enforcement
# ═══════════════════════════════════════════════════════════════════════

CHARACTER_BINDING_RULES = """
## Character Consistency Protocol

1. **First Mention = Definition**: The FIRST time a character appears, define them fully:
   `[Character A: mid-30s Korean woman, shoulder-length black hair, wearing a navy trench coat, 
   carrying a red umbrella, tired but determined expression]`

2. **Subsequent Mentions = Reference**: Every later shot uses the SAME token:
   `[Character A] turns to face the camera`
   NOT: `A woman turns...` or `She turns...`

3. **Maximum 4 characters** per sequence for consistency.

4. **Binding → Engine Mapping**:
   - Kling 3.0: `[Character A: desc]` in prompt directly
   - Seedance 2.0: Upload reference image as `@Image1`, then `@Image1 is Character A`
   - Veo 3.1: Use "Ingredients to Video" feature for character reference
"""


# ═══════════════════════════════════════════════════════════════════════
# TRANSITION INTELLIGENCE — shot-to-shot connection rules
# ═══════════════════════════════════════════════════════════════════════

TRANSITION_RULES = {
    "match_cut": {
        "description": "Visual/motion match between end of shot A and start of shot B",
        "best_for": ["OPENER→RISING", "RISING→RISING"],
        "end_frame_requirement": "End frame must contain a shape/motion that mirrors the start of next shot",
    },
    "smash_cut": {
        "description": "Abrupt, jarring cut for maximum impact",
        "best_for": ["RISING→CLIMAX"],
        "end_frame_requirement": "No easing. Final frame contrasts sharply with next shot's opening.",
    },
    "cross_dissolve": {
        "description": "Gradual blend between shots, implies time passage or connection",
        "best_for": ["CLIMAX→RESOLVE", "OPENER→RISING"],
        "end_frame_requirement": "End frame should share color/light values with next shot for smooth blend",
    },
    "slow_dissolve": {
        "description": "Extended dissolve (1-2s) for dreamlike or emotional transitions",
        "best_for": ["RESOLVE→OPENER (loop)", "emotional moments"],
        "end_frame_requirement": "End frame should be relatively static for clean dissolve",
    },
    "whip_pan_transition": {
        "description": "Fast horizontal pan creating motion blur bridge",
        "best_for": ["RISING→RISING", "time/space jumps"],
        "end_frame_requirement": "End with horizontal motion blur",
    },
}
