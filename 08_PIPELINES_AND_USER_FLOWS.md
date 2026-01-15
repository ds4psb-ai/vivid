# Pipelines & User Flows (2025-12)

<details open>
<summary>한국어</summary>

**작성**: 2025-12-24  
**Updated**: 2026-01-01 (Chat-First Studio 추가)  
**대상**: Product / Design / Engineering  
**목표**: 데이터화 파이프라인과 워크플로우 사용자 흐름을 한 장으로 정리

---

## 0) Canonical Scope

이 문서는 **흐름/역할의 단일 기준**입니다.  
다른 문서는 이 내용을 반복하지 않고 링크로 참조합니다.
원칙/철학은 `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`에서 고정한다.
E2E 상세 파이프라인은 `docs/archive/21_AUTEUR_PIPELINE_E2E_CODEX.md`를 참조한다.
프로덕션(샷 생성/후반) 상세는 `docs/archive/22_AI_PRODUCTION_PIPELINE_CODEX.md`를 참조한다.

---

## 0.1 System Roles (Gemini / NotebookLM / Opal / DB SoR)

- **Gemini 3 Pro/Flash**: 영상 구조화(JSON Schema) 전용 엔진  
  - ASR + 샷/키프레임 기반의 **scene/shot schema** 생성  
  - 결과는 **DB SoR(Video Schema)**에 적재 (NotebookLM 소스는 DB 요약본)  
  - 상세 스펙: `docs/archive/19_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`
- **NotebookLM**: 지식/가이드 레이어 (Light RAG)  
  - 거장/장르 **클러스터 노트북** 운영  
  - 요약/오마주/변주/템플릿 적합도 가이드 출력  
  - Persona/Synapse Logic은 guide_type=persona/synapse로 축적  
  - Studio 다중 출력(Video/Audio/Mind Map) + 출력 언어 선택은 가이드 강화에 사용  
  - 업로드 소스는 SoR가 아니며, 결과는 Sheets Bus → DB 승격 규칙을 따른다  
  - Ultra 구독 기준 다중 출력/대량 처리에 유리  
  - Mega-Notebook은 **발굴/집계/운영 레이어**로만 사용하며, 캡슐은 **phase-locked pack**에서만 승격  
  - 출력 규격: `docs/archive/07_NOTEBOOKLM_OUTPUT_SPEC_V1.md`
  - 소스팩/프롬프트 프로토콜: `docs/archive/25_NOTEBOOKLM_SOURCE_PACK_PROTOCOL_CODEX.md`
- **Opal**: 템플릿 시드 + 내부 워크플로 자동화  
  - 라벨링/QA/프롬프트 체인 도구화  
  - 캡슐 노드 내부 서브그래프로만 실행
- **Sheets Bus**: 운영/검수용 스테이징  
  - DB SoR가 **증명/학습의 정본**  
  - 승격 규칙: `docs/archive/09_DB_PROMOTION_RULES_V1.md`

---

## 1) Dataization Pipeline (Evidence Loop)

```
Admin Ingest
  → Preprocess (ASR/Shot/Keyframe)
  → Gemini Structured Output (Video Schema)
  → DB SoR (Video Schema)
  → (Optional) Mega-Notebook (Discovery/Ops)
  → NotebookLM Source Pack Builder (cluster_id + temporal_phase)
  → NotebookLM/Opal (Guide)
  → Notebook Library (Private)
  → Notebook Assets (Private)
  → Sheets Bus (Derived)
  → Review/Normalize
  → DB SoR (Pattern Library/Trace)
  → Capsule Spec Update
```

핵심 규칙:
- NotebookLM/Opal은 **요약/라벨**만 담당
- 원본 영상은 NotebookLM에 직접 넣지 않고 **구조화 데이터(DB SoR)**로 변환 후 사용
- Notebook Library는 **비공개 지식 베이스**이며 사용자에게 직접 노출하지 않음
- Notebook Assets는 **노트북이 참조하는 자산 링크**이며 관리자 전용
- NotebookLM은 **지식/가이드 레이어**로서 클러스터 요약, 오마주/변주 가이드, 템플릿 적합도 제안을 제공
- Mega-Notebook은 **발굴/집계/운영 전용**이며, 캡슐 승격은 **phase-locked pack**으로만 수행
- Persona/Profile 및 Synapse Logic은 **guide_type=persona/synapse**로 구분해 축적
- Story/Beat/Storyboard는 **guide_type=story/beat_sheet/storyboard**로 구분하고 `story_beats`/`storyboard_cards`에 저장
- DB에 승격되는 것은 **검증된 패턴**만
- `evidence_refs` 포맷 (2026-01-13):
  - `db:capsule_runs:{uuid}` - CapsuleRun 기반 증거
  - `db:rag_docs:{dimension}:{dataset_id}:{doc_id}` - RAG 검색 결과
  - **지원 데이터셋**: `video_ref`, `image_grid`, `film_analysis`, `visual_style`
  - 서버에서 형식 보장 (`build_evidence_ref_id` 함수)
