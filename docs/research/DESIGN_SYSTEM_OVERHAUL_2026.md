# Crebit Studio Design System Overhaul 2026 (Upgraded)

> 2026년 기준 최신 표준/가이드 반영 + Crebit Studio 서비스 특화 개선안

*업데이트: 2026-01-18*  
*작성: Design Systems Research (MCP + Web)*

---

## Executive Summary

Crebit Studio의 디자인 시스템을 **2026년 표준 기반으로 재정비**하여 “AI 크리에이티브 툴”에 최적화된 일관성/확장성/접근성을 확보합니다.

**핵심 업그레이드**

1. **Design Tokens 2025.10 (DTCG) 기반 표준화**
   - DTCG 2025.10 안정판은 테마/다중 브랜드/현대 색공간/토큰 참조를 표준화합니다. 이를 토큰 SSoT로 채택해 디자인-개발 간 동기화를 강화합니다.
2. **OKLCH + Wide Gamut 색공간 정렬**
   - CSS Color 4는 OKLCH/OKLAB 및 wide gamut 색공간을 표준화합니다. Crebit의 색상 시스템을 OKLCH 기반으로 전면 재정렬하여 **지각 균일성 + 테마 일관성** 확보.
3. **WCAG 2.2 최신 접근성 준수**
   - Focus Appearance, Target Size(최소 24x24), Dragging 대체 조작 등 새 기준을 시스템 차원에서 반영.
4. **OS/UA 선호도 대응 강화**
   - `color-scheme` + `prefers-color-scheme`, `prefers-contrast`, `forced-colors`, `prefers-reduced-transparency` 등 최신 CSS 사용자 선호도 지원.
5. **Crebit Studio 서비스 특화 토큰/컴포넌트 레이어링**
   - Dimension/AppRegistry 기반 색상·상태·글로우·미디어 도구 UI에 맞는 토큰 구조 제공.

---

## 0. Crebit 철학 정합성 (SSoT 고정)

본 문서는 **Crebit 핵심 철학(SSoT)**을 변경하거나 재정의하지 않는다.  
디자인 시스템은 철학을 **UI 토큰/컴포넌트/상태 체계로 구현**하는 역할만 수행한다.

**정본 참조(SSoT)**
- `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md` (비타협 철학)
- `08_PIPELINES_AND_USER_FLOWS.md` (Flow/Dimension 중심 UI 흐름)
- `10_UI_DESIGN_GUIDE_2025-12.md` (UI 기본 규칙)
- `docs/DIMENSION_APP_DEVELOPER_GUIDE.md` + `config/apps/content/dimensions/*.yaml` (Dimension/AppRegistry SSoT)

### 0.1 Philosophy → UI Contract (필수 구현)

| Crebit 철학 | UI/디자인 시스템 의무 요소 |
|---|---|
| **Evidence-first** | Evidence Badge, Provenance Panel, Pattern Version Chip, Source Ref UI |
| **Sealed Capsule** | Locked 상태 시각화, 입력/파라미터만 노출, 내부 체인 숨김 |
| **Credit/Observability** | Run 비용/지연/토큰/크레딧 상태를 UI 상단에 고정 노출 |
| **Chat-first + Flow-first** | Chat/Flow 진입점을 우선 배치, Canvas는 레거시 |
| **Dimension SSoT** | Dimension 색상/명칭/기능은 AppRegistry 기준으로 자동 생성 |

### 0.2 정합성 가드레일
- 토큰/컴포넌트는 **철학과 실행 UX**를 우선 반영한다. (트렌드는 옵션)
- Dimension/앱 명칭은 **AppRegistry YAML**을 기준으로 자동 동기화한다.
- Evidence/Run Token 오류/크레딧 상태는 **숨기지 않는다** (핵심 UX).

---

## 1. 2026 기준 표준/가이드 요약 (SSoT 업데이트)

