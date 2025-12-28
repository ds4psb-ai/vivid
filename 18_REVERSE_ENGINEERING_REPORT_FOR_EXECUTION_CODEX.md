# Reverse Engineering Report for Execution (Crebit)

**Date**: 2025-12-24  
**Updated**: 2025-12-28  
**Purpose**: Strengthen the evidence and design decisions that will drive the Execution Plan  
**Scope**: Workstreams A-F (IA, Canvas, Data, Credits, Affiliate, Observability)

---

## 0) Evidence Map (Sources)

- Primary UI extraction and tokens: `16_VIRLO_CONTENT_STUDIO_RESEARCH.md`
- Crebit UI guidance baseline: `13_UI_DESIGN_GUIDE_2025-12.md`
- Credits/Billing draft spec: `17_CREDITS_AND_BILLING_SPEC_V1.md`
- Affiliate draft spec: `35_AFFILIATE_PROGRAM_SPEC_V1.md`

**No user-specific data was extracted or stored.**

---

## 0.1) Confidence Legend

- **[OBSERVED]**: directly visible in extracted UI copy or nav labels
- **[INFERRED]**: plausible but not confirmed by DOM text
- **[PROPOSED]**: design choice for Crebit (not derived from Virlo)
- **[TO_VALIDATE]**: requires manual product review or separate research

---

## 0.2) SoR Alignment

이 문서는 역설계 참고용이며, **최종 결정/계약은 정본 문서에 반영**한다.

- UI/UX 정본: `13_UI_DESIGN_GUIDE_2025-12.md`
- Node/캡슐 계약: `01_NODE_CANVAS_TECHNICAL_SPECIFICATION.md`, `05_CAPSULE_NODE_SPEC.md`
- 파이프라인/역할: `10_PIPELINES_AND_USER_FLOWS.md`
- Growth 스펙: `17_CREDITS_AND_BILLING_SPEC_V1.md`, `35_AFFILIATE_PROGRAM_SPEC_V1.md`

---

## Workstream A: IA + Onboarding (Product Entry)

### A.1 Navigation Structure

**Observed nav groups** [OBSERVED]
- Dashboard
- Research (Outlier, Creator Search, Orbit Search, Collections, Knowledge Center)
- Creator Hub (Content Studio, Media Generation)
- Accounts (Account, Usage, Billing)
- Changelog, Get Free Credits, Affiliate Program, Support, Community

**Crebit alignment (candidate → SoR)** [PROPOSED]
- 후보 요약: Left rail 그룹/CTA 배치/New 배지 규칙
- 확정 문서: `13_UI_DESIGN_GUIDE_2025-12.md`

**Implementation impact**
- Sidebar component needs grouping support and badge chips
- Top bar must reserve space for credit balance and primary action

**Validation checklist**
- Confirm actual user flows require Credits and Affiliate to be top-level
- Confirm Research grouping aligns with Crebit Evidence Loop

---

### A.2 Empty State + Onboarding

**Observed CTAs and copy** [OBSERVED]
- "Create New Canvas"
- "Create Your First Canvas"
- Positioning copy: "Visual AI content workflow builder"
- Onboarding sections: Core Components, What You Can Build, How It Works

**Crebit alignment (candidate → SoR)** [PROPOSED]
- 후보 요약: Empty state CTA / Seed graph / Onboarding cards
- 확정 문서: `13_UI_DESIGN_GUIDE_2025-12.md`, `23_TEMPLATE_SYSTEM_SPEC_CODEX.md`

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

**Crebit alignment (candidate → SoR)** [PROPOSED]
- 후보 요약: 타입 기반 연결 규칙/시각적 호환 피드백
- 확정 문서: `01_NODE_CANVAS_TECHNICAL_SPECIFICATION.md`, `05_CAPSULE_NODE_SPEC.md`

**Implementation impact**
- NodeSpec must include port contracts and type rules
- Canvas must enforce compatibility in UI and backend

**Validation checklist**
- Confirm if Crebit wants strict typing or soft warnings in MVP

---

### B.2 Interaction Controls

**Common canvas behaviors** [INFERRED]
- Minimap bottom-right
- Zoom wheel range 10% to 200%
- Lasso select with shift + drag

**Crebit alignment (candidate → SoR)** [PROPOSED]
- 후보 요약: 미니맵/줌 범위/라쏘 선택/핫키 표기
- 확정 문서: `01_NODE_CANVAS_TECHNICAL_SPECIFICATION.md`, `13_UI_DESIGN_GUIDE_2025-12.md`

**Validation checklist**
- Confirm minimap is essential for first release

---

## Workstream C: Data Model (Context Awareness)

### C.1 NodeSpec Contracts

**Crebit alignment (candidate → SoR)** [PROPOSED]
- 후보 요약: input_contracts 필드(required/optional/max_upstream/allowed_types/context_mode)
- 확정 문서: `05_CAPSULE_NODE_SPEC.md`, `01_NODE_CANVAS_TECHNICAL_SPECIFICATION.md`

**Implementation impact**
- NodeSpec table needs `input_contracts` JSONB
- Validation must be enforced in both UI and server

---

### C.2 Execution Context Snapshot

**Crebit alignment (candidate → SoR)** [PROPOSED]
- 후보 요약: upstream snapshot + token/model version 기록
- 확정 문서: `05_CAPSULE_NODE_SPEC.md`

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

**Crebit alignment (candidate → SoR)** [PROPOSED]
- 후보 요약: 구독+탑업, Creator/API 분리, Credits CTA 위치
- 확정 문서: `17_CREDITS_AND_BILLING_SPEC_V1.md`

**Implementation impact**
- Wallet + ledger schema
- Usage and Billing UI

---

### D.2 Consumption Order and Ledger

**Crebit alignment (candidate → SoR)** [PROPOSED]
- 후보 요약: 소비 우선순위/ledger 컬럼
- 확정 문서: `17_CREDITS_AND_BILLING_SPEC_V1.md`

**Validation checklist**
- Confirm promo expiration policy
- Confirm refund behavior for failed runs

---

## Workstream E: Affiliate (Growth Engine)

### E.1 Referral Logic

**Observed entry point** [OBSERVED]
- Affiliate Program link in nav
- "Get Free Credits" CTA surfaced

**Crebit alignment (candidate → SoR)** [PROPOSED]
- 후보 요약: 리워드 규칙/트리거/지급 방식
- 확정 문서: `35_AFFILIATE_PROGRAM_SPEC_V1.md`

**Implementation impact**
- Referral tracking table + reward issuance job
- Credits page module: Copy Link, Earned, Pending

**Validation checklist**
- Confirm reward amount and activation rule

---

## Workstream F: Observability (Cost Transparency)

**Crebit alignment (candidate → SoR)** [PROPOSED]
- 후보 요약: run telemetry 필드(latency/token/cost/version)
- 확정 문서: `05_CAPSULE_NODE_SPEC.md`

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
- `13_UI_DESIGN_GUIDE_2025-12.md` 승인 (IA/Empty state)
- `05_CAPSULE_NODE_SPEC.md` 확정 (NodeSpec/Run telemetry)
- `17_CREDITS_AND_BILLING_SPEC_V1.md` 확정 (credits 정책)
- `35_AFFILIATE_PROGRAM_SPEC_V1.md` 확정 (reward policy)

---

## 9) Summary of Decisions to Lock

정본 확정 항목은 위 Gate 문서에 반영하며, 이 문서는 **관측/후보 기록**만 유지한다.