- 모든 결과는 **source_id + prompt/model/version**로 추적
- 승격 기준은 `docs/archive/12_PATTERN_PROMOTION_CRITERIA_V1.md`

---

## 2) Creator Pipeline (Flow → Execute)

```
Flow (Train UI)
  → 연결 고리 선택 (3옵션)
  → Teaching Tool 실행
  → 결과 확인/재시도
  → (필요시) Dimension 미니앱으로 보완
```

핵심 규칙:
- 연결 고리는 3개 옵션 중 하나를 선택하도록 제한
- 각 도구는 Dimension API(`/api/dimension/*`)로 실행
- Flow UI는 현재 **Mock 옵션** 기반이며 `/api/v1/workflow` 연동은 진행 중

> Legacy: Canvas 기반 파이프라인은 `_deprecated` 경로에서만 유지됩니다.

### 2.0.1 Story-First Creator Flow (Legacy)

서사 중심 바이럴 콘텐츠 제작 흐름:

```
Canvas Load (legacy)
  → CanvasNarrativePanel 활성화
  → 부조화 설계 (익숙함 ↔ 낯섦)
  → 감정 곡선 설정 (시작/절정/결말)
  → 훅 스타일 선택 (8종)
  → [Optional] A/B 테스트 변형 선택 (2~4개)
  → Capsule Run (Story-First params 포함)
  → DNAComplianceViewer (DNA 준수 확인)
  → Preview / Generate
  → MetricsDashboard (성과 분석)
```

핵심 규칙:
- **Story-First 파라미터**: `narrative_arc`, `hook_variant` 필드로 캡슐에 전달
- **A/B 테스트**: 여러 훅 변형을 선택하여 비교 생성 가능
- **DNA 준수**: 브랜드 가이드라인 위반 시 자동 수정 제안

### 2.1 Production Pipeline (AI Video)

```
Beat Sheet
  → Shot List
  → Storyboard (Nano-banana Pro)
  → Prompt Contract (Shot Contract 기반)
  → Gen Run (Veo 3.1 / Kling)
  → Continuity QC
  → Edit / Sound / Color / Final Export
```

운영 규칙:
- **샷 단위 생성**이 기본이며, Scene/Sequence는 Shot을 묶어 구성
- 프롬프트는 **5~10개 묶음**으로 병렬 실행 후 선별
- **일관성 우선**이면 Image-to-Video, **역동성 우선**이면 Text-to-Video
- 상세 규격은 `22_AI_PRODUCTION_PIPELINE_CODEX.md`를 따른다

### 2.2 Agent Chat (Chokki)

```
Agent Chat (Global)
  → /api/v1/agent/chat (SSE)
  → Tool calls + artifacts
  → (optional) Workflow plan 생성
```

핵심 규칙:
- 채팅은 전역 컴포넌트(Chokki)로 제공된다.
- 스트리밍은 SSE 이벤트로 tool 결과/아티팩트를 즉시 갱신한다.
- 캔버스 동기화는 현재 비활성(레거시 UI만 유지).

---

## 3) User Roles & Responsibilities

- **Admin/Curator**: 원본 수집, NotebookLM 실행, 승격 판단
- **Librarian**: Notebook Library 정리 및 소스 연결 관리
- **Creator (Self-Style)**: 개인 자료를 노트북으로 축적, 자기 색깔 가이드 생성
- **Creator**: 템플릿 선택, 캡슐 파라미터 조정, 프리뷰/생성
- **Reviewer**: 품질 평가, 재사용/승격 근거 제공
- **Ops**: Pipeline Ops 화면에서 상태/Sheets 동기화/쿼런틴/패턴 승격/템플릿 시드/실행 로그 점검

