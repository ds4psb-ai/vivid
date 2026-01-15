# Pre-Roadmap 분석: UQSL 구현 완료 리포트

> **분석 일자**: 2026-01-15 (최초) → **2026-01-16 (완료)**
> **분석 대상**: `UNIVERSAL_QUALITY_SELECTION_SSOT.md`
> **현재 상태**: ✅ **UQSL 전체 구현 완료** (124 테스트 통과)
> **결론**: 모든 Pre-Phase 요구사항 충족, Production Ready

---

## 🎉 Implementation Status: COMPLETE

> **2026-01-16 업데이트**: 모든 UQSL 구성요소가 구현 완료되었습니다!

| 구성요소 | 백엔드 | 프론트엔드 | 상태 |
|---------|-------|----------|------|
| 파일 첨부 | ✅ FileUpload API | ✅ FileUploader.tsx | ✅ Complete |
| 피드백 수집 | ✅ P6 API + UQSL API | ✅ FeedbackButtons.tsx | ✅ Complete |
| NextDimension | ✅ Context | ✅ NextDimensionNav.tsx | ✅ Complete |
| A/B 비교 | ✅ UQSL API | ✅ ABComparisonCard.tsx | ✅ Complete |
| Thompson Sampling | ✅ `app/uqsl/thompson_sampling.py` | ✅ useUQSL.ts | ✅ Complete |
| Multi-Generate | ✅ `app/uqsl/multi_generate.py` | ✅ MultiGenerateWrapper.tsx | ✅ Complete |
| Quality Evaluator | ✅ `app/uqsl/quality_evaluator.py` | ✅ QualityScorecard.tsx | ✅ Complete |
| Ensemble++ 3-Way | ✅ `app/uqsl/ensemble_plus_plus.py` | ✅ ThreeWayComparison.tsx | ✅ Complete |
| Cloud Integration | ✅ `app/uqsl/cloud_integration.py` | - | ✅ Complete |
| Panel Design Unity | - | ✅ DimensionPanel Compound | ✅ Complete |

**결과**: UQSL_SPEC.md.resolved 100% 구현 완료

---

## 1. Executive Summary

UQSL(Universal Quality Selection Layer) 문서는 **"사용자 피드백 기반 자동 진화 시스템"**을 설계합니다. 핵심 가치는:

```
사용자 선택 → 데이터 축적 → Thompson Sampling → 자동 진화 → 더 나은 품질 → 반복
```

**✅ 2026-01-16 기준 모든 구성요소 구현 완료!**

상세 구현 문서: [`docs/UQSL_IMPLEMENTATION_SPEC.md`](UQSL_IMPLEMENTATION_SPEC.md)

---

## 2. UQSL 문서 요구사항 분석

### 2.1 3-Tier Cost Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│        Tier 1: FREE (모든 사용자) - 비용: $0~2/월               │
├─────────────────────────────────────────────────────────────────┤
│  • A/B 비교 + 사용자 투표                                       │
│  • Thompson Sampling 자동 조정                                  │
│  • 규칙 기반 Quality Score                                      │
│  • 앙상블 결과 머지                                             │
│  → Cloud Run만 사용, LLM 호출 없음                              │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│     Tier 2: PREMIUM (구독 사용자) - 비용: $20~100/월            │
├─────────────────────────────────────────────────────────────────┤
│  • Multi-Generate (3개 생성)                                    │
│  • 거장 DNA 분석                                                │
│  • Query Classification (선택적)                                │
│  → LLM 호출 포함                                                │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│        Tier 3: DEV (개발자 전용) - 비용: $50~200/월             │
├─────────────────────────────────────────────────────────────────┤
│  • LLM-as-Judge (품질 평가)                                     │
│  • A/B/C 3-Way 앙상블                                           │
│  • 무제한 Multi-Generate                                        │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 핵심 구성요소

