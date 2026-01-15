# Frontend CLAUDE.md

> Next.js 16 + React 19 + TypeScript + Tailwind

---

## Quick Commands

```bash
# 개발 서버
npm run dev  # localhost:3100

# 빌드
npm run build

# 린트
npm run lint

# E2E 테스트
npm run test:e2e
```

---

## 코딩 스타일

- **들여쓰기**: 2 spaces
- **컴포넌트**: PascalCase
- **Hooks**: useXxx
- **Utilities**: camelCase
- **ESLint**: `eslint.config.mjs` 참조

```tsx
// 컴포넌트 예시
interface ButtonProps {
  variant: 'primary' | 'secondary';
  onClick: () => void;
  children: React.ReactNode;
}

export function Button({ variant, onClick, children }: ButtonProps) {
  return (
    <button
      className={cn('px-4 py-2', variant === 'primary' && 'bg-blue-500')}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
```

---

## 디렉토리 구조

```
src/
├── app/                    # Next.js App Router
│   ├── (dashboard)/        # 대시보드 레이아웃 그룹
│   ├── api/                # API routes
│   └── _deprecated/        # 레거시 캔버스 코드
├── components/             # 재사용 컴포넌트
│   ├── ui/                 # 기본 UI 컴포넌트
│   └── AppShell.tsx        # 글로벌 레이아웃
├── contexts/               # React Context
│   └── DimensionSettingsContext.tsx
├── lib/                    # 유틸리티
│   ├── api.ts              # Typed API 클라이언트
│   └── utils.ts
├── hooks/                  # Custom hooks
└── types/                  # TypeScript 타입
```

---

## API 클라이언트 사용법

```typescript
import { api } from '@/lib/api';

// Dimension API 호출
const result = await api.dimension.generate1D({
  prompt: 'Create a video prompt',
  style: 'cinematic'
});

// Agent Chat (SSE)
const stream = await api.agent.chat({
  message: 'Help me create a storyboard',
  sessionId: 'xxx'
});

for await (const event of stream) {
  console.log(event.type, event.data);
}
```

---

## 상태 처리 패턴

### Loading/Error/Success
```tsx
function DataComponent() {
  const { data, isLoading, error } = useQuery(...);

  if (isLoading) return <Skeleton />;
  if (error) return <ErrorMessage error={error} />;
  if (!data) return <EmptyState />;

  return <DataView data={data} />;
}
```

### 폼 상태
```tsx
const [state, formAction] = useActionState(submitAction, initialState);

return (
  <form action={formAction}>
    {state.error && <ErrorBanner message={state.error} />}
    <SubmitButton pending={state.pending} />
  </form>
);
```

---

## Dimension 도구 통합

### Context 사용
```tsx
import { useDimensionSettings } from '@/contexts/DimensionSettingsContext';

function DimensionTool() {
  const { settings, updateSettings } = useDimensionSettings();

  const handleGenerate = async () => {
    const result = await api.dimension.generate1D(settings);
    // ...
  };
}
```

---

## 테스트 가이드

### E2E 테스트 (Playwright)
```typescript
// e2e/dimension.spec.ts
test('1D 생성 흐름', async ({ page }) => {
  await page.goto('/dimension/1d');
  await page.fill('[data-testid="prompt-input"]', 'Test prompt');
  await page.click('[data-testid="generate-button"]');
  await expect(page.locator('[data-testid="result"]')).toBeVisible();
});
```

### 필수 E2E 파일
| 변경 영역 | 테스트 파일 |
|-----------|-------------|
| Dimension | `e2e/dimension.spec.ts` |
| Credits | `e2e/credits.spec.ts` |
| Agent | `e2e/agent-chat.spec.ts` |
| Flow | `e2e/flow.spec.ts` |

---

## 환경 변수

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://127.0.0.1:8100
NEXT_PUBLIC_USER_ID=demo-user  # Dev 전용
```

---

## 주의사항

### Sealed Capsule 원칙
```typescript
// ❌ 금지 - 프론트에서 Gemini 직접 호출
const response = await fetch('https://generativelanguage.googleapis.com/...');

// ✅ 올바름 - 백엔드 캡슐 통해 호출
const response = await api.dimension.generate1D(params);
```

### 크레딧 UI
```tsx
// 크레딧 부족 시 처리
if (error?.status === 402) {
  return <InsufficientCreditsModal onTopUp={handleTopUp} />;
}
```
