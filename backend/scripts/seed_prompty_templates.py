#!/usr/bin/env python3
"""Seed Prompty Templates from viral-video-automation.

Migrates workflow templates to the database for prompty.co.kr marketplace.
"""
import asyncio
import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models_prompty import PromptyTemplate

# Default templates based on viral-video-automation
TEMPLATES = [
    {
        "title": "바이럴 영상 패러디 (Dual AI)",
        "description": "Gemini CLI + Claude Code 티키타카 워크플로우. 레퍼런스 영상 분석부터 최종 편집까지 단계별 가이드.",
        "category": "video",
        "tags": ["viral", "parody", "dual-ai", "tiktok", "reels"],
        "is_featured": True,
        "workflow_config": {
            "stages": ["analysis", "image", "video", "assembly"],
            "steps": {
                "analysis": [
                    {
                        "id": "analyze_reference",
                        "name": "레퍼런스 분석",
                        "description": "원본 영상의 스타일, 구성, 연출을 분석합니다.",
                        "prompt_text": """당신은 영상 분석 전문가입니다. 첨부된 영상을 분석해주세요.

## 요청 사항

### 1. 컷 분해 (Cut Breakdown)
각 씬을 0.01초 단위로 정밀하게 분석하여 아래 테이블을 완성하세요:
| Scene | Start | End | Duration | Camera | Subject | Action |

### 2. 캐릭터 프로파일
등장하는 모든 인물에 대해: 예상 나이, 성별, 외형 특징, 표정/감정 상태

### 3. 시각 스타일 분석
조명 색온도, 색감 팔레트, 필름 스타일, 카메라 움직임 패턴

### 4. 앵커 씬 추천
캐릭터 일관성을 위해 "앵커"로 사용할 가장 좋은 씬을 추천하세요.""",
                        "external_tool": None,
                        "tips": [
                            "Gemini에 영상 파일을 직접 첨부하세요",
                            "컷 전환 타이밍을 0.01초 단위로 정확히 기록하세요",
                            "앵커 씬은 얼굴이 가장 선명한 것으로 선택하세요",
                        ],
                    },
                    {
                        "id": "character_profile",
                        "name": "캐릭터 프로파일",
                        "description": "각 캐릭터의 상세 정보를 정리합니다.",
                        "prompt_text": """분석 결과를 바탕으로 PROFILES.md를 작성해주세요.

## CHARACTER PROFILES

각 인물마다:
- ID: ID_[역할] (예: ID_ANCHOR_GIRL)
- Ethnicity: (Korean/Asian/Western)
- Age Range: (예: 20-25)
- Hair: (색상, 길이, 스타일)
- Face: (얼굴형, 특징)
- Eyes: (눈 모양, 색)
- Clothing: (의상 상세)
- Position: (영상 내 역할)""",
                        "tips": ["일관된 ID 명명 규칙을 사용하세요", "피부톤을 정확히 기록하세요"],
                    },
                ],
                "image": [
                    {
                        "id": "anchor_girl",
                        "name": "앵커 걸 생성",
                        "description": "주인공 여성 캐릭터의 기준 이미지를 생성합니다.",
                        "prompt_text": """[NanoBanana Pro Prompt]

Portrait of young Korean woman, 20-25 years old,
facing camera, neutral expression, soft studio lighting,
photorealistic, high detail face, natural skin texture,
--ar 9:16 --cw 100 --stylize 50

[Negative]
deformed hands, 6 fingers, western features,
unnatural lighting, oversaturated""",
                        "external_tool": "nanobanana",
                        "tips": [
                            "--cw 값을 높여 캐릭터 일관성을 유지하세요",
                            "손이 보이면 반드시 검증하세요",
                            "앵커는 최소 3개 버전을 생성하세요",
                        ],
                    },
                    {
                        "id": "anchor_boy",
                        "name": "앵커 보이 생성",
                        "description": "주인공 남성 캐릭터의 기준 이미지를 생성합니다.",
                        "prompt_text": """[NanoBanana Pro Prompt]

Portrait of young Korean man, 25-30 years old,
facing camera, neutral expression, soft studio lighting,
photorealistic, high detail face, natural skin texture,
--ar 9:16 --cw 100 --stylize 50""",
                        "external_tool": "nanobanana",
                        "tips": ["앵커 걸과 동일한 조명 설정을 사용하세요"],
                    },
                    {
                        "id": "scene_images",
                        "name": "씬별 이미지 생성",
                        "description": "각 씬에 맞는 이미지를 생성합니다.",
                        "prompt_text": """각 씬 프롬프트를 ANALYSIS.md에서 가져와 생성하세요.

[COLOR CONSISTENCY KEY]
모든 씬에서 동일하게 적용:
- Tone: [분석 결과]
- Grain: [분석 결과]
- Lighting: [분석 결과]""",
                        "external_tool": "nanobanana",
                        "tips": [
                            "앵커 이미지를 ref로 사용하세요",
                            "씬마다 COLOR_KEY를 일관되게 적용하세요",
                        ],
                    },
                ],
                "video": [
                    {
                        "id": "scene_videos",
                        "name": "씬별 영상 생성",
                        "description": "이미지를 영상으로 변환합니다.",
                        "prompt_text": """[Kling Motion Prompt]

Take the image and add subtle natural movement:
- Slow breathing motion
- Slight head turn
- Natural eye movement
- Duration: 2-4 seconds

[Settings]
- Mode: Image-to-Video
- Duration: 4s
- Motion: Subtle""",
                        "external_tool": "kling",
                        "tips": [
                            "과한 모션은 캐릭터 일관성을 해칩니다",
                            "2-4초가 최적 길이입니다",
                        ],
                    },
                ],
                "assembly": [
                    {
                        "id": "final_edit",
                        "name": "최종 편집",
                        "description": "모든 클립을 편집하고 사운드를 추가합니다.",
                        "prompt_text": """DaVinci Resolve에서:

1. 모든 씬 클립 임포트
2. 원본 영상 타이밍에 맞춰 배치
3. 컬러 그레이딩 통일
4. 트랜지션 추가
5. 사운드/BGM 추가
6. 자막 추가 (필요시)
7. 최종 렌더링: 1080x1920, 30fps""",
                        "external_tool": "davinci",
                        "tips": [
                            "원본 타이밍을 정확히 맞추세요",
                            "컬러 그레이딩으로 통일감을 주세요",
                        ],
                    },
                ],
            },
        },
        "critique_config": {
            "items": [
                {"id": "composition", "label": "구도", "description": "시각적 균형과 구성", "weight": 0.15},
                {"id": "consistency", "label": "캐릭터 일관성", "description": "앵커와의 일치도", "weight": 0.25},
                {"id": "lighting", "label": "조명", "description": "조명 품질과 일관성", "weight": 0.15},
                {"id": "anatomy", "label": "해부학", "description": "손, 얼굴 등 정확성", "weight": 0.20},
                {"id": "style", "label": "스타일", "description": "원본 스타일과의 일치", "weight": 0.15},
                {"id": "detail", "label": "디테일", "description": "세부 묘사 품질", "weight": 0.10},
            ],
            "passing_score": 75,
        },
    },
    {
        "title": "틱톡 이미지 카드 (5-Frame)",
        "description": "5장의 이미지로 구성된 틱톡 슬라이드쇼. 빠른 제작, 높은 바이럴 확률.",
        "category": "image",
        "tags": ["tiktok", "slideshow", "quick", "image-card"],
        "is_featured": True,
        "workflow_config": {
            "stages": ["concept", "image", "assembly"],
            "steps": {
                "concept": [
                    {
                        "id": "hook_design",
                        "name": "훅 디자인",
                        "description": "첫 장면의 시선을 사로잡는 훅을 설계합니다.",
                        "prompt_text": """5프레임 스토리 구조:

1. Hook: 강렬한 시작 (질문 or 충격)
2. Setup: 상황 설명
3. Build: 긴장감 고조
4. Climax: 핵심 전달
5. CTA: 행동 유도 (저장/팔로우)

각 프레임의 텍스트와 비주얼 구상:""",
                        "tips": ["첫 0.5초에 시선을 사로잡아야 합니다"],
                    },
                ],
                "image": [
                    {
                        "id": "frame_generation",
                        "name": "5프레임 이미지 생성",
                        "description": "각 프레임에 맞는 이미지를 생성합니다.",
                        "prompt_text": """[NanoBanana Prompt Template]

Frame [N]: [DESCRIPTION]
- Style: Consistent throughout
- Text overlay area: Top/Bottom 20%
- Aspect ratio: 9:16

--ar 9:16 --stylize 100""",
                        "external_tool": "nanobanana",
                        "tips": ["모든 프레임의 스타일을 통일하세요"],
                    },
                ],
                "assembly": [
                    {
                        "id": "slideshow_edit",
                        "name": "슬라이드쇼 편집",
                        "description": "이미지를 슬라이드쇼로 조립합니다.",
                        "prompt_text": """CapCut/DaVinci에서:

1. 5장 이미지 임포트
2. 각 프레임 2-3초
3. 트랜지션: Fade/Swipe
4. 텍스트 오버레이 추가
5. 트렌딩 BGM 추가
6. 총 길이: 15초 이내""",
                        "tips": ["15초 이내가 완주율이 높습니다"],
                    },
                ],
            },
        },
        "critique_config": {
            "items": [
                {"id": "hook", "label": "훅", "description": "첫 장면의 임팩트", "weight": 0.30},
                {"id": "flow", "label": "흐름", "description": "스토리 전개의 자연스러움", "weight": 0.25},
                {"id": "style", "label": "스타일", "description": "시각적 일관성", "weight": 0.20},
                {"id": "text", "label": "텍스트", "description": "가독성과 임팩트", "weight": 0.15},
                {"id": "cta", "label": "CTA", "description": "행동 유도 효과", "weight": 0.10},
            ],
            "passing_score": 70,
        },
    },
    {
        "title": "AI 음악 비디오",
        "description": "Suno로 음악 생성, 이미지로 비주얼라이저 제작. 1분 내외 완성.",
        "category": "audio",
        "tags": ["music-video", "suno", "ai-music"],
        "is_featured": False,
        "workflow_config": {
            "stages": ["music", "visual", "assembly"],
            "steps": {
                "music": [
                    {
                        "id": "music_generation",
                        "name": "AI 음악 생성",
                        "description": "Suno로 음악을 생성합니다.",
                        "prompt_text": """[Suno Prompt]

Genre: [장르]
Mood: [분위기]
Tempo: [BPM]
Duration: 60-90 seconds

Lyrics (optional):
[가사]""",
                        "external_tool": "suno",
                        "tips": ["여러 버전을 생성해서 비교하세요"],
                    },
                ],
                "visual": [
                    {
                        "id": "visualizer_images",
                        "name": "비주얼라이저 이미지",
                        "description": "음악에 맞는 시각적 이미지를 생성합니다.",
                        "prompt_text": """[NanoBanana Prompt]

Abstract visualization of [MOOD]:
- Colors: [음악 무드에 맞는 색상]
- Movement suggestion: [빛줄기, 파티클 등]
- Style: Cinematic, high contrast

--ar 16:9 --stylize 200""",
                        "external_tool": "nanobanana",
                        "tips": ["음악의 비트에 맞는 시각적 리듬을 고려하세요"],
                    },
                ],
                "assembly": [
                    {
                        "id": "music_video_edit",
                        "name": "뮤직비디오 편집",
                        "description": "음악과 이미지를 결합합니다.",
                        "prompt_text": """편집 가이드:

1. 음악 파형 분석 (비트 추출)
2. 비트에 맞춰 이미지 전환
3. Ken Burns 효과로 움직임 추가
4. 가사 자막 추가 (있을 경우)
5. 페이드 인/아웃 처리""",
                        "tips": ["비트와 시각적 전환을 동기화하세요"],
                    },
                ],
            },
        },
        "critique_config": {
            "items": [
                {"id": "sync", "label": "음악 싱크", "description": "비트와 시각의 동기화", "weight": 0.35},
                {"id": "visual", "label": "비주얼", "description": "시각적 임팩트", "weight": 0.30},
                {"id": "music", "label": "음악", "description": "음악 품질", "weight": 0.25},
                {"id": "overall", "label": "전체", "description": "완성도", "weight": 0.10},
            ],
            "passing_score": 70,
        },
    },
]


async def seed_templates():
    """Seed templates to database."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if templates already exist
        result = await session.execute(text("SELECT COUNT(*) FROM prompty_templates"))
        count = result.scalar()

        if count and count > 0:
            print(f"Templates already exist ({count}). Skipping seed.")
            return

        # Insert templates
        for template_data in TEMPLATES:
            template = PromptyTemplate(
                id=uuid.uuid4(),
                title=template_data["title"],
                description=template_data["description"],
                creator_id="system",
                creator_name="Prompty Team",
                category=template_data["category"],
                workflow_config=template_data["workflow_config"],
                critique_config=template_data["critique_config"],
                tags=template_data["tags"],
                is_featured=template_data["is_featured"],
                is_public=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(template)
            print(f"Added template: {template_data['title']}")

        await session.commit()
        print(f"\nSuccessfully seeded {len(TEMPLATES)} templates!")


if __name__ == "__main__":
    asyncio.run(seed_templates())
