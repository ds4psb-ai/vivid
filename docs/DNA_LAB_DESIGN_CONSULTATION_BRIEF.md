# DNA Lab Design Consultation Brief

> **Purpose**: Silicon Valley 디자이너가 https://www.prompty.co.kr/dna-lab?master=velvet&mode=quick 페이지를 혁신적으로 심플하고 미니멀리스틱하게 재디자인할 수 있도록 작성된 상세 브리프
>
> **Target**: 코드 접근 불가, 웹사이트 토큰 확인 가능, HTML/CSS 산출물 제작 예정

---

## Executive Summary

**Crebit Studio**는 크리에이티브 AI 콘텐츠 생성 플랫폼입니다. **DNA Lab**은 이 플랫폼의 핵심 "메가앱"으로, 영상 분석 → 미학 적용 → 페르소나 추출 → 품질 검증의 4단계 워크플로우를 3단계로 통합한 전문가용 도구입니다.

**현재 문제점**:
- 기능이 많아 시각적으로 복잡함
- 온보딩 → 개요 → 상세의 3-depth 네비게이션이 혼란스러움
- Quick Start 모드임에도 불구하고 선택지가 많음

**목표**:
- 기능 100% 유지하면서 시각적 복잡도 70% 감소
- "One glance, full understanding" 달성
- Apple/Linear 수준의 미니멀리즘

---

## 1. Brand Identity & Philosophy

### 1.1 Core Brand Colors

| Token | Value | Usage |
|-------|-------|-------|
| **Primary (Neon Red)** | `oklch(0.62 0.28 20)` → `#FF003C` | CTA 버튼, 강조 |
| **DNA Lab Accent** | `oklch(0.64 0.18 148)` → Cyan-Green | DNA Lab 전용 테마 |
| **Background Dark** | `oklch(0.15 0.006 280)` → `#1a1a1a` | 다크모드 배경 |
| **Surface** | `rgba(0, 0, 0, 0.4)` | 글래스모피즘 카드 |
| **Border** | `rgba(255, 255, 255, 0.1)` | 서브틀 보더 |

### 1.2 Typography

```css
/* Font Stack */
--font-sans: "Pretendard", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
--font-display: "Space Grotesk", var(--font-sans);
--font-mono: "JetBrains Mono", ui-monospace, monospace;

/* Scale */
--text-xs: 0.75rem;    /* 12px - Labels */
--text-sm: 0.875rem;   /* 14px - Body small */
--text-base: 1rem;     /* 16px - Body */
--text-lg: 1.125rem;   /* 18px - Subhead */
--text-xl: 1.25rem;    /* 20px - Card title */
--text-2xl: 1.5rem;    /* 24px - Section title */
--text-3xl: 1.875rem;  /* 30px - Page title */
```

### 1.3 Design Philosophy (Crebit 원칙)

| 원칙 | UI 구현 방식 |
|------|------------|
| **Evidence-First** | 모든 결과물에 출처 배지 표시 |
| **Sealed Capsule** | 내부 프로세스 숨김, 입력/출력만 노출 |
| **Credit Transparency** | 각 액션 비용 우측 상단 표시 |
| **Non-Blocking** | 경고(amber)는 차단(red)이 아님 |

---

## 2. DNA Lab Current Structure

### 2.1 Page Flow (현재 3-depth)

```
URL: /dna-lab?master=velvet&mode=quick

┌─────────────────────────────────────────────────────┐
│  DEPTH 1: Onboarding (현재 스킵됨 - quick mode)     │
│  ├── Option 1: 기존 IP 선택                         │
│  ├── Option 2: 영상 URL 입력                        │
│  ├── Option 3: 빠른 시작 (Master 선택) ← 현재 경로  │
│  └── Option 4: 수동 시작                            │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  DEPTH 2: Overview (2x2 그리드)                     │
│  ┌─────────────┐  ┌─────────────┐                   │
│  │  영상분석   │  │  미학적용   │                   │
│  │  (Step 1)   │  │  (Step 1)   │   ← 통합됨       │
│  └─────────────┘  └─────────────┘                   │
│  ┌─────────────┐  ┌─────────────┐                   │
│  │  창작DNA    │  │  품질검증   │                   │
│  │  (Step 2)   │  │  (Step 3)   │                   │
│  └─────────────┘  └─────────────┘                   │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  DEPTH 3: Step Detail (패널)                        │
│  ┌──────────────────────────────────────────┐      │
│  │  [Sidebar Controls]  │  [Result Area]    │      │
│  │  - Input fields      │  - Generated      │      │
│  │  - Options           │    content        │      │
│  │  - Generate btn      │  - Evidence       │      │
│  └──────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────┘
```

### 2.2 현재 URL 파라미터

