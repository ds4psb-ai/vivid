# Crebit Architecture Evolution (CODEX v20)

<details open>
<summary>한국어</summary>

**Date**: 2025-12-24  
**Updated**: 2026-01-01  
**Status**: CODEX 기준선 (철학 보존)  
**Purpose**: 리버스 엔지니어링 학습을 Crebit 전용 아키텍처 개선으로 전환하되 원래 철학을 훼손하지 않는다.

---

## 0) 결정 요약 (이 문서가 고정하는 것)

- NotebookLM Library는 거장 지식의 정본이며, 최종 사용자는 원본 노트북을 보지 않는다.
- NotebookLM은 **지식/가이드 레이어**이다: 거장별 노트북을 클러스터링하고 오마주/변주 가이드와 템플릿 적합도 제안을 출력한다.
- Mega-Notebook은 **발굴/집계/운영 레이어**로만 사용하며, 캡슐 승격은 **phase-locked source pack**에서만 한다.
- 비디오 이해는 **Gemini 3 Pro 구조화 출력**을 사용하며, NotebookLM 이전에 DB SoR에 저장한다.
- LLM 래핑 노드는 sealed capsule이며, 입력/출력 포트와 공개 파라미터만 노출한다.
- Evidence Loop가 엔진이다: Sheets Bus -> DB SoR -> Pattern Library/Trace -> Capsule/Template 진화.
- 템플릿은 1급 객체이자 학습 대상이다: GA가 탐색하고, RL이 최적화하며, 증거가 승격을 촉진한다.
- 크레딧 + 관측성은 핵심 UX이다(설정에 숨기지 않는다).
- UI 흐름은 "Pick -> Connect -> Run" 열차 워크플로우를 유지하고, 노드 그래프는 내부에 둔다.
- Admin/Ops 접근은 **세션 + 역할** 기반이며, SoR나 프롬프트의 공개 편집은 금지한다.
- Agent Chat + Flow/Dimension이 1순위이고, Canvas는 레거시/내부용이다.

---

## 1) 비타협 철학 (Crebit DNA)

1. **NotebookLM Library는 거장 지식의 정본**  
   - 거장/대중 작품에서 큐레이션된 노트북은 증거 라이브러리가 된다.  
   - 노트북은 사용자에게 직접 노출하지 않고, 요약 출력과 evidence refs만 제공한다.
   - Mega-Notebook은 **분석/운영 집계용**이며, 캡슐/템플릿 승격에 직접 사용하지 않는다.

2. **LLM 래핑 노드는 sealed capsule**  
   - 사용자는 입력과 공개 파라미터만 조정한다.  
   - 내부 체인, 프롬프트, 워크플로우는 서버에서만 유지된다.

3. **Evidence Loop가 엔진**  
   - Sheets Bus -> DB SoR -> Pattern Library/Trace -> Capsule Spec.  
   - NotebookLM/Opal은 가속기이며 SoR이 아니다.

4. **템플릿은 1급 객체이자 학습 대상**  
   - Creator/PD/Writer 파이프라인은 템플릿으로 정의된다.  
   - 템플릿은 증거 기반 피드백을 통해 GA/RL로 진화한다.

5. **Chat-first 오케스트레이션 (Agent Studio)**  
   - Agent Chat이 워크플로우를 컴파일하고 도구를 실행하며, Flow/Dimension UI가 기본이고 Canvas는 내부용이다.  
   - 도구 출력은 evidence refs가 포함된 표준 아티팩트로 제공한다.

---

## 2) 2025-12 아키텍처 기준선 ("modern"의 의미)

- 입력 계약과 컨텍스트 집계를 갖춘 타입드 그래프 워크플로우.
- 구조화 출력 + provenance(증거 참조)가 신뢰의 필수 조건.
- sealed composite(캡슐)로 프롬프트와 내부 체인을 보호.
- 비용 투명성: 실행 단위 토큰, 지연, 크레딧 원장.
- 드리프트 방지를 위한 멀티 모델 어댑터와 버전 계약.
- "Creator Hub" UX: 빠른 빈 상태 온보딩, 템플릿 중심 흐름.

### 2.1 리서치 기반 추가 요소 (RAG/LLMOps/Inference)

