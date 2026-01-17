# RAG Next-Phase Plan (Post-Wiring)

> **Type**: Execution Plan (Active)
> **Status**: In Progress
> **Owner**: Vivid RAG
> **Created**: 2026-01-11
> **Last Updated**: 2026-01-15
> **Related**: [RAG Refactor Design](./RAG_REFACTOR_FINAL_PLAN_2026-01-11.md) | [RAG Reliability](./RAG_RELIABILITY.md) | [RAG Quality](./RAG_QUALITY.md)

**Scope**: Observability + quality evaluation + deprecation cleanup + operational hardening + **Plugin-Registry 아키텍처 (NEW)**


---

## Status Update (2026-01-14)

**Completed**
- Observability + SLOs (Grafana + PromQL + alerts)
- RouterDecisionLog + reports (`router_decision_report.py`)
- Cache report (`rag_cache_report.py`) + retention (`cleanup_router_logs.py`)
- Qdrant 384-dim reindex + real embeddings

**Remaining (data-dependent)**
- NotebookLM Park/Shinkai registration (source pack pending)
- Cache TTL tuning after traffic accumulation
- Cron setup (ops)

---

## 0) Baseline State (Completed)
- Router heuristic wired into `hybrid_rag.py`
- `@track_rag_operation` applied to core query functions
- `merge_rag_config()` integrated into `get_rag_preset()`
- `rag_cache.py` shim in place
- `semantic_cache` metrics hooked

---

## 1) Objectives (Next 2–4 Weeks)
1. Quantify reliability: error rate, latency SLOs, cache hit rate.
2. Prove quality: groundedness + retrieval relevance + deflection when evidence is weak.
3. Reduce maintenance cost: deprecate legacy components cleanly.
4. Stabilize operations: dashboards + alerting + notebook coverage.

---

## 2) Workstreams & Deliverables

### A) Observability + SLOs (Highest ROI) ✅ DONE
**Goal:** Real-time visibility and meaningful percentiles.
- **Define explicit latency histograms for RAG steps** ✅
  - Ensure bucket ranges cover expected latency *and* long-tail (2–3× max).
  - Add `histogram_quantile()` queries for p95/p99 dashboards.
- **Standardize labels/tags** ✅
  - Keep tag count ≤ 6–8 and stable ordering.
  - Avoid high-cardinality labels (e.g., raw query text).
- **Add error-rate counters by stage** ✅
  - e.g., `rag_errors_total{stage=notebooklm|vertex|cache}`.

**Deliverables**
- ✅ Grafana dashboard: `RAG Overview` (15 panels) - `config/grafana/rag_overview.json`
- ✅ PromQL snippets documented in `docs/RAG_RELIABILITY.md`

---

### B) Router Tuning & Safety Guards
**Goal:** Score thresholds validated by telemetry, not guesswork.
- **Add tuning knobs** (env / YAML overrides):
  - `router.score_threshold`, `router.force_grounding_threshold`.
- **Introduce a fallback guardrail**
  - If `confidence < threshold` AND `not grounded`, force grounding.
- **Automated A/B or shadow logging**
  - Log router decisions and compare against “would-have-used” strategy.
- **Privacy & cardinality guard (mandatory)**
  - Log `query_hash` only; never log raw query text.
  - Keep labels bounded (dimension, strategy, stage only).

**Deliverables**
- `RouterDecisionLog` schema (dimension, score, chosen_strategy, latency, confidence).

---

### C) Cache Quality & Hygiene
**Goal:** Improve hit rate without polluting quality.
- **Add hit/miss metrics by dimension** (bounded cardinality).
- **Track “cache poisoning risk”**
  - Count cache hits that later lead to low confidence or user complaints.
- **TTL policy review**
  - Compare hit rate vs staleness: adjust `TTL_AUTEUR_DNA` and `TTL_DEFAULT`.

**Deliverables**
- Cache tuning report (hit %, avg similarity, stale rate)

---

### D) NotebookLM Coverage Completion ⚠️ PARTIAL
**Goal:** Close PENDING/SIMULATION gaps.
- ✅ Upload Tarantino notebook (11 sources, ID: `ec799223...`)
- ⚠️ Park/Shinkai: SIMULATION (소스 자료 미준비)
- ✅ Add periodic health check in admin endpoint.

**Deliverables**
- ⚠️ `NOTEBOOK_REGISTRY` 5/7 real IDs (봉, 왕, 빌, 놀, 타란티노)
- ✅ Health check log line: `NotebookLM health status`

---

### E) Quality Evaluation Harness
**Goal:** Prove groundedness & retrieval precision.
- Build **offline evaluation harness**:
  - Retrieval relevance (precision@k)
  - Answer groundedness (citation alignment)
  - Deflection correctness when evidence is missing
- Integrate **benchmark references** as sanity checks (optional):
  - Use GaRAGe/DICE-style criteria or internal equivalents.

**Deliverables**
- `backend/tests/e2e/test_rag_quality.py` (offline only)
- Quality summary in `docs/RAG_QUALITY.md`

---

### F) Deprecation Cleanup
**Goal:** Remove dead paths safely.
- Remove legacy `notebooklm_client.py` usage (worker, deprecated scripts).
- Remove deprecated class methods in `rag_cache.py` once callers migrated.

**Deliverables**
- `rg notebooklm_client` = 0
- `rg get_rag_cache` only in tests/compat
- **SSoT for deprecation safety**: `/Users/ted/.gemini/antigravity/brain/2d64b1b5-d57e-45e5-a082-32b2a90bf6a2/implementation_plan.md.resolved`