| Parameter | Value | Description |
|-----------|-------|-------------|
| `master` | `velvet` | 선택된 거장 (Auteur) |
| `mode` | `quick` | 빠른 시작 모드 |
| `step` | (optional) | `analysis`, `mirror`, `qc` |
| `ip` | (optional) | IP slug for chain data |

### 2.3 3-Step Workflow

| Step | ID | Korean | Purpose | Input | Output |
|------|-----|--------|---------|-------|--------|
| 1 | `analysis` | 통합분석 | VPE + AD 통합 | Video URL, Master | Logic Vector, Aesthetic Guidelines |
| 2 | `mirror` | 창작DNA | Abyss Mirror | Analysis output | Persona DNA, Genome |
| 3 | `qc` | 품질검증 | Quality Director | All previous | Quality Report, Pass/Fail |

---

## 3. Current UI Components

### 3.1 Header Section

```
┌─────────────────────────────────────────────────────┐
│  [DNA Icon]  DNA Lab                                │
│              통합 워크플로우                          │
│                                   [IP Badge] [Run]  │
└─────────────────────────────────────────────────────┘
```

- **DNA Icon**: Lucide `Dna` icon
- **Title**: "DNA Lab" (Space Grotesk, 30px, bold)
- **Subtitle**: "통합 워크플로우" (14px, muted)
- **IP Badge**: 선택된 IP 표시 (있을 경우)
- **Run Button**: "전체 파이프라인 실행" (Primary CTA)

### 3.2 Progress Stepper

```
┌─────────────────────────────────────────────────────┐
│  [●] 통합분석 ────── [○] 창작DNA ────── [○] 품질검증 │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│  33% 완료                                           │
└─────────────────────────────────────────────────────┘
```

- 3단계 수평 스테퍼
- 각 단계 클릭 시 해당 Step Detail로 이동
- 완료 퍼센티지 프로그레스 바
- 비순차적 접근 가능 (클릭으로 점프)

### 3.3 Step Card (Overview Mode)

```
┌─────────────────────────────────────────────────────┐
│  [Video Icon]                                       │
│                                                     │
│  영상분석                                            │
│  Logic Vector 추출                                   │
│                                                     │
│  ─────────────────────────────────────────────────  │
│  [시작하기 →]                                        │
└─────────────────────────────────────────────────────┘
```

- Glass morphism card: `bg-black/40 backdrop-blur-xl`
- Border: `border border-white/10 rounded-2xl`
- Hover: `hover:border-white/20 hover:scale-[1.02]`
- Icon: Step-specific (Video, Palette, Brain, CheckCircle)

### 3.4 Step Detail Panel

**Sidebar (Controls)**:
```
┌─────────────────────────┐
│  MASTER AUTEUR          │
│  [Velvet ▼]             │
│                         │
│  VIDEO URL              │
│  [_________________]    │
│                         │
│  ANALYSIS MODE          │
│  [● Standard] [○ Deep]  │
│                         │
│  ─────────────────────  │
│  [Advanced Options ▼]   │
│  ─────────────────────  │
│                         │
│  [Generate] (50 credits)│
└─────────────────────────┘
```

**Content Area (Results)**:
```
┌─────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────┐  │
│  │  [Result Card]                               │  │
│  │  Logic Vector 추출 완료                       │  │
│  │  ────────────────────────────────────────── │  │
│  │  { camera_grammar: {...}, rhythm: {...} }   │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  [Evidence Card]                             │  │
│  │  📚 출처: NotebookLM, Qdrant                  │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  [← Previous]                      [Next Step →]   │
└─────────────────────────────────────────────────────┘
```

---

## 4. Design Token System (웹사이트에서 확인 가능)

### 4.1 CSS Custom Properties

디자이너가 DevTools에서 확인할 수 있는 주요 토큰:

```css
:root {
  /* Colors */
  --bg-0: #0a0a0a;
  --bg-1: #141414;
  --bg-2: #1f1f1f;
  --fg-0: #e8e8ed;
  --fg-muted: #71717a;

  /* DNA Lab specific */
  --color-mega-app-dna-lab: oklch(0.64 0.18 148);

  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;

  /* Radius */
  --radius-lg: 0.75rem;
  --radius-xl: 1rem;
  --radius-2xl: 1.5rem;

  /* Shadows */
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1);

  /* Glass */
  --glass-bg: rgba(0, 0, 0, 0.4);
  --glass-border: rgba(255, 255, 255, 0.1);
  --glass-blur: blur(24px);
}
```

### 4.2 Tailwind Classes (실제 사용 중)

```css
/* Card Glass */
.card-glass {
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1.5rem;
}

/* Glow Effect */
.glow-cyan {
  box-shadow: 0 0 30px oklch(0.64 0.18 148 / 0.4);
}

/* Progress Bar */
.progress-bar {
  background: linear-gradient(90deg,
    oklch(0.64 0.18 148),
    oklch(0.70 0.15 148)
  );
}
```

