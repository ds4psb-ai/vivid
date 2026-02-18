# Vivid Dimension Apps - Comprehensive Audit Report

> **Version**: 2.0
> **Date**: 2026-01-18
> **Purpose**: AI MV 전문가 워크플로우 vs Vivid 앱 비교 분석 + 2026 백엔드 구현 가이드

---

## Executive Summary

### 분석 소스
1. **전문가 강의**: AI 애니메이션 뮤비 전문가 (흑백요리사 AI 애니메이션 오프닝 제작자) 58분 강의
2. **2026 산업 트렌드**: Tavily MCP 웹 리서치 (AI Video, Music, Character Consistency)
3. **Vivid 현황**: 13개 Dimension 앱 프론트엔드/백엔드 코드 분석

### 핵심 발견

| 영역 | 전문가 방식 | Vivid 현황 | Gap Level |
|------|-------------|------------|-----------|
| 레퍼런스 분석 | 작업의 50%+ 할애 | 4D 단순 분석 | 🔴 Critical |
| 스타일 일관성 | Style + Scene 분리 | 단일 프롬프트 | 🟡 Medium |
| 품질 선별 | 인간 판단 영역 | A/B 비교 미지원 | 🟡 Medium |
| 음악 우선순위 | 영상보다 음악이 바이럴 핵심 | Suno 기본 기능만 | 🟡 Medium |
| 캐릭터 일관성 | Start/End Frame 기법 | StoryMem 기반 | 🟢 Good |

### 우선순위별 하드닝 필요 앱

| Priority | App | 이유 |
|----------|-----|------|
| P0 | 4D Reference Decoder | 레퍼런스 분석이 전체 작업의 핵심 |
| P0 | 3D Visual Realizer | Style Extraction 기능 부재 |
| P1 | VEO Video Maker | Start/End Frame 기능 미지원 |
| P1 | Suno AI Music | Cover/Remix, Stem 기능 부재 |
| P2 | QC Quality Director | A/B 비교 UI 부재 |
| P2 | Story Architect | Shot List 자동 생성 미지원 |

---

## Part 1: 전문가 워크플로우 분석

### 1.1 사용 도구 스택

전문가가 사용하는 도구:
```
이미지 생성: Nana Banana (품질 최상)
비디오 생성: Kling (일관성 우수), Sora (품질 우수)
음악 생성: Suno (멜로디/가사), GPT (작사)
프롬프트 작성: GPT/Claude
```

### 1.2 핵심 인사이트

#### 인사이트 1: 레퍼런스 리서치가 작업의 50% 이상
```
"레퍼런스 조사가 저한테는 제일 중요한 것 같아요...
제가 느끼는 AI 뮤직비디오가 완성되기까지 가장 중요한 포인트는
레퍼런스라고 생각해요... 이게 컨셉이 거의 절반을 차지해요"
```

**현재 Vivid 4D Reference Decoder 문제점**:
- 단순 이미지/영상 분석만 제공
- 프레임별 분석 기능 없음
- 레퍼런스에서 스타일 추출 기능 없음
- 레퍼런스 라이브러리/태깅 시스템 없음

#### 인사이트 2: Style Prompt + Scene Prompt 분리
```
"스타일 프롬프트라고 따로 둬요... 일관성을 위해서
모든 이미지에 동일한 스타일 프롬프트를 적용하고
씬 프롬프트만 바꿔가면서 생성"
```

**현재 Vivid 3D Visual Realizer 문제점**:
- 스타일과 씬을 분리하지 않음
- 스타일 프리셋은 있지만 커스텀 스타일 저장 불가
- 레퍼런스에서 자동 스타일 추출 기능 없음

#### 인사이트 3: 품질 선별은 인간 판단 영역
```
"저는 생성된 것 중에서 고르는 작업을 제일 많이 해요...
AI가 20개 만들어주면 그중에 쓸만한 거 하나 고르는 게
더 빠르더라고요"
```

**현재 Vivid QC Quality Director 문제점**:
- 자동 품질 점수만 제공
- A/B 비교 UI 없음
- 배치 생성 + 선별 워크플로우 미지원

#### 인사이트 4: 음악이 바이럴의 핵심
```
"영상 퀄리티보다 음악이 더 중요해요...
중독성 있는 멜로디가 조회수를 결정"
```

**현재 Vivid Suno AI Music 문제점**:
- 기본 음악 생성만 지원
- Cover/Remix 기능 없음
- 스템 분리/다운로드 없음
- BPM/키 기반 검색 없음

---

## Part 2: 2026 산업 트렌드 분석

### 2.1 AI Video Generation (2026)

| Tool | 주요 기능 | Vivid 비교 |
|------|----------|-----------|
| **Kling 2.6** | Start/End Frame, 5분 영상, Motion Brush | 🔴 Start/End Frame 미지원 |
| **Veo 3.1** | 4K, Native Audio, 16:9 | 🟢 지원 중 |
| **Sora 2** | Storyboard, Remix, Re-cut | 🟡 Storyboard 부분 지원 |
| **Runway Gen-4** | Character Lock, Act-One | 🟡 CC앱에서 부분 지원 |

**핵심 Gap**: Kling의 Start/End Frame 기능
- 첫 프레임과 마지막 프레임을 지정하면 일관된 캐릭터로 영상 생성
- 전문가가 캐릭터 일관성 유지에 가장 많이 사용하는 기법

### 2.2 AI Music Generation (2026)

| Tool | 주요 기능 | Vivid 비교 |
|------|----------|-----------|
| **Suno Studio** | AI-native DAW, Timeline, Persona | 🔴 기본 생성만 |
| **Udio** | Stem Download, Cover/Remix | 🔴 미지원 |
| **Stable Audio 3** | 긴 곡, 스타일 제어 | 🟡 부분 지원 |

**핵심 Gap**: Suno Studio의 Persona 기능
- 음악 스타일을 저장하고 재사용
- 프로젝트 전체에 일관된 음악 스타일 적용

### 2.3 Character Consistency (2026)

| 기법 | 설명 | Vivid 비교 |
|------|------|-----------|
| **Reference Pro** | 레퍼런스 이미지 기반 일관성 | 🟢 CC앱 지원 |
| **LoRA Training** | 캐릭터별 모델 학습 | 🟡 미지원 (고급) |
| **Seed Locking** | 시드 고정으로 일관성 | 🟢 지원 |
| **Style Extraction** | 레퍼런스에서 스타일 추출 | 🔴 미지원 |

---

## Part 3: 앱별 Gap 분석 및 권고

### 3.1 4D Reference Decoder 🔴 Critical

**현황**:
```typescript
// 현재: 단순 이미지 분석
const analyzeReference = async (image: File) => {
  const result = await api.dimension.analyze4D({ image });
  return result; // 기본 분석 결과만
};
```