### 3.1 Access & Session Gate (Auth)

- Admin/Ops 화면은 **세션 기반 역할(Role)**로 접근 제어한다.
- 로그인 미인증 상태에서는 **admin-only + 로그인 CTA**를 제공한다.
- 캡슐/템플릿의 **공개 편집은 허용하지 않는다** (서버에서 강제).
- 인증은 **Google OAuth + 세션 쿠키**가 기본이며, `X-User-Id`는 개발용 fallback이다.

---

## 4) Event Boundaries (확장 시점)

- `ingest.raw` → `derive.summary` → `promote.pattern`
- `capsule.run` → `capsule.stream` → `preview.generate` → `final.generate`
- `capsule.cancel` → `run.cancelled` (사용자 중단)
- 모든 이벤트는 trace_id로 연결

</details>

<details>
<summary>English</summary>

**Created**: 2025-12-24  
**Updated**: 2026-01-01 (Chat-First Studio added)  
**Audience**: Product / Design / Engineering  
**Goal**: Summarize the dataization pipeline and user workflow flows on one page

---

## 0) Canonical Scope

This document is the **single source of truth for flows and roles**.  
Other documents should link to it rather than repeating the content.
Principles/philosophy are fixed in `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`.
E2E pipeline details are in `docs/archive/21_AUTEUR_PIPELINE_E2E_CODEX.md`.
Production (shot generation/post) details are in `docs/archive/22_AI_PRODUCTION_PIPELINE_CODEX.md`.

---

## 0.1 System Roles (Gemini / NotebookLM / Opal / DB SoR)

- **Gemini 3 Pro/Flash**: dedicated engine for video structuring (JSON Schema)  
  - Create **scene/shot schema** based on ASR + shots/keyframes  
  - Results are stored in **DB SoR (Video Schema)** (NotebookLM sources are DB summaries)  
  - Detailed spec: `docs/archive/19_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`
- **NotebookLM**: knowledge/guide layer (light RAG)  
  - Operate **auteur/genre cluster notebooks**  
  - Output summary/homage/variation/template fit guides  
  - Store Persona/Synapse Logic with guide_type=persona/synapse  
  - Studio multi-outputs (Video/Audio/Mind Map) + output language selection strengthen guides  
  - Uploaded sources are not SoR; results follow Sheets Bus → DB promotion rules  
  - Ultra subscription is better for multi-output/batch processing  
  - Mega-Notebook is **discovery/aggregation/ops only**, and capsules are promoted only from **phase-locked packs**  
  - Output spec: `docs/archive/07_NOTEBOOKLM_OUTPUT_SPEC_V1.md`
  - Source pack/prompt protocol: `docs/archive/25_NOTEBOOKLM_SOURCE_PACK_PROTOCOL_CODEX.md`
- **Opal**: template seeds + internal workflow automation  
  - Labeling/QA/prompt-chain tooling  
  - Runs only as a subgraph inside capsule nodes
- **Sheets Bus**: staging for ops and review  
  - DB SoR is the **canonical source for proof and learning**  
  - Promotion rules: `docs/archive/09_DB_PROMOTION_RULES_V1.md`

---

## 1) Dataization Pipeline (Evidence Loop)

```
Admin Ingest
  → Preprocess (ASR/Shot/Keyframe)
  → Gemini Structured Output (Video Schema)
  → DB SoR (Video Schema)
  → (Optional) Mega-Notebook (Discovery/Ops)
  → NotebookLM Source Pack Builder (cluster_id + temporal_phase)
  → NotebookLM/Opal (Guide)
  → Notebook Library (Private)
  → Notebook Assets (Private)
  → Sheets Bus (Derived)
  → Review/Normalize
  → DB SoR (Pattern Library/Trace)
  → Capsule Spec Update
```

