# Reverse Engineering Report for Execution (Vivid)

**Date**: 2025-12-24  
**Purpose**: Strengthen the evidence and design decisions that will drive the Execution Plan  
**Scope**: Workstreams A-F (IA, Canvas, Data, Credits, Affiliate, Observability)

---

## 0) Evidence Map (Sources)

- Primary UI extraction and tokens: `16_VIRLO_CONTENT_STUDIO_RESEARCH.md`
- Vivid UI guidance baseline: `13_UI_DESIGN_GUIDE_2025-12.md`
- Credits/Billing draft spec: `17_CREDITS_AND_BILLING_SPEC_V1.md`
- Affiliate draft spec: `18_AFFILIATE_PROGRAM_SPEC_V1.md`

**No user-specific data was extracted or stored.**

---

## 0.1) Confidence Legend

- **[OBSERVED]**: directly visible in extracted UI copy or nav labels
- **[INFERRED]**: plausible but not confirmed by DOM text
- **[PROPOSED]**: design choice for Vivid (not derived from Virlo)
- **[TO_VALIDATE]**: requires manual product review or separate research

---

## Workstream A: IA + Onboarding (Product Entry)

### A.1 Navigation Structure

**Observed nav groups** [OBSERVED]
- Dashboard
- Research (Outlier, Creator Search, Orbit Search, Collections, Knowledge Center)
- Creator Hub (Content Studio, Media Generation)
- Accounts (Account, Usage, Billing)
- Changelog, Get Free Credits, Affiliate Program, Support, Community

**Vivid decision** [PROPOSED]
- Left rail groups: Research / Creator Hub / Accounts / Credits / Affiliate
- Credits and Affiliate are top-level for visibility
- "New" badge reserved for major feature launches

**Implementation impact**
- Sidebar component needs grouping support and badge chips
- Top bar must reserve space for credit balance and primary action

**Validation checklist**
- Confirm actual user flows require Credits and Affiliate to be top-level
- Confirm Research grouping aligns with Vivid Evidence Loop

---

### A.2 Empty State + Onboarding

**Observed CTAs and copy** [OBSERVED]
- "Create New Canvas"
- "Create Your First Canvas"
- Positioning copy: "Visual AI content workflow builder"
- Onboarding sections: Core Components, What You Can Build, How It Works

**Vivid decision** [PROPOSED]
- Primary CTA: "Create First Canvas"
- Seed graph: Input -> Capsule -> Script/Beat -> Storyboard -> Output
- Onboarding cards: Core Components, What You Can Build, How It Works

**Implementation impact**
- Empty state component + seed template API
- Onboarding content cards in first-run view

**Validation checklist**
- Confirm seed graph should be the default start for new users

---

## Workstream B: Canvas UX (Interaction DNA)

### B.1 Node Model and Port Logic

**Base structure** [PROPOSED]
- Input nodes: 0 inputs, 1 output
- Processor/Capsule nodes: N inputs, 1 output
- Output nodes: 1 input, 0 outputs

**Connection semantics** [PROPOSED]
- Connection rules by data type (video, text, image, audio, meta)
- Visual affordances (compatible glow, incompatible dim)

**Implementation impact**
- NodeSpec must include port contracts and type rules
- Canvas must enforce compatibility in UI and backend

**Validation checklist**
- Confirm if Vivid wants strict typing or soft warnings in MVP

---

### B.2 Interaction Controls

**Common canvas behaviors** [INFERRED]
- Minimap bottom-right
- Zoom wheel range 10% to 200%
- Lasso select with shift + drag

**Vivid decision** [PROPOSED]
- Include minimap, zoom bounds, and lasso selection for MVP
- Keep hotkeys documented in UI help

**Validation checklist**
- Confirm minimap is essential for first release

---

## Workstream C: Data Model (Context Awareness)

### C.1 NodeSpec Contracts

**Proposed schema** [PROPOSED]
```json
{
  "input_contracts": {
    "required": ["source_context"],
    "optional": ["style_reference"],
    "max_upstream": 5,
    "allowed_types": ["video/mp4", "text/plain", "application/json"],
    "context_mode": "aggregate"
  }
}
```

**Implementation impact**
- NodeSpec table needs `input_contracts` JSONB
- Validation must be enforced in both UI and server

---

### C.2 Execution Context Snapshot

**Requirement** [PROPOSED]
- `CapsuleRun.upstream_inputs`: snapshot of connected lineage
- Store per-run token usage and model version

**Implementation impact**
- CapsuleRun schema extension
- Execution pipeline must serialize upstream inputs

**Validation checklist**
- Confirm max upstream size for performance

---

## Workstream D: Credits + Billing (Economy)

### D.1 Plan Architecture

**Observed tier composition** [OBSERVED]
- Starter: 1,000 credits, 2 account connections
- Pro: 5,000 credits, 4 account connections
- Elite: 12,500 credits, 6 account connections
- Research Analyst: 1 account connection
- Top-up packs: 500 / 2,000 / 5,000 credits
- API packs: 5,000 / 15,000 / 40,000 credits
- Monthly vs Annual toggle with "Annual 30% Off"

**Vivid decision** [PROPOSED]
- Adopt dual model: subscription credits + top-up credits
- Separate creator credits and API credits
- Surface "Get Free Credits" in nav and empty state

**Implementation impact**
- Wallet + ledger schema
- Usage and Billing UI

---

### D.2 Consumption Order and Ledger

**Proposed consumption hierarchy** [PROPOSED]
- Promo (expires) -> Subscription -> Top-up

**Ledger columns** [PROPOSED]
- transaction_id, event_type, amount, balance_snapshot, meta

**Validation checklist**
- Confirm promo expiration policy
- Confirm refund behavior for failed runs

---

## Workstream E: Affiliate (Growth Engine)

### E.1 Referral Logic

**Observed entry point** [OBSERVED]
- Affiliate Program link in nav
- "Get Free Credits" CTA surfaced

**Vivid decision** [PROPOSED]
- Reward: Give 500 / Get 500 credits (draft)
- Trigger: verified email + first generation run
- Rewards issued as promo credits in ledger

**Implementation impact**
- Referral tracking table + reward issuance job
- Credits page module: Copy Link, Earned, Pending

**Validation checklist**
- Confirm reward amount and activation rule

---

## Workstream F: Observability (Cost Transparency)

**Required logs** [PROPOSED]
- model_latency_ms
- input_tokens
- output_tokens
- cost_usd_est
- model_version / prompt_version

**Implementation impact**
- CapsuleRun telemetry fields
- Usage page needs "cost per run" view

**Validation checklist**
- Confirm cost estimation formula

---

## 7) Non-Goals and Cautions

- No OAuth scope or auth callback values are considered verified here.
- No private API endpoints are assumed.
- Do not treat competitor product internals as factual without separate research.

---

## 8) Gate for Execution Plan

Execution Plan should only proceed once:
- IA hierarchy is approved
- NodeSpec contracts are finalized
- Credits consumption order is confirmed
- Affiliate reward trigger is approved
- Observability fields are agreed

---

## 9) Summary of Decisions to Lock

- Left rail grouping and top bar contents
- Empty state CTA + seed graph
- NodeSpec input_contracts format
- Credits wallet hierarchy and tier counts
- Affiliate reward policy
- Observability fields for cost transparency
