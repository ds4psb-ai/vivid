# Pre-Phase 0: UX Foundation Implementation SPEC

> **Date**: 2026-01-15
> **Version**: 1.0
> **Status**: IN PROGRESS
> **Prerequisites**: P0-P6 RAG Phases (Completed)
> **Next**: P5-P8 Adaptive RAG Roadmap

---

## 1. Executive Summary

### 1.1 Purpose

Pre-Phase 0는 **UQSL(Universal Quality Selection Layer)** 및 **P5-P8 Adaptive RAG** 진행 전 필수 UX Foundation을 구축하는 단계입니다.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RAG Evolution Timeline                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  P0-P4 (Completed)        Pre-Phase 0         P5-P8 (Planned)              │
│  ─────────────────        ───────────         ───────────────              │
│  • Qdrant Sparse     →    • FileUploader  →   • Adaptive RAG               │
│  • Hybrid Search          • FeedbackButtons   • Thompson Sampling          │
│  • YAML Manifest          • NextDimensionNav  • Self-Correction            │
│  • Reranker Plugin        • Panel Unity       • Continual Learning         │
│                                                                             │
│  [Backend Focus]          [Frontend Focus]    [Full-Stack Evolution]       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Why Pre-Phase 0?

UQSL과 P5-P8의 핵심 가치는 **"사용자 피드백 기반 자동 진화"**입니다:

```
사용자 선택 → 데이터 축적 → Thompson Sampling → 자동 진화 → 더 나은 품질
```

이 루프를 실현하려면 **사용자가 피드백을 제출할 수 있는 UI**가 필수입니다.

### 1.3 Implementation Status

| Component | Status | File |
|-----------|--------|------|
| FileUploader | ✅ **완료** | `src/components/dimension/FileUploader.tsx` |
| FeedbackButtons | ✅ **완료** | `src/components/dimension/FeedbackButtons.tsx` |
| useFeedback Hook | ✅ **완료** | `src/hooks/useFeedback.ts` |
| NextDimensionNav | ✅ **완료** (11/11 패널) | `src/components/dimension/NextDimensionNav.tsx` |
| Panel Design Unity | 🔄 진행 예정 | Week 2 |
| E2E Testing | 🔄 진행 예정 | Week 2 |

---

## 2. 2025-2026 Architecture Patterns Reference