**Inventory (surveyed)**
| Location | Files | Size |
| --- | --- | --- |
| `backend/app/_deprecated/` | 23 | ~180KB |
| `backend/app/routers/_deprecated/` | 20 | ~320KB |
| `backend/app/agents/_deprecated/` | 7 | ~105KB |
| `frontend` (4 dirs) | 24+ | ~200KB |
| **Total** | **70+** | **~823KB** |

**Risk Tiers**
| Tier | Scope | Reason |
| --- | --- | --- |
| P0 | Empty folders + `motion-legacy` | Safe to delete once unused |
| P1 | 5 high-risk files (auteur_templates/seed/adapters) | Still imported |
| P2 | `capsules.py` (70KB), `ops.py` (52KB) | Large, complex |

**P0 Checklist (10–20m)**
1) Confirm no live imports: `rg "(_deprecated|motion-legacy)" backend frontend`
2) Confirm no doc refs: `rg "_deprecated|motion-legacy" docs`
3) Delete empty folders and dead assets
4) `rg` re-run to ensure zero references
**Go Criteria**: import=0 AND doc refs=0

**P1 Checklist (2–4h)**
1) Identify all importers (see Import Report template below)
2) Create shim or re-route to new module with same public API
3) Add `DeprecationWarning` or structured log at shim boundary
4) Update importers to new module
5) Remove shim only after `rg` shows no usage
**Go Criteria**: shim route verified + existing API smoke passes

**P2 Checklist (4–8h)**
1) Build legacy route mapping (see template below)
2) Define replacement endpoints + schemas
3) Add compatibility layer if needed (thin adapter)
4) Migrate traffic + add logging
5) Remove legacy endpoints after 1–2 release cycles
**Go Criteria**: mapping complete + smoke tests pass + 1–2 release cycles elapsed

**Import Usage Report Template**
```
Title: Deprecated Import Report (YYYY-MM-DD)

Commands:
  rg --files -g '*_deprecated*'
  rg "from .*_deprecated|import .*_deprecated|_deprecated" backend frontend

Findings:
| File | Import Path | Used By | Status | Notes |
| --- | --- | --- | --- | --- |
| path/to/file.py | app._deprecated.foo | backend/app/x.py | migrate | maps to app/foo.py |
```

**Large Router Mapping Template**
```
Title: Legacy Router Mapping (capsules.py / ops.py)

| Legacy Route | Method | New Route | Request Schema | Response Schema | Dependencies | Status |
| --- | --- | --- | --- | --- | --- | --- |
| /api/legacy/capsule/run | POST | /api/dimension/run | RunRequest | RunResponse | rag_cache | planned |
```

**Frontend Deprecation Notes**
- Confirm route tree and lazy imports before delete.
- Avoid removing shared components until import graph is clean.
- Require 1-week telemetry on deprecated usage before deletion.

**Test Gates (minimum)**
- `cd backend && pytest -v tests/routers/test_dimension_sse.py`
- `cd backend && pytest -v tests/e2e/test_rag_reliability.py`

---

## 3) Metrics Targets (Initial)
- Cache hit rate: 30–50% (dimension-specific)
- p95 RAG latency: < 2s for cache hits, < 10–15s for live RAG
- Circuit open events: < 3/day
- Grounding coverage: ≥ 80% for queries flagged as “recency”

---

## 4) Risks & Mitigations
- **High-cardinality metrics** → enforce label policy.
- **NotebookLM UI automation breakage** → add health check + circuit breaker alerts.
- **Cache poisoning** → add quality regression tests and record low-confidence hits.

---

## 5) Definition of Done
- Dashboard live with p95/p99 latency + error rate + cache hit rate.
- Router score thresholds tunable without code changes.
- Offline quality harness produces weekly report.
- Legacy notebooklm_client references eliminated.

---

## 6) Suggested Next 3 Tasks (Fast ROI)
1. Add error counter + p95/p99 dashboards
2. Add RouterDecisionLog and telemetry export
3. Launch cache tuning report

---

## 7) P7: Plugin-Registry 아키텍처 (NEW 2026-01-15)

> **참조**: [Implementation Plan](../.gemini/antigravity/brain/fd50d920-5052-44e8-a0ad-c5b0bc32d4f9/implementation_plan.md)

### 목표
- **"앱 추가 = YAML 1개 추가"** (코드 수정 0)
- BM25 Hybrid Search + RRF Fusion 활성화
- 검색 정확도 +48% (62% → 91%)

### 구현 우선순위

| Phase | 작업 | 예상 노력 | 효과 |
|-------|------|----------|------|
| P0 | BM25 검색 활성화 | 1-2h | 검색 정확도 +48% |
| P1 | YAML Manifest 도입 | 2-3h | 앱 추가 = YAML 1개 |
| P2 | Backend ABC + Auto-discovery | 3-4h | 백엔드 플러그인화 |
| P3 | Ensemble Retriever (병렬 RRF) | 2h | 지연시간 50% 감소 |

### 디렉토리 구조 (계획)

```
backend/app/rag/
├── manifests/                    # YAML 기반 앱 설정
│   ├── _schema.yaml
│   ├── dimension.persona.yaml
│   └── dimension.aesthetic.yaml
├── backends/                     # 백엔드 플러그인
│   ├── base.py                  # BaseBackend ABC
│   ├── qdrant_dense.py
│   ├── bm25_sparse.py
│   └── notebooklm.py
└── fusion/                       # 결과 융합
    └── weighted_rrf.py
```

