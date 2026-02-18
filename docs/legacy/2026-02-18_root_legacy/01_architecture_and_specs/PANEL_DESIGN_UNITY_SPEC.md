# Panel Design Unity SPEC

> **Date**: 2026-01-15 → **2026-01-16 (Complete)**
> **Version**: 1.1
> **Status**: ✅ IMPLEMENTATION COMPLETE
> **Phase**: Pre-Phase 0 (UX Foundation) → **Production Ready**
> **Prerequisites**: Phase -1 Design Tokens (Complete)

---

## 1. Executive Summary

### 1.1 Purpose

Panel Design Unity는 11개 Dimension Panel의 일관된 UX/UI를 구현하는 Compound Component System입니다.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Panel Design Unity Architecture                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    DimensionPanel (Root)                             │   │
│  │  • Context Provider (theme, state, callbacks)                        │   │
│  │  • Design Token Integration (tokens.ts SSoT)                         │   │
│  │  • Compound Component Pattern (2026 Best Practice)                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│           │                                                                 │
│           ├── Header ─────────────────────────────────────────────────────  │
│           │   • Title (with dimension color)                               │
│           │   • Credit Cost Badge                                          │
│           │   • Help Button                                                │
│           │                                                                 │
│           ├── Sidebar ────────────────────────────────────────────────────  │
│           │   • Input, Textarea, Select (unified styling)                  │
│           │   • FileUpload (wraps FileUploader)                            │
│           │   • GenerateButton (gradient + glow)                           │
│           │                                                                 │
│           ├── Content ────────────────────────────────────────────────────  │
│           │   • Result (glassmorphism card)                                │
│           │   • Evidence (wraps EvidenceDisplay)                           │
│           │   • Feedback (wraps FeedbackButtons)                           │
│           │   • NextNav (wraps NextDimensionNav)                           │
│           │                                                                 │
│           └── States ─────────────────────────────────────────────────────  │
│               • Loading (skeleton animation)                               │
│               • Error (red alert with retry)                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 2026 Architecture Patterns Applied

| Pattern | Source | Application |
|---------|--------|-------------|
| **Compound Components** | patterns.dev, Telerik 2025 | DimensionPanel + sub-components |
| **Design Tokens SSoT** | W3C DTCG 2025.10, Tailwind @theme | tokens.ts + globals.css |
| **Oklch Color Space** | CSS Color Level 4 | Perceptually uniform dimension colors |
| **Glassmorphism** | 2025-2026 UI Trends | backdrop-blur + transparency |
| **Context Provider** | React 19 | Theme and state sharing |
| **Container/Presentation** | React Best Practices | Logic separation |

### 1.3 Dependencies

| Dependency | Status | Location |
|------------|--------|----------|
| Design Tokens | ✅ Complete | `lib/tokens.ts`, `app/globals.css` |
| FeedbackButtons | ✅ Complete | `components/dimension/FeedbackButtons.tsx` |
| NextDimensionNav | ✅ Complete | `components/dimension/NextDimensionNav.tsx` |
| FileUploader | ✅ Complete | `components/dimension/FileUploader.tsx` |
| EvidenceDisplay | ✅ Complete | `components/dimension/EvidenceDisplay.tsx` |

---

## 2. Compound Component Architecture

### 2.1 Component Hierarchy

```typescript
// Usage Example
import { DimensionPanel } from '@/components/dimension/panel';

export default function AestheticDirectorPanel() {
  const [result, setResult] = useState(null);

  return (
    <DimensionPanel dimensionCode="ad">
      <DimensionPanel.Header
        title="Aesthetic Director"
        titleKo="미학 디렉터"
        creditCost={10}
      />

      <DimensionPanel.Sidebar>
        <DimensionPanel.Textarea
          label="Creative Concept"
          placeholder="Describe your vision..."
          name="concept"
        />
        <DimensionPanel.Select
          label="Style Mode"
          options={STYLE_OPTIONS}
          name="styleMode"
        />
        <DimensionPanel.GenerateButton onClick={handleGenerate}>
          Generate Aesthetic
        </DimensionPanel.GenerateButton>
      </DimensionPanel.Sidebar>

      <DimensionPanel.Content>
        {isLoading && <DimensionPanel.Loading />}
        {error && <DimensionPanel.Error error={error} onRetry={handleRetry} />}
        {result && (
          <>
            <DimensionPanel.Result responseId={result.id}>
              <AestheticResultDisplay data={result} />
            </DimensionPanel.Result>
            <DimensionPanel.Evidence refs={result.evidence_refs} />
            <DimensionPanel.Feedback responseId={result.id} />
            <DimensionPanel.NextNav show={true} />
          </>
        )}
      </DimensionPanel.Content>
    </DimensionPanel>
  );
}
```

