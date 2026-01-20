# Vivid Design System 종합 컨설팅 문서

> **대상**: 외부 UI/UX 디자인 전문가
> **작성일**: 2026-01-21
> **플랫폼**: Vivid (Crebit Studio) - AI 콘텐츠 생성 플랫폼
> **접근 권한**: 코드베이스 전체 접근 가능

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [디자인 토큰 시스템](#2-디자인-토큰-시스템)
3. [주요 페이지별 분석](#3-주요-페이지별-분석)
4. [UI 컴포넌트 패턴](#4-ui-컴포넌트-패턴)
5. [일관성 문제점](#5-일관성-문제점)
6. [개선 제안](#6-개선-제안)
7. [코드 참조 맵](#7-코드-참조-맵)

---

## 1. 프로젝트 개요

### 1.1 제품 설명

**Vivid**는 IP(지적재산) 기반 AI 콘텐츠 생성 플랫폼입니다.

- **주요 사용자**: 콘텐츠 크리에이터, 팬 아트 제작자
- **핵심 기능**: IP 탐색 → 워크플로우 선택 → AI 콘텐츠 생성
- **기술 스택**: Next.js 16, React 19, TypeScript, Tailwind CSS

### 1.2 핵심 사용자 흐름

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MAIN USER JOURNEY                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. IP 갤러리      2. IP 상세        3. 워크플로우       4. Dimension 앱    │
│  (/ip)          →  (/ip/[slug])   →  (모달/선택)     →  (/dimension/*)     │
│                                                                              │
│  ┌──────────┐     ┌──────────┐      ┌──────────┐       ┌──────────┐        │
│  │ Rail     │     │ 비디오   │      │ Reference│       │ AI 분석  │        │
│  │ 카드들   │  →  │ 상세정보 │  →   │ Decoder  │   →   │ 결과     │        │
│  │          │     │ 워크플로우│      │ Abyss    │       │ 생성     │        │
│  └──────────┘     └──────────┘      │ Mirror   │       └──────────┘        │
│                                      └──────────┘                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 페이지 구조

| 페이지 | 경로 | 용도 | 복잡도 |
|--------|------|------|--------|
| IP 갤러리 | `/ip` | IP 탐색/검색 | 중간 |
| IP 상세 | `/ip/[slug]` | IP 정보 + 워크플로우 시작 | **높음** |
| Dimension Hub | `/dimension` | 도구 목록 | 낮음 |
| Dimension 앱 (15개) | `/dimension/*` | AI 도구 실행 | 중간~높음 |

---

## 2. 디자인 토큰 시스템

### 2.1 토큰 구조 (DTCG 2025.10 기반)

```
frontend/src/styles/tokens/
├── index.css           # 진입점 (import order)
├── tokens.base.css     # Level 1: Raw primitives
├── tokens.semantic.css # Level 2: Semantic aliases
├── tokens.demo.css     # Level 3: Component tokens (데모용)
└── tokens.motion.css   # Level 4: Animation tokens
```

### 2.2 Base Tokens (Level 1)

**파일**: `tokens.base.css`

#### 중립 색상 (Neutral Scale)

```css
--neutral-0: oklch(100% 0 0);       /* 순백 */
--neutral-50: oklch(98% 0.002 280);
--neutral-100: oklch(96% 0.004 280);
...
--neutral-950: oklch(10% 0.004 280);
--neutral-1000: oklch(5% 0.002 280); /* 순흑 */
```

#### 브랜드 색상

```css
/* Primary: Violet */
--violet-500: oklch(62% 0.20 280);  /* 메인 브랜드 */

/* Secondary: Cyan */
--cyan-500: oklch(62% 0.18 200);
```

#### Dimension 앱 색상 (10개)

| Dimension | 변수 | OKLCH | 용도 |
|-----------|------|-------|------|
| Mirror | `--dim-mirror` | `oklch(50% 0.20 290)` | Abyss Mirror |
| Decoder | `--dim-decoder` | `oklch(55% 0.14 180)` | Reference Decoder |
| Scenario | `--dim-scenario` | `oklch(72% 0.16 85)` | Story Architect |
| Sound | `--dim-sound` | `oklch(65% 0.18 25)` | Sound Crafter |
| Storyboard | `--dim-storyboard` | `oklch(52% 0.18 260)` | Storyboard |
| Prompt | `--dim-prompt` | `oklch(58% 0.22 320)` | Prompt Alchemy |
| Visual | `--dim-visual` | `oklch(60% 0.16 155)` | Visual Realizer |
| VEO | `--dim-veo` | `oklch(52% 0.18 210)` | Video Maker |
| Quality | `--dim-quality` | `oklch(55% 0.20 15)` | Quality Director |
| Aesthetic | `--dim-aesthetic` | `oklch(62% 0.18 350)` | Aesthetic Director |

### 2.3 Semantic Tokens (Level 2)

**파일**: `tokens.semantic.css`

```css
/* 배경 */
--bg-base: var(--neutral-0);        /* 기본 배경 */
--bg-subtle: var(--neutral-50);     /* 미묘한 배경 */
--bg-primary: var(--violet-500);    /* 브랜드 배경 */

/* 텍스트 */
--fg-default: var(--neutral-900);   /* 기본 텍스트 */
--fg-muted: var(--neutral-600);     /* 보조 텍스트 */
--fg-on-primary: var(--neutral-0);  /* 브랜드 배경 위 텍스트 */

/* 테두리 */
--border-default: var(--neutral-200);
--border-focus: var(--violet-500);

/* Glass Morphism */
--glass-bg: oklch(100% 0 0 / 0.7);
--glass-border: oklch(0% 0 0 / 0.1);
--glass-shadow: 0 8px 32px oklch(0% 0 0 / 0.1);
```

### 2.4 다크 모드

```css
.dark {
  --bg-base: var(--neutral-950);
  --fg-default: var(--neutral-100);
  --glass-bg: oklch(15% 0.006 280 / 0.7);
}
```

### 2.5 토큰 적용 현황

| 영역 | 적용률 | 비고 |
|------|--------|------|
| IP 갤러리 | 80% | 일부 하드코딩 색상 존재 |
| IP 상세 | 60% | Tailwind 직접 사용 다수 |
| Dimension 앱 | 40% | 패널별 스타일 불일치 |
| 공통 UI | 70% | 버튼, 카드 등 |

---

## 3. 주요 페이지별 분석

### 3.1 IP 갤러리 (`/ip`)

**파일**: `frontend/src/app/ip/_components/IPCatalogClient.tsx`

#### 현재 구조

```
┌─────────────────────────────────────────────────────────────────┐
│ HEADER: 제목 + 설명 + 뷰 토글(Rail/Grid)                        │
├─────────────────────────────────────────────────────────────────┤
│ FILTERS: 검색 + 장르 드롭다운 + 정렬 드롭다운                   │
├─────────────────────────────────────────────────────────────────┤
│ CONTENT:                                                         │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Rail 뷰: 섹션별 가로 스크롤 카드                            │ │
│ │ - Featured IPs                                               │ │
│ │ - 로맨스                                                     │ │
│ │ - 액션                                                       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ 또는                                                             │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Grid 뷰: 5열 그리드                                         │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### 문제점

1. **Rail/Grid 토글 모호함**: 왜 두 가지 뷰가 필요한지 불명확
2. **필터 위치**: 헤더에 밀집, 모바일에서 문제
3. **빈 상태 처리**: 검색 결과 없을 때 UX 개선 필요

#### 코드 참조

- `IPCatalogClient.tsx:177-396` - 전체 컴포넌트
- `IPCatalogClient.tsx:214-265` - 필터 섹션
- `IPCatalogClient.tsx:271-319` - Rail 뷰

---

### 3.2 IP 상세 (`/ip/[slug]`) ⚠️ 주요 문제

**파일**: `frontend/src/app/ip/[slug]/_components/IPDetailClient.tsx`

#### 현재 구조 (1,457 라인)

```
┌─────────────────────────────────────────────┬───────────────────────────────┐
│ LEFT (flex-1)                               │ RIGHT (420px fixed)           │
├─────────────────────────────────────────────┼───────────────────────────────┤
│ [비디오 플레이어 - 9:16 또는 16:9]          │ [AI 콘텐츠 생성 헤더]         │
│ + 뮤트 버튼                                  │ + 설명 텍스트                 │
│ + 오버레이 배지들                            │                               │
│                                             │ [프리셋 선택]                 │
│ [IP 정보 헤더]                              │ - 프리셋 1 (선택됨)           │
│ [썸네일][제목, 장르 태그, 통계]             │ - 프리셋 2                    │
│                                             │ - 프리셋 3                    │
│ [설명 텍스트]                               │                               │
│                                             │ [추천 도구 섹션] ⚠️            │
│ [이 IP로 만들 수 있는 것]                   │ - 토글 버튼 3개               │
│ - 워크플로우 카드 그리드                    │ - 배지 5개                    │
│   또는 스텝퍼 형식                          │ - Evidence Card               │
│                                             │ - 대안 추천 2개               │
│ [세계관 섹션] ⚠️                            │ - 피드백 버튼 2개             │
│ - 로그라인                                  │                               │
│ - 배경 설정                                 │ [프롬프트 입력]               │
│ - 콘텐츠 정보                               │                               │
│ - 테마 태그들                               │ [예상 크레딧/시간]            │
│ - 캐릭터 카드들 (각 6개 필드)               │                               │
│                                             │ [생성하기 CTA]                │
└─────────────────────────────────────────────┴───────────────────────────────┘
```

#### 문제점 상세

##### A. 정보 과부하

| 섹션 | 요소 수 | 심각도 |
|------|---------|--------|
| 워크플로우 카드 | 2~6개 × 4요소 | 🟡 중간 |
| 세계관 | 로그라인+배경+테마(4~6)+캐릭터(2~4×6) | 🔴 높음 |
| 추천 도구 | 토글3+배지5+카드3+피드백2 = 13+ 요소 | 🔴 높음 |

##### B. CTA 경쟁

```
사용자 혼란 포인트:
├── "워크플로우 카드 클릭해야 하나?"
├── "프리셋 선택하고 생성하기 눌러야 하나?"
└── "추천 도구 카드 클릭하면 어떻게 되나?"
```

##### C. 스크롤 깊이

- 모바일에서 세계관 섹션까지 5+ 스크롤
- CTA 버튼이 스크롤 밖에 위치할 수 있음

#### 코드 참조

| 영역 | 라인 |
|------|------|
| 비디오 플레이어 | `486-624` |
| IP 정보 헤더 | `627-670` |
| 워크플로우 카드 | `680-889` |
| 세계관 섹션 | `892-1036` |
| 사이드바 전체 | `1040-1400` |
| 추천 도구 | `1114-1334` |

---

### 3.3 Dimension 앱 페이지 (`/dimension/*`)

**패턴**: 각 앱은 `*Panel.tsx` 컴포넌트를 사용

#### 공통 구조

```
┌─────────────────────────────────────────────────────────────────┐
│ DimensionPanel (Compound Component)                             │
├─────────────────────────────────────────────────────────────────┤
│ ┌───────────────────┐ ┌───────────────────────────────────────┐ │
│ │ DimensionPanel    │ │ DimensionPanel.Content                │ │
│ │ .Sidebar          │ │                                       │ │
│ │                   │ │ - Loading State                       │ │
│ │ - 입력 폼        │ │ - Error State                         │ │
│ │ - 옵션 선택      │ │ - Result Display                      │ │
│ │ - 실행 버튼      │ │                                       │ │
│ │                   │ │                                       │ │
│ └───────────────────┘ └───────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### 패널 목록 (15개)

| 패널 | 파일 | 복잡도 |
|------|------|--------|
| AbyssMirrorPanel | `AbyssMirrorPanel.tsx` | 높음 |
| ReferenceDecoderPanel | `ReferenceDecoderPanel.tsx` | 중간 |
| StoryArchitectPanel | `StoryArchitectPanel.tsx` | 중간 |
| SoundCrafterPanel | `SoundCrafterPanel.tsx` | 중간 |
| StoryboardPanel | `StoryboardPanel.tsx` | 높음 |
| PromptAlchemyPanel | `PromptAlchemyPanel.tsx` | 낮음 |
| VisualRealizerPanel | `VisualRealizerPanel.tsx` | 중간 |
| VeoVideoPanel | `VeoVideoPanel.tsx` | 높음 |
| QualityDirectorPanel | `QualityDirectorPanel.tsx` | 중간 |
| AestheticDirectorPanel | `AestheticDirectorPanel.tsx` | 중간 |
| PromptGeneratorPanel | `PromptGeneratorPanel.tsx` | 낮음 |
| CharacterConsistencyPanel | `CharacterConsistencyPanel.tsx` | 중간 |
| KlingPanel | `KlingPanel.tsx` | 중간 |
| SunoPanel | `SunoPanel.tsx` | 중간 |
| CreativeEditorPanel | `CreativeEditorPanel.tsx` | 높음 |

#### 문제점

1. **스타일 불일치**: 패널마다 다른 스타일링 접근
2. **토큰 미적용**: 일부 패널은 하드코딩된 색상 사용
3. **반응형 미흡**: 사이드바 폭 고정 (데스크톱 최적화)

---

## 4. UI 컴포넌트 패턴

### 4.1 공통 컴포넌트

**경로**: `frontend/src/components/`

| 컴포넌트 | 용도 | 토큰 적용 |
|----------|------|-----------|
| `AppShell.tsx` | 글로벌 레이아웃 | ✅ |
| `ip/IPCard.tsx` | IP 썸네일 카드 | ✅ |
| `ip/IPRailCard.tsx` | Rail용 IP 카드 | ✅ |
| `ui/EvidenceCard.tsx` | 추천 신뢰도 표시 | ⚠️ 부분 |
| `WorkflowPreviewModal.tsx` | 워크플로우 모달 | ✅ |
| `WorkflowStepNav.tsx` | 워크플로우 네비게이션 | ✅ |

### 4.2 DimensionPanel Compound Component

**경로**: `frontend/src/components/dimension/panel/`

```tsx
// 사용 예시
<DimensionPanel>
  <DimensionPanel.Sidebar>
    <DimensionPanel.Form>
      {/* 입력 폼 */}
    </DimensionPanel.Form>
    <DimensionPanel.Actions>
      <DimensionPanel.SubmitButton>실행</DimensionPanel.SubmitButton>
    </DimensionPanel.Actions>
  </DimensionPanel.Sidebar>
  <DimensionPanel.Content>
    <DimensionPanel.LoadingState />
    <DimensionPanel.ErrorState />
    <DimensionPanel.Result>
      {/* 결과 표시 */}
    </DimensionPanel.Result>
  </DimensionPanel.Content>
</DimensionPanel>
```

---

## 5. 일관성 문제점

### 5.1 스타일링 혼재

```
현재 상태:
├── Tailwind 직접 사용 (예: "bg-violet-500")
├── CSS Variables (예: "bg-[var(--bg-primary)]")
├── 하드코딩 (예: "#8b5cf6")
└── oklch 직접 사용 (예: "oklch(62% 0.20 280)")
```

**권장**: 모든 색상을 semantic token으로 통일

### 5.2 컴포넌트 스타일 불일치

| 컴포넌트 | 문제 |
|----------|------|
| 버튼 | 각 페이지마다 다른 radius, padding |
| 카드 | shadow 깊이 불일치 |
| 입력 필드 | focus ring 색상 다름 |
| 모달 | backdrop 투명도 다름 |

### 5.3 반응형 전략 부재

- 모바일 브레이크포인트 일관성 없음
- 일부 페이지는 2-column 고정 (IP 상세)
- 다른 페이지는 적응형 (Dimension)

### 5.4 다크 모드 불완전

- 일부 하드코딩 색상은 다크 모드에서 미변환
- 이미지/비디오 오버레이 대비 문제

---

## 6. 개선 제안

### 6.1 단기 개선 (Quick Wins)

| 우선순위 | 작업 | 예상 효과 |
|----------|------|-----------|
| P0 | IP 상세 세계관 섹션 접힘 처리 | 정보 과부하 해소 |
| P0 | 추천 도구 섹션 기본 숨김 | 사이드바 단순화 |
| P1 | 워크플로우 카드 → 히어로 CTA 승격 | CTA 명확화 |
| P1 | 하드코딩 색상 → 토큰 변환 | 일관성 |
| P2 | 모바일 최적화 | 접근성 |

### 6.2 중장기 리디자인

#### Option A: 탭 기반 정보 분리

```
[개요] [세계관] [캐릭터] [생성]
```

#### Option B: 워크플로우 중심 단순화

```
비디오 + 핵심 정보 (3줄)
↓
[🎬 레퍼런스 분석으로 시작] ← 주요 CTA
↓
세계관 더보기 (접힘) ▼
```

#### Option C: 피그마 참조 디자인

> 디자이너가 직접 피그마에서 redesign 후 반영

### 6.3 디자인 시스템 강화

1. **Component Library 문서화** (Storybook)
2. **토큰 → Figma Sync** 자동화
3. **접근성 체크리스트** (WCAG 2.2 AA)

---

## 7. 코드 참조 맵

### 7.1 핵심 파일 경로

```
frontend/src/
├── styles/tokens/              # 디자인 토큰 시스템
│   ├── tokens.base.css         # 원시 값 (색상, 스페이싱, 타이포)
│   ├── tokens.semantic.css     # 시맨틱 별칭 (라이트/다크)
│   ├── tokens.demo.css         # 데모용 컴포넌트 토큰
│   └── tokens.motion.css       # 애니메이션 토큰
│
├── app/
│   ├── ip/
│   │   ├── page.tsx                          # IP 갤러리 진입
│   │   ├── _components/IPCatalogClient.tsx   # 갤러리 메인 (399줄)
│   │   └── [slug]/
│   │       └── _components/
│   │           └── IPDetailClient.tsx        # IP 상세 (1,457줄) ⚠️
│   │
│   └── dimension/
│       ├── page.tsx                          # Dimension Hub
│       ├── layout.tsx                        # 공통 레이아웃
│       ├── abyss/page.tsx                    # Abyss Mirror
│       ├── reference-decoder/page.tsx        # Reference Decoder
│       └── ...                               # 13개 더
│
├── components/
│   ├── AppShell.tsx                          # 글로벌 레이아웃
│   ├── ip/
│   │   ├── IPCard.tsx                        # IP 카드
│   │   └── IPRailCard.tsx                    # Rail용 카드
│   ├── dimension/
│   │   ├── panel/                            # Compound Component
│   │   │   ├── DimensionPanelContext.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Content.tsx
│   │   │   └── ...
│   │   ├── AbyssMirrorPanel.tsx
│   │   ├── ReferenceDecoderPanel.tsx
│   │   └── ...                               # 13개 패널
│   └── ui/
│       ├── EvidenceCard.tsx
│       └── ToolRecommendationCard.tsx
│
└── lib/
    ├── demo-ip-overrides.ts                  # 데모 IP 데이터
    └── workflow-state.ts                     # 워크플로우 상태 관리
```

### 7.2 토큰 적용 예시

**권장 사용법:**

```tsx
// ✅ 좋은 예: Semantic token 사용
<div className="bg-[var(--bg-base)] text-[var(--fg-default)]">
  <button className="bg-[var(--bg-primary)] text-[var(--fg-on-primary)]">
    CTA
  </button>
</div>

// ⚠️ 피해야 할 예: Tailwind 직접 또는 하드코딩
<div className="bg-white text-slate-900">
  <button className="bg-violet-500 text-white">
    CTA
  </button>
</div>
```

### 7.3 브라우저 확인 URL

| 페이지 | URL |
|--------|-----|
| IP 갤러리 | http://localhost:3100/ip |
| IP 상세 (데모) | http://localhost:3100/ip/umbrella-encounter |
| IP 상세 (가로) | http://localhost:3100/ip/cooking-anime-mv |
| Dimension Hub | http://localhost:3100/dimension |
| Reference Decoder | http://localhost:3100/dimension/reference-decoder |
| Abyss Mirror | http://localhost:3100/dimension/abyss |

---

## 부록: 추가 자료

### A. 데모 IP 데이터 구조

**파일**: `frontend/src/lib/demo-ip-overrides.ts`

```typescript
interface DemoIPOverride {
  contentType: "vertical-shortform" | "horizontal-anime-mv" | "default";
  detailVideoUrl?: string;
  thumbnailUrl?: string;
  workflows: DemoWorkflow[];
}

interface DemoWorkflow {
  id: string;           // "reference-decoder"
  title: string;        // "Reference Analysis"
  titleKo: string;      // "레퍼런스 분석"
  description: string;
  icon: string;         // "BookOpen" (Lucide icon)
  href: string;         // "/dimension/reference-decoder"
  badge?: string;       // "AI"
  stepNumber?: number;  // 1, 2, 3...
}
```

### B. 접근성 고려사항

- `prefers-contrast: more` 지원 (tokens.semantic.css:276)
- `aria-label` 사용 (비디오 뮤트 버튼 등)
- 키보드 네비게이션 (일부 미지원)

### C. 성능 고려사항

- ISR (Incremental Static Regeneration) 적용
- 비디오 자동재생 + preload 설정
- 이미지 lazy loading

---

**문서 끝**

> 질문 또는 추가 자료 요청: [담당자 이메일]
