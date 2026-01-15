# UI Design Guide (2025-12, Crebit)

<details open>
<summary>한국어</summary>

**작성**: 2025-12-28 (Last Updated: 2026-01-01 - Agent Studio 추가)  
**대상**: Product / Design / Frontend  
**목표**: 최신 UI/UX 기준과 기술 트렌드를 반영한 Crebit 전용 UI 가이드

---

> **Status (2026-01)**  
> 현재 메인 UI는 **Dimension(/dimension)** 및 **Flow(열차 UI, /flow)**가 중심이며, Canvas UI는 레거시로 유지됩니다.

## 1) Research baseline (2025-12)

### UI/UX fundamentals
- **WCAG 2.2**: 접근성 표준은 Perceivable/Operable/Understandable/Robust 4원칙을 기반으로 하며, UI 전반의 가독성/조작성/명확성을 보장해야 함.  
  https://www.w3.org/WAI/standards-guidelines/wcag/

### Modern UI engineering primitives (web)
- **Container Queries**: 컴포넌트가 자신의 컨테이너 크기에 반응하도록 설계 가능.  
  https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_container_queries
- **View Transitions API**: 화면 전환 시 컨텍스트 유지/인지 부하 감소에 효과적.  
  https://developer.mozilla.org/en-US/docs/Web/API/View_Transitions_API
- **OKLCH + color-mix()**: 지각적으로 균일한 컬러 보간/조합에 유리.  
  https://developer.mozilla.org/en-US/docs/Web/CSS/color_value/oklch  
  https://developer.mozilla.org/en-US/docs/Web/CSS/color_value/color-mix
- **accent-color**: 시스템 컨트롤 스타일 일관성 유지에 유효.  
  https://developer.mozilla.org/en-US/docs/Web/CSS/accent-color

### Product context (NotebookLM/Opal)
- 역할 정의는 `08_PIPELINES_AND_USER_FLOWS.md`를 따른다.  
- NotebookLM Studio 다중 출력/다국어는 **다중 결과 카드/언어 스위치 UI**로 반영 필요.  
- Opal 워크플로는 **검수/라벨링 패널**을 통해 캡슐 스펙과 연결.  
  (출처는 `03_RESEARCH_SOURCES_2025-12.md` 참고)

### Benchmark UI notes
- Virlo Content Studio benchmark findings: `16_VIRLO_CONTENT_STUDIO_RESEARCH.md`

---

## 2) Crebit UI 방향성 (프로젝트 적합)

핵심 키워드:
- **Studio-grade**: 제작 도구처럼 깊이감 있는 레이어 구조
- **Evidence-first**: 근거/패턴/버전 정보가 UI에 자연스럽게 드러남
- **Capsule-first**: 핵심 로직은 봉인, 사용자는 입력/파라미터만 조정
- **Low-friction**: 템플릿 선택 → 캡슐 실행 → 프리뷰까지 3~5 클릭

---

## 3) Layout blueprint

기본 구조 (현재):
- **Top bar**: 상태/크레딧 + 실행 CTA
- **Left rail**: Dimension / Flow / Credits / Settlements / Settings
- **Main**: Train Workflow (Flow) 또는 Dimension 미니앱
- **Right inspector**: 선택 도구/카드 요약 (옵션)
- **Bottom panel**: 아티팩트 프리뷰/로그 (옵션)

Legacy Canvas 레이아웃:
- 노드/엣지 편집 + Inspector + Bottom Preview 구성을 유지하되 `_deprecated` 경로에만 존재

모바일/소형 화면:
- 좌/우 패널은 **스와이프 드로어**로 전환
- 캔버스는 **read-only 축소 뷰** 제공

---

## 4) Visual system (tokens)

기본 테마는 기존 `globals.css`와 정합성을 유지:

색상 토큰 (예시):
- `--bg-0/#0b0e13`, `--bg-1/#0f172a`, `--bg-2/#111827`
- `--fg-0/#e2e8f0`, `--fg-muted` 65% alpha
- `--accent/#38bdf8`, `--accent-2/#f59e0b`

확장 토큰:
- `--surface-1`: color-mix(in oklch, var(--bg-2) 80%, white 20%)
- `--surface-2`: color-mix(in oklch, var(--bg-1) 70%, white 30%)
- `--border-muted`: rgba(148, 163, 184, 0.25)