| 구성요소 | 역할 | 프론트엔드 필요 |
|---------|------|---------------|
| **Multi-Generate Engine** | 동일 프롬프트 N개 후보 생성 | ✅ N개 후보 표시 UI |
| **Quality Evaluator** | groundedness, relevance 등 평가 | ✅ 점수 시각화 |
| **Best Selector** | auto/hitl/hybrid/llm_judge 선택 | ✅ 비교 선택 UI |
| **Thompson Sampling** | Beta 분포 기반 가중치 자동 조정 | ✅ 피드백 버튼 |
| **Ensemble++ 3-Way** | A vs B vs A+B 비교 | ✅ 3개 결과 비교 UI |

### 2.3 문서의 암묵적 전제조건

UQSL 문서는 다음을 전제로 합니다 (명시되어 있지 않음):

1. **사용자가 결과를 비교할 수 있는 UI** 존재
2. **사용자가 피드백을 제출할 수 있는 버튼** 존재
3. **N개 후보를 표시할 수 있는 컴포넌트** 존재
4. **파일/이미지 입력이 가능한 인터페이스** 존재

현재 Vivid는 이 전제조건을 충족하지 않습니다.

---

## 3. 현재 구현 상태 vs UQSL 요구사항

### 3.1 백엔드 ✅ COMPLETE

| UQSL 요구사항 | Vivid 구현 | 상태 |
|--------------|-----------|------|
| P0-P5 RAG | `app/rag/*.py` | ✅ 완료 |
| Feedback API | `app/routers/rag_feedback.py` | ✅ P6 완료 |
| YAML Manifest | `app/rag/manifests/` (13개) | ✅ 완료 |
| Dimension API | `app/routers/dimension/` | ✅ 완료 |
| Thompson Sampling | `app/uqsl/thompson_sampling.py` (489 lines) | ✅ 완료 |
| Multi-Generate | `app/uqsl/multi_generate.py` (428 lines) | ✅ 완료 |
| Quality Evaluator | `app/uqsl/quality_evaluator.py` (554 lines) | ✅ 완료 |
| Best Selector | `app/uqsl/best_selector.py` (243 lines) | ✅ 완료 |
| Ensemble++ 3-Way | `app/uqsl/ensemble_plus_plus.py` (528 lines) | ✅ 완료 |
| UQSL API | `app/routers/uqsl.py` (960 lines) | ✅ 완료 |
| Metrics | `app/uqsl/metrics.py` (492 lines) | ✅ 완료 |
| Cloud Integration | `app/uqsl/cloud_integration.py` (581 lines) | ✅ 완료 |
| DB Migration | `alembic/versions/012_add_uqsl_tables.py` | ✅ 완료 |

### 3.2 프론트엔드 ✅ COMPLETE

| UQSL 요구사항 | Vivid 구현 | 상태 |
|--------------|-----------|------|
| Dimension 앱 페이지 | `src/app/dimension/*/page.tsx` (11개) | ✅ 완료 |
| Panel 컴포넌트 | `src/components/dimension/*.tsx` (11개) | ✅ 완료 |
| NextDimensionNav | `NextDimensionNav.tsx` | ✅ 완료 |
| 파일 첨부 | `FileUploader.tsx` | ✅ 완료 |
| 피드백 버튼 | `FeedbackButtons.tsx` | ✅ 완료 |
| A/B 비교 | `ABComparisonCard.tsx` (332 lines) | ✅ 완료 |
| Multi-Generate 표시 | `MultiGenerateWrapper.tsx` (419 lines) | ✅ 완료 |
| Quality Score 표시 | `QualityScorecard.tsx` (501 lines) | ✅ 완료 |
| 3-Way 선택 | `ThreeWayComparison.tsx` (482 lines) | ✅ 완료 |
| useUQSL Hook | `hooks/useUQSL.ts` (563 lines) | ✅ 완료 |
| Panel Design Unity | `DimensionPanel` Compound Component | ✅ 완료 |
| E2E Tests | `e2e/uqsl.spec.ts` (342 lines) | ✅ 완료 |

### 3.3 Critical Gap 상세

