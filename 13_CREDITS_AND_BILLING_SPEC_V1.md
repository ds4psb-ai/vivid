# Credits + Billing Spec v1 (Crebit)

<details open>
<summary>한국어</summary>

**작성**: 2026-01-01  
**범위**: 크리에이터 크레딧, 탑업, API 크레딧, 사용 UI, Teaching Apps  
**목표**: 콘텐츠 생성 워크로드와 정렬된 명확하고 확장 가능한 크레딧 모델

---

## 1) 크레딧 유형 (현재 코드)

1) **구독 크레딧** (`subscription_credits`)  
- 요금제별 월간 할당  
- 결제 주기마다 리셋

2) **탑업 크레딧** (`topup_credits`)  
- 구매 팩  
- 기본적으로 자동 만료 없음

3) **프로모 크레딧** (`promo_credits`)  
- 어필리에이트/리퍼럴 보상  
- 선택적 만료 (90~180일)

> 계획: API 크레딧(B2B 지갑)은 현재 코드에 미구현.

---

## 2) 지갑 모델

각 사용자는 크레딧 유형별 지갑을 보유:
- `subscription_credits`
- `topup_credits`
- `promo_credits`
- `balance` (합산)

차감 순서 (기본):
1. 프로모 크레딧 (만료 우선)
2. 구독 크레딧
3. 탑업 크레딧

---

## 3) 원장 이벤트

원장은 append-only:
- `promo` (웰컴/프로모 지급)
- `topup` (구매)
- `usage` (생성)
- `reward` (어필리에이트/리워드)
- `refund` (실패 실행)

필수 필드:
- `user_id`
- `event_type`
- `credit_type`
- `amount`
- `run_id` (optional)
- `capsule_id` (optional)
- `source` (subscription, promo, api, admin)
- `created_at`

---

## 4) 요금제 티어 (초안)

크리에이터 요금제 (월/년):
- Starter: 1,000 credits, **2 계정 연결**
- Pro: 5,000 credits, **4 계정 연결**
- Elite: 12,500 credits, **10 계정 연결**
- Research Analyst: **1 계정 연결** (리서치 전용 포지셔닝)

**시각 요구사항**:
- 연간 요금제는 토글 또는 가격 옆에 **"Save 30%"** 배지를 표시해야 함 (pill 형태, accent 색상).
- 참고: `virlo_pricing_plans_1766553472579.png`

탑업 팩:
- 500 / 2,000 / 5,000 credits

API 팩:
- 5,000 / 15,000 / 40,000 credits

메모:
- 수치는 초안이며 사용량 분석 후 조정.
- 티어 이름은 단순하고 크리에이터 친화적으로 유지.

---

## 5) 사용 + 빌링 UI

### Usage 페이지
- 현재 잔액(크레딧 유형별)
- 월간 사용량 (MTD)
- 최근 실행과 크레딧 비용
- 사용 내역 CSV 내보내기
- 상단 바에 현재 크레딧 잔액 상시 표시

### Billing 페이지
- 월간/연간 토글
- 연간 할인 라벨 (예: "Annual 30% Off")
- 티어 카드 + "Upgrade" CTA
- 탑업 팩(일회성 구매)
- API 팩(별도 섹션)

### Credits CTA
- 네비게이션에 "Get Free Credits"
- Credits 페이지에 "Invite + Earn" 모듈

---

## 5.1) Dimension Apps 크레딧 모델

> **추가**: 2026-01-01, **업데이트**: 2026-01-09 (SSoT 통합)

Dimension Apps는 **YAML 기반 SSoT**를 사용:
- **SSoT 위치**: `config/apps/content/dimensions/*.yaml` → `execution.credit_cost`
- **백엔드**: `get_credit_cost()` → AppRegistry SSoT 우선, 하드코딩 폴백
- **프론트엔드**: `/api/dimension/tools` → AppRegistry에서 동적 로딩

| API Endpoint | Credits | Dimension | Description |
|-------------|---------|-----------|-------------|
| `/api/dimension/1d/generate` | 5 | 1D | Veo 프롬프트 생성 |
| `/api/dimension/2d/create` | 10 | 2D | 스토리보드 생성 |
| `/api/dimension/3d/generate` | 5 | 3D | 이미지 프롬프트 생성 |
| `/api/dimension/4d/analyze` | 8 | 4D | 레퍼런스 분석 |
| `/api/dimension/quality/check` | 8 | QC | 품질 검수 |
| `/api/dimension/aesthetic/direct` | 10 | AD | 미학 디렉터 |
| `/api/dimension/persona/analyze` | 5 | AI | 심연 해석 |
| `/api/dimension/story/architect` | 10 | STORY | 스토리 아키텍트 |
| `/api/dimension/sound/craft` | 8 | SOUND | 사운드 크래프터 |
| `/api/dimension/veo/generate` | 200 | VEO | AI 비디오 생성 |

> **Pro 모델 사용 시 3x 비용** (예: 1D Pro = 15 credits)

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

## 6) 크레딧 비용 모델

### 6.1 출력 타입별 기본 비용

