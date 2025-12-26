# Vivid Execution Plan v1 (Post-Research, CODEX-aligned)

**Date**: 2025-12-24  
**Basis**: `20_VIVID_ARCHITECTURE_EVOLUTION_CODEX.md`  
**Goal**: Preserve Vivid philosophy while sequencing the work to avoid rework.
**Flow/Roles**: Canonical definitions live in `10_PIPELINES_AND_USER_FLOWS.md`.
**Principles/Contracts**: `05_CAPSULE_NODE_SPEC.md`, `08_SHEETS_SCHEMA_V1.md`, `11_DB_PROMOTION_RULES_V1.md`.

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
**Spec (SoR references)**:
- `10_PIPELINES_AND_USER_FLOWS.md`
- `11_DB_PROMOTION_RULES_V1.md`
- `31_NOTEBOOKLM_PATTERN_ENGINE_AND_CAPSULE_NODE_CODEX.md`

**Dev Tasks**:
- [ ] Extend Sheets ingest to include Notebook Library (manual first, automate later).
- [ ] Add Notebook Library tables in DB (metadata + outputs).
- [ ] Add promotion rules for Notebook outputs -> Pattern Library/Trace.

### Workstream B: Capsule Contracts + Execution
**Spec (SoR references)**:
- `05_CAPSULE_NODE_SPEC.md`

**Dev Tasks**:
- [ ] Add input contract validation in capsule run.
- [ ] Capture upstream context snapshot per run.
- [ ] Enforce evidence refs from DB SoR only.

### Workstream C: Canvas UX (Creator Hub)
**Spec (SoR references)**:
- `13_UI_DESIGN_GUIDE_2025-12.md`

**Dev Tasks**:
- [ ] Refactor Sidebar + TopBar.
- [ ] Empty-state seed graph UI.
- [ ] Node status states + preview panel integration.

### Workstream D: Template Learning (GA/RL)
**Spec (SoR references)**:
- `12_PATTERN_PROMOTION_CRITERIA_V1.md`

**Dev Tasks**:
- [ ] Define evidence reward function for GA/RL.
- [ ] Add template version promotion rules.
- [ ] Persist learning history for auditability.

### Workstream E: Commerce + Observability
**Spec (Reference)**:
- `17_CREDITS_AND_BILLING_SPEC_V1.md`
- `18_AFFILIATE_PROGRAM_SPEC_V1.md`
- `05_CAPSULE_NODE_SPEC.md` (run telemetry)

**Dev Tasks**:
- [ ] Implement credit ledger + balance.
- [ ] Add affiliate reward gating (verified email + first run).
- [ ] Surface token usage and cost per run in UI.

---

## 3) Immediate Next Steps

1. Freeze contracts based on CODEX v20.
2. Implement Phase 1 (Data + Schema) first to protect evidence integrity.
3. Proceed to Phase 2 (Capsule + Preview) once evidence flows are stable.