- RAG 규율: chunking → enrichment → embedding → index → hybrid search, 그리고 **단계별 평가**.
- 오케스트레이터 중심 실행: 툴 라우팅 + 컨텍스트 패키징, 장기 작업은 이벤트 기반.
- LLMOps: 프롬프트/체인 버저닝, 오프라인 평가셋 + 휴먼 피드백, CI/CD + Dev/QA/Prod 게이트.
- 인퍼런스 최적화: 저지연, 동적 스케일링, 캐싱, 비용 제어.

### 2.2 S2S 보안 및 앱 무결성 (현재)

- **Run Token**: `/api/v1/run-token/*`에서 실행 토큰 발급/검증/차감 수행 (fingerprint 바인딩, 단기 TTL).
- **Internal S2S**: `/api/v1/internal/*`는 mTLS 미들웨어로 보호되며 `MTLS_ENABLED=true`일 때 강제.
- **2-Phase Credit Commit**: `credit-reserve/commit/rollback`으로 앱 실행 크레딧을 이중 검증.
- **Gateway**: `backend/deploy/api-gateway.yaml`는 배포 옵션이며 코드 상 강제 경로는 아님.

---

## 3) Crebit 레퍼런스 아키텍처 (Layered)

```
Sources -> Gemini Structuring -> Video Schema DB -> NotebookLM Library -> Sheets Bus -> DB SoR
  -> Pattern Library/Trace -> Capsule Specs -> Templates
  -> Workflow Runs -> Evidence -> Learning (GA/RL)
```

### 3.1 Knowledge Layer: Notebook Library

**엔티티**
- NotebookLibrary: 큐레이션된 노트북 메타데이터.
- NotebookAssets: 영화, 장면, 대본, 스틸 참조.
- NotebookOutputs: 요약 + 패턴 라벨 + 증거 참조.

**불변 조건**
- 라이브러리 데이터는 비공개이며, 사용자에게는 파생 출력만 제공한다.

**Guide layer (NotebookLM)**
- 거장/장르 **클러스터 단위 노트북**을 유지한다.
- "요약/오마주/변주 가이드" 출력은 **가이드 레이어**로만 사용한다.
- 사용자 성향 기반 **템플릿 적합도/추천**은 참고 신호(최종 결정은 DB SoR).
- Mega-Notebook은 **클러스터/phase 집계**용이며, 캡슐 생성 시에는 **phase-locked source pack**으로 재구성한다.

### 3.2 Execution Layer: Capsule Nodes

**Capsule Types**
- Notebook Capsule: NotebookLM 출력에서 파생.
- Workflow Capsule: Opal 또는 내부 DAG runner.
- Hybrid Capsule: NotebookLM 요약 + 내부 룰 엔진.

**불변 조건**
- 공개 그래프는 포트 + 파라미터만 노출한다.
- 비공개 서브그래프는 서버에서 실행한다.

### 3.3 Template Layer: Creator/PD/Writer Pipelines

템플릿은 재사용 가능한 파이프라인 블루프린트:
- 숏폼 스크립트 파이프라인.
- 스토리보드 파이프라인.
- 비주얼 스타일 트랜스퍼 파이프라인.

템플릿은 학습 가능:
- GA가 변주를 탐색한다.
- RL이 증거 점수를 사용해 파라미터를 개선한다.

### 3.4 Tong Dataset (Synapse Framework) 매핑

통 데이터셋의 A/B/C/D 구조를 Crebit에 매핑하면 다음과 같다.

- **A (Origin Visual)**: Raw Asset + Visual Schema (조명/색/구도/동선 등)
- **B (Origin Persona)**: Origin Persona Profile (작가 철학/무의식/시대 맥락)
- **D (Filter Persona)**: Homage/Creator Persona Profile (필터 역할)
- **C (Result Visual)**: Capsule 실행/생성 결과의 Visual Schema
- **Synapse Rule**: A+B가 D를 거쳐 C로 변환되는 규칙(캡슐 스펙의 핵심 로직)

실행 원칙:
- B/D는 **NotebookLM 가이드 레이어**로 요약·라벨링
- Synapse Rule은 **DB SoR**에 구조화해 재현성을 확보
- 결과(C)는 **Evidence Loop**로 검증하고 Template Learning에 반영

---

## 3.5 로직/페르소나 융합 + 변주 프로토콜 (SoR)

