# Node Canvas System: 기술 명세서 (2025-12 최신 정본)

**작성**: 2025-12-24  
**Updated**: 2025-12-28  
**버전**: 정본 v1.1  
**대상**: Tech Lead / Architect / Backend / Frontend  
**목표**: Node Canvas + 최적화 + AI 생성 파이프라인 설계 기준 수립  

---

## 0) 설계 원칙

1. **MVP 우선**: 캔버스 저장/불러오기 + 기본 계산을 먼저 완성한다.
2. **모듈형 확장**: 최적화/생성/배포는 플러그형 서비스로 추가한다.
3. **비용/지연 최소화**: 미리보기는 저비용 모델, 최종 생성은 고품질 모델.
4. **데이터 신뢰성**: 스펙/템플릿/생성 결과는 버전/출처를 보존한다.
5. **IP 보호**: 핵심 로직은 캡슐 노드로 봉인하고 입·출력만 공개한다.
6. **관찰성/재현성**: 실행 로그/근거/버전을 추적 가능하게 유지한다.
7. **RAG/LLMOps 규율**: chunking/embedding/hybrid retrieval + 평가, 프롬프트/체인 버전 관리.

---

## 1) 전체 아키텍처 개요

```
[Ingestion + Gemini Structuring] ──> [Video Schema DB] ──> [NotebookLM/Opal] ──> [Notebook Library] ──> [Sheets Bus] ──> [DB SoR + Pattern Library]
                                                                                                                   │
                                                                                                                   └──> [Capsule Spec Repo]

[Web UI] ──> [Canvas API] ──> [Spec Engine] ──> [Preview]
    │             │                │               │
    │             └──> [Template Service]           │
    │                                               │
    └──> [Model Gateway] ──> [AI Generation Pipeline] ──> [Assets + Metadata]
                                    │
                                    └──> [Optimization (GA/RL)]

* Event/Queue: ingestion, capsule run, generation run
```

핵심 계층:
- **Canvas 계층**: 노드/엣지 편집, 저장, 템플릿 관리
- **Spec 계층**: 노드 계산, 제약 조건, 품질 점수 산정
- **Optimization 계층**: GA/RL로 조합 개선
- **Generation 계층**: 스토리/이미지/영상/오디오 생성 및 합성
- **Data/Evidence 계층**: Video Schema DB, Notebook Library, 패턴 라이브러리, 증거 누적
 - **Observability/Eval**: 실행 추적, 품질/비용/지연 평가

### 1.1 핵심 사용자 플로우

- 메인에 **거장 템플릿 카드** 노출 → 클릭 시 템플릿 그래프 로드
- 기본 그래프: `Input → Auteur Capsule → Script/Beat → Storyboard → Output`
- **캡슐 노드**는 내부 체인을 숨기고 노출 파라미터만 편집 가능

### 1.2 Data → Capsule 파이프라인 (최신 기준)

1. 거장/레퍼런스 데이터 수집 (링크/메타/씬 단위)
2. ASR/키프레임/샷 분할 → Gemini 구조화 출력
3. **Video Schema DB** 적재 (scene/shot 단위)
4. NotebookLM 요약/라벨링 → **Notebook Library** 축적
5. Sheets Bus 기록 → 검수/정규화
6. **DB SoR + Pattern Library** 승격
7. Pattern Library/Trace 기반 캡슐 스펙 업데이트
8. 캔버스에서 캡슐 실행 시 DB 근거만 사용
9. Creator Self-Style 노트북은 동일 파이프라인으로 축적

상세 흐름/역할은 `10_PIPELINES_AND_USER_FLOWS.md`, 영상 구조화는 `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md` 참고.

> 원본 소스를 직접 인제스트하는 경우, RAG 파이프라인(Chunking → Enrichment → Embedding → Index)과
> hybrid search 및 retrieval 평가를 거쳐 승격한다.

### 1.3 Creator → Generation 파이프라인

