"""Dimension Capsule Fixtures: 4-Stage Video Workflow Capsule Specs.

4-Stage Workflow:
- Stage 1 (Planning): 심연의 거울, 레퍼런스 해석기, 시나리오 생성기
- Stage 2 (Pre-production): 사운드 크래프터, 스토리보드 스케치, 프롬프트 연금술
- Stage 3 (Production): 비주얼 리얼라이저, 비디오 메이커
- Stage 4 (Finishing): 퀄리티 디렉터
"""
from __future__ import annotations

from typing import List, Dict, Any

# Stage definitions for 4-Stage Workflow
WORKFLOW_STAGES = {
    "planning": {"order": 1, "name_ko": "기획", "name_en": "Planning"},
    "pre_production": {"order": 2, "name_ko": "사전 제작", "name_en": "Pre-production"},
    "production": {"order": 3, "name_ko": "제작", "name_en": "Production"},
    "finishing": {"order": 4, "name_ko": "완성", "name_en": "Finishing"},
}

DIMENSION_CAPSULES: List[Dict[str, Any]] = [
    {
        "capsule_key": "teaching.prompt.generate",
        "version": "1.0.0",
        "stage": "pre_production",
        "stage_order": 3,
        "display_name": "프롬프트 연금술",
        "display_name_en": "Prompt Alchemy",
        "route_key": "prompt-alchemy",
        "input_dimensions": ["story-architect", "storyboard-sketch"],
        "output_dimensions": ["visual-realizer", "video-maker"],
        "credit_costs": {
            "gemini-3-flash-preview": 5,
            "gemini-3-pro-preview": 15,
        },
        "spec": {
            "name": "프롬프트 연금술",
            "description": "AI가 이해하는 전문 언어로 번역",
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
                    "options": ["gemini-3-flash-preview", "gemini-3-pro-preview"],
                },
            },
        },
    },
    {
        "capsule_key": "teaching.storyboard.create",
        "version": "1.0.0",
        "stage": "pre_production",
        "stage_order": 2,
        "display_name": "스토리보드 스케치",
        "display_name_en": "Storyboard Sketch",
        "route_key": "storyboard-sketch",
        "input_dimensions": ["story-architect", "reference-decoder"],
        "output_dimensions": ["sound-crafter", "prompt-alchemy"],
        "credit_costs": {
            "gemini-3-flash-preview": 10,
            "gemini-3-pro-preview": 25,
        },
        "spec": {
            "name": "스토리보드 스케치",
            "description": "글을 시각적 컷으로 스케치",
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
        "stage": "production",
        "stage_order": 1,
        "display_name": "비주얼 리얼라이저",
        "display_name_en": "Visual Realizer",
        "route_key": "visual-realizer",
        "input_dimensions": ["prompt-alchemy", "storyboard-sketch"],
        "output_dimensions": ["video-maker", "quality-director"],
        "credit_costs": {
            "gemini-3-flash-preview": 5,
            "gemini-3-pro-preview": 12,
        },
        "spec": {
            "name": "비주얼 리얼라이저",
            "description": "Key Frame 고품질 생성 (Midjourney 스타일)",
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
        "stage": "planning",
        "stage_order": 2,
        "display_name": "레퍼런스 해석기",
        "display_name_en": "Reference Decoder",
        "route_key": "reference-decoder",
        "input_dimensions": ["abyss-mirror"],
        "output_dimensions": ["story-architect", "storyboard-sketch"],
        "credit_costs": {
            "gemini-3-flash-preview": 8,
            "gemini-3-pro-preview": 20,
        },
        "spec": {
            "name": "레퍼런스 해석기",
            "description": "조명, 색감, 연출의 전문가적 분석",
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
    # ==========================================================================
    # Quality Director (퀄리티 디렉터) - Stage 4: Finishing
    # ==========================================================================
    {
        "capsule_key": "dimension.quality.check",
        "version": "1.0.0",
        "stage": "finishing",
        "stage_order": 1,
        "display_name": "퀄리티 디렉터",
        "display_name_en": "Quality Director",
        "route_key": "quality-director",
        "input_dimensions": ["video-maker", "visual-realizer"],
        "output_dimensions": [],
        "credit_costs": {
            "gemini-3-flash-preview": 8,
            "gemini-3-pro-preview": 20,
        },
        "spec": {
            "name": "퀄리티 디렉터",
            "description": "시각적 일관성 및 동작 자연스러움 검수",
            "category": "dimension",
            "adapter": "quality",
            "inputs": {
                "content": {
                    "type": "string",
                    "required": True,
                    "description": "검수할 콘텐츠 (프롬프트, 스크립트, 설명 등)",
                },
                "content_type": {
                    "type": "string",
                    "required": True,
                    "description": "콘텐츠 유형 (prompt, storyboard, script, image_prompt)",
                },
                "criteria": {
                    "type": "array",
                    "required": False,
                    "default": ["aesthetic", "consistency", "safety"],
                    "description": "검수 기준 (aesthetic, ad_suitability, consistency, safety, technical, narrative)",
                },
                "context": {
                    "type": "object",
                    "required": False,
                    "description": "추가 컨텍스트 (브랜드 가이드, 이전 콘텐츠 등)",
                },
            },
            "outputs": {
                "passed": {
                    "type": "boolean",
                    "description": "전체 검수 통과 여부",
                },
                "score": {
                    "type": "number",
                    "description": "종합 점수 (0-100)",
                },
                "criteria_results": {
                    "type": "object",
                    "description": "기준별 상세 결과 {criterion: {score, passed, details}}",
                },
                "issues": {
                    "type": "array",
                    "description": "발견된 문제점 목록",
                },
                "suggestions": {
                    "type": "array",
                    "description": "개선 제안 목록",
                },
            },
            "params": {
                "model": {
                    "type": "string",
                    "default": "gemini-3-pro-preview",
                    "options": ["gemini-3-flash-preview", "gemini-3-pro-preview"],
                    "description": "Pro 모델 권장 (정확도 우선)",
                },
                "threshold": {
                    "type": "number",
                    "default": 70,
                    "description": "통과 임계값 (0-100)",
                },
            },
        },
    },
    # ==========================================================================
    # Aesthetic Director (미학디렉터) - Extended Tool (모든 Stage에서 참조 가능)
    # ==========================================================================
    {
        "capsule_key": "dimension.aesthetic.direct",
        "version": "1.0.0",
        "stage": "planning",
        "stage_order": 4,
        "display_name": "미학디렉터",
        "display_name_en": "Aesthetic Director",
        "route_key": "aesthetic-director",
        "input_dimensions": ["abyss-mirror", "reference-decoder"],
        "output_dimensions": ["story-architect", "visual-realizer"],
        "is_extended": True,
        "credit_costs": {
            "gemini-3-flash-preview": 10,
            "gemini-3-pro-preview": 25,
        },
        "spec": {
            "name": "미학디렉터",
            "description": "시각적 스타일 가이드라인 생성 (6개 감독 스타일 + RAG)",
            "category": "dimension",
            "adapter": "aesthetic",
            "inputs": {
                "concept": {
                    "type": "string",
                    "required": True,
                    "description": "컨셉 또는 주제 설명",
                },
                "reference_style": {
                    "type": "string",
                    "required": False,
                    "description": "참조 스타일 (auteur: bong, park, shinkai, lee, na, hong)",
                },
                "mood": {
                    "type": "string",
                    "required": False,
                    "default": "neutral",
                    "description": "원하는 분위기",
                },
                "target_medium": {
                    "type": "string",
                    "required": False,
                    "default": "video",
                    "description": "대상 미디어 (video, image, animation)",
                },
            },
            "outputs": {
                "visual_guidelines": {
                    "type": "object",
                    "description": "시각적 가이드라인 (composition, lighting, camera, pacing)",
                },
                "color_palette": {
                    "type": "array",
                    "description": "추천 색상 팔레트 (hex 코드 배열)",
                },
                "style_keywords": {
                    "type": "array",
                    "description": "스타일 키워드 목록",
                },
                "avoid_elements": {
                    "type": "array",
                    "description": "피해야 할 요소 목록",
                },
                "auteur_influence": {
                    "type": "object",
                    "description": "매칭된 감독 스타일 정보 (있는 경우)",
                },
            },
            "params": {
                "model": {
                    "type": "string",
                    "default": "gemini-3-pro-preview",
                    "options": ["gemini-3-flash-preview", "gemini-3-pro-preview"],
                },
                "use_rag": {
                    "type": "boolean",
                    "default": True,
                    "description": "RAG 컨텍스트 사용 여부",
                },
            },
        },
    },
    # ==========================================================================
    # Abyss Mirror (심연의 거울) - Stage 1: Planning
    # ==========================================================================
    {
        "capsule_key": "dimension.persona.analyze",
        "version": "1.0.0",
        "stage": "planning",
        "stage_order": 1,
        "display_name": "심연의 거울",
        "display_name_en": "Abyss Mirror",
        "route_key": "abyss-mirror",
        "input_dimensions": [],
        "output_dimensions": ["reference-decoder", "story-architect", "aesthetic-director"],
        "credit_costs": {
            "gemini-3-flash-preview": 5,
            "gemini-3-pro-preview": 12,
        },
        "spec": {
            "name": "심연의 거울",
            "description": "나만의 취향과 창작 DNA 분석 (Gemini 기반 7단계 분석)",
            "category": "dimension",
            "adapter": "persona",
            "inputs": {
                "user_message": {
                    "type": "string",
                    "required": True,
                    "description": "사용자 응답 메시지",
                },
                "analysis_stage": {
                    "type": "string",
                    "required": False,
                    "default": "intro",
                    "description": "분석 단계 (intro, saju, mbti, subconscious, unconscious, background, synthesis)",
                },
                "persona_data": {
                    "type": "object",
                    "required": False,
                    "description": "누적된 페르소나 데이터",
                },
                "birth_info": {
                    "type": "object",
                    "required": False,
                    "description": "생년월일시 정보 (사주 분석용)",
                },
            },
            "outputs": {
                "assistant_message": {
                    "type": "string",
                    "description": "다음 질문 또는 분석 결과",
                },
                "next_stage": {
                    "type": "string",
                    "description": "다음 분석 단계",
                },
                "persona_update": {
                    "type": "object",
                    "description": "업데이트된 페르소나 데이터",
                },
                "analysis_complete": {
                    "type": "boolean",
                    "description": "분석 완료 여부",
                },
                "final_persona": {
                    "type": "object",
                    "description": "최종 페르소나 프로필 (완료 시)",
                },
            },
            "params": {
                "model": {
                    "type": "string",
                    "default": "gemini-3-pro-preview",
                    "options": ["gemini-3-flash-preview", "gemini-3-pro-preview"],
                },
                "depth_level": {
                    "type": "string",
                    "default": "deep",
                    "options": ["quick", "standard", "deep"],
                    "description": "분석 깊이 (quick: 3단계, standard: 5단계, deep: 7단계)",
                },
            },
        },
    },
    # ==========================================================================
    # Video Maker (비디오 메이커) - Stage 3: Production
    # ==========================================================================
    {
        "capsule_key": "veo.video.generate",
        "version": "1.0.0",
        "stage": "production",
        "stage_order": 2,
        "display_name": "비디오 메이커",
        "display_name_en": "Video Maker",
        "route_key": "video-maker",
        "input_dimensions": ["visual-realizer", "prompt-alchemy", "sound-crafter"],
        "output_dimensions": ["quality-director"],
        "credit_costs": {
            "veo-3.1-generate-preview": 200,
            "veo-3.1-fast-generate-preview": 60,
        },
        "spec": {
            "name": "비디오 메이커",
            "description": "영상 변환 및 모션 제어 (Veo 3.1, Kling)",
            "category": "generation",
            "adapter": "veo",
            "inputs": {
                "prompt": {
                    "type": "string",
                    "required": True,
                    "description": "비디오 생성 프롬프트",
                },
                "negative_prompt": {
                    "type": "string",
                    "required": False,
                    "description": "피해야 할 요소",
                },
                "duration_seconds": {
                    "type": "integer",
                    "required": False,
                    "default": 8,
                    "enum": [4, 6, 8],
                    "description": "비디오 길이 (초)",
                },
                "aspect_ratio": {
                    "type": "string",
                    "required": False,
                    "default": "16:9",
                    "description": "화면 비율",
                },
                "include_audio": {
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "description": "오디오 포함 여부 (Veo 3.1)",
                },
            },
            "outputs": {
                "video_uri": {
                    "type": "string",
                    "description": "생성된 비디오 URI",
                },
                "duration_ms": {
                    "type": "integer",
                    "description": "생성 소요 시간 (밀리초)",
                },
                "metadata": {
                    "type": "object",
                    "description": "비디오 메타데이터",
                },
            },
            "params": {
                "model": {
                    "type": "string",
                    "default": "veo-3.1-generate-preview",
                    "options": ["veo-3.1-generate-preview", "veo-3.1-fast-generate-preview"],
                },
                "max_wait_seconds": {
                    "type": "integer",
                    "default": 360,
                    "description": "최대 대기 시간 (초)",
                },
            },
        },
    },
    # ==========================================================================
    # Story Architect (시나리오 생성기) - Stage 1: Planning [NEW]
    # ==========================================================================
    {
        "capsule_key": "dimension.story.architect",
        "version": "1.0.0",
        "stage": "planning",
        "stage_order": 3,
        "display_name": "시나리오 생성기",
        "display_name_en": "Story Architect",
        "route_key": "story-architect",
        "input_dimensions": ["abyss-mirror", "reference-decoder"],
        "output_dimensions": ["storyboard-sketch", "sound-crafter", "prompt-alchemy"],
        "credit_costs": {
            "gemini-3-flash-preview": 10,
            "gemini-3-pro-preview": 25,
        },
        "spec": {
            "name": "시나리오 생성기",
            "description": "DNA와 스타일을 결합한 시나리오 작성",
            "category": "dimension",
            "adapter": "story",
            "inputs": {
                "concept": {
                    "type": "string",
                    "required": True,
                    "min_length": 10,
                    "max_length": 3000,
                    "description": "영상 컨셉 또는 아이디어",
                },
                "persona_data": {
                    "type": "object",
                    "required": False,
                    "description": "심연의 거울에서 생성된 페르소나 데이터",
                },
                "reference_analysis": {
                    "type": "object",
                    "required": False,
                    "description": "레퍼런스 해석기에서 생성된 분석 데이터",
                },
                "genre": {
                    "type": "string",
                    "required": False,
                    "default": "drama",
                    "enum": ["drama", "ad", "mv", "documentary", "short"],
                    "description": "영상 장르",
                },
                "duration": {
                    "type": "string",
                    "required": False,
                    "default": "60s",
                    "enum": ["15s", "30s", "60s", "3m", "5m"],
                    "description": "목표 영상 길이",
                },
                "structure": {
                    "type": "string",
                    "required": False,
                    "default": "3act",
                    "enum": ["3act", "hero", "circular", "montage"],
                    "description": "스토리 구조",
                },
                "language": {
                    "type": "string",
                    "required": False,
                    "default": "ko",
                    "description": "출력 언어",
                },
            },
            "outputs": {
                "title": {
                    "type": "string",
                    "description": "시나리오 제목",
                },
                "logline": {
                    "type": "string",
                    "description": "한 줄 요약",
                },
                "synopsis": {
                    "type": "string",
                    "description": "3-5문장 개요",
                },
                "structure": {
                    "type": "array",
                    "description": "구조별 상세 [{act, description, duration, emotion}]",
                },
                "characters": {
                    "type": "array",
                    "description": "등장인물 [{name, role, arc, traits}]",
                },
                "themes": {
                    "type": "array",
                    "description": "주제 키워드 목록",
                },
                "visual_motifs": {
                    "type": "array",
                    "description": "시각적 모티프 (레퍼런스 연결)",
                },
                "next_dimension": {
                    "type": "string",
                    "description": "추천 다음 차원",
                },
            },
            "params": {
                "model": {
                    "type": "string",
                    "default": "gemini-3-pro-preview",
                    "options": ["gemini-3-flash-preview", "gemini-3-pro-preview"],
                },
                "use_rag": {
                    "type": "boolean",
                    "default": True,
                    "description": "RAG 컨텍스트 사용 여부",
                },
            },
        },
    },
    # ==========================================================================
    # Sound Crafter (사운드 크래프터) - Stage 2: Pre-production [NEW]
    # ==========================================================================
    {
        "capsule_key": "dimension.sound.craft",
        "version": "1.0.0",
        "stage": "pre_production",
        "stage_order": 1,
        "display_name": "사운드 크래프터",
        "display_name_en": "Sound Crafter",
        "route_key": "sound-crafter",
        "input_dimensions": ["story-architect", "storyboard-sketch"],
        "output_dimensions": ["video-maker"],
        "credit_costs": {
            "gemini-3-flash-preview": 8,
            "gemini-3-pro-preview": 18,
        },
        "spec": {
            "name": "사운드 크래프터",
            "description": "BGM 및 성우 내레이션 생성 (Suno, Udio 호환)",
            "category": "dimension",
            "adapter": "sound",
            "inputs": {
                "concept": {
                    "type": "string",
                    "required": True,
                    "min_length": 10,
                    "max_length": 2000,
                    "description": "사운드 컨셉 또는 분위기 설명",
                },
                "storyboard": {
                    "type": "array",
                    "required": False,
                    "description": "스토리보드 데이터 (씬 배열)",
                },
                "sound_type": {
                    "type": "string",
                    "required": False,
                    "default": "bgm",
                    "enum": ["bgm", "sfx", "narration", "full"],
                    "description": "사운드 유형",
                },
                "mood": {
                    "type": "string",
                    "required": False,
                    "default": "neutral",
                    "description": "원하는 분위기",
                },
                "genre": {
                    "type": "string",
                    "required": False,
                    "default": "cinematic",
                    "enum": ["cinematic", "electronic", "acoustic", "ambient", "pop", "classical"],
                    "description": "음악 장르",
                },
                "tempo": {
                    "type": "string",
                    "required": False,
                    "default": "medium",
                    "enum": ["slow", "medium", "fast", "dynamic"],
                    "description": "템포",
                },
                "duration": {
                    "type": "string",
                    "required": False,
                    "default": "60s",
                    "description": "목표 길이",
                },
                "target_platform": {
                    "type": "string",
                    "required": False,
                    "default": "suno",
                    "enum": ["suno", "udio", "elevenlabs"],
                    "description": "타겟 플랫폼",
                },
                "language": {
                    "type": "string",
                    "required": False,
                    "default": "ko",
                    "description": "출력 언어",
                },
            },
            "outputs": {
                "music_prompt": {
                    "type": "string",
                    "description": "Suno/Udio용 음악 프롬프트",
                },
                "style_tags": {
                    "type": "array",
                    "description": "스타일 태그 목록 [cinematic, emotional, ...]",
                },
                "bpm_range": {
                    "type": "string",
                    "description": "권장 BPM 범위 (예: 80-100 BPM)",
                },
                "key_signature": {
                    "type": "string",
                    "description": "권장 조성 (예: C minor)",
                },
                "instrumentation": {
                    "type": "array",
                    "description": "악기 구성 [piano, strings, ...]",
                },
                "dynamics": {
                    "type": "string",
                    "description": "다이나믹 설명 (예: starts soft, builds to climax)",
                },
                "narration_script": {
                    "type": "string",
                    "description": "내레이션 스크립트 (narration 모드)",
                },
                "voice_direction": {
                    "type": "object",
                    "description": "성우 디렉션 {tone, pace, emotion}",
                },
                "sfx_cues": {
                    "type": "array",
                    "description": "효과음 큐 [{time, sound, description}]",
                },
                "next_dimension": {
                    "type": "string",
                    "description": "추천 다음 차원",
                },
            },
            "params": {
                "model": {
                    "type": "string",
                    "default": "gemini-3-flash-preview",
                    "options": ["gemini-3-flash-preview", "gemini-3-pro-preview"],
                },
                "use_rag": {
                    "type": "boolean",
                    "default": True,
                    "description": "RAG 컨텍스트 사용 여부",
                },
            },
        },
    },
]


def get_dimension_capsule_specs() -> List[Dict[str, Any]]:
    """Return all teaching capsule specs for database seeding."""
    return DIMENSION_CAPSULES


# =============================================================================
# Frontend UI Metadata (SSoT for icon, color, toolId mapping)
# =============================================================================

DIMENSION_UI_CONFIG: Dict[str, Dict[str, Any]] = {
    # Core Dimensions (1D-4D)
    "prompt_generator": {
        "toolId": "prompt_generator",
        "dimension": "1D",
        "displayName": "프롬프트 연금술",
        "displayNameEn": "Prompt Alchemy",
        "description": "AI가 이해하는 전문 언어로 번역",
        "icon": "sparkles",
        "color": "violet",
        "stage": "pre_production",
        "capsuleKey": "teaching.prompt.generate",
        "endpoint": "/api/dimension/1d/generate",
        "creditCost": 5,
    },
    "storyboard": {
        "toolId": "storyboard",
        "dimension": "2D",
        "displayName": "스토리보드 스케치",
        "displayNameEn": "Storyboard Sketch",
        "description": "글을 시각적 컷으로 스케치",
        "icon": "layout-grid",
        "color": "emerald",
        "stage": "pre_production",
        "capsuleKey": "teaching.storyboard.create",
        "endpoint": "/api/dimension/2d/create",
        "creditCost": 10,
    },
    "image_tool": {
        "toolId": "image_tool",
        "dimension": "3D",
        "displayName": "비주얼 리얼라이저",
        "displayNameEn": "Visual Realizer",
        "description": "Key Frame 고품질 생성",
        "icon": "image",
        "color": "amber",
        "stage": "production",
        "capsuleKey": "teaching.image.generate",
        "endpoint": "/api/dimension/3d/generate",
        "creditCost": 5,
    },
    "reference_analyzer": {
        "toolId": "reference_analyzer",
        "dimension": "4D",
        "displayName": "레퍼런스 해석기",
        "displayNameEn": "Reference Decoder",
        "description": "조명, 색감, 연출의 전문가적 분석",
        "icon": "film",
        "color": "cyan",
        "stage": "planning",
        "capsuleKey": "teaching.reference.analyze",
        "endpoint": "/api/dimension/4d/analyze",
        "creditCost": 8,
    },
    # Extended Dimensions
    "quality_check": {
        "toolId": "quality_check",
        "dimension": "QC",
        "displayName": "퀄리티 디렉터",
        "displayNameEn": "Quality Director",
        "description": "시각적 일관성 및 품질 검수",
        "icon": "check-circle",
        "color": "rose",
        "stage": "finishing",
        "capsuleKey": "dimension.quality.check",
        "endpoint": "/api/dimension/quality/check",
        "creditCost": 8,
    },
    "aesthetic_direct": {
        "toolId": "aesthetic_direct",
        "dimension": "AD",
        "displayName": "미학디렉터",
        "displayNameEn": "Aesthetic Director",
        "description": "시각적 스타일 가이드라인 생성",
        "icon": "palette",
        "color": "fuchsia",
        "stage": "planning",
        "capsuleKey": "dimension.aesthetic.direct",
        "endpoint": "/api/dimension/aesthetic/direct",
        "creditCost": 10,
    },
    "persona_analyze": {
        "toolId": "persona_analyze",
        "dimension": "AI",
        "displayName": "심연의 거울",
        "displayNameEn": "Abyss Mirror",
        "description": "내면의 욕구와 감정 해석",
        "icon": "moon",
        "color": "indigo",
        "stage": "planning",
        "capsuleKey": "dimension.persona.analyze",
        "endpoint": "/api/dimension/persona/analyze",
        "creditCost": 5,
    },
    "veo_generate": {
        "toolId": "veo_generate",
        "dimension": "VEO",
        "displayName": "비디오 메이커",
        "displayNameEn": "Video Maker",
        "description": "최종 AI 영상 생성",
        "icon": "video",
        "color": "sky",
        "stage": "production",
        "capsuleKey": "veo.video.generate",
        "endpoint": "/api/dimension/veo/generate",
        "creditCost": 200,
    },
    # Additional Tools
    "story_architect": {
        "toolId": "story_architect",
        "dimension": "SA",
        "displayName": "시나리오 생성기",
        "displayNameEn": "Story Architect",
        "description": "창작 시나리오 생성",
        "icon": "book-open",
        "color": "orange",
        "stage": "planning",
        "capsuleKey": "dimension.story.architect",
        "endpoint": "/api/dimension/story/architect",
        "creditCost": 10,
    },
    "sound_craft": {
        "toolId": "sound_craft",
        "dimension": "SC",
        "displayName": "사운드 크래프터",
        "displayNameEn": "Sound Crafter",
        "description": "BGM 및 성우 내레이션 생성",
        "icon": "music",
        "color": "pink",
        "stage": "pre_production",
        "capsuleKey": "dimension.sound.craft",
        "endpoint": "/api/dimension/sound/craft",
        "creditCost": 8,
    },
    # 4-Stage Workflow Aliases (for flow/page.tsx compatibility)
    "sound_crafter": {
        "toolId": "sound_crafter",
        "dimension": "SOUND",
        "displayName": "사운드 크래프터",
        "displayNameEn": "Sound Crafter",
        "description": "BGM 및 성우 내레이션 생성",
        "icon": "music",
        "color": "pink",
        "stage": "pre_production",
        "capsuleKey": "dimension.sound.craft",
        "endpoint": "/api/dimension/sound/craft",
        "creditCost": 8,
    },
    "reference_decoder": {
        "toolId": "reference_decoder",
        "dimension": "REF",
        "displayName": "레퍼런스 해석기",
        "displayNameEn": "Reference Decoder",
        "description": "조명, 색감, 연출의 전문가적 분석",
        "icon": "film",
        "color": "cyan",
        "stage": "planning",
        "capsuleKey": "teaching.reference.analyze",
        "endpoint": "/api/dimension/4d/analyze",
        "creditCost": 8,
    },
    "visual_realizer": {
        "toolId": "visual_realizer",
        "dimension": "VIS",
        "displayName": "비주얼 리얼라이저",
        "displayNameEn": "Visual Realizer",
        "description": "Key Frame 고품질 생성",
        "icon": "image",
        "color": "amber",
        "stage": "production",
        "capsuleKey": "teaching.image.generate",
        "endpoint": "/api/dimension/3d/generate",
        "creditCost": 5,
    },
}

# Workflow stage order for recommendations
STAGE_ORDER = ["planning", "pre_production", "production", "finishing"]

# Initial dimension options (shown when no cars exist)
INITIAL_DIMENSION_ORDER = [
    "prompt_generator",    # 1D - 가장 일반적인 시작점
    "reference_analyzer",  # 4D - 레퍼런스가 있는 경우
    "aesthetic_direct",    # AD - 스타일 우선
    "persona_analyze",     # AI - 창작 DNA 분석
    "storyboard",          # 2D
    "image_tool",          # 3D
    "quality_check",       # QC
    "veo_generate",        # VEO
    "story_architect",     # SA - 시나리오 생성기
    "sound_craft",         # SC - 사운드 크래프터
]


def get_dimension_ui_config() -> Dict[str, Dict[str, Any]]:
    """Return UI configuration for all dimension tools (SSoT for frontend)."""
    return DIMENSION_UI_CONFIG


def get_dimension_tools_for_frontend() -> List[Dict[str, Any]]:
    """Return dimension tools list formatted for frontend consumption."""
    tools = []
    for tool_id in INITIAL_DIMENSION_ORDER:
        config = DIMENSION_UI_CONFIG.get(tool_id)
        if config:
            tools.append(config)
    return tools