통데이터셋화(A/B/C/D), 수학적 로직, 거장 페르소나, 둘의 결합, 신규 장르 변주 마이그레이션,
NotebookLM 소스 구성/가이드 추출 프로토콜은 아래 정본에서 고정한다.

- `25_NOTEBOOKLM_SOURCE_PACK_PROTOCOL_CODEX.md`

핵심 요약:
- **Logic Vector**(컷/구도/모티프/리듬) + **Persona Vector**(톤/감정/해석) 분리 후 결합
- **cluster_id + temporal_phase** 단위 노트북 운영
- 변주 추천은 NotebookLM 가이드 + Evidence/RL 점수로 보정

---

## 3.6 Intent → Capsule Resolver 패턴 (2026-01)

### 설계 철학

템플릿이 앱의 세부 파라미터를 직접 알지 않고, **"의도(Intent)"만 선언**한다.  
각 Dimension Capsule이 자체 **Resolver**로 Intent를 해석하여 최적 파라미터를 결정한다.

```
Template → Intent(mood, pace, target) → Capsule Resolver → Params → Execution
```

### Intent 스키마

모든 파이프라인이 공유하는 창작 의도 스키마:

| Attribute | Type | Description |
|-----------|------|-------------|
| `mood` | enum | cinematic, energetic, calm, documentary, experimental |
| `pace` | enum | fast, slow, dynamic, contemplative |
| `target` | enum | expert, beginner, general, kids |
| `domain_sources` | list | RAG 소스 힌트 (거장명, 장르, saju 등) |

### Capsule별 Resolver

각 Dimension App은 `resolve_from_intent(intent, rag_context) → params` 함수를 구현한다.

- **VEO Resolver**: mood=cinematic → lens=anamorphic, fps=24
- **Sound Resolver**: mood=cinematic → genre=orchestral, reverb=hall
- **Prompt Resolver**: mood + target → 프롬프트 톤/복잡도 조절

### 확장된 RAG 소스 (집단지성)

NotebookLM Library 외의 지식 소스를 통합하여 **집단지성 활용**:

| Source Type | Use Case | 기여 주체 |
|-------------|----------|----------|
| NotebookLM | 거장 페르소나, 작품 분석 | 큐레이터/전문가 |
| Papers | 영화 이론, 시각 연구 | 학술 기여자 |
| 사주/주역 DB | 시간/공간 기반 창작 가이드 | 동양철학 전문가 |
| Books | 예술/철학/교양 | 바이브 코더/일반 사용자 |

### Evidence Loop와의 통합

Intent-Quality 관계를 Evidence Loop에 기록하여 GA/RL 학습에 활용한다:

```
Intent → Resolved Params → Execution → Quality Score → Evidence
                                                        ↓
                                               Template Learning
```

### Benefits

1. **결합도 감소**: 앱 변경 시 템플릿 수정 불필요
2. **집단지성**: 비개발자가 RAG 소스에 지식 축적 → 시스템 자동 활용
3. **확장성**: 새 RAG 소스 추가 시 Resolver만 확장
4. **일관성**: 하나의 Intent로 전체 파이프라인 톤앤매너 통일

---

## 4) NotebookLM -> DB (정규화 파이프라인)

**목표**: NotebookLM 출력을 안정적이고 조회 가능하며 학습 가능한 데이터로 전환한다.

흐름:
1. 관리자가 소스를 큐레이션하고 Gemini 비디오 구조화(ASR + keyframe)를 실행한다.
2. 구조화 출력은 **Video Schema DB**에 저장된다.
3. NotebookLM 출력은 Sheets Bus(계약 스키마)로 전달된다.
4. Promotion 작업이 Sheets -> DB SoR로 매핑한다.
5. 패턴 + evidence refs를 Pattern Library/Trace에 저장한다.

**옵션: 내부 검색 인덱스(향후)**
- Crebit이 원천 소스를 직접 인제스트하는 경우 RAG 파이프라인을 따른다(chunk/enrich/embed).
- 프로모션 전에 하이브리드 검색(벡터 + 렉시컬)과 검색 평가를 수행한다.

**계약 의존성**
- `06_SHEETS_SCHEMA_V1.md`
- `07_NOTEBOOKLM_OUTPUT_SPEC_V1.md`
- `09_DB_PROMOTION_RULES_V1.md`
- `docs/archive/12_PATTERN_PROMOTION_CRITERIA_V1.md`