#### Gap 1: 파일 첨부 없음

현재 Dimension Panel들은 텍스트 입력만 지원합니다.

```tsx
// 현재 (AestheticDirectorPanel.tsx)
const [concept, setConcept] = useState("");
// 텍스트만 입력 가능

// 필요 (UQSL 완전 지원 시)
const [concept, setConcept] = useState("");
const [files, setFiles] = useState<File[]>([]);
// 이미지/영상 참조 가능
```

**영향**: 이미지/영상 기반 품질 비교 불가

#### Gap 2: 피드백 수집 UI 없음

P6에서 Feedback API를 구현했지만, 프론트엔드에서 호출하는 UI가 없습니다.

```tsx
// 현재: 존재하지 않음

// 필요
<FeedbackButtons
  responseId={result.response_id}
  onFeedback={(type, rating) => {
    // POST /api/v1/rag/feedback/explicit
  }}
/>
```

**영향**: Thompson Sampling에 필요한 피드백 데이터 수집 불가

#### Gap 3: NextDimensionNav 부분 통합

`NextDimensionNav.tsx`가 존재하지만, 모든 Panel에 일관되게 적용되지 않았습니다.

```tsx
// NextDimensionNav.tsx 존재하지만
// AestheticDirectorPanel.tsx, StoryArchitectPanel.tsx 등에서
// 실제 사용 여부 확인 필요
```

**영향**: 앱 간 워크플로우 연결 불완전

---

## 4. 제안: Pre-Phase 0 로드맵

### 4.1 개요

UQSL 구현 전 **2주** 동안 UX Foundation을 구축합니다.

```
┌─────────────────────────────────────────────────────────────────┐
│ Pre-Phase 0: UX Foundation (Week 1-2)                          │
├─────────────────────────────────────────────────────────────────┤
│ Week 1: 핵심 컴포넌트                                           │
│   • FileUploader.tsx - 드래그&드롭 파일 첨부                    │
│   • FeedbackButtons.tsx - 좋아요/싫어요 + 평점                  │
│   • useFeedback.ts - P6 API 연동 훅                             │
│                                                                 │
│ Week 2: 통합 및 통일                                            │
│   • NextDimensionNav 전체 앱 통합                               │
│   • Panel 디자인 통일                                           │
│   • E2E 테스트                                                  │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ UQSL Phase 1-4 (Week 3-8)                                      │
│ 문서대로 진행                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Week 1: 핵심 컴포넌트

#### 4.2.1 FileUploader.tsx

```tsx
// src/components/dimension/FileUploader.tsx

interface FileUploaderProps {
  accept: string[];              // ["image/*", "video/*"]
  maxSizeMB: number;             // 50
  onUpload: (files: File[]) => void;
  multiple?: boolean;            // default: false
  preview?: boolean;             // 썸네일 표시
  disabled?: boolean;
}

// 핵심 기능
// 1. 드래그&드롭 + 버튼 클릭
// 2. 파일 타입/크기 검증
// 3. 업로드 진행률 표시
// 4. 썸네일 미리보기
// 5. Next.js 16 Server Actions 활용
```

**구현 위치**: `src/components/dimension/FileUploader.tsx`
**예상 시간**: 1일

#### 4.2.2 FeedbackButtons.tsx

```tsx
// src/components/dimension/FeedbackButtons.tsx

interface FeedbackButtonsProps {
  responseId: string;            // P6 RAGResponse ID
  onFeedback?: (type: 'positive' | 'negative', rating?: number) => void;
  showRating?: boolean;          // 1-5 별점 표시
  showComment?: boolean;         // 코멘트 입력 표시
  disabled?: boolean;
  compact?: boolean;             // 간소화 모드
}

// 핵심 기능
// 1. 좋아요/싫어요 버튼
// 2. 선택적 1-5 별점
// 3. 선택적 코멘트 입력
// 4. P6 Feedback API 연동
// 5. Optimistic UI 업데이트
```

**구현 위치**: `src/components/dimension/FeedbackButtons.tsx`
**예상 시간**: 1일

#### 4.2.3 useFeedback.ts

```typescript
// src/hooks/useFeedback.ts

