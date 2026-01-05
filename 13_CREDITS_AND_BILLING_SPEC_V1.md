# Credits + Billing Spec v1 (Crebit)

**Date**: 2026-01-01  
**Scope**: Creator credits, top-ups, API credits, usage UI, Teaching Apps  
**Goal**: Clear, scalable credit model aligned with content generation workloads

---

## 1) Credit Types (Current Code)

1) **Subscription Credits** (`subscription_credits`)  
- monthly allocation by plan  
- reset on billing cycle  

2) **Top-up Credits** (`topup_credits`)  
- purchased packs  
- no auto-expiry by default  

3) **Promo Credits** (`promo_credits`)  
- affiliate/referral rewards  
- optional expiry (90~180 days)

> Planned: API credits (B2B wallet) are not implemented in current code.

---

## 2) Wallet Model

Each user has a wallet per credit type:
- `subscription_credits`
- `topup_credits`
- `promo_credits`
- `balance` (aggregate)

Consumption order (default):
1. Promo credits (expire first)
2. Creator credits
3. Top-up credits

---

## 3) Ledger Events

Ledger is append-only:
- `promo` (welcome/promo grants)
- `topup` (purchase)
- `usage` (generation)
- `reward` (affiliate/reward)
- `refund` (failed run)

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
- Annual discount label (ex: "Annual 30% Off")
- Tier cards with "Upgrade" CTA
- Top-up packs with one-time purchase
- API packs (separate section)

### Credits CTA
- "Get Free Credits" in nav
- "Invite + Earn" module in Credits page

---

## 5.1) Dimension Apps Credit Model

> **Added**: 2026-01-01, **Updated**: 2026-01-05 (Teaching → Dimension)

Dimension Apps는 **모델별 동적 비용**을 사용 (SSoT: `backend/app/fixtures/dimension_capsules.py`):

| API Endpoint | Credits | Description |
|-------------|---------|-------------|
| `/api/dimension/1d/generate` | 5 (기본값) | 1D Origin - Veo 프롬프트 생성 |
| `/api/dimension/2d/create` | 10 (기본값) | 2D Blueprint - 스토리보드 생성 |
| `/api/dimension/3d/generate` | 5 (기본값) | 3D Ambience - 이미지 프롬프트 생성 |
| `/api/dimension/4d/analyze` | 8 (기본값) | 4D Moment - 레퍼런스 분석 |

### BYOK (Bring Your Own Key)

사용자가 `X-Gemini-API-Key` 헤더로 자신의 API Key를 전달하면:
- 크레딧 차감 없음
- 키는 클라이언트에만 저장 (localStorage 또는 secure storage)
- 서버는 키를 **저장하지 않고** 요청 처리에만 사용

### Error Handling

크레딧 부족 시 `402 Payment Required`:
```json
{
  "code": "INSUFFICIENT_CREDITS",
  "message": "크레딧이 부족합니다.",
  "required": 10,
  "balance": 3
}
```

### Refund Policy

AI 호출 실패 시 자동 환불 (`credit_service.refund_credits`):
- 실패 사유 기록
- topup_credits 버킷으로 복원

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

## 7) API Endpoints (Current)

- `GET /api/v1/credits/balance`
- `GET /api/v1/credits/transactions`
- `POST /api/v1/credits/topup`
- `POST /api/v1/credits/deduct` (internal)

---

## 8) Data Model (Draft)

Tables:
- `user_credits` (wallet per user)
- `credit_ledger`
- `plans`
- `prices`
- `subscriptions`

---

## 9) Guardrails

- No negative balances
- Refund on failed generation
- Promo credits cannot be transferred