---

## 5. Homepage Design Consistency

### 5.1 메인 페이지 레이아웃 (정합성 필요)

메인 페이지(`/`)는 다음 구조를 가집니다:

```
┌─────────────────────────────────────────────────────┐
│  [Glass Navbar - Fixed]                             │
│  Logo | Nav Links | Theme Toggle | Login           │
├─────────────────────────────────────────────────────┤
│  [Cinematic Hero - Full Screen]                     │
│  Featured IP with Character Card                    │
│  CTA: "Start Creative Journey"                      │
├─────────────────────────────────────────────────────┤
│  [Horizontal Rails]                                 │
│  - User Cinema (Recent videos)                      │
│  - Mega Apps Grid (13+ apps)                        │
│  - Variations Bento Grid                            │
│  - Featured Characters                              │
├─────────────────────────────────────────────────────┤
│  [CTA Sections with Animated Borders]               │
│  - AI Director                                      │
│  - Human Cloud                                      │
├─────────────────────────────────────────────────────┤
│  [Dark Footer]                                      │
└─────────────────────────────────────────────────────┘
```

### 5.2 DNA Lab과 메인 페이지 정합성 포인트

| 요소 | 메인 페이지 | DNA Lab (현재) | 정합성 방향 |
|------|------------|---------------|------------|
| **배경** | Aurora gradient orbs | Solid dark | Aurora 적용 필요 |
| **카드** | Glass morphism + hover glow | Glass 있음 | OK |
| **CTA 버튼** | Neon Red gradient | Cyan gradient | 통일 필요 |
| **타이포** | Space Grotesk + Inter | 혼합 | Space Grotesk 강조 |
| **스테퍼** | 없음 | 복잡한 3단계 | 단순화 필요 |

---

## 6. Functional Requirements (유지 필수)

### 6.1 Core Features (절대 삭제 불가)

1. **Master (Auteur) Selection**: 거장 스타일 선택
2. **3-Step Workflow**: Analysis → Mirror → QC
3. **Chain Data Flow**: 이전 단계 출력 → 다음 단계 입력
4. **Evidence Display**: 출처 표시 (Evidence-First 원칙)
5. **Credit Cost Display**: 각 액션 비용 표시
6. **Non-Sequential Access**: 순서 무관 단계 접근

### 6.2 Quick Mode Specific (master=velvet&mode=quick)

- **자동 Master 선택**: URL의 `master=velvet`으로 자동 설정
- **온보딩 스킵**: 바로 Overview 또는 Step 1으로 진입
- **간소화된 옵션**: Advanced Options 기본 숨김

### 6.3 Interaction Patterns (유지 필수)

| Pattern | Description |
|---------|-------------|
| **Click to Navigate** | Step card 클릭 → Step Detail 이동 |
| **Progress Indication** | 완료된 단계 시각적 표시 |
| **Warning Banner** | 이전 단계 미완료 시 amber 경고 (blocking 아님) |
| **Auto-Save** | 1초 debounce로 세션 자동 저장 |
| **Pipeline Run** | 전체 단계 순차 실행 버튼 |

---

## 7. Design Direction (제안)

### 7.1 Minimalist Principles

**Apple/Linear 스타일 적용**:
- **White Space**: 현재 대비 2배 여백
- **Single Focus**: 한 번에 하나의 액션만 강조
- **Progressive Disclosure**: 고급 옵션은 숨김
- **Quiet Interface**: 불필요한 장식 제거

### 7.2 Proposed Layout Simplification

**현재 (복잡)**:
```
Header → Progress Stepper → 2x2 Grid → Step Panel
```

**제안 (단순화)**:
```
┌─────────────────────────────────────────────────────┐
│  DNA Lab                                [Run All]   │
│  ────────────────────────────────────────────────── │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │                                             │   │
│  │     [1] ───────── [2] ───────── [3]        │   │
│  │    분석           DNA           검증        │   │
│  │     ●             ○             ○          │   │
│  │                                             │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  Current Step: 통합분석                      │   │
│  │  ──────────────────────────────────────────  │   │
│  │                                             │   │
│  │  Master: Velvet                             │   │
│  │  [Video URL input________________]          │   │
│  │                                             │   │
│  │  [Generate]  50 credits                     │   │
│  │                                             │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 7.3 Visual Hierarchy (제안)

```
Level 1: Page Title "DNA Lab" (30px, bold)
Level 2: Current Step Name (24px, semibold)
Level 3: Section Labels (12px, uppercase, muted)
Level 4: Input Labels (14px, medium)
Level 5: Helper Text (12px, muted)
```

### 7.4 Color Usage (제안)

| Element | Color | Token |
|---------|-------|-------|
| **Background** | Near black | `--bg-0` |
| **Card Surface** | Glass black/40 | `--glass-bg` |
| **Primary CTA** | Neon Red | `#FF003C` |
| **Step Accent** | DNA Lab Cyan | `oklch(0.64 0.18 148)` |
| **Completed Step** | Emerald | `--state-success` |
| **Current Step** | Cyan glow | `--color-mega-app-dna-lab` |
| **Pending Step** | Muted gray | `--fg-muted` |