| 출력 유형             | 기본 크레딧 | 비고                                   |
|-----------------------|-----------|----------------------------------------|
| 텍스트 요약           | 1         | NotebookLM 출력, 단일 청크             |
| 스크립트 (숏폼)       | 1-5       | Hook/body/CTA, 약 60초 영상            |
| 스크립트 (롱폼)       | 5-15      | 다중 섹션, 약 3~10분 영상              |
| 스토리보드 프리뷰     | 10-25     | 비주얼 비트 레이아웃, 최종 렌더 없음   |
| 오디오 오버뷰         | 15-30     | NotebookLM 팟캐스트 스타일 오디오      |
| 프레젠테이션 덱       | 50-150    | 비주얼 포함 멀티 슬라이드 내보내기     |
| 최종 비디오 렌더      | 100-300   | 전체 출력, 해상도/길이 기반            |

### 6.2 곱셈 요소

| 요소                  | 배수 범위           | 비고                                  |
|-----------------------|---------------------|---------------------------------------|
| **해상도**            | 1x (720p) ~ 2x (4K) | 해상도 높을수록 비용 증가             |
| **길이**              | 1x (≤60s) ~ 3x (>5min) | 길이가 길수록 비용 증가             |
| **모델 티어**         | 1x (Standard) ~ 1.5x (Premium) | 고급 모델 사용                 |
| **캡슐 타입**         | 1x (Notebook) / 1.2x (Workflow) / 1.5x (Hybrid) | 복잡도 계수  |

### 6.3 크레딧 계산식

```
total_credits = base_cost × resolution_mult × length_mult × model_mult × capsule_mult
```

### 6.4 예시 시나리오

1. **빠른 스크립트** (숏폼, 720p, Standard): `5 × 1 × 1 × 1 × 1 = 5 credits`
2. **롱폼 비디오 렌더** (4K, 8 min, Premium, Hybrid): `200 × 2 × 2.5 × 1.5 × 1.5 = 2,250 credits`
3. **프레젠테이션 덱** (Standard, Notebook): `100 × 1 × 1 × 1 × 1 = 100 credits`

> [!TIP]
> 실제 비용은 Virlo 벤치마크 (`18_REVERSE_ENGINEERING_REPORT`) 기반 추정치입니다.
> 런칭 후 실제 사용량 분석을 통해 조정 예정.

---

## 7) API 엔드포인트 (현재)

- `GET /api/v1/credits/balance`
- `GET /api/v1/credits/transactions`
- `POST /api/v1/credits/topup`
- `POST /api/v1/credits/deduct` (internal)

---

## 8) 데이터 모델 (초안)

Tables:
- `user_credits` (wallet per user)
- `credit_ledger`
- `plans`
- `prices`
- `subscriptions`

---

## 9) 가드레일

- 마이너스 잔액 금지
- 생성 실패 시 환불
- 프로모 크레딧 양도 불가

</details>

<details>
<summary>English</summary>

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
2. Subscription credits
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
- Research Analyst: **1 account connection** (research-only positioning)

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

> **Added**: 2026-01-01, **Updated**: 2026-01-09 (SSoT aligned)

Dimension Apps use **YAML-based SSoT**:
- **SSoT location**: `config/apps/content/dimensions/*.yaml` → `execution.credit_cost`
- **Backend**: `get_credit_cost()` → AppRegistry SSoT first, hardcoded fallback
- **Frontend**: `/api/dimension/tools` → dynamic load from AppRegistry

| API Endpoint | Credits | Dimension | Description |
|-------------|---------|-----------|-------------|
| `/api/dimension/1d/generate` | 5 | 1D | Generate Veo prompt |
| `/api/dimension/2d/create` | 10 | 2D | Create storyboard |
| `/api/dimension/3d/generate` | 5 | 3D | Generate image prompt |
| `/api/dimension/4d/analyze` | 8 | 4D | Analyze reference |
| `/api/dimension/quality/check` | 8 | QC | Quality check |
| `/api/dimension/aesthetic/direct` | 10 | AD | Aesthetic director |
| `/api/dimension/persona/analyze` | 5 | AI | Persona analysis |
| `/api/dimension/story/architect` | 10 | STORY | Story architect |
| `/api/dimension/sound/craft` | 8 | SOUND | Sound crafter |
| `/api/dimension/veo/generate` | 200 | VEO | AI video generation |

> **3x cost for Pro models** (e.g., 1D Pro = 15 credits)

### BYOK (Bring Your Own Key)

If the user passes their API key via `X-Gemini-API-Key` header:
- No credit deduction
- Key is stored only on the client (localStorage or secure storage)
- Server **does not store** the key and uses it only to fulfill the request

### Error Handling

Return `402 Payment Required` on insufficient credits:
```json
{
  "code": "INSUFFICIENT_CREDITS",
  "message": "크레딧이 부족합니다.",
  "required": 10,
  "balance": 3
}
```

### Refund Policy

Auto-refund on AI call failure (`credit_service.refund_credits`):
- Record failure reason
- Restore to topup_credits bucket

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
> Actual costs are estimates based on the Virlo benchmark (`18_REVERSE_ENGINEERING_REPORT`).
> Adjust after launch based on real usage data.

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

</details>