**전문가 워크플로우와 차이**:
| 전문가 | Vivid 현황 | Gap |
|--------|-----------|-----|
| 프레임별 분석 | 단일 이미지 분석 | 🔴 |
| 스타일 태그 추출 | 설명 텍스트만 | 🔴 |
| 레퍼런스 라이브러리 | 없음 | 🔴 |
| 무드보드 생성 | 없음 | 🔴 |

**하드닝 권고**:
```python
# 권고: 프레임별 분석 + 스타일 추출
class ReferenceAnalyzer:
    async def analyze_video_frames(self, video_url: str) -> FrameAnalysis:
        """프레임별 분석 및 스타일 추출"""
        frames = await self.extract_key_frames(video_url)
        style_tags = await self.extract_style_tags(frames)
        moodboard = await self.generate_moodboard(frames, style_tags)
        return FrameAnalysis(
            frames=frames,
            style_tags=style_tags,  # ["anime", "cel-shading", "vibrant"]
            moodboard=moodboard,
            reusable_style_prompt=self.generate_style_prompt(style_tags)
        )
```

**UI 개선 권고**:
- 프레임 타임라인 뷰 추가
- 스타일 태그 추출 및 편집 UI
- 레퍼런스 라이브러리 (저장/태깅/검색)
- 무드보드 자동 생성

---

### 3.2 3D Visual Realizer 🔴 Critical

**현황 (VisualRealizerPanel.tsx)**:
```typescript
const styleOptions = [
  { value: "photorealistic", label: "Photorealistic" },
  { value: "cinematic", label: "Cinematic" },
  // ... 고정된 스타일 프리셋
];
```

**전문가 워크플로우와 차이**:
| 전문가 | Vivid 현황 | Gap |
|--------|-----------|-----|
| Style + Scene 분리 | 단일 프롬프트 | 🔴 |
| 커스텀 스타일 저장 | 고정 프리셋만 | 🔴 |
| 레퍼런스 스타일 추출 | 없음 | 🔴 |

**하드닝 권고**:
```typescript
// 권고: Style Prompt + Scene Prompt 분리
interface ImageGenerationRequest {
  stylePrompt: string;       // 전체 프로젝트에 공통 적용
  scenePrompt: string;       // 씬마다 다름
  referenceImage?: string;   // 스타일 추출용
}

// UI 추가
const [stylePrompt, setStylePrompt] = useState(""); // 저장 가능
const [scenePrompt, setScenePrompt] = useState(""); // 씬별 입력

// 스타일 추출 기능
const extractStyleFromReference = async (image: File) => {
  const style = await api.dimension.extractStyle(image);
  setStylePrompt(style.stylePrompt);
};
```

---

### 3.3 VEO Video Maker 🟡 Medium

**현황 (VeoVideoPanel.tsx)**:
```typescript
// 지원: 시드 제어, 이미지-투-비디오, 스타일 옵션
const [seed, setSeed] = useState<string>("");
const [referenceImage, setReferenceImage] = useState<File | null>(null);
```

**전문가 워크플로우와 차이**:
| 전문가 (Kling) | Vivid (VEO) | Gap |
|----------------|-------------|-----|
| Start/End Frame | 없음 | 🔴 |
| Motion Brush | 없음 | 🟡 |
| 5분 영상 | 8초 최대 | 🟡 |

**하드닝 권고**:
```typescript
// 권고: Start/End Frame 기능 추가
interface VeoGenerationRequest {
  prompt: string;
  startFrame?: string;    // 첫 프레임 이미지
  endFrame?: string;      // 마지막 프레임 이미지
  duration: number;
  // ... existing fields
}

// UI 추가
<div className="grid grid-cols-2 gap-4">
  <ImageUploader
    label="Start Frame"
    onUpload={setStartFrame}
  />
  <ImageUploader
    label="End Frame"
    onUpload={setEndFrame}
  />
</div>
```

**참고**: Veo 3.1 API가 Start/End Frame을 지원하는지 확인 필요. 미지원 시 Kling 2.6 통합 고려.

---

### 3.4 Suno AI Music 🟡 Medium

**현황**:
- 기본 음악 생성만 지원
- 프롬프트 기반 생성

**전문가 워크플로우와 차이**:
| 전문가 | Vivid 현황 | Gap |
|--------|-----------|-----|
| Cover 생성 | 없음 | 🔴 |
| Remix 기능 | 없음 | 🔴 |
| Stem 다운로드 | 없음 | 🔴 |
| Persona (스타일 저장) | 없음 | 🔴 |

**하드닝 권고**:
```typescript
// 권고: 고급 음악 기능 추가
interface SunoGenerationRequest {
  prompt: string;
  mode: "create" | "cover" | "remix";  // 모드 추가
  referenceUrl?: string;               // 커버/리믹스 원본
  persona?: string;                     // 저장된 스타일
  outputFormat: "full" | "stems";      // 스템 분리
}

// UI 탭 추가
<Tabs defaultValue="create">
  <TabsList>
    <TabsTrigger value="create">Create</TabsTrigger>
    <TabsTrigger value="cover">Cover</TabsTrigger>
    <TabsTrigger value="remix">Remix</TabsTrigger>
  </TabsList>
</Tabs>
```

---

### 3.5 QC Quality Director 🟡 Medium

**현황**:
- 자동 품질 점수 제공 (hps_score, clip_score)
- 단일 결과물 분석

**전문가 워크플로우와 차이**:
| 전문가 | Vivid 현황 | Gap |
|--------|-----------|-----|
| A/B 비교 선별 | 없음 | 🔴 |
| 배치 생성 | 없음 | 🔴 |
| 수동 선별 UI | 없음 | 🔴 |

**하드닝 권고**:
```typescript
// 권고: A/B 비교 UI
interface QualityComparisonView {
  candidates: GeneratedContent[];  // 배치 생성 결과
  selected?: string[];            // 사용자 선택
}

// UI 컴포넌트
<div className="grid grid-cols-2 gap-4">
  {candidates.map((c, i) => (
    <div
      key={i}
      className={selected.includes(c.id) ? "ring-2 ring-primary" : ""}
      onClick={() => toggleSelect(c.id)}
    >
      <img src={c.url} />
      <Badge>Score: {c.score}</Badge>
    </div>
  ))}
</div>
```

---

### 3.6 Story Architect 🟡 Medium

**현황**:
- 시나리오/대사 생성
- 씬 분할

**전문가 워크플로우와 차이**:
| 전문가 | Vivid 현황 | Gap |
|--------|-----------|-----|
| Shot List 자동 생성 | 수동 | 🟡 |
| 타임코드 연동 | 없음 | 🟡 |
| 음악 싱크 | 없음 | 🔴 |

