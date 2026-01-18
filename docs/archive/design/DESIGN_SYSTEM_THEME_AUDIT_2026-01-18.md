# Design System Theme Audit (Phase 1 Inventory)

**Date**: 2026-01-18  
**Scope**: Light/Dark mode token inventory & gap analysis  
**Sources**: `docs/research/DESIGN_SYSTEM_OVERHAUL_2026.md`, `frontend/src/app/globals.css`

---

## 1) SSoT Anchors

- **Philosophy**: `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
- **UI Flow**: `08_PIPELINES_AND_USER_FLOWS.md`
- **UI Rules**: `10_UI_DESIGN_GUIDE_2025-12.md`
- **Design System Overhaul**: `docs/research/DESIGN_SYSTEM_OVERHAUL_2026.md`

---

## 2) Current Theme Tokens (globals.css)

### 2.1 Light (`:root`)

| Token | Value |
|---|---|
| --bg-0 | #ffffff |
| --bg-1 | #FAFAFA |
| --bg-2 | #F4F4F5 |
| --fg-0 | #09090B |
| --fg-muted | #71717A |
| --accent | #7C3AED |
| --accent-glow | rgba(124, 58, 237, 0.2) |
| --accent-2 | #D97706 |
| --surface-1 | rgba(255, 255, 255, 0.8) |
| --surface-2 | rgba(244, 244, 245, 0.8) |
| --glass-border | rgba(0, 0, 0, 0.08) |
| --glass-highlight | rgba(0, 0, 0, 0.03) |
| --border-muted | rgba(0, 0, 0, 0.1) |
| --border-subtle | rgba(0, 0, 0, 0.05) |
| --success | #059669 |
| --warning | #D97706 |
| --error | #DC2626 |
| --info | #2563EB |

### 2.2 Dark (`.dark`)

| Token | Value |
|---|---|
| --bg-0 | #0F0F1A |
| --bg-1 | #151522 |
| --bg-2 | #1A1A2E |
| --fg-0 | #E8E8ED |
| --fg-muted | #A0A0B0 |
| --accent | #8B5CF6 |
| --accent-glow | rgba(139, 92, 246, 0.4) |
| --accent-2 | #f59e0b |
| --surface-1 | rgba(22, 22, 24, 0.6) |
| --surface-2 | rgba(30, 30, 35, 0.6) |
| --glass-border | rgba(255, 255, 255, 0.08) |
| --glass-highlight | rgba(255, 255, 255, 0.03) |
| --border-muted | rgba(255, 255, 255, 0.1) |
| --border-subtle | rgba(255, 255, 255, 0.05) |
| --success | #10b981 |
| --warning | #f59e0b |
| --error | #ef4444 |
| --info | #3b82f6 |

### 2.3 Common Tokens (`:root` shared)

| Token | Value |
|---|---|
| --lusion-blue | #1a2ffb |
| --lusion-dark-blue | #071bdf |
| --lusion-green | #c1ff00 |
| --lusion-purple | #8832f7 |
| --lusion-red | #ff4c41 |
| --lusion-black | #000000 |
| --lusion-white | #ffffff |
| --lusion-off-white | #f0f1fa |
| --lusion-dark-white | #e4e6ef |
| --vivid-violet | #8B5CF6 |
| --vivid-cyan | #1A2FFB |
| --vivid-emerald | #C1FF00 |
| --vivid-amber | #F59E0B |
| --text-hero | clamp(3rem, 8vw, 8rem) |
| --text-heading | clamp(2rem, 4vw, 4rem) |
| --text-subheading | clamp(1.25rem, 2vw, 2rem) |
| --text-body | clamp(0.875rem, 1vw, 1.125rem) |
| --text-caption | clamp(0.75rem, 0.8vw, 0.875rem) |
| --ease-lusion | cubic-bezier(0.16, 1, 0.3, 1) |
| --ease-bounce | cubic-bezier(0.34, 1.56, 0.64, 1) |
| --ease-out-expo | var(--ease-lusion) |
| --radius-lusion | 20px |
| --global-border-radius | 20px |

---

## 3) Gaps vs 2026 Overhaul Spec

1. **`color-scheme` 미설정** → UA 테마 협상 부재
2. **`prefers-contrast`/`forced-colors`/`prefers-reduced-transparency` 대응 없음**
3. **Semantic/Alias 토큰 부재** → `--bg-base`, `--bg-subtle`, `--fg-on-emphasis` 등 정의 필요
4. **High-Contrast 모드 토큰 없음**
5. **Evidence/Sealed/Credit/Run-State 토큰 미구현** (SSoT 철학 반영 전 단계)
6. **OKLCH/Neutral Scale 미도입** (fallback 전략 필요)

---

## 4) 다음 스텝 (Phase 2 준비)

- **Step 2.1**: Semantic/Alias 토큰 추가 (기존 값 매핑, UI 영향 최소)
- **Step 2.2**: `color-scheme` + preference media queries 뼈대 추가
- **Step 2.3**: High-Contrast 토큰 스켈레톤 도입

> 다음 단계에서는 UI 변경을 최소화하고 **토큰 구조만 확장**한다.