1. 템플릿 카드 선택 → 캔버스 로드
2. 캡슐 파라미터 조정 → 실행 요약 확인
3. GA/RL 추천 반영 → 스펙 고정
4. Script/Storyboard 프리뷰 생성
5. Scene/Audio 합성 → 최종 Export

### 1.4 사용자/역할 흐름

사용자/역할 흐름은 `10_PIPELINES_AND_USER_FLOWS.md`에 정본화한다.

### 1.5 RAG/LLMOps 정렬 (2025-12 기준)

- **RAG 설계**: chunking → enrichment → embedding → index → hybrid search 단계 분리
- **RAG 평가**: retrieval + end-to-end 평가(groundedness, relevancy, completeness) 기록
- **오케스트레이션**: tool routing + context packaging, 장기 작업은 이벤트/큐로 분리
- **LLMOps**: 프롬프트/체인도 버전 관리, 오프라인 평가셋 + 휴먼 피드백 기반 개선
- **운영**: Dev/QA/Prod 분리, CI/CD, 모니터링/알림
---

## 2) 데이터 모델 (핵심)

### 2.1 Canvas Graph

```typescript
interface Canvas {
  id: string;
  ownerId?: string;
  title: string;
  nodes: Node[];
  edges: Edge[];
  version: number;
  isPublic: boolean;
  createdAt: string;
  updatedAt: string;
}

interface Node {
  id: string;
  type: "input" | "style" | "customization" | "processing" | "output" | "capsule";
  position: { x: number; y: number };
  data: Record<string, unknown>;
}

interface Edge {
  id: string;
  source: string;
  target: string;
  data?: Record<string, unknown>;
}
```

### 2.2 Capsule Node Spec

```typescript
interface CapsuleNodeSpec {
  id: string; // example: "auteur.bong-joon-ho"
  version: string; // semantic version
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
  outputs: Record<string, { type: string }>; // summary-only by default
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
  params: Record<string, unknown>;
  locked: boolean; // UI cannot open internal graph
}
```

Note: `contextMode=sequential`이면 `upstreamContext.sequence`에 위상 정렬된 노드 리스트를 포함한다.  
`contextMode=aggregate`이면 `upstreamContext.mode=aggregate`를 포함한다.

### 2.3 Template

```typescript
interface Template {
  id: string;
  title: string;
  graphData: Canvas;
  tags: string[];
  price?: number;
  creatorId?: string;
  version: number;
  isPublic: boolean;
  createdAt: string;
  updatedAt: string;
}

interface TemplateVersion {
  id: string;
  templateId: string;
  version: number;
  graphData: Canvas;
  notes?: string;
  creatorId?: string;
  createdAt: string;
}
```

### 2.4 Node Run / Generation Run

```typescript
interface NodeRun {
  id: string;
  nodeId: string;
  capsuleId?: string;
  capsuleVersion?: string;
  status: "queued" | "running" | "done" | "failed";
  upstreamContext?: Record<string, unknown>;
  outputSummary?: Record<string, unknown>;
  evidenceRefs?: string[];
  tokenUsage?: { input: number; output: number; total: number };
  latencyMs?: number;
  costUsdEst?: number;
  evalScores?: { groundedness?: number; relevancy?: number; completeness?: number };
  ownerId?: string;
  createdAt: string;
  updatedAt: string;
}

interface GenerationRun {
  id: string;
  canvasId: string;
  spec: Record<string, unknown>;
  status: "queued" | "running" | "done" | "failed";
  outputs: {
    previewUrl?: string;
    videoUrl?: string;
    audioUrl?: string;
    metadataUrl?: string;
  };
  ownerId?: string;
  createdAt: string;
  updatedAt: string;
}
```

### 2.5 Pattern Library / Trace (Evidence Loop)

```typescript
interface Pattern {
  id: string;
  name: string;
  patternType: "hook" | "scene" | "subtitle" | "audio" | "pacing";
  description?: string;
  status: "proposed" | "validated" | "promoted";
  createdAt: string;
  updatedAt: string;
}

interface PatternTrace {
  id: string;
  sourceAssetId: string;
  patternId: string;
  weight?: number; // 0~1
  evidenceRefs?: string[];
  createdAt: string;
}
```

