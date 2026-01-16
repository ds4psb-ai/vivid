# Dimension App Development Strategy 2026

> 2026 Best Practices 기반 앱 개발 순서 및 워크플로우 협응 가이드

---

## Executive Summary

10개 Dimension 앱의 개발 순서, 차별화 전략, 워크플로우 협응 구조를 분석한 결과:

- **UI 조화도**: ✅ 높음 (DimensionPanel 통합 시스템)
- **React 19 준수율**: 80% (8/10 앱이 Golden App 패턴)
- **워크플로우 협응**: ✅ 완벽한 파이프라인 구조
- **개선 필요**: QualityDirectorPanel, AbyssMirrorPanel React 19 마이그레이션

---

## 1. 2026 Best Practices Research Summary

### 1.1 Key Trends (Web Search 결과)

| 트렌드 | 설명 | Vivid 적용 상태 |
|--------|------|-----------------|
| **One-Decision Per Screen** | 화면당 하나의 인지 결정만 요구 | ⚠️ 부분 적용 (다단계 앱은 위저드 형태) |
| **AI-First Creative Workflow** | Figma Make, Canva Magic Studio 패턴 | ✅ Dimension 앱 전체 구조 |
| **Context-Native Workflows** | 이전 출력이 다음 단계의 입력 | ✅ DimensionChainContext |
| **Design System Consistency** | Tailwind + shadcn/ui 표준화 | ✅ DimensionPanel 통합 |

### 1.2 React 19 Golden App Pattern

```tsx
// 2026 필수 패턴
import { useTransition, useOptimistic } from "react";

function GoldenPanel() {
  const [isPending, startTransition] = useTransition();
  const [optimisticResult, setOptimisticResult] = useOptimistic(null);

  const handleSubmit = () => {
    startTransition(async () => {
      setOptimisticResult({ status: "pending" }); // Instant UI feedback
      const result = await api.generate(...);
      // ...
    });
  };
}
```

---

## 2. App Development Order (권장 순서)

### Phase 1: Foundation (Core Pipeline) 🎯

기본 크리에이티브 워크플로우의 핵심 앱들

| 순서 | 앱 | Dimension | 역할 | 우선순위 이유 |
|------|-----|-----------|------|---------------|
| 1 | **Reference Decoder** | 4D | 레퍼런스 분석 | 입력 단계의 시작점 |
| 2 | **Story Architect** | Story | 내러티브 구조화 | 레퍼런스 → 스토리 변환 |
| 3 | **Prompt Generator** | 1D | 프롬프트 생성 | 핵심 텍스트 생성 엔진 |
| 4 | **Aesthetic Director** | AD | 비주얼 스타일 | 모든 시각 단계에 스타일 주입 |

**Flow**: `User Input → 4D → Story → 1D + AD`

### Phase 2: Visual Pipeline 🎨

Phase 1 출력에 의존하는 시각화 앱들

| 순서 | 앱 | Dimension | 역할 | 의존성 |
|------|-----|-----------|------|--------|
| 5 | **Storyboard** | 2D | 샷 계획 | 1D, Story 출력 필요 |
| 6 | **Visual Realizer** | 3D | 이미지 생성 | 2D 스토리보드 기반 |
| 7 | **VEO Video Maker** | VEO | 비디오 합성 | 3D, Sound 통합 |

**Flow**: `1D → 2D → 3D → VEO`

### Phase 3: Quality & Specialization ⚙️

병렬 개발 가능한 독립/보조 앱들

| 순서 | 앱 | Dimension | 역할 | 특성 |
|------|-----|-----------|------|------|
| 8 | **Quality Director** | QC | 품질 검증 | 모든 단계 삽입 가능 |
| 9 | **Sound Crafter** | Sound | 오디오 디자인 | VEO 병합 전용 |
| 10 | **Abyss Mirror** | AI | 페르소나 분석 | 독립 체험 앱 |

**Flow**: `QC ⟷ [Any Stage]`, `Sound → VEO`, `AI (Standalone)`

---

## 3. App Differentiation Matrix

### 3.1 기능별 분류