**하드닝 권고**:
```python
# 권고: Shot List 자동 생성
class StoryArchitect:
    async def generate_shot_list(
        self,
        script: str,
        music_bpm: Optional[int] = None
    ) -> ShotList:
        """스크립트에서 Shot List 자동 생성"""
        scenes = await self.parse_scenes(script)
        shots = []
        for scene in scenes:
            shot = Shot(
                description=scene.visual_description,
                duration=self.calculate_duration(scene, music_bpm),
                camera_movement=scene.suggested_camera,
                transition=scene.transition_type
            )
            shots.append(shot)
        return ShotList(shots=shots, total_duration=sum(s.duration for s in shots))
```

---

### 3.7 Character Consistency (CC) 🟢 Good

**현황 (CharacterConsistencyPanel.tsx)**:
```typescript
// StoryMem 기반, 플랫폼 연동
const platforms = ["Veo", "Kling", "Runway", "Hailuo"];
// Memory Keyframes with scores
```

**강점**:
- StoryMem 기반 캐릭터 라이브러리 ✅
- 다중 플랫폼 연동 ✅
- Memory Keyframes ✅

**개선 권고**:
- LoRA 학습 옵션 추가 (고급 사용자용)
- Start/End Frame 연동 (VEO/Kling)

---

### 3.8 Aesthetic Director (AD) 🟢 Good

**현황**: 거장 스타일 프리셋 지원

**개선 권고**:
- 레퍼런스 기반 스타일 분석 연동 (4D → AD)
- 커스텀 스타일 저장 기능

---

### 3.9 Storyboard Sketcher (2D) 🟢 Good

**현황**: 스토리보드 생성 지원

**개선 권고**:
- 타임코드 표시
- Shot List 연동 (Story → 2D)

---

### 3.10 Prompt Alchemy (1D) 🟢 Good

**현황**: 프롬프트 최적화

**개선 권고**:
- Style/Scene 프롬프트 분리 템플릿 추가
- 플랫폼별 프롬프트 변환

---

### 3.11 Abyss Mirror (AI) 🟢 Good

**현황**: 페르소나 분석

**개선 권고**:
- 음악 페르소나 분석 추가 (Suno Persona 연동)

---

### 3.12 Kling Video 🟢 Good

**현황**: Kling 2.6 통합

**강점**: Start/End Frame 네이티브 지원

**개선 권고**:
- VEO 패널과 UI 통일
- Motion Brush 지원

---

### 3.13 Sound Crafter 🔧 Development

**현황**: 개발 중

**권고**:
- 효과음 생성
- 영상 타임라인 싱크

---

## Part 4: 하드닝 로드맵

### Phase 1: Critical (2주)

| Task | App | 설명 |
|------|-----|------|
| H1-1 | 4D | 프레임별 분석 API |
| H1-2 | 4D | 스타일 추출 기능 |
| H1-3 | 3D | Style/Scene 프롬프트 분리 |
| H1-4 | 3D | 커스텀 스타일 저장 |

### Phase 2: Medium (4주)

| Task | App | 설명 |
|------|-----|------|
| H2-1 | VEO | Start/End Frame 기능 |
| H2-2 | Suno | Cover/Remix 모드 |
| H2-3 | Suno | Stem 다운로드 |
| H2-4 | QC | A/B 비교 UI |
| H2-5 | Story | Shot List 자동 생성 |

### Phase 3: Enhancement (4주)

| Task | App | 설명 |
|------|-----|------|
| H3-1 | 4D | 레퍼런스 라이브러리 |
| H3-2 | CC | LoRA 학습 옵션 |
| H3-3 | Story | 음악 싱크 |
| H3-4 | AD | 커스텀 스타일 저장 |

---

## Part 5: 기술 구현 상세

### 5.1 스타일 추출 API (4D)

```python
# backend/app/routers/dimension/reference_decoder.py

from pydantic import BaseModel
from typing import List

class StyleExtractionResult(BaseModel):
    style_tags: List[str]          # ["anime", "cel-shading", "vibrant"]
    style_prompt: str              # 재사용 가능한 스타일 프롬프트
    color_palette: List[str]       # 추출된 컬러 팔레트
    composition_notes: str         # 구도 분석
    mood: str                      # "energetic", "melancholic" 등

@router.post("/extract-style")
async def extract_style(
    file: UploadFile,
    user_id: str = Depends(get_current_user)
) -> StyleExtractionResult:
    """레퍼런스 이미지에서 스타일 추출"""
    # Gemini Vision으로 스타일 분석
    analysis = await gemini_client.analyze_image(
        file,
        prompt="""Analyze this reference image and extract:
        1. Style tags (anime, realistic, cel-shading, etc.)
        2. A reusable style prompt for image generation
        3. Color palette (hex codes)
        4. Composition notes
        5. Overall mood"""
    )
    return StyleExtractionResult.model_validate(analysis)
```

### 5.2 Style/Scene 분리 UI (3D)

```typescript
// frontend/src/components/dimension/VisualRealizerPanel.tsx

interface VisualRealizerState {
  stylePrompt: string;      // 프로젝트 전체 공통
  scenePrompt: string;      // 씬별 입력
  savedStyles: SavedStyle[]; // 저장된 스타일들
}

// 스타일 저장/로드 컴포넌트
<Card className="mb-4">
  <CardHeader>
    <CardTitle className="flex items-center justify-between">
      <span>{isKo ? "스타일 프롬프트" : "Style Prompt"}</span>
      <Button
        size="sm"
        variant="outline"
        onClick={saveCurrentStyle}
      >
        {isKo ? "저장" : "Save"}
      </Button>
    </CardTitle>
  </CardHeader>
  <CardContent>
    <Textarea
      value={stylePrompt}
      onChange={(e) => setStylePrompt(e.target.value)}
      placeholder={isKo
        ? "모든 이미지에 적용될 스타일을 입력하세요"
        : "Enter style applied to all images"
      }
    />
    {/* 저장된 스타일 목록 */}
    <div className="mt-2 flex gap-2 flex-wrap">
      {savedStyles.map((style) => (
        <Badge
          key={style.id}
          variant="outline"
          className="cursor-pointer"
          onClick={() => setStylePrompt(style.prompt)}
        >
          {style.name}
        </Badge>
      ))}
    </div>
  </CardContent>
</Card>

<Card>
  <CardHeader>
    <CardTitle>{isKo ? "씬 프롬프트" : "Scene Prompt"}</CardTitle>
  </CardHeader>
  <CardContent>
    <Textarea
      value={scenePrompt}
      onChange={(e) => setScenePrompt(e.target.value)}
      placeholder={isKo
        ? "이 씬의 내용을 입력하세요"
        : "Enter this scene's content"
      }
    />
  </CardContent>
</Card>
```

### 5.3 A/B 비교 UI (QC)

