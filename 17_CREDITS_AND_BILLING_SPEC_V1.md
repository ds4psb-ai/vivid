# Credits + Billing Spec v1 (Vivid)

**Date**: 2025-12-24  
**Scope**: Creator credits, top-ups, API credits, usage UI  
**Goal**: Clear, scalable credit model aligned with content generation workloads

---

## 1) Credit Types

1) **Creator Credits (subscription)**  
- monthly allocation by plan  
- reset on billing cycle  

2) **Top-up Credits (one-time)**  
- purchased packs  
- no auto-expiry by default  

3) **API Credits (B2B)**  
- separate wallet for API usage  
- one-time packs  

4) **Promo Credits**  
- affiliate/referral rewards  
- optional expiry (90~180 days)

---

## 2) Wallet Model

Each user has a wallet per credit type:
- `creator_balance`
- `topup_balance`
- `api_balance`
- `promo_balance`

Consumption order (default):
1. Promo credits (expire first)
2. Creator credits
3. Top-up credits

---

## 3) Ledger Events

Ledger is append-only:
- `credit_grant` (subscription, promo, manual)
- `credit_purchase` (top-up, API pack)
- `credit_spend` (generation, export)
- `credit_refund` (failed run)
- `credit_expire`

Required fields:
- `user_id`
- `event_type`
- `credit_type`
- `amount`
- `run_id` (optional)
- `capsule_id` (optional)
- `source` (subscription, promo, api, admin)
- `created_at`

---

## 4) Pricing Tiers (Draft)

Creator plans (monthly / yearly):
- Starter: 1,000 credits, **2 account connections**
- Pro: 5,000 credits, **4 account connections**
- Elite: 12,500 credits, **10 account connections**
- Research Analyst: **1 account connection** (research‑only positioning)

**Visual Requirement**:
- Annual plans must display a **"Save 30%"** badge (pill shape, accent color) near the toggle or price.
- Reference: `virlo_pricing_plans_1766553472579.png`

Top-up packs:
- 500 / 2,000 / 5,000 credits

API packs:
- 5,000 / 15,000 / 40,000 credits

Notes:
- Numbers are draft; adjust after usage analysis.
- Keep tier names simple and creator-friendly.

---

## 5) Usage + Billing UI

### Usage page
- Current balance (by credit type)
- Month-to-date spend
- Recent runs with credit cost
- Export usage CSV
 - Top bar always shows current credit balance

### Billing page
- Monthly/Yearly toggle
- Annual discount label (ex: “Annual 30% Off”)
- Tier cards with "Upgrade" CTA
- Top-up packs with one-time purchase
- API packs (separate section)

### Credits CTA
- "Get Free Credits" in nav
- "Invite + Earn" module in Credits page

---

## 6) Credit Cost Model

### 6.1 Base Cost by Output Type

| Output Type           | Base Credits | Notes                                   |
|-----------------------|--------------|-----------------------------------------|
| Text Summary          | 1            | NotebookLM output, single chunk         |
| Script (Short-form)   | 1-5          | Hook/body/CTA, ~60s video               |
| Script (Long-form)    | 5-15         | Multi-section, ~3-10 min video          |
| Storyboard Preview    | 10-25        | Visual beat layout, no final render     |
| Audio Overview        | 15-30        | NotebookLM podcast-style audio          |
| Presentation Deck     | 50-150       | Multi-slide export with visuals         |
| Final Video Render    | 100-300      | Full output, resolution/length-based    |

### 6.2 Multipliers

| Factor                | Multiplier Range | Notes                                   |
|-----------------------|------------------|-----------------------------------------|
| **Resolution**        | 1x (720p) ~ 2x (4K) | Higher resolution = more compute      |
| **Length**            | 1x (≤60s) ~ 3x (>5min) | Longer outputs scale cost           |
| **Model Tier**        | 1x (Standard) ~ 1.5x (Premium) | Advanced model access           |
| **Capsule Type**      | 1x (Notebook) / 1.2x (Workflow) / 1.5x (Hybrid) | Complexity factor  |

### 6.3 Credit Calculation Formula

```
total_credits = base_cost × resolution_mult × length_mult × model_mult × capsule_mult
```

### 6.4 Example Scenarios

1. **Quick Script** (Short-form, 720p, Standard): `5 × 1 × 1 × 1 × 1 = 5 credits`
2. **Long-form Video Render** (4K, 8 min, Premium, Hybrid): `200 × 2 × 2.5 × 1.5 × 1.5 = 2,250 credits`
3. **Presentation Deck** (Standard, Notebook): `100 × 1 × 1 × 1 × 1 = 100 credits`

> [!TIP]
> 실제 비용은 Virlo 벤치마크 (`18_REVERSE_ENGINEERING_REPORT`) 기반 추정치입니다.
> 런칭 후 실제 사용량 분석을 통해 조정 예정.

---

## 7) API Endpoints (Spec)

- `GET /api/v1/credits/wallet`
- `GET /api/v1/credits/ledger`
- `POST /api/v1/credits/topup`
- `POST /api/v1/credits/allocate`
- `POST /api/v1/credits/refund`

---

## 8) Data Model (Draft)

Tables:
- `credit_wallets`
- `credit_ledger`
- `plans`
- `prices`
- `subscriptions`

---

## 9) Guardrails

- No negative balances
- Refund on failed generation
- Promo credits cannot be transferred
