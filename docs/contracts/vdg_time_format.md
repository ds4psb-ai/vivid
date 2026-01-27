# VDG Time Format Contract

> VDG 스키마 내 시간 데이터 표현 규약

## 규칙

### 1. API 응답 (백엔드 → 프론트엔드)

- **항상 밀리초(`_ms` suffix)** 사용
- 필드명 규약: `start_ms`, `end_ms`, `peak_ms`, `t_ms`

```json
{
  "viral_kicks": [
    {
      "start_ms": 1500,
      "end_ms": 3200,
      "peak_ms": 2400,
      "keyframes": [
        { "t_ms": 1500, "role": "start" },
        { "t_ms": 2400, "role": "peak" },
        { "t_ms": 3200, "role": "end" }
      ]
    }
  ]
}
```

### 2. 프론트엔드 표시

- 사용자에게 표시 시 **초 단위로 변환** (`/ 1000`)
- 소수점 1자리까지 표시 (예: `2.4s`)

```typescript
// 변환 예시
const displayTime = (ms: number) => `${(ms / 1000).toFixed(1)}s`;
```

### 3. 레거시 호환 (v3 스키마)

일부 v3 필드는 초 단위 사용. 정규화 시 변환 필요:

| 레거시 필드 | 단위 | 정규화 후 |
|------------|------|----------|
| `t` (microbeat) | 초 | `t_ms` (밀리초) |
| `start_sec`, `end_sec` | 초 | `start_ms`, `end_ms` |
| `time_start`, `time_end` (scene) | 초 | `t_start_ms`, `t_end_ms` |

## 필드별 규약

### Hook Genome

```typescript
interface HookGenome {
  hook_start_ms: number;  // 훅 시작 (ms)
  hook_end_ms: number;    // 훅 종료 (ms)
  // 레거시 호환
  start_sec?: number;     // deprecated, hook_start_ms 사용
  end_sec?: number;       // deprecated, hook_end_ms 사용
}
```

### Microbeat

```typescript
interface Microbeat {
  t_start_ms: number;     // 비트 시작 (ms)
  t_end_ms?: number;      // 비트 종료 (ms, 옵션)
  // 레거시 호환
  t?: number;             // deprecated, t_start_ms로 변환 (t * 1000)
  t_ms?: number;          // deprecated, t_start_ms 사용
}
```

### Viral Kick

```typescript
interface ViralKick {
  start_ms: number;       // 킥 시작 (ms)
  end_ms: number;         // 킥 종료 (ms)
  peak_ms?: number;       // 피크 시점 (ms, 옵션)
}
```

### Scene

```typescript
interface Scene {
  t_start_ms: number;     // 씬 시작 (ms)
  t_end_ms: number;       // 씬 종료 (ms)
  // 레거시 호환
  time_start?: number;    // deprecated (초 단위)
  time_end?: number;      // deprecated (초 단위)
}
```

## 정규화 함수

### 백엔드 (Python)

```python
# backend/app/services/vdg_schema_normalizer.py
def normalize_time_to_ms(value: float | int, unit: str = "sec") -> int:
    """시간값을 밀리초로 정규화"""
    if unit == "sec":
        return int(value * 1000)
    return int(value)
```

### 프론트엔드 (TypeScript)

```typescript
// frontend/src/utils/normalizeVDG.ts
export function normalizeMicrobeat(raw: unknown): Microbeat {
  const beat = raw as Record<string, unknown>;

  // t_start_ms 우선, 없으면 t (초)에서 변환
  let t_start_ms: number;
  if (typeof beat.t_start_ms === "number") {
    t_start_ms = beat.t_start_ms;
  } else if (typeof beat.t === "number") {
    t_start_ms = beat.t * 1000;  // 초 → 밀리초
  } else {
    t_start_ms = 0;
  }

  return { t_start_ms, ... };
}
```

## SSoT (Single Source of Truth)

| 레이어 | 파일 | 역할 |
|--------|------|------|
| 백엔드 스키마 | `backend/app/schemas/vdg_base.py` | 타입 정의 |
| 백엔드 정규화 | `backend/app/services/vdg_schema_normalizer.py` | 변환 로직 |
| 프론트엔드 정규화 | `frontend/src/utils/normalizeVDG.ts` | 변환 로직 |

## 변경 이력

- **2026-01-27**: 초기 문서 작성 (VDG 기술부채 해결 Phase 0)
