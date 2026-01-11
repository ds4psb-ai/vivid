# 4-Stage Workflow 앱 리네이밍 및 개발 계획

## Executive Summary

현재 10개의 Dimension 앱이 구현되어 있으며, 4-Stage Workflow 기준의 슬러그/라우트 정합화가 필요합니다.

---

## 1. 현재 상태 → 4-Stage 매핑

### Stage 1: 기획 (Planning)

| 신규 이름 | 현재 상태 | 액션 | Route slug | Workflow key |
|----------|---------|------|--------|--------|
| **심연의 거울** | ✅ 구현됨 | 유지 | `abyss` | `abyss-mirror` |
| **레퍼런스 해석기** | ✅ 구현됨 | 유지 | `reference-decoder` | `reference-decoder` |
| **시나리오 생성기** | ✅ 구현됨 | 유지 | `story-architect` | `story-architect` |

### Stage 2: 사전 제작 (Pre-production)

| 신규 이름 | 현재 상태 | 액션 | Route slug | Workflow key |
|----------|---------|------|--------|--------|
| **사운드 크래프터** | ✅ 구현됨 | 유지 | `sound-crafter` | `sound-crafter` |
| **스토리보드 스케치** | ✅ 구현됨 | 유지 | `storyboard` | `storyboard-sketch` |
| **프롬프트 연금술** | ✅ 구현됨 | 유지 | `prompt` | `prompt-alchemy` |

### Stage 3: 제작 (Production)

| 신규 이름 | 현재 상태 | 액션 | Route slug | Workflow key |
|----------|---------|------|--------|--------|
| **비주얼 리얼라이저** | ✅ 구현됨 | 유지 | `visual-realizer` | `visual-realizer` |
| **비디오 메이커** | ✅ 구현됨 | 유지 | `video-maker` | `video-maker` |

### Stage 4: 완성 (Finishing)

| 신규 이름 | 현재 상태 | 액션 | Route slug | Workflow key |
|----------|---------|------|--------|--------|
| **퀄리티 디렉터** | ✅ 구현됨 | 유지 | `quality-check` | `quality-director` |

---

## 2. 리네이밍 상세

### 2.1 reference-decoder (현행)

- Frontend: `/dimension/reference-decoder` → `ReferenceDecoderPanel.tsx`
- API: `POST /api/dimension/4d/analyze`
- Capsule: `teaching.reference.analyze`

### 2.2 visual-realizer (현행)

- Frontend: `/dimension/visual-realizer` → `VisualRealizerPanel.tsx`
- API: `POST /api/dimension/3d/generate`
- Capsule: `teaching.image.generate`

### 2.3 video-maker (현행)

- Frontend: `/dimension/video-maker` → `VeoVideoPanel.tsx`
- API: `POST /api/dimension/veo/generate` (SSE: `/api/dimension/veo/generate/stream`)
- Capsule: `veo.video.generate`

---

## 3. 신규 개발 상세

### 3.1 시나리오 생성기 (Story Architect)

**목적**: DNA + 스타일을 결합한 시나리오 자동 작성

**입력 스키마**:
```python
class StoryArchitectRequest(BaseModel):
    concept: str = Field(..., min_length=10, max_length=3000)
    persona_data: Optional[dict] = None  # 심연의 거울 출력
    reference_analysis: Optional[dict] = None  # 레퍼런스 해석기 출력
    genre: str = Field(default="drama", pattern="^(drama|ad|mv|documentary|short)$")
    duration: str = Field(default="60s", pattern="^(15s|30s|60s|3m|5m)$")
    structure: str = Field(default="3act", pattern="^(3act|hero|circular|montage)$")
    language: str = Field(default="ko", pattern="^(ko|en)$")
    use_rag: bool = True
```

**출력 스키마**:
```python
class StoryArchitectResponse(BaseModel):
    title: str
    logline: str  # 한 줄 요약
    synopsis: str  # 3-5문장 개요
    structure: list[dict]  # [{act, description, duration, emotion}]
    characters: list[dict]  # [{name, role, arc, traits}]
    themes: list[str]
    visual_motifs: list[str]  # 레퍼런스 연결
    next_dimension: str  # 추천 다음 단계 (workflow key: storyboard-sketch)
```

**크레딧**: 10 (Flash) / 25 (Pro)

**API**: `POST /api/dimension/story/architect`

**Frontend**: `/dimension/story-architect` → `StoryArchitectPanel.tsx`

---

### 3.2 사운드 크래프터 (Sound Crafter)

**목적**: BGM/효과음/내레이션 방향 생성 (Suno, Udio 호환)