```typescript
// frontend/src/components/dimension/QualityDirectorPanel.tsx

interface ComparisonViewProps {
  candidates: GeneratedContent[];
  onSelect: (ids: string[]) => void;
}

function ComparisonView({ candidates, onSelect }: ComparisonViewProps) {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const { isKo } = useLanguage();

  const toggleSelect = (id: string) => {
    const newSelected = new Set(selected);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelected(newSelected);
    onSelect(Array.from(newSelected));
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="font-medium">
          {isKo ? "결과 비교 및 선택" : "Compare & Select"}
        </h3>
        <Badge variant="secondary">
          {selected.size} / {candidates.length} {isKo ? "선택됨" : "selected"}
        </Badge>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {candidates.map((c) => (
          <div
            key={c.id}
            className={cn(
              "relative rounded-lg overflow-hidden cursor-pointer transition-all",
              selected.has(c.id)
                ? "ring-2 ring-primary shadow-lg"
                : "hover:ring-1 hover:ring-muted-foreground"
            )}
            onClick={() => toggleSelect(c.id)}
          >
            <img src={c.url} alt="" className="w-full aspect-video object-cover" />
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 p-2">
              <div className="flex justify-between text-white text-xs">
                <span>Score: {c.quality_score.toFixed(2)}</span>
                {selected.has(c.id) && (
                  <CheckCircle className="w-4 h-4 text-green-400" />
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Part 6: 결론

### 핵심 Action Items

1. **4D Reference Decoder**: 전문가 워크플로우의 핵심인 레퍼런스 분석 강화
   - 프레임별 분석
   - 스타일 추출
   - 레퍼런스 라이브러리

2. **3D Visual Realizer**: Style/Scene 분리로 일관성 향상
   - 스타일 프롬프트 분리
   - 커스텀 스타일 저장

3. **VEO Video Maker**: Start/End Frame 기능으로 캐릭터 일관성
   - Kling 기능 참고
   - API 지원 여부 확인

4. **Suno AI Music**: Cover/Remix로 활용도 향상
   - Suno API 신규 기능 확인
   - Persona 기능 추가

5. **QC Quality Director**: A/B 비교로 선별 효율화
   - 배치 생성 지원
   - 비교 UI 추가

### ROI 예상

| 하드닝 | 예상 효과 |
|--------|----------|
| 4D + 3D 스타일 추출 | 작업 시간 40% 단축 |
| VEO Start/End Frame | 캐릭터 일관성 80%+ |
| Suno Cover/Remix | 음악 활용도 3배 |
| QC A/B 비교 | 선별 효율 50% 향상 |

---

## Part 7: Backend Implementation Guide (2026 Best Practices)

> **Based on 2026 Web Research**: FastAPI LLM patterns, Veo 3.1 API, Kling 2.6 API, Suno API

---

### 7.1 FastAPI 2026 Best Practices for AI Services

#### 7.1.1 Project Structure

```
backend/app/
├── services/
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── base.py              # AIServiceBase ABC
│   │   ├── veo_service.py       # Veo 3.1 integration
│   │   ├── kling_service.py     # Kling 2.6 integration
│   │   ├── suno_service.py      # Suno music integration
│   │   ├── style_extractor.py   # Style extraction service
│   │   └── reference_analyzer.py # Reference analysis service
│   └── ...
├── routers/
│   └── dimension/
│       ├── _base.py             # Common utilities
│       ├── reference_decoder.py  # 4D - Enhanced
│       ├── visual_realizer.py    # 3D - Style/Scene split
│       ├── veo.py               # VEO - First/Last frame
│       ├── kling.py             # Kling - Start/End frame
│       └── suno.py              # Suno - Cover/Remix
└── schemas/
    └── ai/
        ├── video.py             # Video generation schemas
        ├── music.py             # Music generation schemas
        └── style.py             # Style extraction schemas
```

#### 7.1.2 AI Service Base Class

```python
# backend/app/services/ai/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
import httpx
import asyncio
from contextlib import asynccontextmanager

T = TypeVar("T", bound=BaseModel)
R = TypeVar("R", bound=BaseModel)