---

## 5) Capsule Node 계약 (필수 조건)

**NodeSpec (public)**
- `input_contracts`: 필수 입력, 허용 타입, 최대 upstream.
- `output_contracts`: 캡슐이 반환하는 타입.
- `exposed_params`: UI 컨트롤이 있는 파라미터 리스트.
- `capsule_id@version`: 재현성을 위한 고정 ID.

**CapsuleRun (private)**
- `upstream_context`: 연결된 upstream 출력의 스냅샷.
- `evidence_refs`: NotebookLibrary 또는 Pattern Trace 참조.
- `token_usage`, `latency_ms`, `cost_est_usd`.

---

## 6) Template Learning Loop (GA/RL)

**이유**: 템플릿은 원래 거장 DNA를 유지하면서 개선되어야 한다.

루프:
- 템플릿 실행 -> evidence score 수집.
- Pattern Trace와 Pattern Lift 기록.
- GA가 후보 파라미터 셋 생성.
- RL이 evidence reward로 다음 best set을 선택.
- 승자 템플릿을 새 버전으로 승격.

**가드레일**
- evidence 임계치를 충족할 때만 승격.
- 재현성 보장을 위해 capsule 버전을 유지.

---

## 7) 사용자 플로우 (Two Lanes)

사용자/역할 흐름은 `08_PIPELINES_AND_USER_FLOWS.md`에 정본화한다.

---

## 8) UX/IA 가이드 (RE 기반, 적용)

- Left rail: Research, Creator Hub, Accounts, Credits, Affiliate.
- Empty state: "Create First Workflow" + 1-click seed flow.
- Top bar: Run + Preview + Credit balance.
- Train workflow: car order + connection selector + status states (node graph hidden).

시각 시스템은 `10_UI_DESIGN_GUIDE_2025-12.md`를 참고한다.

---

## 9) Credits + Observability (필수)

**Credits**
- Promo -> Subscription -> Top-up 우선순위.
- 모든 실행/구매에 대한 원장 기록.

**Observability**
- 실행 단위 토큰 사용량, 지연, 비용 추정.
- 템플릿 학습을 위한 캡슐 레벨 분석.
- 평가 지표: groundedness, completeness, relevancy, evidence coverage.

---

## 10) Security / IP Protection

- 원본 노트북, 프롬프트, 내부 체인을 클라이언트에 전달하지 않는다.
- 요약 + evidence refs만 반환한다.
- 관리자 리뷰는 역할 기반 접근으로 제한한다.
- 캡슐 실행과 승격에 대한 감사 추적을 남긴다.

---

## 11) 선택적 개방 정책 (Reject 항목 리뷰)

모든 것을 공개하지 않는다. IP 누출, 증거 약화, 재현성 훼손 위험만 잠근다.

결정 규칙:
- 원본 프롬프트나 내부 체인을 노출한다면 sealed 유지.
- IP를 노출하지 않고 크리에이터 제어를 높인다면 안전한 파라미터/템플릿 변형으로 허용.
- Evidence Loop나 DB SoR을 우회한다면 서버 사이드 유지.

항목별 판단:
- Open multi-model selector  
  결정: **최종 사용자에겐 비공개**, **model tier** 또는 **capsule variant** 선택만 허용.  
  이유: sealed capsule을 유지하면서 통제된 커스터마이징을 제공.

- Real-time prompt editing  
  결정: **공개 편집 금지**, **admin 전용 prompt 모듈** 또는 Opal 워크플로우 허용.  
  이유: IP를 보호하면서 내부 반복을 지원.

- Supabase direct client  
  결정: **클라이언트 SoR 직접 접근 금지**, 인증 또는 읽기 전용 메타데이터에 한해 Supabase 옵션 허용.  
  이유: Evidence Loop + DB 무결성은 서버 강제가 필요.

---

## 12) 마이그레이션 전략 (Breaking changes 없음)

Phase 0: 문서 정렬 및 계약 동결.  
Phase 1: 누락된 스키마 필드 추가 (input contracts, upstream context).  
Phase 2: 캡슐 실행 + 프리뷰 파이프라인.  
Phase 3: 템플릿 학습 루프 (GA/RL) + 승격 규칙.  
Phase 4: 크레딧, 어필리에이트, 관측성 강화.