### 1.1 Design Tokens 2025.10 (DTCG)
- W3C Design Tokens Community Group는 **2025.10 안정판**을 공개하고 테마/색공간/토큰 관계 등을 표준화했습니다.  
  *(Community Group 스펙이며 W3C Recommendation은 아님 — 업계 표준 포맷으로 빠르게 정착 중)*  
- **단일 JSON SSoT → 디자인 툴 + 코드 동기화**의 기반으로 사용 가능.

### 1.2 CSS Color 4 (OKLCH 포함)
- CSS Color Module 4는 OKLCH/OKLAB 등 **지각적으로 균일한 색공간**을 지원합니다.
- OKLCH 기반 토큰은 “명도·채도·색상”의 의미 분리가 명확해 **다크/라이트 전환에 강함**.
- 현 시점은 CRD 단계이므로 **fallback 색상 토큰과 함께 점진 적용**한다.

### 1.3 WCAG 2.2 주요 추가 사항
- **Focus Appearance**: 포커스 링 대비 3:1 이상, 최소 2px 두께 기준.
- **Target Size (Minimum)**: 인터랙션 요소 최소 24x24 CSS px.
- **Dragging Movements**: 드래그 동작에 대한 대체 입력 제공.
- **Accessible Authentication**: 인증 과정에서 접근성 보장.

### 1.4 Color Scheme + User Preferences
- `color-scheme` 속성으로 브라우저 UI까지 라이트/다크 테마 협상.
- `prefers-contrast`, `forced-colors`, `prefers-reduced-transparency` 지원으로 **고대비/강제색상/투명도 최소화 선호** 대응.  
  *(Media Queries Level 5 기반 기능은 브라우저 지원 범위 확인 필요)*

### 1.5 Figma Variables & DTCG Import
- Figma 변수는 **Mode(라이트/다크/고대비)** 를 지원하며, DTCG JSON 형식 토큰을 직접 import 할 수 있음.

### 1.6 Fluent 2 토큰 구조 참고
- Fluent 2는 **Global → Alias → Component** 토큰 계층을 사용.
- 라이트/다크/고대비/브랜드 테마 확장에 유리한 구조.

---

## 2. 현재 Crebit Studio 디자인 시스템 진단

### 핵심 문제

1. **토큰 계층 미흡**: primitive/semantic/component 분리 불완전
2. **다크 모드 대비 과도**: 거의 검정 배경으로 피로감 + 레이어 깊이 약화
3. **Dimension 색상 일관성 부족**: 명도/채도 분포가 균일하지 않음
4. **접근성 및 사용자 선호 대응 부족**: WCAG 2.2, prefers-contrast, forced-colors 대응 미흡
5. **Crebit 핵심 철학 반영 부족**: Evidence/Sealed/Credit/Chat-first가 시스템 토큰에 없음
6. **Dimension/앱 구조 불일치**: 1D~15D 고정 스키마가 실제 AppRegistry와 불일치

---

## 3. 2026 업그레이드 디자인 원칙 (Crebit 특화)

### 3.1 Token Architecture (Global → Alias → Component)

**Global Tokens**: 순수값 (색상/타이포/간격/반경/그림자)

**Alias Tokens**: 의미 기반 (bg, fg, border, status, brand, dimension)

**Component Tokens**: 버튼, 카드, 입력, 패널 등 컴포넌트 레벨

> **목표**: Crebit Studio 내 모든 UI가 Alias/Component 토큰만 사용하도록 강제.

### 3.2 Theming & Modes

- Light / Dark / High-Contrast / Pro Mode(선택)
- Figma Variables **Mode**와 DTCG JSON 파일을 매핑하여 디자인↔코드 동기화

### 3.3 Color System (OKLCH 기반)

- OKLCH로 **Neutral Scale** + Dimension Accent를 구성
- 모든 Alias/Component 토큰은 OKLCH 기반으로 자동 변환
  - **주의**: CSS Color 4는 CRD 단계이므로 `@supports (color: oklch(...))` + hex fallback 토큰을 병행

**Neutral Scale 예시 (OKLCH)**

