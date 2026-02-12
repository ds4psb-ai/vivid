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

DIRECTOR_SYSTEM_V2 = """You are a Cinematic Director AI — expert in directing, cinematography, and editing.
Decompose scenarios into multi-shot video sequences for AI video engines.

## CORE PRINCIPLES

### 1. Beat Structure
Every sequence follows narrative beats:
- OPENER (1-2 shots): Establishing shot, WIDE/EWS. Location, mood, scale.
- RISING (1-3 shots): Build tension, MEDIUM→MCU. Introduce characters.
- CLIMAX (1-2 shots): Peak moment, CU/ECU. Dynamic camera.
- RESOLVE (1 shot): Emotional landing, pull back to WIDE.

### 2. Character Binding
- First mention: `[Character A: full visual description]` — age, gender, clothing, hair, features.
- Later shots: reuse exact token. Never use pronouns or vague references.
- Max 4 characters per sequence.

### 3. Engine Awareness
- Kling 3.0: Max 6 shots, 3-15s. `[Char: desc]` binding. 30-80 words/prompt.
- Seedance 2.0: 30-100 words/shot. @tag references. Single prompt, multi-shot.
- Veo 3.1: 4/6/8s clips. Cinematic language: 1 camera verb + 1 lighting + 1 action.

## OUTPUT RULES
- `description` fields: Korean. `description_en`, `action_en`, `prompt`, `audio`: English.
- No real directors, artists, or copyrighted works.
- Physical verbs only (walks, turns, shatters) — never abstract (experiences, feels).
- 3-6 shots per sequence. 30-80 words per prompt.
- Maintain 180° rule. Camera angle change ≥30° between cuts.
- For each shot: specify audio (ambient, sfx, music, dialogue).
"""


# ═══════════════════════════════════════════════════════════════════════
# USER PROMPT TEMPLATE — 5-Domain Decomposition
# ═══════════════════════════════════════════════════════════════════════

DECOMPOSITION_USER_TEMPLATE = """Decompose this scenario into a cinematic multi-shot video sequence.

## SCENARIO
{scenario}

{style_hint_section}

## REFERENCE EXAMPLE
Follow the exact structure and level of detail shown below:

__FEW_SHOT_PLACEHOLDER__

## INSTRUCTIONS
1. Extract ALL characters → bind with `[Character X: visual description]`
2. Design beat structure: OPENER → RISING → CLIMAX → RESOLVE (all required)
3. Per shot: shot_type, camera, lighting, color, audio, engine prompts (kling_3_0, seedance_2_0, veo_3_1)
4. Ensure cross-shot continuity: character binding, style anchors, lighting progression
5. Every prompt must be unique and specific — no lazy references to other shots
6. Include five_domains analysis for cross-shot coherence

Target engines: {engines}
Respond ONLY with valid JSON matching the schema."""


# ═══════════════════════════════════════════════════════════════════════
# FEW-SHOT EXAMPLES — high-quality decomposition output per genre
# ═══════════════════════════════════════════════════════════════════════