---

## 13) 문서 정렬 권고 (컨설팅)

CODEX v20을 정본으로 채택한다면, 다음 문서를 정렬한다:

- `00_EXECUTIVE_SUMMARY_NODE_CANVAS.md`: Notebook Library를 정본 레이어로 추가.
- `01_NODE_CANVAS_TECHNICAL_SPECIFICATION.md`: input/output contracts + upstream context 추가.
- `04_CAPSULE_NODE_SPEC.md`: capsule_id@version, evidence refs, cost 필드 추가.
- `06_SHEETS_SCHEMA_V1.md`: Notebook Library + Pattern Trace 출력 추가.
- `08_PIPELINES_AND_USER_FLOWS.md`: Admin vs Creator 플로우 분리.
- `10_UI_DESIGN_GUIDE_2025-12.md`: nav + empty-state + credit balance 추가.
- `11_INGEST_RUNBOOK_V1.md`: NotebookLM 실행 + Sheets 승격 상세.
- `13_CREDITS_AND_BILLING_SPEC_V1.md`: 크레딧 우선순위 + 원장 확인.
- `26_AFFILIATE_PROGRAM_SPEC_V1.md`: 크레딧 리워드 흐름 정의 확인.
- `docs/archive/19_CREBIT_EXECUTION_PLAN_V1.md`: 이 문서에 맞게 단계 재정렬.

---

## 14) 결정 게이트 (사용자 결정)

1. v1 Library에 포함할 거장 노트북은?
2. v1 템플릿 타입(스크립트, 스토리보드, 비주얼)은?
3. 어떤 evidence 임계치로 템플릿 승격을 수행할 것인가?
4. 캡슐 실행당 기본 크레딧 비용은?
5. 공개 가능한 evidence 상세 수준은?

</details>

<details>
<summary>English</summary>

**Date**: 2025-12-24  
**Updated**: 2026-01-01  
**Status**: CODEX baseline (philosophy-preserving)  
**Purpose**: Convert reverse-engineering learnings into Crebit-specific architecture improvements without breaking the original philosophy.

---

## 0) Decision Summary (What this doc locks)

- NotebookLM Library is the canonical auteur knowledge base; end users never see raw notebooks.
- NotebookLM is the **knowledge/guide layer**: cluster notebooks per auteur and output homage/variation guidance + template fit suggestions.
- Mega-Notebook is used only as a **discovery/aggregation/operations layer**; capsule promotion happens only from **phase-locked source packs**.
- Video understanding uses **Gemini 3 Pro structured outputs** and is stored in DB SoR before NotebookLM.
- LLM-wrapped nodes are sealed capsules; only input/output ports + exposed params are public.
- Evidence Loop remains the engine: Sheets Bus -> DB SoR -> Pattern Library/Trace -> Capsule/Template evolution.
- Templates are first-class and learnable: GA explores, RL exploits, evidence promotes.
- Credits + observability are core UX (not hidden in settings).
- UI flow keeps "Pick -> Connect -> Run" train workflow; node graph stays internal.
- Admin/Ops access is **session + role** gated; no public editing of SoR or prompts.
- Agent Chat + Flow/Dimension are primary; Canvas is legacy/internal.

---

## 1) Non-Negotiable Philosophy (Crebit DNA)

1. **NotebookLM Library is the canonical auteur knowledge base**  
   - Curated notebooks from auteur/popular works become a library of evidence.  
   - These notebooks are never exposed to end users; only summary outputs + evidence refs are surfaced.
   - Mega-Notebook is for **analysis/ops aggregation** and is not used directly for capsule/template promotion.

2. **LLM-wrapped nodes are sealed capsules**  
   - Users can customize inputs + exposed params only.  
   - Internal chains, prompts, and workflows remain server-side.

3. **Evidence Loop remains the engine**  
   - Sheets Bus -> DB SoR -> Pattern Library/Trace -> Capsule Spec.  
   - NotebookLM/Opal are accelerators, not the source of truth.

4. **Templates are first-class and learnable**  
   - Creator/PD/Writer pipelines are defined as templates.  
   - Templates evolve via GA/RL using evidence-based feedback.

