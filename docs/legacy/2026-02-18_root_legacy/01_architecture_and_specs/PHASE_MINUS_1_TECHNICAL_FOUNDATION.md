# Phase -1: Technical Foundation

> **Discovery Date**: 2026-01-15
> **Status**: CRITICAL - Must complete before Pre-Phase 0
> **Estimated Duration**: 1 Week
> **Priority**: P0 (Blocking)

---

## 1. Executive Summary

### 1.1 Discovery

Pre-Phase 0 (UX Foundation) 분석 중 **더 근본적인 기술 기반 부재**를 발견했습니다.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     REVISED ROADMAP HIERARCHY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Phase -1: Technical Foundation  ← YOU ARE HERE (NEW)                      │
│       │                                                                     │
│       ├── Testing Infrastructure                                            │
│       ├── CI/CD Pipeline                                                    │
│       ├── API Contract Validation                                           │
│       ├── Error Boundary System                                             │
│       └── Design Tokens Foundation                                          │
│                                                                             │
│       ▼                                                                     │
│                                                                             │
│   Pre-Phase 0: UX Foundation                                                │
│       │                                                                     │
│       ├── FileUploader ✅                                                   │
│       ├── FeedbackButtons ✅                                                │
│       ├── NextDimensionNav ✅                                               │
│       └── Panel Design Unity                                                │
│                                                                             │
│       ▼                                                                     │
│                                                                             │
│   P5-P8: Adaptive RAG Evolution                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Why Phase -1?

> **"UX Foundation 없이 UQSL 불가"** → **"Technical Foundation 없이 UX Foundation 불안정"**

| Risk | Without Phase -1 | With Phase -1 |
|------|------------------|---------------|
| 배포 실패 | 사후 발견 | CI에서 사전 차단 |
| API 계약 깨짐 | 런타임 에러 | 컴파일타임 + 런타임 검증 |
| 컴포넌트 회귀 | 수동 테스트 | 자동화 테스트 |
| UI 충돌 | 일관성 없음 | Design Token으로 통제 |
| 에러 화면 | 흰 화면 (WSOD) | Graceful Fallback |

### 1.3 Current Gap Analysis

| Category | Current State | Target State | Gap |
|----------|--------------|--------------|-----|
| **Unit Tests** | 2 files (sse-utils, agent-handlers) | 50+ files | 🔴 Critical |
| **CI/CD** | None (0 workflows) | GitHub Actions | 🔴 Critical |
| **API Validation** | Response types only | Request + Response Zod | 🟡 High |
| **Error Boundaries** | None standardized | React Error Boundary | 🟡 High |
| **Design Tokens** | Hardcoded Tailwind | @theme + CSS Variables | 🟡 Medium |
| **Test Script** | Only `test:e2e` | `test` (unit) + `test:e2e` | 🔴 Critical |

---

## 2. Research Sources (2025-2026)

### 2.1 API Contract Validation

