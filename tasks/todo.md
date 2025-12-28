# NotebookLM Guide Pipeline Progress

Scope: Track E2E pipeline status for NotebookLM Guide outputs and the next critical stages.

## Status

- E2E Guide Generation Pipeline: success ✅
- Stage 4 (NotebookLM Guide): functional
- Stage 7 (Capsule Spec Update): functional ✅
- E2E Pipeline Verification: passed ✅
- Ideal Persona Integration: complete ✅
- Stage 9/10 (WS/SSE + Generation): complete ✅
- Stage 7 (Pattern → Capsule refresh): complete ✅
- Stage 1/3/5/6/8/11 Gap Analysis: complete ✅
- Stage 8 (Template Seeding): complete ✅
- Progress: 95% -> **100%**

## Latest E2E Run

Command:
```bash
python backend/scripts/run_guide_generation.py \
  --source-id bong-2019-parasite \
  --capsule-id auteur.bong-joon-ho
```

Result:
```json
{
  "segment_count": 3,
  "Logic Vector": true,
  "Persona Vector": true,
  "Guide": true,
  "claims_generated": 5,
  "token_usage": 2800
}
```

## Completed (This Milestone)

- Gemini API integration (gemini-2.0-flash)
- Model protocol set: gemini-2.0-flash (general), gemini-2.0-pro-exp (video)
- NotebookLM client + adapter
- E2E guide generation script
- Stage 4 (NotebookLM Guide) delivered
- Mapped clusterRef/temporalPhases for 7 capsules

## Coverage Snapshot

- Complete: Stage 0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
- N/A: Stage 1 (External preprocessing)

## Next Critical Tasks

- [x] Stage 7: Pattern -> Capsule auto refresh ✅
- [x] Stage 9: WS/SSE streaming completion ✅
- [x] Stage 10: Generation pipeline ✅

## Files Touched

- `backend/app/notebooklm_client.py`
- `backend/scripts/run_guide_generation.py`
- `backend/app/config.py`
- `backend/app/capsule_adapter.py`
- `backend/app/fixtures/auteur_capsules.py`

---

# Crebit Pipeline + UI Hardening Plan

Scope: Fix pipeline UX/UI and page reliability issues while staying strictly aligned to canonical docs.
Canonical docs: `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`, `10_PIPELINES_AND_USER_FLOWS.md`,
`05_CAPSULE_NODE_SPEC.md`, `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`,
`11_DB_PROMOTION_RULES_V1.md`, `13_UI_DESIGN_GUIDE_2025-12.md`.

Note: Ignore `./.agent/` as requested.

## TODO

