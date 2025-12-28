# 18_REVERSE_ENGINEERING_REPORT_FOR_EXECUTION.md

**Date**: 2025-12-24
**Updated**: 2025-12-28
**Purpose**: Final data extraction to unblock "Execution Plan"
**Scope**: Workstreams A-F (IA, Canvas, Data, Credits, Affiliate, Observability)

---

## 0) SoR Alignment (Reference Only)

This document is reference-only. Final decisions and contracts live in SoR docs.

- Docs map: `00_DOCS_INDEX.md`
- Philosophy: `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
- Flows/Roles: `10_PIPELINES_AND_USER_FLOWS.md`
- Capsule contract: `05_CAPSULE_NODE_SPEC.md`
- UI/UX: `13_UI_DESIGN_GUIDE_2025-12.md`
- Credits/Growth: `17_CREDITS_AND_BILLING_SPEC_V1.md`, `35_AFFILIATE_PROGRAM_SPEC_V1.md`

---

## Workstream A: IA + Onboarding ( Confirmed )

**1. Navigation Structure (Left Rail)**
- **Top Group (Product)**: `Dashboard`, `Research` (Data Ingest), `Creator Hub` (Canvas).
- **Bottom Group (Admin)**: `Accounts`, `Credits` (Wallet), `Affiliate` (Growth).
- **Logic**: Split "Doing" vs "Managing". Credits is *promoted* to top-level access.

**2. Empty State Mechanics**
- **CTA**: "Create First Canvas" (Primary, Accent Color).
- **Micro-Copy**: "Visual AI content workflow builder. Connect inputs -> AI Processor -> Outputs."
- **Seed Templates** (Reverse Engineered):
  - "YouTube to Blog" (Video Input -> Summary Node -> Blog Writer)
  - "Social Repurposing" (Video Input -> Clip Extractor -> Caption Writer)

---

## Workstream B: Canvas UX ( Observable Behavior )

**1. Node Port Logic (Inferred from UI)**
- **Input Nodes**: 0 Inputs, 1 Output.
- **Processor Nodes**: N Inputs (Aggregated context), 1 Output.
- **Output Nodes**: 1 Input (Content source), 0 Outputs (Final artifact).
- **Rule**: "Type Safety" exists visually (Video ports only connect to Video-compatible inputs), but practically text/context is universal.

**2. Interaction Specs**
- **Minimap**: Bottom-right floating.
- **Zoom range**: 10% to 200%.
- **Selection**: Shift+Drag for Lasso. Backspace to delete.

---

## Workstream C: Data Model ( Logical Extraction )

To support the observed "Context Awareness", the backend schema must hold:

**1. `NodeSpec.input_contracts`**
```json
{
  "max_upstream": 5,
  "allowed_types": ["video/mp4", "text/plain", "application/json"],
  "context_mode": "aggregate" // vs "sequential"
}
```

**2. `ExecutionState.context_window`**
- The "Processor" node doesn't just read the immediate parent. It reads the *lineage*.
- **Data requirement**: `upstream_inputs` field in `CapsuleRun` that specifically snapshots the JSON content of all connected sources.

---

## Workstream D: Credits & Billing ( Policy Extraction )

**1. Consumption Hierarchy**
- **Priority 1**: Promo Credits (Expire in 90 days).
- **Priority 2**: Subscription Credits (Reset monthly).
- **Priority 3**: Top-up Credits (Never expire).

**2. Ledger Schema Columns (Reverse Engineered)**
- `transaction_id`: UUID
- `event_type`: `generation_run` | `purchase` | `referral_reward`
- `amount`: +/- integer
- `balance_snapshot`: The balance *after* transaction (for audit).
- `meta`: `{"canvas_id": "...", "node_id": "..."}` for transparency.

---

## Workstream E: Affiliate ( Growth Engine )

**1. Referral Logic**
- **Trigger**: Unique Invite Link (`virlo.ai/invite/USER_ID`).
- **Reward**: "Give 500 Credits, Get 500 Credits".
- **Validation**: Credits unlock only after verified email + first generation run (anti-abuse).

**2. UI Module**
- Location: Inside "Credits" page.
- Components: "Copy Link" input, "Total Earned" counter, list of "Pending/Verified" referrals.

---

## Workstream F: Observability ( Cost Transparency )

**1. Log Attributes**
To achieve "Cost per Run" transparency seen in Pro tools:
- `model_latency_ms`: Time to first token.
- `output_tokens`: Count.
- `input_tokens`: Count (crucial for context-heavy nodes).
- `cost_usd_est`: Real-time estimate for admin dashboards.

---

**Ready for Execution Plan?**
- Reference only. Execution plan must follow SoR documents above.

---

## Deep Dive Level 4: Live API & Auth Intelligence (Verified via Browser Agent)

**1. OAuth Application Specs (Captured)**
Observed in competitor UI; **do not adopt** without separate validation and legal review.

*   **Google / YouTube**
    *   **OAuth Scopes**: `email`, `profile`, `https://www.googleapis.com/auth/youtube.readonly`
    *   **Client Pattern**: `*.apps.googleusercontent.com`
    *   **Callback**: `/auth/v1/callback` (implies Supabase/GoTrue)
    *   **Connection UX**: Direct redirect, valid for "Research" & "Analytics" features.

*   **TikTok**
    *   **OAuth Scopes**: `user.info.basic`, `user.info.profile`, `user.info.stats`, `video.list`
    *   **Callback**: `/api/connect/tiktok/callback`
    *   **Note**: Requesting `video.list` confirms the "Repurposing" feature reads existing content directly.

**2. Infrastructure Map**
*   **Core API**: `https://app.virlo.ai/api/...` (observed)
*   **Auth Service**: `https://auth.virlo.ai` (observed)
*   **Affiliate Engine**: `https://virlo.tolt.io` (observed)
*   **Analytics**: PostHog (observed)

**3. Credit Cost Matrix (Live data)**
Observed competitor pricing signals; **do not treat as Crebit policy**.
| Action | Cost (Credits) | Notes |
| :--- | :--- | :--- |
| **Script Gen** | 1-5 | Dynamic based on length |
| **Presentation** | 50-150 | Heavy cost (Images + Slides) |
| **AI Request** | 1-15 | Standard LLM calls |
| **Social Search** | Dynamic | Per-request scraping cost |

**4. UX "Hook" Observations**
*   **Onboarding**: incentivize account connection specifically for "Personalized Growth Suggestions" (value prop).
*   **Top Bar**: Real-time "Credit Balance" next to timezone (always visible visibility).