interface UseFeedbackOptions {
  responseId: string;
  onSuccess?: () => void;
  onError?: (error: Error) => void;
}

interface UseFeedbackReturn {
  submitExplicit: (type: 'positive' | 'negative', rating?: number, comment?: string) => Promise<void>;
  trackImplicit: (eventType: ImplicitEventType, metadata?: object) => Promise<void>;
  isSubmitting: boolean;
  hasSubmitted: boolean;
  error: Error | null;
}

// 핵심 기능
// 1. P6 Explicit Feedback API 호출
// 2. P6 Implicit Feedback API 호출 (클릭, 복사 등)
// 3. 에러 핸들링 + 재시도
// 4. 제출 상태 관리
```

**구현 위치**: `src/hooks/useFeedback.ts`
**예상 시간**: 0.5일

### 4.3 Week 2: 통합 및 통일

#### 4.3.1 NextDimensionNav 전체 통합

```tsx
// 각 Panel에 NextDimensionNav 추가
// 예: AestheticDirectorPanel.tsx

import NextDimensionNav from "./NextDimensionNav";

export default function AestheticDirectorPanel() {
  const [result, setResult] = useState<AestheticResult | null>(null);

  return (
    <TeachingPanelLayout>
      {/* 기존 UI */}

      {/* 결과 표시 후 NextDimensionNav */}
      {result && (
        <NextDimensionNav
          currentDimension="aesthetic"
          show={true}
          themeColor="fuchsia"
        />
      )}
    </TeachingPanelLayout>
  );
}
```

**대상 Panel**: 10개 전체
**예상 시간**: 2일

#### 4.3.2 Panel 디자인 통일

```tsx
// DimensionPanelLayout.tsx 확장

// 공통 요소 추가
// 1. 파일 첨부 슬롯
// 2. 피드백 버튼 슬롯
// 3. NextDimension 슬롯
// 4. 일관된 버튼 스타일
// 5. 일관된 결과 카드 스타일
```

**예상 시간**: 2일

#### 4.3.3 E2E 테스트

```typescript
// e2e/dimension-workflow.spec.ts

test('Aesthetic → Visual Realizer 워크플로우', async ({ page }) => {
  // 1. Aesthetic에서 결과 생성
  await page.goto('/dimension/aesthetic');
  await page.fill('[data-testid="concept-input"]', 'Test concept');
  await page.click('[data-testid="generate-button"]');
  await expect(page.locator('[data-testid="result"]')).toBeVisible();

  // 2. 피드백 제출
  await page.click('[data-testid="feedback-positive"]');

  // 3. NextDimension으로 이동
  await page.click('[data-testid="next-dimension-visual-realizer"]');
  await expect(page).toHaveURL('/dimension/visual-realizer');

  // 4. 이전 데이터 연결 확인
  await expect(page.locator('[data-testid="chain-data"]')).toContainText('Test concept');
});
```

**예상 시간**: 1일

---

## 5. 수정된 UQSL 로드맵

### 5.1 전체 타임라인

| Phase | 기간 | 내용 | 담당 |
|-------|------|------|------|
| **Pre-Phase 0** | Week 1-2 | UX Foundation | 프론트엔드 |
| **Phase 1** | Week 3-4 | UQSL Core | 백엔드 + 프론트엔드 |
| **Phase 2** | Week 5-6 | Selection & Feedback Loop | 백엔드 + 프론트엔드 |
| **Phase 3** | Week 7-8 | Production & Analytics | 인프라 |

### 5.2 병렬 진행 가능 작업

```
Week 1-2 (Pre-Phase 0)
┌─────────────────────────────────────────────────────────────────┐
│ 프론트엔드                    │ 백엔드 (병렬)                   │
├──────────────────────────────┼──────────────────────────────────┤
│ FileUploader.tsx             │ bandit_arms 테이블 마이그레이션  │
│ FeedbackButtons.tsx          │ uqsl_configs 테이블 마이그레이션 │
│ useFeedback.ts               │ selection_history 테이블         │
│ NextDimensionNav 통합        │ YAML Manifest 스키마 확장        │
│ Panel 디자인 통일            │                                  │
└──────────────────────────────┴──────────────────────────────────┘