### 2.2 Context Structure (React 19 Optimized)

> **React 19 Updates Applied:**
> - `use()` API for conditional context reading
> - Simplified `<Context>` syntax (no `.Provider`)
> - "use client" directive for Client Components

```typescript
// DimensionPanelContext.tsx
"use client";

import { createContext, use, useState, useMemo, type ReactNode } from 'react';
import {
  type DimensionCode,
  type ThemeColor,
  type DimensionToken,
  type ThemeColorClasses,
  getDimensionToken,
  getDimensionThemeClasses,
  getDimensionGradient,
  getDimensionGlow,
  getDimensionGlassStyle,
  getDimensionInputStyle,
} from '@/lib/tokens';

interface DimensionPanelContextValue {
  // Token Integration
  dimensionCode: DimensionCode;
  themeColor: ThemeColor;
  token: DimensionToken;
  classes: ThemeColorClasses;

  // Style Utilities (React 19 - memoized)
  styles: {
    gradient: string;
    glow: string;
    glowSm: string;
    glowLg: string;
    glass: string;
    input: string;
  };

  // State Management
  isLoading: boolean;
  setLoading: (loading: boolean) => void;
  error: Error | null;
  setError: (error: Error | null) => void;
  result: unknown;
  setResult: (result: unknown) => void;

  // Computed
  hasResult: boolean;
}

const DimensionPanelContext = createContext<DimensionPanelContextValue | null>(null);

/**
 * Hook to access DimensionPanel context
 * React 19: Uses use() API for conditional reading capability
 */
export function useDimensionPanel() {
  const context = use(DimensionPanelContext);
  if (!context) {
    throw new Error('useDimensionPanel must be used within DimensionPanel');
  }
  return context;
}

/**
 * Optional hook - returns null if outside provider (no throw)
 */
export function useDimensionPanelOptional() {
  return use(DimensionPanelContext);
}

export function DimensionPanelProvider({
  dimensionCode,
  children
}: {
  dimensionCode: DimensionCode;
  children: ReactNode;
}) {
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<unknown>(null);

  const token = getDimensionToken(dimensionCode);
  const classes = getDimensionThemeClasses(dimensionCode);

  // Memoize style utilities to prevent re-computation
  const styles = useMemo(() => ({
    gradient: getDimensionGradient(dimensionCode),
    glow: getDimensionGlow(dimensionCode, 'md'),
    glowSm: getDimensionGlow(dimensionCode, 'sm'),
    glowLg: getDimensionGlow(dimensionCode, 'lg'),
    glass: getDimensionGlassStyle(dimensionCode),
    input: getDimensionInputStyle(dimensionCode),
  }), [dimensionCode]);

  // Memoize context value to prevent unnecessary re-renders
  const value = useMemo<DimensionPanelContextValue>(() => ({
    dimensionCode,
    themeColor: token.themeColor,
    token,
    classes,
    styles,
    isLoading,
    setLoading,
    error,
    setError,
    result,
    setResult,
    hasResult: result !== null,
  }), [dimensionCode, token, classes, styles, isLoading, error, result]);

  // React 19: Direct Context usage without .Provider
  return (
    <DimensionPanelContext value={value}>
      {children}
    </DimensionPanelContext>
  );
}
```

### 2.3 Sub-Component API Specification

#### DimensionPanel.Header