> Sources: [LangChain OSS](https://docs.langchain.com), [Qdrant Documentation](https://qdrant.tech/documentation), [AI UX Patterns](https://www.aiuxpatterns.com), [Vercel AI SDK](https://ai-sdk.dev)

### 2.1 Adaptive RAG Architecture (Latest)

2025-2026년 RAG 시스템의 핵심 트렌드:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Modern Adaptive RAG Architecture                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Query     │    │  Semantic   │    │  Retrieval  │    │  Response   │  │
│  │Classification│→→ │   Router    │→→ │  Strategy   │→→ │  Generation │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│        │                  │                  │                  │          │
│        ▼                  ▼                  ▼                  ▼          │
│  • Simple/Complex    • Skip RAG       • Dense+Sparse      • Streaming     │
│  • Domain Detection  • Single Source  • Multi-hop         • Token-by-token│
│  • Ambiguity Score   • Multi Source   • Reranking         • Tool Calling  │
│        │                  │                  │                  │          │
│        └──────────────────┴──────────────────┴──────────────────┘          │
│                                    │                                        │
│                         ┌─────────┴─────────┐                              │
│                         │  Feedback Loop    │                              │
│                         │  (Thompson/UCB)   │                              │
│                         └───────────────────┘                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Patterns**:

1. **Self-RAG**: 언어 모델이 "reflection" 토큰을 생성하여 검색 필요성 자체 판단
2. **Corrective RAG (CRAG)**: 검색 품질 평가기로 잘못된/모호한 정보 자동 필터링
3. **Agentic RAG**: 복잡한 추론을 위한 멀티 에이전트 오케스트레이션
4. **Auto-Adapt**: 청크 크기, top-k, 임베딩 모델 자동 튜닝

### 2.2 Hybrid Search Best Practices

**Qdrant RRF (Reciprocal Rank Fusion)** 패턴:

```python
# 2026 Best Practice: Prefetch + RRF Fusion
results = client.query_points(
    collection_name="{collection_name}",
    prefetch=[
        # Dense Vector (Semantic)
        models.Prefetch(
            query=models.Document(text=query, model="sentence-transformers/all-MiniLM-L6-v2"),
            using="dense_vector",
            limit=20
        ),
        # Sparse Vector (BM25)
        models.Prefetch(
            query=models.Document(text=query, model="Qdrant/bm25"),
            using="bm25_sparse_vector",
            limit=20
        )
    ],
    # Reranking with ColBERT or Cross-Encoder
    query=models.FusionQuery(fusion=models.Fusion.RRF),
    limit=10,
    with_payload=True
)
```

### 2.3 Thompson Sampling for LLM Quality Selection

**Multi-Armed Bandit 기반 품질 선택**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Thompson Sampling Selection Loop                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   User Query                                                                │
│       │                                                                     │
│       ▼                                                                     │
│   ┌───────────────────────────────────────────────────────────┐            │
│   │              Multi-Generate Engine (N candidates)          │            │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │            │
│   │  │ Arm A   │  │ Arm B   │  │ Arm C   │  │ Arm D   │       │            │
│   │  │β(α,β)   │  │β(α,β)   │  │β(α,β)   │  │β(α,β)   │       │            │
│   │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘       │            │
│   │       │            │            │            │             │            │
│   │       └────────────┴─────┬──────┴────────────┘             │            │
│   │                          │                                  │            │
│   │                    Sample θ ~ Beta(α, β)                   │            │
│   │                    Select arm with max θ                   │            │
│   └──────────────────────────┬─────────────────────────────────┘            │
│                              │                                              │
│                              ▼                                              │
│                    ┌─────────────────────┐                                 │
│                    │   Display Result    │                                 │
│                    │   + FeedbackButtons │←─── User selects thumbs up/down │
│                    └─────────────────────┘                                 │
│                              │                                              │
│                              ▼                                              │
│                    ┌─────────────────────┐                                 │
│                    │   Update Beta Dist  │                                 │
│                    │   α += reward       │                                 │
│                    │   β += (1-reward)   │                                 │
│                    └─────────────────────┘                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Implementation Note**: Thompson Sampling은 A/B 테스트보다 적은 샘플로 빠르게 수렴하며, 실시간 최적화에 적합합니다.

### 2.4 AI UX Design Patterns (2025-2026)

> Source: [AI UX Patterns](https://www.aiuxpatterns.com), [Shape of AI](https://www.shapeof.ai)

**핵심 UX 패턴**:

| Pattern | Description | Vivid Implementation |
|---------|-------------|---------------------|
| **Confidence Indicators** | AI 확신도 표시 (%, 바) | EvidenceDisplay 신뢰도 |
| **Chain-of-Thought Display** | AI 추론 과정 노출 | RAG evidence_refs |
| **Structured Feedback** | 세분화된 피드백 수집 | FeedbackButtons |
| **Graceful Degradation** | 오류 시 우아한 복구 | 재시도 버튼, fallback |
| **Human-Verified Badge** | AI vs 검증된 콘텐츠 구분 | 품질 배지 |
| **Predictive Assistance** | 다음 단계 제안 | NextDimensionNav |

**FeedbackButtons 설계 원칙**:

```
                    FeedbackButtons Component
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   ┌─────────┐  ┌─────────┐      ┌─────────────────────────┐    │
│   │  👍    │  │  👎    │      │  ⭐⭐⭐⭐⭐ (Optional)  │    │
│   │ Helpful │  │  Not   │      │     Rating Scale        │    │
│   └─────────┘  └─────────┘      └─────────────────────────┘    │
│                                                                 │
│   ┌───────────────────────────────────────────────────────┐    │
│   │  💬 "What could be improved?" (Optional)              │    │
│   │  [                                                  ] │    │
│   └───────────────────────────────────────────────────────┘    │
│                                                                 │
│   Design Principles:                                            │
│   • One-tap primary action (thumbs)                            │
│   • Progressive disclosure (rating → comment)                  │
│   • Optimistic UI update                                       │
│   • Fire-and-forget implicit tracking                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.5 Vercel AI SDK Streaming Patterns

> Source: [Vercel AI SDK](https://ai-sdk.dev), [Next.js AI Streaming](https://blog.logrocket.com/nextjs-vercel-ai-sdk-streaming/)

**2026 Production Pattern**:

```typescript
// Server Component with Streaming
import { streamText } from 'ai';
import { google } from '@ai-sdk/google';

// Route Handler (app/api/generate/route.ts)
export async function POST(req: Request) {
  const { prompt, ragContext } = await req.json();

  const result = await streamText({
    model: google('gemini-2.5-flash'),
    system: ragContext, // RAG 컨텍스트 주입
    prompt,
    // Tool calling for agentic behavior
    tools: {
      searchKnowledge: {
        description: 'Search the knowledge base',
        parameters: z.object({
          query: z.string(),
          dimension: z.enum(['AD', '3D', '4D', 'VEO']),
        }),
        execute: async ({ query, dimension }) => {
          return await hybridQuery(query, dimension);
        },
      },
    },
  });

  return result.toDataStreamResponse();
}

// Client Component with useChat
'use client';
import { useChat } from 'ai/react';

export function ChatInterface() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: '/api/generate',
    onFinish: (message) => {
      // Track implicit feedback (session completion)
      trackImplicit('session_end', { messageCount: messages.length });
    },
  });

  return (
    <>
      {messages.map((m) => (
        <Message key={m.id} {...m}>
          <FeedbackButtons
            responseId={m.id}
            compact
          />
        </Message>
      ))}
    </>
  );
}
```

---

## 3. Implementation Details

### 3.1 FileUploader.tsx (Completed)

**Location**: `src/components/dimension/FileUploader.tsx`

```typescript
export interface FileUploaderProps {
  /** 허용 파일 타입 - MIME types */
  accept: string[];
  /** 최대 파일 크기 (MB) */
  maxSizeMB: number;
  /** 업로드 콜백 */
  onUpload: (files: File[]) => void;
  /** 다중 파일 허용 */
  multiple?: boolean;
  /** 썸네일 미리보기 */
  preview?: boolean;
  /** 비활성화 */
  disabled?: boolean;
  /** 테마 색상 */
  themeColor?: ThemeColor;
  /** 라벨 텍스트 */
  label?: string;
  /** 도움말 텍스트 */
  helperText?: string;
}
```

**Features**:
- Drag & Drop 지원
- 파일 타입/크기 검증
- 이미지 썸네일 미리보기
- 테마 색상 연동
- 에러 메시지 표시

### 3.2 FeedbackButtons.tsx (Completed)

**Location**: `src/components/dimension/FeedbackButtons.tsx`

```typescript
export type FeedbackType = 'positive' | 'negative';

