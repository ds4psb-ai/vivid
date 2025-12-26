"""Fixture data for auteur capsule specs."""
from __future__ import annotations

import copy

COMMON_INPUTS = {
    "source_id": {"type": "string", "required": False},
    "emotion_curve": {"type": "float[]", "required": True},
    "scene_summary": {"type": "string", "required": True},
    "duration_sec": {"type": "number", "required": True},
}
REQUIRED_INPUTS = ["emotion_curve", "scene_summary", "duration_sec"]

COMMON_OUTPUTS = {
    "style_vector": {"type": "float[]"},
    "palette": {"type": "string[]"},
    "composition_hints": {"type": "string[]"},
    "pacing_hints": {"type": "string[]"},
}

COMMON_INPUT_CONTRACTS = {
    "required": REQUIRED_INPUTS,
    "optional": ["source_id"],
    "maxUpstream": 5,
    "contextMode": "aggregate",
}

COMMON_OUTPUT_CONTRACTS = {
    "types": list(COMMON_OUTPUTS.keys()),
}

COMMON_PARAM_DEFS = {
    "style_intensity": {"type": "number", "min": 0.4, "max": 1.0, "step": 0.05},
    "pacing": {"type": "enum", "options": ["slow", "medium", "fast"]},
    "color_bias": {"type": "enum", "options": ["cool", "neutral", "warm"]},
    "camera_motion": {"type": "enum", "options": ["static", "controlled", "dynamic"]},
}

POLICY = {"evidence": "summary_only", "allowRawLogs": False}
PATTERN_VERSION = "v1"

PRODUCTION_INPUTS = {
    "scene_summary": {"type": "string", "required": True},
    "story_beats": {"type": "object[]", "required": False},
    "storyboard_cards": {"type": "object[]", "required": False},
    "duration_sec": {"type": "number", "required": False},
}

PRODUCTION_OUTPUTS = {
    "shot_contracts": {"type": "object[]"},
    "prompt_contracts": {"type": "object[]"},
    "prompt_contract_version": {"type": "string"},
    "storyboard_refs": {"type": "string[]"},
}

PRODUCTION_INPUT_CONTRACTS = {
    "required": ["scene_summary"],
    "optional": ["story_beats", "storyboard_cards", "duration_sec"],
    "maxUpstream": 8,
    "contextMode": "aggregate",
}

PRODUCTION_OUTPUT_CONTRACTS = {
    "types": list(PRODUCTION_OUTPUTS.keys()),
}

PRODUCTION_PARAM_DEFS = {
    "render_quality": {"type": "enum", "options": ["preview", "final"], "default": "preview", "visibility": "public"},
    "aspect_ratio": {"type": "enum", "options": ["16:9", "9:16", "2.39:1"], "default": "2.39:1", "visibility": "public"},
    "lens": {
        "type": "enum",
        "options": ["35mm anamorphic", "50mm anamorphic", "85mm anamorphic"],
        "default": "50mm anamorphic",
        "visibility": "public",
    },
    "film_stock": {
        "type": "enum",
        "options": ["Kodak Vision3 250D", "Kodak Vision3 500T", "Digital clean"],
        "default": "Kodak Vision3 250D",
        "visibility": "public",
    },
    "time_of_day": {"type": "enum", "options": ["day", "sunset", "night"], "default": "night", "visibility": "public"},
    "mood": {
        "type": "enum",
        "options": ["neutral", "anticipation", "discipline", "resolve", "intense"],
        "default": "neutral",
        "visibility": "public",
    },
}

COMMON_SPEC_BASE = {
    "inputs": COMMON_INPUTS,
    "outputs": COMMON_OUTPUTS,
    "inputContracts": COMMON_INPUT_CONTRACTS,
    "outputContracts": COMMON_OUTPUT_CONTRACTS,
    "patternVersion": PATTERN_VERSION,
}


def build_exposed_params(defaults: dict, signature: dict) -> dict:
    exposed = copy.deepcopy(COMMON_PARAM_DEFS)
    for key, value in defaults.items():
        exposed[key]["default"] = value
        exposed[key]["visibility"] = "public"
    for key, value in signature.items():
        exposed[key] = {
            "type": "number",
            "min": 0.0,
            "max": 1.0,
            "step": 0.1,
            "default": value,
            "visibility": "public",
        }
    return exposed