```typescript
interface DimensionPanelHeaderProps {
  /** Panel title */
  title: string;
  /** Korean title (optional) */
  titleKo?: string;
  /** Credit cost to display */
  creditCost?: number;
  /** Help content for modal */
  helpContent?: React.ReactNode;
  /** Additional actions slot */
  actions?: React.ReactNode;
}
```

#### DimensionPanel.Input / Textarea

```typescript
interface DimensionPanelInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Field label */
  label: string;
  /** Error message */
  error?: string;
  /** Helper text below input */
  helperText?: string;
  /** Show character count */
  showCount?: boolean;
  /** Max characters */
  maxLength?: number;
}

interface DimensionPanelTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /** Field label */
  label: string;
  /** Error message */
  error?: string;
  /** Helper text below input */
  helperText?: string;
  /** Show character count */
  showCount?: boolean;
  /** Max characters */
  maxLength?: number;
  /** Auto-resize height */
  autoResize?: boolean;
}
```

#### DimensionPanel.Select

```typescript
interface SelectOption {
  value: string;
  label: string;
  description?: string;
}

interface DimensionPanelSelectProps {
  /** Field label */
  label: string;
  /** Options to display */
  options: SelectOption[];
  /** Current value */
  value?: string;
  /** Change handler */
  onChange?: (value: string) => void;
  /** Error message */
  error?: string;
  /** Placeholder */
  placeholder?: string;
}
```

#### DimensionPanel.GenerateButton

```typescript
interface DimensionPanelGenerateButtonProps {
  /** Click handler */
  onClick: () => void | Promise<void>;
  /** Loading state (auto-detected from context if not provided) */
  loading?: boolean;
  /** Disabled state */
  disabled?: boolean;
  /** Button text */
  children?: React.ReactNode;
  /** Credit cost to show */
  creditCost?: number;
}
```

#### DimensionPanel.Result

```typescript
interface DimensionPanelResultProps {
  /** Result content */
  children: React.ReactNode;
  /** Response ID for feedback tracking */
  responseId?: string;
  /** Custom className */
  className?: string;
}
```

#### DimensionPanel.Loading / Error

```typescript
interface DimensionPanelLoadingProps {
  /** Loading message */
  message?: string;
  /** Show progress indicator */
  progress?: number;
}

interface DimensionPanelErrorProps {
  /** Error object or message */
  error: Error | string;
  /** Retry handler */
  onRetry?: () => void;
  /** Dismiss handler */
  onDismiss?: () => void;
}
```

---

## 3. Design Token Integration

### 3.1 Existing Tokens (Phase -1)

```typescript
// lib/tokens.ts - Already implemented
export const DIMENSION_TOKENS: Record<DimensionCode, DimensionToken> = {
  "1d": { code: "1d", cssVar: "--color-dimension-1d", tailwindKey: "dimension-1d", ... },
  "2d": { code: "2d", cssVar: "--color-dimension-2d", tailwindKey: "dimension-2d", ... },
  // ... all 10 dimensions
};

export function getDimensionThemeClasses(code: DimensionCode): ThemeColorClasses {
  return {
    bg: `bg-${key}`,
    bgSubtle: `bg-${key}/10`,
    border: `border-${key}/20`,
    text: `text-${key}`,
    button: `bg-${key}/20 hover:bg-${key}/30 text-${key}`,
    buttonActive: `bg-${key} text-black dark:text-white`,
    glow: `shadow-[0_0_20px] shadow-${key}/30`,
  };
}
```

### 3.2 New Token Utilities (To Add)

