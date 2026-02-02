# DNA Lab Design Brief V2

> **CRITICAL REVISION** - 이전 결과물의 문제점을 해결하기 위한 상세 브리프
>
> **Target URL**: https://www.prompty.co.kr/dna-lab?master=velvet&mode=quick
> **Deliverable**: HTML/CSS 단일 파일, Dark mode 기본

---

## ⚠️ MANDATORY REQUIREMENTS (위반 시 리젝)

### 1. Brand Color - MUST USE NEON RED

```css
/* ❌ WRONG - 이전 결과물 */
--primary: #00FFC2; /* Cyan - 사용 금지 */

/* ✅ CORRECT - 반드시 사용 */
--primary: #FF003C; /* Neon Red - Crebit Primary */
--primary-rgb: 255, 0, 60;
```

**Primary 버튼, 강조 요소, Glow 효과 모두 Neon Red 사용**

### 2. Dark Mode DEFAULT

```css
/* 배경은 반드시 어두운 색상 */
--bg-primary: #0a0a0a;   /* Near black */
--bg-secondary: #141414; /* Slightly lighter */
--bg-surface: #1a1a1a;   /* Card surface */

/* Light mode는 옵션, Dark mode가 기본 */
```

### 3. Credit Cost Display - MANDATORY

모든 액션 버튼에 크레딧 비용 표시:

```html
<!-- ✅ CORRECT -->
<button>Generate Analysis <span class="text-xs opacity-70">50 credits</span></button>

<!-- ❌ WRONG - 크레딧 없음 -->
<button>Run Analysis</button>
```

### 4. 3-Step Korean Labels - EXACT NAMES

| Step | English | Korean (필수) | Icon |
|------|---------|--------------|------|
| 1 | Analysis | **통합분석** | `analytics` |
| 2 | DNA | **창작DNA** | `psychology` |
| 3 | Quality | **품질검증** | `verified` |

**영어와 한글 병기 권장**: `통합분석 (Analysis)`

---

## 🎯 Quick Mode 특화 UX

### URL Parameter 해석

```
/dna-lab?master=velvet&mode=quick
         ↑              ↑
         │              └── 빠른 시작 모드 (온보딩 스킵)
         └── 선택된 거장: Velvet
```

### Quick Mode에서 보여야 할 화면

**이전 결과물 문제**: 실시간 분석 중인 화면을 보여줌 (잘못됨)

**올바른 화면**: Quick Start 진입점 - 사용자가 바로 시작할 수 있는 간소화된 온보딩

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                        DNA Lab                              │
│                   Quick Start Mode                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │    Selected Master: Velvet                          │   │
│  │    [Avatar] Ren Velvet • Cinematic Style           │   │
│  │                                                     │   │
│  │    ─────────────────────────────────────────────   │   │
│  │                                                     │   │
│  │    Video URL (Optional)                             │   │
│  │    [____________________________________]           │   │
│  │                                                     │   │
│  │    ─────────────────────────────────────────────   │   │
│  │                                                     │   │
│  │    [Start Analysis]  50 credits                     │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│           ○ ─────── ○ ─────── ○                            │
│         통합분석    창작DNA    품질검증                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📐 Layout Specification

### Option A: Centered Card (권장 - 미니멀)

