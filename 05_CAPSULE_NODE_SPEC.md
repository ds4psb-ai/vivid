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
7. **DB SoR 우선**: NotebookLM/Opal 결과는 Derived, DB 승격된 근거만 증거로 취급

---

## 3) 데이터 스키마

```typescript
interface CapsuleNodeSpec {
  id: string; // example: "auteur.bong-joon-ho"
  version: string; // semver
  displayName: string;
  description?: string;
  inputContracts: {
    required: string[];
    optional?: string[];
    maxUpstream?: number;
    allowedTypes?: string[];
    contextMode?: "aggregate" | "sequential";
  };
  outputContracts: {
    types: string[];
  };
  inputs: Record<string, { type: string; required?: boolean }>;
  outputs: Record<string, { type: string }>; // summary-only
  patternVersion?: string; // Pattern Library snapshot version
  clusterRef?: string; // cluster_id from Logic/Persona Fusion (see 33_...)
  temporalPhase?: "HOOK" | "BUILD" | "PAYOFF" | "CTA" | "SETUP" | "TURN" | "ESCALATION" | "CLIMAX" | "RESOLUTION";
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

interface CapsuleRunRecord {
  id: string;
  capsuleId: string;
  capsuleVersion: string;
  status: "queued" | "running" | "done" | "failed" | "cancelled";
  upstreamContext?: Record<string, unknown>;
  summary?: Record<string, unknown>;
  evidenceRefs?: string[];
  synapseRuleRef?: string;
  tokenUsage?: { input: number; output: number; total: number };
  latencyMs?: number;
  costUsdEst?: number;
  createdAt: string;
  updatedAt: string;
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
  "inputs": { "source_id": "auteur-bong-1999-barking-dogs", "emotion": "tension" },
  "params": { "style_intensity": 0.7 }
}
```

노트:
- `upstream_context`가 없으면 서버가 `canvas_id + node_id` 기준으로 캔버스 그래프에서 자동 계산합니다.

응답:
```json
{
  "run_id": "...",
  "status": "done",
  "summary": {
    "style_vector": [0.8, 0.6, 0.7],
    "pattern_version": "v1",
    "recommended_palette": ["#102A43", "#243B53"]
  },
  "evidence_refs": ["sheet:CREBIT_DERIVED_INSIGHTS:128"],
  "token_usage": { "input": 320, "output": 180, "total": 500 },
  "latency_ms": 820,
  "cost_usd_est": 0.08,
  "version": "1.2.0"
}
```

### 5.2 비동기 실행 (옵션)

- 긴 작업은 큐 기반 비동기로 전환
- 상태 조회: `GET /api/v1/capsules/run/{run_id}`
- `POST /api/v1/capsules/run` 요청에 `async_mode: true` 전달 시 `queued` 상태로 즉시 반환

### 5.3 스트리밍 실행 (WS / SSE)

캡슐 실행 진행 상황을 실시간으로 노출합니다.  
UI는 `loading → streaming → complete` 상태로 전환됩니다.

- **WebSocket**: `GET /ws/runs/{run_id}`
- **SSE**: `GET /api/v1/capsules/run/{run_id}/stream`

**이벤트 타입**
- `run.queued`
- `run.started`
- `run.progress`
- `run.partial`
- `run.completed`
- `run.failed`
- `run.cancelled`

**이벤트 페이로드 예시**
```json
{
  "event_id": "runId:3",
  "run_id": "runId",
  "type": "run.progress",
  "seq": 3,
  "ts": "2025-12-24T12:00:00Z",
  "payload": {
    "progress": 40,
    "message": "Generating style vector"
  }
}
```

**정책**
- `summary + evidence_refs`만 노출
- `evidence_refs`는 `sheet:` 또는 `db:` 포맷만 허용되며, 나머지는 서버에서 필터링
- 필터링된 항목은 `summary.evidence_warnings[]`에 사유로 기록
- `outputContracts` 불일치 항목은 `summary.output_warnings[]`에 기록
- 허용 `db` 테이블: `raw_assets`, `video_segments`, `evidence_records`, `patterns`, `pattern_trace`, `notebook_library`
- `raw_logs / debug / trace`는 정책에 따라 비공개

**취소**
- `POST /api/v1/capsules/run/{run_id}/cancel`
- 실행 중인 캡슐을 취소하고 `run.cancelled` 이벤트 발행
- WS 컨트롤: `/ws/runs/{run_id}`에 `{"type":"cancel"}` 전송

---

## 6) 실행 파이프라인

1. 입력/파라미터 검증
   - 필수 입력 누락 시 `ALLOW_INPUT_FALLBACKS=true`면 기본값 대체
2. upstream_context 수집 (연결된 모든 상위 노드 스냅샷)
   - contextMode=sequential이면 `upstream_context.sequence`에 위상 정렬된 노드 리스트를 포함
   - contextMode=aggregate이면 `upstream_context.mode=aggregate`를 포함
3. Adapter 실행 (NotebookLM/Opal/Internal)
4. 결과 요약/정규화
5. **Sheets Bus 기록 (Derived)** → DB 승격은 별도 파이프라인
6. 증거 참조 생성 (DB SoR 우선, Synapse Rule 포함)
7. 캐시 저장 및 반환

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
- `persona_priority`: `script | blended | user` (default: script) — 페르소나 우선순위

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