CAPSULE_SPECS = [
    {
        "capsule_key": "auteur.bong-joon-ho",
        "version": "1.0.1",
        "display_name": "봉준호 스타일 캡슐",
        "description": "구조적 긴장과 장르 믹스의 리듬을 설계합니다.",
        "spec": {
            **COMMON_SPEC_BASE,
            "exposedParams": build_exposed_params(
                {
                    "style_intensity": 0.7,
                    "pacing": "medium",
                    "color_bias": "cool",
                    "camera_motion": "controlled",
                },
                {"tension_bias": 0.7},
            ),
            "policy": POLICY,
            "adapter": {
                "type": "hybrid",
                "internalGraphRef": "private-dag://auteur/bong/v1",
            },
        },
    },
    {
        "capsule_key": "auteur.park-chan-wook",
        "version": "1.0.1",
        "display_name": "박찬욱 스타일 캡슐",
        "description": "대칭 미장센과 강한 대비를 강조합니다.",
        "spec": {
            **COMMON_SPEC_BASE,
            "exposedParams": build_exposed_params(
                {
                    "style_intensity": 0.75,
                    "pacing": "medium",
                    "color_bias": "warm",
                    "camera_motion": "controlled",
                },
                {"symmetry_bias": 0.8},
            ),
            "policy": POLICY,
            "adapter": {
                "type": "hybrid",
                "internalGraphRef": "private-dag://auteur/park/v1",
            },
        },
    },
    {
        "capsule_key": "auteur.shinkai",
        "version": "1.0.1",
        "display_name": "신카이 스타일 캡슐",
        "description": "감정적인 빛 확산과 서정적인 컬러 전이를 구성합니다.",
        "spec": {
            **COMMON_SPEC_BASE,
            "exposedParams": build_exposed_params(
                {
                    "style_intensity": 0.7,
                    "pacing": "slow",
                    "color_bias": "warm",
                    "camera_motion": "controlled",
                },
                {"light_diffusion": 0.75},
            ),
            "policy": POLICY,
            "adapter": {
                "type": "hybrid",
                "internalGraphRef": "private-dag://auteur/shinkai/v1",
            },
        },
    },
    {
        "capsule_key": "auteur.lee-junho",
        "version": "1.0.1",
        "display_name": "이준호 스타일 캡슐",
        "description": "음악 싱크 비트와 리듬감 있는 전개를 만듭니다.",
        "spec": {
            **COMMON_SPEC_BASE,
            "exposedParams": build_exposed_params(
                {
                    "style_intensity": 0.68,
                    "pacing": "medium",
                    "color_bias": "neutral",
                    "camera_motion": "dynamic",
                },
                {"music_sync": 0.7},
            ),
            "policy": POLICY,
            "adapter": {
                "type": "hybrid",
                "internalGraphRef": "private-dag://auteur/leejunho/v1",
            },
        },
    },
    {
        "capsule_key": "auteur.na-hongjin",
        "version": "1.0.1",
        "display_name": "나홍진 스타일 캡슐",
        "description": "거친 리얼리즘과 긴박한 서스펜스를 강화합니다.",
        "spec": {
            **COMMON_SPEC_BASE,
            "exposedParams": build_exposed_params(
                {
                    "style_intensity": 0.8,
                    "pacing": "fast",
                    "color_bias": "cool",
                    "camera_motion": "dynamic",
                },
                {"chaos_bias": 0.8},
            ),
            "policy": POLICY,
            "adapter": {
                "type": "hybrid",
                "internalGraphRef": "private-dag://auteur/na/v1",
            },
        },
    },
    {
        "capsule_key": "auteur.hong-sangsoo",
        "version": "1.0.1",
        "display_name": "홍상수 스타일 캡슐",
        "description": "정적 카메라와 대화 중심의 호흡을 유지합니다.",
        "spec": {
            **COMMON_SPEC_BASE,
            "exposedParams": build_exposed_params(
                {
                    "style_intensity": 0.65,
                    "pacing": "slow",
                    "color_bias": "neutral",
                    "camera_motion": "static",
                },
                {"stillness": 0.85},
            ),
            "policy": POLICY,
            "adapter": {
                "type": "hybrid",
                "internalGraphRef": "private-dag://auteur/hong/v1",
            },
        },
    },
    {
        "capsule_key": "production.stage-rehearsal",
        "version": "1.0.0",
        "display_name": "프로덕션 캡슐: 무대 리허설",
        "description": "샷 계약과 프롬프트 계약을 생성하는 프로덕션 캡슐입니다.",
        "spec": {
            "inputs": PRODUCTION_INPUTS,
            "outputs": PRODUCTION_OUTPUTS,
            "inputContracts": PRODUCTION_INPUT_CONTRACTS,
            "outputContracts": PRODUCTION_OUTPUT_CONTRACTS,
            "patternVersion": PATTERN_VERSION,
            "exposedParams": PRODUCTION_PARAM_DEFS,
            "policy": POLICY,
            "adapter": {
                "type": "internal",
                "internalGraphRef": "private-dag://production/stage-rehearsal/v1",
            },
        },
    },
]
