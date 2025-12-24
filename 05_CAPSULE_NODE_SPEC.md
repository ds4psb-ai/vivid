# Capsule Node Spec (Sealed / Compound Node)

**작성**: 2025-12-24  
**버전**: 정본 v1.0  
**목표**: 내부 체인을 숨기고 외부 포트/파라미터만 노출하는 캡슐 노드 규격 정의  

---

## 1) 핵심 개념

- **Public Graph**: 사용자가 보는 캔버스 노드/엣지
- **Private Subgraph**: 서버에서만 실행되는 내부 DAG
- **Capsule Node**: Public Graph에서 단일 노드처럼 보이지만, Private Subgraph를 실행하는 래퍼

---

## 2) 설계 원칙

1. **입출력만 공개**: 포트 스키마와 노출 파라미터만 UI에 표시
2. **내부 체인 완전 비공개**: 프롬프트/워크플로우/서브노드 정보는 클라이언트로 전송 금지
3. **요약 반환**: 원문·중간 로그 대신 요약/참조만 반환
4. **버전 고정**: `capsuleId@version`으로 재현성 확보
5. **패턴 버전 고정**: `patternVersion`으로 근거 스냅샷 고정
6. **권한 기반 노출**: 고가치 노드는 관리자 전용 파라미터만 허용

---

## 3) 데이터 스키마

```typescript
interface CapsuleNodeSpec {
  id: string; // example: "auteur.bong-joon-ho"
  version: string; // semver
  displayName: string;
  description?: string;
  inputs: Record<string, { type: string; required?: boolean }>;
  outputs: Record<string, { type: string }>; // summary-only
  patternVersion?: string; // Pattern Library snapshot version
  exposedParams: Record<
    string,
    {
      type: "enum" | "number" | "boolean" | "string";
      options?: string[];
      min?: number;
      max?: number;
      step?: number;
      default?: unknown;
      visibility: "public" | "admin";
    }
  >;
  policy: {
    evidence: "summary_only" | "references_only";
    allowRawLogs: boolean;
  };
  adapter: {
    type: "notebooklm" | "opal" | "internal" | "hybrid";
    internalGraphRef: string; // private DAG reference
  };
}

interface CapsuleNodeInstance {
  capsuleId: string;
  capsuleVersion: string;
  patternVersion?: string;
  params: Record<string, unknown>;
  locked: boolean;
}
```

---

## 4) 노출 파라미터 규칙

- **노출 가능한 타입**: enum, number, boolean (string은 제한)
- **고가치 노드**: enum/slider 중심, free-text 제한
- **기본값 강제**: policy에 따라 기본값 유지
- **관리자 전용**: visibility=admin은 관리자만 수정 (`X-Admin-Mode: true`)

---

## 5) 실행 API

### 5.1 동기 실행 (요약 결과)

`POST /api/v1/capsules/run`

요청:
```json
{
  "canvas_id": "...",
  "node_id": "...",
  "capsule_id": "auteur.bong-joon-ho",
  "capsule_version": "1.2.0",
  "inputs": { "emotion": "tension" },
  "params": { "style_intensity": 0.7 }
}
```

응답:
```json
{
  "run_id": "...",
  "status": "done",
  "summary": {
    "style_vector": [0.8, 0.6, 0.7],
    "recommended_palette": ["#102A43", "#243B53"]
  },
  "evidence_refs": ["evidence:sheet:row:128"],
  "version": "1.2.0"
}
```

### 5.2 비동기 실행 (옵션)

- 긴 작업은 큐 기반 비동기로 전환
- 상태 조회: `GET /api/v1/capsules/run/{run_id}`
- `POST /api/v1/capsules/run` 요청에 `async_mode: true` 전달 시 `queued` 상태로 즉시 반환

---

## 6) 실행 파이프라인

1. 입력/파라미터 검증
   - 필수 입력 누락 시 `ALLOW_INPUT_FALLBACKS=true`면 기본값 대체
2. Adapter 실행 (NotebookLM/Opal/Internal)
3. 결과 요약/정규화
4. **Sheets Bus 기록 (Derived)** → DB 승격은 별도 파이프라인
5. 증거 참조 생성 (선택)
6. 캐시 저장 및 반환

---

## 7) 보안/로그 정책