> Sources: [tRPC Type-Safe Backend](https://thinhdanggroup.github.io/type-safe-backend-evolution/), [Zod v4 Docs](https://zod.dev/v4), [Full Stack TypeScript](https://stevekinney.com/courses/full-stack-typescript/zod-to-open-api)

**2026 Best Practice: "Define Once" Approach**

```typescript
// ❌ 현재 (2배 정의)
// api.ts - Response 타입만 정의
interface DimensionResponse {
  success: boolean;
  output: { ... };
}

// Panel에서 request 검증 없이 전송
const response = await api.dimension.generate1D({ topic, model });
```

```typescript
// ✅ Phase -1 목표 (한번 정의, 양방향 검증)
// schemas/dimension.ts
import { z } from 'zod';

export const Generate1DRequestSchema = z.object({
  topic: z.string().min(1).max(500),
  model: z.enum(['gemini-3-flash-preview', 'gemini-3-pro-preview']),
  style_mode: z.enum(['cinematic', 'documentary', 'commercial']).optional(),
});

export const Generate1DResponseSchema = z.object({
  success: z.boolean(),
  output: z.object({
    title: z.string(),
    premise: z.string(),
    keywords: z.array(z.string()),
    evidence_refs: z.array(z.string()).optional(),
  }),
});

// 타입 추론 자동
export type Generate1DRequest = z.infer<typeof Generate1DRequestSchema>;
export type Generate1DResponse = z.infer<typeof Generate1DResponseSchema>;
```

**Key Benefits**:
- 런타임 검증 + 컴파일타임 타입 안전
- 프론트엔드/백엔드 계약 동기화
- OpenAPI 스펙 자동 생성 가능

### 2.2 Testing Infrastructure

> Sources: [Vitest Component Testing](https://vitest.dev/guide/browser/component-testing), [React Testing Library Guide](https://blog.incubyte.co/blog/vitest-react-testing-library-guide/), [Best Practices 2026](https://trio.dev/best-practices-for-react-ui-testing/)

**2026 Best Practice: Vitest + RTL + Browser Mode**

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      exclude: ['node_modules/', 'src/test/', '**/*.d.ts'],
    },
    include: ['src/**/*.test.{ts,tsx}'],
  },
  resolve: {
    alias: { '@': '/src' },
  },
});
```

**Required Packages**:
```bash
npm install -D vitest @vitest/coverage-v8 @vitest/ui
npm install -D @testing-library/react @testing-library/jest-dom @testing-library/user-event
npm install -D jsdom
```

### 2.3 CI/CD Pipeline

> Sources: [Auto-Deploy Next.js Guide 2025](https://ayyaztech.com/blog/auto-deploy-nextjs-with-github-actions-complete-cicd-guide-2025/), [CI/CD Best Practices](https://dev.to/vishnusatheesh/how-to-set-up-a-cicd-pipeline-with-github-actions-for-automated-deployments-j39)

**2026 Best Practice: GitHub Actions Matrix**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - run: cd frontend && npm ci
      - run: cd frontend && npm run lint

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - run: cd frontend && npm ci
      - run: cd frontend && npm run test -- --coverage
      - uses: codecov/codecov-action@v4
        with:
          files: frontend/coverage/lcov.info

  build:
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - run: cd frontend && npm ci
      - run: cd frontend && npm run build

  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - run: cd backend && pip install -r requirements.txt
      - run: cd backend && pytest --tb=short -q
```

### 2.4 Error Boundary System