```
┌─────────────────────────────────────────────────────────────┐
│  [Logo]                                    [Theme] [User]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    ┌───────────────────┐                    │
│                    │                   │                    │
│                    │   Quick Start     │                    │
│                    │   Card Content    │                    │
│                    │                   │                    │
│                    │   [CTA Button]    │                    │
│                    │                   │                    │
│                    └───────────────────┘                    │
│                                                             │
│              [Step 1] ── [Step 2] ── [Step 3]              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

- 중앙 정렬된 단일 카드
- 최대 너비: 480px
- 배경: Aurora gradient (optional) 또는 solid dark
- 하단: 3-step indicator (현재 단계 없음, 모두 pending)

### Option B: Split Layout (사이드바)

```
┌───────────────────┬─────────────────────────────────────────┐
│                   │                                         │
│   Sidebar         │         Main Content                    │
│   (Controls)      │         (Preview/Result)                │
│                   │                                         │
│   - Master        │         Empty State:                    │
│   - Input         │         "Start your DNA analysis"       │
│   - Options       │                                         │
│                   │                                         │
│   [Generate]      │         OR                              │
│   50 credits      │                                         │
│                   │         Result Cards                    │
│                   │                                         │
└───────────────────┴─────────────────────────────────────────┘
```

- 사이드바 너비: 320px (고정)
- 메인 영역: 유동적

---

## 🎨 Design Tokens (DevTools에서 확인 가능)

### Colors

```css
:root {
  /* Brand */
  --color-primary: #FF003C;
  --color-primary-hover: #E60036;
  --color-primary-glow: rgba(255, 0, 60, 0.4);

  /* DNA Lab Accent (Secondary) */
  --color-dna-lab: oklch(0.64 0.18 148); /* Cyan-green for accents only */

  /* Backgrounds - DARK MODE */
  --bg-0: #0a0a0a;
  --bg-1: #141414;
  --bg-2: #1a1a1a;
  --bg-3: #242424;

  /* Text */
  --text-primary: #ffffff;
  --text-secondary: #a1a1aa;
  --text-muted: #71717a;

  /* Borders */
  --border-default: rgba(255, 255, 255, 0.1);
  --border-hover: rgba(255, 255, 255, 0.2);

  /* Status */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
}
```

### Typography

```css
:root {
  --font-sans: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-display: 'Space Grotesk', var(--font-sans);

  /* Scale */
  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
  --text-3xl: 1.875rem;  /* 30px */
}
```

### Spacing

```css
:root {
  --space-1: 0.25rem;  /* 4px */
  --space-2: 0.5rem;   /* 8px */
  --space-3: 0.75rem;  /* 12px */
  --space-4: 1rem;     /* 16px */
  --space-6: 1.5rem;   /* 24px */
  --space-8: 2rem;     /* 32px */
  --space-12: 3rem;    /* 48px */
}
```

### Effects

```css
:root {
  /* Border Radius */
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-xl: 1rem;
  --radius-2xl: 1.5rem;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.5);
  --shadow-glow: 0 0 30px var(--color-primary-glow);

  /* Glass */
  --glass-bg: rgba(26, 26, 26, 0.8);
  --glass-border: rgba(255, 255, 255, 0.1);
  --glass-blur: blur(24px);
}
```

---

## 🧩 Component Specifications

### 1. Header (Minimal)

```html
<header class="h-16 flex items-center justify-between px-6 border-b border-white/10">
  <!-- Left: Logo -->
  <div class="flex items-center gap-2">
    <div class="w-8 h-8 bg-[#FF003C] rounded-lg flex items-center justify-center">
      <span class="text-white font-bold">C</span>
    </div>
    <span class="font-semibold text-white">Crebit</span>
  </div>

  <!-- Center: Page Title (optional) -->
  <span class="text-sm text-white/60">DNA Lab</span>

  <!-- Right: Actions -->
  <div class="flex items-center gap-2">
    <button class="p-2 rounded-lg hover:bg-white/5">🌙</button>
    <button class="p-2 rounded-lg hover:bg-white/5">⚙️</button>
  </div>
</header>
```

### 2. Master Selection Card

```html
<div class="p-4 rounded-xl bg-white/5 border border-white/10">
  <label class="text-xs font-semibold text-white/50 uppercase tracking-wider mb-3 block">
    Selected Master
  </label>
  <div class="flex items-center gap-3">
    <img src="velvet-avatar.jpg" class="w-12 h-12 rounded-full" />
    <div>
      <div class="font-medium text-white">Ren Velvet</div>
      <div class="text-xs text-white/50">v2.4 • Cinematic Style</div>
    </div>
    <button class="ml-auto text-white/40 hover:text-white">
      Change ▾
    </button>
  </div>