```
┌─────────────────────────────────────────────────────────────────┐
│                      INPUT STAGE                                │
│  ┌─────────┐                                                    │
│  │   4D    │  Reference Decoder (Analysis)                      │
│  │ always  │  레퍼런스 영상/이미지 분석                           │
│  └────┬────┘                                                    │
├───────┼─────────────────────────────────────────────────────────┤
│       │             PLANNING STAGE                              │
│       ▼                                                         │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐                   │
│  │  Story  │────▶│   1D    │────▶│   AD    │                   │
│  │ always  │     │auteur   │     │ always  │                   │
│  └────┬────┘     └────┬────┘     └────┬────┘                   │
│       │               │               │                         │
├───────┼───────────────┼───────────────┼─────────────────────────┤
│       │               │               │  VISUALIZATION STAGE    │
│       ▼               ▼               ▼                         │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐                   │
│  │   2D    │────▶│   3D    │────▶│   VEO   │                   │
│  │auteur   │     │auteur   │     │auteur   │                   │
│  └─────────┘     └─────────┘     └────┬────┘                   │
│                                       │                         │
├───────────────────────────────────────┼─────────────────────────┤
│                                       │   OUTPUT STAGE          │
│  ┌─────────┐     ┌─────────┐         ▼                         │
│  │  Sound  │────▶│  Final  │◀────────┘                         │
│  │ never   │     │ Output  │                                   │
│  └─────────┘     └─────────┘                                   │
├─────────────────────────────────────────────────────────────────┤
│                     UTILITY APPS                                │
│  ┌─────────┐     ┌─────────┐                                   │
│  │   QC    │     │   AI    │                                   │
│  │ always  │     │ never   │                                   │
│  │ (Gate)  │     │(Persona)│                                   │
│  └─────────┘     └─────────┘                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 상세 비교표

| App | Type | RAG Mode | Credits | Streaming | 주요 입력 | 주요 출력 |
|-----|------|----------|---------|-----------|-----------|-----------|
| **4D** | analysis | always | 8 | ❌ | 영상/이미지 URL | 분석 JSON |
| **Story** | generation | always | 10 | ✅ SSE | 컨셉/4D출력 | 시나리오 구조 |
| **1D** | generation | auteur_only | 5 | ✅ SSE | 스토리/주제 | 프롬프트 |
| **AD** | generation | always | 10 | ✅ SSE | 레퍼런스/키워드 | 비주얼 DNA |
| **2D** | generation | auteur_only | 10 | ✅ SSE | 1D 프롬프트 | 샷 리스트 |
| **3D** | generation | auteur_only | 5 | ✅ SSE | 2D 샷/프롬프트 | 이미지 |
| **VEO** | generation | auteur_only | 200 | ✅ SSE | 3D/2D 출력 | 비디오 |
| **QC** | analysis | always | 8 | ❌ | 모든 콘텐츠 | Pass/Fail |
| **Sound** | generation | never | 8 | ✅ SSE | 장르/무드 | 오디오 |
| **AI** | introspection | never | 5 | ✅ Chat | 개인정보 | 페르소나 |

### 3.3 RAG Mode 차별화

```python
# RAG Mode별 동작
"always"      # 4D, Story, AD, QC - 항상 거장 지식베이스 참조
"auteur_only" # 1D, 2D, 3D, VEO - auteur_key 선택 시에만
"never"       # Sound, AI - RAG 사용 안함
```

---

## 4. UI Harmony Analysis

### 4.1 Consistent Patterns ✅

모든 앱에서 일관되게 적용된 패턴:

| 패턴 | 구현체 | 상태 |
|------|--------|------|
| Compound Component | `DimensionPanel` + `useDimensionPanel` | ✅ 전체 적용 |
| Credit Modal | `InsufficientCreditsModal` | ✅ 전체 적용 |
| BYOK Integration | `useBYOK` + `getBYOKHeaders` | ✅ 전체 적용 |
| Config Context | `useDimensionConfig` | ✅ 전체 적용 |
| Input Schema | `dimension-input-schemas.ts` (SSoT) | ✅ 전체 적용 |
| Theme System | `dimension-theme.ts` | ✅ 전체 적용 |

### 4.2 Button/Action Terminology ✅

| 앱 타입 | 버튼 텍스트 | 아이콘 |
|---------|-------------|--------|
| Generation | "생성하기" / "Generate" | Sparkles |
| Analysis | "분석하기" / "Analyze" | Search |
| Quality | "평가하기" / "Evaluate" | Shield |
| Chat | "전송" / "Send" | Send |

→ **문맥에 맞는 차별화**: 일관성 문제 아님

### 4.3 Improvements Needed ⚠️

| 앱 | 현재 상태 | 필요 작업 |
|----|-----------|-----------|
| QualityDirectorPanel | Legacy React | useTransition, useOptimistic 추가 |
| AbyssMirrorPanel | Legacy React | React 19 패턴 마이그레이션 |

---

## 5. Workflow Coordination Patterns

### 5.1 Linear Chain (주 워크플로우)

```
4D ──▶ Story ──▶ 1D ──▶ 2D ──▶ 3D ──▶ Sound ──▶ VEO
 │        │        │       │       │               │
 │        │        │       │       │               │
 └────────┴────────┴───────┴───────┴───────────────┘
              DimensionChainContext로 데이터 전달