> Sources: [React Error Handling 2025](https://javascript.plainenglish.io/react-error-handling-2025-edition-onuncaughterror-boundaries-logging-ea7a679de22a), [Advanced Error Boundaries](https://johal.in/advanced-error-handling-with-react-error-boundaries-and-monitoring-2025/)

**2026 Best Practice: Layered Error Boundaries**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Error Boundary Hierarchy                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    GlobalErrorBoundary                               │   │
│  │  • Catches unhandled errors                                          │   │
│  │  • Reports to monitoring (Sentry)                                    │   │
│  │  • Shows "Something went wrong" page                                 │   │
│  │  └─────────────────────────────────────────────────────────────────┐ │   │
│  │    │                    LayoutErrorBoundary                        │ │   │
│  │    │  • Catches layout-level errors                                │ │   │
│  │    │  • Preserves navigation                                       │ │   │
│  │    │  └─────────────────────────────────────────────────────────┐  │ │   │
│  │    │    │                    PanelErrorBoundary                 │  │ │   │
│  │    │    │  • Catches individual panel errors                    │  │ │   │
│  │    │    │  • Shows retry button                                 │  │ │   │
│  │    │    │  • Isolates failures                                  │  │ │   │
│  │    │    │                                                       │  │ │   │
│  │    │    │    [Dimension Panel Content]                          │  │ │   │
│  │    │    │                                                       │  │ │   │
│  │    │    └───────────────────────────────────────────────────────┘  │ │   │
│  │    └───────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

```typescript
// components/ErrorBoundary.tsx
'use client';

import { Component, ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  level?: 'global' | 'layout' | 'panel';
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Report to monitoring
    this.props.onError?.(error, errorInfo);

    // Log with context
    console.error(`[${this.props.level || 'unknown'}] Error caught:`, error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="flex flex-col items-center justify-center p-8 text-center">
          <div className="text-red-400 mb-4">Something went wrong</div>
          <button
            onClick={this.handleRetry}
            className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg"
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### 2.5 Design Tokens System

> Sources: [Tailwind CSS 4 @theme Guide](https://medium.com/@sureshdotariya/tailwind-css-4-theme-the-future-of-design-tokens-at-2025-guide-48305a26af06), [Design Tokens with Tailwind](https://nicolalazzari.ai/articles/integrating-design-tokens-with-tailwind-css), [Typesafe Design Tokens](https://dev.to/wearethreebears/exploring-typesafe-design-tokens-in-tailwind-4-372d)

**2026 Best Practice: Tailwind @theme + CSS Variables**

```css
/* app.css - Design Tokens SSoT */
@import "tailwindcss";

@theme {
  /* Color Palette - Dimension Themes */
  --color-dimension-1d: oklch(0.75 0.18 275);      /* violet */
  --color-dimension-2d: oklch(0.75 0.15 170);      /* teal */
  --color-dimension-3d: oklch(0.75 0.17 145);      /* emerald */
  --color-dimension-4d: oklch(0.75 0.16 45);       /* amber */
  --color-dimension-ad: oklch(0.75 0.19 335);      /* pink */
  --color-dimension-ai: oklch(0.75 0.17 290);      /* indigo */
  --color-dimension-qc: oklch(0.75 0.18 15);       /* rose */
  --color-dimension-veo: oklch(0.75 0.15 220);     /* sky */

  /* Semantic Colors */
  --color-success: oklch(0.75 0.17 145);
  --color-warning: oklch(0.80 0.16 80);
  --color-error: oklch(0.70 0.20 25);
  --color-info: oklch(0.75 0.15 220);

  /* Spacing Scale */
  --spacing-panel: 1.5rem;
  --spacing-card: 1rem;
  --spacing-button: 0.75rem;

  /* Typography */
  --font-heading: 'Inter', system-ui, sans-serif;
  --font-body: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, monospace;

  /* Border Radius */
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-xl: 1rem;
  --radius-2xl: 1.5rem;

  /* Shadows */
  --shadow-glow-sm: 0 0 10px;
  --shadow-glow-md: 0 0 20px;
  --shadow-glow-lg: 0 0 30px;
}
```

```typescript
// lib/tokens.ts - TypeScript 타입 연동
export const dimensionThemes = {
  '1d': { key: 'dimension-1d', label: 'Violet' },
  '2d': { key: 'dimension-2d', label: 'Teal' },
  '3d': { key: 'dimension-3d', label: 'Emerald' },
  '4d': { key: 'dimension-4d', label: 'Amber' },
  'ad': { key: 'dimension-ad', label: 'Pink' },
  'ai': { key: 'dimension-ai', label: 'Indigo' },
  'qc': { key: 'dimension-qc', label: 'Rose' },
  'veo': { key: 'dimension-veo', label: 'Sky' },
} as const;

export type DimensionKey = keyof typeof dimensionThemes;
```

---

## 3. Implementation Plan

### 3.1 Day 1-2: Testing Infrastructure

| Task | Output | Priority |
|------|--------|----------|
| Install Vitest + RTL | `package.json` updated | 🔴 |
| Create `vitest.config.ts` | Config file | 🔴 |
| Create `src/test/setup.ts` | Test setup | 🔴 |
| Add `npm run test` script | `package.json` | 🔴 |
| Write 5 example tests | `*.test.ts` files | 🟡 |

**Files to Create**:
```
frontend/
├── vitest.config.ts
├── src/
│   └── test/
│       ├── setup.ts
│       └── mocks/
│           └── api.ts
├── src/components/dimension/
│   └── FeedbackButtons.test.tsx
├── src/hooks/
│   └── useFeedback.test.ts
└── src/lib/
    └── (existing tests)
```

### 3.2 Day 2-3: CI/CD Pipeline

| Task | Output | Priority |
|------|--------|----------|
| Create `.github/workflows/ci.yml` | CI workflow | 🔴 |
| Configure lint job | Lint on PR | 🔴 |
| Configure test job | Unit tests on PR | 🔴 |
| Configure build job | Build verification | 🔴 |
| Add backend pytest job | Backend tests | 🟡 |

**Files to Create**:
```
.github/
└── workflows/
    ├── ci.yml          # Main CI workflow
    └── preview.yml     # PR preview deployment (optional)
```

### 3.3 Day 3-4: API Contract Validation

| Task | Output | Priority |
|------|--------|----------|
| Create `schemas/` directory | Schema organization | 🟡 |
| Define Dimension request schemas | `schemas/dimension.ts` | 🟡 |
| Create validation hook | `useValidatedRequest.ts` | 🟡 |
| Integrate with api.ts | Type-safe requests | 🟡 |

**Files to Create**:
```
frontend/src/
├── schemas/
│   ├── index.ts
│   ├── dimension.ts
│   ├── agent.ts
│   └── credits.ts
└── hooks/
    └── useValidatedRequest.ts
```

### 3.4 Day 4-5: Error Boundary System

| Task | Output | Priority |
|------|--------|----------|
| Create ErrorBoundary component | `ErrorBoundary.tsx` | 🟡 |
| Create error fallback UI | `ErrorFallback.tsx` | 🟡 |
| Wrap layout with boundary | `layout.tsx` update | 🟡 |
| Add error logging utility | `lib/errorReporting.ts` | 🟡 |

**Files to Create**:
```
frontend/src/
├── components/
│   ├── ErrorBoundary.tsx
│   └── ErrorFallback.tsx
└── lib/
    └── errorReporting.ts
```

### 3.5 Day 5-6: Design Tokens Foundation

| Task | Output | Priority |
|------|--------|----------|
| Define @theme tokens | `app.css` update | 🟡 |
| Create tokens TypeScript | `lib/tokens.ts` | 🟡 |
| Document token usage | Comments/README | 🟡 |

---

## 4. Success Criteria

### 4.1 Phase -1 Gate

| Criterion | Measurement | Target |
|-----------|-------------|--------|
| Unit test runner | `npm run test` works | ✅ Pass |
| Test coverage | `vitest --coverage` | ≥ 30% |
| CI workflow | GitHub Actions green | ✅ Pass |
| Build verification | `npm run build` in CI | ✅ Pass |
| Zod schemas | 5+ endpoint schemas | ✅ Complete |
| Error boundary | Layout-level wrapper | ✅ Deployed |
| Design tokens | @theme defined | ✅ Defined |

### 4.2 Unlock Pre-Phase 0

Phase -1 완료 후 Pre-Phase 0 진입 가능:

```
Phase -1 Gate ✅
    │
    ├── Unit Tests: npm run test passes
    ├── CI: GitHub Actions green on main
    ├── Zod: Request validation in place
    ├── ErrorBoundary: Layout wrapped
    └── Tokens: @theme defined
    │
    ▼
Pre-Phase 0 Unlocked
    │
    ├── FileUploader ✅
    ├── FeedbackButtons ✅
    ├── NextDimensionNav ✅
    ├── Panel Design Unity
    └── E2E Tests
```

---

## 5. Risk Mitigation

### 5.1 Without Phase -1

| Scenario | Impact | Probability |
|----------|--------|-------------|
| Pre-Phase 0 컴포넌트 회귀 | 수동 테스트 필요, 지연 | High |
| API 계약 변경 미감지 | 런타임 에러, 사용자 영향 | High |
| 배포 후 빌드 실패 | 롤백 필요 | Medium |
| UI 충돌 시 디버깅 | 원인 파악 어려움 | High |

### 5.2 With Phase -1

| Mitigation | Benefit |
|------------|---------|
| 자동화 테스트 | 회귀 즉시 감지 |
| CI 빌드 검증 | 배포 전 실패 차단 |
| Zod 검증 | 계약 변경 컴파일타임 감지 |
| Error Boundary | Graceful degradation |
| Design Tokens | 일관된 UI 변경 |

---

## 6. Dependencies & Prerequisites

### 6.1 Already Available

| Item | Status | Notes |
|------|--------|-------|
| Zod v4.3.5 | ✅ Installed | Request schemas 미사용 |
| Tailwind v4 | ✅ Installed | @theme 미설정 |
| TypeScript strict | ✅ Enabled | Good foundation |
| Backend pytest | ✅ Working | ~60% coverage |

### 6.2 To Install

| Package | Purpose | Command |
|---------|---------|---------|
| vitest | Test runner | `npm i -D vitest` |
| @vitest/coverage-v8 | Coverage | `npm i -D @vitest/coverage-v8` |
| @vitest/ui | Test UI | `npm i -D @vitest/ui` |
| @testing-library/react | RTL | `npm i -D @testing-library/react` |
| @testing-library/jest-dom | DOM matchers | `npm i -D @testing-library/jest-dom` |
| @testing-library/user-event | User events | `npm i -D @testing-library/user-event` |
| jsdom | DOM environment | `npm i -D jsdom` |

---

## 7. Timeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Phase -1 Timeline (1 Week)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Day 1-2          Day 2-3          Day 3-4          Day 4-5          Day 6  │
│  ────────         ────────         ────────         ────────         ────── │
│  Vitest           CI/CD            Zod              Error            Review │
│  Setup            Pipeline         Schemas          Boundary         & Gate │
│                                                                             │
│  • Install        • ci.yml         • schemas/       • Component      • Test │
│  • Config         • lint job       • 5 endpoints    • Fallback UI    • CI   │
│  • Setup.ts       • test job       • Hook           • Layout wrap    • Docs │
│  • 5 tests        • build job      • api.ts         • Logging        │      │
│                                                                             │
│  ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│                              Day 7: Phase -1 Gate                           │
│                              → Unlock Pre-Phase 0                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Related Documents

| Document | Relationship |
|----------|--------------|
| `docs/PRE_PHASE_0_IMPLEMENTATION_SPEC.md` | Next phase after -1 |
| `docs/TESTING_GUIDE.md` | Testing standards |
| `docs/RAG_RELIABILITY.md` | Backend patterns |
| `docs/P5_P8_RAG_ROADMAP_SPEC.md` | Long-term roadmap |
| `frontend/CLAUDE.md` | Frontend conventions |

---

## 9. References

### Testing
- [Vitest Component Testing](https://vitest.dev/guide/browser/component-testing)
- [React Testing Library Guide](https://blog.incubyte.co/blog/vitest-react-testing-library-guide/)
- [Best Practices for React UI Testing 2026](https://trio.dev/best-practices-for-react-ui-testing/)

### API Contracts
- [Type-Safe Backend Evolution](https://thinhdanggroup.github.io/type-safe-backend-evolution/)
- [Zod v4 Documentation](https://zod.dev/v4)
- [Full Stack TypeScript](https://stevekinney.com/courses/full-stack-typescript/zod-to-open-api)

### CI/CD
- [Auto-Deploy Next.js Guide 2025](https://ayyaztech.com/blog/auto-deploy-nextjs-with-github-actions-complete-cicd-guide-2025/)
- [GitHub Actions Best Practices](https://dev.to/vishnusatheesh/how-to-set-up-a-cicd-pipeline-with-github-actions-for-automated-deployments-j39)

### Error Handling
- [React Error Handling 2025](https://javascript.plainenglish.io/react-error-handling-2025-edition-onuncaughterror-boundaries-logging-ea7a679de22a)
- [Advanced Error Boundaries](https://johal.in/advanced-error-handling-with-react-error-boundaries-and-monitoring-2025/)

### Design Tokens
- [Tailwind CSS 4 @theme Guide](https://medium.com/@sureshdotariya/tailwind-css-4-theme-the-future-of-design-tokens-at-2025-guide-48305a26af06)
- [Design Tokens with Tailwind](https://nicolalazzari.ai/articles/integrating-design-tokens-with-tailwind-css)

---

*Document created: 2026-01-15*
*Status: Ready for Implementation*
*Priority: BLOCKING - Must complete before Pre-Phase 0*