5. **Chat-first orchestration (Agent Studio)**  
   - Agent Chat compiles workflows and executes tools; Flow/Dimension are primary UI, Canvas is internal.  
   - Tool outputs are surfaced as standardized artifacts with evidence refs.

---

## 2) 2025-12 Architecture Baseline (What "modern" implies)

- Typed graph workflows with input contracts and context aggregation.
- Structured outputs + provenance (evidence refs) are required for trust.
- Sealed composites (capsules) protect prompts and internal chains.
- Cost transparency: per-run tokens, latency, and credit ledger.
- Multi-model adapters with versioned contracts to avoid drift.
- "Creator Hub" UX: fast empty-state onboarding, template-first flow.

### 2.1 Research-backed additions (RAG/LLMOps/Inference)

- RAG discipline: chunking → enrichment → embedding → index → hybrid search, and **per-phase evaluation**.
- Orchestrator-first execution: tool routing + context packaging, long jobs are event-driven.
- LLMOps: prompts/chains are versioned artifacts, offline eval sets + human feedback, CI/CD + Dev/QA/Prod gates.
- Inference optimization: low latency, dynamic scaling, caching, and cost controls.

### 2.2 S2S Security & App Integrity (Current)

- **Run Token**: issue/verify/deduct execution tokens at `/api/v1/run-token/*` (fingerprint binding, short TTL).
- **Internal S2S**: `/api/v1/internal/*` is protected by mTLS middleware and enforced when `MTLS_ENABLED=true`.
- **2-Phase Credit Commit**: double-verify app execution credits via `credit-reserve/commit/rollback`.
- **Gateway**: `backend/deploy/api-gateway.yaml` is a deployment option; not enforced by code.

---

## 3) Crebit Reference Architecture (Layered)

```
Sources -> Gemini Structuring -> Video Schema DB -> NotebookLM Library -> Sheets Bus -> DB SoR
  -> Pattern Library/Trace -> Capsule Specs -> Templates
  -> Workflow Runs -> Evidence -> Learning (GA/RL)
```

### 3.1 Knowledge Layer: Notebook Library

**Entities**
- NotebookLibrary: curated notebook metadata.
- NotebookAssets: references to films, scenes, scripts, stills.
- NotebookOutputs: summary + pattern labels + evidence refs.

**Invariant**
- Library data is private; only derived outputs are returned to users.

**Guide layer (NotebookLM)**
- Maintain notebooks by **auteur/genre clusters**.
- "Summary/homage/variation guides" are used only as a **guide layer**.
- User affinity-based **template fit/recommendations** are advisory signals (final decision is DB SoR).
- Mega-Notebook is for **cluster/phase aggregation** and must be reconstituted as **phase-locked source packs** for capsule creation.

### 3.2 Execution Layer: Capsule Nodes

**Capsule Types**
- Notebook Capsule: derived from NotebookLM outputs.
- Workflow Capsule: Opal or internal DAG runner.
- Hybrid Capsule: NotebookLM summary + internal rule engine.

**Invariant**
- Public graph shows ports + params only.
- Private subgraph executes server-side.

### 3.3 Template Layer: Creator/PD/Writer Pipelines

Templates are reusable pipeline blueprints:
- Short-form script pipeline.
- Storyboard pipeline.
- Visual style transfer pipeline.

Templates are learnable:
- GA explores variants.
- RL improves parameters using evidence scores.

### 3.4 Tong Dataset (Synapse Framework) Mapping

Mapping Tong dataset A/B/C/D to Crebit:

- **A (Origin Visual)**: Raw Asset + Visual Schema (lighting/color/composition/blocking)
- **B (Origin Persona)**: Origin Persona Profile (author philosophy, subconscious, era context)
- **D (Filter Persona)**: Homage/Creator Persona Profile (filter role)
- **C (Result Visual)**: Visual Schema of capsule outputs
- **Synapse Rule**: A+B transforms through D into C (core capsule spec logic)

Execution principles:
- Summarize/label B/D in the **NotebookLM guide layer**.
- Structure Synapse Rules in **DB SoR** for reproducibility.
- Validate C via **Evidence Loop** and feed into template learning.

---

## 3.5 Logic/Persona Fusion + Variation Protocol (SoR)