---

## 8. Component Specifications

### 8.1 Simplified Progress Indicator

```css
/* Minimal 3-dot stepper */
.step-indicator {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.step-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--fg-muted);
  transition: all 0.3s ease;
}

.step-dot.active {
  background: var(--color-mega-app-dna-lab);
  box-shadow: 0 0 20px var(--color-mega-app-dna-lab);
}

.step-dot.completed {
  background: var(--state-success);
}

.step-connector {
  flex: 1;
  height: 1px;
  background: var(--glass-border);
}
```

### 8.2 Minimal Card

```css
.minimal-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 1rem;
  padding: 2rem;
  transition: all 0.2s ease;
}

.minimal-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.1);
}
```

### 8.3 Primary Button

```css
.btn-primary {
  background: linear-gradient(135deg, #FF003C, #CC0030);
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 30px rgba(255, 0, 60, 0.3);
}
```

---

## 9. Responsive Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | < 640px | Single column, stacked cards |
| Tablet | 640-1024px | 2-column, reduced padding |
| Desktop | 1024px+ | Full layout, sidebar visible |

### 9.1 Mobile Considerations

- Progress stepper: Vertical orientation
- Cards: Full width, stacked
- Sidebar controls: Drawer from bottom
- Touch targets: Minimum 44x44px

---

## 10. Animation & Motion

### 10.1 Transitions

```css
/* Default transition */
--transition-default: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

/* Hover scale */
--transition-scale: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);

/* Glow pulse */
@keyframes glow-pulse {
  0%, 100% { box-shadow: 0 0 20px var(--color-mega-app-dna-lab); }
  50% { box-shadow: 0 0 30px var(--color-mega-app-dna-lab); }
}
```

### 10.2 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 11. Accessibility Requirements

| Requirement | Implementation |
|-------------|----------------|
| **Focus visible** | 2px solid ring, 3:1 contrast |
| **Color contrast** | 4.5:1 minimum (WCAG AA) |
| **Touch targets** | 44x44px minimum |
| **Keyboard nav** | Tab order, Escape to close |
| **Screen reader** | ARIA labels on icons |

---

## 12. Deliverables Expected

디자이너에게 요청할 산출물:

1. **HTML/CSS 프로토타입**: 단일 페이지
2. **Desktop 뷰** (1440px)
3. **Mobile 뷰** (375px)
4. **Light/Dark 모드** (Dark 우선)
5. **Interactive States**: Hover, Focus, Active, Disabled
6. **3 Step States**: Pending, Active, Completed

---

## 13. Reference Sites

미니멀 디자인 참고:
- **Linear.app**: 깔끔한 워크플로우 UI
- **Vercel.com**: 개발자 도구 미니멀리즘
- **Raycast.com**: macOS 네이티브 느낌
- **Notion.so**: Progressive disclosure 패턴

---

## 14. Do's and Don'ts

### Do's
- White space 충분히 활용
- 한 번에 하나의 액션에 집중
- 단계 간 전환을 부드럽게
- Evidence/Credit 정보는 subtle하게

### Don'ts
- 2x2 그리드로 모든 옵션 동시 표시 (현재 문제점)
- 복잡한 Progress bar
- 과도한 그림자/글로우
- 작은 클릭 영역

---

## 15. Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Visual complexity (subjective) | High | Low |
| Click to first action | 3 clicks | 1 click |
| Cognitive load | High | Minimal |
| Brand consistency with homepage | 60% | 95% |

---

## Appendix: Current Screenshot Description

`/dna-lab?master=velvet&mode=quick` 접속 시:

1. **Header**: DNA 아이콘 + "DNA Lab" 타이틀 + 서브타이틀
2. **Progress Stepper**: 3단계 수평 바 (퍼센티지 포함)
3. **2x2 Overview Grid**: 4개의 큰 카드 (영상분석, 미학적용, 창작DNA, 품질검증)
4. **각 카드**: 아이콘 + 제목 + 설명 + "시작하기" 버튼
5. **배경**: 단색 다크 그레이 (Aurora 없음)

**개선 필요 포인트**:
- 2x2 그리드 → Linear 스타일 단계 표시
- 4개 카드 → 현재 단계 1개만 강조
- 복잡한 스테퍼 → 심플한 3-dot indicator
- Aurora 배경 추가로 메인 페이지와 통일

---

**Document Version**: 1.0
**Last Updated**: 2026-01-31
**Author**: Claude Code (AI Assistant)
**For**: Silicon Valley Design Consultation
