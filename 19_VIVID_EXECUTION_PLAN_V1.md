# Vivid Execution Plan v1 (Post-Research, CODEX-aligned)

**Date**: 2025-12-24  
**Basis**: `20_VIVID_ARCHITECTURE_EVOLUTION_CODEX.md`  
**Goal**: Preserve Vivid philosophy while sequencing the work to avoid rework.
**Flow/Roles**: Canonical definitions live in `10_PIPELINES_AND_USER_FLOWS.md`.

---

## 1) Roadmap Overview

| Phase | Focus | Key Deliverables |
| :--- | :--- | :--- |
| **Phase 0** | **Doc Alignment** | Contract freeze, Notebook Library + DB SoR policies, capsule contract baselines |
| **Phase 1** | **Data + Schema** | Notebook Library schema, input contracts, upstream context, evidence refs |
| **Phase 2** | **Capsule + Preview** | Capsule execution pipeline, preview panel, evidence refs in UI |
| **Phase 3** | **Template Learning** | GA exploration + RL exploitation, promotion rules + versioning |
| **Phase 4** | **Commerce + Observability** | Credits wallet, affiliate flow, token/cost analytics |

---

## 2) Detailed Workstreams

### Workstream A: Knowledge Pipeline (Notebook Library -> DB SoR)
**Spec**:
- Notebook Library is private and canonical.
- NotebookLM outputs go to Sheets Bus, then DB SoR.
- Pattern Library/Trace is the only evidence source for capsules.
- NotebookLM guide layer: 클러스터 노트북 + 오마주/변주 가이드 + 템플릿 적합도 제안.

**Dev Tasks**:
- [ ] Extend Sheets ingest to include Notebook Library (manual first, automate later).
- [ ] Add Notebook Library tables in DB (metadata + outputs).
- [ ] Add promotion rules for Notebook outputs -> Pattern Library/Trace.

### Workstream B: Capsule Contracts + Execution
**Spec**:
- Capsule spec must include `input_contracts`, `output_contracts`, `capsule_id@version`.
- Capsule run must capture `upstream_context`, `evidence_refs`, `token_usage`, `latency_ms`.

**Dev Tasks**:
- [ ] Add input contract validation in capsule run.
- [ ] Capture upstream context snapshot per run.
- [ ] Enforce evidence refs from DB SoR only.

### Workstream C: Canvas UX (Creator Hub)
**Spec**:
- Left rail: Research / Creator Hub / Accounts / Credits / Affiliate.
- Empty state: one-click seed graph.
- Top bar: Run + Preview + Credit balance.

**Dev Tasks**:
- [ ] Refactor Sidebar + TopBar.
- [ ] Empty-state seed graph UI.
- [ ] Node status states + preview panel integration.

### Workstream D: Template Learning (GA/RL)
**Spec**:
- GA explores candidate parameters; RL exploits evidence reward.
- Promote new template versions only when evidence thresholds pass.

**Dev Tasks**:
- [ ] Define evidence reward function for GA/RL.
- [ ] Add template version promotion rules.
- [ ] Persist learning history for auditability.

### Workstream E: Commerce + Observability
**Spec**:
- Credits are not hidden in settings.
- Ledger is append-only, tied to capsule runs.
- Token usage + latency visible per run.

**Dev Tasks**:
- [ ] Implement credit ledger + balance.
- [ ] Add affiliate reward gating (verified email + first run).
- [ ] Surface token usage and cost per run in UI.

---

## 3) Immediate Next Steps

1. Freeze contracts based on CODEX v20.
2. Implement Phase 1 (Data + Schema) first to protect evidence integrity.
3. Proceed to Phase 2 (Capsule + Preview) once evidence flows are stable.