Dataset normalization (A/B/C/D), mathematical logic, auteur persona, their fusion, and genre variation migration,
NotebookLM source composition/guide extraction protocol are fixed in the canonical doc below:

- `25_NOTEBOOKLM_SOURCE_PACK_PROTOCOL_CODEX.md`

Key summary:
- Separate and then combine **Logic Vector** (cuts/composition/motifs/rhythm) and **Persona Vector** (tone/emotion/interpretation).
- Operate notebooks by **cluster_id + temporal_phase**.
- Variation recommendations are adjusted by NotebookLM guides + Evidence/RL scores.

---

## 3.6 Intent → Capsule Resolver Pattern (2026-01)

### Design Philosophy

Templates do not know app-specific parameters; they declare only **Intent**.  
Each Dimension Capsule interprets Intent via its own **Resolver** to decide optimal params.

```
Template → Intent(mood, pace, target) → Capsule Resolver → Params → Execution
```

### Intent Schema

Shared creative intent schema across all pipelines:

| Attribute | Type | Description |
|-----------|------|-------------|
| `mood` | enum | cinematic, energetic, calm, documentary, experimental |
| `pace` | enum | fast, slow, dynamic, contemplative |
| `target` | enum | expert, beginner, general, kids |
| `domain_sources` | list | RAG source hints (auteur name, genre, saju, etc.) |

### Per-Capsule Resolver

Each Dimension App implements `resolve_from_intent(intent, rag_context) → params`:

- **VEO Resolver**: mood=cinematic → lens=anamorphic, fps=24
- **Sound Resolver**: mood=cinematic → genre=orchestral, reverb=hall
- **Prompt Resolver**: mood + target → prompt tone/complexity adjustment

### Extended RAG Sources (Collective Intelligence)

Integrate knowledge sources beyond NotebookLM Library for collective intelligence:

| Source Type | Use Case | Contributor |
|-------------|----------|----------|
| NotebookLM | auteur persona, work analysis | curators/experts |
| Papers | film theory, visual studies | academic contributors |
| Saju/I Ching DB | time/space-based creative guidance | eastern philosophy experts |
| Books | arts/philosophy/culture | vibe coders/general users |

### Integration with Evidence Loop

Record Intent-Quality relationships in Evidence Loop for GA/RL learning:

```
Intent → Resolved Params → Execution → Quality Score → Evidence
                                                        ↓
                                               Template Learning
```

### Benefits

1. **Lower coupling**: no template edits when apps change.
2. **Collective intelligence**: non-devs contribute RAG sources; system uses them automatically.
3. **Scalability**: add new RAG sources by extending Resolvers only.
4. **Consistency**: a single Intent unifies pipeline tone and manner.

---

## 4) NotebookLM -> DB (Canonicalization Pipeline)

**Goal**: turn NotebookLM outputs into stable, queryable, learnable data.

Flow:
1. Admin curates sources and runs Gemini video structuring (ASR + keyframe).
2. Structured outputs are stored in **Video Schema DB**.
3. NotebookLM outputs go to Sheets Bus (contracted schema).
4. Promotion job maps Sheets -> DB SoR.
5. Patterns + evidence refs are stored as Pattern Library/Trace.

**Optional: internal retrieval index (future)**
- If Crebit directly ingests raw sources, follow RAG pipeline (chunk/enrich/embed).
- Use hybrid search (vector + lexical) and retrieval evaluation before promotion.

**Contract dependencies**
- `06_SHEETS_SCHEMA_V1.md`
- `07_NOTEBOOKLM_OUTPUT_SPEC_V1.md`
- `09_DB_PROMOTION_RULES_V1.md`
- `docs/archive/12_PATTERN_PROMOTION_CRITERIA_V1.md`

---

## 5) Capsule Node Contract (What must be true)

**NodeSpec (public)**
- `input_contracts`: required inputs, allowed types, max upstream.
- `output_contracts`: types returned by the capsule.
- `exposed_params`: param list with UI controls.
- `capsule_id@version`: fixed for reproducibility.

**CapsuleRun (private)**
- `upstream_context`: snapshot of all connected upstream outputs.
- `evidence_refs`: references to NotebookLibrary or Pattern Trace.
- `token_usage`, `latency_ms`, `cost_est_usd`.

---

## 6) Template Learning Loop (GA/RL)

**Why**: templates should improve without losing the original auteur DNA.