export interface FeedbackButtonsProps {
  /** P6 RAG Response ID */
  responseId: string;
  /** 피드백 콜백 */
  onFeedback?: (type: FeedbackType, rating?: number, comment?: string) => Promise<void>;
  /** 별점 표시 여부 */
  showRating?: boolean;
  /** 코멘트 입력 표시 여부 */
  showComment?: boolean;
  /** 비활성화 */
  disabled?: boolean;
  /** 간소화 모드 */
  compact?: boolean;
  /** 테마 색상 */
  themeColor?: ThemeColor;
  /** 초기 피드백 상태 */
  initialFeedback?: FeedbackType | null;
}
```

**P6 API Integration**:
- `POST /api/v1/rag/feedback/explicit` - 명시적 피드백
- `POST /api/v1/rag/feedback/implicit` - 암묵적 피드백 (fire-and-forget)

### 3.3 useFeedback.ts Hook (Completed)

**Location**: `src/hooks/useFeedback.ts`

```typescript
export type ImplicitEventType =
  | 'source_click'
  | 'text_copy'
  | 'query_reformulate'
  | 'session_end';

export interface UseFeedbackReturn {
  /** 명시적 피드백 제출 */
  submitExplicit: (
    type: FeedbackType,
    rating?: number,
    comment?: string
  ) => Promise<void>;
  /** 암묵적 피드백 추적 (fire-and-forget) */
  trackImplicit: (
    eventType: ImplicitEventType,
    metadata?: Record<string, unknown>
  ) => void;
  /** 제출 중 여부 */
  isSubmitting: boolean;
  /** 이미 제출했는지 */
  hasSubmitted: boolean;
  /** 피드백 타입 */
  feedbackType: FeedbackType | null;
  /** 에러 */
  error: Error | null;
}
```

### 3.4 NextDimensionNav Integration (Completed)

**11개 패널 통합 완료**:

| Panel | DIMENSION_KEY | Theme | Status |
|-------|---------------|-------|--------|
| StoryArchitectPanel | `story-architect` | indigo | ✅ |
| SoundCrafterPanel | `sound-crafter` | teal | ✅ |
| AestheticDirectorPanel | `aesthetic-director` | pink | ✅ |
| VisualRealizerPanel | `visual-realizer` | emerald | ✅ |
| PromptGeneratorPanel | `prompt-alchemy` | violet | ✅ |
| VeoVideoPanel | `video-maker` | sky | ✅ |
| QualityDirectorPanel | `quality-director` | rose | ✅ |
| StoryboardPanel | `storyboard` | cyan | ✅ |
| AbyssMirrorPanel | `abyss-mirror` | violet | ✅ |
| ReferenceDecoderPanel | `reference-decoder` | amber | ✅ |
| CreativeEditorPanel | `creative-editor` | rose | ✅ |

**Integration Pattern**:

```tsx
import NextDimensionNav from "./NextDimensionNav";