class AIServiceBase(ABC, Generic[T, R]):
    """Base class for all AI service integrations (2026 pattern)."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 300.0,  # 5 minutes for video generation
        max_retries: int = 3,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    @asynccontextmanager
    async def get_client(self):
        """Async context manager for httpx client reuse."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
        try:
            yield self._client
        finally:
            pass  # Keep client alive for reuse

    async def close(self):
        """Close the client connection."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @abstractmethod
    async def generate(self, request: T) -> R:
        """Generate content - implemented by subclasses."""
        pass

    async def poll_operation(
        self,
        operation_id: str,
        poll_interval: float = 15.0,
        max_wait: float = 600.0,
    ) -> dict:
        """Poll long-running operation until completion."""
        elapsed = 0.0
        while elapsed < max_wait:
            async with self.get_client() as client:
                response = await client.get(f"/operations/{operation_id}")
                data = response.json()

                if data.get("done"):
                    return data.get("response", data)

                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

        raise TimeoutError(f"Operation {operation_id} timed out after {max_wait}s")
```

#### 7.1.3 Streaming Response Pattern (SSE)

```python
# backend/app/routers/dimension/_base.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json
import asyncio

async def stream_generation_progress(
    operation_id: str,
    service: AIServiceBase,
    poll_interval: float = 5.0,
):
    """SSE streaming for long-running AI operations."""
    yield f"data: {json.dumps({'type': 'started', 'operation_id': operation_id})}\n\n"

    elapsed = 0.0
    max_wait = 600.0

    while elapsed < max_wait:
        try:
            status = await service.get_operation_status(operation_id)

            if status.get("done"):
                yield f"data: {json.dumps({'type': 'completed', 'result': status.get('response')})}\n\n"
                return

            # Progress update
            progress = status.get("progress", 0)
            yield f"data: {json.dumps({'type': 'progress', 'progress': progress})}\n\n"

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return

    yield f"data: {json.dumps({'type': 'timeout'})}\n\n"
```

---

### 7.2 Veo 3.1 First/Last Frame API Integration

> **2026 Discovery**: Veo 3.1 supports `first_frame` and `last_frame` parameters for interpolation!

#### 7.2.1 Veo Service Implementation

```python
# backend/app/services/ai/veo_service.py
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import Optional
import time
import base64

class VeoGenerationRequest(BaseModel):
    prompt: str
    first_frame: Optional[str] = None   # base64 encoded image
    last_frame: Optional[str] = None    # base64 encoded image
    aspect_ratio: str = "16:9"
    resolution: str = "720p"
    duration_seconds: int = 8
    seed: Optional[int] = None

class VeoGenerationResponse(BaseModel):
    video_url: str
    duration: float
    operation_id: str

class VeoService:
    """Veo 3.1 Service with First/Last Frame Support (2026)."""

    def __init__(self):
        self.client = genai.Client()
        self.model = "veo-3.1-generate-preview"

    async def generate_video(
        self,
        request: VeoGenerationRequest,
    ) -> VeoGenerationResponse:
        """Generate video with optional first/last frame interpolation."""

        # Build config
        config = types.GenerateVideosConfig(
            aspect_ratio=request.aspect_ratio,
            resolution=request.resolution,
            duration_seconds=request.duration_seconds,
        )

        # Add last frame if provided (for interpolation)
        if request.last_frame:
            last_image = self._decode_image(request.last_frame)
            config.last_frame = last_image

        # Build generation params
        gen_params = {
            "model": self.model,
            "prompt": request.prompt,
            "config": config,
        }

        # Add first frame if provided
        if request.first_frame:
            first_image = self._decode_image(request.first_frame)
            gen_params["image"] = first_image

        # Start generation (async operation)
        operation = self.client.models.generate_videos(**gen_params)

        # Poll until complete
        while not operation.done:
            time.sleep(15)
            operation = self.client.operations.get(operation)

        # Get result
        video = operation.response.generated_videos[0]

        return VeoGenerationResponse(
            video_url=video.video.uri,
            duration=request.duration_seconds,
            operation_id=str(operation.name),
        )

    def _decode_image(self, base64_str: str) -> types.Image:
        """Decode base64 image for API."""
        image_bytes = base64.b64decode(base64_str)
        return types.Image(image_bytes=image_bytes)
```

#### 7.2.2 VEO Router with First/Last Frame

```python
# backend/app/routers/dimension/veo.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from app.services.ai.veo_service import VeoService, VeoGenerationRequest
from app.services.credit_service import CreditService
from app.auth import get_current_user
import base64

router = APIRouter(prefix="/veo", tags=["VEO Video"])

@router.post("/generate")
async def generate_video(
    prompt: str = Form(...),
    first_frame: Optional[UploadFile] = File(None),
    last_frame: Optional[UploadFile] = File(None),
    aspect_ratio: str = Form("16:9"),
    duration: int = Form(8),
    user_id: str = Depends(get_current_user),
    credit_service: CreditService = Depends(),
    veo_service: VeoService = Depends(),
):
    """Generate video with optional first/last frame for character consistency."""

    # Check credits
    cost = 50 if duration <= 8 else 100
    await credit_service.check_and_reserve(user_id, cost)

    try:
        # Encode frames if provided
        first_frame_b64 = None
        last_frame_b64 = None

        if first_frame:
            content = await first_frame.read()
            first_frame_b64 = base64.b64encode(content).decode()

        if last_frame:
            content = await last_frame.read()
            last_frame_b64 = base64.b64encode(content).decode()

        request = VeoGenerationRequest(
            prompt=prompt,
            first_frame=first_frame_b64,
            last_frame=last_frame_b64,
            aspect_ratio=aspect_ratio,
            duration_seconds=duration,
        )

        result = await veo_service.generate_video(request)
        await credit_service.commit(user_id, cost)

        return {
            "success": True,
            "video_url": result.video_url,
            "evidence_refs": [f"db:veo_generations:{result.operation_id}"],
        }

    except Exception as e:
        await credit_service.refund(user_id, cost)
        raise HTTPException(status_code=500, detail=str(e))
```

---

### 7.3 Kling 2.6 Start/End Frame Integration

> **2026 Discovery**: Kling 2.6 has native Start/End Frame support via fal.ai API

#### 7.3.1 Kling Service Implementation

```python
# backend/app/services/ai/kling_service.py
import httpx
from pydantic import BaseModel
from typing import Optional
import asyncio

class KlingGenerationRequest(BaseModel):
    prompt: str
    start_image_url: Optional[str] = None   # URL or base64
    end_image_url: Optional[str] = None     # URL or base64 - KEY FEATURE!
    duration: str = "5"                      # "5" or "10" seconds
    negative_prompt: str = "blur, distort, low quality"
    generate_audio: bool = True              # Native audio in 2.6!
    aspect_ratio: str = "16:9"

class KlingService:
    """Kling 2.6 Service via fal.ai (2026)."""

    FAL_API_URL = "https://fal.run/fal-ai/kling-video/v2.6/pro/image-to-video"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate_video(
        self,
        request: KlingGenerationRequest,
    ) -> dict:
        """Generate video with Start/End Frame interpolation."""

        payload = {
            "prompt": request.prompt,
            "duration": request.duration,
            "negative_prompt": request.negative_prompt,
            "generate_audio": request.generate_audio,
        }

        # Add start frame (image-to-video)
        if request.start_image_url:
            payload["start_image_url"] = request.start_image_url

        # Add end frame (KEY: character consistency!)
        if request.end_image_url:
            payload["end_image_url"] = request.end_image_url

        async with httpx.AsyncClient() as client:
            # Submit request
            response = await client.post(
                self.FAL_API_URL,
                json=payload,
                headers={"Authorization": f"Key {self.api_key}"},
                timeout=30.0,
            )

            if response.status_code != 200:
                raise Exception(f"Kling API error: {response.text}")

            result = response.json()

            # If queue-based, poll for result
            if "request_id" in result:
                return await self._poll_result(client, result["request_id"])

            return result

    async def _poll_result(
        self,
        client: httpx.AsyncClient,
        request_id: str,
        max_attempts: int = 40,
    ) -> dict:
        """Poll for result (Kling takes ~2-5 minutes)."""

        status_url = f"https://fal.run/fal-ai/kling-video/v2.6/pro/requests/{request_id}/status"

        for _ in range(max_attempts):
            response = await client.get(
                status_url,
                headers={"Authorization": f"Key {self.api_key}"},
            )

            data = response.json()

            if data.get("status") == "COMPLETED":
                return data.get("response", data)

            if data.get("status") == "FAILED":
                raise Exception(f"Generation failed: {data.get('error')}")

            await asyncio.sleep(15)  # 15 seconds between polls

        raise TimeoutError("Kling generation timed out")
```

#### 7.3.2 Kling Router

```python
# backend/app/routers/dimension/kling.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from app.services.ai.kling_service import KlingService, KlingGenerationRequest
from app.services.storage_service import StorageService
from app.auth import get_current_user

router = APIRouter(prefix="/kling", tags=["Kling Video"])

@router.post("/generate")
async def generate_kling_video(
    prompt: str = Form(...),
    start_frame: Optional[UploadFile] = File(None),
    end_frame: Optional[UploadFile] = File(None),
    duration: str = Form("5"),
    generate_audio: bool = Form(True),
    user_id: str = Depends(get_current_user),
    kling_service: KlingService = Depends(),
    storage: StorageService = Depends(),
):
    """Generate Kling video with Start/End Frame for perfect character consistency."""

    # Upload frames to get URLs
    start_url = None
    end_url = None

    if start_frame:
        start_url = await storage.upload_temp(await start_frame.read(), "image/jpeg")

    if end_frame:
        end_url = await storage.upload_temp(await end_frame.read(), "image/jpeg")

    request = KlingGenerationRequest(
        prompt=prompt,
        start_image_url=start_url,
        end_image_url=end_url,
        duration=duration,
        generate_audio=generate_audio,
    )

    result = await kling_service.generate_video(request)

    return {
        "success": True,
        "video": result.get("video", {}).get("url"),
        "audio_included": generate_audio,
        "evidence_refs": [f"db:kling_generations:{result.get('id')}"],
    }
```

---

### 7.4 Suno API Integration (Music Generation)

> **2026 Note**: Suno has no official API. Use sunoapi.org or AIMLAPI for integration.

#### 7.4.1 Suno Service Implementation

```python
# backend/app/services/ai/suno_service.py
import httpx
from pydantic import BaseModel
from typing import Optional, Literal
from enum import Enum
import asyncio

class SunoMode(str, Enum):
    CREATE = "create"
    COVER = "cover"       # NEW: Cover generation
    REMIX = "remix"       # NEW: Remix generation
    EXTEND = "extend"     # Extend existing track

class SunoGenerationRequest(BaseModel):
    prompt: str
    mode: SunoMode = SunoMode.CREATE
    reference_url: Optional[str] = None    # For cover/remix
    model: str = "chirp-v3-5"              # or "chirp-v4", "chirp-v5"
    instrumental: bool = False
    custom_lyrics: Optional[str] = None
    style_of_music: Optional[str] = None
    persona: Optional[str] = None          # NEW: Saved style persona

class SunoService:
    """Suno Music Service via sunoapi.org (2026)."""

    BASE_URL = "https://api.sunoapi.org/api/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate_music(
        self,
        request: SunoGenerationRequest,
    ) -> dict:
        """Generate music with various modes."""

        payload = {
            "prompt": request.prompt,
            "model": request.model,
            "instrumental": request.instrumental,
        }

        if request.custom_lyrics:
            payload["lyrics"] = request.custom_lyrics

        if request.style_of_music:
            payload["style"] = request.style_of_music

        # Mode-specific handling
        if request.mode == SunoMode.COVER:
            payload["cover_url"] = request.reference_url
            endpoint = "/cover"
        elif request.mode == SunoMode.REMIX:
            payload["remix_url"] = request.reference_url
            endpoint = "/remix"
        elif request.mode == SunoMode.EXTEND:
            payload["extend_from"] = request.reference_url
            endpoint = "/extend"
        else:
            endpoint = "/generate"

        async with httpx.AsyncClient() as client:
            # Submit generation
            response = await client.post(
                f"{self.BASE_URL}{endpoint}",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )

            data = response.json()

            if data.get("code") != 200:
                raise Exception(f"Suno API error: {data.get('msg')}")

            task_id = data.get("data", {}).get("taskId")

            # Poll for result (music generation takes 30-60s)
            return await self._poll_result(client, task_id)

    async def _poll_result(
        self,
        client: httpx.AsyncClient,
        task_id: str,
        max_attempts: int = 20,
    ) -> dict:
        """Poll for music generation result."""

        for _ in range(max_attempts):
            response = await client.get(
                f"{self.BASE_URL}/status/{task_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )

            data = response.json()
            status = data.get("data", {}).get("status")

            if status == "SUCCESS":
                return data.get("data", {})

            if status == "FAILED":
                raise Exception(f"Music generation failed")

            await asyncio.sleep(30)  # 30 seconds as recommended

        raise TimeoutError("Suno generation timed out")

    async def get_stems(self, song_id: str) -> dict:
        """Download separated stems (vocals, drums, bass, etc.)."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/generate_stems",
                json={"song_id": song_id},
                headers={"Authorization": f"Bearer {self.api_key}"},
            )

            return response.json()