Week 3-4 (Phase 1)
┌─────────────────────────────────────────────────────────────────┐
│ 프론트엔드                    │ 백엔드 (병렬)                   │
├──────────────────────────────┼──────────────────────────────────┤
│ MultiGenerateDisplay.tsx     │ multi_generate_engine.py        │
│ QualityScoreCard.tsx         │ quality_evaluator.py            │
│ SelectionStrategyToggle.tsx  │ Manifest 로딩 확장              │
└──────────────────────────────┴──────────────────────────────────┘

Week 5-6 (Phase 2)
┌─────────────────────────────────────────────────────────────────┐
│ 프론트엔드                    │ 백엔드 (병렬)                   │
├──────────────────────────────┼──────────────────────────────────┤
│ ABComparisonPanel.tsx        │ best_selector.py                │
│ ThreeWaySelector.tsx         │ thompson_sampling_router.py     │
│ 피드백 대시보드              │ 피드백 집계 API                 │
└──────────────────────────────┴──────────────────────────────────┘
```

---

## 6. UQSL 문서 수정 권장사항

### 6.1 Prerequisites 섹션 추가

```markdown
## Prerequisites (사전 조건)

UQSL 구현 전 다음 항목이 완료되어야 합니다:

### 필수 (Pre-Phase 0)
1. **FileUploader 컴포넌트**: 이미지/영상 입력 UI
2. **FeedbackButtons 컴포넌트**: 좋아요/싫어요 + 평점 UI
3. **useFeedback 훅**: P6 Feedback API 연동
4. **NextDimensionNav 통합**: 모든 앱 간 워크플로우 연결
5. **Panel 디자인 통일**: 일관된 UX

### 권장
1. E2E 테스트 기반 구축
2. 디자인 시스템 문서화
```

### 6.2 Implementation Roadmap 수정

```markdown
## 📋 Implementation Roadmap

### Pre-Phase 0: UX Foundation (Week 1-2) - 신규
- [ ] FileUploader.tsx
- [ ] FeedbackButtons.tsx
- [ ] useFeedback.ts
- [ ] NextDimensionNav 전체 통합
- [ ] Panel 디자인 통일
- [ ] E2E 테스트

### Phase 1: Core (Week 3-4) - 기존
- [ ] multi_generate_engine.py
- [ ] quality_evaluator.py
- [ ] MultiGenerateDisplay.tsx
- [ ] QualityScoreCard.tsx
- [ ] YAML manifest 스키마 확장

### Phase 2: Selection & Feedback (Week 5-6) - 기존 통합
- [ ] best_selector.py
- [ ] thompson_sampling_router.py
- [ ] ABComparisonPanel.tsx
- [ ] ThreeWaySelector.tsx
- [ ] bandit_arms, selection_history 테이블

### Phase 3: Production (Week 7-8) - 기존
- [ ] 배포 (Railway or Cloud Run)
- [ ] 모니터링 대시보드
- [ ] 문서화
```

### 6.3 MCP 통합 섹션 수정

현재 Railway를 사용 중이므로, Cloud Run MCP는 **선택적**으로 표기:

```markdown
## 🔌 Infrastructure Options

### Option A: Railway (현재 - 권장)
- 이미 운영 중
- 추가 설정 불필요
- 비용 예측 가능