FEW_SHOT_EXAMPLES = {
    # ── dramatic: rain city, 4 shots, medium tempo ──
    "dramatic": {
        "characters": [
            {
                "binding_token": "[Character A: mid-30s Korean man, short black hair, grey wool overcoat, exhausted expression]",
                "name": "Character A",
                "description_en": "mid-30s Korean man, short black hair, grey wool overcoat, exhausted expression",
                "first_appears_in_shot": 2,
                "arc_summary_en": "Walks aimlessly in rain, stops, looks up — quiet acceptance",
            }
        ],
        "beat_structure": {
            "type": "4-act",
            "pacing_profile": "dramatic",
            "total_target_duration_sec": 10,
            "beats": [
                {"beat": "OPENER", "shot_numbers": [1], "purpose_en": "Establish midnight rain-soaked city"},
                {"beat": "RISING", "shot_numbers": [2], "purpose_en": "Character walks through empty streets"},
                {"beat": "CLIMAX", "shot_numbers": [3], "purpose_en": "Character stops, looks skyward"},
                {"beat": "RESOLVE", "shot_numbers": [4], "purpose_en": "Wide pullback, rain continues"},
            ],
        },
        "shots": [
            {
                "shot_number": 1,
                "beat": "OPENER",
                "description": "자정의 비 내리는 도시. 네온이 웅덩이에 반사된다.",
                "description_en": "Midnight rain-soaked city streets. Neon signs reflect in puddles across empty asphalt.",
                "shot_type": "establishing",
                "duration_weight": 1.2,
                "techniques": {
                    "shot_scale": ["extreme_wide"],
                    "camera_movement": ["crane_down"],
                    "camera_angle": ["bird_eye"],
                    "lighting": ["neon_saturated", "low_key_lighting"],
                    "color": ["teal_orange_grade"],
                    "composition": ["leading_lines"],
                },
                "characters_in_shot": [],
                "action_en": "Camera descends from aerial view to street level, revealing wet cityscape with glowing neon.",
                "audio": {
                    "ambient": "Heavy rain on concrete, distant thunder",
                    "sfx": "Neon sign buzzing",
                    "music": "Low synth drone, minor key",
                    "dialogue": None,
                },
                "continuity_anchors": {
                    "character": "",
                    "style": "neo-noir, wet reflections, teal-orange",
                    "end_frame_hint": "Street level view of empty wet road",
                },
                "transition_to_next": "match_cut",
                "prompts": {
                    "kling_3_0": "Midnight city aerial descending through rain. Neon signs glow teal and orange, reflecting in puddles on empty streets. Crane down from bird's eye to street level. Heavy rain, cinematic low-key lighting.",
                    "seedance_2_0": "Cinematic aerial descent through midnight rain over empty city streets. Neon lights cast teal and orange reflections across wet asphalt. Camera cranes down smoothly from bird's eye to street level. Heavy rainfall, shimmering surfaces. Low-key neo-noir atmosphere with buzzing neon ambiance.",
                    "veo_3_1": "Aerial crane shot descending through heavy rain over midnight city streets. Teal and orange neon signs reflect in puddles across empty wet asphalt. Camera moves from bird's eye down to street level in one continuous motion. Neo-noir atmosphere, low-key lighting. Rain creates shimmering reflections on every surface.",
                },
            },
            {
                "shot_number": 2,
                "beat": "RISING",
                "description": "[Character A]가 빈 거리를 우산 없이 걷는다. 비에 젖은 코트.",
                "description_en": "[Character A: mid-30s Korean man, short black hair, grey wool overcoat] walks without umbrella. Rain soaks his coat.",
                "shot_type": "tracking",
                "duration_weight": 1.0,
                "techniques": {
                    "shot_scale": ["medium_shot"],
                    "camera_movement": ["lateral_tracking"],
                    "camera_angle": ["eye_level"],
                    "lighting": ["practical_light", "neon_saturated"],
                    "color": ["desaturated_cool"],
                    "composition": ["center_frame"],
                },
                "characters_in_shot": ["[Character A: mid-30s Korean man, short black hair, grey wool overcoat]"],
                "action_en": "[Character A] walks slowly down wet street, head bowed, rain running down his face.",
                "audio": {
                    "ambient": "Footsteps on wet pavement, steady rain",
                    "sfx": "Coat fabric rustling",
                    "music": "Piano enters, sparse and melancholic",
                    "dialogue": None,
                },
                "continuity_anchors": {
                    "character": "[Character A: grey overcoat, rain-soaked]",
                    "style": "neo-noir, wet surfaces",
                    "end_frame_hint": "Character walking frame-right toward intersection",
                },
                "transition_to_next": "match_cut",
                "prompts": {
                    "kling_3_0": "[Character A: mid-30s Korean man, grey wool overcoat, rain-soaked]. Walking slowly through empty wet street without umbrella. Medium shot, lateral tracking. Practical neon lighting, desaturated cool tones.",
                    "seedance_2_0": "Lateral tracking medium shot of [Character A: mid-30s Korean man in grey wool overcoat] walking through rain-soaked empty street. No umbrella, rain on his face. Desaturated cool tones with practical neon lighting. Sparse piano, steady rain. Neo-noir atmosphere.",
                    "veo_3_1": "Lateral tracking medium shot following a mid-30s Korean man in grey wool overcoat walking through empty rain-soaked streets. No umbrella, head slightly bowed as rain streams down his face. Cool desaturated palette with warm neon accents. Steady rain creates rhythm on wet pavement.",
                },
            },
            {
                "shot_number": 3,
                "beat": "CLIMAX",
                "description": "[Character A]가 멈춰 서서 천천히 하늘을 올려다본다. 빗방울이 얼굴에 떨어진다.",
                "description_en": "[Character A] stops and slowly looks up at the sky. Raindrops fall onto his upturned face.",
                "shot_type": "emotional_peak",
                "duration_weight": 0.8,
                "techniques": {
                    "shot_scale": ["closeup_shot"],
                    "camera_movement": ["slow_push_in"],
                    "camera_angle": ["slightly_low_angle"],
                    "lighting": ["rim_light", "neon_saturated"],
                    "color": ["teal_orange_grade"],
                    "composition": ["center_frame"],
                },
                "characters_in_shot": ["[Character A]"],
                "action_en": "[Character A] halts mid-step, turns face upward. Raindrops strike his closed eyes. Slow push in to extreme close-up.",
                "audio": {
                    "ambient": "Rain intensifies hitting face",
                    "sfx": "Deep breath, exhale",
                    "music": "Piano swells, strings enter softly",
                    "dialogue": None,
                },
                "continuity_anchors": {
                    "character": "[Character A: upturned face, eyes closed, rain streaming]",
                    "style": "neo-noir, rim-lit rain",
                    "end_frame_hint": "Extreme close-up of rain on closed eyelids",
                },
                "transition_to_next": "cross_dissolve",
                "prompts": {
                    "kling_3_0": "[Character A: mid-30s Korean man, grey wool overcoat]. Stops walking, looks up at sky. Close-up, slow push in, slightly low angle. Raindrops on upturned face. Rim lighting with neon glow, teal-orange grade.",
                    "seedance_2_0": "Close-up slow push in from slightly low angle. [Character A: mid-30s Korean man] stops and tilts face skyward. Raindrops strike closed eyes, streaming down cheeks. Neon rim lighting halo. Teal-orange grade deepens. Piano swells with soft strings.",
                    "veo_3_1": "Close-up slow push in from slightly low angle as a mid-30s Korean man in grey overcoat stops walking and turns face upward to rain. Raindrops strike closed eyes, streaming down cheeks. Neon rim lighting creates luminous halo. Teal-orange grade. Piano swells with soft strings.",
                },
            },
            {
                "shot_number": 4,
                "beat": "RESOLVE",
                "description": "넓은 프레임. [Character A]가 빗속에 서 있고, 도시가 그를 감싼다.",
                "description_en": "Wide pullback reveals [Character A] standing in rain as the city surrounds him.",
                "shot_type": "resolution",
                "duration_weight": 1.3,
                "techniques": {
                    "shot_scale": ["wide_shot"],
                    "camera_movement": ["crane_up"],
                    "camera_angle": ["slightly_high_angle"],
                    "lighting": ["neon_saturated", "low_key_lighting"],
                    "color": ["teal_orange_grade"],
                    "composition": ["center_frame", "negative_space"],
                },
                "characters_in_shot": ["[Character A]"],
                "action_en": "Camera cranes up, revealing [Character A] as small figure in vast rain-soaked city.",
                "audio": {
                    "ambient": "Rain fading, city hum returns",
                    "sfx": "Distant car horn",
                    "music": "Piano fades to sustained string chord",
                    "dialogue": None,
                },
                "continuity_anchors": {
                    "character": "[Character A: standing still, face up, small in frame]",
                    "style": "neo-noir, solitary figure in urban expanse",
                    "end_frame_hint": "High wide shot of lone figure in rain",
                },
                "transition_to_next": "fade_to_black",
                "prompts": {
                    "kling_3_0": "[Character A: mid-30s Korean man, grey wool overcoat]. Standing still in rain, face upturned. Wide shot, crane up. Neon city surrounds small figure. Low-key teal-orange, negative space.",
                    "seedance_2_0": "Wide crane up revealing [Character A] as solitary figure in vast rain-soaked city. Neon lights glow in background. Camera ascends to high angle, emphasizing isolation. Teal-orange grade, low-key neo-noir. Piano fades to sustained string chord.",
                    "veo_3_1": "Wide crane up from eye level to high angle, revealing solitary figure standing in rain-soaked city streets. Neon-lit buildings frame the small human form. Camera ascends slowly. Teal-orange grade, low-key lighting. Sustained string chord fades.",
                },
            },
        ],
        "sequence": {
            "emotional_arc": [
                {"shot_number": 1, "emotion": "고독", "intensity": 0.3, "description": "텅 빈 도시의 고립감"},
                {"shot_number": 2, "emotion": "체념", "intensity": 0.5, "description": "무력하게 걷는 모습"},
                {"shot_number": 3, "emotion": "수용", "intensity": 0.9, "description": "하늘을 올려다보는 카타르시스"},
                {"shot_number": 4, "emotion": "평온", "intensity": 0.4, "description": "고요한 해소"},
            ],
            "visual_rhythm": {
                "camera_distance_curve": ["EWS", "MS", "CU", "WS"],
                "edit_tempo": "느린 시작 → 점진적 집중 → 클로즈업 → 넓은 해소",
            },
            "color_progression": [
                {"shot_number": 1, "temperature": "cool", "palette": "틸-오렌지, 네온 반사"},
                {"shot_number": 2, "temperature": "cool", "palette": "저채도 쿨톤"},
                {"shot_number": 3, "temperature": "mixed", "palette": "틸-오렌지 강화, 림 라이트"},
                {"shot_number": 4, "temperature": "cool", "palette": "틸-오렌지, 네거티브 스페이스"},
            ],
            "continuity_anchors": {
                "character_anchors": ["[Character A: mid-30s Korean man, grey wool overcoat]"],
                "style_anchors": ["neo-noir", "wet surfaces", "neon reflections"],
                "lighting_anchors": ["low-key with practical neon sources"],
            },
            "five_domains": {
                "character_dynamics": "Character A: aimless walking → halting → looking up → acceptance. Solo arc of quiet catharsis.",
                "background_continuity": "Midnight rain-soaked urban streets throughout. Neon signs as consistent light sources.",
                "relationship_evolution": "Solo character arc — isolation → self-confrontation → acceptance",
                "camera_evolution": "Aerial EWS → lateral MS tracking → frontal CU push-in → crane-up WS",
                "lighting_evolution": "Neon-saturated wide → practical street lights → rim-lit close-up → wide neon cityscape",
            },
        },
    },

    # ── explosive: rooftop chase, 4 shots, fast cuts ──
    "explosive": {
        "characters": [
            {
                "binding_token": "[Character A: early-20s woman, athletic build, black tactical jacket, ponytail, determined stare]",
                "name": "Character A",
                "description_en": "early-20s woman, athletic build, black tactical jacket, ponytail, determined stare",
                "first_appears_in_shot": 1,
                "arc_summary_en": "Flees across rooftops, leaps gap, lands and escapes",
            },
            {
                "binding_token": "[Character B: tall man in dark hoodie, masked face, heavy boots, menacing posture]",
                "name": "Character B",
                "description_en": "tall man in dark hoodie, masked face, heavy boots, menacing posture",
                "first_appears_in_shot": 2,
                "arc_summary_en": "Pursues across rooftops, reaches gap, hesitates",
            },
        ],
        "beat_structure": {
            "type": "4-act",
            "pacing_profile": "explosive",
            "total_target_duration_sec": 7,
            "beats": [
                {"beat": "OPENER", "shot_numbers": [1], "purpose_en": "Character A sprints across rooftop"},
                {"beat": "RISING", "shot_numbers": [2], "purpose_en": "Pursuer closing distance"},
                {"beat": "CLIMAX", "shot_numbers": [3], "purpose_en": "Leap across building gap"},
                {"beat": "RESOLVE", "shot_numbers": [4], "purpose_en": "Landing, pursuer left behind"},
            ],
        },
        "shots": [
            {
                "shot_number": 1,
                "beat": "OPENER",
                "description": "[Character A]가 옥상을 전력질주한다. 도시 스카이라인이 배경.",
                "description_en": "[Character A: early-20s woman, black tactical jacket, ponytail] sprints across rooftop. City skyline behind.",
                "shot_type": "action_establishing",
                "duration_weight": 0.8,
                "techniques": {
                    "shot_scale": ["wide_shot"],
                    "camera_movement": ["lateral_tracking"],
                    "camera_angle": ["slightly_low_angle"],
                    "lighting": ["golden_hour_backlit"],
                    "color": ["warm_amber"],
                    "composition": ["rule_of_thirds"],
                },
                "characters_in_shot": ["[Character A: early-20s woman, black tactical jacket, ponytail]"],
                "action_en": "[Character A] sprints full speed across flat rooftop, arms pumping, jacket flaring behind her.",
                "audio": {
                    "ambient": "Wind rushing, distant city traffic",
                    "sfx": "Boots pounding gravel rooftop",
                    "music": "Driving electronic pulse, 140bpm",
                    "dialogue": None,
                },
                "continuity_anchors": {
                    "character": "[Character A: running, jacket flaring]",
                    "style": "golden hour action, urban rooftop",
                    "end_frame_hint": "Character A mid-stride approaching rooftop edge",
                },
                "transition_to_next": "smash_cut",
                "prompts": {
                    "kling_3_0": "[Character A: early-20s woman, black tactical jacket, ponytail]. Sprinting across rooftop at full speed. Wide shot, lateral tracking, slightly low angle. Golden hour backlight, warm amber tones. City skyline behind.",
                    "seedance_2_0": "Wide lateral tracking shot of [Character A: athletic woman in black tactical jacket] sprinting across gravel rooftop. Golden hour backlight silhouettes her against city skyline. Boots pound gravel. Jacket flares behind her. Warm amber tones. Driving electronic pulse soundtrack.",
                    "veo_3_1": "Wide lateral tracking shot following an athletic woman in black tactical jacket sprinting across a gravel rooftop. Golden hour backlight creates dramatic silhouette against city skyline. Jacket flares behind her as she runs. Warm amber tones, slightly low angle emphasizing speed and determination.",
                },
            },
            {
                "shot_number": 2,
                "beat": "RISING",
                "description": "[Character B]가 뒤에서 추격한다. 거리가 좁혀진다.",
                "description_en": "[Character B: tall man in dark hoodie, masked] chases from behind. Gap narrowing.",
                "shot_type": "pursuit",
                "duration_weight": 0.7,
                "techniques": {
                    "shot_scale": ["medium_shot"],
                    "camera_movement": ["handheld_shaky"],
                    "camera_angle": ["over_the_shoulder"],
                    "lighting": ["golden_hour_backlit"],
                    "color": ["warm_amber"],
                    "composition": ["depth_layering"],
                },
                "characters_in_shot": ["[Character A]", "[Character B: tall man in dark hoodie, masked]"],
                "action_en": "[Character B] gains ground behind [Character A]. Heavy boots close the distance. Over-shoulder from pursuer's POV.",
                "audio": {
                    "ambient": "Wind, labored breathing",
                    "sfx": "Heavy boots on gravel, fabric swishing",
                    "music": "Electronic builds, tension stacking",
                    "dialogue": None,
                },
                "continuity_anchors": {
                    "character": "[Character B: closing in on Character A]",
                    "style": "golden hour action, handheld urgency",
                    "end_frame_hint": "Both characters approaching rooftop edge with gap visible",
                },
                "transition_to_next": "smash_cut",
                "prompts": {
                    "kling_3_0": "[Character B: tall man in dark hoodie, masked face]. Chasing [Character A] across rooftop. Medium shot, handheld, over-shoulder. Gap narrowing. Golden hour backlight, warm amber. Heavy breathing.",
                    "seedance_2_0": "Handheld over-shoulder medium shot from [Character B: masked man in dark hoodie] pursuing [Character A] across rooftop. Gap narrowing rapidly. Golden hour backlight. Heavy boots pound gravel. Breathing intensifies. Electronic music builds tension layers.",
                    "veo_3_1": "Handheld over-shoulder medium shot from pursuer's perspective chasing a woman across rooftop. Gap narrowing. Golden hour backlight catches dust kicked up by heavy boots. Warm amber palette. Shaky camera conveys urgent pursuit energy.",
                },
            },
            {
                "shot_number": 3,
                "beat": "CLIMAX",
                "description": "[Character A]가 건물 사이 틈을 향해 도약한다. 공중에 떠있는 순간.",
                "description_en": "[Character A] leaps across the gap between buildings. Frozen mid-air moment.",
                "shot_type": "action_climax",
                "duration_weight": 0.6,
                "techniques": {
                    "shot_scale": ["full_body_shot"],
                    "camera_movement": ["crash_zoom"],
                    "camera_angle": ["low_angle"],
                    "lighting": ["golden_hour_backlit"],
                    "color": ["high_contrast"],
                    "composition": ["center_frame"],
                    "editing_rhythm": ["slow_motion_editing"],
                },
                "characters_in_shot": ["[Character A]"],
                "action_en": "[Character A] plants foot on edge, launches across gap. Slow-motion mid-air. Arms spread, city below.",
                "audio": {
                    "ambient": "Wind silence — isolated moment",
                    "sfx": "Foot impact on ledge, whoosh of air",
                    "music": "Music drops out. Single sustained bass note.",
                    "dialogue": None,
                },
                "continuity_anchors": {
                    "character": "[Character A: mid-air, arms spread, silhouetted]",
                    "style": "golden hour silhouette, slow-motion peak",
                    "end_frame_hint": "Character A reaching for far ledge, city lights below",
                },
                "transition_to_next": "smash_cut",
                "prompts": {
                    "kling_3_0": "[Character A: early-20s woman, black tactical jacket]. Leaps across building gap. Full body, low angle crash zoom. Slow motion mid-air. Golden hour silhouette, high contrast. Arms spread, city below.",
                    "seedance_2_0": "Low angle crash zoom capturing [Character A: woman in black tactical jacket] mid-leap across building gap. Slow motion freeze. Golden hour backlight creates dramatic silhouette. Arms spread wide against sky. City lights far below. Music drops to single bass note.",
                    "veo_3_1": "Low angle crash zoom as an athletic woman in black tactical jacket leaps across a gap between buildings. Slow motion captures her mid-air, arms spread, silhouetted against golden hour sky. City lights glimmer far below. Sound drops to wind and a single sustained bass note.",
                },
            },
            {
                "shot_number": 4,
                "beat": "RESOLVE",
                "description": "[Character A]가 반대편 옥상에 착지한다. 뒤를 돌아보면 [Character B]가 멈춰 서 있다.",
                "description_en": "[Character A] lands on far rooftop. Looks back — [Character B] stands at the edge, unable to follow.",
                "shot_type": "resolution",
                "duration_weight": 0.9,
                "techniques": {
                    "shot_scale": ["medium_shot"],
                    "camera_movement": ["static_hold"],
                    "camera_angle": ["eye_level"],
                    "lighting": ["golden_hour_backlit"],
                    "color": ["warm_amber"],
                    "composition": ["split_screen_natural"],
                },
                "characters_in_shot": ["[Character A]", "[Character B]"],
                "action_en": "[Character A] lands hard, rolls, rises. Turns back. Across gap, [Character B] stands at edge, fists clenched.",
                "audio": {
                    "ambient": "City hum resumes",
                    "sfx": "Impact roll on gravel, heavy breathing",
                    "music": "Electronic returns, resolving chord",
                    "dialogue": None,
                },
                "continuity_anchors": {
                    "character": "[Character A: landed, looking back] / [Character B: stranded at edge]",
                    "style": "golden hour, physical resolution",
                    "end_frame_hint": "Two figures separated by gap, facing each other",
                },
                "transition_to_next": "fade_to_black",
                "prompts": {
                    "kling_3_0": "[Character A: early-20s woman, black tactical jacket] lands on far rooftop, rolls, rises. Looks back at [Character B: masked man in hoodie] stranded across gap. Medium shot, static, eye level. Golden hour, warm amber.",
                    "seedance_2_0": "Static medium shot at eye level. [Character A: woman in tactical jacket] lands hard on far rooftop, rolls forward, rises. Turns to look back across the gap. [Character B: masked man] stands at opposite edge, unable to follow. Golden hour warm amber. Resolving electronic chord.",
                    "veo_3_1": "Static medium shot at eye level as a woman in black tactical jacket lands hard on rooftop, rolls and rises. She turns to look back across the gap where a masked man stands at the opposite edge, unable to follow. Golden hour warm amber palette. Two figures separated by the void between buildings.",
                },
            },
        ],
        "sequence": {
            "emotional_arc": [
                {"shot_number": 1, "emotion": "긴박", "intensity": 0.7, "description": "전력 질주의 긴장감"},
                {"shot_number": 2, "emotion": "공포", "intensity": 0.85, "description": "추격자가 좁혀오는 위기"},
                {"shot_number": 3, "emotion": "경외", "intensity": 1.0, "description": "도약 순간의 극적 정점"},
                {"shot_number": 4, "emotion": "안도", "intensity": 0.5, "description": "탈출 성공의 해소"},
            ],
            "visual_rhythm": {
                "camera_distance_curve": ["WS", "MS", "FS", "MS"],
                "edit_tempo": "빠른 시작 → 가속 → 슬로모션 정점 → 정적 해소",
            },
            "color_progression": [
                {"shot_number": 1, "temperature": "warm", "palette": "골든아워 앰버, 백라이트"},
                {"shot_number": 2, "temperature": "warm", "palette": "앰버 강화, 핸드헬드 거칠기"},
                {"shot_number": 3, "temperature": "warm", "palette": "하이 콘트라스트 실루엣"},
                {"shot_number": 4, "temperature": "warm", "palette": "앰버 해소, 부드러운 톤"},
            ],
            "continuity_anchors": {
                "character_anchors": [
                    "[Character A: early-20s woman, black tactical jacket, ponytail]",
                    "[Character B: tall man in dark hoodie, masked]",
                ],
                "style_anchors": ["golden hour", "urban rooftop", "action kinetic"],
                "lighting_anchors": ["golden hour backlight throughout"],
            },
            "five_domains": {
                "character_dynamics": "Character A flees, physically dominant. Character B pursues, increasingly desperate. Power reversal at the gap.",
                "background_continuity": "Urban rooftop environment. City skyline constant backdrop. Gravel surface, concrete ledges.",
                "relationship_evolution": "Predator-prey → gap creates reversal → pursuer stranded, prey freed",
                "camera_evolution": "Wide lateral → handheld OTS → low-angle crash zoom → static medium",
                "lighting_evolution": "Golden hour backlight consistent, intensity peaks at silhouette leap",
            },
        },
    },

    # ── contemplative: lake at dawn, 3 shots, long takes ──
    "contemplative": {
        "characters": [
            {
                "binding_token": "[Character A: late-40s woman, silver-streaked hair in loose bun, white linen dress, bare feet, serene expression]",
                "name": "Character A",
                "description_en": "late-40s woman, silver-streaked hair in loose bun, white linen dress, bare feet, serene expression",
                "first_appears_in_shot": 2,
                "arc_summary_en": "Walks to lake shore, wades in, stands in still water — moment of peace",
            }
        ],
        "beat_structure": {
            "type": "3-act",
            "pacing_profile": "contemplative",
            "total_target_duration_sec": 14,
            "beats": [
                {"beat": "OPENER", "shot_numbers": [1], "purpose_en": "Establish misty lake at dawn"},
                {"beat": "CLIMAX", "shot_numbers": [2], "purpose_en": "Character walks into water"},
                {"beat": "RESOLVE", "shot_numbers": [3], "purpose_en": "Standing still, mist and sunrise"},
            ],
        },
        "shots": [
            {
                "shot_number": 1,
                "beat": "OPENER",
                "description": "새벽 안개 속의 고요한 호수. 수면 위로 빛이 번진다.",
                "description_en": "Still lake at dawn, mist hovering over water. First light spreads across the surface.",
                "shot_type": "establishing",
                "duration_weight": 1.5,
                "techniques": {
                    "shot_scale": ["extreme_wide"],
                    "camera_movement": ["static_hold"],
                    "camera_angle": ["eye_level"],
                    "lighting": ["natural_dawn", "soft_diffused"],
                    "color": ["pastel_cool"],
                    "composition": ["symmetry"],
                    "focus_technique": ["deep_focus"],
                },
                "characters_in_shot": [],
                "action_en": "Static wide shot. Mist drifts slowly over mirror-still lake. Dawn light gradually intensifies.",
                "audio": {
                    "ambient": "Distant birdsong, gentle water lapping",
                    "sfx": "Faint wind through reeds",
                    "music": "Solo cello, sustained open fifth",
                    "dialogue": None,
                },
                "continuity_anchors": {
                    "character": "",
                    "style": "ethereal dawn, mirror-still water, soft pastels",
                    "end_frame_hint": "Wide lake with mist, light growing",
                },
                "transition_to_next": "slow_dissolve",
                "prompts": {
                    "kling_3_0": "Misty lake at dawn. Extreme wide, static. Mirror-still water reflects pale sky. Mist drifts slowly. Natural dawn light, soft diffused, pastel cool tones. Symmetrical composition. Deep silence.",
                    "seedance_2_0": "Static extreme wide shot of misty lake at dawn. Mirror-still water reflects pale pink and blue sky. Mist drifts slowly across the surface. Natural dawn light gradually intensifies. Pastel cool tones. Symmetrical composition. Distant birdsong and gentle water lapping. Solo cello sustains.",
                    "veo_3_1": "Static extreme wide shot of a misty lake at dawn. Mirror-still water perfectly reflects the pale sky above. Thin mist drifts slowly across the surface as natural dawn light gradually intensifies. Pastel cool tones of pink and blue. Symmetrical composition with perfect horizon line. Distant birdsong breaks the silence.",
                },
            },
            {
                "shot_number": 2,
                "beat": "CLIMAX",
                "description": "[Character A]가 호숫가를 맨발로 걸어 물속으로 들어간다. 잔잔한 파문.",
                "description_en": "[Character A: late-40s woman, white linen dress, bare feet] walks barefoot into the lake. Gentle ripples spread.",
                "shot_type": "emotional_peak",
                "duration_weight": 1.3,
                "techniques": {
                    "shot_scale": ["medium_shot"],
                    "camera_movement": ["slow_push_in"],
                    "camera_angle": ["eye_level"],
                    "lighting": ["natural_dawn", "rim_light"],
                    "color": ["warm_golden"],
                    "composition": ["center_frame"],
                },
                "characters_in_shot": ["[Character A: late-40s woman, silver-streaked hair, white linen dress, bare feet]"],
                "action_en": "[Character A] walks slowly from shore into shallow water. Ripples spread from each step. Linen dress hems darken with water.",
                "audio": {
                    "ambient": "Water splashing softly with each step",
                    "sfx": "Wet linen, gentle ripples",
                    "music": "Cello joined by piano, ascending phrase",
                    "dialogue": None,
                },
                "continuity_anchors": {
                    "character": "[Character A: wading, dress darkening at hems]",
                    "style": "ethereal dawn, golden rim light",
                    "end_frame_hint": "Character standing knee-deep, facing away",
                },
                "transition_to_next": "cross_dissolve",
                "prompts": {
                    "kling_3_0": "[Character A: late-40s woman, silver hair in bun, white linen dress, bare feet]. Walking into lake. Medium shot, slow push in. Dawn rim light. Warm golden tones. Ripples spread from each step.",
                    "seedance_2_0": "Slow push in medium shot of [Character A: woman in white linen dress] walking barefoot into still lake. Each step sends gentle ripples across mirror surface. Dawn rim light catches silver-streaked hair. Warm golden tones emerge. Linen hems darken with water. Cello and piano ascending phrase.",
                    "veo_3_1": "Slow push in medium shot of a woman in white linen dress walking barefoot into a still lake at dawn. Each step sends gentle ripples across the mirror surface. Dawn rim light catches her silver-streaked hair. Warm golden tones emerge as sun rises. Linen dress hems darken with water.",
                },
            },
            {
                "shot_number": 3,
                "beat": "RESOLVE",
                "description": "멀리서 바라본 [Character A]. 안개와 빛 사이에 고요히 서 있다.",
                "description_en": "Wide view of [Character A] standing still in water, surrounded by mist and dawn light.",
                "shot_type": "resolution",
                "duration_weight": 1.5,
                "techniques": {
                    "shot_scale": ["extreme_wide"],
                    "camera_movement": ["static_hold"],
                    "camera_angle": ["eye_level"],
                    "lighting": ["natural_dawn", "soft_diffused"],
                    "color": ["warm_golden"],
                    "composition": ["center_frame", "negative_space"],
                },
                "characters_in_shot": ["[Character A]"],
                "action_en": "[Character A] stands motionless in shallow water. Mist parts around her. Morning light grows warmer.",
                "audio": {
                    "ambient": "Water stillness, birds growing louder",
                    "sfx": "Light breeze",
                    "music": "Cello and piano resolve to major chord, fade",
                    "dialogue": None,
                },
                "continuity_anchors": {
                    "character": "[Character A: still figure in water, surrounded by mist]",
                    "style": "ethereal dawn, golden warmth, vast negative space",
                    "end_frame_hint": "Small white figure in vast golden lake",
                },
                "transition_to_next": "fade_to_black",
                "prompts": {
                    "kling_3_0": "[Character A: late-40s woman, white linen dress] standing motionless in lake. Extreme wide, static. Dawn mist parts around her. Warm golden light, negative space. Serene resolution.",
                    "seedance_2_0": "Static extreme wide shot of [Character A: woman in white linen dress] standing motionless in shallow lake water. Dawn mist parts around her small figure. Warm golden light fills the frame. Vast negative space. Birds grow louder. Cello and piano resolve to major chord.",
                    "veo_3_1": "Static extreme wide shot of a woman in white linen dress standing motionless in shallow lake water at dawn. Mist parts gently around her small figure. Morning light grows warmer, transforming cool pastels to golden tones. Vast negative space emphasizes solitude and peace. Birds sing as music resolves.",
                },
            },
        ],
        "sequence": {
            "emotional_arc": [
                {"shot_number": 1, "emotion": "고요", "intensity": 0.2, "description": "새벽 호수의 정적"},
                {"shot_number": 2, "emotion": "평화", "intensity": 0.7, "description": "물에 들어가는 의식적 행위"},
                {"shot_number": 3, "emotion": "초월", "intensity": 0.5, "description": "자연과 하나 된 고요"},
            ],
            "visual_rhythm": {
                "camera_distance_curve": ["EWS", "MS", "EWS"],
                "edit_tempo": "느린 정적 → 부드러운 접근 → 다시 넓은 정적",
            },
            "color_progression": [
                {"shot_number": 1, "temperature": "cool", "palette": "파스텔 쿨톤, 안개빛"},
                {"shot_number": 2, "temperature": "warm", "palette": "골든 림 라이트, 따뜻한 전환"},
                {"shot_number": 3, "temperature": "warm", "palette": "골든 워밍, 넓은 여백"},
            ],
            "continuity_anchors": {
                "character_anchors": ["[Character A: late-40s woman, white linen dress, silver hair]"],
                "style_anchors": ["ethereal dawn", "mirror water", "soft pastels to gold"],
                "lighting_anchors": ["natural dawn light, gradually warming"],
            },
            "five_domains": {
                "character_dynamics": "Character A: approaches lake → enters water → stands still. Minimal action, maximal presence.",
                "background_continuity": "Misty lake at dawn throughout. Same body of water, mist gradually thinning as sun rises.",
                "relationship_evolution": "Character and nature — separation → immersion → unity",
                "camera_evolution": "Static EWS → slow push-in MS → return to static EWS (breathing pattern)",
                "lighting_evolution": "Cool dawn pastels → warm golden rim light → full golden morning",
            },
        },
    },
}


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