```typescript
// lib/tokens.ts - New utilities for Panel Design Unity

/**
 * Get gradient classes for dimension buttons
 */
export function getDimensionGradient(code: DimensionCode): string {
  const gradients: Record<DimensionCode, string> = {
    "1d": "bg-gradient-to-r from-violet-500 to-purple-600",
    "2d": "bg-gradient-to-r from-cyan-500 to-teal-600",
    "3d": "bg-gradient-to-r from-emerald-500 to-green-600",
    "4d": "bg-gradient-to-r from-amber-500 to-orange-600",
    "ad": "bg-gradient-to-r from-rose-500 to-pink-600",
    "ai": "bg-gradient-to-r from-indigo-500 to-blue-600",
    "qc": "bg-gradient-to-r from-red-500 to-rose-600",
    "veo": "bg-gradient-to-r from-sky-500 to-blue-600",
    "story": "bg-gradient-to-r from-fuchsia-500 to-purple-600",
    "mirror": "bg-gradient-to-r from-purple-500 to-violet-600",
  };
  return gradients[code];
}

/**
 * Get glow shadow classes by size
 */
export function getDimensionGlow(code: DimensionCode, size: 'sm' | 'md' | 'lg' = 'md'): string {
  const key = DIMENSION_TOKENS[code].tailwindKey;
  const sizes = {
    sm: `shadow-[0_0_10px] shadow-${key}/20`,
    md: `shadow-[0_0_20px] shadow-${key}/30`,
    lg: `shadow-[0_0_30px] shadow-${key}/40`,
  };
  return sizes[size];
}

/**
 * Get glassmorphism panel classes
 */
export function getDimensionGlassStyle(code: DimensionCode): string {
  const key = DIMENSION_TOKENS[code].tailwindKey;
  return `bg-black/40 backdrop-blur-xl border border-${key}/20 rounded-2xl`;
}

/**
 * Get unified input classes
 */
export function getDimensionInputStyle(code: DimensionCode): string {
  const key = DIMENSION_TOKENS[code].tailwindKey;
  return `bg-white/5 border border-white/10 rounded-lg px-4 py-3
          text-white placeholder:text-white/40
          focus:border-${key}/50 focus:ring-1 focus:ring-${key}/30
          transition-colors duration-200`;
}
```

---

## 4. Unified Style Specification

### 4.1 Panel Container

> **⚠️ Accessibility Warning (Glassmorphism):**
> - Ensure text contrast meets WCAG 2.1 AA (4.5:1 for normal text)
> - Test on low-powered devices (backdrop-blur can cause performance issues)
> - Provide `prefers-reduced-motion` fallback for animations
> - Consider `prefers-contrast: high` media query for high contrast mode

```css
/* Glassmorphism Panel */
.dimension-panel {
  @apply bg-black/40 backdrop-blur-xl;
  @apply border border-white/10;
  @apply rounded-2xl;
  @apply p-6;
}

/* Reduced motion fallback */
@media (prefers-reduced-motion: reduce) {
  .dimension-panel {
    @apply backdrop-blur-none bg-black/80;
  }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .dimension-panel {
    @apply bg-black border-white/50;
  }
}

/* With dimension border */
.dimension-panel[data-dimension="ad"] {
  @apply border-dimension-ad/20;
}
```

### 4.2 Input Components

```css
/* Unified Input Style */
.dimension-input {
  @apply bg-white/5;
  @apply border border-white/10;
  @apply rounded-lg;
  @apply px-4 py-3;
  @apply text-white placeholder:text-white/40;
  @apply focus:outline-none focus:ring-1;
  @apply transition-colors duration-200;
}

/* Dimension-specific focus */
.dimension-input[data-dimension="ad"]:focus {
  @apply border-dimension-ad/50 ring-dimension-ad/30;
}
```

### 4.3 Generate Button

```css
/* Primary Generate Button */
.dimension-generate-button {
  @apply relative overflow-hidden;
  @apply px-6 py-3;
  @apply rounded-xl;
  @apply font-semibold;
  @apply text-white;
  @apply transition-all duration-300;
  @apply disabled:opacity-50 disabled:cursor-not-allowed;
}

/* Dimension-specific gradient + glow */
.dimension-generate-button[data-dimension="ad"] {
  @apply bg-gradient-to-r from-rose-500 to-pink-600;
  @apply shadow-[0_0_30px] shadow-dimension-ad/40;
  @apply hover:shadow-[0_0_40px] hover:shadow-dimension-ad/50;
  @apply hover:scale-[1.02];
}
```

### 4.4 Result Card

```css
/* Result Display Card */
.dimension-result-card {
  @apply bg-black/40 backdrop-blur-xl;
  @apply border border-white/10;
  @apply rounded-2xl;
  @apply p-6;
  @apply space-y-4;
}

/* With dimension accent */
.dimension-result-card[data-dimension="ad"] {
  @apply border-dimension-ad/20;
}
```

