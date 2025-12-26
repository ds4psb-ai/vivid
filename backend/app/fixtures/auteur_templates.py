"""Fixture data for auteur templates."""
from __future__ import annotations

from typing import Dict, List, Optional

from app.fixtures.auteur_capsules import PATTERN_VERSION
from app.graph_utils import collect_storyboard_refs
from app.template_graph import build_template_graph


def build_meta(
    notebook_id: str,
    guide_types: Optional[List[str]] = None,
    evidence_refs: Optional[List[str]] = None,
    story_beats: Optional[List[Dict]] = None,
    storyboard_cards: Optional[List[Dict]] = None,
) -> Dict:
    resolved_guide_types = guide_types or ["homage", "variation"]
    resolved_refs = evidence_refs or [f"db:notebook_library:{notebook_id}"]
    storyboard_cards = storyboard_cards or []
    return {
        "guide_sources": [
            {
                "notebook_id": notebook_id,
                "guide_types": resolved_guide_types,
            }
        ],
        "narrative_seeds": {
            "story_beats": story_beats or [],
            "storyboard_cards": storyboard_cards,
        },
        "production_contract": {
            "shot_contracts": [],
            "prompt_contracts": [],
            "prompt_contract_version": "v1",
            "storyboard_refs": collect_storyboard_refs(storyboard_cards),
        },
        "evidence_refs": resolved_refs,
    }



PRODUCTION_STORY_BEATS = [
    {"beat": "Setup", "note": "비 오는 밤, 주인공이 빈 무대를 바라본다."},
    {"beat": "Turn", "note": "조명이 켜지고 리허설이 시작된다."},
    {"beat": "Climax", "note": "완벽한 동선으로 피날레를 만든다."},
]

PRODUCTION_STORYBOARD_CARDS = [
    {
        "shot": 1,
        "composition": "wide shot, stage silhouette",
        "dominant_color": "#0F172A",
        "accent_color": "#F59E0B",
        "pacing_note": "slow",
    },
    {
        "shot": 2,
        "composition": "medium shot, side profile",
        "dominant_color": "#1E293B",
        "accent_color": "#38BDF8",
        "pacing_note": "steady",
    },
    {
        "shot": 3,
        "composition": "close-up, spotlight",
        "dominant_color": "#111827",
        "accent_color": "#F97316",
        "pacing_note": "hold",
    },
]

PRODUCTION_SHOT_CONTRACTS = [
    {
        "shot_id": "shot-01",
        "sequence_id": "seq-01",
        "scene_id": "scene-01",
        "shot_type": "wide",
        "aspect_ratio": "2.39:1",
        "lens": "40mm anamorphic",
        "film_stock": "Kodak Vision3 250D",
        "lighting": "single spotlight rim",
        "time_of_day": "night",
        "mood": "anticipation",
        "character": {
            "name": "PROTAGONIST",
            "age": "20s",
            "wardrobe": "black rehearsal suit",
            "notes": "focused gaze",
        },
        "pose_motion": "slow walk toward center stage",
        "dialogue": "",
        "environment_layers": {
            "foreground": "dust particles in spotlight",
            "midground": "silhouette of performer",
            "background": "empty seats fading into darkness",
        },
        "continuity_tags": ["character:protagonist", "location:stage", "palette:slate"],
        "seed_image_ref": "nb:storyboard:shot-01",
        "duration_sec": 4,
        "palette": {"primary": "#0F172A", "accent": "#F59E0B"},
    },
    {
        "shot_id": "shot-02",
        "sequence_id": "seq-01",
        "scene_id": "scene-01",
        "shot_type": "medium",
        "aspect_ratio": "2.39:1",
        "lens": "50mm anamorphic",
        "film_stock": "Kodak Vision3 250D",
        "lighting": "soft key + blue backlight",
        "time_of_day": "night",
        "mood": "discipline",
        "character": {
            "name": "PROTAGONIST",
            "age": "20s",
            "wardrobe": "black rehearsal suit",
            "notes": "counting beats under breath",
        },
        "pose_motion": "stretching and marking choreography",
        "dialogue": "Count to eight.",
        "environment_layers": {
            "foreground": "stage tape markings",
            "midground": "profile of performer",
            "background": "mirror wall glow",
        },
        "continuity_tags": ["character:protagonist", "location:stage", "palette:midnight"],
        "seed_image_ref": "nb:storyboard:shot-02",
        "duration_sec": 3,
        "palette": {"primary": "#1E293B", "accent": "#38BDF8"},
    },
    {
        "shot_id": "shot-03",
        "sequence_id": "seq-01",
        "scene_id": "scene-01",
        "shot_type": "close-up",
        "aspect_ratio": "2.39:1",
        "lens": "85mm anamorphic",
        "film_stock": "Kodak Vision3 250D",
        "lighting": "hard spotlight",
        "time_of_day": "night",
        "mood": "resolve",
        "character": {
            "name": "PROTAGONIST",
            "age": "20s",
            "wardrobe": "black rehearsal suit",
            "notes": "steady breathing",
        },
        "pose_motion": "still, eyes locked forward",
        "dialogue": "This is it.",
        "environment_layers": {
            "foreground": "sweat catching light",
            "midground": "focused face in frame",
            "background": "dark stage curtains",
        },
        "continuity_tags": ["character:protagonist", "location:stage", "palette:ember"],
        "seed_image_ref": "nb:storyboard:shot-03",
        "duration_sec": 3,
        "palette": {"primary": "#111827", "accent": "#F97316"},
    },
]

