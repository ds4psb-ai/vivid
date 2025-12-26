# Vivid Architecture Evolution (CODEX v20)

**Date**: 2025-12-24  
**Status**: CODEX baseline (philosophy-preserving)  
**Purpose**: Convert reverse-engineering learnings into Vivid-specific architecture improvements without breaking the original philosophy.

---

## 0) Decision Summary (What this doc locks)

- NotebookLM Library is the canonical auteur knowledge base; end users never see raw notebooks.
- NotebookLM is the **knowledge/guide layer**: cluster notebooks per auteur and output homage/variation guidance + template fit suggestions.
- Video understanding uses **Gemini 3 Pro structured outputs** and is stored in DB SoR before NotebookLM.
- LLM-wrapped nodes are sealed capsules; only input/output ports + exposed params are public.
- Evidence Loop remains the engine: Sheets Bus -> DB SoR -> Pattern Library/Trace -> Capsule/Template evolution.
- Templates are first-class and learnable: GA explores, RL exploits, evidence promotes.
- Credits + observability are core UX (not hidden in settings).
- UI flow keeps "Add -> Connect -> Generate" with strong empty-state onboarding.

---

## 1) Non-Negotiable Philosophy (Vivid DNA)

1. **NotebookLM Library is the canonical auteur knowledge base**  
   - Curated notebooks from auteur/popular works become a library of evidence.  
   - These notebooks are never exposed to end users; only summary outputs + evidence refs are surfaced.

2. **LLM-wrapped nodes are sealed capsules**  
   - Users can customize inputs + exposed params only.  
   - Internal chains, prompts, and workflows remain server-side.

3. **Evidence Loop remains the engine**  
   - Sheets Bus -> DB SoR -> Pattern Library/Trace -> Capsule Spec.  
   - NotebookLM/Opal are accelerators, not the source of truth.

4. **Templates are first-class and learnable**  
   - Creator/PD/Writer pipelines are defined as templates.  
   - Templates evolve via GA/RL using evidence-based feedback.

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

---

## 3) Vivid Reference Architecture (Layered)

```
Sources -> Gemini Structuring -> Video Schema DB -> NotebookLM Library -> Sheets Bus -> DB SoR
  -> Pattern Library/Trace -> Capsule Specs -> Templates
  -> Canvas Runs -> Evidence -> Learning (GA/RL)
```

### 3.1 Knowledge Layer: Notebook Library

**Entities**
- NotebookLibrary: curated notebook metadata.
- NotebookAssets: references to films, scenes, scripts, stills.
- NotebookOutputs: summary + pattern labels + evidence refs.

**Invariant**
- Library data is private; only derived outputs are returned to users.

**Guide layer (NotebookLM)**
- 거장/장르 **클러스터 단위 노트북**을 유지
- “요약/오마주/변주 가이드” 출력은 **가이드 레이어**로만 사용
- 사용자 성향 기반 **템플릿 적합도/추천**은 참고 신호 (최종 결정은 DB SoR)

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

통 데이터셋의 A/B/C/D 구조를 Vivid에 매핑하면 다음과 같습니다.

- **A (Origin Visual)**: Raw Asset + Visual Schema (조명/색/구도/동선 등)
- **B (Origin Persona)**: Origin Persona Profile (작가 철학/무의식/시대 맥락)
- **D (Filter Persona)**: Homage/Creator Persona Profile (필터 역할)
- **C (Result Visual)**: Capsule 실행/생성 결과의 Visual Schema
- **Synapse Rule**: A+B가 D를 거쳐 C로 변환되는 규칙 (캡슐 스펙의 핵심 로직)

실행 원칙:
- B/D는 **NotebookLM 가이드 레이어**로 요약·라벨링
- Synapse Rule은 **DB SoR**에 구조화해 재현성을 확보
- 결과(C)는 **Evidence Loop**로 검증하고 Template Learning에 반영

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
- If Vivid directly ingests raw sources, follow RAG pipeline (chunk/enrich/embed).
- Use hybrid search (vector + lexical) and retrieval evaluation before promotion.

**Contract dependencies**
- `08_SHEETS_SCHEMA_V1.md`
- `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`
- `11_DB_PROMOTION_RULES_V1.md`
- `12_PATTERN_PROMOTION_CRITERIA_V1.md`

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

사용자/역할 흐름은 `10_PIPELINES_AND_USER_FLOWS.md`에 정본화한다.

---

## 8) UX/IA Guidance (From RE, adapted)

- Left rail: Research, Creator Hub, Accounts, Credits, Affiliate.
- Empty state: "Create First Canvas" + 1-click seed graph.
- Top bar: Run + Preview + Credit balance.
- Canvas: port rules, status states, lasso select, minimap.

See `13_UI_DESIGN_GUIDE_2025-12.md` for visual system.

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
- `05_CAPSULE_NODE_SPEC.md`: add capsule_id@version, evidence refs, cost fields.
- `08_SHEETS_SCHEMA_V1.md`: add Notebook Library + Pattern Trace outputs.
- `10_PIPELINES_AND_USER_FLOWS.md`: split Admin vs Creator flows.
- `13_UI_DESIGN_GUIDE_2025-12.md`: add nav + empty-state + credit balance.
- `14_INGEST_RUNBOOK_V1.md`: detail NotebookLM run + Sheets promotion.
- `17_CREDITS_AND_BILLING_SPEC_V1.md`: confirm credit priority + ledger.
- `18_AFFILIATE_PROGRAM_SPEC_V1.md`: ensure credits reward flow is defined.
- `19_VIVID_EXECUTION_PLAN_V1.md`: re-sequence phases to match this doc.

---

## 14) Decision Gates (You decide)

1. Which auteur notebooks are in v1 Library?
2. Which template types are v1 (script, storyboard, visual)?
3. Which evidence thresholds promote a template?
4. What is the default credit cost per capsule run?
5. What level of evidence detail is safe to expose?