```

### 5.2 Style Injection (AD 스타일 주입)

```
       ┌─────────────────────────────────────────┐
       │           Aesthetic Director (AD)       │
       │         Visual Identity DNA 생성         │
       └───┬────────────┬────────────┬───────────┘
           │            │            │
           ▼            ▼            ▼
        ┌──────┐    ┌──────┐    ┌──────┐
        │  2D  │    │  3D  │    │ VEO  │
        └──────┘    └──────┘    └──────┘
```

### 5.3 Quality Gates (QC 삽입 지점)

```
Any Stage ──▶ QC ──▶ Pass? ──▶ Next Stage
                      │
                      ▼ Fail
                   Revise Current Stage
```

### 5.4 Context-Native Data Flow

```tsx
// DimensionChainContext 사용 예시
const { chainData, addToChain, getFromChain } = useDimensionChain();

// Story → 1D 데이터 전달
addToChain("story", { synopsis, characters, themes });
const storyData = getFromChain("story");
```

---

## 6. Development Roadmap

### Sprint 1: React 19 Unity (1주)

```
[ ] QualityDirectorPanel - useTransition 추가
[ ] QualityDirectorPanel - useOptimistic 추가
[ ] AbyssMirrorPanel - React 19 패턴 마이그레이션
[ ] 공유 MODEL_OPTIONS 상수 생성
```

### Sprint 2: Chain Integration Enhancement (2주)

```
[ ] ChainDataInput 컴포넌트 전체 앱 확산
[ ] Chain 데이터 시각화 개선
[ ] 자동 다음 단계 추천 기능
```

### Sprint 3: Quality Gates (2주)

```
[ ] QC 워크플로우 삽입 UI
[ ] Pass/Fail 후 자동 라우팅
[ ] QC 결과 기반 수정 제안
```

---

## 7. Code References

### 핵심 파일

| 파일 | 역할 |
|------|------|
| `frontend/src/components/dimension/panel/index.tsx` | DimensionPanel Compound Component |
| `frontend/src/lib/dimension-input-schemas.ts` | 입력 필드 SSoT |
| `frontend/src/lib/dimension-theme.ts` | 테마 시스템 |
| `frontend/src/contexts/DimensionChainContext.tsx` | 워크플로우 체인 |
| `config/apps/content/dimensions/*.yaml` | 앱 설정 |

### Panel 컴포넌트 (11개)

```
frontend/src/components/dimension/
├── PromptGeneratorPanel.tsx      # 1D ✅ React 19
├── StoryboardPanel.tsx           # 2D ✅ React 19
├── VisualRealizerPanel.tsx       # 3D ✅ React 19
├── ReferenceDecoderPanel.tsx     # 4D ✅ React 19
├── AestheticDirectorPanel.tsx    # AD ✅ React 19 (Golden)
├── StoryArchitectPanel.tsx       # Story ✅ React 19
├── QualityDirectorPanel.tsx      # QC ⚠️ Legacy
├── SoundCrafterPanel.tsx         # Sound ✅ React 19
├── VeoVideoPanel.tsx             # VEO ✅ React 19
├── AbyssMirrorPanel.tsx          # AI ⚠️ Legacy
└── CreativeEditorPanel.tsx       # (Utility)
```

---

## 8. Conclusion

### 현재 상태 평가

| 항목 | 점수 | 비고 |
|------|------|------|
| **UI 일관성** | 9/10 | DimensionPanel 통합 완료 |
| **워크플로우 협응** | 10/10 | ChainContext 완벽 구현 |
| **React 19 준수** | 8/10 | 2개 앱 마이그레이션 필요 |
| **2026 트렌드 적합** | 9/10 | AI-First, Context-Native 구현 |

### 최종 권장사항

1. **즉시 실행**: QC, AI 패널 React 19 마이그레이션
2. **단기**: 공유 MODEL_OPTIONS 상수화
3. **중기**: Chain 데이터 시각화 대시보드
4. **장기**: 자동 워크플로우 추천 시스템

---

*Generated with ultrathink analysis based on 2026 MCP research and web search*

*Last Updated: 2026-01-16*