**입력 스키마**:
```python
class SoundCrafterRequest(BaseModel):
    storyboard: Optional[list[dict]] = None  # 스토리보드 출력
    concept: str = Field(..., min_length=10, max_length=2000)
    sound_type: str = Field(default="bgm", pattern="^(bgm|sfx|narration|full)$")
    mood: str = Field(default="neutral")
    genre: str = Field(default="cinematic", pattern="^(cinematic|electronic|acoustic|ambient|pop|classical)$")
    tempo: str = Field(default="medium", pattern="^(slow|medium|fast|dynamic)$")
    duration: str = Field(default="60s")
    target_platform: str = Field(default="suno", pattern="^(suno|udio|elevenlabs)$")
    language: str = Field(default="ko")
    use_rag: bool = True
```

**출력 스키마**:
```python
class SoundCrafterResponse(BaseModel):
    music_prompt: str  # Suno/Udio용 프롬프트
    style_tags: list[str]  # [cinematic, emotional, building]
    bpm_range: str  # "80-100 BPM"
    key_signature: str  # "C minor"
    instrumentation: list[str]  # [piano, strings, subtle percussion]
    dynamics: str  # "starts soft, builds to climax at 0:45"
    narration_script: Optional[str]  # 내레이션 스크립트
    voice_direction: Optional[dict]  # {tone, pace, emotion}
    sfx_cues: list[dict]  # [{time, sound, description}]
    next_dimension: str  # 추천 다음 단계 (workflow key)
```

**크레딧**: 8 (Flash) / 18 (Pro)

**API**: `POST /api/dimension/sound/craft`

**Frontend**: `/dimension/sound-crafter` → `SoundCrafterPanel.tsx`

---

## 4. 기술 표준 (Technical Standards)

### 4.1 Capsule 등록 패턴

`backend/app/fixtures/dimension_capsules.py`:

```python
# 신규 캡슐 추가 템플릿
{
    "key": "dimension.story.architect",
    "name": "시나리오 생성기",
    "name_en": "Story Architect",
    "description": "DNA와 스타일을 결합한 시나리오 작성",
    "stage": "planning",  # planning | pre_production | production | finishing
    "stage_order": 3,  # Stage 내 순서
    "credit_cost": {
        "flash": 10,
        "pro": 25
    },
    "request_model": "StoryArchitectRequest",
    "response_model": "StoryArchitectResponse",
    "supports_rag": True,
    "input_dimensions": ["abyss-mirror", "reference-decoder"],  # 연결 가능 입력
    "output_dimensions": ["storyboard-sketch", "prompt-alchemy"],  # 연결 가능 출력
}
```

### 4.2 API Router 패턴

`backend/app/routers/dimension.py`:

```python
@router.post("/story/architect", response_model=StoryArchitectResponse)
async def architect_story(
    request: StoryArchitectRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    use_rag: bool = Query(default=True),
    model: str = Query(default="flash", regex="^(flash|pro)$"),
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key"),
):
    """시나리오 생성기 - DNA와 스타일을 결합한 시나리오 작성"""
    adapter = DimensionAdapter(db, user, x_gemini_api_key)
    return await adapter.execute(
        capsule_key="dimension.story.architect",
        request=request,
        use_rag=use_rag,
        model=model,
    )
```

### 4.3 Frontend Panel 패턴

`frontend/src/components/dimension/StoryArchitectPanel.tsx`:

```tsx
"use client";

import { useState } from "react";
import { DimensionPanelLayout } from "./DimensionPanelLayout";
import { useDimensionExecution } from "@/hooks/useDimensionExecution";
import { api } from "@/lib/api";

interface StoryArchitectRequest {
    concept: string;
    persona_data?: object;
    reference_analysis?: object;
    genre: string;
    duration: string;
    structure: string;
}

interface StoryArchitectResponse {
    title: string;
    logline: string;
    synopsis: string;
    structure: Array<{ act: string; description: string; duration: string; emotion: string }>;
    characters: Array<{ name: string; role: string; arc: string }>;
    themes: string[];
    visual_motifs: string[];
    next_dimension: string;
}

export function StoryArchitectPanel() {
    const [request, setRequest] = useState<StoryArchitectRequest>({
        concept: "",
        genre: "drama",
        duration: "60s",
        structure: "3act",
    });

    const { execute, result, isLoading, error } = useDimensionExecution<
        StoryArchitectRequest,
        StoryArchitectResponse
    >({
        endpoint: "/api/dimension/story/architect",
        capsuleKey: "dimension.story.architect",
    });

    return (
        <DimensionPanelLayout
            title="시나리오 생성기"
            subtitle="Story Architect"
            description="DNA와 스타일을 결합한 시나리오 작성"
            creditCost={{ flash: 10, pro: 25 }}
            stage="planning"
        >
            {/* Input Form */}
            {/* Result Display */}
            {/* Connection Buttons to next dimensions */}
        </DimensionPanelLayout>
    );
}
```