### 2.6 Notebook Library (Canonical, private)

```typescript
interface NotebookLibrary {
  id: string;
  title: string;
  notebookRef: string; // notebooklm id/url
  auteurClusterId?: string; // cluster grouping (auteur/genre)
  auteurClusterLabel?: string; // human-readable label
  clusterTags?: string[];
  sourceCount: number;
  createdAt: string;
  updatedAt: string;
}

interface NotebookOutput {
  id: string;
  notebookId: string;
  sourceId: string;
  summary: string;
  labels: string[];
  outputType?: "summary" | "homage" | "variation_guide" | "template_fit";
  variationGuide?: string; // how to adapt or remix
  homageGuide?: string; // homage checklist
  templateRecommendations?: string[]; // template ids or slugs
  userFitNotes?: string; // persona or taste alignment notes
  evidenceRefs?: string[];
  promptVersion: string;
  modelVersion: string;
  generatedAt: string;
}
```

### 2.7 Video Structured Segment (Gemini)

```typescript
interface VideoSegment {
  id: string;
  sourceId: string;
  timeStart: string; // HH:MM:SS.mmm
  timeEnd: string; // HH:MM:SS.mmm
  shotIndex?: number;
  keyframes?: string[];
  transcript?: string;
  visualSchema?: Record<string, unknown>;
  audioSchema?: Record<string, unknown>;
  motifs?: string[];
  promptVersion: string;
  modelVersion: string;
  confidence?: number;
  generatedAt: string;
}
```

### 2.8 Tong Dataset (Synapse) Entities

```typescript
interface VisualSchema {
  composition?: string;
  lighting?: string;
  colorPalette?: string[];
  cameraMotion?: string;
  lensDepth?: string;
  blocking?: string;
  pacing?: string;
}

interface PersonaProfile {
  id: string;
  name: string;
  traits?: string[];
  philosophy?: string;
  motifs?: string[];
  notes?: string;
  sourceRefs?: string[];
}

interface SynapseRule {
  id: string;
  originPersonaRef?: string; // B
  filterPersonaRef?: string; // D
  ruleSummary: string; // A+B -> C transform
  transformSteps?: string[];
  constraints?: string[];
  confidence?: number;
}
```

### 2.9 Ingestion / Evidence Record (NotebookLM → Sheets → DB)

```typescript
interface EvidenceRecord {
  id: string;
  sourceId: string;
  sourceUrl: string;
  summary: string;
  guideType?: string; // summary/homage/variation/template_fit/persona/synapse/story/beat_sheet/storyboard
  outputType?: string; // video_overview/audio_overview/mind_map/report
  outputLanguage?: string;
  storyBeats?: Array<Record<string, unknown>>;
  storyboardCards?: Array<Record<string, unknown>>;
  keyPatterns?: Array<Record<string, unknown>>;
  evidenceRefs?: string[];
  labels: string[];
  notebookRef?: string;
  promptVersion: string;
  modelVersion: string;
  confidence?: number;
  createdAt: string;
}
```

> Video 구조화 출력은 `VideoSegment`에 저장하고, EvidenceRecord는 NotebookLM/Opal 요약 전용으로 유지한다.

---

## 3) Node Compute Engine

- **입력 노드**: 캐릭터, 감정, 배경, 시간
- **스타일 노드**: 거장 스타일, 컬러 톤, 구도, 페이싱
- **커스터마이징 노드**: 유저 미학, 음악, 개인 서사
- **처리 노드**: Auto Calculate, GA, RL
- **출력 노드**: 최종 Spec, Render 요청

계산 방식:
- 노드별 `compute(inputs) -> outputs` 규칙 적용
- 변경된 노드만 재계산하여 0.5초 내 미리보기

---

## 4) Capsule Node Architecture

### 4.1 Public Graph vs Private Subgraph

- **Public Graph**: 사용자에게 보이는 노드/엣지 (캔버스 UI)
- **Private Subgraph**: 서버 내부에서만 실행되는 DAG
- 캡슐 노드는 **입력/출력 포트 + 노출 파라미터만** UI에 표시