### 4.5 Loading State

```css
/* Skeleton Loading */
.dimension-skeleton {
  @apply animate-pulse;
  @apply bg-white/10;
  @apply rounded-lg;
}

/* Loading Spinner with dimension color */
.dimension-spinner[data-dimension="ad"] {
  @apply border-dimension-ad;
  @apply border-t-transparent;
}
```

### 4.6 Error State

```css
/* Error Alert */
.dimension-error {
  @apply bg-red-500/10;
  @apply border border-red-500/20;
  @apply rounded-xl;
  @apply p-4;
  @apply text-red-400;
}
```

---

## 5. File Structure

```
frontend/src/
├── components/
│   ├── dimension/
│   │   ├── panel/                          # NEW: Compound Component System
│   │   │   ├── index.ts                    # Barrel export
│   │   │   ├── DimensionPanel.tsx          # Root component
│   │   │   ├── DimensionPanelContext.tsx   # Context provider
│   │   │   ├── Header.tsx                  # Panel.Header
│   │   │   ├── Sidebar.tsx                 # Panel.Sidebar
│   │   │   ├── Content.tsx                 # Panel.Content
│   │   │   ├── Input.tsx                   # Panel.Input
│   │   │   ├── Textarea.tsx                # Panel.Textarea
│   │   │   ├── Select.tsx                  # Panel.Select
│   │   │   ├── FileUpload.tsx              # Panel.FileUpload (wrapper)
│   │   │   ├── GenerateButton.tsx          # Panel.GenerateButton
│   │   │   ├── ResultCard.tsx              # Panel.Result
│   │   │   ├── LoadingState.tsx            # Panel.Loading
│   │   │   ├── ErrorState.tsx              # Panel.Error
│   │   │   ├── EvidenceWrapper.tsx         # Panel.Evidence (wrapper)
│   │   │   ├── FeedbackWrapper.tsx         # Panel.Feedback (wrapper)
│   │   │   └── NextNavWrapper.tsx          # Panel.NextNav (wrapper)
│   │   ├── FeedbackButtons.tsx             # ✅ Existing
│   │   ├── FileUploader.tsx                # ✅ Existing
│   │   ├── NextDimensionNav.tsx            # ✅ Existing
│   │   └── EvidenceDisplay.tsx             # ✅ Existing
│   └── ui/
│       └── ValidationError.tsx             # ✅ Existing
├── lib/
│   └── tokens.ts                           # ✅ Existing + NEW utilities
└── hooks/
    └── useDimensionPanel.ts                # NEW: Panel state hook (optional)
```

**New Files**: 17 files
**Modified Files**: 1 file (tokens.ts)

---

## 6. Migration Strategy

### 6.1 Phase 1: Foundation (Day 1-2)

| Task | Output | Priority |
|------|--------|----------|
| Create DimensionPanelContext | `DimensionPanelContext.tsx` | P0 |
| Create DimensionPanel root | `DimensionPanel.tsx` | P0 |
| Create Header component | `Header.tsx` | P0 |
| Create Sidebar/Content | `Sidebar.tsx`, `Content.tsx` | P0 |
| Add token utilities | `tokens.ts` update | P0 |

### 6.2 Phase 2: Input Components (Day 2-3)

| Task | Output | Priority |
|------|--------|----------|
| Create Input component | `Input.tsx` | P0 |
| Create Textarea component | `Textarea.tsx` | P0 |
| Create Select component | `Select.tsx` | P1 |
| Create GenerateButton | `GenerateButton.tsx` | P0 |
| Create FileUpload wrapper | `FileUpload.tsx` | P1 |

### 6.3 Phase 3: Result Components (Day 3-4)

| Task | Output | Priority |
|------|--------|----------|
| Create ResultCard | `ResultCard.tsx` | P0 |
| Create LoadingState | `LoadingState.tsx` | P0 |
| Create ErrorState | `ErrorState.tsx` | P0 |
| Create wrapper components | Evidence, Feedback, NextNav | P1 |

### 6.4 Phase 4: Panel Migrations (Day 4-6)