PRODUCTION_PROMPT_CONTRACTS = [
    {
        "shot_id": "shot-01",
        "prompt": "Wide shot, 2.39:1. Kodak Vision3 250D, subtle grain. 40mm anamorphic. PROTAGONIST in black rehearsal suit, slow walk toward center stage. Foreground: dust particles in spotlight. Midground: silhouette of performer. Background: empty seats fading into darkness. Mood: anticipation.",
    },
    {
        "shot_id": "shot-02",
        "prompt": "Medium shot, 2.39:1. Kodak Vision3 250D, soft key + blue backlight. 50mm anamorphic. PROTAGONIST stretching and marking choreography, counting beats. Foreground: stage tape markings. Midground: profile of performer. Background: mirror wall glow. Mood: discipline.",
    },
    {
        "shot_id": "shot-03",
        "prompt": "Close-up, 2.39:1. Kodak Vision3 250D, hard spotlight. 85mm anamorphic. PROTAGONIST still, eyes locked forward. Foreground: sweat catching light. Midground: focused face in frame. Background: dark stage curtains. Mood: resolve. Dialogue: \"This is it.\"",
    },
]


def build_production_meta(notebook_id: str, guide_types: Optional[List[str]] = None) -> Dict:
    meta = build_meta(
        notebook_id,
        guide_types,
        story_beats=PRODUCTION_STORY_BEATS,
        storyboard_cards=PRODUCTION_STORYBOARD_CARDS,
    )
    meta["production_contract"] = {
        "shot_contracts": PRODUCTION_SHOT_CONTRACTS,
        "prompt_contracts": PRODUCTION_PROMPT_CONTRACTS,
        "prompt_contract_version": "v1",
        "storyboard_refs": collect_storyboard_refs(PRODUCTION_STORYBOARD_CARDS),
    }
    return meta


