"""Teaching Capsule Fixtures: Capsule specs for teaching tools.

These capsules provide AI-powered teaching tools for video production:
- Prompt Generator: Veo video prompt generation
- Storyboard Creator: Scene-based storyboard creation
- Image Generator: AI image prompt optimization
- Reference Analyzer: Video reference analysis
"""
from __future__ import annotations

from typing import List, Dict, Any


TEACHING_CAPSULES: List[Dict[str, Any]] = [
    {
        "capsule_key": "teaching.prompt.generate",
        "version": "1.0.0",
        "credit_costs": {
            "gemini-3-flash-preview": 5,
            "gemini-2.5-pro": 15,
            "gemini-3-flash-preview": 5,
        },
        "spec": {
            "name": "Veo 프롬프트 생성기",
            "description": "AI 기반 Veo 3.1 비디오 프롬프트 생성",
            "category": "teaching",
            "adapter": "teaching",
            "inputs": {
                "topic": {
                    "type": "string",
                    "required": True,
                    "description": "영상 주제 또는 컨셉",
                },
                "style": {
                    "type": "string",
                    "required": False,
                    "default": "cinematic",
                    "description": "시각적 스타일 (cinematic, documentary, etc.)",
                },
                "mood": {
                    "type": "string",
                    "required": False,
                    "default": "neutral",
                    "description": "감정적 톤",
                },
                "duration": {
                    "type": "string",
                    "required": False,
                    "default": "15 seconds",
                    "description": "목표 영상 길이",
                },
                "language": {
                    "type": "string",
                    "required": False,
                    "default": "ko",
                    "description": "출력 언어 (ko/en)",
                },
            },
            "outputs": {
                "prompt": {
                    "type": "string",
                    "description": "생성된 Veo 프롬프트",
                },
                "negative_prompt": {
                    "type": "string",
                    "description": "네거티브 프롬프트",
                },
                "style": {
                    "type": "object",
                    "description": "스타일 상세 (cinematography, lighting, color_grade)",
                },
                "technical": {
                    "type": "object",
                    "description": "기술 사양 (aspect_ratio, duration, fps)",
                },
            },
            "params": {
                "model": {
                    "type": "string",
                    "default": "gemini-3-flash-preview",
                    "options": ["gemini-3-flash-preview", "gemini-2.5-pro"],
                },
            },
        },
    },
    {
        "capsule_key": "teaching.storyboard.create",
        "version": "1.0.0",
        "credit_costs": {
            "gemini-3-flash-preview": 10,
            "gemini-2.5-pro": 25,
            "gemini-3-flash-preview": 10,
        },
        "spec": {
            "name": "스토리보드 생성기",
            "description": "컨셉 기반 스토리보드 카드 생성",
            "category": "teaching",
            "adapter": "teaching",
            "inputs": {
                "concept": {
                    "type": "string",
                    "required": True,
                    "description": "스토리 컨셉 또는 영상 아이디어",
                },
                "prompt": {
                    "type": "string",
                    "required": False,
                    "description": "확장할 Veo 프롬프트 (선택)",
                },
                "scene_count": {
                    "type": "integer",
                    "required": False,
                    "default": 5,
                    "description": "생성할 씬 개수",
                },
                "language": {
                    "type": "string",
                    "required": False,
                    "default": "ko",
                    "description": "출력 언어",
                },
            },
            "outputs": {
                "scenes": {
                    "type": "array",
                    "description": "스토리보드 씬 카드 배열",
                },
            },
            "params": {
                "model": {
                    "type": "string",
                    "default": "gemini-3-flash-preview",
                },
            },
        },
    },
    {
        "capsule_key": "teaching.image.generate",
        "version": "1.0.0",
        "credit_costs": {
            "gemini-3-flash-preview": 5,
            "gemini-2.5-pro": 12,
            "gemini-3-flash-preview": 5,
        },
        "spec": {
            "name": "이미지 프롬프트 생성기",
            "description": "AI 이미지 생성용 최적화 프롬프트",
            "category": "teaching",
            "adapter": "teaching",
            "inputs": {
                "description": {
                    "type": "string",
                    "required": True,
                    "description": "이미지 설명",
                },
                "style": {
                    "type": "string",
                    "required": False,
                    "default": "photorealistic",
                    "description": "아트 스타일",
                },
                "aspect_ratio": {
                    "type": "string",
                    "required": False,
                    "default": "16:9",
                    "description": "이미지 비율",
                },
            },
            "outputs": {
                "prompt": {
                    "type": "string",
                    "description": "최적화된 이미지 프롬프트",
                },
                "parameters": {
                    "type": "object",
                    "description": "생성 파라미터",
                },
            },
            "params": {
                "model": {
                    "type": "string",
                    "default": "gemini-3-flash-preview",
                },
            },
        },
    },
    {
        "capsule_key": "teaching.reference.analyze",
        "version": "1.0.0",
        "credit_costs": {
            "gemini-3-flash-preview": 8,
            "gemini-2.5-pro": 20,
            "gemini-3-flash-preview": 8,
        },
        "spec": {
            "name": "레퍼런스 분석기",
            "description": "영상 레퍼런스 시네마틱 분석",
            "category": "teaching",
            "adapter": "teaching",
            "inputs": {
                "video_description": {
                    "type": "string",
                    "required": True,
                    "description": "분석할 영상 설명",
                },
                "focus_areas": {
                    "type": "array",
                    "required": False,
                    "default": ["composition", "lighting", "color", "movement"],
                    "description": "분석 집중 영역",
                },
            },
            "outputs": {
                "analysis": {
                    "type": "object",
                    "description": "시네마틱 분석 결과",
                },
            },
            "params": {
                "model": {
                    "type": "string",
                    "default": "gemini-3-flash-preview",
                },
            },
        },
    },
]


def get_teaching_capsule_specs() -> List[Dict[str, Any]]:
    """Return all teaching capsule specs for database seeding."""
    return TEACHING_CAPSULES