Key rules:
- NotebookLM/Opal handle **summaries and labels only**
- Raw videos are not fed directly into NotebookLM; convert to **structured data (DB SoR)** first
- Notebook Library is a **private knowledge base** and never exposed to users
- Notebook Assets are **asset links referenced by notebooks** and are admin-only
- NotebookLM is the **knowledge/guide layer** that provides cluster summaries, homage/variation guides, and template fit suggestions
- Mega-Notebook is **discovery/aggregation/ops only**, and capsule promotion happens only via **phase-locked packs**
- Persona/Profile and Synapse Logic are stored under **guide_type=persona/synapse**
- Story/Beat/Storyboard are stored under **guide_type=story/beat_sheet/storyboard** in `story_beats`/`storyboard_cards`
- Only **verified patterns** are promoted into the DB
- `evidence_refs` format (2026-01-13):
  - `db:capsule_runs:{uuid}` - evidence from CapsuleRun
  - `db:rag_docs:{dimension}:{dataset_id}:{doc_id}` - RAG search results
  - **Supported datasets**: `video_ref`, `image_grid`, `film_analysis`, `visual_style`
  - Format guaranteed server-side (`build_evidence_ref_id` function)
- All results are tracked by **source_id + prompt/model/version**
- Promotion criteria: `docs/archive/12_PATTERN_PROMOTION_CRITERIA_V1.md`

---

## 2) Creator Pipeline (Flow → Execute)

```
Flow (Train UI)
  → Select connection link (3 options)
  → Execute Teaching Tool
  → Review/retry results
  → (If needed) supplement with Dimension mini-apps
```

Key rules:
- Connection links are limited to one of three options
- Each tool executes via the Dimension API (`/api/dimension/*`)
- Flow UI currently uses **mock options**; `/api/v1/workflow` integration is in progress

> Legacy: Canvas-based pipelines are kept only under the `_deprecated` path.

### 2.0.1 Story-First Creator Flow (Legacy)

Story-driven viral content creation flow:

```
Canvas Load (legacy)
  → CanvasNarrativePanel enable
  → Design dissonance (familiar ↔ unfamiliar)
  → Set emotional arc (start/climax/end)
  → Choose hook style (8 types)
  → [Optional] Select A/B test variants (2~4)
  → Capsule Run (with Story-First params)
  → DNAComplianceViewer (check DNA compliance)
  → Preview / Generate
  → MetricsDashboard (performance analysis)
```

Key rules:
- **Story-First params**: pass `narrative_arc` and `hook_variant` to the capsule
- **A/B testing**: generate and compare multiple hook variants
- **DNA compliance**: auto-suggest fixes on brand guideline violations

### 2.1 Production Pipeline (AI Video)

```
Beat Sheet
  → Shot List
  → Storyboard (Nano-banana Pro)
  → Prompt Contract (Shot Contract-based)
  → Gen Run (Veo 3.1 / Kling)
  → Continuity QC
  → Edit / Sound / Color / Final Export
```

Operational rules:
- **Shot-level generation** is the default; Scenes/Sequences group shots together
- Prompts are run in parallel in **batches of 5~10** and then curated
- **Consistency-first** uses Image-to-Video; **dynamism-first** uses Text-to-Video
- Follow `22_AI_PRODUCTION_PIPELINE_CODEX.md` for detailed specs

### 2.2 Agent Chat (Chokki)

```
Agent Chat (Global)
  → /api/v1/agent/chat (SSE)
  → Tool calls + artifacts
  → (optional) Generate workflow plan
```

Key rules:
- Chat is provided as a global component (Chokki).
- Streaming uses SSE events to update tool results and artifacts immediately.
- Canvas sync is currently disabled (legacy UI only).

---

## 3) User Roles & Responsibilities

- **Admin/Curator**: ingest sources, run NotebookLM, decide promotion
- **Librarian**: organize Notebook Library and manage source linking
- **Creator (Self-Style)**: collect personal materials into notebooks, generate personal style guides
- **Creator**: select templates, adjust capsule params, preview/generate
- **Reviewer**: evaluate quality, provide evidence for reuse/promotion
- **Ops**: check status/Sheets sync/quarantine/pattern promotion/template seeds/run logs in the Pipeline Ops view

### 3.1 Access & Session Gate (Auth)

- Admin/Ops screens are gated by **session-based roles**.
- When unauthenticated, show **admin-only + login CTA**.
- **Public editing is not allowed** for capsules/templates (enforced server-side).
- Auth uses **Google OAuth + session cookies**; `X-User-Id` is dev-only fallback.

---

## 4) Event Boundaries (Scaling Points)

- `ingest.raw` → `derive.summary` → `promote.pattern`
- `capsule.run` → `capsule.stream` → `preview.generate` → `final.generate`
- `capsule.cancel` → `run.cancelled` (user-initiated stop)
- All events are connected by trace_id

</details>