### 4.2 Node Adapter

```text
execute(nodeInstance, inputPayload) -> { summary, evidenceRefs }
```

- NotebookLM/Opal/외부 모듈은 Adapter로 연결
- 결과는 **요약/참조만 반환**하고 원문/프롬프트는 절대 클라이언트로 보내지 않음
- Adapter는 필요 시 **Sheets Bus에 기록**하고 DB 승격은 별도 파이프라인에서 수행
- inputPayload에는 **upstream_context**가 포함되어 캡슐이 전체 문맥을 읽을 수 있음

### 4.3 실행 흐름

1. 캔버스에서 캡슐 노드 실행 요청
2. 서버가 upstream_context 수집 및 계약 검증
3. Private Subgraph 실행 (NotebookLM/Opal 포함)
4. 요약 결과 + 참조만 반환
5. 노드 출력으로 주입

### 4.4 노출 파라미터 규칙

- 고가치 캡슐은 **슬라이더/선택형만** 노출
- 자유 텍스트 입력은 제한 또는 관리자 전용
- 파라미터와 버전은 실행 기록에 고정

### 4.5 Evidence 처리 원칙

- NotebookLM/Opal 결과는 **Derived 레이어**로만 저장
- DB SoR에는 **검증된 Pattern/Trace**만 승격
- 캡슐 실행 응답에는 summary + evidenceRef만 제공

---

## 5) AI Generation Pipeline (MVP → 고도화)

1. **Script/Beat Sheet 생성** (텍스트/시퀀스)
2. **Storyboard 생성** (컷 단위 이미지/요약)
3. **Scene Generation** (영상 모델 or 이미지 + 모션)
4. **Audio/Music** (BGM, SFX, VO)
5. **Compositing** (자막/이펙트/컷 편집)
6. **Export** (MP4/WebM/GIF)

MVP에서는 1~2단계만 구현하고, 후속 단계는 플러그형으로 확장한다.

---

## 6) 서비스 구성 (권장)

- **Canvas Service**: 그래프 저장/버전 관리
- **Template Service**: 템플릿 저장/마켓
- **Capsule Service**: 캡슐 스펙/버전/어댑터 실행
- **Spec Engine**: 노드 계산 + 규칙 기반 검증
- **Optimization Service**: GA/RL 최적화
- **Model Gateway**: 외부 모델 호출 표준화
- **Asset Service**: 오브젝트 스토리지 + 메타데이터
- **Ingestion Service**: 거장 레퍼런스 수집/메타 정리
- **Evidence Service**: Pattern Library/Trace/승격 관리
- **Sheets Connector**: NotebookLM/Opal 결과 수집/정규화
- **Analytics**: 품질/성능/피드백 로그
- **Observability**: 실행 추적, 비용/지연, 에러 알림

---

## 7) 스토리지/인프라

- **Postgres (JSONB)**: 캔버스, 템플릿, 실행 기록, 패턴 라이브러리
- **Object Storage (S3/GCS)**: 생성된 영상/이미지/오디오
- **Vector DB**: 스타일/프롬프트/미학 임베딩
- **Sheets Bus**: NotebookLM/Opal Derived 결과 스테이징
- **Queue**: 생성 작업 비동기 처리
- **GPU Cluster**: 고품질 생성 모델 실행

---

## 8) Observability & Evaluation (최신 기준)

- **Run Trace**: 캡슐/생성 실행의 trace_id, 버전, 근거 링크 저장
- **품질 지표**: 스타일 유사도, 완성도, 비용/지연, 사용자 선택률
- **데이터 거버넌스**: source_url, prompt_version, model_version 기록
- **경보/리커버리**: 실패 재시도, 비용 초과 차단, 품질 하한선

---

## 9) Event-driven + 마이그레이션 전략

- 초기: **NotebookLM/Opal → Sheets Bus → DB SoR** (저개발/고속)
- 확장: 수집/요약/생성 작업을 **큐 기반 이벤트**로 분리
- 최종: DB/Queue/Observability 중심의 표준 파이프라인으로 전환