```

#### 7.4.2 Suno Router with Cover/Remix

```python
# backend/app/routers/dimension/suno.py
from fastapi import APIRouter, Depends, HTTPException, Form
from app.services.ai.suno_service import SunoService, SunoGenerationRequest, SunoMode
from app.auth import get_current_user

router = APIRouter(prefix="/suno", tags=["Suno Music"])

@router.post("/generate")
async def generate_music(
    prompt: str = Form(...),
    mode: SunoMode = Form(SunoMode.CREATE),
    reference_url: Optional[str] = Form(None),
    style: Optional[str] = Form(None),
    instrumental: bool = Form(False),
    lyrics: Optional[str] = Form(None),
    user_id: str = Depends(get_current_user),
    suno_service: SunoService = Depends(),
):
    """Generate music with Create, Cover, or Remix modes."""

    request = SunoGenerationRequest(
        prompt=prompt,
        mode=mode,
        reference_url=reference_url,
        style_of_music=style,
        instrumental=instrumental,
        custom_lyrics=lyrics,
    )

    result = await suno_service.generate_music(request)

    return {
        "success": True,
        "tracks": result.get("songs", []),
        "mode": mode,
        "evidence_refs": [f"db:suno_generations:{result.get('id')}"],
    }

@router.post("/stems/{song_id}")
async def get_stems(
    song_id: str,
    user_id: str = Depends(get_current_user),
    suno_service: SunoService = Depends(),
):
    """Get separated stems for a generated song."""

    result = await suno_service.get_stems(song_id)

    return {
        "success": True,
        "stems": result.get("stems", {}),
    }
```

---

### 7.5 Style Extraction Service (4D/3D Core Feature)

> **Expert Insight**: "스타일 프롬프트라고 따로 둬요... 일관성을 위해서"

#### 7.5.1 Style Extraction Service

```python
# backend/app/services/ai/style_extractor.py
from pydantic import BaseModel
from typing import List, Optional
from app.gemini_client import GeminiClient
import json

class StyleExtractionResult(BaseModel):
    style_tags: List[str]           # ["anime", "cel-shading", "vibrant", "high-contrast"]
    style_prompt: str               # Reusable style prompt
    color_palette: List[str]        # ["#FF5733", "#33FF57", ...]
    lighting: str                   # "dramatic", "soft", "neon"
    composition: str                # "centered", "rule-of-thirds", "symmetrical"
    mood: str                       # "energetic", "melancholic", "mysterious"
    camera_angle: Optional[str]     # "low-angle", "eye-level", "bird's-eye"
    reference_artists: List[str]    # Similar known artists/styles