규칙:
- 배경은 **다층 그라데이션** 유지
- 포커스/선택은 **accent 색상**만 사용 (보라색 회피)
- 카드/노드에는 **약한 글로우 + 보더**로 깊이감 부여

---

## 5) Typography

현재 폰트와 정합:
- UI 본문: **Space Grotesk**
- 코드/ID: **JetBrains Mono**

스케일 제안:
- Display 24/28
- Title 18/24
- Body 14/20
- Meta 12/16

규칙:
- 긴 텍스트는 **최대 60자/줄** 제한
- Inspector 레이블은 **12~13px** 고정

---

## 6) Component guidelines

### 6.1 Template Cards
- 카드 상단: 제목/태그라인
- 카드 하단: Start 버튼 + mini preview
- hover 시 preview_video_url 재생 (자동 음소거)
- Evidence refs가 있으면 **근거 배지** 표시 (count)

### 6.2 Capsule Node

**Visual Identity:**
- 잠금 아이콘 + "Sealed" 배지 (기본 상태)
- 파라미터는 슬라이더/드롭다운 중심
- evidence refs는 **접기 가능한 리스트**

**Node FSM (Virlo 기반 5-State Machine):**

| State       | Visual Cue                                      | UX Behavior                                    |
|-------------|-------------------------------------------------|------------------------------------------------|
| `Idle`      | `--border-muted`, 잠금 아이콘                     | 입력 대기, 파라미터 편집 가능                      |
| `Loading`   | `--accent` pulse border, spinner                | 입력 커밋 후 서버 응답 대기 (Optimistic)            |
| `Streaming` | `--accent-2` glow, partial text reveal          | 청크 단위 결과 표시 (SSE/WebSocket)              |
| `Complete`  | `--accent` solid border, checkmark badge        | 전체 결과 확정, 요약 카드 표시                     |
| `Error`     | `--red-500` border, warning icon                | 오류 메시지 + Retry CTA                         |
| `Cancelled` | `--muted` border, neutral badge                 | 사용자가 중단, Cancelled 배지 노출                |

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Loading : Run Click
    Loading --> Streaming : First Chunk Received
    Loading --> Error : Timeout / API Error
    Loading --> Cancelled : Cancel
    Streaming --> Complete : Stream End
    Streaming --> Error : Stream Error
    Streaming --> Cancelled : Cancel
    Complete --> Idle : Reset / New Run
    Error --> Idle : Dismiss / Retry
    Cancelled --> Idle : Retry / New Run