```css
:root {
  --neutral-0:   oklch(100% 0 0);
  --neutral-50:  oklch(97% 0.005 280);
  --neutral-100: oklch(94% 0.01 280);
  --neutral-200: oklch(88% 0.015 280);
  --neutral-300: oklch(75% 0.02 280);
  --neutral-400: oklch(60% 0.02 280);
  --neutral-500: oklch(50% 0.02 280);
  --neutral-600: oklch(40% 0.02 280);
  --neutral-700: oklch(30% 0.02 280);
  --neutral-800: oklch(20% 0.015 280);
  --neutral-900: oklch(12% 0.01 280);
}
```

### 3.4 Dimension Color System

> **중요**: Dimension/앱 목록은 **AppRegistry YAML**이 SSoT다.  
> 1D~15D 고정 체계를 사용하지 않고, 실제 `config/apps/content/dimensions/*.yaml`에서
> `app_id`를 읽어 색상 토큰을 자동 생성한다.

**Dimension/앱 색상은 다음 3요소로 표준화**

- **Hue**: 고정 (브랜드/기능 의미)
- **Lightness**: Light/Dark 모드별 기준값
- **Chroma**: 시각적 강도 균일화

```ts
// AppRegistry 기반 (예시). 실제 목록은 YAML에서 동기화.
const APP_IDS = [
  "1D", "2D", "3D", "4D",
  "STORY", "STORYBOARD", "PROMPT", "CHARACTER",
  "VEO", "KLING", "SUNO", "SOUND",
  "QC", "AI", "AD", "JSON", "MIRROR"
];

const APP_COLORS = {
  "1D":  { hue: 240, chroma: 0.14, L: { light: 0.48, dark: 0.62 } },
  "2D":  { hue: 45,  chroma: 0.18, L: { light: 0.52, dark: 0.64 } },
  "3D":  { hue: 290, chroma: 0.20, L: { light: 0.50, dark: 0.66 } },
  "4D":  { hue: 200, chroma: 0.16, L: { light: 0.50, dark: 0.62 } },
  "VEO": { hue: 210, chroma: 0.18, L: { light: 0.52, dark: 0.66 } },
  "KLING": { hue: 160, chroma: 0.18, L: { light: 0.50, dark: 0.64 } },
  // ... 기타 앱은 동일 규칙으로 확장
};

const appColor = (appId, theme) => {
  const d = APP_COLORS[appId];
  return `oklch(${d.L[theme]} ${d.chroma} ${d.hue})`;
};
```

### 3.5 철학 기반 시스템 토큰 (필수)

**Evidence / Provenance**
- `--evidence-badge-bg`, `--evidence-badge-fg`
- `--provenance-border`, `--pattern-version-fg`

**Sealed Capsule**
- `--capsule-locked-bg`, `--capsule-locked-border`, `--capsule-lock-icon`

**Run State**
- `--run-idle`, `--run-loading`, `--run-streaming`, `--run-complete`, `--run-error`, `--run-cancelled`

**Credit/Cost**
- `--credit-ok`, `--credit-low`, `--credit-zero`, `--credit-pending`

---

## 4. Accessibility & User Preference 대응

### 4.1 WCAG 2.2 반영 사항

- **Focus Appearance**: 2px 이상 + 3:1 대비 포커스 링
- **Target Size**: 24x24 최소 터치/클릭 영역 확보
- **Dragging 대체**: drag UI는 키보드/버튼 대체 제공
- **Accessible Authentication**: 캡차/인증 흐름 대체 수단 확보
- **Focus Not Obscured (2.4.11/2.4.12)**: 포커스가 다른 레이어/오버레이에 가려지지 않도록 보장
- **Consistent Help (3.2.6)**: 도움말/지원 위치 일관성 유지
- **Redundant Entry (3.3.7)**: 동일 정보 재입력 최소화

### 4.2 CSS User Preference 대응