### 4.4 차원 연결 패턴 (Dimension Chaining)

```tsx
// 차원 간 데이터 전달
interface DimensionOutput {
    data: object;
    dimension: string;
    timestamp: string;
}

// Context로 관리
const DimensionChainContext = createContext<{
    outputs: Record<string, DimensionOutput>;
    setOutput: (dimension: string, data: object) => void;
    getInput: (dimension: string) => object | null;
}>({...});

// 사용 예시
const { setOutput } = useDimensionChain();

// 심연의 거울 완료 시 (workflow key 사용, route slug는 /dimension/abyss)
setOutput("abyss-mirror", personaData);

// 시나리오 생성기에서 사용
const { getInput } = useDimensionChain();
const personaData = getInput("abyss-mirror");
```

---

## 5. 구현 우선순위

### Phase 1: 리네이밍 (1-2일)

| 순서 | 작업 | 파일 수 | 난이도 |
|-----|------|--------|-------|
| 1 | reference-decoder 라우트 정합화 | ~5 | 낮음 |
| 2 | visual-realizer 라우트 정합화 | ~5 | 낮음 |
| 3 | video-maker 라우트 정합화 | ~5 | 낮음 |
| 4 | route slug 일관화 (abyss/storyboard/prompt/quality-check) | ~10 | 낮음 |

### Phase 2: 신규 개발 (3-5일)

| 순서 | 작업 | 예상 시간 | 의존성 |
|-----|------|---------|-------|
| 1 | Story Architect (시나리오 생성기) | 2일 | Abyss, Reference |
| 2 | Sound Crafter (사운드 크래프터) | 1.5일 | Storyboard |

### Phase 3: 통합 및 테스트 (2일)

| 순서 | 작업 |
|-----|------|
| 1 | dimension/page.tsx Hub 업데이트 |
| 2 | Train Workflow에 새 차원 추가 |
| 3 | Capsule Registry 정합성 검증 |
| 4 | E2E 연결 테스트 |

---

## 6. 최종 4-Stage Workflow 구조

표기 기준: **Route slug**는 `/dimension/...` 경로, **Workflow key**는 체이닝용 식별자입니다.

```
Stage 1: 기획 (Planning)
├── 심연의 거울 (/dimension/abyss, abyss-mirror) ──────────┐
├── 레퍼런스 해석기 (/dimension/reference-decoder, reference-decoder) ──┼──▶ Stage 2
└── 시나리오 생성기 (/dimension/story-architect, story-architect) ◀──┘

Stage 2: 사전 제작 (Pre-production)
├── 사운드 크래프터 (/dimension/sound-crafter, sound-crafter) ─────┐
├── 스토리보드 스케치 (/dimension/storyboard, storyboard-sketch) ──┼──▶ Stage 3
└── 프롬프트 연금술 (/dimension/prompt, prompt-alchemy) ◀──────────┘

Stage 3: 제작 (Production)
├── 비주얼 리얼라이저 (/dimension/visual-realizer, visual-realizer) ──┬──▶ Stage 4
└── 비디오 메이커 (/dimension/video-maker, video-maker) ◀─────────────┘

Stage 4: 완성 (Finishing)
└── 퀄리티 디렉터 (/dimension/quality-check, quality-director) ──▶ 완료
```

---

## 7. 파일 변경 목록

### Backend

| 파일 | 변경 내용 |
|-----|---------|
| `fixtures/dimension_capsules.py` | 새 캡슐 2개 추가, 기존 캡슐 stage 필드 추가 |
| `routers/dimension.py` | 새 엔드포인트 2개 추가, 리네이밍 엔드포인트 추가 |
| `dimension_adapter.py` | story_architect, sound_crafter 핸들러 추가 |
| `models/` | StoryArchitect, SoundCrafter 모델 추가 |

### Frontend

| 파일 | 변경 내용 |
|-----|---------|
| `app/dimension/story-architect/page.tsx` | 신규 |
| `app/dimension/sound-crafter/page.tsx` | 신규 |
| `app/dimension/reference-decoder/page.tsx` | 리네이밍 (legacy route 정리: `/dimension/shot-catch`) |
| `app/dimension/visual-realizer/page.tsx` | 리네이밍 (legacy route 정리: `/dimension/image-tool`) |
| `app/dimension/video-maker/page.tsx` | 리네이밍 (legacy route 정리: `/dimension/veo-video`) |
| `components/dimension/StoryArchitectPanel.tsx` | 신규 |
| `components/dimension/SoundCrafterPanel.tsx` | 신규 |
| `app/dimension/page.tsx` | Hub 업데이트 (4-Stage 구조) |

---

*Generated: 2025-01-07*