**Migration Order** (by complexity):

1. **PromptGeneratorPanel** (simplest, validation)
2. **AestheticDirectorPanel** (reference implementation)
3. **VisualRealizerPanel** (file upload)
4. **SoundCrafterPanel** (audio specific)
5. **StoryArchitectPanel** (complex form)
6. **VeoVideoPanel** (video specific)
7. **QualityDirectorPanel** (analysis)
8. **StoryboardPanel** (multi-step)
9. **AbyssMirrorPanel** (reflection)
10. **ReferenceDecoderPanel** (decode)
11. **CreativeEditorPanel** (editing)

### 6.5 Phase 5: Testing & Polish (Day 7)

| Task | Output | Priority |
|------|--------|----------|
| Visual regression tests | Snapshot tests | P1 |
| E2E workflow tests | `e2e/panel-workflow.spec.ts` | P1 |
| Documentation | Storybook or README | P2 |

---

## 7. Migration Example

### 7.1 Before (Current)

```tsx
// AestheticDirectorPanel.tsx - BEFORE
export default function AestheticDirectorPanel() {
  const [concept, setConcept] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  return (
    <div className="bg-black/40 backdrop-blur-xl rounded-2xl p-6 border border-pink-500/20">
      {/* Header - custom implementation */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-pink-400">
          Aesthetic Director
        </h1>
        <span className="bg-pink-500/20 px-3 py-1 rounded-full text-sm">
          10 credits
        </span>
      </div>

      {/* Input - custom styling */}
      <textarea
        className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3
                   text-white placeholder:text-white/40 focus:border-pink-500/50"
        placeholder="Enter your concept..."
        value={concept}
        onChange={(e) => setConcept(e.target.value)}
      />

      {/* Button - custom gradient */}
      <button
        className="w-full mt-4 px-6 py-3 rounded-xl font-semibold
                   bg-gradient-to-r from-rose-500 to-pink-600
                   shadow-[0_0_30px] shadow-pink-500/40"
        onClick={handleGenerate}
        disabled={isLoading}
      >
        {isLoading ? 'Generating...' : 'Generate Aesthetic'}
      </button>

      {/* Result - custom card */}
      {result && (
        <div className="mt-6 bg-black/40 backdrop-blur-xl rounded-2xl p-6 border border-pink-500/20">
          <AestheticResultContent data={result} />
          <EvidenceDisplay refs={result.evidence_refs} />
          <FeedbackButtons responseId={result.id} />
          <NextDimensionNav currentDimension="aesthetic-director" />
        </div>
      )}

      {/* Error - custom styling */}
      {error && (
        <div className="mt-4 bg-red-500/10 border border-red-500/20 rounded-xl p-4">
          {error.message}
        </div>
      )}
    </div>
  );
}
```

### 7.2 After (Unified)

```tsx
// AestheticDirectorPanel.tsx - AFTER
import { DimensionPanel } from '@/components/dimension/panel';

export default function AestheticDirectorPanel() {
  const [concept, setConcept] = useState('');
  const { submitExplicit } = useFeedback();

  const handleGenerate = async () => {
    // Generation logic
  };

  return (
    <DimensionPanel dimensionCode="ad">
      <DimensionPanel.Header
        title="Aesthetic Director"
        titleKo="미학 디렉터"
        creditCost={10}
      />

      <DimensionPanel.Sidebar>
        <DimensionPanel.Textarea
          label="Creative Concept"
          placeholder="Enter your concept..."
          value={concept}
          onChange={(e) => setConcept(e.target.value)}
          maxLength={500}
          showCount
        />
        <DimensionPanel.GenerateButton onClick={handleGenerate}>
          Generate Aesthetic
        </DimensionPanel.GenerateButton>
      </DimensionPanel.Sidebar>

      <DimensionPanel.Content>
        <DimensionPanel.Loading message="Analyzing aesthetic vision..." />
        <DimensionPanel.Error onRetry={handleGenerate} />
        <DimensionPanel.Result>
          {(result) => <AestheticResultContent data={result} />}
        </DimensionPanel.Result>
        <DimensionPanel.Evidence />
        <DimensionPanel.Feedback />
        <DimensionPanel.NextNav />
      </DimensionPanel.Content>
    </DimensionPanel>
  );
}
```