- 프롬프트/원문/서브그래프는 **서버 저장만 허용**
- 클라이언트에는 summary + evidenceRef만 반환
- 디버그 로그는 관리자 권한으로 제한 (`X-Admin-Mode: true` + `allowRawLogs=true`)
- evidenceRef는 **sheet_ref 또는 db_ref** 형태로 유지 (재현성)

---

## 8) UI 적용 방식

- 캡슐 노드는 **잠금 아이콘 + 내부 확장 불가**
- 입력/출력 포트와 노출 파라미터만 편집 가능
- 실행 결과는 요약 카드로 표시

---

## 9) 템플릿 적용 방식

- 거장 템플릿은 캡슐 노드를 포함한 그래프로 제공
- 사용자는 템플릿 카드를 클릭해 즉시 캔버스 시작
- 템플릿 그래프는 **Public Graph만 공개**

---

## 10) Auteur Capsule Catalog (v1)

### 10.1 공통 입력/출력

- **inputs**: `emotion_curve(float[])`, `scene_summary(string)`, `duration_sec(number)`
- **outputs**: `style_vector(float[])`, `palette(string[])`, `composition_hints(string[])`, `pacing_hints(string[])`

### 10.2 공통 노출 파라미터 범위

- `style_intensity`: 0.4 ~ 1.0 (step 0.05)
- `pacing`: `slow | medium | fast`
- `color_bias`: `cool | neutral | warm`
- `camera_motion`: `static | controlled | dynamic`

### 10.3 거장 캡슐 노드 목록

- **auteur.bong-joon-ho** (봉준호)
  - signature: `tension_bias` 0.0~1.0 (default 0.7)
  - defaults: pacing=medium, color_bias=cool, camera_motion=controlled
  - adapter: `private-dag://auteur/bong/v1`
- **auteur.park-chan-wook** (박찬욱)
  - signature: `symmetry_bias` 0.0~1.0 (default 0.8)
  - defaults: pacing=medium, color_bias=warm, camera_motion=controlled
  - adapter: `private-dag://auteur/park/v1`
- **auteur.shinkai** (신카이)
  - signature: `light_diffusion` 0.0~1.0 (default 0.75)
  - defaults: pacing=slow, color_bias=warm, camera_motion=controlled
  - adapter: `private-dag://auteur/shinkai/v1`
- **auteur.lee-junho** (이준호)
  - signature: `music_sync` 0.0~1.0 (default 0.7)
  - defaults: pacing=medium, color_bias=neutral, camera_motion=dynamic
  - adapter: `private-dag://auteur/leejunho/v1`
- **auteur.na-hongjin** (나홍진)
  - signature: `chaos_bias` 0.0~1.0 (default 0.8)
  - defaults: pacing=fast, color_bias=cool, camera_motion=dynamic
  - adapter: `private-dag://auteur/na/v1`
- **auteur.hong-sangsoo** (홍상수)
  - signature: `stillness` 0.0~1.0 (default 0.85)
  - defaults: pacing=slow, color_bias=neutral, camera_motion=static
  - adapter: `private-dag://auteur/hong/v1`

### 10.4 예시 스펙 (봉준호)

```typescript
const auteurCapsule: CapsuleNodeSpec = {
  id: "auteur.bong-joon-ho",
  version: "1.0.0",
  displayName: "Bong Joon-ho Style Capsule",
  inputs: {
    emotion_curve: { type: "float[]" },
    scene_summary: { type: "string" },
    duration_sec: { type: "number" }
  },
  outputs: {
    style_vector: { type: "float[]" },
    palette: { type: "string[]" },
    composition_hints: { type: "string[]" },
    pacing_hints: { type: "string[]" }
  },
  exposedParams: {
    style_intensity: { type: "number", min: 0.4, max: 1.0, step: 0.05, default: 0.7, visibility: "public" },
    pacing: { type: "enum", options: ["slow", "medium", "fast"], default: "medium", visibility: "public" },
    color_bias: { type: "enum", options: ["cool", "neutral", "warm"], default: "cool", visibility: "public" },
    camera_motion: { type: "enum", options: ["static", "controlled", "dynamic"], default: "controlled", visibility: "public" },
    tension_bias: { type: "number", min: 0.0, max: 1.0, step: 0.1, default: 0.7, visibility: "public" }
  },
  policy: { evidence: "summary_only", allowRawLogs: false },
  adapter: { type: "hybrid", internalGraphRef: "private-dag://auteur/bong/v1" }
};
```