class StyleExtractor:
    """Extract reusable style from reference images (2026 Expert Workflow)."""

    EXTRACTION_PROMPT = """Analyze this reference image and extract style information.

Return a JSON object with:
1. style_tags: List of style descriptors (anime, photorealistic, cel-shading, etc.)
2. style_prompt: A reusable prompt that captures this exact visual style (50-100 words)
3. color_palette: List of 5-7 dominant colors as hex codes
4. lighting: Type of lighting (dramatic, soft, neon, natural, etc.)
5. composition: Composition style (centered, rule-of-thirds, etc.)
6. mood: Overall mood/atmosphere
7. camera_angle: If applicable
8. reference_artists: Similar known artists or styles this resembles

The style_prompt should be detailed enough to recreate this visual style consistently
across different scenes. Focus on technical aspects like rendering style, color grading,
line work, shading technique, and atmosphere.

Return ONLY valid JSON, no markdown."""

    def __init__(self, gemini_client: GeminiClient):
        self.gemini = gemini_client

    async def extract_style(
        self,
        image_bytes: bytes,
        additional_context: Optional[str] = None,
    ) -> StyleExtractionResult:
        """Extract style from reference image."""

        prompt = self.EXTRACTION_PROMPT
        if additional_context:
            prompt += f"\n\nAdditional context: {additional_context}"

        response = await self.gemini.analyze_image(
            image_bytes=image_bytes,
            prompt=prompt,
            response_format="json",
        )

        # Parse JSON response
        try:
            data = json.loads(response)
            return StyleExtractionResult.model_validate(data)
        except json.JSONDecodeError:
            # Fallback parsing
            return self._fallback_parse(response)

    async def extract_from_video_frames(
        self,
        video_url: str,
        num_frames: int = 5,
    ) -> StyleExtractionResult:
        """Extract consistent style from video key frames."""

        # Extract key frames
        frames = await self._extract_key_frames(video_url, num_frames)

        # Analyze each frame
        results = []
        for frame in frames:
            result = await self.extract_style(frame)
            results.append(result)

        # Merge results (find common elements)
        return self._merge_style_results(results)

    def _merge_style_results(
        self,
        results: List[StyleExtractionResult],
    ) -> StyleExtractionResult:
        """Merge multiple style extractions into consistent result."""

        # Find common style tags
        all_tags = [set(r.style_tags) for r in results]
        common_tags = list(set.intersection(*all_tags)) if all_tags else []

        # Use first result as base, augment with common elements
        base = results[0]
        base.style_tags = common_tags or base.style_tags

        return base
```

#### 7.5.2 Reference Analyzer Service (4D Enhancement)

```python
# backend/app/services/ai/reference_analyzer.py
from pydantic import BaseModel
from typing import List, Optional
from app.services.ai.style_extractor import StyleExtractor, StyleExtractionResult
import cv2
import numpy as np
from io import BytesIO

class FrameAnalysis(BaseModel):
    timestamp: float
    description: str
    objects: List[str]
    actions: List[str]
    camera_movement: Optional[str]

class VideoReferenceAnalysis(BaseModel):
    total_duration: float
    frame_count: int
    frames: List[FrameAnalysis]
    style: StyleExtractionResult
    suggested_shot_list: List[dict]
    moodboard_images: List[str]      # Key frame URLs for moodboard

class ReferenceAnalyzer:
    """Comprehensive reference analysis (Expert Workflow Core)."""

    def __init__(
        self,
        style_extractor: StyleExtractor,
        gemini_client: GeminiClient,
    ):
        self.style_extractor = style_extractor
        self.gemini = gemini_client

    async def analyze_video_reference(
        self,
        video_bytes: bytes,
        analysis_depth: str = "detailed",  # "quick", "detailed", "comprehensive"
    ) -> VideoReferenceAnalysis:
        """Analyze video reference frame by frame."""

        # Extract key frames
        frames, timestamps = self._extract_key_frames(
            video_bytes,
            num_frames=10 if analysis_depth == "quick" else 20,
        )

        # Analyze each frame
        frame_analyses = []
        for frame, timestamp in zip(frames, timestamps):
            analysis = await self._analyze_frame(frame, timestamp)
            frame_analyses.append(analysis)

        # Extract overall style
        style = await self.style_extractor.extract_style(frames[0])

        # Generate shot list suggestions
        shot_list = await self._generate_shot_list(frame_analyses)

        # Select best frames for moodboard
        moodboard = self._select_moodboard_frames(frames, frame_analyses)

        return VideoReferenceAnalysis(
            total_duration=timestamps[-1] if timestamps else 0,
            frame_count=len(frames),
            frames=frame_analyses,
            style=style,
            suggested_shot_list=shot_list,
            moodboard_images=moodboard,
        )

    def _extract_key_frames(
        self,
        video_bytes: bytes,
        num_frames: int = 10,
    ) -> tuple[List[bytes], List[float]]:
        """Extract key frames from video."""

        # Write to temp file for OpenCV
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(video_bytes)
            temp_path = f.name

        cap = cv2.VideoCapture(temp_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        # Calculate frame intervals
        interval = max(1, total_frames // num_frames)

        frames = []
        timestamps = []

        for i in range(0, total_frames, interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()

            if ret:
                # Encode frame as JPEG bytes
                _, buffer = cv2.imencode(".jpg", frame)
                frames.append(buffer.tobytes())
                timestamps.append(i / fps)

        cap.release()
        return frames[:num_frames], timestamps[:num_frames]

    async def _analyze_frame(
        self,
        frame_bytes: bytes,
        timestamp: float,
    ) -> FrameAnalysis:
        """Analyze single frame."""

        response = await self.gemini.analyze_image(
            image_bytes=frame_bytes,
            prompt="""Analyze this video frame and return JSON:
            {
                "description": "Brief scene description",
                "objects": ["list", "of", "objects"],
                "actions": ["list", "of", "actions"],
                "camera_movement": "pan/tilt/zoom/static/etc or null"
            }""",
        )

        data = json.loads(response)
        data["timestamp"] = timestamp
        return FrameAnalysis.model_validate(data)

    async def _generate_shot_list(
        self,
        frame_analyses: List[FrameAnalysis],
    ) -> List[dict]:
        """Generate shot list from frame analyses."""

        # Group similar frames into shots
        shots = []
        current_shot = {"frames": [], "start": 0}

        for i, frame in enumerate(frame_analyses):
            if i == 0:
                current_shot["frames"].append(frame)
                continue

            # Check if scene changed
            prev = frame_analyses[i-1]
            if self._is_scene_change(prev, frame):
                current_shot["end"] = prev.timestamp
                shots.append(self._create_shot_entry(current_shot))
                current_shot = {"frames": [frame], "start": frame.timestamp}
            else:
                current_shot["frames"].append(frame)

        # Add last shot
        if current_shot["frames"]:
            current_shot["end"] = frame_analyses[-1].timestamp
            shots.append(self._create_shot_entry(current_shot))

        return shots
```

---

### 7.6 Multi-Model Router Pattern

> **2026 Best Practice**: Route to different AI models based on task complexity and cost

```python
# backend/app/services/ai/model_router.py
from typing import Literal, Optional
from pydantic import BaseModel
import os

class ModelRouter:
    """Route AI requests to appropriate models based on task."""

    # Video model tiers
    VIDEO_MODELS = {
        "fast": "veo-3.1-generate-preview",      # Fast, lower quality
        "balanced": "kling-video@2.6-pro",        # Good quality, reasonable speed
        "premium": "sora-2",                       # Best quality, slow
    }

    # Image model tiers
    IMAGE_MODELS = {
        "fast": "gemini-2.5-flash-image",
        "balanced": "flux-2-pro",
        "premium": "dall-e-3",
    }

    @classmethod
    def select_video_model(
        cls,
        task_type: str,
        priority: Literal["speed", "quality", "cost"] = "balanced",
        has_reference_frames: bool = False,
    ) -> str:
        """Select appropriate video model for task."""

        # If using Start/End frames, prefer Kling (best support)
        if has_reference_frames and priority != "premium":
            return cls.VIDEO_MODELS["balanced"]  # Kling

        if priority == "speed":
            return cls.VIDEO_MODELS["fast"]
        elif priority == "premium":
            return cls.VIDEO_MODELS["premium"]
        else:
            return cls.VIDEO_MODELS["balanced"]

    @classmethod
    def estimate_cost(cls, model: str, duration: int) -> int:
        """Estimate credit cost for generation."""

        costs = {
            "veo-3.1-generate-preview": 50,
            "kling-video@2.6-pro": 80,
            "sora-2": 150,
        }

        base_cost = costs.get(model, 50)

        # Scale by duration
        if duration > 8:
            base_cost = int(base_cost * 1.5)

        return base_cost
```

---

### 7.7 Database Schema Updates

```python
# backend/app/models/style_library.py
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class StylePreset(Base):
    """User-saved style presets (Expert Workflow)."""

    __tablename__ = "style_presets"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    style_prompt = Column(String(2000), nullable=False)
    style_tags = Column(JSON, default=list)
    color_palette = Column(JSON, default=list)
    reference_image_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    usage_count = Column(Integer, default=0)

    user = relationship("User", back_populates="style_presets")


class ReferenceLibrary(Base):
    """User reference library with tagging."""

    __tablename__ = "reference_library"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String(200))
    type = Column(String(20))  # "image", "video"
    url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500))
    tags = Column(JSON, default=list)
    extracted_style_id = Column(String, ForeignKey("style_presets.id"))
    analysis = Column(JSON)  # Cached analysis result
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="references")
    extracted_style = relationship("StylePreset")