```css
:root {
  color-scheme: light dark;
}

@media (prefers-contrast: more) {
  /* 고대비 모드에서 테두리/텍스트 대비 강화 */
}

@media (forced-colors: active) {
  /* 시스템 색상 기반으로 최소 스타일 */
  /* 필요 시에만 forced-color-adjust: none 사용 */
  * { forced-color-adjust: auto; }
}

@media (prefers-reduced-transparency: reduce) {
  /* glass/blur 효과 최소화 */
  .glass-card { backdrop-filter: none; background: var(--bg-muted); }
}
```

---

## 5. Liquid Glass → “Adaptive Glass” 시스템

**핵심 변화**: 정적 Glass → 환경/선호도/모드에 반응하는 Adaptive Glass

```css
:root {
  --glass-bg: rgba(255, 255, 255, 0.7);
  --glass-blur: 16px;
  --glass-saturate: 180%;
  --glass-border: rgba(255, 255, 255, 0.3);
}

[data-theme="dark"] {
  --glass-bg: rgba(30, 30, 46, 0.6);
  --glass-blur: 20px;
  --glass-saturate: 150%;
  --glass-border: rgba(148, 163, 184, 0.15);
}

@media (prefers-reduced-transparency: reduce) {
  :root {
    --glass-bg: var(--bg-muted);
    --glass-blur: 0px;
    --glass-saturate: 100%;
  }
}
```

### 5.1 배포 안정성 가드레일 (성능 리스크 최소화)

Adaptive Glass는 **표준 기능**이지만, `blur/backdrop-filter`는 GPU 리소스를 많이 사용하는 편입니다.  
**따라서 아래 가드레일을 지키면 배포 시 버벅임 리스크를 크게 낮출 수 있습니다.**

**권장 가드레일**
1. **면적/개수 제한**: 화면 전체 blur 금지, 카드/패널 단위로 제한
2. **애니메이션 금지**: blur 값 자체를 애니메이션하지 않기
3. **Feature Query**: 지원 브라우저에서만 활성화
4. **User Preference 대응**: `prefers-reduced-transparency`에서 blur 해제
5. **저사양 테스트**: 모바일/저사양 노트북에서 스크롤 FPS 확인

```css
@supports (backdrop-filter: blur(8px)) {
  .glass-card { backdrop-filter: blur(var(--glass-blur)); }
}

@media (prefers-reduced-transparency: reduce) {
  .glass-card { backdrop-filter: none; background: var(--bg-muted); }
}
```

---

## 6. Token Pipeline (Design → Code)

### 6.1 DTCG JSON 구조 (예시)

```json
{
  "color": {
    "neutral": {
      "0": {
        "$type": "color",
        "$value": { "colorSpace": "oklch", "components": [1, 0, 0], "alpha": 1 }
      }
    },
    "brand": {
      "primary": {
        "$type": "color",
        "$value": "{color.purple.500}"
      }
    }
  },
  "spacing": {
    "md": { "$type": "dimension", "$value": { "value": 16, "unit": "px" } }
  }
}
```

### 6.2 파일 구조 (권장)

```
/tokens
  tokens.base.json
  tokens.theme.light.json
  tokens.theme.dark.json
  tokens.theme.high-contrast.json
```

### 6.3 Figma Variables 연동

- DTCG JSON 파일을 Figma Variables로 import
- 각 JSON 파일은 **Mode**로 매핑
- Figma → repo tokens → Style Dictionary → CSS/TS 생성

---

## 7. 컴포넌트 레벨 가이드

### 7.1 버튼

```css
.btn-primary {
  background: var(--interactive-default);
  color: var(--fg-on-emphasis);
  border-radius: var(--radius-md);
  min-height: 44px; /* Target Size 확보 */
  transition: transform 150ms ease, box-shadow 150ms ease;
}

.btn-primary:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}
```

### 7.2 카드

```css
.card {
  background: var(--bg-subtle);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}
```

### 7.3 입력 필드

```css
.input {
  background: var(--bg-base);
  border: 1px solid var(--border-default);
  min-height: 44px;
}

.input:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}
```