TEMPLATES: List[Dict] = [
    {
        "slug": "tmpl-auteur-bong",
        "title": "구조적 긴장",
        "description": "정교한 동선과 장르 전환의 긴장감을 설계합니다.",
        "tags": ["스릴러", "풍자", "다이내믹"],
        "preview_video_url": "/images/templates/bong_tension.png",
        "graph_data": build_template_graph(
            "auteur.bong-joon-ho",
            "1.0.1",
            {
                "style_intensity": 0.7,
                "pacing": "medium",
                "color_bias": "cool",
                "camera_motion": "controlled",
                "tension_bias": 0.7,
            },
            pattern_version=PATTERN_VERSION,
            meta=build_meta("nlb-auteur-bong", ["homage", "storyboard"]),
        ),
    },
    {
        "slug": "tmpl-auteur-park",
        "title": "대칭 누아르",
        "description": "강박적 대칭과 강한 대비로 복수 서사를 강화합니다.",
        "tags": ["누아르", "강렬", "스타일리시"],
        "preview_video_url": "/images/templates/park_symmetry.png",
        "graph_data": build_template_graph(
            "auteur.park-chan-wook",
            "1.0.1",
            {
                "style_intensity": 0.75,
                "pacing": "medium",
                "color_bias": "warm",
                "camera_motion": "controlled",
                "symmetry_bias": 0.8,
            },
            pattern_version=PATTERN_VERSION,
            meta=build_meta("nlb-auteur-park", ["homage", "variation"]),
        ),
    },
    {
        "slug": "tmpl-auteur-shinkai",
        "title": "빛의 하늘",
        "description": "현실적인 빛과 구름, 감정의 여운을 살립니다.",
        "tags": ["애니메이션", "로맨스", "풍경"],
        "preview_video_url": "/images/templates/shinkai_sky.png",
        "graph_data": build_template_graph(
            "auteur.shinkai",
            "1.0.1",
            {
                "style_intensity": 0.7,
                "pacing": "slow",
                "color_bias": "warm",
                "camera_motion": "controlled",
                "light_diffusion": 0.75,
            },
            pattern_version=PATTERN_VERSION,
            meta=build_meta("nlb-auteur-shinkai", ["summary", "storyboard"]),
        ),
    },
    {
        "slug": "tmpl-auteur-leejunho",
        "title": "무대 리듬",
        "description": "음악 싱크 컷과 퍼포먼스 에너지에 집중합니다.",
        "tags": ["뮤직", "퍼포먼스", "리듬"],
        "preview_video_url": "/images/templates/lee_rhythm.png",
        "graph_data": build_template_graph(
            "auteur.lee-junho",
            "1.0.1",
            {
                "style_intensity": 0.68,
                "pacing": "medium",
                "color_bias": "neutral",
                "camera_motion": "dynamic",
                "music_sync": 0.7,
            },
            pattern_version=PATTERN_VERSION,
            meta=build_meta("nlb-auteur-leejunho", ["homage", "variation"]),
        ),
    },
    {
        "slug": "tmpl-auteur-na",
        "title": "거친 추격",
        "description": "거친 핸드헬드와 긴박한 추격을 쌓습니다.",
        "tags": ["액션", "추격", "거칠음"],
        "preview_video_url": "/images/templates/na_chase.png",
        "graph_data": build_template_graph(
            "auteur.na-hongjin",
            "1.0.1",
            {
                "style_intensity": 0.8,
                "pacing": "fast",
                "color_bias": "cool",
                "camera_motion": "dynamic",
                "chaos_bias": 0.8,
            },
            pattern_version=PATTERN_VERSION,
            meta=build_meta("nlb-auteur-na", ["homage", "variation"]),
        ),
    },
    {
        "slug": "tmpl-auteur-hong",
        "title": "정적 대화",
        "description": "롱테이크와 어색한 침묵, 돌연한 줌으로 대화를 밀도 있게 만듭니다.",
        "tags": ["드라마", "미니멀", "대화"],
        "preview_video_url": "/images/templates/hong_static.png",
        "graph_data": build_template_graph(
            "auteur.hong-sangsoo",
            "1.0.1",
            {
                "style_intensity": 0.65,
                "pacing": "slow",
                "color_bias": "neutral",
                "camera_motion": "static",
                "stillness": 0.85,
            },
            pattern_version=PATTERN_VERSION,
            meta=build_meta("nlb-auteur-hong", ["summary", "persona"]),
        ),
    },
    {
        "slug": "tmpl-production-stage",
        "title": "프로덕션: 무대 리허설",
        "description": "샷 리스트 → 프롬프트 → 생성까지 이어지는 AI 프로덕션 템플릿입니다.",
        "tags": ["프로덕션", "샷리스트", "프롬프트", "쇼트폼"],
        "preview_video_url": "/images/templates/production_stage.png",
        "graph_data": build_template_graph(
            "production.stage-rehearsal",
            "1.0.0",
            {
                "style_intensity": 0.7,
                "pacing": "medium",
                "color_bias": "neutral",
                "camera_motion": "controlled",
                "music_sync": 0.6,
                "render_quality": "preview",
                "aspect_ratio": "2.39:1",
                "lens": "50mm anamorphic",
                "film_stock": "Kodak Vision3 250D",
                "time_of_day": "night",
                "mood": "anticipation",
            },
            pattern_version=PATTERN_VERSION,
            story_beats=PRODUCTION_STORY_BEATS,
            storyboard_cards=PRODUCTION_STORYBOARD_CARDS,
            meta=build_production_meta("nlb-production-stage", ["story", "storyboard", "variation"]),
            capsule_label="프로덕션 캡슐",
        ),
    },
]