```

**Implementation Notes:**
- `Loading` 상태 진입 시 **500ms 이내** 시각적 피드백 필수.
- `Streaming` 중 사용자 입력 필드는 **disabled** 상태로 전환하여 충돌 방지.
- `Error` 상태에서 `Retry` 클릭 시 마지막 파라미터로 재실행.

### 6.3 Inspector
- 섹션 분리: Params / Evidence / Runs
- Evidence는 **source_id + patternVersion** 고정 표기

### 6.4 Admin Panels (Optional)
- Notebook Library 뷰는 관리자 전용
- Evidence/Pattern Trace 테이블은 읽기 전용 + 필터 제공
- Pipeline Ops: 단계별 상태 카드 + Quarantine 요약 + 템플릿 시드 액션 + Ops 실행 로그
- Template Provenance: 템플릿별 guide_sources + evidence_refs 요약 카드 + 누락 카운트 배지
- Templates Stage Card: 공개 템플릿 + 근거 누락 수 표시
- Pattern Version History 카드 (최근 5개 버전 + note 표시)
- Quarantine 샘플 카드 (sheet/reason/row)
- Admin-only 메시지: 권한이 없을 때는 **admin-only** 힌트 + 로그인 CTA 출력

### 6.5 Preview Panel
- Storyboard 카드 (컷, 색감, 리듬)
- 다중 출력 전환: Video/Audio/Mind Map (NotebookLM Ultra 반영)

### 6.6 Onboarding / Empty State (Detailed)
- **Primary Action**: "Get Data" or "Create First Workflow" (Clear, singular CTA).
- **Empty Workflow State**:
  - Show a "Seed Flow" selection (e.g., "Start with YouTube Repurposing", "Start with PDF Analysis").
  - Do not show a completely blank grid; guide the first tool placement.
- **Visuals**:
  - Use "Input / Processor / Output" conceptual icons in the empty state.
  - See `virlo_content_studio_canvas` for reference on clear node ports (legacy canvas reference).
- Core Components / What You Can Build / How It Works 카드 구성

### 6.7 Story-First Components (NEW: 2025-12-30)

Legacy Canvas UI의 우측 패널에 통합된 Story-First 제어 컴포넌트들:

#### 6.7.1 CanvasNarrativePanel
서사 구조와 훅 설계를 위한 확장 가능한 패널.

**구성:**
- **헤더**: Story-First DNA 활성화 토글 + 현재 설정 요약
- **3-Tab 구조**:
  - `부조화 설계`: 익숙함/낯섦 조합 (Cognitive Dissonance)
  - `감정 곡선`: 시작/절정/결말 감정 설정
  - `훅 스타일`: HookVariantSelector 통합

**스타일:**
- Glassmorphism 컨테이너 (`bg-[#0A0A0C]/90 backdrop-blur-xl`)
- Motion Tab (Framer Motion `layoutId`)
- Gradient 버튼 (`from-yellow-600 to-orange-600` 등)

#### 6.7.2 HookVariantSelector
8가지 훅 스타일 중 선택 및 A/B 테스트 설정.

**훅 스타일 (8종):**
| Style     | Label    | Color       | Description              |
|-----------|----------|-------------|--------------------------|
| shock     | 충격형   | red-400     | 강렬한 시각적 충격        |
| curiosity | 호기심형 | purple-400  | 미스터리와 궁금증 유발    |
| emotion   | 감정형   | pink-400    | 감정적 연결로 시작        |
| question  | 의문형   | blue-400    | 직접적 질문으로 시작      |
| paradox   | 역설형   | yellow-400  | 예상을 뒤집는 부조화      |
| tease     | 티저형   | cyan-400    | 결과를 먼저 보여주기      |
| action    | 액션형   | orange-400  | 바로 액션으로 돌입        |
| calm      | 차분형   | emerald-400 | 여유로운 분위기 조성      |

**VariantCard 스타일:**
- 기본: `bg-white/5 border-white/5 hover:bg-white/10`
- 선택됨: 해당 색상 배경 + Glow 효과 (`shadow-lg`)
- A/B 테스트 모드: `ring-2 ring-blue-500`

#### 6.7.3 DNAComplianceViewer
브랜드 DNA 가이드라인 준수 여부를 시각적으로 표시.

**구성:**
- **Summary Card**: 준수율 퍼센트 + 적합/주의/위반 카운트
- **Shot Reports**: 확장 가능한 샷별 상세 리포트
- **Action Items**: AI 수정 제안 + 재생성 버튼

**레벨 배지:**
| Level      | Icon           | Color        |
|------------|----------------|--------------|
| compliant  | CheckCircle    | emerald-400  |
| partial    | AlertTriangle  | yellow-400   |
| violation  | XCircle        | red-400      |
| unknown    | HelpCircle     | gray-400     |

#### 6.7.4 MetricsDashboard
바이럴 성과 분석 및 A/B 테스트 결과 대시보드.

**탭 구성:**
- `개요`: 총 조회수/콘텐츠/참여율/바이럴점수 + 훅 스타일별 바 차트
- `A/B 테스트`: 테스트별 변형 성과 비교 카드
- `인사이트`: AI 기반 성과 인사이트 + 추천 액션

**스타일:**
- StatCard: `bg-white/5 backdrop-blur-md rounded-2xl`
- 바 차트: Motion 애니메이션 (`width: 0 → X%`)
- 인사이트 카드: Hover 시 Purple Glow

---

## 6.8 Agent Studio (Chat-first) (NEW: 2026-01-01)

Chat-first 진입점을 위한 Agent Studio UI 가이드.

**구성 원칙:**
- **Simple / Expert** 토글: Simple은 결과 중심(아티팩트/텍스트), Expert는 도구/메타/세션 정보 노출.
- **Chat Panel**: role 구분(User/Agent/Tool) + SSE 스트리밍 상태 표시.
- **Tool Result Card**: 실패/거절은 명확한 색상/문구, 성공은 payload 요약.
- **Artifact Preview**: Audio Overview는 현행 적용. Storyboard/Shot List/Data Table은 **legacy capsule 경로**에서만 생성되며 Flow/Teaching 연동은 계획 단계.
- **Canvas Sync**: 워크플로우 수신 시 적용/무시 선택 + 자동 적용 토글 (현재 비활성).

권장 톤:
- 에이전트 메시지는 **부드러운 카드 대비**와 충분한 행간으로 가독성 확보.
- 도구 결과는 **작고 밀도 있는 카드**, 아티팩트는 **큰 프리뷰 카드**로 분리.

## 6.9 Glassmorphism Design System (NEW: 2025-12-30)

Story-First 컴포넌트 전반에 적용된 Premium 디자인 시스템.

### 기본 원칙

1. **투명도 계층 (Opacity Hierarchy)**
   - 배경: `bg-[#0A0A0C]/90` 또는 `bg-white/5`
   - 보더: `border-white/5` → `border-white/10` → `border-white/20`
   - 호버: `hover:bg-white/10`

2. **블러 효과 (Backdrop Blur)**
   - 기본 패널: `backdrop-blur-xl`
   - 모달/오버레이: `backdrop-blur-md`
   - 카드: `backdrop-blur-sm`

3. **그림자 및 Glow**
   - 선택/활성 상태: `shadow-lg shadow-{color}-500/20`
   - 패널 그림자: `shadow-2xl`
   - Glow Ring: `ring-1 ring-{color}-500/50`

### 색상 팔레트 (Story-First 전용)

```css
/* Primary Actions */
--sf-purple: #a855f7;  /* purple-500 */
--sf-pink: #ec4899;    /* pink-500 */

/* Status Colors */
--sf-success: #10b981; /* emerald-500 */
--sf-warning: #f59e0b; /* amber-500 */
--sf-error: #ef4444;   /* red-500 */

/* Neutral */
--sf-bg-base: #0A0A0C;
--sf-border-muted: rgba(255, 255, 255, 0.05);
--sf-border-default: rgba(255, 255, 255, 0.10);
```

### 인터랙션 패턴

1. **Tab 전환**: `layoutId` 기반 Shared Layout Animation
2. **카드 호버**: `scale: 1.02, y: -2` (Framer Motion)
3. **버튼 호버**: Gradient Shift + Shadow 증가
4. **Input 포커스**: `border-purple-500/50` + `ring-1 ring-purple-500/20`

---

## 7) Motion & Interaction

- **View Transition**: 패널 전환, 템플릿 → 워크플로우 이동
- **Reduced motion**: `prefers-reduced-motion` 시 애니메이션 제거
- Drag/Drop은 **100ms 이하 반응성** 유지

---

## 8) Accessibility (WCAG 2.2 준수)

- 텍스트 대비 **4.5:1 이상**
- 모든 주요 액션 **키보드 접근 가능**
- 상태 변화는 **색상 + 텍스트**로 이중 표현
- 포커스 링은 **명확하고 일관성 있게**

---

## 9) Implementation notes (frontend)

- `container-type: inline-size`로 Inspector/Preview 패널 반응형 설계
- `accent-color`로 체크박스/슬라이더 톤 정렬
- 컬러 계산은 `oklch` + `color-mix()` 활용
- View Transition 지원 브라우저에서만 활성화 (폴백 제공)

---

## 10) Acceptance checklist

- 템플릿 카드 → 워크플로우 전환이 1초 내 완료
- 캡슐 실행 후 요약/근거가 한 화면에서 확인 가능
- Storyboard/Preview는 다중 출력 전환 가능
- 모든 주요 UI는 키보드만으로 조작 가능

</details>

<details>
<summary>English</summary>

**Created**: 2025-12-28 (Last Updated: 2026-01-01 - Agent Studio added)  
**Audience**: Product / Design / Frontend  
**Goal**: A Crebit-specific UI guide reflecting the latest UI/UX standards and technology trends

---

> **Status (2026-01)**  
> The main UI centers on **Dimension (/dimension)** and **Flow (train UI, /flow)**, while Canvas UI remains legacy.

## 1) Research baseline (2025-12)

### UI/UX fundamentals
- **WCAG 2.2**: Accessibility standards are based on the four principles Perceivable/Operable/Understandable/Robust, ensuring readability, operability, and clarity across the UI.  
  https://www.w3.org/WAI/standards-guidelines/wcag/

### Modern UI engineering primitives (web)
- **Container Queries**: Design components to respond to their container size.  
  https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_container_queries
- **View Transitions API**: Effective for preserving context and reducing cognitive load during transitions.  
  https://developer.mozilla.org/en-US/docs/Web/API/View_Transitions_API
- **OKLCH + color-mix()**: Useful for perceptually uniform color interpolation and combinations.  
  https://developer.mozilla.org/en-US/docs/Web/CSS/color_value/oklch  
  https://developer.mozilla.org/en-US/docs/Web/CSS/color_value/color-mix
- **accent-color**: Helps maintain consistent system control styling.  
  https://developer.mozilla.org/en-US/docs/Web/CSS/accent-color

### Product context (NotebookLM/Opal)
- Role definitions follow `08_PIPELINES_AND_USER_FLOWS.md`.  
- NotebookLM Studio multi-output/multilingual should be reflected as **multi-result cards and language switch UI**.  
- Opal workflows connect to capsule specs via **review/labeling panels**.  
  (See `03_RESEARCH_SOURCES_2025-12.md` for sources)

### Benchmark UI notes
- Virlo Content Studio benchmark findings: `16_VIRLO_CONTENT_STUDIO_RESEARCH.md`

---

## 2) Crebit UI Direction (Project Fit)

Key keywords:
- **Studio-grade**: deep layered structure like a production tool
- **Evidence-first**: evidence/pattern/version info is naturally visible in the UI
- **Capsule-first**: core logic is sealed; users adjust inputs/parameters only
- **Low-friction**: template select → capsule run → preview in 3-5 clicks

---

## 3) Layout blueprint

Default structure (current):
- **Top bar**: status/credits + run CTA
- **Left rail**: Dimension / Flow / Credits / Settlements / Settings
- **Main**: Train Workflow (Flow) or Dimension mini-apps
- **Right inspector**: selected tool/card summary (optional)
- **Bottom panel**: artifact preview/logs (optional)

Legacy Canvas layout:
- Keep node/edge editing + Inspector + Bottom Preview, but only under the `_deprecated` path

Mobile/small screens:
- Left/right panels become **swipe drawers**
- Canvas provides a **read-only compact view**

---

## 4) Visual system (tokens)

Base theme aligns with `globals.css`:

Color tokens (examples):
- `--bg-0/#0b0e13`, `--bg-1/#0f172a`, `--bg-2/#111827`
- `--fg-0/#e2e8f0`, `--fg-muted` 65% alpha
- `--accent/#38bdf8`, `--accent-2/#f59e0b`

Extended tokens:
- `--surface-1`: color-mix(in oklch, var(--bg-2) 80%, white 20%)
- `--surface-2`: color-mix(in oklch, var(--bg-1) 70%, white 30%)
- `--border-muted`: rgba(148, 163, 184, 0.25)

Rules:
- Maintain **multi-layer gradients** for backgrounds
- Use **accent colors only** for focus/selection (avoid purple)
- Add depth with **subtle glow + borders** on cards/nodes

---

## 5) Typography

Aligned with current fonts:
- UI body: **Space Grotesk**
- Code/IDs: **JetBrains Mono**

Scale suggestions:
- Display 24/28
- Title 18/24
- Body 14/20
- Meta 12/16

Rules:
- Limit long text to **max 60 characters/line**
- Inspector labels fixed at **12-13px**

---

## 6) Component guidelines

### 6.1 Template Cards
- Card header: title/tagline
- Card footer: Start button + mini preview
- Play preview_video_url on hover (muted)
- If evidence refs exist, show an **evidence badge** (count)

### 6.2 Capsule Node

**Visual Identity:**
- Lock icon + "Sealed" badge (default)
- Parameters use sliders/dropdowns
- Evidence refs shown as a **collapsible list**

**Node FSM (Virlo-based 5-State Machine):**

| State       | Visual Cue                                      | UX Behavior                                    |
|-------------|-------------------------------------------------|------------------------------------------------|
| `Idle`      | `--border-muted`, lock icon                     | Await input, parameters editable               |
| `Loading`   | `--accent` pulse border, spinner                | Wait for server response after input commit    |
| `Streaming` | `--accent-2` glow, partial text reveal          | Show chunked results (SSE/WebSocket)           |
| `Complete`  | `--accent` solid border, checkmark badge        | Finalize output, show summary card             |
| `Error`     | `--red-500` border, warning icon                | Error message + Retry CTA                      |
| `Cancelled` | `--muted` border, neutral badge                 | User cancelled, show Cancelled badge           |

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Loading : Run Click
    Loading --> Streaming : First Chunk Received
    Loading --> Error : Timeout / API Error
    Loading --> Cancelled : Cancel
    Streaming --> Complete : Stream End
    Streaming --> Error : Stream Error
    Streaming --> Cancelled : Cancel
    Complete --> Idle : Reset / New Run
    Error --> Idle : Dismiss / Retry
    Cancelled --> Idle : Retry / New Run
```

**Implementation Notes:**
- Provide visual feedback within **500ms** when entering `Loading`.
- Disable input fields during `Streaming` to avoid conflicts.
- On `Error`, Retry should rerun with the last parameters.

### 6.3 Inspector
- Section split: Params / Evidence / Runs
- Evidence displays fixed `source_id + patternVersion`

### 6.4 Admin Panels (Optional)
- Notebook Library view is admin-only
- Evidence/Pattern Trace tables are read-only with filters
- Pipeline Ops: step status cards + quarantine summary + template seed actions + ops run logs
- Template Provenance: per-template guide_sources + evidence_refs summary cards + missing count badge
- Templates Stage Card: public templates + missing evidence count
- Pattern Version History card (latest 5 versions + notes)
- Quarantine sample cards (sheet/reason/row)
- Admin-only message: show **admin-only** hint + login CTA when unauthorized

### 6.5 Preview Panel
- Storyboard cards (cuts, color, rhythm)
- Multi-output switch: Video/Audio/Mind Map (NotebookLM Ultra)

### 6.6 Onboarding / Empty State (Detailed)
- **Primary Action**: "Get Data" or "Create First Workflow" (clear, singular CTA)
- **Empty Workflow State**:
  - Show a "Seed Flow" selection (e.g., "Start with YouTube Repurposing", "Start with PDF Analysis").
  - Do not show a completely blank grid; guide the first tool placement.
- **Visuals**:
  - Use "Input / Processor / Output" conceptual icons in the empty state.
  - See `virlo_content_studio_canvas` for reference on clear node ports (legacy canvas reference).
- Compose cards for Core Components / What You Can Build / How It Works

### 6.7 Story-First Components (NEW: 2025-12-30)

Story-First control components integrated into the right panel of the legacy Canvas UI:

#### 6.7.1 CanvasNarrativePanel
Expandable panel for narrative structure and hook design.

**Structure:**
- **Header**: Story-First DNA toggle + current settings summary
- **3-Tab layout**:
  - `Dissonance Design`: combine familiar/unfamiliar (Cognitive Dissonance)
  - `Emotional Arc`: set start/climax/end emotions
  - `Hook Style`: HookVariantSelector integration

**Style:**
- Glassmorphism container (`bg-[#0A0A0C]/90 backdrop-blur-xl`)
- Motion Tab (Framer Motion `layoutId`)
- Gradient buttons (`from-yellow-600 to-orange-600`, etc.)

#### 6.7.2 HookVariantSelector
Select one of 8 hook styles and set A/B testing.

**Hook styles (8):**
| Style     | Label       | Color       | Description                 |
|-----------|-------------|-------------|-----------------------------|
| shock     | Shock       | red-400     | Start with a strong visual  |
| curiosity | Curiosity   | purple-400  | Trigger mystery and interest|
| emotion   | Emotion     | pink-400    | Start with emotional tie-in |
| question  | Question    | blue-400    | Start with a direct question|
| paradox   | Paradox     | yellow-400  | Subvert expectations        |
| tease     | Tease       | cyan-400    | Show the result first       |
| action    | Action      | orange-400  | Jump into action immediately|
| calm      | Calm        | emerald-400 | Set a relaxed mood          |

**VariantCard styles:**
- Default: `bg-white/5 border-white/5 hover:bg-white/10`
- Selected: colored background + glow (`shadow-lg`)
- A/B mode: `ring-2 ring-blue-500`

#### 6.7.3 DNAComplianceViewer
Visually indicates compliance with brand DNA guidelines.

**Structure:**
- **Summary Card**: compliance rate + compliant/partial/violation counts
- **Shot Reports**: expandable per-shot reports
- **Action Items**: AI fixes + regenerate button

**Level badges:**
| Level      | Icon           | Color        |
|------------|----------------|--------------|
| compliant  | CheckCircle    | emerald-400  |
| partial    | AlertTriangle  | yellow-400   |
| violation  | XCircle        | red-400      |
| unknown    | HelpCircle     | gray-400     |

#### 6.7.4 MetricsDashboard
Dashboard for viral performance and A/B test results.

**Tabs:**
- `Overview`: total views/content/engagement/viral score + hook style bar chart
- `A/B Tests`: per-test variant comparison cards
- `Insights`: AI-driven insights + recommended actions

**Style:**
- StatCard: `bg-white/5 backdrop-blur-md rounded-2xl`
- Bar charts: motion animation (`width: 0 → X%`)
- Insight cards: purple glow on hover

---

## 6.8 Agent Studio (Chat-first) (NEW: 2026-01-01)

Agent Studio UI guide for the chat-first entry point.

**Principles:**
- **Simple / Expert** toggle: Simple focuses on results (artifacts/text), Expert shows tools/meta/session info.
- **Chat Panel**: role separation (User/Agent/Tool) + SSE streaming state.
- **Tool Result Card**: failure/refusal uses explicit colors/text, success summarizes payload.
- **Artifact Preview**: Audio Overview is live; Storyboard/Shot List/Data Table are generated only via **legacy capsule paths** and Flow/Teaching integration is planned.
- **Canvas Sync**: apply/ignore on workflow receipt + auto-apply toggle (currently disabled).

Recommended tone:
- Agent messages use **soft card contrast** and generous line spacing for readability.
- Tool results use **compact dense cards**, artifacts use **large preview cards**.

## 6.9 Glassmorphism Design System (NEW: 2025-12-30)

Premium design system applied across Story-First components.

### Core principles

1. **Opacity hierarchy**
   - Background: `bg-[#0A0A0C]/90` or `bg-white/5`
   - Border: `border-white/5` → `border-white/10` → `border-white/20`
   - Hover: `hover:bg-white/10`

2. **Backdrop blur**
   - Base panels: `backdrop-blur-xl`
   - Modals/overlays: `backdrop-blur-md`
   - Cards: `backdrop-blur-sm`

3. **Shadows and glow**
   - Selected/active: `shadow-lg shadow-{color}-500/20`
   - Panel shadow: `shadow-2xl`
   - Glow ring: `ring-1 ring-{color}-500/50`

### Color palette (Story-First only)

```css
/* Primary Actions */
--sf-purple: #a855f7;  /* purple-500 */
--sf-pink: #ec4899;    /* pink-500 */

/* Status Colors */
--sf-success: #10b981; /* emerald-500 */
--sf-warning: #f59e0b; /* amber-500 */
--sf-error: #ef4444;   /* red-500 */

/* Neutral */
--sf-bg-base: #0A0A0C;
--sf-border-muted: rgba(255, 255, 255, 0.05);
--sf-border-default: rgba(255, 255, 255, 0.10);
```

### Interaction patterns

1. **Tab transitions**: shared layout animation via `layoutId`
2. **Card hover**: `scale: 1.02, y: -2` (Framer Motion)
3. **Button hover**: gradient shift + stronger shadow
4. **Input focus**: `border-purple-500/50` + `ring-1 ring-purple-500/20`

---

## 7) Motion & Interaction

- **View Transition**: panel transitions, template → workflow navigation
- **Reduced motion**: disable animations with `prefers-reduced-motion`
- Drag/Drop maintains **sub-100ms responsiveness**

---

## 8) Accessibility (WCAG 2.2 compliant)

- Text contrast **>= 4.5:1**
- All primary actions **keyboard accessible**
- State changes indicated by **color + text**
- Focus rings are **clear and consistent**

---

## 9) Implementation notes (frontend)

- Use `container-type: inline-size` for responsive Inspector/Preview panels
- Use `accent-color` to align checkbox/slider tones
- Color calculations via `oklch` + `color-mix()`
- Enable View Transitions only where supported (with fallbacks)

---

## 10) Acceptance checklist

- Template card → workflow transition completes within 1 second
- After a capsule run, summary/evidence are visible in one view
- Storyboard/Preview support multi-output switching
- All key UI is operable via keyboard only

</details>