Loop:
- Run templates -> collect evidence scores.
- Record Pattern Trace and Pattern Lift.
- GA generates candidate parameter sets.
- RL selects the next best set using evidence reward.
- Promote winner to a new template version.

**Guardrails**
- Only promote when evidence thresholds are met.
- Preserve capsule versions to keep reproducibility.

---

## 7) User Flows (Two Lanes)

User/role flows are canonized in `08_PIPELINES_AND_USER_FLOWS.md`.

---

## 8) UX/IA Guidance (From RE, adapted)

- Left rail: Research, Creator Hub, Accounts, Credits, Affiliate.
- Empty state: "Create First Workflow" + 1-click seed flow.
- Top bar: Run + Preview + Credit balance.
- Train workflow: car order + connection selector + status states (node graph hidden).

See `10_UI_DESIGN_GUIDE_2025-12.md` for visual system.

---

## 9) Credits + Observability (Non-optional)

**Credits**
- Promo -> Subscription -> Top-up priority.
- Ledger entries for all runs and purchases.

**Observability**
- Per-run token usage, latency, cost estimate.
- Capsule-level analytics for template learning.
- Evaluation metrics: groundedness, completeness, relevancy, and evidence coverage.

---

## 10) Security / IP Protection

- Never ship raw notebooks, prompts, or internal chains to clients.
- Return summary + evidence refs only.
- Role-based access for admin review.
- Audit trail for capsule runs and promotions.

---

## 11) Selective Openness Policy (Rejected Items Review)

We do not need to wrap everything. We only lock what risks IP leakage, weakens evidence, or breaks reproducibility.

Decision rules:
- If it exposes raw prompts or internal chains, keep sealed.
- If it improves creator control without leaking IP, allow it as a safe param or template variant.
- If it bypasses Evidence Loop or DB SoR, keep server-side.

Item-by-item:
- Open multi-model selector  
  Decision: **Hide from end users**, allow **model tier** or **capsule variant** selection.  
  Rationale: preserves sealed capsules while enabling controlled customization.

- Real-time prompt editing  
  Decision: **No public editing**, allow **admin-only prompt modules** or Opal workflows.  
  Rationale: keeps IP safe while supporting internal iteration.

- Supabase direct client  
  Decision: **No direct client SoR**, optional Supabase for auth or read-only metadata.  
  Rationale: Evidence Loop + DB integrity require server enforcement.

---

## 12) Migration Strategy (No breaking changes)

Phase 0: Documentation alignment and contract freeze.  
Phase 1: Add missing schema fields (input contracts, upstream context).  
Phase 2: Capsule execution + preview pipeline.  
Phase 3: Template learning loop (GA/RL) + promotion rules.  
Phase 4: Credits, affiliate, observability hardening.

---

## 13) Doc Alignment Recommendations (Consulting)

If you accept this CODEX v20 as canonical, align these docs next:

- `00_EXECUTIVE_SUMMARY_NODE_CANVAS.md`: add Notebook Library as canonical layer.
- `01_NODE_CANVAS_TECHNICAL_SPECIFICATION.md`: add input/output contracts + upstream context.
- `04_CAPSULE_NODE_SPEC.md`: add capsule_id@version, evidence refs, cost fields.
- `06_SHEETS_SCHEMA_V1.md`: add Notebook Library + Pattern Trace outputs.
- `08_PIPELINES_AND_USER_FLOWS.md`: split Admin vs Creator flows.
- `10_UI_DESIGN_GUIDE_2025-12.md`: add nav + empty-state + credit balance.
- `11_INGEST_RUNBOOK_V1.md`: detail NotebookLM run + Sheets promotion.
- `13_CREDITS_AND_BILLING_SPEC_V1.md`: confirm credit priority + ledger.
- `26_AFFILIATE_PROGRAM_SPEC_V1.md`: ensure credits reward flow is defined.
- `docs/archive/19_CREBIT_EXECUTION_PLAN_V1.md`: re-sequence phases to match this doc.

---

## 14) Decision Gates (You decide)

1. Which auteur notebooks are in v1 Library?
2. Which template types are v1 (script, storyboard, visual)?
3. Which evidence thresholds promote a template?
4. What is the default credit cost per capsule run?
5. What level of evidence detail is safe to expose?

</details>