const DIMENSION_KEY = "aesthetic-director";
const THEME_COLOR: ThemeColor = "pink";

export default function AestheticDirectorPanel() {
  return (
    <TeachingPanelLayout>
      {/* Panel Content */}

      {/* Result Section */}
      {result && (
        <>
          <EvidenceDisplay refs={result.evidence_refs} />

          {/* Next Dimension Navigation */}
          <NextDimensionNav
            currentDimension={DIMENSION_KEY}
            show={true}
            themeColor={THEME_COLOR}
          />
        </>
      )}
    </TeachingPanelLayout>
  );
}
```

---

## 4. Week 2 Roadmap

### 4.1 Panel Design Unity

**목표**: 모든 Dimension Panel의 일관된 UX 패턴 적용

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Unified Panel Layout Structure                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Header Section                               │   │
│  │  • Tool Title                                                        │   │
│  │  • Credit Cost Badge                                                 │   │
│  │  • Help Button                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌───────────────────────┐  ┌─────────────────────────────────────────┐   │
│  │    Sidebar Section    │  │             Main Content                 │   │
│  │                       │  │                                          │   │
│  │  • Input Fields       │  │  ┌──────────────────────────────────┐   │   │
│  │  • File Upload Slot   │  │  │        Result Display            │   │   │
│  │  • Options            │  │  │                                  │   │   │
│  │  • Model Selector     │  │  │  • Generated Content             │   │   │
│  │  • Generate Button    │  │  │  • EvidenceDisplay               │   │   │
│  │                       │  │  │  • FeedbackButtons               │   │   │
│  │                       │  │  │  • NextDimensionNav              │   │   │
│  │                       │  │  └──────────────────────────────────┘   │   │
│  └───────────────────────┘  └─────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**통일 항목**:

| Item | Pattern | Implementation |
|------|---------|----------------|
| Button Style | Gradient + Glow | `bg-gradient-to-r shadow-[0_0_30px]` |
| Input Style | Dark glass | `bg-white/5 border-white/10` |
| Result Card | Blur backdrop | `bg-black/40 backdrop-blur-xl` |
| Loading State | Skeleton + Spinner | `OperationProgress` component |
| Error Display | Red alert box | `bg-red-500/10 border-red-500/20` |

### 4.2 E2E Testing Plan

**테스트 파일**: `e2e/dimension-workflow.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Dimension Workflow Tests', () => {
  test('Complete workflow: Aesthetic → Visual Realizer', async ({ page }) => {
    // 1. Navigate to Aesthetic Director
    await page.goto('/dimension/aesthetic');

    // 2. Fill input and generate
    await page.fill('[data-testid="concept-input"]', 'Cyberpunk city at night');
    await page.click('[data-testid="generate-button"]');

    // 3. Wait for result
    await expect(page.locator('[data-testid="result-card"]')).toBeVisible({ timeout: 30000 });

    // 4. Submit positive feedback
    await page.click('[data-testid="feedback-positive"]');
    await expect(page.locator('[data-testid="feedback-submitted"]')).toBeVisible();

    // 5. Navigate to next dimension
    await page.click('[data-testid="next-dimension-visual-realizer"]');
    await expect(page).toHaveURL('/dimension/visual-realizer');

    // 6. Verify chain data passed
    await expect(page.locator('[data-testid="chain-badge"]')).toContainText('aesthetic-director');
  });

  test('Feedback collection integrates with P6 API', async ({ page, request }) => {
    await page.goto('/dimension/aesthetic');
    // ... generate result

    // Submit feedback
    await page.click('[data-testid="feedback-negative"]');
    await page.fill('[data-testid="feedback-comment"]', 'Too generic');
    await page.click('[data-testid="feedback-submit"]');

    // Verify API was called (intercept)
    const response = await page.waitForResponse(
      (resp) => resp.url().includes('/api/v1/rag/feedback/explicit')
    );
    expect(response.status()).toBe(200);
  });

  test('File upload works with supported formats', async ({ page }) => {
    await page.goto('/dimension/visual-realizer');

    // Upload image
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.click('[data-testid="file-upload-button"]');
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles('tests/fixtures/sample-image.png');

    // Verify preview shown
    await expect(page.locator('[data-testid="file-preview"]')).toBeVisible();
  });
});
```

---

## 5. Integration with P5-P8 Roadmap

### 5.1 Pre-Phase 0 → P5 Transition

```
Pre-Phase 0 완료 조건:
├── FileUploader.tsx ✅
├── FeedbackButtons.tsx ✅
├── useFeedback.ts ✅
├── NextDimensionNav (11/11) ✅
├── Panel Design Unity 🔄
└── E2E Tests 🔄

         ▼

