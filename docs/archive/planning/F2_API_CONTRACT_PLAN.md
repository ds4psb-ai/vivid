# F2: API Contract Implementation Plan

> **Date**: 2026-01-15
> **Phase**: -1 (Technical Foundation)
> **Status**: PLANNING
> **Depends on**: F1 Testing Infrastructure (Completed)

---

## Executive Summary

Zod v4를 사용하여 프론트엔드 API 호출의 Request/Response 스키마를 런타임 검증하고, 컴파일타임 타입 안전성을 확보한다.

### Key Decisions (2026 Best Practices 기반)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Zod vs Zod Mini | **Regular Zod** | 5-10kb 차이는 무의미, DX가 우선 |
| Error Format | `z.treeifyError()` | v4에서 `.flatten()` deprecated |
| Validation Point | safeParse | 절대 throw하지 않음, 에러 객체 반환 |
| Schema Location | `src/lib/schemas/` | 중앙화된 SSoT |

---

## Research Summary

### Sources

- [Zod v4 Official Documentation](https://zod.dev/v4)
- [Zod Mini Guide](https://zod.dev/packages/mini) - Bundle size 비교
- [Schema Validation with Zod 2025](https://www.turing.com/blog/data-integrity-through-zod-validation)
- [Next.js 15 API Validation with Zod](https://dev.to/saiful7778/api-validation-in-nextjs-15-with-zod-and-typescript-5aa9)
- [Sharing Zod Schemas in Monorepo](https://leapcell.io/blog/sharing-types-and-validations-with-zod-across-a-monorepo)
- [useActionState with Zod](https://medium.com/@sorayacantos/handling-forms-in-next-js-with-next-form-server-actions-useactionstate-and-zod-validation-15f9932b0a9e)
- [Type-Safe Backend Evolution](https://thinhdanggroup.github.io/type-safe-backend-evolution/)

### Zod v4 Key Changes

```typescript
// ❌ Deprecated in v4
error.flatten()
error.format()

// ✅ v4 Recommended
z.treeifyError(error)
```

### Bundle Size Analysis

| Schema Complexity | Zod | Zod Mini | Decision |
|-------------------|-----|----------|----------|
| Simple boolean | 5.91 KB | 2.12 KB | Use Zod |
| Login form | 17.7 KB | 6.88 KB | Use Zod |

**Rationale**: 10-15kb 차이는 ~0.6ms 로딩 시간 증가에 불과. DX 우선.

---

## Current State Analysis

### 현재 문제점

1. **Zod 설치되어 있으나 미사용**
   ```json
   // package.json
   "zod": "^4.3.5"  // 설치됨
   ```

2. **dimension-input-schemas.ts**: Plain TypeScript interfaces (런타임 검증 없음)
   ```typescript
   // 현재: 컴파일타임만
   export interface InputFieldConfig {
     key: string;
     label: string;
     type: "text" | "textarea" | "select" | "toggle";
   }
   ```

3. **api.ts**: 72개 이상의 인터페이스, 런타임 검증 없음
   ```typescript
   // 현재: 타입만, 검증 없음
   export interface Canvas {
     id: string;
     title: string;
     // ...
   }
   ```

4. **useAsyncOperation**: body를 `object`로 받음, 검증 없음
   ```typescript
   execute: (url: string, body: object, headers?: Record<string, string>) => Promise<T | null>;
   ```

---

## Implementation Architecture

### Directory Structure

```
frontend/src/lib/
├── schemas/
│   ├── index.ts                    # Re-exports all schemas
│   ├── common.ts                   # Shared primitives (pagination, error, etc.)
│   ├── dimension/
│   │   ├── index.ts
│   │   ├── 1d.schema.ts            # Generate1D request/response
│   │   ├── 2d.schema.ts            # Storyboard request/response
│   │   ├── 3d.schema.ts            # VisualRealizer request/response
│   │   ├── 4d.schema.ts            # ReferenceDecoder request/response
│   │   ├── veo.schema.ts           # VEO request/response
│   │   └── quality.schema.ts       # QC tools schemas
│   ├── feedback.schema.ts          # RAG Feedback schemas
│   ├── canvas.schema.ts            # Canvas CRUD schemas
│   └── auth.schema.ts              # Auth schemas
├── api-client.ts                   # Enhanced with Zod validation
└── validated-fetch.ts              # Wrapper with schema validation
```

### Schema Pattern (2026 Best Practice)

```typescript
// src/lib/schemas/dimension/1d.schema.ts
import { z } from "zod";

// =============================================================================
// Request Schema
// =============================================================================

export const Generate1DRequestSchema = z.object({
  topic: z.string().min(1, "주제를 입력해주세요"),
  style: z.enum(["cinematic", "documentary", "commercial", "artistic", "vlog"]),
  mood: z.enum(["neutral", "dramatic", "calm", "energetic", "melancholic"]),
  duration: z.enum(["5 seconds", "10 seconds", "15 seconds", "30 seconds", "60 seconds"]),
  language: z.enum(["ko", "en"]).default("ko"),
  model: z.enum(["gemini-3-flash-preview", "gemini-3-pro-preview"]).default("gemini-3-flash-preview"),
  use_rag: z.boolean().default(true),
  auteur_key: z.string().optional(),
});

// =============================================================================
// Response Schema
// =============================================================================

export const Generate1DOutputSchema = z.object({
  title: z.string(),
  premise: z.string(),
  keywords: z.array(z.string()),
  evidence_refs: z.array(z.string()).optional(),
  rag_context: z.string().optional(),
});

export const Generate1DResponseSchema = z.object({
  success: z.literal(true),
  output: Generate1DOutputSchema,
}).or(z.object({
  success: z.literal(false),
  error: z.string(),
}));

// =============================================================================
// Type Exports (Inferred from Schema)
// =============================================================================

export type Generate1DRequest = z.infer<typeof Generate1DRequestSchema>;
export type Generate1DResponse = z.infer<typeof Generate1DResponseSchema>;
export type Generate1DOutput = z.infer<typeof Generate1DOutputSchema>;
```

### Validated Fetch Wrapper

```typescript
// src/lib/validated-fetch.ts
import { z, ZodSchema } from "zod";

export interface ValidatedFetchOptions<TReq, TRes> {
  url: string;
  method?: "GET" | "POST" | "PUT" | "DELETE";
  requestSchema?: ZodSchema<TReq>;
  responseSchema: ZodSchema<TRes>;
  headers?: Record<string, string>;
}

export interface ValidatedResult<T> {
  success: true;
  data: T;
} | {
  success: false;
  error: string;
  validationErrors?: z.ZodError;
}

export async function validatedFetch<TReq, TRes>(
  body: TReq,
  options: ValidatedFetchOptions<TReq, TRes>
): Promise<ValidatedResult<TRes>> {
  const { url, method = "POST", requestSchema, responseSchema, headers } = options;

  // 1. Request Validation
  if (requestSchema) {
    const reqResult = requestSchema.safeParse(body);
    if (!reqResult.success) {
      return {
        success: false,
        error: "Request validation failed",
        validationErrors: reqResult.error,
      };
    }
  }

  // 2. Fetch
  try {
    const response = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...headers,
      },
      body: method !== "GET" ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return {
        success: false,
        error: errorData.detail || `HTTP ${response.status}`,
      };
    }

    const data = await response.json();

    // 3. Response Validation
    const resResult = responseSchema.safeParse(data);
    if (!resResult.success) {
      console.warn("[validatedFetch] Response validation failed:", z.treeifyError(resResult.error));
      // Log but don't fail - backend contract might be ahead of frontend
      return { success: true, data: data as TRes };
    }

    return { success: true, data: resResult.data };
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : "Unknown error",
    };
  }
}
```

### Integration with useAsyncOperation

```typescript
// Enhanced useAsyncOperation with schema validation
export function useValidatedOperation<TReq, TRes>(
  requestSchema: ZodSchema<TReq>,
  responseSchema: ZodSchema<TRes>,
  options?: UseAsyncOperationOptions<TRes>
) {
  const asyncOp = useAsyncOperation<TRes>(options);

  const executeValidated = useCallback(
    async (url: string, body: TReq, headers?: Record<string, string>) => {
      // Validate request before sending
      const reqResult = requestSchema.safeParse(body);
      if (!reqResult.success) {
        const errorTree = z.treeifyError(reqResult.error);
        throw new Error(`Validation failed: ${JSON.stringify(errorTree)}`);
      }

      return asyncOp.execute(url, reqResult.data, headers);
    },
    [requestSchema, asyncOp]
  );

  return {
    ...asyncOp,
    executeValidated,
  };
}
```

---

## Implementation Phases

### Phase 1: Foundation (Day 1)

| Task | Files | Priority |
|------|-------|----------|
| Create schemas directory structure | `src/lib/schemas/` | P0 |
| Create common schemas | `common.ts` | P0 |
| Create validated-fetch utility | `validated-fetch.ts` | P0 |
| Add schema barrel export | `schemas/index.ts` | P0 |

### Phase 2: Dimension Schemas (Day 1-2)

| Dimension | Schema File | Priority |
|-----------|-------------|----------|
| 1D Prompt Generator | `dimension/1d.schema.ts` | P0 |
| 2D Storyboard | `dimension/2d.schema.ts` | P0 |
| 3D Visual Realizer | `dimension/3d.schema.ts` | P1 |
| 4D Reference Decoder | `dimension/4d.schema.ts` | P1 |
| VEO Video | `dimension/veo.schema.ts` | P1 |
| Quality Tools | `dimension/quality.schema.ts` | P1 |

### Phase 3: Integration (Day 2-3)

| Task | Files | Priority |
|------|-------|----------|
| Create useValidatedOperation hook | `hooks/useValidatedOperation.ts` | P0 |
| Update PromptGeneratorPanel | `dimension/PromptGeneratorPanel.tsx` | P0 |
| Add validation error display | `dimension/ValidationError.tsx` | P0 |
| Update remaining panels | All dimension panels | P1 |

### Phase 4: Testing (Day 3)

| Task | Files | Priority |
|------|-------|----------|
| Schema unit tests | `schemas/**/*.test.ts` | P0 |
| validated-fetch tests | `validated-fetch.test.ts` | P0 |
| Integration tests | `useValidatedOperation.test.ts` | P1 |

---

## Error Handling Pattern (2026)

### Using z.treeifyError()

```typescript
import { z } from "zod";

const result = schema.safeParse(data);

if (!result.success) {
  // v4 recommended approach
  const errorTree = z.treeifyError(result.error);

  // errorTree structure:
  // {
  //   _errors: ["Root level errors"],
  //   fieldName: {
  //     _errors: ["Field specific errors"]
  //   }
  // }

  return {
    success: false,
    errors: errorTree,
  };
}
```

### Validation Error Component

```typescript
// src/components/ui/ValidationError.tsx
interface ValidationErrorProps {
  errors: z.ZodError | null;
  field?: string;
}

export function ValidationError({ errors, field }: ValidationErrorProps) {
  if (!errors) return null;

  const tree = z.treeifyError(errors);
  const fieldErrors = field ? tree[field]?._errors : tree._errors;

  if (!fieldErrors?.length) return null;

  return (
    <div className="text-sm text-red-400 mt-1">
      {fieldErrors.map((err, i) => (
        <p key={i}>{err}</p>
      ))}
    </div>
  );
}
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Schema Coverage | 100% Dimension APIs | Count schemas vs API endpoints |
| Type Safety | 0 `any` types in API layer | ESLint rule |
| Runtime Validation | All API calls validated | Code review |
| Test Coverage | 80%+ for schemas | Vitest coverage |
| Error UX | Clear validation messages | Manual QA |

---

## Risk Mitigation

### Risk 1: Backend Schema Drift

**Problem**: Backend response changes, frontend schema fails.

**Mitigation**:
- Response validation logs warning but doesn't fail
- Add schema version header for future
- Consider shared schema package (future)

### Risk 2: Performance Overhead

**Problem**: Zod parsing adds latency.

**Mitigation**:
- Zod v4 is 2x faster than v3
- Only validate at API boundaries
- Skip validation in production for known-safe calls (optional flag)

### Risk 3: DX Complexity

**Problem**: Too many schemas to maintain.

**Mitigation**:
- Generate schemas from OpenAPI (future)
- Clear naming conventions
- Barrel exports for discoverability

---

## Timeline

| Day | Tasks | Deliverables |
|-----|-------|--------------|
| 1 | Foundation + Common schemas | `schemas/`, `validated-fetch.ts` |
| 2 | Dimension schemas (6 files) | All dimension schemas |
| 3 | Integration + Tests | useValidatedOperation, 80% coverage |

**Total: 3 days**

---

## Next Steps After F2

- **F3**: Error Boundaries (React 19 patterns)
- **F4**: Design Tokens (Tailwind @theme)
- **Pre-Phase 0**: UX Foundation with validated schemas

---

## Appendix: Example Migration

### Before (Current)

```typescript
// PromptGeneratorPanel.tsx
const handleGenerate = async () => {
  if (!topic.trim()) {
    setValidationError("주제를 입력해주세요");
    return;
  }

  await execute(`${API_BASE}/api/dimension/1d/generate`, {
    topic,  // No type checking
    style,
    mood,
    // Missing fields won't be caught
  });
};
```

### After (With Zod)

```typescript
// PromptGeneratorPanel.tsx
import { Generate1DRequestSchema, type Generate1DRequest } from "@/lib/schemas";

const handleGenerate = async () => {
  const input: Generate1DRequest = {
    topic,
    style,
    mood,
    duration,
    language,
    model,
    use_rag: useRag,
  };

  const result = Generate1DRequestSchema.safeParse(input);
  if (!result.success) {
    setValidationErrors(result.error);
    return;
  }

  await execute(`${API_BASE}/api/dimension/1d/generate`, result.data);
};
```

---

*Plan created: 2026-01-15*
*Ready for implementation*