```

---

### 7.8 API Endpoints Summary

| Endpoint | Method | Description | Priority |
|----------|--------|-------------|----------|
| `/api/dimension/4d/analyze-frames` | POST | Frame-by-frame video analysis | P0 |
| `/api/dimension/4d/extract-style` | POST | Style extraction from reference | P0 |
| `/api/dimension/3d/generate` | POST | Image with Style/Scene split | P0 |
| `/api/dimension/veo/generate` | POST | Video with first/last frame | P1 |
| `/api/dimension/kling/generate` | POST | Video with start/end frame | P1 |
| `/api/dimension/suno/generate` | POST | Music with cover/remix modes | P1 |
| `/api/dimension/suno/stems/{id}` | POST | Get separated stems | P1 |
| `/api/dimension/qc/batch-generate` | POST | Batch generation for A/B | P2 |
| `/api/style-presets` | CRUD | Style preset management | P0 |
| `/api/reference-library` | CRUD | Reference library management | P0 |

---

## Appendix: 참조 자료

### A. 전문가 강의 원문 주요 발췌

```
1. "레퍼런스 조사가 저한테는 제일 중요한 것 같아요"
2. "스타일 프롬프트라고 따로 둬요"
3. "생성된 것 중에서 고르는 작업을 제일 많이 해요"
4. "영상 퀄리티보다 음악이 더 중요해요"
5. "처음부터 내가 원하는 이미지가 나오는 경우는 거의 없어요"
```

### B. 2026 Tavily 웹 리서치 소스

#### B.1 FastAPI & AI Integration

| Source | URL | Key Insight |
|--------|-----|-------------|
| Nucamp AI APIs 2026 | nucamp.co/blog/integrating-ai-apis-in-2026 | MCP protocol, model routing |
| Medium: FastAPI LLM Architecture | medium.com/@moradikor296 | DDD, async patterns, ProcessPoolExecutor |
| Zestminds FastAPI 2026 | zestminds.com/blog/fastapi-requirements-setup-guide | Weaviate + OpenAI integration |
| DataCamp FastAPI AI Course | datacamp.com/courses/deploying-ai-into-production | Rate limiting, API versioning |

#### B.2 Video Generation APIs

| Source | URL | Key Insight |
|--------|-----|-------------|
| Google Veo 3.1 Docs | ai.google.dev/gemini-api/docs/video | First/last frame interpolation |
| fal.ai Kling 2.6 Pro | fal.ai/models/fal-ai/kling-video/v2.6/pro | start_image_url, end_image_url params |
| Pixazo Best I2V APIs | pixazo.ai/blog/best-image-to-video-api | Kling vs Veo vs Runway comparison |
| WaveSpeed AI Video 2026 | wavespeed.ai/blog/posts/best-ai-video-generators-2026 | Multi-model API approach |
| Leonardo AI Kling Docs | docs.leonardo.ai/docs/generate-with-kling-2-6 | guidances.start_frame schema |

#### B.3 Music Generation APIs

| Source | URL | Key Insight |
|--------|-----|-------------|
| Suno Official Hub | suno.com/hub/create-music-with-ai | Suno Studio DAW, Persona feature |
| AIMLAPI Suno | aimlapi.com/suno-ai-api | chirp-v3-5, chirp-v4 models |
| sunoapi.org Docs | docs.sunoapi.org | Cover, Remix, Stems endpoints |
| GitHub gcui-art/suno-api | github.com/gcui-art/suno-api | generate_stems, extend_audio |

#### B.4 Style Extraction & Analysis

| Source | URL | Key Insight |
|--------|-----|-------------|
| WaveSpeed Style Transfer | wavespeed.ai/blog/posts/complete-guide-ai-image-apis-2026 | style_reference + style_strength |
| Index.dev AI API Tools | index.dev/blog/best-ai-tools-for-api-development-testing | Claude for nuanced analysis |
| Firecrawl Semantic Search | firecrawl.dev/blog/best-semantic-search-apis | RAG backbone for AI apps |

### C. Vivid 현황 분석 파일

- `frontend/src/components/dimension/VeoVideoPanel.tsx`
- `frontend/src/components/dimension/CharacterConsistencyPanel.tsx`
- `frontend/src/components/dimension/VisualRealizerPanel.tsx`
- `frontend/src/components/dimension/StoryArchitectPanel.tsx`
- `frontend/src/components/dimension/AbyssMirrorPanel.tsx`
- `backend/app/routers/dimension/*.py`
- `backend/app/services/veo_service.py`
- `backend/app/services/credit_service.py`

### D. 관련 Vivid 문서

- `docs/DIMENSION_APP_DEVELOPER_GUIDE.md` - 앱 개발 가이드
- `docs/RAG_ARCHITECTURE.md` - Multi-RAG Router 아키텍처
- `docs/TESTING_GUIDE.md` - 테스트 작성 가이드
- `backend/CLAUDE.md` - Backend 개발 패턴

---

*Report generated: 2026-01-18*
*Report version: 2.0 (Backend Implementation Guide 추가)*
*Author: Claude Code + Vivid Expert Agent*
*Research: Tavily MCP Web Search (2026-01-18)*