### 7.4 Evidence Badge / Provenance

```css
.evidence-badge {
  background: var(--evidence-badge-bg);
  color: var(--evidence-badge-fg);
  border: 1px solid var(--provenance-border);
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 999px;
}
```

### 7.5 Sealed Capsule (Locked State)

```css
.capsule-locked {
  background: var(--capsule-locked-bg);
  border: 1px solid var(--capsule-locked-border);
  opacity: 0.85;
}
```

### 7.6 Run State / Credits

```css
.run-state.loading { color: var(--run-loading); }
.run-state.streaming { color: var(--run-streaming); }
.run-state.error { color: var(--run-error); }
.credit-chip.low { color: var(--credit-low); }
.credit-chip.zero { color: var(--credit-zero); }
```

---

## 8. 실행 로드맵 (4주)

### Phase 0 (2~3일) — 철학 정합성 패치
- Evidence/Sealed/Credit/Run-State 토큰 및 컴포넌트 정의
- AppRegistry 기반 Dimension 색상 스키마로 재정렬

### Phase 1 (1주) — Token 구조 재정비
- DTCG JSON 기반 토큰 구조 전환
- Global/Alias/Component 계층 재정립

### Phase 2 (1주) — Theme & Preference 대응
- Light/Dark/High-Contrast 모드 구축
- `color-scheme`, `prefers-contrast`, `forced-colors` 대응

### Phase 3 (1주) — Component Refresh
- Button, Card, Input, Panel 리디자인
- Focus/Target Size 표준 적용

### Phase 4 (1주) — QA & Accessibility
- WCAG 2.2 체크리스트 테스트
- 대비/포커스/키보드 접근성 검증

---

## 9. 참고 표준/문서 (2026 최신)

- W3C Design Tokens Community Group (2025.10 안정판)
  - https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/
  - https://www.designtokens.org/tr/2025.10/
- CSS Color Module Level 4 (OKLCH/OKLAB)
  - https://www.w3.org/TR/css-color-4/
- WCAG 2.2 (W3C Recommendation)
  - https://www.w3.org/TR/WCAG22/
- CSS Color Adjustment Module Level 1 (`color-scheme`, `forced-colors`)
  - https://www.w3.org/TR/css-color-adjust-1/
- Media Queries Level 5 (`prefers-contrast`, `forced-colors`, `prefers-reduced-transparency`)
  - https://www.w3.org/TR/mediaqueries-5/
- Figma Variables & DTCG import 가이드
  - https://help.figma.com/hc/en-us/articles/15343816063383-Modes-for-variables
- Fluent 2 Design Tokens / Color Tokens
  - https://fluent2.microsoft.design/design-tokens
  - https://fluent2.microsoft.design/color-tokens/
- Crebit SSoT (내부)
  - `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
  - `08_PIPELINES_AND_USER_FLOWS.md`
  - `10_UI_DESIGN_GUIDE_2025-12.md`
  - `docs/DIMENSION_APP_DEVELOPER_GUIDE.md`
  - `config/apps/content/dimensions/*.yaml`

---

## Appendix A: 2026 트렌드 (옵션, 비필수)

> 이 섹션은 **SSoT 우선순위가 아님**.  
> 철학/실행 UX를 해치지 않는 선에서 **선택적으로만 적용**한다.

### A.1 Bento Grid 레이아웃

2026년 UI 트렌드로 자주 언급되는 모듈형 그리드 패턴. 일본 도시락(벤토)에서 영감받은 레이아웃.
> **주의**: 표준/SSoT가 아니라 **옵션 패턴**이며, 적용 전 실사용 UX 검증이 필요.

```css
/* Bento Grid 기본 구현 */
.bento-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

/* Dimension 패널용 Bento */
.dimension-bento {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: repeat(2, 200px);
  gap: 16px;
}