P5 Adaptive RAG 시작 조건:
├── QueryClassifier 구현
├── SemanticRouter 구현
├── Strategy Selector 구현
└── Skip Retrieval Logic
```

### 5.2 Feedback Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Feedback Collection Architecture                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Frontend                    Backend                    Database            │
│  ────────                    ───────                    ────────            │
│                                                                             │
│  FeedbackButtons             /feedback/explicit         rag_feedback        │
│       │                           │                          │              │
│       ├──────────────────────────→├─────────────────────────→│              │
│       │  {responseId,             │  INSERT INTO             │              │
│       │   feedbackType,           │  rag_feedback            │              │
│       │   rating, comment}        │                          │              │
│       │                           │                          │              │
│  useFeedback                 /feedback/implicit         rag_implicit        │
│       │                           │                          │              │
│       ├──────────────────────────→├─────────────────────────→│              │
│       │  {eventType,              │  INSERT INTO             │              │
│       │   metadata}               │  rag_implicit            │              │
│       │  (fire-and-forget)        │  (async)                 │              │
│                                                                             │
│                                   ▼                                         │
│                           P7 Self-Correction                                │
│                           (Weekly Cron Job)                                 │
│                                   │                                         │
│                    ┌──────────────┴──────────────┐                          │
│                    │  Aggregate Feedback         │                          │
│                    │  Tune Prompts               │                          │
│                    │  Update Thresholds          │                          │
│                    └─────────────────────────────┘                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Success Criteria

### 6.1 Pre-Phase 0 완료 기준

| Metric | Target | Measurement |
|--------|--------|-------------|
| 컴포넌트 구현 | 100% | FileUploader, FeedbackButtons, useFeedback |
| NextDimension 통합 | 11/11 panels | ✅ 완료 |
| 디자인 일관성 | 통과 | 디자인 리뷰 |
| E2E 테스트 | 100% 통과 | Playwright CI |
| 빌드 성공 | 0 errors | `npm run build` |

### 6.2 P5-P8 준비도

| Readiness | Status | Dependency |
|-----------|--------|------------|
| 피드백 수집 UI | ✅ Ready | FeedbackButtons |
| 피드백 API 연동 | ✅ Ready | useFeedback |
| 워크플로우 연결 | ✅ Ready | NextDimensionNav |
| 파일 입력 | ✅ Ready | FileUploader |
| Thompson Sampling UI | 🔄 P5에서 구현 | MultiGenerateDisplay |

---

## 7. Related Documents

| Document | Purpose |
|----------|---------|
| `docs/PRE_ROADMAP_ANALYSIS.md` | UQSL 분석 및 Gap 분석 |
| `docs/P5_P8_RAG_ROADMAP_SPEC.md` | Adaptive RAG 상세 SPEC |
| `docs/RAG_ARCHITECTURE.md` | 현재 RAG 아키텍처 |
| `docs/DIMENSION_APP_DEVELOPER_GUIDE.md` | Dimension 앱 개발 가이드 |

---

## 8. References & Sources

### Architecture & Patterns
- [RAG Architecture Explained 2025](https://orq.ai/blog/rag-architecture)
- [8 RAG Architectures You Should Know](https://humanloop.com/blog/rag-architectures)
- [LangChain OSS Python Documentation](https://docs.langchain.com/oss/python)
- [Qdrant Hybrid Search](https://qdrant.tech/documentation/concepts/hybrid-queries)

### Thompson Sampling & Bandits
- [Thompson Sampling for Smart AI Selection](https://sourcepilot.co/blog/2025/11/22/how-thompson-sampling-works)
- [Multi-Armed Bandits Meet LLMs (arXiv)](https://arxiv.org/html/2505.13355v1)
- [Stanford Tutorial on Thompson Sampling](https://web.stanford.edu/~bvr/pubs/TS_Tutorial.pdf)

### UX Patterns
- [AI UX Patterns](https://www.aiuxpatterns.com)
- [The Shape of AI](https://www.shapeof.ai)
- [20+ GenAI UX Patterns](https://uxdesign.cc/20-genai-ux-patterns-examples-and-implementation-tactics-5b1868b7d4a1)

### Streaming & SDK
- [Vercel AI SDK](https://ai-sdk.dev)
- [Real-time AI in Next.js](https://blog.logrocket.com/nextjs-vercel-ai-sdk-streaming/)
- [AI SDK Architecture Patterns](https://learnwebcraft.com/learn/ai/vercel-ai-sdk-advanced-guide)

---

*Document created: 2026-01-15*
*Last updated: 2026-01-15*
*Status: Week 1 Complete, Week 2 In Progress*