### Option B: Cloud Run MCP (선택적)
- 서버리스 자동 스케일링
- Antigravity MCP 통합
- 초기 설정 필요
```

---

## 7. 성공 기준

### 7.1 Pre-Phase 0 완료 기준

| 기준 | 측정 방법 | 목표 |
|-----|----------|------|
| 파일 첨부 | 10개 앱에서 동작 | 100% |
| 피드백 수집 | P6 API 연동 | 동작 |
| NextDimension | 10개 앱 연결 | 100% |
| 디자인 일관성 | 디자인 리뷰 | 통과 |
| E2E 테스트 | 테스트 통과 | 100% |

### 7.2 UQSL 완료 기준

| 기준 | 측정 방법 | 목표 |
|-----|----------|------|
| Multi-Generate | N개 후보 생성 | 동작 |
| Quality Score | 자동 평가 | 5개 지표 |
| Best Selection | 4가지 전략 | 동작 |
| Thompson Sampling | 피드백 → 가중치 | 자동 조정 |
| 3-Way 비교 | A vs B vs A+B | UI 동작 |

---

## 8. 의사결정 포인트

### 8.1 즉시 결정 필요

| 결정 사항 | 옵션 | 권장 |
|----------|------|------|
| 인프라 | Railway vs Cloud Run | **Railway 유지** (비용/안정성) |
| 분석 DB | PostgreSQL vs BigQuery | **PostgreSQL 시작** (스케일 시 전환) |
| 첫 구현 Tier | Free vs Premium | **Free Tier 먼저** (Thompson Sampling) |

### 8.2 추후 결정 가능

| 결정 사항 | 시점 | 비고 |
|----------|------|------|
| LLM-as-Judge 도입 | Phase 2 이후 | Dev Tier용 |
| BigQuery 전환 | 데이터 100만건+ | 비용 분석 후 |
| Cloud Run 마이그레이션 | 트래픽 급증 시 | 자동 스케일링 필요 시 |

---

## 9. 결론

### 9.1 핵심 메시지

> **"UQSL의 핵심 가치는 '사용자 피드백 기반 자동 진화'입니다. 이를 위해 사용자가 피드백을 제출할 수 있는 UI가 필수입니다."**

### 9.2 권장 실행 순서

```
1. Pre-Phase 0 시작 (즉시)
   → FileUploader, FeedbackButtons 컴포넌트 개발
   → 병렬: bandit_arms 테이블 마이그레이션

2. UQSL 문서 업데이트
   → Prerequisites 섹션 추가
   → Roadmap 8주로 확장

3. Phase 1 시작 (Week 3)
   → Multi-Generate Engine
   → Quality Evaluator
```

### 9.3 총 기간

| 구분 | 기간 | 비고 |
|-----|------|------|
| Pre-Phase 0 | 2주 | UX Foundation |
| UQSL Phase 1-3 | 6주 | 문서 기준 |
| **총 기간** | **8주** | |

---

## Appendix: 컴포넌트 인터페이스 명세

### A.1 FileUploader

```tsx
interface FileUploaderProps {
  /** 허용 파일 타입 */
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
}
```

### A.2 FeedbackButtons

```tsx
interface FeedbackButtonsProps {
  /** P6 RAGResponse ID */
  responseId: string;
  /** 피드백 콜백 */
  onFeedback?: (type: 'positive' | 'negative', rating?: number) => void;
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
}
```

### A.3 useFeedback Hook

```tsx
interface UseFeedbackReturn {
  /** 명시적 피드백 제출 */
  submitExplicit: (
    type: 'positive' | 'negative',
    rating?: number,
    comment?: string
  ) => Promise<void>;
  /** 암묵적 피드백 추적 */
  trackImplicit: (
    eventType: 'source_click' | 'text_copy' | 'query_reformulate' | 'session_end',
    metadata?: Record<string, unknown>
  ) => Promise<void>;
  /** 제출 중 여부 */
  isSubmitting: boolean;
  /** 이미 제출했는지 */
  hasSubmitted: boolean;
  /** 에러 */
  error: Error | null;
}
```

---

*문서 작성: 2026-01-15*
*기반 문서: UNIVERSAL_QUALITY_SELECTION_SSOT.md*