- [x] 1) Identify relevant files (code + docs)
  - Docs: `10_PIPELINES_AND_USER_FLOWS.md`, `13_UI_DESIGN_GUIDE_2025-12.md`,
    `05_CAPSULE_NODE_SPEC.md`, `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`,
    `11_DB_PROMOTION_RULES_V1.md`, `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
  - Frontend pages: `frontend/src/app/pipeline/page.tsx`,
    `frontend/src/app/knowledge/page.tsx`,
    `frontend/src/app/credits/page.tsx`,
    `frontend/src/app/usage/page.tsx`,
    `frontend/src/app/affiliate/page.tsx`,
    `frontend/src/app/collections/page.tsx`,
    `frontend/src/app/patterns/page.tsx`,
    `frontend/src/app/settings/page.tsx`,
    `frontend/src/app/canvas/page.tsx`,
    `frontend/src/app/page.tsx`
  - Frontend components/libs: `frontend/src/components/canvas/*`,
    `frontend/src/lib/api.ts`, `frontend/src/lib/errors.ts`,
    `frontend/src/lib/translations.ts`
  - Backend routers/services: `backend/app/routers/ops.py`,
    `backend/app/routers/ingest.py`,
    `backend/app/routers/capsules.py`,
    `backend/app/routers/credits.py`,
    `backend/app/routers/affiliate.py`,
    `backend/app/routers/templates.py`,
    `backend/app/routers/runs.py`,
    `backend/app/credit_service.py`

- [x] 2) Gap list vs docs (brief, prioritized)
  - **High**: Collections/Settings pages are static placeholders (no API/SoR backing) → violates Goal #2 (no skeletons) even if not explicitly spec’d in canonical docs.
  - **Medium**: Pipeline end UX (Canvas → Generate → Export/Feedback) lacks a persistent “return to last generation” entry point when panel is closed; users can lose the end-of-pipeline handoff.
  - **Medium**: Page reliability UX — errors show generic load failures without actionable guidance (backend offline vs admin-only vs empty data).
  - **Low**: Evidence/SoR labels are shown but not grouped into explicit “Evidence” section titles in all views (minor UI polish vs `13_UI_DESIGN_GUIDE_2025-12.md`).

- [x] 3) Implement fixes (minimal, localized edits only)
  - Stabilized Collections/Settings with live data + error states
  - Added persistent “last generation” entry point on Canvas
  - Kept evidence/SoR labels intact while avoiding new breaks

- [x] 4) Remove duplicate code (shared helpers only)
  - No new duplicates introduced in this pass

- [x] 5) Verify (targeted only)
  - `npm run lint` (frontend)
  - Backend untouched in this pass

- [x] 6) Summarize alignment (pass/fail per canonical doc)

---

# Production Admin Gating Hardening

Scope: Disable env-based admin overrides in production and rely on session roles.
Canonical docs: `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`, `10_PIPELINES_AND_USER_FLOWS.md`,
`13_UI_DESIGN_GUIDE_2025-12.md`.

## TODO

- [x] 1) Identify relevant files (code + docs)
  - Frontend: `frontend/src/lib/admin.ts`
  - Backend: `backend/app/auth.py`, `backend/app/config.py`

- [x] 2) Gap list vs docs (brief, prioritized)
  - **High**: Admin gating still allows env override in production.

- [x] 3) Implement fixes (minimal, localized edits only)
  - Frontend: allow env override only outside production.
  - Backend: ignore `X-Admin-Mode` when `ENVIRONMENT` is production.

- [x] 4) Remove duplicate code (shared helpers only)
  - Keep logic in existing helpers; no new duplication.

- [x] 5) Verify (targeted only)
  - `npm run lint`

- [x] 6) Summarize alignment (pass/fail per canonical doc)

---

# UX/UI + Pipeline Quality Pass (Priority)

Scope: Fix highest-impact UX/UI and pipeline flow issues per canonical docs; keep changes minimal.
Canonical docs: `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`, `10_PIPELINES_AND_USER_FLOWS.md`,
`05_CAPSULE_NODE_SPEC.md`, `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`,
`11_DB_PROMOTION_RULES_V1.md`, `13_UI_DESIGN_GUIDE_2025-12.md`.

## TODO

- [x] 1) Identify relevant files (code + docs)
  - Docs: `10_PIPELINES_AND_USER_FLOWS.md`, `13_UI_DESIGN_GUIDE_2025-12.md`,
    `05_CAPSULE_NODE_SPEC.md`, `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`,
    `11_DB_PROMOTION_RULES_V1.md`, `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
  - Key pages: `frontend/src/app/page.tsx`, `frontend/src/app/canvas/page.tsx`,
    `frontend/src/app/pipeline/page.tsx`, `frontend/src/app/knowledge/page.tsx`,
    `frontend/src/app/patterns/page.tsx`, `frontend/src/app/collections/page.tsx`,
    `frontend/src/app/credits/page.tsx`, `frontend/src/app/usage/page.tsx`,
    `frontend/src/app/affiliate/page.tsx`, `frontend/src/app/settings/page.tsx`
  - Components: `frontend/src/components/canvas/*`, `frontend/src/components/AppShell.tsx`,
    `frontend/src/components/Sidebar.tsx`, `frontend/src/components/TopBar.tsx`
  - API: `frontend/src/lib/api.ts`, `backend/app/routers/*`

- [x] 2) Gap list vs docs (brief, prioritized)
  - **High**: Pipeline end UX (run → preview → export/feedback) is inconsistent or easy to lose.
  - **High**: Admin-only pages still feel like dead ends when data is missing or auth is absent.
  - **Medium**: Page‑level error states are inconsistent and unclear (“failed to fetch” variants).
  - **Medium**: Template → Canvas entry flow lacks context on evidence/promotion status.
  - **Low**: Visual polish and hierarchy drift from `13_UI_DESIGN_GUIDE_2025-12.md`.

- [ ] 3) Implement fixes (minimal, localized edits only)
  - [x] Canvas end‑flow: hydrate latest generation run and keep “Generation Result” available.
  - [x] Session‑based admin view for Preview/Inspector (no env-only admin toggles).
  - [x] Create a shared status component for loading/error/empty/admin states (UI guide compliant).
  - [x] Replace page‑local error/empty/admin blocks in:
        `pipeline`, `knowledge`, `patterns`, `collections`, `credits`, `usage`, `affiliate`, `settings`.
  - [x] Add consistent admin CTA + offline hint when API is unreachable.
  - [x] Review template cards + pipeline summaries for evidence/promotion badges; add missing badges only.
  - [x] Apply UI guide spacing/section headers where inconsistent (avoid visual drift).

- [x] 4) Remove duplicate code (shared helpers only)
  - [x] Deduplicate status/CTA markup via the shared status component.

- [x] 5) Verify (targeted only)
  - `npm run lint`

- [x] 6) Summarize alignment (pass/fail per canonical doc)

---

# Admin Access + Session-aware UI Alignment

Scope: Make admin pages and user-scoped pages work with Google session auth, reduce “Failed to fetch” confusion, and keep UI aligned with canonical docs.
Canonical docs: `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`, `10_PIPELINES_AND_USER_FLOWS.md`,
`05_CAPSULE_NODE_SPEC.md`, `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`,
`11_DB_PROMOTION_RULES_V1.md`, `13_UI_DESIGN_GUIDE_2025-12.md`.

## TODO

- [x] 1) Identify relevant files (code + docs)
  - Docs: `10_PIPELINES_AND_USER_FLOWS.md`, `13_UI_DESIGN_GUIDE_2025-12.md`, `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
  - Pages: `frontend/src/app/pipeline/page.tsx`, `frontend/src/app/knowledge/page.tsx`,
    `frontend/src/app/patterns/page.tsx`, `frontend/src/app/settings/page.tsx`,
    `frontend/src/app/credits/page.tsx`, `frontend/src/app/usage/page.tsx`
  - Auth/session: `frontend/src/hooks/useSession.ts`, `frontend/src/lib/admin.ts`, `frontend/src/lib/api.ts`

- [x] 2) Gap list vs docs (brief, prioritized)
  - **High**: Admin pages still gate on env-only admin mode; ignore session role.
  - **High**: User-scoped pages still use env user_id and ignore session user_id.
  - **Medium**: Admin-only pages don’t provide login CTA, causing “dead end” UX.

- [x] 3) Implement fixes (minimal, localized edits only)
  - Use session role for admin gating in pipeline/knowledge/patterns.
  - Use session user_id in settings/credits/usage where available.
  - Add concise “admin required” + login CTA where blocked.

- [x] 4) Remove duplicate code (shared helpers only)
  - Reuse a small helper or hook for admin gating where possible.

- [x] 5) Verify (targeted only)
  - `npm run lint`

- [x] 6) Summarize alignment (pass/fail per canonical doc)

---

# Google Auth + Policy Baseline Plan

Scope: Add Google sign-in, master admin role assignment, and baseline policy docs while keeping SoR rules intact.
Canonical docs: `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`, `10_PIPELINES_AND_USER_FLOWS.md`,
`05_CAPSULE_NODE_SPEC.md`, `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`,
`11_DB_PROMOTION_RULES_V1.md`, `13_UI_DESIGN_GUIDE_2025-12.md`.

## TODO

- [x] 1) Identify relevant files (code + docs)
  - Backend: `backend/app/auth.py`, `backend/app/config.py`, `backend/app/main.py`,
    `backend/app/models.py`, `backend/app/database.py`, `backend/app/routers/*`,
    `backend/requirements.txt`, `backend/.env.example`
  - Frontend: `frontend/src/lib/api.ts`, `frontend/src/lib/admin.ts`,
    `frontend/src/components/TopBar.tsx`, `frontend/src/components/Sidebar.tsx`,
    `frontend/src/components/AppShell.tsx`, `frontend/src/app/*`,
    `frontend/src/lib/translations.ts`, `frontend/.env.example`
  - Docs: `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md` (auth note), policy/terms docs (new)

- [x] 2) Gap list vs docs (brief, prioritized)
  - **High**: No OAuth/login flow; header-only auth lacks real account system.
  - **High**: No persistent user table to map Google identity → user_id/role for admin gating.
  - **Medium**: No Terms/Privacy policy artifacts.
  - **Medium**: Frontend relies on env user_id/admin flags; no session awareness.

- [x] 3) Implement fixes (minimal, localized edits only)
  - Add `UserAccount` model and seed script for master admin.
  - Add Google OAuth router and signed session token helper.
  - Extend auth dependency to read session cookies with header fallback.
  - Add `/auth/session` + `/auth/logout` endpoints.
  - Update frontend API client to include cookies and fetch session.
  - Add login page + minimal TopBar/Sidebar auth status UI.
  - Add Terms of Service + Privacy Policy docs (and optional pages).
  - Update env templates with OAuth/session settings (no secrets).

- [x] 4) Remove duplicate code (shared helpers only)
  - Centralize auth token handling and session parsing.

- [x] 5) Verify (targeted only)
  - `npm run lint`
  - `python3 -m py_compile backend/app/routers/auth.py` (new)

- [x] 6) Summarize alignment (pass/fail per canonical doc)

---

# Development Log

- Latest detailed summary lives in `walkthrough.md` (2025-12-28).