## 10) NotebookLM / Google Opal 활용 (운영 설계 포함)

### NotebookLM (2025-12 최신)
- Video/Audio Overviews, Studio 다중 출력, Mind Map, 출력 언어 선택 활용
- 대량 문서 요약/지식 베이스 구축 → 캔버스 설계에 반영
- 영상 해석은 Gemini 구조화 출력으로 **DB SoR**에 적재 후 NotebookLM 소스로 사용
- 거장/장르 **클러스터 노트북** 생성 + **오마주/변주 가이드** 출력
- 사용자 성향 기반 **템플릿 적합도/추천**은 지식 레이어로만 제공
- **Ultra 구독 기준**: 출력 한도/다중 포맷 생성에 유리 (현재 Ultra)
- 결과는 **Sheets Bus**에 기록 후 DB 승격 (Derived only)
- **캡슐 노드 내부 서브그래프**에서 실행 후 요약만 전달

### Google Opal
- 노코드 미니앱 제작으로 내부 도구를 빠르게 구축
- 프롬프트 워크플로우, 라벨링, QA 체크, 템플릿 검수 자동화
- Gemini 웹앱 내 Opal 실험 기능으로 즉시 공유/배포
- **캡슐 노드 실행 체인**으로 래핑

---

## 11) 보안/거버넌스

- 템플릿 라이선싱, 사용 기록, 수익 쉐어 추적
- 저작권/출처 메타데이터 자동 기록
- 민감 데이터 분리 및 접근 제어
- 캡슐 노드의 프롬프트/워크플로우는 서버에서만 보관

---

## 12) API 스케치 (MVP)

- `GET /api/v1/templates/`
- `PATCH /api/v1/templates/{id}`
- `GET /api/v1/templates/{id}/versions`
- `POST /api/v1/canvases/from-template`
- `POST /api/v1/canvases/`
- `GET /api/v1/canvases/`
- `GET /api/v1/canvases/{id}`
- `PATCH /api/v1/canvases/{id}`
- `GET /api/v1/capsules/`
- `GET /api/v1/capsules/{capsule_key}`
- `GET /api/v1/capsules/{capsule_key}/runs`
- `POST /api/v1/capsules/run`
- `GET /api/v1/capsules/{capsule_key}/runs/{run_id}/preview`
- `POST /api/v1/runs/`
- `GET /api/v1/runs/{id}`

Auth (MVP): `X-User-Id` header for private canvases/templates/runs.

Dataization (MVP):
- `POST /api/v1/ingest/raw`
- `POST /api/v1/ingest/video-structured` (optional)
- `POST /api/v1/ingest/derive`
- `POST /api/v1/ingest/pattern-candidate`

---

## 13) 성능 목표 (MVP)

- 캔버스 미리보기: 500ms 이하
- 저장/불러오기: 200ms 이하
- 캡슐 실행 요약: 3초 내 반환 (캐시 히트 기준)
- GA 추천: 3초 내 상위 3개 반환

---

## 14) 참고 문서 (리서치 기반)

- NotebookLM 공식 업데이트 및 기능: 2025-03 / 2025-07 / 2025-12 (Google Workspace Updates, Google Labs)
- Google Opal 공식 소개 및 실험: 2025-07 / 2025-12 (Google Developers Blog, Google Labs)
- `08_SHEETS_SCHEMA_V1.md`
- `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`
- `10_PIPELINES_AND_USER_FLOWS.md`
- `11_DB_PROMOTION_RULES_V1.md`
- `12_PATTERN_PROMOTION_CRITERIA_V1.md`
- `13_UI_DESIGN_GUIDE_2025-12.md`
- `14_INGEST_RUNBOOK_V1.md`
- `15_PATTERN_TAXONOMY_V1.md`
- `16_VIRLO_CONTENT_STUDIO_RESEARCH.md`
- `17_CREDITS_AND_BILLING_SPEC_V1.md`
- `35_AFFILIATE_PROGRAM_SPEC_V1.md`