---

## 8. Success Criteria

### 8.1 Implementation Checklist

| Criterion | Measurement | Target |
|-----------|-------------|--------|
| Compound Component System | Sub-component count | 14 components |
| Token Integration | Utility functions | 4 new functions |
| Panel Migrations | Panels using system | 11/11 |
| TypeScript | Strict mode errors | 0 |
| Build | `npm run build` | ✅ Pass |
| Lint | `npm run lint` | 0 new errors |

### 8.2 Visual Consistency Checklist

| Element | Specification | Check |
|---------|---------------|-------|
| Panel Container | `bg-black/40 backdrop-blur-xl rounded-2xl` | ☐ |
| Input Fields | `bg-white/5 border-white/10` + focus ring | ☐ |
| Generate Button | Dimension gradient + glow | ☐ |
| Result Card | Glassmorphism + dimension border | ☐ |
| Loading State | Skeleton + spinner | ☐ |
| Error State | Red alert + retry button | ☐ |

### 8.3 E2E Test Coverage

| Test Case | Description | Priority |
|-----------|-------------|----------|
| Panel Load | All panels render without error | P0 |
| Generate Flow | Input → Generate → Result display | P0 |
| Feedback Flow | Result → Feedback buttons work | P0 |
| Navigation Flow | NextDimensionNav transitions work | P0 |
| Error Recovery | Error display → Retry works | P1 |
| File Upload | FileUploader integration works | P1 |

---

## 9. Timeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Panel Design Unity Timeline (7 Days)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Day 1-2         Day 2-3         Day 4-5         Day 6          Day 7      │
│  ────────        ────────        ────────        ────────       ────────   │
│  Foundation      Input           Panel           Remaining      Testing    │
│  Components      Components      Migrations      Migrations     & Polish   │
│                                                                             │
│  • Context       • Input         • 1D Panel      • Story        • E2E      │
│  • Root          • Textarea      • AD Panel      • Sound        • Visual   │
│  • Header        • Select        • 3D Panel      • VEO          • Docs     │
│  • Sidebar       • Generate      • 4D Panel      • QC           │          │
│  • Content       • FileUpload    • AI Panel      • Storyboard   │          │
│  • Tokens        • Result        │               • Mirror       │          │
│                  • Loading       │               • Reference    │          │
│                  • Error         │               • Creative     │          │
│                                                                             │
│  ────────────────────────────────────────────────────────────────────────── │
│                              Day 8: Gate Review                             │
│                              → Unlock P5-P8                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. References

### React 19 Official (2025)
- [React 19 Release Notes](https://react.dev/blog/2024/12/05/react-19) - Official React 19 features
- [React 19 use() API](https://www.telerik.com/blogs/react-context-new-use-api) - Conditional context reading
- [Server Components](https://react.dev/reference/rsc/server-components) - RSC architecture

### React Design Patterns (2025-2026)
- [React Design Patterns - Telerik](https://www.telerik.com/blogs/react-design-patterns-best-practices)
- [Compound Components - Refine](https://refine.dev/blog/react-design-patterns/)
- [React Stack Patterns - patterns.dev](https://www.patterns.dev/react/react-2026/)
- [Essential React Design Patterns - Trio Dev](https://trio.dev/essential-react-design-patterns/)

### Design Systems & Tokens
- [W3C Design Tokens Community Group](https://www.designtokens.org/)
- [Tailwind CSS @theme Guide](https://tailwindcss.com/docs/theme)
- [Design Tokens with Tailwind](https://nicolalazzari.ai/articles/integrating-design-tokens-with-tailwind-css)

### Component Libraries (Reference)
- [Radix UI](https://www.radix-ui.com/) - Headless primitives
- [shadcn/ui](https://ui.shadcn.com/) - Tailwind components
- [React Aria](https://react-spectrum.adobe.com/react-aria/) - Accessibility

---

*Document created: 2026-01-15*
*Status: READY FOR IMPLEMENTATION*
*Estimated Duration: 7 days*
