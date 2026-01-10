# Vivid Frontend Components Guide

> **Version**: 1.0
> **Framework**: Next.js 16.1 + TypeScript + TailwindCSS
> **Package Manager**: npm

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Dimension Panel System](#2-dimension-panel-system)
3. [Shared Components](#3-shared-components)
4. [Hooks](#4-hooks)
5. [Creating New Dimension Panels](#5-creating-new-dimension-panels)

---

## 1. Architecture Overview

```
frontend/src/
├── app/                    # Next.js App Router pages
│   ├── dimension/          # Dimension hub + static routes
│   │   ├── page.tsx        # Dimension hub
│   │   └── */page.tsx      # Static dimension pages
│   ├── flow/               # Workflow (Train) pages
│   └── singularity/        # Template gallery
├── components/
│   ├── dimension/          # 10 Dimension panel components
│   ├── shared/             # Reusable UI components
│   ├── train/              # Train workflow UI
│   └── AgentChatAccordion.tsx  # Global chat component
├── hooks/                  # Custom React hooks
├── lib/                    # Utilities, API clients
└── contexts/              # React contexts (Credit, Theme)
```

---

## 2. Dimension Panel System

### 2.1 Core Layout: `DimensionPanelLayout`

All 10 dimension panels use a shared layout component that provides:
- **Split-pane UI**: Left sidebar (inputs) + Main content (results)
- **Theme system**: 8 color themes (violet, cyan, emerald, amber, rose, fuchsia, indigo, sky)
- **Credit display**: Shows user balance with link to top-up
- **BYOK integration**: "Bring Your Own Key" modal for API keys
- **Loading overlay**: With `OperationProgress` component

#### Props Interface

```typescript
interface TeachingPanelLayoutProps {
  title: string;                  // Panel title (e.g., "Veo 프롬프트 생성")
  sidebarContent: ReactNode;      // Input form JSX
  children: ReactNode;            // Result display JSX
  onBack?: () => void;            // Optional back handler
  isLoading?: boolean;            // Show loading overlay
  creditCost?: number;            // Cost displayed in sidebar
  themeColor?: ThemeColor;        // Theme: "violet" | "cyan" | ...

  // Progress tracking (optional, enhances UX)
  progress?: ProgressEvent | null;
  onCancel?: () => void;
  onRetry?: () => void;
  canRetry?: boolean;
  error?: string | null;
  retryCount?: number;
  maxRetries?: number;
}
```

#### Usage Example

```tsx
import TeachingPanelLayout, { useAsyncOperation, useResultExport } from "./DimensionPanelLayout";

export default function PromptGeneratorPanel() {
  const { isLoading, execute, data } = useAsyncOperation<Result>();

  return (
    <TeachingPanelLayout
      title="Veo 프롬프트 생성"
      themeColor="violet"
      sidebarContent={<InputForm onSubmit={execute} />}
      isLoading={isLoading}
    >
      {data ? <ResultDisplay result={data} /> : <EmptyState />}
    </TeachingPanelLayout>
  );
}
```

---

### 2.2 Theme System

8 predefined themes with consistent styling:

| Theme | Primary Color | Use Case |
|-------|---------------|----------|
| `violet` | Purple/Violet | 1D Prompt Generation |
| `cyan` | Cyan/Blue | 4D Reference Analysis |
| `emerald` | Green/Teal | 2D Storyboard |
| `amber` | Amber/Orange | 3D Image Generation |
| `rose` | Rose/Pink | QC Quality Check |
| `fuchsia` | Fuchsia/Purple | AD Aesthetic Director |
| `indigo` | Indigo/Violet | AI Persona Analysis |
| `sky` | Sky/Blue | VEO Video Generation |

Each theme provides:
- `accent`: Text color class
- `border`: Border color class
- `bg`: Background color class
- `glow`: Shadow effect class
- `gradient`: Gradient classes
- `button`: Button gradient classes
- `spinner`: Loading spinner colors

---

### 2.3 Dimension Panels (11 total, Creative Editor 포함)

| Panel | File | Theme | API Endpoint |
|-------|------|-------|--------------|
| Prompt Alchemy | `PromptGeneratorPanel.tsx` | violet | `/api/dimension/1d/generate` |
| Storyboard Sketch | `StoryboardPanel.tsx` | emerald | `/api/dimension/2d/create` |
| Visual Realizer | `VisualRealizerPanel.tsx` | amber | `/api/dimension/3d/generate` |
| Reference Decoder | `ReferenceDecoderPanel.tsx` | cyan | `/api/dimension/4d/analyze` |
| Quality Director | `QualityDirectorPanel.tsx` | rose | `/api/dimension/quality/check` |
| Creative Editor | `CreativeEditorPanel.tsx` | rose | `/api/dimension/quality/editor` |
| Aesthetic Director | `AestheticDirectorPanel.tsx` | fuchsia | `/api/dimension/aesthetic/direct` |
| Abyss Interpreter | `AbyssInterpreterPanel.tsx` | indigo | `/api/dimension/persona/analyze` |
| Video Maker | `VeoVideoPanel.tsx` | sky | `/api/dimension/veo/generate/stream` |
| Story Architect | `StoryArchitectPanel.tsx` | emerald | `/api/dimension/story/architect` |
| Sound Crafter | `SoundCrafterPanel.tsx` | rose | `/api/dimension/sound/craft` |

---

## 3. Shared Components

### 3.1 `OperationProgress`

Displays operation progress with cancel/retry actions.

```tsx
import OperationProgress from "@/components/shared/OperationProgress";

<OperationProgress
  progress={{ phase: "PROCESSING", percent: 50, message: "Generating..." }}
  isLoading={true}
  error={null}
  onCancel={() => controller.abort()}
  onRetry={() => execute()}
  canRetry={true}
  themeColor="violet"
  retryCount={1}
  maxRetries={3}
/>
```

### 3.2 `InsufficientCreditsModal`

Modal shown when user lacks credits for an operation.

```tsx
import InsufficientCreditsModal from "./InsufficientCreditsModal";

<InsufficientCreditsModal
  isOpen={showModal}
  onClose={() => setShowModal(false)}
  requiredCredits={10}
  currentBalance={5}
  onRetry={handleRetry}
/>
```

### 3.3 `BYOKSettingsModal`

Modal for setting up Bring-Your-Own-Key API access.

---

## 4. Hooks

### 4.1 `useAsyncOperation<T>`

Manages async API calls with progress, retry, and cancellation.

```tsx
const {
  isLoading,
  progress,
  error,
  data,
  execute,
  cancel,
  retry,
  canRetry,
  currentRetryCount,
} = useAsyncOperation<ResponseType>({
  onSuccess: (data) => console.log("Done:", data),
  onError: (err) => console.error("Failed:", err),
  retryCount: 3,
  retryDelay: 1000,
  nonRetryableErrors: ["400", "401", "402"],
});

// Execute API call
await execute(
  "http://localhost:8100/api/dimension/1d/generate",
  { topic: "도시 야경" },
  { "X-User-Id": "user123" }
);
```

### 4.2 `useResultExport`

Utilities for copying and exporting results.

```tsx
const { copyToClipboard, isCopied, exportJSON } = useResultExport();

copyToClipboard(prompt);  // Copy to clipboard with toast
exportJSON(result, "output.json");  // Download as JSON file
```

### 4.3 `useBYOK`

Manages Bring-Your-Own-Key state.

```tsx
const { byokKey, isBYOKEnabled, setBYOKKey, clearBYOKKey } = useBYOK();

// Get headers for API calls
import { getBYOKHeaders } from "@/hooks/useBYOK";
const headers = getBYOKHeaders(byokKey);
```

### 4.4 `useCreditContextOptional`

Access credit context (balance, loading state).

```tsx
const creditCtx = useCreditContextOptional();

if (!creditCtx?.hasEnoughCredits(10)) {
  setShowCreditModal(true);
}
```

---

## 5. Creating New Dimension Panels

### Step-by-Step Guide

1. **Create the component file**:
   ```bash
   touch frontend/src/components/dimension/NewDimensionPanel.tsx
   ```

2. **Use the template structure**:

```tsx
"use client";

import { useState, useCallback } from "react";
import TeachingPanelLayout, {
  type ThemeColor,
  useAsyncOperation,
  useResultExport,
} from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";

const CREDIT_COST = 5;
const THEME_COLOR: ThemeColor = "violet";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

interface Result {
  // Define your result type
  output: string;
}

export default function NewDimensionPanel() {
  // State
  const [inputValue, setInputValue] = useState("");
  const [showCreditModal, setShowCreditModal] = useState(false);

  // Hooks
  const { byokKey } = useBYOK();
  const creditCtx = useCreditContextOptional();
  const { copyToClipboard, isCopied } = useResultExport();

  const {
    isLoading,
    progress,
    error,
    data: result,
    execute,
    cancel,
    retry,
    canRetry,
  } = useAsyncOperation<{ success: boolean; output: Result }>({
    onSuccess: (data) => {
      if (data.success && !byokKey && creditCtx) {
        void creditCtx.refresh();
      }
    },
    onError: (err) => {
      if (err.message.includes("402")) {
        setShowCreditModal(true);
      }
    },
    retryCount: 3,
  });

  // Handlers
  const handleGenerate = useCallback(async () => {
    if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
      setShowCreditModal(true);
      return;
    }

    await execute(
      `${API_BASE}/api/dimension/your-endpoint`,
      { input: inputValue },
      getBYOKHeaders(byokKey)
    );
  }, [inputValue, byokKey, creditCtx, execute]);

  // Render
  const SidebarContent = (
    <div className="space-y-4">
      <input
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        placeholder="Enter input..."
        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white"
      />
      <button
        onClick={handleGenerate}
        disabled={isLoading || !inputValue}
        className="w-full py-4 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl"
      >
        Generate
      </button>
    </div>
  );

  return (
    <>
      <TeachingPanelLayout
        title="새 차원 앱"
        sidebarContent={SidebarContent}
        isLoading={isLoading}
        themeColor={THEME_COLOR}
        progress={progress}
        onCancel={cancel}
        onRetry={retry}
        canRetry={canRetry}
        error={error}
      >
        {result?.output ? (
          <div className="p-8 bg-black/40 rounded-2xl">
            <pre>{JSON.stringify(result.output, null, 2)}</pre>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-zinc-500">
            결과가 여기에 표시됩니다
          </div>
        )}
      </TeachingPanelLayout>

      <InsufficientCreditsModal
        isOpen={showCreditModal}
        onClose={() => setShowCreditModal(false)}
        requiredCredits={CREDIT_COST}
        currentBalance={creditCtx?.balance ?? 0}
        onRetry={handleGenerate}
      />
    </>
  );
}
```

3. **Register in the route**:
   - Add to `frontend/src/lib/dimension-theme.ts` (if using dynamic routing)
   - Or create a new page at `frontend/src/app/dimension/your-slug/page.tsx`

4. **Add to dimension list**:
   Update `DIMENSION_CAPSULES` in `backend/app/fixtures/dimension_capsules.py`

---

## Appendix: CSS Variables

The app uses CSS custom properties for theming:

```css
:root {
  --fg-muted: rgb(113, 113, 122);  /* zinc-500 */
  --bg-card: rgba(15, 15, 26, 0.6);
  --border-subtle: rgba(255, 255, 255, 0.1);
}
```

Custom scrollbar styling is provided via `.custom-scrollbar` utility class.