.dimension-bento .featured {
  grid-column: span 2;
  grid-row: span 2;
}
```

**Crebit 적용**: Dimension 선택 화면에 Bento Grid 적용, 주요 Dimension(3D, 4D)은 큰 카드로 강조.

---

### A.2 Spatial Design / Depth Layers

2026년 웹은 2D → 2.5D로 진화. UI 요소가 z-axis에서 층위를 가지며 동적으로 반응.

```css
/* Depth Layer 시스템 */
:root {
  --layer-base: 0;
  --layer-raised: 1;
  --layer-overlay: 2;
  --layer-modal: 3;
}

.layer-raised {
  box-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.1),
    0 4px 8px rgba(0, 0, 0, 0.05);
}

/* 동적 패럴랙스 (마우스/스크롤 반응) */
.parallax-card:hover {
  transform: perspective(1000px) rotateX(2deg) rotateY(-2deg);
}

@media (prefers-reduced-motion: reduce) {
  .parallax-card { transform: none !important; }
}
```

---

### A.3 Variable Fonts + Kinetic Typography

```css
:root {
  --font-sans: 'Inter Variable', 'Pretendard Variable', system-ui;
}

/* 다크모드에서 약간 더 두꺼운 텍스트 (가독성) */
[data-theme="dark"] {
  --font-weight-normal: 420;
}

/* 호버 시 weight 전환 */
.interactive-text {
  font-variation-settings: 'wght' 400;
  transition: font-variation-settings 0.2s ease;
}
.interactive-text:hover {
  font-variation-settings: 'wght' 600;
}

/* Kinetic Hero 텍스트 */
.kinetic-hero {
  background: linear-gradient(90deg, var(--color-purple-500), var(--color-purple-300), var(--color-purple-500));
  background-size: 200% 100%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: shimmer 3s ease-in-out infinite;
}
```

---

### A.4 W3C DTCG 2025.10 토큰 스키마

```json
{
  "$schema": "https://design-tokens.github.io/community-group/format/",
  "color": {
    "neutral": {
      "900": {
        "$type": "color",
        "$value": "oklch(12% 0.008 300)"
      }
    }
  },
  "semantic": {
    "bg": {
      "base": {
        "$type": "color",
        "$value": "{color.neutral.0}",
        "$extensions": {
          "mode": { "dark": "{color.neutral.900}" }
        }
      }
    }
  }
}
```

핵심: `$type`, `$value`, `$extensions` (테마별 오버라이드)

---

### A.5 AI Creative Tool UI 패턴

| 원칙 | 설명 | 구현 |
|------|------|------|
| **Explainability** | AI 결과의 출처/근거 표시 | 인용 배지, 신뢰도 표시 |
| **Adaptability** | 사용자 숙련도에 따른 UI 조정 | Progressive disclosure |
| **Reliability** | 신뢰도 표시, 오류 처리 | 로딩 상태, 폴백 UI |

```css
/* AI 색상 관례: 보라색 그라디언트 */
.ai-accent {
  background: linear-gradient(135deg, #8B5CF6, #06B6D4);
}

/* AI 생성 콘텐츠 표시 */
.ai-generated::before {
  content: '✨';
  position: absolute;
  top: -8px;
  right: -8px;
}
```

> 주의: 포커스/선택 컬러는 `10_UI_DESIGN_GUIDE_2025-12.md` 규칙을 따른다.

---

## 결론

Crebit Studio 디자인 시스템은 **2026년 표준을 흡수한 토큰 중심 구조**로 개편될 준비가 되어 있습니다. 이 문서의 업그레이드를 적용하면:

- 디자인↔개발 간 토큰 동기화
- 다크/라이트/고대비의 체계적 대응
- WCAG 2.2 수준 접근성 확보
- **Evidence-first / Sealed Capsule / Credit-First** UX를 토큰/컴포넌트로 고정
- Chat-first + Flow-first 구조의 일관성 강화
- AppRegistry 기반 Dimension/앱 컬러 정합성 확보

을 동시에 달성할 수 있습니다.

---

*문서 업데이트: 2026-01-18*