</div>
```

### 3. Input Area

```html
<div class="space-y-3">
  <label class="text-xs font-semibold text-white/50 uppercase tracking-wider">
    Video URL (Optional)
  </label>
  <div class="relative">
    <input
      type="text"
      placeholder="https://youtube.com/watch?v=..."
      class="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10
             text-white placeholder-white/30
             focus:border-[#FF003C] focus:ring-1 focus:ring-[#FF003C]/30"
    />
    <button class="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white">
      📎
    </button>
  </div>
  <p class="text-xs text-white/40">
    YouTube, Vimeo, or direct video URL supported
  </p>
</div>
```

### 4. Primary CTA Button (NEON RED)

```html
<button class="w-full py-4 rounded-xl
               bg-gradient-to-r from-[#FF003C] to-[#CC0030]
               text-white font-semibold
               hover:shadow-[0_0_30px_rgba(255,0,60,0.4)]
               transition-all duration-200
               flex items-center justify-center gap-3">
  <span>Start Analysis</span>
  <span class="text-sm opacity-70">50 credits</span>
</button>
```

### 5. Step Indicator (3-Step)

```html
<div class="flex items-center justify-center gap-4 py-6">
  <!-- Step 1: Current or Pending -->
  <div class="flex flex-col items-center gap-2">
    <div class="w-10 h-10 rounded-full bg-[#FF003C]/20 border-2 border-[#FF003C]
                flex items-center justify-center text-[#FF003C]">
      1
    </div>
    <span class="text-xs text-white">통합분석</span>
  </div>

  <!-- Connector -->
  <div class="w-12 h-px bg-white/20"></div>

  <!-- Step 2: Pending -->
  <div class="flex flex-col items-center gap-2 opacity-40">
    <div class="w-10 h-10 rounded-full bg-white/5 border border-white/20
                flex items-center justify-center text-white/50">
      2
    </div>
    <span class="text-xs text-white/50">창작DNA</span>
  </div>

  <!-- Connector -->
  <div class="w-12 h-px bg-white/20"></div>

  <!-- Step 3: Pending -->
  <div class="flex flex-col items-center gap-2 opacity-40">
    <div class="w-10 h-10 rounded-full bg-white/5 border border-white/20
                flex items-center justify-center text-white/50">
      3
    </div>
    <span class="text-xs text-white/50">품질검증</span>
  </div>
</div>
```

### 6. Evidence Badge (MANDATORY)

```html
<!-- Result 카드 하단에 반드시 포함 -->
<div class="mt-4 pt-4 border-t border-white/10">
  <div class="flex items-center gap-2 text-xs text-white/50">
    <span class="px-2 py-1 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
      📚 NotebookLM
    </span>
    <span class="px-2 py-1 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
      🔍 Qdrant RAG
    </span>
  </div>
</div>
```

### 7. Credit Balance (Header or Footer)

```html
<div class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10">
  <span class="text-sm">💰</span>
  <span class="text-sm font-medium text-white">1,250</span>
  <span class="text-xs text-white/50">credits</span>
</div>
```

---

## 🚫 DO NOT (금지사항)

| ❌ 금지 | ✅ 대신 |
|--------|--------|
| Cyan을 Primary로 사용 | Neon Red `#FF003C` |
| Light mode 기본 | **Dark mode 기본** |
| Credit 표시 생략 | 모든 버튼에 credit 표시 |
| 영어만 사용 | 한글 병기 (통합분석, 창작DNA, 품질검증) |
| 복잡한 대시보드 | 심플한 온보딩 카드 |
| 실시간 분석 화면 | Quick Start 진입점 |
| Evidence 생략 | 출처 배지 필수 포함 |

---

## ✅ DO (필수사항)

1. **Dark background**: `#0a0a0a` ~ `#1a1a1a`
2. **Neon Red CTA**: `#FF003C` with glow effect
3. **Korean labels**: 통합분석, 창작DNA, 품질검증
4. **Credit display**: "50 credits" on generate button
5. **Master pre-selected**: Velvet already chosen (from URL)
6. **Minimal UI**: One card, one action, one focus
7. **3-Step indicator**: Visual progress (all pending initially)
8. **Evidence placeholder**: Show where sources will appear

---

## 📱 Responsive Behavior

### Desktop (1024px+)
- Centered card layout
- Max-width: 480px for main card
- Step indicator below card

### Tablet (768px - 1023px)
- Same as desktop
- Slightly reduced padding

### Mobile (< 768px)
- Full-width card (with 16px margins)
- Step indicator: smaller dots, abbreviated labels
- Touch targets: minimum 44x44px

---

## 🎬 Interaction States

### Button States

```css
/* Default */
.btn-primary {
  background: linear-gradient(135deg, #FF003C, #CC0030);
  box-shadow: none;
}

/* Hover */
.btn-primary:hover {
  box-shadow: 0 0 30px rgba(255, 0, 60, 0.4);
  transform: translateY(-1px);
}

/* Active/Pressed */
.btn-primary:active {
  transform: translateY(0);
  box-shadow: 0 0 15px rgba(255, 0, 60, 0.3);
}

/* Disabled */
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}
```

### Input Focus

```css
.input:focus {
  border-color: #FF003C;
  box-shadow: 0 0 0 3px rgba(255, 0, 60, 0.1);
  outline: none;
}
```

### Card Hover

```css
.card:hover {
  border-color: rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.03);
}
```

---

## 📦 Deliverables Checklist

디자이너가 제출해야 할 항목:

- [ ] **HTML 파일**: 단일 파일, 외부 의존성 최소화
- [ ] **Dark mode 기본**: 배경 `#0a0a0a`
- [ ] **Neon Red Primary**: `#FF003C` 사용 확인
- [ ] **한글 라벨**: 통합분석, 창작DNA, 품질검증
- [ ] **Credit 표시**: Generate 버튼에 "50 credits"
- [ ] **Master 표시**: Velvet 선택됨 상태
- [ ] **3-Step indicator**: 하단 또는 상단
- [ ] **Evidence 영역**: placeholder 또는 예시
- [ ] **Responsive**: Mobile 뷰 포함
- [ ] **스크린샷**: Light/Dark 모드 모두 (Dark 우선)

---

## 🔗 Reference - Current Website Tokens

디자이너가 https://www.prompty.co.kr/dna-lab?master=velvet&mode=quick 에서 DevTools로 확인할 수 있는 CSS 변수:

```css
/* 실제 사이트에서 확인 가능 */
--color-mega-app-dna-lab: oklch(0.64 0.18 148);
--bg-0: #0a0a0a;
--radius-2xl: 1.5rem;
--glass-bg: rgba(0, 0, 0, 0.4);
```

---

## 📋 Summary: Key Changes from V1 Brief

| Aspect | V1 Brief | V2 Brief (이번) |
|--------|----------|----------------|
| Primary Color | 언급했지만 강조 부족 | **⚠️ MANDATORY** 섹션으로 최상단 배치 |
| Dark Mode | 권장 | **필수 (위반 시 리젝)** |
| Credits | 언급 | **모든 버튼에 필수 표시** |
| Korean Labels | 옵션 | **정확한 3개 명칭 명시** |
| Quick Mode UX | 설명 부족 | **정확한 화면 레이아웃 제공** |
| Evidence | 간략 언급 | **컴포넌트 코드 제공** |
| Checklist | 없음 | **제출 전 체크리스트 추가** |

---

**Document Version**: 2.0
**Last Updated**: 2026-01-31
**Revision Reason**: 이전 결과물이 브랜드 가이드라인 미준수 (Cyan 사용, Light mode, Credit 누락)
