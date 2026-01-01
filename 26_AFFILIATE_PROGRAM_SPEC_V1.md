# Affiliate Program Spec v1 (Crebit)

**Date**: 2025-12-24  
**Scope**: Referral + affiliate flow, credits reward, tracking  
**Goal**: Acquire creators while keeping rewards measurable and fraud-resistant

---

## 1) Roles

- **Referrer**: Existing user who shares invite link
- **Referee**: New user who signs up via link

---

## 2) Reward Model (Draft)

- **Referrer**: +X promo credits after referee activation
- **Referee**: +Y promo credits on activation

Constraints:
- One-time reward per referee
- No reward if refund/chargeback occurs
- Activation requires: verified email + first generation run (완료 시 `activated`)

---

## 3) Tracking

Required fields:
- `affiliate_code`
- `referrer_user_id`
- `referee_user_id`
- `status` (clicked, signed_up, activated, paid)
- `reward_status` (pending, granted, revoked)
 - `reward_ledger_id` (links to credit ledger entry)

---

## 4) UI Surfaces

- Nav item: "Affiliate Program"
- Credits page: "Invite + Earn" card
- Share dialog: copy link + social icons
- Referrals table: status + earned credits

---

## 5) API Endpoints (Spec)

- `GET /api/v1/affiliate/profile`
- `POST /api/v1/affiliate/link`
- `POST /api/v1/affiliate/track` (clicked 기록)
- `POST /api/v1/affiliate/register` (signed_up/activated)
- `GET /api/v1/affiliate/referrals`
- `POST /api/v1/affiliate/reward`

Activation rule:
- referee가 **첫 generation run 완료** 시 `activated`로 승격

---

## 6) Anti-fraud Basics

- Block self-referral by device/IP
- Delay rewards until payment clears
- Manual review for abnormal spikes

---

## 7) External Portal Option

- External affiliate platform (optional)
- Sync rewards into credit ledger
- Keep user-facing stats in Crebit UI
